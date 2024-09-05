import warnings
from typing import Optional, Tuple

from actfw_core.system import EnvironmentVariableNotSet, get_actcast_firmware_type

from .edid import EDID


class Display:
    size: Tuple[int, int]
    preferred_size: Tuple[int, int]
    scale: float
    ofs_w: float
    ofs_h: float
    camera: "picamera.PiCamera"  # type: ignore  # reason: can't depend on picamera  # noqa F821
    layer: Optional["picamera.PiOverlayRenderer"]  # type: ignore  # reason: can't depend on picamera  # noqa F821

    """Display using PiCamera Overlay"""

    def __init__(
        self,
        camera: "picamera.PiCamera",  # type: ignore  # reason: can't depend on picamera  # noqa F821
        size: Tuple[int, int],
    ) -> None:
        """

        Args:
            camera (:class:`~picamera.PiCamera`): picamera object
            size (int, int): display area resolution

        """
        try:
            firmware_type: Optional[str] = get_actcast_firmware_type()
        except EnvironmentVariableNotSet:
            firmware_type = None

        if firmware_type == "raspberrypi-bullseye":
            raise RuntimeError("Display do not work in bullseye.")
        else:
            warnings.warn(
                "actfw_raspberrypi.Display do not work in bullseye and actfw_raspberrypi.Display will be deprecated soon.",
                PendingDeprecationWarning,
            )

        self.size = size
        self.preferred_size = EDID().prefferd_mode()
        scale_w = self.preferred_size[0] / self.size[0]
        scale_h = self.preferred_size[1] / self.size[1]
        self.scale = min(scale_w, scale_h)
        self.ofs_w = (self.preferred_size[0] - self.size[0] * self.scale) / 2.0
        self.ofs_h = (self.preferred_size[1] - self.size[1] * self.scale) / 2.0
        self.camera = camera
        self.layer = None

    def update(
        self,
        dst_rect: Tuple[int, int, int, int],
        src_buf: bytes,
        src_size: Tuple[int, int],
        src_format: str,
    ) -> None:
        """

        Update display.

        Args:
            dst_rect (int, int, int, int): destination area rectangle (left, upper, width, height)
            src_buf (bytes): update image data buffer
            src_size (int, int): update image data size (width, height)
            src_format (string): "rgb"

        """
        rect = (
            int(dst_rect[0] * self.scale + self.ofs_w),
            int(dst_rect[1] * self.scale + self.ofs_h),
            int(dst_rect[2] * self.scale),
            int(dst_rect[3] * self.scale),
        )
        layer = self.camera.add_overlay(
            src_buf,
            size=src_size,
            format=src_format,
            layer=2,
            alpha=255,
            fullscreen=False,
            window=rect,
        )
        if self.layer is not None:
            self.camera.remove_overlay(self.layer)
        self.layer = layer
