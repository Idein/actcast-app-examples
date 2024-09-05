# type: ignore
# flake8: noqa

import mmap
import os
from ctypes import *
from ctypes.util import find_library
from typing import List

"""
libdrm API:

- https://gitlab.freedesktop.org/mesa/drm/-/blob/main/xf86drm.h
- https://gitlab.freedesktop.org/mesa/drm/-/blob/main/xf86drmMode.h
"""

DRM_MODE_OBJECT_CRTC = 0xCCCCCCCC
DRM_MODE_OBJECT_CONNECTOR = 0xC0C0C0C0
DRM_MODE_OBJECT_ENCODER = 0xE0E0E0E0
DRM_MODE_OBJECT_MODE = 0xDEDEDEDE
DRM_MODE_OBJECT_PROPERTY = 0xB0B0B0B0
DRM_MODE_OBJECT_FB = 0xFBFBFBFB
DRM_MODE_OBJECT_BLOB = 0xBBBBBBBB
DRM_MODE_OBJECT_PLANE = 0xEEEEEEEE
DRM_MODE_OBJECT_ANY = 0

DRM_FORMAT_RGB888 = 0x34324752
DRM_FORMAT_BGR888 = 0x34324742
DRM_FORMAT_RGBA8888 = 0x34324152
DRM_FORMAT_BGRA8888 = 0x34324142
DRM_FORMAT_ARGB8888 = 0x34325241
DRM_FORMAT_ABGR8888 = 0x34324241

DRM_PROP_NAME_LEN = 32
DRM_DISPLAY_MODE_LEN = 32

DRM_CAP_DUMB_BUFFER = 0x1

DRM_IOCTL_MODE_CREATE_DUMB = 0xC02064B2
DRM_IOCTL_MODE_MAP_DUMB = 0xC01064B3
DRM_IOCTL_MODE_DESTROY_DUMB = 0xC00464B4

DRM_MODE_CONNECTED = 1
DRM_MODE_DISCONNECTED = 2
DRM_MODE_UNKNOWNCONNECTION = 3

DRM_MODE_SUBPIXEL_UNKNOWN = 1
DRM_MODE_SUBPIXEL_HORIZONTAL_RGB = 2
DRM_MODE_SUBPIXEL_HORIZONTAL_BGR = 3
DRM_MODE_SUBPIXEL_VERTICAL_RGB = 4
DRM_MODE_SUBPIXEL_VERTICAL_BGR = 5
DRM_MODE_SUBPIXEL_NONE = 6

DRM_MODE_CONNECTOR_Unknown = 0
DRM_MODE_CONNECTOR_VGA = 1
DRM_MODE_CONNECTOR_DVII = 2
DRM_MODE_CONNECTOR_DVID = 3
DRM_MODE_CONNECTOR_DVIA = 4
DRM_MODE_CONNECTOR_Composite = 5
DRM_MODE_CONNECTOR_SVIDEO = 6
DRM_MODE_CONNECTOR_LVDS = 7
DRM_MODE_CONNECTOR_Component = 8
DRM_MODE_CONNECTOR_9PinDIN = 9
DRM_MODE_CONNECTOR_DisplayPort = 10
DRM_MODE_CONNECTOR_HDMIA = 11
DRM_MODE_CONNECTOR_HDMIB = 12
DRM_MODE_CONNECTOR_TV = 13
DRM_MODE_CONNECTOR_eDP = 14
DRM_MODE_CONNECTOR_VIRTUAL = 15
DRM_MODE_CONNECTOR_DSI = 16


class DRMModePropertyEnum(Structure):
    """
    struct drm_mode_property_enum {
        __u64 value;
        char name[DRM_PROP_NAME_LEN];
    };
    """

    _fields_ = [("value", c_uint64), ("name", c_char * DRM_PROP_NAME_LEN)]


