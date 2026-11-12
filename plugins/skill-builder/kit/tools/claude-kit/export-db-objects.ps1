<#
.SYNOPSIS
  Exports the SQL Server objects a solution uses (procs, views, functions, table columns)
  into <solution>/db/ so Claude and reviewers can read them next to the code.

.DESCRIPTION
  Reads <solution>/.ai/generated/db-objects.json (written by docgen.py) to find which
  objects the code touches, then reads their definitions from SQL Server.

  - Objects written as Db.dbo.Name are read from that database.
  - Objects written without a database are read from the database behind the handler's
    connection string key, using <solution>/.ai/db-map.json, for example:
        { "PreSaleConnectionString": "Presale", "WorkshopConnectionString": "TSWorkshop" }
    db-map.json holds database NAMES only and is safe to commit. Never put connection
    strings or passwords in it.
  - Databases listed in "_ignore_databases" (in db-map.json) are skipped, e.g. databases that
    no longer exist but are still referenced by old code:
        { "_ignore_databases": ["DCES"], "Constring": "Presale" }

  Use a READ-ONLY login (db_datareader + VIEW DEFINITION). The script only runs SELECTs.
  Works in Windows PowerShell 5.1 and PowerShell 7 with no extra modules.

.EXAMPLE
  # SQL Server on a remote Linux host, SQL authentication, self-signed certificate
  .\tools\claude-kit\export-db-objects.ps1 -Solution net10_services\MyService -Server 10.0.0.25 -Port 1433 -SqlUser docs_reader -TrustServerCertificate
.EXAMPLE
  # Windows authentication, default instance
  .\tools\claude-kit\export-db-objects.ps1 -Solution MyApi -Server DEVSQL01
.EXAMPLE
  # Non-interactive (CI or scheduled): password from an environment variable instead of a prompt
  $env:KIT_SQL_PASSWORD = '...'; .\tools\claude-kit\export-db-objects.ps1 -Solution MyApi -Server sql.internal -SqlUser docs_reader -TrustServerCertificate
#>
param(
    [Parameter(Mandatory = $true)] [string] $Solution,
    [Parameter(Mandatory = $true)] [string] $Server,   # host name or IP of the SQL Server (Linux or Windows)
    [int] $Port = 0,                         # 0 = default (1433 / SQL Browser); set it for a non-default port
    [string] $SqlUser,                       # SQL authentication login; omit to use Windows authentication
    [switch] $TrustServerCertificate,        # encrypt but accept the server's self-signed certificate (default on Linux installs)
    [int] $TimeoutSeconds = 15,
    [string] $RepoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
)

$ErrorActionPreference = 'Stop'
$solDir = Join-Path $RepoRoot $Solution
if (-not (Test-Path $solDir)) {
    $hint = (Get-ChildItem $RepoRoot -Recurse -Filter "$(Split-Path $Solution -Leaf).slnx" -ErrorAction SilentlyContinue | Select-Object -First 1)
    $msg = "Solution folder not found: $solDir."
    if ($hint) { $msg += " Did you mean -Solution $($hint.Directory.FullName.Substring($RepoRoot.Length).TrimStart('\','/')) ?" }
    throw $msg
}
$objectsPath = Join-Path $solDir '.ai/generated/db-objects.json'
if (-not (Test-Path $objectsPath)) { throw "Run 'python tools/claude-kit/docgen.py' first: $objectsPath not found." }
# PowerShell 5.1 emits a JSON array as one object; piping through ForEach-Object unrolls it in 5.1 and 7
$objects = @((Get-Content $objectsPath -Raw -Encoding UTF8 | ConvertFrom-Json) | ForEach-Object { $_ })

