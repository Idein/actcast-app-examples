import json
import mmap
import select
from ctypes import POINTER, c_int16, c_void_p, cast, pointer, sizeof
from dataclasses import dataclass
from math import floor
from os import path
from typing import Any, Dict, List, Optional, Tuple

from actfw_core.capture import Frame
from actfw_core.linux.dma_heap import DMAHeap  # type: ignore
from actfw_core.task import Producer
from actfw_core.v4l2.types import (
    AWB_REGIONS,
    CONTRAST_NUM_POINTS,
    NUM_HISTOGRAM_BINS,
    bcm2835_isp_black_level,
    bcm2835_isp_gain_format,
    bcm2835_isp_gamma,
    bcm2835_isp_lens_shading,
    bcm2835_isp_stats,
    v4l2_ext_control,
)
from actfw_core.v4l2.video import (  # type: ignore
    MEDIA_BUS_FMT,
    V4L2_BUF_TYPE,
    V4L2_CID,
    V4L2_MEMORY,
    V4L2_META_FMT,
    V4L2_PIX_FMT,
    RawVideo,
    V4LConverter,
)

_EMPTY_LIST: List[str] = []

AGC_INTERVAL: int = 3
# TODO: support other than imx219
# pick from https://github.com/kbingham/libcamera/blob/22ffeae04de2e7ce6b2476a35233c790beafb67f/src/ipa/raspberrypi/data/imx219.json#L132-L142 # noqa: E501, B950

MAX_LS_GRID_SIZE = 0x8000
LS_TABLE_W = 16
LS_TABLE_H = 12


# correspond to [libcamera's CameraMode](https://github.com/raspberrypi/libcamera/blob/3fad116f89e0d3497567043cbf6d8c49f1c102db/src/ipa/raspberrypi/controller/camera_mode.h#L19) # noqa: E501, B950
@dataclass(frozen=True, eq=True)
class CameraMode:
    size: Tuple[int, int]
    scale: Tuple[float, float]
    crop: Tuple[int, int]


V1_SENSOR_SIZE = (2592, 1944)
V1_UNICAM_MODES: List[CameraMode] = [
    CameraMode(size=(2592, 1944), scale=(1.0, 1.0), crop=(0, 0)),
    CameraMode(size=(1920, 1080), scale=(1.0, 1.0), crop=(336, 432)),
    CameraMode(size=(1296, 972), scale=(2.0, 2.0), crop=(0, 0)),
    CameraMode(size=(640, 480), scale=(4.0, 4.0), crop=(0, 0)),
]

V2_SENSOR_SIZE = (3280, 2464)
V2_UNICAM_MODES: List[CameraMode] = [
    CameraMode(size=(3280, 2464), scale=(1.0, 1.0), crop=(0, 0)),
    CameraMode(size=(1920, 1080), scale=(1.0, 1.0), crop=(680, 692)),
    CameraMode(size=(1640, 1232), scale=(2.0, 2.0), crop=(0, 0)),
    CameraMode(size=(640, 480), scale=(2.0, 2.0), crop=(1000, 752)),
]

V3_SENSOR_SIZE = (4608, 2592)
V3_UNICAM_MODES: List[CameraMode] = [
    CameraMode(size=(4608, 2592), scale=(1.0, 1.0), crop=(0, 0)),
    CameraMode(size=(2304, 1296), scale=(2.0, 2.0), crop=(0, 0)),
    CameraMode(size=(1536, 864), scale=(2.0, 2.0), crop=(768, 432)),
]


