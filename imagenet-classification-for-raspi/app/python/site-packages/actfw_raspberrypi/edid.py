import re
import subprocess
from typing import Tuple


class EDID:
    edid: str

    """Extended Display Information Data"""

    def __init__(self) -> None:
        subprocess.run("/opt/vc/bin/tvservice -d /tmp/edid".split(), stdout=subprocess.DEVNULL)
        p = subprocess.run("/opt/vc/bin/edidparser /tmp/edid".split(), stdout=subprocess.PIPE)
        self.edid = p.stdout.decode("utf-8")

    def prefferd_mode(self) -> Tuple[int, int]:
        """Preffered Display Resolution.

        Returns:
            (int, int): (width, height)

        """
        prog = re.compile(r"^.+preferred mode.+(DMT|CEA) \(([0-9]+)\) ([0-9]+)x([0-9]+)[pi]? @.+")
        for line in self.edid.split("\n"):
            result = prog.match(line)
            if result is not None:
                xres = result.group(3)
                yres = result.group(4)
                return (int(xres), int(yres))
        return (640, 480)  # fallback
