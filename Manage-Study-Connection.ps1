param([string]$Configuration=(Join-Path $PSScriptRoot 'config\chat.local.json'),
      [ValidateSet('Menu','Setup','Status','Start','Stop','DisableStartup','Forget')][string]$Action='Menu')
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'scripts\StudyConnection.psm1') -Force

function Show-KeySetup {
    param($Context)
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $form=New-Object Windows.Forms.Form
    $form.Text='OpenSci - encrypted background connection'; $form.Size=New-Object Drawing.Size(640,410)
    $form.StartPosition='CenterScreen'; $form.FormBorderStyle='FixedDialog'; $form.MaximizeBox=$false
    $label=New-Object Windows.Forms.Label
    $label.Location=New-Object Drawing.Point(20,20); $label.Size=New-Object Drawing.Size(590,92)
    $label.Text="Create a restricted OpenAI key with Tunnels Read + Use only.`r`nChoose the longest expiry your account allows. This does not extend expiry.`r`nPaste it below once. Windows encrypts it for your current account.`r`nYour computer must stay awake and online; no console window is needed."
    $form.Controls.Add($label)
    $link=New-Object Windows.Forms.LinkLabel; $link.Text='Open official tunnel setup and key guidance'
    $link.Location=New-Object Drawing.Point(20,115); $link.Size=New-Object Drawing.Size(550,24)
    $link.Add_Click({ Start-Process 'https://developers.openai.com/api/docs/guides/secure-mcp-tunnels' }); $form.Controls.Add($link)
    $box=New-Object Windows.Forms.TextBox; $box.Location=New-Object Drawing.Point(20,150); $box.Size=New-Object Drawing.Size(580,25)
    $box.UseSystemPasswordChar=$true; $form.Controls.Add($box)
    $expiryLabel=New-Object Windows.Forms.Label; $expiryLabel.Text='Expiry (YYYY-MM-DD, optional; blank does not override platform expiry):'
    $expiryLabel.Location=New-Object Drawing.Point(20,190); $expiryLabel.Size=New-Object Drawing.Size(590,24); $form.Controls.Add($expiryLabel)
    $expiry=New-Object Windows.Forms.TextBox; $expiry.Location=New-Object Drawing.Point(20,216); $expiry.Size=New-Object Drawing.Size(220,24); $form.Controls.Add($expiry)
    $auto=New-Object Windows.Forms.CheckBox; $auto.Text='Start automatically after I sign in to Windows'; $auto.Checked=$true
    $auto.Location=New-Object Drawing.Point(20,255); $auto.Size=New-Object Drawing.Size(560,26); $form.Controls.Add($auto)
    $button=New-Object Windows.Forms.Button; $button.Text='Save encrypted and connect'; $button.Location=New-Object Drawing.Point(20,300); $button.Size=New-Object Drawing.Size(260,35)
    $runtime=$PSScriptRoot
    $button.Add_Click({
        $secret=$null
        try {
            if ((Get-ConnectionStatus $Context).worker_running) { Stop-ConnectionBackground $Context }
            $secret=ConvertTo-SecureString -String $box.Text -AsPlainText -Force; $box.Clear()
            $date=''; if ($expiry.Text.Trim()) { $date=[DateTime]::ParseExact($expiry.Text.Trim(),'yyyy-MM-dd',[Globalization.CultureInfo]::InvariantCulture).ToUniversalTime().ToString('o') }
            Save-ConnectionCredential $Context $secret $date
            Set-ConnectionAutoStart $Context $runtime $auto.Checked
            Start-ConnectionBackground $Context $runtime
            [Windows.Forms.MessageBox]::Show('Encrypted key saved. Connection is starting. Use Status to confirm Ready = True.','OpenSci') | Out-Null
            $form.Close()
        } catch {
            [Windows.Forms.MessageBox]::Show('Setup did not complete. Check the key, expiry date, configuration and existing connection. No secret is included in this message.','OpenSci') | Out-Null
        } finally { if ($secret) { $secret.Dispose() } }
    }.GetNewClosure())
    $form.Controls.Add($button)
    try { $form.ShowDialog() | Out-Null } finally { $box.Clear(); $form.Dispose() }
}

try {
    $context=Get-ConnectionContext $Configuration
    do {
        $selected=$Action
        if ($Action -eq 'Menu') {
            Write-Host "`nOpenSci Study connection"
            Write-Host '1 Save or replace encrypted key and enable background connection'
            Write-Host '2 Status    3 Start    4 Stop now (sign-in setting remains)'
            Write-Host '5 Disable sign-in startup    6 Stop, disable startup and forget stored key'
            Write-Host '0 Exit'
            $choice=Read-Host 'Choose'
            $selected=switch ($choice) { '1' {'Setup'} '2' {'Status'} '3' {'Start'} '4' {'Stop'} '5' {'DisableStartup'} '6' {'Forget'} default {'Exit'} }
        }
        switch ($selected) {
            'Setup' { Show-KeySetup $context }
            'Status' { Get-ConnectionStatus $context | ConvertTo-Json }
            'Start' { Start-ConnectionBackground $context $PSScriptRoot; Write-Host 'Start requested. Check Status for readiness.' }
            'Stop' { Stop-ConnectionBackground $context; Write-Host 'Connection stopped.' }
            'DisableStartup' { Set-ConnectionAutoStart $context $PSScriptRoot $false; Write-Host 'Sign-in startup disabled. Use Stop to stop the current connection.' }
            'Forget' {
                Stop-ConnectionBackground $context; Set-ConnectionAutoStart $context $PSScriptRoot $false
                if (Test-Path -LiteralPath $context.Credential) { Remove-Item -LiteralPath $context.Credential }
                Write-Host 'Stored key removed. Revoke it separately in OpenAI if it is no longer needed.'
            }
        }
    } while ($Action -eq 'Menu' -and $selected -ne 'Exit')
} catch {
    Write-Host 'Connection management failed. Check chat.local.json, the official client checksum and private storage permissions.'
    exit 1
}
