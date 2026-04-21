#!/usr/bin/env python3
import http.server
import json
import sys

import actfw_core
from actfw_core.application import Application
from actfw_core.task import Isolated

PORT = 8080

def debug_log(msg, *args, **kwargs):
    kwargs["flush"] = True
    kwargs["file"] = sys.stderr
    print(f"debug_log| {msg}", *args, **kwargs)

class SampleHttpRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        debug_log(f"req from {self.client_address}")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = json.dumps({"message": "Hello, World!"})

        self.wfile.write(response.encode())

class Server(Isolated):
    def __init__(self):
        super().__init__()
        self.httpd = http.server.HTTPServer(('', PORT), SampleHttpRequestHandler)

    def run(self):
        debug_log(f"server started in {PORT}")
        self.httpd.serve_forever()

    def stop(self):
        super().stop()
        self.httpd.shutdown()


def main() -> None:
    debug_log("app init")
    app = actfw_core.Application()

    server = Server()
    app.register_task(server)

    app.run()


if __name__ == "__main__":
    main()
