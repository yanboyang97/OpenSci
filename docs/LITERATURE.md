# Literature Workspace

[Handbook](../DOCUMENTATION.md) · [Protocol and configuration](../LITERATURE.md)

Zotero keeps your library, attachments, notes and annotations. OpenSci searches sources, records screening decisions, reads selected evidence, dispatches bounded analysis and helps maintain citations. Searching alone never imports a paper.

## Configure Literature Workspace

1. Preserve the library and OpenSci backups, and inventory existing manuscripts and fixed citation keys. Start with an explicitly authorized collection or copy.
2. Open Zotero 10 and enable its setting allowing other applications on this computer to communicate with Zotero. Keep the connection local.
3. In the OpenSci menu, select **9**, then enter `capabilities`. This is a read-only probe. A working API does not prove browser, source, model or Word readiness.
4. Create a Study in Research Workspace before study mutations; discussion/literature Studies do not require Git. The Operation Service records literature operations with the same revision and receipt checks as other study changes.
5. Prepare protected `config/literature.local.json` using [the example](../config/literature.example.json) and the observed server instance. Select only the desired write operations. An operator can apply later settings changes through `literature.config_update`.
6. Authorize the local Zotero prompt when a chosen write needs it. Opt into the named Windows credential reference only if you want the grant retained for this Windows user. Keep all key values out of requests and chat.
7. Associate the desired item/collection references with `literature.bind_study`, and grant only the relevant agent operations and targets. Configure the existing node/provider and finite limits before paid analysis.

The example settings contain no research directions, five source definitions and Edge. Add your own topics in protected `config/literature.local.json`, or use the operator-only `literature.config_update` request; there is no visual settings editor. A listed source still needs its own access rights. Zotero remains the only place for library storage settings. Switching to Chrome requires its own Connector, website login and access checks.

A capability response with `read_only: true` and `committed: false` means no study update was requested. Read each returned availability status; these fields alone do not indicate a failed check or a ready integration.

## Search, then decide what to collect

In a connected assistant conversation, state the question, dates/types, sources and stopping condition, for example: “Search PubMed for up to ten papers about reusable food packaging; show candidates before adding anything to my library.” The assistant prepares the same `literature.search` request used by CLI or menu option 9. The protocol document lists exact payloads. Save a reviewed request as, for example, `config/command.local.json`; choose **9 Literature Workspace** and enter that path. Relative paths are resolved from the OpenSci folder, regardless of where the launcher was opened. Only `literature.*` requests are accepted here; use the Operation Service for other requests. The current menu accepts a reviewed request-file path; it does not include a separate natural-language model or a visual settings editor.

Review each source's actual query, returned window and status. Campus web access does not grant an API key. Login or CAPTCHA steps may need you. A failed source is retained as incomplete while other sources continue. Native RIS/BibTeX exports can be attached to the original search using `search_import`; they stay candidate records and retain partial-coverage notes.

To import, identify candidates and the destination collection explicitly. `collect` reuses strong matching records, adds permitted tags/collection membership and tries a known public PDF/PMC route. Suspected duplicates wait for review. The result shows metadata, full-text and reading status separately. If metadata succeeded but a PDF failed, retain the record and use `fetch_fulltext` after resolving access. Do not click a browser save repeatedly when its outcome is unknown.

## Read and analyze selected evidence

Use discovery for metadata/abstract screening, regular for available text/notes/annotations, and deep for evidence that still needs precise checking. Read the coverage report: extracted text does not mean a figure, proof, scan or supplement was verified. AI notes are new Zotero child notes; cross-paper results stay in OpenSci. Explicit user instructions are required for new PDF highlights/comments.

An index search identifies the evidence snapshot and freshness. If Zotero changed, refresh affected evidence instead of treating a historical hit as current. A missing or failed attachment does not justify inventing page numbers.

`analyze` creates a persistent job; `job_dispatch` starts it on the selected existing node after reservation. Use `evidence_matrix` for a deterministic, unassessed matrix without a model call. A model analysis requires an enabled provider and finite request/token/cost/concurrency allowances. Requests lacking limits stay `waiting_budget`. Estimated cost is not an invoice. Online analysis is optional and never enabled merely by reading a paper.

Follow the original job with `job_status`, then `job_import` to register the result. Pause/cancel may remain pending until the worker acknowledges them. After a lost connection, recover the existing job and call receipt; do not create a replacement to guess whether the first one ran.

## Write with real citations

For Word, save a copy under `manuscript/`, choose real Zotero items and a unique insertion marker, and prepare a native task. The local desktop agent must see the correct Word window and use the Zotero plugin. It stops for unsaved/concurrent edits, ambiguous focus or a missing plugin. Save, verify the resulting native fields, and test plugin re-edit, refresh, bibliography, style and reopening. A waiting task is not a completed citation, and static text is not dynamic Zotero integration.

For LaTeX/Quarto, export the selected snapshot for a stable manuscript ID, inspect `references.bib`, then insert keys at a saved-version marker. Existing fixed keys remain stable across metadata edits. Compile with both installed toolchains before accepting the manuscript. Key conflicts and unresolved citations require repair in a copy.

## Recovery and maintenance

Keep the original command ID when querying a missing receipt. For a completed partial collection/organization/PDF result, use `literature.reconcile` with its original request ID; this preserves successful objects and reuses uncertain external intents. A newer manual edit causes a version conflict. Replacement/removal/deletion first requires a fresh preview and targeted confirmation. Native merge belongs in Zotero followed by reconciliation.

OpenSci backups preserve literature evidence, receipts and manuscripts, but do not back up the external Zotero database, original attachments, credentials or browser profile. Restore each separately into isolated destinations, then reconcile library identity, citations and jobs before activating one coordinator. Never restore a second writer over an active workspace.

Use your existing Zotero backup policy for its separate recovery exercise. Routine integration use does not require OpenSci to copy the whole library or restart Zotero. An untested restore remains an acceptance limitation, not a finding that the library is damaged.

This release requires deployment-specific acceptance: complete personal-library reads, five-source coverage, both browser Connector paths, representative scanned/visual material, model limits and scientific checks, separate Zotero restoration and production rollout. The private acceptance record must identify passed, blocked, deferred and inapplicable cases; source installation alone does not complete those checks.
