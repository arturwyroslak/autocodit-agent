/**
 * AutoCodit Agent - GitHub MCP Server
 * 
 * Model Context Protocol server for GitHub repository operations.
 * Provides tools for file operations, branch management, and GitHub API interactions.
 */

const http = require('http');
const url = require('url');
const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');
const { promisify } = require('util');

const exec = promisify(require('child_process').exec);

// Configuration
const CONFIG = {
    port: parseInt(process.env.MCP_PORT || '2301'),
    workspace: '/workspace/repository',
    githubToken: process.env.GITHUB_TOKEN || '',
    repository: process.env.GITHUB_REPOSITORY || '',
    branch: process.env.GITHUB_BRANCH || 'main',
    sessionId: process.env.SESSION_ID || '',
    taskId: process.env.TASK_ID || ''
};

// Logging utility
function log(level, message, metadata = {}) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        level,
        message,
        component: 'github-mcp-server',
        session_id: CONFIG.sessionId,
        task_id: CONFIG.taskId,
        ...metadata
    };
    
    console.log(JSON.stringify(logEntry));
}

// MCP Tool implementations
const tools = {
    async list_files(params = {}) {
        const targetPath = params.path || '.';
        const fullPath = path.join(CONFIG.workspace, targetPath);
        
        try {
            const files = [];
            
            async function walkDir(dir, relativePath = '') {
                const entries = await fs.readdir(dir, { withFileTypes: true });
                
                for (const entry of entries) {
                    const entryPath = path.join(relativePath, entry.name);
                    
                    if (entry.isDirectory()) {
                        // Skip common ignore directories
                        if (['.git', 'node_modules', '__pycache__', '.pytest_cache', 'target', 'dist'].includes(entry.name)) {
                            continue;
                        }
                        await walkDir(path.join(dir, entry.name), entryPath);
                    } else {
                        files.push(entryPath);
                    }
                }
            }
            
            await walkDir(fullPath);
            
            log('DEBUG', `Listed ${files.length} files`, { path: targetPath });
            
            return { files };
        } catch (error) {
            log('ERROR', `Failed to list files: ${error.message}`, { path: targetPath });
            throw error;
        }
    },
    
    async read_file(params) {
        const { file_path } = params;
        const fullPath = path.join(CONFIG.workspace, file_path);
        
        try {
            const content = await fs.readFile(fullPath, 'utf8');
            
            log('DEBUG', `Read file: ${file_path}`, { size: content.length });
            
            return { content, file_path, size: content.length };
        } catch (error) {
            log('ERROR', `Failed to read file: ${error.message}`, { file_path });
            throw error;
        }
    },
    
    async write_file(params) {
        const { file_path, content } = params;
        const fullPath = path.join(CONFIG.workspace, file_path);
        
        try {
            // Ensure directory exists
            await fs.mkdir(path.dirname(fullPath), { recursive: true });
            
            // Write file
            await fs.writeFile(fullPath, content, 'utf8');
            
            log('INFO', `Wrote file: ${file_path}`, { size: content.length });
            
            return { file_path, size: content.length, success: true };
        } catch (error) {
            log('ERROR', `Failed to write file: ${error.message}`, { file_path });
            throw error;
        }
    },
    
    async execute_command(params) {
        const { command, timeout = 300 } = params;
        
        try {
            log('INFO', `Executing command: ${command}`);
            
            const { stdout, stderr } = await exec(command, {
                cwd: CONFIG.workspace,
                timeout: timeout * 1000,
                maxBuffer: 1024 * 1024 // 1MB
            });
            
            log('DEBUG', 'Command executed successfully', { command });
            
            return {
                exit_code: 0,
                stdout: stdout.trim(),
                stderr: stderr.trim(),
                success: true
            };
        } catch (error) {
            log('ERROR', `Command failed: ${error.message}`, { command });
            
            return {
                exit_code: error.code || 1,
                stdout: error.stdout || '',
                stderr: error.stderr || error.message,
                success: false
            };
        }
    },
    
    async create_branch(params) {
        const { branch_name, base_branch = 'main' } = params;
        
        try {
            // Create new branch
            await exec(`git checkout -b ${branch_name}`, { cwd: CONFIG.workspace });
            
            log('INFO', `Created branch: ${branch_name}`, { base_branch });
            
            return { branch_name, base_branch, success: true };
        } catch (error) {
            log('ERROR', `Failed to create branch: ${error.message}`, { branch_name });
            throw error;
        }
    },
    
    async create_commit(params) {
        const { branch_name, commit_message, files = [] } = params;
        
        try {
            // Switch to branch
            await exec(`git checkout ${branch_name}`, { cwd: CONFIG.workspace });
            
            // Stage files
            if (files.length > 0) {
                const filePaths = files.map(f => f.file_path).join(' ');
                await exec(`git add ${filePaths}`, { cwd: CONFIG.workspace });
            } else {
                await exec('git add .', { cwd: CONFIG.workspace });
            }
            
            // Create commit
            await exec(`git commit -m "${commit_message}"`, { cwd: CONFIG.workspace });
            
            // Get commit SHA
            const { stdout: sha } = await exec('git rev-parse HEAD', { cwd: CONFIG.workspace });
            
            log('INFO', `Created commit: ${sha.trim()}`, { branch_name, files_count: files.length });
            
            return {
                sha: sha.trim(),
                branch_name,
                commit_message,
                files_changed: files.length,
                success: true
            };
        } catch (error) {
            log('ERROR', `Failed to create commit: ${error.message}`, { branch_name });
            throw error;
        }
    },
    
    async search_relevant_files(params) {
        const { query, max_results = 10 } = params;
        
        try {
            // Simple grep-based search
            const { stdout } = await exec(
                `grep -r -l "${query}" . --include="*.py" --include="*.js" --include="*.ts" --include="*.java" --include="*.go" | head -${max_results}`,
                { cwd: CONFIG.workspace }
            );
            
            const files = stdout.trim().split('\n').filter(f => f);
            
            log('DEBUG', `Found ${files.length} relevant files`, { query });
            
            return { files, query };
        } catch (error) {
            // No matches found is not an error
            return { files: [], query };
        }
    },
    
    async validate_syntax(params) {
        const { file_path } = params;
        const fullPath = path.join(CONFIG.workspace, file_path);
        
        try {
            const ext = path.extname(file_path).toLowerCase();
            let command;
            
            switch (ext) {
                case '.py':
                    command = `python3 -m py_compile ${fullPath}`;
                    break;
                case '.js':
                case '.jsx':
                    command = `node --check ${fullPath}`;
                    break;
                case '.ts':
                case '.tsx':
                    command = `npx tsc --noEmit ${fullPath}`;
                    break;
                default:
                    return { valid: true, message: 'Syntax validation not supported for this file type' };
            }
            
            await exec(command);
            
            return { valid: true, file_path };
        } catch (error) {
            return {
                valid: false,
                file_path,
                error: error.message
            };
        }
    }
};

