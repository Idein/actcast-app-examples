import socket
import sys
from typing import Generic, TypeVar
import actfw_core
from actfw_core.task import Producer


T = TypeVar("T")


class RecvData(Generic[T]):
    value: T

    def __init__(self, value: T) -> None:
        self.value = value

    def getvalue(self) -> T:
        return self.value


class Receiver(Producer[RecvData[bytes]]):
    def __init__(self):
        super().__init__()
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Enable address reuse
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to all interfaces
        sock.bind(("", 5000))
        self.sock = sock

    def run(self):
        # Set socket timeout to allow checking is_running periodically
        self.sock.settimeout(1.0)

        while self._is_running():
            try:
                data, addr = self.sock.recvfrom(1024)
                # Create RecvData object with the received data
                recv_data = [{"data": data.decode("utf-8")}]
                # Send data to next stage in pipeline
                debug_log(f"Socket received: {recv_data}, addr: {addr}")
                actfw_core.notify(recv_data)
            except socket.timeout:
                continue  # Check is_running condition
            except Exception as e:
                print(f"Error receiving broadcast: {e}")
                break

        # Cleanup
        self.sock.close()


def debug_log(str):
    print(str, file=sys.stderr, flush=True)


def main():
    app = actfw_core.Application()
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)
    receiver = Receiver()
    app.register_task(receiver)
    app.run()


if __name__ == "__main__":
    main()
