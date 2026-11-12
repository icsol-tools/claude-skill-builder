<#
.SYNOPSIS
  Creates a new service (solution) from a claude-kit template (Icsol CQS API).

.DESCRIPTION
  Copies tools/templates/<Template>/__SOLUTION__ to <Folder>/<Name>, renames files and folders,
  and fills in the placeholders (name, purpose, local port, user-secrets id, date).
  It never overwrites: it stops if the target folder already exists.
  Works in Windows PowerShell 5.1 and PowerShell 7. Normally run by the {{PREFIX}}-new-service skill.

.EXAMPLE
  .\tools\claude-kit\templates\new-service.ps1 -Name Gain.Flipkart.Integration -Purpose "Receives Flipkart vehicle bookings and creates DMS bookings."
.EXAMPLE
  .\tools\claude-kit\templates\new-service.ps1 -Name Gain.Warranty.API -Folder net10_services -Port 5240 -Purpose "Warranty claims API for the dealer app."
#>
param(
    [Parameter(Mandatory = $true)] [string] $Name,
    [Parameter(Mandatory = $true)] [string] $Purpose,
    [string] $Folder = 'net10_services',
    [string] $Template = 'a1-api',
    [int] $Port = 0,
    [string] $RepoRoot = (Resolve-Path "$PSScriptRoot/../../..").Path
)
$ErrorActionPreference = 'Stop'

if ($Name -notmatch '^[A-Z][A-Za-z0-9]*(\.[A-Z][A-Za-z0-9]*)+$') {
    throw "Name '$Name' must be dotted PascalCase, e.g. Gain.Warranty.API (letters and digits only)."
}
if ($Purpose -match '["`$]') { throw "Purpose must not contain quotes, backticks or dollar signs." }

$templateDir = Join-Path $PSScriptRoot "$Template/__SOLUTION__"
if (-not (Test-Path $templateDir)) { throw "Template not found: $templateDir" }
$target = Join-Path (Join-Path $RepoRoot $Folder) $Name
if (Test-Path $target) { throw "Target already exists: $target. Choose another name or remove the folder." }

# pick a free local port: not used by any launchSettings.json in the repo
if ($Port -eq 0) {
    $used = @{}
    Get-ChildItem $RepoRoot -Recurse -Filter launchSettings.json -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '[\\/](bin|obj|templates)[\\/]' } |
        ForEach-Object { foreach ($m in [regex]::Matches((Get-Content $_.FullName -Raw), 'localhost:(\d+)')) { $used[[int]$m.Groups[1].Value] = $true } }
    $Port = 5100
    while ($used.ContainsKey($Port)) { $Port++ }
}

# Project prefix: Gain.Warranty.API -> projects Gain.Warranty.API + Gain.Warranty.CQS (house convention)
$prefix = if ($Name.EndsWith('.API')) { $Name.Substring(0, $Name.Length - 4) } else { $Name }

$tokens = [ordered]@{
    '__SOLUTION__'      = $Name
    '__PREFIX__'        = $prefix
    '__PURPOSE__'       = $Purpose
    '__PORT__'          = [string]$Port
    '__USERSECRETSID__' = [guid]::NewGuid().ToString()
    '__DATE__'          = (Get-Date -Format 'yyyy-MM-dd')
}
$textExt = '.cs', '.csproj', '.json', '.md', '.yaml', '.yml', '.config', '.slnx', '.template', '.gitignore', '.txt'
$utf8 = New-Object System.Text.UTF8Encoding($false)

New-Item -ItemType Directory -Path $target -Force | Out-Null
$files = Get-ChildItem $templateDir -Recurse -File -Force
foreach ($f in $files) {
    $relative = $f.FullName.Substring($templateDir.Length).TrimStart('\', '/')
    $relative = $relative.Replace('__SOLUTION__', $Name).Replace('__PREFIX__', $prefix)
    if ($relative.EndsWith('.slnx.template')) { $relative = $relative.Substring(0, $relative.Length - '.template'.Length) }
    $dest = Join-Path $target $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
    if ($textExt -contains $f.Extension -or $f.Name -eq '.gitignore') {
        $text = [IO.File]::ReadAllText($f.FullName)
        foreach ($k in $tokens.Keys) { $text = $text.Replace($k, $tokens[$k]) }
        [IO.File]::WriteAllText($dest, $text, $utf8)
    }
    else {
        Copy-Item $f.FullName $dest
    }
}

$left = @(Get-ChildItem $target -Recurse -File -Force | Select-String -Pattern '__[A-Z]+__' -CaseSensitive -List)
if ($left.Count) { Write-Warning "Unreplaced placeholders in: $(($left | ForEach-Object { $_.Path.Substring($target.Length) }) -join ', ')" }

$relTarget = $target.Substring($RepoRoot.Length).TrimStart('\', '/')
Write-Host "Created $relTarget from template '$Template': projects $prefix.API and $prefix.CQS, local port $Port."
Write-Host ""
Write-Host "Next:"
Write-Host "  dotnet build `"$relTarget\$Name.slnx`" -c Release"
Write-Host "  dotnet user-secrets set `"ConnectionStrings:CommonConnectionString`" `"<dev connection string>`" --project `"$relTarget\$prefix.API`""
Write-Host "  dotnet user-secrets set `"Security:ApiKeys:0`" `"<local key>`" --project `"$relTarget\$prefix.API`""
Write-Host "  python tools\claude-kit\docgen.py"
