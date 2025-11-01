# Configuration

## Environment Variables
- GITHUB_APP_ID: GitHub App ID
- GITHUB_PRIVATE_KEY: PEM private key of the GitHub App (multiline)
- GITHUB_WEBHOOK_SECRET: Webhook secret shared with GitHub
- OPENAI_API_KEY / ANTHROPIC_API_KEY: model providers
- DATABASE_URL: postgresql://user:pass@host:5432/db
- REDIS_URL: redis://host:6379/0

## Secrets & Config (Kubernetes)
- templates/secret.yaml: GITHUB_PRIVATE_KEY, GITHUB_WEBHOOK_SECRET, OPENAI/ANTHROPIC
- templates/configmap.yaml: DATABASE_URL, REDIS_URL

## GitHub App Setup
- Webhook URL: https://<host>/api/v1/github/webhook
- Permissions: Contents, Pull Requests, Issues (Read & Write)
- Subscribed events: issues, issue_comment, pull_request, push

