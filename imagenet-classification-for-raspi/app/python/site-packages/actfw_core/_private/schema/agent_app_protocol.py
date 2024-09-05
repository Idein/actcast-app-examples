import enum
import io
import socket
from dataclasses import dataclass

from ..util.result import ResultTuple


def _read_int(stream: socket.socket) -> int:
    bs = b""
    while True:
        b = stream.recv(1)
        if b == b" ":
            return int(bs)
        else:
            bs += b


def _read_bytes(stream: socket.socket, n: int) -> bytes:
    bs = io.BytesIO()
    while n > 0:
        n -= bs.write(stream.recv(min(n, 1024)))
    return bs.getvalue()


@dataclass(frozen=True, eq=True)
class RequestId:
    _id: int

    def next_(self) -> "RequestId":
        return RequestId(self._id + 1)


class CommandKind(enum.Enum):
    TAKE_PHOTO = 0


class Status(enum.Enum):
    OK = 0
    BUSY = 1
    UNIMPLEMENTED = 2
    DEVICE_ERROR = 3
    APP_ERROR = 4
    GENERAL_ERROR = 5


@dataclass(frozen=True, eq=False)
class CommandRequest:
    id_: RequestId
    kind: CommandKind
    data: bytes

    @classmethod
    def parse(cls, stream: socket.socket) -> ResultTuple["CommandRequest", Exception]:
        try:
            id_ = RequestId(_read_int(stream))
            kind = CommandKind(_read_int(stream))
            data_length = _read_int(stream)
            data = _read_bytes(stream, data_length)
            return cls(id_, kind, data), None
        except Exception as e:
            return None, e

    def to_bytes(self) -> bytes:
        id_ = self.id_._id
        kind = self.kind.value
        data = self.data
        return f"{id_} {kind} {len(data)} ".encode() + data


@dataclass(frozen=True, eq=False)
class CommandResponse:
    id_: RequestId
    status: Status
    data: bytes

    @classmethod
    def parse(cls, stream: socket.socket) -> ResultTuple["CommandResponse", Exception]:
        try:
            id_ = RequestId(_read_int(stream))
            status = Status(_read_int(stream))
            data_length = _read_int(stream)
            data = _read_bytes(stream, data_length)
            return cls(id_, status, data), None
        except Exception as e:
            return None, e

    def to_bytes(self) -> bytes:
        id_ = self.id_._id
        status = self.status.value
        data = self.data
        return f"{id_} {status} {len(data)} ".encode() + data


class ServiceKind(enum.Enum):
    RS_256 = 0


@dataclass(frozen=True, eq=False)
class ServiceRequest:
    id_: RequestId
    kind: ServiceKind
    data: bytes

    @classmethod
    def parse(cls, stream: socket.socket) -> ResultTuple["ServiceRequest", Exception]:
        try:
            id_ = RequestId(_read_int(stream))
            kind = ServiceKind(_read_int(stream))
            data_length = _read_int(stream)
            data = _read_bytes(stream, data_length)
            return cls(id_, kind, data), None
        except Exception as e:
            return None, e

    def to_bytes(self) -> bytes:
        id_ = self.id_._id
        kind = self.kind.value
        data = self.data
        return f"{id_} {kind} {len(data)} ".encode() + data


@dataclass(frozen=True, eq=False)
class ServiceResponse:
    id_: RequestId
    status: Status
    data: bytes

    @classmethod
    def parse(cls, stream: socket.socket) -> ResultTuple["ServiceResponse", Exception]:
        try:
            id_ = RequestId(_read_int(stream))
            status = Status(_read_int(stream))
            data_length = _read_int(stream)
            data = _read_bytes(stream, data_length)
            return cls(id_, status, data), None
        except Exception as e:
            return None, e

    def to_bytes(self) -> bytes:
        id_ = self.id_._id
        status = self.status.value
        data = self.data
        return f"{id_} {status} {len(data)} ".encode() + data
