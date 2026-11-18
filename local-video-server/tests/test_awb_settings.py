"""Tests for settings conversion and camera routing, without camera hardware."""

import importlib.util
import inspect
import json
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import Mock, patch

import jsonschema

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "app"))
import awb_settings


class AwbTests(unittest.TestCase):
    def setUp(self):
        self.libcamera = types.ModuleType("libcamera")
        self.presets = types.SimpleNamespace(**{name: object() for name in awb_settings.AWB_PRESETS.values()})
        self.libcamera.controls = types.SimpleNamespace(AwbModeEnum=self.presets)
        self.libcamera.PixelFormat = Mock(side_effect=lambda fmt: fmt)
        self.capture = types.ModuleType("actfw_core.libcamera_capture")
        self.auto = object()
        self.capture.Auto = types.SimpleNamespace(AUTO=self.auto)
        self.capture.AwbManual = Mock(side_effect=lambda r, b: ("manual", r, b))
        self.capture.AwbGreyWorld = Mock(side_effect=lambda r, b, k: ("greyworld", r, b, k))
        self.capture.LibcameraCapture = Mock()
        self.capture.LibcameraCapture.__signature__ = inspect.Signature([
            inspect.Parameter("awb", inspect.Parameter.KEYWORD_ONLY, default=None),
        ])
        self.capture.find_csi_camera_index = Mock(return_value=0)
        self.capture.SensorConfig = Mock(side_effect=lambda **kw: types.SimpleNamespace(**kw))
        self.capture.ScalerCrop = Mock(side_effect=lambda **kw: types.SimpleNamespace(**kw))
        self.cameras = [types.SimpleNamespace(id="platform/soc/imx219@10")]
        self.libcamera.CameraManager = types.SimpleNamespace(singleton=Mock(return_value=types.SimpleNamespace(cameras=self.cameras)))
        self.core = types.ModuleType("actfw_core")
        self.core.__path__ = []
        self.core.Application = Mock()
        self.core.CommandServer = Mock()
        self.core.LocalVideoServer = Mock()
        self.system = types.ModuleType("actfw_core.system")
        self.system.get_actcast_firmware_type = Mock(return_value="raspberrypi-bookworm")
        self.system.find_csi_camera_device = Mock(return_value="/dev/csi")
        self.system.find_usb_camera_device = Mock(return_value="/dev/usb")
        self.task = types.ModuleType("actfw_core.task")
        self.task.Consumer = type("Consumer", (), {})
        self.v4l = types.ModuleType("actfw_core.capture")
        self.v4l.V4LCameraCapture = Mock()
        self.v4l.V4LCameraCapture.FormatSelector.PROPER = "proper"
        self.unicam = types.ModuleType("actfw_core.unicam_isp_capture")
        self.unicam.UnicamIspCapture = Mock()
        self.vc4 = types.ModuleType("actfw_raspberrypi.vc4")
        self.vc4.Display = Mock()
        pil = types.ModuleType("PIL")
        pil.Image = Mock()
        pil.ImageDraw = Mock()
        pil.ImageFont = Mock()
        modules = {
            "libcamera": self.libcamera,
            "actfw_core": self.core,
            "actfw_core.system": self.system,
            "actfw_core.task": self.task,
            "actfw_core.capture": self.v4l,
            "actfw_core.unicam_isp_capture": self.unicam,
            "actfw_core.libcamera_capture": self.capture,
            "actfw_raspberrypi": types.ModuleType("actfw_raspberrypi"),
            "actfw_raspberrypi.vc4": self.vc4,
            "PIL": pil,
        }
        self.patcher = patch.dict(sys.modules, modules)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.main = runpy.run_path(str(APP / "app/main"))

    def test_default_and_explicit_auto_preserve_camera_defaults(self):
        for settings in ({}, {"awb_mode": "auto"}):
            with self.subTest(settings=settings):
                self.main["setup_camera_capture"](False, settings)
                self.assertIs(self.capture.LibcameraCapture.call_args.kwargs["awb"], self.auto)
                self.assertEqual(self.capture.LibcameraCapture.call_args.args, ((640, 480), "BGR888"))

    def test_greyworld_defaults_and_explicit_parameters(self):
        self.assertEqual(awb_settings.make_awb_settings({"awb_mode": "greyworld"}), ("greyworld", 1.6, 1.6, 0.45))
        settings = {"awb_mode": "greyworld", "awb_gain_r": 0.5, "awb_gain_b": 8, "awb_k": 1}
        self.main["setup_camera_capture"](False, settings)
        self.assertEqual(self.capture.LibcameraCapture.call_args.kwargs["awb"], ("greyworld", 0.5, 8, 1))

    def test_manual_uses_fixed_gains_and_ignores_greyworld_k(self):
        settings = {"awb_mode": "manual", "awb_gain_r": 1.04, "awb_gain_b": 2.30, "awb_k": 0}
        self.main["setup_camera_capture"](False, settings)
        self.assertEqual(self.capture.LibcameraCapture.call_args.kwargs["awb"], ("manual", 1.04, 2.30))
        self.capture.AwbGreyWorld.assert_not_called()

    def test_every_lighting_preset_reaches_capture(self):
        for name, member in awb_settings.AWB_PRESETS.items():
            with self.subTest(mode=name):
                self.main["setup_camera_capture"](False, {"awb_mode": name})
                self.assertIs(self.capture.LibcameraCapture.call_args.kwargs["awb"], getattr(self.presets, member))

    def test_imx219_uses_os3_field_of_view(self):
        self.main["setup_camera_capture"](False, {"awb_mode": "greyworld"})
        options = self.capture.LibcameraCapture.call_args.kwargs
        self.assertEqual(options["sensor_config"].output_size, (1640, 1232))
        self.assertEqual(options["sensor_config"].bit_depth, 10)
        self.assertEqual(vars(options["scaler_crop"]), {"x": 0, "y": 2, "width": 3280, "height": 2460})

    def test_csi_is_selected_even_when_usb_is_first(self):
        self.cameras.insert(0, types.SimpleNamespace(id="usb/camera"))
        self.capture.find_csi_camera_index.return_value = 1
        self.main["setup_camera_capture"](False)
        self.assertEqual(self.capture.LibcameraCapture.call_args.kwargs["camera_index"], 1)

    def test_other_csi_sensors_keep_automatic_geometry(self):
        self.cameras[0].id = "platform/soc/imx708@1a"
        self.main["setup_camera_capture"](False)
        options = self.capture.LibcameraCapture.call_args.kwargs
        self.assertNotIn("sensor_config", options)
        self.assertNotIn("scaler_crop", options)

    def test_missing_csi_does_not_fall_back_to_usb(self):
        self.capture.find_csi_camera_index.return_value = None
        with self.assertRaisesRegex(RuntimeError, "No CSI camera"):
            self.main["setup_camera_capture"](False)
        self.capture.LibcameraCapture.assert_not_called()

    def test_mode_selection_matches_os3_branches(self):
        from csi_camera_settings import imx219_sensor_config_and_scaler_crop
        cases = [
            ((640, 480), 30, (1640, 1232), (0, 2, 3280, 2460)),
            ((640, 480), 40, (1640, 1232), (0, 2, 3280, 2460)),
            ((640, 480), 41, (640, 480), (1000, 752, 1280, 960)),
            ((1280, 720), 50, (1640, 1232), (360, 512, 2560, 1440)),
            ((1440, 1080), 30, (3280, 2464), (0, 2, 3280, 2460)),
        ]
        for size, fps, mode_size, expected_crop in cases:
            with self.subTest(size=size, fps=fps):
                sensor, crop = imx219_sensor_config_and_scaler_crop(size, fps)
                self.assertEqual(sensor.output_size, mode_size)
                self.assertEqual((crop.x, crop.y, crop.width, crop.height), expected_crop)

    def test_os3_auto_does_not_import_libcamera(self):
        self.system.get_actcast_firmware_type.return_value = "raspberrypi-bullseye"
        with patch.dict(sys.modules, {"libcamera": None, "actfw_core.libcamera_capture": None}):
            result = self.main["setup_camera_capture"](False)
        self.assertIs(result, self.unicam.UnicamIspCapture.return_value)
        self.capture.LibcameraCapture.assert_not_called()

    def test_usb_auto_keeps_existing_capture_without_libcamera(self):
        with patch.dict(sys.modules, {"libcamera": None, "actfw_core.libcamera_capture": None}):
            result = self.main["setup_camera_capture"](True)
        self.assertIs(result, self.v4l.V4LCameraCapture.return_value)
        self.system.get_actcast_firmware_type.assert_not_called()

    def test_unsupported_modes_fail_before_camera_acquisition(self):
        for usb, firmware in ((True, "raspberrypi-bookworm"), (False, "raspberrypi-bullseye")):
            for mode in ("manual", "greyworld", *awb_settings.AWB_PRESETS):
                with self.subTest(usb=usb, firmware=firmware, mode=mode):
                    self.system.get_actcast_firmware_type.return_value = firmware
                    with self.assertRaisesRegex(ValueError, "ActcastOS 4 CSI"):
                        self.main["setup_camera_capture"](usb, {"awb_mode": mode})
        self.system.find_csi_camera_device.assert_not_called()
        self.system.find_usb_camera_device.assert_not_called()

    def test_unknown_mode_fails_before_camera_acquisition(self):
        for mode in ("unknown", None, [], 3):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(ValueError, "Unknown awb_mode"):
                    self.main["setup_camera_capture"](False, {"awb_mode": mode})
        self.system.find_csi_camera_device.assert_not_called()

    def test_invalid_active_numbers_fail_before_capture(self):
        for field in ("awb_gain_r", "awb_gain_b", "awb_k"):
            for value in (0, -1, float("nan"), float("inf"), True, "1.6", None):
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(ValueError, field):
                        self.main["setup_camera_capture"](False, {"awb_mode": "greyworld", field: value})
        self.capture.LibcameraCapture.assert_not_called()

    def test_reusable_module_import_needs_no_libcamera(self):
        with patch.dict(sys.modules, {"libcamera": None, "actfw_core.libcamera_capture": None}):
            spec = importlib.util.spec_from_file_location("portable_awb_settings", APP / "app/awb_settings.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.get_awb_mode({}), "auto")

    def test_main_passes_act_settings_to_camera(self):
        app = self.core.Application.return_value
        app.get_settings.return_value = {"display": False, "local_video_server": False, "use_usb_camera": False, "awb_mode": "manual", "awb_gain_r": 1.1, "awb_gain_b": 2.2}
        self.main["main"]()
        self.assertEqual(self.capture.LibcameraCapture.call_args.kwargs["awb"], ("manual", 1.1, 2.2))
        defaults = app.get_settings.call_args.args[0]
        for key, value in awb_settings.AWB_DEFAULTS.items():
            self.assertEqual(defaults[key], value)
        app.run.assert_called_once()


    def test_old_constructor_without_awb_starts_with_legacy_defaults(self):
        # The keyword parameters match the published actfw-core 2.22.0 API.
        def legacy_capture(size, pixel_format, camera_index=0, orientation=None,
                           framerate=30, depad=True, sensor_config=None, scaler_crop=None):
            return {"size": size, "framerate": framerate, "sensor_config": sensor_config}
        self.capture.LibcameraCapture = legacy_capture
        for name in ("Auto", "AwbManual", "AwbGreyWorld"):
            delattr(self.capture, name)
        for settings in ({}, *({"awb_mode": mode} for mode in ("auto", "manual", "greyworld", *awb_settings.AWB_PRESETS))):
            with self.subTest(settings=settings), self.assertLogs("awb_settings", level="WARNING") as logs:
                result = self.main["setup_camera_capture"](False, settings)
                self.assertEqual(result["size"], (640, 480))
                self.assertEqual(result["framerate"], 30)
                self.assertEqual(result["sensor_config"].output_size, (1640, 1232))
                self.assertIn("legacy behavior", logs.output[0])
                self.assertIn(settings.get("awb_mode", "auto"), logs.output[0])

    def test_missing_mode_specific_api_omits_awb_keyword(self):
        for mode, name in (("auto", "Auto"), ("manual", "AwbManual"), ("greyworld", "AwbGreyWorld")):
            with self.subTest(mode=mode), patch.object(self.capture, name, None):
                with self.assertLogs("awb_settings", level="WARNING"):
                    self.main["setup_camera_capture"](False, {"awb_mode": mode})
                self.assertNotIn("awb", self.capture.LibcameraCapture.call_args.kwargs)

    def test_partial_awb_support_keeps_supported_modes(self):
        del self.capture.AwbGreyWorld
        with self.assertNoLogs("awb_settings", level="WARNING"):
            self.main["setup_camera_capture"](False, {"awb_mode": "manual"})
            self.assertEqual(self.capture.LibcameraCapture.call_args.kwargs["awb"], ("manual", 1.6, 1.6))
            self.main["setup_camera_capture"](False)
            self.assertIs(self.capture.LibcameraCapture.call_args.kwargs["awb"], self.auto)

    def test_missing_lighting_preset_falls_back(self):
        del self.presets.Daylight
        with self.assertLogs("awb_settings", level="WARNING"):
            self.main["setup_camera_capture"](False, {"awb_mode": "daylight"})
        self.assertNotIn("awb", self.capture.LibcameraCapture.call_args.kwargs)

    def test_missing_preset_enum_falls_back(self):
        del self.libcamera.controls.AwbModeEnum
        with self.assertLogs("awb_settings", level="WARNING"):
            self.main["setup_camera_capture"](False, {"awb_mode": "cloudy"})
        self.assertNotIn("awb", self.capture.LibcameraCapture.call_args.kwargs)

    def test_opaque_or_kwargs_only_constructor_is_not_assumed_to_support_awb(self):
        for capture in (Mock(), object()):
            with self.subTest(capture=capture), self.assertLogs("awb_settings", level="WARNING"):
                self.assertEqual(awb_settings.make_awb_options({}, capture), {})

    def test_unrelated_constructor_failure_is_not_hidden_or_retried(self):
        self.capture.LibcameraCapture.side_effect = TypeError("camera configuration failed")
        with self.assertRaisesRegex(TypeError, "camera configuration failed"):
            self.main["setup_camera_capture"](False)
        self.capture.LibcameraCapture.assert_called_once()


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((APP / "setting_schema.json").read_text())
        cls.fragment = json.loads((APP / "docs/awb-settings.schema.json").read_text())

    def test_schema_defaults_and_portable_fragment_match_module(self):
        jsonschema.Draft7Validator.check_schema(self.schema)
        jsonschema.Draft7Validator.check_schema(self.fragment)
        jsonschema.Draft7Validator(self.schema).validate({})
        jsonschema.Draft7Validator(self.schema).validate(awb_settings.AWB_DEFAULTS)
        for key, value in self.fragment["properties"].items():
            self.assertEqual(self.schema["properties"][key], value)
            self.assertEqual(value["default"], awb_settings.AWB_DEFAULTS[key])
        self.assertEqual(set(self.schema["properties"]["awb_mode"]["enum"]), {"auto", "manual", "greyworld", *awb_settings.AWB_PRESETS})

    def test_invalid_modes_types_and_ranges_rejected_by_schema(self):
        for field, values in {"awb_mode": ["unknown", 0, None], "awb_gain_r": [0, -1, True, "1.6"], "awb_gain_b": [0, -1], "awb_k": [0, -0.1, 1.1]}.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(jsonschema.ValidationError):
                        jsonschema.Draft7Validator(self.schema).validate({field: value})

    def test_dependency_uses_awb_release(self):
        dependencies = json.loads((APP / ".actdk/dependencies.json").read_text())
        self.assertIn("actfw-core==2.23.0", dependencies["pip"])


if __name__ == "__main__":
    unittest.main()
