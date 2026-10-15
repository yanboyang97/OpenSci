# Plugins and MCP

[Handbook](../DOCUMENTATION.md) · [Requirements](INSTALLATION.md)

Connect an assistant so it can read your Study Overview and save progress when you ask. This tutorial covers **ChatGPT, Codex, Claude Desktop and Claude Code**. MCP is the connection protocol; OpenSci's local server is `scripts/hub_mcp.py`. The **OpenSci Study** plugin packages that server for compatible plugin hosts. Neither installation method creates your Study or supplies an account, tunnel or credentials.

## Choose your route

| Where you want to work | Windows | macOS / Linux |
| --- | --- | --- |
| ChatGPT in a browser | Private Secure MCP Tunnel; supplied Windows launcher | Official tunnel client on the computer with OpenSci; terminal launch |
| Codex on your computer | Direct local MCP or compatible OpenSci plugin | Same MCP settings with native Python and paths |
| Claude Desktop | Local MCP configuration | macOS local MCP; Linux desktop is currently beta, use its Developer settings when available |
| Claude Code | Local stdio MCP from the Windows terminal | Same CLI with native Python and paths |

These are connection routes, not a claim that every operating system's full research workflow has passed acceptance. Claude's current desktop availability is documented in its [installation guide](https://support.claude.com/en/articles/10065433-install-claude-desktop). For each client, use the computer/process that can actually access the records. Windows paths do not work inside WSL or a cloud container. Keep Zotero on the coordinator's computer; never forward its local port. For phone task continuation see [Research from Your Phone](MOBILE_RESEARCH.md).

<a id="connection-prerequisites"></a>
## 1. Prepare one selected Study

First complete [Getting Started](GETTING_STARTED.md), create a Study and confirm that you can read its Overview locally. You need Python 3.10+ and the full OpenSci software folder. Direct MCP needs no MCP SDK or extra Python package. Have these four values ready:

| Value | Beginner Windows example | Where to find your value |
| --- | --- | --- |
| Python executable | `C:/Tools/Python/python.exe` | `python` in software `config/runtime.local.json`; macOS/Linux: `command -v python3`, then check its version |
| Software folder | `C:/OpenSci` | Folder containing `scripts/hub_mcp.py` |
| Records folder | `C:/OpenSci-Data` | Your selected folder containing `config/hub.local.json` and saved Studies |
| Study ID | `STUDY-001` | ID shown after creating/listing your Study |

On macOS use your own paths, for example `/Users/yourname/OpenSci` and `/Users/yourname/OpenSci-Data`; on Linux, `/home/yourname/OpenSci` and `/home/yourname/OpenSci-Data`. Replace `yourname` and every sample path with a real absolute path. In JSON/TOML arguments do not use `~` or shell variables: they are not automatically expanded.

Copy software `config/mcp.unselected.example.json` to records `config/mcp.policy.local.json`. Open the copy in a text editor and replace `connection_id` with a unique label, such as `opensci-codex-01`. Keep the other fields unchanged for now. This label is not a password. When connecting a second client, make a **separate policy file and connection ID**, for example `mcp.claude.local.json` / `opensci-claude-01`, and use that path in its commands. All clients can point to the same authoritative records folder; do not copy the Study to each client.

Stop the connection before selecting its Study. On first setup it is not running yet. In PowerShell:

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
$OpenSciPython = (Get-Content -LiteralPath '.\config\runtime.local.json' -Raw -Encoding UTF8 | ConvertFrom-Json).python
& $OpenSciPython -E -s -B scripts/select_study_connection.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json --study-id STUDY-001 --connection-stopped
```

On macOS/Linux, run from your software folder, substituting actual paths:

```bash
/usr/bin/python3 -E -s -B scripts/select_study_connection.py --coordinator-root /home/yourname/OpenSci-Data --policy /home/yourname/OpenSci-Data/config/mcp.policy.local.json --study-id STUDY-001 --connection-stopped
```

`Study selected.` confirms selection. This also enables permitted agent writes. For a read-only connection, set `allow_write` back to `false` in the policy before launch. Leave `allow_remote_checks` false for the first read. The identity/context fields remain unknown unless you have a trusted host binding; a model's name is not proof of project identity.

<a id="direct-mcp-installation"></a>
## 2A. Codex: connect the local server

Use either the direct connection here or the plugin route below for a given client, so you do not accidentally expose duplicate tools with different identities.

Codex keeps MCP entries in `~/.codex/config.toml` by default (`%USERPROFILE%\.codex\config.toml` on Windows). If you configured a different Codex home, use its active file. Back up the file and merge **only** the following table, preserving other settings. If the name already exists, review that entry rather than adding a duplicate. [Official MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

```toml
[mcp_servers.opensci]
command = 'C:/Tools/Python/python.exe'
args = ['-E', '-s', '-B', 'C:/OpenSci/scripts/hub_mcp.py', '--coordinator-root', 'C:/OpenSci-Data', '--policy', 'C:/OpenSci-Data/config/mcp.policy.local.json']
cwd = 'C:/OpenSci'
startup_timeout_sec = 20
tool_timeout_sec = 60
enabled = true
```

Replace the executable and paths with step 1's values. On macOS/Linux change all paths, including `cwd`, to native absolute paths. The reusable template is [mcp.desktop.example.toml](../config/mcp.desktop.example.toml).

Restart the local client/server and start a new conversation. In Codex CLI run `codex mcp list`, then `/mcp` inside Codex to inspect the active connection. A desktop host exposing **Settings → MCP servers** can add the same STDIO command/arguments and restart it there. Complete the common acceptance steps below; a listed configuration alone does not prove a successful read. Local configuration does not automatically connect a hosted/cloud chat.

### Optional: install the OpenSci Study plugin

Use this only in a client supporting OpenAI's plugin format. The repository root contains `plugin.json`, `mcp.json`, assets and the server; `.agents/plugins/marketplace.json` points to that root. Python must be launchable as `python` in the host environment. If you need an absolute Python path, use direct MCP instead.

Copy `config/plugin.connection.example.json` into a new `OpenSci/connection.json` under `%LOCALAPPDATA%` on Windows. Press Windows+R and enter `%LOCALAPPDATA%` to open that location. On macOS/Linux the OpenSci entry script uses `~/.config/opensci/connection.json`; alternatively set `OPENSCI_CONNECTION_FILE` to an absolute file path in the host process. Edit only your actual values:

```json
{"schema_version":1,"coordinator_root":"C:/OpenSci-Data","policy":"C:/OpenSci-Data/config/mcp.policy.local.json"}
```

Save UTF-8 without an extra `.txt` suffix. Keep this operator-owned file outside plugin caches; missing or invalid settings stop the plugin. In a compatible Codex CLI use `codex plugin marketplace add yanboyang97/OpenSci`, then `codex plugin add opensci-study@opensci` if supported by that installed version. A compatible desktop marketplace can select and install **OpenSci Study** from the repository. If the command/UI is unavailable, use direct MCP above and consult the [current plugin guide](https://developers.openai.com/plugins/build/plugins). Start a new conversation after installation. The GitHub download does not imply a public directory listing or provision a hosted service.

<a id="claude-desktop"></a>
## 2B. Claude Desktop: add the local MCP entry

1. Install/sign in to Claude Desktop for your operating system. Open the app's **Settings → Developer → Edit Config**. On Windows the file is `%APPDATA%\Claude\claude_desktop_config.json`; on macOS it is `~/Library/Application Support/Claude/claude_desktop_config.json`. On Linux beta use the file opened by the app, avoiding a guessed configuration location. If managed settings hide this control, ask your administrator or use an allowed Claude Code installation. [Official local-server tutorial](https://modelcontextprotocol.io/docs/develop/connect-local-servers)
2. Back up the file. Merge the `opensci-study` entry below into its existing `mcpServers` object, preserving other entries. For an empty file, the whole example is valid. Use the separate policy you prepared for this client.

```json
{
  "mcpServers": {
    "opensci-study": {
      "command": "C:/Tools/Python/python.exe",
      "args": ["-E", "-s", "-B", "C:/OpenSci/scripts/hub_mcp.py", "--coordinator-root", "C:/OpenSci-Data", "--policy", "C:/OpenSci-Data/config/mcp.policy.local.json"]
    }
  }
}
```

3. Substitute all paths from step 1; on macOS/Linux use the absolute Python path and native software/records/policy paths. JSON strings can use forward slashes on Windows. Do not add comments or trailing commas. Fully quit/reopen Claude Desktop, then inspect **Connectors / Manage connectors** and Developer status for `opensci-study`.
4. Start a conversation, enable this connector if needed, and perform the acceptance steps below. OpenSci's ZIP is not a Claude `.mcpb` desktop extension, so do not import it through an extension installer. The local entry does not by itself connect Claude's website/mobile app.

<a id="claude-code"></a>
## 2C. Claude Code: register a stdio command

Install/sign in to Claude Code in the environment that can access your records. In Windows PowerShell, with your actual paths:

```powershell
claude mcp add --transport stdio --scope user opensci-study -- C:/Tools/Python/python.exe -E -s -B C:/OpenSci/scripts/hub_mcp.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json
claude mcp get opensci-study
```

For macOS/Linux:

```bash
claude mcp add --transport stdio --scope user opensci-study -- /usr/bin/python3 -E -s -B /home/yourname/OpenSci/scripts/hub_mcp.py --coordinator-root /home/yourname/OpenSci-Data --policy /home/yourname/OpenSci-Data/config/mcp.policy.local.json
claude mcp get opensci-study
```

Substitute step 1's paths and this client's separate policy. Quote any path containing spaces as one argument. `--scope user` registers for your user; it does not publish a project setting. The `--` separates Claude's options from OpenSci's arguments. Start Claude Code, use `/mcp` to inspect connection status, then perform the common acceptance. To remove this registration later, run `claude mcp remove opensci-study --scope user`; saved OpenSci records remain. [Claude Code MCP commands](https://code.claude.com/docs/en/mcp)

<a id="ordinary-chat"></a>
## 2D. ChatGPT: connect your private tunnel

ChatGPT in a browser cannot launch your local Python command directly. Run the official Secure MCP Tunnel client on the computer holding OpenSci, using a separate selected policy. You need access to the intended Platform organization and ChatGPT workspace. Creating a tunnel requires **Tunnels Read + Manage**; the runtime key and connector operator need **Read + Use**. Associate the tunnel with the target ChatGPT workspace as well as its owning organization. [Official tunnel setup](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

### Prepare the tunnel profile

Open [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels), create/select your private tunnel, and record its `tunnel_id` and organization ID. Download the official client for your OS from that page or its linked release. Keep the binary in a chosen folder. Confirm its published provenance/checksum where supplied and inspect `help quickstart`; OpenSci does not redistribute this client.

For a Windows example client at `C:\Tools\tunnel-client\tunnel-client.exe`, run:

```powershell
& 'C:\Tools\tunnel-client\tunnel-client.exe' help quickstart
& 'C:\Tools\tunnel-client\tunnel-client.exe' init --sample sample_mcp_stdio_local --profile opensci-chat --tunnel-id YOUR_TUNNEL_ID --mcp-command 'C:/Tools/Python/python.exe -E -s -B C:/OpenSci/scripts/hub_mcp.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json'
```

Replace the tunnel ID and all paths; if a path contains spaces, preserve the quoting required by the client's help. Note the generated profile's **actual absolute file path** from its output. The profile is the local file telling the tunnel how to start OpenSci; do not assume it is named `chat.local.yaml`.

For macOS/Linux, use the official native binary's absolute path with the same `init` options and your native Python/server/records/policy paths. The `--mcp-command` value remains one quoted command string. If initialization requests credentials, supply them locally using the protected process-environment method below; never put a literal key in command history or the profile.

### Start on Windows

Copy software `config/chat.example.json` to software `config/chat.local.json`. Fill in:

| Field | Value to use |
| --- | --- |
| `client` | Absolute path to the downloaded executable |
| `client_sha256` | Its SHA-256 from `Get-FileHash -Algorithm SHA256` after checking the download's provenance |
| `profile` | Actual generated profile path |
| `organization_id` | Your intended Platform organization ID |
| `pid_file`, `health_file`, `log_file` | Separate files in a private directory, e.g. `C:/OpenSci-Data/connection/`; create the directory first |

For the example executable, copy the hash returned by `(Get-FileHash -LiteralPath 'C:\Tools\tunnel-client\tunnel-client.exe' -Algorithm SHA256).Hash.ToLowerInvariant()` into `client_sha256`.

Inspect the installed client's help for the flags used by `Start-Study-Chat.ps1`, especially `--profile-file`, `--mcp.stdio-send-initialized-notification`, and PID/health/log flags. Do not bypass the launcher's checks if the client version is incompatible.

To diagnose a profile, run `doctor --profile opensci-chat --explain`. If it needs the runtime key, this PowerShell pattern keeps entry hidden and clears the temporary environment on exit:

```powershell
if (Test-Path Env:CONTROL_PLANE_API_KEY) { throw 'Use a fresh terminal without an existing tunnel key.' }
$OpenSciSecret = Read-Host 'Tunnel runtime key' -AsSecureString
try {
    $env:CONTROL_PLANE_API_KEY = [System.Net.NetworkCredential]::new('', $OpenSciSecret).Password
    & 'C:\Tools\tunnel-client\tunnel-client.exe' doctor --profile opensci-chat --explain
} finally {
    Remove-Item Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
    $OpenSciSecret.Dispose()
}
```

If initialization also requires the key, run the reviewed `init` command inside the same `try` block before `doctor`. For one-time use, double-click `Start-Study-Chat.cmd` and enter the restricted key at its hidden prompt; keep that window open. For saved-key background use, follow the optional Windows steps below. Inspect readiness at the local health address written to your configured `health_file`.

<a id="optional-remember-the-key-and-connect-in-the-background-windows"></a>
### Optional: remember the key and connect in the background (Windows)

OpenSci 1.1.0 adds an optional saved-key mode. The existing one-time prompt remains available. This key connects the tunnel; it is separate from keys used to call a model. Windows DPAPI (the Windows facility for encrypting data for your signed-in account) encrypts the key on this computer. OpenSci never generates a real OpenAI key locally or extends its expiry.

1. Complete the tunnel profile and `config/chat.local.json` setup above. Stop the old tunnel window with **Ctrl+C**. Keep only one client for this tunnel.
2. Open the official [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels) and follow [OpenAI's runtime-key guidance](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels). Select the same organization as your tunnel. Create a dedicated restricted API key with **Tunnels Read + Use** only. Select a long expiry that the account permits, or no expiry only if that option is actually available. Keep the organization and ChatGPT workspace association unchanged. If the permission or expiry option is unavailable, ask the organization administrator; do not substitute a broad model/admin key.
3. In File Explorer open your OpenSci installation folder and double-click **Manage-Study-Connection.cmd**. Enter **1**. A small Windows form opens. Paste the new key into its masked field once. Do not paste it into a conversation, a command, or a JSON file. Record the platform expiry in the optional `YYYY-MM-DD` field; a blank field does not remove platform expiry.
4. Leave **Start automatically after I sign in to Windows** checked if desired. Click **Save encrypted and connect**. The key is saved under `%LOCALAPPDATA%\OpenSci\connections\<connection-id>\credential.dpapi`; the form never saves a plaintext key. The private folder is restricted to your Windows account and SYSTEM. The optional sign-in entry is named `OpenSciStudy-<connection-id>` in your user's Windows Run settings; it contains paths, never the key.
5. In the connection menu enter **2 Status**. Wait briefly and check `stored_key: true`, `worker_running: true`, `client_running: true`, and `ready: true`. With auto-start selected, `start_at_sign_in` is also true. Finally ask the ChatGPT connection to read your selected Study Overview. A healthy client alone does not prove the ChatGPT tool call works.
6. Close the setup/menu window. The background process continues. On subsequent Windows sign-in it starts automatically if selected; otherwise double-click **Start-Study-Chat.cmd** to start it without re-entering the key. This is a per-user background process, not a system service: the computer must remain awake and online, and the user must remain signed in. Locking the screen is different from signing out. A sleeping/offline computer cannot serve live requests.

The background worker supplies the decrypted key only to the tunnel child's process environment. It checks the client checksum and binds the stored credential to the configuration path, organization, client hash and profile hash. Ordinary OpenSci updates at the same installation path retain these settings. Changing the client or profile requires reviewing the new values and saving the key again. The client handles transient network reconnection; if the client exits, the worker tries at most five launches, with increasing delays, then reports `attention_required`.

| Need | Action in Manage-Study-Connection.cmd |
| --- | --- |
| Closed the menu/window accidentally | Check **2 Status**; a saved-key worker keeps running. Use **3 Start** if stopped. No new tunnel or Study is needed. |
| Stop now before backup/update | **4 Stop**. Wait until worker/client are false. The sign-in preference stays saved. |
| Replace an expired/revoked key | Create a new restricted key in the same organization, then **1** to save it. Test the connection, then revoke the superseded key in Platform. |
| Disable automatic sign-in launch | **5**. Use **4** too if you want to stop the current connection. |
| Return to one-time input | **6** stops, disables startup and removes this stored key. Revoke it separately in Platform if no longer needed. |
| Readiness stays false | Check internet access, account permission, actual key expiry and the configured local tunnel log. Do not enable raw HTTP logging or share secret-bearing logs. |
| Restored onto another PC/account | Recreate the restricted key or securely obtain it from your password manager and run setup again. A copied DPAPI file is not a portable key backup. |

If a save was interrupted, reconnect with the same connection identity and query the original request receipt before retrying. Do not create a new request ID merely because the window closed. This Windows feature does not install a Linux service or change another assistant's credentials.


### Start on macOS/Linux

Use an interactive **Bash** terminal (enter `bash` first if your current shell differs). Replace paths and IDs in this example; the native binary is assumed here to be `/home/yourname/Tools/tunnel-client`:

```bash
if [ -n "${CONTROL_PLANE_API_KEY+x}" ]; then
  printf '%s\n' 'Use a fresh terminal without an existing tunnel key.'
else
  read -r -s -p 'Tunnel runtime key: ' CONTROL_PLANE_API_KEY
  printf '\n'
  export CONTROL_PLANE_API_KEY
  trap 'unset CONTROL_PLANE_API_KEY' EXIT
  if /home/yourname/Tools/tunnel-client doctor --profile opensci-chat --explain; then
    /home/yourname/Tools/tunnel-client run --profile opensci-chat --control-plane.organization-id YOUR_ORGANIZATION_ID --mcp.stdio-send-initialized-notification
  fi
  unset CONTROL_PLANE_API_KEY
  trap - EXIT
fi
```

Check the installed client's help before launch; only continue after `doctor` succeeds. If `init` requires the key, run the reviewed initialization after `export` and before `doctor`. Use one client per tunnel, keep the terminal and computer awake, and stop with Ctrl+C when finished. Confirm the key has been unset or close this dedicated terminal after interruption.

### Add it to ChatGPT and make a real tool call

In ChatGPT **Plugins**, choose **+ → Add custom MCP server**, set **Connection: Tunnel**, select/paste the same tunnel ID, complete the required authentication and disclosure, and create the private plugin. Workspace policy may control access. [Custom MCP setup](https://developers.openai.com/api/docs/guides/custom-mcp-server)

Keep the tunnel healthy during discovery. In a new chat enable/select the plugin, then perform the acceptance steps below. If the tunnel is missing, check the workspace association and Read + Use permission. A computer going to sleep or a stopped client makes live calls unavailable but does not erase saved Study records. Refresh the plugin's tools after server updates. This is a private single-user connection, not a shared hosted service.

<a id="connection-acceptance"></a>
## 3. Verify, save and recover in any client

1. Ask: “Read OpenSci's connection capabilities, resolve the selected Study, then read its Overview. Tell me the Study ID and goal. Do not save anything yet.” The tools are `opensci_get_capabilities`, `opensci_resolve_study_link` and `opensci_get_study_brief`; the assistant should use the schema it receives. Check that the ID matches your intended Study.
2. If you want to test saving, ask: “Save this as a progress note: connection check completed; next step is to review the selected papers. Preserve the existing progress and report the committed receipt.” Inspect the proposed complete progress snapshot before saving; structured progress replaces the previous snapshot. A chat reply alone is not a save.
3. Verify `committed: true`, retain the request ID/revision, and read the Overview back. A read-only policy deliberately refuses step 2. If a write times out, query the original request through the same connection identity; follow [receipt recovery](TROUBLESHOOTING.md#save-recovery). Do not create a replacement write merely because the response was lost.

| Symptom | Smallest useful check |
| --- | --- |
| No OpenSci tools | Confirm the correct local client/host, full server folder, executable/path spelling, valid JSON/TOML and restart |
| `selection_required` | Stop the connection, select the Study in its actual policy, then restart |
| Overview is for the wrong Study | Stop immediately and correct the selected policy; do not save |
| Read works but save is refused | Check `allow_write`, selected Study and operation-specific grants; do not broaden unrelated access |
| Remote analysis is refused | Only when needed, review `allow_remote_checks` and the existing executor setup |
| Tunnel is healthy but ChatGPT cannot discover it | Check organization/workspace association, connector permissions and chosen tunnel ID |
| Native Word/browser work is unavailable | MCP access does not supply those apps or desktop control; complete their own setup |

To switch Studies, stop this client/server and tunnel, rerun step 1 for the new Study, and restart. To revoke selection, replace `--study-id STUDY-001` with `--clear` while stopped. Policies are fixed when a process starts; editing a running process's file does not reload its permissions. Removing a client entry does not delete the records.

## Existing remote computers

For an already provisioned remote coordinator use [mcp.remote.example.toml](../config/mcp.remote.example.toml) with a server-enforced fixed SSH command. If inbound SSH is unavailable, follow the existing [SSH reverse connection guide](STUDY_CONNECTION.md#remote-access-when-the-coordinator-is-a-local-computer). The loopback gateway is not an HTTP MCP endpoint. Do not publish it or Zotero's port. Setting up new accounts, host keys and remote deployment is separate from choosing one of the clients above.
