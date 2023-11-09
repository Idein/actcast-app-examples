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
from typing import Dict
from urllib.parse import urlparse, urlunparse

import actfw_gstreamer.gstreamer.preconfigured_pipeline as preconfigured_pipeline
from actfw_gstreamer.capture import GstreamerCapture
from actfw_gstreamer.gstreamer.converter import ConverterPIL
from actfw_gstreamer.gstreamer.stream import GstStreamBuilder
from actfw_gstreamer.restart_handler import SimpleRestartHandler


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


def make_rtsp_capture(rtsp_url: str, caps: Dict[str, int], decoder_type: str):
    """
    Make `GstreamerCapture` task that read RTSP.

    Parameters
    ----------
    rtsp_url     : url
        RTSP url
        e.g. tcp://127.0.0.1:1081,
    caps         : dict, { 'width': int, 'height': int, 'framerate': int }
        caps of appsink
    decoder_type : 'v4l2' | 'omx'
        type of decoder
    """
    tcp2socksd_bind = urlparse("tcp://127.0.0.1:1081")
    start_tcp2socksd(
        urlunparse(tcp2socksd_bind),
        f"socks5h://{os.environ['ACTCAST_SOCKS_SERVER']}",
        f"tcp://{urlparse(rtsp_url).netloc}",
    )
    proxy_url = tcp2socksd_bind.netloc
    pipeline_generator = preconfigured_pipeline.rtsp_h264(
        proxy_url, rtsp_url, "tcp", decoder_type, caps
    )
    builder = GstStreamBuilder(pipeline_generator, ConverterPIL())

    connection_lost_secs_threshold = 10
    error_count_threshold = 5
    restart_handler = SimpleRestartHandler(
        connection_lost_secs_threshold, error_count_threshold
    )
    return GstreamerCapture(builder, restart_handler)
