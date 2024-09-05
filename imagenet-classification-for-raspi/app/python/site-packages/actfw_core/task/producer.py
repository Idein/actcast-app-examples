from queue import Full
from typing import Generic, List, TypeVar

from ..util.pad import _PadBase, _PadBlocking, _PadIn
from .consumer import _ConsumerMixin
from .task import Task, _TaskI

T_OUT = TypeVar("T_OUT")


class _ProducerMixin(Generic[T_OUT], _TaskI):
    out_queues: List[_PadIn[T_OUT]]
    out_queue_id: int

    def __init__(self) -> None:
        """"""
        self.out_queues = []
        self.out_queue_id = 0

    def _add_out_queue(self, q: _PadIn[T_OUT]) -> None:
        self.out_queues.append(q)

    def _new_pad(self) -> _PadBase[T_OUT]:
        return _PadBlocking()

    def connect(self, follow: _ConsumerMixin[T_OUT]) -> None:
        """
        Connect following task.
        """
        assert isinstance(follow, _ConsumerMixin)

        pad_out, pad_in = self._new_pad().into_pad_pair()
        follow._add_in_queue(pad_out)
        self._add_out_queue(pad_in)

    def _outlet(self, o: T_OUT) -> bool:
        length = len(self.out_queues)
        while self._is_running():
            try:
                self.out_queues[self.out_queue_id].put(o, timeout=1)
                self.out_queue_id = (self.out_queue_id + 1) % length
                return True
            except Full:
                pass
        return False


class Producer(Generic[T_OUT], Task, _ProducerMixin[T_OUT]):
    """Producer Task."""

    def __init__(self) -> None:
        """"""
        Task.__init__(self)
        _ProducerMixin.__init__(self)

    def run(self) -> None:
        """Run and start the activity"""
        while True:
            o = self.proc()
            self._outlet(o)
            if not self._is_running():
                break

    def proc(self) -> T_OUT:
        """
        Pipeline Task Processor
        """
        raise NotImplementedError("'proc' must be overridden.")
