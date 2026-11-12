# Archetype: .NET message / background worker (<!-- fill: RabbitMQ / Service Bus / MassTransit / timers -->)

**Applies to:** <!-- fill -->

## How it flows
```
<!-- fill: queue/topic names (config keys) --> -> consumer (<!-- fill: class -->) -> routing (<!-- fill: switch on code / message type -->)
  -> handler/domain service -> <!-- fill: data / external API --> -> <!-- fill: status/log table -->
Retries: <!-- fill: ACK/NACK policy, retry counts, schedulers, dead-letter -->
```

## Golden rules
<!-- fill, typical: consumers never throw / never NACK on business failures; failures persisted with a stage; idempotent handlers;
every routing code appears in every routing table -->

## Recipe: add-message-handler
<!-- fill: numbered steps incl. config/mapping rows, query, payload classes, endpoint constants, domain method, every consumer
switch to update, write-back, DI. See examples/contoso-orders/recipe-skill-add-message-handler.md for the depth expected. -->

## Recipe: add-integration-target
<!-- fill: auth config section, base URL, auth handler, per-target payloads, routing branch -->

## Recipe: add-scheduled-job
<!-- fill: hosted service pattern, timer config key, scope creation, overlap protection -->

## Diagnosing
<!-- fill: status table query by business key, failure stages, log/raw exchange tables, republish/reset tools -->
