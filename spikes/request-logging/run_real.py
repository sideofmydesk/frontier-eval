"""Stage 1 of the logging spike: one real, billed Claude Code session.

THIS MAKES PAID API CALLS. It reads the API key from a file outside the
repository and never prints or stores it. Each session is capped with
Claude Code's own --max-budget-usd.

Telemetry is exported to a local receiver (mock_api.py, used here only as an
OpenTelemetry receiver; ANTHROPIC_BASE_URL is NOT set, so inference goes to
Anthropic directly). Raw request and response bodies are written to files.

Usage:
  python run_real.py --claude <binary> --env-file <.env> --out <fresh dir>
      --cwd <working dir> --model <id> --budget <usd> --prompt <text>
      [--plugin-dir <dir>] [--allowed-tools <rule> ...] [--effort high]
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_key(env_file):
    for line in Path(env_file).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("ANTHROPIC_API_KEY not found in env file")


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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--claude", required=True)
    p.add_argument("--env-file", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--cwd", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--budget", type=float, required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--plugin-dir")
    p.add_argument("--allowed-tools", action="append", default=[])
    p.add_argument("--effort", default="high")
    p.add_argument("--prepend-path", action="append", default=[],
                   help="directory to put at the front of PATH for the session, e.g. where gh lives")
    p.add_argument("--timeout", type=int, default=1800)
    args = p.parse_args()

    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} already exists; pass a fresh --out directory")
    (out / "bodies").mkdir(parents=True)
    (out / "config").mkdir()

    port = free_port()
    receiver_log = out / "receiver.jsonl"
    receiver = subprocess.Popen(
        [sys.executable, "-I", str(HERE / "mock_api.py"), "--port", str(port), "--scenario", "normal",
         "--main-model", "unused", "--log", str(receiver_log)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_for_port(port):
            raise SystemExit("telemetry receiver did not start")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("OTEL_", "CLAUDE", "ANTHROPIC_"))}
        settings = {
            "CLAUDE_CONFIG_DIR": str(out / "config"),
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            "OTEL_LOGS_EXPORTER": "otlp",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
            "OTEL_EXPORTER_OTLP_ENDPOINT": f"http://127.0.0.1:{port}",
            "OTEL_METRICS_EXPORTER": "none",
            "OTEL_LOGS_EXPORT_INTERVAL": "1000",
            "OTEL_LOG_RAW_API_BODIES": "file:" + str(out / "bodies"),
            "OTEL_LOG_TOOL_DETAILS": "1",
            "CLAUDE_CODE_EFFORT_LEVEL": args.effort,
            "CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK": "1",
            "DISABLE_AUTOUPDATER": "1",
        }
        env.update(settings)
        if args.prepend_path:
            path_key = next((k for k in env if k.upper() == "PATH"), "PATH")
            env[path_key] = os.pathsep.join(args.prepend_path) + os.pathsep + env.get(path_key, "")
        env["ANTHROPIC_API_KEY"] = read_key(args.env_file)

        cmd = [args.claude, "-p", args.prompt, "--model", args.model,
               "--output-format", "stream-json", "--verbose",
               "--max-budget-usd", str(args.budget)]
        if args.plugin_dir:
            cmd += ["--plugin-dir", args.plugin_dir]
        if args.allowed_tools:
            cmd += ["--allowedTools", *args.allowed_tools]

        manifest = {
            "model": args.model, "effort": args.effort, "budget_usd": args.budget,
            "prompt": args.prompt, "plugin_dir": args.plugin_dir, "allowed_tools": args.allowed_tools,
            "cwd": args.cwd, "claude": args.claude, "settings": settings,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        started = time.time()
        with open(out / "stream.jsonl", "w", encoding="utf-8") as so, open(out / "stderr.txt", "w", encoding="utf-8") as se:
            try:
                proc = subprocess.run(cmd, cwd=args.cwd, env=env, stdout=so, stderr=se,
                                      stdin=subprocess.DEVNULL, timeout=args.timeout)
                manifest["exit_code"], manifest["timed_out"] = proc.returncode, False
            except subprocess.TimeoutExpired:
                manifest["exit_code"], manifest["timed_out"] = None, True
        manifest["elapsed_s"] = round(time.time() - started, 1)
        (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        time.sleep(2)  # let the receiver finish writing
        print(json.dumps({"out": str(out), "exit_code": manifest["exit_code"], "elapsed_s": manifest["elapsed_s"]}))
    finally:
        receiver.terminate()
        try:
            receiver.wait(timeout=5)
        except subprocess.TimeoutExpired:
            receiver.kill()


if __name__ == "__main__":
    main()
