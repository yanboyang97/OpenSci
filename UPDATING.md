# Updating OpenSci

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
