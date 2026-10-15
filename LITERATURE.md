# Literature Workspace Reference

OpenSci **1.0.1**. Literature Workspace connects literature search, a personal Zotero library, evidence snapshots, bounded analysis and citation writing. The [daily guide](docs/LITERATURE.md) explains the workflow; this reference lists exact operations and integration limits.


## Ownership and deployment

Zotero owns the personal library, collection tree, original attachments, single-paper notes and native annotations. OpenSci owns study associations, search attempts, immutable evidence snapshots, derived indexes, jobs, usage, cross-paper results and manuscript mappings. No OpenSci setting controls Zotero's storage directory or sync policy. Group-library operations are rejected.

The existing coordinator remains the only study writer. Its local Windows context handles Zotero, campus/browser access, PDF extraction and Word. The configured SSH development node receives bounded immutable evidence for explicitly dispatched analysis. It never receives a forwarded Zotero port, Windows grant, browser session or a continuous PDF mirror. A remote worker cannot write the study head. Results become formal only after coordinator verification and import.

| Module | Responsibility |
| --- | --- |
| `literature_contract.py`, `literature_service.py` | Strict requests, protected grants, settings, workflow and command results |
| `zotero_adapter.py`, `literature_credentials.py` | Zotero Local API on loopback, personal/instance binding, versioned writes, named Windows grants |
| `literature_sources.py`, `literature_import.py` | Official metadata APIs and bounded native RIS/BibTeX exports |
| `literature_fulltext.py` | Public PDF validation and licensed PMC version resolution |
| `literature_store.py`, `literature_evidence.py` | Durable external intents, immutable snapshots, parsed evidence and SQLite FTS5 |
| `literature_jobs.py`, `literature_transport.py` | Budget reservations, fixed-node detached workers, control and result import |
| `literature_word.py`, `literature_writing.py` | Observed native Word tasks, saved-document checks, stable BibTeX keys and text citations |

## Protected configuration

Create operator-owned `config/literature.local.json` in the **records directory** from [the example](config/literature.example.json), or apply `literature.config_update` through the coordinator. Keep it out of source distribution. `config_update` requires the current revision and a complete validated configuration at revision + 1. Existing library rebinds stop for migration and reconciliation. A capability probe can run before binding and before creating a Study. Study mutations require an existing Study and the relevant grants; discussion and literature Studies do not require Git.

Research directions are user-defined. The distributed example leaves them empty and supplies five source definitions. Add the topics and authorized sources needed for your work. Stable IDs survive renaming. Adding a source name does not implement an adapter.

| Group | Semantics |
| --- | --- |
| `research` | Directions, keywords/exclusions, source IDs, adapters, access modes, capabilities and request rates |
| `browser.preferred` | `edge` or `chrome`; independent Connector, login and campus verification |
| `zotero` | Fixed loopback port 23119, binding ID, server instance, optional user ID, credential reference, prompt permission and allowed operations |
| `execution` | Existing node reference, bounded timeout and retry configuration; unknown call outcomes are never automatically retried |
| `models.provider_ref` | Existing provider entry on the executor, with no automatic provider fallback |
| `limits` | Finite request/token/estimated-cost allowance and global/node/model/study concurrency for paid work |
| `accounting` | Named accounting period and finite cumulative request/token/cost allowances |
| `grants` | Study-to-operation/item/collection/manuscript allowlist for the fixed agent role |
| `retention` | Declared unreferenced-cache retention policy; no automatic destructive pruning is scheduled |

`inherit` reads current research settings when a task starts. `pinned` preserves the study's settings; an operator can supply a full `pinned_config` when binding. Pinned research settings cannot change Zotero access. New tasks always use the smaller current global/study/task limit and the current accounting period. Every started task preserves its effective configuration. Historical tasks and evidence survive deletion of a direction or source. Current grants and write permissions are checked again at execution/recovery and cannot be inherited from stale authority.

Source credentials accept only `env:VARIABLE_NAME`. Zotero additionally supports `wincred:OpenSci/Zotero/personal` on Windows. This is a reference, not a key. With explicit user consent, an Always Allow grant is retained in the current Windows user's Credential Manager under that name plus the bound instance digest. An Allow Once grant remains process-only. No credentials are enumerated. Revocation removes only the named rejected grant and stops the write; it does not silently reprompt. An instance change requires reconciliation and cannot reuse another instance's grant. Other platforms can use environment references supplied by the operator.

