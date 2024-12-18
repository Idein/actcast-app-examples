from actfw_core.task import Pipe
from PIL import Image
from consts import CAPTURE_HEIGHT, CAPTURE_WIDTH


class Preprocess(Pipe):
    def __init__(self, capture_size):
        super(Preprocess, self).__init__()
        self.capture_size = capture_size

    def proc(self, frame):
        rgb_image = Image.frombuffer(
            "RGB", self.capture_size, frame.getvalue(), "raw", "RGB"
        )
        rgb_image = rgb_image.resize((CAPTURE_WIDTH, CAPTURE_HEIGHT))
        return rgb_image
