import numpy as np
from hailo_platform import VDevice, HailoSchedulingAlgorithm

# # These values are taken from translated_params.csv
OUT_ZP = 45.0
OUT_SCALE = 0.09447

timeout_ms = 500

params = VDevice.create_params()
params.scheduling_algorithm = HailoSchedulingAlgorithm.ROUND_ROBIN

class Model:
    def __init__(self):
        self.vdevice = VDevice(params)
        self.infer_model = self.vdevice.create_infer_model("./resnet_v1_18.hef")
        self.configured_infer_model = self.infer_model.configure()

    def __del__(self):
        self.configured_infer_model.__exit__(None, None, None)
        self.vdevice.__exit__(None, None, None)

    def infer(self, image):
        bindings = self.configured_infer_model.create_bindings()

        buffer = image.reshape(self.infer_model.input().shape).astype(np.uint8)
        bindings.input().set_buffer(buffer)

        buffer = np.zeros(self.infer_model.output().shape).astype(np.uint8)
        bindings.output().set_buffer(buffer)

        # self.configured_infer_model.run([bindings], timeout_ms)

        job = self.configured_infer_model.run_async([bindings])
        job.wait(timeout_ms)
        buffer = bindings.output().get_buffer()
        out = OUT_SCALE * (buffer.astype(np.float32) - OUT_ZP)
        expx = np.exp(out)
        prob = expx / expx.sum()
        return (prob,)

