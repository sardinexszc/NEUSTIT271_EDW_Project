"""Compile the documentation into one submission report: docs/submission/DRIW_Final_Report.docx (+ .pdf).

The chapters are the Markdown files in docs/, so the report is rebuilt whenever they change.
Run the generators first when the data changes:

    python docs/build/data_dictionary.py
    python docs/build/diagrams.py
    python docs/build/screenshots.py      (XAMPP must be serving http://localhost/driw/)
    python ingestion/benchmark_queries.py
    python docs/build/build_report.py     (Word updates the table of contents and exports the PDF)
"""

import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT_DIR = DOCS / "submission"
DOCX = OUT_DIR / "DRIW_Final_Report.docx"

NAVY = RGBColor(0x14, 0x23, 0x3A)
ORANGE = RGBColor(0xB9, 0x47, 0x1A)
GREY = RGBColor(0x4A, 0x55, 0x66)
HEADER_FILL = "ECE8DF"
CODE_FILL = "F3F1EC"

# (chapter title, [(markdown file, heading-level shift)])
CHAPTERS = [
    ("Requirements Coverage", [("requirements-traceability.md", 0)]),
    ("Business Case and Requirements Analysis", [("business-case.md", 0)]),
    ("Data Warehouse Design", [("warehouse-design.md", 0), ("dimensional-model.md", 1)]),
    ("Data Dictionary and Metadata", [("data-dictionary.md", 0)]),
    ("ETL Design", [("etl-design.md", 0)]),
    ("Data Quality Framework", [("data-quality-framework.md", 0)]),
    ("Data Governance, Security and Privacy", [("governance.md", 0)]),
    ("Analytics: OLAP and Dashboards", [("analytics.md", 0)]),
    ("Testing and Validation", [("validation-report.md", 0), ("query-performance.md", 1)]),
    ("Implementation and Live Demo", [("implementation.md", 0)]),
]


# ----------------------------------------------------------------------------- docx helpers

def shade(element, fill: str) -> None:
    props = element.get_or_add_tcPr() if element.tag.endswith("}tc") else element.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    props.append(shd)


def add_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    for tag, attr in (("w:fldChar", "begin"), ("w:instrText", None), ("w:fldChar", "separate"),
                      ("w:t", None), ("w:fldChar", "end")):
        el = OxmlElement(tag)
        if tag == "w:fldChar":
            el.set(qn("w:fldCharType"), attr)
        elif tag == "w:instrText":
            el.set(qn("xml:space"), "preserve")
            el.text = instruction
        else:
            el.text = "Right-click and choose Update Field to build the table of contents."
        run._r.append(el)


def setup(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, side, Cm(2.2))
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.paragraph_format.space_after = Pt(6)
    for level, size in ((1, 18), (2, 14), (3, 12), (4, 11)):
        h = styles[f"Heading {level}"]
        h.font.name, h.font.size, h.font.bold = "Calibri", Pt(size), True
        h.font.color.rgb = NAVY
        h.paragraph_format.space_before = Pt(14 if level <= 2 else 10)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True


def footer(doc: Document) -> None:
    p = doc.sections[0].footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("DRIW · IT271 Enterprise Data Warehousing · page ")
    run.font.size, run.font.color.rgb = Pt(8), GREY
    add_field(p, "PAGE")
    p.runs[-1].font.size = Pt(8)


def title_page(doc: Document) -> None:
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run("IT271 ENTERPRISE DATA WAREHOUSING · SEMESTER PROJECT")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(11), True, ORANGE
    p = doc.add_paragraph()
    r = p.add_run("Disaster Response Intelligence Warehouse (DRIW)")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(28), True, NAVY
    p = doc.add_paragraph()
    r = p.add_run("Design, implementation and validation of an enterprise data warehouse for disaster "
                  "impact, evacuation, relief and emergency-response analytics in the Philippines, 2020–2025")
    r.font.size, r.font.color.rgb = Pt(13), GREY
    for _ in range(4):
        doc.add_paragraph()
    for label, value in (("Author", "Ivan Christian Salinas"),
                         ("Course", "IT271 Enterprise Data Warehousing"),
                         ("Submitted", date.today().strftime("%B %d, %Y")),
                         ("Repository", "github.com/sardinexszc/NEUSTIT271_EDW_Project")):
        p = doc.add_paragraph()
        r = p.add_run(f"{label}: ")
        r.font.bold = True
        p.add_run(value)
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run("Data notice: event names, dates and PSGC geography are real. All damage, evacuation, relief "
                  "and response figures are synthetic, generated for demonstration.")
    r.font.size, r.font.italic, r.font.color.rgb = Pt(9.5), True, GREY
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    p = doc.add_paragraph()
    r = p.add_run("Contents")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(18), True, NAVY
    add_field(doc.add_paragraph(), 'TOC \\o "1-2" \\h \\z \\u')
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ----------------------------------------------------------------------------- markdown -> docx

