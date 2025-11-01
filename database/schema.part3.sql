-- AutoCodit Agent Database Schema (Part 3: mcp servers, indexes & triggers)

-- MCP Servers table
CREATE TABLE IF NOT EXISTS mcpservers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    server_type VARCHAR(50) NOT NULL, -- 'builtin', 'docker', 'http'
    configuration JSONB NOT NULL,
    tools JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES users(id),
    usage_count INTEGER DEFAULT 0,
    health_status VARCHAR(50) DEFAULT 'unknown',
    last_health_check TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_installations_github_id ON installations(github_installation_id);
CREATE INDEX IF NOT EXISTS idx_installations_account_login ON installations(account_login);
CREATE INDEX IF NOT EXISTS idx_repositories_github_id ON repositories(github_id);
CREATE INDEX IF NOT EXISTS idx_repositories_full_name ON repositories(full_name);
CREATE INDEX IF NOT EXISTS idx_repositories_installation_id ON repositories(installation_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_repository_id ON tasks(repository_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_task_id ON sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_agentconfigs_user_id ON agentconfigs(user_id);
CREATE INDEX IF NOT EXISTS idx_agentconfigs_is_public ON agentconfigs(is_public);
CREATE INDEX IF NOT EXISTS idx_mcpservers_user_id ON mcpservers(user_id);
CREATE INDEX IF NOT EXISTS idx_mcpservers_is_public ON mcpservers(is_public);

-- Full-text search
CREATE INDEX IF NOT EXISTS idx_tasks_title_search ON tasks USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_tasks_description_search ON tasks USING gin(to_tsvector('english', description));

-- Triggers
CREATE TRIGGER set_timestamp_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_installations BEFORE UPDATE ON installations FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_agentconfigs BEFORE UPDATE ON agentconfigs FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_repositories BEFORE UPDATE ON repositories FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_tasks BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_sessions BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
CREATE TRIGGER set_timestamp_mcpservers BEFORE UPDATE ON mcpservers FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();
