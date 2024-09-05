from queue import Full
from typing import Generic, TypeVar

from .consumer import _ConsumerMixin
from .producer import _ProducerMixin
from .task import Task

T = TypeVar("T")


class Tee(Generic[T], Task, _ProducerMixin[T], _ConsumerMixin[T]):
    """Tee Task."""

    def __init__(self) -> None:
        """"""
        Task.__init__(self)
        _ProducerMixin.__init__(self)
        _ConsumerMixin.__init__(self)

    def _outlet(self, o: T) -> bool:
        while self._is_running():
            for out_queue in self.out_queues:
                try:
                    out_queue.put(o, timeout=1)
                except Full:
                    pass
            return True
        return False

    def run(self) -> None:
        """Run and start the activity"""
        for i in self._inlet():
            o = i
            self._outlet(o)
            if not self._is_running():
                break
