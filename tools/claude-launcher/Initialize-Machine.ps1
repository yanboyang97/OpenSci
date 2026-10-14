#Requires -Version 7.0
[CmdletBinding()]
param([string]$ImportMachine = '', [string]$ClaudePath = '')
$ErrorActionPreference = 'Stop'
$candidateRoot = $null
try {
    Import-Module (Join-Path $PSScriptRoot 'Launcher.psm1') -Force
    if (!$IsWindows) { throw 'PLATFORM_UNSUPPORTED: This launcher requires Windows and PowerShell 7.' }
    $target = Join-Path $PSScriptRoot 'machine.local.psd1'
    if (Test-Path -LiteralPath $target) { throw 'CONFIG_EXISTS: Existing machine.local.psd1 will not be overwritten.' }
    if ($ImportMachine -and $ClaudePath) { throw 'ARGUMENT_CONFLICT: Use ImportMachine or ClaudePath, not both.' }
    if ($ImportMachine) {
        $machine = Import-PowerShellDataFile -LiteralPath $ImportMachine
        if ($machine.Keys.Count -ne 3 -or $machine.SchemaVersion -ne 1 -or
            $machine.Secrets -isnot [Collections.IDictionary]) { throw 'CONFIG_INVALID: Invalid machine configuration.' }
        foreach ($key in $machine.Keys) {
            if ($key -notin @('SchemaVersion','ClaudePath','Secrets')) { throw 'CONFIG_INVALID: Unsupported machine field.' }
        }
        foreach ($key in $machine.Secrets.Keys) {
            $entry = $machine.Secrets[$key]
            if ($entry -isnot [Collections.IDictionary] -or $entry.Keys.Count -ne 2 -or
                !$entry.Contains('Path') -or !$entry.Contains('AllowedEndpointHosts')) { throw 'CONFIG_INVALID: Unsupported secret mapping.' }
        }
    } else {
        $userDirectory = [Environment]::GetFolderPath('UserProfile')
        if (!$ClaudePath) {
            $native = Join-Path $userDirectory '.local\bin\claude.exe'
            if (Test-Path -LiteralPath $native -PathType Leaf) { $ClaudePath = $native }
            else {
                $command = Get-Command claude.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($command) { $ClaudePath = $command.Source }
            }
        }
        if (!$ClaudePath) { throw 'EXECUTABLE_NOT_FOUND: Supply -ClaudePath with the existing native claude.exe path.' }
        $machine = @{
            SchemaVersion = 1; ClaudePath = $ClaudePath
            Secrets = @{
                'deepseek/default' = @{Path=(Join-Path $userDirectory '.deepseek\api-key.txt');AllowedEndpointHosts=@('api.deepseek.com')}
                'kimi/default' = @{Path=(Join-Path $userDirectory '.kimi\api-key.txt');AllowedEndpointHosts=@('api.kimi.com')}
            }
        }
    }
    # Validate the entire imported data before serializing. Import-PowerShellDataFile
    # never executes arbitrary profile code; keys/ciphertexts are not copied.
    $candidateRoot = Join-Path $PSScriptRoot ('.setup-' + [guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory((Join-Path $candidateRoot 'providers'))
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'providers\deepseek.psd1'), (Join-Path $PSScriptRoot 'providers\kimi.psd1') -Destination (Join-Path $candidateRoot 'providers')
    function Quote-Data([string]$Value) { "'" + $Value.Replace("'", "''") + "'" }
    $text = "@{`n    SchemaVersion = 1`n    ClaudePath = $(Quote-Data $machine.ClaudePath)`n    Secrets = @{`n"
    foreach ($id in @('deepseek/default','kimi/default')) {
        if (!$machine.Secrets.Contains($id)) { throw 'SECRET_REFERENCE_MISSING: Both bundled provider mappings are required.' }
        $entry = $machine.Secrets[$id]
        $hosts = @($entry.AllowedEndpointHosts | ForEach-Object { Quote-Data $_ }) -join ', '
        $text += "        $(Quote-Data $id) = @{ Path = $(Quote-Data $entry.Path); AllowedEndpointHosts = @($hosts) }`n"
    }
    $text += "    }`n}`n"
    [IO.File]::WriteAllText((Join-Path $candidateRoot 'machine.local.psd1'), $text, [Text.UTF8Encoding]::new($false))
    foreach ($id in @('deepseek','kimi')) { $null = Get-LauncherPlan $candidateRoot $id -AllowDisabled }
    # File.Move without overwrite also rejects a concurrent setup writer.
    [IO.File]::Move((Join-Path $candidateRoot 'machine.local.psd1'), $target, $false)
    [pscustomobject]@{Created=$target;CredentialsCopied=$false;ProfileChanged=$false;NetworkUsed=$false} | ConvertTo-Json
} catch {
    $message = if (Get-Command Get-LauncherError -ErrorAction SilentlyContinue) { Get-LauncherError $_ } else { 'SETUP_FAILED: Check the configuration source and executable path.' }
    [Console]::Error.WriteLine($message)
    exit 1
} finally {
    if ($candidateRoot -and [IO.Directory]::Exists($candidateRoot)) {
        $resolvedCandidate = [IO.Path]::GetFullPath($candidateRoot)
        $resolvedRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
        if (!$resolvedCandidate.StartsWith($resolvedRoot, [StringComparison]::OrdinalIgnoreCase) -or
            [IO.Path]::GetFileName($resolvedCandidate) -notmatch '^\.setup-[a-f0-9]{32}$') { throw 'Unsafe setup cleanup path.' }
        Remove-Item -LiteralPath $resolvedCandidate -Recurse -Force
    }
}
