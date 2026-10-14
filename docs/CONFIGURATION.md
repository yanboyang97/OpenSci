# Configuration Reference

[Handbook](../DOCUMENTATION.md)

Configuration consists of source-controlled examples and machine-specific settings. An example defines a format, not a provisioned service. Use absolute English paths and keep credentials out of Research Workspace configuration, Git, documentation and release archives.

## Configuration map

| File | Purpose |
| --- | --- |
| `config/runtime.local.json` | Windows wrapper runtime binding |
| `config/hub.local.json` | Coordinator node catalog |
| `config/providers.local.json` | Operator-provided review/literature providers on the executing node |
| `config/literature.local.json` | Optional protected library binding, directions, sources, grants, limits and accounting period |
| `tools/claude-launcher/machine.local.psd1` | Windows interactive development mapping |
| `config/command.local.json` | Operator-prepared request, not a persistent service switch |
| `config/mcp.policy.local.json` | Assistant Access study and operation policy |
| `config/observer.local.json` | Run Monitor run/source bindings |
| `coordination/resources.json` | Optional stable resource manifest |
| `config/device.local.json` | Optional machine-specific resource paths |
| `environments/*.local.json` | Environment snapshots captured for actual tasks |

Each component has its own loading rules; not every script reads runtime configuration or automatically prefers `.local.json`. In particular, `review_round.py` defaults to `config/providers.example.json`. Pass `--config config/providers.local.json` explicitly to use a local provider configuration.

## Windows runtime selection

`runtime.local.json` uses `schema_version: 1`. `python` points to Python 3.10+, `git` to the Git executable and `powershell` to PowerShell 7. For example, Python may be at `C:\Tools\Python\python.exe`; configure all executable paths for your own installation. The file is the authority for their exact locations.

Python selection is explicit `-Python` → runtime configuration → `python`, `py`, `python3` on PATH. Configured Git is added only to the launcher and child-process PATH and then restored. When Windows PowerShell 5 enters the Claude branch, it first selects configured PowerShell 7 and otherwise looks for `pwsh.exe` on PATH. Invoke calls with `ClaudeArgs` directly from PowerShell 7.

After moving or upgrading a tool, verify the new executable and version, update this project's runtime file and run the [read-only list command](GETTING_STARTED.md). Do not hide an invalid binding by rewriting global PATH or assume another device has the same cached-tool location.

## Node catalog

```json
{
  "schema_version": 1,
  "default_agent": "remote-agent",
  "nodes": {
    "remote-agent": {
      "role": "agent",
      "enabled": true,
      "transport": "ssh",
      "ssh_host": "opensci-dev",
      "account": "researcher",
      "workspace": "/home/researcher/OpenSci",
      "python": "/usr/bin/python3",
      "capabilities": {
        "codex": "unknown", "python": "available", "tests": "unknown",
        "claude": "unknown", "vertex": "unknown"
      }
    }
  }
}
```

This is a generic node example; read your ignored config/hub.local.json for actual bindings. `remote-agent` is an OpenSci node ID; `opensci-dev` is an SSH alias. A command's `--target` takes the node ID. `workspace` must be the actual absolute Linux directory, not a `~` expression. `python` is an executable name or absolute path without arguments. Capability values are declarations limited to `unknown`, `available`, `unavailable`, not live monitoring results.

Studies retain the complete Development Workspace configuration snapshot. Changes to the account, directory, interpreter or even capabilities can conflict with that snapshot. Do not treat this file as a casually refreshed status dashboard. Handle binding changes for existing studies through the [upgrade/migration workflow](UPGRADE_GUIDE.md), preserving old snapshots rather than replacing historical JSON.

Each node has one role: `agent` for a Development Workspace, `compute` for an Execution Node, or `control` for the Coordinator. Enable only the roles required for the installation. When adding co-located roles, use and verify distinct accounts and workspaces; changing an SSH alias alone does not establish isolation.

## Later service configuration

Before enabling live review, confirm the provider kind, model, endpoint, account/region eligibility, budget, credential source and negative tests. Example model names do not guarantee availability for your account. Windows DeepSeek/Kimi development and automated Claude Vertex review use separate configuration chains.

MCP policy defaults to read-only access and a fixed agent role. The observer reads trusted local directories or mounts and does not establish SSH connections itself. Before enabling either service, complete account, permission, source, reconnect and receipt acceptance using the [integration guide](../INTEGRATION.md), then update the operational record. Updating documentation does not enable these services.

## Literature settings

Use [literature.example.json](../config/literature.example.json) and the [protocol](../LITERATURE.md). Store directions, sources, Edge/Chrome selection, stable associations, provider references and finite limits here. Zotero storage and sync stay in Zotero. Source credentials use environment references; a consented Windows Zotero grant may use a named instance-bound Credential Manager reference. No secret value belongs in JSON. Pinned research settings preserve history but cannot raise current global limits or preserve revoked permissions. Installed browser/API/full-text rights require separate verification. Retention is a policy value; no automatic cleanup job is installed.

## Independent Studies and private Chat

`config/studies.local.json` selects the launcher coordinator. `hub.study.example.json` shows node-free configuration. `mcp.study.example.json` defines one private connection, explicit Study scope and trusted/unknown entry context. Keep policies operator-owned; local same-account execution is a single-user installation, not OS isolation. `Start-Study-Chat.ps1` uses local `chat.local.json`/YAML and a session-only restricted key. Do not distribute machine-specific `.local.*` files. Remote Work transport is separately provisioned; see [Study connections](STUDY_CONNECTION.md).
