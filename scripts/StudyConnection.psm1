Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

function Get-ConnectionContext {
    param([Parameter(Mandatory=$true)][string]$Configuration)
    $path=[IO.Path]::GetFullPath($Configuration)
    $config=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($config.schema_version -ne 1) { throw 'Unsupported connection configuration.' }
    foreach ($name in @('client','profile','pid_file','health_file','log_file')) {
        if (-not [IO.Path]::IsPathRooted($config.$name)) { throw 'Connection paths must be absolute.' }
    }
    if ($config.organization_id -notmatch '^org-[A-Za-z0-9_-]+$') { throw 'Set the organization ID in chat.local.json.' }
    if (-not (Test-Path -LiteralPath $config.client -PathType Leaf) -or
        (Get-FileHash -LiteralPath $config.client -Algorithm SHA256).Hash.ToLowerInvariant() -ne $config.client_sha256) {
        throw 'Tunnel client integrity check failed.'
    }
    if (-not (Test-Path -LiteralPath $config.profile -PathType Leaf)) { throw 'The tunnel profile is missing.' }
    $hash=[Security.Cryptography.SHA256]::Create()
    try { $id=([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($path.ToLowerInvariant())))).Replace('-','').Substring(0,24).ToLowerInvariant() }
    finally { $hash.Dispose() }
    $directory=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) ('OpenSci\connections\'+$id)
    [pscustomobject]@{ Path=$path; Config=$config; Id=$id; Directory=$directory;
        Credential=(Join-Path $directory 'credential.dpapi'); State=(Join-Path $directory 'state.json');
        Stop=(Join-Path $directory 'stop.request'); StartupName=('OpenSciStudy-'+$id);
        ProfileHash=(Get-FileHash -LiteralPath $config.profile -Algorithm SHA256).Hash.ToLowerInvariant() }
}

function Assert-OrdinaryConnectionPath {
    param([string]$Path)
    $current=[IO.Path]::GetFullPath($Path)
    while ($current) {
        if ((Test-Path -LiteralPath $current) -and ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Connection storage cannot use a symbolic link or junction.'
        }
        $current=Split-Path -Parent $current
    }
}

function Initialize-ConnectionDirectory {
    param($Context)
    Assert-OrdinaryConnectionPath $Context.Directory
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    if (Test-Path -LiteralPath $Context.Directory) {
        $existing=Get-Acl -LiteralPath $Context.Directory
        if (-not $existing.AreAccessRulesProtected -or $existing.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value) {
            throw 'Private connection directory has unexpected ownership or inherited permissions.'
        }
        foreach ($rule in $existing.Access) {
            if ($rule.AccessControlType -eq 'Allow' -and $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -notin @($sid.Value,'S-1-5-18')) {
                throw 'Private connection directory grants access to another account.'
            }
        }
        return
    }
    New-Item -ItemType Directory -Path $Context.Directory -Force | Out-Null
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $acl.SetOwner($sid); $acl.SetAccessRuleProtection($true,$false)
    $inherit=[Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl',$inherit,'None','Allow')))
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier('S-1-5-18')),'FullControl',$inherit,'None','Allow')))
    Set-Acl -LiteralPath $Context.Directory -AclObject $acl
}

