param([string]$Configuration = (Join-Path $PSScriptRoot 'config\chat.local.json'))
$ErrorActionPreference = 'Stop'
$chatSecret = $null
$chatBstr = [IntPtr]::Zero
$chatOwnsKey = $false
$chatExit = 1
try {
    $chatConfig = Get-Content -LiteralPath $Configuration -Raw | ConvertFrom-Json
    if ($chatConfig.schema_version -ne 1) { throw 'Unsupported connection configuration.' }
    if (-not (Test-Path -LiteralPath $chatConfig.client -PathType Leaf)) { throw 'Install the official tunnel client and configure its verified path.' }
    if ((Get-FileHash -LiteralPath $chatConfig.client -Algorithm SHA256).Hash.ToLowerInvariant() -ne $chatConfig.client_sha256) { throw 'Tunnel client integrity check failed.' }
    if (Test-Path -LiteralPath $chatConfig.pid_file) {
        $chatPreviousId = [int](Get-Content -LiteralPath $chatConfig.pid_file -Raw).Trim()
        if (Get-Process -Id $chatPreviousId -ErrorAction SilentlyContinue) { throw 'A previous connection process is still running. Stop it before starting another.' }
    }
    if ($env:CONTROL_PLANE_API_KEY) { throw 'Start this launcher in a fresh PowerShell process without a preexisting tunnel key.' }
    $Host.UI.RawUI.WindowTitle = 'OpenSci Study Chat - secure connection'
    Write-Host 'Private single-study connection. The computer and this window must stay on.'
    Write-Host 'Paste a valid restricted Tunnels Read + Use key below. It is never saved to disk.'
    Write-Host 'Closing this window disconnects Chat; saved study progress remains on disk.'
    $chatSecret = Read-Host 'Restricted tunnel key' -AsSecureString
    if ($chatSecret.Length -eq 0) { throw 'A key is required.' }
    $chatBstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($chatSecret)
    $env:CONTROL_PLANE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($chatBstr)
    $chatOwnsKey = $true
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($chatBstr)
    $chatBstr = [IntPtr]::Zero
    $chatSecret.Dispose(); $chatSecret = $null
    & $chatConfig.client run --profile-file $chatConfig.profile --control-plane.organization-id $chatConfig.organization_id --control-plane.poll-channel main --mcp.stdio-send-initialized-notification --health.url-file $chatConfig.health_file --pid.file $chatConfig.pid_file --log.file $chatConfig.log_file
    $chatExit = $LASTEXITCODE
} catch {
    # Runtime errors may include secrets: give a bounded message, not raw exceptions.
    Write-Host 'The connection could not start or has stopped. Check the local configuration, existing process, client integrity and key expiry.'
    $chatExit = 1
} finally {
    if ($chatBstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($chatBstr) }
    if ($null -ne $chatSecret) { $chatSecret.Dispose() }
    if ($chatOwnsKey) { Remove-Item Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue }
}
exit $chatExit
