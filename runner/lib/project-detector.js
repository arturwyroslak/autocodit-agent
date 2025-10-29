/**
 * AutoCodit Agent Runner - Project Type Detection
 * 
 * Analyzes repository structure to determine project type and setup requirements
 */

const fs = require('fs').promises;
const path = require('path');

async function detectProjectType() {
    const cwd = process.cwd();
    
    try {
        const files = await fs.readdir(cwd);
        const fileSet = new Set(files);
        
        const projectInfo = {
            type: 'unknown',
            languages: [],
            frameworks: [],
            buildSystems: [],
            testFrameworks: [],
            databases: [],
            deployment: [],
            confidence: 0,
            recommendations: []
        };
        
        // JavaScript/TypeScript detection
        if (fileSet.has('package.json')) {
            const packageJson = JSON.parse(
                await fs.readFile(path.join(cwd, 'package.json'), 'utf8')
            );
            
            projectInfo.languages.push('javascript');
            projectInfo.buildSystems.push('npm');
            
            // TypeScript detection
            if (fileSet.has('tsconfig.json') || packageJson.devDependencies?.typescript) {
                projectInfo.languages.push('typescript');
            }
            
            // Framework detection
            const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
            
            if (deps.react) projectInfo.frameworks.push('react');
            if (deps.vue) projectInfo.frameworks.push('vue');
            if (deps.angular || deps['@angular/core']) projectInfo.frameworks.push('angular');
            if (deps.next) projectInfo.frameworks.push('nextjs');
            if (deps.express) projectInfo.frameworks.push('express');
            if (deps.fastify) projectInfo.frameworks.push('fastify');
            if (deps.nest || deps['@nestjs/core']) projectInfo.frameworks.push('nestjs');
            
            // Test framework detection
            if (deps.jest) projectInfo.testFrameworks.push('jest');
            if (deps.mocha) projectInfo.testFrameworks.push('mocha');
            if (deps.vitest) projectInfo.testFrameworks.push('vitest');
            if (deps.cypress) projectInfo.testFrameworks.push('cypress');
            if (deps.playwright) projectInfo.testFrameworks.push('playwright');
            
            // Database detection
            if (deps.mongoose) projectInfo.databases.push('mongodb');
            if (deps.pg || deps.postgres) projectInfo.databases.push('postgresql');
            if (deps.mysql || deps.mysql2) projectInfo.databases.push('mysql');
            if (deps.sqlite3) projectInfo.databases.push('sqlite');
            if (deps.redis) projectInfo.databases.push('redis');
            
            // Deployment detection
            if (fileSet.has('Dockerfile')) projectInfo.deployment.push('docker');
            if (fileSet.has('docker-compose.yml')) projectInfo.deployment.push('docker-compose');
            if (fileSet.has('vercel.json')) projectInfo.deployment.push('vercel');
            if (fileSet.has('netlify.toml')) projectInfo.deployment.push('netlify');
            
            // Determine project type
            if (projectInfo.frameworks.includes('nextjs') || projectInfo.frameworks.includes('react')) {
                projectInfo.type = 'frontend';
            } else if (projectInfo.frameworks.includes('express') || projectInfo.frameworks.includes('fastify')) {
                projectInfo.type = 'backend';
            } else {
                projectInfo.type = 'web';
            }
            
            projectInfo.confidence = 0.9;
        }
        
        // Python detection
        if (fileSet.has('requirements.txt') || fileSet.has('pyproject.toml') || fileSet.has('setup.py')) {
            projectInfo.languages.push('python');
            
            if (fileSet.has('requirements.txt')) {
                const requirements = await fs.readFile(path.join(cwd, 'requirements.txt'), 'utf8');
                
                // Framework detection
                if (requirements.includes('django')) projectInfo.frameworks.push('django');
                if (requirements.includes('flask')) projectInfo.frameworks.push('flask');
                if (requirements.includes('fastapi')) projectInfo.frameworks.push('fastapi');
                if (requirements.includes('starlette')) projectInfo.frameworks.push('starlette');
                
                // Test framework detection
                if (requirements.includes('pytest')) projectInfo.testFrameworks.push('pytest');
                if (requirements.includes('unittest2')) projectInfo.testFrameworks.push('unittest');
                
                // Database detection
                if (requirements.includes('psycopg2') || requirements.includes('asyncpg')) {
                    projectInfo.databases.push('postgresql');
                }
                if (requirements.includes('pymongo')) projectInfo.databases.push('mongodb');
                if (requirements.includes('redis')) projectInfo.databases.push('redis');
            }
            
            if (projectInfo.frameworks.length > 0) {
                projectInfo.type = 'backend';
            } else {
                projectInfo.type = 'python';
            }
            
            projectInfo.buildSystems.push('pip');
            projectInfo.confidence = Math.max(projectInfo.confidence, 0.8);
        }
        
        // Go detection
        if (fileSet.has('go.mod')) {
            projectInfo.languages.push('go');
            projectInfo.buildSystems.push('go-modules');
            projectInfo.type = 'backend';
            projectInfo.confidence = Math.max(projectInfo.confidence, 0.8);
        }
        
        // Java detection
        if (fileSet.has('pom.xml')) {
            projectInfo.languages.push('java');
            projectInfo.buildSystems.push('maven');
            projectInfo.type = 'backend';
            projectInfo.confidence = Math.max(projectInfo.confidence, 0.8);
        }
        
        if (fileSet.has('build.gradle') || fileSet.has('build.gradle.kts')) {
            projectInfo.languages.push('java');
            projectInfo.buildSystems.push('gradle');
            projectInfo.type = 'backend';
            projectInfo.confidence = Math.max(projectInfo.confidence, 0.8);
        }
        
        // Rust detection
        if (fileSet.has('Cargo.toml')) {
            projectInfo.languages.push('rust');
            projectInfo.buildSystems.push('cargo');
            projectInfo.type = 'backend';
            projectInfo.confidence = Math.max(projectInfo.confidence, 0.8);
        }
        
        // Generate recommendations
        projectInfo.recommendations = generateRecommendations(projectInfo);
        
        return projectInfo;
    
    } catch (error) {
        return {
            type: 'unknown',
            error: error.message,
            confidence: 0
        };
    }
}

function generateRecommendations(projectInfo) {
    const recommendations = [];
    
    // MCP server recommendations
    if (projectInfo.frameworks.includes('react') || projectInfo.frameworks.includes('vue')) {
        recommendations.push('Enable Playwright MCP for UI testing');
    }
    
    if (projectInfo.databases.length > 0) {
        recommendations.push('Enable Database MCP for schema operations');
    }
    
    if (projectInfo.deployment.includes('docker')) {
        recommendations.push('Enable Docker MCP for container operations');
    }
    
    // Security recommendations
    if (projectInfo.type === 'backend') {
        recommendations.push('Enable strict firewall mode for backend projects');
    }
    
    if (projectInfo.languages.includes('javascript') && !projectInfo.languages.includes('typescript')) {
        recommendations.push('Consider TypeScript for better type safety');
    }
    
    // Testing recommendations
    if (projectInfo.testFrameworks.length === 0) {
        recommendations.push('Add automated testing framework');
    }
    
    return recommendations;
}

// Run detection and output JSON
detectProjectType().then(result => {
    console.log(JSON.stringify(result, null, 2));
}).catch(error => {
    console.error(JSON.stringify({ error: error.message }, null, 2));
    process.exit(1);
});