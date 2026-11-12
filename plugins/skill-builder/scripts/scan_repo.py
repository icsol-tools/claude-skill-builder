#!/usr/bin/env python3
"""
scan_repo.py - first step of /skill-builder:setup-repo.

Walks a repository and writes a factual profile Claude uses to interview the team and propose
skills: units (solutions / apps), stack and version, libraries, architecture signals, tests,
CI, existing AI setup, risks and folders that look retired.

Never reads or prints configuration VALUES or secrets: only file paths, key names and counts.
Standard library only (Python 3.10+). Read-only except for the two output files.

  python scan_repo.py --root <repo> [--out <repo>/.ai/kit] [--exclude Archive --exclude old]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "bin", "obj", ".vs", ".idea", ".vscode", "dist", "build", ".next", ".angular",
             "coverage", "packages", "TestResults", ".nuget", "out", ".turbo", ".cache", "__pycache__", ".ai"}
RETIRED_NAMES = re.compile(r"^(_?archive[sd]?|_?old|backup[s]?|bak|deprecated|obsolete|zz_.*|.*[_\-.]old|old[_\-.].*|unused|retired)$", re.I)
CODE_EXT = {".cs", ".ts", ".tsx", ".js", ".jsx", ".vb", ".sql", ".cshtml", ".aspx", ".html", ".scss", ".css", ".ps1", ".py"}

PUBLIC_NUGET = tuple(p.lower() for p in (
    "Microsoft", "System", "Newtonsoft", "Dapper", "NLog", "Serilog", "Swashbuckle", "AutoMapper", "FluentValidation",
    "Polly", "xunit", "NUnit", "MSTest", "Moq", "EntityFramework", "RabbitMQ", "MassTransit", "Azure", "AWSSDK",
    "Google", "StackExchange", "Hangfire", "MediatR", "QRCoder", "log4net", "Autofac", "Unity", "Ninject", "Castle",
    "Owin", "jQuery", "bootstrap", "Antlr", "WebGrease", "Modernizr", "Elmah", "iTextSharp", "itext7", "EPPlus",
    "ClosedXML", "CsvHelper", "Quartz", "Humanizer", "NodaTime", "Npgsql", "MySql", "Oracle", "Twilio", "SendGrid",
    "Stripe", "Hellang", "Scrutor", "Bogus", "coverlet", "NSubstitute", "FluentAssertions", "Shouldly", "Refit",
    "RestSharp", "HtmlAgilityPack", "CommandLineParser", "Spectre", "BCrypt", "IdentityModel", "Duende", "OpenIddict",
    "Sentry", "Elastic", "NEST", "Grpc", "protobuf-net", "MessagePack", "WindowsAzure", "Pomelo", "Mapster",
    "DocumentFormat", "SharpZipLib", "DotNetZip", "PdfSharp", "Rotativa", "Crystal", "ReportViewer", "ExcelDataReader",
    "Swagger", "NSwag", "Asp.Versioning", "Ocelot", "Yarp", "Consul", "OpenTelemetry", "prometheus", "Seq", "Lucene",
    "WebActivatorEx", "Glimpse", "Unity.Mvc", "Ninject.Web", "SimpleInjector", "Lamar", "StructureMap", "Respawn",
    "Testcontainers", "WireMock", "AngleSharp", "MimeKit", "MailKit", "BouncyCastle", "Portable.BouncyCastle", "jose-jwt",
    "JWT", "Otp.NET", "QuestPDF", "SkiaSharp", "ImageSharp", "SixLabors", "Magick", "FastMember", "Z.EntityFramework",
    "LinqKit", "morelinq", "Ardalis", "ErrorOr", "OneOf", "FluentResults", "Carter", "FastEndpoints", "Hl7", "Nito"))
PUBLIC_NPM_SCOPES = {"angular", "types", "tanstack", "vitejs", "testing-library", "reduxjs", "mui", "emotion", "playwright",
                     "ngrx", "babel", "eslint", "typescript-eslint", "next", "vercel", "sentry", "fortawesome", "headlessui",
                     "heroicons", "radix-ui", "hookform", "nestjs", "storybook", "vitest", "swc", "rollup", "esbuild", "jest",
                     "ant-design", "chakra-ui", "mantine", "tailwindcss", "popperjs", "fontsource", "microsoft", "azure",
                     "aws-sdk", "googlemaps", "react-google-maps", "stripe", "auth0", "okta", "clerk", "supabase", "prisma",
                     "trpc", "apollo", "graphql-codegen", "commitlint", "changesets", "nx", "schematics", "ionic", "capacitor",
                     "capacitor-community", "ng-bootstrap", "ng-select", "ngx-translate", "fullcalendar", "ckeditor", "tinymce",
                     "zxing", "date-io", "floating-ui", "dnd-kit", "faker-js", "hapi", "rushstack", "pmmmwh", "svgr", "remix-run"}


# --------------------------------------------------------------------------- helpers

def read(p: Path, limit: int = 2_000_000) -> str:
    try:
        with open(p, "rb") as f:
            return f.read(limit).decode("utf-8-sig", errors="replace")
    except OSError:
        return ""


def rel(p: Path, root: Path) -> str:
    return p.relative_to(root).as_posix() or "."


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def is_excluded(relp: str, excludes: list[str]) -> bool:
    r = relp.lower().strip("/")
    return any(r == e.lower() or r.startswith(e.lower().rstrip("/") + "/") for e in excludes)


def walk(root: Path, base: Path, excludes: list[str]):
    for dirpath, dirnames, filenames in os.walk(base):
        d = Path(dirpath)
        dirnames[:] = sorted(x for x in dirnames if x not in SKIP_DIRS and not is_excluded(rel(d / x, root), excludes))
        for f in sorted(filenames):
            yield d / f


def load_json(p: Path) -> dict:
    try:
        return json.loads(re.sub(r"(?m)^\s*//.*$", "", read(p)))
    except Exception:
        return {}


# --------------------------------------------------------------------------- unit discovery

def discover_units(root: Path, excludes: list[str]) -> list[dict]:
    """A unit is a .NET solution folder, an orphan .csproj, or a frontend app (package.json with a UI framework)."""
    units: list[dict] = []
    owned: list[str] = []  # dirs already owned by a dotnet solution

    def owned_by(relp: str) -> bool:
        return any(relp == o or relp.startswith(o + "/") for o in owned)

    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        relp = rel(d, root)
        dirnames[:] = sorted(x for x in dirnames if x not in SKIP_DIRS and not is_excluded(rel(d / x, root), excludes))
        if relp != "." and is_excluded(relp, excludes):
            dirnames[:] = []
            continue
        if any(f.endswith((".sln", ".slnx")) for f in filenames) and not owned_by(relp):
            units.append({"kind": "dotnet-solution", "path": relp})
            owned.append(relp)
        if "package.json" in filenames:
            pkg = load_json(d / "package.json")
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if any(k in deps for k in ("react", "next", "@angular/core", "vue", "svelte", "vite", "react-scripts")):
                units.append({"kind": "frontend", "path": relp})
            elif pkg.get("workspaces"):
                units.append({"kind": "js-workspace-root", "path": relp})

    # orphan csproj files (not under a solution)
    for p in walk(root, root, excludes):
        if p.suffix == ".csproj":
            r = rel(p.parent, root)
            if not owned_by(r):
                units.append({"kind": "dotnet-project", "path": r})
                owned.append(r)
    # frontend apps nested in another frontend app (not workspaces) are part of the parent
    fronts = sorted((u for u in units if u["kind"] == "frontend"), key=lambda u: len(u["path"]))
    keep = []
    for u in fronts:
        if not any(u["path"].startswith(k["path"] + "/") for k in keep if k["path"] != "."):
            keep.append(u)
    units = [u for u in units if u["kind"] != "frontend"] + keep
    return sorted(units, key=lambda u: u["path"])


# --------------------------------------------------------------------------- .NET analysis

DOTNET_SIGNALS = {
    "cqs_command_handlers": r"\bICommandHandler<",
    "cqs_query_handlers": r"\bIQueryHandler<",
    "mediatr_handlers": r"\bIRequestHandler<",
    "controllers_core": r":\s*(?:Controller|ControllerBase)\b",
    "controllers_webapi2": r":\s*ApiController\b",
    "minimal_api_maps": r"\.Map(?:Get|Post|Put|Delete|Patch)\(",
    "hosted_services": r"\b(?:IHostedService|BackgroundService)\b",
    "rabbitmq": r"\bRabbitMQ\w*|IModel\b.*BasicConsume|RabbitMQConsumer",
    "masstransit_or_servicebus": r"\b(?:MassTransit|ServiceBusClient|IConsumer<)",
    "ef_dbcontext": r":\s*DbContext\b",
    "dapper": r"\bQuery(?:FirstOrDefault|Single|Multiple)?Async?\s*<|\.Execute(?:Async)?\(",
    "ado_sqlcommand": r"\bnew\s+SqlCommand\(|SqlDataAdapter",
    "datatable": r"\bDataTable\b",
    "stored_proc_calls": r"\"\s*EXEC(?:UTE)?\s|CommandType\.StoredProcedure",
    "repository_pattern": r"\bIRepository<",
    "fluentvalidation": r"AbstractValidator<",
    "automapper": r"\bIMapper\b|CreateMap<",
    "authorize_attr": r"\[Authorize",
    "jwt_auth": r"AddJwtBearer|JwtSecurityToken",
    "swagger": r"AddSwaggerGen|SwaggerConfig",
    "nlog": r"\bNLog\b",
    "serilog": r"\bSerilog\b",
    "log4net": r"\blog4net\b",
    "static_config": r"ConfigurationManager\.(?:AppSettings|ConnectionStrings)",
    "di_container_legacy": r"\b(?:UnityContainer|Ninject|ContainerBuilder|SimpleInjector)\b",
    "wcf": r"\[ServiceContract\]|\[OperationContract\]",
    "business_access_layer": r"\b\w+(?:BA|BL|BLL|Manager)\s+\w+\s*=\s*new\b|\bnew\s+\w+(?:BA|BLL)\s*\(",
}
UNSAFE_SQL = re.compile(r"\"[^\"\n]*\b(?:EXEC|SELECT|UPDATE|INSERT|DELETE)\b[^\"\n]*\"\s*\+|\$@?\"[^\"\n]*(?:\b(?:EXEC|SELECT|UPDATE|INSERT|DELETE)\b|@\w+\s*=)[^\"\n]*\{", re.I)


def analyse_dotnet(root: Path, unit: dict, excludes: list[str]) -> dict:
    base = root / unit["path"]
    projects, packages = [], Counter()
    signals = Counter()
    unsafe_sql = 0
    file_types = Counter()
    for p in walk(root, base, excludes):
        file_types[p.suffix.lower()] += 1
        if p.suffix == ".csproj":
            t = read(p)
            sdk = re.search(r'<Project\s+Sdk="([^"]+)"', t)
            tf = re.search(r"<TargetFrameworks?>([^<]+)<", t) or re.search(r"<TargetFrameworkVersion>([^<]+)<", t)
            pkgs = re.findall(r'<PackageReference\s+Include="([^"]+)"(?:\s+Version="([^"]*)")?', t)
            pc = p.parent / "packages.config"
            if pc.exists():
                pkgs += re.findall(r'<package\s+id="([^"]+)"\s+version="([^"]+)"', read(pc))
            refs = re.findall(r'<Reference\s+Include="([^",]+)', t)
            is_test = any(re.match(r"(xunit|nunit|mstest|Microsoft\.NET\.Test\.Sdk)", n, re.I) for n, *_ in pkgs)
            web = bool(sdk and sdk.group(1).endswith(".Web")) or any(r.startswith("System.Web") for r in refs) or (p.parent / "Web.config").exists()
            projects.append({
                "name": p.stem, "path": rel(p.parent, root),
                "style": "sdk" if sdk else "legacy-msbuild",
                "target": (tf.group(1) if tf else ""),
                "kind": "test" if is_test else ("web" if web else "library/other"),
                "packages": sorted({f"{n} {v}".strip() for n, v in pkgs}),
            })
            for n, v in pkgs:
                packages[n] += 1
        elif p.suffix == ".cs":
            t = read(p, 400_000)
            for k, rx in DOTNET_SIGNALS.items():
                c = len(re.findall(rx, t))
                if c:
                    signals[k] += c
            unsafe_sql += len(UNSAFE_SQL.findall(t))
    targets = " ".join(pr["target"] for pr in projects).lower()
    framework = "dotnet-framework" if re.search(r"v4\.|net4\d", targets) and not re.search(r"net[5-9]|net1\d|netcore", targets) else (
        "dotnet-mixed" if re.search(r"v4\.|net4\d", targets) else "dotnet-core")
    internal = sorted(n for n in packages if not n.lower().startswith(PUBLIC_NUGET))
    return {
        "framework": framework, "projects": projects, "signals": dict(signals), "unsafe_sql_fragments": unsafe_sql,
        "candidate_internal_packages": internal,
        "has_tests": any(pr["kind"] == "test" for pr in projects),
        "webforms_pages": file_types.get(".aspx", 0), "razor_views": file_types.get(".cshtml", 0),
        "sql_files": file_types.get(".sql", 0), "cs_files": file_types.get(".cs", 0),
        "archetypes": propose_dotnet_archetypes(framework, signals, file_types, projects),
    }


def propose_dotnet_archetypes(framework: str, s: Counter, ft: Counter, projects: list) -> list[dict]:
    out = []

    def add(name, why, conf):
        out.append({"archetype": name, "confidence": conf, "evidence": why})

    ctrl = s["controllers_core"] + s["controllers_webapi2"]
    if framework == "dotnet-framework":
        if s["wcf"]:
            add("dotnetfx-wcf", f"{s['wcf']} [ServiceContract]/[OperationContract]", "high")
        if ft.get(".aspx", 0):
            add("dotnetfx-webforms", f"{ft['.aspx']} .aspx pages", "high")
        if s["controllers_webapi2"]:
            add("dotnetfx-webapi", f"{s['controllers_webapi2']} ApiController classes", "high")
        if s["controllers_core"] and ft.get(".cshtml", 0):
            add("dotnetfx-mvc", f"{s['controllers_core']} MVC controllers, {ft['.cshtml']} views", "high")
        if not out:
            add("dotnetfx-library", "no web entry points found", "medium")
        return out
    if s["hosted_services"] and (s["rabbitmq"] or s["masstransit_or_servicebus"]):
        add("dotnet-queue-worker", f"{s['hosted_services']} hosted services with queue consumers", "high")
    if ctrl and (s["cqs_command_handlers"] + s["cqs_query_handlers"]):
        add("dotnet-cqs-api", f"{ctrl} controllers, {s['cqs_command_handlers'] + s['cqs_query_handlers']} command/query handlers", "high")
    elif ctrl and s["mediatr_handlers"]:
        add("dotnet-mediatr-api", f"{ctrl} controllers, {s['mediatr_handlers']} MediatR handlers", "high")
    if ctrl and (s["business_access_layer"] or (s["datatable"] > 20 and s["ado_sqlcommand"])):
        add("dotnet-legacy-ba-da", f"business-access classes ({s['business_access_layer']}), DataTable ({s['datatable']}), SqlCommand ({s['ado_sqlcommand']})", "medium")
    if ctrl and not any(a["archetype"] in ("dotnet-cqs-api", "dotnet-mediatr-api", "dotnet-legacy-ba-da") for a in out):
        add("dotnet-web-api", f"{ctrl} controllers, no CQS/MediatR handlers", "medium")
    if s["minimal_api_maps"] and not ctrl:
        add("dotnet-minimal-api", f"{s['minimal_api_maps']} Map* endpoints", "high")
    if s["hosted_services"] and not out:
        add("dotnet-worker", f"{s['hosted_services']} hosted services", "medium")
    if not out:
        add("dotnet-library", "no entry points found", "low")
    return out


# --------------------------------------------------------------------------- frontend analysis

FRONT_SIGNALS = {
    "react_router_routes": r"<Route\s[^>]*path=|createBrowserRouter|createHashRouter|useRoutes\(",
    "angular_routes": r":\s*Routes\s*=|RouterModule\.for(?:Root|Child)",
    "angular_standalone": r"standalone:\s*true|loadComponent:",
    "angular_ngmodule": r"@NgModule\(",
    "http_axios": r"\baxios\b",
    "http_fetch": r"\bfetch\(",
    "http_angular": r"\bHttpClient\b",
    "env_vite": r"import\.meta\.env\.",
    "env_process": r"process\.env\.",
    "dangerously_set_html": r"dangerouslySetInnerHTML|bypassSecurityTrust",
    "eval_like": r"\beval\(|new Function\(",
    "react_query": r"useQuery\(|useMutation\(",
    "swr": r"\buseSWR\(",
    "redux": r"configureStore\(|createSlice\(|useSelector\(",
    "zustand": r"\bcreate\(\s*\(set",
    "ngrx": r"createReducer\(|createEffect\(",
    "server_components_fetch": r"export\s+default\s+async\s+function",
    "server_actions": r"['\"]use server['\"]",
    "client_components": r"['\"]use client['\"]",
}
HARDCODED_SECRET = re.compile(r"sk_live_[0-9A-Za-z]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-[0-9A-Za-z-]{10,}|ghp_[0-9A-Za-z]{30,}|AIza[0-9A-Za-z_\-]{30,}")


def analyse_frontend(root: Path, unit: dict, excludes: list[str]) -> dict:
    base = root / unit["path"]
    pkg = load_json(base / "package.json")
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    signals, files, ts = Counter(), Counter(), 0
    for p in walk(root, base, excludes):
        if p.suffix in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue"):
            files[p.suffix] += 1
            t = read(p, 400_000)
            for k, rx in FRONT_SIGNALS.items():
                c = len(re.findall(rx, t))
                if c:
                    signals[k] += c
    has = lambda *names: any(n in deps for n in names)  # noqa: E731
    if has("next"):
        app_dir = (base / "app").is_dir() or (base / "src" / "app").is_dir()
        pages_dir = (base / "pages").is_dir() or (base / "src" / "pages").is_dir()
        framework = "nextjs"
        router = "app+pages" if app_dir and pages_dir else ("app" if app_dir else "pages")
    elif has("@angular/core"):
        framework = "angular"
        router = "standalone" if signals["angular_standalone"] and not signals["angular_ngmodule"] else ("ngmodule" if signals["angular_ngmodule"] else "unknown")
    elif has("react") and has("vite"):
        framework, router = "react-vite", ("react-router" if has("react-router-dom", "react-router") else ("tanstack-router" if has("@tanstack/react-router") else "none"))
    elif has("react-scripts"):
        framework, router = "react-cra", ("react-router" if has("react-router-dom") else "none")
    elif has("react"):
        framework, router = "react", ("react-router" if has("react-router-dom") else "none")
    elif has("vue"):
        framework, router = "vue", ("vue-router" if has("vue-router") else "none")
    else:
        framework, router = "other", "none"

    def pick(cands):
        return [c for c in cands if c in deps]
    stack = {
        "state": pick(["@reduxjs/toolkit", "redux", "zustand", "mobx", "@ngrx/store", "jotai", "recoil", "@tanstack/react-query", "swr", "pinia"]),
        "http": pick(["axios", "ky", "@angular/common", "swr", "@tanstack/react-query", "graphql", "@apollo/client"]),
        "ui": pick(["tailwindcss", "@mui/material", "antd", "bootstrap", "react-bootstrap", "@angular/material", "primeng", "@chakra-ui/react", "@mantine/core", "styled-components", "sass"]),
        "forms": pick(["react-hook-form", "formik", "zod", "yup", "@angular/forms"]),
        "tests": pick(["vitest", "jest", "@playwright/test", "cypress", "karma", "jasmine-core", "@testing-library/react"]),
        "lint": pick(["eslint", "prettier", "@biomejs/biome", "stylelint"]),
    }
    internal = sorted(n for n in deps if n.startswith("@") and n[1:].split("/")[0] not in PUBLIC_NPM_SCOPES)
    version = deps.get({"nextjs": "next", "angular": "@angular/core"}.get(framework, "react"), "")
    archetype = {
        "nextjs": f"nextjs-{'app-router' if router.startswith('app') else 'pages-router'}",
        "angular": "angular-app",
        "react-vite": "react-vite-spa", "react-cra": "react-cra-spa", "react": "react-spa", "vue": "vue-app",
    }.get(framework, "frontend-generic")
    return {
        "framework": framework, "framework_version": version, "router": router,
        "typescript": "typescript" in deps or files.get(".ts", 0) + files.get(".tsx", 0) > 0,
        "package_manager": "pnpm" if (base / "pnpm-lock.yaml").exists() else ("yarn" if (base / "yarn.lock").exists() else ("npm" if (base / "package-lock.json").exists() else "unknown")),
        "scripts": pkg.get("scripts", {}), "stack": stack, "signals": dict(signals),
        "candidate_internal_packages": internal, "has_tests": bool(stack["tests"]),
        "source_files": sum(files.values()),
        "archetypes": [{"archetype": archetype, "confidence": "high" if framework != "other" else "low",
                        "evidence": f"{framework} {version} ({router} routing)"}],
    }


# --------------------------------------------------------------------------- repo-level

SECRET_KEY = re.compile(r"(password|passwd|pwd|secret|apikey|api_key|token|accesskey|privatekey|clientsecret)", re.I)


def find_config_secrets(root: Path, excludes: list[str]) -> list[dict]:
    """Report config files that hold non-empty values under secret-looking keys. Values are never returned."""
    found = []
    for p in walk(root, root, excludes):
        name = p.name.lower()
        r = rel(p, root)
        if name.startswith("appsettings") and name.endswith(".json") or name in ("secrets.json", "local.settings.json"):
            t = read(p)
            for m in re.finditer(r'"([^"]+)"\s*:\s*"([^"]*)"', t):
                if (SECRET_KEY.search(m.group(1)) or re.search(r"(?i)password\s*=\s*[^;\"]+", m.group(2))) and m.group(2).strip() not in ("", "***", "<secret>"):
                    found.append({"file": r, "key": m.group(1), "line": t.count("\n", 0, m.start()) + 1})
        elif name in ("web.config", "app.config") or name.endswith(".config") and "web" in name:
            t = read(p)
            for m in re.finditer(r'<add\s+(?:key|name)="([^"]+)"\s+(?:value|connectionString)="([^"]*)"', t):
                if (SECRET_KEY.search(m.group(1)) or re.search(r"(?i)password\s*=", m.group(2))) and m.group(2).strip():
                    found.append({"file": r, "key": m.group(1), "line": t.count("\n", 0, m.start()) + 1})
        elif name.startswith(".env") and not name.endswith((".example", ".sample", ".template")):
            for i, line in enumerate(read(p).splitlines(), 1):
                m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", line)
                if m and m.group(2).strip().strip("'\""):
                    found.append({"file": r, "key": m.group(1), "line": i})
        elif p.suffix in (".ts", ".tsx", ".js", ".jsx", ".cs", ".json") and p.stat().st_size < 1_000_000:
            t = read(p)
            for m in HARDCODED_SECRET.finditer(t):
                found.append({"file": r, "key": "(hard-coded credential pattern)", "line": t.count("\n", 0, m.start()) + 1})
    return found


def repo_level(root: Path, excludes: list[str]) -> dict:
    retired = []
    for dirpath, dirnames, _ in os.walk(root):
        d = Path(dirpath)
        depth = len(d.relative_to(root).parts)
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and depth < 3]
        for x in dirnames:
            if RETIRED_NAMES.match(x) and not is_excluded(rel(d / x, root), excludes):
                retired.append(rel(d / x, root))
    ai = [p for p in ("CLAUDE.md", ".claude", ".ai", "AGENTS.md", ".cursorrules", ".github/copilot-instructions.md") if (root / p).exists()]
    ci = [p for p in (".github/workflows", "azure-pipelines.yml", "Jenkinsfile", ".gitlab-ci.yml", "bitbucket-pipelines.yml") if (root / p).exists()]
    remote = git(root, "config", "--get", "remote.origin.url")
    host = "github" if "github.com" in remote else ("azure-devops" if "dev.azure.com" in remote or "visualstudio.com" in remote else ("gitlab" if "gitlab" in remote else ("none" if not remote else "other")))
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?/?$", remote)
    return {"retired_looking_folders": sorted(retired), "existing_ai_setup": ai, "ci": ci,
            "git": {"host": host, "repo": m.group(1) if m else "", "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD"),
                    "dirty_files": len([l for l in git(root, "status", "--porcelain").splitlines() if l.strip()])},
            "gitignore": (root / ".gitignore").exists()}


def unit_activity(root: Path, path: str) -> dict:
    last = git(root, "log", "-1", "--format=%ct", "--", path)
    n90 = git(root, "rev-list", "--count", "--since=90.days", "HEAD", "--", path)
    authors = git(root, "shortlog", "-sn", "--since=365.days", "HEAD", "--", path)
    top = [re.sub(r"^\s*\d+\s+", "", a) for a in authors.splitlines()[:3]]
    out = {"commits_90d": int(n90) if n90.isdigit() else 0, "top_committers_12m": top}
    if last.isdigit():
        dt = datetime.fromtimestamp(int(last), tz=timezone.utc)
        out["last_commit"] = dt.date().isoformat()
        out["inactive"] = (datetime.now(timezone.utc) - dt).days > 540
    return out


# --------------------------------------------------------------------------- render

def render_md(profile: dict) -> str:
    L = ["# Repository scan", "", f"Root: `{profile['root_name']}`  ·  scanned {profile['scanned_at']}  ·  scanner {profile['scanner_version']}", ""]
    g = profile["repo"]["git"]
    L += [f"Git: {g['host']} `{g['repo']}` on `{g['branch']}` ({g['dirty_files']} uncommitted files)  ·  CI: {', '.join(profile['repo']['ci']) or 'none'}  ·  existing AI setup: {', '.join(profile['repo']['existing_ai_setup']) or 'none'}", ""]
    L += ["## Units", "", "| Unit | Kind | Stack | Proposed archetype(s) | Tests | Activity |", "|---|---|---|---|---|---|"]
    for u in profile["units"]:
        a = u.get("analysis", {})
        stack = a.get("framework", "")
        if u["kind"] == "frontend":
            stack = f"{a.get('framework')} {a.get('framework_version', '')} ({a.get('router')})"
        elif u["kind"].startswith("dotnet"):
            stack = f"{a.get('framework')} · " + ", ".join(sorted({p['target'] for p in a.get('projects', []) if p['target']}))
        arch = "; ".join(f"{x['archetype']} ({x['confidence']})" for x in a.get("archetypes", []))
        act = u.get("activity", {})
        L.append(f"| `{u['path']}` | {u['kind']} | {stack} | {arch} | {'yes' if a.get('has_tests') else 'no'} | "
                 f"{act.get('commits_90d', 0)} commits/90d, last {act.get('last_commit', '?')}{' **inactive**' if act.get('inactive') else ''} |")
    L += ["", "## Evidence per unit", ""]
    for u in profile["units"]:
        a = u.get("analysis", {})
        L.append(f"### `{u['path']}`")
        for x in a.get("archetypes", []):
            L.append(f"- {x['archetype']}: {x['evidence']}")
        if a.get("signals"):
            L.append("- signals: " + ", ".join(f"{k}={v}" for k, v in sorted(a["signals"].items())))
        if a.get("stack"):
            L.append("- stack: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in a["stack"].items() if v))
        if a.get("candidate_internal_packages"):
            L.append("- possible in-house packages: " + ", ".join(a["candidate_internal_packages"][:20]))
        if a.get("unsafe_sql_fragments"):
            L.append(f"- SQL built from values: {a['unsafe_sql_fragments']} fragments")
        L.append("")
    r = profile["repo"]
    L += ["## Suggested exclusions", ""]
    sugg = sorted(set(r["retired_looking_folders"] + [u["path"] for u in profile["units"] if u.get("activity", {}).get("inactive")]))
    sugg = [x for x in sugg if not any(x.startswith(y + "/") for y in sugg)]  # keep the top-most folder only
    L += [f"- `{x}`" for x in sugg] or ["- none"]
    L += ["", "## Risks", ""]
    if profile["config_secrets"]:
        by = defaultdict(list)
        for s in profile["config_secrets"]:
            by[s["file"]].append(f"{s['key']} (line {s['line']})")
        L += [f"- `{f}`: secret-looking values under {', '.join(v[:6])}{' …' if len(v) > 6 else ''}" for f, v in sorted(by.items())]
    else:
        L.append("- no secret-looking values found in config files")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", help="output folder (default <root>/.ai/kit)")
    ap.add_argument("--exclude", action="append", default=[], help="repo-relative folder to skip (repeatable)")
    ap.add_argument("--stdout", action="store_true", help="print the markdown summary instead of only writing files")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    excludes = [e.replace("\\", "/").strip("/") for e in a.exclude]
    ex_file = root / ".ai" / "exclude-paths.txt"
    if ex_file.exists():
        excludes += [l.split("#", 1)[0].strip().replace("\\", "/").strip("/") for l in read(ex_file).splitlines() if l.split("#", 1)[0].strip()]

    units = discover_units(root, excludes)
    for u in units:
        if u["kind"].startswith("dotnet"):
            u["analysis"] = analyse_dotnet(root, u, excludes)
        elif u["kind"] == "frontend":
            u["analysis"] = analyse_frontend(root, u, excludes)
        u["activity"] = unit_activity(root, u["path"])
    profile = {
        "scanner_version": "1.0.0", "root_name": root.name,
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "excludes": excludes, "units": units, "repo": repo_level(root, excludes),
        "config_secrets": find_config_secrets(root, excludes),
    }
    out = Path(a.out) if a.out else root / ".ai" / "kit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "scan.json").write_text(json.dumps(profile, indent=1), encoding="utf-8")
    md = render_md(profile)
    (out / "scan.md").write_text(md, encoding="utf-8")
    if a.stdout:
        print(md)
    else:
        print(f"Scanned {len(units)} unit(s). Wrote {rel(out / 'scan.md', root) if str(out).startswith(str(root)) else out / 'scan.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
