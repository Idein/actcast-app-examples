#!/usr/bin/env python3
"""GStreamer WebRTC publisher with Actcast Custom Command signaling.

Branches (MEDIA_TYPE=video|audio|both):
  video: frames reach the streaming pipeline through appsrc, not
         from a source element. A separate capture pipeline
         (libcamerasrc, or videotestsrc when VIDEO_SRC=test) ends
         in appsink; a pump thread pulls each frame through
         process_frame() -- the hook where upstream processing
         such as Hailo inference plugs in -- and pushes it on to
         appsrc. On device the encoder is the VideoCore hardware
         encoder, with the same recipe as the
         amazon-kinesis-video-streams example:
           appsrc -> v4l2convert -> v4l2h264enc -> (level=4 caps)
                  -> h264parse -> rtph264pay -> webrtcbin
         (Without the level caps the codec refuses to start
         streaming. The test branch swaps the encoder chain for
         videoconvert/x264enc so the logic also runs on machines
         without the VideoCore codec.)
  audio (device): alsasrc      -> opusenc -> rtpopuspay -> webrtcbin
  audio (test):   audiotestsrc -> opusenc -> rtpopuspay -> webrtcbin
If MEDIA_TYPE=both on a unit with no ALSA capture device, the audio
branch is dropped (with a loud log line) instead of failing the video.

Signaling runs over Actcast Custom Command (see command_bridge.py);
no separate signaling server is needed. The viewer drives the
session with JSON commands:
  {"op": "offer"}             -> {"sdp": "<complete SDP>"}
  (with "restart": true, offer forces a fresh session)
  {"op": "answer", "sdp": ..} -> {"ok": true}
  {"op": "status"}            -> session / ICE state
  {"op": "reset"}             -> tear the session down
ICE is non-trickle: the offer waits for gathering to complete and
embeds the candidates in the SDP. STUN only, no TURN.
"""

import glob
import json
import os
import secrets
import sys
import threading
import time

import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstWebRTC", "1.0")
gi.require_version("GstSdp", "1.0")
from gi.repository import GLib, Gst, GstSdp, GstWebRTC  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from command_bridge import CommandBridge  # noqa: E402

Gst.init(None)

VIDEO_SRC = os.environ.get("VIDEO_SRC", "test")
MEDIA_TYPE = os.environ.get("MEDIA_TYPE", "both").lower()
STUN = os.environ.get("STUN", "stun://stun.l.google.com:19302")
VIDEO_CAPS_STR = (
    "video/x-raw,format=NV12,width=1280,height=720,framerate=30/1"
)


def log(msg):
    print("[pub] %s" % msg, flush=True)


def has_capture_device():
    # Docker masks /proc/asound inside the app container, so check
    # the ALSA capture device nodes that the sound device declaration
    # maps in instead (pcmC<card>D<device>c = capture).
    return bool(glob.glob("/dev/snd/pcmC*D*c"))


def effective_media_type():
    mt = MEDIA_TYPE if MEDIA_TYPE in ("video", "audio", "both") else "both"
    if mt in ("audio", "both") and VIDEO_SRC == "camera":
        if not has_capture_device():
            if mt == "both":
                log("NO ALSA capture device: falling back to video only")
                return "video"
            log("NO ALSA capture device: audio requested but unavailable")
    return mt


def process_frame(data):
    """Per-frame hook on the way from capture to the encoder.

    Receives one raw frame (see VIDEO_CAPS_STR) as bytes and
    returns the frame to publish, or None to drop the frame.
    This is where upstream processing plugs in: run inference
    (e.g. Hailo) over the frame, draw results on it, gate it --
    the streaming code below does not care. Returned bytes must
    match the appsrc caps (same format and size).
    """
    return data


class FrameSource:
    """Capture as a pipeline of its own, ending in appsink.

    Keeping capture separate from the streaming pipeline is what
    lets frames pass through Python (process_frame) on their way
    to appsrc: in a real application the frames would come from
    the app's own capture/inference loop instead of this helper.
    """

    def __init__(self):
        if VIDEO_SRC == "camera":
            desc = (
                "libcamerasrc ! " + VIDEO_CAPS_STR
                + " ! appsink name=fsink"
            )
        else:
            desc = (
                "videotestsrc is-live=true pattern=ball ! "
                + VIDEO_CAPS_STR + " ! appsink name=fsink"
            )
        self.pipeline = Gst.parse_launch(desc)
        self.sink = self.pipeline.get_by_name("fsink")
        self.sink.set_property("emit-signals", False)
        self.sink.set_property("sync", False)
        self.sink.set_property("max-buffers", 2)
        self.sink.set_property("drop", True)

    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def pull_frame(self):
        """One frame as bytes, or None on timeout."""
        sample = self.sink.emit("try-pull-sample", 500 * Gst.MSECOND)
        if sample is None:
            return None
        buf = sample.get_buffer()
        ok, mapinfo = buf.map(Gst.MapFlags.READ)
        if not ok:
            return None
        try:
            return bytes(mapinfo.data)
        finally:
            buf.unmap(mapinfo)

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)


