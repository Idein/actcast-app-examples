# type: ignore
# flake8: noqa

from ctypes import *
from ctypes.util import find_library


class _libbcm_host(object):
    def __init__(self):
        self.lib = None
        path = find_library("bcm_host")
        if path is not None:
            self.lib = CDLL(path, use_errno=True)

    def init(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.bcm_host_init(*args, **kwargs)

    def vc_dispmanx_display_open(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_display_open(*args, **kwargs)

    def vc_dispmanx_display_get_info(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_display_get_info(*args, **kwargs)

    def vc_dispmanx_resource_create(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_resource_create(*args, **kwargs)

    def vc_dispmanx_rect_set(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_rect_set(*args, **kwargs)

    def vc_dispmanx_update_start(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_update_start(*args, **kwargs)

    def vc_dispmanx_element_add(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_element_add(*args, **kwargs)

    def vc_dispmanx_element_change_layer(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_element_change_layer(*args, **kwargs)

    def vc_dispmanx_update_submit_sync(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_update_submit_sync(*args, **kwargs)

    def vc_dispmanx_element_remove(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_element_remove(*args, **kwargs)

    def vc_dispmanx_resource_delete(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_resource_delete(*args, **kwargs)

    def vc_dispmanx_display_close(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_display_close(*args, **kwargs)

    def vc_dispmanx_resource_write_data(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_resource_write_data(*args, **kwargs)

    def vc_dispmanx_element_change_source(self, *args, **kwargs):
        if self.lib is None:
            raise FileNotFoundError("Not found: 'libbcm_host.so'")
        return self.lib.vc_dispmanx_element_change_source(*args, **kwargs)


_bcm_host = _libbcm_host()

DISPMANX_DISPLAY_HANDLE_T = c_uint
DISPMANX_UPDATE_HANDLE_T = c_uint
DISPMANX_ELEMENT_HANDLE_T = c_uint
DISPMANX_RESOURCE_HANDLE_T = c_uint

DISPMANX_PROTECTION_MAX = 0x0F
DISPMANX_PROTECTION_NONE = 0
DISPMANX_PROTECTION_HDCP = 11

DISPMANX_TRANSFORM_T = c_uint
DISPMANX_NO_ROTATE = 0
DISPMANX_ROTATE_90 = 1
DISPMANX_ROTATE_180 = 2
DISPMANX_ROTATE_270 = 3
DISPMANX_FLIP_HRIZ = 1 << 16
DISPMANX_FLIP_VERT = 1 << 17
DISPMANX_STEREOSCOPIC_INVERT = 1 << 19
DISPMANX_STEREOSCOPIC_NONE = 0 << 20
DISPMANX_STEREOSCOPIC_MONO = 1 << 20
DISPMANX_STEREOSCOPIC_SBS = 2 << 20
DISPMANX_STEREOSCOPIC_TB = 3 << 20
DISPMANX_STEREOSCOPIC_MASK = 15 << 20
DISPMANX_SNAPSHOT_NO_YUV = 1 << 24
DISPMANX_SNAPSHOT_NO_RGB = 1 << 25
DISPMANX_SNAPSHOT_FILL = 1 << 26
DISPMANX_SNAPSHOT_SWAP_RED_BLUE = 1 << 27
DISPMANX_SNAPSHOT_PACK = 1 << 28

VCOS_DISPLAY_INPUT_FORMAT_T = c_uint
DISPLAY_INPUT_FORMAT_T = VCOS_DISPLAY_INPUT_FORMAT_T
VCOS_DISPLAY_INPUT_FORMAT_INVALID = 0
VCOS_DISPLAY_INPUT_FORMAT_RGB888 = 1
VCOS_DISPLAY_INPUT_FORMAT_RGB565 = 2
DISPLAY_INPUT_FORMAT_INVALID = VCOS_DISPLAY_INPUT_FORMAT_INVALID
DISPLAY_INPUT_FORMAT_RGB888 = VCOS_DISPLAY_INPUT_FORMAT_RGB888
DISPLAY_INPUT_FORMAT_RGB565 = VCOS_DISPLAY_INPUT_FORMAT_RGB565

VC_IMAGE_TYPE_T = c_uint
VC_IMAGE_RGB888 = 5

TRANSFORM_HFLIP = 1 << 0
TRANSFORM_VFLIP = 1 << 1
TRANSFORM_TRANSPOSE = 1 << 2

VC_IMAGE_TRANSFORM_T = c_uint
VC_IMAGE_ROT0 = 0
VC_IMAGE_MIRROR_ROT0 = TRANSFORM_HFLIP
VC_IMAGE_MIRROR_ROT180 = TRANSFORM_VFLIP
VC_IMAGE_ROT180 = TRANSFORM_HFLIP | TRANSFORM_VFLIP
VC_IMAGE_MIRROR_ROT90 = TRANSFORM_TRANSPOSE
VC_IMAGE_ROT270 = TRANSFORM_TRANSPOSE | TRANSFORM_HFLIP
VC_IMAGE_ROT90 = TRANSFORM_TRANSPOSE | TRANSFORM_VFLIP
VC_IMAGE_MIRROR_ROT270 = TRANSFORM_TRANSPOSE | TRANSFORM_HFLIP | TRANSFORM_VFLIP


class DISPMANX_MODEINFO_T(Structure):
    _fields_ = [
        ("width", c_uint),
        ("height", c_uint),
        ("transform", DISPMANX_TRANSFORM_T),
        ("input_format", DISPLAY_INPUT_FORMAT_T),
        ("display_num", c_uint),
    ]


class VC_RECT_T(Structure):
    _fields_ = [
        ("x", c_uint),
        ("y", c_uint),
        ("width", c_uint),
        ("height", c_uint),
    ]


DISPMANX_FLAGS_ALPHA_T = c_uint
DISPMANX_FLAGS_ALPHA_FROM_SOURCE = 0
DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS = 1
DISPMANX_FLAGS_ALPHA_FIXED_NON_ZERO = 2
DISPMANX_FLAGS_ALPHA_FIXED_EXCEED_0X07 = 3
DISPMANX_FLAGS_ALPHA_PREMULT = 1 << 16
DISPMANX_FLAGS_ALPHA_MIX = 1 << 17
DISPMANX_FLAGS_ALPHA_DISCARD_LOWER_LAYERS = 1 << 18


class VC_DISPMANX_ALPHA_T(Structure):
    _fields_ = [
        ("flags", DISPMANX_FLAGS_ALPHA_T),
        ("opacity", c_uint),
        ("mask", DISPMANX_RESOURCE_HANDLE_T),
        ("height", c_uint),
    ]


class Display(object):

    """Display using VideoCore4 dispmanx"""

    def __init__(self, display_num=0):
        self.display_num = display_num
        _bcm_host.init()
        self.handle = _bcm_host.vc_dispmanx_display_open(self.display_num)
        self.info = DISPMANX_MODEINFO_T()
        self.get_info()

    def get_info(self):
        """
        Get display information.

        Returns:
            :class:`~actfw_raspberrypi.vc4.display.DISPMANX_MODEINFO_T`: display information
        """
        self.info = DISPMANX_MODEINFO_T()
        result = _bcm_host.vc_dispmanx_display_get_info(self.handle, byref(self.info))
        if result != 0:
            self.info = None
            raise RuntimeError("Failed to get display({}) information.".format(self.display_num))
        return self.info

    def open_window(self, dst, size, layer):
        """
        Open new window.

        Args:
            dst ((int, int, int, int)): destination rectangle (left, top, width, height)
            size ((int, int)): window size (width, height)
            layer (int): layer

        Returns:
            :class:`~actfw_raspberrypi.vc4.display.Window`: window
        """
        return Window(self, dst, size, layer)

    def size(self):
        """
        Get display size.

        Returns:
            ((int, int)): (width, height)
        """
        return (self.info.width, self.info.height)

    def close(self):
        _bcm_host.vc_dispmanx_display_close(self.handle)

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()


class Window(object):

    """
    Double buffered window.
    """

    def __init__(self, display, dst, size, layer):
        self.display = display
        self.size = size
        self.layer = layer

        if self.size[0] % 32 != 0:
            raise RuntimeError("Window width must be a multiple of 32.")

        self.format = VC_IMAGE_RGB888
        self.num_of_resources = 2
        self.resources = []
        self.native_image_handle = [c_uint()] * self.num_of_resources
        for i in range(self.num_of_resources):
            native_image_handle = c_uint()
            handle = _bcm_host.vc_dispmanx_resource_create(self.format, size[0], size[1], byref(self.native_image_handle[i]))
            if handle == 0:
                raise RuntimeError("Failed to create window resource.")
            self.resources.append(handle)

        src_rect = VC_RECT_T()
        _bcm_host.vc_dispmanx_rect_set(byref(src_rect), 0, 0, size[0] << 16, size[1] << 16)
        dst_rect = VC_RECT_T()
        _bcm_host.vc_dispmanx_rect_set(byref(dst_rect), dst[0], dst[1], dst[2], dst[3])

        update = _bcm_host.vc_dispmanx_update_start(0)

        alpha = VC_DISPMANX_ALPHA_T()
        alpha.flags = DISPMANX_FLAGS_ALPHA_FROM_SOURCE | DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS
        alpha.opacity = 255
        alpha.mask = 0

        self.element = _bcm_host.vc_dispmanx_element_add(
            update,
            self.display.handle,
            self.layer,
            byref(dst_rect),
            self.resources[1],
            byref(src_rect),
            DISPMANX_PROTECTION_NONE,
            byref(alpha),
            None,
            VC_IMAGE_ROT0,
        )
        if self.element == 0:
            raise RuntimeError("Failed to add element.")

        _bcm_host.vc_dispmanx_update_submit_sync(update)

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
        update = _bcm_host.vc_dispmanx_update_start(0)
        _bcm_host.vc_dispmanx_element_change_layer(update, self.element, layer)
        _bcm_host.vc_dispmanx_update_submit_sync(update)
        self.layer = layer

    def swap_layer(self, window):
        """
        Swap window layer.

        Args:
            window (:class:`~actfw_raspberrypi.vc4.display.Window`): target window
        """
        update = _bcm_host.vc_dispmanx_update_start(0)
        _bcm_host.vc_dispmanx_element_change_layer(update, self.element, window.layer)
        _bcm_host.vc_dispmanx_element_change_layer(update, window.element, self.layer)
        _bcm_host.vc_dispmanx_update_submit_sync(update)
        self.layer, window.layer = window.layer, self.layer

    def blit(self, image):
        """
        Blit image to window.

        Args:
            image (bytes): RGB image with which size is the same as window size
        """
        src_rect = VC_RECT_T()
        _bcm_host.vc_dispmanx_rect_set(byref(src_rect), 0, 0, self.size[0], self.size[1])
        pitch = (self.size[0] * 3 + 32 - 1) // 32 * 32
        buf = c_char_p(image)
        result = _bcm_host.vc_dispmanx_resource_write_data(self.resources[0], self.format, c_int(pitch), buf, byref(src_rect))
        if result != 0:
            raise RuntimeError("Failed to blit.: {}".format(result))

    def update(self):
        """
        Update window.
        """
        update = _bcm_host.vc_dispmanx_update_start(0)
        _bcm_host.vc_dispmanx_element_change_source(update, self.element, self.resources[0])
        _bcm_host.vc_dispmanx_update_submit_sync(update)
        self.resources.append(self.resources.pop(0))

    def close(self):
        """
        Close window.
        """
        update = _bcm_host.vc_dispmanx_update_start(0)
        _bcm_host.vc_dispmanx_element_remove(update, self.element)
        _bcm_host.vc_dispmanx_update_submit_sync(update)
        for resource in self.resources:
            _bcm_host.vc_dispmanx_resource_delete(resource)

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()
