# How setup-repo turns a starter into the repo's archetype file

1. Copy the starter to `<repo>/.ai/archetypes/<scanner-archetype-id>.md`.
2. Replace every `<!-- fill: ... -->` with this repo's facts from the convention-miner report, each with an evidence path.
3. Delete sections and variants that do not apply. Keep the headings `How it flows`, `Rules for new code`,
   `Recipe: <name>` (one per recipe the team chose), `Diagnosing`, `Known variations`.
4. Recipes are numbered steps a developer (or Claude) can follow literally in this repo: exact folders, file-name patterns,
   base classes/interfaces, registration points, and the existing file to copy. The recipe skills point here.
5. Anything the team did not confirm stays marked `(confirm)`.
Depth and tone to aim for: `examples/contoso-orders/a1-cqs-api.md` and `a2-queue-worker.md` (a fictional repo).