class DRMModeProperty(Structure):
    """
    typedef struct _drmModeProperty {
        uint32_t prop_id;
        uint32_t flags;
        char name[DRM_PROP_NAME_LEN];
        int count_values;
        uint64_t *values; /* store the blob lengths */
        int count_enums;
        struct drm_mode_property_enum *enums;
        int count_blobs;
        uint32_t *blob_ids; /* store the blob IDs */
    } drmModePropertyRes, *drmModePropertyPtr;
    """

    _fields_ = [
        ("prop_id", c_uint32),
        ("flags", c_uint32),
        ("name", c_char * DRM_PROP_NAME_LEN),
        ("count_values", c_int),
        ("values", POINTER(c_uint64)),
        ("count_enums", c_int),
        ("enums", POINTER(DRMModePropertyEnum)),
        ("count_blobs", c_int),
        ("blob_ids", POINTER(c_uint32)),
    ]


class DRMModeObjectProperties(Structure):
    """
    typedef struct _drmModeObjectProperties {
        uint32_t count_props;
        uint32_t *props;
        uint64_t *prop_values;
    } drmModeObjectProperties, *drmModeObjectPropertiesPtr;
    """

    _fields_ = [
        ("count_props", c_uint32),
        ("props", POINTER(c_uint32)),
        ("prop_values", POINTER(c_uint64)),
    ]


class DRMModeResource(Structure):
    """
    typedef struct _drmModeRes {
            int count_fbs;
            uint32_t *fbs;
            int count_crtcs;
            uint32_t *crtcs;
            int count_connectors;
            uint32_t *connectors;
            int count_encoders;
            uint32_t *encoders;
            uint32_t min_width, max_width;
            uint32_t min_height, max_height;
    } drmModeRes, *drmModeResPtr;
    """

    _fields_ = [
        ("count_fbs", c_int),
        ("fbs", POINTER(c_uint32)),
        ("count_crtcs", c_int),
        ("_crtcs", POINTER(c_uint32)),
        ("count_connectors", c_int),
        ("_connectors", POINTER(c_uint32)),
        ("count_encoders", c_int),
        ("encoders", POINTER(c_uint32)),
        ("min_width", c_uint32),
        ("max_width", c_uint32),
        ("min_height", c_uint32),
        ("max_height", c_uint32),
    ]


class DRMModeModeInfo(Structure):
    """
    typedef struct _drmModeModeInfo {
            uint32_t clock;
            uint16_t hdisplay, hsync_start, hsync_end, htotal, hskew;
            uint16_t vdisplay, vsync_start, vsync_end, vtotal, vscan;
            uint32_t vrefresh;
            uint32_t flags;
            uint32_t type;
            char name[DRM_DISPLAY_MODE_LEN];
    } drmModeModeInfo, *drmModeModeInfoPtr;
    """

    _fields_ = [
        ("clock", c_uint32),
        ("hdisplay", c_uint16),
        ("hsync_start", c_uint16),
        ("hsync_end", c_uint16),
        ("htotal", c_uint16),
        ("hskew", c_uint16),
        ("vdisplay", c_uint16),
        ("vsync_start", c_uint16),
        ("vsync_end", c_uint16),
        ("vtotal", c_uint16),
        ("vscan", c_uint16),
        ("vrefresh", c_uint32),
        ("flags", c_uint32),
        ("type", c_uint32),
        ("name", c_char * DRM_DISPLAY_MODE_LEN),
    ]


class DRMModeConnector(Structure):
    """
    typedef struct _drmModeConnector {
            uint32_t connector_id;
            uint32_t encoder_id; /**< Encoder currently connected to */
            uint32_t connector_type;
            uint32_t connector_type_id;
            drmModeConnection connection;
            uint32_t mmWidth, mmHeight; /**< HxW in millimeters */
            drmModeSubPixel subpixel;
            int count_modes;
            drmModeModeInfoPtr modes;
            int count_props;
            uint32_t *props; /**< List of property ids */
            uint64_t *prop_values; /**< List of property values */
            int count_encoders;
            uint32_t *encoders; /**< List of encoder ids */
    } drmModeConnector, *drmModeConnectorPtr;
    """

    _fields_ = [
        ("connector_id", c_uint32),
        ("encoder_id", c_uint32),
        ("connector_type", c_uint32),
        ("connector_type_id", c_uint32),
        ("connection", c_uint),
        ("mmWidth", c_uint32),
        ("mmHeight", c_uint32),
        ("subpixel", c_uint),
        ("count_modes", c_int),
        ("modes", POINTER(DRMModeModeInfo)),
        ("count_props", c_int),
        ("props", POINTER(c_uint32)),
        ("prop_values", POINTER(c_uint64)),
        ("count_encoders", c_int),
        ("encoders", POINTER(c_uint32)),
    ]


