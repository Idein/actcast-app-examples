import base64
import copy
import os
import socket
from pathlib import Path
from typing import Optional

import OpenSSL.crypto

from ..compat.queue import SimpleQueue
from ..schema.agent_app_protocol import ServiceRequest, ServiceResponse, Status
from ..util.result import ResultTuple
from ..util.thread import LoopThread


class AgentAppProtocolServiceServer:
    _path: Path
    _pkey: OpenSSL.crypto.PKey
    _thread: LoopThread
    _listener: Optional[socket.socket]

    def __init__(self, path: Path, pkey: OpenSSL.crypto.PKey) -> None:
        self._path = path
        self._pkey = pkey
        dummy_ch: SimpleQueue = SimpleQueue()
        self._thread = LoopThread(dummy_ch, self._loop_body)
        self._listener = None

    def path(self) -> Path:
        return self._path

    def startup(self) -> None:
        try:
            os.unlink(self._path)
        except FileNotFoundError:
            pass
        self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener.bind(str(self._path))
        self._path.chmod(0o664)
        self._listener.settimeout(1)
        self._listener.listen(1)

        self._thread.startup()

    def teardown(self) -> None:
        self._thread.teardown()

    def join(self) -> None:
        self._thread.join()

    def _loop_body(self) -> None:
        assert self._listener is not None

        try:
            stream, _ = self._listener.accept()
        except socket.timeout:
            return

        request, err = ServiceRequest.parse(stream)

        if request is None:
            raise RuntimeError("couldn't parse a request from actcast agent: `ServiceRequest.parse()` failed")

        if err is not None:
            response = ServiceResponse(
                copy.copy(request.id_),
                Status.GENERAL_ERROR,
                b"",
            )
            stream.sendall(response.to_bytes())
            return

        # Currently, only RS_256 is supported.
        response = self._handle_rs_256(request)

        stream.sendall(response.to_bytes())

    def _handle_rs_256(self, request: ServiceRequest) -> ServiceResponse:
        bs, err = _base64_decode_url_safe_no_pad(request.data)
        if (err is not None) or (bs is None):
            return ServiceResponse(
                copy.copy(request.id_),
                Status.GENERAL_ERROR,
                b"",
            )

        bs = OpenSSL.crypto.sign(self._pkey, bs, "sha256")
        bs = _base64_encode_url_safe_no_pad(bs)
        return ServiceResponse(
            copy.copy(request.id_),
            Status.OK,
            bs,
        )


def _base64_decode_url_safe_no_pad(data: bytes) -> ResultTuple[bytes, bool]:
    """
    Decode with config `base64::URL_SAFE_NO_PAD`.
    c.f. https://docs.rs/base64/0.13.0/base64/constant.URL_SAFE_NO_PAD.html
    """
    missing_pad_len = -(len(data) % -4)
    data_ = data + b"=" * missing_pad_len
    try:
        return base64.urlsafe_b64decode(data_), None
    except Exception:
        return None, True


def _base64_encode_url_safe_no_pad(data: bytes) -> bytes:
    """
    Encode with config `base64::URL_SAFE_NO_PAD`.
    c.f. https://docs.rs/base64/0.13.0/base64/constant.URL_SAFE_NO_PAD.html
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=")
