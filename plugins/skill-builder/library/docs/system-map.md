# System map: {{REPO_NAME}}

How the units of this repo (and the systems around them) fit together. Generated facts: `generated/contracts.md`
(frontend → backend calls, payloads, queues, shared SQL) and `generated/index.md`. Update this file when a flow changes.

```mermaid
flowchart LR
{{MERMAID}}
```

## Contracts between units
| Contract | Parties | Rule |
|---|---|---|
{{CONTRACT_ROWS}}
