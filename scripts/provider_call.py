"""Internal provider adapter. Snapshot hash and completion checks fail closed."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit
from common import atomic_write, canonical, digest, limited_env, read_json, stamp, write_json

class IncompleteResponse(RuntimeError):
    def __init__(self, reason, status="incomplete"):
        super().__init__(reason)
        self.reason, self.status = reason, status

def reason_name(reason):
    return str(getattr(reason, "name", reason) or "unknown").rsplit(".", 1)[-1].lower()

def check_finish(reason, complete=("stop",)):
    reason = reason_name(reason)
    if reason not in complete:
        status = "truncated" if reason in ("length", "max_tokens", "max_output_tokens") else "refused" if reason in ("safety", "content_filter", "recitation", "blocklist", "prohibited_content") else "incomplete"
        raise IncompleteResponse(reason, status)
    return reason

def decode_compatible(obj):
    choice = obj["choices"][0]
    finish = check_finish(choice.get("finish_reason"))
    message = choice["message"]
    if message.get("refusal") or message.get("tool_calls"):
        raise IncompleteResponse("refusal_or_tool_request", "refused")
    return message.get("content") or "", obj.get("usage", {}), obj.get("model"), finish

def decode_gemini(response):
    candidates = response.candidates or []
    if not candidates:
        raise IncompleteResponse("no_candidate", "refused")
    finish = check_finish(candidates[0].finish_reason)
    usage = response.usage_metadata.model_dump(mode="json") if response.usage_metadata else {}
    return response.text or "", usage, getattr(response, "model_version", None), finish

def decode_claude(obj):
    if obj.get("is_error") or obj.get("subtype") != "success":
        raise IncompleteResponse(str(obj.get("subtype", "unknown_claude_completion")))
    finish = check_finish(obj.get("stop_reason", "end_turn"), ("end_turn", "stop_sequence"))
    usage = {k: obj[k] for k in ("usage", "modelUsage", "total_cost_usd", "duration_ms") if k in obj}
    return obj.get("result", ""), usage, list(obj.get("modelUsage", {})) or None, finish

def endpoint_url(value):
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("An HTTPS endpoint without credentials/query/fragment is required")
    return value.rstrip("/")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Endpoint redirects are refused; review the configured destination")

def provider_env(cfg):
    # Credentials needed by a provider stay available only to its own adapter/CLI.
    extras = {
        "codex": ("CODEX_HOME", "CODEX_API_KEY", "OPENAI_API_KEY"),
        "claude": ("GOOGLE_APPLICATION_CREDENTIALS", "CLAUDE_CONFIG_DIR"),
        "gemini": ("GOOGLE_APPLICATION_CREDENTIALS",),
        "openai_compatible": (cfg.get("api_key_env", ""),),
    }[cfg["kind"]]
    env = limited_env(extras)
    if cfg["kind"] == "claude":
        env.update(CLAUDE_CODE_USE_VERTEX="1", ANTHROPIC_VERTEX_PROJECT_ID=cfg["project"],
                   CLOUD_ML_REGION=cfg["location"], ANTHROPIC_MODEL=cfg["model"],
                   ANTHROPIC_DEFAULT_SONNET_MODEL=cfg["model"], ANTHROPIC_DEFAULT_OPUS_MODEL=cfg["model"],
                   ANTHROPIC_DEFAULT_HAIKU_MODEL=cfg["model"], CLAUDE_CODE_DISABLE_MODEL_ACCESS_FALLBACK="1",
                   CLAUDE_CODE_DISABLE_1M_CONTEXT="1")
    return env

def cli_version(name, env):
    result = subprocess.run([name, "--version"], env=env, capture_output=True, text=True, encoding="utf-8", timeout=10)
    if result.returncode:
        raise RuntimeError(name+" version probe failed")
    return result.stdout.strip()[:200]

def invoke(cfg, prompt, out, meta):
    kind, env = cfg["kind"], provider_env(cfg)
    if kind == "codex":
        meta["client_version"] = cli_version("codex", env)
        last = out.with_suffix(".last-message.txt")
        command = ["codex", "exec", "--sandbox", "read-only", "--ephemeral", "--ignore-user-config",
                   "--skip-git-repo-check", "--color", "never", "--json", "--output-last-message", str(last)]
        if cfg.get("model"):
            command += ["--model", cfg["model"]]
        result = subprocess.run(command+["-"], input=prompt, text=True, encoding="utf-8", errors="replace",
                                capture_output=True, env=env)
        atomic_write(out.with_suffix(".response.jsonl"), result.stdout.encode("utf-8"))
        events = []
        for line in result.stdout.splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                continue
        completed = [e for e in events if e.get("type") == "turn.completed"]
        if result.returncode or not completed or any(e.get("type") in ("turn.failed", "error") for e in events):
            raise IncompleteResponse("codex_turn_not_completed")
        actual = next((e.get("model") for e in reversed(events) if e.get("model")), None)
        return last.read_text(encoding="utf-8"), completed[-1].get("usage", {}), actual, "turn.completed"
    if kind == "claude":
        meta["client_version"] = cli_version("claude", env)
        command = ["claude", "--bare", "-p", "--model", cfg["model"], "--tools", "", "--disallowedTools", "mcp__*",
                   "--no-session-persistence", "--max-turns", "2", "--max-budget-usd", str(cfg["max_budget_usd"]), "--output-format", "json"]
        result = subprocess.run(command, input=prompt, text=True, encoding="utf-8", errors="replace", capture_output=True, env=env)
        atomic_write(out.with_suffix(".response.json"), result.stdout.encode("utf-8"))
        if result.returncode:
            raise IncompleteResponse("claude_cli_exit_"+str(result.returncode))
        return decode_claude(json.loads(result.stdout))
    if kind == "gemini":
        from google import genai
        from google.genai import types
        import importlib.metadata
        meta["client_version"] = importlib.metadata.version("google-genai")
        with genai.Client(vertexai=True, project=cfg["project"], location=cfg["location"],
                          http_options=types.HttpOptions(timeout=300000)) as client:
            result = client.models.generate_content(model=cfg["model"], contents=prompt,
                     config=types.GenerateContentConfig(max_output_tokens=cfg["max_output_tokens"]))
        write_json(out.with_suffix(".response.json"), result.model_dump(mode="json"))
        return decode_gemini(result)
    if kind == "openai_compatible":
        key = env.get(cfg["api_key_env"])
        if not key:
            raise RuntimeError("Required API-key environment variable is absent")
        payload = {"model": cfg["model"], "messages": [{"role": "user", "content": prompt}],
                   "max_tokens": cfg["max_output_tokens"], "stream": False}
        request = urllib.request.Request(endpoint_url(cfg["base_url"])+"/chat/completions", data=canonical(payload),
                  headers={"Content-Type": "application/json", "Authorization": "Bearer "+key})
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=300) as response:
            obj = json.load(response)
        write_json(out.with_suffix(".response.json"), obj)
        meta["client_version"] = "python-urllib "+sys.version.split()[0]
        return decode_compatible(obj)
    raise ValueError("Unknown provider kind")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True, help="Frozen per-review snapshot")
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    meta = {"schema_version": 1, "provider": args.provider, "started_utc": stamp(), "status": "failed"}
    code = 1
    try:
        snapshot, _ = read_json(args.config, args.config_sha256)
        cfg = snapshot["providers"][args.provider]
        if cfg.get("enabled") is not True:
            raise ValueError("Provider disabled")
        raw = args.prompt.read_bytes()
        meta.update(requested_model=cfg.get("model") or None, config_sha256=args.config_sha256, prompt_sha256=digest(raw),
                    destination={k: cfg[k] for k in ("kind", "project", "location", "base_url") if k in cfg})
        text, usage, actual, finish = invoke(cfg, raw.decode("utf-8"), args.out, meta)
        if not isinstance(text, str) or not text.strip():
            raise IncompleteResponse("empty_output")
        if len(text.encode("utf-8")) > 32000:
            raise IncompleteResponse("report_exceeds_32KB")
        atomic_write(args.out, (text.rstrip()+"\n").encode("utf-8"))
        write_json(args.out.with_suffix(".usage.json"), usage)
        meta.update(status="complete", finish_reason=finish, actual_model=actual, usage=usage,
                    actual_model_observed=actual is not None)
        code = 0
    except IncompleteResponse as exc:
        meta.update(status=exc.status, finish_reason=exc.reason)
    except Exception as exc:
        # Provider exceptions can contain prompts/keys; retain type, not raw exception text.
        meta.update(status="failed", error_type=type(exc).__name__)
    finally:
        meta.update(finished_utc=stamp(), exit_code=code)
        write_json(args.out.with_suffix(".call.json"), meta)
    if code:
        print("Provider did not produce a complete report; inspect the protected call record", file=sys.stderr)
    return code

if __name__ == "__main__":
    raise SystemExit(main())
