# Simulation Lab

## Purpose and contract

The pure-Python Sum Calculation (`sum-v1`) and Quadratic Calculation (`quadratic-v1`) adapters exercise one lifecycle without networking, licenses or professional tools. They validate software interfaces and durable records, not scientific conclusions or production approval.

Preflight verifies registration, API version and implementation/engine hashes; prepare bounds finite parameters and freezes a request; submit records a queued state and immediately returns a simulation ID; query/cancel reload state and cancel queued work; collect checks raw artifact digests; validate independently recomputes the example result. Real tools still need installation/license/resources, locked data/environment, actual scheduler submission/query/cancellation, bulk collection and scientific units/convergence/sensitivity acceptance.

State is stored under simulation-runs/<ID> in the selected store. Identical ID/request retries return the original state; conflicting reuse fails. A restarted process queries the same directory without resubmission. Advance explicitly progresses queued → running → finished. There is no daemon: queued work does not execute after the terminal closes. Interrupted running state is not automatically rerun or declared cancelled; reconcile the original ID. Preserve incomplete disk-failure directories instead of deleting them to reuse an ID.

```text
python -B scripts/simulation.py preflight --adapter sum-v1
python -B scripts/simulation.py prepare --adapter sum-v1 --parameters config/simulation.sum.example.json --output ../simulation-request.json
python -B scripts/simulation.py --store ../simulation-store submit --request ../simulation-request.json --expected-sha256 PRINTED_REQUEST_SHA256 --id SIM-001
python -B scripts/simulation.py --store ../simulation-store query --id SIM-001
python -B scripts/simulation.py --store ../simulation-store advance --id SIM-001
python -B scripts/simulation.py --store ../simulation-store collect --id SIM-001
python -B scripts/simulation.py --store ../simulation-store validate --id SIM-001
```

Choose new output paths outside source. Repeat the same submit to test idempotency. For cancellation use a new SIM-002 and cancel before advance. For Quadratic Calculation (`quadratic-v1`), use its parameter example, new request path and new ID. Simulation records have separate record_type/schema and simulation_only=true. Neither side accepts the other's task contract. They do not write formal experiment runs, bind approval or invoke run_task. Example stores lie outside project backup scope.

## Extension

Add an explicitly registered module in scripts/simulation_adapters defining api_version=1, version and prepare/execute/validate. Register the instance under an English ASCII key in REGISTRY; the key supplies the name, so no name attribute is required. No caller-supplied modules or shell commands are loaded. Requests freeze adapter/engine digests, so changed implementation rejects old continuation. Preserve old source for historical inspection and prepare new IDs with changed source. Require bounded input, deterministic artifacts, independent validation and failure tests. Regression covers an additional registered adapter without engine changes, duplicate/conflicting requests, cancellation, process recreation, tampering and refusal to rerun interruptions. These examples do not implement professional software, license scheduling or scientific acceptance.
