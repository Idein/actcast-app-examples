"""Reusable Act-setting adapter with optional actfw-core white-balance support."""

import importlib
import inspect
import logging
import math


_LOG = logging.getLogger(__name__)


AWB_DEFAULTS = {
    "awb_mode": "auto",
    "awb_gain_r": 1.6,
    "awb_gain_b": 1.6,
    "awb_k": 0.45,
}
AWB_PRESETS = {
    "incandescent": "Incandescent",
    "tungsten": "Tungsten",
    "fluorescent": "Fluorescent",
    "indoor": "Indoor",
    "daylight": "Daylight",
    "cloudy": "Cloudy",
    "custom": "Custom",
}


def awb_number(settings, name):
    value = settings.get(name, AWB_DEFAULTS[name])
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


def get_awb_mode(settings):
    """Validate and return the mode; importing this module needs no camera libraries."""
    mode = settings.get("awb_mode", "auto")
    if mode not in ("auto", "manual", "greyworld", *AWB_PRESETS):
        raise ValueError(f"Unknown awb_mode: {mode!r}")
    return mode


def make_awb_settings(settings):
    """Convert Act settings to a LibcameraCapture awb argument.

    Call this only for a LibcameraCapture camera, before constructing the capture.
    Imports are lazy so applications can still support OS3 and USB cameras.
    Unrelated settings are ignored; missing AWB fields use AWB_DEFAULTS.
    """
    # Keep libcamera imports inside the OS4 CSI path for OS3/USB compatibility.
    import libcamera
    capture_api = importlib.import_module("actfw_core.libcamera_capture")

    mode = get_awb_mode(settings)
    if mode == "auto":
        return capture_api.Auto.AUTO
    if mode in ("manual", "greyworld"):
        gain_r = awb_number(settings, "awb_gain_r")
        gain_b = awb_number(settings, "awb_gain_b")
        if mode == "manual":
            return capture_api.AwbManual(gain_r, gain_b)
        return capture_api.AwbGreyWorld(gain_r, gain_b, awb_number(settings, "awb_k"))
    return getattr(libcamera.controls.AwbModeEnum, AWB_PRESETS[mode])


def make_awb_options(settings, capture_class):
    """Return optional constructor keywords, falling back on older APIs.

    Use ``LibcameraCapture(..., **make_awb_options(settings, LibcameraCapture))``.
    Missing AWB support logs a warning and returns {}, leaving the installed
    capture implementation's defaults untouched. Detection is per requested mode
    and does not depend on package version strings. Camera construction and
    setting errors are deliberately not caught or retried.
    """
    mode = get_awb_mode(settings)
    reason = None
    try:
        parameter = inspect.signature(capture_class).parameters.get("awb")
    except (TypeError, ValueError):
        parameter = None
    if parameter is None or parameter.kind not in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY
    ):
        reason = "LibcameraCapture has no explicit awb keyword parameter"
    else:
        capture_api = importlib.import_module("actfw_core.libcamera_capture")
        if mode == "auto":
            if not hasattr(getattr(capture_api, "Auto", None), "AUTO"):
                reason = "Auto.AUTO is unavailable"
        elif mode in ("manual", "greyworld"):
            name = "AwbManual" if mode == "manual" else "AwbGreyWorld"
            if not callable(getattr(capture_api, name, None)):
                reason = f"{name} is unavailable"
        else:
            import libcamera
            enum = getattr(getattr(libcamera, "controls", None), "AwbModeEnum", None)
            if not hasattr(enum, AWB_PRESETS[mode]):
                reason = f"AwbModeEnum.{AWB_PRESETS[mode]} is unavailable"

    if reason is not None:
        _LOG.warning(
            "AWB mode %r was not applied: %s; using the installed "
            "LibcameraCapture defaults (legacy behavior).", mode, reason
        )
        return {}
    return {"awb": make_awb_settings(settings)}
