"""Read-only capability checks; no login, API calls, or credential output."""
import argparse
import importlib.util
import platform
import shutil
import subprocess
import sys
from common import print_json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["offline", "compute", "models", "scheduler"], default="offline")
    parser.add_argument("--provider", choices=["codex", "claude", "gemini", "openai_compatible"])
    args = parser.parse_args()
    requirements = {"offline": [], "compute": ["git"], "models": [], "scheduler": ["git"]}
    tools = {}
    for tool in ("git", "ssh", "tmux", "codex", "claude", "gcloud", "dvc"):
        tools[tool] = {"found": shutil.which(tool) is not None}
        if tools[tool]["found"] and tool in ("git", "codex", "claude"):
            try:
                result = subprocess.run([tool, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
                tools[tool]["version"] = result.stdout.strip()[:200] if result.returncode == 0 else "probe_failed"
            except (OSError, subprocess.TimeoutExpired):
                tools[tool]["version"] = "probe_failed"
    modules = {}
    for name in ("mlflow", "prefect", "google.genai"):
        try:
            modules[name] = importlib.util.find_spec(name) is not None
        except (ModuleNotFoundError, ImportError):
            modules[name] = False
    failures = []
    if sys.version_info < (3, 10):
        failures.append("Python 3.10+ required")
    if args.profile != "offline" and not sys.platform.startswith("linux"):
        failures.append("This execution profile requires Linux/WSL")
    failures += [name+" is required" for name in requirements[args.profile] if not tools[name]["found"]]
    if args.profile == "scheduler" and not modules["prefect"]:
        failures.append("Prefect is not installed in this scheduler interpreter")
    if args.profile == "models":
        if not args.provider:
            failures.append("Select --provider for model-specific local prerequisites")
        elif args.provider in ("codex", "claude"):
            tool = tools[args.provider]
            if not tool["found"] or tool.get("version") in (None, "", "probe_failed"):
                failures.append(args.provider+" CLI is missing or its version probe failed")
        elif args.provider == "gemini" and not modules["google.genai"]:
            failures.append("google.genai is not installed in this interpreter")
    report = {"profile": args.profile, "provider": args.provider, "ready": not failures,
              "local_prerequisites_ready": not failures, "authentication": "not_checked",
              "connectivity": "not_checked", "service_ready": "not_checked", "python": platform.python_version(),
              "platform": platform.platform(), "tools": tools, "optional_python": modules, "failures": failures,
              "scope": "Offline readiness only; model-specific credentials, versions and connectivity require separate acceptance"}
    print_json(report)
    return 0 if not failures else 2

if __name__ == "__main__":
    raise SystemExit(main())
