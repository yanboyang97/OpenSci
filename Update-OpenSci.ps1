param([string]$RuntimeRoot=$PSScriptRoot)
$ErrorActionPreference='Stop'
try {
    $RuntimeRoot=[IO.Path]::GetFullPath($RuntimeRoot)
    $runtime=Get-Content -LiteralPath (Join-Path $RuntimeRoot 'config\runtime.local.json') -Raw | ConvertFrom-Json
    $python=$runtime.python
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Configure the Python path first.' }
    $script=Join-Path $PSScriptRoot 'scripts\update_runtime.py'
    $coordinator=$RuntimeRoot
    $settings=Join-Path $RuntimeRoot 'config\studies.local.json'
    if (Test-Path -LiteralPath $settings) { $coordinator=(Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json).coordinator_root }
    Write-Host 'OpenSci update and backup'
    Write-Host 'Before every upgrade, back up ALL your data to independent protected storage.'
    Write-Host 'Read UPDATING.md and BACKUP_AND_MIGRATION.md first. This tool does not discover external research folders or Zotero data.'
    Write-Host '1 Check latest version    2 Download and prepare update    3 Use a downloaded runtime ZIP'
    Write-Host '4 Back up selected folders    5 Recover an interrupted update    0 Exit'
    $choice=Read-Host 'Choose'
    if ($choice -eq '0') { exit 0 }
    if ($choice -eq '1') { & $python -B -X utf8 $script check; if ($LASTEXITCODE) { throw 'Version check failed.' }; Read-Host 'Press Enter to close'; exit 0 }
    if ($choice -eq '5') {
        $transaction=Read-Host 'Full path to transaction.json from the failed update'
        Write-Host 'Stop all OpenSci writers first. Recovery restores only software, preserving current user data and configuration.'
        if ((Read-Host 'Type STOPPED to confirm writers are stopped') -cne 'STOPPED') { exit 0 }
        & $python -B -X utf8 $script recover --transaction $transaction --quiesced
        if ($LASTEXITCODE) { throw 'Recovery requires attention; retain the transaction and backup.' }
        Read-Host 'Press Enter to close'; exit 0
    }
    if ($choice -notin @('2','3','4')) { exit 0 }
    $parent=Read-Host 'Existing private folder OUTSIDE OpenSci and its data folders for update records and backups'
    if (-not [IO.Path]::IsPathRooted($parent) -or -not (Test-Path -LiteralPath $parent -PathType Container)) { throw 'Choose an existing absolute folder path.' }
    $stamp=[DateTime]::Now.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
    $work=Join-Path $parent ('OpenSci-update-'+$stamp)
    $extra=@()
    $private=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'OpenSci\connections'
    if (Test-Path -LiteralPath $private) { $extra+=@('--extra',$private) }
    Write-Host ('Software: '+$RuntimeRoot)
    Write-Host ('Study data: '+$coordinator)
    Write-Host 'Add each external research/data folder you want included. Close its writers first. Leave blank when done.'
    do {
        $folder=Read-Host 'Additional full folder path (or Enter)'
        if ($folder) { $extra+=@('--extra',$folder) }
    } while ($folder)
    if ($choice -eq '4') {
        if ((Read-Host 'Stop all writers, then type STOPPED') -cne 'STOPPED') { exit 0 }
        & $python -B -X utf8 $script backup --runtime $RuntimeRoot --coordinator $coordinator --output $work @extra --quiesced
        if ($LASTEXITCODE) { throw 'Backup failed. Do not upgrade.' }
        Write-Host 'Copy the verified backup and receipt to independent protected storage. ZIP contents are not encrypted.'
        Read-Host 'Press Enter to close'; exit 0
    }
    if ($choice -eq '2') {
        $raw=& $python -B -X utf8 $script download --output (Join-Path $parent ('OpenSci-download-'+$stamp))
        if ($LASTEXITCODE) { throw 'Download failed.' }
        $download=$raw -join "`n" | ConvertFrom-Json
        $package=$download.package; $digest=$download.sha256
        Write-Host ('Downloaded '+$download.version+' from '+$download.release_url)
    } else {
        $package=Read-Host 'Full path to OpenSci-VERSION.zip from the official release'
        $digest=Read-Host 'SHA-256 for that ZIP from the official release SHA256SUMS.txt'
    }
    & $python -B -X utf8 $script plan --package $package --sha256 $digest --runtime $RuntimeRoot --coordinator $coordinator --work $work @extra
    if ($LASTEXITCODE) { throw 'Update planning failed; no installed software was changed.' }
    Write-Host ('Review the exact software changes in '+(Join-Path $work 'plan.json'))
    Write-Host 'Back up external data, Zotero and credentials as described in the guide. The apply step also makes a verified local full-folder backup.'
    if ((Read-Host 'Type BACKED UP after completing your independent backup') -cne 'BACKED UP') { exit 0 }
    $chat=Join-Path $RuntimeRoot 'config\chat.local.json'
    if (Test-Path -LiteralPath $chat) {
        Import-Module (Join-Path $PSScriptRoot 'scripts\StudyConnection.psm1') -Force
        $context=Get-ConnectionContext $chat
        Stop-ConnectionBackground $context
    }
    Write-Host 'Close other assistant connections, OpenSci menus, observers and data editors. Finish pending saves and retain their receipts.'
    if ((Read-Host 'Type STOPPED to confirm all other writers are stopped') -cne 'STOPPED') { exit 0 }
    if ((Read-Host 'Type UPDATE to apply the reviewed software changes') -cne 'UPDATE') { exit 0 }
    & $python -B -X utf8 $script apply --plan (Join-Path $work 'plan.json') --quiesced --backup-confirmed
    if ($LASTEXITCODE) { throw 'Update did not finish. Keep all records; use recovery before restarting OpenSci.' }
    Write-Host 'Update complete. Verify the version and read your saved Study before saving anything new.'
    Write-Host 'Open Start-Study-Chat.cmd to restart a saved-key connection. Startup preferences and encrypted credentials are retained.'
    Read-Host 'Press Enter to close'
} catch {
    Write-Host 'Update/backup stopped. Review the preceding diagnostic. Keep the original installation, backup and transaction records.'
    exit 1
}
