# Backup and Transfer

<a id="before-every-upgrade-full-folder-backup"></a>
## Before every upgrade: full-folder backup

The 1.1.0 full-folder backup is an additional option alongside the source/state migration tools below. It copies every regular file and empty directory in explicitly selected roots, including uncommitted source, local configuration, extra files and encrypted credential files. It refuses symbolic links/junctions and changing inputs rather than silently omitting them. The combined limit is 20 GiB of file contents and 100,000 ZIP entries. For larger or linked data, use your established verified backup tool and retain a scope inventory.

### 1. List everything you need to preserve

| What | How to locate it and preserve it |
| --- | --- |
| OpenSci software and local settings | The folder containing `Start-OpenSci.cmd`. Include the whole folder, especially `config`, local launchers and local profiles. |
| Study records, history, evidence and receipts | Open `config/studies.local.json` in Notepad and read `coordinator_root`. If absent, inspect your existing deployment; legacy records may be under the installation. Include the whole coordinator folder. |
| Research code, papers, datasets, models, manuscripts and outputs | List every external folder used by your Studies. Include uncommitted work and Git history. A reference/path in OpenSci does not copy the referenced file. Preserve remote data separately on its owning machine. |
| Windows tunnel credentials | Press **Windows+R**, enter `%LOCALAPPDATA%\OpenSci\connections`, and press Enter. The update menu automatically includes this directory if present. DPAPI ciphertext usually requires the same Windows account and machine; keep a secure password-manager recovery route or plan to issue a replacement key. Never export a plaintext key into the backup instructions. |
| Other credentials and assistant settings | Preserve your password-manager recovery method and the actual Codex/Claude, SSH, provider and browser settings through each application's supported backup. They are outside the automatic scope. Do not publish these backups. |
| Zotero library and attachments | In Zotero open Settings/Preferences, then Advanced → Files and Folders to find the data directory. Close Zotero, then use your established full-library backup procedure, including linked attachments stored elsewhere. Confirm the [official backup instructions](https://www.zotero.org/support/zotero_data) for your version. Do not treat a bibliography export or sync alone as a full backup. |

### 2. Stop writes and make the copy

Finish saves and retain their receipts. Stop the tunnel in **Manage-Study-Connection.cmd → 4**, close other assistant connections, OpenSci menus, observers, imports and editors for the selected files. Stop Zotero before copying its library. Do not cancel an external compute job merely to back up OpenSci: record the original run IDs and preserve its output through that system's procedure.

Create a private backup destination outside all selected folders. On Windows double-click **Update-OpenSci.cmd → 4**, supply that existing parent folder, verify the two default roots and add the external folders from your list. Confirm **STOPPED**. For a first upgrade from 1.0.1, run the extracted 1.1.0 updater with `-RuntimeRoot` as shown in [Updating](UPDATING.md#first-upgrade-from-101), then choose **4**. Missing paths, permissions, links, disk-space shortage or a changing input cause failure; do not proceed to upgrade after a failed backup.

The result contains the archive path, SHA-256 fingerprint and `verified: true`. A separate `receipt.json` records the same fingerprint and selected roots. The ZIP is **not encrypted**. It may contain private configuration and research. The tool creates a restricted directory, but protect copied backups with an encrypted device or encrypted backup service and appropriate access permissions. Never upload a backup to the public repository or issue tracker.

### 3. Verify an independent copy and test recovery

Copy the ZIP and receipt to separate protected storage. Retain the fingerprint in an independent trusted record. Open PowerShell or a Linux terminal in a verified OpenSci installation. Use the actual configured Python and replace the paths and `TRUSTED_BACKUP_SHA256` with the receipt's fingerprint:

```text
python -B scripts/update_runtime.py verify-backup --archive /private/backup.zip --sha256 TRUSTED_BACKUP_SHA256
python -B scripts/update_runtime.py restore-backup --archive /private/backup.zip --sha256 TRUSTED_BACKUP_SHA256 --destination /private/new-recovery-check
```

The destination must **not exist**. On Windows paths can be quoted absolute paths such as `"D:\OpenSci-Backups\backup.zip"`; substitute the full Python executable path if `python` is not on PATH. The output contains `runtime`, `coordinator` and any `extra-N` folders; consult the archive's `backup-manifest.json` for their original roots. Check several representative Study records, manuscripts and attachments against the original. Test restored Zotero separately through Zotero's own procedure. Restoration starts no service and does not activate another coordinator.

A restored directory is a recovery copy, not a live replacement. Original filesystem ACLs, Windows registry/startup settings, installed applications, live processes and credential portability are not restored by this ZIP tool. Re-establish those settings deliberately, with one active coordinator. For a failed software update, use transaction recovery first; it preserves newer Study data rather than rolling it back.

Record which folders were included, which external systems were handled separately, the trusted digest and whether a recovery exercise succeeded. An untested recovery remains unverified. Keep at least one known-good older backup until the upgraded installation and real integrations have been checked.


## Coverage

Source-and-state backup requires Python 3.10+ and Git; explicit coordinator-only `--state-only` backup requires Python without Git or extra packages. It archives reachable source history and workspace state, not a whole-machine image. Store originals, trusted SHA-256 and external assets in independent controlled storage; another copy on the same disk is not an off-machine backup.

| Included | Additional work |
| --- | --- |
| Tracked files and Git HEAD/refs-reachable history in a self-contained bundle | Commit or separately preserve uncommitted work; reflogs/unreachable objects are excluded |
| Coordination projects/imports/requests/reviews/approvals with original bytes and hashes, excluding locks | Back up protected external approval originals separately; imported approval is not execution authority |
| Environments and supported local JSON configuration | Inspect for secrets first; .env, SSH keys and licenses are not collected |
| Resource manifest | Separately copy referenced datasets/models/results |

Software, PDK/toolboxes, virtual environments, Git LFS objects, Git remotes/user config/hooks, OS accounts/ACLs and services are excluded and must be rebuilt/reaccepted. No home or credential-store scan is performed. Already tracked secrets or secrets in local JSON may still be archived; the tool does not scan for secrets or encrypt. Protect backups appropriately. Payload is limited to 4 GiB uncompressed and roughly 100,000 entries. Symlinks, junctions and submodules are rejected for automatic migration.

## Create and verify

Commit source; stop every state writer, autosave, import and active Research Workspace session. Reconcile running IDs. Jobs may continue independently, but coordinator records must remain quiescent during backup. Use a clean repository and an existing output directory outside it. --quiesced asserts that the operator stopped writers; it does not stop services.

```text
python -B scripts/backup_project.py backup --workspace . --output ../OpenSci-backup.zip --quiesced
python -B scripts/backup_project.py verify --archive ../OpenSci-backup.zip --expected-sha256 TRUSTED_SHA256
```

Retain the first output's digest in an independent trusted record and use it for all later checks. Rehashing an untrusted archive does not establish provenance. The backup takes Research Workspace's local lock and rechecks inventory/content/HEAD/refs, but external editors do not honor that lock. Verification checks exact archive files/sizes/digests and referenced snapshots without contacting hosts or executing archived code. complete_project_migration=false explicitly leaves software, external assets and actual reproduction unaccepted.

## Restore

```text
python -B scripts/backup_project.py restore --archive ../OpenSci-backup.zip --expected-sha256 TRUSTED_SHA256 --destination ../OpenSci-recovery
```

Keep the old writer stopped. Destination must not exist. The resulting workspace is `../OpenSci-recovery/workspace`. A same-disk staging area verifies/restores Git before exclusive destination publication; no merging or overwriting occurs. Temporary staging is cleaned on failure; rare publication failure may leave the newly created empty target, requiring inspection and a different retry destination. No tasks are submitted.

HEAD/refs and raw state are preserved, with detached HEAD. The operator later chooses a development branch and restores the reviewed origin. Restore does not connect agents, approve work or start services. Reconcile the origin digest and actual local path before claiming readiness. Explicit upgrade/relocate may continue a study after device loss when writers/runs/identity/history are verified; historical task and approval bytes remain unchanged. Changed code or execution environment requires new tasks, IDs and approval.

## External resources and acceptance

Create coordination/resources.json from its example using stable resource IDs, versions, relative filenames and trusted raw digests. Only config/device.local.json maps these IDs to actual absolute roots. Run verify_resources with the trusted manifest digest and the device mapping. Exit 0 proves listed bytes match; empty/unmapped/missing/mismatched manifests fail. Extra files, installation, licenses and downloads are not validated. List each relevant file and bind manifest versions to the protocol.

Fill [MIGRATION_ACCEPTANCE.md](coordination/templates/MIGRATION_ACCEPTANCE.md) with separate conclusions for materials, decision history, original-run traceability and scientific reproducibility. Byte recovery is distinct from numerical tolerances, units, convergence or sensitivity. Study history and operation receipts are backed up and checked throughout the committed chain. Restore into a new directory and retain the current records and their later facts. Stop observer and MCP writers before backup. Default protected observer/MCP policy local JSON is included; custom config locations, desktop settings, SSH restrictions, services and ACLs need separate backup. Restore retains receipts/status bytes, not processes or bulk artifacts, and must never silently activate a second writer. Windows runtime.local.json and the local shortcut must be recreated for the installed tool paths on the destination machine.

## Zotero and literature coverage

The backup collector includes coordination/literature, untracked manuscript files and config/literature.local.json. It excludes coordination/literature/cache, which is rebuildable. Preserve snapshots, original search/operation receipts, job events/results, budget allocations, citation mappings and manuscript recovery copies. The external Zotero database, original attachment storage, browser profile, Windows Credential Manager and installed writing tools are not included. Validate Zotero restoration independently in isolation. An unresolved write or model charge must survive software rollback; restoring source cannot undo its external effect. [LITERATURE.md](LITERATURE.md) describes library rebind and recovery gates.

The library owner can perform the Zotero exercise through an existing backup policy. It does not make whole-library copying or restarting Zotero a prerequisite for routine OpenSci use. Record an unperformed recovery exercise as unverified, without inferring data damage.

## Independent coordinator backup

For separated record storage, add `--state-only` to the backup command and point `--workspace` at the coordinator directory. The versioned archive retains Study heads, immutable history, evidence/import/literature records and the selected local configuration; it has no research Git commit or bundle. Keep runtime software and external research folders separately. The same verify/restore commands recognize this archive and restore exact state bytes into a new directory without initializing Git or activating a writer. Both kinds require actual stopped writers and verified external assets. See [Study integration recovery](docs/STUDY_CONNECTION.md#upgrade-and-recovery).
