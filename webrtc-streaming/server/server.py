#!/usr/bin/env python3
"""Server-side sample for the WebRTC streaming example.

A browser cannot call the Actcast API directly (requests that
carry an Origin header are rejected), so this small server sits
in between and relays the signaling:

  browser --HTTP--> this server --Actcast API--> device app
                      Custom Command: offer / answer / status / reset

It serves viewer.html at / and exposes:

  POST /api/offer   -> device {"op": "offer"}   -> {"sdp": ...}
  POST /api/answer  <- {"sdp": ...} -> device {"op": "answer", ...}
  POST /api/reset   -> device {"op": "reset"}
  GET  /api/status  -> device {"op": "status"}

Configuration is by environment variables:

  ACTCAST_API_TOKEN   group API token (required)
  ACTCAST_GROUP_ID    group id of the device (required)
  ACTCAST_DEVICE_ID   device id (UUID) of the device (required)
  ACTCAST_API_BASE    default https://api.actcast.io
                      (development: https://api.dev.actcast.io)
  HOST                listen address, default 127.0.0.1
  PORT                listen port, default 8080

Python standard library only; no pip packages are needed.
The token stays on this server and is never sent to the browser.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_BASE = os.environ.get("ACTCAST_API_BASE", "https://api.actcast.io")
GROUP_ID = os.environ.get("ACTCAST_GROUP_ID", "")
DEVICE_ID = os.environ.get("ACTCAST_DEVICE_ID", "")
TOKEN = os.environ.get("ACTCAST_API_TOKEN", "")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))

HERE = os.path.dirname(os.path.abspath(__file__))
COMMAND_TIMEOUT = 150  # seconds; the platform drops results after 5 min


class ApiError(Exception):
    pass


def api_request(method, path, body=None):
    req = urllib.request.Request(API_BASE + path, method=method)
    req.add_header("Authorization", "token " + TOKEN)
    data = None
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise ApiError(
            "Actcast API %s %s -> HTTP %d" % (method, path, e.code)
        )
    except Exception as e:
        raise ApiError("Actcast API %s %s failed: %r" % (method, path, e))


def send_command(payload, timeout=COMMAND_TIMEOUT):
    """Issue one Custom Command and wait for the app's reply.

    The request body IS the command object: the platform delivers
    the whole body verbatim to the app as the command payload.
    """
    base = "/v0/groups/%s/devices/%s" % (GROUP_ID, DEVICE_ID)
    job = api_request("POST", base + "/jobs/custom_command", payload)
    job_id = job.get("id")
    if not job_id:
        raise ApiError("no job id in response: %r" % (job,))
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(1)
        res = api_request("GET", base + "/custom_command/%s" % job_id)
        status = res.get("status")
        if status == "processing":
            continue
        if status != "finished":
            raise ApiError("command %s ended with status %r"
                           % (payload.get("op"), status))
        return json.loads(res.get("data") or "{}")
    raise ApiError("command %s timed out" % payload.get("op"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[srv] " + (fmt % args), flush=True)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _command(self, payload):
        try:
            self._json(200, send_command(payload))
        except ApiError as e:
            self._json(502, {"error": str(e)})

    def do_GET(self):
        if self.path == "/":
            try:
                with open(os.path.join(HERE, "viewer.html"), "rb") as f:
                    body = f.read()
            except OSError:
                self._json(500, {"error": "viewer.html not found"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            self._command({"op": "status"})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/offer":
            self._command({"op": "offer"})
        elif self.path == "/api/reset":
            self._command({"op": "reset"})
        elif self.path == "/api/answer":
            length = int(self.headers.get("Content-Length", "0"))
            try:
                req = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                self._json(400, {"error": "request body is not JSON"})
                return
            sdp = req.get("sdp")
            if not sdp:
                self._json(400, {"error": "missing sdp"})
                return
            self._command({"op": "answer", "sdp": sdp})
        else:
            self._json(404, {"error": "not found"})


def main():
    missing = [name for name, value in (
        ("ACTCAST_API_TOKEN", TOKEN),
        ("ACTCAST_GROUP_ID", GROUP_ID),
        ("ACTCAST_DEVICE_ID", DEVICE_ID),
    ) if not value]
    if missing:
        print("missing environment variables: %s" % ", ".join(missing),
              file=sys.stderr)
        sys.exit(1)
    print("serving viewer on http://%s:%d/ (device %s in group %s via %s)"
          % (HOST, PORT, DEVICE_ID, GROUP_ID, API_BASE), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
