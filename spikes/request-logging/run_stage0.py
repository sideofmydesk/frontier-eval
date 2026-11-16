"""Stage 0 of the logging spike: run Claude Code against the local stand-in.

No request reaches Anthropic and nothing is billed. For each scenario this
starts mock_api.py, runs one non-interactive Claude Code session pointed at
it with a dummy key and a fresh configuration directory, and collects:

  - the stand-in's own request log (what was actually sent)
  - Claude Code's raw API body files and index (OTEL_LOG_RAW_API_BODIES)
  - Claude Code's OpenTelemetry events (console exporter)
  - the session's JSON result

Usage:
  python run_stage0.py --claude <path to claude binary> --out <dir> [--scenario NAME ...]
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

MAIN_MODEL = "claude-opus-5-5"
SCENARIOS = ["normal", "model_mismatch", "fallback", "refusal", "error"]
DUMMY_KEY = "sk-ant-stage0-dummy-not-a-real-key"
HERE = Path(__file__).resolve().parent

# Variables that could route a session to real credentials or another provider.
SCRUB = [
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_MODEL",
    "ANTHROPIC_PROFILE", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY", "ANTHROPIC_BEDROCK_BASE_URL", "ANTHROPIC_VERTEX_BASE_URL",
    "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT", "CLAUDE_AGENT_SDK_VERSION",
]


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_port(port, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def run_scenario(claude, out_root, scenario, extra_env=None, label=None, timeout=180):
    label = label or scenario
    out = out_root / label
    if out.exists():
        raise RuntimeError(f"{out} already exists; pass a fresh --out directory")
    (out / "bodies").mkdir(parents=True)
    (out / "config").mkdir()
    (out / "cwd").mkdir()
    port = free_port()
    mock_log = out / "standin-requests.jsonl"
    mock = subprocess.Popen(
        [sys.executable, "-I", str(HERE / "mock_api.py"), "--port", str(port), "--scenario", scenario,
         "--main-model", MAIN_MODEL, "--log", str(mock_log)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_for_port(port):
            raise RuntimeError("stand-in did not start")
        # Start from the parent environment minus anything that belongs to another
        # Claude Code session, real credentials, or another telemetry setup.
        env = {k: v for k, v in os.environ.items()
               if k not in SCRUB and not k.startswith(("OTEL_", "CLAUDE", "ANTHROPIC_"))}
        env.update({
            "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{port}",
            "ANTHROPIC_API_KEY": DUMMY_KEY,
            "CLAUDE_CONFIG_DIR": str(out / "config"),
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            # Export events to the stand-in, which doubles as a local OTLP receiver.
            # (The console exporter produced no output in a non-interactive run.)
            "OTEL_LOGS_EXPORTER": "otlp",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
            "OTEL_EXPORTER_OTLP_ENDPOINT": f"http://127.0.0.1:{port}",
            "OTEL_METRICS_EXPORTER": "none",
            "OTEL_LOGS_EXPORT_INTERVAL": "1000",
            "OTEL_LOG_RAW_API_BODIES": "file:" + str(out / "bodies"),
            "OTEL_LOG_TOOL_DETAILS": "1",
            "CLAUDE_CODE_EFFORT_LEVEL": "high",
            "CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK": "1",
            "CLAUDE_CODE_MAX_RETRIES": "0",
            "DISABLE_AUTOUPDATER": "1",
        })
        env.update(extra_env or {})
        cmd = [str(claude), "-p", "Reply with the single word: ok", "--model", MAIN_MODEL,
               "--output-format", "json", "--max-turns", "2"]
        started = time.time()
        try:
            proc = subprocess.run(cmd, cwd=out / "cwd", env=env, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
            code, stdout, stderr, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as e:
            code, timed_out = None, True
            stdout = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        elapsed = time.time() - started
        (out / "claude-stdout.txt").write_text(stdout, encoding="utf-8")
        (out / "claude-stderr.txt").write_text(stderr, encoding="utf-8")
        (out / "run.json").write_text(json.dumps({
            "scenario": scenario, "label": label, "exit_code": code, "timed_out": timed_out,
            "elapsed_s": round(elapsed, 1), "extra_env": sorted((extra_env or {}).keys()),
        }, indent=1), encoding="utf-8")
        return out
    finally:
        mock.terminate()
        try:
            mock.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mock.kill()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--claude", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--scenario", action="append", choices=SCENARIOS)
    p.add_argument("--no-telemetry", action="store_true",
                   help="also run 'normal' with telemetry switched off, to check a harness failure is detectable")
    args = p.parse_args()
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    for scenario in args.scenario or SCENARIOS:
        out = run_scenario(Path(args.claude), out_root, scenario)
        print("ran", scenario, "->", out)
    if args.no_telemetry:
        out = run_scenario(Path(args.claude), out_root, "normal", label="normal-telemetry-off",
                           extra_env={"CLAUDE_CODE_ENABLE_TELEMETRY": "0", "OTEL_LOG_RAW_API_BODIES": ""})
        print("ran normal-telemetry-off ->", out)


if __name__ == "__main__":
    main()
