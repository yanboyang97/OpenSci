# Research Workspace

Research Workspace is the main OpenSci entry for creating and continuing studies. It keeps one authoritative study record on the Coordinator. Development Workspaces may be local, WSL or SSH hosts; Execution Nodes are selected separately. See the [Feature Catalog](FEATURES.md) for all modules.

## Open the workspace

On Windows, open `Start-OpenSci.cmd` or an existing `OpenSci.lnk` in the project root. The [read-only list command](docs/GETTING_STARTED.md#command-context) selects configured tools without connecting to a remote host. For script examples below, use the command context in that guide. `-Python` selects an interpreter explicitly; otherwise `config/runtime.local.json` takes precedence over PATH discovery. The command wrapper's execution-policy setting applies only to its child process; institutional policy still takes precedence.

```text
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data menu
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data show --study STUDY-001
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data history --study STUDY-001 --limit 20
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001
```

## Menu functions

| Entry | Purpose |
| --- | --- |
| 1 Browse Studies | Read locally recorded studies |
| 2 Create Study | Create a study through the Operation Service and receive a durable receipt |
| 3 Resume Study | Check the selected Development Workspace against the recorded source |
| 4 Choose Development Workspace | Check and select the workspace for evidence and development work |
| 5 Choose Execution Node | Choose the node for future tasks; existing tasks keep their original bindings |
| 6 Check Development Environment | Run the configured development environment checks |
| 7 Preview Evidence Review | Preview inputs, models, limits and the review-plan digest |
| 10 Study Overview | Read bounded saved goals and structured progress |
| 11 Save Discussion Progress | Save discussion, hypotheses, evidence references and next steps without Git |
| 8 Record Progress | Record a human planning phase and notes after source checks |
| 9 Literature Workspace | Check local capabilities or execute a prepared literature request |
| 0 Exit | Close the menu |

Discussion Study creation does not require Git or nodes. Source-dependent checkpoints still require reviewed research provenance. It does not authenticate remote nodes. The menu prints a request ID before current study creation or updates; preserve it if interrupted and query the receipt before creating replacement work. Follow [Daily Use](docs/DAILY_USE.md) for complete examples.

Workspace and execution-node choices list only enabled nodes with the appropriate role. Select a displayed number or ID; blank cancels. Record Progress lists planning phases the same way. With no configured Execution Node, the menu explains what is missing and leaves the study unchanged. **Check Development Environment** checks the selected study workspace; it is not the initial configuration wizard.

## Workspaces and remote checks

Configure actual accounts, absolute paths and interpreters in ignored local configuration. In a source-backed workflow, both source workspaces must share one clean Git commit and the same origin spelling. A separated coordinator/runtime does not substitute for the per-Study research repository. Separate independent commits of identical files do not establish a shared source baseline.

Resume, workspace selection, Record Progress and development steps may contact the selected host. The menu asks before connecting. SSH uses an existing alias, trusted host key and noninteractive authentication; it never updates known_hosts. Choosing a workspace transfers neither files nor credentials and does not start a desktop chat or model session.

Before a workspace switch, stop edits, synchronize the reviewed commit and reconcile original run IDs. Source and destination must be reachable, clean and match the Coordinator. Source changes require a deliberate Record Progress operation. Current records are limited to 4,000,000 UTF-8 bytes; full history is retained separately.

## Evidence and execution

Place small reviewed imports under `coordination/imports/`, then register them with the Operation Service's `attach` operation and their trusted original SHA-256. Register tasks before approvals and runs. Registration preserves an immutable snapshot; it does not establish scientific validity or grant approval.

Task Preparation produces a draft. Only an independent human submitter approves and runs a fixed task. Research Workspace, Assistant Access and Run Monitor never approve, submit or rerun experiments. See [Execution](IMPLEMENTATION.md) and [Record Reference](RECORDS.md).

## Continue after an interruption

Read the study, planning phase, latest note, source binding and original run IDs. For an uncertain operation, query its original receipt and retain the exact request contents. For an uncertain experiment, inspect the original run on its Execution Node. Do not infer process death from a stale heartbeat or create a replacement run automatically.

Use [History and Recovery](HISTORY.md) for maintenance plans and [Backup and Transfer](BACKUP_AND_MIGRATION.md) for a new recovery directory. A restored copy must not become a second writer. The [Research Brief](RESEARCH_BRIEF.md) is a dated snapshot and sends nothing automatically.

The [Claude Development Launcher](CLAUDE_LAUNCHER.md) is a separate Windows entry. Menu option 9 uses the [Literature Workspace](docs/LITERATURE.md), including its protected grants, per-operation receipts and native writing boundaries.

For the configured private Study connection, double-click `Start-Study-Chat.cmd`. Keep that window open; see [Study connections](docs/STUDY_CONNECTION.md).
