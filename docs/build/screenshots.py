"""Capture the dashboards (served by XAMPP at http://localhost/driw/) as PNGs for the report.

Charts are captured fully drawn: reduced motion skips their entry animation. The window is just
wider than the content column, at 2x pixel density, so text stays legible on an A4 page; the
blank space below the footer is trimmed.

    python docs/build/screenshots.py
"""

import shutil
import subprocess
import tempfile
import time

import pymupdf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "img"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
BASE = "http://localhost/driw"
WIDTH, HEIGHT, SCALE = 1180, 3000, 2   # CSS pixels; content column is max 1152 px
PAGES = {
    "dash_executive": "/",
    "dash_operations": "/operations/?event=TC2024-KRISTINE",
    "dash_logistics": "/logistics/",
}


def trim_bottom(png: Path) -> None:
    """Crop the uniform background below the last row of content."""
    pix = pymupdf.Pixmap(str(png))
    n, stride, data = pix.n, pix.stride, pix.samples
    background = data[(pix.height - 1) * stride:(pix.height - 1) * stride + n]  # bottom-left pixel
    last = 0
    for y in range(pix.height - 1, -1, -1):
        row = data[y * stride:(y + 1) * stride]
        if row != background * pix.width:
            last = y
            break
    keep = min(pix.height, last + 24 * SCALE)
    doc = pymupdf.open(str(png))
    page = doc[0]
    clip = pymupdf.Rect(0, 0, page.rect.width, page.rect.height * keep / pix.height)
    out = page.get_pixmap(clip=clip, matrix=pymupdf.Matrix(pix.width / page.rect.width,
                                                           pix.width / page.rect.width))
    doc.close()
    out.save(str(png))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, path in PAGES.items():
        png = OUT / f"{name}.png"
        png.unlink(missing_ok=True)
        profile = tempfile.mkdtemp(prefix="driw-edge-")
        subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={profile}", "--force-prefers-reduced-motion",
                        "--blink-settings=preferredColorScheme=1", f"--force-device-scale-factor={SCALE}",
                        f"--window-size={WIDTH},{HEIGHT}", "--virtual-time-budget=8000",
                        f"--screenshot={png}", BASE + path], capture_output=True, timeout=120)
        for _ in range(100):  # msedge.exe can return before the file is written
            if png.exists() and png.stat().st_size > 0:
                break
            time.sleep(0.2)
        time.sleep(0.5)
        shutil.rmtree(profile, ignore_errors=True)
        if png.exists():
            trim_bottom(png)
        print(f"{'wrote' if png.exists() else 'FAILED'} {png.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
