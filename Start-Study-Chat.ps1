param([string]$Configuration=(Join-Path $PSScriptRoot 'config\chat.local.json'),[switch]$Worker)
$ErrorActionPreference='Stop'
$key=$null
try {
    Import-Module (Join-Path $PSScriptRoot 'scripts\StudyConnection.psm1') -Force
    $context=Get-ConnectionContext $Configuration
    if ($Worker) { Invoke-ConnectionWorker $context }
    elseif ((Get-ConnectionStatus $context).stored_key) {
        Start-ConnectionBackground $context $PSScriptRoot
        Write-Host 'Background connection requested. This window can close. Use Manage-Study-Connection.cmd to check readiness or stop.'
    } else {
        Write-Host 'One-time connection: keep this window open. Saved Study records remain on disk after disconnecting.'
        Write-Host 'For encrypted key storage and background connection, open Manage-Study-Connection.cmd.'
        $key=Read-Host 'Restricted Tunnels Read + Use key' -AsSecureString
        Invoke-ConnectionWorker $context $key
    }
} catch {
    Write-Host 'Connection unavailable. Check configuration, client integrity, existing process, stored-key identity and key expiry.'
    exit 1
} finally { if ($null -ne $key) { $key.Dispose() } }
