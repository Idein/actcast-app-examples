import enum
from typing import Callable, Generic, Iterable, Tuple, TypeVar, Union

from actfw_core.system import DeviceInfo, EnvironmentVariableNotSet, get_actcast_firmware_type
from actfw_core.v4l2.video import V4L2_PIX_FMT, Video, VideoPort  # type: ignore

from .task import Producer
from .util.pad import _PadBase, _PadDiscardingOld

T = TypeVar("T")


class Frame(Generic[T]):
    value: T

    """Captured Frame"""

    def __init__(self, value: T) -> None:
        self.value = value

    def getvalue(self) -> T:
        """
        Get frame data.

        Returns:
            bytes: captured image data

        """
        return self.value


CONFIGURATOR_RETURN = TypeVar("CONFIGURATOR_RETURN")


class V4LCameraCapture(Producer[Frame[bytes]]):
    video: Video
    capture_width: int
    capture_height: int
    capture_format: V4L2_PIX_FMT

    FormatSelector = enum.Enum("FormatSelector", "DEFAULT PROPER MAXIMUM")

    """Captured Frame Producer for Video4Linux"""

    def __init__(
        self,
        device: Union[str, DeviceInfo] = "/dev/video0",
        size: Tuple[int, int] = (640, 480),
        framerate: int = 30,
        expected_format: V4L2_PIX_FMT = V4L2_PIX_FMT.RGB24,
        fallback_formats: Iterable[V4L2_PIX_FMT] = (
            V4L2_PIX_FMT.YUYV,
            V4L2_PIX_FMT.MJPEG,
        ),
        format_selector: FormatSelector = FormatSelector.DEFAULT,
    ) -> None:
        """

        Args:
            device (str | DeviceInfo): v4l device path or info
            size (int, int): expected capture resolution
            framerate (int): expected capture framerate
            expected_format (:class:`~actfw_core.v4l2.video.V4L2_PIX_FMT`): expected capture format
            fallback_formats (list of :class:`~actfw_core.v4l2.video.V4L2_PIX_FMT`): fallback capture format
            format_selector (:class:`~actfw_core.capture.V4LCameraCapture.FormatSelector): how to select a format from listed formats supported by a camera. # noqa: B006 B950
                DEFAULT selects the first format that meets the conditions.
                PROPER selects the smallest format that meets the conditions.
                MAXIMUM selects the largest resolution format as a camera can.
                **MAXIMUM ignores framerate parameters (uses appropriate framerate for the selected resolution).**
                If a camera lists [1280x720, 1920x1080, 640x480, 800x600] and an expected capture resolution is (512, 512),
                DEFAULT selects 1280x720, PROPER selects 800x600 and MAXIMUM selects 1920x1080.

        Notes:
            If a camera doesn't support the expected_format,
            try to capture one of the fallback_formats and convert it to expected_format.

        """
        super().__init__()
        if isinstance(device, DeviceInfo):
            device_path = None
            for node in device.nodes:
                if node.label == "image_source":
                    device_path = node.path
            if device_path is None:
                raise RuntimeError("not found image_source.")
            else:
                device = str(device_path)
        elif isinstance(device, str):
            pass
        else:
            raise RuntimeError(f"the type of device={device} must be str or DeviceInfo.")

        self.video = Video(device)

        width, height = size

        cap = self.video.query_capability()
        try:
            firmware_type = get_actcast_firmware_type()
            if firmware_type == "raspberrypi-bullseye" and cap == VideoPort.CSI:
                raise RuntimeError("CSI camera is not supported in bullseye yet.")
        except EnvironmentVariableNotSet:
            pass

        if cap == VideoPort.CSI:
            # workaround for bcm2835-v4l2 format pixsize & bytesperline bug
            width = (width + 31) // 32 * 32
            height = (height + 15) // 16 * 16

            # workaround for bcm2835-v4l2 IMX219 32x32 -> 800x800 capture timeout bug
            candidates = self.video.lookup_config(64, 64, 5, V4L2_PIX_FMT.RGB24, V4L2_PIX_FMT.RGB24)
            self.video.set_format(candidates[0], 64, 64, V4L2_PIX_FMT.RGB24)

        if format_selector in [
            V4LCameraCapture.FormatSelector.PROPER,
            V4LCameraCapture.FormatSelector.MAXIMUM,
        ]:

            def cmp(config):  # type: ignore
                return (
                    config.width * config.height,
                    config.height,
                    config.width,
                    config.interval.denominator / config.interval.numerator,
                )

        else:

            def cmp(config):  # type: ignore
                return 1

        config = None
        fmts = [expected_format] + [f for f in fallback_formats]
        for fmt in fmts:
            expected_framerate = 1 if format_selector == V4LCameraCapture.FormatSelector.MAXIMUM else framerate
            candidates = self.video.lookup_config(width, height, expected_framerate, fmt, expected_format)
            candidates = sorted(candidates, key=cmp)
            if len(candidates) > 0:
                config = candidates[-1 if format_selector == V4LCameraCapture.FormatSelector.MAXIMUM else 0]
                break
        if config is None:
            raise RuntimeError("expected capture format is unsupported")
        if format_selector == V4LCameraCapture.FormatSelector.MAXIMUM:
            fmt = self.video.set_format(config, expected_format=expected_format)
        else:
            fmt = self.video.set_format(config, width, height, expected_format=expected_format)
        self.capture_width, self.capture_height, self.capture_format = fmt
        # TODO: v3.0.0. Comment out.
        # assert type(self.capture_format) is V4L2_PIX_FMT
        self.video.set_framerate(config)
        # video.set_rotation(90)
        self.video.request_buffers(4)
        self.video.queue_buffer()

    def capture_size(self) -> Tuple[int, int]:
        """
        Get configured capture resolution.
        A configured resolution may be more larger than expected one.

        Returns:
            (int, int): configured capture resolution (width, height)
        """
        return (self.capture_width, self.capture_height)

    def configure(self, configurator: Callable[[Video], CONFIGURATOR_RETURN]) -> CONFIGURATOR_RETURN:
        """
        Run user defined video configurator.

        Args:
            configurator : unary function (`actfw_core.v4l2.video.Video` -> a)

        Returns:
            object: return type of configurator
        """
        return configurator(self.video)

    def run(self) -> None:
        """Run producer activity"""
        with self.video.start_streaming() as stream:
            while self._is_running():
                value = stream.capture(timeout=5)
                frame = Frame(value)
                self._outlet(frame)
        self.video.close()

    def _new_pad(self) -> _PadBase[Frame[bytes]]:
        return _PadDiscardingOld()
