# flake8: noqa

import enum
from ctypes import *


class capability(Structure):
    _fields_ = [
        ("driver", c_uint8 * 16),
        ("card", c_uint8 * 32),
        ("bus_info", c_uint8 * 32),
        ("version", c_uint32),
        ("capabilities", c_uint32),
        ("device_caps", c_uint32),
        ("reserved", c_uint32 * 3),
    ]


class fmtdesc(Structure):
    _fields_ = [
        ("index", c_uint32),
        ("type", c_uint32),
        ("flags", c_uint32),
        ("description", c_uint8 * 32),
        ("pixelformat", c_uint32),
        ("reserved", c_uint32 * 4),
    ]


class frmsize_discrete(Structure):
    _fields_ = [
        ("width", c_uint32),
        ("height", c_uint32),
    ]


class frmsize_stepwise(Structure):
    _fields_ = [
        ("min_width", c_uint32),
        ("max_width", c_uint32),
        ("step_width", c_uint32),
        ("min_height", c_uint32),
        ("max_height", c_uint32),
        ("step_height", c_uint32),
    ]


class _frmsize_for_frmsizeenum(Union):
    _fields_ = [
        ("discrete", frmsize_discrete),
        ("stepwise", frmsize_stepwise),
    ]


class frmsizeenum(Structure):
    _anonymous_ = ("_frmsize",)
    _fields_ = [
        ("index", c_uint32),
        ("pixel_format", c_uint32),
        ("type", c_uint32),
        ("_frmsize", _frmsize_for_frmsizeenum),
        ("reserved", c_uint32 * 2),
    ]


class fract(Structure):
    _fields_ = [
        ("numerator", c_uint32),
        ("denominator", c_uint32),
    ]


class frmival_stepwise(Structure):
    _fields_ = [
        ("min", fract),
        ("max", fract),
        ("step", fract),
    ]


class _frmival_for_frmivalenum(Union):
    _fields_ = [
        ("discrete", fract),
        ("stepwise", frmival_stepwise),
    ]


class frmivalenum(Structure):
    _anonymous_ = ("_frmival",)
    _fields_ = [
        ("index", c_uint32),
        ("pixel_format", c_uint32),
        ("width", c_uint32),
        ("height", c_uint32),
        ("type", c_uint32),
        ("_frmival", _frmival_for_frmivalenum),
        ("reserved", c_uint32 * 2),
    ]


class pix_format(Structure):
    _fields_ = [
        ("width", c_uint32),
        ("height", c_uint32),
        ("pixelformat", c_uint32),
        ("field", c_uint32),
        ("bytesperline", c_uint32),
        ("sizeimage", c_uint32),
        ("colorspace", c_uint32),
        ("priv", c_uint32),
        ("flags", c_uint32),
        ("ycbcr_enc", c_uint32),
        ("quantization", c_uint32),
        ("xfer_func", c_uint32),
    ]


class plane_pix_format(Structure):
    _pack_ = 1
    _fields_ = [
        ("sizeimage", c_uint32),
        ("bytesperline", c_uint32),
        ("reserved", c_uint16 * 6),
    ]


class pix_format_mplane(Structure):
    _pack_ = 1
    _fields_ = [
        ("width", c_uint32),
        ("height", c_uint32),
        ("pixelformat", c_uint32),
        ("field", c_uint32),
        ("colorspace", c_uint32),
        ("plane_fmt", plane_pix_format * 8),  # VIDEO_MAX_PLANES
        ("num_planes", c_uint8),
        ("flags", c_uint8),
        ("ycbcr_enc", c_uint8),
        ("quantization", c_uint8),
        ("xfer_func", c_uint8),
        ("reserved", c_uint8 * 7),
    ]


class rect(Structure):
    _fields_ = [
        ("left", c_int32),
        ("top", c_int32),
        ("width", c_uint32),
        ("height", c_uint32),
    ]


