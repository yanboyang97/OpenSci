#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:LauncherVersion = '1.0.1'
$script:ManagedExact = @(
    'ANTHROPIC_BASE_URL','ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_CUSTOM_HEADERS',
    'ANTHROPIC_MODEL','ANTHROPIC_DEFAULT_MODEL','ANTHROPIC_SMALL_FAST_MODEL',
    'ANTHROPIC_CUSTOM_MODEL_OPTION','ANTHROPIC_CUSTOM_MODEL_OPTION_NAME',
    'ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION','ANTHROPIC_CUSTOM_MODEL_OPTION_SUPPORTED_CAPABILITIES',
    'CLAUDE_CODE_SUBAGENT_MODEL','CLAUDE_CODE_SUBAGENT_MODEL_FORCE',
    'CLAUDE_CODE_EFFORT_LEVEL','CLAUDE_CODE_AUTO_COMPACT_WINDOW','CLAUDE_CODE_MAX_CONTEXT_TOKENS',
    'CLAUDE_CODE_DISABLE_1M_CONTEXT','CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT',
    'CLAUDE_CODE_OAUTH_TOKEN','CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR','CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR',
    'CLAUDE_CODE_EXTRA_BODY','CLOUD_ML_REGION','ENABLE_TOOL_SEARCH'
)
function Stop-Launcher {
    param([string]$Code, [string]$Message)
    throw [InvalidOperationException]::new("${Code}: $Message")
}
function Get-LauncherError {
    param($ErrorRecord)
    $message = $ErrorRecord.Exception.Message
    if ($message -match '^[A-Z_]+: ') { return $message }
    return 'LAUNCH_FAILED: Operation failed. Credential data and raw exception details were not logged.'
}
function Test-ManagedVariable {
    param([string]$Name)
    return ($Name -in $script:ManagedExact -or
        $Name -match '^ANTHROPIC_(DEFAULT_(OPUS|SONNET|HAIKU|FABLE)_|VERTEX_|BEDROCK_|FOUNDRY_|AWS_)' -or
        $Name -match '^CLAUDE_CODE_(USE_|SKIP_(VERTEX|BEDROCK|FOUNDRY|MANTLE|AWS)_AUTH)' -or
        $Name -match '^VERTEX_REGION_CLAUDE_')
}
function Assert-Fields {
    param($Data, [string[]]$Required, [string[]]$Optional = @(), [string]$Context)
    if ($Data -isnot [Collections.IDictionary]) { Stop-Launcher CONFIG_INVALID "$Context must be a data table." }
    foreach ($field in $Required) {
        if (!$Data.Contains($field)) { Stop-Launcher CONFIG_INVALID "$Context is missing $field." }
    }
    foreach ($field in $Data.Keys) {
        if ($field -notin ($Required + $Optional)) { Stop-Launcher CONFIG_INVALID "$Context contains an unsupported field." }
    }
}
function Read-LauncherData {
    param([string]$Path)
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { Stop-Launcher CONFIG_MISSING "Missing configuration: $Path" }
    try { return Import-PowerShellDataFile -LiteralPath $Path -ErrorAction Stop }
    catch { Stop-Launcher CONFIG_INVALID "Cannot parse data configuration: $Path" }
}
function Get-LauncherPlan {
    param([string]$Root, [string]$Provider, [switch]$AllowDisabled)
    if ($Provider -cnotmatch '^[a-z][a-z0-9-]{0,63}$') { Stop-Launcher PROVIDER_INVALID 'Invalid provider identifier.' }
    $configPath = Join-Path $Root "providers\$Provider.psd1"
    $config = Read-LauncherData $configPath
    Assert-Fields $config @('SchemaVersion','Id','Enabled','Backend','Endpoint','Auth','Models','Runtime') @('RestrictModels') 'Provider'
    if ($config.SchemaVersion -isnot [int] -or $config.SchemaVersion -ne 1) { Stop-Launcher SCHEMA_UNSUPPORTED 'Only SchemaVersion 1 is supported.' }
    if ($config.Id -cne $Provider -or $config.Enabled -isnot [bool]) { Stop-Launcher CONFIG_INVALID 'Provider identity or Enabled type is invalid.' }
    if (!$config.Enabled -and !$AllowDisabled) { Stop-Launcher PROVIDER_DISABLED 'This provider is disabled.' }
    if ($config.Backend -cne 'AnthropicCompatible') { Stop-Launcher BACKEND_UNSUPPORTED 'This release supports Anthropic-compatible providers only.' }
    $endpoint = $null
    if ($config.Endpoint -isnot [string] -or ![uri]::TryCreate($config.Endpoint, [UriKind]::Absolute, [ref]$endpoint) -or
        $endpoint.Scheme -ne 'https' -or !$endpoint.IsDefaultPort -or $endpoint.UserInfo -or $endpoint.Query -or $endpoint.Fragment) {
        Stop-Launcher ENDPOINT_INVALID 'Endpoint must be an HTTPS URL without credentials, query or fragment.'
    }
    Assert-Fields $config.Auth @('Kind','SecretRef','Variable') @() 'Auth'
    if ($config.Auth.Kind -cne 'DpapiFile' -or $config.Auth.SecretRef -isnot [string] -or
        $config.Auth.SecretRef -cnotmatch '^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$' -or
        $config.Auth.Variable -cnotin @('ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY')) {
        Stop-Launcher AUTH_INVALID 'Unsupported credential reference or authentication variable.'
    }
    Assert-Fields $config.Models @('Main','Opus','Sonnet','Haiku','Subagent') @('Fable','Custom') 'Models'
    foreach ($value in $config.Models.Values) {
        if ($value -isnot [string] -or $value -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._:/@+\-]*(\[1m\])?$') {
            Stop-Launcher MODEL_INVALID 'Model identifiers must be explicit, nonempty values without whitespace.'
        }
    }
    Assert-Fields $config.Runtime @() @('Effort','AutoCompactWindow','MaxContextTokens','ForceSubagent') 'Runtime'
    if ($config.Runtime.Contains('ForceSubagent') -and $config.Runtime.ForceSubagent -isnot [bool]) { Stop-Launcher CONFIG_INVALID 'ForceSubagent must be boolean.' }
    if ($config.Runtime.Contains('Effort') -and $config.Runtime.Effort -cnotin @('low','medium','high','xhigh','max','auto')) {
        Stop-Launcher CONFIG_INVALID 'Unsupported effort level.'
    }
    foreach ($field in @('AutoCompactWindow','MaxContextTokens')) {
        if ($config.Runtime.Contains($field)) {
            $number = $config.Runtime[$field]
            if (($number -isnot [int] -and $number -isnot [long]) -or $number -lt 100000 -or $number -gt 1048576) {
                Stop-Launcher CONFIG_INVALID 'Context windows must be integers between 100000 and 1048576.'
            }
        }
    }
    if ($config.Contains('RestrictModels') -and $config.RestrictModels -isnot [bool]) { Stop-Launcher CONFIG_INVALID 'RestrictModels must be boolean.' }
    $machinePath = Join-Path $Root 'machine.local.psd1'
    $machine = Read-LauncherData $machinePath
    Assert-Fields $machine @('SchemaVersion','ClaudePath','Secrets') @() 'Machine'
    if ($machine.SchemaVersion -ne 1 -or $machine.Secrets -isnot [Collections.IDictionary]) { Stop-Launcher CONFIG_INVALID 'Invalid machine schema or Secrets table.' }
    if ($machine.ClaudePath -isnot [string] -or ![IO.Path]::IsPathFullyQualified($machine.ClaudePath) -or
        [IO.Path]::GetExtension($machine.ClaudePath) -ne '.exe' -or !(Test-Path -LiteralPath $machine.ClaudePath -PathType Leaf)) {
        Stop-Launcher EXECUTABLE_NOT_FOUND 'ClaudePath must identify an existing absolute .exe path.'
    }
    if (!$machine.Secrets.Contains($config.Auth.SecretRef)) { Stop-Launcher SECRET_REFERENCE_MISSING 'No machine mapping for the selected credential.' }
    $secret = $machine.Secrets[$config.Auth.SecretRef]
    Assert-Fields $secret @('Path','AllowedEndpointHosts') @() 'Secret mapping'
    if ($secret.Path -isnot [string] -or ![IO.Path]::IsPathFullyQualified($secret.Path) -or $secret.Path.StartsWith('\\')) {
        Stop-Launcher SECRET_PATH_INVALID 'Credential path must be an absolute local filesystem path.'
    }
    $hosts = @($secret.AllowedEndpointHosts)
    if ($hosts.Count -eq 0) { Stop-Launcher ENDPOINT_UNBOUND 'No permitted credential endpoint host.' }
    foreach ($hostName in $hosts) {
        if ($hostName -isnot [string] -or $hostName -notmatch '^[a-z0-9]+([.-][a-z0-9]+)*$') { Stop-Launcher ENDPOINT_UNBOUND 'Invalid credential endpoint host.' }
    }
    if ($endpoint.DnsSafeHost -notin $hosts) { Stop-Launcher ENDPOINT_UNBOUND 'Endpoint host is not bound to this credential.' }
    $envMap = @{
        ANTHROPIC_BASE_URL = $config.Endpoint
        ANTHROPIC_MODEL = $config.Models.Main
        CLAUDE_CODE_SUBAGENT_MODEL = $config.Models.Subagent
    }
    foreach ($tier in @('Opus','Sonnet','Haiku','Fable')) {
        if ($config.Models.Contains($tier)) { $envMap["ANTHROPIC_DEFAULT_$($tier.ToUpperInvariant())_MODEL"] = $config.Models[$tier] }
    }
    if ($config.Models.Contains('Custom')) { $envMap.ANTHROPIC_CUSTOM_MODEL_OPTION = $config.Models.Custom }
    $runtimeMap = @{Effort='CLAUDE_CODE_EFFORT_LEVEL';AutoCompactWindow='CLAUDE_CODE_AUTO_COMPACT_WINDOW';MaxContextTokens='CLAUDE_CODE_MAX_CONTEXT_TOKENS'}
    foreach ($field in $runtimeMap.Keys) {
        if ($config.Runtime.Contains($field)) { $envMap[$runtimeMap[$field]] = [string]$config.Runtime[$field] }
    }
    if ($config.Runtime.Contains('ForceSubagent') -and $config.Runtime.ForceSubagent) { $envMap.CLAUDE_CODE_SUBAGENT_MODEL_FORCE = '1' }
    [pscustomobject]@{
        LauncherVersion=$script:LauncherVersion; Provider=$Provider; ConfigPath=$configPath; MachinePath=$machinePath
        Config=$config; ClaudePath=$machine.ClaudePath; SecretPath=$secret.Path
        SecretExists=(Test-Path -LiteralPath $secret.Path -PathType Leaf)
        Environment=$envMap; AllowedModels=@($config.Models.Values | Sort-Object -Unique)
        RestrictModels=($config.Contains('RestrictModels') -and $config.RestrictModels)
    }
}
function Find-SettingsConflicts {
    param([Collections.IDictionary]$Settings, [string]$Source)
    foreach ($field in @('model','modelOverrides','modelSettings','availableModels','deniedModels','fallbackModel',
        'apiKeyHelper','awsAuthRefresh','awsCredentialExport','gcpAuthRefresh','forceLoginMethod','forceLoginGatewayUrl','policyHelper')) {
        if ($Settings.Contains($field)) { [pscustomobject]@{Source=$Source;Field=$field} }
    }
    if ($Settings.Contains('env')) {
        if ($Settings.env -isnot [Collections.IDictionary]) { Stop-Launcher SETTINGS_INVALID "env must be an object in $Source" }
        foreach ($name in $Settings.env.Keys) {
            if ((Test-ManagedVariable $name) -or $name -eq 'CLAUDE_CONFIG_DIR' -or $name -match '^ANTHROPIC_') {
                [pscustomobject]@{Source=$Source;Field="env.$name"}
            }
        }
    }
}
function Get-LauncherSettingsCheck {
    param([string]$WorkingDirectory = (Get-Location).ProviderPath,
        [string]$UserDirectory = [Environment]::GetFolderPath('UserProfile'))
    if ($env:CLAUDE_CONFIG_DIR -and [IO.Path]::GetFullPath($env:CLAUDE_CONFIG_DIR) -ne (Join-Path $UserDirectory '.claude')) {
        Stop-Launcher CONFIG_DIRECTORY_CONFLICT 'CLAUDE_CONFIG_DIR selects a different configuration directory.'
    }
    if ($env:CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST) { Stop-Launcher HOST_MANAGED 'Provider routing is managed by the embedding host.' }
    $paths = [Collections.Generic.List[string]]::new()
    $paths.Add((Join-Path $UserDirectory '.claude\settings.json'))
    $directory = [IO.DirectoryInfo]::new($WorkingDirectory)
    while ($null -ne $directory) {
        $paths.Add((Join-Path $directory.FullName '.claude\settings.json'))
        $paths.Add((Join-Path $directory.FullName '.claude\settings.local.json'))
        $directory = $directory.Parent
    }
    $managedRoot = Join-Path $env:ProgramFiles 'ClaudeCode'
    $paths.Add((Join-Path $managedRoot 'managed-settings.json'))
    $fragmentRoot = Join-Path $managedRoot 'managed-settings.d'
    if (Test-Path -LiteralPath $fragmentRoot -PathType Container) {
        foreach ($fragment in Get-ChildItem -LiteralPath $fragmentRoot -Filter '*.json' -File) { $paths.Add($fragment.FullName) }
    }
    $checked = [Collections.Generic.List[string]]::new()
    $conflicts = [Collections.Generic.List[object]]::new()
    foreach ($path in ($paths | Select-Object -Unique)) {
        if (!(Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        try { $data = Get-Content -LiteralPath $path -Raw -ErrorAction Stop | ConvertFrom-Json -AsHashtable -ErrorAction Stop }
        catch { Stop-Launcher SETTINGS_INVALID "Cannot parse settings: $path" }
        if ($data -isnot [Collections.IDictionary]) { Stop-Launcher SETTINGS_INVALID "Settings must be an object: $path" }
        $checked.Add($path)
        foreach ($conflict in @(Find-SettingsConflicts $data $path)) { $conflicts.Add($conflict) }
    }
    foreach ($registryPath in @('HKLM:\SOFTWARE\Policies\ClaudeCode','HKCU:\SOFTWARE\Policies\ClaudeCode')) {
        if (Test-Path -LiteralPath $registryPath) {
            $registryKey = Get-Item -LiteralPath $registryPath
            if ('Settings' -in $registryKey.GetValueNames()) {
                try { $data = $registryKey.GetValue('Settings') | ConvertFrom-Json -AsHashtable -ErrorAction Stop }
                catch { Stop-Launcher SETTINGS_INVALID "Cannot parse policy: $registryPath" }
                $checked.Add($registryPath)
                foreach ($conflict in @(Find-SettingsConflicts $data $registryPath)) { $conflicts.Add($conflict) }
            }
        }
    }
    [pscustomobject]@{CheckedSources=@($checked.ToArray());Conflicts=@($conflicts.ToArray());Scope='Local files and Windows policy registry; server-side policy remains enforced by Claude Code.'}
}
function Assert-LauncherArguments {
    param($Plan, [AllowEmptyCollection()][string[]]$Arguments)
    for ($index = 0; $index -lt $Arguments.Count; $index++) {
        $token = $Arguments[$index]
        if ($token -eq '--') { break }
        $name = ($token -split '=',2)[0]
        if ($name -in @('--settings','--setting-sources','--cloud','--environment','--desktop','--teleport','--bare')) {
            Stop-Launcher ARGUMENT_CONFLICT "$name changes the managed launch context; use plain claude for this operation."
        }
        if ($name -in @('--model','--fallback-model')) {
            if ($token.Contains('=')) { $value = ($token -split '=',2)[1] }
            elseif ($index + 1 -lt $Arguments.Count) { $index++; $value = $Arguments[$index] }
            else { Stop-Launcher ARGUMENT_INVALID "$name requires a value." }
            foreach ($model in ($value -split ',')) {
                $alias = @{opus='Opus';sonnet='Sonnet';haiku='Haiku';fable='Fable';opusplan='Opus'}
                if ($model -in $Plan.AllowedModels) { continue }
                if ($alias.Contains($model) -and $Plan.Config.Models.Contains($alias[$model])) { continue }
                Stop-Launcher MODEL_NOT_ALLOWED 'Requested model is outside this provider configuration.'
            }
        }
    }
}
function Read-LauncherSecret {
    param([string]$Path)
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { Stop-Launcher SECRET_MISSING 'Credential file is missing. Use the secure SetKey action.' }
    $secure = $null
    try {
        $cipher = [IO.File]::ReadAllText($Path).Trim()
        $secure = ConvertTo-SecureString -String $cipher -ErrorAction Stop
        $plain = [PSCredential]::new('launcher', $secure).GetNetworkCredential().Password
        if ([string]::IsNullOrWhiteSpace($plain) -or $plain -match '[\r\n\x00]') { throw 'invalid credential' }
        return $plain
    }
    catch { Stop-Launcher SECRET_UNAVAILABLE 'Credential cannot be decrypted as the current Windows user, or is invalid.' }
    finally { if ($null -ne $secure) { $secure.Dispose() }; $cipher=$null; $plain=$null }
}
function New-LauncherProcessInfo {
    param($Plan, [AllowEmptyCollection()][string[]]$Arguments, [AllowNull()][string]$Credential,
        [string]$WorkingDirectory = (Get-Location).ProviderPath)
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $Plan.ClaudePath
    $start.UseShellExecute = $false
    $start.WorkingDirectory = $WorkingDirectory
    foreach ($name in @($start.Environment.Keys)) {
        if (Test-ManagedVariable $name) { [void]$start.Environment.Remove($name) }
        elseif ($name -match '^ANTHROPIC_') { Stop-Launcher ENVIRONMENT_UNKNOWN "Unrecognized provider variable: $name" }
    }
    foreach ($entry in $Plan.Environment.GetEnumerator()) { $start.Environment[$entry.Key] = $entry.Value }
    if ($null -ne $Credential) { $start.Environment[$Plan.Config.Auth.Variable] = $Credential }
    if ($Plan.RestrictModels) {
        # Contains only public model IDs; no credential is placed in the argument list.
        $start.ArgumentList.Add('--settings')
        $start.ArgumentList.Add((@{availableModels=@($Plan.AllowedModels);enforceAvailableModels=$true} | ConvertTo-Json -Compress -Depth 3))
    }
    foreach ($argument in $Arguments) { $start.ArgumentList.Add([string]$argument) }
    return $start
}
function Invoke-LauncherProcess {
    param([Diagnostics.ProcessStartInfo]$StartInfo)
    $process = $null
    try {
        $process = [Diagnostics.Process]::Start($StartInfo)
        while (!$process.WaitForExit(200)) { }
        return $process.ExitCode
    }
    finally {
        [void]$StartInfo.Environment.Remove('ANTHROPIC_API_KEY')
        [void]$StartInfo.Environment.Remove('ANTHROPIC_AUTH_TOKEN')
        if ($null -ne $process) {
            if (!$process.HasExited) { $process.Kill($true); [void]$process.WaitForExit(5000) }
            $process.Dispose()
        }
    }
}
function Invoke-Launcher {
    param([string]$Root, [string]$Provider, [AllowEmptyCollection()][string[]]$ClaudeArgs = @())
    if ($null -eq $ClaudeArgs) { $ClaudeArgs = [string[]]@() }
    $plan = Get-LauncherPlan $Root $Provider
    Assert-LauncherArguments $plan $ClaudeArgs
    $check = Get-LauncherSettingsCheck
    if ($check.Conflicts.Count -gt 0) {
        $summary = ($check.Conflicts | ForEach-Object { "$($_.Source) [$($_.Field)]" }) -join '; '
        Stop-Launcher SETTINGS_CONFLICT $summary
    }
    $credential = $null
    try {
        $infoOnly = $ClaudeArgs.Count -eq 1 -and $ClaudeArgs[0] -in @('--version','-v','--help','-h')
        if (!$infoOnly) { $credential = Read-LauncherSecret $plan.SecretPath }
        $start = New-LauncherProcessInfo $plan $ClaudeArgs $credential
        if (!$infoOnly) {
            [Console]::Error.WriteLine("Provider: $Provider | Main: $($plan.Config.Models.Main) | Project: $((Get-Location).ProviderPath)")
        }
        return Invoke-LauncherProcess $start
    }
    finally { $credential = $null }
}
function Get-LauncherStatus {
    param([string]$Root, [string]$Provider)
    $plan = Get-LauncherPlan $Root $Provider -AllowDisabled
    $check = Get-LauncherSettingsCheck
    [pscustomobject]@{
        LauncherVersion=$plan.LauncherVersion; Provider=$plan.Provider; Enabled=$plan.Config.Enabled
        ConfigPath=$plan.ConfigPath; ClaudePath=$plan.ClaudePath
        ClaudeFileVersion=[Diagnostics.FileVersionInfo]::GetVersionInfo($plan.ClaudePath).FileVersion
        CredentialPath=$plan.SecretPath; CredentialExists=$plan.SecretExists; AuthenticationVariable=$plan.Config.Auth.Variable
        Models=$plan.Config.Models; Environment=$plan.Environment; RestrictModels=$plan.RestrictModels
        SettingsCheck=$check; InheritedManagedVariables=@(Get-ChildItem Env: | Where-Object { Test-ManagedVariable $_.Name } | Select-Object -ExpandProperty Name)
    }
}
function Test-LauncherCredential {
    param([string]$Root, [string]$Provider)
    $plan = Get-LauncherPlan $Root $Provider -AllowDisabled
    $credential = $null
    try { $credential = Read-LauncherSecret $plan.SecretPath; [pscustomobject]@{Provider=$Provider;Decryption='Passed';NetworkUsed=$false} }
    finally { $credential=$null }
}
function Save-LauncherKey {
    param([string]$Root, [string]$Provider)
    if ([Console]::IsInputRedirected) { Stop-Launcher INPUT_REQUIRED 'Open an interactive PowerShell 7 terminal to enter the key securely.' }
    $plan = Get-LauncherPlan $Root $Provider -AllowDisabled
    if ($plan.SecretExists) { Stop-Launcher SECRET_ALREADY_EXISTS 'An existing credential will not be overwritten by SetKey.' }
    $directory = Split-Path -Parent $plan.SecretPath
    [void][IO.Directory]::CreateDirectory($directory)
    $candidate = $plan.SecretPath + '.' + [guid]::NewGuid().ToString('N') + '.candidate'
    $secure = $null
    $roundTrip = $null
    try {
        $secure = Read-Host "Enter $Provider API key (hidden input; no quotes)" -AsSecureString
        if ($secure.Length -eq 0) { Stop-Launcher SECRET_EMPTY 'No credential was entered.' }
        $cipher = ConvertFrom-SecureString -SecureString $secure -ErrorAction Stop
        [IO.File]::WriteAllText($candidate, $cipher, [Text.UTF8Encoding]::new($false))
        $acl = [Security.AccessControl.FileSecurity]::new()
        $acl.SetAccessRuleProtection($true, $false)
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent().User
        $acl.SetOwner($identity)
        foreach ($sid in @($identity, [Security.Principal.SecurityIdentifier]::new('S-1-5-18'), [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))) {
            $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid, 'FullControl', 'Allow'))
        }
        Set-Acl -LiteralPath $candidate -AclObject $acl -ErrorAction Stop
        $roundTrip = ConvertTo-SecureString -String ([IO.File]::ReadAllText($candidate).Trim()) -ErrorAction Stop
        if ($roundTrip.Length -ne $secure.Length) { Stop-Launcher SECRET_VERIFY_FAILED 'Encrypted credential verification failed.' }
        [IO.File]::Move($candidate, $plan.SecretPath, $false)
        [pscustomobject]@{Provider=$Provider;SavedTo=$plan.SecretPath;Encryption='Windows DPAPI';Verification='Passed';NetworkUsed=$false}
    }
    finally {
        if ($null -ne $secure) { $secure.Dispose() }
        if ($null -ne $roundTrip) { $roundTrip.Dispose() }
        $cipher=$null
        if ([IO.File]::Exists($candidate)) { [IO.File]::Delete($candidate) }
    }
}
Export-ModuleMember -Function Get-LauncherError,Get-LauncherPlan,Get-LauncherSettingsCheck,Invoke-Launcher,Get-LauncherStatus,Test-LauncherCredential,Save-LauncherKey
