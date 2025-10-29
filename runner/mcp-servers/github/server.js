/**
 * AutoCodit Agent - GitHub MCP Server
 * 
 * Model Context Protocol server for GitHub operations
 */

const { MCPServer } = require('@modelcontextprotocol/sdk/server');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio');
const { Octokit } = require('octokit');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const config = {
    port: process.env.MCP_SERVER_PORT || 2301,
    githubToken: process.env.GITHUB_TOKEN,
    installationId: process.env.GITHUB_INSTALLATION_ID,
    logLevel: process.env.LOG_LEVEL || 'INFO'
};

// Logging
function log(level, message, data = {}) {
    console.log(JSON.stringify({
        timestamp: new Date().toISOString(),
        level,
        component: 'github-mcp-server',
        message,
        ...data
    }));
}

class GitHubMCPServer {
    constructor() {
        this.server = new MCPServer(
            {
                name: 'github-mcp-server',
                version: '1.0.0'
            },
            {
                capabilities: {
                    tools: {},
                    resources: {},
                    prompts: {}
                }
            }
        );
        
        this.octokit = null;
        this.setupToolHandlers();
    }
    
    async initialize() {
        // Initialize GitHub client
        if (config.githubToken) {
            this.octokit = new Octokit({ auth: config.githubToken });
        } else {
            log('WARN', 'No GitHub token provided, some operations will fail');
        }
        
        log('INFO', 'GitHub MCP Server initialized');
    }
    
    setupToolHandlers() {
        // File operations
        this.server.setRequestHandler('tools/call', 'list_files', async (request) => {
            return await this.listFiles(request.params);
        });
        
        this.server.setRequestHandler('tools/call', 'read_file', async (request) => {
            return await this.readFile(request.params);
        });
        
        this.server.setRequestHandler('tools/call', 'write_file', async (request) => {
            return await this.writeFile(request.params);
        });
        
        // Git operations
        this.server.setRequestHandler('tools/call', 'create_branch', async (request) => {
            return await this.createBranch(request.params);
        });
        
        this.server.setRequestHandler('tools/call', 'commit_changes', async (request) => {
            return await this.commitChanges(request.params);
        });
        
        // Repository analysis
        this.server.setRequestHandler('tools/call', 'analyze_repository', async (request) => {
            return await this.analyzeRepository(request.params);
        });
        
        // Code search
        this.server.setRequestHandler('tools/call', 'search_code', async (request) => {
            return await this.searchCode(request.params);
        });
        
        log('INFO', 'Tool handlers registered');
    }
    
