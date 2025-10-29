# AutoCodit Agent

🤖 **Self-hosted GitHub Copilot Coding Agent clone** - Complete autonomous AI coding system with GitHub App bot integration, lightweight container runners, and mission control dashboard.

## 🎯 Overview

AutoCodit Agent is a production-ready alternative to GitHub Copilot Coding Agent that gives you full control over your AI-powered development workflow. It operates as a GitHub App bot that can be triggered through GitHub issues, comments, and PR events, while running on your own infrastructure.

### Key Features

- 🤖 **GitHub App Bot Integration** - Native GitHub experience with webhooks and bot account
- 🐳 **Lightweight Container Runners** - Your own isolated execution environment
- 🎛️ **Mission Control Dashboard** - Real-time monitoring and task management
- 📱 **Multi-platform Access** - Web dashboard, mobile app, and CLI tools
- 🔒 **Enterprise Security** - eBPF firewall, sandboxing, and audit trails
- 🧠 **Multi-LLM Support** - OpenAI, Anthropic, and local models with fallback
- 🔧 **MCP Integration** - Model Context Protocol for extensible tools
- ⚡ **Cost Efficient** - 60-80% cheaper than GitHub-hosted solutions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Web Dashboard │   Mobile Apps   │      CLI Tools          │
│                 │                 │                         │
│ • React/Next.js │ • React Native  │ • Go CLI                │
│ • Real-time UI  │ • Push Notifs   │ • Node.js CLI           │
│ • Monaco Editor │ • Voice Input   │ • Shell Integration     │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                     GITHUB APP BOT                         │
├─────────────────────────────────────────────────────────────┤
│ • Webhook Events          • Issue/PR Assignment            │
│ • Comment Commands        • Branch/Commit Management       │
│ • Installation Tokens     • Review/Check-run Integration   │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND SERVICES                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Core API      │  Agent Manager  │    Runner Engine        │
│                 │                 │                         │
│ • FastAPI/Gin   │ • Task Queue    │ • Docker Orchestration  │
│ • GraphQL       │ • Session Mgmt  │ • Container Isolation   │
│ • WebSocket     │ • AI Integration│ • Resource Management   │
│ • Auth/RBAC     │ • MCP Servers   │ • Security Enforcement  │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                EXECUTION ENVIRONMENT                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Container Pool  │   AI Models     │    Storage Layer        │
│                 │                 │                         │
│ • Docker/gVisor │ • OpenAI API    │ • PostgreSQL + Redis   │
│ • eBPF Firewall │ • Anthropic     │ • MinIO Object Store    │
│ • Auto-scaling  │ • Local LLMs    │ • Prometheus Metrics    │
│ • Multi-tenancy │ • Multi-provider│ • Grafana Dashboard     │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 🚀 Quick Start

### 1. GitHub App Setup

1. Create a new GitHub App in your organization settings
2. Configure webhook URL: `https://your-domain.com/api/v1/github/webhook`
3. Set permissions: Contents, Pull Requests, Issues (Read & Write)
4. Subscribe to events: issues, issue_comment, pull_request, push

### 2. Local Development

```bash
# Clone the repository
git clone https://github.com/arturwyroslak/autocodit-agent.git
cd autocodit-agent

# Copy environment template
cp .env.example .env
# Edit .env with your GitHub App credentials

# Start development environment
docker-compose up -d

# Initialize database
npm run db:migrate

# Start the services
npm run dev
```

### 3. Production Deployment

```bash
# Deploy to Kubernetes
helm install autocodit-agent ./charts/autocodit-agent \
  --set github.appId=YOUR_APP_ID \
  --set github.privateKey=YOUR_PRIVATE_KEY \
  --set github.webhookSecret=YOUR_WEBHOOK_SECRET

# Or use Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## 💻 Usage

### GitHub Interface

**Assign Issues to Agent:**
```
# Assign any issue to @autocodit-bot
# The bot will automatically start working on it
```

**Command Comments:**
```
# In any issue or PR comment:
@autocodit-bot plan: Refactor the authentication module to use JWT
@autocodit-bot apply: Fix the failing tests in /tests/auth
@autocodit-bot review: Check this PR for security issues
@autocodit-bot stop: Stop the current task
```

### Web Dashboard

Access the mission control at `https://your-domain.com/dashboard`

- 📊 **Task Overview** - All running and completed tasks
- 🔍 **Live Sessions** - Real-time progress monitoring
- ⚙️ **Agent Profiles** - Custom agent configurations
- 📈 **Analytics** - Performance and cost metrics
- 🔧 **Settings** - GitHub integrations and MCP servers

### CLI Tools

```bash
# Install CLI
npm install -g @autocodit/cli

# Create task
autocodit task create "Add unit tests for user service" --repo myorg/myrepo

# Monitor progress
autocodit task watch abc123

# List tasks
autocodit task list --status running
```

## 🔧 Configuration

### Agent Profiles

Create custom agent behaviors in `config/agents/`:

