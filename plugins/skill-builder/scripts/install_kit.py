#!/usr/bin/env python3
"""
install_kit.py - deterministic deploy step of /skill-builder:setup-repo and /skill-builder:upgrade-kit.

Reads the plan Claude wrote after the interview (<repo>/.ai/kit/plan.json) and writes into the repo:

  managed files  (kit-owned; recorded with sha256 in .ai/kit/manifest.json; upgrades replace them only if unmodified)
    tools/claude-kit/docgen.py, kit_check.py, [export-db-objects.ps1], [templates/...]
    .claude/skills/<prefix>-<core skill>/SKILL.md      (generic procedures from library/skills)
    .claude/agents/*.md                                  (unit-mapper, db-mapper, pack-reviewer)
    .ai/templates/*                                      (pack templates)
    .github/workflows/kit-docs-*.yml                     [optional]
  seeded files   (repo-owned; written only if absent, then edited by Claude/people; never overwritten)
    CLAUDE.md, .ai/README.md, .ai/GUIDE.md, .ai/exclude-paths.txt, .ai/standards/<starters>
  merged         .claude/settings.json (permission rules unioned; other keys kept)

Existing files the kit did not create are never overwritten: the new version is written next to them as <file>.kit-new.

  python install_kit.py --repo <repo> [--dry-run]           # install from <repo>/.ai/kit/plan.json
  python install_kit.py --repo <repo> --upgrade [--dry-run]  # upgrade managed files to this builder's kit
Standard library only, Python 3.10+.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
KIT = PLUGIN / "kit"
LIB = PLUGIN / "library"
CORE_SKILLS = ["onboard", "feature", "fix", "verify", "docs-refresh", "map-unit"]
OPTIONAL_SKILLS = ["change-contract", "new-service"]
TEXT_EXT = {".md", ".py", ".ps1", ".yml", ".yaml", ".json", ".txt", ".cs", ".csproj", ".config", ".template", ".gitignore", ".slnx"}


def kit_version() -> str:
    return (KIT / "VERSION").read_text(encoding="utf-8").strip()


def builder_version() -> str:
    return json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def render(src: Path, subs: dict[str, str]) -> bytes:
    data = src.read_bytes()
    if src.suffix in TEXT_EXT or src.name in (".gitignore",):
        text = data.decode("utf-8")
        for k, v in subs.items():
            text = text.replace("{{" + k + "}}", v)
        return text.encode("utf-8")
    return data


def validate_plan(plan: dict) -> list[str]:
    errs = []
    if not re.fullmatch(r"[a-z][a-z0-9]{1,15}", plan.get("prefix", "")):
        errs.append("prefix must be 2-16 lower-case letters/digits, starting with a letter (e.g. 'gain', 'dms')")
    if not plan.get("repo_name"):
        errs.append("repo_name is required")
    if not plan.get("units"):
        errs.append("units is empty - nothing to set up")
    for u in plan.get("units", []):
        if not u.get("path") or not u.get("kind") or not u.get("archetypes"):
            errs.append(f"unit needs path, kind and archetypes: {u}")
    for s in plan.get("skills", []):
        if s not in CORE_SKILLS + OPTIONAL_SKILLS:
            errs.append(f"unknown library skill '{s}' (recipe/custom skills are written by Claude, not the installer)")
    return errs


def managed_sources(plan: dict) -> dict[str, Path]:
    """target path (repo-relative, posix) -> source file in the plugin."""
    p = plan["prefix"]
    out: dict[str, Path] = {}
    tools = KIT / "tools" / "claude-kit"
    for name in ("docgen.py", "kit_check.py"):
        out[f"tools/claude-kit/{name}"] = tools / name
    if plan.get("include_db_export"):
        out["tools/claude-kit/export-db-objects.ps1"] = tools / "export-db-objects.ps1"
    if plan.get("include_service_template"):
        for f in sorted((tools / "templates").rglob("*")):
            if f.is_file():
                out[f"tools/claude-kit/templates/{f.relative_to(tools / 'templates').as_posix()}"] = f
    for s in sorted(set(CORE_SKILLS + [x for x in plan.get("skills", []) if x in OPTIONAL_SKILLS])):
        if s == "new-service" and not plan.get("include_service_template"):
            continue
        out[f".claude/skills/{p}-{s}/SKILL.md"] = LIB / "skills" / s / "SKILL.md"
    for f in sorted((LIB / "agents").glob("*.md")):
        out[f".claude/agents/{f.name}"] = f
    for name in ("overview.md", "gotchas.md", "decisions.md", "evals.md", "unit.yaml", "CLAUDE.unit.md", "system-map.md"):
        out[f".ai/templates/{name}"] = LIB / "docs" / name
    if plan.get("include_workflows", True):
        for f in sorted((KIT / "workflows").glob("*.yml")):
            out[f".github/workflows/{f.name}"] = f
    return out


def seeded_sources(plan: dict) -> dict[str, Path]:
    out = {
        "CLAUDE.md": LIB / "docs" / "CLAUDE.root.md",
        ".ai/README.md": LIB / "docs" / "ai-README.md",
        ".ai/GUIDE.md": LIB / "docs" / "GUIDE.md",
        ".ai/exclude-paths.txt": LIB / "docs" / "exclude-paths.txt",
        ".ai/system/system-map.md": LIB / "docs" / "system-map.md",
        ".ai/standards/sql-safety.md": LIB / "standards" / "sql-safety.md",
        ".ai/standards/secrets-and-config.md": LIB / "standards" / "secrets-and-config.md",
        ".ai/standards/definition-of-done.md": LIB / "standards" / "definition-of-done.md",
    }
    if any(u["kind"] == "frontend" for u in plan["units"]):
        out[".ai/standards/frontend-security.md"] = LIB / "standards" / "frontend-security.md"
    return out


def substitutions(plan: dict) -> dict[str, str]:
    kinds = {u["kind"] for u in plan["units"]}
    stack_tools = []
    if any(k.startswith("dotnet") for k in kinds):
        stack_tools.append(".NET SDK (and Visual Studio / MSBuild for .NET Framework units)" if plan.get("has_dotnet_framework") else ".NET SDK")
    if "frontend" in kinds:
        stack_tools.append("Node.js LTS")
    return {
        "PREFIX": plan["prefix"],
        "REPO_NAME": plan["repo_name"],
        "DEFAULT_BRANCH": plan.get("default_branch", "main"),
        "DRIFT_CRON": plan.get("drift_cron", "17 3 * * 1"),
        "KIT_VERSION": kit_version(),
        "EXCLUDES": "\n".join(plan.get("excludes", [])),
        "STACK_TOOLS": (", " + ", ".join(stack_tools)) if stack_tools else "",
        "TEMPLATE_LINE": ", `templates/` (new-service scaffold)" if plan.get("include_service_template") else "",
    }


def merge_settings(repo: Path, plan: dict, dry: bool, log: list[str]) -> None:
    target = repo / ".claude" / "settings.json"
    base = json.loads((KIT / "settings.base.json").read_text(encoding="utf-8"))
    current = {}
    if target.exists():
        try:
            current = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.append("CONFLICT .claude/settings.json is not valid JSON - left unchanged; merge permissions by hand")
            return
    perms = current.setdefault("permissions", {})
    deny = list(dict.fromkeys(perms.get("deny", []) + base["permissions"]["deny"] +
                              [r for e in plan.get("excludes", []) if not e.startswith("tools/") for r in (f"Read({e}/**)", f"Edit({e}/**)")]))
    allow = perms.get("allow", []) + base["permissions"]["allow"]
    kinds = {u["kind"] for u in plan["units"]}
    if any(k.startswith("dotnet") for k in kinds):
        allow += ["Bash(dotnet build:*)", "Bash(dotnet test:*)", "Bash(dotnet list:*)"]
    if "frontend" in kinds:
        allow += ["Bash(npm run lint:*)", "Bash(npm run build:*)", "Bash(npm run test:*)", "Bash(npm test:*)",
                  "Bash(pnpm run lint:*)", "Bash(pnpm run build:*)", "Bash(yarn lint:*)", "Bash(yarn build:*)"]
    if plan.get("include_service_template"):
        allow.append("Bash(powershell -NoProfile -ExecutionPolicy Bypass -File tools/claude-kit/templates/new-service.ps1:*)")
    perms["deny"] = deny
    perms["allow"] = list(dict.fromkeys(allow))
    new = json.dumps(current, indent=2) + "\n"
    old = target.read_text(encoding="utf-8") if target.exists() else None
    if new != old:
        log.append(("UPDATE " if old else "CREATE ") + ".claude/settings.json (permissions merged)")
        if not dry:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(new, encoding="utf-8", newline="\n")


def write(repo: Path, relp: str, data: bytes, dry: bool) -> None:
    if dry:
        return
    p = repo / relp
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def install(repo: Path, plan: dict, dry: bool, upgrade: bool) -> int:
    log: list[str] = []
    man_path = repo / ".ai" / "kit" / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}
    old_managed: dict[str, str] = manifest.get("managed_files", {})
    customised: dict[str, str] = dict(manifest.get("customised_files", {}))  # file -> kit hash it was merged against
    subs = substitutions(plan)
    managed = managed_sources(plan)
    new_managed: dict[str, str] = {}
    conflicts = 0

    for relp, src in managed.items():
        data = render(src, subs)
        target = repo / relp
        h = sha(data)
        if not target.exists():
            log.append(f"CREATE {relp}")
            write(repo, relp, data, dry)
            new_managed[relp] = h
            continue
        current = sha(target.read_bytes())
        if current == h:
            new_managed[relp] = h
            customised.pop(relp, None)
            continue
        if relp in customised and customised[relp] == h:
            new_managed[relp] = old_managed.get(relp, current)   # team's merged version, kit unchanged since the merge
            continue
        if relp in old_managed and current == old_managed[relp] and relp not in customised:
            log.append(f"UPDATE {relp}")
            write(repo, relp, data, dry)
            new_managed[relp] = h
        else:
            why = "changed locally since the kit installed it" if relp in old_managed else "exists and was not created by the kit"
            log.append(f"CONFLICT {relp} ({why}) - new version written to {relp}.kit-new; merge by hand")
            write(repo, relp + ".kit-new", data, dry)
            new_managed[relp] = old_managed.get(relp, current)
            conflicts += 1
    for relp in sorted(set(old_managed) - set(managed)):
        log.append(f"OBSOLETE {relp} (no longer part of the kit - delete it if nothing uses it)")

    seeded = manifest.get("seeded_files", [])
    if not upgrade:
        for relp, src in seeded_sources(plan).items():
            if (repo / relp).exists():
                if relp not in seeded:
                    log.append(f"KEEP {relp} (already exists - not overwritten; Claude merges the kit sections in)")
                    seeded.append(relp)
                continue
            log.append(f"SEED {relp}")
            write(repo, relp, render(src, subs), dry)
            seeded.append(relp)
        merge_settings(repo, plan, dry, log)
    else:
        merge_settings(repo, plan, dry, log)

    skills = sorted({Path(k).parent.name for k in new_managed if k.startswith(".claude/skills/")} |
                    set(manifest.get("skills", [])) | set(plan.get("generated_skills", [])))
    manifest_new = {
        "kit_version": kit_version(), "builder_version": builder_version(),
        "installed_at": manifest.get("installed_at") or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "upgraded_at": datetime.now(timezone.utc).strftime("%Y-%m-%d") if upgrade else manifest.get("upgraded_at"),
        "prefix": plan["prefix"], "repo_name": plan["repo_name"], "default_branch": plan.get("default_branch", "main"),
        "units": [{"path": u["path"], "kind": u["kind"], "archetypes": u["archetypes"]} for u in plan["units"]],
        "skills": skills, "managed_files": dict(sorted(new_managed.items())), "seeded_files": sorted(set(seeded)),
        "customised_files": dict(sorted(customised.items())),
        "options": {k: plan.get(k) for k in ("include_db_export", "include_service_template", "include_workflows", "has_dotnet_framework")},
    }
    if not dry:
        man_path.parent.mkdir(parents=True, exist_ok=True)
        man_path.write_text(json.dumps(manifest_new, indent=1) + "\n", encoding="utf-8", newline="\n")
    log.append(("WOULD WRITE " if dry else "WRITE ") + ".ai/kit/manifest.json")

    print(f"{'DRY RUN - ' if dry else ''}{'upgrade' if upgrade else 'install'} kit {kit_version()} into {repo}")
    for line in log:
        print("  " + line)
    print(f"{sum(1 for l in log if l.startswith(('CREATE', 'SEED', 'UPDATE')))} written, {conflicts} conflict(s)")
    return 0


def accept(repo: Path, files: list[str]) -> int:
    man_path = repo / ".ai" / "kit" / "manifest.json"
    m = json.loads(man_path.read_text(encoding="utf-8"))
    for f in files:
        relp = Path(f).as_posix().removesuffix(".kit-new")
        new = repo / (relp + ".kit-new")
        if not new.exists() or not (repo / relp).exists():
            print(f"Nothing to accept for {relp} (need both {relp} and {relp}.kit-new)", file=sys.stderr)
            return 2
        m.setdefault("customised_files", {})[relp] = sha(new.read_bytes())
        m.setdefault("managed_files", {})[relp] = sha((repo / relp).read_bytes())
        new.unlink()
        print(f"ACCEPTED {relp} as team-customised (future kit changes to it will be offered as .kit-new again)")
    man_path.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--plan", help="default <repo>/.ai/kit/plan.json")
    ap.add_argument("--upgrade", action="store_true", help="refresh managed files from this builder; uses the manifest when no plan is given")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--accept", action="append", default=[], metavar="FILE",
                    help="after merging <FILE>.kit-new into FILE by hand: record FILE as a team-customised kit file and delete the .kit-new")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    if a.accept:
        return accept(repo, a.accept)
    plan_path = Path(a.plan) if a.plan else repo / ".ai" / "kit" / "plan.json"
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    elif a.upgrade and (repo / ".ai" / "kit" / "manifest.json").exists():
        m = json.loads((repo / ".ai" / "kit" / "manifest.json").read_text(encoding="utf-8"))
        plan = {"prefix": m["prefix"], "repo_name": m["repo_name"], "default_branch": m.get("default_branch", "main"), "units": m["units"],
                "skills": [s[len(m["prefix"]) + 1:] for s in m.get("skills", []) if s[len(m["prefix"]) + 1:] in OPTIONAL_SKILLS],
                "excludes": [], **{k: v for k, v in m.get("options", {}).items() if v is not None}}
        ex = repo / ".ai" / "exclude-paths.txt"
        if ex.exists():
            plan["excludes"] = [l.split("#", 1)[0].strip() for l in ex.read_text(encoding="utf-8").splitlines() if l.split("#", 1)[0].strip()]
    else:
        print(f"No plan found at {plan_path}", file=sys.stderr)
        return 2
    errs = validate_plan(plan)
    if errs:
        for e in errs:
            print("PLAN ERROR: " + e, file=sys.stderr)
        return 2
    return install(repo, plan, a.dry_run, a.upgrade)


if __name__ == "__main__":
    sys.exit(main())
