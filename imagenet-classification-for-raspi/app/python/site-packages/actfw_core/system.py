import json
import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from actfw_core.v4l2.video import Video, VideoPort  # type: ignore


class EnvironmentVariableNotSet(Exception):
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"Environment variable {self.name} is not set. Perhaps the host agent is too old?"


@dataclass
class DeviceNode:
    path: Path
    label: Optional[str] = None

    @staticmethod
    def from_json(json: Dict[str, Any]) -> "DeviceNode":
        path = json.get("path", None)
        if path is None:
            raise ValueError("must have path property")

        if type(path) is not str:
            raise ValueError("path must be string")

        path = Path(path)

        label = json.get("label", None)
        if label is None:
            return DeviceNode(path=path, label=None)
        else:
            if type(label) is not str:
                raise ValueError("label must be string")
            return DeviceNode(path=path, label=label)


@dataclass
class DeviceInfo:
    type: str
    nodes: List[DeviceNode]

    @staticmethod
    def from_json(json: Dict[str, Any]) -> "DeviceInfo":
        if "type" not in json.keys():
            raise ValueError("must have type property")
        if "nodes" not in json.keys():
            raise ValueError("must have nodes property")

        device_type = json["type"]
        if type(device_type) is not str:
            raise ValueError("type must be string")

        nodes = [DeviceNode.from_json(node) for node in json["nodes"]]
        return DeviceInfo(type=device_type, nodes=nodes)


@dataclass
class DeviceSupply:
    devices: List[DeviceInfo]

    @staticmethod
    def from_json(json: Dict[str, Any]) -> "DeviceSupply":
        if "devices" not in json.keys():
            raise ValueError("must have devices property")

        devices = [DeviceInfo.from_json(d) for d in json["devices"]]
        return DeviceSupply(devices=devices)


def _get_env_str(name: str) -> str:
    ret = os.environ.get(name)
    if ret is None:
        raise EnvironmentVariableNotSet(name)
    return ret


def _get_env_int(name: str) -> int:
    ret = os.environ.get(name)
    if ret is None:
        raise EnvironmentVariableNotSet(name)
    return int(ret)


def get_actcast_protocol_version() -> str:
    "Protocol version of agent-app communication. Since ACTCAST_PROTOCOL_VERSION 1.0.0."
    return _get_env_str("ACTCAST_PROTOCOL_VERSION")


def get_actcast_device_id() -> str:
    "Device ID of the device running the actcast application. Since ACTCAST_PROTOCOL_VERSION 1.0.0."
    return _get_env_str("ACTCAST_DEVICE_ID")


def get_actcast_group_id() -> int:
    "Group ID that the device is belonging to. Since ACTCAST_PROTOCOL_VERSION 1.2.0."
    return _get_env_int("ACTCAST_GROUP_ID")


def get_actcast_act_id() -> int:
    "Act ID of the actcast application. Since ACTCAST_PROTOCOL_VERSION 1.0.0."
    return _get_env_int("ACTCAST_ACT_ID")


def get_actcast_instance_id() -> str:
    "ID that identifies the launch of the actcast application, like PID. Since ACTCAST_PROTOCOL_VERSION 1.0.0."
    return _get_env_str("ACTCAST_INSTANCE_ID")


def get_actcast_device_type() -> str:
    "Device type. Since ACTCAST_PROTOCOL_VERSION 1.1.0."
    return _get_env_str("ACTCAST_DEVICE_TYPE")


def get_act_settings_path() -> str:
    """
    Path of act settings.
    This is rather low level API.
    Use get_settings in Application to get act settings.
    Since ACTCAST_PROTOCOL_VERSION 1.0.0.
    """
    return _get_env_str("ACT_SETTINGS_PATH")


def get_actcast_command_sock() -> str:
    """
    Path of socket file to receive command from actcast agent.
    This is rather low level API.
    Use CommandServer to receive commands from actcast agent.
    Since ACTCAST_PROTOCOL_VERSION 1.0.0.
    """
    return _get_env_str("ACTCAST_COMMAND_SOCK")


