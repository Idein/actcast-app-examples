#!/usr/bin/env python3
import os
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
        debug_log(f"response: {res}")
        if res.status == 200:
            act_log("allowed", url, "expected")
        else:
            act_log("allowed", url, "unexpected")
    except e:
        debug_log(f"req error: {e}")
        act_log("allowed", url, "unexpected")

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
        if res.status == 200:
            act_log("denied", url, "unexpected")
        else:
            # TODO: ちゃんと確認する
            act_log("denied", url, "expected")
    except e:
        debug_log(f"req error: {e}")
        act_log("denied", url, "expected")

class ReqChecker(Isolated):
    def __init__(self):
        super().__init__()

        self.count = 1

    def run(self):
        debug_log("req checker started")

        while self.running:
            debug_log(f"req check {n} -------------")
            actfw_core.heartbeat()

            req_by_allowed_domain("https://actcast.io")
            req_by_denied_domain("https://idein.jp")

            self.count += 1
            time.sleep(5)

        debug_log("req checker finished")


def main() -> None:
    debug_log("app init")
    app = actfw_core.Application()

    checker = ReqChecker()
    app.register_task(checker)

    app.run()


if __name__ == "__main__":
    main()