class UnicamIspCapture(Producer[Frame[bytes]]):
    def __init__(
        self,
        unicam: str = "/dev/video0",
        unicam_subdev: str = "/dev/v4l-subdev0",
        isp_in: str = "/dev/video13",
        isp_out_high: str = "/dev/video14",
        isp_out_metadata: str = "/dev/video16",
        size: Tuple[int, int] = (640, 480),
        unicam_size: Optional[Tuple[int, int]] = None,
        crop_size: Optional[Tuple[int, int, int, int]] = None,
        framerate: int = 30,
        expected_format: V4L2_PIX_FMT = V4L2_PIX_FMT.RGB24,
        auto_whitebalance: bool = True,
        init_controls: List[str] = _EMPTY_LIST,
        agc: bool = True,
        target_Y: float = 0.16,  # Temporary set for the developement of agc algorithm
        alsc: bool = True,
        default_color_temperature: int = 4500,
        contrast: bool = True,
        config: Optional[Dict[str, Any]] = None,
        vflip: bool = False,
        hflip: bool = False,
        timeout: float = 1.0,
    ) -> None:
        super().__init__()

        self.dma_buffer_num = 4
        self.isp_out_buffer_num = 4
        self.isp_out_metadata_buffer_num = 2
        self.shared_dma_fds: List[int] = []
        self.sensor_name = self.get_sensor_name(unicam_subdev)
        self.timeout = timeout
        if self.sensor_name not in ["imx708", "imx219", "ov5647"]:
            raise RuntimeError(f"not supported sensor: {self.sensor_name}")

        self.unicam = RawVideo(
            unicam,
            v4l2_buf_type=V4L2_BUF_TYPE.VIDEO_CAPTURE,
            init_controls=init_controls,
        )
        self.unicam_subdev = RawVideo(
            unicam_subdev,
            v4l2_buf_type=V4L2_BUF_TYPE.VIDEO_CAPTURE,
            init_controls=init_controls,
        )
        self.isp_in = RawVideo(
            isp_in,
            v4l2_buf_type=V4L2_BUF_TYPE.VIDEO_OUTPUT,
            init_controls=init_controls,
        )
        self.isp_out_high = RawVideo(
            isp_out_high,
            v4l2_buf_type=V4L2_BUF_TYPE.VIDEO_CAPTURE,
            init_controls=init_controls,
        )
        self.isp_out_metadata = RawVideo(
            isp_out_metadata,
            v4l2_buf_type=V4L2_BUF_TYPE.META_CAPTURE,
            init_controls=init_controls,
        )
        self.do_awb = auto_whitebalance
        self.do_agc = agc
        self.do_contrast = contrast
        self.do_alsc = alsc

        (self.expected_width, self.expected_height) = size
        self.expected_pix_format = expected_format
        self.expected_fps = framerate

        if unicam_size is not None and crop_size is not None:
            matched_modes = list(filter(lambda mode: mode.size == unicam_size, V2_UNICAM_MODES))
            if len(matched_modes) == 0:
                raise RuntimeError(f"({unicam_size}) is not supported for unicam size")
            self.camera_mode = matched_modes[0]
            self.crop_size = crop_size
        elif unicam_size is None and crop_size is None:
            # Auto selection of unicam_size and crop_size.
            if self.sensor_name == "imx219":
                self.auto_size_selection_for_imx219()
            elif self.sensor_name == "imx708":
                self.auto_size_selection_for_imx708()
            else:
                self.auto_size_selection_for_ov5647()
        else:
            raise RuntimeError("Both unicam_size and crop_size must be None or tuples.")

        # control values
        if self.sensor_name == "imx708":
            config_file = self.get_subdevice_name(unicam_subdev) + ".json"
        else:
            config_file = self.sensor_name + ".json"
        # config precedence: default < sensor specific < user given
        with open(path.join(path.dirname(__file__), "data", config_file), "r") as f:
            sensor_config = json.load(f)
        sensor_config.update(config or {})

        # black level config
        _bl = sensor_config.get("rpi.black_level", {})
        self.black_level: int = _bl.get("black_level", 4096)

        # lux config
        _lx = sensor_config.get("rpi.lux", {})
        self.reference_shutter_speed: float = _lx.get("reference_shutter_speed", 27685.0)
        self.reference_gain: float = _lx.get("reference_gain", 1.0)
        self.reference_aperture: float = _lx.get("reference_aperture", 1.0)
        self.reference_lux: float = _lx.get("reference_lux", 998.0)
        self.reference_Y: float = _lx.get("reference_Y", 12744.0)
        self.aperture: float = 1.0
        # - update by awb
        self.gain_r: float = 1.6
        self.gain_b: float = 1.6
        # - update by agc
        _ag = sensor_config.get("rpi.agc", {})
        _ag = _ag["channels"][0] if "channels" in _ag else _ag
        self.shutters = _ag.get("exposure_modes", {}).get("normal", {}).get("shutter")
        self.gains = _ag.get("exposure_modes", {}).get("normal", {}).get("gain")
        self.gain: float = 1.0
        self.shutter_speed: float = 1000.0
        self.exposure: float = 100  # `shutter speed(us)` * `analogue gain`
        self.degital_gain: float = 1.0  # Currently, this value is constant.
        self.agc_interval_count: int = 0
        self.target_Y: float = target_Y
        # - update by contrast
        _cr = sensor_config.get("rpi.contrast", {})
        self.ce_enable = _cr.get("ce_enable", True)
        self.brightness: float = _cr.get("brightness", 0.0)
        self.contrast: float = _cr.get("contrast", 1.0)
        self.lo_histogram: float = _cr.get("hi_histogram", 0.01)
        self.lo_level: float = _cr.get("lo_level", 0.015)
        self.lo_max: int = _cr.get("lo_max", 500)
        self.hi_histogram: float = _cr.get("hi_histogram", 0.95)
        self.hi_level: float = _cr.get("hi_level", 0.95)
        self.hi_max: int = _cr.get("hi_max", 0.95)
        gamma_curve = _cr["gamma_curve"]
        self.gamma_curve: List[Tuple[float, float]] = [
            (gamma_curve[2 * n], gamma_curve[2 * n + 1]) for n in range(0, len(gamma_curve) // 2)
        ]

        self.color_temperature = default_color_temperature

        # - update by alsc
        self.ls_table_dma_heap_fd = DMAHeap("/dev/dma_heap/linux,cma").alloc("_ls_grid", MAX_LS_GRID_SIZE)
        self.ls_table_mm = mmap.mmap(
            self.ls_table_dma_heap_fd,
            MAX_LS_GRID_SIZE,
            flags=mmap.MAP_SHARED,
            prot=mmap.PROT_READ | mmap.PROT_WRITE,
        )
        _alsc = sensor_config.get("rpi.alsc", {})
        self.calibrations_Cr: List[Dict[str, Any]] = _alsc["calibrations_Cr"]
        self.calibrations_Cb: List[Dict[str, Any]] = _alsc["calibrations_Cb"]
        self.luminace_lut: List[float] = _alsc["luminance_lut"]
        self.luminace_strength: float = _alsc["luminance_strength"]

        # some device status cache (set by set_unicam_fps)
        self.vblank: int = 0
        self.hblank: int = 0
        self.pixel_late: int = 0

        # vflip & hflip
        self.vflip = vflip
        self.hflip = hflip

        # setup
        self.converter = V4LConverter(self.isp_out_high.device_fd)
        self.setup_pipeline()
        self.output_fmt = self.converter.try_convert(
            self.isp_out_high.fmt,
            self.expected_width,
            self.expected_height,
            self.expected_pix_format,
        )

        self.request_buffer()

    def get_sensor_name(self, subdev: str) -> str:
        with open(f"/sys/class/video4linux/{subdev[5:]}/device/name") as f:
            sensor_name = f.read()
        return sensor_name.rstrip()

    def get_subdevice_name(self, subdev: str) -> str:
        with open(f"/sys/class/video4linux/{subdev[5:]}/device/video4linux/{subdev[5:]}/name") as f:
            subdevice_name = f.read()
        return subdevice_name.rstrip()

    def setup_pipeline(self) -> None:
        # setup unicam
        if self.sensor_name in ["imx219", "imx708"]:
            # imx219 is flipped by default
            if not (
                self.unicam_subdev.set_vertical_flip(not self.vflip) and self.unicam_subdev.set_horizontal_flip(not self.hflip)
            ):
                raise RuntimeError("fail to setup unicam subdevice node")
            # https://www.kernel.org/doc/html/v5.15/userspace-api/media/v4l/subdev-formats.html?highlight=media_bus_fmt
            if self.vflip and self.hflip:
                bus_fmt = MEDIA_BUS_FMT.SRGGB10_1X10
                self.unicam_format = V4L2_PIX_FMT.SRGGB10P
            elif self.vflip and not self.hflip:
                bus_fmt = MEDIA_BUS_FMT.SGRBG10_1X10
                self.unicam_format = V4L2_PIX_FMT.SGRBG10P
            elif not self.vflip and self.hflip:
                bus_fmt = MEDIA_BUS_FMT.SGBRG10_1X10
                self.unicam_format = V4L2_PIX_FMT.SGBRG10P
            else:
                bus_fmt = MEDIA_BUS_FMT.SBGGR10_1X10
                self.unicam_format = V4L2_PIX_FMT.SBGGR10P
        else:
            if not (self.unicam_subdev.set_vertical_flip(self.vflip) and self.unicam_subdev.set_horizontal_flip(self.hflip)):
                raise RuntimeError("fail to setup unicam subdevice node")
            if self.vflip and self.hflip:
                bus_fmt = MEDIA_BUS_FMT.SGRBG10_1X10
                self.unicam_format = V4L2_PIX_FMT.SGRBG10P
            elif self.vflip and not self.hflip:
                bus_fmt = MEDIA_BUS_FMT.SRGGB10_1X10
                self.unicam_format = V4L2_PIX_FMT.SRGGB10P
            elif not self.vflip and self.hflip:
                bus_fmt = MEDIA_BUS_FMT.SBGGR10_1X10
                self.unicam_format = V4L2_PIX_FMT.SBGGR10P
            else:
                bus_fmt = MEDIA_BUS_FMT.SGBRG10_1X10
                self.unicam_format = V4L2_PIX_FMT.SGBRG10P

        self.unicam_subdev.set_subdev_format(*self.camera_mode.size, bus_fmt)
        if (
            self.unicam_subdev.subdev_fmt.format.width != self.camera_mode.size[0]
            or self.unicam_subdev.subdev_fmt.format.height != self.camera_mode.size[1]
        ):
            raise RuntimeError("fail to setup unicam device node")

        self.unicam_width = self.unicam_subdev.subdev_fmt.format.width
        self.unicam_height = self.unicam_subdev.subdev_fmt.format.height
        (unicam_width, unicam_height, unicam_format) = self.unicam.set_pix_format(
            self.unicam_width, self.unicam_height, self.unicam_format
        )
        if unicam_width != self.unicam_width or unicam_height != self.unicam_height or unicam_format != self.unicam_format:
            raise RuntimeError("fail to setup unicam device node")

        self.set_unicam_fps()
        if self.do_agc:
            init_shutter_time = self.shutters[len(self.shutters) // 2]  # (us)
            init_analogue_gain = self.gains[len(self.gains) // 2]
            self.set_unicam_exposure(init_analogue_gain, init_shutter_time)
            self.exposure = init_shutter_time * init_analogue_gain

        # current alsc implementation does not change lens_shading table dynamically
        if self.do_alsc:
            self.alsc()

        # sutup isp_in
        bl = bcm2835_isp_black_level()
        bl.enabled = 1
        bl.black_level_r = self.black_level
        bl.black_level_g = self.black_level
        bl.black_level_b = self.black_level
        black_level = v4l2_ext_control()
        black_level.id = V4L2_CID.USER_BCM2835_ISP_BLACK_LEVEL
        black_level.size = sizeof(bcm2835_isp_black_level)
        black_level.ptr = cast(pointer(bl), c_void_p)
        self.isp_in.set_ext_controls([black_level])
        (isp_in_width, isp_in_height, isp_in_format) = self.isp_in.set_pix_format(
            self.unicam_width, self.unicam_height, self.unicam_format
        )
        if isp_in_width != self.unicam_width or isp_in_height != self.unicam_height or isp_in_format != self.unicam_format:
            raise RuntimeError("fail to setup isp input")

        if self.crop_size is not None:
            self.isp_in.set_selection(*self.crop_size)

        # setup isp_out_high

        # TODO: Ensure that the value of bytesperline is equal to width or handle padding appropriately.
        # One possible solution is to use only width of multiples of 32.
        (
            isp_out_width,
            isp_out_height,
            isp_out_format,
        ) = self.isp_out_high.set_pix_format(self.expected_width, self.expected_height, self.expected_pix_format)

        self.output_fmt = self.converter.try_convert(
            self.isp_out_high.fmt,
            self.expected_width,
            self.expected_height,
            self.expected_pix_format,
        )

        # setup isp_out_metadata
        self.isp_out_metadata.set_meta_format(V4L2_META_FMT.BCM2835_ISP_STATS, sizeof(bcm2835_isp_stats))

    def set_unicam_fps(self) -> None:
        ctrls = self.unicam_subdev.get_ext_controls([V4L2_CID.HBLANK, V4L2_CID.PIXEL_RATE])
        hblank = ctrls[0].value
        pixel_late = ctrls[1].value64

        expected_pixel_per_second = pixel_late // self.expected_fps
        expected_line_num = expected_pixel_per_second // (self.unicam_width + hblank)
        expected_vblank = expected_line_num - self.unicam_height
        # TODO: check supported vblank range
        vblank_ctrl = v4l2_ext_control()
        vblank_ctrl.id = V4L2_CID.VBLANK
        vblank_ctrl.value = expected_vblank
        ctrls = self.unicam_subdev.set_ext_controls([vblank_ctrl])

        self.hblank = hblank
        self.vblank = expected_vblank
        self.pixel_late = pixel_late

    def set_unicam_exposure(self, analogue_gain: float, shutter_time: float) -> None:
        # convert analogue_gain to V4L2_CID.ANALOGUE_GAIN
        unicam_subdev_analogue_gain = self.v4l2_control_value_for_analogue_gain(analogue_gain)

        # convert shutter time to V4L2_CID.EXPOSURE
        time_per_line = (self.unicam_width + self.hblank) * (1.0 / self.pixel_late) * 1e6
        unicam_subdev_exposure = shutter_time / time_per_line

        exposure_ctrl = v4l2_ext_control()
        exposure_ctrl.id = V4L2_CID.EXPOSURE
        exposure_ctrl.value = int(unicam_subdev_exposure)
        gain_ctrl = v4l2_ext_control()
        gain_ctrl.id = V4L2_CID.ANALOGUE_GAIN
        gain_ctrl.value = int(unicam_subdev_analogue_gain)
        self.unicam_subdev.set_ext_controls([exposure_ctrl, gain_ctrl])

    def v4l2_control_value_for_analogue_gain(self, analogue_gain: float) -> float:
        if self.sensor_name == "imx219":
            return 256 - (
                256 / analogue_gain
            )  # https://github.com/raspberrypi/libcamera/blob/3fad116f89e0d3497567043cbf6d8c49f1c102db/src/ipa/raspberrypi/cam_helper_imx219.cpp#L67 # noqa: E501, B950
        elif self.sensor_name == "imx708":
            return 1024 - (
                1024 / analogue_gain
            )  # https://github.com/raspberrypi/libcamera/blob/6ddd79b5bdbedc1f61007aed35391f1559f9e29a/src/ipa/rpi/cam_helper/cam_helper_imx708.cpp#L103-L106 # noqa: E501, B950
        elif self.sensor_name == "ov5647":
            return (
                analogue_gain * 16.0
            )  # https://github.com/raspberrypi/libcamera/blob/3fad116f89e0d3497567043cbf6d8c49f1c102db/src/ipa/raspberrypi/cam_helper_ov5647.cpp#L45 # noqa: E501, B950
        else:
            raise RuntimeError(f"not supported sensor: {self.sensor_name}")

    def calc_crop_size(
        self,
        isp_out_width: int,
        isp_out_height: int,
        unicam_width: int,
        unicam_height: int,
    ) -> Tuple[int, int, int, int]:
        scale = min(unicam_height / isp_out_height, unicam_width / isp_out_width)
        w = round(isp_out_width * scale)
        h = round(isp_out_height * scale)
        assert w <= unicam_width and h <= unicam_height

        left = int((unicam_width - w) / 2)
        top = int((unicam_height - h) / 2)
        return (left, top, w, h)

    def auto_size_selection_for_imx708(self) -> None:
        if self.expected_width <= 1920 and self.expected_height <= 1080:
            if self.expected_fps <= 50:
                self.camera_mode = V3_UNICAM_MODES[1]
            else:
                self.camera_mode = V3_UNICAM_MODES[2]
        else:
            self.camera_mode = V3_UNICAM_MODES[0]
        self.crop_size = self.calc_crop_size(self.expected_width, self.expected_height, *self.camera_mode.size)

    def auto_size_selection_for_imx219(self) -> None:
        # Support only v2 camera module.
        if self.expected_width <= 1280 and self.expected_height <= 720:
            if self.expected_fps <= 40:
                self.camera_mode = V2_UNICAM_MODES[2]
                self.crop_size = self.calc_crop_size(self.expected_width, self.expected_height, *self.camera_mode.size)
            else:
                if abs(self.expected_width / self.expected_height - 16 / 9) < 0.05:
                    self.camera_mode = V2_UNICAM_MODES[2]
                    self.crop_size = (180, 256, 1280, 720)
                else:
                    self.camera_mode = V2_UNICAM_MODES[3]
                    self.crop_size = self.calc_crop_size(
                        self.expected_width,
                        self.expected_height,
                        *self.camera_mode.size,
                    )
        else:
            self.camera_mode = V2_UNICAM_MODES[0]
            self.crop_size = self.calc_crop_size(self.expected_width, self.expected_height, *self.camera_mode.size)

    def auto_size_selection_for_ov5647(self) -> None:
        # TODO: fix to make compatiblity with buster
        self.camera_mode = V1_UNICAM_MODES[0]
        self.crop_size = self.calc_crop_size(self.expected_width, self.expected_height, *self.camera_mode.size)

    def capture_size(self) -> Tuple[int, int]:
        return (self.output_fmt.fmt.pix.width, self.output_fmt.fmt.pix.height)

    def request_buffer(self) -> None:
        self.dma_buffer_num = self.unicam.request_buffers(self.dma_buffer_num, V4L2_MEMORY.MMAP)
        self.dma_fds = self.unicam.export_buffers()
        if self.unicam.request_buffers(self.dma_buffer_num, V4L2_MEMORY.DMABUF, self.dma_fds) != self.dma_buffer_num:
            raise RuntimeError("dma buffer count mismatch with the number of shared dma file descrptors")
        if self.isp_in.request_buffers(self.dma_buffer_num, V4L2_MEMORY.DMABUF, self.dma_fds) != self.dma_buffer_num:
            raise RuntimeError("dma buffer count mismatch with the number of shared dma file descrptors")
        self.isp_out_buffer_num = self.isp_out_high.request_buffers(self.isp_out_buffer_num, V4L2_MEMORY.MMAP)
        self.isp_out_metadata_buffer_num = self.isp_out_metadata.request_buffers(
            self.isp_out_metadata_buffer_num, V4L2_MEMORY.MMAP
        )

    def unicam2isp(self) -> None:
        buffer = self.unicam.dequeue_buffer_nonblocking(v4l2_memory=V4L2_MEMORY.DMABUF)
        if buffer is None:
            return
        self.isp_in.queue_buffer(buffer.buf.index)

    def isp2unicam(self) -> None:
        buffer = self.isp_in.dequeue_buffer_nonblocking(v4l2_memory=V4L2_MEMORY.DMABUF)
        if buffer is None:
            return
        self.unicam.queue_buffer(buffer.buf.index)

    def produce_image_from_isp(self) -> None:
        buffer = self.isp_out_high.dequeue_buffer_nonblocking(v4l2_memory=V4L2_MEMORY.MMAP)
        if buffer is None:
            return

        dst = self.converter.convert(buffer, self.isp_out_high.fmt, self.output_fmt)
        frame = Frame(dst)
        self._outlet(frame)
        self.isp_out_high.queue_buffer(buffer.buf.index)

    def calc_lux(self, isp_stats: bcm2835_isp_stats) -> None:
        current_aperture = self.aperture
        current_gain = self.gain
        current_shutter_speed = self.shutter_speed

        hist_sum = 0
        hist_num = 0
        hist = isp_stats.hist[0].g_hist
        for i in range(NUM_HISTOGRAM_BINS):
            hist_sum += hist[i] * i
            hist_num += hist[i]
        current_Y = float(hist_sum) / float(hist_num) + 0.5
        gain_ratio = self.reference_gain / current_gain
        shutter_speed_ratio = self.reference_shutter_speed / current_shutter_speed
        aperture_ratio = self.reference_aperture / current_aperture
        Y_ratio = current_Y * (65536.0 / NUM_HISTOGRAM_BINS) / self.reference_Y
        estimated_lux = shutter_speed_ratio * gain_ratio * aperture_ratio * aperture_ratio * Y_ratio * self.reference_lux

        self.lux = estimated_lux

    def get_cal_table(self, ct: float, calibrations: List[Dict[str, Any]]) -> List[float]:
        if len(calibrations) == 0:
            return [1.0] * AWB_REGIONS
        elif ct <= calibrations[0]["ct"]:
            return calibrations[0]["table"].copy()  # type: ignore
        elif calibrations[-1]["ct"] <= ct:
            return calibrations[-1]["table"].copy()  # type: ignore
        else:
            idx = 0
            while calibrations[idx + 1]["ct"] < ct:
                idx += 1

            ct0 = calibrations[idx]["ct"]
            ct1 = calibrations[idx + 1]["ct"]
            calibration0 = calibrations[idx]["table"]
            calibration1 = calibrations[idx + 1]["table"]
            return [(x0 * (ct1 - ct) + x1 * (ct - ct0)) / (ct1 - ct0) for (x0, x1) in zip(calibration0, calibration1)]

    # simplified version of [alsc algorithm in libcamera](https://github.com/raspberrypi/libcamera/blob/3fad116f89e0d3497567043cbf6d8c49f1c102db/src/ipa/raspberrypi/controller/rpi/alsc.cpp#L772) # noqa: E501, B950
    # with the following omitted
    #  - dynamic lens shading table calculation based on estimated colour templature
    #  - "Adaptive ALSC Algorithm"
    def alsc(self) -> None:
        ct = self.color_temperature

        cal_table_r = self.get_cal_table(ct, self.calibrations_Cr)
        cal_table_b = self.get_cal_table(ct, self.calibrations_Cb)

        def normalize(table: List[float]) -> List[float]:
            m = min(table)
            return [x / m for x in table]

        cal_table_r = self.resample_cal_table(cal_table_r, self.camera_mode)
        cal_table_b = self.resample_cal_table(cal_table_b, self.camera_mode)
        luminace_table = self.resample_cal_table(self.luminace_lut, self.camera_mode)

        self.ls_table_r = normalize(
            [r * ((lut - 1) * self.luminace_strength + 1) for (r, lut) in zip(cal_table_r, luminace_table)]
        )
        self.ls_table_g = normalize([1.0 * ((lut - 1) * self.luminace_strength + 1) for lut in luminace_table])
        self.ls_table_b = normalize(
            [b * ((lut - 1) * self.luminace_strength + 1) for (b, lut) in zip(cal_table_b, luminace_table)]
        )

        self.apply_ls_tables()

    # correspond to [resampleCalTable](https://github.com/raspberrypi/libcamera/blob/3fad116f89e0d3497567043cbf6d8c49f1c102db/src/ipa/raspberrypi/controller/rpi/alsc.cpp#L463) # noqa: E501, B950
    def resample_cal_table(self, src: List[float], camera_mode: CameraMode) -> List[float]:
        if self.sensor_name == "imx708":
            _sensor_size = V3_SENSOR_SIZE
        elif self.sensor_name == "imx219":
            _sensor_size = V2_SENSOR_SIZE
        else:
            _sensor_size = V1_SENSOR_SIZE
        assert len(src) == LS_TABLE_W * LS_TABLE_H
        new_table: List[float] = []

        x_lo: List[int] = [0] * LS_TABLE_W
        x_hi: List[int] = [0] * LS_TABLE_W
        xf: List[float] = [0] * LS_TABLE_W
        scale_x = _sensor_size[0] / (camera_mode.size[0] * camera_mode.scale[0])
        offset_x = (camera_mode.crop[0] / _sensor_size[0]) * LS_TABLE_W
        x = (0.5 / scale_x) + offset_x - 0.5
        x_inc = 1 / scale_x
        for i in range(0, LS_TABLE_W):
            x_lo[i] = floor(x)
            xf[i] = x - x_lo[i]
            x_hi[i] = min(x_lo[i] + 1, LS_TABLE_W - 1)
            x_lo[i] = max(x_lo[i], 0)
            x += x_inc

        scale_y = _sensor_size[1] / (camera_mode.size[1] * camera_mode.scale[1])
        offset_y = (camera_mode.crop[1] / _sensor_size[1]) * LS_TABLE_H
        y = (0.5 / scale_y) + offset_y - 0.5
        y_inc = 1 / scale_y
        for _ in range(0, LS_TABLE_H):
            y_lo = floor(y)
            yf = y - y_lo
            y_hi = min(y_lo + 1, LS_TABLE_H - 1)
            y_lo = max(y_lo, 0)
            row_above = src[y_lo * LS_TABLE_W : (y_lo + 1) * LS_TABLE_W]
            row_below = src[y_hi * LS_TABLE_W : (y_hi + 1) * LS_TABLE_W]
            for i in range(0, LS_TABLE_W):
                above = row_above[x_lo[i]] * (1 - xf[i]) + row_above[x_hi[i]] * xf[i]
                below = row_below[x_lo[i]] * (1 - xf[i]) + row_below[x_hi[i]] * xf[i]
                new_table.append(above * (1 - yf) + below * yf)

            y += y_inc

        assert len(new_table) == LS_TABLE_W * LS_TABLE_H
        return new_table

    # correspond to [applyLS](https://github.com/raspberrypi/libcamera/blob/1c4c323e5d684b57898c083ed2f1af313bf6a98d/src/ipa/raspberrypi/raspberrypi.cpp#L1343) # noqa: E501, B950
    def apply_ls_tables(self) -> None:
        assert len(self.ls_table_b) == LS_TABLE_W * LS_TABLE_H
        assert len(self.ls_table_r) == LS_TABLE_W * LS_TABLE_H
        assert len(self.ls_table_g) == LS_TABLE_W * LS_TABLE_H
        cell_size_candidate = [16, 32, 64, 128, 256]
        for i in range(0, len(cell_size_candidate)):
            cell_size = cell_size_candidate[i]
            w = (self.unicam_width + cell_size - 1) // cell_size
            h = (self.unicam_height + cell_size - 1) // cell_size
            if w < 64 and h <= 48:
                break

        w += 1
        h += 1

        self.populate_ls_table(self.ls_table_r, w, h, self.ls_table_mm, 0)
        self.populate_ls_table(self.ls_table_g, w, h, self.ls_table_mm, 1 * (2 * w * h))
        self.ls_table_mm[2 * (2 * w * h) : 3 * (2 * w * h)] = memoryview(self.ls_table_mm)[1 * (2 * w * h) : 2 * (2 * w * h)]
        self.populate_ls_table(self.ls_table_b, w, h, self.ls_table_mm, 3 * (2 * w * h))

        ls = bcm2835_isp_lens_shading()
        ls.enabled = 1
        ls.grid_cell_size = cell_size
        ls.grid_width = w
        ls.grid_stride = w
        ls.grid_height = h
        ls.dmabuf = self.ls_table_dma_heap_fd
        ls.ref_transform = 0
        ls.corner_sampled = 1
        ls.gain_format = bcm2835_isp_gain_format.GAIN_FORMAT_U4P10

        ls_ctrl = v4l2_ext_control()
        ls_ctrl.id = V4L2_CID.USER_BCM2835_ISP_LENS_SHADING
        ls_ctrl.size = sizeof(bcm2835_isp_lens_shading)
        ls_ctrl.ptr = cast(pointer(ls), c_void_p)
        self.isp_in.set_ext_controls([ls_ctrl])

    # correspond to [resampleTable](https://github.com/raspberrypi/libcamera/blob/1c4c323e5d684b57898c083ed2f1af313bf6a98d/src/ipa/raspberrypi/raspberrypi.cpp#L1403) # noqa: E501, B950
    def populate_ls_table(self, src: List[float], dst_w: int, dst_h: int, ls_table: mmap.mmap, offset: int) -> None:
        assert len(src) == LS_TABLE_W * LS_TABLE_H
        x_lo: List[int] = [0] * dst_w
        xf: List[float] = [0.0] * dst_w
        x_hi: List[int] = [0] * dst_w

        x = -0.5
        x_inc = LS_TABLE_W / (dst_w - 1)
        for i in range(0, dst_w):
            x_lo[i] = floor(x)
            xf[i] = x - x_lo[i]
            x_hi[i] = min(x_lo[i] + 1, LS_TABLE_W - 1)
            x_lo[i] = max(x_lo[i], 0)
            x += x_inc

        ls_table_idx = offset
        y = -0.5
        y_inc = LS_TABLE_H / (dst_h - 1)
        for _ in range(0, dst_h):
            y_lo = floor(y)
            yf = y - y_lo
            y_hi = min(y_lo + 1, LS_TABLE_H - 1)
            y_lo = max(y_lo, 0)
            row_above = src[y_lo * LS_TABLE_W : (y_lo + 1) * LS_TABLE_W]
            row_below = src[y_hi * LS_TABLE_W : (y_hi + 1) * LS_TABLE_W]
            for i in range(0, dst_w):
                above = row_above[x_lo[i]] * (1 - xf[i]) + row_above[x_hi[i]] * xf[i]
                below = row_below[x_lo[i]] * (1 - xf[i]) + row_below[x_hi[i]] * xf[i]
                result = floor(1024 * (above * (1 - yf) + below * yf) + 0.5)
                result = min(result, 16383)
                result_as_bytes = bytes(c_int16(result))  # type: ignore
                assert len(result_as_bytes) == 2  # 16 bits
                ls_table[ls_table_idx : ls_table_idx + 2] = result_as_bytes
                ls_table_idx += 2

            y += y_inc

        assert ls_table_idx == offset + (2 * dst_w * dst_h)

    def calculate_y(self, stats: bcm2835_isp_stats, additional_gain: float) -> float:
        PIPELINE_BITS = 13  # https://github.com/kbingham/libcamera/blob/f995ff25a3326db90513d1fa936815653f7cade0/src/ipa/raspberrypi/controller/rpi/agc.cpp#L31 # noqa: E501, B950
        r_sum = 0
        g_sum = 0
        b_sum = 0
        pixel_sum = 0
        for region in stats.agc_stats:
            counted = region.counted
            r_sum += min(region.r_sum * additional_gain, ((1 << PIPELINE_BITS) - 1) * counted)
            b_sum += min(region.b_sum * additional_gain, ((1 << PIPELINE_BITS) - 1) * counted)
            g_sum += min(region.g_sum * additional_gain, ((1 << PIPELINE_BITS) - 1) * counted)
            pixel_sum += counted

        if pixel_sum == 0:
            return 0

        y_sum = r_sum * self.gain_r * 0.299 + b_sum * self.gain_b * 0.144 + g_sum * 0.587

        return y_sum / pixel_sum / (1 << PIPELINE_BITS)

    def agc(self, stats: bcm2835_isp_stats) -> None:
        # compute addtional gain to acheive target_Y
        # https://github.com/raspberrypi/libcamera/blob/1c4c323e5d684b57898c083ed2f1af313bf6a98d/src/ipa/raspberrypi/controller/rpi/agc.cpp#L572-L582 # noqa: E501, B950
        gain = 1.0
        for _ in range(8):
            initial_Y = self.calculate_y(stats, gain)
            extra_gain = min(10.0, self.target_Y / (initial_Y + 0.001))
            gain *= extra_gain
            if extra_gain < 1.01:
                break

        max_exposure = self.shutters[-1] * self.gains[-1]
        target_exposure = min(self.exposure * gain, max_exposure)

        # decompose target_exposure to analogue_gain and shutter_time
        # TODO: Also decompose to digital gain.
        analogue_gain = self.gains[0]
        shutter_time = self.shutters[0]
        if shutter_time * analogue_gain < target_exposure:
            for stage in range(1, len(self.gains)):
                max_analogue_gain = self.gains[stage]
                max_shutter_time = self.shutters[stage]
                # fix gain, increase shutter time
                if max_shutter_time * analogue_gain >= target_exposure:
                    shutter_time = target_exposure / analogue_gain
                    break
                shutter_time = max_shutter_time

                # fix shutter time, increase gain
                if shutter_time * max_analogue_gain >= target_exposure:
                    analogue_gain = target_exposure / shutter_time
                    break
                analogue_gain = max_analogue_gain

        # may need flicker avoidance here. ref. https://github.com/kbingham/libcamera/blob/d7415bc4e46fe8aa25a495c79516d9882a35a5aa/src/ipa/raspberrypi/controller/rpi/agc.cpp#L724 # noqa: E501, B950

        self.shutter_speed = shutter_time
        self.gain = analogue_gain
        self.exposure = shutter_time * analogue_gain
        self.set_unicam_exposure(analogue_gain, shutter_time)

    def awb(self, stats: bcm2835_isp_stats) -> None:
        sum_r = 0
        sum_b = 0
        sum_g = 0
        # len(stats.awb_stats) == 192
        for region in stats.awb_stats:
            sum_r += region.r_sum
            sum_b += region.b_sum
            sum_g += region.g_sum
        self.gain_r = sum_g / (sum_r + 1)
        self.gain_b = sum_g / (sum_b + 1)
        red_balance_ctrl = v4l2_ext_control()
        red_balance_ctrl.id = V4L2_CID.RED_BALANCE
        red_balance_ctrl.value64 = int(self.gain_r * 1000)
        blue_balance_ctrl = v4l2_ext_control()
        blue_balance_ctrl.id = V4L2_CID.BLUE_BALANCE
        blue_balance_ctrl.value64 = int(self.gain_b * 1000)
        self.isp_in.set_ext_controls([red_balance_ctrl, blue_balance_ctrl])

    # linearly find appropriate range, this might be inefficient
    def find_span(self, gamma_curve: List[Tuple[float, float]], x: float) -> int:
        last_span = len(gamma_curve) - 2
        for i in range(0, last_span + 1):
            if gamma_curve[i][0] <= x < gamma_curve[i + 1][0]:
                return i
        return last_span

    def eval_gamma_curve(self, gamma_curve: List[Tuple[float, float]], x: float) -> float:
        span = self.find_span(gamma_curve, x)
        return gamma_curve[span][1] + (x - gamma_curve[span][0]) * (gamma_curve[span + 1][1] - gamma_curve[span][1]) / (
            gamma_curve[span + 1][0] - gamma_curve[span][0]
        )

    # gamma2(gamma1(x)) with care of boundary values
    def compose_gamma_curve(
        self,
        one: List[Tuple[float, float]],
        other: List[Tuple[float, float]],
        eps: float = 1e-6,
    ) -> List[Tuple[float, float]]:
        this_x = one[0][0]
        this_y = one[0][1]
        this_span = 0
        other_span = self.find_span(other, this_y)
        result = [(this_y, self.eval_gamma_curve(other, this_y))]
        while this_span != len(one) - 1:
            dx = one[this_span + 1][0] - one[this_span][0]
            dy = one[this_span + 1][1] - one[this_span][1]
            if abs(dy) > eps and other_span + 1 < len(other) and one[this_span + 1][1] >= other[other_span + 1][0] + eps:
                # next control point in result will be where this
                # function's y reaches the next span in other
                this_x = one[this_span][0] + (other[other_span + 1][0] - one[this_span][1]) * dx / dy
                other_span += 1
                this_y = other[other_span][0]
            elif abs(dy) > eps and other_span > 0 and one[this_span + 1][1] <= other[other_span - 1][0] - eps:
                this_x = one[this_span][0] + (other[other_span + 1][0] - one[this_span][1]) * dx / dy
                other_span -= 1
                this_y = other[other_span][0]
            else:
                this_span += 1
                this_x = one[this_span][0]
                this_y = one[this_span][1]
            if result[-1][0] + eps < this_x:
                result.append((this_x, self.eval_gamma_curve(other, this_y)))
        return result

    def histogram_cumulative(self, histogram: List[int]) -> List[int]:
        cumulative = [0]
        for i in range(0, len(histogram)):
            cumulative.append(cumulative[-1] + histogram[i])
        return cumulative

    def cumulative_quantile(self, cumulative: List[int], q: float, first: int = -1, last: int = -1) -> float:
        if first == -1:
            first = 0
        if last == -1:
            last = len(cumulative) - 2
        assert first <= last
        items = int(q * cumulative[-1])
        while first < last:
            middle = (first + last) // 2
            if cumulative[middle + 1] > items:
                last = middle
            else:
                first = middle + 1
        assert items >= cumulative[first] and items <= cumulative[last + 1]
        frac = (
            0
            if cumulative[first + 1] == cumulative[first]
            else (items - cumulative[first]) / (cumulative[first + 1] - cumulative[first])
        )
        return first + frac

    def compute_stretch_curve(self, histogram: List[int]) -> List[Tuple[float, float]]:
        enhance = [(0.0, 0.0)]
        eps = 1e-6

        # If the start of the histogram is rather empty, try to pull it down a
        # bit.
        cumulative = self.histogram_cumulative(histogram)
        hist_lo = self.cumulative_quantile(cumulative, self.lo_histogram) * (65536 / NUM_HISTOGRAM_BINS)
        level_lo = self.lo_level * 65536
        hist_lo = max(level_lo, min(65535, min(hist_lo, level_lo + self.lo_max)))
        if enhance[-1][0] + eps < hist_lo:
            enhance.append((hist_lo, level_lo))

        # Keep the mid-point (median) in the same place, though, to limit the
        # apparent amount of global brightness shift.
        mid = self.cumulative_quantile(cumulative, 0.5) * (65536 / NUM_HISTOGRAM_BINS)
        if enhance[-1][0] + eps < mid:
            enhance.append((mid, mid))

        # If the top to the histogram is empty, try to pull the pixel values
        # there up.
        hist_hi = self.cumulative_quantile(cumulative, self.hi_histogram) * (65536 / NUM_HISTOGRAM_BINS)
        level_hi = self.hi_level * 65536
        hist_hi = min(level_hi, max(0.0, max(hist_hi, level_hi - self.hi_max)))
        if enhance[-1][0] + eps < hist_hi:
            enhance.append((hist_hi, level_hi))
        if enhance[-1][0] + eps < 65535:
            enhance.append((65535, 65535))
        return enhance

    def fill_in_contrast_status(self, gm: bcm2835_isp_gamma, gamma_curve: List[Tuple[float, float]]) -> None:
        gm.enabled = 1
        for i in range(0, CONTRAST_NUM_POINTS - 1):
            if i < 16:
                x = i * 1024
            elif i < 24:
                x = (i - 16) * 2048 + 16384
            else:
                x = (i - 24) * 4096 + 32768
            gm.x[i] = x
            gm.y[i] = int(min(65535.0, self.eval_gamma_curve(gamma_curve, x)))

        gm.x[CONTRAST_NUM_POINTS - 1] = 65535
        gm.y[CONTRAST_NUM_POINTS - 1] = 65535

    def contrast_control(self, isp_stats: bcm2835_isp_stats) -> None:
        histogram = isp_stats.hist[0].g_hist
        gamma_curve = self.gamma_curve
        if self.ce_enable:
            if self.lo_max != 0 or self.hi_max != 0:
                gamma_curve = self.compose_gamma_curve(self.compute_stretch_curve(histogram), gamma_curve)
        if self.brightness != 0 or self.contrast != 1.0:
            gamma_curve = [
                (
                    x,
                    max(
                        0.0,
                        min(
                            65535.0,
                            (y - 32768) * self.contrast + 32768 + self.brightness,
                        ),
                    ),
                )
                for (x, y) in gamma_curve
            ]
        gm = bcm2835_isp_gamma()
        self.fill_in_contrast_status(gm, gamma_curve)
        gamma = v4l2_ext_control()
        gamma.id = V4L2_CID.USER_BCM2835_ISP_GAMMA
        gamma.size = sizeof(bcm2835_isp_gamma)
        gamma.ptr = cast(pointer(gm), c_void_p)
        self.isp_in.set_ext_controls([gamma])

    def adjust_setting_from_isp(self) -> None:
        buffer = self.isp_out_metadata.dequeue_buffer_nonblocking(v4l2_memory=V4L2_MEMORY.MMAP)
        if buffer is None:
            return

        stats: bcm2835_isp_stats = cast(buffer.mapped_buf, POINTER(bcm2835_isp_stats)).contents
        self.calc_lux(stats)
        if self.do_agc:
            if self.agc_interval_count < AGC_INTERVAL:
                self.agc_interval_count += 1
            else:
                self.agc_interval_count = 0
                self.agc(stats)

        if self.do_awb:
            self.awb(stats)

        if self.do_contrast:
            self.contrast_control(stats)

        self.isp_out_metadata.queue_buffer(buffer.buf.index)

    def run(self) -> None:
        self.unicam.queue_all_buffers()
        self.isp_out_high.queue_all_buffers()
        self.isp_out_metadata.queue_all_buffers()

        self.unicam.start_streaming()
        self.isp_in.start_streaming()
        self.isp_out_high.start_streaming()
        self.isp_out_metadata.start_streaming()

        while self._is_running():
            rlist, wlist, _ = select.select(
                [
                    self.unicam.device_fd,
                    self.isp_out_high.device_fd,
                    self.isp_out_metadata.device_fd,
                ],
                [self.isp_in.device_fd],
                [],
                self.timeout,
            )

            if len(rlist) == 0 and len(wlist) == 0:
                raise RuntimeError("Capture timeout")

            for r in rlist:
                if r == self.unicam.device_fd:
                    self.unicam2isp()
                elif r == self.isp_out_high.device_fd:
                    self.produce_image_from_isp()
                elif r == self.isp_out_metadata.device_fd:
                    self.adjust_setting_from_isp()
            for w in wlist:
                if w == self.isp_in.device_fd:
                    self.isp2unicam()
