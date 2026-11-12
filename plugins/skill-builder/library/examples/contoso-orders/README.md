# Example: Contoso Orders (fictional)

A finished reference for the depth `setup-repo` should reach. Contoso Orders is an invented repository with three units:

| Unit | Archetype | What it does |
|---|---|---|
| `services/Contoso.Orders.API` | `dotnet-cqs-api` | REST API for orders; commands and queries with handlers and dispatchers |
| `services/Contoso.Orders.Worker` | `dotnet-queue-worker` | Consumes `orders.events` from RabbitMQ and pushes changes to partner systems |
| `legacy/Contoso.Billing` | `dotnet-legacy-ba-da` | .NET Framework web app with business-access (BA) and data-access (DA) layers |

Files:
- `a1-cqs-api.md`, `a2-queue-worker.md`, `b-legacy-ba-da.md` - finished `.ai/archetypes/` files: exact folders, base types,
  registration points and the file to copy for every recipe.
- `recipe-skill-add-message-handler.md` - a finished recipe skill (`.claude/skills/co-add-message-handler/SKILL.md`).

All names, tables and queues here are invented. Never copy facts from this example into a real repo: mine them from its code.
