-- AutoCodit Agent Database Schema (Part 1: core tables)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    avatar_url VARCHAR(500),
    access_token VARCHAR(500),
    refresh_token VARCHAR(500),
    token_expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}',
    total_tasks INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Installations table (GitHub App installations)
CREATE TABLE IF NOT EXISTS installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_installation_id INTEGER UNIQUE NOT NULL,
    account_id INTEGER NOT NULL,
    account_login VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    repository_selection VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    suspended_by VARCHAR(255),
    suspended_at TIMESTAMP WITH TIME ZONE,
    permissions JSONB DEFAULT '{}',
    events JSONB DEFAULT '[]',
    access_token VARCHAR(500),
    token_expires_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}',
    webhook_secret VARCHAR(255),
    user_id UUID REFERENCES users(id),
    total_repositories INTEGER DEFAULT 0,
    total_tasks INTEGER DEFAULT 0,
    monthly_task_limit INTEGER,
    plan VARCHAR(50) DEFAULT 'free',
    billing_cycle VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Configurations table
CREATE TABLE IF NOT EXISTS agentconfigs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    model_config JSONB DEFAULT '{}',
    tools JSONB DEFAULT '[]',
    mcp_servers JSONB DEFAULT '[]',
    firewall_rules JSONB DEFAULT '{}',
    resource_limits JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES users(id),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
