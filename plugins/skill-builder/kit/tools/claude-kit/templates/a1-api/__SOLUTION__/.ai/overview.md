# __SOLUTION__: overview

> Narrative. Facts the code proves are in `generated/`. Keep this current as endpoints are added.

## Purpose
__PURPOSE__

## Who calls it and what it calls
- Callers: TODO (who sends requests, how they authenticate)
- Calls: TODO (databases, queues, external APIs)

## Endpoints
| Route | Business meaning | Caller |
|---|---|---|
| GET /api/v1/health | Liveness + database reachability | monitoring |

## Running locally
1. `dotnet user-secrets set "ConnectionStrings:CommonConnectionString" "<dev connection string>" --project __PREFIX__.API`
2. `dotnet user-secrets set "Security:ApiKeys:0" "<any local key>" --project __PREFIX__.API`
3. `dotnet run --project __PREFIX__.API`, then open http://localhost:__PORT__/swagger
