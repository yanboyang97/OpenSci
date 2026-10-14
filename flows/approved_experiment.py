"""Human-controlled Prefect adapter. Staging and environment selection are explicit."""
import os
from pathlib import Path
import re
import subprocess
import sys
from prefect import flow

@flow(name="approved-experiment", retries=0, log_prints=True)
def approved_experiment(run_id: str, approval_sha256: str) -> None:
    if not re.fullmatch(r"[A-Z][A-Z0-9-]{2,47}", run_id):
        raise ValueError("Invalid run ID")
    if not re.fullmatch(r"[0-9a-f]{64}", approval_sha256):
        raise ValueError("Invalid approval checksum")
    # Controlled worker configuration, never a free-form task/flow command parameter.
    python = Path(os.environ["OPENSCI_EXPERIMENT_PYTHON"]).expanduser()
    if not python.is_absolute() or not python.is_file():
        raise ValueError("Configure an absolute approved experiment interpreter on this worker")
    snapshot = Path.home()/"research-snapshots"/run_id
    task = Path.home()/"research-requests"/(run_id+".json")
    approval = Path.home()/"research-approvals"/(run_id+".json")
    subprocess.run([sys.executable, str(snapshot/"scripts/run_task.py"), "--task", str(task),
                    "--approval", str(approval), "--approve", approval_sha256, "--python", str(python)],
                   cwd=snapshot, check=True)