class DRMModeEncoder(Structure):
    """
    typedef struct _drmModeEncoder {
            uint32_t encoder_id;
            uint32_t encoder_type;
            uint32_t crtc_id;
            uint32_t possible_crtcs;
            uint32_t possible_clones;
    } drmModeEncoder, *drmModeEncoderPtr;
    """

    _fields_ = [
        ("encoder_id", c_uint32),
        ("encoder_type", c_uint32),
        ("crtc_id", c_uint32),
        ("possible_crtcs", c_uint32),
        ("possible_clones", c_uint32),
    ]


class DRMModeCrtc(Structure):
    """
    typedef struct _drmModeCrtc {
            uint32_t crtc_id;
            uint32_t buffer_id; /**< FB id to connect to 0 = disconnect */
            uint32_t x, y; /**< Position on the framebuffer */
            uint32_t width, height;
            int mode_valid;
            drmModeModeInfo mode;
            int gamma_size; /**< Number of gamma stops */
    } drmModeCrtc, *drmModeCrtcPtr;
    """

    _fields_ = [
        ("crtc_id", c_uint32),
        ("buffer_id", c_uint32),
        ("x", c_uint32),
        ("y", c_uint32),
        ("width", c_uint32),
        ("height", c_uint32),
        ("mode_valid", c_int),
        ("mode", DRMModeModeInfo),
        ("gamma_size", c_int),
    ]


class DRMModePlaneRes(Structure):
    """
    typedef struct _drmModePlaneRes {
        uint32_t count_planes;
        uint32_t *planes;
    } drmModePlaneRes, *drmModePlaneResPtr;
    """

    _fields_ = [("count_planes", c_uint32), ("planes", POINTER(c_uint32))]


class DRMModePlane(Structure):
    """
    typedef struct _drmModePlane {
        uint32_t count_formats;
        uint32_t *formats;
        uint32_t plane_id;
        uint32_t crtc_id;
        uint32_t fb_id;
        uint32_t crtc_x, crtc_y;
        uint32_t x, y;
        uint32_t possible_crtcs;
        uint32_t gamma_size;
    } drmModePlane, *drmModePlanePtr;
    """

    _fields_ = [
        ("count_formats", c_uint32),
        ("formats", POINTER(c_uint32)),
        ("plane_id", c_uint32),
        ("crtc_id", c_uint32),
        ("fb_id", c_uint32),
        ("crtc_x", c_uint32),
        ("crtc_y", c_uint32),
        ("x", c_uint32),
        ("y", c_uint32),
        ("possible_crtcs", c_uint32),
        ("gamma_size", c_uint32),
    ]


class _DRMModeCreateDumb(Structure):
    """
    struct drm_mode_create_dumb {
        __u32 height;
        __u32 width;
        __u32 bpp;
        __u32 flags;
        /* handle, pitch, size will be returned */
        __u32 handle;
        __u32 pitch;
        __u64 size;
    };
    """

    _fields_ = [
        ("height", c_uint32),
        ("width", c_uint32),
        ("bpp", c_uint32),
        ("flags", c_uint32),
        ("handle", c_uint32),
        ("pitch", c_uint32),
        ("size", c_uint64),
    ]


class _DRMModeMapDumb(Structure):
    """
    struct drm_mode_map_dumb {
        /** Handle for the object being mapped. */
        __u32 handle;
        __u32 pad;
        /**
         * Fake offset to use for subsequent mmap call
         *
         * This is a fixed-size type for 32/64 compatibility.
         */
        __u64 offset;
    };
    """

    _fields_ = [("handle", c_uint32), ("pad", c_uint32), ("offset", c_uint32)]