$dbMap = @{}
$ignoreDbs = @()
$dbMapPath = Join-Path $solDir '.ai/db-map.json'
if (Test-Path $dbMapPath) {
    (Get-Content $dbMapPath -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object {
        if ($_.Name -eq '_ignore_databases') { $ignoreDbs = @($_.Value) }
        elseif (-not $_.Name.StartsWith('_')) { $dbMap[$_.Name] = $_.Value }
    }
}
$ignored = New-Object System.Collections.Generic.List[string]

$password = $null
if ($SqlUser) {
    if ($env:KIT_SQL_PASSWORD) {
        $password = $env:KIT_SQL_PASSWORD
    }
    else {
        $sec = Read-Host -AsSecureString "Password for $SqlUser"
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
        try { $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    }
}
$dataSource = if ($Port -gt 0) { "$Server,$Port" } else { $Server }

function Get-Connection([string] $database) {
    $b = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
    $b['Data Source'] = $dataSource
    $b['Initial Catalog'] = $database
    $b['Application Name'] = 'claude-kit-export'
    $b['Connect Timeout'] = $TimeoutSeconds
    if ($TrustServerCertificate) { $b['Encrypt'] = $true; $b['TrustServerCertificate'] = $true }
    if ($SqlUser) { $b['User ID'] = $SqlUser; $b['Password'] = $password } else { $b['Integrated Security'] = $true }
    $c = New-Object System.Data.SqlClient.SqlConnection $b.ConnectionString
    $c.Open()
    return $c
}

function Invoke-Select($conn, [string] $sql, [hashtable] $params) {
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = $sql
    foreach ($k in $params.Keys) { [void]$cmd.Parameters.AddWithValue($k, $params[$k]) }
    $t = New-Object System.Data.DataTable
    $t.Load($cmd.ExecuteReader())
    return , $t
}

# Collect (database, schema, name) for every object the code references
$targets = @{}
function Add-Target([string] $raw, [string] $connKey) {
    $parts = ($raw -replace '[\[\]]', '').Split('.')
    switch ($parts.Count) {
        3 { $db = $parts[0]; $schema = $parts[1]; $name = $parts[2] }
        2 { $db = $dbMap[$connKey]; $schema = $parts[0]; $name = $parts[1] }
        default { $db = $dbMap[$connKey]; $schema = 'dbo'; $name = $parts[0] }
    }
    if (-not $db) { Write-Warning "No database for '$raw' (connection key '$connKey'). Add it to .ai/db-map.json."; return }
    if ($ignoreDbs -contains $db) { $ignored.Add("$db.$schema.$name"); return }
    $targets["$db|$schema|$name".ToLowerInvariant()] = "$db|$schema|$name"   # SQL names are case-insensitive
}
foreach ($o in $objects) { if ($o.object) { Add-Target ([string]$o.object) ([string]$o.connection) } }

# Fail fast with a clear message if the server is unreachable or the login is wrong
try { $probe = Get-Connection 'master'; $probe.Close(); Write-Host "Connected to $dataSource as $(if ($SqlUser) { $SqlUser } else { 'Windows user' })." }
catch { throw "Cannot connect to $dataSource : $($_.Exception.Message)" }

$outRoot = Join-Path $solDir 'db'
$byDb = $targets.Values | Group-Object { $_.Split('|')[0] }
$missing = New-Object System.Collections.Generic.List[string]
foreach ($g in $byDb) {
    $db = $g.Name
    try { $conn = Get-Connection $db } catch { Write-Warning "Cannot open database $db : $($_.Exception.Message)"; continue }
    try {
        foreach ($key in ($g.Group | Sort-Object)) {
            $null, $schema, $name = $key.Split('|')
            $info = Invoke-Select $conn @"
SELECT o.type_desc, OBJECT_DEFINITION(o.object_id) AS def
FROM sys.objects o JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE s.name = @schema AND o.name = @name
"@ @{ '@schema' = $schema; '@name' = $name }
            if ($info.Rows.Count -eq 0) {
                # synonyms and objects in other databases are reported, not followed
                $missing.Add("$db.$schema.$name"); continue
            }
            $type = [string]$info.Rows[0].type_desc
            $dir = Join-Path $outRoot $db
            if ($type -eq 'USER_TABLE') {
                $cols = Invoke-Select $conn @"
SELECT c.name, t.name AS type, c.max_length, c.is_nullable, c.is_identity
FROM sys.columns c JOIN sys.types t ON t.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(QUOTENAME(@schema) + '.' + QUOTENAME(@name))
ORDER BY c.column_id
"@ @{ '@schema' = $schema; '@name' = $name }
                $lines = @("# $db.$schema.$name (table)", '', '| Column | Type | Max length | Nullable | Identity |', '|---|---|---|---|---|')
                foreach ($r in $cols.Rows) { $lines += "| $($r.name) | $($r.type) | $($r.max_length) | $($r.is_nullable) | $($r.is_identity) |" }
                $file = Join-Path (Join-Path $dir 'tables') "$schema.$name.md"
                New-Item -ItemType Directory -Force -Path (Split-Path $file) | Out-Null
                Set-Content -Path $file -Value ($lines -join "`n") -Encoding UTF8
            }
            else {
                $sub = switch -Wildcard ($type) { '*PROCEDURE*' { 'procs' } '*VIEW*' { 'views' } '*FUNCTION*' { 'functions' } default { 'other' } }
                $file = Join-Path (Join-Path $dir $sub) "$schema.$name.sql"
                New-Item -ItemType Directory -Force -Path (Split-Path $file) | Out-Null
                Set-Content -Path $file -Value ([string]$info.Rows[0].def) -Encoding UTF8
            }
        }
    }
    finally { $conn.Close() }
}
if ($ignored.Count) {
    Write-Host "Skipped $($ignored.Count) object(s) in ignored databases ($($ignoreDbs -join ', ')): $(($ignored | Sort-Object) -join ', ')"
}
if ($missing.Count) {
    $report = Join-Path $outRoot 'NOT-FOUND.md'
    Set-Content $report -Encoding UTF8 -Value (@('# Objects referenced in code but not found', '', 'Synonyms, cross-server objects, temp tables or dead references. Check each one.', '') + ($missing | Sort-Object | ForEach-Object { "- $_" }))
    Write-Warning "$($missing.Count) objects not found; see $report"
}
Write-Host "Exported $($targets.Count) objects for $Solution into $outRoot"
