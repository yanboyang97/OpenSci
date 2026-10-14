# Registers functions for THIS copy. No profile edits or credential reads.
#Requires -Version 7.0
$rhLauncherRoot = $PSScriptRoot
$rhLauncherChild = {
    param([string]$ScriptName, [AllowEmptyCollection()][string[]]$ForwardArgs)
    if ($PSVersionTable.PSEdition -ne 'Core') {
        $global:LASTEXITCODE = 1
        Write-Error 'POWERSHELL_UNSUPPORTED: Please use PowerShell 7.'
        return
    }
    $runner = Join-Path $rhLauncherRoot $ScriptName
    $child = $null
    try {
        if (!(Test-Path -LiteralPath $runner -PathType Leaf)) {
            throw 'LAUNCHER_MISSING: The launcher runtime is missing.'
        }
        if ((Get-Location).Provider.Name -ne 'FileSystem') {
            throw 'WORKDIR_INVALID: Change to a filesystem project directory first.'
        }
        $start = [Diagnostics.ProcessStartInfo]::new()
        $start.FileName = Join-Path $PSHOME 'pwsh.exe'
        $start.UseShellExecute = $false
        $start.WorkingDirectory = (Get-Location).ProviderPath
        foreach ($part in @('-NoLogo', '-NoProfile', '-File', $runner) + $ForwardArgs) {
            $start.ArgumentList.Add([string]$part)
        }
        $child = [Diagnostics.Process]::Start($start)
        while (!$child.WaitForExit(200)) { }
        $global:LASTEXITCODE = $child.ExitCode
    }
    catch {
        $global:LASTEXITCODE = 1
        Write-Error ('LAUNCH_FAILED: ' + $_.Exception.Message)
    }
    finally {
        if ($null -ne $child) {
            if (!$child.HasExited) { $child.Kill($true); [void]$child.WaitForExit(5000) }
            $child.Dispose()
        }
    }
}.GetNewClosure()
Set-Item -Path Function:global:Invoke-CodeProviderChild -Value $rhLauncherChild
Remove-Variable rhLauncherRoot, rhLauncherChild
function global:code-provider {
    Invoke-CodeProviderChild -ScriptName 'run.ps1' -ForwardArgs ([string[]]$args)
}
function global:deepseek-code {
    code-provider 'deepseek' @args
}
function global:kimi-code {
    code-provider 'kimi' @args
}
function global:code-provider-admin {
    Invoke-CodeProviderChild -ScriptName 'manage.ps1' -ForwardArgs ([string[]]$args)
}
