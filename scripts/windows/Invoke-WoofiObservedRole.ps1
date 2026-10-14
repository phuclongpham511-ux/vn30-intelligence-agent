param(
    [Parameter(Mandatory)][ValidateSet('Backend','Frontend','Collector')][string]$Role,
    [Parameter(Mandatory)][string]$RuntimeRoot,
    [Parameter(Mandatory)][string]$RunDirectory
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path -LiteralPath $RuntimeRoot).Path
$run=(Resolve-Path -LiteralPath $RunDirectory).Path
$allowed=Join-Path $root 'state\observed-role-runs'
if(-not $run.StartsWith($allowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){
    throw 'Receipt directory must be inside the runtime observed-role-runs directory'
}
if((Test-Path -LiteralPath (Join-Path $run 'started.json')) -or (Test-Path -LiteralPath (Join-Path $run 'exit.json'))){
    throw 'Existing role receipts must not be overwritten'
}
$config=Get-Content -LiteralPath (Join-Path $root 'config\runtime.json') -Raw|ConvertFrom-Json
$started=[datetime]::UtcNow
$record=[ordered]@{role=$Role;observer_pid=$PID;started_at_utc=$started.ToString('o');
    sha=$config.canonical_sha;source=$config.source_checkout;database=$config.product_database;
    job_membership='UNKNOWN';console_present=$null;credentials_copied=$false}
if($IsWindows){
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class WoofiLocalSessionProbe {
 [DllImport("kernel32.dll")] public static extern IntPtr GetCurrentProcess();
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool member);
 [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
}
'@
    $member=$false
    if([WoofiLocalSessionProbe]::IsProcessInJob([WoofiLocalSessionProbe]::GetCurrentProcess(),[IntPtr]::Zero,[ref]$member)){
        $record.job_membership=$member
    }
    $record.console_present=([WoofiLocalSessionProbe]::GetConsoleWindow() -ne [IntPtr]::Zero)
}
$record|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $run 'started.json') -Encoding utf8
$code=1;$errorType=$null
try{
    # Unchanged canonical launcher still owns credentials, pin/gate and port checks;
    # unchanged collector obtains its database-scoped OS mutex.
    & (Join-Path $root 'launch\Invoke-Woofi.ps1') -Role $Role
    $code=if($null -ne $LASTEXITCODE){[int]$LASTEXITCODE}else{0}
}catch{
    $errorType=$_.Exception.GetType().Name
    $code=if($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0){[int]$LASTEXITCODE}else{1}
}finally{
    [ordered]@{role=$Role;observer_pid=$PID;started_at_utc=$started.ToString('o');
        exited_at_utc=[datetime]::UtcNow.ToString('o');exit_code=$code;error_type=$errorType;
        auto_restart=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $run 'exit.json') -Encoding utf8
}
exit $code
