#!/usr/bin/python3
import argparse
import actfw_core
from actfw_core.autofocus import AfMode, AfSpeed, AutoFocuserIMX708
from actfw_core.capture import V4LCameraCapture
from actfw_core.unicam_isp_capture import UnicamIspCapture
from actfw_core.system import find_csi_camera_device, find_usb_camera_device
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
            "hflip": False,
            "vflip": False,
            "display": False,
            "capture_framerate": 8,
            "use_usb_camera": False,
            "use_v3_camera": False,
            "stream_name": "",
            "region_name": "",
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            'afmode': 'continuous',
            'afvalue': 420,
            'aftimer': 10,
        }
    )
    print(settings["afmode"])

    # CommandServer (for `Take Photo` command)
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)
    use_usb_camera = settings["use_usb_camera"]

    # pi camera v3 のときのみ有効
    auto_focuser = None
    try:
        if use_usb_camera:
            device = find_usb_camera_device()
            cap = V4LCameraCapture(
                device,
                size=(CAPTURE_WIDTH, CAPTURE_HEIGHT),
                framerate=int(settings["capture_framerate"]),
                format_selector=V4LCameraCapture.FormatSelector.PROPER
            )
            def config(video):
                # ignore result (requires camera capability)
                video.set_horizontal_flip(settings["hflip"])
                if settings['vflip']:
                    video.set_rotation(180)
            cap.configure(config)
        elif settings["use_v3_camera"]:
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

    preview_window = None
    if settings["display"]:
        with Display() as display:
            preview_area = (0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT)
            with display.open_window(
                preview_area, (CAPTURE_WIDTH, CAPTURE_HEIGHT), 16
            ) as preview_window_:
                preview_window = preview_window_

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
    pres = Presenter(
        preview_window,
        cmd,
        kvssink,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video capture application")
    main(parser.parse_args())
