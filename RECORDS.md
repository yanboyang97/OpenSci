# Record Reference

## Serialization and task contract

Runtime data comes from scripts, never inferred chat memory. JSON is UTF-8, rejects duplicate keys and NaN/Infinity, and uses temporary-file replacement. Task/approval hashes bind original bytes. Nested review/environment/limits and plans use common.canonical: sorted keys, two-space indentation, Unicode retained and a final newline; this is the project convention, not RFC 8785. Do not reformat approved records. The executable authority is scripts/task_contract.py.

| Task field | Meaning |
| --- | --- |
| study_id/task_id/run_id/attempt | Study, logical task, unique run and attempt; uppercase-letter/digit/hyphen IDs, 3–48 characters |
| created_utc/research_question | Timezone-aware creation and nonempty question |
| git_commit/entrypoint | Clean source commit; demo only |
| data_class/dataset | Public synthetic definition, version and definition digest |
| evidence/protocol | Repository-relative path and SHA-256, rechecked before execution |
| review | human_only with rationale, or model_assisted with a complete manifest and canonical digest |
| parameters | Integer seed, samples and trials |
| environment | Specification/digest and interpreter identity: invocation/real paths, prefixes, OS and architecture |
| target | Exact hostname; Linux only |
| limits | Timeout, CPU/GPU declarations, human budget and currency; supported synthetic resource combination only |
| acceptance | Six artifacts, finite nonnegative metrics, 2×trials rows and recomputation consistency |

Preparation creates only a task and DRAFT template, with blank approver/times. Model-assisted preparation requires genuinely executed complete review artifacts and their hashes; demo reviews are invalid for this purpose. A human-only review with recorded reason is available independently of final execution approval.

## Approval

Bindings are run_id, task_sha256, git_commit, environment_sha256, node, limits_sha256, evidence_sha256, protocol_sha256 and review_sha256. Environment_sha256 covers the complete canonical task.environment, including interpreter identity. A real human fills decision=APPROVED, approved_by, approved_at_utc, expires_utc and rationale. Approval cannot predate task creation or be future-dated. Expiry is rechecked at preflight, after locking and immediately before process launch; it must cover startup, not the entire subsequent execution. Expiry during a running job does not cancel it.

The run command's --approve is the approval file's raw 64-character lowercase SHA-256, not the task hash. Invalid/empty values are rejected before a run directory is created. JSON is an audit record, not a digital signature or identity system. An account with write access can forge it; protect originals and submission rights through separate human-owned accounts. Test approvals are offline fixtures only.

## Environment

Capture on the actual target with the selected interpreter. Preparation checks schema, hostname, Linux and absolute invocation path. Execution recollects and compares spec and interpreter. Preserve a virtual environment's invocation path; realpath is recorded separately and must not replace it. Python/package versions, paths, prefixes, OS and architecture must match. Prefect uses the worker's explicit OPENSCI_EXPERIMENT_PYTHON, not its own scheduler environment.

The fingerprint is not a reproducible image: wheel bytes, system libraries, GPU drivers and hardware equivalence are not fully verified. Platform text is diagnostic; kernel version is not a forced-equality field. Real adapters need data digests, dependency locks/image hashes and hardware acceptance. Capture excludes environment-variable values and credentials; protect environment/lock records according to project sensitivity.

## Status and recovery

Status transitions starting → running → completed, failed, launch_failed, timeout, cancelled, failed_validation_or_runtime, initialization_failed or cleanup_failed. Persistent record failure returns recording_failed with status_persisted=false and status_sha256=null; this result may never reach disk. Terminal states retain finish time, exit code and available artifact hashes; completed requires all six artifacts. Heartbeats update about every two seconds, increasing source_sequence from 1. Statuses without a source sequence use conservative time/digest observation. SIGINT/SIGTERM/timeout clean up the entire child process group before final recording.

Power loss, SIGKILL and disk failure can prevent final writes. inspect_run diagnoses stale/absent/corrupt/initialization-failed state and lists leftovers, without proving death or restarting jobs. Humans reconcile actual host, PID ownership, scheduler, logs and output. A further attempt needs a new run ID and approval. There is no central authenticated approval database, distributed lock or automatic process recovery.

## Study Record