Use Zotero's own local communication setting and authorization dialog. Do not directly edit its database. Local reads are not authenticated; keep port 23119 on loopback and do not forward it to any node. Website login, campus access, API authorization and full-text entitlement are separate capabilities.

## Shared command envelope

CLI, menu option 9 and MCP use `CommandService`. Commands have the usual `schema_version`, `request_id`, `study_id`, `expected_revision`, `operation` and `arguments`. Literature arguments contain exactly `payload`. The 64,000-byte request limit still applies, including embedded citation exports; split larger exports into bounded, traceable batches.

```json
{
  "schema_version": 1,
  "request_id": "STUDY-001-LIT-001",
  "study_id": "STUDY-001",
  "expected_revision": 1,
  "operation": "literature.search",
  "arguments": {
    "payload": {
      "intent": "Find papers about reusable food packaging",
      "queries": {"pubmed": "reusable food packaging"},
      "limit": 10
    }
  }
}
```

Save a reviewed request as `C:/OpenSci-Data/config/literature-request.local.json` and use its absolute path from the software directory (or enter that same absolute path in menu option 9):

```text
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data execute --request C:/OpenSci-Data/config/literature-request.local.json
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data receipt --study STUDY-001 --request-id STUDY-001-LIT-001
```

MCP `opensci_literature_read` accepts only read operations. `opensci_execute_command` needs writable launch policy plus the protected literature grant for agent mutations. Config changes, destructive apply, pinned-setting edits and native annotation creation require operator scope. Requests never supply their own principal, role, executable command or secret. Protected files and OS isolation remain necessary; a same-account agent with unrestricted file access is not isolated by JSON alone.

| Operation | Required payload | Optional payload / behavior |
| --- | --- | --- |
| `literature.capabilities` | Empty object | Read-only live API probe; untested Word/browser/source features remain unverified |
| `literature.get` | Empty object | `item_key`, `kind`; or `request_id`; or Word `task_id`; otherwise study binding/settings |
| `literature.search_library` | `query` | `limit`, `index`; index results include freshness and snapshot ID |
| `literature.search` | `intent`, source-to-query `queries`, `limit` | `overrides`, `resume_run`; writes a search record, never Zotero |
| `literature.search_import` | `search_run`, `source_id`, `format`, `text`, `source_url`, `coverage_note` | RIS/BibTeX native export creates candidates, not library items |
| `literature.collect` | `search_run`, selected `candidate_ids`, `collection_keys` | `tags`, candidate-to-URL `fulltext_urls`; per-item receipts |
| `literature.fetch_fulltext` | One-element `item_keys` | Exactly one of public `url` or `pmcid` |
| `literature.organize` | `item_keys`, `collection_keys`, `tags` | `new_collection`, item-to-text `notes`, explicit `annotation` |
| `literature.bind_study` | `config_mode`, `collection_refs`, `item_refs` | `item_links`, operator `pinned_config` |
| `literature.read` | `level`: discovery/regular/deep | `item_keys`, `index`; empty keys resolve current study associations |
| `literature.analyze` | `snapshot_id`, `node_ref`, `analysis_kind` | `overrides`, `parent_job`; kind is `evidence_matrix` or `model` |
| `literature.job_dispatch` / `job_import` | `job_id` | Trusted remote-check policy required |
| `literature.job_status` | `job_id` | `refresh` contacts the fixed executor but does not import formal results |
| `literature.job_pause` / `job_resume` / `job_cancel` | `job_id` | Control request and effective state are separate |
| `literature.export` | `snapshot_id`, `manuscript_id` | Stable bibliography and sample LaTeX/Quarto files |
| `literature.cite` | `manuscript_id`, `path`, `expected_sha256`, `format`, `item_refs`, `marker` | Word `phase`, `task_id`, `native_action`; see writing below |
| `literature.preview_change` | `kind`, `item_key`, `change` | Version-bound before-image, digest, impact and recovery |
| `literature.apply_change` | `preview_id`, `confirmed_digest` | Operator only; stale object/instance/preview rejects |
| `literature.reconcile` | `original_request_id` | Original caller/study/scope; collection, organization or PDF intent only |
| `literature.config_update` | `expected_config_revision`, full `config` | Operator only |

