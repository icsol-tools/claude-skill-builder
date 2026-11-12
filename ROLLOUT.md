# Rolling the kit out to ~50 repositories

## 0. Prepare (once, about half a day)
1. Install the builder (README). Clone all repos under one folder.
2. `python plugins/skill-builder/scripts/fleet_scan.py --repos <folder> --out fleet.md --no-write`, then read `fleet.md`.
3. From "Archetypes across the fleet", pick the 3-4 archetypes that cover the most units. Polish their starters in
   `library/archetypes/` with anything that is genuinely shared across teams. Leave team-specific rules to each repo.

## 1. Pilot wave (2-3 repos, one per main stack)
Pick an active repo for each main stack (for example a .NET Core API repo, a .NET Framework repo, a React or Next.js repo).
- Run `/skill-builder:setup-repo` **with a developer from that team present**. The interview is where the value is.
- Use the result for a week: real tickets through `/<prefix>-feature` and `/<prefix>-fix`, and the evals in a pilot unit's `evals.md`.
- Feed what you learn back into the builder (library skills, starters, scanner), bump the version and the CHANGELOG, then
  `/skill-builder:upgrade-kit` the pilots.

## 2. Waves of 5-8 repos per week
Order by activity (most commits first: they get the most value) and group by stack, so each miner run benefits from the last.
For each repo:
1. Team lead plus one developer, 1-3 hours: run `/skill-builder:setup-repo` and answer the questions.
2. PR `chore: Claude kit`, reviewed by the team, then merged.
3. Within two weeks: map the remaining units with `/<prefix>-map-unit` (about one hour each), and owners answer the `(confirm)` items.
Track each repo through four stages: scanned, set up, PR merged, all units mapped.
Inactive or retired repos: leave them out, or give them generated docs only (setup-repo, with every unit marked "later").

## 3. Run it
- Org-level `ANTHROPIC_API_KEY` secret and the Claude GitHub App installed for all repos, so `kit-docs-update` works everywhere.
- A builder owner releases a new version about monthly (CHANGELOG), and teams run `/skill-builder:upgrade-kit`. For a fleet-wide
  view, a weekly scheduled `fleet_scan` shows which repos are behind (the Kit column, plus `kit_version` in each manifest).
- When a team writes a good custom skill or recipe that other teams could use, generalise it into `library/` so every repo can
  install it with `add-skill`.

## Time budget (rough)
| Item | Effort |
|---|---|
| Preparation and pilots | about 1 week, 1 person part-time |
| Per repo setup | 1-3 hours with 1-2 team members |
| Per unit pack | about 1 hour of owner review |
| 50 repos | about 8-10 weeks in waves of 5-8, alongside normal work |
