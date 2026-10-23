"""Draw the documentation diagrams as SVG (and PNG for the Word report).

- er_<fact>.svg      one ER diagram per star, read from the live catalog (columns, PK, FK)
- conceptual.svg     business processes and the business entities they involve
- etl_workflow.svg   the ETL pipeline from source files to dashboards

    python docs/build/diagrams.py        (needs the `driw` database and, for PNGs, Microsoft Edge)
"""

import shutil
import subprocess
import sys
import tempfile
import time
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ingestion"))
from common import connect  # noqa: E402

OUT = ROOT / "docs" / "img"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

INK, PAPER, CARD, LINE = "#14233A", "#F6F4EF", "#FCFBF8", "#B8B2A3"
ACCENT, BLUE, MUTED, HEADER_DIM = "#E0612A", "#1F5FA8", "#6A7179", "#E7EEF7"
FONT = "Arial, Helvetica, sans-serif"
ROW, HEAD, PAD = 22, 34, 10


# ----------------------------------------------------------------------------- svg helpers

class Svg:
    def __init__(self, width: int, height: int, title: str):
        self.w, self.h, self.parts = width, height, []
        self.rect(0, 0, width, height, PAPER, PAPER)
        self.text(24, 36, title, 22, INK, bold=True)

    def rect(self, x, y, w, h, fill, stroke, radius=8, width=1.2):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
                          f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def text(self, x, y, s, size=13, color=INK, bold=False, anchor="start", italic=False):
        weight = ' font-weight="700"' if bold else ""
        style = ' font-style="italic"' if italic else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{color}" '
                          f'text-anchor="{anchor}"{weight}{style}>{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, color=LINE, width=1.5, arrow=False, dashed=False):
        marker = ' marker-end="url(#arrow)"' if arrow else ""
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.parts.append(f'<path d="M{x1},{y1} C{(x1 + x2) / 2},{y1} {(x1 + x2) / 2},{y2} {x2},{y2}" fill="none" '
                          f'stroke="{color}" stroke-width="{width}"{marker}{dash}/>')

    def straight(self, x1, y1, x2, y2, color=INK, width=1.6, label=None):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" '
                          f'marker-end="url(#arrow)"/>')
        if label:
            self.text((x1 + x2) / 2, (y1 + y2) / 2 - 6, label, 11, MUTED, anchor="middle", italic=True)

    def save(self, name: str) -> Path:
        defs = (f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}">{defs}{"".join(self.parts)}</svg>')
        path = OUT / f"{name}.svg"
        path.write_text(svg, encoding="utf-8")
        return path


def table_box(svg: Svg, x, y, w, name, columns, kind):
    """columns: list of (name, type, marker) where marker is 'PK', 'FK', 'PK/FK' or ''."""
    h = HEAD + ROW * len(columns) + PAD
    header = INK if kind == "fact" else HEADER_DIM
    svg.rect(x, y, w, h, CARD, INK if kind == "fact" else LINE, width=1.8 if kind == "fact" else 1.2)
    svg.parts.append(f'<path d="M{x},{y + 8} a8,8 0 0 1 8,-8 h{w - 16} a8,8 0 0 1 8,8 v{HEAD - 8} h-{w} z" '
                     f'fill="{header}"/>')
    svg.text(x + 12, y + 22, name, 14, PAPER if kind == "fact" else INK, bold=True)
    rows = {}
    for i, (col, typ, marker) in enumerate(columns):
        cy = y + HEAD + ROW * i + 16
        if marker:
            svg.text(x + 10, cy, marker, 10, ACCENT if "PK" in marker else BLUE, bold=True)
        svg.text(x + 50, cy, col, 12, INK)
        svg.text(x + w - 10, cy, typ, 11, MUTED, anchor="end")
        rows[col] = cy - 4
    return h, rows


# ----------------------------------------------------------------------------- catalog

SHORT_TYPES = {"integer": "int", "bigint": "bigint", "numeric": "numeric", "text": "text", "date": "date",
               "boolean": "bool", "timestamp without time zone": "timestamp", "character": "char",
               "timestamp with time zone": "timestamptz", "double precision": "float"}