An `item_ref` is `{binding_id, item_key}`; a collection reference uses `collection_key`. An item link records `status` (included/excluded/undecided) and `reason` within one study. One study's screening never changes another's. Collection membership is resolved at task creation; a renamed collection keeps its key, while a missing collection stops with `collection_deleted` and preserves history.

## Searches, import and library writes

PubMed uses ESearch/EFetch and retains original article XML. Web of Science uses its Starter API; Scopus and IEEE use their official metadata APIs when separately authorized. API credentials are not inferred from campus web access. Google Scholar uses a browser-assisted path and native per-record export; no generic bulk API is claimed. Unsupported adapters remain `not_executed`.

Each source attempt preserves its literal query, adapter version, timestamp, sort, cursor, requested window, candidates, capabilities and coverage. Failures are isolated; `zero_results` is distinct from `permission_denied`, `waiting_user`, `partial` and unavailable. Resume preserves the original query/settings and appends history. A native export is deliberately partial: it cannot prove the entire external search was exhausted. RIS must be terminated; BibTeX accepts explicit values and nested braces, and rejects macros/preambles/concatenation rather than silently changing their meaning.

Only explicit collection requests create Zotero items. Strong DOI/PMID matches also require title/type consistency; ambiguous identifiers or title-only matches wait for review. Existing records are reused with additive collection/tag changes. Original user notes remain untouched; new AI notes are separate objects labeled with the generating request. Reanalysis creates another note version. New PDF annotations require explicit operator permission and position data; reading never creates highlights.

Creates use deterministic object keys, version zero, an external intent journal and a post-write read. Updates/deletes bind the current local object version. The external journal distinguishes intent, started, verified, rejected and unknown outcomes. A crash after a possible write never causes an unconditional resend. Batch results retain each successful item and each failure. `reconcile` creates a new coordinator receipt while reusing original external intent IDs; original result blobs remain immutable. An unresolved intent remains `outcome_unknown`. A known rejected change needs a reread and a newly reviewed intent.

Field/note replacement, relationship removal and deletion require a concrete preview and confirmation digest. A newer manual edit invalidates the preview. Native merging is intentionally handed to Zotero, followed by survivor/reference reconciliation; copying fields then deleting another item is not a supported merge.

## Full text and evidence

PDF acquisition validates HTTPS destination, media type, magic/end markers, bounded size and checksums. Generic downloads reject private-network destinations and redirects. The fixed official PMC bucket supports licensed article versions, checks DOI/PMID, selects a published version from its listing and verifies its recorded PDF MD5. It does not infer subscription entitlement. Publisher login/CAPTCHA or unavailable full text waits for browser/user assistance. Attachment creation/upload uses Zotero's API; no direct storage-file writes occur. Metadata may succeed while full text remains missing.

Discovery snapshots contain metadata/abstracts. Regular/deep snapshots add available notes, native annotations and extracted PDF text, retaining attachment bytes' SHA-256, parser/version, one-based PDF pages, separate printed labels and failed pages. PyMuPDF is optional. No OCR, image understanding or formula verification is inferred from text extraction. Scans and failed pages are reported for OCR or visual reading; `deep_verified` remains false until separate scientific checks. Annotation read failure does not suppress otherwise available attachment parsing.

Snapshots use content-derived IDs excluding their own ID field. Exact manifest/file bytes are validated on publication, transfer, load and model/result processing. They are historical evidence even after a Zotero edit or deletion. The local SQLite FTS5 index is derived and rebuildable. A full versions-map digest conservatively invalidates cached freshness after new children or library edits; deleted/changed/unrevalidated rows are not presented as current. Parsing and indexing are explicit operations, not a background whole-library synchronization service.