class _DRMModeDestroyDumb(Structure):
    """
    struct drm_mode_destroy_dumb {
        __u32 handle;
    };
    """

    _fields_ = [("handle", c_uint32)]


class _libdrm(object):
    def __init__(self):
        self.lib = None
        path = find_library("drm")
        if path is not None:
            self.lib = CDLL(path, use_errno=True)

        if self.lib is None:
            raise FileNotFoundError("Not found: libdrm.so")

        self.lib.drmOpen.argtypes = [c_char_p, c_char_p]
        self.lib.drmOpen.restype = c_int
        self.lib.drmClose.argtypes = [c_int]
        self.lib.drmClose.restype = c_int

        self.lib.drmGetCap.argtypes = [c_int, c_uint64, POINTER(c_uint64)]
        self.lib.drmGetCap.restype = c_int

        self.lib.drmModeGetResources.argtypes = [c_int]
        self.lib.drmModeGetResources.restype = POINTER(DRMModeResource)
        self.lib.drmModeFreeResources.argtypes = [POINTER(DRMModeResource)]
        self.lib.drmModeFreeResources.restype = None

        self.lib.drmModeGetConnector.argtypes = [c_int, c_uint32]
        self.lib.drmModeGetConnector.restype = POINTER(DRMModeConnector)
        self.lib.drmModeFreeConnector.argtypes = [POINTER(DRMModeConnector)]
        self.lib.drmModeFreeConnector.restype = None

        self.lib.drmModeGetEncoder.argtypes = [c_int, c_uint32]
        self.lib.drmModeGetEncoder.restype = POINTER(DRMModeEncoder)
        self.lib.drmModeFreeEncoder.argtypes = [POINTER(DRMModeEncoder)]
        self.lib.drmModeFreeEncoder.restype = None

        self.lib.drmModeGetCrtc.argtypes = [c_int, c_uint32]
        self.lib.drmModeGetCrtc.restype = POINTER(DRMModeCrtc)
        self.lib.drmModeSetCrtc.argtypes = [
            c_int,
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32,
            POINTER(c_uint32),
            c_int,
            POINTER(DRMModeModeInfo),
        ]
        self.lib.drmModeSetCrtc.restype = c_int
        self.lib.drmModeFreeCrtc.argtypes = [POINTER(DRMModeCrtc)]
        self.lib.drmModeFreeCrtc.restype = None

        self.lib.drmModeGetPlaneResources.argtypes = [c_int]
        self.lib.drmModeGetPlaneResources.restype = POINTER(DRMModePlaneRes)
        self.lib.drmModeFreePlaneResources.argtypes = [POINTER(DRMModePlaneRes)]
        self.lib.drmModeFreePlaneResources.restype = None

        self.lib.drmModeGetPlane.argtypes = [c_int, c_uint32]
        self.lib.drmModeGetPlane.restype = POINTER(DRMModePlane)
        self.lib.drmModeSetPlane.argtypes = [
            c_int,
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32,
            c_int32,
            c_int32,
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32,
        ]
        self.lib.drmModeSetPlane.restype = c_int
        self.lib.drmModeFreePlane.argtypes = [POINTER(DRMModePlane)]
        self.lib.drmModeFreePlane.restype = None

        self.lib.drmModeAddFB2.argtypes = [
            c_int,
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint32 * 4,
            c_uint32 * 4,
            c_uint32 * 4,
            POINTER(c_uint32),
            c_uint32,
        ]
        self.lib.drmModeAddFB2.restype = c_int
        self.lib.drmModeRmFB.argtypes = [c_int, c_uint32]
        self.lib.drmModeRmFB.restype = c_int

        self.lib.drmModeGetProperty.argtypes = [c_int, c_uint32]
        self.lib.drmModeGetProperty.restype = POINTER(DRMModeProperty)
        self.lib.drmModeFreeProperty.argtypes = [POINTER(DRMModeProperty)]
        self.lib.drmModeFreeProperty.restype = None

        self.lib.drmModeObjectGetProperties.argtypes = [c_int, c_uint32, c_uint32]
        self.lib.drmModeObjectGetProperties.restype = POINTER(DRMModeObjectProperties)
        self.lib.drmModeFreeObjectProperties.argtypes = [POINTER(DRMModeObjectProperties)]
        self.lib.drmModeFreeObjectProperties.restype = None
        self.lib.drmModeObjectSetProperty.argtypes = [
            c_int,
            c_uint32,
            c_uint32,
            c_uint32,
            c_uint64,
        ]
        self.lib.drmModeObjectSetProperty.restype = c_int

        self.lib.drmIoctl.argtypes = [c_int, c_ulong, c_voidp]
        self.lib.drmIoctl.restype = c_int

    def open(self, *args, **kwargs):
        return self.lib.drmOpen(*args, **kwargs)

    def close(self, *args, **kwargs):
        return self.lib.drmClose(*args, **kwargs)

    def support_dumb_buffer(self, fd):
        cap = c_uint64(0)
        res = self.lib.drmGetCap(fd, DRM_CAP_DUMB_BUFFER, byref(cap))
        return not (res < 0 or cap == 0)

    def get_resources(self, *args, **kwargs):
        return self.lib.drmModeGetResources(*args, **kwargs).contents

    def free_resouces(self, *args, **kwargs):
        return self.lib.drmModeFreeResources(*args, **kwargs)

    def get_connector(self, *args, **kwargs):
        return self.lib.drmModeGetConnector(*args, **kwargs).contents

    def free_connector(self, *args, **kwargs):
        return self.lib.drmModeFreeConnector(*args, **kwargs)

    def get_encoder(self, *args, **kwargs):
        return self.lib.drmModeGetEncoder(*args, **kwargs).contents

    def free_encoder(self, *args, **kwargs):
        return self.lib.drmModeFreeEncoder(*args, **kwargs)

    def get_crtc(self, *args, **kwargs):
        return self.lib.drmModeGetCrtc(*args, **kwargs).contents

    def set_crtc(self, *args, **kwargs):
        return self.lib.drmModeSetCrtc(*args, **kwargs)

    def free_crtc(self, *args, **kwargs):
        return self.lib.drmModeFreeCrtc(*args, **kwargs)

    def get_plane_resources(self, *args, **kwargs):
        return self.lib.drmModeGetPlaneResources(*args, **kwargs).contents

    def free_plane_resources(self, *args, **kwargs):
        return self.lib.drmModeFreePlaneResources(*args, **kwargs)

    def get_plane(self, *args, **kwargs):
        return self.lib.drmModeGetPlane(*args, **kwargs).contents

    def set_plane(self, *args, **kwargs):
        return self.lib.drmModeSetPlane(*args, **kwargs)

    def free_plane(self, *args, **kwargs):
        return self.lib.drmModeFreePlane(*args, **kwargs)

    def add_fb(self, *args, **kwargs):
        return self.lib.drmModeAddFB2(*args, **kwargs)

    def rm_fb(self, *args, **kwargs):
        return self.lib.drmModeRmFB(*args, **kwargs)

    def get_property(self, *args, **kwargs):
        return self.lib.drmModeGetProperty(*args, **kwargs).contents

    def free_property(self, *args, **kwargs):
        return self.lib.drmModeFreeProperty(*args, **kwargs)

    def get_object_properties(self, *args, **kwargs):
        return self.lib.drmModeObjectGetProperties(*args, **kwargs).contents

    def free_object_properties(self, *args, **kwargs):
        return self.lib.drmModeFreeObjectProperties(*args, **kwargs)

    def set_object_property(self, *args, **kwargs):
        return self.lib.drmModeObjectSetProperty(*args, **kwargs)

    def ioctl(self, *args, **kwargs):
        return self.lib.drmIoctl(*args, **kwargs)


