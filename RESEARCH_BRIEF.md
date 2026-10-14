# Research Brief

## Read a dated study summary

`python -B scripts/hub.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001` prints a shareable JSON summary from the fixed Coordinator. The command does not create an output file; save the output explicitly when a file is needed. It does not connect to nodes, change records, send messages or provide a dedicated mobile API.

Output includes goal, planning phase, latest progress note, next step, pending decisions and registered run IDs/status. generated_utc is the summary time; record_updated_utc is the underlying record time. live_node_status=not_queried makes the absence of live inspection explicit. When relaying, preserve record time/revision and label status as a local snapshot. Goals and progress notes may be sensitive; use authorized channels and cite verified artifacts. A phase alone cannot establish experiment completion.

Ordinary chat assent creates neither approval nor execution. An independent human submitter still reviews the fixed version and approves/runs it. Remote-desktop/SSH/app connections are configured separately and are outside brief checks. During recovery, reconcile the sole writer, formal state and original run IDs using [HISTORY.md](HISTORY.md) and [BACKUP_AND_MIGRATION.md](BACKUP_AND_MIGRATION.md).
