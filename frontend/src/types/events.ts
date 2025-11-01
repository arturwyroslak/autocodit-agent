export type SessionEventPayload =
  | { type: 'session:event'; phase: 'analyze' | 'plan' | 'execute' | 'evaluate' | 'finalize'; message: string; timestamp: string }
  | { type: 'session:filemodified'; path: string; added: string[]; removed: string[]; timestamp: string }
  | { type: 'task:progress'; iteration: number; total?: number; percent?: number; timestamp: string }
  | { type: 'task:completed'; status: 'success' | 'failed'; pr_number?: number; branch?: string; summary?: string; timestamp: string }
  | { type: 'tool:invoked'; name: string; args?: any; timestamp: string }
  | { type: 'tool:result'; name: string; ok: boolean; output?: string; error?: string; timestamp: string }
  | { type: 'test:result'; passed: number; failed: number; coverage?: number; timestamp: string }
  | { type: 'linter:result'; errors: number; warnings: number; timestamp: string }
  | { type: 'build:status'; status: 'success' | 'failed'; logs_url?: string; timestamp: string }
