# OpenSci Architecture

## Architecture and boundaries

OpenSci combines one command service, durable file records, an independent observer, bounded reviews and human-approved execution. CLI and MCP share business rules; the desktop is an access layer, not a core runtime dependency. Development and execution are linked through fixed source commits, evidence digests and run IDs. Only the coordinator writes formal study state.

The desktop may assist discussion, development and review through tools actually available and authorized in the session. Its remote project connection is separate from the Development Workspace stored as `active_agent`; choosing that workspace does not start or migrate a conversation. Formal state is stored in project files, not inferred from chat. Research Brief is a dated local snapshot. The automated Codex reviewer is a separate process with frozen inputs, not the current conversation.

Desktop operation follows read state → submit an authorized structured command → verify a durable receipt → read observer changes. An independently hosted observer can continue when the desktop closes; reconnection recovers history. There is no full-chat ingestion or proactive desktop message push. Ordinary chat assent and command receipts do not substitute for human approval.

Official names are defined in the [Feature Catalog](FEATURES.md). This implementation map groups supporting code under those names.

| Module | Implementation and responsibility |
| --- | --- |
| Research Workspace | `Start-OpenSci.ps1`, `hub.py`, `workspace_probe.py`: studies, workspace checks, planning phases and separate node selection |
| Operation Service | `command_service.py`, `hub_command.py`, `os_identity.py`: requests, receipts, roles, revisions and outcome recovery |
| Assistant Access | `hub_mcp.py`: restricted tools and study scope |
| Run Monitor | `observe_runs.py`, `observation_contract.py`: source validation, freshness and conflict handling |
| History and Recovery | `project_store.py`, `common.py`, `storage_paths.py`, `lifecycle.py`, `record_reader.py`: bounded storage, locks, immutable revisions and explicit maintenance |
| Backup and Transfer | `backup_project.py`: source/state archives and verified restoration |
| Resource Catalog | `verify_resources.py`: resource identity and device path checks |
| Environment Check | `doctor.py`, `capture_environment.py`, `environment_contract.py`: readiness and interpreter/environment bindings |
| Task Preparation and Human Approval | `prepare_task.py`, `task_contract.py`: draft specifications, approval templates and fixed-input validation; approval remains a separate human act |
| Experiment Execution and Results Verification | `run_task.py`, `inspect_run.py`, `experiments/demo.py`: synthetic execution, heartbeat, cancellation, artifacts and result validation |
| Evidence Review | `review_round.py`, `provider_call.py`, `review_contract.py`: frozen inputs/rules, bounded calls, reports and provenance |
| Literature Workspace | `literature_*`, `zotero_adapter.py`: sources, protected credentials, imports, full text, evidence, jobs, writing and recovery |
| Claude Development Launcher | `Start-ClaudeCode.ps1`, `tools/claude-launcher/`: explicit provider selection and local credential references |
| Experiment Tracking and Workflow Scheduling | `log_mlflow.py`, Prefect flow/configuration: optional artifact upload and controlled execution workers |
| Research Brief and Simulation Lab | `project_brief.py`, `simulation.py`, `simulation_adapters/`: dated summaries and separate software simulations |
| Research Plans | `methodology/`, `literature/`, `coordination/templates/`: protocol, evidence matrix and human decisions |
| Package Verification and Documentation Builder | `verify_delivery.py`, `tools/build_docs.py`: package integrity and separate language handbooks |

Source/protocol/packets use Git. Current records/history live in `coordination/projects/`; immutable imports in `coordination/imports/`; tasks/reviews in their respective coordination directories. Device paths are local configuration; large data, secrets and run artifacts remain external. Task Specifications, Human Approvals, Execution Environments and Run Status records have separate validators. The Operation Service writes Study Records and preserves receipts. Each review freezes the single AGENTS.md; source/rule changes require renewed binding checks.

OS accounts/ACLs must protect coordinator state, approvals, service source, interpreter/import paths and policy. Hashes authenticate bytes, not people. The Codex review adapter's read-only sandbox does not itself disable all tools or reject tool events; separate isolation and negative acceptance remain necessary before enabling live review.

The current-head limit is 4,000,000 UTF-8 bytes; history is separate. Locks are local, not distributed leases. Windows may coordinate; remote agents and production reviews/execution require Linux/WSL. Execution is public estimator example only, one CPU, zero GPUs. Backups omit external data, credentials, virtual environments and services. Other authorized clients can receive Research Briefs, but there is no dedicated mobile API, professional-tool runner, GPU contract, license scheduler or automatic process recovery. A resident observer records facts; it is not an autonomous research scheduler.

## Literature integration

[Literature Workspace](LITERATURE.md) uses literature_service and the Zotero/source/evidence/writing/job adapters through the Operation Service. The study record head stores only content-addressed result references; history retains prior references. The Windows context owns library/browser/Word access, while a fixed SSH executor receives validated evidence and bounded reservations. Detached literature workers are designed to return version-bound results to the same Coordinator independently of a chat session; actual close-chat recovery still requires live acceptance. SQLite FTS is derived local data. This is separate from the experiment runner and observer; it grants no experiment/GPU or arbitrary-command capability.

## Study integration contract

`Hub.runtime_root` locates installed software; `Hub.coordinator_root` (implementation alias `root`) locates authoritative state and imports. `research_workspace` is per Study and optional. Record contract 4 adds optional source provenance, protected project links and structured progress. A source-free Study supports discussion and literature, while source-dependent operations fail explicitly. Git-backed source operations remain separate.

`project_binding.py` enforces canonical provider/namespace/project/type/host identity under the coordinator and Study locks. Its reverse lookup is derived from heads, never a second authority. `study_context.py` validates six progress fields, preserves trusted/unknown source context, and builds deterministic bounded overviews and revision-pinned detail pages without model calls. The existing Operation Service owns every commit and receipt. See [Study connections](docs/STUDY_CONNECTION.md) for identity, native-host limits and exact input bounds.
