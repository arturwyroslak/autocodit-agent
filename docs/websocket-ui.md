# WebSocket Protocol & UI

## Event Types
- session:event { phase: analyze|plan|execute|evaluate|finalize, message, timestamp }
- session:filemodified { path, added[], removed[], timestamp }
- task:progress { iteration, total?, percent?, timestamp }
- task:completed { status: success|failed, pr_number?, branch?, summary?, timestamp }
- tool:invoked { name, args?, timestamp }
- tool:result { name, ok, output?, error?, timestamp }
- test:result { passed, failed, coverage?, timestamp }
- linter:result { errors, warnings, timestamp }
- build:status { status: success|failed, logs_url?, timestamp }

## Frontend Integration
- websocketStore.ts (Zustand) for connections & subscriptions
- useWebSocket hook invalidates queries on events
- LiveSessionView: timeline + metrics + code diff
- TaskReview: status, PR, summary, tests & coverage

