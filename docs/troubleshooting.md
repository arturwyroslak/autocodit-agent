# Troubleshooting

## Common Issues
- Webhook signature mismatch: verify GITHUB_WEBHOOK_SECRET and GitHub App settings
- 401 on API/WS: ensure tokens/headers and CORS allowed origins
- DB migrations failing: check DB_USER/DB_NAME and run scripts/migrate.sh
- Ingress 404: verify host in values.yaml and DNS/Ingress controller

## Diagnostics
- docker compose logs -f (dev)
- kubectl logs -l app=autocodit-agent-api -f (k8s)
- /health endpoints and Prometheus metrics

