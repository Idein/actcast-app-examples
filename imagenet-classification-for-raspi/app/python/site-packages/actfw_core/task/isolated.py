from .task import Task


class Isolated(Task):

    """A task which has no connection."""

    def __init__(self) -> None:
        super().__init__()
