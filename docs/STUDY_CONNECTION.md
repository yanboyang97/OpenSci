# Continue a Study in Chat or Work

OpenSci keeps selected research progress in one authoritative Study. Local and remote Work remain full research entry points; ordinary Chat is an optional way to discuss, reason and revise text. You may start in either mode. Reading or saving progress never starts Work, creates another conversation, calls an extra model or submits an experiment.

For step-by-step phone use, start with [Research from Your Phone](MOBILE_RESEARCH.md). That guide covers the host's connection to your computer; this reference describes OpenSci's narrower Study connection and saved-progress contract.

## Current capability and limits

The connection reads and saves structured progress in a selected Study. Ordinary Chat uses a private tunnel; local and remote Work use their configured MCP transport. A trusted host may supply native project identity. Without that context, the connection remains scoped to one explicitly selected Study and reports its source as unknown.

A Study can register a research workspace when creating a Study. Adding or replacing that workspace after creation is not yet exposed as a supported operation. Existing Studies created without source provenance can continue discussion and literature work; their source-dependent checkpoints and experiment preparation remain blocked. Do not edit the stored workspace or anchor manually.

The initial connection selects exactly one Study. Native project type, Chat/Work mode, execution host and conversation reference remain unknown when the host does not supply trustworthy context. A folder name, chat message, project instruction or path cannot grant access. A private connection identifies the configured connection, not a cloud human inferred from the server's OS account. It must remain private to its intended user/workspace.

## Locations and first use

Keep three responsibilities separate:

| Location | Purpose |
| --- | --- |
| `runtime_root`, for example `C:/OpenSci` | Installed scripts, examples and handbook |
| `coordinator_root`, for example `C:/OpenSci-Data` | The only authoritative Study records, history, evidence references and receipts |
| `research_workspace` | Optional primary research folder and additional source folders, identified separately per Study |

The new Study can have no Git repository and no execution node. Discussion, structured progress and literature operations remain available subject to their own grants. Checkpoints and experiment registration requiring source provenance are blocked until a reviewed Git research workspace is available. Additional folders do not establish multi-repository experiment provenance. Runtime installation files never substitute for research source commits.

1. Select one coordinator directory. Copy `config/hub.study.example.json` there as `config/hub.local.json` if no execution/development nodes are needed. No credentials belong in it.
2. In the root launcher, set an absolute coordinator in `config/studies.local.json` using `config/studies.example.json`. The launcher reads this location without changing other local runtime settings. Alternatively pass `-CoordinatorRoot` to the launcher or `--coordinator-root` to `hub.py`, `hub_command.py` or `hub_mcp.py`.
3. Choose **2 Create Study**, enter its stable ID and goal, and retain the receipt. The menu supports creation without Git. For explicit automation, use the operator-only `create_study` request from `config/create-study.example.json`; `binding` and `research_workspace` may both be null. The source-backed `init` entry has its Git-backed creation contract.
4. Choose **10 Study Overview** to read saved progress and **11 Save Discussion Progress** to save a summary, decisions, hypotheses, evidence references, open questions and next steps. Menu 8 remains the source-checked checkpoint entry.

For example, from the installation directory with a configured Python:

```text
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data brief --study EXAMPLE-STUDY
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data execute --request config/create-study.local.json
```

Read before creating or saving; replace example IDs and revisions. A successful save means `committed=true`. It does not prove scientific correctness, file access or experiment approval.

## Connect ordinary Chat

Complete the installable plugin, direct MCP and tunnel configuration steps in [Plugins and MCP](PLUGINS.md).

