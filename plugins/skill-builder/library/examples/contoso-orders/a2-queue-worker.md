# Archetype: dotnet-queue-worker (Contoso.Orders.Worker)

## How it flows
`RabbitConsumerService` (BackgroundService) reads `orders.events` → deserialises `OrderEventMessage` → `MessageRouter.Route(eventType)`
picks an `IMessageHandler` by `EventType` → the handler calls partner APIs through typed `HttpClient`s → writes the result to
`Orders.dbo.IntegrationLog` → ack. Failures are nacked to `orders.events.retry` (3 tries, then `orders.events.dlq`).

| Part | Where | Example to copy |
|---|---|---|
| Message handlers | `Contoso.Orders.Worker/Handlers/` | `OrderShippedHandler.cs` |
| Router switch | `Routing/MessageRouter.cs` → `_handlers` dictionary | |
| Partner clients | `Clients/<Partner>Client.cs` + `Clients/I<Partner>Client.cs` | `CarrierClient.cs` |
| Settings | `appsettings.json` → `Partners:<Name>` (key names only) bound to `PartnerSettings` | |
| Registration | `Program.cs` → `AddHandlers()` and `AddPartnerClients()` | |
| Tests | `Contoso.Orders.Worker.Tests/Handlers/` | `OrderShippedHandlerTests.cs` |

## Rules for new code
- One handler per `EventType`; handlers are idempotent (check `IntegrationLog` by `MessageId` first).
- Never ack before the write-back succeeds. Throw `RetryableException` for timeouts/5xx, `PermanentException` for 4xx.
- HTTP clients via `IHttpClientFactory` with Polly retry from `AddPartnerClients()`; no `new HttpClient()`.

## Recipe: add-message-handler
See `recipe-skill-add-message-handler.md` for the finished skill.

## Recipe: add-integration-target
1. Interface + client in `Clients/`, copying `CarrierClient.cs`. 2. Settings section `Partners:<Name>` and a property on
`PartnerSettings`. 3. Register in `AddPartnerClients()`. 4. Use it from a handler. 5. Tests with a fake `HttpMessageHandler`.

## Diagnosing
- Messages pile up in `orders.events.retry` → a partner returns 5xx; check `IntegrationLog.LastError`.
- Event ignored silently → no entry in `MessageRouter._handlers` for that `EventType` (it logs `Unrouted event` at Warning).
