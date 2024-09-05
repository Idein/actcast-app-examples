import base64
import copy
import os
import socket
from pathlib import Path
from typing import Optional

from ._private.util.result import ResultTuple
from .schema.agent_app_protocol import RequestId, ServiceKind, ServiceRequest, ServiceResponse, Status


class ServiceClient:
    _socket_path: Path
    _request_id: RequestId

    """Actcast Service Client

    This client handles these commands

    * 'RS256'
        * sign a message with an actcast device specific secret key.

    """

    def __init__(self, socket_path: Optional[Path] = None) -> None:
        if socket_path is None:
            socket_path = Path(os.environ["ACTCAST_SERVICE_SOCK"])

        self._socket_path = socket_path
        self._request_id = RequestId(0)

    def _get_request_id(self) -> RequestId:
        self._request_id = self._request_id.next_()
        return copy.copy(self._request_id)

    def _sendrecv(self, request: ServiceRequest) -> ResultTuple[ServiceResponse, RuntimeError]:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(self._socket_path))

        sock.sendall(request.to_bytes())

        response, err = ServiceResponse.parse(sock)
        if err:
            return None, RuntimeError("couldn't parse a response from actcast agent: `ServiceResponse.parse()` failed")
        if response is None:
            return None, RuntimeError(f"service request failed: request = {request}, response = {response}")
        if response.status != Status.OK:
            return None, RuntimeError(f"service request failed: request = {request}, response = {response}")

        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

        return response, None

    def rs256(self, payload: bytes) -> str:
        """

        Sign a message with an actcast device specific secret key.

        Args:
            payload (bytes): message

        Returns:
            str: signature (base64url encoded)

        Exceptions:
            RuntimeError
        """
        payload = base64.urlsafe_b64encode(payload).rstrip(b"=")
        request = ServiceRequest(
            self._get_request_id(),
            ServiceKind.RS_256,
            payload,
        )
        response, err = self._sendrecv(request)
        if err:
            raise err
        if response is None:
            raise RuntimeError(f"service request failed: request = {request}, response = {response}")
        return response.data.decode()


if __name__ == "__main__":
    import json

    agent_service_client = ServiceClient()
    sign = agent_service_client.rs256(
        json.dumps(
            {
                "foo": 1,
                "bar": True,
                "baz": "Test",
            }
        ).encode("ascii")
    )
    print(sign)
    sign = agent_service_client.rs256(b"test")
    print(sign)
