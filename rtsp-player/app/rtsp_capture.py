# Direct RTSP streaming using GStreamer

import os
import sys

if True:
    # Set stderr line buffering mode.
    sys.stderr = os.fdopen(sys.stderr.fileno(), "w", buffering=1)

# Uncomment when debug gstreamer
# os.environ['GST_DEBUG'] = '4'

from typing import Dict

import actfw_gstreamer.gstreamer.preconfigured_pipeline as preconfigured_pipeline
from actfw_gstreamer.capture import GstreamerCapture
from actfw_gstreamer.gstreamer.converter import ConverterPIL
from actfw_gstreamer.gstreamer.stream import GstStreamBuilder
from actfw_gstreamer.restart_handler import SimpleRestartHandler


def make_rtsp_capture(rtsp_url: str, caps: Dict[str, int], decoder_type: str):
    """
    Make `GstreamerCapture` task that reads RTSP directly.

    Parameters
    ----------
    rtsp_url     : str
        RTSP URL
        e.g. rtsp://192.168.1.1:554/test
    caps         : dict, { 'width': int, 'height': int, 'framerate': int }
        Caps of appsink
    decoder_type : str, 'v4l2' | 'omx'
        Type of decoder
    """
    # Direct RTSP connection without proxy
    pipeline_generator = preconfigured_pipeline.rtsp_h264(
        None,  # proxy=None for direct connection
        rtsp_url,
        "tcp",
        decoder_type,
        caps
    )
    builder = GstStreamBuilder(pipeline_generator, ConverterPIL())

    connection_lost_secs_threshold = 10
    error_count_threshold = 5
    restart_handler = SimpleRestartHandler(
        connection_lost_secs_threshold, error_count_threshold
    )
    return GstreamerCapture(builder, restart_handler)
