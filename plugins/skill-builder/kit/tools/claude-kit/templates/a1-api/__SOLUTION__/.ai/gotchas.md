# __SOLUTION__: gotchas

> One line per trap: `- <trap>: <cause / evidence>. <how to avoid>`.

## Code
- Handlers are auto-registered only from `__PREFIX__.CQS`, and only because the API project uses types from it. A new CQS project needs its own `AddCommandQueryHandlers` call in `DILoader`.

## Configuration
- No API keys configured means every protected request returns 401 (fail closed). Set `Security:ApiKeys` on each server.
- CORS allows no browser origin until `Cors:AllowedOrigins` lists them.
