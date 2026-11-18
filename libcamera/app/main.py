#!/usr/bin/env python3
# type: ignore
import os
import time
from typing import Tuple

import actfw_core
import libcamera as libcam
import numpy as np
from actfw_core.application import Application
from actfw_core.capture import Frame
from actfw_core.command_server import CommandServer
from actfw_core.libcamera_capture import LibcameraCapture, ScalerCrop, SensorConfig
from actfw_core.task import Consumer, Pipe
from actfw_raspberrypi.vc4.drm import Display
from PIL import Image


class FPSCounter(Pipe):
    def __init__(self, moving_average=30, fps_key="fps"):
        super().__init__()

        self.fps_key = fps_key
        self.moving_average = moving_average
        self.prev_time = time.time()
        self.dtimes = []

    def update_fps(self):
        cur_time = time.time()
        dtime = cur_time - self.prev_time
        self.prev_time = cur_time
        self.dtimes.append(dtime)
        if len(self.dtimes) > self.moving_average:
            self.dtimes.pop(0)
        return self.get_fps()

    def get_fps(self):
        if len(self.dtimes) == 0:
            return None
        else:
            return len(self.dtimes) / sum(self.dtimes)

    def proc(self, i):
        fps = self.update_fps()
        actfw_core.notify([{'fps': f"{fps:.2f}"}])
        if isinstance(i, dict):
            i[self.fps_key] = fps
            return i
        else:
            res = dict()
            res[self.fps_key] = fps
            res["result"] = i
            return res

# capture image size
(CAPTURE_WIDTH, CAPTURE_HEIGHT) = (640, 480)

# display area size
(DISPLAY_WIDTH, DISPLAY_HEIGHT) = (640, 480)


class Converter(Pipe):
    def __init__(self, capture_size: Tuple[int, int]) -> None:
        super(Converter, self).__init__()
        self.capture_size = capture_size

    def proc(self, frame: Frame) -> Image.Image:
        rgb_image = Image.frombuffer("RGB", self.capture_size, frame.getvalue(), "raw", "RGB")
        return rgb_image


class Presenter(Consumer):
    def __init__(self, preview_window, cmd: CommandServer) -> None:
        super(Presenter, self).__init__()
        self.preview_window = preview_window
        self.cmd = cmd

    def proc(self, i) -> None:
        image = i["result"]
        # update `Take Photo` image
        self.cmd.update_image(image)
        actfw_core.heartbeat()
        if self.preview_window is not None:
            self.preview_window.blit(np.asarray(image).tobytes())
            self.preview_window.update()


def run(app: Application, preview_window=None) -> None:
    cmd = actfw_core.CommandServer()
    camera_options = {}
    camera = libcam.CameraManager.singleton().cameras[0]
    if "imx219" in str(camera.id).lower():
        capture_width, capture_height = (CAPTURE_WIDTH, CAPTURE_HEIGHT)
        sensor_width, sensor_height, scale, offset_x, offset_y = 1640, 1232, 2, 0, 0
        crop_scale = min(sensor_width / capture_width, sensor_height / capture_height)
        crop_width, crop_height = round(capture_width * crop_scale), round(capture_height * crop_scale)
        crop_x, crop_y = int((sensor_width - crop_width) / 2), int((sensor_height - crop_height) / 2)
        # OS3と画角を合わせるため、IMX219のセンサーモードを明示する。
        sensor_config = SensorConfig(bit_depth=10, output_size=(sensor_width, sensor_height))
        camera_options.update(sensor_config=sensor_config, scaler_crop=ScalerCrop(
            x=offset_x + crop_x * scale, y=offset_y + crop_y * scale,
            width=crop_width * scale, height=crop_height * scale))
    else:
        print(f"WARNING: Camera {camera.id!r} is not IMX219; use automatic sensor mode and crop.", flush=True)
    cap = LibcameraCapture((CAPTURE_WIDTH, CAPTURE_HEIGHT), libcam.PixelFormat("BGR888"), **camera_options)

    conv = Converter((CAPTURE_WIDTH, CAPTURE_HEIGHT))
    fps = FPSCounter()
    pres = Presenter(preview_window, cmd)

    app.register_task(cmd)
    app.register_task(cap)
    app.register_task(conv)
    app.register_task(fps)
    app.register_task(pres)

    cap.connect(conv)
    conv.connect(fps)
    fps.connect(pres)

    app.run()


def main() -> None:
    app = actfw_core.Application()

    # Load act setting
    settings = app.get_settings({'display': False, 'libcamera_log_levels': 'FATAL'})
    os.environ['LIBCAMERA_LOG_LEVELS'] = settings['libcamera_log_levels']

    if settings['display']:
        with Display() as display:
            preview_area = (0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT)
            capture_size = (CAPTURE_WIDTH, CAPTURE_HEIGHT)
            layer = 16
            with display.open_window(preview_area, capture_size, layer) as preview_window:
                run(app, preview_window)
    else:
        run(app)


if __name__ == "__main__":
    main()
