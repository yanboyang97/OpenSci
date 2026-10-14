# Daily Use

Before using `Invoke-OpenSci`, paste the complete [command helper](GETTING_STARTED.md#command-context) into the same PowerShell window. Example study IDs and paths must be replaced with your actual values.

A study is the record container for a continuing research objective. Tasks, reviews, approvals and runs are distinct objects linked to it. Read the current record before a deliberate update and verify the result afterwards. Discussion in a conversation does not automatically become formal state.

## Browse Studies

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File 'C:\OpenSci\Start-OpenSci.ps1' -List
```

This command does not connect remotely or create a study. `STUDY-001` below is an example, not an existing study. Use your own ID, consisting of 3–48 uppercase letters, digits or hyphens and starting with an uppercase letter.

<a id="first-study"></a>
## Creating the first study

Open the root launcher, select **2 Create Study**, and enter a study ID and research goal. Research Workspace creates the study through the Operation Service and displays a receipt. Keep the printed request ID if the operation is interrupted; query that receipt before retrying.

For automation without source provenance use `create_study`, as below. The command-line `hub.py init` entry requires a configured Git-backed workspace and creates a study through the Operation Service. It accepts `--request-id`; if omitted, it prints a generated ID to standard error before writing. `select-agent`, `select-compute`, `checkpoint` and `attach` use the same service for current study records. Preserve the ID and exact inputs for receipt recovery. These commands keep JSON results on standard output.

For automation, save a request with a new ID and execute it using the [Operation Service](../INTEGRATION.md). A new study uses `expected_revision: 0`. Do not execute this example after creating the same study in the menu.

```json
{
  "schema_version": 1,
  "request_id": "STUDY-001-INIT-001",
  "study_id": "STUDY-001",
  "expected_revision": 0,
  "operation": "create_study",
  "arguments": {"goal": "Define the research question and acceptance criteria", "research_workspace": null, "binding": null}
}
```

```powershell
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'execute', '--request', 'config/command.local.json')
```

## Inspecting and resuming

After creation, `show`, `history` and `brief` read coordinator records without checking live nodes. `resume` for a source-free Study reads saved progress without a remote probe. Source-backed resume probes the selected Development Workspace using the SSH alias in coordinator `config/hub.local.json` (`opensci-dev` is only an example). A successful listing does not establish remote readiness.

```powershell
Invoke-OpenSci -Arguments @('scripts/hub.py', '--coordinator-root', 'C:/OpenSci-Data', 'show', '--study', 'STUDY-001')
Invoke-OpenSci -Arguments @('scripts/hub.py', '--coordinator-root', 'C:/OpenSci-Data', 'history', '--study', 'STUDY-001', '--limit', '20')
Invoke-OpenSci -Arguments @('scripts/hub.py', '--coordinator-root', 'C:/OpenSci-Data', 'brief', '--study', 'STUDY-001')
# Remote check; use after the SSH development workspace is ready.
Invoke-OpenSci -Arguments @('scripts/hub.py', '--coordinator-root', 'C:/OpenSci-Data', 'resume', '--study', 'STUDY-001')
```

On continuation, inspect the goal and phase, latest progress note, Development Workspace binding, source commit, missing material and all registered run IDs. Preserve IDs after a disconnect and reconcile the actual node before creating replacement work or resubmitting anything.

## Recording progress

Menu phases are **Evidence**, **Plan review**, **Implementation**, **Awaiting approval**, **Experiment running**, **Analysis** and **Archived**. The menu shows numbered choices and their stable request IDs; enter a number or ID, or leave blank to cancel. A phase label is not proof of experiment completion. Research Workspace validates the prerequisites for each transition.

Select **8 Record Progress** to record a phase and notes after reviewing and committing source changes. The Operation Service checks source/workspace consistency and uses the latest study revision. The menu asks before a remote check. Resolve configuration or source discrepancies before retrying a failed transition.

Use **10 Study Overview** and **11 Save Discussion Progress** for source-free research discussion. The `save_progress` operation records summary, decisions, hypotheses, evidence references, questions and next steps. See [Chat and Work continuation](STUDY_CONNECTION.md).

For automation, `operation: note` records text without probing the Development Workspace, while `checkpoint` validates source-related phase changes. Read the revision, prepare a unique request and verify the receipt. Prepare the request file below with actual values; an unchanged example is not a ready request.

```powershell
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'show', '--study', 'STUDY-001')
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'execute', '--request', 'config/command.local.json')
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'receipt', '--study', 'STUDY-001', '--request-id', 'STUDY-001-NOTE-001')
```

For a unified command that requires a remote probe, place `--allow-remote-check` before the `execute` subcommand. Pure text `note` and read-only queries do not require that permission for their operation.

## Evidence, tasks and experiments

Use `literature/evidence_matrix.csv` for sources and claims, and `methodology/experiment_protocol.md` for hypotheses, data, methods and acceptance criteria. Preserve source bytes and a trusted digest when attaching material. The Operation Service restricts `attach` inputs to `coordination/imports/`, rather than arbitrary paths.

The later execution workflow is evidence/protocol → review → fixed source/environment → DRAFT task → independent human approval → execution by the human submission account → artifact checks using the original run ID. `prepare_task.py` does not approve, unified commands do not submit, and the observer does not rerun jobs. See [implementation](../IMPLEMENTATION.md) and [record contracts](../RECORDS.md) for the complete parameters. Enable and verify each part of the execution chain before use.

## Before finishing a session

Save and review source changes, record completed work, unresolved questions and next steps, reconcile run IDs and last known states, then generate a brief for handover. A brief is a dated local snapshot and is not automatically sent to a desktop, phone or another conversation.

## Literature work

Use menu option 9, a shared CLI request, or the restricted MCP entry described in the [literature guide](LITERATURE.md). Search produces candidates; collect requires explicit targets and a destination. Read the current study revision, inspect per-source/per-item coverage and verify the command receipt. Native Word actions wait for a local observed session; remote analysis starts only after explicit dispatch and budget reservation.