    async listFiles(params) {
        const { path: dirPath = '.' } = params;
        
        try {
            const fullPath = path.resolve('/workspace/repo', dirPath);
            const entries = await fs.readdir(fullPath, { withFileTypes: true });
            
            const files = entries.map(entry => ({
                name: entry.name,
                type: entry.isDirectory() ? 'directory' : 'file',
                path: path.join(dirPath, entry.name)
            }));
            
            log('DEBUG', `Listed ${files.length} files in ${dirPath}`);
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ files, path: dirPath })
                }]
            };
            
        } catch (error) {
            log('ERROR', 'Failed to list files', { path: dirPath, error: error.message });
            throw new Error(`Failed to list files: ${error.message}`);
        }
    }
    
    async readFile(params) {
        const { path: filePath } = params;
        
        if (!filePath) {
            throw new Error('File path is required');
        }
        
        try {
            const fullPath = path.resolve('/workspace/repo', filePath);
            const content = await fs.readFile(fullPath, 'utf8');
            
            log('DEBUG', `Read file: ${filePath}`, { size: content.length });
            
            return {
                content: [{
                    type: 'text',
                    text: content
                }]
            };
            
        } catch (error) {
            log('ERROR', 'Failed to read file', { path: filePath, error: error.message });
            throw new Error(`Failed to read file: ${error.message}`);
        }
    }
    
    async writeFile(params) {
        const { path: filePath, content, message = 'Update file via AutoCodit Agent' } = params;
        
        if (!filePath || content === undefined) {
            throw new Error('File path and content are required');
        }
        
        try {
            const fullPath = path.resolve('/workspace/repo', filePath);
            
            // Ensure directory exists
            await fs.mkdir(path.dirname(fullPath), { recursive: true });
            
            // Write file
            await fs.writeFile(fullPath, content, 'utf8');
            
            log('INFO', `Wrote file: ${filePath}`, { size: content.length });
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({
                        success: true,
                        path: filePath,
                        size: content.length
                    })
                }]
            };
            
        } catch (error) {
            log('ERROR', 'Failed to write file', { path: filePath, error: error.message });
            throw new Error(`Failed to write file: ${error.message}`);
        }
    }
    
    async analyzeRepository(params) {
        log('INFO', 'Analyzing repository structure');
        
        try {
            const analysis = {
                structure: await this.analyzeStructure(),
                languages: await this.analyzeLanguages(),
                dependencies: await this.analyzeDependencies(),
                tests: await this.analyzeTests(),
                documentation: await this.analyzeDocumentation()
            };
            
            log('INFO', 'Repository analysis completed', {
                files_analyzed: analysis.structure.total_files,
                languages: analysis.languages.map(l => l.name)
            });
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify(analysis, null, 2)
                }]
            };
            
        } catch (error) {
            log('ERROR', 'Repository analysis failed', { error: error.message });
            throw new Error(`Repository analysis failed: ${error.message}`);
        }
    }
    
    async analyzeStructure() {
        const structure = {
            directories: [],
            files: [],
            total_files: 0,
            total_directories: 0
        };
        
        async function walkDir(dir, relativePath = '') {
            const entries = await fs.readdir(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                const relPath = path.join(relativePath, entry.name);
                
                // Skip common ignore patterns
                if (entry.name.startsWith('.') || 
                    entry.name === 'node_modules' ||
                    entry.name === '__pycache__' ||
                    entry.name === 'target' ||
                    entry.name === 'dist' ||
                    entry.name === 'build') {
                    continue;
                }
                
                if (entry.isDirectory()) {
                    structure.directories.push(relPath);
                    structure.total_directories++;
                    await walkDir(fullPath, relPath);
                } else {
                    const stats = await fs.stat(fullPath);
                    structure.files.push({
                        path: relPath,
                        size: stats.size,
                        extension: path.extname(entry.name),
                        modified: stats.mtime
                    });
                    structure.total_files++;
                }
            }
        }
        
        await walkDir('/workspace/repo');
        return structure;
    }
    
    async analyzeLanguages() {
        // Simple language detection based on file extensions
        const languageMap = {
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.py': 'Python',
            '.go': 'Go',
            '.java': 'Java',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        };
        
        const languageCounts = {};
        
        // Count files by extension
        const structure = await this.analyzeStructure();
        
        for (const file of structure.files) {
            const lang = languageMap[file.extension];
            if (lang) {
                languageCounts[lang] = (languageCounts[lang] || 0) + 1;
            }
        }
        
        // Convert to sorted array
        return Object.entries(languageCounts)
            .map(([name, count]) => ({ name, count, percentage: (count / structure.total_files * 100).toFixed(1) }))
            .sort((a, b) => b.count - a.count);
    }
    
    async analyzeDependencies() {
        const dependencies = [];
        
        // Check package.json
        try {
            const packageJson = JSON.parse(
                await fs.readFile('/workspace/repo/package.json', 'utf8')
            );
            
            const deps = {
                ...packageJson.dependencies,
                ...packageJson.devDependencies
            };
            
            dependencies.push({
                type: 'npm',
                count: Object.keys(deps).length,
                packages: Object.keys(deps)
            });
            
        } catch (error) {
            // No package.json found
        }
        
        // Check requirements.txt
        try {
            const requirements = await fs.readFile('/workspace/repo/requirements.txt', 'utf8');
            const packages = requirements.split('\n')
                .filter(line => line.trim() && !line.startsWith('#'))
                .map(line => line.split(/[>=<~!]/)[0]);
            
            dependencies.push({
                type: 'pip',
                count: packages.length,
                packages
            });
            
        } catch (error) {
            // No requirements.txt found
        }
        
        return dependencies;
    }
    
    async analyzeTests() {
        const tests = {
            frameworks: [],
            test_files: [],
            coverage_config: null
        };
        
        // Look for test files and configurations
        const structure = await this.analyzeStructure();
        
        for (const file of structure.files) {
            const filename = path.basename(file.path);
            
            // Test files
            if (filename.includes('test') || filename.includes('spec') || 
                file.path.includes('__tests__') || file.path.includes('/tests/')) {
                tests.test_files.push(file.path);
            }
            
            // Test configurations
            if (filename === 'jest.config.js' || filename === 'jest.config.json') {
                tests.frameworks.push('jest');
            }
            if (filename === 'vitest.config.js') {
                tests.frameworks.push('vitest');
            }
            if (filename === 'pytest.ini' || filename === 'pyproject.toml') {
                tests.frameworks.push('pytest');
            }
        }
        
        return tests;
    }
    
    async analyzeDocumentation() {
        const docs = {
            readme: null,
            documentation_files: [],
            api_docs: null
        };
        
        const structure = await this.analyzeStructure();
        
        for (const file of structure.files) {
            const filename = path.basename(file.path).toLowerCase();
            
            if (filename.startsWith('readme')) {
                docs.readme = file.path;
            }
            
            if (filename.endsWith('.md') || filename.endsWith('.rst')) {
                docs.documentation_files.push(file.path);
            }
        }
        
        return docs;
    }
    
    extractRepoFromUrl(url) {
        const match = url.match(/github\.com[:/]([^/]+)\/([^/.]+)/);
        if (match) {
            return { owner: match[1], repo: match[2] };
        }
        throw new Error(`Invalid repository URL: ${url}`);
    }
}

// Start the MCP server
async function main() {
    const mcpServer = new GitHubMCPServer();
    
    try {
        await mcpServer.initialize();
        
        // Create transport
        const transport = new StdioServerTransport();
        await mcpServer.server.connect(transport);
        
        log('INFO', 'GitHub MCP Server started successfully');
        
    } catch (error) {
        log('ERROR', 'Failed to start GitHub MCP Server', { error: error.message });
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGTERM', () => {
    log('INFO', 'GitHub MCP Server shutting down');
    process.exit(0);
});

process.on('SIGINT', () => {
    log('INFO', 'GitHub MCP Server shutting down');
    process.exit(0);
});

main();