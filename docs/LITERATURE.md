# Literature Workspace

[Handbook](../DOCUMENTATION.md) · [Exact operations and limits](../LITERATURE.md)

This tutorial takes you from one paper in Zotero to a checked citation in a manuscript. Zotero holds the papers, attachments and personal notes. OpenSci records which evidence a Study used, what was screened, and what was saved. A search produces candidates; it does not add them to your library.

Start with [connecting and reading one paper](#literature-first-paper). Continue to [search and collect](#literature-search), [read and organize](#literature-evidence), [optional analysis](#literature-analysis), [citations](#literature-writing), or [recovery](#literature-recovery) when needed. You can stop after any completed step.

## Before you start

Complete [Getting Started](GETTING_STARTED.md) and create a Study. A discussion/literature Study needs no Git repository, remote computer or paid model provider. This chapter uses software in `C:\OpenSci`, records in `C:\OpenSci-Data`, and Study `STUDY-001`; substitute your own paths and ID throughout. On macOS/Linux use your actual absolute paths and Python 3.10+; the Windows launchers and native Word workflow are separate integrations.

Have Zotero 10 running on the computer holding the records, one paper in **My Library**, and a small collection you are willing to use. Preserve your existing Zotero and OpenSci backups. Group libraries are outside this release's supported scope. For assistant use, first complete [assistant setup](PLUGINS.md); you can also follow the structured requests below from the local command entry.

<a id="literature-first-paper"></a>
## 1. Connect Zotero and read one existing paper

1. In Zotero, open **Settings → Advanced** and enable **Allow other applications on this computer to communicate with Zotero**. Keep Zotero running. This is the local connection, not your Zotero website password. [Zotero local API](https://www.zotero.org/support/dev/web_api/v3/local_api)
2. Open the OpenSci menu, select **9 Literature Workspace**, and enter `capabilities`. Look under `result.zotero` for `read: available`, `api_version: 3` and `instance_id`. Copy the actual `instance_id`; it identifies this library database. `read_only: true` and `committed: false` are normal for this check. Browser, Word, sources and model checks can still be unverified.
3. For **first setup only**, copy the software file `config/literature.example.json` to `C:\OpenSci-Data\config\literature.local.json`. If that destination already exists, preserve it and follow [settings updates](#literature-settings). Open the copy in a text editor, find its `zotero` object, and replace just that object with the following. Replace `INSTANCE_FROM_CAPABILITIES` with step 2's value. Keep the rest of the example intact and save UTF-8 without a `.txt` suffix.

```json
{
  "base_url": "http://127.0.0.1:23119",
  "binding_id": "personal-library",
  "instance_id": "INSTANCE_FROM_CAPABILITIES",
  "user_id": null,
  "credential_ref": null,
  "allow_authorization_prompt": false,
  "allowed_operations": []
}
```

`personal-library` is a name you choose once; the instance value comes from Zotero. Leave `user_id` null unless you have checked the numeric `library.id` of your personal-library result. Keep port 23119 local to this computer. A different instance requires reconciliation, not copying the new ID over an old binding.

4. Search for a word from the title of your existing paper with `literature.search_library`, using the request instructions below. Read `result.items`, match the title, and copy the paper's `key` (eight capital letters/digits). This is the parent paper key, not a PDF attachment key or DOI.
5. Use `literature.get` with payload `{"item_key":"ABCD1234"}`, replacing the sample key. A returned item with the expected title is the first successful read. No Zotero write permission is needed.

### How to submit a request and see its result

In a connected assistant, say: “Read the selected Study and search my local Zotero library for the title ‘reusable food packaging’. Show matching titles and item keys. Do not change the library.” The assistant uses the same operations. Review its proposed targets before allowing a change. The menu itself has no natural-language model or visual settings editor.

For a local request, open PowerShell in the software folder and read the current Study revision:

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
$OpenSciPython = (Get-Content -LiteralPath '.\config\runtime.local.json' -Raw -Encoding UTF8 | ConvertFrom-Json).python
& $OpenSciPython -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data show --study STUDY-001
```

Use the integer in `cursor.revision` as `expected_revision`. Save this complete example to `C:\OpenSci-Data\config\literature-request.local.json`, replacing the title, Study ID and revision:

```json
{
  "schema_version": 1,
  "request_id": "LIT-LOCAL-001",
  "study_id": "STUDY-001",
  "expected_revision": 1,
  "operation": "literature.search_library",
  "arguments": {"payload": {"query": "reusable food packaging", "limit": 10}}
}
```

Run the saved request:

```powershell
& $OpenSciPython -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data execute --request C:/OpenSci-Data/config/literature-request.local.json
```

Alternatively enter that **absolute file path** in menu option 9. The menu resolves relative paths from the records directory; the CLI resolves them from its current directory. Absolute paths work in both. Menu 9 accepts only `literature.*` operations.

On macOS/Linux, from your software folder, use the same arguments after your Python executable, for example `/usr/bin/python3 -B scripts/hub_command.py --coordinator-root /home/researcher/OpenSci-Data ...`. Replace `...` with the `show` or `execute` arguments above and use the actual absolute request-file path. Find Python with `command -v python3`; check it is 3.10+.

For later examples, keep the six outer fields and replace `operation` and the object inside `arguments.payload`. Use a new `request_id` for each new action and reread the Study revision before each change. Keep an unchanged original request for recovery. Do not paste a payload by itself as a full request.

Read operations return data under `result`. Changes return a committed receipt with a literature result reference. To see a change's detailed result, submit a new **read** request with `operation: literature.get` and payload `{"request_id":"THE_ORIGINAL_CHANGE_REQUEST_ID"}`. Copy the returned `run_id`, `snapshot_id`, `job_id` or `task_id` into the next step; do not invent these values. A committed receipt proves the Study recorded the operation, while individual external results may still be partial or waiting.

<a id="literature-settings"></a>
## 2. Choose permissions and associate papers with the Study

### Update an existing configuration safely

Copy the current records file `config/literature.local.json` to a separate working copy. Note its `revision`, edit only the settings you need, and increase `revision` by one. Submit an operator request with `operation: literature.config_update`. Its payload contains `expected_config_revision` (the old number) and `config` (the **entire edited configuration**, not just changed fields). The outer `expected_revision` is still the Study revision; these are different counters. Read back the result and saved file. If either counter is stale, reread and reconcile before a new request. Agents cannot grant themselves these permissions.

For collecting papers or adding notes, set `allow_authorization_prompt` to `true` and select only needed `allowed_operations`: `create` for new items/notes/attachments and `update` for adding tags or collection membership. Zotero presents its own local authorization dialog at the first write. Choose the permission you intend. If you explicitly want a Windows grant retained, use `credential_ref: "wincred:OpenSci/Zotero/personal"` and approve retention; a one-use grant is not retained. Other systems can use the prompt or an operator-supplied environment reference. Never place a literal key in a request, configuration or conversation. `delete` and `annotation` are separate permissions, unnecessary for the ordinary steps below.

For an assistant to create a reading snapshot of the selected paper, replace the empty `grants` object with a narrowly chosen grant, substituting your Study and item keys:

```json
{
  "STUDY-001": {
    "operations": ["literature.bind_study", "literature.read", "literature.export"],
    "item_keys": ["ABCD1234"],
    "collection_keys": [],
    "manuscript_paths": []
  }
}
```

This is the value of `grants`, not a whole configuration. Add an operation, item, collection or manuscript path only when you authorize that work. The MCP policy must also allow writes. These grants restrict delegated changes and snapshot targets; they do not make the unauthenticated local Zotero API a read-isolation boundary.

### Bind the selected evidence

Use `literature.bind_study` with:

```json
{
  "config_mode": "inherit",
  "collection_refs": [],
  "item_refs": [{"binding_id": "personal-library", "item_key": "ABCD1234"}],
  "item_links": {"ABCD1234": {"status": "included", "reason": "Relevant to the packaging question; full text still needs checking"}}
}
```

`inherit` uses current research settings for new tasks. `pinned` freezes a copy; neither can override current permissions or budgets. `included`, `excluded` and `undecided` record screening decisions for this Study. A later bind replaces its item/collection reference lists, so retain associations you still need. Inspect the result to confirm the intended key and reason.

For a collection, obtain its eight-character key from a local API listing, then put `{"binding_id":"personal-library","collection_key":"COLL1234"}` in `collection_refs`. Here is a read-only Windows listing of the first 20 collections:

```powershell
(Invoke-RestMethod -Uri 'http://127.0.0.1:23119/api/users/0/collections?limit=20&start=0' -Headers @{'Zotero-API-Version'='3'; 'Zotero-Allowed-Request'='1'}) | Select-Object key, @{Name='name'; Expression={$_.data.name}}
```

On macOS/Linux use `curl -H 'Zotero-API-Version: 3' -H 'Zotero-Allowed-Request: 1' 'http://127.0.0.1:23119/api/users/0/collections?limit=20&start=0'`. Read each result's `key` and `data.name`; increase `start` to 20, 40, and so on for further pages. The header accommodates Zotero 10's browser-request protection. [Zotero 10 local API changes](https://www.zotero.org/support/dev/zotero_10_for_developers)

When reading a bound collection through an assistant, grant its key **and every resolved paper key** you intend to read. Newly added papers can require a grant update. A renamed collection keeps its key; a deleted collection needs a reviewed replacement.

<a id="literature-search"></a>
## 3. Search, screen and collect

### Search one source first

State the question, date/type restrictions, sources and stopping condition. For example: “Search PubMed for up to ten papers about reusable food packaging. Show relevance, publication type and missing information before adding anything.” Use `literature.search` with:

```json
{"intent":"Find evidence about reusable food packaging","queries":{"pubmed":"reusable food packaging"},"limit":10}
```

Read its detailed result with `literature.get`. Save `run_id`, inspect every source attempt's query, returned range, status and candidates, and note the `candidate_id` of each chosen paper. Ten results are a bounded first pass, not a complete systematic review. To continue the same query, add `resume_run` with the previous `run_id`, retaining the same query/settings and reviewing the new range.

| Source ID | What to prepare | If direct search is unavailable |
| --- | --- | --- |
| `pubmed` | Network access to PubMed's metadata API | Preserve the error and retry the intended search when reachable |
| `web_of_science` | Authorized Starter API credentials | Review the website and import a native citation export |
| `scopus` | Authorized Scopus API credentials | Review the website and import its native export |
| `ieee` | Authorized IEEE Xplore API credentials | Review the website and import its native export |
| `google_scholar` | Your browser and any required human interaction | Export selected records; OpenSci has no generic bulk API |

Source credentials are references such as `env:SCOPUS_API_KEY`, supplied to the process by the operator. Institutional website login is not an API credential. Sources, research directions and preferred Edge/Chrome browser are configured in the records file; each browser needs its own Connector and access checks. A source name alone does not add an adapter.

For a browser export, first run a search including that source so OpenSci retains its query. On the website, review results, choose RIS or BibTeX export, and open the downloaded text. Submit `literature.search_import` with the original `search_run`, matching `source_id`, `format` (`ris` or `bibtex`), exact export `text`, original HTTPS `source_url`, and a `coverage_note` explaining what you selected and what remains unsearched. Ask your assistant to prepare the JSON string so newlines and quotes remain valid; inspect it before submission. The complete request must stay under 64,000 bytes; split larger exports into traced batches. Use the **new** returned `run_id` for collecting imported candidates. Import remains partial coverage and still does not add papers to Zotero.

### Collect only reviewed candidates

After confirming titles, identifiers and the destination collection, use `literature.collect`:

```json
{"search_run":"RUN_ID_FROM_RESULT","candidate_ids":["CANDIDATE_ID_FROM_RESULT"],"collection_keys":["COLL1234"],"tags":["packaging-screening"]}
```

Replace every sample value. Authorize this operation and target collection before using an assistant. Read per-item receipts and check the selected collection in Zotero. Strong matching records may be reused; uncertain duplicates wait for review. Metadata, full text and reading status are separate. Keep successful items if another item or PDF fails.

To fetch a missing publicly accessible PDF for one known item, use `literature.fetch_fulltext` with `{"item_keys":["ABCD1234"],"url":"https://publisher.example/paper.pdf"}` after replacing the URL with the actual permitted PDF. Alternatively replace `url` with `pmcid: "PMC1234567"` using the real article's PMC identifier. Supply exactly one route. A login page, abstract page or subscription barrier is not a PDF. If access requires your browser, obtain the paper through your authorized route and attach it in Zotero, then reread the item. Do not repeat an uncertain browser save blindly.

<a id="literature-evidence"></a>
## 4. Read, take notes and check evidence

Use `literature.read` with the selected paper:

```json
{"level":"regular","item_keys":["ABCD1234"],"index":true}
```

This saves an evidence snapshot in OpenSci. It does not itself generate a model summary or write highlights into Zotero. Read its result, retain `snapshot_id`, and inspect coverage and failures before drawing conclusions.

To open the captured material, use the returned `manifest` path under `C:\OpenSci-Data\coordination\literature\`. For example, `snapshots/ACTUAL_SNAPSHOT_ID/manifest.json` lists evidence files relative to that snapshot folder, including each paper's `metadata.json`, notes and any extracted attachment text. Open only files actually listed; missing full text is not filled in automatically. A local assistant with separately authorized file access can read these files. A chat connected only through OpenSci MCP receives the result's location/coverage, not an arbitrary file-reading tool or the complete snapshot text: provide the selected material yourself if you want to discuss it there, or use the configured analysis-job route below.

| Level | What to use it for | What still needs checking |
| --- | --- | --- |
| `discovery` | Screen title, metadata and abstract | Methods, full text and detailed claims |
| `regular` | Read available text, notes and annotations | Missing attachments, failed pages, figures and scans |
| `deep` | Prepare material for detailed evidence checking | Scientific validity, equations, visual content and supplements; extraction alone never proves these |

PDF text extraction needs optional PyMuPDF, listed in [requirements](INSTALLATION.md). Missing parser/text coverage must remain visible. To search an explicitly built index, use `literature.search_library` with `{"query":"packaging","limit":10,"index":true}`. Read freshness and snapshot identity; after Zotero changes, make a new snapshot of affected papers rather than treating old hits as current evidence.

A useful reading request is: “For this snapshot, separate the author's findings, my notes and your interpretation. For each claim give the item, attachment/page when actually available, uncertainty and unreviewed material.” Never infer a page number from an abstract or missing file. Paper contents cannot authorize tools or expand permissions.

To add a reviewed note without replacing existing notes, use `literature.organize`:

```json
{"item_keys":["ABCD1234"],"collection_keys":[],"tags":["needs-method-check"],"notes":{"ABCD1234":"Screening note: check the sample size and reuse conditions in the full text before using this result."}}
```

OpenSci creates a separate child note labeled with the generating request. Check it in Zotero and retain original notes. Adding PDF annotations needs explicit operator permission and actual position data; it is not a side effect of reading. Collection creation is also an operator action. Cross-paper conclusions stay with the Study.

<a id="literature-analysis"></a>
## 5. Optional: run and recover an analysis job

You can read papers and discuss them with your chosen assistant without enabling OpenSci's job runner. The assistant's own plan/usage terms still apply. For a recorded analysis job, first configure an existing enabled development node using SSH with role `agent` in the [node catalog](CONFIGURATION.md). Use its node ID, not an SSH hostname. The node-free beginner setup cannot dispatch jobs.

Use `literature.analyze` with:

```json
{"snapshot_id":"SNAPSHOT_ID_FROM_RESULT","node_ref":"remote-agent","analysis_kind":"evidence_matrix"}
```

This creates a job; it does not start it. `evidence_matrix` produces a deterministic, unassessed evidence table without a model call. Read the result and copy `job_id`.

For `analysis_kind: model`, first configure an enabled provider in the executor's `config/providers.local.json`, verify its model/account/credential settings, and set `models.provider_ref` in the literature configuration to that entry's name. Follow [configuration](CONFIGURATION.md) rather than assuming sample model names work for your account. Set **every** field in `limits` to finite values and define a named `accounting` period with finite cumulative allowances. A bounded single-job trial could use the following two objects, after you choose and approve the amounts:

```json
{
  "limits":{"max_requests":1,"max_tokens":4000,"max_cost_usd":1.0,"concurrency":1,"node_concurrency":1,"model_concurrency":1,"study_concurrency":1},
  "accounting":{"period_id":"trial-01","max_requests":1,"max_tokens":4000,"max_cost_usd":1.0}
}
```

These are settings fragments, not a full configuration or a price quote. Apply them through step 2. A model job without complete limits remains `waiting_budget`; do not raise limits just to clear an error. Cost accounting is an estimate, not a provider invoice.

| Next action | Operation and payload | Success to look for |
| --- | --- | --- |
| Start the prepared job | `literature.job_dispatch`, `{"job_id":"JOB_ID_FROM_RESULT"}` | The fixed executor accepted the existing job |
| Check without contacting the executor | `literature.job_status`, same payload | Local recorded status; it may be old |
| Check the executor | `literature.job_status`, add `"refresh":true` | Current executor response; result is not yet imported |
| Register the result | `literature.job_import`, job ID payload | Verified result attached to the original job/Study |
| Pause, resume or cancel | `literature.job_pause`, `literature.job_resume` or `literature.job_cancel`, job ID payload | Worker acknowledgement, not just a pending control request |

Dispatch, import and refreshed status require trusted remote-check permission. For a reviewed CLI request, put `--allow-remote-check` **before** `execute`; for MCP an operator must enable `allow_remote_checks` in the stopped connection's policy and restart it. Keep ordinary local reading at its default permission. After a timeout, recover the original job and receipt before starting anything else. Unknown paid-call outcomes retain their reservation until reconciled.

<a id="literature-writing"></a>
## 6. Use real references in a manuscript

### LaTeX / BibTeX and Quarto

These tools turn a text manuscript and a bibliography file into a formatted paper. Use `literature.export` with `{"snapshot_id":"SNAPSHOT_ID_FROM_RESULT","manuscript_id":"paper-01"}`. Keep the same manuscript ID when updating that paper. Inspect `entry_count`, `citation_map` and any key conflicts in the result.

Files are under `C:\OpenSci-Data\coordination\literature\exports\paper-01\`: `references.bib`, `sample.tex` and `sample.qmd`. Check titles/authors against Zotero. Existing fixed citation keys are retained; the map links keys to real items. Create a working folder under `C:\OpenSci-Data\manuscript\`, for example `manuscript/paper-01/`, and copy the needed sample and bibliography there. For the citation example below, name your working manuscript `draft.tex` (or `draft.qmd`).

Place a unique marker such as `OPENSCI_CITE_HERE_01` where the citation belongs. Save and close other editors. On Windows obtain the saved file's SHA-256 with:

```powershell
(Get-FileHash -LiteralPath 'C:\OpenSci-Data\manuscript\paper-01\draft.tex' -Algorithm SHA256).Hash.ToLowerInvariant()
```

On macOS use `shasum -a 256 /absolute/path/to/draft.tex`; on Linux use `sha256sum /absolute/path/to/draft.tex`. Copy the 64-character hash. Submit `literature.cite` with:

```json
{"manuscript_id":"paper-01","path":"manuscript/paper-01/draft.tex","expected_sha256":"SAVED_FILE_SHA256","format":"latex","item_refs":[{"binding_id":"personal-library","item_key":"ABCD1234"}],"marker":"OPENSCI_CITE_HERE_01"}
```

For Quarto use a `.qmd` path and `format: quarto`. An assistant also needs this exact path in its manuscript grant. The marker must occur exactly once and the saved hash must still match. The result reports the new hash and recovery copy. Refresh/copy matching `references.bib` alongside the manuscript after a new export.

With the appropriate toolchain already installed, open a terminal in the working manuscript folder. For the supplied LaTeX sample run `pdflatex sample.tex`, `bibtex sample`, then `pdflatex sample.tex` twice. For Quarto run `quarto render sample.qmd`. Use your actual filename for a renamed draft. Inspect the produced PDF/HTML and resolve missing citations. Each format you use needs its own compile check; `not_compiled` in an export result is not a successful build.

### Word with the Zotero plugin

1. On the local desktop with Word and Zotero's Word plugin available, create the records folder's `manuscript` directory if needed and save a copy as `C:\OpenSci-Data\manuscript\draft.docx`. Insert `OPENSCI_CITE_HERE_01` once outside existing citation fields, save, and obtain its hash as above.
2. Submit `literature.cite` with the same fields as the text example, but `path: manuscript/draft.docx`, `format: word`, and `phase: prepare`. Use actual item references. Read the resulting task and retain `task_id`. `waiting_local` means Word still needs attention.
3. You or an authorized desktop assistant must observe the actual document path/window. Select only the marker, use Zotero **Add/Edit Citation**, select the real requested paper, and save. Stop for unsaved/concurrent edits, unclear focus or a missing plugin. Never substitute typed text or unlink citation fields. [Zotero Word plugin](https://www.zotero.org/support/word_processor_plugin_usage)
4. Compute the **new saved hash**. Submit a new `literature.cite` request keeping the original manuscript, path, item references and marker, adding `task_id`, changing `phase` to `verify` and setting `expected_sha256` to the new hash. A `succeeded` result verifies saved field structure and edit scope.
5. In a copy, test reopening and editing the citation through Zotero. For bibliography, refresh or style changes, prepare and verify separate tasks using `native_action: bibliography`, `refresh` or `style`. Bibliography/refresh allow an empty marker; style uses the installed style's Zotero URL. Do not combine these changes into the insertion task. Record observed plugin checks separately from structural verification.

OpenSci does not open Word or drive the plugin by itself. Its supplied workflow depends on a real local desktop session; connecting ChatGPT/Claude/Codex alone does not grant desktop control or establish native Word acceptance on every operating system.

<a id="literature-recovery"></a>
## 7. Recover safely and recognize incomplete work

| What you see | What to do next |
| --- | --- |
| `waiting_local`, `local_api_disabled` or `unsupported_version` at the first probe | Open Zotero 10, check its local setting, then rerun the read-only probe |
| `binding_required` / `instance_changed` | Check the configured personal library; after a restore/move, reconcile identities before rebinding |
| `forbidden` / `authorization_required` | Check the selected Study, agent grant, allowed write operation and Zotero dialog; do not grant unrelated access |
| Empty search vs `permission_denied`, `waiting_user`, `partial` | Distinguish no results from incomplete access; retain failed source coverage and complete authorized browser steps |
| Saved metadata with missing PDF/text | Keep the item, resolve access/parser coverage, then fetch or reread only what is missing |
| `version_conflict` | Reread the Study, Zotero item or manuscript that changed; review the new state before a new request |
| Lost response or `outcome_unknown` | Query the original request through the same caller identity; never assume an external write did not happen |
| `waiting_budget` / pending job control | Review reservations or worker acknowledgement on the existing job before retrying |

For a completed partial `collect`, `organize` or `fetch_fulltext`, use `literature.reconcile` with `{"original_request_id":"ORIGINAL_REQUEST_ID"}` through the original caller and Study. It preserves verified objects and checks uncertain intents. If the command itself lacks a receipt, first recover that original request as described in [save recovery](TROUBLESHOOTING.md#save-recovery).

Replacing fields/notes, removing relationships or deleting objects needs `literature.preview_change` first. For example, `{"kind":"items","item_key":"ABCD1234","change":{"action":"update","fields":{"title":"Reviewed corrected title"}}}` returns old content, impact, `preview_id` and `digest`. A human checks the concrete change; only then does an operator use `literature.apply_change` with `{"preview_id":"PREVIEW_ID_FROM_RESULT","confirmed_digest":"DIGEST_FROM_PREVIEW"}`. A newer manual edit invalidates the preview. Native duplicate merging belongs in Zotero, followed by survivor/reference reconciliation.

OpenSci backups cover its receipts, snapshots and manuscripts. They do not back up Zotero's external database, original attachments, browser profile or credentials. Back up and restore those separately using your Zotero policy, into isolated destinations for a recovery exercise. Reconcile library identity, citations and unfinished jobs before reactivating one coordinator. Reading this tutorial or installing the source does not complete deployment acceptance: real source access, browser Connector paths, PDF/visual coverage, model limits, Word/toolchain behavior and separate restoration must be checked where you use them.