class clip(Structure):
    pass


clip._fields_ = [
    ("c", rect),
    ("next", POINTER(clip)),
]


class window(Structure):
    _fields_ = [
        ("w", rect),
        ("field", c_uint32),
        ("chromakey", c_uint32),
        ("clips", POINTER(clip)),
        ("clipcount", c_uint32),
        ("bitmap", c_void_p),
        ("global_alpha", c_uint8),
    ]


class vbi_format(Structure):
    _fields_ = [
        ("sampling_rate", c_uint32),
        ("offset", c_uint32),
        ("samples_per_line", c_uint32),
        ("sample_format", c_uint32),
        ("start", c_int32 * 2),
        ("count", c_uint32 * 2),
        ("flags", c_uint32),
        ("reserved", c_uint32 * 2),
    ]


class sliced_vbi_format(Structure):
    _fields_ = [
        ("service_lines", 2 * (24 * c_ushort)),
        ("io_size", c_uint),
        ("reserved", c_uint * 2),
    ]


class sdr_format(Structure):
    _pack_ = 1
    _fields_ = [
        ("pixelformat", c_uint32),
        ("buffersize", c_uint32),
        ("reserved", c_uint8 * 24),
    ]


class meta_format(Structure):
    _pack_ = 1
    _fields_ = [
        ("dataformat", c_uint32),
        ("buffersize", c_uint32),
    ]


class _fmt_for_format(Union):
    _fields_ = [
        ("pix", pix_format),
        ("pix_mp", pix_format_mplane),
        ("win", window),
        ("vbi", vbi_format),
        ("sliced", sliced_vbi_format),
        ("sdr", sdr_format),
        ("meta", meta_format),
        ("raw_data", c_uint8 * 200),
    ]


class format(Structure):
    _fields_ = [
        ("type", c_uint32),
        ("fmt", _fmt_for_format),
    ]


class captureparm(Structure):
    _fields_ = [
        ("capability", c_uint32),
        ("capturemode", c_uint32),
        ("timeperframe", fract),
        ("extendedmode", c_uint32),
        ("readbufferbs", c_uint32),
        ("reserved", c_uint32 * 4),
    ]


class outputparm(Structure):
    _fields_ = [
        ("capability", c_uint32),
        ("outputmode", c_uint32),
        ("timeperframe", fract),
        ("extendedmode", c_uint32),
        ("writebuffers", c_uint32),
        ("reserved", c_uint32 * 4),
    ]


class _parm_for_streamparm(Union):
    _fields_ = [
        ("capture", captureparm),
        ("output", outputparm),
        ("raw_data", c_uint8 * 200),
    ]


class streamparm(Structure):
    _fields_ = [
        ("type", c_uint32),
        ("parm", _parm_for_streamparm),
    ]


class control(Structure):
    _fields_ = [
        ("id", c_uint32),
        ("value", c_int32),
    ]


class queryctrl(Structure):
    _fields_ = [
        ("id", c_uint32),
        ("type", c_uint32),
        ("name", c_uint8 * 32),
        ("minimum", c_int32),
        ("maximum", c_int32),
        ("step", c_int32),
        ("default_value", c_int32),
        ("flags", c_uint32),
        ("reserved", c_uint32 * 2),
    ]


class v4l2_query_ext_ctrl(Structure):
    _fields_ = [
        ("id", c_uint32),
        ("type", c_uint32),
        ("name", c_char * 32),
        ("minimum", c_longlong),
        ("maximum", c_longlong),
        ("step", c_int32),
        ("default_value", c_longlong),
        ("flags", c_uint32),
        ("elem_size", c_uint32),
        ("elems", c_uint32),
        ("nr_of_dims", c_uint32),
        ("dims", c_uint32 * 4),
        ("reserved", c_uint32 * 32),
    ]


class requestbuffers(Structure):
    _fields_ = [
        ("count", c_uint32),
        ("type", c_uint32),
        ("memory", c_uint32),
        ("reserved", c_uint32 * 2),
    ]


