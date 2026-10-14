# Plugins and MCP

[Handbook](../DOCUMENTATION.md) · [Requirements](INSTALLATION.md)

**OpenSci Study** is the distributable assistant plugin. **Study MCP Server** is its bundled local server, implemented by `scripts/hub_mcp.py`. Both use the same Operation Service and protected coordinator. Installation includes no Study records, keys, personal library data, organization IDs or hosted connection.

MCP is the connection protocol that lets an assistant use OpenSci's tools. A plugin packages that connection for a supported client. First finish [Getting Started](GETTING_STARTED.md) and create a Study. If you want to use your phone to continue a computer task, follow [Research from Your Phone](MOBILE_RESEARCH.md); return here to connect that computer's assistant to the Study.

## Choose a connection

| Use | Connection | Required setup |
| --- | --- | --- |
| Local Work or a local MCP client | OpenSci Study plugin, or direct stdio MCP | Python 3.10+, local coordinator and protected policy |
| Ordinary Chat | Your own private Secure MCP Tunnel and custom MCP connection | Eligible account, your tunnel, authorized workspace and restricted key |
| Remote Work | Restricted SSH command or authenticated loopback gateway inside SSH | Operator-managed accounts, host keys, selected Study and per-connection token |

These packages are distributed through GitHub. They are not automatically listed in OpenAI's universal directory. Public directory submission of local MCP plugins requires the platform's partner eligibility and review; see [desktop-only submissions](https://developers.openai.com/plugins/deploy/desktop-only). Do not publish a personal tunnel as a shared service. OpenSci currently provides a private single-user connection, not a multi-user hosted service.

## Prepare the protected policy

Complete [first setup](GETTING_STARTED.md). Copy `config/mcp.unselected.example.json` to `COORDINATOR/config/mcp.policy.local.json`. Replace `connection_id` with a new local identifier. It is an identity label, not a credential. An unselected policy has `studies: []`, `allow_write: false` and no native project context.

For the beginner Windows setup, `COORDINATOR` means `C:\OpenSci-Data`. Use File Explorer to copy the file, then Notepad to replace the placeholder connection name with one such as `opensci-desktop-01`. Use a different name for each connection and retain it when recovering that connection's requests.

After creating the intended Study, stop its connection and run the operator command below from the installation directory. Replace the example paths and ID:

```text
python -E -s -B scripts/select_study_connection.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json --study-id YOUR-STUDY --connection-stopped
```

If you configured an absolute Python path during first setup, use this PowerShell version from the software folder instead:

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
$OpenSciPython = (Get-Content -LiteralPath '.\config\runtime.local.json' -Raw -Encoding UTF8 | ConvertFrom-Json).python
& $OpenSciPython -E -s -B scripts/select_study_connection.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json --study-id STUDY-001 --connection-stopped
```

Replace `STUDY-001` with the ID you created. `Study selected.` confirms the saved selection. On first setup no connection is running yet; for an existing connection, disable it in the assistant and stop its tunnel launcher before changing the selection.

This selects the Study and enables its permitted agent writes. If only reading is wanted, keep `allow_write: false` in the protected file before starting. Use `--clear` instead of `--study-id YOUR-STUDY` to revoke the selection while stopped. Restart after every policy change. The process does not reload grants from edits made while it runs.

## Install the OpenSci Study plugin

The repository root is the plugin root: `plugin.json`, `mcp.json`, the Python server and assets are bundled together. The marketplace at `.agents/plugins/marketplace.json` points to that root. Python must be available as `python` in the host's execution environment; use direct MCP below when an absolute interpreter path is needed.

Create an operator-owned connection file from `config/plugin.connection.example.json`:

- Windows: `%LOCALAPPDATA%/OpenSci/connection.json`.
- Linux: `~/.config/opensci/connection.json`.
- Alternative: set the host process's `OPENSCI_CONNECTION_FILE` to an absolute path.

Set `coordinator_root` and `policy` to the existing absolute paths. Protect this file and the policy from unauthorized edits. Keep them outside the plugin cache so an update cannot replace them. The plugin refuses to start when this file is missing or invalid.

On Windows, press Windows+R, enter `%LOCALAPPDATA%`, and open it. Create an `OpenSci` folder there, copy `config/plugin.connection.example.json` into it, and rename the copy to `connection.json`. Open it in Notepad. Its two sample paths already match the beginner setup; change them only if you used different folders. Save as UTF-8 and make sure the filename does not end in `.json.txt`.

In a client that supports local marketplaces, add the repository as a marketplace with `codex plugin marketplace add yanboyang97/OpenSci`, or open its local checkout and select the OpenSci marketplace in the desktop plugin browser. Install **OpenSci Study** and start a new conversation. In Codex CLI 0.162.1+, installation is also available as `codex plugin add opensci-study@opensci`. Consult the current [plugin packaging and marketplace guide](https://developers.openai.com/plugins/build/plugins) if the host presents a different installation UI.

The downloadable plugin ZIP has its manifest at the archive root and contains the same audited server source. Installing a plugin does not create a coordinator or grant access.

<a id="direct-mcp-installation"></a>
## Direct MCP installation

No MCP SDK or extra Python package is required. Merge the following server entry into a client that supports stdio MCP, substituting actual paths. Do not replace unrelated client settings.

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

For TOML clients use `config/mcp.desktop.example.toml`. On Linux substitute `/usr/bin/python3` and Linux paths. The standalone MCP archive includes the runtime and documentation so imports resolve without installation into global Python.

After connecting, read capabilities and resolve the selected Study, then read its Overview. Unselected access returns `selection_required` and denies Study reads and writes. A write-enabled policy exposes `opensci_execute_command`; it does not expose experiment approval, submission, cancellation or arbitrary shell execution. Save only on the user's instruction and retain the committed receipt. On timeout query the original request ID through the same connection identity.

<a id="ordinary-chat"></a>
## Connect ordinary Chat

Follow the official [Secure MCP Tunnel setup](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) using your own organization and authorized ChatGPT workspace. Download the official client separately; OpenSci does not redistribute it. Use its `init` command to generate a stdio profile for the absolute Python/server/coordinator/policy command above, and use `doctor` to check that profile. Keep the profile private.

On Windows copy `config/chat.example.json` to `config/chat.local.json`. Set the verified client path and SHA-256, generated profile path, your organization ID, and PID/health/log locations in a new private connection directory. Create those parent directories first. Confirm the installed client's help supports the launcher's options. Run `Start-Study-Chat.cmd`; enter a restricted **Tunnels Read + Use** key in its hidden local prompt. Do not paste the key into a chat or save it in the profile. Renew it before the expiry you chose. The launcher stores the key only in its process environment and removes it on normal exit.

Keep one client per tunnel running. Add your tunnel as a private custom MCP connection in the account's plugin settings, restrict it to the intended workspace and refresh its tools after server updates. Keep the computer awake and the connection window open. Stopping the connection preserves saved records but makes live reads and saves unavailable. Linux users can run the official client directly under its documented credential handling.

This publication provides the code and setup instructions. It does not provision a tunnel or register another user's account. The [Study connection reference](STUDY_CONNECTION.md) covers scoped tools, structured progress, native project links and receipt recovery.

## Remote access

Use `config/mcp.remote.example.toml` only after provisioning a server-enforced fixed SSH command. If inbound SSH to the coordinator is unavailable, `scripts/study_remote.py` supports a token-authenticated loopback gateway carried inside an operator-managed SSH reverse forward. Follow [remote connection setup](STUDY_CONNECTION.md#remote-access-when-the-coordinator-is-a-local-computer). Never expose its port or Zotero's local API to the public internet. The gateway is not an HTTP MCP endpoint.
