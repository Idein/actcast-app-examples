# ## How it works
#
#     +-------------+
#     | RTSP server |
#     +------+------+
#            | <rtsp-location> (e.g. rtsp://192.168.1.1:554/test)
#            |
#     +-------------+
#     | socksserver |
#     +------+------+
#            | socks5h://${ACTCAST_SOCKS_SERVER}
#            |
#     +------+------+
#     |  tcp2socksd |
#     +------+------+
#            | tcp://127.0.0.1:1081
#            |
#     +------+------+
#     |     Act     |
#     +------+------+
#
# This application read RTSP (RTP/RTCP) using TCP connection.
# Network connection of act is restricted and we must use tpc2socksd to relay the streaming.

import os
import sys

if True:
    # Set stderr line buffering mode.
    sys.stderr = os.fdopen(sys.stderr.fileno(), "w", buffering=1)

# Uncomment when debug gstreamer
# os.environ['GST_DEBUG'] = '4'

import errno
import subprocess
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse

import actfw_gstreamer.gstreamer.preconfigured_pipeline as preconfigured_pipeline
from actfw_core.system import get_actcast_firmware_type
from actfw_gstreamer.capture import GstreamerCapture
from actfw_gstreamer.gstreamer.converter import ConverterPIL, ConverterRaw
from actfw_gstreamer.gstreamer.stream import (
    GstStreamBuilder,
    Inner,
    _BuiltPipeline,
    _GstStream,
)
from actfw_gstreamer.restart_handler import RestartHandlerBase, SimpleRestartHandler

import gi  # noqa isort:skip
gi.require_version('Gst', '1.0')  # noqa isort:skip
from gi.repository import Gst  # noqa isort:skip


class RTSPCaptureBuilder(GstStreamBuilder):
    def __init__(self, width: int, height: int, rtsp_url: str, proxy_url: Optional[str] = None, protocol: Optional[str] = None):
        add_props = "" if proxy_url is None else f"protocols={protocol} proxy={proxy_url}"
        caps_str = f"capssetter replace=true caps=\"video/x-h264, width=(int){width}, height=(int){height}, stream-format=(string)byte-stream, alignment=(string)au, profile=(string)baseline, level=(string)4\" ! " if get_actcast_firmware_type() == "raspberrypi-bullseye" else ""
        self.rtspsrc = f"""rtspsrc location="{rtsp_url}" {add_props} latency=0 max-rtcp-rtp-time-diff=100 drop-on-latency=true"""
        pipeline_str = f"""\
        {self.rtspsrc} ! queue ! rtph264depay ! h264parse ! {caps_str} v4l2h264dec ! \
        v4l2convert ! \
        video/x-raw,format=RGB ! \
        appsink emit-signals=true max-buffers=1 drop=true sync=false
        """
        print(pipeline_str)
        self.pipeline = Gst.parse_launch(pipeline_str)
        appsink = self.pipeline.get_by_name("appsink0")
        self.built_pipeline = _BuiltPipeline(self.pipeline, appsink)
        self.converter = ConverterPIL()

    def start_streaming(self) -> "_GstStream":  # noqa F821 (Hey linter, see below.)
        inner = Inner(self.built_pipeline, self.converter)
        return _GstStream(inner)


class RTSPCapture(GstreamerCapture):
    def __init__(self,
                 width: int,
                 height: int,
                 rtsp_url: str,
                 proxy_url: Optional[str],
                 protocol: Optional[str],
                 restart_handler: RestartHandlerBase):
        builder = RTSPCaptureBuilder(width, height, rtsp_url, proxy_url, protocol)
        super(RTSPCapture, self).__init__(
            builder=builder, restart_handler=restart_handler)


def start_tcp2socksd(bind, socks5, server):
    """
    start tcp -> socks relay process

    Parameters
    ----------
    bind   : url
        bind address of tcp2socksd process
        e.g. tcp://127.0.0.1:1081,
    socks5 : url
        url of socks5 server
        e.g. socks5h://{os.environ['ACTCAST_SOCKS_SERVER']}
    server : url
        url of target server
    """
    TCP2SOCKSD_BIN = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "bin/tcp2socksd"
    )
    if not os.path.exists(TCP2SOCKSD_BIN):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), TCP2SOCKSD_BIN)
    command = [TCP2SOCKSD_BIN, bind, socks5, server]

    # 標準出力の場合はすべて Act Log として扱われるため、このようなデバッグ用途の print は標準エラー出力に print する
    print(
        f"start tcp2socksd proxy: {bind} {socks5} {server}", file=sys.stderr, flush=True
    )

    p = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # 起動完了するまで待つ
        p.wait(1)
    except:
        pass

    if p.returncode is None:
        return
    else:
        raise Exception(
            f"command exited unexpectedly: command = {command}, status code = {p.returncode}"
        )


def make_rtsp_capture(width: int, height: int, rtsp_url: str):
    """
    Make `GstreamerCapture` task that read RTSP.

    Parameters
    ----------
    rtsp_url     : url
        RTSP url
        e.g. tcp://127.0.0.1:1081,
"""
    tcp2socksd_bind = urlparse("tcp://127.0.0.1:1081")
    start_tcp2socksd(
        urlunparse(tcp2socksd_bind),
        f"socks5h://{os.environ['ACTCAST_SOCKS_SERVER']}",
        f"tcp://{urlparse(rtsp_url).netloc}"
    )
    proxy_url = tcp2socksd_bind.netloc
    protocol = "tcp"
    connection_lost_secs_threshold = 10
    error_count_threshold = 5
    restart_handler = SimpleRestartHandler(
        connection_lost_secs_threshold, error_count_threshold
    )
    capture = RTSPCapture(width, height, rtsp_url, proxy_url, protocol, restart_handler)
    return capture
