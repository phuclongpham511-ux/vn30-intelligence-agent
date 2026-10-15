param(
    [ValidateSet('Backend','Frontend','Collector')][string]$Role = 'Backend',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$runtimeRoot = Split-Path -Parent $PSScriptRoot
$runtimeConfig = Get-Content -LiteralPath (Join-Path $runtimeRoot 'config\runtime.json') -Raw | ConvertFrom-Json
$sourcePath = $runtimeConfig.source_checkout
$actualHead = (& git -C $sourcePath rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actualHead -ne $runtimeConfig.canonical_sha) { throw 'Runtime SHA does not match the pinned release' }
$secretPath = $runtimeConfig.secret_configuration
$pythonPath = Join-Path $sourcePath '.venv\Scripts\python.exe'
$credentialHelper = Join-Path $PSScriptRoot 'ssi_configuration.py'
$credentialCheck = & $pythonPath -B $credentialHelper --mode check
$credentialExit = $LASTEXITCODE
$credentialMetadata = $credentialCheck | ConvertFrom-Json
$secretReady = ($credentialExit -eq 0) -and ($credentialMetadata.runtime_recognizes_credentials -eq $true)
$databaseExists = Test-Path -LiteralPath $runtimeConfig.product_database
$gatePath = Join-Path $runtimeRoot 'state\cutover-ready.json'
$gateReady = $false
if (Test-Path -LiteralPath $gatePath) {
    $gate = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json
    $gateReady = ($gate.canonical_sha -eq $actualHead) -and ($gate.database_path -eq $runtimeConfig.product_database) -and
                 ($gate.old_writers_exited -eq $true) -and ($gate.final_backup_verified -eq $true) -and ($gate.live_launch_authorized -eq $true)
}
if ($CheckOnly) {
    [pscustomobject]@{SHA=$actualHead; SecretConfigured=$secretReady; ProductDatabaseExists=$databaseExists; CutoverGate=$gateReady; Ready=($secretReady -and $databaseExists -and $gateReady)} | ConvertTo-Json
    return
}
if (-not ($secretReady -and $databaseExists -and $gateReady)) { throw 'Cutover prerequisites are incomplete. Run -CheckOnly and consult CUTOVER.md. No process was started.' }
if ($Role -eq 'Collector') {
    $legacyCollectors = Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('uv.exe','python.exe','pythonw.exe') -and $_.CommandLine -match 'scripts\.ingest_news' }
    if ($legacyCollectors) { throw 'A legacy News collector still exists. Do not overlap ownership.' }
}
$rolePort = if ($Role -eq 'Backend') { $runtimeConfig.backend_port } elseif ($Role -eq 'Frontend') { $runtimeConfig.frontend_port } else { $null }
if ($rolePort -and (Get-NetTCPConnection -State Listen -LocalPort $rolePort -ErrorAction SilentlyContinue)) { throw "Port $rolePort already has an owner" }
$env:DATABASE_URL = 'sqlite:///' + $runtimeConfig.product_database.Replace('\','/')
$env:APP_ENV = 'production'
$env:MARKET_DATA_PROVIDER = 'ssi'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:NEXT_TELEMETRY_DISABLED = '1'
Push-Location -LiteralPath $sourcePath
try {
    if ($Role -eq 'Backend') { & $pythonPath -B $credentialHelper --mode backend }
    elseif ($Role -eq 'Collector') { & $pythonPath -B $credentialHelper --mode collector }
    else {
        $env:BACKEND_URL = 'http://127.0.0.1:' + $runtimeConfig.backend_port
        Push-Location frontend
        try { & npm run start -- --port $runtimeConfig.frontend_port } finally { Pop-Location }
    }
    if ($LASTEXITCODE -ne 0) { throw "Role $Role exited with code $LASTEXITCODE" }
} finally { Pop-Location }
