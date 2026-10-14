# Deployment and Execution Guide

## Deployment model

Use one fixed coordinator. Discussion Studies need no execution node; the approved experiment workflow additionally needs a Linux/WSL execution environment. Enable optional services only after individual acceptance.

| Role | Requirements | Responsibility |
| --- | --- | --- |
| Coordinator | Windows/Linux, Python 3.10+; Git for source-dependent work | Sole writer of studies, evidence links, history and original run IDs |
| Development Workspace | Local or configured SSH/WSL Linux, Python and Git | Development, tests, reviews and task drafts |
| Human submitter | Linux/WSL, selected experiment interpreter, protected approvals | Review fixed versions, submit and inspect approved experiments |
| Windows Claude launcher | PowerShell 7, native claude.exe, separate credentials | Explicit DeepSeek/Kimi development |
| Optional service account | Validated MLflow/Prefect environment | Artifact archival or controlled workers |

Roles may share hardware, but accounts, directories, permissions and credentials must be separated. Choosing a Development Workspace does not choose an Execution Node. Portable devices access the fixed coordinator; copying this directory creates a different workspace, not an automatic connection to the original.

Verify the original delivery before configuration with `python -B verify_delivery.py`. This validates bytes, not publisher identity. Confirm OS/Git access and avoid multi-writer synchronization folders.

## Git and machine configuration

For source-dependent work, in the separate research workspace initialize a new repository with `git init -b main`, set the actual operator's repository-local `user.name` and `user.email`, review staged files, then create the initial source commit. Do not invent a deployment identity. Existing studies must retain their Git history. Task preparation and workspace continuation require a clean commit. Use the same reviewed origin URL spelling and commit across workspaces. An initial single workspace may omit origin; configure identity before future cross-workspace switching. Do not edit recorded identity fields to repair an old study.

Copy `config/hub.fixed-host.example.json` for SSH or `config/hub.example.json` for WSL to `config/hub.local.json`. Fill in exact alias/distribution, account, absolute Linux workspace, Python and hostname; remove placeholders and enable only intended nodes. SSH authentication and host fingerprints must already be trusted; OpenSci does not accept new fingerprints automatically.

Windows can use `config/runtime.local.json` based on `config/runtime.example.json`. These paths select already installed tools. The launcher prepends the configured Git directory only within its own process and restores that process value afterward; global PATH and execution policy are not changed. `Start-OpenSci.cmd` uses a process-only execution-policy override. The root shortcut uses the project icon. Use `Start-OpenSci.ps1 -Python 'C:\Tools\Python\python.exe' -List` to override Python explicitly.

```text
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data list
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data menu
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data show --study STUDY-001
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data resume --study STUDY-001
```

List/show/brief read local records. Menu **Create Study** uses the Operation Service and returns a receipt. It requires valid configuration but does not authenticate the remote endpoint. Resume probes the configured workspace and never restarts experiments. Choose Development Workspace, Record Progress and development steps also check the configured workspace. Use the latest revision from show for writes. The main launcher only exposes doctor, review-plan and review-demo development steps; it never submits experiments.

## Environment readiness

Use `python -B scripts/doctor.py --profile offline` to inspect the installed environment and `python -B scripts/review_round.py` to preview provider configuration. These commands do not prove remote authentication or model access. Complete the [installation prerequisites](docs/INSTALLATION.md) before enabling an optional service.

## Estimator Comparison workflow

The only production entrypoint is `experiments/demo.py`, using public synthetic data, one CPU thread and no GPU. Read [experiment_protocol.md](methodology/experiment_protocol.md) and [DEMO.md](coordination/packets/DEMO.md).

1. On the actual Linux compute node, select a stable absolute interpreter invocation path and run `scripts/capture_environment.py --out environments/cpu-01.environment.local.json` with that interpreter. Share the record through an authorized channel; do not substitute a development-machine environment.
2. From clean source, run `scripts/prepare_task.py --id EXP-001 --study-id STUDY-001 --node ACTUAL_TARGET_HOSTNAME --environment environments/cpu-01.environment.local.json --samples 100 --trials 100 --human-review-reason 'Public synthetic example; protocol and source reviewed by a human'`. Replace hostname with the real recorded value. This creates a task and a DRAFT approval template. Alternatively bind a completed real review using `--review-manifest`; do not combine the two modes.
3. A human checks source, task, protocol, evidence, environment, node, limits and review, then creates a separate approval in a protected directory. Fill APPROVED, real approver, timezone-aware approval/expiry and rationale without changing binding fields. The development agent must not control the approval original.
4. On the compute node, use the exact source snapshot and task. Run `scripts/run_task.py --task coordination/requests/EXP-001.json --approval /home/submitter/research-approvals/EXP-001.json --approve REVIEWED_APPROVAL_SHA256 --python /home/submitter/venvs/experiment/bin/python`. All paths and digests are examples to replace with reviewed values.