class Renderer:
    def __init__(self, doc: Document, base: Path):
        self.doc, self.base = doc, base
        self.md = MarkdownIt("commonmark").enable("table")
        self.section = 0

    def inline(self, paragraph, children, size=None, bold=False):
        state = {"bold": bold, "italic": False, "code": False}
        for tok in children:
            t = tok.type
            if t in ("strong_open", "strong_close"):
                state["bold"] = t == "strong_open" or bold
            elif t in ("em_open", "em_close"):
                state["italic"] = t == "em_open"
            elif t in ("text", "code_inline", "html_inline"):
                run = paragraph.add_run(tok.content)
                run.bold, run.italic = state["bold"], state["italic"]
                if t == "code_inline":
                    run.font.name = "Consolas"
                    run.font.size = Pt((size or 10.5) - 1)
                    run.font.color.rgb = NAVY
                elif size:
                    run.font.size = Pt(size)
            elif t in ("softbreak",):
                paragraph.add_run(" ")
            elif t == "hardbreak":
                paragraph.add_run().add_break()
            elif t == "image":
                self.image(tok.attrs.get("src", ""), tok.content)

    def image(self, src: str, alt: str):
        path = (self.base / src).resolve()
        if not path.exists():
            self.doc.add_paragraph(f"[missing image: {src}]")
            return
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Cm(16.4))
        if alt:
            cap = self.doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = cap.add_run(f"Figure: {alt}")
            r.font.size, r.font.italic, r.font.color.rgb = Pt(9), True, GREY

    def table(self, rows):
        ncols = max(len(r) for r in rows)
        table = self.doc.add_table(rows=0, cols=ncols)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        size = 8 if ncols >= 5 else 9
        # widths proportional to each column's longest text, so descriptions get the room
        def measure(children):
            """(longest unbreakable word, total length); monospace code counts wider."""
            longest, total = 0, 0
            for c in children:
                if c.type in ("text", "code_inline"):
                    scale = 1.25 if c.type == "code_inline" else 1.0
                    total += len(c.content) * scale
                    longest = max([longest] + [len(w) * scale for w in c.content.split()])
            return longest, total

        weights = []
        for j in range(ncols):
            sizes = [measure(r[j]) for r in rows if j < len(r)]
            word = max(w for w, _ in sizes)
            text = min(max(t for _, t in sizes), 60)
            weights.append(max(word + 2, text * 0.6, 5))
        total_cm = 16.6
        widths = [Cm(total_cm * w / sum(weights)) for w in weights]
        table.autofit = False
        for i, cells in enumerate(rows):
            row = table.add_row()
            for j in range(ncols):
                cell = row.cells[j]
                cell.width = widths[j]
                cell.paragraphs[0].paragraph_format.space_after = Pt(0)
                if j < len(cells):
                    self.inline(cell.paragraphs[0], cells[j], size=size, bold=(i == 0))
                if i == 0:
                    shade(cell._tc, HEADER_FILL)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def code(self, text: str):
        for line in text.rstrip("\n").split("\n"):
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.left_indent = Cm(0.3)
            shade(p._p, CODE_FILL)
            r = p.add_run(line if line else " ")
            r.font.name, r.font.size = "Consolas", Pt(8.5)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def render(self, text: str, shift: int, chapter_title: str | None, chapter: int | None = None):
        tokens = self.md.parse(text)
        i, list_stack, first_h1 = 0, [], True
        while i < len(tokens):
            tok = tokens[i]
            if tok.type == "heading_open":
                level = int(tok.tag[1]) + shift
                content = tokens[i + 1].content.replace("`", "")
                if level == 1 and first_h1 and chapter_title:
                    content = chapter_title  # the chapter's own numbered title
                    first_h1 = False
                elif level == 2 and chapter:
                    self.section += 1  # number sections chapter.section, replacing the file's own numbers
                    content = f"{chapter}.{self.section} " + re.sub(r"^\d+\.\s+", "", content)
                self.doc.add_heading(content, level=min(level, 4))
                i += 3
                continue
            if tok.type in ("bullet_list_open", "ordered_list_open"):
                list_stack.append([tok.type == "ordered_list_open", int(tok.attrs.get("start", 1) or 1)])
            elif tok.type in ("bullet_list_close", "ordered_list_close"):
                list_stack.pop()
            elif tok.type == "paragraph_open":
                inline = tokens[i + 1]
                if len(inline.children) == 1 and inline.children[0].type == "image":
                    self.image(inline.children[0].attrs["src"], inline.children[0].content)
                elif list_stack and tokens[i - 1].type == "list_item_open":
                    ordered, counter = list_stack[-1]
                    p = self.doc.add_paragraph(style="List Bullet" if not ordered else None)
                    p.paragraph_format.space_after = Pt(3)
                    if ordered:
                        p.paragraph_format.left_indent = Cm(0.8)
                        p.paragraph_format.first_line_indent = Cm(-0.5)
                        p.add_run(f"{counter}. ")
                        list_stack[-1][1] += 1
                    self.inline(p, inline.children)
                else:
                    p = self.doc.add_paragraph()
                    if list_stack:
                        p.paragraph_format.left_indent = Cm(0.8)
                    self.inline(p, inline.children)
                i += 3
                continue
            elif tok.type == "table_open":
                rows, cur = [], None
                i += 1
                while tokens[i].type != "table_close":
                    t = tokens[i]
                    if t.type == "tr_open":
                        cur = []
                    elif t.type == "inline":
                        cur.append(t.children)
                    elif t.type == "tr_close":
                        rows.append(cur)
                    i += 1
                self.table(rows)
            elif tok.type in ("fence", "code_block"):
                self.code(tok.content)
            i += 1


