#Requires -Version 7.0
param(
    [ValidateSet('List','Validate','Inspect','Doctor','TestCredential','SetKey')]
    [string]$Action = 'List',
    [string]$Provider
)
$ErrorActionPreference = 'Stop'
try {
    Import-Module (Join-Path $PSScriptRoot 'Launcher.psm1') -Force
    if ($Action -eq 'List') {
        $items = @(foreach ($file in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'providers') -Filter '*.psd1' -File) {
            $plan = Get-LauncherPlan $PSScriptRoot $file.BaseName -AllowDisabled
            [pscustomobject]@{Provider=$plan.Provider;Enabled=$plan.Config.Enabled;Main=$plan.Config.Models.Main;CredentialExists=$plan.SecretExists}
        })
        ConvertTo-Json -InputObject $items -Depth 4
        exit 0
    }
    if (!$Provider) { throw 'PROVIDER_REQUIRED: Supply -Provider for this action.' }
    switch ($Action) {
        'Validate' { $plan=Get-LauncherPlan $PSScriptRoot $Provider -AllowDisabled; [pscustomobject]@{Provider=$Provider;Schema='Valid';Enabled=$plan.Config.Enabled} | ConvertTo-Json }
        'Inspect' { Get-LauncherStatus $PSScriptRoot $Provider | ConvertTo-Json -Depth 8 }
        'Doctor' {
            $status=Get-LauncherStatus $PSScriptRoot $Provider
            $status | ConvertTo-Json -Depth 8
            if (!$status.CredentialExists -or $status.SettingsCheck.Conflicts.Count -gt 0) { exit 1 }
        }
        'TestCredential' { Test-LauncherCredential $PSScriptRoot $Provider | ConvertTo-Json }
        'SetKey' { Save-LauncherKey $PSScriptRoot $Provider | ConvertTo-Json }
    }
    exit 0
}
catch {
    $message = if (Get-Command Get-LauncherError -ErrorAction SilentlyContinue) { Get-LauncherError -ErrorRecord $_ } else { 'MODULE_UNAVAILABLE: Launcher module could not be loaded.' }
    [Console]::Error.WriteLine($message)
    exit 1
}
