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
from actfw_core.libcamera_capture import LibcameraCapture
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
    # framerateを指定しないとFPSが8-30FPSの間で変動するので注意
    cap = LibcameraCapture((CAPTURE_WIDTH, CAPTURE_HEIGHT), libcam.PixelFormat("BGR888"), framerate=30)

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
