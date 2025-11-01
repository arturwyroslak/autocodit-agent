# Architecture

## System Overview

AutoCodit Agent is a self-hosted, GitHub App-driven coding agent platform built for enterprise-grade autonomy.

### Core Components
- API (FastAPI): REST endpoints, Webhook handler, WS server, health/metrics
- Runner Manager: orchestrates container-based execution
- Celery Workers & Beat: background processing and scheduling
- Frontend (Next.js 14, shadcn/ui): dashboard, live sessions, review
- CLI (Go): task creation, monitoring, repo operations
- PostgreSQL & Redis: state and queue/cache backend
- Monitoring: Prometheus & Grafana dashboards

### Execution Flow
1. GitHub event or Copilot-like job triggers Task creation
2. Orchestrator builds plan (analyze → plan → execute → evaluate → finalize)
3. Runner executes tools in isolated containers; commits changes; opens PR
4. WebSocket emits timeline events; UI shows progress/diffs/results
5. Monitoring collects metrics; audit trail records actions

## Security Model
- GitHub App scoped permissions & installation tokens
- Container isolation (rootless, read-only FS), network egress allowlist
- Secrets stored as K8s Secrets; RBAC per environment
- Audit logging (actions, commits, approvals)

## Data Model (high-level)
- users, installations, agentconfigs, repositories, tasks, sessions, mcpservers