_drm = _libdrm()


class Framebuffer(object):
    def __init__(self, fd, width, height, bpp=24):
        self.fd = fd

        creq = _DRMModeCreateDumb()
        creq.width = width
        creq.height = height
        creq.bpp = bpp
        creq.flags = 0

        res = _drm.ioctl(self.fd, DRM_IOCTL_MODE_CREATE_DUMB, byref(creq))
        if res != 0:
            raise RuntimeError("fail to create dumb")

        fb = c_uint32()
        if creq.bpp == 24:
            pixel_format = DRM_FORMAT_BGR888
        else:
            raise RuntimeError(f"not support bpp: {creq.bpp}")

        bo_handles = (c_uint32 * 4)()
        bo_handles[0] = creq.handle
        bo_handles[1] = 0
        bo_handles[2] = 0
        bo_handles[3] = 0
        pitches = (c_uint32 * 4)()
        pitches[0] = creq.pitch
        pitches[1] = 0
        pitches[2] = 0
        pitches[3] = 0
        offsets = (c_uint32 * 4)()
        offsets[0] = 0
        offsets[1] = 0
        offsets[2] = 0
        offsets[3] = 0
        res = _drm.add_fb(
            self.fd,
            creq.width,
            creq.height,
            pixel_format,
            bo_handles,
            pitches,
            offsets,
            byref(fb),
            creq.flags,
        )
        if res != 0:
            raise RuntimeError("fail to add framebuffer")
        self.fb_id = fb
        self.handle = creq.handle

        mreq = _DRMModeMapDumb()
        mreq.handle = creq.handle
        res = _drm.ioctl(self.fd, DRM_IOCTL_MODE_MAP_DUMB, byref(mreq))
        if res != 0:
            raise RuntimeError("fail to map dumb")

        self.buffer = mmap.mmap(
            self.fd,
            creq.size,
            flags=mmap.MAP_SHARED,
            prot=mmap.PROT_READ | mmap.PROT_WRITE,
            offset=mreq.offset,
        )

        self.write(bytearray(creq.size))

    def close(self):
        self.buffer.close()

        res = _drm.rm_fb(self.fd, self.fb_id)
        if res != 0:
            raise RuntimeError("fail to remove framebuffer")

        dreq = _DRMModeDestroyDumb()
        dreq.handle = self.handle
        res = _drm.ioctl(self.fd, DRM_IOCTL_MODE_DESTROY_DUMB, byref(dreq))
        if res != 0:
            raise RuntimeError("fail to destroy dumb")

    def write(self, bs):
        pos = self.buffer.tell()
        self.buffer.write(bs)
        self.buffer.seek(pos)


