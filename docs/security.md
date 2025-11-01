# Security & Compliance

## Principles
- Least privilege (GitHub App & infra RBAC)
- Secret management via K8s Secrets
- Network egress allowlists for tools
- Audit logging of actions, commits, approvals

## Compliance
- GDPR-ready data handling (logs retention policy)
- SOC 2 Type II ready architecture (segregation, monitoring)

## Hardening Checklist
- Enforce TLS (Ingress)
- Rotate secrets regularly
- Read-only containers where possible
- Enable resource limits for all workloads

