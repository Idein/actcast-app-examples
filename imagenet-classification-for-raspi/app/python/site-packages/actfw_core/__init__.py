import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from . import capture, linux, system, task, unicam_isp_capture  # noqa: F401
from .application import Application  # noqa: F401
from .command_server import CommandServer  # noqa: F401
from .service_client import ServiceClient  # noqa: F401


def notify(
    notification: List[Dict[str, Any]],
    *args: Any,
    **kwargs: Any,
) -> None:
    """

    Make a notification to Actcast.

    Args:
        notification (list of dict): dicts must be encodable to JSON.

    Example:

        >>> import actfw_core
        >>> actfw_core.notify([{'msg': 'Hello!'}])
        [{"msg": "Hello!"}]

    """
    if type(notification) != list:
        raise TypeError("must be a list of JSON encodable objects.")
    kwargs["flush"] = True
    print(json.dumps(notification), *args, **kwargs)


_default_heartbeat_file = Path("/root/heartbeat")


def _default_heartbeat(*args: Any, **kwargs: Any) -> None:
    _default_heartbeat_file.touch()


_heartbeat_function = _default_heartbeat


def set_heartbeat_function(f: Callable[..., None]) -> None:
    """

    Set heartbeat action.

    Args:
        f (function): function which execute heartbeat action

    Example:

        >>> import actfw_core
        >>> def heartbeat(): print("working!")
        ...
        >>> actfw_core.set_heartbeat_function(heartbeat)
        >>> actfw_core.heartbeat()
        working!

    """
    global _heartbeat_function
    _heartbeat_function = f


def heartbeat(*args: Any, **kwargs: Any) -> None:
    """

    Execute heartbeat action.

    Notes:
        Default action is 'touch /root/heartbeat'.

    """
    _heartbeat_function(*args, **kwargs)
