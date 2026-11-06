# md_to_word.py : Word copies of the Markdown documents (docs/word/*.docx), for readers who prefer Word.
#   python3 code/tools/md_to_word.py            (from the project root; run_all.R calls it after the checks when
#                                                pandoc is installed - the Word files are derived copies, not build outputs)
# Needs pandoc (3.x).  Each file is converted with pandoc, then the page setup and the tables are adjusted: the codebook
# and the worked example are landscape with narrow margins and a small base font (their per-survey tables have up to ten
# columns), every table is stretched to the text width with a wider first column, and the code font follows the base size.
import os, re, shutil, subprocess, sys, tempfile, zipfile

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("IMPD_ROOT", os.getcwd())   # argument first: run_all.R passes the root
OUT = os.path.join(ROOT, "docs", "word")
DOCS = [  # (source, landscape, base font size in half-points, pandoc input format)
    ("README.md", False, 22, "gfm"),
    ("docs/decisions.md", False, 22, "gfm"),
    ("docs/run_log.md", False, 22, "gfm"),
    ("docs/example_analysis.md", True, 20, "gfm"),
    ("docs/harmonization.md", False, 22, "gfm"),
    ("docs/codebook.md", True, 18, "gfm+attributes"),   # heading ids {#...} are attributes, not text
]
LANDSCAPE = ('<w:sectPr><w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/><w:pgMar w:top="720" w:right="720" '
             'w:bottom="720" w:left="720" w:header="400" w:footer="400" w:gutter="0"/></w:sectPr>')


def fix_tables(xml, width):
    """Full-width tables: fixed layout, grid and cell widths summing to the text width, first column wider."""
    def one(m):
        t = m.group(0)
        n = t.count("<w:gridCol")
        if n == 0:
            return t
        first = int(width * (0.16 if n > 2 else 0.35)) if n > 1 else width
        rest = (width - first) // (n - 1) if n > 1 else 0
        ws = [first] + [rest] * (n - 1)
        t = re.sub(r"<w:tblW [^>]*/>", '<w:tblW w:type="dxa" w:w="%d" />' % width, t, count=1)
        t = re.sub(r"<w:tblLook ", '<w:tblLayout w:type="fixed" /><w:tblLook ', t, count=1)
        t = re.sub(r"<w:tblGrid>.*?</w:tblGrid>", "<w:tblGrid>" + "".join('<w:gridCol w:w="%d" />' % w for w in ws) + "</w:tblGrid>", t, count=1, flags=re.S)
        def row(rm):
            i = [0]
            def cell(_):
                w = ws[min(i[0], n - 1)]; i[0] += 1
                return '<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa" /></w:tcPr>' % w
            return re.sub(r"<w:tc>", cell, rm.group(0))
        return re.sub(r"<w:tr>.*?</w:tr>", row, t, flags=re.S)
    return re.sub(r"<w:tbl>.*?</w:tbl>", one, xml, flags=re.S)


def convert(src, landscape, size, fmt):
    out = os.path.join(OUT, os.path.splitext(os.path.basename(src))[0] + ".docx")
    path = os.path.join(ROOT, src)
    text = open(path, encoding="utf-8").read()
    if "<details class='more'>" in text:
        # the codebook's collapsible 'more detail' blocks: Word cannot fold, so the block title becomes a bold run-in
        # heading and the content follows as ordinary paragraphs (pandoc would drop the raw HTML and its title)
        text = re.sub(r"^<details class='more'><summary>(.*)</summary>$", r"**\1** *(more detail)*", text, flags=re.M)
        text = re.sub(r"^</details>$", "", text, flags=re.M)
        path = os.path.join(tempfile.mkdtemp(), os.path.basename(src))
        open(path, "w", encoding="utf-8").write(text)
    subprocess.run(["pandoc", path, "-f", fmt, "-t", "docx", "-o", out], check=True)
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(out) as z:
        z.extractall(tmp)
    p = os.path.join(tmp, "word", "document.xml"); d = open(p, encoding="utf-8").read()
    if landscape:
        d = d.replace("<w:sectPr />", LANDSCAPE); width = 16838 - 1440
    else:
        width = 11906 - 2880
    open(p, "w", encoding="utf-8").write(fix_tables(d, width))
    ps = os.path.join(tmp, "word", "styles.xml"); s = open(ps, encoding="utf-8").read()
    s = s.replace('<w:sz w:val="24" />\n        <w:szCs w:val="24" />', '<w:sz w:val="%d" />\n        <w:szCs w:val="%d" />' % (size, size), 1)
    s = re.sub(r'(<w:style [^>]*w:styleId="VerbatimChar"[^>]*>.*?)<w:sz w:val="22" />', lambda m: m.group(1) + '<w:sz w:val="%d" />' % max(size - 2, 16), s, count=1, flags=re.S)
    open(ps, "w", encoding="utf-8").write(s)
    os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(tmp):
            for f in files:
                full = os.path.join(root, f); z.write(full, os.path.relpath(full, tmp))
    shutil.rmtree(tmp)
    return out


if shutil.which("pandoc") is None:
    sys.exit("md_to_word.py: pandoc not found - Word copies not produced (the Markdown and HTML documents are the reference)")
os.makedirs(OUT, exist_ok=True)
for src, landscape, size, fmt in DOCS:
    out = convert(src, landscape, size, fmt)
    print("Word copy: %s -> %s (%.1f MB)" % (src, os.path.relpath(out, ROOT), os.path.getsize(out) / 1e6))
