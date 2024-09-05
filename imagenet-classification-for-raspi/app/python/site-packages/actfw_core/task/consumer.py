from queue import Empty
from typing import Generator, Generic, List, TypeVar

from ..util.pad import _PadOut
from .task import Task, _TaskI

T_IN = TypeVar("T_IN")


class _ConsumerMixin(Generic[T_IN], _TaskI):
    in_queues: List[_PadOut[T_IN]]

    def __init__(self) -> None:
        self.in_queues = []

    def _add_in_queue(self, q: _PadOut[T_IN]) -> None:
        self.in_queues.append(q)

    def _inlet(self) -> Generator[T_IN, None, None]:
        in_queue_id = 0
        length = len(self.in_queues)
        while self._is_running():
            try:
                i = self.in_queues[in_queue_id].get(timeout=1)
                yield i
                in_queue_id = (in_queue_id + 1) % length
            except Empty:
                pass
            except GeneratorExit:
                break


class Consumer(Generic[T_IN], Task, _ConsumerMixin[T_IN]):
    """Consumer Task."""

    def __init__(self) -> None:
        Task.__init__(self)
        _ConsumerMixin.__init__(self)

    def run(self) -> None:
        """Run and start the activity"""
        for i in self._inlet():
            self.proc(i)
            if not self._is_running():
                break

    def proc(self, i: T_IN) -> None:
        """
        Pipeline Task Processor

        Args:
            i : task input
        """
        raise NotImplementedError("'proc' must be overridden.")
