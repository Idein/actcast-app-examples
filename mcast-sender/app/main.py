import actfw_core
from actfw_core.task import Producer, Consumer
import socket
from typing import Generic, TypeVar
import sys
import os
import struct
import time

T = TypeVar("T")


class SendData(Generic[T]):
    value: T

    def __init__(self, value: T) -> None:
        self.value = value

    def getvalue(self) -> T:
        return self.value


class Sender(Producer[SendData[bytes]]):
    def __init__(self, multicast_group, multicast_port):
        super(Sender, self).__init__()
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.multicast_message = b"Hello, Multicast World!"
        debug_log(f"Multicast address: {multicast_group}:{multicast_port}")
        debug_log(f"ACTCAST_SOCKS_SERVER: {os.environ.get('ACTCAST_SOCKS_SERVER')}")
        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Set the time-to-live (TTL) for messages to 1 so they do not go past the local network segment
        ttl = struct.pack("b", 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        debug_log("Socket is ready")

    def run(self):
        debug_log("Socket send start")
        while True:
            try:
                # Send data to the multicast group
                debug_log(
                    f"Sending message: {self.multicast_message.decode()} to {self.multicast_group}:{self.multicast_port}"
                )
                self.sock.sendto(
                    self.multicast_message, (self.multicast_group, self.multicast_port)
                )
            finally:
                time.sleep(3)
            if not self._is_running():
                break
        self.sock.close()
        debug_log("Socket send close")


class Presenter(Consumer):
    def __init__(self):
        super(Presenter, self).__init__()

    def proc(self, data: dict):
        # 後続の処理
        actfw_core.heartbeat()


def run(app, settings: dict):
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)

    send = Sender(settings["multicast_group"], int(settings["multicast_port"]))
    app.register_task(send)

    pres = Presenter()
    app.register_task(pres)

    send.connect(pres)

    app.run()


def main():
    app = actfw_core.Application()

    # Load act setting
    settings = app.get_settings(
        {"multicast_group": "239.255.0.1", "multicast_port": 30001}
    )
    debug_log(f"settings: {settings}")
    run(app, settings)


def debug_log(str):
    print(str, file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