def catalog():
    with connect() as conn:
        cols = conn.execute("""
            select table_name, column_name, data_type
            from information_schema.columns where table_schema = 'dw'
            order by table_name, ordinal_position""").fetchall()
        keys = conn.execute("""
            select c.conrelid::regclass::text, a.attname, c.contype,
                   c.confrelid::regclass::text, fa.attname
            from pg_constraint c
            join pg_attribute a on a.attrelid = c.conrelid and a.attnum = any (c.conkey)
            left join pg_attribute fa on fa.attrelid = c.confrelid and fa.attnum = any (c.confkey)
            where c.connamespace = 'dw'::regnamespace and c.contype in ('p', 'f')""").fetchall()
    tables = {}
    for t, c, typ in cols:
        tables.setdefault(t, []).append([c, SHORT_TYPES.get(typ, typ), ""])
    fks = {}
    for table, col, kind, ref_table, ref_col in keys:
        t = table.split(".")[-1]
        for entry in tables[t]:
            if entry[0] == col:
                entry[2] = "PK" if kind == "p" else ("PK/FK" if entry[2] == "PK" else "FK")
        if kind == "f":
            fks.setdefault(t, []).append((col, ref_table.split(".")[-1], ref_col))
    return tables, fks


# ----------------------------------------------------------------------------- diagrams