Model prompts receive only evidence in the selected snapshot: metadata, abstracts, readable text pages, separately attributed notes/annotations and coverage. Failed pages are excluded. Claims require item identity, attribution, attachment hash and an actual page or note/annotation version. Missing abstracts, unparsed attachments, failed pages, invented printed labels and self-certified model verification are rejected. Structural validation cannot establish scientific truth; humans still check conditions, counterexamples, equations, figures and conclusions against originals.

## Jobs, costs and recovery

Analysis first creates a persistent queued job and reservation; dispatch is a separate explicit step to the existing SSH node. A complete checksum-verified snapshot is required before the detached worker launches. Job/attempt/generation/node/snapshot bindings prevent stale results and duplicate execution. A launch marker with unknown outcome stops takeover; confirmed dead-process recovery reuses the original attempt. Closing chat does not stop a dispatched worker. Local offline actions wait; the remote uses only its received snapshot. No recurring search, new service, compute/GPU authority or alternate node is enabled automatically.

Paid work requires finite request, token, estimated-cost and concurrency ceilings plus a named global accounting period. Unsettled reservations remain charged across disconnection and are not reallocated. Smaller limits prevail. The executor reuses an enabled `openai_compatible`, `gemini` or `claude` provider with tools disabled. Supply its ordinary `config/providers.local.json` locally on the executor, and a versioned `literature_price_per_million` object with `input`, `output`, `revision`. No provider secret is transmitted from the coordinator. Input uses a conservative UTF-8-byte allowance; provider output tokens are bounded. Oversized context waits for a smaller batch/budget. A lost/timed-out call remains unresolved and cannot auto-retry.

Response token counts and estimated dollars are separate from an actual provider invoice. Estimates cannot enforce the provider's final bill or spending outside visible OpenSci jobs. Configured retries do not authorize repeating an unknown call; use a new explicitly linked request after reconciliation. The deterministic evidence matrix has no model charge and marks scientific conclusions unassessed.

Pause/cancel first persist a control request. An active provider call may finish and be billed before acknowledgement; effective state changes only when the worker observes control. Queued, running, waiting_local, waiting_user, waiting_budget, paused, succeeded, partial, failed and cancelled are distinct. Terminal attempts remain immutable. Poll/import the original job after reconnect; never delete launch/operation journals to force a restart.

## Writing and backup

Word uses `format=word`, `phase=prepare`, a saved `manuscript/*.docx` hash, real item references and `native_action` (insert/edit/refresh/bibliography/style). Insert uses a unique text marker; edit uses an existing citation ID; style uses an installed Zotero style URL. Preparation stores a recovery copy and holds a manuscript slot. The trusted local desktop agent uses the observed Zotero plugin and saves the document. It then submits `phase=verify` with the task ID and resulting saved hash. The verifier checks native fields, item targets, unrelated citations, bibliography, style and body scope. Zotero 10's single selected citation-ID change is recorded as a migration. It never fabricates field structures or invokes Unlink Citations. A client without an observed native session remains `waiting_local`; there is no headless Word automation claim. Plugin re-edit, refresh and save/reopen require separate live acceptance on the installed combination.

LaTeX/Quarto exports maintain manuscript-specific stable keys, respect recognized fixed keys and stop on collisions. Generated samples are not reported compiled until both actual toolchains run. Text insertion checks the saved hash and exactly one marker under `manuscript/`, preserves a recovery copy and modifies only that marker. Existing manuscripts require inventory and a copy before acceptance; there is no promised lossless cross-format conversion.

OpenSci backup includes literature journals, snapshots, usage, results, mappings, recovery copies, untracked manuscripts and literature local configuration, excluding rebuildable `coordination/literature/cache`. Zotero's external database/original files, Windows credentials, browser profiles and tools are not included. Verify Zotero's own independent backup and restore separately. Software rollback does not undo already applied Zotero or Word changes: retain their records and use reviewed compensating changes. Do not delete unresolved jobs or the only copy of cited evidence as cache cleanup. See [backup and migration](BACKUP_AND_MIGRATION.md).

Zotero restoration is a separate owner-managed acceptance exercise using the user's existing backup policy. OpenSci does not require a new full-library copy, a storage change or an application restart for ordinary integration use. If that exercise is not performed, record the recovery gate as unverified; this alone is not evidence of damaged or untrustworthy library data.