Use a private [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) and a [custom ChatGPT MCP connection](https://developers.openai.com/plugins/deploy/connect-chatgpt) supported by the actual account. The local stdio server remains bounded; it does not expose an arbitrary shell, filesystem proxy or public HTTP endpoint.

On Windows, double-click `Start-Study-Chat.cmd` to run `Start-Study-Chat.ps1`. Its protected `config/chat.local.json` selects the official client, expected client SHA-256, profile, organization and local PID/health/log files. The launcher checks client integrity and refuses to overlap a recorded running process. The profile fixes the single MCP command, coordinator and policy. `config/mcp.study.example.json` illustrates the policy; protected identity fields are never accepted inside a model's tool request.

The launcher prompts locally for a restricted Tunnels Read + Use key. The key remains in that process and its children, is removed on normal exit, and is never written to a file or chat. No service, scheduled task, automatic startup or secret persistence is installed. Keep the computer and connection window open. Renew the restricted key before its chosen expiry; closing the window, suspending the computer or losing connectivity makes live reads/saves unavailable. A retained snapshot is dated saved state, not a live successful save.

Run only one active tunnel client per tunnel ID. Stop the old writer before restarting. Refresh the custom connection's tools after a server tool-list change. Do not open optional runtime assistant/admin features to perform study synchronization. The OpenSci path uses only the configured `main` MCP channel and no model SDK. Connection health proves transport readiness only. It does not establish model activity, subscription usage or billing attribution.

In ordinary Chat, select the connected **OpenSci Study** app and ask:

> Continue the selected OpenSci Study. Stay in ordinary Chat, read the Study Overview, distinguish facts from hypotheses, and load only relevant details. Do not start Work or another conversation.

To save:

> Save these conclusions and next steps to the same Study. Read its latest revision first, use `save_progress`, retain evidence references, and return the committed receipt. Keep the original request ID/content after any timeout.

## Select a Study or leave the connection unselected

To leave a connection unselected or revoke the current selection, clear its grant. Stop the affected connection and use the operator command:

```text
python -E -s -B scripts/select_study_connection.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.chat.local.json --clear --connection-stopped
```

The protected connection policy may contain no Studies only when writes are disabled and native project context is null. Capabilities remain available, resolution returns `selection_required`, and all Study reads and writes are denied. This is a valid unconfigured installation, not a missing or fabricated Study.

To enable a real Study after creating it through the operator menu, replace `--clear` with `--study-id YOUR-STUDY` and restart the affected connection. The command verifies that the Study exists, selects only that Study, clears inferred native context, and preserves the configured connection identity. Linking a native project is still a separate receipted operator action. Running processes retain their loaded policy until stopped; editing a file alone does not revoke a live process.

Keep one stable protected identity for saving and recovering receipts. A `local_process` policy identifies the OS caller, so sandboxed and non-sandboxed processes can have different identities. A private single-user connection uses its configured connection principal. Do not change identity to recover someone else's receipt, and never replace an uncertain save with a new request ID.

## Tools and bounded context

| Tool | Behavior |
| --- | --- |
| `opensci_get_capabilities` | Protected scope, enabled operations, identity limitations and connection status; no inferred usage |
| `opensci_resolve_study_link` | Resolve protected native context or one explicitly selected Study; never creates on a miss |
| `opensci_get_study_brief` | Deterministic saved overview, revision, digest and time; at most 8192 UTF-8 bytes in its JSON value |
| `opensci_get_study_detail` | Revision-pinned JSON text fragments for omitted fields; concatenate pages before parsing; referenced files are not fetched |
| `opensci_execute_command` | Existing request envelope plus `save_progress`; agents cannot create Studies, bind projects or grant themselves access |
| Existing project, receipt, event and literature tools | Preserved names and contracts; large full-state responses may require a brief/detail read |

`save_progress` takes exactly `arguments: {"progress": {...}}`. Progress has `summary` plus five string arrays: `decisions`, `hypotheses`, `evidence_refs`, `open_questions`, `next_steps`. The summary permits 16000 UTF-8 bytes; each array permits 64 items of at most 4000 bytes; the whole progress object is limited to 48000 bytes and the command to 64000 bytes. Evidence strings are references, not assertions that files were read. The service attaches only protected source context. Original conversations stay in the native app.

Each save replaces the entire current progress object; it does not append to the previous summary or retain lists sent as empty arrays. Read the latest progress, including omitted detail, and carry forward content that should remain current. Earlier versions stay in history; follow [progress and history](DAILY_USE.md#saved-progress) to read them.

Overviews remove whole fields when needed and return `has_more` and revision-pinned detail references; they never truncate JSON silently. Record heads remain limited to 4 MB. Input and output MCP frames are limited to 256000 bytes. Capacity rejection preserves the old head. Saving calls no model and does not poll transcripts.

## Native project links and Work

The management channel is the local protected Operation Service CLI under an operator identity. `bind_project` takes `binding`; `unbind_project` takes `identity`. A binding contains `identity`, `display_name`, `availability`. Identity has exactly `provider`, `namespace`, `project_id`, `project_type` (`chatgpt_project`, `local_folder`, `remote_folder`) and `host_id`. Availability is `available`, `unavailable` or `unknown`.

Obtain native IDs from trusted host tools or explicit operator onboarding. One native project links to one current Study; multiple native projects can link to the same Study. Rename by updating the display value for the same identity. Temporary invisibility marks availability; it does not delete the Study. A copied folder or new worktree does not inherit a link or grant. Rebind using two separate receipted operations: unlink the old Study, then bind the new one. The intermediate unlinked state remains visible.

Links live inside authoritative records. The reverse index is rebuilt from heads on demand. Both coordinator and Study locks cover uniqueness checks and the single atomic commit. Create-and-bind uses one commit. Grants and links are separate: a missing grant or unavailable link never counts as ready. Multi-Study writes require protected native project context; model-supplied IDs do not select a broader write scope.

Local Work can use `config/mcp.desktop.example.toml` with the coordinator and policy paths. Remote Work needs the restricted fixed-command transport in `config/mcp.remote.example.toml` to the same coordinator. That example does not provision SSH accounts, keys or Windows SSH service. Do not create a second writable remote copy. Sharing a native project does not grant OpenSci access. Native project creation or instruction editing remains a host/UI step when no supported API exists; preserve existing instructions.

<a id="remote-access-when-the-coordinator-is-a-local-computer"></a>
### Remote access when the coordinator is a local computer

If the remote host cannot run a fixed command on the coordinator directly, an operator can use `scripts/study_remote.py` with an SSH reverse forward. The server binds only `127.0.0.1`, checks a 32-byte random token encoded as 64 lowercase hex characters before opening an MCP session, fixes the coordinator and policy, caps sessions at eight, and retains the existing MCP frame and operation limits. Tokens are separate from OpenAI keys. Store them with owner-only permissions and do not place them in commands, project files, logs or examples.

1. Provision an SSH connection with host-key verification. Check existing forwards first; do not interrupt or overwrite another session's forwarding configuration.
2. Start `study_remote.py server --port COORDINATOR_PORT --token-file PROTECTED_TOKEN --coordinator-root STATE_ROOT --policy PROTECTED_POLICY --ready-file NEW_READY_FILE` on the coordinator. For a port chosen by the OS, pass `--port 0` and read the local ready file. The policy should identify the dedicated private connection and verified remote entry.
3. Establish an operator-owned SSH reverse forward from remote `127.0.0.1:REMOTE_PORT` to coordinator `127.0.0.1:COORDINATOR_PORT`, with `ExitOnForwardFailure=yes`. Do not expose either port publicly. Deliver only the stdlib `study_remote.py` client and the per-connection token over the authenticated channel; do not copy coordinator records or OpenAI credentials.
4. Use `config/mcp.ssh-loopback.example.toml` on the remote host. A fixed-command Work entry may invoke the same client. The remote client has no authority to select another coordinator or policy. Read capabilities and resolve the Study before saving.
5. After disconnection, re-establish the same scope and query the original receipt. Stop the gateway and SSH forward when no longer needed, remove the temporary token on both endpoints, and remove the ready marker only after verifying that its process has stopped. The helper does not install a service or auto-start rule.

The plain loopback transport relies on the authenticated SSH channel for encryption and host verification. It is not a public MCP endpoint or multi-user server. Same-account filesystem access is not a security boundary.

For handoff, read the latest Study ID, revision, goal, selected evidence, questions and next steps. Local/remote Work may perform reading, analysis, planning, writing and development directly, with no Chat prerequisite. Switching entry points does not transfer complete transcripts, file permissions, uploaded files or running processes. Report unavailable files honestly. Actual host/model usage remains unknown unless reliably reported; no fixed percentage of savings is promised.

<a id="upgrade-and-recovery"></a>
## Upgrade and recovery

New Studies are ready for structured progress. If an imported record reports that preparation is required, use the named operation in that diagnostic and the preflight/apply procedure in [Maintenance Plans](UPGRADE_GUIDE.md). Stop all writers, verify a backup and reconcile original run IDs first. Preserve original bytes and history; never change format markers manually. Keep compatible source available for recovery.

After a timeout, query the original receipt through the same trusted principal and role. A private Chat connection receipt uses its configured connection principal; a local `--agent` OS identity is not interchangeable. After a revision conflict, read differences and prepare a deliberate new intent. Offline drafts stay unsaved until reconciled.

For a coordinator without Git, use `backup_project.py backup --workspace PATH --output NEW_ARCHIVE --quiesced --state-only`. This includes configured state/evidence/history and selected local policies; it excludes runtime software, external research folders, credentials and connection processes. Verify and restore into a new directory. Restoration never activates another writer. Planning rollback creates a new revision and preserves later receipts/evidence/runs; it does not erase later records or move external processes.
