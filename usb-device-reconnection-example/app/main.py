#!/usr/bin/python3
import numpy as np
from PIL import Image
from PIL.Image import Image as PIL_Image
import actfw_core
import subprocess
import os
import time
from actfw_core.capture import Frame
from actfw_core.task import Consumer, Producer
from actfw_core.system import find_usb_camera_device
from actfw_raspberrypi.vc4 import Display


# capture image size
(CAPTURE_WIDTH, CAPTURE_HEIGHT) = (320, 240)

# display area size
(DISPLAY_WIDTH, DISPLAY_HEIGHT) = (640, 480)


class FfmpegCapture(Producer[PIL_Image]):
    def __init__(self, device_path):
        super().__init__()
        self.device_path = device_path
    
    def run(self):
        while self._is_running():
            try:
                # Run ffmpeg command to capture an image from the USB camera
                cmd = f"ffmpeg -i {self.device_path} -f image2 -s {CAPTURE_WIDTH}x{CAPTURE_HEIGHT} -vframes 1 /tmp/image.jpg -y"
                subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE)
                
                # Check if the image file was created
                if os.path.exists("/tmp/image.jpg"):
                    # Read the captured image
                    img = Image.open("/tmp/image.jpg")
                    
                    self._outlet(img)
                    
                    # Remove the temporary image file
                    os.remove("/tmp/image.jpg")
                
                # Add a small delay to avoid high CPU usage
                time.sleep(1)
                
            except Exception as e:
                print(f"Error capturing image: {e}", flush=True)
                time.sleep(1)  # Wait a bit before retrying

class Presenter(Consumer):
    """Display grayscale image on preview window and take photo view"""

    def __init__(self, preview_window, cmd):
        super(Presenter, self).__init__()
        self.preview_window = preview_window
        self.cmd = cmd

    def proc(self, image):
        # update `Take Photo` image
        self.cmd.update_image(image)

        # if preview window is available, display grayscale image
        if self.preview_window is not None:
            self.preview_window.blit(np.asarray(image).tobytes())
            self.preview_window.update()

        actfw_core.heartbeat()


def run(app, preview_window=None):
    # CommandServer (for `Take Photo` command)
    cmd = actfw_core.CommandServer()
    app.register_task(cmd)

    # register capture task
    device = find_usb_camera_device()
    cap = FfmpegCapture(device)
    app.register_task(cap)

    # register converter task

    # register presenter task
    pres = Presenter(preview_window, cmd)
    app.register_task(pres)

    # make task connection
    cap.connect(pres)

    # Start application
    app.run()


def main():
    # Actcast application
    app = actfw_core.Application()

    # Load act setting
    settings = app.get_settings({"display": False})

    if settings["display"]:
        with Display() as display:
            preview_area = (0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT)
            capture_size = (CAPTURE_WIDTH, CAPTURE_HEIGHT)
            layer = 16
            with display.open_window(
                preview_area, capture_size, layer
            ) as preview_window:
                run(app, preview_window)
    else:
        run(app)


if __name__ == "__main__":
    main()