class Plane(object):
    def __init__(self, fd, drm_plane):
        self.fd = fd
        self.plane_id = drm_plane.plane_id
        self.crtc_id = drm_plane.crtc_id
        self.fb_id = drm_plane.fb_id
        self.crtc_x = drm_plane.crtc_x
        self.crtc_y = drm_plane.crtc_y
        self.x = drm_plane.x
        self.y = drm_plane.y

        self.zpos = self._get_zpos()

    def set(self, crtc_id, fb_id, dst, src):
        x, y, w, h = dst
        x0, y0, w0, h0 = src
        flags = 0
        res = _drm.set_plane(
            self.fd,
            self.plane_id,
            crtc_id,
            fb_id,
            flags,
            x,
            y,
            w,
            h,
            x0 << 16,
            y0 << 16,
            w0 << 16,
            h0 << 16,
        )
        if res != 0:
            errno = get_errno()
            err = os.strerror(errno)
            raise RuntimeError(f"fail to set plane: {res} {errno} {err}")

    def __str__(self):
        res = f"""Plane {self.plane_id}:
    crtc_id = {self.crtc_id}
    fb_id = {self.fb_id}
    crtc_x, crtc_y = {self.crtc_x}, {self.crtc_y}
    x, y = {self.x}, {self.y}
    zpos = {self.zpos}"""
        return res

    def _get_zpos(self):
        zpos = None
        props = _drm.get_object_properties(self.fd, self.plane_id, DRM_MODE_OBJECT_PLANE)
        for i in range(props.count_props):
            prop_id = props.props[i]
            prop = _drm.get_property(self.fd, prop_id)
            if prop.name == b"zpos":
                zpos = props.prop_values[i]
            _drm.free_property(byref(prop))
        _drm.free_object_properties(byref(props))
        if zpos is None:
            raise RuntimeError("zpos not found")
        else:
            return zpos

    def _set_color_space(self):
        props = _drm.get_object_properties(self.fd, self.plane_id, DRM_MODE_OBJECT_PLANE)
        for i in range(props.count_props):
            prop_id = props.props[i]
            prop = _drm.get_property(self.fd, prop_id)
            if prop.name == b"COLOR_ENCODING":
                # Use ITU-R BT.601 YCbCr
                ret = _drm.set_object_property(self.fd, self.plane_id, DRM_MODE_OBJECT_PLANE, prop_id, 0)
                if ret < 0:
                    raise RuntimeError("fail to set color_encoding")
            elif prop.name == b"COLOR_RANGE":
                # Use YCbCr full range
                ret = _drm.set_object_property(self.fd, self.plane_id, DRM_MODE_OBJECT_PLANE, prop_id, 1)
                if ret < 0:
                    raise RuntimeError("fail to set color_range")
            _drm.free_property(byref(prop))
        _drm.free_object_properties(byref(props))


