from abc import ABC, abstractmethod
from queue import Empty, Queue
from typing import Generic, Optional, Tuple, TypeVar

T = TypeVar("T")


class _PadBase(ABC, Generic[T]):
    _queue: "Queue[T]"

    @abstractmethod
    def empty(self) -> bool:
        pass

    @abstractmethod
    def put(
        self,
        item: T,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        pass

    @abstractmethod
    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> T:
        return self._queue.get(block=block, timeout=timeout)

    def into_pad_pair(self) -> "Tuple[_PadOut[T], _PadIn[T]]":
        return (_PadOut(self), _PadIn(self))


class _PadBlocking(_PadBase[T]):
    _queue: "Queue[T]"

    def __init__(self) -> None:
        self._queue = Queue(1)

    def empty(self) -> bool:
        return self._queue.empty()

    def put(
        self,
        item: T,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        self._queue.put(item, block=block, timeout=timeout)

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> T:
        return self._queue.get(block=block, timeout=timeout)


class _PadDiscardingOld(_PadBase[T]):
    _queue: "Queue[T]"

    def __init__(self) -> None:
        self._queue = Queue(1)

    def empty(self) -> bool:
        return self._queue.empty()

    def put(
        self,
        item: T,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        # First, make the queue empty.
        # Notice that only the owner of `_PadIn` can `put()`, but the owner can call `put()` cuncurrently.
        try:
            self.get(block=False)
        except Empty:
            pass
        # Then put.
        self._queue.put(item, block=block, timeout=timeout)

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> T:
        return self._queue.get(block=block, timeout=timeout)


class _PadIn(Generic[T]):
    _pad: _PadBase[T]

    def __init__(self, pad: _PadBase[T]) -> None:
        self._pad = pad

    def put(
        self,
        item: T,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        self._pad.put(item, block=block, timeout=timeout)


class _PadOut(Generic[T]):
    _pad: _PadBase[T]

    def __init__(self, pad: _PadBase[T]) -> None:
        self._pad = pad

    def empty(self) -> bool:
        return self._pad.empty()

    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> T:
        return self._pad.get(block=block, timeout=timeout)
