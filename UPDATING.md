# Updating OpenSci

## Upgrade with your data and settings intact

**Before every upgrade, back up all your data and verify that backup.** Read the [complete backup checklist](BACKUP_AND_MIGRATION.md#before-every-upgrade-full-folder-backup). Include research folders, Zotero and external credentials as applicable; the updater cannot discover every file you use. Keep a second copy on a separate, protected device or encrypted backup service. Another folder on the same disk protects against an update mistake, not disk loss.

OpenSci 1.1.0 adds **Update-OpenSci.cmd** on Windows and `scripts/update_runtime.py` for command-line use. The updater changes only files in the reviewed software manifest. It preserves `.local.*` configuration, Study records, extra user files and the encrypted connection store. It neither removes retired files nor migrates Study formats, rewrites settings, starts experiments, or enables connections. It stops on edited/missing managed files, new-path conflicts, invalid packages, or detected concurrent changes. No software can guarantee safety against an actively writing external application; stopping writers is still required.

### Windows: ordinary updates from 1.1.0 onward

1. In File Explorer open the existing installation folder (for example `C:\OpenSci`) and double-click **Update-OpenSci.cmd**. Your configured Python must still exist. Use **1** to check the newest stable version, **2** to download and prepare it, or **3** to use a previously downloaded full runtime ZIP. Version checking sends no local configuration or Study data.
2. Choose an existing private folder outside the software and all data folders, for example create `D:\OpenSci-Backups` in File Explorer first. The tool creates a new dated, access-restricted subfolder. The automatic local backup is a ZIP, **not encrypted**; use an encrypted backup disk/storage for the independent copy.
3. Check the displayed software and Study data paths. The Study path comes from `config/studies.local.json`; when absent, the installation is the legacy coordinator. Add any other research/data folders you want included, one full folder path at a time, then press Enter on a blank line. The current Windows user's existing OpenSci encrypted-connection directory is automatically included; it is copied as ciphertext, not decrypted.
4. The tool verifies the archive checksum, exact file inventory and per-file hashes, then creates `plan.json` in the new update folder. Open it with Notepad. `changes` lists every software path that will change; `before` and `after` are file fingerprints. `retained_retired_files` lists old software kept on disk. Planning changes no installed files. A file-conflict diagnostic means your copy needs review; keep the custom file and do not delete it to force the upgrade.
5. Complete and verify the independent backup checklist. Type **BACKED UP** only after doing so. The menu stops its managed background connection. Close other assistant/MCP connections, OpenSci sessions, observers, importers and editors; finish or reconcile pending save receipts. Type **STOPPED** to attest that all other writers are stopped, then **UPDATE** to approve the displayed plan. These words are operator assertions, not automatic detection of every program.
6. Before replacing any software, the updater makes and verifies a full-folder `backup\backup.zip` and `backup\receipt.json`. It rechecks file fingerprints before each replacement, preserves existing file permissions during replacement, and records progress in `transaction.json`. A tiny `.opensci-update.lock` remains in the installation as an inert concurrency lock; it contains no user data.
7. When the result says `updated: true`, verify the new version and your saved Study Overview. Open **Start-Study-Chat.cmd** if you want to resume a stored-key connection. Its encrypted key and sign-in preference are retained. No data migration or new Study selection is performed. Keep backups until you have checked your actual research work.

<a id="first-upgrade-from-101"></a>
### First upgrade from 1.0.1

Version 1.0.1 does not have the new updater. Download **OpenSci-1.1.0.zip** and **SHA256SUMS.txt** from the [official release](https://github.com/yanboyang97/OpenSci/releases/tag/v1.1.0). Match the ZIP's SHA-256 against that file before running code. In Windows, search Start for **PowerShell**, open it and paste the following command, replacing the ZIP path with the downloaded file's actual location:

```powershell
Get-FileHash -LiteralPath 'C:\Users\YOURNAME\Downloads\OpenSci-1.1.0.zip' -Algorithm SHA256
```

If it matches, right-click the ZIP in File Explorer and **Extract All** into a new folder. Find the inner folder containing `Update-OpenSci.ps1`. Run this in PowerShell, replacing the first path with that extracted script's location and `C:\OpenSci` with the **existing** installation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Downloads\OpenSci-1.1.0\Update-OpenSci.ps1' -RuntimeRoot 'C:\OpenSci'
```

This execution policy applies only to this process. Choose **3**, provide the downloaded runtime ZIP and its trusted checksum, and follow the normal backup/plan/apply steps above. Keep the extracted updater until the upgrade is complete. Do not extract a release directly over an existing installation. A Git clone's customized source needs review; the updater does not commit, stash or merge Git work.

<a id="interrupted-update"></a>
### Interrupted update

Keep all writers stopped. Do not simply rerun Apply or delete `transaction.json`. Open the updater from the intact extracted package if the installed copy cannot start, choose **5**, and supply the full path to the failed update's `transaction.json`. A transaction in `applying` or `recovery_required` state can restore the earlier software bytes from its verified backup. Recovery refuses files edited since the interruption. It removes only unchanged new software files introduced by that transaction; it never restores older Study/configuration data over newer records. It does not provide a one-click downgrade of a completed update.

After recovery says `recovered: true`, inspect the original failure, verify the old installation and prepare a new plan in a new folder. If recovery reports a conflict, preserve both copies and seek maintenance help. Full data restoration is a separate operation into a **new empty destination**, described in the backup guide.

### Command-line entry (Windows or Linux)

In a terminal opened in the extracted verified release, use your configured Python (`python3` on many Linux systems). Replace every path and `TRUSTED_ZIP_SHA256` with your real values. `--extra` may be repeated for additional explicitly selected folders. The pure-Python maintenance tool does not install a Linux credential service.

```text
python -B scripts/update_runtime.py check
python -B scripts/update_runtime.py download --output /private/new-download
python -B scripts/update_runtime.py plan --package /private/OpenSci-1.1.0.zip --sha256 TRUSTED_ZIP_SHA256 --runtime /opt/OpenSci --coordinator /srv/OpenSci-Data --work /private/new-update
python -B scripts/update_runtime.py apply --plan /private/new-update/plan.json --quiesced --backup-confirmed
python -B scripts/update_runtime.py recover --transaction /private/new-update/transaction.json --quiesced
```

`--quiesced` asserts stopped writers; `--backup-confirmed` asserts your independent backup is ready. They do not perform those actions. Installers must have write permission to the selected installation; do not run a whole research assistant as administrator to bypass a file conflict. Checksums verify bytes; the official HTTPS release origin is the download trust source, not a cryptographic publisher signature.

## Record maintenance and research source changes


Update source, study records and deployment settings as separate reviewed actions. An update never grants experiment approval or activates services automatically. [History and Recovery](HISTORY.md) explains record preservation; [Maintenance Plans](docs/UPGRADE_GUIDE.md) gives the operating procedure.

1. Identify the Coordinator and all record writers. Stop writes, reconcile original run IDs and save a verified backup with its trusted digest stored separately.
2. Verify the new package in an isolated directory. Preserve original source, Git history, local configuration, study records, evidence, literature operations and manuscripts.
3. Review the source changes and shared rules. Maintain the same source identity and synchronize one reviewed commit to the intended workspaces.
4. Run the affected checks on each target platform. Verify package hashes, both handbooks, launcher behavior and the actual integrations being used.
5. If existing records require maintenance, prepare and review an explicit plan. Apply only against the unchanged record, configuration and source used for that plan.
6. Hand over to one writer. Read the resulting study and history, verify receipts and inspect original run IDs before normal use.

Changed source or shared rules can change future review/task bindings even when the product version stays the same. Preserve frozen reviews and approval originals; never edit their digests to make them authorize changed work.

Restore backups only into new directories. Verify accounts, paths, permissions, credentials and external assets separately before a recovered copy becomes the Coordinator. Planning recovery creates a new revision and preserves later evidence and runs. Restoring source does not undo external Zotero or Word effects.

Keep deployment reports, source snapshots, test output and configuration/cache ledgers in an archive outside the distribution. Current user documentation describes the current product; development chronology belongs in that archive.
