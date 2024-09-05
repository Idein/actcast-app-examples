# type: ignore
# flake8: noqa

from .drm import *


class Display(object):

    """Display using libdrm"""

    def __init__(self, display_num=0):
        if display_num != 0:
            raise RuntimeError(f"display_num={display_num} is not supported in bullseye.")
        self.device = Device()

    def get_info(self):
        """
        DEPRECATED: Get display information.
        """
        raise RuntimeError("This API is deprecated. If you need width and height, use Display.size().")

    def open_window(self, dst, size, layer):
        """
        Open new window.

        Args:
            dst ((int, int, int, int)): destination rectangle (left, top, width, height)
            size ((int, int)): window size (width, height)
            layer (int): layer

        Returns:
            :class:`~actfw_raspberrypi.vc4.drm.display.Window`: window
        """
        return Window(self.device, dst, size, layer)

    def size(self):
        """
        Get display size.

        Returns:
            ((int, int)): (width, height)
        """
        return (self.device.width, self.device.height)

    def close(self):
        self.device.close()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()


class Window(object):

    """
    Double buffered window.
    """

    def __init__(self, device, dst, size, layer):
        self.device = device
        self.size = size
        width, height = size
        self.crtc_id = self.device.crtc.crtc_id
        self.src = (0, 0, width, height)
        self.dst = dst
        self.front_fb = self.device.create_fb(width, height)
        self.back_fb = self.device.create_fb(width, height)

        self.plane = self.device.pick_plane(layer)
        self.plane.set(self.crtc_id, self.front_fb.fb_id, self.dst, self.src)

    def clear(self, rgb=(0, 0, 0)):
        """
        Clear window.

        Args:
            rgb ((int, int, int)): clear color
        """
        color = b"".join(map(lambda x: x.to_bytes(1, "little"), rgb))
        self.blit(color * self.size[0] * self.size[1])

    def set_layer(self, layer):
        """
        Set window layer.

        Args:
            layer (int): new layer
        """
        if self.plane.zpos == layer:
            return
        else:
            self.device.free_plane(self.plane)
            self.plane = self.device.pick_plane(layer)
            self.plane.set(self.crtc_id, self.front_fb.fb_id, self.dst, self.src)

    def swap_layer(self, window):
        """
        Swap window layer.

        Args:
            window (:class:`~actfw_raspberrypi.vc4.display.Window`): target window
        """
        zpos0 = self.plane.zpos
        zpos1 = window.plane.zpos
        self.device.free_plane(self.plane)
        window.set_layer(zpos0)
        self.plane = self.device.pick_plane(zpos1)
        self.plane.set(self.crtc_id, self.front_fb.fb_id, self.dst, self.src)

    def blit(self, image):
        """
        Blit image to window.

        Args:
            image (bytes): RGB image with which size is the same as window size
        """
        self.back_fb.write(image)

    def update(self):
        """
        Update window.
        """
        self.plane.set(self.crtc_id, self.back_fb.fb_id, self.dst, self.src)
        self.front_fb, self.back_fb = self.back_fb, self.front_fb

    def close(self):
        """
        Close window.
        """
        self.front_fb.close()
        self.back_fb.close()
        self.device.free_plane(self.plane)

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()