function Write-ConnectionJson {
    param([string]$Path,$Value)
    Assert-OrdinaryConnectionPath $Path
    $temporary=$Path+'.'+[Guid]::NewGuid().ToString('N')+'.tmp'
    try {
        [IO.File]::WriteAllText($temporary,($Value | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
        if (Test-Path -LiteralPath $Path) { [IO.File]::Replace($temporary,$Path,[System.Management.Automation.Language.NullString]::Value) }
        else { [IO.File]::Move($temporary,$Path) }
    } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
}

function Save-ConnectionCredential {
    param($Context,[Parameter(Mandatory=$true)][Security.SecureString]$Key,[string]$Expires='')
    if ($Key.Length -lt 20) { throw 'Enter a valid restricted tunnel API key.' }
    if ($Expires) {
        $date=[DateTimeOffset]::Parse($Expires)
        if ($date -le [DateTimeOffset]::UtcNow) { throw 'The chosen expiry is in the past.' }
        $Expires=$date.ToUniversalTime().ToString('o')
    }
    Initialize-ConnectionDirectory $Context
    Write-ConnectionJson $Context.Credential @{ schema_version=1; configuration=$Context.Path;
        organization_id=$Context.Config.organization_id; client_sha256=$Context.Config.client_sha256;
        profile_sha256=$Context.ProfileHash; encrypted_key=(ConvertFrom-SecureString -SecureString $Key);
        expires_utc=$Expires; protected_by='Windows DPAPI CurrentUser'; saved_utc=[DateTime]::UtcNow.ToString('o') }
}

function Read-ConnectionCredential {
    param($Context)
    Assert-OrdinaryConnectionPath $Context.Credential
    $value=Get-Content -LiteralPath $Context.Credential -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($value.schema_version -ne 1 -or $value.configuration -ne $Context.Path -or
        $value.organization_id -ne $Context.Config.organization_id -or
        $value.client_sha256 -ne $Context.Config.client_sha256 -or $value.profile_sha256 -ne $Context.ProfileHash) {
        throw 'Connection identity changed. Review the configuration and save the key again.'
    }
    if ($value.expires_utc -and [DateTimeOffset]::Parse($value.expires_utc) -le [DateTimeOffset]::UtcNow) { throw 'The recorded key expiry has passed.' }
    ConvertTo-SecureString -String $value.encrypted_key
}

function Get-OwnedConnectionProcess {
    param($Record)
    if ($null -eq $Record) { return $null }
    try {
        $process=Get-Process -Id ([int]$Record.id) -ErrorAction Stop
        # PowerShell 7 can deserialize an ISO date as DateTime; 5.1 keeps a string.
        if ($process.StartTime.ToUniversalTime().Ticks -eq ([DateTimeOffset]$Record.started_utc).UtcDateTime.Ticks -and $process.Path -eq $Record.path) { return $process }
    } catch { }
    return $null
}

function Get-ConnectionStatus {
    param($Context)
    $worker=$null; $client=$null; $phase='stopped'; $ready=$false
    if (Test-Path -LiteralPath $Context.State) {
        try {
            $state=Get-Content -LiteralPath $Context.State -Raw | ConvertFrom-Json
            $worker=Get-OwnedConnectionProcess $state.worker; $client=Get-OwnedConnectionProcess $state.client; $phase=$state.phase
        } catch { $phase='state_unreadable' }
    }
    if ($client -and (Test-Path -LiteralPath $Context.Config.health_file)) {
        try {
            $url=[Uri](Get-Content -LiteralPath $Context.Config.health_file -Raw).Trim()
            if ($url.Scheme -eq 'http' -and $url.Host -in @('127.0.0.1','localhost','[::1]') -and -not $url.UserInfo -and -not $url.Query) {
                $response=Invoke-WebRequest -UseBasicParsing -Uri ($url.GetLeftPart([UriPartial]::Authority)+'/readyz') -TimeoutSec 2
                $ready=($response.StatusCode -eq 200)
            }
        } catch { }
    }
    $startup=Get-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $Context.StartupName -ErrorAction SilentlyContinue
    [pscustomobject]@{ stored_key=(Test-Path -LiteralPath $Context.Credential); start_at_sign_in=($null -ne $startup);
        worker_running=($null -ne $worker); client_running=($null -ne $client); ready=$ready; phase=$phase; private_directory=$Context.Directory }
}

function Get-ConnectionWorkerArguments {
    param($Context,[string]$Runtime)
    foreach ($p in @($Runtime,$Context.Path)) { if ($p.Contains('"') -or $p.Contains("`r") -or $p.Contains("`n")) { throw 'Unsupported path characters.' } }
    '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+(Join-Path $Runtime 'Start-Study-Chat.ps1')+'" -Configuration "'+$Context.Path+'" -Worker'
}

function Set-ConnectionAutoStart {
    param($Context,[string]$Runtime,[bool]$Enabled)
    $registry='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    if ($Enabled) {
        $key=Read-ConnectionCredential $Context; $key.Dispose()
        $command='"'+(Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')+'" '+(Get-ConnectionWorkerArguments $Context $Runtime)
        if (-not (Test-Path -LiteralPath $registry)) { New-Item -Path $registry -Force | Out-Null }
        New-ItemProperty -LiteralPath $registry -Name $Context.StartupName -Value $command -PropertyType String -Force | Out-Null
    } else { Remove-ItemProperty -LiteralPath $registry -Name $Context.StartupName -ErrorAction SilentlyContinue }
}

function Start-ConnectionBackground {
    param($Context,[string]$Runtime)
    $key=Read-ConnectionCredential $Context; $key.Dispose()
    if ((Get-ConnectionStatus $Context).worker_running) { return }
    Initialize-ConnectionDirectory $Context
    if (Test-Path -LiteralPath $Context.Stop) { Remove-Item -LiteralPath $Context.Stop }
    Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList (Get-ConnectionWorkerArguments $Context $Runtime) -WindowStyle Hidden | Out-Null
}

function Stop-ConnectionBackground {
    param($Context)
    if (-not (Get-ConnectionStatus $Context).worker_running) { return }
    [IO.File]::WriteAllText($Context.Stop,'stop')
    for ($i=0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        if (-not (Get-ConnectionStatus $Context).worker_running) { return }
    }
    throw 'The connection did not stop. Inspect its state before updating or starting another client.'
}

function Get-ProcessRecord {
    param($Process)
    @{ id=$Process.Id; started_utc=$Process.StartTime.ToUniversalTime().ToString('o'); path=$Process.Path }
}

function Invoke-ConnectionWorker {
    param($Context,[Security.SecureString]$InteractiveKey=$null)
    Initialize-ConnectionDirectory $Context
    $lock=$null; $child=$null; $key=$null
    $state=@{ worker=(Get-ProcessRecord (Get-Process -Id $PID)); client=$null; phase='starting'; updated_utc='' }
    try {
        $lock=[IO.File]::Open((Join-Path $Context.Directory 'worker.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
        if (Test-Path -LiteralPath $Context.Config.pid_file) {
            $previous=[int](Get-Content -LiteralPath $Context.Config.pid_file -Raw).Trim()
            if (Get-Process -Id $previous -ErrorAction SilentlyContinue) { throw 'An existing client is running.' }
        }
        if (Test-Path -LiteralPath $Context.Stop) { Remove-Item -LiteralPath $Context.Stop }
        for ($attempt=0; $attempt -lt 5; $attempt++) {
            if ($null -ne $child) { $child.Dispose(); $child=$null }
            $key=if ($null -ne $InteractiveKey) { $InteractiveKey } else { Read-ConnectionCredential $Context }
            $info=New-Object Diagnostics.ProcessStartInfo
            $info.FileName=$Context.Config.client; $info.UseShellExecute=$false; $info.CreateNoWindow=$true
            $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
            $values=@('run','--profile-file',$Context.Config.profile,'--control-plane.organization-id',$Context.Config.organization_id,
                '--control-plane.api-key','env:CONTROL_PLANE_API_KEY','--control-plane.poll-channel','main','--mcp.stdio-send-initialized-notification',
                '--health.listen-addr','127.0.0.1:0','--health.url-file',$Context.Config.health_file,'--pid.file',$Context.Config.pid_file,
                '--log.file',$Context.Config.log_file,'--log.http-raw-unsafe=false')
            foreach ($value in $values) { if ($value.Contains('"') -or $value.EndsWith('\')) { throw 'Unsupported client argument path.' } }
            $info.Arguments=($values | ForEach-Object { '"'+$_+'"' }) -join ' '
            $pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($key)
            try { $info.EnvironmentVariables['CONTROL_PLANE_API_KEY']=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
            try { $child=[Diagnostics.Process]::Start($info) }
            finally {
                $info.EnvironmentVariables.Remove('CONTROL_PLANE_API_KEY')
                if ($null -eq $InteractiveKey) { $key.Dispose() }; $key=$null
            }
            $child.BeginOutputReadLine(); $child.BeginErrorReadLine()
            $state.client=Get-ProcessRecord $child; $state.phase='running'; $state.updated_utc=[DateTime]::UtcNow.ToString('o')
            Write-ConnectionJson $Context.State $state
            while (-not $child.WaitForExit(1000)) { if (Test-Path -LiteralPath $Context.Stop) { break } }
            if (Test-Path -LiteralPath $Context.Stop) { break }
            $state.phase='retry_wait'; $state.updated_utc=[DateTime]::UtcNow.ToString('o'); Write-ConnectionJson $Context.State $state
            if ($null -ne $InteractiveKey) { break }
            for ($delay=0; $delay -lt (15 * ($attempt+1)); $delay++) {
                if (Test-Path -LiteralPath $Context.Stop) { break }; Start-Sleep -Seconds 1
            }
            if (Test-Path -LiteralPath $Context.Stop) { break }
        }
        $state.phase=if (Test-Path -LiteralPath $Context.Stop) { 'stopped' } else { 'attention_required' }
    } catch {
        if ($null -eq $lock) { return }
        $state.phase='attention_required'
        $state.error_type=$_.Exception.GetType().FullName
    } finally {
        if ($null -ne $child) {
            if (-not $child.HasExited -and (Get-OwnedConnectionProcess $state.client)) {
                & "$env:SystemRoot\System32\taskkill.exe" /PID $child.Id /T /F 2>$null | Out-Null
                $child.WaitForExit(5000) | Out-Null
            }
            $child.Dispose()
        }
        if ($key -and $null -eq $InteractiveKey) { $key.Dispose() }
        if ($null -ne $lock) {
            $state.worker=$null; $state.client=$null; $state.updated_utc=[DateTime]::UtcNow.ToString('o')
            Write-ConnectionJson $Context.State $state; $lock.Dispose()
        }
    }
}

Export-ModuleMember -Function Get-ConnectionContext,Save-ConnectionCredential,Read-ConnectionCredential,Get-ConnectionStatus,Set-ConnectionAutoStart,Start-ConnectionBackground,Stop-ConnectionBackground,Invoke-ConnectionWorker
