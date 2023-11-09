import time

from actfw_core.task import Pipe
from PIL import ImageDraw, ImageFont


class FPS(object):
    def __init__(self, moving_average=30):
        self.moving_average = moving_average
        self.prev_time = time.time()
        self.dtimes = []

    def update(self):
        cur_time = time.time()
        dtime = cur_time - self.prev_time
        self.prev_time = cur_time
        self.dtimes.append(dtime)
        if len(self.dtimes) > self.moving_average:
            self.dtimes.pop(0)
        return self.get()

    def get(self):
        if len(self.dtimes) == 0:
            return None
        else:
            return len(self.dtimes) / sum(self.dtimes)


class Drawer(Pipe):
    def __init__(self):
        super(Drawer, self).__init__()
        fontname = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        self.font = ImageFont.truetype(font=fontname, size=14)
        self.font_large = ImageFont.truetype(font=fontname, size=18)
        self.fps = FPS(30)

    def proc(self, inputs):
        pil_img = inputs
        self.fps.update()
        drawer = ImageDraw.Draw(pil_img)
        fps = self.fps.get()
        if fps is None:
            fps_txt = "FPS: N/A"
        else:
            fps_txt = "FPS: {:>6.3f}".format(fps)
        drawer.text((0, 0), fps_txt, font=self.font, fill="gray")
        return (pil_img, fps)
