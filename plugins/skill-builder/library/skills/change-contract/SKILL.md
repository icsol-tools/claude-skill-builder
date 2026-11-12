---
name: {{PREFIX}}-change-contract
description: Safely change something shared between units of {{REPO_NAME}} - an API route or response used by a frontend, a queue/message payload, a routing code, a shared table or stored procedure. Finds every party, applies compatibility rules, and plans the deploy order. Use before editing any of those.
argument-hint: "<what changes>"
---

# Change a cross-unit contract

1. **Find every party**: `.ai/system/system-map.md`, `.ai/system/generated/contracts.md` (frontend → backend calls, payload classes,
   queues, shared SQL objects), each unit's `generated/` files, and a repo-wide search for the route / class / property / code / object.
   The generators are regex-based and can miss usages; the search is mandatory. Show the list and confirm it is complete.
2. **Compatibility rules**:
   | Change | Rule |
   |---|---|
   | Add a field to a request/response/payload | Allowed. Consumers must tolerate it missing (old clients, queued messages) |
   | Rename/remove a field, change a type or route | Only with every party in the same release - or add new, migrate, remove later |
   | Proc result set | Additive columns at the end only; positional readers break on reorder |
   | Shared table | Additive, nullable columns only, unless every user is updated |
   | Queue / topic name | Coordinated release; drain the old queue |
3. **Implement and document**: all parties in one PR where possible; update `.ai/system/system-map.md`; regenerate docs; write a
   **deploy order** in the PR (normally consumers/backends first, then producers/frontends).
