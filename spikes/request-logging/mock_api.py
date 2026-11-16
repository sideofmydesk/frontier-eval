"""Local stand-in for the Claude Messages API, for stage 0 of the logging spike.

It never contacts Anthropic. It answers POST /v1/messages with a canned
response chosen by --scenario, and writes one JSON line per request it
receives to --log. Credentials in request headers are never written.

Scenarios:
  normal          a plain text reply from the requested model
  model_mismatch  a reply whose `model` differs from the request
  fallback        a reply carrying a `fallback` content block and
                  `usage.iterations`, served by another model
  refusal         stop_reason "refusal" with a stop_details category
  error           HTTP 400 invalid_request_error

Standard library only.
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FALLBACK_MODEL = "claude-opus-4-8"
SECRET_HEADERS = {"authorization", "x-api-key", "cookie", "proxy-authorization"}

_lock = threading.Lock()
_counter = 0


def next_id():
    global _counter
    with _lock:
        _counter += 1
        return _counter


def build_message(scenario, requested_model, n):
    """Return (message dict, stop_reason, stop_details, usage_final)."""
    model = requested_model
    content = [{"type": "text", "text": "ok"}]
    stop_reason = "end_turn"
    stop_details = None
    usage = {
        "input_tokens": 25,
        "output_tokens": 7,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    if scenario == "model_mismatch":
        model = FALLBACK_MODEL
    elif scenario == "fallback":
        model = FALLBACK_MODEL
        content = [
            {
                "type": "fallback",
                "from": {"model": requested_model},
                "to": {"model": FALLBACK_MODEL},
                "trigger": {"type": "refusal", "category": "cyber"},
            },
            {"type": "text", "text": "ok"},
        ]
        usage["iterations"] = [
            {
                "type": "message",
                "model": requested_model,
                "input_tokens": 30,
                "output_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
            {
                "type": "fallback_message",
                "model": FALLBACK_MODEL,
                "input_tokens": 25,
                "output_tokens": 7,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
        ]
    elif scenario == "refusal":
        content = []
        stop_reason = "refusal"
        stop_details = {
            "type": "refusal",
            "category": "cyber",
            "explanation": "Canned refusal from the stage 0 stand-in.",
        }
        usage["output_tokens"] = 0
    message = {
        "id": f"msg_mock_{n:04d}",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "stop_details": stop_details,
        "usage": usage,
    }
    return message


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


def stream_events(message):
    """Yield SSE frames that add up to `message`."""
    start = dict(message)
    start["content"] = []
    start["stop_reason"] = None
    start["stop_details"] = None
    start["usage"] = {
        "input_tokens": message["usage"]["input_tokens"],
        "output_tokens": 1,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    yield sse("message_start", {"type": "message_start", "message": start})
    for i, block in enumerate(message["content"]):
        if block["type"] == "text":
            yield sse(
                "content_block_start",
                {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}},
            )
            yield sse(
                "content_block_delta",
                {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": block["text"]}},
            )
        else:
            yield sse("content_block_start", {"type": "content_block_start", "index": i, "content_block": block})
        yield sse("content_block_stop", {"type": "content_block_stop", "index": i})
    delta = {"stop_reason": message["stop_reason"], "stop_sequence": None}
    if message["stop_details"] is not None:
        delta["stop_details"] = message["stop_details"]
    final_usage = {k: v for k, v in message["usage"].items() if k != "input_tokens"}
    final_usage["input_tokens"] = message["usage"]["input_tokens"]
    yield sse("message_delta", {"type": "message_delta", "delta": delta, "usage": final_usage})
    yield sse("message_stop", {"type": "message_stop"})


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    scenario = "normal"
    main_model = ""
    log_path = ""

    def log_message(self, *args):  # silence default stderr logging
        pass

    def _record(self, entry):
        with _lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def _send_json(self, status, obj, request_id):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("request-id", request_id)
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        n = next_id()
        request_id = f"req_mock_{n:04d}"
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            body = {"_unparsed_bytes": len(raw)}
        headers = {k.lower(): v for k, v in self.headers.items() if k.lower() not in SECRET_HEADERS}
        path = self.path.split("?")[0]

        # OpenTelemetry receiver (OTLP over HTTP, JSON): store what Claude Code exports.
        if self.command == "POST" and path in ("/v1/logs", "/v1/metrics", "/v1/traces"):
            with _lock:
                with open(self.log_path + ".otel.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"signal": path[4:], "content_type": headers.get("content-type"), "body": body}) + "\n")
            return self._send_json(200, {}, request_id)
        entry = {
            "n": n,
            "time": time.time(),
            "request_id": request_id,
            "method": self.command,
            "path": self.path,
            "model": body.get("model"),
            "stream": body.get("stream"),
            "thinking": body.get("thinking"),
            "output_config": body.get("output_config"),
            "has_fallbacks_param": "fallbacks" in body,
            "fallbacks": body.get("fallbacks"),
            "n_messages": len(body.get("messages") or []),
            "n_tools": len(body.get("tools") or []),
            "anthropic_beta": headers.get("anthropic-beta"),
            "anthropic_version": headers.get("anthropic-version"),
            "user_agent": headers.get("user-agent"),
            "header_names": sorted(headers),
            "body_keys": sorted(body) if isinstance(body, dict) else None,
        }

        if self.command == "POST" and path == "/v1/messages/count_tokens":
            entry["served"] = "count_tokens"
            self._record(entry)
            return self._send_json(200, {"input_tokens": 25}, request_id)

        if self.command == "POST" and path == "/v1/messages":
            requested = body.get("model") or "unknown"
            # Only requests for the model under test get the scenario.
            scenario = self.scenario if requested == self.main_model else "normal"
            entry["served"] = scenario
            if scenario == "error":
                self._record(entry)
                return self._send_json(
                    400,
                    {"type": "error", "error": {"type": "invalid_request_error", "message": "Canned error from the stage 0 stand-in."}},
                    request_id,
                )
            message = build_message(scenario, requested, n)
            entry["returned_model"] = message["model"]
            self._record(entry)
            if body.get("stream"):
                self.send_response(200)
                self.send_header("content-type", "text/event-stream")
                self.send_header("cache-control", "no-cache")
                self.send_header("connection", "close")
                self.send_header("request-id", request_id)
                self.end_headers()
                for frame in stream_events(message):
                    self.wfile.write(frame)
                    self.wfile.flush()
                self.close_connection = True
                return
            return self._send_json(200, message, request_id)

        entry["served"] = "not_found"
        self._record(entry)
        self._send_json(404, {"type": "error", "error": {"type": "not_found_error", "message": "stand-in: no such endpoint"}}, request_id)

    do_GET = do_POST = do_HEAD = do_PUT = do_DELETE = _handle


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--scenario", default="normal", choices=["normal", "model_mismatch", "fallback", "refusal", "error"])
    p.add_argument("--main-model", required=True, help="requests for this model get the scenario; others get a normal reply")
    p.add_argument("--log", required=True)
    args = p.parse_args()
    Handler.scenario = args.scenario
    Handler.main_model = args.main_model
    Handler.log_path = args.log
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"stand-in listening on 127.0.0.1:{args.port} scenario={args.scenario}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
