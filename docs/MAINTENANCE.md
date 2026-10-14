# Maintenance and Recovery

Before using `Invoke-OpenSci`, paste the complete [command helper](GETTING_STARTED.md#command-context) into the same PowerShell window. Example study IDs and paths must be replaced with your actual values.

Maintenance preserves trusted source, one study history, original evidence and traceable runs. Include service health checks when Run Monitor or Assistant Access is deployed; record actual enabled services separately from the product documentation.

## Routine and pre-change checks

| When | Check | Action |
| --- | --- | --- |
| Session start or handover | Goal, revision, Development Workspace, source commit, open questions and run IDs | Preserve a dated brief; reconcile disconnections |
| After a tool update | Three runtime paths, Python version and launcher | Update local configuration and verify |
| After source changes | Commit, dirty state and origin digest on both hosts | Review, test and synchronize one commit |
| After enabling observation | Disk, history growth, scan latency, logs and freshness | Set an appropriate schedule; do not silently prune history |
| Before upgrade, migration or rollback | Quiescence, trusted backup, external assets and run reconciliation | Use a reviewable plan and a new destination |

`doctor.py --profile offline` checks local prerequisites and may invoke `--version` on discovered Git, Codex and Claude CLIs. It does not log in, call a model or establish remote/model readiness. Reading installed files does not require running doctor.

```powershell
Invoke-OpenSci -Arguments @('scripts/doctor.py', '--profile', 'offline')
```

## Preserving the installation before Git

If no Git source baseline exists, stop editing and preserve the source release, actual local configuration and shortcut reconstruction details in controlled storage. This preserves the basic deployment; it is not a complete study backup or evidence that experiments can resume. A source release excludes future studies, external data and credentials.

<a id="backup"></a>
## Project backup after Git setup

After establishing Git history, verify that the workspace is the Git repository root, review and commit source changes, and ensure a clean working tree. Preserve any still-uncommitted work separately. Choose an existing controlled output directory outside the workspace, for example `C:\OpenSci-Backups`. This is an example and has not been created automatically. Use a new archive name. Stop all record writers and autosave, then reconcile actual run IDs. `--quiesced` declares that those prerequisites are satisfied; it does not stop services for you.

```powershell
Invoke-OpenSci -Arguments @('scripts/backup_project.py', 'backup', '--workspace', '.', '--output', 'C:/OpenSci-Backups/OpenSci-backup-001.zip', '--quiesced')
Invoke-OpenSci -Arguments @('scripts/backup_project.py', 'verify', '--archive', 'C:/OpenSci-Backups/OpenSci-backup-001.zip', '--expected-sha256', 'REPLACE_WITH_TRUSTED_SHA256')
```

Save the first command's SHA-256 in a separate trusted record and use it for verification. Recomputing a digest from an untrusted archive does not authenticate its origin. The backup tool neither encrypts the archive nor detects secrets previously placed in history or configuration.

| Automatically collected | Separately managed |
| --- | --- |
| Tracked source and history reachable from refs | Uncommitted work, reflog, unreachable objects and Git configuration |
| Specified coordination state, history, imports and requests | Approval originals and artifacts outside the collected directories |
| Listed local configuration files | Runtime binding, command requests, Claude machine mapping and shortcut |
| Environment files and resource manifest | External data/models, LFS objects, software, venvs, credentials, ACLs and services |

The [backup contract](../BACKUP_AND_MIGRATION.md) and the collection list in `scripts/backup_project.py` define the exact scope. Rebuild runtime bindings and the shortcut for the destination's tool paths. Do not commit credentials merely to include them in a backup.

## Restore and acceptance

The destination must not exist, for example `C:\OpenSci-Recovery-001`, rather than the active `C:\OpenSci`. The restored workspace is the destination's `workspace` subdirectory. Keep the old writer stopped and do not activate the new copy before acceptance.

```powershell
Invoke-OpenSci -Arguments @('scripts/backup_project.py', 'restore', '--archive', 'C:/OpenSci-Backups/OpenSci-backup-001.zip', '--expected-sha256', 'REPLACE_WITH_TRUSTED_SHA256', '--destination', 'C:/OpenSci-Recovery-001')
```

Restore retains records and Git refs with a detached HEAD; the operator chooses the subsequent working branch. Reconcile origin, identity, runtime, node configuration, external resources, service accounts and permissions. Assess material completeness, history completeness, run traceability and reproducibility separately before claiming the corresponding recovery capability.

## Capacity, records and handover

The current study-head limit is 4,000,000 UTF-8 bytes; backup uncompressed payload is limited to 4 GiB. History grows separately, and observer updates can create frequent full versions. There is no automatic pruning or unlimited-capacity guarantee. Back up and review data organization before approaching limits; do not delete history to force continuation.

A handover should identify the entry point, sole coordinator, commit/origin reconciliation, enabled services, backup location and trusted digest, original run IDs and unresolved issues. Record credential ownership and management location, not credential values.

## Literature recovery

Retain operation IDs, before-images, immutable snapshots, Word recovery copies, launch markers and unsettled reservations. A lost response must be reconciled before another write/call. [Literature Workspace](../LITERATURE.md) defines the original-caller reconciliation operation. Backups include literature state, untracked manuscripts and literature local settings, excluding the derived SQLite cache. Zotero data and attachments, Windows grants, browser sessions and tools need independent recovery. Restore into isolated destinations before activating a single coordinator. Never prune unresolved writes or the only evidence behind a result.

An independent coordinator without Git supports explicit `backup_project.py backup --state-only`. This saves authoritative Study state, not runtime software or external research folders. See [Study recovery](STUDY_CONNECTION.md#upgrade-and-recovery); the Git-based procedure above remains for source-and-state archives.
