# make_deck.py : the slide decks, built from Markdown sources with the numbers of the current build.
#   python3 code/tools/make_deck.py [root]          (run_all.R calls it after the Word copies when pandoc is installed)
#
# 1. Computes the facts the decks quote - survey, person and variable counts, check and review results, version and
#    build identity - from files in the repository only (crosswalks/, docs/run_log.md, docs/routing_check.csv,
#    docs/BUILD_ID, docs/decisions.md, code/), and writes them to docs/facts.csv.  Anyone with the repository can
#    rebuild a deck; the data are not needed.
# 2. Fills each deck source (docs/slides/<deck>.md) where it writes {{name}} with the fact of that name.  A name that
#    is not a fact stops the build, so a deck cannot show a placeholder or a stale number.
# 3. Converts the filled source with pandoc into docs/slides/<deck>.pptx, using the NIDI reference template
#    (docs/slides/template/nidi_reference.pptx, derived from NIDI's template by code/tools/make_slide_template.py).
#
# 4. Adjusts what pandoc wrote, as md_to_word.py does for the Word copies: code blocks get explicit line breaks
#    (PowerPoint does not reliably show the raw ones pandoc writes) in Courier New; tables get a text size that
#    follows their content and column widths in proportion to it.
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


def shown(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


def code_block(m, size):
    """pandoc writes a code block as one run whose text holds raw line breaks, which PowerPoint does not reliably show:
    one run per line, joined by explicit line breaks, in Courier New at the page's code size."""
    lines = m.group(1).split("\n")
    rpr = f'<a:rPr sz="{size}"><a:latin typeface="Courier New" /><a:cs typeface="Courier New" /></a:rPr>'
    return f'<a:br>{rpr}</a:br>'.join(f'<a:r>{rpr}<a:t>{line}</a:t></a:r>' for line in lines)


def fix_slides(pptx):
    """Adjust what pandoc wrote: code blocks (see code_block); tables, which get the 18 pt default and equal columns:
    the text size follows how much the table holds (16, 14 or 12 pt; 2 pt less in one of two columns) and the width is
    shared among the columns by their content."""
    def table(m, columns):
        t = m.group(0)
        chars = len(html.unescape("".join(re.findall(r"<a:t>([^<]*)</a:t>", t))))
        size = (1600 if chars <= 500 else 1400 if chars <= 1000 else 1200) - (200 if columns else 0)
        cols = re.findall(r'<a:gridCol w="(\d+)"\s*/>', t)
        if not cols:
            return t
        total, n = sum(int(c) for c in cols), len(cols)
        need = [4] * n                                       # characters a column needs: its longest cell, capped
        for row in re.findall(r"<a:tr\b.*?</a:tr>", t, re.S):
            for j, cell in enumerate(re.findall(r"<a:tc>.*?</a:tc>", row, re.S)[:n]):
                words = html.unescape(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", cell)))
                longest_word = max((len(w) for w in words.split()), default=0)
                need[j] = max(need[j], min(len(words), 70), 2 * longest_word)
        weights = [x ** 0.75 for x in need]
        widths = [int(total * w / sum(weights)) for w in weights]
        widths[-1] += total - sum(widths)
        t = re.sub(r"<a:tblGrid>.*?</a:tblGrid>", "<a:tblGrid>" + "".join(f'<a:gridCol w="{w}" />' for w in widths) + "</a:tblGrid>",
                   t, count=1, flags=re.S)
        return re.sub(r"<a:rPr\b([^>]*?)(/?)>",
                      lambda r: r.group(0) if "sz=" in r.group(1) else f'<a:rPr{r.group(1)} sz="{size}"{r.group(2)}>', t)
    tmp = pptx + ".tmp"
    with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
                x = data.decode("utf-8")
                columns = x.count("<p:sp>") >= 3                      # title + two column bodies
                # a code block is a paragraph holding one Courier run; inline code inside a sentence keeps its size
                x = re.sub(r'(?<=</a:pPr>)<a:r><a:rPr><a:latin typeface="Courier" /></a:rPr><a:t>([^<]*)</a:t></a:r>(?=</a:p>)',
                           lambda m: code_block(m, 1100 if columns else 1300), x)
                x = x.replace('<a:latin typeface="Courier" />', '<a:latin typeface="Courier New" />')
                x = re.sub(r"<a:tbl>.*?</a:tbl>", lambda m: table(m, columns), x, flags=re.S)
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
