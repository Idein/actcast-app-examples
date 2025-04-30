import numpy as np
from hailo_platform import VDevice, HailoSchedulingAlgorithm

# # These values are taken from translated_params.csv
OUT_ZP = 45.0
OUT_SCALE = 0.09447

timeout_ms = 1000

params = VDevice.create_params()
params.scheduling_algorithm = HailoSchedulingAlgorithm.ROUND_ROBIN

class Model:
    def __init__(self):
        self.vdevice = VDevice(params)
        self.infer_model = self.vdevice.create_infer_model("./resnet_v1_18.hef")
        self.configured_infer_model = self.infer_model.configure()

    def __del__(self):
        self.vdevice.release()

    def infer(self, image):
        bindings = self.configured_infer_model.create_bindings()

        # buffer = np.empty(self.infer_model.input().shape).astype(np.uint8)
        buffer = image.reshape(self.infer_model.input().shape).astype(np.uint8)
        bindings.input().set_buffer(buffer)

        # buffer = np.empty(self.infer_model.output().shape).astype(np.uint8)
        buffer = np.zeros(self.infer_model.output().shape).astype(np.uint8)
        bindings.output().set_buffer(buffer)

        # self.infer_model.run([bindings], timeout_ms)
        # buffer = bindings.output().get_buffer()

        job = self.configured_infer_model.run_async([bindings])
        job.wait(timeout_ms)
        buffer = bindings.output().get_buffer()
        out = OUT_SCALE * (buffer.astype(np.float32) - OUT_ZP)
        expx = np.exp(out)
        prob = expx / expx.sum()
        return (prob,)

