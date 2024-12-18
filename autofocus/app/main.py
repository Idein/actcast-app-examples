#!/usr/bin/python3
import argparse
import actfw_core
from actfw_core.autofocus import AfMode, AfSpeed, AutoFocuserIMX708
from actfw_core.capture import V4LCameraCapture
from actfw_core.unicam_isp_capture import UnicamIspCapture
from actfw_core.system import find_csi_camera_device, find_usb_camera_device
from actfw_raspberrypi.vc4 import Display

from presenter import Presenter
from preprocess import Preprocess
from consts import (
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
            "hflip": False,
            "vflip": False,
            "display": False,
            "capture_framerate": 8,
            "use_v3_camera": False,
            "afmode": "continuous",
            "afvalue": 420,
            "aftimer": 10,
        }
    )

    # CommandServer (for `Take Photo` command)
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)

    # pi camera v3 のときのみ有効
    auto_focuser = None
    try:
        if settings["use_v3_camera"]:
            if settings["afmode"] == "continuous":
                mode = AfMode.AfModeContinuous
            elif settings["afmode"] == "timer":
                mode = AfMode.AfModeAuto
            elif settings["afmode"] == "manual":
                mode = AfMode.AfModeManual
            else:
                mode = AfMode.AfModeContinuous
            auto_focuser = AutoFocuserIMX708(afmode=mode, afspeed=AfSpeed.AfSpeedNormal)
            device = find_csi_camera_device()
            cap = UnicamIspCapture(
                unicam=device,
                size=(CAPTURE_WIDTH, CAPTURE_HEIGHT),
                framerate=int(settings["capture_framerate"]),
                hflip=settings["hflip"],
                vflip=settings["vflip"],
                auto_focuser=auto_focuser,
            )
        else:
            device = find_csi_camera_device()
            cap = UnicamIspCapture(
                unicam=device,
                size=(CAPTURE_WIDTH, CAPTURE_HEIGHT),
                framerate=int(settings["capture_framerate"]),
                hflip=settings["hflip"],
                vflip=settings["vflip"],
            )

    except RuntimeError as e:
        raise ActSettingsError(str(e))
    except OSError as e:
        if e.errno == 16:
            raise ActSettingsError(str(e))
        else:
            raise

    capture_size = cap.capture_size()

    app.register_task(cap)

    # Preprocess task
    pre = Preprocess(capture_size)
    app.register_task(pre)

    def run(preview_window=None):
        # Presenter task
        pres = Presenter(
            preview_window,
            cmd,
            auto_focuser=auto_focuser,
            afmode=settings["afmode"],
            aftimer=settings["aftimer"],
            afvalue=settings["afvalue"],
        )
        app.register_task(pres)

        # Make task connection
        cap.connect(pre)  # from `cap` to `pre`
        pre.connect(pres)  # from `pre` to `pres

        # Start application
        app.run()

    if settings["display"]:
        with Display() as display:
            actual_display_width, actual_display_height = display.size()
            scale = min(
                float(actual_display_width / CAPTURE_WIDTH),
                float(actual_display_height / CAPTURE_WIDTH),
            )
            width = int(scale * CAPTURE_WIDTH)
            height = int(scale * CAPTURE_HEIGHT)
            left = (actual_display_width - width) // 2
            upper = (actual_display_height - height) // 2
            preview_area = (left, upper, width, height)
            with display.open_window(
                preview_area, (CAPTURE_WIDTH, CAPTURE_HEIGHT), 16
            ) as preview_window:
                run(preview_window)
    else:
        run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video capture application")
    main(parser.parse_args())
