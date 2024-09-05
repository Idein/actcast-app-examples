from threading import Thread
from typing import Callable

from ..compat.queue import SimpleQueue


class LoopThread:
    _error_ch: SimpleQueue
    _loop_body: Callable[[], None]
    _allow_extra_loop_for_teardown: bool
    _thread: Thread
    _teardown_ch: SimpleQueue

    def __init__(
        self,
        error_ch: SimpleQueue,
        loop_body: Callable[[], None],
        allow_extra_loop_for_teardown: bool = False,
        daemon: bool = False,
    ) -> None:
        self._error_ch = error_ch
        self._teardown_ch = SimpleQueue()
        self._loop_body = loop_body
        self._thread = Thread(target=self._loop, daemon=daemon)
        self._allow_extra_loop_for_teardown = allow_extra_loop_for_teardown

    def startup(self) -> None:
        self._thread.start()

    def teardown(self) -> None:
        self._teardown_ch.put(None)

    def join(self) -> None:
        self._thread.join()

    def _loop(self) -> None:
        try:
            while self._teardown_ch.empty():
                self._loop_body()
            if self._allow_extra_loop_for_teardown:
                self._loop_body()
        except Exception as e:
            self._error_ch.put(e)
