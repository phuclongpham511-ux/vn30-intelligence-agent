# Offline local certificate setup only. Never accesses Groq or an account key.
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'Requires Windows with PowerShell 7 and modern .NET.'
}
if ($PSVersionTable.PSVersion.Major -lt 7) {
    # Windows PowerShell 5.1 has neither $IsWindows nor the required PEM APIs.
    # Delegate before using modern .NET; preserve the output path and security checks.
    $modernShell = Get-Command pwsh.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    $candidates = @()
    if ($null -ne $modernShell) { $candidates += $modernShell.Source }
    $candidates += (Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'PowerShell\7\pwsh.exe')
    $candidates += (Join-Path ([Environment]::GetFolderPath('UserProfile')) '.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            if ($OutputDirectory.Contains('"')) { throw 'Invalid output directory.' }
            $childArguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',
                ('"' + $PSCommandPath + '"'),'-OutputDirectory',('"' + $OutputDirectory + '"'))
            $child = Start-Process -FilePath $candidate -ArgumentList $childArguments -NoNewWindow -Wait -PassThru
            if ($child.ExitCode -ne 0) { throw 'PowerShell 7 TLS preparation failed; existing files were not replaced.' }
            return
        }
    }
    throw 'PowerShell 7 was not found. Install or select an approved PowerShell 7 runtime; TLS was not weakened.'
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
$repoPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
if ($outputPath.Equals($repoPath, [StringComparison]::OrdinalIgnoreCase) -or
    $outputPath.StartsWith($repoPath.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'TLS credentials must be outside the repository.'
}
if (Test-Path -LiteralPath $outputPath) { throw 'Choose a new private output directory; nothing will be overwritten.' }
[IO.Directory]::CreateDirectory($outputPath) | Out-Null
$acl = Get-Acl -LiteralPath $outputPath
$acl.SetAccessRuleProtection($true, $false)
$userSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
foreach ($sid in @($userSid, $systemSid)) {
    $rule = [Security.AccessControl.FileSystemAccessRule]::new(
        $sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
    $acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $outputPath -AclObject $acl
$caKey = $serverKey = $ca = $server = $null
try {
    $now = [DateTimeOffset]::UtcNow
    $caKey = [Security.Cryptography.RSA]::Create(3072)
    $caRequest = [Security.Cryptography.X509Certificates.CertificateRequest]::new(
        'CN=Woofi Local Trial CA', $caKey, [Security.Cryptography.HashAlgorithmName]::SHA256,
        [Security.Cryptography.RSASignaturePadding]::Pkcs1)
    $caRequest.CertificateExtensions.Add(
        [Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]::new($true,$false,0,$true))
    $caRequest.CertificateExtensions.Add(
        [Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new(
            ([Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyCertSign -bor
             [Security.Cryptography.X509Certificates.X509KeyUsageFlags]::CrlSign), $true))
    $ca = $caRequest.CreateSelfSigned($now.AddMinutes(-5), $now.AddDays(2))
    $serverKey = [Security.Cryptography.RSA]::Create(3072)
    $serverRequest = [Security.Cryptography.X509Certificates.CertificateRequest]::new(
        'CN=127.0.0.1', $serverKey, [Security.Cryptography.HashAlgorithmName]::SHA256,
        [Security.Cryptography.RSASignaturePadding]::Pkcs1)
    $san = [Security.Cryptography.X509Certificates.SubjectAlternativeNameBuilder]::new()
    $san.AddIpAddress([Net.IPAddress]::Loopback)
    $san.AddDnsName('localhost')
    $serverRequest.CertificateExtensions.Add($san.Build())
    $serverRequest.CertificateExtensions.Add(
        [Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]::new($false,$false,0,$true))
    $serverRequest.CertificateExtensions.Add(
        [Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new(
            ([Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature -bor
             [Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyEncipherment), $true))
    $purposes = [Security.Cryptography.OidCollection]::new()
    $purposes.Add([Security.Cryptography.Oid]::new('1.3.6.1.5.5.7.3.1')) | Out-Null
    $serverRequest.CertificateExtensions.Add(
        [Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($purposes,$true))
    $serial = [Security.Cryptography.RandomNumberGenerator]::GetBytes(16)
    $serial[0] = $serial[0] -band 0x7f
    $server = $serverRequest.Create($ca, $now.AddMinutes(-5), $now.AddDays(1), $serial)
    $utf8 = [Text.UTF8Encoding]::new($false)
    [IO.File]::WriteAllText((Join-Path $outputPath 'loopback-ca.pem'), $ca.ExportCertificatePem(), $utf8)
    [IO.File]::WriteAllText((Join-Path $outputPath 'loopback-cert.pem'), $server.ExportCertificatePem(), $utf8)
    [IO.File]::WriteAllText((Join-Path $outputPath 'loopback-key.pem'), $serverKey.ExportRSAPrivateKeyPem(), $utf8)
    [PSCustomObject]@{PowerShellVersion=$PSVersionTable.PSVersion.ToString();Ca=(Join-Path $outputPath 'loopback-ca.pem');
        Certificate=(Join-Path $outputPath 'loopback-cert.pem');
        PrivateKey=(Join-Path $outputPath 'loopback-key.pem');
        ServerExpiresUtc=$server.NotAfter.ToUniversalTime().ToString('o')} | ConvertTo-Json
}
finally {
    foreach ($item in @($server,$ca,$serverKey,$caKey)) { if ($null -ne $item) { $item.Dispose() } }
}
