# Maintenance Plans

Before using `Invoke-OpenSci`, paste the complete [command helper](GETTING_STARTED.md#command-context) into the same PowerShell window. Example study IDs and paths must be replaced with your actual values.

Use a maintenance plan when changing a study's source binding, moving its Development Workspace or recovering planning fields. For a software-only update, start with [Updating OpenSci](../UPDATING.md). A newly created study already supports the Operation Service.

## Choose the operation

| Purpose | Maintenance operation | Preserved facts |
| --- | --- | --- |
| Apply reviewed source or prepare an imported study | `upgrade` | Study identity, original record bytes and available history |
| Prepare a restored study for the Operation Service | `enable-commands` | Original history and source bindings |
| Prepare an imported Study for links and structured progress | `enable-study` | Original raw bytes, receipts, evidence and source identity |
| Move the Development Workspace with unchanged code | `relocate` | Source identity, original environments, approvals and run IDs |
| Recover earlier planning fields | `rollback` with `--to-revision` | A new revision retains later evidence, runs and approvals |

## Before applying a plan

Stop formal writers, including enabled Assistant Access and Run Monitor processes. Save and verify the project backup and external assets. Reconcile actual Execution Nodes by original run IDs. Verify clean commits, origins, accounts, interpreters and target configuration. The plan does not perform these human checks for you.

<a id="prepare-a-restored-study"></a>
## Prepare a restored study

Use this procedure only if a restored or imported study reports that preparation is required. Read the diagnostic first. When it requests `upgrade`, prepare and apply that operation before `enable-commands`. Never change `schema_version` by hand. Normal study creation does not need this procedure.

The output parent must exist and the plan filename must be new. `--workspace` selects the records folder, `C:/OpenSci-Data` in the beginner setup; for recovery use the new restored `workspace` directory instead. It does not follow `studies.local.json`. Add `--allow-remote-check` to both commands only after authorizing a configured SSH/WSL workspace check. Omit it for a local-only operation.

```powershell
Invoke-OpenSci -Arguments @('scripts/lifecycle.py', '--workspace', 'C:/OpenSci-Data', 'preflight', '--study', 'STUDY-001', '--operation', 'enable-commands', '--reason', 'Prepare the restored study for the Operation Service', '--output', 'C:/OpenSci-Backups/study-preparation-001.json')
```

Review the study ID, current revision and digest, source, target configuration and original runs. Keep the printed plan SHA-256 separately. After actually stopping writers, saving the backup and reconciling runs, apply the reviewed plan:

```powershell
Invoke-OpenSci -Arguments @('scripts/lifecycle.py', '--workspace', 'C:/OpenSci-Data', 'apply', '--plan', 'C:/OpenSci-Backups/study-preparation-001.json', '--expected-sha256', 'REPLACE_WITH_PRINTED_PLAN_SHA256', '--quiesced', '--backup-saved', '--runs-reconciled')
```

Plans expire after one hour. Changed source, configuration or records require a new preflight. Confirmation flags are assertions, not automatic backup or reconciliation. After success, read the study and history, verify the new revision and use the Operation Service for daily writes.

## Transfer or recover a study

Prepare target configuration before `relocate`; use `--target-agent` and `--config` as needed. The tool does not rewrite node configuration or move processes. If an original host is unavailable, stop all writers and resolve ownership of original runs before continuation.

Planning recovery copies selected planning fields into a new revision and preserves later evidence, approvals and runs. It does not make an earlier `experiment_running` label proof of a running job. Backup restoration creates a separate copy and does not activate a second writer.

Preserve all literature records and manuscripts. Reconcile a restored Zotero instance before writes. Neither source recovery nor plan recovery reverses external library or Word changes. See [History and Recovery](../HISTORY.md) for limits and [Literature Workspace](../LITERATURE.md) for external-operation recovery.

When a diagnostic requests `enable-study`, use that operation in the same preflight/apply sequence. It does not silently re-anchor the research source or contact a remote host. Use software that supports the resulting record contract. Preserve later progress during rollback and use `--state-only` backup for independent coordinators without Git. See [Study recovery](STUDY_CONNECTION.md#upgrade-and-recovery).
