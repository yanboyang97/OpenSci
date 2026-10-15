# Research Brief

## Read a dated study summary

For discussion handover, use **10 Study Overview** or `python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001`. These include the saved structured progress, as does MCP `opensci_get_study_brief`. If `has_more: true`, follow the revision-pinned `detail_refs` with `opensci_get_study_detail`, or read the full record with `hub_command.py show`; see [progress and history](docs/DAILY_USE.md#saved-progress). On Windows, use the [command helper](docs/GETTING_STARTED.md#command-context) from the software installation folder.

`python -B scripts/hub.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001` prints a shareable JSON summary from the fixed Coordinator. The command does not create an output file; save the output explicitly when a file is needed. It does not connect to nodes, change records, send messages or provide a dedicated mobile API.

This `hub.py brief` output includes goal, planning phase, checkpoint note (`checkpoint_note`), phase-based next step, pending decisions and registered run IDs/status. It does **not** include the structured progress saved by menu 11 or `save_progress`. generated_utc is the summary time; record_updated_utc is the underlying record time. live_node_status=not_queried makes the absence of live inspection explicit. When relaying, preserve record time/revision and label status as a local snapshot. Goals and progress notes may be sensitive; use authorized channels and cite verified artifacts. A phase alone cannot establish experiment completion.

Ordinary chat assent creates neither approval nor execution. An independent human submitter still reviews the fixed version and approves/runs it. Remote-desktop/SSH/app connections are configured separately and are outside brief checks. During recovery, reconcile the sole writer, formal state and original run IDs using [HISTORY.md](HISTORY.md) and [BACKUP_AND_MIGRATION.md](BACKUP_AND_MIGRATION.md).
