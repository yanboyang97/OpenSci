# Operation Service, Assistant Access and Run Monitor

## Operation Service

The fixed coordinator holds the only formal state. CLI, restricted desktop MCP and the independent observer share command_service.py for transactions, receipts and role checks. They use the Python standard library; source checks additionally require Git. CLI and observation do not depend on desktop software, an MCP SDK, a model SDK, a database, Prefect or MLflow.

The desktop loop is read study → submit an already authorized structured decision → verify a durable receipt → read observer changes. Chat text is not imported as authoritative state, and ordinary assent does not approve experiments. An independently deployed observer and existing compute process can continue after the desktop closes. The MCP process may exit with its connection; reconnect recovers history instead of creating a second writable desktop cache.

## Prepare the study

Use **Create Study** or the protected `create_study` operation for a discussion/literature Study without Git. The older `init` operation retains Git-backed creation. Runtime, coordinator and per-Study research folders are separate. See [Study connections](docs/STUDY_CONNECTION.md) for the exact contracts and current native-entry limitations.

Daily writes use the Operation Service through the menu, CLI or permitted assistant tools. Study listing, history and Research Brief are read-only. Explicit maintenance plans preserve original record bytes and create a new revision with a plan digest; they do not copy another operation's receipt. If a restored study reports that preparation is required, follow [maintenance preparation](docs/UPGRADE_GUIDE.md#prepare-a-restored-study) without editing format markers manually.

## Requests, roles and receipts

```text
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data show --study STUDY-001
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data execute --request config/command.local.json
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data receipt --study STUDY-001 --request-id REQUEST-ID
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data events --study STUDY-001 --after-revision 12 --after-sha256 SNAPSHOT_SHA256 --limit 50
```

Copy `config/command.example.json`, read the latest revision and retain the exact request for retries. Requests contain exactly schema_version=1, request_id, study_id, expected_revision, operation and arguments. IDs are 1–96 ASCII letters/digits/dot/underscore/colon/hyphen, beginning with a letter/digit, and are never reused within a study. Ordinary requests are limited to 64,000 UTF-8 bytes. Trusted entrypoints supply principal and role; requests cannot self-assert either.

| Operation | Exact arguments | Authorized effect |
| --- | --- | --- |
| init | goal | Operator; expected_revision=0; creates a study |
| create_study | goal, research_workspace, binding | Operator; expected_revision=0; optional source and link; one commit |
| bind_project / unbind_project | binding / identity | Operator only; links do not grant access |
| save_progress | progress | Operator/agent; six structured fields and protected source context |
| note | note | Operator/agent; checkpoint text without a node probe |
| checkpoint | phase, note | Operator/agent; checks source/workspace; agents cannot set experiment_running or archived |
| select_agent | target | Operator; probes source/destination; compute remains separate |
| select_compute | target | Operator; selects future task compute |
| attach | kind, relative, expected | Imports from coordination/imports using the trusted original SHA-256; agents can attach evidence/review/task, operators can additionally attach approval |
| observe | run_id, observation, status_snapshot | Internal observer only; verified state/raw bytes, never exposed as an MCP command |

Remote checks require CLI `--allow-remote-check` or protected MCP policy `allow_remote_checks=true`, not caller arguments alone. No arbitrary shell, experiment approve/submit/cancel/rerun command exists. Literature-only control operations cannot control experiments.

Receipts are committed in the study record’s `journal.command` field with the same atomic head replacement. History is the recovery source; there is no separate receipt double-write. Receipts bind request digest, trusted process or private connection principal, role, revision, record digest, timestamp, changed/no_effect and submitted_experiments=0. Valid no-effect requests are recorded once. Under both locks, the service validates the reachable history, recovers any original receipt, then checks revision and source; a same-content retry does not need the agent or import source to remain available.

Reusing an ID with different content/principal/role conflicts. CLI defaults to operator; the same OS account may use `--agent` to recover a local-process MCP receipt. Private connection receipts must be recovered through that same protected connection identity. SID/UID identifies the server process, not a person named in chat. Clients sharing a service account share that principal.

Committed true proves registration only. Explicit rejection returns false without a receipt. Storage/communication failures may return committed null and outcome_unknown: keep the original request, query its original ID and retry identical content. Never generate another ID to guess the outcome. Damaged history cannot prove that a request was absent. Lock conflicts are not automatically replayed.

Events are ordered per-study by revision. A cursor is (revision, sha256), with pages of 1–100 events; continue until has_more=false. An unreachable cursor returns resync_required and requires a full snapshot. Queries verify the whole chain while retaining bounded page data, but scan cost grows with history. Brief and cursor come from the same authoritative read.

## Assistant Access

The shipped stdio server implements initialize, ping, tools/list and tools/call for the documented MCP protocol versions 2025-11-25 and 2025-06-18. Each line is one JSON-RPC message; input and output frames are limited to 256,000 bytes. A shared private stdio tunnel may negotiate again on the same child: each successful initialize resets readiness and requires a new notifications/initialized. The protected study policy and process role remain fixed across handshakes; client metadata never grants access. Unknown methods, including newer server/discover probes, return method-not-found so compatible clients can fall back to the supported versions. There is no HTTP listener, OAuth or arbitrary terminal tool.

