"""Capture the dashboards (served by XAMPP at http://localhost/driw/) as PNGs for the report.

Charts are captured fully drawn: reduced motion skips their entry animation.

    python docs/build/screenshots.py
"""

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "img"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
BASE = "http://localhost/driw"
PAGES = {
    "dash_executive": ("/", 1600, 1180),
    "dash_operations": ("/operations/?event=TC2024-KRISTINE", 1600, 1240),
    "dash_logistics": ("/logistics/", 1600, 1180),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (path, w, h) in PAGES.items():
        png = OUT / f"{name}.png"
        png.unlink(missing_ok=True)
        profile = tempfile.mkdtemp(prefix="driw-edge-")
        subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={profile}", "--force-prefers-reduced-motion",
                        "--blink-settings=preferredColorScheme=1", "--force-device-scale-factor=1",
                        f"--window-size={w},{h}", "--virtual-time-budget=8000",
                        f"--screenshot={png}", BASE + path], capture_output=True, timeout=120)
        for _ in range(100):  # msedge.exe can return before the file is written
            if png.exists() and png.stat().st_size > 0:
                break
            time.sleep(0.2)
        time.sleep(0.5)
        shutil.rmtree(profile, ignore_errors=True)
        print(f"{'wrote' if png.exists() else 'FAILED'} {png.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
