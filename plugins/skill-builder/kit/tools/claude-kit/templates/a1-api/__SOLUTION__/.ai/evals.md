# __SOLUTION__: evals

> Add 3-5 realistic tasks once the first endpoints exist. Run each in plan mode in a fresh session.

## E1 "Add an endpoint that returns <something> by id"
- **Must touch:** Dto, Query + Result + Handler in `__PREFIX__.CQS/Queries`, a controller action shaped like `HealthController`.
- **Must not:** build SQL from values; skip the API key; put logic in the controller.
- **Pass if:** the plan follows `.ai/archetypes/dotnet-cqs-api.md` step by step.
