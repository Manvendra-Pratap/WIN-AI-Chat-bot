"""Throwaway OpenAI-compatible mock used only for local end-to-end verification
(no real LLM credentials in this environment). Not part of the shipped app.
"""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        messages = body.get("messages", [])
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        reply = f"Mock reply to: {last_user}"
        prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
        completion_tokens = len(reply.split())
        response = {
            "id": "chatcmpl-fake",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", "fake-model"),
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9009
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"fake LLM server listening on {port}")
    server.serve_forever()