def build_description(mt):
    parts = [
        "webrtcbin name=wb bundle-policy=max-bundle stun-server=" + STUN
    ]
    if mt in ("video", "both"):
        head = (
            "appsrc name=vsrc is-live=true format=time "
            "do-timestamp=true block=false max-bytes=13824000 "
            "caps=" + VIDEO_CAPS_STR + " ! "
        )
        if VIDEO_SRC == "camera":
            encode = (
                "v4l2convert ! "
                "v4l2h264enc extra-controls=\"encode,"
                "video_bitrate=2500000,repeat_sequence_header=0,"
                "h264_i_frame_period=30\" ! "
                "video/x-h264,level=(string)4 ! h264parse ! "
            )
        else:
            encode = (
                "videoconvert ! x264enc tune=zerolatency "
                "speed-preset=ultrafast key-int-max=30 "
                "bitrate=2000 ! "
            )
        parts.append(
            head + encode
            + "rtph264pay config-interval=1 pt=96 ! "
            "application/x-rtp,media=video,encoding-name=H264,"
            "payload=96 ! wb."
        )
    if mt in ("audio", "both"):
        src = "alsasrc" if VIDEO_SRC == "camera" else (
            "audiotestsrc is-live=true wave=sine freq=440"
        )
        parts.append(
            src + " ! audioconvert ! audioresample ! "
            "opusenc bitrate=32000 ! rtpopuspay pt=97 ! "
            "application/x-rtp,media=audio,encoding-name=OPUS,"
            "payload=97 ! wb."
        )
    return " ".join(parts)


