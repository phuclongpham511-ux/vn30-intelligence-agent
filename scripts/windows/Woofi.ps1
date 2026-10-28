param(
    [Parameter(Mandatory)][ValidateSet('Start','Stop','Status','Resume')][string]$Action,
    [string]$RuntimeRoot='C:\Users\PC\WoofiRuntime'
)
$ErrorActionPreference='Stop'
if(-not $IsWindows){throw 'Windows is required'}
$root=(Resolve-Path -LiteralPath $RuntimeRoot).Path
$config=Get-Content -LiteralPath (Join-Path $root 'config\runtime.json') -Raw|ConvertFrom-Json
$python=Join-Path $config.source_checkout '.venv\Scripts\python.exe'
& $python -B (Join-Path $PSScriptRoot 'runtime_supervisor.py') $Action.ToLowerInvariant() --runtime $root --pwsh (Get-Command pwsh.exe).Source
exit $LASTEXITCODE
