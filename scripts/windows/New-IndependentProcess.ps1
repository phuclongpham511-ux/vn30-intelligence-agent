param([Parameter(Mandatory)][string]$RequestFile)
$ErrorActionPreference='Stop'
if(-not $IsWindows){throw 'Windows is required'}
$request=Get-Content -LiteralPath $RequestFile -Raw|ConvertFrom-Json
$properties=@{
    ShowWindow=[uint16]0
    # Microsoft documents WMI provider-job limits unless this creation flag is
    # selected. It changes only the NEW process, never any existing Codex job.
    CreateFlags=[uint32]0x01000000
}
if($request.environment){$properties.EnvironmentVariables=[string[]]$request.environment}
$startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property $properties
# WMI creates this under Windows management, not as a child of the calling job.
# No elevation, existing-job mutation or task registration. Failure is final;
# never fall back to an attached launch that silently loses independence.
$result=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine=[string]$request.command_line
    CurrentDirectory=[string]$request.directory
    ProcessStartupInformation=$startup
}
if($result.ReturnValue -ne 0){throw ('WMI creation failed: '+$result.ReturnValue)}
@{launch_pid=$result.ProcessId}|ConvertTo-Json -Compress
