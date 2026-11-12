---
name: {{PREFIX}}-fix
description: Diagnose and fix a bug in {{REPO_NAME}} - pin down the symptom, find the root cause from data and code with evidence, smallest fix, regression evidence, record the trap. Use for errors, wrong data, broken screens, failed integrations or anything that used to work.
argument-hint: "<symptom, error text, screen/endpoint, record id>"
---

# Bug fix

## 1. Load context
As in `{{PREFIX}}-feature` step 1: unit, folder archetype, `.ai/standards/`, archetype file, unit pack. Read `gotchas.md` first;
many bugs are known traps.

## 2. Pin down the symptom
Exact error text (server log, browser console, network tab), when it started, the business key (record id, document number,
user/branch), environment, steps to reproduce, expected result. Never ask for secrets or connection strings.

## 3. Root cause, with evidence
- **Backend endpoint**: route → controller → handler/service → SQL/proc, using `generated/entry-points.md` and `data-map.md`.
- **Frontend**: route/page → component → API call (`generated/contracts-and-risks.md`) → backend route
  (`.ai/system/generated/contracts.md`). Check whether the request or the response is wrong before touching UI code.
- **Integration / queue**: follow the archetype file's "Diagnosing" section if it has one (status tables, failure stages).
- **Data inside procs**: read the exported definition in `<unit>/db/` (export with `tools/claude-kit/export-db-objects.ps1`).
  Never guess what a proc does.
State the root cause in 1-2 sentences with file:line or query evidence **before** changing code.

## 4. Fix minimally
Smallest change that removes the cause. If the line you touch breaks a rule in `.ai/standards/` (e.g. SQL built from values),
fix that line too. If the bug is a missing route/registration/case, check every sibling list for the same omission.

## 5. Prove and record
1. `{{PREFIX}}-verify`.
2. Regression evidence for the PR: before/after request-response, screenshot, or log/row.
3. Add to `<unit>/.ai/gotchas.md` if someone could fall into it again: `- <symptom>: <cause>. <how to avoid>`.
