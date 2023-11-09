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
    def __init__(self, resolution, stream_name, region, access_key, secret_key):
        super(KinesisVideoStream, self).__init__()
        self.running = True
        self.in_queue = Queue(maxsize=2)
        self.out_queue = Queue()
        self.data = []
        self.resolution = resolution

        self._is_push_buffer_allowed = False

        dirname = os.path.dirname(os.path.abspath(__file__))
        # https://docs.aws.amazon.com/ja_jp/kinesisvideostreams/latest/dg/examples-gstreamer-plugin-parameters.html
        pipeline = " ! ".join(
            [
                "appsrc name=source",
                f"video/x-raw,format=RGB,width={resolution[0]},height={resolution[1]},bpp=24,depth=24,framerate=5/1",
                "videoconvert",
                "omxh264enc periodicty-idr=17 inline-header=FALSE",
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