// HTTP server for MCP protocol
const server = http.createServer(async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Content-Type', 'application/json');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;
    
    try {
        if (req.method === 'GET' && pathname === '/health') {
            res.writeHead(200);
            res.end(JSON.stringify({ status: 'healthy', server: 'github-mcp' }));
            return;
        }
        
        if (req.method === 'GET' && pathname === '/tools') {
            res.writeHead(200);
            res.end(JSON.stringify({
                tools: Object.keys(tools).map(name => ({
                    name,
                    description: `GitHub MCP tool: ${name}`
                }))
            }));
            return;
        }
        
        if (req.method === 'POST' && pathname.startsWith('/tools/')) {
            const toolName = pathname.replace('/tools/', '');
            
            if (!tools[toolName]) {
                res.writeHead(404);
                res.end(JSON.stringify({ error: `Tool not found: ${toolName}` }));
                return;
            }
            
            // Parse request body
            let body = '';
            req.on('data', chunk => {
                body += chunk.toString();
            });
            
            req.on('end', async () => {
                try {
                    const params = body ? JSON.parse(body) : {};
                    const result = await tools[toolName](params);
                    
                    res.writeHead(200);
                    res.end(JSON.stringify(result));
                } catch (error) {
                    log('ERROR', `Tool execution failed: ${error.message}`, { tool: toolName });
                    
                    res.writeHead(500);
                    res.end(JSON.stringify({ error: error.message }));
                }
            });
            
            return;
        }
        
        // Not found
        res.writeHead(404);
        res.end(JSON.stringify({ error: 'Not found' }));
        
    } catch (error) {
        log('ERROR', `Server error: ${error.message}`);
        
        res.writeHead(500);
        res.end(JSON.stringify({ error: 'Internal server error' }));
    }
});

// Start server
server.listen(CONFIG.port, '0.0.0.0', () => {
    log('INFO', `GitHub MCP Server listening on port ${CONFIG.port}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    log('INFO', 'Received SIGTERM, shutting down GitHub MCP Server');
    server.close(() => {
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    log('INFO', 'Received SIGINT, shutting down GitHub MCP Server');
    server.close(() => {
        process.exit(0);
    });
});