/**
 * AutoCodit Agent Runner - Main Agent Process
 * 
 * Core agent logic that orchestrates task execution using MCP servers and AI models
 */

const { EventEmitter } = require('events');
const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');

// Configuration from environment
const config = {
    taskId: process.env.TASK_ID,
    sessionId: process.env.SESSION_ID,
    repositoryUrl: process.env.REPOSITORY_URL,
    taskDescription: process.env.TASK_DESCRIPTION,
    actionType: process.env.ACTION_TYPE || 'plan',
    agentConfig: JSON.parse(process.env.AGENT_CONFIG || '{}'),
    apiEndpoint: process.env.API_ENDPOINT,
    githubInstallationId: process.env.GITHUB_INSTALLATION_ID,
    logLevel: process.env.LOG_LEVEL || 'INFO'
};

// Logging function
function log(level, message, data = {}) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        level,
        component: 'agent-main',
        message,
        task_id: config.taskId,
        session_id: config.sessionId,
        ...data
    };
    
    console.log(JSON.stringify(logEntry));
}

// Agent class
class CodingAgent extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.mcpClients = new Map();
        this.currentStep = 0;
        this.totalSteps = 0;
        this.executionPlan = [];
        this.artifacts = [];
    }
    
    async initialize() {
        log('INFO', 'Initializing Coding Agent');
        
        // Connect to MCP servers
        await this.connectMCPServers();
        
        // Load project information
        this.projectInfo = await this.loadProjectInfo();
        
        // Generate execution plan
        this.executionPlan = await this.generateExecutionPlan();
        this.totalSteps = this.executionPlan.length;
        
        log('INFO', 'Agent initialization complete', {
            project_type: this.projectInfo.type,
            total_steps: this.totalSteps,
            mcp_servers: Array.from(this.mcpClients.keys())
        });
    }
    
    async connectMCPServers() {
        log('INFO', 'Connecting to MCP servers');
        
        // GitHub MCP Server
        try {
            this.mcpClients.set('github', await this.createMCPClient('github', {
                port: 2301,
                capabilities: ['list_files', 'read_file', 'write_file', 'create_branch', 'commit']
            }));
            log('INFO', 'GitHub MCP server connected');
        } catch (error) {
            log('ERROR', 'Failed to connect to GitHub MCP server', { error: error.message });
        }
        
        // Playwright MCP Server (if web project)
        if (this.projectInfo?.type === 'web' || this.projectInfo?.type === 'frontend') {
            try {
                this.mcpClients.set('playwright', await this.createMCPClient('playwright', {
                    port: 2302,
                    capabilities: ['screenshot', 'validate_ui', 'run_tests']
                }));
                log('INFO', 'Playwright MCP server connected');
            } catch (error) {
                log('WARN', 'Failed to connect to Playwright MCP server', { error: error.message });
            }
        }
    }
    
    async createMCPClient(serverName, serverConfig) {
        // Simplified MCP client implementation
        // In production, this would be a full MCP client with JSON-RPC 2.0
        return {
            name: serverName,
            config: serverConfig,
            connected: true,
            
            async call(method, params) {
                log('DEBUG', `MCP call: ${serverName}.${method}`, { params });
                
                // Simulate MCP call
                await new Promise(resolve => setTimeout(resolve, 100));
                
                return {
                    success: true,
                    result: `Mock result for ${method}`,
                    method,
                    params
                };
            }
        };
    }
    
    async loadProjectInfo() {
        try {
            const projectInfoPath = '/workspace/project-info.json';
            const data = await fs.readFile(projectInfoPath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            log('WARN', 'Failed to load project info', { error: error.message });
            return { type: 'unknown', languages: [], frameworks: [] };
        }
    }
    
    async generateExecutionPlan() {
        log('INFO', 'Generating execution plan');
        
        const steps = [];
        
        // Always start with repository analysis
        steps.push({
            name: 'Analyze Repository',
            type: 'analysis',
            tool: 'github',
            method: 'analyze_repository',
            estimated_duration: 30
        });
        
        // Action-specific steps
        switch (this.config.actionType) {
            case 'plan':
                steps.push(
                    {
                        name: 'Generate Implementation Plan',
                        type: 'ai_request',
                        tool: 'ai',
                        method: 'generate_plan',
                        estimated_duration: 60
                    },
                    {
                        name: 'Validate Plan',
                        type: 'validation',
                        tool: 'github',
                        method: 'validate_plan',
                        estimated_duration: 15
                    }
                );
                break;
                
            case 'fix':
            case 'apply':
                steps.push(
                    {
                        name: 'Identify Issues',
                        type: 'analysis',
                        tool: 'ai',
                        method: 'analyze_issues',
                        estimated_duration: 45
                    },
                    {
                        name: 'Generate Solution',
                        type: 'ai_request',
                        tool: 'ai',
                        method: 'generate_fix',
                        estimated_duration: 90
                    },
                    {
                        name: 'Apply Changes',
                        type: 'file_operation',
                        tool: 'github',
                        method: 'write_files',
                        estimated_duration: 30
                    },
                    {
                        name: 'Run Tests',
                        type: 'validation',
                        tool: 'test_runner',
                        method: 'run_tests',
                        estimated_duration: 120
                    },
                    {
                        name: 'Create Pull Request',
                        type: 'git_operation',
                        tool: 'github',
                        method: 'create_pr',
                        estimated_duration: 20
                    }
                );
                break;
                
            case 'review':
                steps.push(
                    {
                        name: 'Analyze Code Changes',
                        type: 'analysis',
                        tool: 'ai',
                        method: 'analyze_diff',
                        estimated_duration: 60
                    },
                    {
                        name: 'Security Review',
                        type: 'analysis',
                        tool: 'security_scanner',
                        method: 'scan_changes',
                        estimated_duration: 45
                    },
                    {
                        name: 'Generate Review',
                        type: 'ai_request',
                        tool: 'ai',
                        method: 'generate_review',
                        estimated_duration: 30
                    },
                    {
                        name: 'Post Review Comments',
                        type: 'git_operation',
                        tool: 'github',
                        method: 'create_review',
                        estimated_duration: 15
                    }
                );
                break;
                
            case 'test':
                steps.push(
                    {
                        name: 'Analyze Test Requirements',
                        type: 'analysis',
                        tool: 'ai',
                        method: 'analyze_test_needs',
                        estimated_duration: 30
                    },
                    {
                        name: 'Generate Tests',
                        type: 'ai_request',
                        tool: 'ai',
                        method: 'generate_tests',
                        estimated_duration: 90
                    },
                    {
                        name: 'Write Test Files',
                        type: 'file_operation',
                        tool: 'github',
                        method: 'write_files',
                        estimated_duration: 20
                    },
                    {
                        name: 'Run Test Suite',
                        type: 'validation',
                        tool: 'test_runner',
                        method: 'run_all_tests',
                        estimated_duration: 120
                    }
                );
                break;
        }
        
        log('INFO', 'Execution plan generated', {
            total_steps: steps.length,
            estimated_total_duration: steps.reduce((sum, step) => sum + step.estimated_duration, 0)
        });
        
        return steps;
    }
    
    async execute() {
        log('INFO', 'Starting task execution');
        
        try {
            for (let i = 0; i < this.executionPlan.length; i++) {
                const step = this.executionPlan[i];
                this.currentStep = i + 1;
                
                log('INFO', `Executing step ${this.currentStep}/${this.totalSteps}: ${step.name}`);
                
                const stepResult = await this.executeStep(step);
                
                if (!stepResult.success) {
                    log('ERROR', `Step failed: ${step.name}`, { error: stepResult.error });
                    
                    // Attempt recovery or fail
                    if (step.type === 'validation' && this.config.actionType === 'apply') {
                        // For apply actions, try to fix validation failures
                        const fixResult = await this.attemptStepFix(step, stepResult);
                        if (!fixResult.success) {
                            throw new Error(`Step '${step.name}' failed and could not be recovered`);
                        }
                    } else {
                        throw new Error(`Step '${step.name}' failed: ${stepResult.error}`);
                    }
                }
                
                // Report progress
                const progress = (this.currentStep) / this.totalSteps;
                await this.reportProgress(progress, `Completed: ${step.name}`);
            }
            
            log('INFO', 'Task execution completed successfully');
            await this.reportProgress(1.0, 'Task completed');
            
            return {
                success: true,
                artifacts: this.artifacts,
                summary: await this.generateSummary()
            };
        
        } catch (error) {
            log('ERROR', 'Task execution failed', { error: error.message });
            
            return {
                success: false,
                error: error.message,
                progress: this.currentStep / this.totalSteps,
                artifacts: this.artifacts
            };
        }
    }
    
    async executeStep(step) {
        const startTime = Date.now();
        
        try {
            let result;
            
            switch (step.type) {
                case 'analysis':
                    result = await this.executeAnalysisStep(step);
                    break;
                case 'ai_request':
                    result = await this.executeAIStep(step);
                    break;
                case 'file_operation':
                    result = await this.executeFileStep(step);
                    break;
                case 'git_operation':
                    result = await this.executeGitStep(step);
                    break;
                case 'validation':
                    result = await this.executeValidationStep(step);
                    break;
                default:
                    throw new Error(`Unknown step type: ${step.type}`);
            }
            
            const duration = Date.now() - startTime;
            
            log('INFO', `Step completed: ${step.name}`, {
                duration_ms: duration,
                step_type: step.type
            });
            
            return { success: true, result, duration };
        
        } catch (error) {
            const duration = Date.now() - startTime;
            
            log('ERROR', `Step failed: ${step.name}`, {
                error: error.message,
                duration_ms: duration,
                step_type: step.type
            });
            
            return { success: false, error: error.message, duration };
        }
    }
    
    async executeAnalysisStep(step) {
        // Use GitHub MCP to analyze repository
        const githubMCP = this.mcpClients.get('github');
        if (!githubMCP) {
            throw new Error('GitHub MCP server not available');
        }
        
        const result = await githubMCP.call(step.method, {
            repository: this.config.repositoryUrl,
            description: this.config.taskDescription
        });
        
        return result;
    }
    
    async executeAIStep(step) {
        // Make AI request to API backend
        const fetch = require('node-fetch');
        
        const response = await fetch(`${this.config.apiEndpoint}/api/v1/ai/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.API_TOKEN || 'mock-token'}`
            },
            body: JSON.stringify({
                messages: [
                    {
                        role: 'system',
                        content: this.generateSystemPrompt()
                    },
                    {
                        role: 'user',
                        content: `${step.method}: ${this.config.taskDescription}`
                    }
                ],
                model: this.config.agentConfig.primary_model || 'gpt-4-turbo',
                max_tokens: this.config.agentConfig.max_tokens || 4000,
                temperature: this.config.agentConfig.temperature || 0.1
            })
        });
        
        if (!response.ok) {
            throw new Error(`AI request failed: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        log('INFO', 'AI request completed', {
            tokens_used: result.usage?.total_tokens || 0,
            model: result.model,
            provider: result.provider
        });
        
        return result;
    }
    
    async executeFileStep(step) {
        const githubMCP = this.mcpClients.get('github');
        if (!githubMCP) {
            throw new Error('GitHub MCP server not available');
        }
        
        return await githubMCP.call(step.method, step.params || {});
    }
    
    async executeGitStep(step) {
        const githubMCP = this.mcpClients.get('github');
        if (!githubMCP) {
            throw new Error('GitHub MCP server not available');
        }
        
        return await githubMCP.call(step.method, {
            installation_id: this.config.githubInstallationId,
            repository: this.extractRepoFromUrl(this.config.repositoryUrl),
            ...step.params
        });
    }
    
    async executeValidationStep(step) {
        // Run tests or validation
        if (step.method === 'run_tests') {
            return await this.runTests();
        }
        
        if (step.method === 'validate_ui' && this.mcpClients.has('playwright')) {
            const playwrightMCP = this.mcpClients.get('playwright');
            return await playwrightMCP.call('validate_ui', step.params || {});
        }
        
        return { success: true, message: 'Validation skipped' };
    }
    
    async runTests() {
        log('INFO', 'Running test suite');
        
        const testCommands = this.getTestCommands();
        
        for (const command of testCommands) {
            try {
                const result = await this.executeCommand(command);
                
                if (result.exitCode !== 0) {
                    log('WARN', `Test command failed: ${command}`, {
                        exit_code: result.exitCode,
                        stderr: result.stderr
                    });
                    
                    return {
                        success: false,
                        error: `Tests failed with exit code ${result.exitCode}`,
                        output: result.stderr
                    };
                }
                
                log('INFO', `Test command succeeded: ${command}`);
                
            } catch (error) {
                return {
                    success: false,
                    error: `Test execution failed: ${error.message}`
                };
            }
        }
        
        return { success: true, message: 'All tests passed' };
    }
    
    getTestCommands() {
        const commands = [];
        
        // JavaScript/TypeScript
        if (this.projectInfo.languages.includes('javascript') || this.projectInfo.languages.includes('typescript')) {
            if (this.projectInfo.testFrameworks.includes('jest')) {
                commands.push('npm test');
            } else if (this.projectInfo.testFrameworks.includes('vitest')) {
                commands.push('npm run test');
            }
        }
        
        // Python
        if (this.projectInfo.languages.includes('python')) {
            if (this.projectInfo.testFrameworks.includes('pytest')) {
                commands.push('python3 -m pytest');
            } else {
                commands.push('python3 -m unittest discover');
            }
        }
        
        // Go
        if (this.projectInfo.languages.includes('go')) {
            commands.push('go test ./...');
        }
        
        // Java
        if (this.projectInfo.languages.includes('java')) {
            if (this.projectInfo.buildSystems.includes('maven')) {
                commands.push('mvn test');
            } else if (this.projectInfo.buildSystems.includes('gradle')) {
                commands.push('./gradlew test');
            }
        }
        
        return commands;
    }
    
    async executeCommand(command) {
        return new Promise((resolve, reject) => {
            const process = spawn('sh', ['-c', command], {
                cwd: '/workspace/repo',
                env: { ...process.env, NODE_ENV: 'test' }
            });
            
            let stdout = '';
            let stderr = '';
            
            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            process.on('close', (code) => {
                resolve({
                    exitCode: code,
                    stdout,
                    stderr
                });
            });
            
            process.on('error', (error) => {
                reject(error);
            });
            
            // Timeout after 10 minutes
            setTimeout(() => {
                process.kill('SIGKILL');
                reject(new Error('Command timeout'));
            }, 10 * 60 * 1000);
        });
    }
    
    generateSystemPrompt() {
        const basePrompt = `You are AutoCodit Agent, an autonomous coding assistant.
        
Task: ${this.config.taskDescription}
Action Type: ${this.config.actionType}
Repository: ${this.config.repositoryUrl}
Project Type: ${this.projectInfo.type}
Languages: ${this.projectInfo.languages.join(', ')}
Frameworks: ${this.projectInfo.frameworks.join(', ')}

You have access to the following tools through MCP servers:
${Array.from(this.mcpClients.keys()).map(name => `- ${name}`).join('\n')}

Always:
1. Analyze before making changes
2. Run tests after modifications
3. Follow project conventions
4. Write clear commit messages
5. Create descriptive pull requests

Be thorough, methodical, and always validate your changes.`;
        
        // Add custom prompt if provided
        const customPrompt = this.config.agentConfig.system_prompt;
        if (customPrompt) {
            return basePrompt + '\n\nAdditional Instructions:\n' + customPrompt;
        }
        
        return basePrompt;
    }
    
    async reportProgress(progress, message) {
        log('INFO', 'Progress update', {
            progress,
            message,
            step: this.currentStep,
            total_steps: this.totalSteps
        });
        
        // TODO: Send progress update to API backend
        try {
            const fetch = require('node-fetch');
            
            await fetch(`${this.config.apiEndpoint}/api/v1/sessions/${this.config.sessionId}/progress`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${process.env.API_TOKEN || 'mock-token'}`
                },
                body: JSON.stringify({
                    progress,
                    message,
                    step: this.currentStep,
                    total_steps: this.totalSteps
                })
            });
        } catch (error) {
            log('WARN', 'Failed to report progress', { error: error.message });
        }
    }
    
    async generateSummary() {
        return {
            task_id: this.config.taskId,
            action_type: this.config.actionType,
            steps_completed: this.currentStep,
            total_steps: this.totalSteps,
            project_type: this.projectInfo.type,
            languages: this.projectInfo.languages,
            artifacts_generated: this.artifacts.length,
            execution_time: Date.now() - this.startTime
        };
    }
    
    extractRepoFromUrl(url) {
        // Extract owner/repo from GitHub URL
        const match = url.match(/github\.com[:/]([^/]+)\/([^/.]+)/);
        if (match) {
            return `${match[1]}/${match[2]}`;
        }
        throw new Error(`Invalid repository URL: ${url}`);
    }
    
    async attemptStepFix(failedStep, stepResult) {
        log('INFO', `Attempting to fix failed step: ${failedStep.name}`);
        
        // TODO: Implement intelligent step recovery
        // This would use AI to analyze the failure and attempt fixes
        
        return { success: false, error: 'Step recovery not implemented' };
    }
}

// Main execution
async function main() {
    log('INFO', 'AutoCodit Agent starting', config);
    
    const agent = new CodingAgent(config);
    
    try {
        await agent.initialize();
        const result = await agent.execute();
        
        log('INFO', 'Agent execution completed', { success: result.success });
        
        // Exit with appropriate code
        process.exit(result.success ? 0 : 1);
        
    } catch (error) {
        log('ERROR', 'Agent execution failed', { error: error.message });
        process.exit(1);
    }
}

// Handle uncaught exceptions
process.on('unhandledRejection', (reason, promise) => {
    log('ERROR', 'Unhandled Promise Rejection', { reason: reason.toString() });
    process.exit(1);
});

process.on('uncaughtException', (error) => {
    log('ERROR', 'Uncaught Exception', { error: error.message });
    process.exit(1);
});

// Start the agent
main();