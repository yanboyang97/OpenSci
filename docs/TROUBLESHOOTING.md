# Troubleshooting

[Handbook](../DOCUMENTATION.md)

Identify whether the failure concerns the launcher, source, study record, receipt or actual run. Preserve the error, timestamp, relevant IDs and original files. Diagnosis must not rewrite evidence or treat uncertainty as permission to rerun. The table describes the current implementation and does not replace checking the actual node.

| Symptom | Cause and action |
| --- | --- |
| A source-dependent operation reports missing provenance | Discussion and literature remain available. Existing Studies cannot add or replace their research folder through a supported operation; keep the old Study and use [Create a Study with research source](DAILY_USE.md#source-study) for source-dependent work. |
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
| revision conflict / stale revision | Follow [Recover a save](#save-recovery), read the current record and review changes before preparing a new request. |
| outcome_unknown / committed:null | Follow [Recover a save](#save-recovery) with the original request and caller identity. |
| resync_required | Fetch a full snapshot and restart from its cursor. |
| Lock conflict | Establish ownership and process state first. |
| Lifecycle plan invalid / expired | Re-run preflight; do not alter the old digest. |
| stale / unavailable / invalid / needs_reconciliation | Reconcile actual execution and original artifacts. |
| Record or backup size limit | Preserve state and review storage organization. |

Wording can differ by entry point. Report the complete error code/text rather than only “it does not open”. Exclude API keys, tokens, credential-bearing origin URLs and private environment-variable values.

<a id="save-recovery"></a>
## Recover a save

1. Keep the Study ID, original `request_id`, complete request or menu inputs, and error. Stop further save attempts until the result is clear.
2. For a save made in the local menu or operator command line, open PowerShell **under the same Windows account**, load the [command helper](GETTING_STARTED.md#command-context), and run the following with the original IDs. The examples use `STUDY-001` and `STUDY-001-NOTE-001`; copy your real values from the failed operation.

```powershell
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'receipt', '--study', 'STUDY-001', '--request-id', 'STUDY-001-NOTE-001')
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'show', '--study', 'STUDY-001')
```

For a save made by a connected assistant, return to **the same protected connection** and ask it to query `opensci_get_receipt` with the original `study_id` and `request_id`, then read the current Study. A local CLI call cannot impersonate a private connection. Add `--agent` before `receipt` only if the original operation actually used the local CLI agent role; it does not recover another identity's receipt.

| Result | Next action |
| --- | --- |
| Receipt has `committed: true` | It was saved. Compare the receipt's revision and the current record; later saves may already exist. Do not send it again as a new request. |
| Receipt query succeeds with `committed: false` and no error | No committed receipt was found for that ID in the verified history. Once the original attempt has stopped, retry only the identical saved request, with the same ID, contents and caller context. For a CLI request, use the original `execute --request` file. If the menu/request no longer preserves the complete original request, ask an operator to reconcile it; simply repeating menu 11 creates a new ID. |
| Query errors, `committed: null`, `request_conflict`, or damaged history | The result remains unresolved. Preserve the files and response for operator review; changing IDs, identities or history does not resolve it. |
| Save explicitly returns `revision_conflict` with `committed: false` | That request was rejected. Read `show`: the current revision is `cursor.revision` and progress is `project.project.progress.content`. Compare with your draft, retain newer content, then prepare a new deliberate request with a new ID and the current `expected_revision`. In the menu, read option 10 before a new option 11 save. |

After a retry or reviewed new save, require a committed receipt and read the result back. For unknown literature effects, also preserve the literature operation/job IDs and follow the [literature recovery procedure](LITERATURE.md); a missing Study receipt alone does not prove that an external write did not happen.

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
