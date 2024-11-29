from PIL import ImageDraw, ImageFont
import numpy as np
from actfw_core.task import Consumer
import time
import actfw_core
from consts import INFO_COLOR, JSTDT
from datetime import datetime


def to_datetime(t):
    return datetime.fromtimestamp(float(t) + JSTDT)


class FPS(object):

    """FPS Counter"""

    def __init__(self, moving_average=30):
        """

        Args:
            moving_average (int): recent N frames moving average

        """
        self.moving_average = moving_average
        self.prev_time = time.time()
        self.dtimes = []

    def update(self):
        """

        Update FPS.

        Returns:
            fps: current fps

        """
        cur_time = time.time()
        dtime = cur_time - self.prev_time
        self.prev_time = cur_time
        self.dtimes.append(dtime)
        if len(self.dtimes) > self.moving_average:
            self.dtimes.pop(0)
        return self.get()

    def get(self):
        """

        Get FPS.

        Returns:
            fps: current fps

        """
        if len(self.dtimes) == 0:
            return None
        else:
            return len(self.dtimes) / sum(self.dtimes)


class Presenter(Consumer):
    def __init__(self, preview_window, cmd, kvssink):
        super(Presenter, self).__init__()
        self.preview_window = preview_window
        self.cmd = cmd
        self.font = ImageFont.truetype(
            font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            size=int(20),
        )
        self.smallfont = ImageFont.truetype(
            font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            size=int(10),
        )
        self.font_height = self.font.getsize("99.9%")[1]
        self.smallfont_height = self.smallfont.getsize("99.9%")[1]
        self.fps = FPS()

        self.kvssink = kvssink

    def proc(self, captured_image):
        current_time = time.time()
        result_image = captured_image.copy()
        actfw_core.heartbeat()

        draw = ImageDraw.Draw(result_image)

        # Add a black box below FPS
        draw.rectangle(
            (0, 2, self.font_height * 8, self.font_height),
            fill=(0, 0, 0),
            outline=(0, 0, 0),
        )

        fps = "FPS: {:>6.3f}".format(self.fps.update())
        draw.text((0, 0), fps, font=self.font, fill=(255, 255, 255))

        y = self.font_height

        draw.text(
            (2, y),
            to_datetime(current_time).isoformat(),
            font=self.smallfont,
            fill=INFO_COLOR,
        )
        y += self.smallfont_height

        if self.kvssink is not None:
            self.kvssink.add_image(result_image)

        self.cmd.update_image(result_image)

        if self.preview_window is not None:
            self.preview_window.blit(np.asarray(result_image).tobytes())
            self.preview_window.update()
