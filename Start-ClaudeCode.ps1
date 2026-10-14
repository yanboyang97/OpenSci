#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Provider = '',
    [ValidateSet('Menu','Launch','List','Validate','Inspect','Doctor','TestCredential','SetKey','Setup')]
    [string]$Action = 'Menu',
    [string]$WorkingDirectory = $PSScriptRoot,
    [AllowEmptyCollection()][AllowEmptyString()][string[]]$ClaudeArgs = @(),
    [string]$ImportMachine = '',
    [string]$ClaudePath = ''
)
$ErrorActionPreference = 'Stop'
try {
    $launcher = Join-Path $PSScriptRoot 'tools\claude-launcher'
    $module = Import-Module (Join-Path $launcher 'Launcher.psm1') -Force -PassThru
    if (!$IsWindows) { throw 'PLATFORM_UNSUPPORTED: Claude launcher requires Windows and PowerShell 7.' }
    $work = Get-Item -LiteralPath $WorkingDirectory -ErrorAction Stop
    if ($work -isnot [IO.DirectoryInfo]) { throw 'WORKDIR_INVALID: WorkingDirectory must be a directory.' }
    if ($Action -eq 'Menu' -and $Provider) { $Action = 'Launch' }
    if ($Action -eq 'Menu') {
        Write-Host 'OpenSci - Claude Code Development launcher'
        Write-Host ('Working directory: ' + $work.FullName)
        Write-Host '1 DeepSeek   2 Kimi   3 List configuration   4 Setup   0 Exit'
        switch (Read-Host 'Select') {
            '1' { $Action='Launch'; $Provider='deepseek' }
            '2' { $Action='Launch'; $Provider='kimi' }
            '3' { $Action='List' }
            '4' { $Action='Setup' }
            '0' { exit 0 }
            default { throw 'SELECTION_INVALID: Select an item from the menu.' }
        }
    }
    if ($Action -ne 'Setup' -and ($ImportMachine -or $ClaudePath)) { throw 'ARGUMENT_CONFLICT: ImportMachine and ClaudePath require Setup.' }
    if ($Action -ne 'Launch' -and $ClaudeArgs.Count) { throw 'ARGUMENT_CONFLICT: ClaudeArgs require Launch.' }
    if ($Action -notin @('List','Setup') -and !$Provider) { throw 'PROVIDER_REQUIRED: Supply -Provider deepseek or kimi.' }
    $arguments = [Collections.Generic.List[string]]::new()
    if ($Action -eq 'Setup') {
        $scriptFile = Join-Path $launcher 'Initialize-Machine.ps1'
        if ($ImportMachine) {
            $source = Get-Item -LiteralPath $ImportMachine -ErrorAction Stop
            if ($source -isnot [IO.FileInfo]) { throw 'CONFIG_INVALID: ImportMachine must be a filesystem file.' }
            $arguments.Add('-ImportMachine'); $arguments.Add($source.FullName)
        }
        if ($ClaudePath) { $arguments.Add('-ClaudePath'); $arguments.Add($ClaudePath) }
    } elseif ($Action -eq 'Launch') {
        $scriptFile = Join-Path $launcher 'run.ps1'
        $arguments.Add($Provider)
        foreach ($part in $ClaudeArgs) { $arguments.Add([string]$part) }
    } else {
        $scriptFile = Join-Path $launcher 'manage.ps1'
        $arguments.Add('-Action'); $arguments.Add($Action)
        if ($Provider) { $arguments.Add('-Provider'); $arguments.Add($Provider) }
    }
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = Join-Path $PSHOME 'pwsh.exe'
    $start.UseShellExecute = $false
    $start.WorkingDirectory = $work.FullName
    foreach ($part in @('-NoLogo','-NoProfile','-File',$scriptFile) + $arguments.ToArray()) { $start.ArgumentList.Add($part) }
    # Shared wait/termination path propagates the child's exit code.
    $code = & $module { param($Info) Invoke-LauncherProcess $Info } $start
    exit $code
} catch {
    $message = if (Get-Command Get-LauncherError -ErrorAction SilentlyContinue) { Get-LauncherError $_ } else { 'LAUNCH_FAILED: Check the working directory and launcher arguments.' }
    [Console]::Error.WriteLine($message)
    exit 1
}
