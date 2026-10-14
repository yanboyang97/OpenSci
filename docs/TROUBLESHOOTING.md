# Troubleshooting

[Handbook](../DOCUMENTATION.md)

Identify whether the failure concerns the launcher, source, study record, receipt or actual run. Preserve the error, timestamp, relevant IDs and original files. Diagnosis must not rewrite evidence or treat uncertainty as permission to rerun. The table describes the current implementation and does not replace checking the actual node.

| Symptom | Cause and action |
| --- | --- |
| A source-dependent operation reports missing provenance | Discussion and literature remain available. Register a reviewed Git research workspace before the requested checkpoint or experiment. |
| Scripts are disabled in PowerShell | Use `Start-OpenSci.cmd` or the explicit child-process command in Getting Started; do not change global policy. |
| No enabled Execution Node | Configure an execution-role node before selecting one; choosing a Development Workspace does not create it. |
| read_only:true with committed:false | Normal read-only response; inspect the individual capability states. |
| Python 3.10+ required | Verify the executable binding rather than relying on a WindowsApps alias. |
| Configured Git executable is missing | A bound tool moved; verify its replacement and update local runtime only. |
| Claude launcher requires PowerShell 7 | Validate PS7 binding or launch from it. |
| CONFIG_MISSING | Interactive Claude mapping is absent; expected while deferred. |
| Unlisted files found | Use a fresh extraction; do not delete valid machine files to suppress this message. |
| CHECKSUM MISMATCH | Reconcile the change against trusted source before generating a new manifest. |
| Coordinator Git checkout must be clean | Inspect and preserve changes before committing. |
| Workspace Git version mismatch | Reconcile one reviewed Git history. |
| Repository origin mismatch | Reconcile the original origin identity and migration plan. |
| Development Workspace configuration differs | Inspect the complete binding and use lifecycle migration. |
| Host unavailable / account mismatch / real path mismatch | Check the approved backend binding and host identity. |
| Remote check required | Use the option in the parser position for that tool. |
| revision conflict / stale revision | Re-read and reassess instead of overwriting newer state. |
| outcome_unknown / committed:null | Recover the original receipt with unchanged request and identity. |
| resync_required | Fetch a full snapshot and restart from its cursor. |
| Lock conflict | Establish ownership and process state first. |
| Lifecycle plan invalid / expired | Re-run preflight; do not alter the old digest. |
| stale / unavailable / invalid / needs_reconciliation | Reconcile actual execution and original artifacts. |
| Record or backup size limit | Preserve state and review storage organization. |

Wording can differ by entry point. Report the complete error code/text rather than only “it does not open”. Exclude API keys, tokens, credential-bearing origin URLs and private environment-variable values.

## Run disconnection procedure

1. Identify the original run ID, node, task/approval digests, directory and last recorded timestamp.
2. Reconcile the process on the actual node with read-only `inspect_run.py` output. Distinguish stale state, inaccessible storage, inconsistent terminal facts and actual process exit.
3. Preserve logs, state and artifacts before deciding whether a new task, run ID and approval are needed.

## Reporting a reproducible issue

Record the code version/commit, OS/Python version, entry and arguments, expected behavior, actual error, relevant revision/request/run IDs and recent configuration/source changes. Provide a minimal redacted reproduction and relevant test evidence. Mark uncertain state as unknown instead of inventing history.

## Literature failures

| State | Meaning and next action |
| --- | --- |
| local_api_disabled / waiting_local | Open Zotero and verify local communication; do not forward its port |
| authorization_required | Check the original write receipt, then use the intended local grant; never send a key in chat |
| instance_changed / version_conflict | Reconcile the library or reread the changed object; stale previews cannot overwrite it |
| api_rejected during inventory | Preserve failed item keys and incomplete coverage; do not infer corruption or alter the database |
| permission_denied / waiting_user | API rights, website login, CAPTCHA or native integration needs attention; not a zero-result search |
| fulltext_missing / partial | Metadata may be saved while attachment/text coverage is incomplete |
| waiting_budget | Configure finite limits and versioned price estimates; reconcile outstanding allocations |
| outcome_unknown | Keep original request/operation/job IDs and query/reconcile; no blind resend |
| Word waiting_local | Continue the prepared task in an observed native plugin session, then verify saved fields |

See the [literature guide](LITERATURE.md). A successful local API probe does not establish Connector or model readiness.
