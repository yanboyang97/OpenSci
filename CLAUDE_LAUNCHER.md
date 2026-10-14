# Claude Development Launcher

## Scope and setup

The Windows launcher explicitly selects DeepSeek or Kimi for interactive development in a chosen project directory. Provider data declares endpoints and model slots; eligibility, quota and observed model identity still require real-service acceptance. It needs Windows, PowerShell 7 and native claude.exe. Python offline functions keep their original platform support. Claude automated review continues through separate Vertex configuration. Development-provider selection never changes the Development Workspace, Execution Node or human approval.

For the menu entry, open `Start-ClaudeCode.cmd` in the project root and choose Setup or the desired provider. The commands below require a PowerShell 7 session in that root. If scripts are blocked, open the configured PowerShell 7 as a child session with `-NoLogo -NoProfile -ExecutionPolicy Bypass`; this affects only that session, and organizational policy still takes precedence. Run Setup from that session. To import an existing machine mapping, pass -ImportMachine with its actual path. Otherwise Setup uses the current user's .deepseek/api-key.txt and .kimi/api-key.txt references, locating .local/bin/claude.exe first and then PATH. Supply -ClaudePath for another native executable.

```powershell
.\Start-OpenSci.ps1 -LauncherAction Setup
.\Start-OpenSci.ps1 -LauncherAction Setup -ClaudePath 'C:\Tools\claude.exe'
```

Setup creates only this copy's tools/claude-launcher/machine.local.psd1 and refuses overwrite. Import retains required executable/credential-reference/endpoint bindings without copying, reading or decrypting keys. It changes neither Profile nor another installed launcher. Validate/Doctor after manually reviewed mapping edits. DPAPI credentials depend on the Windows account and machine; configure new credentials after migration. Machine mapping and home-directory keys are outside project backups.

## Interactive use

```powershell
.\Start-OpenSci.ps1 -ClaudeProvider deepseek
.\Start-OpenSci.ps1 -ClaudeProvider kimi
.\Start-OpenSci.ps1 -ClaudeProvider kimi -ClaudeArgs @('--model','k3[1m]')
.\Start-OpenSci.ps1 -ClaudeProvider kimi -ClaudeArgs @('--model','kimi-for-coding')
```

The default directory is the script's project root, independent of the caller's directory. -WorkingDirectory selects another reviewed copy. ClaudeArgs preserves empty values, spaces and Unicode; use PowerShell 7 directly for argument arrays. The root Start-ClaudeCode.cmd opens the English provider/setup menu; it can use the configured PowerShell path from runtime.local.json. No hub.local.json is required and no WSL/SSH Development Workspace is contacted automatically.

Calling tools/claude-launcher/run.ps1 directly retains the current terminal directory. Dot-sourcing init.ps1 registers functions only in the current session, bound to this copy, replacing any same-name session functions; closing the terminal removes them. Return to a previous installation via a fresh terminal or its init script, without editing Profile.

## Provider configuration and credentials

The bundled provider files declare DeepSeek's deepseek-flash[1m] main model and deepseek-flash smaller slots through ANTHROPIC_AUTH_TOKEN, and Kimi's k3-256k main model with k3[1m]/kimi-for-coding options through ANTHROPIC_API_KEY. Endpoints in the supplied data are https://api.deepseek.com/anthropic and https://api.kimi.com/coding/. These are package declarations, not a claim that a service/model was verified during this deployment. Consult the actual providers/*.psd1 for exact slots/context/reasoning settings. Enabled permits explicit selection, not automatic calls. Automated-review providers remain separately disabled by default.

SecretRef locates a machine-local file and HTTPS host must match AllowedEndpointHosts. Decryption supplies a key only to the child environment, never command-line diagnostics or the parent terminal environment.

Use LauncherAction List, Validate, Inspect and Doctor for non-decrypting local checks; TestCredential checks local decryption only; SetKey securely prompts and saves DPAPI ciphertext, refusing overwrite. None establishes remote authentication, entitlement or quota. The launcher checks user/project/ancestor Claude settings and managed Windows policy. Model/auth/routing conflicts stop with source field names, without printing secret values or changing settings. Existing shared Vertex settings require operator review, not automatic removal.

Arguments that take over routing are refused: --settings, --setting-sources, --cloud, --environment, --desktop, --teleport and --bare. Model/fallback choices must be configured values/slots; there is no cross-provider fallback. Sole --version/--help probes avoid key decryption but still check machine configuration/settings conflicts.

| Error | Action |
| --- | --- |
| CONFIG_MISSING | Run Setup or repair missing configuration |
| CONFIG_EXISTS | Preserve existing mapping and inspect/validate it |
| EXECUTABLE_NOT_FOUND | Provide an existing absolute native .exe path |
| SECRET_MISSING / SECRET_UNAVAILABLE | Check path, Windows identity and credential; use SetKey if needed |
| ENDPOINT_UNBOUND | Verify allowed credential endpoint hosts |
| SETTINGS_CONFLICT | Review the reported source file/field with Doctor |

## Maintenance and testing

Copies are managed independently and never auto-synchronized. Maintain project rules only in root AGENTS.md. Validate this copy's executable, argument handling and credential references before using a provider. Keep verification output outside the distribution.
