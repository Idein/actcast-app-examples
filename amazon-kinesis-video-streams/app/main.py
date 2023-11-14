#!/usr/bin/python3
import argparse
import subprocess
import os
import actfw_core
from actfw_core.capture import V4LCameraCapture
from actfw_raspberrypi.vc4 import Display

# from configuration import *
from kvs import KinesisVideoStream
from presenter import Presenter
from preprocess import Preprocess
from consts import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    CAPTURE_HEIGHT,
    CAPTURE_WIDTH,
)


class ActSettingsError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        err_msg = (
            "This error may be due to poor camera performance or a connection problem. "
            "Please review the camera you are using or the act settings of the camera, "
            "for example, camera resolution, and capture frame rate."
        )

        return f"{self.msg}. {err_msg}"


def main(_args):

    # Actcast application
    app = actfw_core.Application()

    # Load act setting
    settings = app.get_settings(
        {
            "camera_rotation": "0",
            "hflip": False,
            "display": True,
            "exposure_time": 0,
            "capture_framerate": 8,
            "stream_name": "",
            "region_name": "",
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
        }
    )
    if settings["exposure_time"] <= 0:
        settings["exposure_time"] = None

    # CommandServer (for `Take Photo` command)
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)

    # Capture task
    format_selector = V4LCameraCapture.FormatSelector.DEFAULT

    try:
        cap = V4LCameraCapture(
            "/dev/video0",
            (CAPTURE_WIDTH, CAPTURE_HEIGHT),
            settings["capture_framerate"],
            format_selector=format_selector,
        )
    except RuntimeError as e:
        raise ActSettingsError(str(e))
    except OSError as e:
        if e.errno == 16:
            raise ActSettingsError(str(e))
        else:
            raise

    capture_size = cap.capture_size()

    def config(video):
        # ignore result (requires camera capability)
        video.set_rotation(int(settings["camera_rotation"]))
        # ignore result (requires camera capability)
        video.set_horizontal_flip(settings["hflip"])
        video.set_exposure_time(settings["exposure_time"])

    cap.configure(config)
    app.register_task(cap)

    # Preprocess task
    pre = Preprocess(capture_size)
    app.register_task(pre)

    def run(preview_window=None):
        if settings["stream_name"] == "":
            kvssink = None
        else:
            # print("Kinesis Video Stream is enabled.")
            kvssink = KinesisVideoStream(
                (CAPTURE_WIDTH, CAPTURE_HEIGHT),
                settings["stream_name"],
                settings["region_name"],
                settings["aws_access_key_id"],
                settings["aws_secret_access_key"],
            )
            kvssink.play()
            app.register_task(kvssink)

        # Presenter task
        pres = Presenter(preview_window, cmd, kvssink)
        app.register_task(pres)

        # Make task connection
        cap.connect(pre)  # from `cap` to `pre`
        pre.connect(pres)  # from `pre` to `pres

        # Start application
        app.run()

    if settings["display"]:
        with Display() as display:
            preview_area = (0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT)
            with display.open_window(
                preview_area, (CAPTURE_WIDTH, CAPTURE_HEIGHT), 2000
            ) as preview_window:
                run(preview_window)
    else:
        run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video capture application")
    main(parser.parse_args())
