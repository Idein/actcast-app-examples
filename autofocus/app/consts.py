from datetime import datetime, timezone

(CAPTURE_WIDTH, CAPTURE_HEIGHT) = (320, 240)  # capture image size
INFO_COLOR = (0, 255, 0)
JSTDT = datetime(1970, 1, 1, 9, tzinfo=timezone.utc).timestamp()