class exportbuffer(Structure):
    _fields_ = [
        ("type", c_uint32),
        ("index", c_uint32),
        ("plane", c_uint32),
        ("flags", c_uint32),
        ("fd", c_int32),
        ("reserved", c_uint32 * 11),
    ]


class timeval(Structure):
    # TODO: check
    _fields_ = [
        ("sec", c_long),
        ("usec", c_long),
    ]


class timecode(Structure):
    _fields_ = [
        ("type", c_uint32),
        ("flags", c_uint32),
        ("frames", c_uint8),
        ("seconds", c_uint8),
        ("minutes", c_uint8),
        ("hours", c_uint8),
        ("userbits", c_uint8 * 4),
    ]


class _m_for_plane(Union):
    _fields_ = [
        ("mem_offset", c_uint32),
        ("userptr", c_ulong),
        ("fd", c_int32),
    ]


class plane(Structure):
    _fields_ = [
        ("bytesused", c_uint32),
        ("length", c_uint32),
        ("m", _m_for_plane),
        ("data_offset", c_uint32),
        ("reserved", c_uint32 * 11),
    ]


class _m_for_buffer(Union):
    _fields_ = [
        ("offset", c_uint32),
        ("userptr", c_ulong),
        ("planes", POINTER(plane)),
        ("fd", c_int32),
    ]


class _fd_or_reserved(Union):
    _fields_ = [
        ("request_fd", c_int32),
        ("reserved", c_uint32),
    ]


class buffer(Structure):
    _fields_ = [
        ("index", c_uint32),
        ("type", c_uint32),
        ("bytesused", c_uint32),
        ("flags", c_uint32),
        ("field", c_uint32),
        ("timestamp", timeval),
        ("timecode", timecode),
        ("sequence", c_uint32),
        ("memory", c_uint32),
        ("m", _m_for_buffer),
        ("length", c_uint32),
        ("reserved2", c_uint32),
        ("reserved", _fd_or_reserved),
    ]


class mbus_framefmt(Structure):
    _fields_ = [
        ("width", c_uint32),
        ("height", c_uint32),
        ("code", c_uint32),
        ("field", c_uint32),
        ("colorspace", c_uint32),
        ("ycbcr_enc", c_uint16),
        ("quantization", c_uint16),
        ("xfer_func", c_uint16),
        ("reserved", c_uint16 * 11),
    ]


class subdev_format(Structure):
    _fields_ = [
        ("which", c_uint32),
        ("pad", c_uint32),
        ("format", mbus_framefmt),
        ("reserved", c_uint32 * 8),
    ]


class selection(Structure):
    _fields_ = [
        ("type", c_uint32),
        ("target", c_uint32),
        ("flags", c_uint32),
        ("r", rect),
        ("reserved", c_uint32 * 9),
    ]


class _value_for_ext_control(Union):
    _fields_ = [
        ("value", c_int32),
        ("value64", c_int64),
        ("string", c_char_p),
        ("p_u8", POINTER(c_uint8)),
        ("p_u16", POINTER(c_uint16)),
        ("p_u32", POINTER(c_uint32)),
        ("ptr", c_void_p),
    ]


class v4l2_ext_control(Structure):
    _pack_ = 1
    _anonymous_ = ("_value",)
    _fields_ = [
        ("id", c_uint32),
        ("size", c_uint32),
        ("reserved2", c_uint32 * 1),
        ("_value", _value_for_ext_control),
    ]


class _class_or_which_for_ext_controls(Union):
    _fields_ = [
        ("ctrl_class", c_uint32),
        ("which", c_uint32),
    ]


class v4l2_ext_controls(Structure):
    _anonymous_ = ("_class_or_which",)
    _fields_ = [
        ("_class_or_which", _class_or_which_for_ext_controls),
        ("count", c_uint32),
        ("error_idx", c_uint32),
        ("request_fd", c_int32),
        ("reserved", c_uint32),
        ("controls", POINTER(v4l2_ext_control)),
    ]