```yaml
# config/agents/frontend-specialist.yml
name: Frontend Specialist
description: Expert in React, TypeScript, and modern frontend practices
model:
  primary: gpt-4-turbo
  fallback: claude-3-sonnet
  temperature: 0.2
tools:
  - github-mcp
  - playwright-mcp
  - npm-mcp
system_prompt: |
  You are a frontend development expert. Focus on:
  - React best practices and TypeScript
  - Accessibility and performance
  - Modern CSS and responsive design
  - Unit testing with Jest/RTL
firewall:
  allowed_domains:
    - npmjs.org
    - unpkg.com
    - cdn.jsdelivr.net
resources:
  memory: 2Gi
  cpu: 1000m
  timeout: 3600s
```

### MCP Servers

Extend functionality with Model Context Protocol servers:

```json
{
  "mcpServers": {
    "github": {
      "type": "builtin",
      "tools": ["list_files", "read_file", "write_file", "create_branch"]
    },
    "playwright": {
      "type": "docker",
      "image": "autocodit/mcp-playwright:latest",
      "tools": ["screenshot", "validate_ui", "run_tests"]
    },
    "sentry": {
      "type": "http",
      "url": "https://sentry.io/api/mcp/",
      "auth": "Bearer ${SENTRY_TOKEN}",
      "tools": ["get_errors", "create_issue"]
    }
  }
}
```

## 📊 Monitoring & Analytics

### Metrics Dashboard

- **Task Success Rate** - Completion percentage over time
- **Resource Usage** - CPU, memory, and storage consumption
- **Cost Analysis** - Token usage and infrastructure costs
- **Performance** - Average task completion time
- **Security Events** - Firewall blocks and policy violations

### Audit Trail

Complete logging of:
- All bot actions and GitHub API calls
- Code changes and commit history
- User interactions and approvals
- Resource allocation and cleanup
- Security policy enforcement

## 🔒 Security

### Multi-layer Protection

1. **GitHub App Security** - Minimal permissions, installation tokens
2. **Container Isolation** - gVisor sandboxing, read-only filesystem
3. **Network Firewall** - eBPF packet filtering, domain allowlists
4. **Content Filtering** - Input sanitization, hidden character detection
5. **Resource Limits** - CPU, memory, and execution time constraints
6. **Audit Logging** - Complete activity tracking and compliance

### Compliance Features

- **SOC 2 Type II** ready architecture
- **GDPR** compliant data handling
- **Enterprise SSO** integration (SAML, OIDC)
- **Role-based Access Control** (RBAC)
- **Data encryption** at rest and in transit

## 💰 Cost Comparison

| Feature | GitHub Copilot Pro | AutoCodit Agent |
|---------|-------------------|------------------|
| Monthly Cost (10 users) | $200 + Actions | $50-100 |
| Infrastructure Control | ❌ | ✅ |
| Custom Models | ❌ | ✅ |
| Data Privacy | Limited | Full |
| Custom Tools | Limited | Unlimited |
| Enterprise Features | Extra cost | Included |

**Break-even point:** 15-20 users  
**Annual savings:** $15,000-30,000 for 50+ user teams

## 🛠️ Development

### Tech Stack

- **Backend:** FastAPI (Python) / Gin (Go)
- **Frontend:** Next.js 14, TailwindCSS, shadcn/ui
- **Mobile:** React Native with Expo
- **Database:** PostgreSQL, Redis, MinIO
- **AI:** OpenAI, Anthropic, Ollama integration
- **Infrastructure:** Docker, Kubernetes, Helm
- **Monitoring:** Prometheus, Grafana, Jaeger

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Project Structure

```
autocodit-agent/
├── backend/           # Core API and services
├── frontend/          # Web dashboard
├── mobile/            # React Native app
├── cli/               # Command-line tools
├── runner/            # Container execution engine
├── charts/            # Kubernetes Helm charts
├── docker/            # Docker configurations
├── docs/              # Documentation
├── scripts/           # Deployment and utility scripts
└── tests/             # Test suites
```

## 📚 Documentation

- [📖 Full Documentation](./docs/README.md)
- [🏗️ Architecture Guide](./docs/architecture.md)
- [⚙️ Installation Guide](./docs/installation.md)
- [🔧 Configuration Reference](./docs/configuration.md)
- [🛡️ Security Guide](./docs/security.md)
- [📊 Monitoring Setup](./docs/monitoring.md)
- [🔌 MCP Development](./docs/mcp-development.md)
- [🤖 Agent Profiles](./docs/agent-profiles.md)

## 🤝 Community

- [💬 Discord](https://discord.gg/autocodit) - Community chat
- [🐛 Issues](https://github.com/arturwyroslak/autocodit-agent/issues) - Bug reports and feature requests
- [💡 Discussions](https://github.com/arturwyroslak/autocodit-agent/discussions) - Ideas and questions
- [📧 Newsletter](https://autocodit.dev/newsletter) - Updates and tips

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- GitHub Copilot team for inspiration
- OpenAI and Anthropic for AI model APIs
- The open-source community for amazing tools and libraries

---

**Built with ❤️ by [Artur Wyroslak](https://github.com/arturwyroslak)**

*Transform your development workflow with autonomous AI agents that work the way you do.*