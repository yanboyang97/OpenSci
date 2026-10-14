param(
    [string]$Python = '', [switch]$List, [string]$CoordinatorRoot = '',
    [string]$ClaudeProvider = '',
    [ValidateSet('Menu','List','Validate','Inspect','Doctor','TestCredential','SetKey','Setup')]
    [string]$LauncherAction,
    [string]$WorkingDirectory = $PSScriptRoot,
    [AllowEmptyCollection()][AllowEmptyString()][string[]]$ClaudeArgs = @(),
    [string]$ImportMachine = '', [string]$ClaudePath = ''
)
$ErrorActionPreference = 'Stop'
$rhRuntimePath = Join-Path $PSScriptRoot 'config\runtime.local.json'
$rhRuntime = $null
if (Test-Path -LiteralPath $rhRuntimePath) {
    $rhRuntime = Get-Content -LiteralPath $rhRuntimePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($rhRuntime.schema_version -ne 1) { throw 'Unsupported local runtime configuration.' }
}
if ($ClaudeProvider -or $LauncherAction) {
    if ($List -or $Python) { throw 'Use Hub parameters or Claude launcher parameters separately.' }
    $rhPreviousPath = $env:PATH
    try {
        if ($rhRuntime.git) {
            if (-not [IO.Path]::IsPathRooted($rhRuntime.git) -or -not (Test-Path -LiteralPath $rhRuntime.git -PathType Leaf)) {
                throw 'Configured Git executable is missing. Update config/runtime.local.json.'
            }
            $env:PATH = (Split-Path -Parent $rhRuntime.git) + [IO.Path]::PathSeparator + $env:PATH
        }
        if ($PSVersionTable.PSVersion.Major -lt 7) {
            $rhPowerShell = $rhRuntime.powershell
            if (-not $rhPowerShell) {
                $rhPowerShellCommand = Get-Command pwsh.exe -ErrorAction SilentlyContinue
                if ($rhPowerShellCommand) { $rhPowerShell = $rhPowerShellCommand.Source }
            }
            if (-not $rhPowerShell -or -not (Test-Path -LiteralPath $rhPowerShell -PathType Leaf)) {
                throw 'Claude launcher requires PowerShell 7. Configure config/runtime.local.json or run with pwsh.'
            }
            if ($ClaudeArgs.Count) { throw 'For ClaudeArgs, run this script directly in PowerShell 7.' }
            & $rhPowerShell -NoLogo -NoProfile -File $PSCommandPath @PSBoundParameters
            $rhExitCode = $LASTEXITCODE
        } else {
            $rhParameters = @{Provider=$ClaudeProvider;WorkingDirectory=$WorkingDirectory;ClaudeArgs=$ClaudeArgs;ImportMachine=$ImportMachine;ClaudePath=$ClaudePath}
            if ($LauncherAction) { $rhParameters.Action = $LauncherAction }
            & (Join-Path $PSScriptRoot 'Start-ClaudeCode.ps1') @rhParameters
            $rhExitCode = $LASTEXITCODE
        }
    } finally {
        $env:PATH = $rhPreviousPath
    }
    exit $rhExitCode
}
if ($ClaudeArgs.Count -or $ImportMachine -or $ClaudePath -or $PSBoundParameters.ContainsKey('WorkingDirectory')) {
    throw 'Select -ClaudeProvider or -LauncherAction for Claude launcher options.'
}
$rhScript = Join-Path $PSScriptRoot 'scripts\hub.py'
$rhCandidates = if ($Python) { @($Python) } elseif ($rhRuntime.python) { @($rhRuntime.python) } else { @('python', 'py', 'python3') }
$rhExecutable = $null
foreach ($rhCandidate in $rhCandidates) {
    $rhCommand = Get-Command $rhCandidate -ErrorAction SilentlyContinue
    if ($null -eq $rhCommand) { continue }
    try {
        & $rhCommand.Source -B -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 2)' 2>$null
    } catch { continue }
    if ($LASTEXITCODE -eq 0) { $rhExecutable = $rhCommand.Source; break }
}
if (-not $rhExecutable) {
    throw 'Python 3.10+ required. Use: .\Start-OpenSci.ps1 -Python C:\path\python.exe'
}
$rhAction = if ($List) { 'list' } else { 'menu' }
$rhPreviousPath = $env:PATH
try {
    if ($rhRuntime.git) {
        if (-not [IO.Path]::IsPathRooted($rhRuntime.git) -or -not (Test-Path -LiteralPath $rhRuntime.git -PathType Leaf)) {
            throw 'Configured Git executable is missing. Update config/runtime.local.json.'
        }
        $env:PATH = (Split-Path -Parent $rhRuntime.git) + [IO.Path]::PathSeparator + $env:PATH
    }
    $rhStudyConfig = Join-Path $PSScriptRoot 'config\studies.local.json'
    if (-not $CoordinatorRoot -and (Test-Path -LiteralPath $rhStudyConfig)) {
        $rhStudies = Get-Content -LiteralPath $rhStudyConfig -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($rhStudies.schema_version -ne 1) { throw 'Unsupported study location configuration.' }
        $CoordinatorRoot = $rhStudies.coordinator_root
    }
    if ($CoordinatorRoot) {
        if (-not [IO.Path]::IsPathRooted($CoordinatorRoot) -or -not (Test-Path -LiteralPath $CoordinatorRoot -PathType Container)) { throw 'The configured coordinator directory is unavailable.' }
        & $rhExecutable -B -X utf8 $rhScript --coordinator-root $CoordinatorRoot $rhAction
    } else {
        & $rhExecutable -B -X utf8 $rhScript $rhAction
    }
    $rhExitCode = $LASTEXITCODE
} finally {
    $env:PATH = $rhPreviousPath
}
exit $rhExitCode
