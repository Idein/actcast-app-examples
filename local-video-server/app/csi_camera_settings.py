"""Reusable IMX219 field-of-view compatibility for OS3 and LibcameraCapture.

Mode selection and sensor-space crop follow actfw-core 2.23.0 UnicamIspCapture
and People Counter commit d2b26c74dac4b7cf60a22890a682fcc89b66f960.
Only IMX219 receives these sensor-specific overrides. Imports are lazy for OS3.
"""

IMX219_MODE_FULL = ((3280, 2464), (1, 1), (0, 0))
IMX219_MODE_BINNED = ((1640, 1232), (2, 2), (0, 0))
IMX219_MODE_VGA = ((640, 480), (2, 2), (1000, 752))


def _calc_crop_size(out_width, out_height, mode_width, mode_height):
    scale = min(mode_height / out_height, mode_width / out_width)
    width = round(out_width * scale)
    height = round(out_height * scale)
    left = int((mode_width - width) / 2)
    top = int((mode_height - height) / 2)
    return left, top, width, height


def select_imx219_mode_and_crop(capture_size, framerate):
    """Return the OS3-compatible mode and crop in binned-image coordinates."""
    width, height = capture_size
    if width <= 1280 and height <= 720:
        if framerate <= 40:
            mode = IMX219_MODE_BINNED
        elif abs(width / height - 16 / 9) < 0.05:
            return IMX219_MODE_BINNED, (180, 256, 1280, 720)
        else:
            mode = IMX219_MODE_VGA
    else:
        mode = IMX219_MODE_FULL
    return mode, _calc_crop_size(width, height, *mode[0])


def imx219_sensor_config_and_scaler_crop(capture_size, framerate):
    """Convert the selected mode and crop to actfw-core's libcamera types."""
    from actfw_core.libcamera_capture import ScalerCrop, SensorConfig

    mode, (left, top, width, height) = select_imx219_mode_and_crop(capture_size, framerate)
    mode_size, (scale_x, scale_y), (offset_x, offset_y) = mode
    return (
        SensorConfig(bit_depth=10, output_size=mode_size),
        ScalerCrop(
            x=int(offset_x + left * scale_x),
            y=int(offset_y + top * scale_y),
            width=int(width * scale_x),
            height=int(height * scale_y),
        ),
    )


def libcamera_csi_options(capture_size, framerate):
    """Select a CSI camera and add IMX219-only field-of-view overrides.

    Other CSI sensors retain libcamera's automatic mode selection. A missing CSI
    camera is an error rather than silently selecting a USB camera at index zero.
    """
    import libcamera
    from actfw_core.libcamera_capture import find_csi_camera_index

    camera_index = find_csi_camera_index()
    if camera_index is None:
        raise RuntimeError("No CSI camera found; connect a CSI camera or enable use_usb_camera")
    camera = libcamera.CameraManager.singleton().cameras[camera_index]
    options = {"camera_index": camera_index}
    if "imx219" in str(camera.id).lower():
        sensor_config, scaler_crop = imx219_sensor_config_and_scaler_crop(capture_size, framerate)
        options.update(sensor_config=sensor_config, scaler_crop=scaler_crop)
    return options
