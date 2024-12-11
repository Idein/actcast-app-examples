from PIL import ImageDraw, ImageFont
import numpy as np
from actfw_core.task import Consumer
from actfw_core.autofocus import AfMode
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
    def __init__(
        self,
        preview_window,
        cmd,
        auto_focuser=None,
        afmode=None,
        aftimer=None,
        afvalue=None,
    ):
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

        self.auto_focuser = auto_focuser
        self.afmode = afmode
        self.afvalue = 420 if afvalue is None else afvalue
        self.aftimer = 10 if aftimer is None else aftimer
        self.aftimer_countdown = self.aftimer
        self.prev_time = None

    def focus_control(self):
        if self.auto_focuser is not None:
            if self.afmode == "timer":
                if self.prev_time is not None:
                    elapsed = time.time() - self.prev_time
                    self.aftimer_countdown -= elapsed
                    if self.aftimer_countdown < 0:
                        self.auto_focuser.trigger_scan()
                        self.aftimer_countdown = self.aftimer
            elif self.afmode == "manual":
                self.auto_focuser.set_focus_value(self.afvalue)

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

        if self.auto_focuser is not None:
            self.focus_control()
            stats = self.auto_focuser.get_focus_stats()
            txt = "afmode: " + str(self.afmode)
            draw.text(
                (2, y),
                txt,
                font=self.smallfont,
                fill=INFO_COLOR,
            )
            y += self.smallfont_height
            txt = "focus_val: " + str(stats.lensSetting)
            draw.text(
                (2, y),
                txt,
                font=self.smallfont,
                fill=INFO_COLOR,
            )
            y += self.smallfont_height
            txt = "aftimer: " + ":{:.2f}".format(self.aftimer_countdown)
            draw.text(
                (2, y),
                txt,
                font=self.smallfont,
                fill=INFO_COLOR,
            )
            y += self.smallfont_height
            txt = "af status: " + stats.state.name
            draw.text(
                (2, y),
                txt,
                font=self.smallfont,
                fill=INFO_COLOR,
            )
            y += self.smallfont_height

        self.cmd.update_image(result_image)

        if self.preview_window is not None:
            self.preview_window.blit(result_image.tobytes())
            self.preview_window.update()

        self.prev_time = time.time()
