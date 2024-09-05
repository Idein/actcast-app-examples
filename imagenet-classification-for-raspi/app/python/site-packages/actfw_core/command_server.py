import base64
import copy
import io
import os
import socket
from threading import Lock
from typing import Optional

from PIL.Image import Image as PIL_Image

from .schema.agent_app_protocol import CommandRequest, CommandResponse, Status
from .task import Isolated


class CommandServer(Isolated):
    sock_path: Optional[str]
    img_lock: Lock
    img: Optional[PIL_Image]

    """Actcast Command Server

    This server handles these commands

    * 'Take Photo'
        * responses cached image as png data

    """

    def __init__(self, sock_path: Optional[str] = None) -> None:
        super().__init__()
        self.sock_path = None
        env = "ACTCAST_COMMAND_SOCK"
        if env in os.environ:
            self.sock_path = os.environ[env]
        if sock_path is not None:
            self.sock_path = sock_path
        self.running = True
        self.img_lock = Lock()
        self.img = None

    def run(self) -> None:
        """Run and start the activity"""
        if self.sock_path is None:
            return
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            os.unlink(self.sock_path)
        except FileNotFoundError:
            pass  # ignore
        s.bind(self.sock_path)
        s.settimeout(1)
        s.listen(1)
        while self.running:
            # Wait photo
            while self.running:
                with self.img_lock:
                    if self.img is None:
                        continue
                    else:
                        break
            try:
                if self.img is None:
                    # this server may be terminating
                    # re-check self.running
                    continue  # type: ignore[unreachable]

                conn, _ = s.accept()
                request, err = CommandRequest.parse(conn)

                if request is None:
                    raise RuntimeError("couldn't parse a request from actcast agent: `CommandRequest.parse()` failed")

                if err:
                    response = CommandResponse(
                        copy.copy(request.id_),
                        Status.GENERAL_ERROR,
                        b"",
                    )
                    conn.sendall(response.to_bytes())
                    continue

                # Currently, only 'Take Photo' command is supported.
                header = b"data:image/png;base64,"
                with self.img_lock:
                    pngimg = io.BytesIO()
                    self.img.save(pngimg, format="PNG")
                    b64img = base64.b64encode(pngimg.getbuffer())
                data = header + b64img
                response = CommandResponse(copy.copy(request.id_), Status.OK, data)

                conn.sendall(response.to_bytes())
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except socket.timeout:
                pass
        os.remove(self.sock_path)

    def update_image(self, image: PIL_Image) -> None:
        """

        Update the cached 'Take Photo' command image.

        Args:
            image (:class:`~PIL.Image`): image

        """
        with self.img_lock:
            self.img = image.copy()