Default output is `~/research-runs/EXP-001` under the submission account. Preserve the executor's final status_sha256 in an independent trusted record. Existing run directories are not overwritten; retries need a new run ID, task and approval. Interpreter/path/package/node changes require new preparation. The fingerprint is not a complete environment reconstruction system; retain dependency sources, lockfiles, system libraries and driver details separately.

Inspect original runs with `scripts/inspect_run.py --run /home/submitter/research-runs/EXP-001`. A stale heartbeat is not proof of process death. Reconcile host, process/scheduler ID, logs and artifacts; preserve partial files. Resume, reopening a menu and restoring a backup do not restore processes. First-node acceptance must include normal completion, duplicate rejection, invalid approval/environment rejection, timeout, SIGTERM and reconnecting to the original run. Budget fields and local node locks are not cloud billing limits or distributed schedulers.

## Optional development, review and services

For Windows Claude, run Setup and Doctor before explicitly selecting DeepSeek or Kimi; see [CLAUDE_LAUNCHER.md](CLAUDE_LAUNCHER.md). Setup creates only this copy's machine mapping and credential references, refuses overwrites and does not change Profile. Use interactive SetKey for missing credentials. Local checks do not establish real service eligibility, rule loading, endpoints, response identity, long-context behavior or exit handling. This launcher does not change Development Workspace or Execution Node bindings or create approval.

For live reviews, use a separate Linux/WSL review environment, enable only accepted entries in `config/providers.local.json`, and verify eligibility, data permission, endpoint, model and budget. Secrets remain in controlled credential mechanisms. Claude automated review uses Vertex separately from Windows development. Preview a fixed-source plan using `review_round.py --config config/providers.local.json --providers claude_sonnet --rounds 1 --parallel 1 --bind-source --protocol methodology/experiment_protocol.md`; execute identical parameters only after human review, adding `--execute --approved-input --approve-plan PRINTED_PLAN_SHA256`. Preserve prompts, rules, responses and summaries. Incomplete/refused/truncated/tampered outputs stop later rounds. Record an unobserved model version as unknown. Codex review uses a read-only sandbox, but the adapter does not forcibly disable tools or reject tool events; validate isolation using a separate restricted account before enabling it.

Optional requirements are not a lockfile. Use separately validated environments. MLflow only uploads completed runs bound to a trusted status digest; designate one uploader and test retries. Prefect requires fixed snapshots, tasks and approvals under the submitter's home, an explicit `OPENSCI_EXPERIMENT_PYTHON`, actual pool/workdir settings and tested cancellation/restart behavior; retries default off and a GPU-sounding pool name does not enable GPU tasks. Resource manifests map stable IDs to machine-local directories; verify_resources validates listed bytes without downloading, mounting or synchronizing them.

## Recovery and acceptance order

Stop writers, create and verify a backup, preserve the trusted digest and restore only into a new directory. Backups exclude external data, live run directories, credentials, installed software, virtual environments and OS permissions. Retain original run IDs and hand over the sole writer explicitly. Prepare imported records through explicit maintenance plans; plan rollback preserves later facts. Retain newer evidence and receipts when recovering a separate copy from backup.

Accept in order: actual Coordinator and Development Workspace configuration and clean matching commits; platform regression, study/history/backup-restore/environment capture; synthetic completion/cancellation/timeout/duplicate/disconnect behavior; then selected live models, MLflow and Prefect with [REMOTE_ACCEPTANCE.md](coordination/templates/REMOTE_ACCEPTANCE.md). Real research additionally needs reviewed adapters, data versions and scientific acceptance criteria. Assistant Access and Run Monitor use the Operation Service; begin read-only, then test scoped writes, same-ID retries, closed-desktop observation and reconnection. Accounts, ACLs, read-only sources, long-term storage and latency still require target-environment acceptance. See [INTEGRATION.md](INTEGRATION.md).

## Literature deployment

[Literature Workspace](LITERATURE.md) provides the literature workflow. Configure the intended scope: personal identity and complete inventory; five-source/API/browser capability records; explicit collection and uncertain-write recovery; parsed evidence and fixed-node no-fee dispatch; separately budgeted models; native Word and both LaTeX/Quarto toolchains; independent backups and production rollout. Do not infer complete acceptance from unit tests or an API connection. Missing OCR/visual verification, access gates and user-deferred checks must remain visible in the deployment record.