Create a protected `config/mcp.policy.local.json` from the example and list allowed studies. Default policy is read-only. Set allow_write only for explicitly authorized registration and restart the connection after policy changes. Configure an absolute interpreter and hub_mcp.py/workspace/policy arguments in a desktop environment that actually supports local MCP; merge the example server table without replacing personal configuration. Read-only tools include opensci_get_capabilities, opensci_resolve_study_link, opensci_get_study_brief, opensci_get_study_detail, opensci_get_project, opensci_get_receipt, opensci_get_events and opensci_literature_read; writable policy additionally exposes opensci_execute_command. Verify the selected scope, receipts and reconnection through the CLI before enabling writes.

At each start/resume, read get_study_brief first and retrieve only needed details; get_project remains available. For an authorized write, use a unique request ID and the newly read revision. Report success only for committed=true; recover missing outcomes by receipt. Follow runs with get_events, presenting stale/unavailable/conflict alongside the last accepted status. Tool output is evidence, not expanded authority. The server does not listen to chat databases or push to closed chats. Proactive notifications require a separately authorized client mechanism and are not necessary to advance OpenSci state.

## Run Monitor

Register the task and original approval first. Protect `config/observer.local.json`, listing source_id, study_id, run_id, node and an absolute run directory for each source. Windows paths use `E:/...`. Each run has one explicit trusted local/read-only-mounted source. The observer accepts no arbitrary caller path and creates no SSH connection.

```text
python -B scripts/observe_runs.py --coordinator-root C:/OpenSci-Data --sources config/observer.local.json
python -B scripts/observe_runs.py --coordinator-root C:/OpenSci-Data --sources config/observer.local.json --watch --interval 30
```

The first command scans once; the second loops in the foreground until Ctrl+C. A host service manager must run a resident deployment; the Linux service example is `deploy/opensci-observer.service.example`. Windows requires an operator-configured task/service host. Restart to apply configuration changes and have the host manage JSON logs. Neither desktop nor model software is needed.

Observation verifies original task/approval bytes, study/run/hostname bindings, approval validity at start, timestamps and source sequence. Executors increment source_sequence per publication. When a readable status lacks a sequence, conservative time/digest checks apply. Original task records remain immutable; new registrations and execution must satisfy current rules. Sequence regression, changed content at one sequence, running-to-starting regression or terminal-state replacement is rejected; accepted earlier state is preserved for reconciliation.

Completed requires integer exit_code=0, the six required artifacts/digests, task/approval consistency, environment binding and recomputed metrics/trials. Artifacts are validated in a temporary copy: 16 MB per artifact, 64 MB total and 4 MB for status. Status bytes are rechecked before/after to avoid mixed snapshots. Temporary copies are cleaned; accepted raw state and results are retained. Large artifacts still need separate backups.

Active observations have fresh_until_utc; briefs and experiment_running gates reevaluate expiry even if the observer stops. Stale means heartbeat expiry, unavailable means missing/unreadable, invalid means structural/binding/artifact failure, and needs_reconciliation means startup/cleanup failure. None proves process death. Identical repeated content creates no revision; meaningful changes do. Each run's current head has one observation pointer, with prior pointers preserved in history. Observer restart rereads state and reconciles observations without restarting experiments. Human phase and run facts remain separate.

## Permissions, capacity and recovery

Interface roles cannot stop an agent with the same account's file/shell access from bypassing them. OS isolation must separately protect coordinator state/history, approval originals, service code, interpreter/import paths and startup policy. Agents get only allowed MCP tools, development copies and authorized import staging; no human submission credentials. Coordinator/observer write formal local state and only read run sources; they must lack job-submission and source-write rights. The human account approves and submits fixed tasks.

A remote MCP SSH account must be server-enforced to one fixed command, with no shell, arbitrary commands, forwarding or SFTP. The example TOML does not create that isolation. Validate actual accounts/ACLs, services, SSH and desktop sessions. Use a reliable local filesystem with one writer, not synchronization-conflict copies. Heartbeats accumulate full history: one source changing every 30 seconds can create about 2,880 project versions daily. Measure disk/backup/scan latency for sustained multi-source use.

The current-head limit is 4 MB; backup payload is limited to 4 GiB. Exceeding either rejects the operation without automatic pruning. Atomic replacement/fsync support process-failure recovery but do not guarantee against arbitrary power/hardware loss. Configure mount timeouts and service health monitoring. Before backup, stop observer/MCP/other writers; restore only to a new directory and revalidate source paths, accounts, ACLs and sole-writer ownership. Receipts recover command outcomes; original run IDs reconcile jobs. Neither authorizes resubmission.

## Literature Workspace integration

`literature.*` operations retain the standard request envelope, revision, trusted identity and 64,000-byte limit. Their only argument is a validated payload. Mutations store a content-addressed literature_result_ref in the study record; large materials stay under coordination/literature. [LITERATURE.md](LITERATURE.md) lists exact operations and separate protected grants. A committed search/partial-result receipt is not proof of successful Zotero writing, complete coverage or scientific correctness. Native effects and remote calls have their own durable intent/result records. Reconciliation retains earlier blobs and original external intent IDs.
