# AIOS Runtime Architecture

## Core services

- Input adapters: text now; voice and vision later
- AI Kernel: intent + planning + policy
- Task Manager: persistent task lifecycle
- Environment Engine: safe dynamic workspace schemas
- Tool/Agent layer: deterministic execution
- Memory: durable user/task context
- Event Engine: extract and store events
- Scheduler: reminder execution
- Action Ledger: audit trail
- Rollback: task-state snapshots

## Dynamic environment contract

An LLM should produce structured environment data, not arbitrary executable UI code.

Example:

```json
{
  "environment":"email",
  "components":[
    {"type":"contact_picker"},
    {"type":"email_editor"},
    {"type":"send_button","requiresConfirmation":true}
  ]
}
```

The renderer owns the actual React components.

## External action contract

```text
plan -> policy -> confirmation -> connector -> verification -> ledger -> memory
```

Never let the model bypass the policy layer.
