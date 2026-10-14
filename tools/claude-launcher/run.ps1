#Requires -Version 7.0
# No param block: preserve CLI flags and empty argument boundaries verbatim.
$ErrorActionPreference = 'Stop'
try {
    Import-Module (Join-Path $PSScriptRoot 'Launcher.psm1') -Force -ErrorAction Stop
    if ($args.Count -eq 0) { throw 'PROVIDER_REQUIRED: Use code-provider <provider> [Claude arguments].' }
    $providerId = [string]$args[0]
    # A pipeline assignment from an empty if-branch array becomes $null.
    # Keep the zero-argument case as an actual empty array.
    [string[]]$claudeArgs = @()
    if ($args.Count -gt 1) { $claudeArgs = [string[]]$args[1..($args.Count - 1)] }
    $code = Invoke-Launcher -Root $PSScriptRoot -Provider $providerId -ClaudeArgs $claudeArgs
    exit $code
}
catch {
    $message = if (Get-Command Get-LauncherError -ErrorAction SilentlyContinue) { Get-LauncherError -ErrorRecord $_ } else { 'MODULE_UNAVAILABLE: Launcher module could not be loaded.' }
    [Console]::Error.WriteLine($message)
    exit 1
}
