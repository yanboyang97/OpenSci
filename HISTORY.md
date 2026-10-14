# History and Recovery

## Study history and capacity

History and Recovery preserves study revisions and provides deliberate maintenance plans for source updates, workspace transfers and planning recovery. These operations do not move processes, start experiments or extend approvals.

The current record is coordination/projects/<study_id>.json. Before each update, the full prior bytes are retained in history/<study_id>/<sha256>.json; the head links backward by digest. Checkpoints, phases, sources, runs and device bindings can be traced. Atomic head replacement is the commit point; an unreferenced snapshot is not committed history. Snapshot publication uses non-overwriting Windows rename or POSIX hard links after writing/syncing/checking. Validate real filesystems. Crashes may leave .snapshot-*.tmp or uncommitted snapshots; stop writers and reconcile the chain before handling them. History is not automatically deleted. Local locks/checks do not guarantee against malicious changes, distributed writers or every hardware failure.

Current reads/writes share a 4,000,000-byte UTF-8 limit; show warns near_capacity at 80%. Oversized serialization is rejected while preserving the old head. History is separate, but run/reference indexes still occupy the head; capacity is not unlimited. Store long materials externally and plan archival for large studies. Backups retain a separate 4 GiB limit. History pages run newest-first; use next_before_revision and stop at an empty page. Updates, migration plans and backups verify the reachable chain, so costs grow with history.

## Inspect records safely

`record_reader.py` requires a trusted original SHA-256 and reports both content and validation scope. It never renews approvals, writes records or submits tasks. Keep frozen review inputs and artifacts together. A readable expired approval remains expired; unknown formats are rejected.

For a restored record that requires preparation, preserve its original bytes and use [maintenance preparation](docs/UPGRADE_GUIDE.md#prepare-a-restored-study). Missing history must remain explicitly unknown. A maintainer can use `--legacy-large` for read-only inspection or maintenance preflight of an oversized record, up to 64,000,000 bytes. Application still requires a resulting record within the normal limit; never truncate records to force acceptance.

Changes to source, shared rules or the execution environment require appropriate new tasks and human approval. Reconcile existing runs by their original IDs on their original nodes.

## Upgrade and relocation

Stop all writers/autosaves, preserve source and a verified backup with an independent digest, and handle external assets separately. Restore into a new directory and keep the original read-only. Reapply the same reviewed origin because backup does not restore Git configuration. Review new source in the restored history, preserve study/local state and commit. Do not replace the study's identity with an unrelated repository.

Fill actual destination account, absolute workspace and Python in local configuration. Generate an external lifecycle preflight plan, review study/source revision/digest, target commit/config/device and original runs, then apply the exact plan digest. For remote targets, explicitly add --allow-remote-check to both preflight and apply after connection authorization. Plans last one hour. Application rechecks inputs under global/study locks; changes require a new plan. Quiesced/backup-saved/runs-reconciled are human assertions, not actions or distributed locks performed by the tool.

Successful upgrade keeps study_id, advances revision and preserves historical evidence/approvals/runs while recording the selected source and Development Workspace. No process is moved, restarted or resubmitted. Read history/show before authorized resume. Use operation relocate for changed account/path with unchanged code; it requires a writable study record and the recorded commit/origin. When the previous Development Workspace is unavailable, humans must first confirm writers stopped and reconcile every original run. Upgrading code at the same time uses upgrade with a destination. Old device bindings stay in history; the selected Execution Node and previous task nodes stay unchanged. Reaccept credentials/licenses/ACLs on new devices. Corrupt identity/history or unknown run ownership blocks automatic continuation and requires human recovery.

## Planning history and source versions

Plan rollback restores goal/phase/checkpoint_note from an earlier committed revision into a new higher revision. It retains later runs, references, approvals, source and device bindings. Old experiment_running becomes analysis rather than implying a live job. Use lifecycle preflight operation rollback with to-revision, reviewed reason and a new plan.

Historical source versions are managed through retained release packages or Git history. OpenSci has no dedicated command to recover an older source/state release. Ordinary backup and restore remain available for a separate recovery directory; verify source compatibility, current records and original run IDs before any writer handover.

## Shared rules and limits

Maintain only root AGENTS.md for both development clients. Historical deliveries remain unchanged. Automated review injects and freezes the same rules in rules.snapshot.md, which is immutable evidence rather than a second maintained source. Check actual interactive rule loading and ancestor-rule precedence for the installed client. This deployment does not alter user-level client settings. Automated review relies on explicit injection.

The framework supports one writer, a small number of execution nodes and a scale humans can reconcile. Storage/lifecycle are separated and source/state/device settings can be recovered separately. The literature SQLite index is derived and rebuildable. Distributed leases, authenticated experiment approval, recurring scheduling, license management and scientific acceptance are not established by offline test success.

## Literature history

Literature Workspace stores registered references to separate immutable evidence and operation records. Retain external effects, receipts and evidence during recovery. Restoring OpenSci source does not undo Zotero writes or native Word edits. Preserve the whole `coordination/literature/` directory and manuscripts, then reconcile the actual library instance before further writes.
