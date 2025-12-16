import os
from queue import Queue, Empty, Full
import traceback
from actfw_core.task import Isolated
import numpy as np
import gi

if gi:
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)


class KinesisVideoStream(Isolated):
    def __init__(self, resolution, stream_name, region, access_key, secret_key, bitrate=None):
        super(KinesisVideoStream, self).__init__()
        self.running = True
        self.in_queue = Queue(maxsize=2)
        self.out_queue = Queue()
        self.data = []
        self.resolution = resolution

        self._is_push_buffer_allowed = False

        dirname = os.path.dirname(os.path.abspath(__file__))
        # https://docs.aws.amazon.com/ja_jp/kinesisvideostreams/latest/dg/examples-gstreamer-plugin-parameters.html
        if is_raspberry_pi_5_from_cpuinfo():
            # pi5 にはハードウェアエンコーダがないため、ソフトウェアエンコーダを使用する
            # bitrate は x264enc だと kbps 指定（例: 2000 = 2Mbps）
            bitrate_s = f"bitrate={bitrate // 1000}," if bitrate is not None else ""
            pipeline = " ! ".join(
                [
                  "appsrc name=source is-live=true do-timestamp=true format=time",
                  f"video/x-raw,format=RGB,width={resolution[0]},height={resolution[1]},framerate=5/1",
                  "videoconvert",
                  "video/x-raw,format=I420",
                  f"x264enc tune=zerolatency speed-preset=ultrafast key-int-max=17 bframes=0 {bitrate_s}",
                  "h264parse config-interval=-1",
                  "video/x-h264,stream-format=avc,alignment=au",
                  f'kvssink log-config="{dirname}/log.cfg" stream-name={stream_name}',
                ]
            )
        else:
            bitrate_s = f"video_bitrate={bitrate}," if bitrate is not None else ""
            pipeline = " ! ".join(
                [
                    "appsrc name=source",
                    f'video/x-raw,format=RGB,width={resolution[0]},height={resolution[1]},bpp=24,depth=24,framerate=5/1',
                    f'capssetter replace=true caps="video/x-raw,format=RGB,width={resolution[0]},height={resolution[1]}"',
                    'v4l2convert',
                    f'v4l2h264enc extra-controls="encode,{bitrate_s}repeat_sequence_header=0,h264_i_frame_period=17"',
                    'video/x-h264,level=(string)4',  # https://github.com/raspberrypi/linux/issues/3974
                    "h264parse",
                    "video/x-h264,stream-format=avc,alignment=au",
                    f'kvssink log-config="{dirname}/log.cfg" stream-name={stream_name}',
                ]
            )
        if region is not None and region != "":
            pipeline += f' aws-region="{region}"'
        if access_key is not None and access_key != "":
            pipeline += f' access-key="{access_key}"'
        if secret_key is not None and secret_key != "":
            pipeline += f' secret-key="{secret_key}"'
        self._pipeline = Gst.parse_launch(pipeline)

        self._src = self._pipeline.get_by_name("source")
        self._src.connect("need-data", self.start_feed)
        self._src.connect("enough-data", self.stop_feed)

        self._src.set_property("format", "time")
        self._src.set_property("do-timestamp", True)
        self._src.set_property("is-live", True)

    def add_image(self, data):
        try:
            self.in_queue.put_nowait((data,))
        except Full:
            pass
        except:
            traceback.print_exc()

    def get_result(self):
        try:
            return self.out_queue.get_nowait()
        except Empty:
            pass
        except:
            traceback.print_exc()

    def run(self):
        while self.running:
            try:
                (data,) = self.in_queue.get(timeout=1)
                _result = self.push(data)
            except Empty:
                pass
            except GeneratorExit:
                break
            except:
                traceback.print_exc()

    def start_feed(self, src, length):
        self._is_push_buffer_allowed = True

    def stop_feed(self, src):
        self._is_push_buffer_allowed = False

    def play(self):
        self._pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.running = False
        self._pipeline.set_state(Gst.State.NULL)

    def push(self, image):
        if not self._is_push_buffer_allowed:
            return False

        image = image.resize(self.resolution)

        result = self._src.emit(
            "push-buffer", Gst.Buffer.new_wrapped(np.array(image).tobytes())
        )

        # print("result", result)

        if result != Gst.FlowReturn.OK:
            raise RuntimeError("Failed to push sample")
        return


def is_raspberry_pi_5_from_cpuinfo(path="/proc/cpuinfo") -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("Model"):
                    model = line.split(":", 1)[1].strip()
                    return "Raspberry Pi 5" in model
    except FileNotFoundError:
        pass
    return False