class Device(object):
    def __init__(self):
        self.fd = _drm.open(b"vc4", None)
        if self.fd < 0:
            raise RuntimeError("fail to open drm device")
        if not _drm.support_dumb_buffer(self.fd):
            raise RuntimeError("not support dumb buffer")

        resources = _drm.get_resources(self.fd)
        self.connector = self._find_connector(resources)
        self.crtc = self._find_crtc(self.connector)
        self.width = self.crtc.mode.hdisplay
        self.height = self.crtc.mode.vdisplay
        _drm.free_resouces(byref(resources))

        self.planes = self._collect_planes()

    def close(self):
        _drm.free_crtc(byref(self.crtc))
        _drm.free_connector(byref(self.connector))
        _drm.close(self.fd)

    def pick_plane(self, layer):
        zposs = sorted([p.zpos for p in self.planes if p.crtc_id == 0])
        if layer in zposs:
            plane = [p for p in self.planes if p.zpos == layer][0]
            self.planes.remove(plane)
            return plane
        else:
            raise RuntimeError(f"layer value must be in {zposs}")

    def free_plane(self, plane):
        plane.set(0, 0, (0, 0, 0, 0), (0, 0, 0, 0))
        self.planes.append(plane)

    def create_fb(self, width, height, bpp=24):
        return Framebuffer(self.fd, width, height, bpp)

    def _find_connector(self, res: DRMModeResource) -> DRMModeConnector:
        for i in range(res.count_connectors):
            conn = _drm.get_connector(self.fd, res._connectors[i])
            if conn.connection == DRM_MODE_CONNECTED:
                return conn
            else:
                _drm.free_connector(byref(conn))
        raise RuntimeError("no connected connector")

    def _find_crtc(self, conn: DRMModeConnector) -> DRMModeCrtc:
        enc = None
        crtc = None

        enc = _drm.get_encoder(self.fd, conn.encoder_id)
        crtc = _drm.get_crtc(self.fd, enc.crtc_id)
        if enc is not None:
            _drm.free_encoder(byref(enc))

        if crtc is None:
            raise RuntimeError("no crtc")
        else:
            return crtc

    def _collect_planes(self) -> List[Plane]:
        planes = []
        res = _drm.get_plane_resources(self.fd)
        for i in range(res.count_planes):
            raw = _drm.get_plane(self.fd, res.planes[i])
            p = Plane(self.fd, raw)
            _drm.free_plane(byref(raw))
            planes.append(p)
        _drm.free_plane_resources(byref(res))
        return planes
