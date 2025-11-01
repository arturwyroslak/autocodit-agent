import { z } from "zod"

// Map of action types to our internal task action_type
export const CopilotAction = z.enum([
  "fix-issue",
  "fix-pr-comment",
  "code-review",
  "security-scan",
  "plan",
  "apply",
])

export type CopilotAction = z.infer<typeof CopilotAction>

export interface CopilotJobSpec {
  action: CopilotAction
  repository: string // owner/name
  issue_number?: number
  pr_number?: number
  description?: string
  timeout_minutes?: number
  priority?: "low" | "normal" | "high" | "urgent"
}

export function mapCopilotToTask(spec: CopilotJobSpec) {
  const actionMap: Record<CopilotAction, string> = {
    "fix-issue": "fix",
    "fix-pr-comment": "fix",
    "code-review": "review",
    "security-scan": "scan",
    "plan": "plan",
    "apply": "apply",
  }

  const title = spec.description?.slice(0, 80) || `${spec.action} task`
  const description = spec.description || `${spec.action} on ${spec.repository}`

  return {
    title,
    description,
    repository: spec.repository,
    action_type: actionMap[spec.action] || "plan",
    priority: spec.priority || "normal",
    issue_number: spec.issue_number,
    pull_request_number: spec.pr_number,
    timeout_minutes: spec.timeout_minutes || 59,
  }
}
