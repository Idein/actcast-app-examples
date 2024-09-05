import sys

if sys.version_info >= (3, 7):
    from queue import SimpleQueue  # noqa F401
else:
    from queue import Queue as SimpleQueue  # noqa F401
