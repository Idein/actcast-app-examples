import actfw_core
from actfw_core.task import Producer, Consumer
import socket
from typing import Generic, TypeVar
import sys
import os

T = TypeVar("T")


class RecvData(Generic[T]):
    value: T

    def __init__(self, value: T) -> None:
        self.value = value

    def getvalue(self) -> T:
        return self.value


class Receiver(Producer[RecvData[bytes]]):
    def __init__(self, multicast_group, multicast_port):
        super(Receiver, self).__init__()
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        debug_log(f"Multicast address: {multicast_group}:{multicast_port}")
        debug_log(f"ACTCAST_SOCKS_SERVER: {os.environ.get('ACTCAST_SOCKS_SERVER')}")
        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", multicast_port))
        self.sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(multicast_group) + socket.inet_aton("0.0.0.0"),
        )
        debug_log("Socket is ready")

    def run(self):
        debug_log("Socket recv start")
        while True:
            debug_log("Socket recv loop")
            data = self.sock.recv(10240).decode("utf-8")
            debug_log(f"Socket received: {data}")
            outlet_data = [{"data": data}]
            actfw_core.notify(outlet_data)
            self._outlet(outlet_data)
            if not self._is_running():
                break
        self.sock.close()
        debug_log("Socket recv close")


class Presenter(Consumer):
    def __init__(self):
        super(Presenter, self).__init__()

    def proc(self, data: dict):
        # 後続の処理
        actfw_core.heartbeat()


def run(app, settings: dict):
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)

    recv = Receiver(settings["multicast_group"], int(settings["multicast_port"]))
    app.register_task(recv)

    pres = Presenter()
    app.register_task(pres)

    recv.connect(pres)

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
