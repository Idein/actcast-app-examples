# type: ignore
# flake8: noqa
import errno
import os
from ctypes import c_char_p, get_errno
from fcntl import ioctl

from actfw_core.linux.ioctl import _IOW, _IOWR
from actfw_core.linux.types import dma_heap_allocation_data

_DMA_HEAP_IOCTL_ALLOC = _IOWR("H", 0, dma_heap_allocation_data)
_DMA_BUF_SET_NAME = _IOW("b", 1, c_char_p)


class DMAHeap(object):
    def __init__(self, node="/dev/dma_heap/linux,cma"):
        self.heap_fd = os.open(node, os.O_RDWR)

    def alloc(self, name: str, size: int) -> int:
        alloc = dma_heap_allocation_data()
        alloc.len = size
        alloc.fd_flags = os.O_CLOEXEC | os.O_RDWR
        result = ioctl(self.heap_fd, _DMA_HEAP_IOCTL_ALLOC, alloc)
        if -1 == result:
            raise RuntimeError(f"ioctl(_DMA_HEAP_IOCTL_ALLOC){errno.errorcode[get_errno()]}")

        result = ioctl(alloc.fd, _DMA_BUF_SET_NAME, name)

        if -1 == result:
            raise RuntimeError(f"ioctl(_DMA_BUF_SET_NAME){errno.errorcode[get_errno()]}")

        return alloc.fd