def er_diagram(fact, tables, fks, max_dim_rows=8):
    refs = fks[fact]
    dims = list(dict.fromkeys(ref for _, ref, _ in refs))   # unique, in FK order
    left, right = dims[: (len(dims) + 1) // 2], dims[(len(dims) + 1) // 2:]
    fact_cols = [tuple(c) for c in tables[fact]]
    W, fact_w, dim_w = 1300, 380, 330
    fact_h = HEAD + ROW * len(fact_cols) + PAD

    def dim_cols(d):
        cols = [tuple(c) for c in tables[d]]
        if len(cols) > max_dim_rows:
            cols = cols[: max_dim_rows - 1] + [(f"… {len(cols) - max_dim_rows + 1} more columns", "", "")]
        return cols

    dim_heights = {d: HEAD + ROW * len(dim_cols(d)) + PAD for d in dims}
    col_h = max(sum(dim_heights[d] for d in side) + 30 * (len(side) - 1) for side in (left, right))
    H = max(fact_h, col_h) + 130
    svg = Svg(W, H, f"ER diagram: {fact} (star schema)")
    svg.text(24, 60, "PK primary key · FK foreign key · arrows point from a fact foreign key to the dimension key",
             12, MUTED)
    fx = (W - fact_w) // 2
    fy = 90 + (H - 120 - fact_h) // 2
    _, fact_rows = table_box(svg, fx, fy, fact_w, fact, fact_cols, "fact")
    positions = {}
    for side, x in ((left, 30), (right, W - dim_w - 30)):
        total = sum(dim_heights[d] for d in side) + 30 * (len(side) - 1)
        y = 90 + (H - 120 - total) // 2
        for d in side:
            _, rows = table_box(svg, x, y, dim_w, d, dim_cols(d), "dim")
            positions[d] = (x, rows)
            y += dim_heights[d] + 30
    for col, ref, ref_col in refs:
        dx, rows = positions[ref]
        y1, y2 = fact_rows[col], rows[ref_col]
        if dx < fx:
            svg.line(fx, y1, dx + dim_w, y2, arrow=True)
        else:
            svg.line(fx + fact_w, y1, dx, y2, arrow=True)
    return svg.save(f"er_{fact}")


def conceptual():
    uses = {
        "Damage assessment": ["Date", "Location (PSGC)", "Hazard event", "Source system"],
        "Evacuation": ["Date", "Location (PSGC)", "Hazard event", "Organization", "Source system"],
        "Displacement outside centers": ["Date", "Location (PSGC)", "Hazard event", "Organization", "Source system"],
        "Relief distribution": ["Date", "Location (PSGC)", "Hazard event", "Organization", "Source system"],
        "Response operations": ["Date", "Location (PSGC)", "Hazard event", "Organization", "Source system"],
        "Lifeline status": ["Date", "Location (PSGC)", "Hazard event", "Organization", "Source system"],
    }
    own = {"Damage assessment": "Damage category", "Evacuation": "Evacuation center",
           "Displacement outside centers": None, "Relief distribution": "Relief resource",
           "Response operations": "Response type", "Lifeline status": "Lifeline"}
    W, H = 1300, 800
    svg = Svg(W, H, "Conceptual model: business processes and the entities they involve")
    svg.text(24, 60, "Each process becomes a fact table; each entity becomes a dimension. Entities in the centre are "
                     "shared (conformed) across processes.", 12, MUTED)
    shared = ["Hazard event", "Location (PSGC)", "Date", "Organization", "Source system"]
    cw, ch, cx = 230, 50, (W - 230) // 2
    svg.rect(cx - 20, 238, cw + 40, len(shared) * 68 + 34, "#ECE8DF", "#ECE8DF", radius=14)
    svg.text(W / 2, 262, "Shared conformed dimensions", 12, MUTED, True, "middle")
    centre = {}
    for i, e in enumerate(shared):
        y = 276 + i * 68
        svg.rect(cx, y, cw, ch, CARD, LINE)
        svg.text(W / 2, y + 31, e, 14, INK, True, "middle")
        centre[e] = y + ch / 2
    pw, ph, ew = 280, 70, 220
    left = ["Damage assessment", "Evacuation", "Displacement outside centers"]
    right = ["Relief distribution", "Response operations", "Lifeline status"]
    spots = {proc: (60 if proc in left else W - 60 - pw, 100 + (left + right).index(proc) % 3 * 215)
             for proc in left + right}
    for proc, (x, y) in spots.items():
        is_left = x < W / 2
        edge = x + pw if is_left else x
        for e in shared:
            if e in uses[proc]:
                svg.parts.append(f'<line x1="{edge}" y1="{y + ph / 2}" x2="{cx if is_left else cx + cw}" '
                                 f'y2="{centre[e]}" stroke="{LINE}" stroke-width="1.4"/>')
        svg.rect(x, y, pw, ph, INK, INK)
        svg.text(x + pw / 2, y + 31, proc, 16, PAPER, True, "middle")
        svg.text(x + pw / 2, y + 52, "business process → fact table", 11, "#C9D3DE", anchor="middle")
        if own[proc]:
            ey, ex = y + ph + 30, x + (pw - ew) / 2
            svg.parts.append(f'<line x1="{x + pw / 2}" y1="{y + ph}" x2="{x + pw / 2}" y2="{ey}" '
                             f'stroke="{LINE}" stroke-width="1.4"/>')
            svg.rect(ex, ey, ew, ch, CARD, LINE)
            svg.text(x + pw / 2, ey + 31, own[proc], 14, INK, True, "middle")
    svg.text(24, 770, "Location is identified by the official PSGC code, which is what lets five agencies’ "
                      "records be integrated. Damage assessment does not involve an organization; "
                      "displacement outside centers has no entity of its own.", 12, MUTED)
    return svg.save("conceptual")


def etl_workflow():
    W, H = 1500, 760
    svg = Svg(W, H, "ETL workflow: from five source systems to the dashboards")
    svg.text(24, 60, "Orchestrated by ingestion/pipeline.py (migrate → reference → psgc → generate → raw → dbt → "
                     "export); every push re-runs it in GitHub Actions.", 12, MUTED)

    def stage(x, y, w, h, title, lines, dark=False, accent=False):
        fill = INK if dark else ("#FBE6DC" if accent else CARD)
        svg.rect(x, y, w, h, fill, INK if dark else (ACCENT if accent else LINE), width=1.4)
        svg.text(x + 14, y + 26, title, 15, PAPER if dark else INK, True)
        for i, ln in enumerate(lines):
            svg.text(x + 14, y + 50 + i * 19, ln, 12, "#C9D3DE" if dark else "#3E4A5A")

    sources = [("NDRRMC sitreps", "CSV: damage, lifelines"), ("DSWD DROMIC", "Excel: inside + outside ECs"),
               ("NGO / LGU relief", "nested JSON"), ("PAGASA bulletins", "CSV"), ("LGU response logs", "CSV")]
    for i, (name, fmt) in enumerate(sources):
        y = 100 + i * 82
        svg.rect(30, y, 200, 62, CARD, LINE)
        svg.text(44, y + 26, name, 13, INK, True)
        svg.text(44, y + 46, fmt, 12, MUTED)
        svg.line(230, y + 31, 300, 300, arrow=True)
    stage(300, 230, 230, 150, "1 · Extract", ["load_raw.py", "files → raw.* as text", "batch id, file, row no.",
                                               "→ meta.load_batch"])
    stage(300, 430, 230, 120, "Reference data", ["load_psgc_api.py (PSGC)", "load_reference.py", "→ ref.*"])
    svg.straight(530, 305, 590, 305)
    svg.straight(530, 490, 640, 412)
    stage(590, 200, 270, 210, "2 · Transform (dbt staging)", ["type & parse dates, numbers", "conform places → PSGC",
                                                              "conform events, orgs, units", "de-duplicate",
                                                              "45 DQ rules → dq_status", "valid/warning only go on"])
    stage(590, 470, 270, 140, "Quarantine (dq)", ["rejected rows + reasons", "issue log, scorecard",
                                                  "reconciliation 19/19"], accent=True)
    svg.straight(725, 410, 725, 470, color=ACCENT)
    svg.text(735, 446, "rejects", 11, ACCENT, italic=True)
    svg.straight(860, 305, 920, 305)
    stage(920, 200, 250, 210, "3 · Load (dw)", ["surrogate keys", "SCD2 dim_location", "(dated change log)",
                                                "6 facts, 10 dims", "PK / FK constraints", "RLS + grants"], dark=True)
    svg.straight(1170, 305, 1220, 305)
    stage(1220, 200, 250, 150, "4 · Aggregate (mart)", ["8 materialized views", "GROUP BY CUBE",
                                                        "GROUPING SETS", "tested vs facts"])
    svg.straight(1345, 350, 1345, 420)
    stage(1220, 420, 250, 150, "5 · Deliver", ["PHP API (XAMPP)", "as driw_web (marts only)",
                                               "JSON snapshot fallback", "Next.js dashboards"])
    stage(920, 470, 250, 140, "Validate", ["117 dbt checks each build", "pytest: e2e, access, API",
                                           "query benchmark"])
    svg.text(24, 730, "Full reload: raw is truncated and reloaded, dbt rebuilds staging, dw and marts; grants, "
                      "row-level security and keys are re-applied on every build.", 12, MUTED)
    return svg.save("etl_workflow")


def to_png(svg_path: Path) -> None:
    if not EDGE.exists():
        print("  (Edge not found: PNG skipped)")
        return
    w = int(svg_path.read_text(encoding="utf-8").split('width="')[1].split('"')[0])
    h = int(svg_path.read_text(encoding="utf-8").split('height="')[1].split('"')[0])
    html = svg_path.with_suffix(".html")
    html.write_text(f'<html><body style="margin:0">{svg_path.read_text(encoding="utf-8")}</body></html>',
                    encoding="utf-8")
    png = svg_path.with_suffix(".png")
    png.unlink(missing_ok=True)  # so the wait below sees the new file, not the old one
    # an isolated profile, or a running Edge window swallows the headless call
    profile = tempfile.mkdtemp(prefix="driw-edge-")
    subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                    "--force-device-scale-factor=2", f"--window-size={w},{h}",
                    f"--screenshot={png}", html.as_uri()], capture_output=True, timeout=120)
    # msedge.exe can return before the browser has written the file: wait for it
    for _ in range(100):
        if png.exists() and png.stat().st_size > 0:
            break
        time.sleep(0.2)
    time.sleep(0.5)
    html.unlink()
    shutil.rmtree(profile, ignore_errors=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tables, fks = catalog()
    paths = [er_diagram(f, tables, fks) for f in sorted(fks)] + [conceptual(), etl_workflow()]
    for p in paths:
        to_png(p)
        print(f"wrote {p.relative_to(ROOT)} (+ png)")


if __name__ == "__main__":
    if not shutil.which("python") and not sys.executable:
        sys.exit("python not found")
    main()
