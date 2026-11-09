# make_deck.py : the slide decks, built from Markdown sources with the numbers of the current build.
#   python3 code/tools/make_deck.py [root]          (run_all.R calls it after the Word copies when pandoc is installed)
#
# 1. Computes the facts the decks quote - survey, person and variable counts, check and review results, version and
#    build identity - from files in the repository only (crosswalks/, docs/run_log.md, docs/routing_check.csv,
#    docs/BUILD_ID, docs/decisions.md, code/), and writes them to docs/facts.csv.  Anyone with the repository can
#    rebuild a deck; the data are not needed.
# 2. Fills each deck source (docs/slides/<deck>.md) where it writes {{name}} with the fact of that name.  A name that
#    is not a fact stops the build, so a deck cannot show a placeholder or a stale number.  A line of the form
#    {{kind: file | option | option}} is an excerpt pulled from a repository file at build time (rows of a crosswalk,
#    a record, lines of the run log, a section or the table of contents of the decisions log, a codebook entry);
#    see EXCERPTS below and docs/slides/README.md.  An excerpt that finds nothing stops the build too.
# 3. Converts the filled source with pandoc into docs/slides/<deck>.pptx, using the NIDI reference template
#    (docs/slides/template/nidi_reference.pptx, derived from NIDI's template by code/tools/make_slide_template.py).
#
# 4. Adjusts what pandoc wrote, as md_to_word.py does for the Word copies: code blocks get explicit line breaks
#    (PowerPoint does not reliably show the raw ones pandoc writes) in Courier New; tables get column widths in
#    proportion to their content and the largest text size at which they fit; two-column slides are laid out here,
#    each column's blocks stacked from the top, because pandoc overlaps a column's tables.
#
# The .pptx files are derived copies (not tracked by Git): edit the .md source, not the PowerPoint file, which the
# next build replaces.  Needs pandoc (3.x) and Python 3 (standard library only).
import csv, datetime, glob, html, os, re, shutil, subprocess, sys, tempfile, zipfile

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("IMPD_ROOT", os.getcwd())
P = lambda *a: os.path.join(ROOT, *a)
DECKS = ["harmonization"]                                          # docs/slides/<name>.md -> docs/slides/<name>.pptx
REFERENCE = P("docs", "slides", "template", "nidi_reference.pptx")
csv.field_size_limit(2 ** 31 - 1)


