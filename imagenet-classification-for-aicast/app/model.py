from ctypes import cdll
import ctypes as c
import numpy as np
from actfw_core.system import get_actcast_firmware_type

# These values are taken from translated_params.csv
OUT_ZP = 45.0
OUT_SCALE = 0.09447


class Model:
    def __init__(self):
        if get_actcast_firmware_type() == "raspberrypi-bookworm":
            lib_path = "./libresnet_v1_18_64bit.so"
        else:
            lib_path = "./libresnet_v1_18.so"
        self.lib = cdll.LoadLibrary(lib_path)
        self.lib.init()

    def __del__(self):
        self.lib.destroy()

    def infer(self, image):
        out = np.zeros(1000, dtype=np.float32)
        self.lib.infer(image.ctypes.data_as(c.c_void_p), out.ctypes.data_as(c.c_void_p))
        expx = np.exp(out)
        prob = expx / expx.sum()
        return (prob,)