def inject_candidates(sdp_text, candidates):
    """Insert gathered candidates into the first m-section of an SDP
    that does not carry them yet (non-trickle fallback)."""
    if "a=candidate" in sdp_text or not candidates:
        return sdp_text
    lines = [ln.rstrip("\r") for ln in sdp_text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    insert_at = len(lines)
    seen_m = 0
    for i, ln in enumerate(lines):
        if ln.startswith("m="):
            seen_m += 1
            if seen_m == 2:
                insert_at = i
                break
    block = ["a=" + c["cand"] for c in candidates]
    block.append("a=end-of-candidates")
    lines[insert_at:insert_at] = block
    return "\r\n".join(lines) + "\r\n"


class Publisher:
    def __init__(self):
        self.pipeline = None
        self.wb = None
        self.sid = None
        self.candidates = []
        self.answer_applied = False
        self.lock = threading.Lock()
        self.bus = None
        self.offer_lock = threading.Lock()
        self.start_pending = False
        self.started = threading.Event()
        self.gather_done = threading.Event()
        self.final_offer = None
        self.start_error = None
        self.appsrc = None
        self.source = None
        self.pump = None
        self.pump_stop = threading.Event()

    def start_session(self, sid):
        with self.lock:
            self._teardown_locked()
            self.sid = sid
            self.candidates = []
            self.answer_applied = False
            mt = effective_media_type()
            log("starting session sid=%s media=%s" % (sid, mt))
            self.started.clear()
            self.gather_done.clear()
            self.final_offer = None
            self.start_error = None
            try:
                desc = build_description(mt)
                self.pipeline = Gst.parse_launch(desc)
            except Exception as e:
                log("pipeline build failed: %r" % (e,))
                self.start_error = str(e)
                self._teardown_locked()
                self.started.set()
                return
            self.wb = self.pipeline.get_by_name("wb")
            self.wb.connect("on-negotiation-needed", self._on_negotiation)
            self.wb.connect("on-ice-candidate", self._on_ice_candidate)
            self.wb.connect(
                "notify::ice-connection-state", self._on_ice_state
            )
            self.wb.connect("notify::connection-state", self._on_conn_state)
            self.wb.connect(
                "notify::ice-gathering-state", self._on_gathering_state
            )
            self.bus = self.pipeline.get_bus()
            self.bus.add_signal_watch()
            self.bus.connect("message", self._on_bus_message)
            self.pipeline.set_state(Gst.State.PLAYING)
            if mt in ("video", "both"):
                try:
                    self.appsrc = self.pipeline.get_by_name("vsrc")
                    self.source = FrameSource()
                    self.source.start()
                except Exception as e:
                    log("frame source failed: %r" % (e,))
                    self.start_error = str(e)
                    self._teardown_locked()
                    self.started.set()
                    return
                self.pump_stop.clear()
                self.pump = threading.Thread(
                    target=self._pump_loop, daemon=True
                )
                self.pump.start()
            self.started.set()

    def _pump_loop(self):
        while not self.pump_stop.is_set():
            data = self.source.pull_frame()
            if data is None:
                continue
            data = process_frame(data)
            if data is None:
                continue
            buf = Gst.Buffer.new_wrapped(data)
            ret = self.appsrc.emit("push-buffer", buf)
            if ret != Gst.FlowReturn.OK:
                if not self.pump_stop.is_set():
                    log("appsrc push returned %s" % (ret,))
                return

    def _teardown_locked(self):
        self.pump_stop.set()
        if self.source is not None:
            self.source.stop()
            self.source = None
        if self.pump is not None:
            self.pump.join(timeout=2)
            self.pump = None
        self.appsrc = None
        if self.bus is not None:
            self.bus.remove_signal_watch()
            self.bus = None
        if self.pipeline is not None:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            self.wb = None

    def stop(self):
        with self.lock:
            self._teardown_locked()

    def _on_negotiation(self, wb):
        log("negotiation needed")
        promise = Gst.Promise.new_with_change_func(
            self._on_offer_created, None
        )
        wb.emit("create-offer", None, promise)

    def _on_offer_created(self, promise, _user_data=None):
        reply = promise.get_reply()
        offer = reply.get_value("offer")
        promise2 = Gst.Promise.new()
        self.wb.emit("set-local-description", offer, promise2)
        promise2.interrupt()
        sdp_text = offer.sdp.as_text()
        log("offer created (%d bytes)" % len(sdp_text))

    def _on_ice_candidate(self, wb, mline, cand):
        with self.lock:
            self.candidates.append({"mline": mline, "cand": cand})
        if "srflx" in cand:
            log("srflx candidate gathered")

    def _on_gathering_state(self, wb, _param):
        state = wb.get_property("ice-gathering-state")
        log("ice-gathering-state=%s" % state)
        if "COMPLETE" in str(state):
            desc = wb.get_property("local-description")
            text = desc.sdp.as_text() if desc is not None else ""
            with self.lock:
                snapshot = list(self.candidates)
            self.final_offer = inject_candidates(text, snapshot)
            if "a=candidate" in self.final_offer:
                log("final offer ready (%d bytes, candidates embedded)"
                    % len(self.final_offer))
            else:
                log("final offer ready but NO candidates embedded")
            # Insurance for the actdk run -a log-reading path.
            print("===OFFER_BEGIN===", flush=True)
            print(self.final_offer, flush=True)
            print("===OFFER_END===", flush=True)
            self.gather_done.set()

    def _on_bus_message(self, _bus, msg):
        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            log("pipeline error from %s: %s (%s)"
                % (msg.src.get_name(), err.message, dbg))
        elif msg.type == Gst.MessageType.EOS:
            log("pipeline EOS")

    def _on_ice_state(self, wb, _param):
        log("ice-connection-state=%s" % wb.get_property("ice-connection-state"))

    def _on_conn_state(self, wb, _param):
        log("connection-state=%s" % wb.get_property("connection-state"))

    def apply_answer(self, sdp_text):
        if self.wb is None or self.answer_applied:
            return False
        res, sdpmsg = GstSdp.SDPMessage.new_from_text(sdp_text)
        # GstSdp parses leniently: even garbage text yields GST_SDP_OK
        # with zero media sections, so check the shape explicitly.
        if (res != GstSdp.SDPResult.OK or sdpmsg is None
                or sdpmsg.medias_len() == 0
                or "a=ice-ufrag:" not in sdp_text):
            log("answer SDP is not a usable WebRTC answer")
            return False
        answer = GstWebRTC.WebRTCSessionDescription.new(
            GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg
        )
        # Do not discard the promise: a rejection by webrtcbin itself
        # (e.g. media sections that do not match the offer) is only
        # reported through it, and the connection state stays NEW.
        done = threading.Event()
        outcome = {}

        def on_applied(promise, _user_data=None):
            # On success webrtcbin replies with no structure at all;
            # a rejection carries a structure with an "error" field.
            err = None
            try:
                reply = promise.get_reply()
                if reply is not None and reply.has_field("error"):
                    err = reply.get_value("error")
            except Exception as e:
                err = e
            outcome["error"] = err
            done.set()

        promise = Gst.Promise.new_with_change_func(on_applied, None)
        self.wb.emit("set-remote-description", answer, promise)
        # apply_answer runs on the main-loop thread; pump the context
        # while waiting so the other callbacks keep flowing.
        ctx = GLib.MainContext.default()
        deadline = time.monotonic() + 10
        while not done.is_set():
            if time.monotonic() > deadline:
                log("set-remote-description timed out")
                return False
            while ctx.pending():
                ctx.iteration(False)
            done.wait(0.02)
        if outcome.get("error") is not None:
            log("webrtcbin rejected the answer: %s" % (outcome["error"],))
            return False
        self.answer_applied = True
        log("answer applied")
        return True

    # ---------- Custom Command entry points (bridge threads) ----------
    def command_offer(self, restart=False, timeout=30):
        # The restart decision, the event clearing and the start
        # scheduling must be atomic: command handlers can be called
        # concurrently, and two threads that both decide to start
        # would start (and tear down) two sessions. A caller that
        # finds a start already scheduled joins that session instead.
        with self.offer_lock:
            need_start = (
                restart or self.wb is None or self.answer_applied
            )
            if need_start and not self.start_pending:
                self.start_pending = True
                # Clear the events BEFORE scheduling the start: they
                # may still be set from a previous session, and
                # waiting on them would return that session's SDP.
                self.started.clear()
                self.gather_done.clear()
                self.final_offer = None

                def ensure():
                    try:
                        self.start_session(
                            "cmd-" + secrets.token_hex(4))
                    finally:
                        with self.offer_lock:
                            self.start_pending = False
                    return False

                GLib.idle_add(ensure)
        if need_start:
            if not self.started.wait(timeout=10):
                return {"error": "session start timed out"}
            if self.start_error:
                return {"error": "session start failed: %s"
                        % self.start_error}
        if not self.gather_done.wait(timeout=timeout):
            return {"error": "ice gathering timed out"}
        return {"sdp": self.final_offer}

    def command_answer(self, sdp_text, timeout=15):
        done = threading.Event()
        result = {}

        def apply():
            result["ok"] = self.apply_answer(sdp_text)
            done.set()
            return False

        GLib.idle_add(apply)
        if not done.wait(timeout=timeout):
            return {"error": "apply answer timed out"}
        if not result.get("ok"):
            return {"error": "answer rejected (no session, already "
                             "applied, or unparsable SDP)"}
        return {"ok": True}

    def command_reset(self, timeout=10):
        done = threading.Event()

        def do_reset():
            with self.lock:
                old = self.sid
                self._teardown_locked()
                self.sid = None
                self.candidates = []
                self.answer_applied = False
                self.final_offer = None
                self.start_error = None
            self.started.clear()
            self.gather_done.clear()
            log("reset done (was sid=%s)" % old)
            done.set()
            return False

        GLib.idle_add(do_reset)
        if not done.wait(timeout=timeout):
            return {"error": "reset timed out"}
        return {"ok": True, "reset": True}

    def command_status(self):
        with self.lock:
            wb = self.wb
            sid = self.sid
            ncand = len(self.candidates)
        if wb is None:
            return {"session": None}
        status = {"session": sid, "candidates": ncand}
        try:
            status["ice"] = str(wb.get_property("ice-connection-state"))
            status["connection"] = str(
                wb.get_property("connection-state"))
            status["gathering"] = str(
                wb.get_property("ice-gathering-state"))
        except Exception as e:
            status["error"] = "state read failed: %r" % (e,)
        return status

    def handle_command(self, payload):
        req = json.loads(payload) if payload else {}
        op = req.get("op")
        log("command op=%s" % op)
        if op == "offer":
            return json.dumps(
                self.command_offer(restart=bool(req.get("restart")))
            )
        if op == "answer":
            sdp = req.get("sdp") or ""
            if not sdp:
                return json.dumps({"error": "missing sdp"})
            return json.dumps(self.command_answer(sdp))
        if op == "status":
            return json.dumps(self.command_status())
        if op == "reset":
            return json.dumps(self.command_reset())
        return json.dumps({"error": "unknown op: %s" % op})


def main():
    pub = Publisher()
    bridge = CommandBridge(pub.handle_command)
    if not bridge.start():
        log("ACTCAST_COMMAND_SOCK is not set; cannot serve commands")
        sys.exit(1)
    log("command mode: session starts on first offer command")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    bridge.stop()
    pub.stop()


if __name__ == "__main__":
    main()
