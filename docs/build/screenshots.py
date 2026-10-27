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
PHONE_WIDTH = 500                      # narrow screen; headless Edge will not size a window below ~500 px
# name -> (path, window width): every page of the web app, a filtered view, the PHP API, a phone
PAGES = {
    "dash_executive": ("/", WIDTH),
    "dash_operations": ("/operations/?event=TC2024-KRISTINE", WIDTH),
    "dash_logistics": ("/logistics/", WIDTH),
    "dash_logistics_event": ("/logistics/?event=TC2024-KRISTINE", WIDTH),
    "dash_about": ("/about/", WIDTH),
    "api_health": ("/api/health.php", 900),
    "api_marts": ("/api/marts.php?name=mart_event_summary&event=TC2024-KRISTINE", 900),
    "dash_mobile": ("/operations/?event=TC2024-KRISTINE", PHONE_WIDTH),
}
# name -> (path, heading of the card, or None for the tile row): close-ups of single panels
SECTIONS = {
    "part_executive_tiles": ("/", None),
    "part_executive_per100k": ("/", "Deaths per 100,000 people"),
    "part_operations_tiles": ("/operations/?event=TC2024-KRISTINE", None),
    "part_operations_displacement": ("/operations/?event=TC2024-KRISTINE",
                                     "People displaced, inside and outside evacuation centers"),
    "part_operations_lifelines": ("/operations/?event=TC2024-KRISTINE",
                                  "Lifelines: roads, bridges, power, water, communications"),
    "part_logistics_providers": ("/logistics/", "Cost of assistance by provider"),
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


def capture_exchange() -> None:
    """The Data exchange page, empty and after checking the Albay sample (needs a real upload,
    so this one is scripted with Playwright driving the installed Edge)."""
    from playwright.sync_api import sync_playwright

    sample = ROOT / "data" / "intake-samples" / "albay-pdrrmo-kristine-evacuation.xlsx"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_context(viewport={"width": WIDTH, "height": 900}, device_scale_factor=SCALE,
                                   color_scheme="light", reduced_motion="reduce").new_page()
        page.goto(BASE + "/exchange/")
        page.wait_for_load_state("networkidle")
        out = OUT / "dash_exchange.png"
        page.screenshot(path=str(out), full_page=True)
        print(f"wrote {out.relative_to(ROOT)}")

        page.select_option("select >> nth=1", "albay-pdrrmo-evacuation")
        page.set_input_files("input[type=file]", str(sample))
        page.get_by_role("button", name="Check file").click()
        page.wait_for_selector("tbody tr", timeout=180_000)
        # the report table scrolls inside a fixed-height box; show every row for the printed figure
        page.add_style_tag(content=".overflow-auto { max-height: none !important; }")
        report = page.locator("section", has_text="2. Check and submit a report")
        out = OUT / "dash_exchange_report.png"
        report.screenshot(path=str(out))
        print(f"wrote {out.relative_to(ROOT)}")
        browser.close()


def capture_sections() -> None:
    """Close-ups of single panels (the tile row, or one card found by its heading), with short
    tables opened so the exact figures are in the picture too."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_context(viewport={"width": WIDTH, "height": 900}, device_scale_factor=SCALE,
                                   color_scheme="light", reduced_motion="reduce").new_page()
        for name, (path, heading) in SECTIONS.items():
            page.goto(BASE + path)
            page.wait_for_load_state("networkidle")
            if heading is None:
                part = page.locator("main div.grid").first
            else:
                part = page.locator("section", has=page.get_by_role("heading", name=heading, exact=True))
                toggle = part.get_by_text("Show table")
                if toggle.count() and "displacement" not in name:   # its 20-row table is too long
                    toggle.first.click()
                    # the table scrolls inside a fixed-height box; show every row for the printed figure
                    page.add_style_tag(content=".overflow-auto { max-height: none !important; }")
            page.wait_for_timeout(500)
            out = OUT / f"{name}.png"
            part.screenshot(path=str(out))
            print(f"wrote {out.relative_to(ROOT)}")
        browser.close()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (path, width) in PAGES.items():
        png = OUT / f"{name}.png"
        png.unlink(missing_ok=True)
        profile = tempfile.mkdtemp(prefix="driw-edge-")
        subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={profile}", "--force-prefers-reduced-motion",
                        "--blink-settings=preferredColorScheme=1", f"--force-device-scale-factor={SCALE}",
                        f"--window-size={width},{HEIGHT}", "--virtual-time-budget=8000",
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
    capture_exchange()
    capture_sections()


if __name__ == "__main__":
    main()
