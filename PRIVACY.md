# Privacy and Data Handling

OpenSci is self-hosted software. The repository and release archives contain source, generic examples, documentation and plugin metadata. They contain no hosted account or connection. The publisher does not receive Study data merely because the software is installed.

## Data stored by your installation

Your coordinator stores Study goals, progress, evidence references, operation receipts, immutable record history and permitted literature results. Research source, raw data, Zotero libraries and manuscripts may have separate locations. The local literature index is derived data. Connection policies contain scope and identity labels; logs and backups can also be sensitive. Choose access permissions, backup locations and retention appropriate to your research.

OpenSci does not include telemetry or a publisher-operated sync service. Optional operations can contact the services you configure: model providers receive the supplied review or analysis material; literature sources receive searches and permitted downloads; Zotero receives local API requests; SSH reaches the chosen node; MLflow and Prefect receive their configured records or work. A ChatGPT/assistant or tunnel connection also processes the tool inputs and outputs required for that interaction under the host provider's policies. No guarantee is made about an external provider's logging, retention or billing.

## Credentials and access

Use local credential stores or environment references. Never put secret values in Study text, source, examples, issues, screenshots or committed configuration. The Windows tunnel launcher uses a hidden prompt and process-only key. A private connection policy limits selected Studies and tools, but same-account filesystem access is not an isolation boundary. Protect policies, source and coordinator records with operating-system permissions. Revoke grants and stop/restart the affected connection when access changes.

Zotero owns its database and attachment storage. OpenSci uses its local API, preserves instance identity and requires explicit grants for changes. Keep the local API on loopback. Search does not authorize collection, deletion, replacement or paid analysis.

## Publishing your own copy

Keep `.local.*` files, credentials, connection profiles, personal research settings, raw data, Study records, manuscripts, result artifacts, logs, caches and backups outside Git. The release builder accepts only the explicit `tools/release_files.json` inventory and refuses unlisted working-tree files. Review that inventory and the staged content before publishing. Ignore rules do not remove already committed files or history.

The public package has no regression suite, test fixtures or test results. Development verification material is maintained outside this distribution. The runnable estimator example and calculation adapters are functional reference modules, with stated scientific limits; they contain no personal research data.

## Reporting a problem

Use the repository's GitHub security reporting channel if enabled, or open an issue containing only a non-sensitive description and ask for a private reporting route. Do not post a key, private file, internal host name or real Study record. If a credential was exposed, revoke or rotate it with its issuer; removing a file or rewriting history cannot invalidate a credential or erase copies already downloaded.
