# Installation

## Prerequisites
- Docker & Docker Compose
- Kubernetes cluster (for Helm deployment)
- cert-manager (for TLS) & NGINX Ingress Controller
- GitHub App (App ID, Private Key, Webhook Secret)

## Local (Docker Compose)
```bash
git clone https://github.com/arturwyroslak/autocodit-agent.git
cd autocodit-agent
cp .env.example .env
# Edit .env with GitHub App credentials

docker compose up -d
npm run db:migrate
```

## Production (Helm)
1. Prepare values file (values.production.yaml)
```yaml
host: "agent.example.com"
env:
  GITHUB_APP_ID: "12345"
  GITHUB_PRIVATE_KEY: |-
    -----BEGIN PRIVATE KEY-----
    ...
    -----END PRIVATE KEY-----
  GITHUB_WEBHOOK_SECRET: "..."
  OPENAI_API_KEY: "..."
  ANTHROPIC_API_KEY: "..."
```

2. Install chart
```bash
helm install autocodit charts/autocodit-agent -f values.production.yaml
```

3. Verify
- https://agent.example.com → Frontend
- https://agent.example.com/api/health → API health

