# type: ignore
# flake8: noqa

from actfw_core.system import EnvironmentVariableNotSet, get_actcast_firmware_type


class Display(object):
    def __init__(self, display_num=0):
        self.display = None

        try:
            firmware_type = get_actcast_firmware_type()
        except EnvironmentVariableNotSet:
            firmware_type = None

        if firmware_type == "raspberrypi-bullseye":
            from actfw_raspberrypi.vc4.drm import Display

            self.display = Display(display_num)
        elif firmware_type == "raspberrypi-buster" or firmware_type is None:
            from actfw_raspberrypi.vc4.dispmanx import Display

            self.display = Display(display_num)
        else:
            raise RuntimeError(f"Error: firmware_type={firmware_type} is not supported.")

    def get_info(self):
        return self.display.get_info()

    def open_window(self, dst, size, layer):
        return self.display.open_window(dst, size, layer)

    def size(self):
        return self.display.size()

    def close(self):
        self.display.close()
        self.display = None

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()
