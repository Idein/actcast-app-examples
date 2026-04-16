#!/usr/bin/env python3
import os
import re
import socks
import sys
import time

import requests

import actfw_core
from actfw_core.application import Application
from actfw_core.task import Isolated


def debug_log(msg, *args, **kwargs):
    kwargs["flush"] = True
    kwargs["file"] = sys.stderr
    print(f"debug_log| {msg}", *args, **kwargs)

def act_log(kind, url, result):
    actfw_core.notify([{"kind": kind, "url": url, "result": result}])

def req_by_allowed_domain(url):
    debug_log(f"req_by_allowed_domain: {url}")
    try:
        res = requests.get(
            url,
            proxies={
                'https': f'socks5h://{os.environ["ACTCAST_SOCKS_SERVER"]}'
            }
        )
        if res.status_code == requests.codes.ok:
            act_log("allowed", url, "expected")
        else:
            debug_log(f"response: {res}")
            act_log("allowed", url, "unexpected")
    except Exception as e:
        debug_log(f"req error: {e}")
        act_log("allowed", url, "unexpected")

def req_by_allowed_ip(url):
    debug_log(f"req_by_allowed_ip: {url}")
    try:
        res = requests.get(
            url,
            proxies={
                'http': f'socks5://{os.environ["ACTCAST_SOCKS_SERVER"]}'
            }
        )
        if res.status_code == requests.codes.ok:
            act_log("allowed", url, "expected")
        else:
            debug_log(f"response: {res}")
            act_log("allowed", url, "unexpected")
    except Exception as e:
        debug_log(f"req error: {e}")
        act_log("allowed", url, "unexpected")

def extract_socks5_reply_code(exc: BaseException) -> int | None:
    visited = set()
    pattern = re.compile(r"0x([0-9a-fA-F]{2})")

    def walk(obj) -> int | None:
        if obj is None:
            return None

        oid = id(obj)
        if oid in visited:
            return None
        visited.add(oid)

        if isinstance(obj, str):
            m = pattern.search(obj)
            if m:
                return int(m.group(1), 16)
            return None

        if isinstance(obj, socks.SOCKS5Error):
            m = pattern.search(str(obj))
            if m:
                return int(m.group(1), 16)
            return None

        if isinstance(obj, BaseException):
            for arg in obj.args:
                code = walk(arg)
                if code is not None:
                    return code

            for attr in ("__cause__", "__context__"):
                code = walk(getattr(obj, attr, None))
                if code is not None:
                    return code

            return None

        if isinstance(obj, (tuple, list)):
            for item in obj:
                code = walk(item)
                if code is not None:
                    return code
            return None

        return None

    return walk(exc)

def req_by_denied_domain(url):
    debug_log(f"req_by_denied_domain: {url}")
    try:
        res = requests.get(
            url,
            proxies={
                'https': f'socks5h://{os.environ["ACTCAST_SOCKS_SERVER"]}'
            }
        )
        debug_log(f"response: {res}")
        act_log("denied", url, "unexpected")
    except Exception as e:
        code = extract_socks5_reply_code(e)
        if code == 0x02:
            act_log("denied", url, "expected")
        else:
            debug_log(f"req error: {e}")
            act_log("denied", url, "unexpected")

def req_by_denied_ip(url):
    debug_log(f"req_by_denied_ip: {url}")
    try:
        res = requests.get(
            url,
            proxies={
                'http': f'socks5://{os.environ["ACTCAST_SOCKS_SERVER"]}'
            }
        )
        debug_log(f"response: {res}")
        act_log("denied", url, "unexpected")
    except Exception as e:
        code = extract_socks5_reply_code(e)
        if code == 0x02:
            act_log("denied", url, "expected")
        else:
            debug_log(f"req error: {e}")
            act_log("denied", url, "unexpected")

class ReqChecker(Isolated):
    def __init__(self, local_server_ip):
        super().__init__()

        self.local_server_ip = local_server_ip
        self.count = 1

    def run(self):
        debug_log("req checker started")

        while self.running:
            debug_log(f"req check {self.count} -------------")
            actfw_core.heartbeat()

            req_by_allowed_domain("https://actcast.io")
            time.sleep(0.5)
            req_by_denied_domain("https://idein.jp")
            time.sleep(0.5)
            req_by_allowed_ip(f"http://{self.local_server_ip}:3000")
            time.sleep(0.5)
            req_by_allowed_ip(f"http://{self.local_server_ip}:8000")
            time.sleep(0.5)
            req_by_denied_ip(f"http://{self.local_server_ip}:9000")

            self.count += 1
            time.sleep(3)

        debug_log("req checker finished")


def main() -> None:
    debug_log("app init")
    app = actfw_core.Application()

    settings = app.get_settings({'local_server_ip': "172.17.0.1"})
    debug_log(f"settings: {settings}")
    checker = ReqChecker(settings["local_server_ip"])
    app.register_task(checker)

    app.run()


if __name__ == "__main__":
    main()
