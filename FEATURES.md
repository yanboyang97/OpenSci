# OpenSci Feature Catalog

OpenSci **1.0.1** organizes research work around a study: its question, evidence, decisions, source code and recorded results. The names below are the official names used in menus and documentation. File paths and API identifiers are stable technical interfaces; they are not additional product names.

## Research workflow

| Module | Features and purpose | Main entry |
| --- | --- | --- |
| Research Workspace | Create, browse and resume studies; choose a Development Workspace and Execution Node; record progress and attach evidence | [Daily use](docs/DAILY_USE.md), menu options 1–5 and 8 |
| Research Plans | Define questions, hypotheses, methods, acceptance criteria and human decisions | `methodology/experiment_protocol.md`, `coordination/templates/` |
| Evidence Review | Preview a review plan, freeze supplied evidence and shared rules, run explicitly authorized model reviews, preserve disagreements and reports | Menu option 7, `scripts/review_round.py` |
| Task Preparation | Bind a draft task to exact source, evidence, environment, node and resource limits | `scripts/prepare_task.py` |
| Human Approval | Record an independent human's approval of a fixed task and its validity period | DRAFT approval template from Task Preparation; [human procedure](IMPLEMENTATION.md) |
| Experiment Execution | Run one approved task and record status, heartbeat, logs and artifacts | `scripts/run_task.py` |
| Results Verification | Inspect a run by its original ID and validate artifacts, metrics and environment bindings | `scripts/inspect_run.py` |
| Study Overview | Read the selected Study's bounded progress, questions and evidence references | Menu 10, `opensci_get_study_brief` |
| Discussion Progress | Save structured conclusions, hypotheses and next steps with a receipt | Menu 11, `save_progress` |
| Project Links | Bind verified native project identities to a Study through operator commands | `create_study`, `bind_project`, `unbind_project` |
| Study Connection | Select and clear the protected single-Study scope | `scripts/select_study_connection.py`, [Plugins and MCP](docs/PLUGINS.md) |
| Remote Study Gateway | Carry token-authenticated loopback MCP through an operator-owned SSH forward | `scripts/study_remote.py` |
| Research Brief | Produce a dated, read-only study summary for continuation or handover | `scripts/hub.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001`, [Research Brief](RESEARCH_BRIEF.md) |

The supplied Experiment Execution module supports the public Estimator Comparison with one CPU thread and no GPU. Research Plans and Evidence Review support preparation and checking; neither proves scientific validity or grants execution approval.

## Literature Workspace

| Feature | What it does | Operation or guide |
| --- | --- | --- |
| Connection Check | Report available library, search, writing and analysis capabilities | `literature.capabilities` |
| Literature Record Lookup | Read study associations, items, operations and native writing tasks | `literature.get` |
| Library Search | Search the local library or derived index, reporting freshness | `literature.search_library` |
| Library Binding | Bind one personal Zotero library and its local instance using protected grants | [Literature setup](docs/LITERATURE.md) |
| Literature Search | Search configured sources, retain exact queries and report coverage per source | `literature.search` with optional `resume_run` |
| Citation Import | Read native RIS/BibTeX exports as search candidates | `literature.search_import` |
| Library Collection | Add explicitly selected candidates to a chosen collection with per-item receipts | `literature.collect` |
| Full-text Retrieval | Fetch one item's permitted public PDF or PMC material | `literature.fetch_fulltext` |
| Library Organization | Apply selected collections, tags, notes and annotations | `literature.organize` |
| Study Literature Association | Associate collections, items and screening reasons with one study | `literature.bind_study` |
| Duplicate Review | Detect likely duplicates and reconcile library changes; native merge is a separate Zotero action | [Literature reference](LITERATURE.md) |
| Evidence Snapshot | Freeze selected bibliographic records, attachment hashes, annotations and extraction coverage | `literature.read` |
| Literature Analysis | Prepare bounded, authorized analysis jobs with reservations, checkpoints and recovery | `literature.analyze` |
| Reading Notes | Distinguish source text, user annotations, AI summaries and inferences | [Daily literature work](docs/LITERATURE.md) |
| Citation Writing | Maintain citation mappings and assist LaTeX/BibTeX or observed native Word workflows | `literature.cite`, [Writing workflow](docs/LITERATURE.md) |
| Library Reconciliation | Resolve uncertain external operations with `literature.reconcile`; separately reconcile restored instances and citation changes | [Literature recovery](LITERATURE.md) |
| Analysis Dispatch | Dispatch a prepared job to the explicitly authorized fixed executor | `literature.job_dispatch` |
| Analysis Result Import | Validate a job's original bindings and import its results | `literature.job_import` |
| Analysis Status | Read job state; an explicit refresh contacts the executor | `literature.job_status` |
| Analysis Control | Request pause, resume or cancellation and verify effective state | `literature.job_pause`, `literature.job_resume`, `literature.job_cancel` |
| Bibliography Export | Export stable bibliography mappings and LaTeX/Quarto examples | `literature.export` |
| Library Change Preview | Review a fixed before-image, impact, digest and recovery method | `literature.preview_change` |
| Library Change Application | Apply the operator-confirmed preview, rejecting stale inputs | `literature.apply_change` |
| Literature Settings | Update complete protected settings using the current configuration revision | `literature.config_update` |

