---
name: co-add-message-handler
description: Add a handler for a new order event type to Contoso.Orders.Worker - handler class, router entry, partner call, idempotent write-back, registration and tests. Use when a new EventType must be processed or forwarded to a partner.
---

# Add a message handler (Contoso.Orders.Worker)

Read first: `.ai/archetypes/dotnet-queue-worker.md`, `services/Contoso.Orders.Worker/.ai/overview.md` and `gotchas.md`.

## Steps
1. Ask for: the `EventType` value, the partner(s) to call, and what counts as success. Check `Routing/MessageRouter.cs` that the
   type is not already routed.
2. Copy `Handlers/OrderShippedHandler.cs` to `Handlers/<EventType>Handler.cs`. Keep the idempotency check on
   `IntegrationLog.MessageId` at the top.
3. Map the message to the partner request in the handler. Missing client → run the add-integration-target recipe first.
4. Add `{ "<EventType>", typeof(<EventType>Handler) }` to `MessageRouter._handlers`.
5. Register the handler in `Program.cs` → `AddHandlers()`.
6. Write-back: call `IntegrationLogRepository.Complete(messageId, partnerRef)`; on failure throw `RetryableException` or
   `PermanentException` (see Rules).
7. Tests: copy `OrderShippedHandlerTests.cs`; cover success, duplicate message, partner 5xx (retry) and 4xx (permanent).
8. Run `dotnet test services/Contoso.Orders.Worker.sln`, then `/co-verify`.
9. Add the event to the Contracts table in `.ai/system/system-map.md`.

## Checklist
- [ ] Router entry and DI registration both added (either one alone fails silently or at runtime)
- [ ] Handler is idempotent and never acks before write-back
- [ ] New settings keys added to `appsettings.json` with empty values; real values only in the environment
- [ ] Four tests pass; system map updated
