# Development and Extension

[Handbook](../DOCUMENTATION.md)

Choose the layer before extending the system: presentation/docs, study commands, storage contracts, model review, offline simulation or production execution. Each has different obligations. Registering a simulation adapter does not enable scientific software, and adding a UI button does not expand approval authority.

## Implementation map

| Change | Read first | Check together |
| --- | --- | --- |
| Launcher/runtime | `Start-OpenSci.ps1`, `Start-ClaudeCode.ps1` | Wrappers, examples, argument/path tests |
| Commands/receipts | `scripts/command_service.py`, `hub_command.py` | Roles, fields, revisions, retries, MCP schema |
| State/history | `project_store.py`, `storage_paths.py` | Atomic writes, limits, history, migration/restore |
| Lifecycle | `lifecycle.py` | Plan digests, quiescence and preservation |
| Review | `review_round.py`, `provider_call.py`, `review_contract.py` | Frozen config, completion, environment allowlist |
| Simulation | `simulation.py`, `simulation_adapters/` | Registration, frozen requests, durable state, validation |
| Execution | `task_contract.py`, `prepare_task.py`, `run_task.py` | Approval, environment, artifacts and observation |
| Observation/interface | `observe_runs.py`, `hub_mcp.py` | Trusted sources, policies, cursors and accounts |

## Minimum contribution workflow

1. Establish the agreed Git baseline and preserve one coordinator. Work in the assigned development copy or an agreed branch, recording the objective, affected contracts and verification approach.
2. Read implementation and the maintained development regression suite. Update validators and migration rules when changing exact fields, state transitions or read/write boundaries; changing examples alone is insufficient.
3. Run tests for meaningful behavior changes. For small documentation changes, check links, commands and generated output. Run applicable platform regression before release and report skipped cases.
4. Update both languages, examples, the generated handbook and release hashes. Follow the applicable workspace review requirements; identify self-review and independent review accurately. Report every file plus verification configuration, caches and temporary-directory outcomes.
5. Commit reviewed clean source and deploy the same commit through the upgrade workflow. Running tasks retain their pinned code.

<a id="simulation"></a>
## Extending an offline simulation adapter

Register an instance under an ASCII name in `REGISTRY` in `scripts/simulation_adapters/__init__.py`. The instance provides `api_version=1`, `version`, `prepare(parameters)`, `execute(prepared)` and `validate(prepared, result)`. A `name` attribute is not required; the registry key supplies the name.

Use the Sum Calculation (`sum-v1`) and Quadratic Calculation (`quadratic-v1`) implementations as executable references. Reject unknown fields, non-finite or oversized inputs and booleans masquerading as numbers; produce bounded serializable output and validate it independently. Never load caller-selected modules or accept arbitrary shell commands.

| Method | Contract |
| --- | --- |
| `prepare(parameters)` | Validate and normalize inputs for the frozen request |
| `execute(prepared)` | Produce results; no scheduling or approval authority |
| `validate(prepared, result)` | Return whether the result meets the adapter's validation rules |

Requests freeze the adapter class's file and the engine file, not every imported dependency. Define a reproduction strategy when introducing dependencies. Changed code may prevent even querying an old request; preserve matching old source for inspection and prepare new requests/IDs for new code. `advance` is explicit and has no background daemon.

Cover valid input, rejection boundaries, identical retries, conflicting ID reuse, cancellation, process recreation, artifact tampering and refusal to rerun interrupted work. See the [simulation guide](../SIMULATION_ADAPTERS.md) for the complete workflow.

## Extending unified commands

A new command must define exact argument fields, permitted roles, write/remote-check prerequisites, revision rules, transaction behavior and receipt semantics. Keep global CLI options before subcommands. Adding MCP access requires a separate tool schema and dispatcher change; do not automatically expose all CLI capabilities.

Test denied roles, unknown fields, stale revisions, identical retries, ID reuse with changed content/identity, lock conflicts, unknown outcomes and damaged history. Recover `committed:null` by querying the original receipt rather than replaying under a new ID. Experiment approval/submission must not be casually added as ordinary agent commands.

## Extending model configuration or protocols

Existing automated-review kinds are `codex`, `claude`, `gemini` and `openai_compatible`. Adding a configuration for an existing kind differs from implementing a protocol. The former still requires account/model/endpoint/budget/completion acceptance; the latter also changes configuration validation, environment allowlists, invocation, completion detection, output records and tests.

