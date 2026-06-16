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

def act_log(url, result, details):
    actfw_core.notify([{"01_url": url, "02_result": result, "03_details": details}])

def req(url):
    debug_log(f"req: {url}")
    try:
        res = requests.get(
            url,
            timeout=5,
            allow_redirects=False,
            proxies={
                'http': f'socks5h://{os.environ["ACTCAST_SOCKS_SERVER"]}',
                'https': f'socks5h://{os.environ["ACTCAST_SOCKS_SERVER"]}'
            }
        )
        act_log(url, "OK", f'{res.status_code}')
    except Exception as e:
        act_log(url, "Err", f"{e}")

def req_without_proxy(url):
    debug_log(f"req_without_proxy: {url}")
    try:
        res = requests.get(
            url,
            timeout=5,
            allow_redirects=False,
        )
        act_log(url, "OK", f'{res.status_code}')
    except Exception as e:
        act_log(url, "Err", f"{e}")



class ReqChecker(Isolated):
    def __init__(self, target_urls, check_without_proxy):
        super().__init__()

        self.target_urls = target_urls
        self.check_without_proxy = check_without_proxy
        self.count = 1

    def run(self):
        debug_log("req checker started")

        while self.running:
            debug_log(f"req check {self.count} -------------")
            actfw_core.heartbeat()

            for url in self.target_urls:
                req(url)
                time.sleep(0.1)

            if self.check_without_proxy:
                for url in self.target_urls:
                    req_without_proxy(url)
                    time.sleep(0.1)

            self.count += 1
            time.sleep(1)

        debug_log("req checker finished")


def main() -> None:
    debug_log("app init")
    app = actfw_core.Application()

    settings = app.get_settings({})
    debug_log(f"settings: {settings}")
    target_urls = settings["target_urls"].split(",")
    checker = ReqChecker(target_urls, settings["check_without_proxy"])

    app.register_task(checker)

    app.run()


if __name__ == "__main__":
    main()