def links_to_text(text: str) -> str:
    """Links to other docs read as plain text in print; external URLs keep their address."""
    def repl(m):
        label, target = m.group(1), m.group(2)
        if target.startswith("http") and target not in label:
            return f"{label} ({target})"
        return label
    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", repl, text)


def sample_queries_appendix(renderer: Renderer) -> None:
    doc = renderer.doc
    doc.add_heading("Appendix A. Sample Analytical Queries", level=1)
    doc.add_paragraph("Each query answers a key business question (section 1.3) and demonstrates an OLAP "
                      "operation. Timings are in the Query Performance Test Report (Chapter 8). Source: "
                      "docs/sample-queries.sql.")
    text = (DOCS / "sample-queries.sql").read_text(encoding="utf-8")
    for part in re.split(r"^-- @query ", text, flags=re.M)[1:]:
        header, _, body = part.partition("\n")
        qid, title, operation = [s.strip() for s in header.split("|")]
        doc.add_heading(f"{qid}. {title}", level=3)
        p = doc.add_paragraph()
        r = p.add_run(f"OLAP operation: {operation}")
        r.font.italic, r.font.color.rgb = True, GREY
        renderer.code(body.strip())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    setup(doc)
    footer(doc)
    title_page(doc)
    renderer = Renderer(doc, DOCS)
    for number, (title, files) in enumerate(CHAPTERS):
        chapter_title = f"{number}. {title}" if number else title
        renderer.section = 0
        for k, (name, shift) in enumerate(files):
            text = links_to_text((DOCS / name).read_text(encoding="utf-8"))
            renderer.render(text, shift, chapter_title if k == 0 else None, number or None)
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    sample_queries_appendix(renderer)
    doc.save(DOCX)
    print(f"wrote {DOCX.relative_to(ROOT)}")
    finish_with_word()


def finish_with_word() -> None:
    """Update the table of contents and export a PDF with Microsoft Word, if installed."""
    try:
        import win32com.client  # type: ignore
    except ImportError:
        import subprocess
        ps = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
              f"try {{ $d = $w.Documents.Open('{DOCX}'); $d.TablesOfContents.Item(1).Update(); "
              f"$d.Save(); $d.ExportAsFixedFormat('{DOCX.with_suffix('.pdf')}', 17); $d.Close() }} "
              f"finally {{ $w.Quit() }}")
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
        if result.returncode != 0:
            print("Word not available: open the .docx, update the table of contents, and save as PDF.")
            print(result.stderr[-500:])
            return
    print(f"wrote {DOCX.with_suffix('.pdf').relative_to(ROOT)} (table of contents updated)")


if __name__ == "__main__":
    main()