def rows(*path):
    with open(P(*path), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def text(*path):
    with open(P(*path), encoding="utf-8") as f:
        return f.read()


def facts():
    """(name, value, description, source) for every number or label a deck may quote."""
    out = []
    add = lambda name, value, desc, src: out.append((name, value, desc, src))

    m = re.search(r'IMPD_VERSION\s*<-\s*"([^"]+)"', text("code", "R", "00_setup.R"))
    add("version", m.group(1), "IMPD public component version", "code/R/00_setup.R")
    bid = text("docs", "BUILD_ID").split()
    add("build_id", bid[0], "build identity (sha256 of crosswalks and code, first 12 hex digits)", "docs/BUILD_ID")
    built = datetime.date.fromisoformat(bid[2]) if len(bid) > 2 and re.match(r"\d{4}-\d\d-\d\d$", bid[2]) else datetime.date.today()
    add("build_date", built.isoformat(), "date of the build", "docs/BUILD_ID")
    add("build_month", built.strftime("%B %Y"), "month of the build", "docs/BUILD_ID")

    inc = [s for s in rows("crosswalks", "surveys.csv") if s["status"] == "included"]
    years = sorted(int(s["svy_year"]) for s in inc)
    add("n_surveys", len(inc), "surveys included", "crosswalks/surveys.csv")
    add("year_first", str(years[0]), "fieldwork year of the first survey", "crosswalks/surveys.csv")      # a year: no separator
    add("year_last", str(years[-1]), "fieldwork year of the last survey", "crosswalks/surveys.csv")
    add("n_survey_flat", sum(s["structure"] == "flat" for s in inc), "person-sample surveys (one person file)", "crosswalks/surveys.csv")
    add("n_survey_hh", sum(s["structure"] != "flat" for s in inc), "household surveys (heads, persons, roster files)", "crosswalks/surveys.csv")

    log = text("docs", "run_log.md")
    m = re.search(r"PASS row count equals the sum of roster/person rows \((\d+)\)", log)
    n_persons = int(m.group(1)) if m else None
    add("n_persons", n_persons, "persons in the main file", "docs/run_log.md")
    vm = rows("crosswalks", "variable_map.csv")
    n_main = sum(v["include_main"] == "1" for v in vm)
    add("n_vars_main", n_main, "harmonized variables in the main file", "crosswalks/variable_map.csv")
    add("n_targets", len(vm), "harmonized variables declared (main file and source-only)", "crosswalks/variable_map.csv")
    add("n_cells", n_persons * n_main if n_persons else None, "cells of the main file (persons x variables)", "docs/run_log.md, crosswalks/variable_map.csv")
    add("n_checks", len(re.findall(r"^- PASS", log, re.M)), "checks passed in the R build", "docs/run_log.md")
    add("n_checks_fail", len(re.findall(r"^- FAIL", log, re.M)), "checks failed in the R build", "docs/run_log.md")

    add("n_source_vars", len(rows("crosswalks", "source_variables.csv")), "source variables in the deposits", "crosswalks/source_variables.csv")
    add("n_skipped", len(rows("crosswalks", "source_skipped.csv")), "source variables deliberately not harmonized", "crosswalks/source_skipped.csv")
    add("n_valuesets", len({r["valueset"] for r in rows("crosswalks", "valuesets.csv")}), "value sets", "crosswalks/valuesets.csv")
    add("n_crosswalks", len(glob.glob(P("crosswalks", "*.csv"))), "crosswalk tables", "crosswalks/")
    add("n_vmap_rows", len(rows("crosswalks", "value_map.csv")), "value-map rows", "crosswalks/value_map.csv")
    add("n_approvals", len(rows("crosswalks", "label_approvals.csv")), "signed label approvals", "crosswalks/label_approvals.csv")
    m = re.search(r"^PARSERS\s*=\s*\{(.*?)\}", text("code", "crosswalk_builder", "questionnaires.py"), re.M)
    add("n_parsers", len(re.findall(r'"\w+"\s*:', m.group(1))), "questionnaire parsers (layouts)", "code/crosswalk_builder/questionnaires.py")

    rc = rows("docs", "routing_check.csv")
    add("routing_pairs", len(rc), "source x gate pairs in the routing check", "docs/routing_check.csv")
    add("routing_hold", sum(r["verdict"] == "holds" for r in rc), "routing pairs that hold exactly", "docs/routing_check.csv")
    add("routing_exc", sum(r["verdict"] == "holds with exceptions" for r in rc), "routing pairs that hold with listed exceptions", "docs/routing_check.csv")
    add("routing_fail", sum(r["verdict"] not in ("holds", "holds with exceptions") for r in rc), "routing pairs that fail", "docs/routing_check.csv")
    tr = [r for r in rc if r["target"] == "mig_yr_arr_cat5" and r["survey"] == "sing2009"]
    add("sing_transit_values", int(tr[0]["n_values"]) if tr else None, "SING 2009 arrival-year values behind the mig_transit gate", "docs/routing_check.csv")
    add("sing_transit_outside", int(tr[0]["n_outside"]) if tr else None, "of which outside the gate", "docs/routing_check.csv")

    w = rows("crosswalks", "wording.csv")
    for svy, how in (("sim2006", "qnum"), ("sim2006", "manual"), ("las2004", "name"), ("las2004", "manual"),
                     ("sim2020", "name"), ("sim2020", "manual"), ("sim2020", "prefix")):
        add(f"link_{svy}_{how}", sum(r["survey"] == svy and r["match"] == how for r in w),
            f"{svy} variables linked to their question by {how}", "crosswalks/wording.csv")

    secs = re.findall(r"^## (\d+)\.", text("docs", "decisions.md"), re.M)
    add("n_decisions", int(secs[-1]) if secs else 0, "numbered sections of the decisions log", "docs/decisions.md")
    missing = [n for n, v, _, _ in out if v is None]
    if missing:
        sys.exit("make_deck.py: could not compute " + ", ".join(missing))
    return out



# ---- excerpts: text pulled from repository files, written on their own line as {{kind: arg | option | option}} -------
#   table: <csv> | col=value | col~regex | columns=a,b,c | head=A,B,C | rows=N | cell=N | labels | transpose
#       rows of a CSV file as a table.  col=value keeps rows where the column equals the value, col~regex where it
#       matches; columns= selects and orders the columns, head= renames them for display; rows= caps the rows (a last
#       row says how many were left out); cell= caps the characters per cell; labels shows survey labels (SING 2009)
#       in place of keys (sing2009); transpose turns the table on its side, the first column becoming the header.
#   record: <csv> | col=value | columns=... | head=... | cell=N
#       one row of a CSV file as a two-column Field / Value table.
#   lines: <file> | match=regex | rows=N | width=N | strip=regex | header
#       lines of a text file that match, as a code block; header adds the file's first line; strip removes a pattern.
#   section: docs/decisions.md | <number> | chars=N
#       heading and opening text of a numbered section of the decisions log, cut at a sentence end.
#   toc: docs/decisions.md | last=N | first=N | cell=N
#       the numbered sections of the decisions log as a table: number, title, date.
#   codebook: <variable> | keep=Theme,Universe,... | strip=regex | cell=N
#       the header lines of a variable's codebook entry (docs/codebook.md): label and the kept bullet lines.
#   codebook-freq: <variable> | columns=code,label,SPVN2003,... | rows=N
#       the frequency table of a variable's codebook entry.
EXCERPT = re.compile(r"^\{\{([a-z][a-z-]*):\s*(.*?)\}\}[ \t]*$", re.M)


def cut(s, n):
    s = " ".join(str(s).split())
    if len(s) <= n:
        return s
    i = s.rfind(" ", 0, n)
    return s[: i if i > n // 2 else n].rstrip(",;:") + "…"


def parse_options(args):
    """'crosswalks/x.csv | target=mig_transit | columns=a,b | labels' -> (first argument, filters, options, flags)."""
    parts = [a.strip() for a in args.split("|")]
    first, filters, options, flags = parts[0], [], {}, set()
    for a in parts[1:]:
        if not a:
            continue
        m = re.match(r"^(\w+)\s*(=|~)\s*(.*)$", a, re.S)
        if m and m.group(1) in ("columns", "head", "rows", "cell", "width", "match", "strip", "chars", "last", "first", "keep"):
            options[m.group(1)] = m.group(3)
        elif m:
            filters.append((m.group(1), m.group(2), m.group(3)))
        else:
            flags.add(a)
    return first, filters, options, flags


def md_cell(s, literal=True):
    """A table cell; literal text (from a CSV) has its Markdown punctuation escaped so pandoc shows it as written."""
    s = str(s).replace("\n", " ")
    return re.sub(r"([\\*_\[\]<>|~^$`])", r"\\\1", s) if literal else s.replace("|", "\\|")


def md_table(header, body, align=None, literal=True):
    align = align or ["---"] * len(header)
    out = ["| " + " | ".join(md_cell(h, literal) for h in header) + " |", "| " + " | ".join(align) + " |"]
    out += ["| " + " | ".join(md_cell(c, literal) for c in r) + " |" for r in body]
    return "\n".join(out)


def select_rows(data, filters, where):
    for col, op, val in filters:
        if data and col not in data[0]:
            sys.exit(f"make_deck.py: {where}: no column {col}")
        data = [r for r in data if (r[col] == val if op == "=" else re.search(val, r[col]))]
    return data


def ex_table(args, where):
    path, filters, opt, flags = parse_options(args)
    data = select_rows(rows(path), filters, where)
    if not data:
        sys.exit(f"make_deck.py: {where}: no rows match")
    cols = opt["columns"].split(",") if "columns" in opt else list(data[0].keys())
    for c in cols:
        if c not in data[0]:
            sys.exit(f"make_deck.py: {where}: no column {c}")
    head = opt["head"].split(",") if "head" in opt else cols
    if len(head) != len(cols):
        sys.exit(f"make_deck.py: {where}: head= needs {len(cols)} names")
    cell = int(opt.get("cell", 90))
    labels = {s["svy_name"].lower(): s["label"] for s in rows("crosswalks", "surveys.csv")} if "labels" in flags else {}
    body = [[cut(labels.get(r[c], r[c]) if c == "survey" else r[c], cell) for c in cols] for r in data]
    limit = int(opt["rows"]) if "rows" in opt else None
    if limit and len(body) > limit:
        left = len(body) - limit
        body = body[:limit] + [[f"… and {left} more row{'s' if left > 1 else ''}"] + [""] * (len(cols) - 1)]
    if "transpose" in flags:
        header = [""] + [r[0] for r in body]
        body = [[head[j]] + [r[j] for r in body] for j in range(1, len(cols))]
        return md_table(header, body)
    numeric = [all(re.fullmatch(r"-?[\d.,]+", r[j]) for r in body if r[j]) for j in range(len(cols))]
    return md_table(head, body, ["---:" if n else "---" for n in numeric])


def ex_record(args, where):
    path, filters, opt, flags = parse_options(args)
    data = select_rows(rows(path), filters, where)
    if len(data) != 1:
        sys.exit(f"make_deck.py: {where}: {len(data)} rows match, one is needed")
    r = data[0]
    cols = opt["columns"].split(",") if "columns" in opt else list(r.keys())
    head = opt["head"].split(",") if "head" in opt else cols
    cell = int(opt.get("cell", 120))
    for c in cols:
        if c not in r:
            sys.exit(f"make_deck.py: {where}: no column {c}")
    return md_table(["Field", "Value"], [[h, cut(r[c], cell)] for h, c in zip(head, cols)])


def ex_lines(args, where):
    path, _, opt, flags = parse_options(args)
    lines = text(path).splitlines()
    picked = [l for l in lines if re.search(opt.get("match", "."), l)]
    if not picked:
        sys.exit(f"make_deck.py: {where}: no line matches")
    limit = int(opt["rows"]) if "rows" in opt else None
    left = len(picked) - limit if limit and len(picked) > limit else 0
    picked = picked[:limit] if limit else picked
    if "strip" in opt:
        picked = [re.sub(opt["strip"], "", l) for l in picked]
    width = int(opt.get("width", 90))
    out = ([lines[0]] if "header" in flags else []) + [l if len(l) <= width else l[: width - 1] + "…" for l in picked]
    if left:
        out.append(f"… and {left} more line{'s' if left > 1 else ''}")
    return "```\n" + "\n".join(out) + "\n```"


def decisions_sections(path):
    """[(number, title, date, body)] from the '## N. title (date)' headings of the decisions log."""
    out, cur = [], None
    for line in text(path).splitlines():
        m = re.match(r"^## (\w+)\. (.*)$", line)
        if m:
            title = m.group(2).strip()
            d = re.search(r"\(([^()]*\b\d{4}\b[^()]*)\)\s*$", title)
            date = d.group(1).split(";")[0].strip() if d else ""
            if d:
                title = title[: d.start()].strip()
            cur = [m.group(1), title, date, []]
            out.append(cur)
        elif cur is not None and not line.startswith("# "):
            cur[3].append(line)
    return [(n, ti, da, "\n".join(b).strip()) for n, ti, da, b in out]


def ex_section(args, where):
    path, _, opt, flags = parse_options(args)
    parts = [a.strip() for a in args.split("|")]
    number = parts[1] if len(parts) > 1 else ""
    secs = [s for s in decisions_sections(path) if s[0] == number]
    if not secs:
        sys.exit(f"make_deck.py: {where}: no section {number} in {path}")
    n, title, date, body = secs[0]
    chars = int(opt.get("chars", 600))
    if len(body) > chars:
        end = max(body.rfind(". ", 0, chars), body.rfind(".\n", 0, chars))
        body = (body[: end + 1] if end > chars // 3 else body[:chars].rstrip()) + " …"
    head = f"**§{n} · {title}**" + (f" *({date})*" if date else "")
    return head + "\n\n" + body


def ex_toc(args, where):
    path, _, opt, flags = parse_options(args)
    secs = decisions_sections(path)
    if "first" in opt:
        secs = secs[: int(opt["first"])]
    if "last" in opt:
        secs = secs[-int(opt["last"]):]
    if not secs:
        sys.exit(f"make_deck.py: {where}: no sections in {path}")
    cell = int(opt.get("cell", 80))
    return md_table(["§", "Decision", "Date"], [[n, cut(ti, cell), da] for n, ti, da, _ in secs], literal=False)


def codebook_entry(var, where):
    cb = text("docs", "codebook.md")
    m = re.search(r"^### `" + re.escape(var) + r"` \{#" + re.escape(var) + r"\}\n(.*?)(?=^---$)", cb, re.M | re.S)
    if not m:
        sys.exit(f"make_deck.py: {where}: no codebook entry for {var}")
    return m.group(1)


def ex_codebook(args, where):
    var, _, opt, flags = parse_options(args)
    entry = codebook_entry(var, where)
    keep = [k.strip() for k in opt["keep"].split(",")] if "keep" in opt else None
    cell = int(opt.get("cell", 140))
    out = []
    for line in entry.splitlines():
        if line.startswith("**") and not out:
            out.append(line)
        elif line.startswith("- "):
            body = line[2:]
            if keep and not any(body.startswith(k) for k in keep):
                continue
            if "strip" in opt:
                body = re.sub(opt["strip"], "", body)
            out.append("- " + cut(body, cell))
    if not out:
        sys.exit(f"make_deck.py: {where}: nothing kept from the entry for {var}")
    return "\n\n".join(out[:1] + ["\n".join(out[1:])]) if out[0].startswith("**") else "\n".join(out)


def ex_codebook_freq(args, where):
    var, _, opt, flags = parse_options(args)
    entry = codebook_entry(var, where)
    m = re.search(r"Frequencies \(unweighted\):\n\n((?:\|.*\n?)+)", entry)
    if not m:
        sys.exit(f"make_deck.py: {where}: no frequency table for {var}")
    tbl = [[c.strip() for c in l.strip().strip("|").split("|")] for l in m.group(1).strip().splitlines()]
    header, body = tbl[0], [r for r in tbl[2:]]
    cols = opt["columns"].split(",") if "columns" in opt else header
    idx = []
    for c in cols:
        if c not in header:
            sys.exit(f"make_deck.py: {where}: no column {c} in the frequency table of {var}")
        idx.append(header.index(c))
    limit = int(opt["rows"]) if "rows" in opt else None
    body = body[:limit] if limit else body
    sel = [[r[i] for i in idx] for r in body]
    numeric = [all(re.fullmatch(r"-?\d+", r[j]) for r in sel) for j in range(len(cols))]
    return md_table(cols, sel, ["---:" if n else "---" for n in numeric])


EXCERPTS = {"table": ex_table, "record": ex_record, "lines": ex_lines, "section": ex_section, "toc": ex_toc,
            "codebook": ex_codebook, "codebook-freq": ex_codebook_freq}


def expand_excerpts(body, deck):
    def one(m):
        kind, args = m.group(1), m.group(2)
        where = f"deck {deck}, {{{{{kind}: {args}}}}}"
        if kind not in EXCERPTS:
            sys.exit(f"make_deck.py: {where}: unknown excerpt kind (known: {', '.join(EXCERPTS)})")
        return EXCERPTS[kind](args, where)
    return EXCERPT.sub(one, body)


def shown(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


def code_block(m, size):
    """pandoc writes a code block as one run whose text holds raw line breaks, which PowerPoint does not reliably show:
    one run per line, joined by explicit line breaks, in Courier New at the page's code size."""
    lines = m.group(1).split("\n")
    rpr = f'<a:rPr sz="{size}"><a:latin typeface="Courier New" /><a:cs typeface="Courier New" /></a:rPr>'
    return f'<a:br>{rpr}</a:br>'.join(f'<a:r>{rpr}<a:t>{line}</a:t></a:r>' for line in lines)


EMU = 914400
COLUMN = dict(x=(0.6, 5.0), width=4.2, top=1.1, bottom=6.5)      # the two columns of the wide NIDI page (inches)
GAP = 0.12


# Arial glyph widths in em, for estimating how text wraps (the few glyphs not listed count as 0.556)
_ARIAL = {"a": .556, "b": .556, "c": .5, "d": .556, "e": .556, "f": .278, "g": .556, "h": .556, "i": .222, "j": .222, "k": .5,
          "l": .222, "m": .833, "n": .556, "o": .556, "p": .556, "q": .556, "r": .333, "s": .5, "t": .278, "u": .556, "v": .5,
          "w": .722, "x": .5, "y": .5, "z": .5, "A": .667, "B": .667, "C": .722, "D": .722, "E": .667, "F": .611, "G": .778,
          "H": .722, "I": .278, "J": .5, "K": .667, "L": .556, "M": .833, "N": .722, "O": .778, "P": .667, "Q": .778, "R": .722,
          "S": .667, "T": .611, "U": .722, "V": .667, "W": .944, "X": .667, "Y": .667, "Z": .611, " ": .278, "_": .556, "-": .333,
          ".": .278, ",": .278, ":": .278, ";": .278, "(": .333, ")": .333, "/": .278, "\\": .278, "|": .26, "=": .584, "<": .584,
          ">": .584, "*": .389, "'": .191, "‘": .222, "’": .222, '"': .355, "^": .469, "→": 1.0, "…": 1.0,
          "·": .333, "≤": .584, "§": .556, "[": .278, "]": .278, "{": .334, "}": .334, "#": .556, "%": .889}


def em(s):
    """Width of a string in em, Arial."""
    return sum(_ARIAL.get(c, .556) for c in s)


def wrapped_lines(s, width_in, pt):
    """Lines a string takes when wrapped at a width, at a size (words break only when wider than the line)."""
    line_em = max(0.1, width_in * 72 / pt)
    lines, used = 1, 0.0
    for word in s.split(" "):
        w = em(word)
        if used and used + em(" ") + w > line_em:
            lines, used = lines + 1, 0.0
        while w > line_em:                                   # a word wider than the line breaks across lines
            lines, w = lines + 1, w - line_em
        used += (em(" ") if used else 0) + w
    return lines


def text_height(sp, width_in, default_sz=1600):
    """Estimated height in inches of a text shape pandoc wrote: paragraphs wrap at the column width."""
    h = 0.0
    for para in re.findall(r"<a:p>.*?</a:p>", sp, re.S):
        m = re.search(r'<a:rPr[^>]*\bsz="(\d+)"', para)
        pt = (int(m.group(1)) if m else default_sz) / 100
        words = html.unescape("".join(re.findall(r"<a:t>([^<]*)</a:t>", para)))
        runs = re.findall(r"<a:r>(.*?)</a:r>", para, re.S)
        if runs and all("Courier" in r for r in runs):      # a code block: one line per explicit break
            lines = para.count("<a:br>") + 1
        else:
            lines = wrapped_lines(words, width_in - 0.3, pt)
        h += (lines * 1.15 * pt + 0.4 * pt) / 72             # Arial line height, and the 0.4-line space before
    return h


def fit_table(xml, width_in, size=None, budget=None):
    """Set a table's column widths and text size.  At a given size every column is at least as wide as its longest
    word (so no word breaks) and the rest of the width is shared by content; the size is the given one, or the largest
    (16 down to 9 pt) at which the words fit and the table fits the budget.  Returns (xml, height in inches, whether
    every word fits its column at that size)."""
    cols = re.findall(r'<a:gridCol w="(\d+)"\s*/>', xml)
    n = len(cols)
    cells = []
    for row in re.findall(r"<a:tr\b.*?</a:tr>", xml, re.S):
        cells.append([html.unescape(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", c)))
                      for c in re.findall(r"<a:tc>.*?</a:tc>", row, re.S)[:n]])
    # the widest word of each column (in em) decides its least width; a header word counts up to 4 em (it may break)
    longest = [max([em(w) for r in cells[1:] for w in r[j].split()] + [min(em(w), 4.0) for w in cells[0][j].split()] + [0.5])
               for j in range(n)]
    need = [max(2.0, min(max((em(r[j]) for r in cells), default=0), 35.0)) for j in range(n)]

    def layout(pt):
        """(column widths in inches, height in inches, whether every word fits its column) at this size."""
        least = [min(lw, 7.0) * pt / 72 + 0.25 for lw in longest]   # cell insets; a word past 7 em may break
        ok = sum(least) <= width_in
        if ok:
            extra = width_in - sum(least)
            widths = [l + extra * nd / sum(need) for l, nd in zip(least, need)]
        else:                                                 # share the width by content; long words will break
            widths = [width_in * nd / sum(need) for nd in need]
        h = 0
        for r in cells:
            lines = max(wrapped_lines(words, widths[j] - 0.2, pt) for j, words in enumerate(r))
            h += lines * 1.2 * pt + 8
        return widths, h / 72, ok
    if size is None:
        size = next((s for s in (16, 14, 12, 11, 10) if layout(s)[2] and layout(s)[1] <= budget), 9)
    widths, height, ok = layout(size)
    emus = [int(w * EMU) for w in widths]
    emus[-1] += int(width_in * EMU) - sum(emus)
    xml = re.sub(r"<a:tblGrid>.*?</a:tblGrid>", "<a:tblGrid>" + "".join(f'<a:gridCol w="{w}" />' for w in emus) + "</a:tblGrid>",
                 xml, count=1, flags=re.S)
    xml = re.sub(r"<a:rPr\b([^>]*?)(/?)>",
                 lambda r: r.group(0) if "sz=" in r.group(1) else f'<a:rPr{r.group(1)} sz="{size * 100}"{r.group(2)}>', xml)
    return xml, height, ok


def place(shape, x, y, w, h):
    """Give a shape an explicit position (inches), overriding the layout placeholder's."""
    xfrm = f'<a:off x="{int(x * EMU)}" y="{int(y * EMU)}" /><a:ext cx="{int(w * EMU)}" cy="{int(h * EMU)}" />'
    if shape.startswith("<p:graphicFrame"):
        return re.sub(r"<p:xfrm>.*?</p:xfrm>", f"<p:xfrm>{xfrm}</p:xfrm>", shape, count=1, flags=re.S)
    shape = re.sub(r"<p:spPr\s*/>", "<p:spPr></p:spPr>", shape, count=1)
    shape = re.sub(r"<p:spPr>(?:<a:xfrm>.*?</a:xfrm>)?", f"<p:spPr><a:xfrm>{xfrm}</a:xfrm>", shape, count=1, flags=re.S)
    return shape


def lay_out_columns(x, layout):
    """A two-column slide: pandoc puts every table of a column into one placeholder, so with more than one block per
    column the pieces overlap.  Stack each column's shapes from the top instead, in the order written, and size the
    tables so that the column fits the page."""
    shapes = [m for m in re.finditer(r"<p:(sp|graphicFrame)>.*?</p:\1>", x, re.S) if 'type="title"' not in m.group(0)]
    def idx_of(m):
        i = re.search(r'<p:ph[^>]*\bidx="(\d+)"', m.group(0))
        return int(i.group(1)) if i else 0
    # which column a shape belongs to: text shapes say so by their placeholder (Two Content: 1 left, 2 right;
    # Comparison: 1 and 2 left, 3 and 4 right); a table carries idx 1 whatever its column, so it follows the text
    # shape before it, except on a Two Content slide whose right column is the table alone
    columns = {0: [], 1: []}
    col = 0
    for k, m in enumerate(shapes):
        i = idx_of(m)
        if m.group(1) == "sp":
            col = 1 if (layout == "Two Content" and i == 2) or (layout == "Comparison" and i in (3, 4)) else 0
        elif layout == "Two Content" and not any(idx_of(n) == 2 for n in shapes[k + 1:] if n.group(1) == "sp"):
            col = 1
        columns[col].append(m)
    out, width = {}, COLUMN["width"]
    room = COLUMN["bottom"] - COLUMN["top"]
    texts = {m.start(): text_height(m.group(0), width) for col in columns for m in columns[col] if m.group(1) == "sp"}
    fixed = {col: sum(texts[m.start()] for m in items if m.group(1) == "sp") + GAP * max(0, len(items) - 1)
             for col, items in columns.items()}

    def fits(col, size):
        fitted = {m.start(): fit_table(m.group(0), width, size=size) for m in columns[col] if m.group(1) == "graphicFrame"}
        ok = all(k for _, _, k in fitted.values()) and fixed[col] + sum(h for _, h, _ in fitted.values()) <= room
        return fitted, ok
    # one text size for every table of the slide: the largest at which both columns fit (9 pt if none does)
    size = next((s for s in (16, 14, 12, 11, 10, 9) if all(fits(col, s)[1] for col in columns)), 9)
    for col, items in columns.items():
        chosen = fits(col, size)[0]
        if os.environ.get("IMPD_DECK_DEBUG") and chosen:
            print(f"    column {col}: text {fixed[col]:.2f} in, tables at {size} pt: {[round(h, 2) for _, h, _ in chosen.values()]}")
        y = COLUMN["top"]
        for m in items:
            if m.group(1) == "sp":
                h, s = texts[m.start()], m.group(0)
            else:
                s, h, _ = chosen[m.start()]
            out[m.start()] = place(s, COLUMN["x"][col], y, width, h)
            y += h + GAP
    for m in reversed(shapes):
        if m.start() in out:
            x = x[: m.start()] + out[m.start()] + x[m.end():]
    return x


def fix_slides(pptx):
    """Adjust what pandoc wrote: code blocks (see code_block); tables, whose width is shared among the columns by
    their content and whose text size is the largest at which they fit the page; and the two-column slides, which are
    laid out here (see lay_out_columns)."""
    with zipfile.ZipFile(pptx) as z:
        layouts = {}
        for n in z.namelist():
            if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", n):
                layouts[os.path.basename(n)] = re.search(r'<p:cSld name="([^"]*)"', z.read(n).decode("utf-8")).group(1)
        slide_layout = {}
        for n in z.namelist():
            m = re.match(r"ppt/slides/_rels/(slide\d+\.xml)\.rels$", n)
            if m:
                lay = re.search(r"slideLayouts/(slideLayout\d+\.xml)", z.read(n).decode("utf-8"))
                slide_layout[m.group(1)] = layouts.get(lay.group(1), "") if lay else ""
    tmp = pptx + ".tmp"
    with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
                x = data.decode("utf-8")
                layout = slide_layout.get(os.path.basename(item.filename), "")
                if os.environ.get("IMPD_DECK_DEBUG"):
                    print(f"  {item.filename} ({layout}): {' '.join(re.findall(r'<a:t>([^<]*)', x))[:60]}")
                columns = layout in ("Two Content", "Comparison")
                # a code block is a paragraph holding one Courier run; inline code inside a sentence keeps its size
                x = re.sub(r'(?<=</a:pPr>)<a:r><a:rPr><a:latin typeface="Courier" /></a:rPr><a:t>([^<]*)</a:t></a:r>(?=</a:p>)',
                           lambda m: code_block(m, 1100 if columns else 1300), x)
                x = x.replace('<a:latin typeface="Courier" />', '<a:latin typeface="Courier New" />')
                if columns:
                    x = lay_out_columns(x, layout)
                else:                                         # a full-width table: the space below its sentence
                    width = 7.8 if layout == "Title and Content" else 8.6
                    x = re.sub(r"<a:tbl>.*?</a:tbl>", lambda m: fit_table(m.group(0), width, budget=4.4)[0], x, flags=re.S)
                data = x.encode("utf-8")
            zout.writestr(item, data)
    os.replace(tmp, pptx)


def main():
    fx = facts()
    with open(P("docs", "facts.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["name", "value", "description", "source"])
        wr.writerows(fx)
    print(f"Facts: {len(fx)} -> docs/facts.csv")
    pandoc = shutil.which("pandoc")
    if not pandoc:
        sys.exit("make_deck.py: pandoc not found; docs/facts.csv written, decks not built")
    value = {n: shown(v) for n, v, _, _ in fx}
    rc = 0
    for deck in DECKS:
        src = P("docs", "slides", deck + ".md")
        body = text("docs", "slides", deck + ".md")
        unknown = sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", body)) - set(value))
        if unknown:
            print(f"Deck {deck}: unknown fact(s) {', '.join(unknown)} - not built (facts are listed in docs/facts.csv)")
            rc = 1
            continue
        filled = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: value[m.group(1)], body)
        filled = expand_excerpts(filled, deck)
        out = P("docs", "slides", deck + ".pptx")
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, deck + ".md")
            with open(md, "w", encoding="utf-8") as f:
                f.write(filled)
            r = subprocess.run([pandoc, md, "-o", out, "--slide-level=2", "--reference-doc=" + REFERENCE],
                               capture_output=True, text=True)
        if r.returncode != 0:
            print(f"Deck {deck}: pandoc failed ({r.stderr.strip()[:500]})")
            rc = 1
            continue
        fix_slides(out)
        print(f"Deck: {os.path.relpath(src, ROOT)} -> {os.path.relpath(out, ROOT)} ({os.path.getsize(out) / 1e6:.1f} MB)")
    sys.exit(rc)


if __name__ == "__main__":
    main()
