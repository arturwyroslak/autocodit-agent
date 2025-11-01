# Copilot-like Jobs API

Accept tasks using a Copilot-compatible job spec.

## Endpoint
POST /api/v1/copilot/jobs

### Request Body
```json
{
  "action": "fix-issue | fix-pr-comment | code-review | security-scan | plan | apply",
  "repository": "owner/name",
  "issue_number": 123,
  "pr_number": 45,
  "description": "optional description",
  "timeout_minutes": 59,
  "priority": "low|normal|high|urgent"
}
```

### Response
```json
{
  "status": "accepted",
  "task_id": "uuid"
}
```

### Mapping
The request is mapped to internal Task via `copilot_mapper.ts` and processed by TaskService.

