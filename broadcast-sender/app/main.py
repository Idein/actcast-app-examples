import socket
import sys
import time
from typing import Generic, TypeVar
from actfw_core.task import Producer
import actfw_core


T = TypeVar("T")


class SendData(Generic[T]):
    value: T

    def __init__(self, value: T) -> None:
        self.value = value

    def getvalue(self) -> T:
        return self.value


class Sender(Producer[SendData[bytes]]):
    def __init__(self):
        super().__init__()
        # Create UDP socket
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Enable address reuse
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock = sock

    def proc(self):
        while True:
            # ブロードキャストでデータを送信
            message = b"Hello, broadcast world!"
            self.sock.sendto(message, ('255.255.255.255', 5000))
            print(f"Sent broadcast message: {message}")
            time.sleep(1)


def debug_log(str):
    print(str, file=sys.stderr, flush=True)


def main():
    app = actfw_core.Application()
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)
    sender = BroadcastSender()
    app.register_task(sender)
    app.run()


if __name__ == "__main__":
    main()