The compatible endpoint appends `/chat/completions` to `base_url` and does not add `/v1` automatically. Truncation, refusal, tool requests or missing completion evidence must not become a successful review. Maintain the Windows interactive Claude `.psd1`/DPAPI chain separately; see the [launcher guide](../CLAUDE_LAUNCHER.md).

## Production-software integration scope

Production tasks currently accept only the public estimator example, fixed data definitions, one CPU and zero GPUs. Scientific-software or GPU integration requires coordinated task/approval contracts, resources/licensing, execution, timeout/cancellation, artifact acceptance, environment binding, observation/recovery and actual scientific validation. This defines the extension boundary; it does not provide or enable that capability.

<a id="documentation"></a>
## Documentation and offline handbook workflow

Edit the `.md` sources. Use English ASCII filenames, explicit anchors and link paths. `README.md` introduces the project in two complete sections, Chinese first and English second; keep detailed setup and commands in the handbooks. All topic guides use English; the separate Chinese handbook is `DOCUMENTATION.zh-CN.md`. `DOCUMENTATION.md` is the handbook index, `docs/` contains operational guides, and root reference files retain detailed contracts. `tools/docs_manifest.json` registers the English guides, the separate Chinese source and the bilingual README under `standalone`. The builder checks the README's links and formatting without inserting it into either single-language handbook. It generates `OpenSci-Manual.html` and `OpenSci-Manual.zh-CN.html`. Never register `.local.md` files or private bindings. `AGENTS.md` remains the single maintained rules source; its HTML rendering is only a generated view.

Place new documentation in the root or `docs/` and update `tools/docs_manifest.json`: `guides` orders the operational guides, `references` orders technical references, `code_version` matches source VERSION, and `revision` is the documentation revision date. Explicitly register references elsewhere; the builder does not automatically publish research material found in the workspace. Unlisted root or `docs/` Markdown causes the build to fail instead of silently omitting pages.

`tools/build_docs.py` uses Python and `markdown-it-py` to build a self-contained offline HTML file. Install the pinned `markdown-it-py 4.0.0` build dependency before generating the HTML. Reading the HTML requires no Python, network or service. Build dependencies are listed separately in `requirements-docs.txt`; they are not baseline research runtime dependencies and are never installed automatically.

```powershell
$OpenSciRuntime = Get-Content -LiteralPath 'C:\OpenSci\config\runtime.local.json' -Raw -Encoding UTF8 | ConvertFrom-Json
& $OpenSciRuntime.python -B -X utf8 'C:\OpenSci\tools\build_docs.py'
& $OpenSciRuntime.python -B -X utf8 'C:\OpenSci\tools\build_docs.py' --check
```

The first command rebuilds root `OpenSci-Manual.html` and `OpenSci-Manual.zh-CN.html`; the second checks source links, rendered prose and generated-file freshness without writing. Unrendered Markdown such as literal double asterisks in prose fails the build; correct its source rather than deleting symbols from generated HTML. Code examples keep their literal syntax. Inspect the two editions separately, including navigation, search, narrow-window layout and printing. At release time, regenerate `SHA256SUMS.txt` for the final distribution and run `verify_delivery.py` in a fresh extraction before adding machine files. Do not overwrite a manifest merely to suppress extra-file warnings in an installed workspace.

## Distribution

The public tree contains runtime source, contracts, generic examples and reusable build tools. Functional regression suites, fixtures and results are maintained separately in the private development archive. Do not add personal records or local validation material to a release. Use `tools/build_release.py` to package the explicit release inventory.

## Literature adapters

The [literature contract](../LITERATURE.md) extends study records with references to external versioned records, without increasing the head limit or granting experiment authority. Add operations to the allowlist, validate payload/grant boundaries and test uncertain writes, partial batches, snapshot integrity and stale generations. Native Word fixture tests validate only parsing/guards; live plugin acceptance is separate. Test Windows and Linux, both real writing toolchains, source rights, full-library failures and user-approved cost limits separately. Keep private live evidence and local bindings outside the source package. Optional PyMuPDF extracts text; OCR/visual/scientific checks cannot be inferred from parser success.
