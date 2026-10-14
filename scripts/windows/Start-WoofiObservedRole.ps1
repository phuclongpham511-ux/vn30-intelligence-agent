param(
    [Parameter(Mandatory)][ValidateSet('Backend','Frontend','Collector')][string]$Role,
    [Parameter(Mandatory)][string]$RuntimeRoot
)
$ErrorActionPreference='Stop'
if(-not $IsWindows){throw 'This manual launcher requires Windows'}
$root=(Resolve-Path -LiteralPath $RuntimeRoot).Path
$launcher=Join-Path $root 'launch\Invoke-Woofi.ps1'
$config=Get-Content -LiteralPath (Join-Path $root 'config\runtime.json') -Raw|ConvertFrom-Json
$gate=& $launcher -CheckOnly|ConvertFrom-Json
if(-not $gate.Ready){throw 'Canonical launch gate is not ready'}
if($Role -eq 'Collector'){
    $workers=@(Get-CimInstance Win32_Process|Where-Object {
        $_.Name -in @('python.exe','pythonw.exe') -and
        $_.CommandLine -match '(?i)\s-m\s+scripts\.ingest_(data|news)(?:\s|$)'
    })
    if($workers.Count){throw 'Acquisition worker exists; manual launch refused'}
}else{
    $port=if($Role -eq 'Backend'){$config.backend_port}else{$config.frontend_port}
    if(@(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue).Count){
        throw 'Role port already has an owner; manual launch refused'
    }
}
$id=[datetime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')+'-'+[guid]::NewGuid().ToString('N')
$run=Join-Path $root ('state\observed-role-runs\'+$id)
$null=New-Item -ItemType Directory -Path $run
$observer=Join-Path $PSScriptRoot 'Invoke-WoofiObservedRole.ps1'
# No scheduler, watchdog, elevation, job breakaway or automatic restart.
$arguments='-NoProfile -File "'+$observer+'" -Role '+$Role+' -RuntimeRoot "'+$root+'" -RunDirectory "'+$run+'"'
$process=Start-Process -FilePath (Get-Command pwsh.exe).Source -ArgumentList $arguments -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $run 'stdout.log') -RedirectStandardError (Join-Path $run 'stderr.log')
[ordered]@{role=$Role;observer_pid=$process.Id;run_directory=$run}|ConvertTo-Json -Compress