# ISP statistics structures.
# TODO: decide where to put the following definitions
DEFAULT_AWB_REGIONS_X = 16
DEFAULT_AWB_REGIONS_Y = 12

NUM_HISTOGRAMS = 2
NUM_HISTOGRAM_BINS = 128
AWB_REGIONS = DEFAULT_AWB_REGIONS_X * DEFAULT_AWB_REGIONS_Y
FLOATING_REGIONS = 16
AGC_REGIONS = 16
FOCUS_REGIONS = 12
CONTRAST_NUM_POINTS: int = 33


class bcm2835_isp_gain_format(enum.IntEnum):
    GAIN_FORMAT_U0P8_1 = 0
    GAIN_FORMAT_U1P7_0 = 1
    GAIN_FORMAT_U1P7_1 = 2
    GAIN_FORMAT_U2P6_0 = 3
    GAIN_FORMAT_U2P6_1 = 4
    GAIN_FORMAT_U3P5_0 = 5
    GAIN_FORMAT_U3P5_1 = 6
    GAIN_FORMAT_U4P10 = 7


class bcm2835_isp_black_level(Structure):
    _fields_ = [
        ("enabled", c_uint32),
        ("black_level_r", c_uint16),
        ("black_level_g", c_uint16),
        ("black_level_b", c_uint16),
        ("padding", c_uint8 * 2),
    ]


class bcm2835_isp_gamma(Structure):
    _fields_ = [
        ("enabled", c_uint32),
        ("x", c_uint16 * CONTRAST_NUM_POINTS),
        ("y", c_uint16 * CONTRAST_NUM_POINTS),
    ]


class bcm2835_isp_stats_hist(Structure):
    _fields_ = [
        ("r_hist", c_uint32 * NUM_HISTOGRAM_BINS),
        ("g_hist", c_uint32 * NUM_HISTOGRAM_BINS),
        ("b_hist", c_uint32 * NUM_HISTOGRAM_BINS),
    ]


class bcm2835_isp_stats_region(Structure):
    _fields_ = [
        ("counted", c_uint32),
        ("noncounted", c_uint32),
        ("r_sum", c_uint64),
        ("g_sum", c_uint64),
        ("b_sum", c_uint64),
    ]


class bcm2835_isp_stats_focus(Structure):
    _fields_ = [
        ("contrast_val", c_uint64 * 2 * 2),
        ("contrast_val_num", c_uint32 * 2 * 2),
    ]


class bcm2835_isp_stats_contrast(Structure):
    _fields_ = [
        ("points", c_uint16 * 2 * CONTRAST_NUM_POINTS),
        ("brightness", c_double),
        ("contrast", c_double),
    ]


class bcm2835_isp_stats(Structure):
    _fields_ = [
        ("version", c_uint32),
        ("size", c_uint32),
        ("hist", bcm2835_isp_stats_hist * NUM_HISTOGRAMS),
        ("awb_stats", bcm2835_isp_stats_region * AWB_REGIONS),
        ("floating_stats", bcm2835_isp_stats_region * FLOATING_REGIONS),
        ("agc_stats", bcm2835_isp_stats_region * AGC_REGIONS),
        ("focus_stats", bcm2835_isp_stats_focus * FOCUS_REGIONS),
    ]


class bcm2835_isp_lens_shading(Structure):
    _fields_ = [
        ("enabled", c_uint32),
        ("grid_cell_size", c_uint32),
        ("grid_width", c_uint32),
        ("grid_stride", c_uint32),
        ("grid_height", c_uint32),
        ("dmabuf", c_int32),
        ("ref_transform", c_uint32),
        ("corner_sampled", c_uint32),
        ("gain_format", c_uint32),
    ]