Source adapters, browser access, full-text rights, native writing applications and paid analysis each need their own configuration and verification. The complete operation list, exact payloads and limits are in the [Literature Workspace reference](LITERATURE.md).

## Integration and maintenance

| Module | Features and purpose | Main entry |
| --- | --- | --- |
| Operation Service | Validate structured requests, enforce entrypoint roles, store receipts and recover uncertain outcomes | `scripts/hub_command.py`, [Integration](INTEGRATION.md) |
| Assistant Access (OpenSci Study plugin and Study MCP Server) | Provide restricted study and literature tools through the Model Context Protocol (MCP) | `scripts/hub_mcp.py` |
| Mobile Research Access | Continue computer tasks through the ChatGPT phone app and preserve outcomes in the same Study; uses the host's remote-computer feature | [Research from Your Phone](docs/MOBILE_RESEARCH.md) |
| Run Monitor | Read configured run sources, verify observations and report freshness or conflicts | `scripts/observe_runs.py` |
| History and Recovery | Inspect immutable study history, prepare maintenance plans and restore planning fields as a new revision | `scripts/lifecycle.py`, [History](HISTORY.md) |
| Backup and Transfer | Back up source and records, verify an archive and restore into a new directory | `scripts/backup_project.py`, [Backup and Transfer](BACKUP_AND_MIGRATION.md) |
| Resource Catalog | Identify external resources independently of their device paths and verify listed files | `scripts/verify_resources.py` |
| Environment Check | Check tool readiness and capture the actual execution interpreter and environment | `scripts/doctor.py`, `scripts/capture_environment.py` |
| Simulation Lab | Run the bounded Sum Calculation and Quadratic Calculation reference adapters | `scripts/simulation.py`, [Simulation Lab](SIMULATION_ADAPTERS.md) |
| Claude Development Launcher | Start an explicitly selected Windows Claude Code provider with this copy's local configuration | [Claude Development Launcher](CLAUDE_LAUNCHER.md) |
| Experiment Tracking | Upload verified completed-run artifacts to an explicitly configured MLflow service | [Execution guide](IMPLEMENTATION.md) |
| Workflow Scheduling | Invoke the fixed execution workflow through an explicitly configured Prefect worker | [Execution guide](IMPLEMENTATION.md) |
| Package Verification | Check distributed file names and hashes | `verify_delivery.py` |
| Documentation Builder | Generate and check separate English and Chinese offline handbooks | `tools/build_docs.py` |

A **Coordinator** is the sole writer of formal study records. A **Development Workspace** holds the reviewed source used for evidence work and development. An **Execution Node** hosts a human-approved experiment. These are deployment roles, not editions of OpenSci. Choosing a workspace never moves an experiment or changes its node.

<a id="availability-and-operating-limits"></a>
## Availability and operating limits

- Installing OpenSci does not create Git identity/history, grant library access, enable models or start resident services. Complete the setup for the feature being used.
- Run Monitor and Assistant Access require deliberate deployment and account isolation. Chat agreement and process identity do not establish independent human approval.
- Library APIs, browser collection, native citation editing and scanned-material coverage depend on the installed applications and access rights. Inspect each operation's coverage and status; unavailable integrations remain explicit.
- Back up Zotero separately; OpenSci archives do not include the external library database and original attachment storage.
- Simulations validate software behavior. Production scientific tools, GPU execution and autonomous research services are outside the supplied runner's scope.

## Study connections

Study Overview (menu 10), Save Discussion Progress (menu 11), protected native project links and the single-Study private Chat path are described in [Study connections](docs/STUDY_CONNECTION.md). The OpenSci Study plugin and Study MCP Server connect to an explicitly selected private Study. Native project identity is used only when a trusted host supplies it; otherwise it remains unknown. No automatic Work dispatch, extra model calls or experiment submission is part of saving.