def get_actcast_service_sock() -> str:
    """
    Path of socket file to send command to actcast agent.
    This is rather low level API.
    Use ServiceClient to send commands to actcast agent.
    Since ACTCAST_PROTOCOL_VERSION 1.0.0.
    """
    return _get_env_str("ACTCAST_SERVICE_SOCK")


def get_actcast_socks_server() -> Optional[str]:
    "URL of SOCKS5 proxy server. Since ACTCAST_PROTOCOL_VERSION 1.0.0."
    return os.environ.get("ACTCAST_SOCKS_SERVER")


def get_actcast_agent_simulator() -> Optional[str]:
    'Fixed value "actsim" if on actsim environment. Not set otherwise. Since ACTCAST_PROTOCOL_VERSION 1.1.0.'
    return os.environ.get("ACTCAST_AGENT_SIMULATOR")


def get_actcast_firmware_type() -> str:
    "Firmware type of the host. Since ACTCAST_PROTOCOL_VERSION 1.3.0."
    return _get_env_str("ACTCAST_FIRMWARE_TYPE")


def get_device_supply_path() -> str:
    """
    Path of device supply file.
    This is rather low level API.
    Use get_device_supply to get DeviceSupply object.
    Since ACTCAST_PROTOCOL_VERSION 1.3.0.
    """
    return _get_env_str("DEVICE_SUPPLY_PATH")


def get_device_supply() -> DeviceSupply:
    """
    Device Supply from actcast agent.
    Since ACTCAST_PROTOCOL_VERSION 1.3.0.
    """
    path = get_device_supply_path()
    with open(path) as f:
        return DeviceSupply.from_json(json.load(f))


def _get_camera_device_info(devs: DeviceSupply, default_image_source: Optional[str] = None) -> DeviceInfo:
    cameras = [dev for dev in devs.devices if dev.type == "camera"]
    if len(cameras) >= 1:
        if len(cameras) > 1:
            warnings.warn(
                "There are multiple camera candidates. Check your manifesto files.",
                RuntimeWarning,
            )
        info = cameras[0]
        sources = [node for node in info.nodes if node.label == "image_source"]
        if len(sources) >= 1:
            return info
        elif default_image_source is not None:
            if Path(default_image_source) in [node.path for node in info.nodes]:
                for node in info.nodes:
                    if node.path == Path(default_image_source):
                        node.label = "image_source"
                return info
            else:
                raise RuntimeError(f"default_image_source={default_image_source} is not mounted. Fix your manifesto files.")
        else:
            raise RuntimeError(
                "Not found image_source. Fix your manifesto files or give default_image_source to get_camera_device_info."
            )

    else:
        raise RuntimeError("Not found camera device. Fix your manifesto files.")


def get_camera_device_info(default_image_source: Optional[str] = None) -> DeviceInfo:
    """
    DeviceInfo for camera.
    Set `default_image_source` only if you write camera device path in manifesto files.
    Since ACTCAST_PROTOCOL_VERSION 1.3.0.
    """
    devs = get_device_supply()
    return _get_camera_device_info(devs, default_image_source)


def _list_video_devices() -> List[str]:
    devs = get_device_supply()
    cameras = [dev for dev in devs.devices if dev.type == "camera"]
    paths: List[str] = []
    for c in cameras:
        for node in filter(lambda n: str(n.path).startswith("/dev/video"), c.nodes):
            paths.append(str(node.path))
    return paths


def _find_specific_video_device(video_port: VideoPort) -> Optional[str]:
    devs = _list_video_devices()
    for dev in devs:
        try:
            # No `video.close()` leads to Capture timeout error.
            with Video(dev) as video:
                if video.query_capability() == video_port:
                    return dev
        except RuntimeError:
            pass
    return None


def find_usb_camera_device() -> Optional[str]:
    """
    Path of USB camera device.
    Since ACTCAST_PROTOCOL_VERSION 1.3.0.
    """
    return _find_specific_video_device(VideoPort.USB)


def find_csi_camera_device() -> Optional[str]:
    """
    Path of CSI camera device.
    Since ACTCAST_PROTOCOL_VERSION 1.3.0.
    """
    return _find_specific_video_device(VideoPort.CSI)
