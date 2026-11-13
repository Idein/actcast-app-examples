#!/usr/bin/env python3
"""Actcast agent command-socket bridge (raw protocol implementation).

Implements the documented application/agent protocol directly instead
of relying on actfw-core >= 2.17 (public PyPI tops out at 2.14.0):

  socket path: env ACTCAST_COMMAND_SOCK (unix stream, one request per
  connection)
  request:  "<id> <kind> <len> <data>"
  response: "<id> <status> <len> <data>"
  kinds:    0 = Take Photo (we answer Unimplemented)
            1 = Check Custom Command Availability (OK, empty)
            2 = Custom Command (data is JSON {"id": uuid, "payload": str},
                response data is the handler's return string)
  unknown kinds: close without responding, per spec.

The handler may be invoked multiple times for the same request and
concurrently; responses are cached by the agent-provided UUID so a
retry returns the same result without re-running the handler.
"""

import json
import os
import socket
import threading

STATUS_OK = 0
STATUS_UNIMPLEMENTED = 2
STATUS_APP_ERROR = 4
STATUS_GENERAL_ERROR = 5

KIND_TAKE_PHOTO = 0
KIND_CHECK_CUSTOM = 1
KIND_CUSTOM_COMMAND = 2


def log(msg):
    print("[bridge] %s" % msg, flush=True)


def _read_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise EOFError("connection closed")
        buf += chunk
    return buf


def _read_header(conn):
    # Header is three space-separated ints terminated by a space
    # after the length field: "<id> <kind> <len> ".
    buf = b""
    while buf.count(b" ") < 3:
        chunk = conn.recv(1)
        if not chunk:
            raise EOFError("connection closed in header")
        buf += chunk
    parts = buf.decode().split(" ")
    return int(parts[0]), int(parts[1]), int(parts[2])


class CommandBridge:
    """handler: callable(payload_str) -> response_str"""

    def __init__(self, handler, sock_path=None):
        self.handler = handler
        self.sock_path = sock_path or os.environ.get("ACTCAST_COMMAND_SOCK")
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        if not self.sock_path:
            log("ACTCAST_COMMAND_SOCK not set; bridge disabled")
            return False
        self.running = True
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        log("listening on %s" % self.sock_path)
        return True

    def stop(self):
        self.running = False

    def _serve(self):
        try:
            os.unlink(self.sock_path)
        except FileNotFoundError:
            pass
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(self.sock_path)
        srv.listen(8)
        srv.settimeout(1.0)
        while self.running:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(target=self._handle, args=(conn,))
            t.daemon = True
            t.start()
        srv.close()

    def _handle(self, conn):
        try:
            req_id, kind, length = _read_header(conn)
            data = _read_exact(conn, length) if length > 0 else b""
            if kind == KIND_TAKE_PHOTO:
                self._respond(conn, req_id, STATUS_UNIMPLEMENTED, b"")
            elif kind == KIND_CHECK_CUSTOM:
                self._respond(conn, req_id, STATUS_OK, b"")
            elif kind == KIND_CUSTOM_COMMAND:
                status, out = self._custom(data)
                self._respond(conn, req_id, status, out)
            else:
                # Unknown kind: close without responding (per spec).
                pass
        except Exception as e:
            log("handle error: %r" % (e,))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _custom(self, data):
        try:
            req = json.loads(data.decode())
            uuid = req.get("id", "")
            payload = req.get("payload", "")
        except Exception as e:
            return STATUS_GENERAL_ERROR, ("bad request: %r" % (e,)).encode()
        with self.cache_lock:
            if uuid and uuid in self.cache:
                return self.cache[uuid]
        try:
            result = self.handler(payload)
            out = (STATUS_OK, result.encode())
        except Exception as e:
            log("handler error: %r" % (e,))
            out = (STATUS_APP_ERROR, ("handler error: %r" % (e,)).encode())
        with self.cache_lock:
            if uuid:
                self.cache[uuid] = out
                if len(self.cache) > 64:
                    self.cache.pop(next(iter(self.cache)))
        return out

    @staticmethod
    def _respond(conn, req_id, status, data):
        header = ("%d %d %d " % (req_id, status, len(data))).encode()
        conn.sendall(header + data)
