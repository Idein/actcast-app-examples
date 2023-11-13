from actfw_core.task import Consumer
from actfw_raspberrypi.vc4 import Display
from PIL import Image
import actfw_core


class Presenter(Consumer):
    def __init__(self, cmd, use_display, display_size):
        super(Presenter, self).__init__()
        self.cmd = cmd
        if use_display:
            display = Display()
            display_width, display_height = display.size()
            scale = min(
                float(display_width / display_size[0]),
                float(display_height / display_size[1]),
            )
            width = int(scale * display_size[0])
            height = int(scale * display_size[1])
            left = (display_width - width) // 2
            upper = (display_height - height) // 2
            self.preview_window = display.open_window(
                (left, upper, width, height), display_size, 1000
            )
            self.canvas = Image.new("RGB", display_size, (0, 0, 0))
        else:
            self.preview_window = None
            self.canvas = None

    def proc(self, inputs):
        (pil_img, fps) = inputs
        actfw_core.heartbeat()
        actfw_core.notify([{"fps": fps}])
        self.cmd.update_image(pil_img)  # update Take Photo image
        if self.preview_window is not None:
            image = self.__paste_contain(self.canvas, pil_img)
            self.preview_window.blit(image.tobytes())
            self.preview_window.update()

    def __paste_contain(self, canvas, src):
        canvasW, canvasH = canvas.size
        srcW, srcH = src.size
        scale_w = canvasW / srcW
        scale_h = canvasH / srcH
        scale = min(scale_h, scale_w)
        scaledW, scaledH = (int(srcW * scale), int(srcH * scale))
        resized = src.resize((scaledW, scaledH))
        offsetW = (canvasW - scaledW) // 2
        offsetH = (canvasH - scaledH) // 2
        canvas.paste(resized, (offsetW, offsetH))
        return canvas