Current study JSON records goal, phase, revision, optional research source commit/origin digest, Development Workspace and its configuration snapshot, separate Execution Node, references, notes, runs and a previous-revision journal digest. Each write preserves prior raw bytes, then atomically replaces the head. Read/write limits are 4,000,000 UTF-8 bytes. History snapshots are content-addressed and immutable; revision and local locks are mandatory. Corrupt records are not reconstructed automatically. Resume neither writes nor submits.

Imports are raw content-addressed blobs under coordination/imports/snapshots, retaining original path/type. Changed sources create new snapshots; conflicts stop. Tasks bind study, code and compute; a run ID cannot change task. Registered run snapshots bind task/raw digest and node, but require actual-node inspection. Historical expired approvals may be archived without extension. Study state is outside Git and requires whole-state backup. Code, data, models, dependencies, credentials and runtime records do not synchronize automatically.

## Review and upload provenance

Review plan and manifest bind clean source/protocol with --bind-source. Every selected provider and planned round must complete, with exact artifacts, raw responses, model/destination/times and digests validated. Preview produces plan_sha256; --approve-plan binds the reviewed evidence, providers, endpoint/project/model, rounds, concurrency and timeout. Each directory retains configuration, full prompts, responses, reports, call records and manifest. Configuration changes afterward do not alter frozen input. Snapshot mismatch, truncation/refusal/oversized output or call failure stops subsequent rounds. Record actual model versions only when observed. HUMAN_DECISION.md is editable human material outside frozen model hashes; final approval binds the task separately.

MLflow requires an explicit tracking URI and a trusted executor status digest. Six allowlisted artifacts are copied into a verified temporary upload snapshot. A designated single uploader uses a local lock, remote run_key and local mlflow-upload.json receipt for idempotency/retry. Missing receipts may be recovered from the remote key; duplicate/conflicting remote records require human handling. Concurrent first uploads across machines have no atomic uniqueness guarantee. Remote later tampering is outside local-integrity guarantees. Only completed runs with a valid execution record upload; separately track failures/timeouts/cancellations so uploaded successes do not imply an overall success rate.

## Supporting and historical records

Backup includes raw digests/sizes, Git HEAD/object format/refs and exclusions. Keep trusted archive digests independently; restore does not activate a writer or rewrite historical approvals. Resources identify stable resource_id/version and relative-file digests; device maps them to local absolute roots. Verification covers listed bytes, not scientific reproducibility. Brief includes record digest/revision, record_updated_utc, generated_utc and recorded runs; it neither queries nodes nor authorizes/sends anything. Locks are local, not leases.

History and maintenance plans are described in [History and Recovery](HISTORY.md). Preserve original bytes and explicitly mark missing history; never fabricate lost progress notes. New reviews freeze AGENTS.md in rules.snapshot.md and bind prompt_template_sha256. Changed rules invalidate old reviews for new execution, while historical reads validate their original pipeline. Simulation request/status is separate from production and marks scientific validity not_assessed.

The Study Record contains journal.command with request/principal/role/operation/outcome/revision/study fields; lifecycle maintenance uses null. Head plus raw history form the only committed chain and receipt/event source. Identity is a protected process SID/UID or private connection principal, never caller self-assertion or a cloud human inferred from an OS account. Observations bind source, raw digest/sequence/times/freshness, node/task/approval, condition and artifact validation. Reevaluate current freshness rather than treating an old current status as permanently online. Preserve prior terminal facts on conflict, and never replace an approval after observed run facts. Receipts prove registration and artifact checks prove internal byte consistency; neither grants execution authority or establishes scientific truth.

## Literature records

The Study Record accepts kind=literature content-addressed JSON references from the shared command service. The head retains the latest reference per literature operation while full study history preserves earlier ones. Literature records live under coordination/literature: study associations, searches, external operations, snapshots, jobs/events, reservations, citation maps and native Word tasks. [LITERATURE.md](LITERATURE.md) defines their boundaries. Zotero local versions are not cloud versions; attachment hashes identify exact content. A claim must distinguish source, user annotation, AI summary and inference, with coverage and verification status.

## Study integration fields

Record contract 4 requires `research_workspace`, `project_bindings` and `progress`. A null anchor represents unavailable research source provenance; no commit is fabricated. Progress contains validated `content` and protected `source_entry`. Only the latest structured progress is in the head; earlier complete values and receipts remain in immutable history. Imported records are read without fabricating missing fields. Explicit lifecycle preparation preserves original bytes; unsupported formats are rejected. Refer to [Study connections](docs/STUDY_CONNECTION.md) for field limits, identities, management operations and migration.
