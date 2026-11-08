"""
IMPD crosswalk builder -- questionnaire text extraction
======================================================

Extracts the full question wording, answer options, routing and
randomisation notes from the questionnaire / codebook PDFs shipped in the
DANS deposits, and writes them to crosswalks/questionnaire_items.csv.

The file is the raw material for the per-variable wording tables in the
codebook (surveys in columns, question text and answer categories in
rows).  Parsing is best-effort: the cleaned full text of every question
block is always kept (column block_text), so a researcher can read the
exact wording even where the structured fields are incomplete.

Sources (all in the DANS deposits; text extracted with pdftotext -layout):
  SPVA 2002  data/raw/spva2002/dat/p1684.pdf            codebook-questionnaire
  SPVN 2003  data/raw/spvn2003/SPVA2003 Codeboek.pdf    questionnaire with variable names
  LAS 2004/05 data/raw/las2004/.../Bijlage 3 Veldwerkverslag LAS 2004-2005.pdf  appendix 1a of the fieldwork report (Veldkamp hardcopy)
  SIM 2006   data/raw/sim2006/.../V3996 klvr 9 aug.pdf                     Veldkamp CAPI script printout (no variable names)
  SING 2009  data/raw/sing2009/SING09-VRAGENLIJST_LAATSTE VERSIE nov09.pdf   Veldkamp CAPI script printout (no variable names)
  SIM 2011   data/raw/sim2011/Bijlagen/Bijlage_g_-_Hardcopy_vragenlijst.pdf  hardcopy with variable names (appendix g)
  SIM 2015   data/raw/sim2015/Docu/SIM2015_Vragenlijst_CAWI.pdf and _CAPI.pdf (TNS NIPO)
  SIM 2020   data/raw/sim2020/documentatie/SIM2020 Vragenlijst.pdf          (Labyrinth/TNS format)

Run from the IMPD root:  python code/crosswalk_builder/questionnaires.py
(build.py calls it as well).
"""
import csv
import os
import re
import subprocess
import sys

ROOT = os.environ.get("IMPD_ROOT", os.getcwd())
OUT_TXT = os.path.join(ROOT, "data", "interim", "questionnaires")
OUT_CSV = os.path.join(ROOT, "crosswalks", "questionnaire_items.csv")

# the questionnaire PDF(s) of every survey, from the survey modules (surveys/<key>.py: QUESTIONNAIRES):
# (survey, instrument, pdf path relative to ROOT, parser, (start, end) regexes slicing the text to the questionnaire or None)
import surveys as _surveys
SOURCES = _surveys.QUESTIONNAIRES

COLS = ["survey", "instrument", "qid", "qnames", "block", "split_half", "subitem_splits", "routing",
        "randomization", "intro", "question_text", "proposition", "format", "answer_options", "subitems", "kind", "block_text"]
# subitem_splits: one letter (or empty) per sub-item, "|"-separated, when a *SPLIT HALF marker stands inside a grid: the marker
# governs the sub-items printed after it; the sub-items before it are not restricted even when a marker precedes the grid
# header (SIM 2020 MENTALGEZ: the common MHI-5 items went to both halves, the three extras to B only - verified in 99_checks.R)
# intro: introduction / lead-in text printed with the question; proposition: the statement of a battery item printed inside
# the question block (hardcopy formats print the lead-in and the statement as one question); format: response widget,
# numeric bounds and units; kind: question | heading | instruction
OUT_CONSTR = os.path.join(ROOT, "crosswalks", "questionnaire_constructed.csv")
CONSTRUCTED = {}
# SCP/Veldkamp constructs in the LAS 2004/05, SIM 2006, SING 2009 and SIM 2011 deposits: these questionnaires print no list
# of derived variables, so the descriptions are written from the data labels and the SCP documentation (name -> description);
# they live in the survey modules (surveys/<key>.py: CONSTRUCTED; shared texts in surveys/_shared.py)
CONSTRUCTED_MANUAL = _surveys.CONSTRUCTED
DERIVED_AT = {}       # survey -> {NAME: qid}: constructed variables printed after the question block they derive from     # survey -> {name: description}: variables the codebooks list as constructed (no questionnaire item)


# ----------------------------------------------------------------- helpers
def pdf_to_text(pdf, txt):
    if not (os.path.exists(txt) and os.path.getmtime(txt) >= os.path.getmtime(pdf)):
        os.makedirs(os.path.dirname(txt), exist_ok=True)
        subprocess.run(["pdftotext", "-layout", pdf, txt], check=True, stderr=subprocess.DEVNULL)
    text = open(txt, encoding="utf-8", errors="replace").read()
    # private-use glyphs (check boxes, arrows) from the PDF fonts carry no wording
    return re.sub(r"[\ue000-\uf8ff]", " ", text)


def squeeze(s):
    return re.sub(r"\s+", " ", s).strip()


def join_block(lines):
    """Full cleaned block text: lines joined with ' / ', internal whitespace squeezed."""
    out = [squeeze(l) for l in lines]
    return " / ".join(x for x in out if x)


STOP = {"ENQ", "INDIEN", "VRAAG", "FORMULIER", "ANDERS", "NIET", "ALLEEN", "EN", "OF", "ZIE",
        "BLOK", "ALS", "DAN", "NAAR", "EINDE", "VAN", "MET", "GEEN", "NEE", "JA", "WEL", "OOK",
        "HET", "DE", "EEN", "VOOR", "BIJ", "OVER", "KAART", "TOON", "NOTEER", "CODE", "ANTWOORD"}


def caps_tokens(text):
    """Variable-name-like tokens (caps, digits, underscore; >= 4 chars) not in STOP."""
    toks = re.findall(r"\b[A-Z][A-Z0-9_]{3,}\b", text)
    seen, out = set(), []
    for t in toks:
        if t in STOP or t in seen or re.fullmatch(r"[0-9_]+", t):
            continue
        seen.add(t)
        out.append(t)
    return out


# ----------------------------------------------------------------- TNS format (SIM 2015, SIM 2020)
RE_Q = re.compile(r"^\s*(Q\d+[A-Za-z]?|T\d+)\s*[:\u2013-]\s*(.*?)\s*$")
RE_Q_NOCOLON = re.compile(r"^\s*(Q\d{3,})\s+([A-Z][A-Z0-9_]{3,})\s*$")        # 'Q14041 CONTACTHERK_6': sub-question header printed without the colon
RE_Q_SAMPLE = re.compile(r"^\s*(9\d{3})\s+([A-Z][A-Z0-9_]{3,})\s*$")           # '9004 GENERATIE': sample-data field header printed without 'Q' and colon (SIM 2020)
RE_WIDGET = re.compile(r"^\s*(NUMBER|OPEN|TEXT|\[\s*MIN\s+\d+\s*[\u2013-]\s*MAX\s+\d+\s*\]|…+\s*\S*|\.{3,}\s*\S*|(?:Max|Min)\s+\d+)\s*$")   # numeric widget / bounds / units lines
RE_MARK = re.compile(r"\s*\*(Position fixed|Open ended|Open|Exclusive|Fixed|Fix|Random|Rotate)\b\.?", re.I)   # TNS scripter markers on option lines
RE_BLOCK = re.compile(r"^\s*(B\d+)\s*:\s*(.*?)\s+(Begin|End) block\s*$")
RE_TYPE = re.compile(r"\s{2,}(Single coded|SINGLE CODED|Multi coded|MULTI CODED|Numeric|NUMERIC|Open|OPEN|Text|TEXT|Grid|GRID|Matrix|MATRIX|Open ended|OPEN ENDED)\s*$")
RE_OPT = re.compile(r"^\s*(\d+)\s{2,}(\S.*?)\s*$")
RE_SUB = re.compile(r"^\s*(\d{3,6})\s*([A-Z][A-Z0-9_]{1,})(?:\s+(\S.*?))?\s*$")
RE_ENDPOINTS = re.compile(r"^\s*(\d+):\s*(.*?)\s+[\u2013-]\s+(\d+):\s*(.*?)\s*$")     # '1: 1 heel erg ontevreden - 10: 10 heel erg tevreden'
RE_FOOT = re.compile(r"(SIM 20\d\d \| version|© TNS|^\s*\d+\s*$|Labyrinth Onderzoek)")


def parse_tns(text, survey, instrument):
    lines = text.split("\n")
    items, cur, block, pending_split, intro, in_intro = [], None, "", "", [], False
    pending_route, last_route = [], False      # TNS prints 'ASK ONLY IF ...' before the header of the question it governs
    for raw in lines:
        line = raw.rstrip("\f")
        if RE_FOOT.search(line):
            continue
        if re.match(r"^\s*ASK\b", line, re.I):
            pending_route.append(squeeze(line)); last_route = True
            continue
        if last_route and pending_route and re.match(r"^\s*(and|or)\b", line, re.I):
            pending_route[-1] = squeeze(pending_route[-1] + " " + line)
            continue
        if line.strip():
            last_route = False
        mb = RE_BLOCK.match(line)
        if mb:
            block = mb.group(2) if mb.group(3) == "Begin" else ""
            continue
        if re.match(r"^\s*\*SPLIT HALF ([AB])", line):
            pending_split = re.match(r"^\s*\*SPLIT HALF ([AB])", line).group(1)
            if cur is not None:          # marker inside a matrix block applies to following sub-items
                cur["lines"].append(line)
            continue
        mq = RE_Q.match(line)
        mq2 = RE_Q_NOCOLON.match(line) if not mq else None
        ms = RE_Q_SAMPLE.match(line) if not mq and not mq2 else None
        if ms:                                                    # administrative field with its own recording categories
            if cur:
                items.append(finish_tns(cur, survey, instrument))
            cur = {"qid": "Q" + ms.group(1), "qnames": ms.group(2), "block": block, "split": pending_split, "lines": [], "intro": intro, "pre_routing": pending_route}
            pending_split, intro, in_intro, pending_route = "", [], False, []
            continue
        if mq2 and cur is not None and not re.match(r"^Q\d+", mq2.group(1)[: len(cur["qid"])]) :
            mq2 = None
        if mq2 and cur is not None and not (mq2.group(1).startswith(cur["qid"]) or mq2.group(1)[:-1] == cur["qid"] or
                                            mq2.group(1)[:-1] == cur["qid"][:-1]):
            mq2 = None                                 # 'Q14041 NAME' is a sub-question header of Q1404 (same prefix); other bare lines are not headers
        if mq or mq2:
            if cur:
                items.append(finish_tns(cur, survey, instrument))
            if mq:
                name = RE_TYPE.sub("", mq.group(2)).strip(); qid = mq.group(1)
            else:
                name, qid = mq2.group(2), mq2.group(1)
            cur = {"qid": qid, "qnames": name, "block": block, "split": pending_split, "lines": [], "intro": intro, "pre_routing": pending_route}
            pending_split, intro, in_intro, pending_route = "", [], False, []
            continue
        if "*PAGE" in line:                     # page break: text after it on the same line introduces the next page/question
            after = line.split("*PAGE", 1)[1].strip()
            if cur is not None:
                cur["lines"].append(line.split("*PAGE", 1)[0])
            if after:
                intro, in_intro = [after], True
            continue
        if in_intro:
            if not line.strip():
                in_intro = False
            elif not re.match(r"^\s*(Scripter notes|ASK|IF\b|\*)", line):
                intro.append(line.strip())
            continue
        if cur is not None:
            if not cur["qnames"] and not cur["lines"] and re.fullmatch(r"\s*[A-Z][A-Z0-9_]{2,}\s*", line):
                cur["qnames"] = line.strip()          # name given on the line after 'Qnnnn :'
                continue
            cur["lines"].append(line)
    if cur:
        items.append(finish_tns(cur, survey, instrument))
    for a, b in zip(items, items[1:]):            # text printed after a completed matrix introduces the next question
        tr = a.pop("trailer", "")
        if tr and not b.get("intro"):
            b["intro"] = squeeze("... " + tr)
    # sub-question blocks (Q1404, Q14041 ... Q14044) share one printed answer scale and the introduction of the first block
    # (only grid continuations: sub-blocks that carry item statements but no question text of their own)
    for it_ in items:
        base = re.match(r"^(Q\d+)\d$", it_["qid"])
        if not base or not it_["subitems"] or it_["question_text"] and not re.match(r"^\d+\.", it_["question_text"]): continue
        sibs = [x for x in items if (x["qid"] == base.group(1) or re.fullmatch(re.escape(base.group(1)) + r"\d", x["qid"])) and x["subitems"]]
        if len(sibs) < 2: continue
        if re.match(r"^\d+\.", it_["question_text"]): it_["question_text"] = ""     # the printed scale was taken as question text
        if not it_["answer_options"]:
            it_["answer_options"] = next((x["answer_options"] for x in sibs if x["answer_options"]), "")   # the friends introduction is not copied
    for it_ in items:
        base = re.match(r"^(Q\d+)$", it_["qid"])
        if base and not it_["answer_options"] and it_["subitems"]:
            sibs = [x for x in items if re.fullmatch(re.escape(base.group(1)) + r"\d", x["qid"]) and x["answer_options"] and x["subitems"]]
            if sibs: it_["answer_options"] = sibs[0]["answer_options"]
    if items:
        items[-1].pop("trailer", None)
    return items


def finish_tns(cur, survey, instrument):
    lines = cur["lines"]
    qtext, opts, subs, notes, routing, qtype, fmt = [], [], [], [], list(cur.get("pre_routing", [])), "", []
    in_notes, in_options, last, inline_scale, trailer, name_line, in_bracket = False, False, "", False, None, False, False
    for l in lines:
        s = l.strip()
        if not s:
            continue
        l = RE_MARK.sub("", l)
        s = l.strip()
        if not s:
            continue
        mt = RE_TYPE.search(l)
        if mt:
            qtype = mt.group(1)
            l = RE_TYPE.sub("", l)
            s = l.strip()
            if not s:
                continue
        if in_bracket:                                # '[IF Q43' continued on the next line: '= 1 AND IF NOT Q9001=7]'
            routing[-1] = squeeze(routing[-1] + " " + s.rstrip("]"))
            in_bracket = "]" not in s
            continue
        if RE_WIDGET.match(s):                        # NUMBER / [MIN 0 - MAX 20] / '……keer': response format, not wording
            fmt.append(s); continue
        mg = re.search(r"\s*\bGOTO\s*(\d+)?\s*$", s)
        if mg and not in_options:                     # 'GOTO' / 'GOTO 903' printed at the end of the question text
            if mg.group(1): routing.append("-> " + mg.group(1))
            s = s[: mg.start()].strip()
            if not s:
                continue
        if "Scripter notes" in s or in_notes or re.match(r"^(Help-button|Helptekst|Instructie\b|inladen\b|Land van HERK|INDIEN\b|ALS Q|antwoordopties\b|Antwoordopties\b)", s):
            in_notes = True                           # scripter notes close a question block in the TNS format
            notes.append(s.replace("Scripter notes:", "").strip())
            continue
        if re.match(r"^(Niet stellen indien|Ask only if|ASK IF|Alleen stellen|Stel alleen|Vraag alleen|IF\b)", s, re.I):
            routing.append(s); last = "route"
            continue
        if last == "route" and routing and re.match(r"^(and|or)\b", s, re.I):
            routing[-1] = squeeze(routing[-1] + " " + s)       # condition continued on the next line
            continue
        if re.search(r"\s(ASK (?:ONLY )?IF|IF)\s", s) and "PUT IN" not in s:     # routing at the end of a question-text line: split
            head, kw, tail = re.split(r"\s(ASK (?:ONLY )?IF|IF)\s", s, maxsplit=1)
            routing.append(kw + " " + tail.strip())
            s = head.strip()
            if not s:
                continue
        mb = re.search(r"\[(ASK|IF)\b[^\]]*\]?", s)
        if mb and not in_options:                     # '[IF NOT Q9001 = 7]' printed inside the question text
            routing.append(mb.group(0).strip("[]"))
            in_bracket = "]" not in mb.group(0)       # condition wrapped to the next line
            s = (s[: mb.start()] + " " + s[mb.end():]).strip()
            if not s:
                continue
        mx = re.match(r"^\|\s*((Max|Min)\s+\d+)\s*(.*)$", s)
        if mx:                                        # '| Max 10 Hoeveel kinderen heeft u?': numeric bound printed before the text
            fmt.append(mx.group(1)); s = mx.group(3).strip()
            if not s:
                continue
        mr = re.search(r"\bMIN\s+\d+\s*[\u2013-]\s*MAX\s+\d+", s)
        if mr:
            notes.append(mr.group(0)); s = (s[: mr.start()] + " " + s[mr.end():]).strip()
            if not s:
                continue
        if s.startswith("*SPLIT HALF"):
            subs.append(("", "", s))
            continue
        sc = re.findall(r"(?:^|[,.]\s+)(\d{1,2})\.\s*([^,.]+?)(?=[,.]\s+\d{1,2}\.|\.?\s*$)", s)
        if len(sc) >= 3 and not opts:                 # answer scale printed on one line: '1. Niemand, 2. Sommige, 3. De helft, ...'
            opts = [(c, squeeze(t)) for c, t in sc]; in_options, last = True, "opt"
            continue
        ms = RE_SUB.match(l)
        if ms and len(ms.group(1)) >= 3:
            subs.append((ms.group(1), ms.group(2), squeeze(ms.group(3) or "")))
            in_options, last, name_line = True, "sub", False
            continue
        ms = re.match(r"^\s*(\d{4,6})\s+([A-Z][a-z].*?)\s*$", l)
        if ms and subs:                            # numbered battery item printed without its variable name
            subs.append((ms.group(1), "", squeeze(ms.group(2))))
            in_options, last = True, "sub"
            continue
        mo = RE_OPT.match(l) or re.match(r"^\s{2,}(\d{1,3})\.\s+(\S.*?)\s*$", l)
        if mo:
            lab = squeeze(mo.group(2))
            mg = re.search(r"\s+GOTO\s+(\d+)\s*$", lab)
            if mg:                                    # '2  nee   GOTO 903': skip instruction on an option line
                routing.append(f"{mo.group(1)} -> {mg.group(1)}"); lab = lab[: mg.start()].strip()
            opts.append((mo.group(1), lab))
            in_options, last = True, "opt"
            continue
        if trailer is not None:                       # text after a completed matrix: introduction of the next question
            trailer.append(s)
            continue
        if last == "sub" and name_line and (re.match(r"^[a-z]", s) or s.startswith("*") or s.startswith("U kunt kiezen")):
            trailer = [s]                             # matrix closed by its name line; what follows belongs to the next page
            continue
        if last == "sub" and subs and not inline_scale and s.count(",") >= 2 and "?" not in s and re.match(r"^[A-Z]", s) and not RE_SUB.match(l):
            opts.append(("", "scale: " + s)); last = "scale"
            continue
        mk = re.match(r"^\s*(9[2-9])\s+((weet|geen|wil|niet|n\.v\.t)\b.*)$", s, re.I)
        if mk:                                        # 'don't know' code printed with a single space
            opts.append((mk.group(1), squeeze(mk.group(2)))); in_options, last = True, "opt"
            continue
        if last == "scale" and opts and len(s) < 80 and not RE_SUB.match(l):
            c, t = opts[-1]
            if re.match(r"^[a-z]", s) and not t.endswith(","):
                opts[-1] = (c, squeeze(t + " " + s))         # label split over two lines
            elif "," in s or s.split()[0] in t:
                opts[-1] = (c, squeeze(t.rstrip(",") + ", " + s))
            continue                                  # otherwise a section header: dropped
        me = RE_ENDPOINTS.match(l)
        if me and not subs:                       # numeric scale given by its endpoints
            opts += [(me.group(1), squeeze(me.group(2))), (me.group(3), squeeze(me.group(4)))]
            in_options, last = True, "opt"
            continue
        mk = re.match(r"^\s*(9[2-9]):\s*(\S.*)$", l)
        if mk and not subs:                       # 'don't know' / refusal code of a numeric question
            opts.append((mk.group(1), squeeze(mk.group(2))))
            in_options, last = True, "opt"
            continue
        mx = re.match(r"^((?:(?:Max|Min)\s+\d+)(?:\s*\|\s*(?:Max|Min)\s+\d+)*)\s*\|?\s*(.*)$", s)
        if mx:                                    # 'Min 1 | Max 10' numeric range constraint printed before the question text
            fmt.append(squeeze(mx.group(1)))
            s = mx.group(2).strip()
            if not s:
                continue
        # matrix row "1:Hoe vaak voelde u ..."  with inline scale "1:Voortdurend 2:Meestal ..."
        mm = re.match(r"^\s*(\d+):(.*)$", l)
        if mm:
            body = mm.group(2)
            scale = re.findall(r"(\d+)[:.]\s*([A-Za-z][^\d]*?)(?=\s+\d+[:.]|\s*\*PAGE|$)", body)
            rowtext = re.split(r"\s{2,}\d+[:.]", body)[0]
            subs.append((mm.group(1), "", squeeze(rowtext)))
            if scale and not opts:
                opts = [(c, squeeze(t)) for c, t in scale]
            in_options, last, inline_scale, name_line = True, "sub", bool(scale), False
            continue
        if in_options and last == "sub" and subs:
            q, n, t = subs[-1]          # continuation of a sub-item text, or its variable name on a line of its own
            if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", s) and not n:
                subs[-1] = (q, s, t); name_line = True
            else:
                cont = re.split(r"\s{2,}", l.strip())[0] if inline_scale else s     # column-aligned matrix: first column only
                if re.search(r"[?.]$", t) and re.match(r"^[A-Z]", cont) and not inline_scale:
                    subs.append(("", "", squeeze(cont)))                     # next item printed without its number/name
                elif not re.fullmatch(r"\*?PAGE|Wilt u", cont):
                    subs[-1] = (q, n, squeeze(t + " " + cont))
            continue
        if in_options and last == "opt" and opts:
            c, t = opts[-1]             # continuation of an option label
            opts[-1] = (c, squeeze(t + " " + s))
            continue
        qtext.append(s)
    rand = "; ".join(n for n in notes if re.search(r"random", n, re.I))
    other_notes = [n for n in notes if not re.search(r"random", n, re.I)]
    question = squeeze(" ".join(qtext))
    # routing fragments embedded in the question text
    mroute = re.search(r"\b(IF Q\d+.*|Niet stellen indien.*|Ask only if.*)$", question)
    if mroute:
        routing.append(mroute.group(1))
        question = question[: mroute.start()].strip()
    intro = squeeze(" ".join(cur["intro"])) if cur.get("intro") else ""
    mi = re.match(r"^\[Inleiding:\s*(.*?)\]\s*(.*)$", question, re.S)
    if mi:                                                   # introduction text kept apart from the spoken question
        intro = squeeze((intro + " " + mi.group(1)).strip()); question = squeeze(mi.group(2))
    for m_ in re.finditer(r"\bMIN\s+\d+\s*[\u2013-]\s*MAX\s+\d+", " ".join(other_notes)):
        fmt.append(m_.group(0))
    other_notes = [n for n in other_notes if not re.search(r"\bMIN\s+\d+\s*[\u2013-]\s*MAX\s+\d+", n)]
    # split marker printed between the sub-items of a grid (a trailing marker belongs to the next element, not to this grid)
    inner = any(t.startswith("*SPLIT") and any(t2 and not t2.startswith("*SPLIT") for _, _, t2 in subs[i + 1:]) for i, (_, _, t) in enumerate(subs))
    sub_splits, cur_split = [], ""
    for q, n, t in subs:
        if t.startswith("*SPLIT"):
            cur_split = re.search(r"\*SPLIT HALF ([AB])", t).group(1) if re.search(r"\*SPLIT HALF ([AB])", t) else cur_split
        elif t:
            sub_splits.append(cur_split if inner else cur["split"])
    return {
        "survey": survey, "instrument": instrument, "qid": cur["qid"], "qnames": cur["qnames"],
        "block": cur["block"], "split_half": "" if inner else cur["split"], "subitem_splits": "|".join(sub_splits) if inner else "",
        "routing": squeeze("; ".join(routing + other_notes))[:600],
        "randomization": squeeze(rand)[:400],
        "question_text": question, "answer_options": "; ".join(f"{c}={t}" if c else t for c, t in opts),
        "subitems": "; ".join(f"{q} {n} {t}".strip() for q, n, t in subs if t and not t.startswith("*SPLIT")),
        "intro": intro, "format": squeeze("; ".join(dict.fromkeys(fmt))),
        "block_text": join_block(lines), "trailer": squeeze(" ".join(trailer or [])),
    }


# ----------------------------------------------------------------- SPVN 2003 (Veldkamp codebook-questionnaire)
RE_VRAAG = re.compile(r"^\s*VRAAG\s+(\d+[A-Za-z]?)\b(.*)$")
RE_QID = re.compile(r"^\s*([A-Z]\d{1,2}[a-z]?[´']?)\.?\s+(\S.*)$")
RE_OPT_SPVN = re.compile(r"^\s{4,}(\d{1,3})\s{2,}(\S.*?)\s*$")
RE_FOOT_SPVN = re.compile(r"(Veldkamp Amsterdam|^\s*V3108)")


RE_VARLIST = re.compile(r"^\s*(\(?\+?[GP]\)?\s+[A-Z][A-Z0-9]+\s*){2,}$")   # lines listing constructed variables only
RE_VARLIST3 = re.compile(r"^\s*((\(?\+?[GP]\)?\s+)?[A-Z][A-Z0-9]{2,}(\s+|$)){3,}$")   # final summary list (4 columns, markers optional)


def parse_spvn(text, survey, instrument):
    items, cur = [], None
    for raw in text.split("\n"):
        line = raw.rstrip("\f")
        if RE_FOOT_SPVN.search(line):
            continue
        toks3 = re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", re.sub(r"(?<!\S)\(?\+?[GP]\)?(?=\s)", " ", line))
        same_stem = len({re.sub(r"\d+$", "", t) for t in toks3}) == 1      # 'ANDLAND1 ANDLAND2 ANDLAND3 ANDLAND4': one question, several answers
        if RE_VARLIST.match(line) or (RE_VARLIST3.match(line) and not same_stem):
            summary = bool(RE_VARLIST3.match(line))
            for nm in re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", re.sub(r"(?<!\S)\(?\+?[GP]\)?(?=\s)", " ", line)):
                CONSTRUCTED.setdefault(survey, {}).setdefault(nm, "listed as constructed/derived variable in the codebook")
                if cur and not summary:
                    DERIVED_AT.setdefault(survey, {}).setdefault(nm, cur["qid"])
            if cur:
                items.append(finish_spvn(cur, survey, instrument))
            cur = None            # trailing variable lists belong to no question: these are constructed variables
            continue
        mv = RE_VRAAG.match(line)
        if mv:
            if cur:
                items.append(finish_spvn(cur, survey, instrument))
            cur = {"qid": "VRAAG " + mv.group(1), "lines": [], "tail": mv.group(2).strip()}
            continue
        if cur is not None:
            cur["lines"].append(line)
    if cur:
        items.append(finish_spvn(cur, survey, instrument))
    return items


def finish_spvn(cur, survey, instrument):
    lines = cur["lines"]
    qtext, opts, names, routing = [], [], [], []
    qsub = ""
    if cur["tail"]:
        routing.append(cur["tail"])
    for l in lines:
        s = l.strip()
        if not s:
            continue
        names += caps_tokens(l)
        body = re.sub(r"(\s+(\(\+G\)|\+G|\(P\)|\(G\)|G|P|\*)?\s*\b[A-Z][A-Z0-9]{1,}\b)+\s*$", "", l).rstrip()   # trailing variable names / markers
        body = re.sub(r"(\(\+G\)|\+G|\(P\)|\(G\))", "", body).rstrip()
        mo = RE_OPT_SPVN.match(body)
        if mo:
            lab = mo.group(2)
            mg = re.search(r"\s*(GA (?:DOOR MET|NAAR) VRAAG\s+\d+[a-z]?)\s*$", lab, re.I)
            if mg:
                routing.append(f"{mo.group(1)} -> {mg.group(1)}")
                lab = lab[: mg.start()].strip()
            opts.append((mo.group(1), lab))
            continue
        mq = RE_QID.match(body)
        if mq and not qsub:
            qsub = mq.group(1)
            qtext.append(mq.group(2))
            continue
        if re.match(r"^(Enq\.|ENQ\.|Indien|INDIEN|Als |ALS |TOON |GA DOOR|GA NAAR)", body.strip()):
            routing.append(squeeze(body))
            continue
        if opts:
            c, t = opts[-1]
            opts[-1] = (c, squeeze(t + " " + body))
        else:
            qtext.append(squeeze(body))
    qid = cur["qid"] + (f" ({qsub})" if qsub else "")
    return {
        "survey": survey, "instrument": instrument, "qid": qid, "qnames": ";".join(names),
        "block": "", "split_half": "", "routing": squeeze("; ".join(routing))[:600], "randomization": "",
        "question_text": squeeze(" ".join(qtext)), "answer_options": "; ".join(f"{c}={t}" for c, t in opts),
        "subitems": "", "block_text": join_block(lines),
    }


# ----------------------------------------------------------------- SPVA 2002 (two-column codebook-questionnaire)
# Layout: question id + text in the left column, answer options ("• label   code") in the right column; grid
# questions list their items as bullet rows ending in the variable name and the scale columns "1 2 3 4 5";
# variable names (CAPS) are printed next to the question; "+G" marks items also asked to household members.
RE_QID2 = re.compile(r"^\s*([A-Z]\d{1,2}[a-z]?[´'’]?)\.\s*(.*?)\s*$")
RE_SECTION = re.compile(r"^\s*([A-Z])\.\s+([A-Z][A-Z ,/&-]{3,})\s*$")
RE_FOOT_SPVA = re.compile(r"(P2945_onderzoek|^\s*\d+\s*$|P1684)")
RE_GRIDROW_END = re.compile(r"\b([A-Z][A-Z0-9]{3,})\b\s+((\d+\s+){1,}\d+)\s*$")
RE_SCALE_WORDS = re.compile(r"^(helemaal|mee|eens|niet|oneens|eens/niet|ja|nee|vaak|soms|nooit|regelmatig|altijd|weet|zelden|goed|matig|slecht|zeer|beetje|een|wel|geen|enigszins|tamelijk|erg|veel|weinig|belangrijk|onbelangrijk|van|toepassing|n\.v\.t\.|meestal|mening|\(|\)|-|/|\d+)+$")
MARKERS = re.compile(r"\(\+G\)|\+G|\(G\)|\bG\b(?=\s|$)")
KNOWN_NAMES = {}      # survey -> set of variable names in the data files (filled by build.py); used to strip names from text
_CUR_SURVEY = [""]


def spva_clean_left(t):
    t = MARKERS.sub("", t)
    known = KNOWN_NAMES.get(_CUR_SURVEY[0])
    if known:
        t = re.sub(r"(?<![/\w])[A-Z][A-Z0-9]{3,}(?![/\w])", lambda m: "" if m.group(0) in known else m.group(0), t)
        t = re.sub(r"\(\s*\)", "", t)
        t = re.sub(r"(^|\s)[-*](\s|$)", " ", t)
    else:
        t = re.sub(r"\b[A-Z][A-Z0-9]{3,}\b( - [A-Z][A-Z0-9]{3,}\b)*", "", t)     # variable names printed next to the text
    t = re.sub(r"_{3,}", "", t)
    t = re.sub(r"(\s*[–-]\s*){2,}", " ", t)
    return squeeze(t)


def spva_clean_right(t):
    """option / grid-item text: markers, fill lines and variable names printed next to an option."""
    t = MARKERS.sub("", t)
    known = KNOWN_NAMES.get(_CUR_SURVEY[0])
    if known:
        t = re.sub(r"(?<![/\w])[A-Z][A-Z0-9]{3,}(?![/\w]|\s*=)", lambda m: "" if m.group(0) in known else m.group(0), t)
        t = re.sub(r"(^|\s)[-–](\s|$)", " ", t)
    t = re.sub(r"_{3,}", "", t)
    return squeeze(t)


def is_scale_header(t):
    toks = re.findall(r"[^\s]+", t.lower())
    return bool(toks) and all(RE_SCALE_WORDS.match(w) for w in toks)


RE_HOLD = re.compile(r"^\s*(INDIEN[^•:]*:)\s*(\(?[A-Z][A-Z0-9]{3,}\)?\s*)*(•.*)?$")      # 'INDIEN GEEN WERK:' printed above the question it conditions


def parse_spva(text, survey, instrument):
    _CUR_SURVEY[0] = survey
    items, cur, section, started = [], None, "", False
    constr = CONSTRUCTED.setdefault(survey, {})
    pending = []                                       # variable names printed above the question they belong to
    hold = []                                          # routing lines that belong to the next question
    for raw in text.split("\n"):
        line = raw.rstrip("\f").replace("●", "•")
        if "HARTELIJK DANK" in line:
            break                                      # end of the questionnaire; documentation chapters follow
        if not started:
            mc = re.match(r"^([A-Z][A-Z0-9]{1,}):\s+(.+)$", line.strip())
            if mc:
                constr[mc.group(1)] = squeeze(mc.group(2))
            if not RE_QID2.match(line):
                continue
        if RE_FOOT_SPVA.search(line):
            continue
        ms = RE_SECTION.match(line)
        if ms:
            section = ms.group(2).title()
            if cur:
                items.append(finish_spva(cur, survey, instrument))
            cur = None                                 # section intro lines belong to no question
            continue
        mq = RE_QID2.match(line) or RE_QINSTR.match(line)
        if mq:
            started = True
            if cur:
                items.append(finish_spva(cur, survey, instrument, pending_out=pending))
            if mq.re is RE_QINSTR:
                line = line.replace(mq.group(1), mq.group(1) + ".", 1)
            for nm in [n for n in pending if n in constr]:
                DERIVED_AT.setdefault(survey, {}).setdefault(nm, mq.group(1))
            cur = {"qid": mq.group(1), "block": section, "lines": [line] + hold, "pending_in": [n for n in pending if n not in constr]}
            pending, hold = [], []
            continue
        if started and cur is not None:
            if RE_HOLD.match(line) and not RE_PENDING.match(line):
                hold.append(line); continue
            if hold and line.strip():
                hold.append(line); continue           # options printed above the question line travel with it
            if hold:                                   # blank line: not followed by a new question after all
                cur["lines"] += hold; hold = []
            cur["lines"].append(line)
    if cur:
        items.append(finish_spva(cur, survey, instrument, pending_out=pending))
    return items


RE_PENDING = re.compile(r"^\s*(INDIEN[^:]*:|[A-Z][A-Z /]+:)\s+([A-Z][A-Z0-9]{3,})\s*$")
RE_CODE_END = re.compile(r"^(.*?)\s*(?<![\w/])(\d{1,3})\s*(⇐.*)?$")      # option text, code, optional skip arrow
RE_QINSTR = re.compile(r"^\s*([A-Z]\d{1,2}[a-z]?[´'’])\s+(ENQ\.|Enq\.|INDIEN|Indien)(.*)$")   # 'C3d´  ENQ.: als vraag ...' instruction blocks


def _col_of(x, positions):
    """index of the bullet column a text position belongs to (-1 = question column left of the first bullet)."""
    col = -1
    for j, bx in enumerate(positions):
        if x >= bx - 2:
            col = j
    return col


def finish_spva(cur, survey, instrument, pending_out=None):
    lines = cur["lines"]
    qtext, subs, names, routing = [], [], [], []
    names += cur.get("pending_in", [])
    multi = []           # (name, option label) pairs of multiple-response blocks
    multi_names = []     # variable names printed in the question column next to the options, in order
    arrow_at = None      # (column, code index) of a skip arrow printed on a line of its own
    await_name = None    # grid row whose variable name is printed on the following line
    scale = set()
    prev_enq = False
    RE_COLS = re.compile(r"^(.*?)\s+((\d+\s+){2,}\d+)\s*$")
    # bullet columns of this block (x positions of '•', clustered)
    bpos = []
    for l in lines:
        for m in re.finditer("•", l):
            x = m.start()
            if not any(abs(x - b) <= 4 for b in bpos):
                bpos.append(x)
    bpos.sort()
    bullets = [[] for _ in bpos]      # per column: list of [text, inline_code, inline_arrow]
    codes = [[] for _ in bpos]        # per column: list of (code, arrow) in order of appearance
    last_bullet_col = None

    def add_code(j, code, arrow):
        if j < 0 or j >= len(codes):
            return
        codes[j].append((code, arrow or ""))
        if bullets[j] and bullets[j][-1][1] == "":
            bullets[j][-1][1], bullets[j][-1][2] = code, arrow or ""

    def take_code(txt):
        m = RE_CODE_END.match(txt)
        if m and not RE_COLS.match(txt):
            return m.group(1).strip(), m.group(2), (m.group(3) or "").strip()
        return txt.strip(), "", ""

    for i, l in enumerate(lines):
        if not l.strip():
            continue
        mp = RE_PENDING.match(l)
        if mp and pending_out is not None and i > 0:
            pending_out.append(mp.group(2))            # 'INDIEN NU OPLEIDING:  VOLTOPL' names the NEXT question's variable
            routing.append(squeeze(mp.group(1)))
            continue
        l = re.sub(r"^(\s*)([A-Z]\d{1,2}[a-z]?[´'’]?)\.", lambda m: m.group(1) + " " * (len(m.group(2)) + 1), l, count=1)   # blank the question id, keep columns
        raw = l.strip()
        # ---- a grid row waiting for its variable name on the next line
        if await_name is not None:
            mn = re.search(r"\b([A-Z][A-Z0-9]{3,})\b", raw)
            if mn:
                extra = spva_clean_left(re.sub(r"(\s+\d+){2,}\s*$", "", raw.replace(mn.group(1), "")))
                subs.append((mn.group(1), squeeze(await_name + " " + extra)))
                await_name = None
                continue
            await_name = squeeze(await_name + " " + spva_clean_left(raw))
            continue
        # ---- split the line into the question column and the bullet columns
        segs = []                                  # (col, text, has_bullet)
        if "•" in l:
            parts = l.split("•")
            segs.append((-1, parts[0], False))
            x = len(parts[0]) + 1
            for part in parts[1:]:
                segs.append((_col_of(x - 1, bpos), part, True))
                x += len(part) + 1
        elif bpos:
            cut = bpos[0]
            left, right = l[:cut], l[cut:]
            xs = cut + (len(right) - len(right.lstrip()))
            if right.strip() and xs >= cut + 3 and (not left.strip() or not left[-1:].strip()):
                segs.append((-1, left, False))
                # text in a bullet column without a bullet: continuation of the last item of that column (or a lone code)
                segs.append((_col_of(xs, bpos), right, False))
            else:
                segs.append((-1, l, False))
        else:
            segs.append((-1, l, False))
        left = next((t for c, t, b in segs if c == -1), "")
        left_names = caps_tokens(left) if not re.match(r"^\s*(INDIEN|Indien)", left) else caps_tokens(left.split(":", 1)[1] if ":" in left else "")
        constr = CONSTRUCTED.get(survey, {})
        known = KNOWN_NAMES.get(survey) or set()
        bare = re.sub(r"\(\+G\)|\+G|\(G\)|\bG\b", " ", left)
        toks2 = re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", bare)
        paired = all((t[:-1] in toks2) if t.endswith("1") else (t + "1" in toks2) for t in toks2)   # 'NAME – NAME1': main / mini questionnaire pair
        list_line = (len(toks2) >= 2 and not re.sub(r"[A-Z][A-Z0-9]{1,}|[\s–\-*]", "", bare).strip()
                     and all(t in constr or t in known for t in toks2) and any(t in constr for t in toks2) and not paired)
        if list_line:
            for nm in [n for n in toks2 if n in known]:             # list of coded/derived variables printed after the block
                DERIVED_AT.setdefault(survey, {}).setdefault(nm, cur["qid"])
            left_names = []
        names += left_names
        if len(left_names) == 1 or (left_names and not re.search(r"[A-Z0-9]\s*[–-]\s*[A-Z]", left)):
            multi_names += [n for n in left_names if n not in multi_names]
        known = KNOWN_NAMES.get(survey) or set()
        names += [n for c, t, b in segs if c >= 0 for n in caps_tokens(t) if n in known]
        for col, txt, has_bullet in segs:
            if col == -1:
                continue
            body = squeeze(txt)
            if not body:
                continue
            if re.match(r"^(⇐|vr\.|EIND\b)", body) and not has_bullet:      # skip arrow split over two lines
                if body.startswith("⇐") and codes[col]:
                    arrow_at = (col, len(codes[col]) - 1)
                if arrow_at and arrow_at[0] == col:
                    c, a = codes[col][arrow_at[1]]
                    codes[col][arrow_at[1]] = (c, squeeze(a + " " + body))
                    for b in bullets[col]:
                        if b[1] == c:
                            b[2] = codes[col][arrow_at[1]][1]
                    if not body.startswith("⇐"):
                        arrow_at = None
                continue
            # ---- grid rows: "text  NAME  1 2 3 4 5" or "text  1 2 3 4 5" (name on the next line)
            mg = RE_GRIDROW_END.search(body)
            mc = RE_COLS.match(body)
            if re.fullmatch(r"[A-Z][A-Z0-9]{3,}", body) and body in (KNOWN_NAMES.get(survey) or set()) and not has_bullet \
                    and bullets[col] and bullets[col][-1][1] == "" and not bullets[col][-1][3]:
                b = bullets[col].pop()                                     # grid item whose name is printed alone on the next line
                subs.append((body, b[0]))
                continue
            if re.fullmatch(r"(\d+\s+)+\d+", body):
                if bullets[col] and bullets[col][-1][1] == "" and not bullets[col][-1][3]:
                    b = bullets[col].pop()                                 # grid item whose scale columns are on the next line
                    mn = re.search(r"\b([A-Z][A-Z0-9]{3,})\b\s*$", b[4])
                    if mn:
                        subs.append((mn.group(1), b[0]))
                    else:
                        await_name = b[0]
                    scale |= set(body.split())
                continue                                                   # otherwise a scale header '1 2 3 4 5'
            if mg:
                t = spva_clean_right(body[: mg.start()])
                if not has_bullet and bullets[col] and bullets[col][-1][1] == "" and not bullets[col][-1][3]:
                    t = squeeze(bullets[col].pop()[0] + " " + t)       # multi-line grid item started on a bullet line
                subs.append((mg.group(1), t))
                scale |= set(mg.group(2).split()); last_bullet_col = None
                continue
            if mc and not re.search(r"\b[A-Z][A-Z0-9]{3,}\b", mc.group(1)):
                t = spva_clean_right(mc.group(1))
                if not has_bullet and bullets[col] and bullets[col][-1][1] == "" and not bullets[col][-1][3]:
                    t = squeeze(bullets[col].pop()[0] + " " + t)
                await_name = t
                scale |= set(mc.group(2).split()); last_bullet_col = None
                continue
            text, code, arrow = take_code(body)
            text = spva_clean_right(text)
            if has_bullet:
                bullets[col].append([text, "", "", False, body])
                last_bullet_col = col
                if code:
                    add_code(col, code, arrow)
                mname = re.fullmatch(r"\s*(\+G|G|\(\+G\))?\s*([A-Z][A-Z0-9]{3,})\s*", left) if i > 0 else None
                if mname:                                 # multi-response item: name printed next to its option (kept only if several)
                    multi.append((mname.group(2), text))
            else:
                if re.match(r"^(ENQ\.|Enq\.)", body) or (text and not code and is_scale_header(text)):
                    continue
                if text and bullets[col] and bullets[col][-1][1] == "":
                    bullets[col][-1][0] = squeeze(bullets[col][-1][0] + " " + text)
                    bullets[col][-1][4] = squeeze(bullets[col][-1][4] + " " + body)
                elif text and bullets[col] and (code or not subs):
                    bullets[col][-1][0] = squeeze(bullets[col][-1][0] + " " + text)
                    bullets[col][-1][4] = squeeze(bullets[col][-1][4] + " " + body)
                    bullets[col][-1][3] = True            # text after a coded line: keeps the code, marks as closed
                elif text:
                    bullets[col].append([text, "", "", False, body])      # item printed without a bullet (grid rows)
                if code:
                    add_code(col, code, arrow)
        # ---- left column: question text / interviewer instructions (scale-header words printed far right are dropped)
        if list_line:
            continue
        ls = spva_clean_left(" ".join(c for c in re.split(r"\s{3,}", left.strip()) if c and not is_scale_header(c)))
        if not ls or is_scale_header(ls):
            continue
        if re.match(r"^(ENQ\.|Enq\.|INDIEN|Indien)", ls):
            routing.append(ls); prev_enq = ls.startswith(("ENQ", "Enq"))
        elif prev_enq and ls[:1].islower() and routing:
            routing[-1] = squeeze(routing[-1] + " " + ls)        # continuation of an interviewer instruction
        else:
            qtext.append(ls); prev_enq = False
    if await_name is not None:
        subs.append(("", await_name))
    all_bullets = [b for col in bullets for b in col]
    inline_codes = {b[1] for b in all_bullets if b[1]}
    if (not subs and len(multi_names) >= 2 and len(all_bullets) >= 2 and inline_codes <= {"1"}
            and abs(len(multi_names) - len(all_bullets)) <= 1):
        # multiple-response question: one variable per option, names printed in the question column in option order
        subs = list(zip(multi_names, [b[0] for b in all_bullets]))
        for col in range(len(bullets)):
            bullets[col], codes[col] = [], []
        scale = inline_codes or {"1"}
    elif len({n for n, _ in multi}) >= 2:
        subs += multi
    # ---- options: per column, codes printed in the same order as the bullets (codes of multi-line options are often
    #      shifted one line down in the PDF, so counts are matched first; inline association is the fallback)
    opts = []
    if os.environ.get("QDEBUG") == cur["qid"]:
        print("BPOS", bpos); print("BULLETS", bullets); print("CODES", codes)
    for j in range(len(bpos)):
        bl, cl = bullets[j], codes[j]
        if bl and len(bl) == len(cl):
            for (t, _, _, _, _), (c, a) in zip(bl, cl):
                opts.append((c, t, a))
        else:
            for t, c, a, _, _ in bl:
                if c:
                    opts.append((c, t, a))
    opts = [(c, t, a) for c, t, a in opts if t]
    try:
        opts.sort(key=lambda o: int(o[0]))
    except ValueError:
        pass
    for c, t, a in opts:
        if a:
            routing.append(f"{c} {a}")
    if not qtext:
        enq = [r for r in routing if re.match(r"^(ENQ\.|Enq\.)", r)]
        if enq:
            qtext = [enq[0]]                                     # interviewer-recorded items (e.g. 'ENQ.: stel vast ...')
    if subs and not opts and scale:
        sc = sorted(scale, key=int)
        opts = [(f"{sc[0]}-{sc[-1]}", "grid scale (labels in the data file)", "")] if len(sc) > 1 else [(sc[0], "genoemd (multiple response; labels in the data file)", "")]
    names = list(dict.fromkeys(names + [n for n, _ in subs if n]))
    routing = [r for r in routing if not re.fullmatch(r"(ENQ\.|Enq\.):?", r)]
    return {
        "survey": survey, "instrument": instrument, "qid": cur["qid"], "qnames": ";".join(names),
        "block": cur["block"], "split_half": "", "routing": squeeze("; ".join(dict.fromkeys(routing)))[:600], "randomization": "",
        "question_text": squeeze(" ".join(qtext)), "answer_options": "; ".join(f"{c}={t}" for c, t, _ in opts),
        "subitems": "; ".join(f"{n} {t}".strip() for n, t in subs), "block_text": join_block(lines),
    }




# ----------------------------------------------------------------- Veldkamp hardcopy questionnaires (LAS 2004/05, SIM 2011)
# 'VRAAG n   NAME [+ P]' headers with the variable name(s) at the right margin, question text, options
# '   1   [q]   label' (q = check-box glyph in the SIM 2011 hardcopy), 'INDIEN ...:' routing lines printed above the
# question they condition, 'ENQ.:' interviewer instructions.  '+ P' marks questions also asked about the partner.
RE_VRAAG_HC = re.compile(r"^\s*V?RAAG\s+(\d+(?:[A-Za-z]|_\d+)?)\b\s*(.*?)\s*$")   # 'RAAG 273' is a typo in the LAS hardcopy; 'VRAAG 42A'
RE_OPT_NOCODE_HC = re.compile(r"^\s{6,}q\s+(\S.*?)\s*$")                       # check box without a code (ranking items, SIM 2011)
RE_OPT_HC = re.compile(r"^\s{3,}(\d{1,3})\s+(?:q\s+)?(\S.*?)\s*$")
# a second header line carrying only variable names at the right margin ('HUWLFTD', 'MIGROUD + P')
RE_NAMES_HC = re.compile(r"^\s{30,}([A-Za-z][A-Za-z0-9_]{2,}(?:\s*(?:\+\s*P\b|\+\s*[A-Za-z0-9_]+|tot en met\s+[A-Za-z0-9_]+))*)\s*$")
# multi-coded questions in the SIM 2011 hardcopy print one variable name at the end of each option line ('... anderen   GELDAND')
RE_OPTNAME_HC = re.compile(r"^(.*\S)\s{2,}([A-Z][A-Z0-9_]{3,})$")
RE_COND_HC = re.compile(r"^\s*(INDIEN\b.*|ALS\b.*:|NB:.*)\s*$")
RE_FOOT_HC = re.compile(r"(Veldkamp Amsterdam|^\s*\d+\s*$|^\s*V\d{4}\s*\||VRAGENLIJST SIM\d+\s*\|\s*SCP\s*\|\s*\d+)")
RE_OPT_DOT_HC = re.compile(r"^\s*(\d{1,2})\.\s+(\S.*?)\s*$")                    # '1. Ja, getrouwd' (SIM 2011 VRAAG 67)
RE_FORMAT_HC = re.compile(r"^\s*((?:Jaar|Maand|Jaren|Maanden|Aantal \w+|Weet niet|Weet niet onbekend\)?|euro|Vul in.*|In jaren of in maanden)[.…\s]*)+:?\s*$|^\s*(\.{3,}.*|…+.*)$", re.I)
RE_SCRIPT_HC = re.compile(r"^\s*(IF\s*\[|PUT IN\b|COMPUTE\b|DUMMY\b)")                 # script lines left in the hardcopy
RE_RANGE_HC = re.compile(r"([A-Za-z][A-Za-z0-9_]*?)(\d+)\s+tot en met\s+([A-Za-z][A-Za-z0-9_]*?)(\d+)\b", re.I)


def _hc_names(tail):
    """Variable names on a VRAAG header: 'CONTVRIE', 'URENID + P', 'v226_1 tot en met V226_10', 'DATDAG + DATMND'."""
    tail = re.sub(r"\+\s*P\b|\(P\)", " ", tail)
    names = []
    for m in RE_RANGE_HC.finditer(tail):
        a, b, w = int(m.group(2)), int(m.group(4)), len(m.group(4))
        pad = m.group(4).startswith("0") or m.group(2).startswith("0")
        step = 1 if b - a < 100 else (100 if (b - a) % 100 == 0 and (b - a) // 100 < 100 else None)   # 'K0101 tot en met K7201'
        if step:
            names += [f"{m.group(3).upper()}{i:0{w}d}" if pad else f"{m.group(3).upper()}{i}" for i in range(a, b + 1, step)]
    tail = RE_RANGE_HC.sub(" ", tail)
    names += [t.upper() for t in re.findall(r"\b[A-Za-z][A-Za-z0-9_]{2,}\b", tail) if t.upper() not in STOP and not re.fullmatch(r"\d+", t)]
    return names


def parse_vk_hc(text, survey, instrument):
    items, cur, pending = [], None, []
    lines = [l.rstrip("\f") for l in text.split("\n") if not RE_FOOT_HC.search(l)]
    skip = set()
    def next_nonblank(j):
        j += 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        return j
    for i, line in enumerate(lines):
        if i in skip:
            continue
        # a condition printed right before the next 'VRAAG n' header governs that question; a wrapped condition
        # ('INDIEN ... EN INDIEN Q101 groter' / 'of gelijk aan 1:') is joined with its continuation line
        if RE_COND_HC.match(line) and not re.search(r"\b(GA )?(NAAR|DOOR|VERDER)\b", line):
            j = next_nonblank(i)
            if j < len(lines) and RE_VRAAG_HC.match(lines[j]):
                pending.append(squeeze(line)); continue
            if j < len(lines) and lines[j].rstrip().endswith(":") and not RE_VRAAG_HC.match(lines[j]) and not RE_COND_HC.match(lines[j]):
                j2 = next_nonblank(j)
                if j2 < len(lines) and RE_VRAAG_HC.match(lines[j2]):
                    pending.append(squeeze(line + " " + lines[j].strip())); skip.add(j); continue
        mv = RE_VRAAG_HC.match(line)
        if mv:
            if re.match(r"^[\u2013-]\s*\d+", mv.group(2)):           # 'VRAAG 21 – 23 herhalen voor ...': a note, not a question
                if cur: cur["lines"].append(line)
                continue
            if cur:
                items.append(finish_vk_hc(cur, survey, instrument))
            cur = {"qid": "VRAAG " + mv.group(1), "names": _hc_names(mv.group(2)), "lines": [], "pre": pending, "optnames": []}
            pending = []
            continue
        if cur is not None and not cur["lines"] and RE_NAMES_HC.match(line):
            cur["names"] += _hc_names(RE_NAMES_HC.match(line).group(1))
            continue
        if RE_COND_HC.match(line) and not re.search(r"\b(GA )?(NAAR|DOOR|VERDER)\b", line) and \
                (cur is None or not cur["lines"] or any(RE_OPT_HC.match(l) for l in cur["lines"]) or
                 (line.rstrip().endswith(":") and any(l.strip() for l in cur["lines"]))):
            # a routing condition printed after the options (or after the text of an open/numeric question) of one question
            # belongs to the next one ('INDIEN PARTNER:'); skip instructions ('INDIEN 2, GA NAAR 561') stay with the
            # question whose answers they refer to
            pending.append(squeeze(line))
            continue
        if cur is not None:
            cur["lines"].append(line)
    if cur:
        items.append(finish_vk_hc(cur, survey, instrument))
    return items


def finish_vk_hc(cur, survey, instrument):
    qtext, opts, routing, optnames, fmt = [], [], list(cur["pre"]), [], []
    in_instr = False                                            # a wrapped '(ENQ.: ...' / 'INDIEN ...' instruction continues
    for l in cur["lines"]:
        if not l.strip():
            continue
        if in_instr and not RE_OPT_HC.match(l) and not RE_OPT_NOCODE_HC.match(l):
            routing[-1] = squeeze(routing[-1] + " " + l.strip())
            in_instr = routing[-1].count("(") > routing[-1].count(")")
            continue
        in_instr = False
        mo = RE_OPT_HC.match(l) or RE_OPT_NOCODE_HC.match(l) or (RE_OPT_DOT_HC.match(l) if not qtext or not any(RE_OPT_HC.match(x) for x in cur["lines"]) else None)
        if mo and mo.re is RE_OPT_DOT_HC and (len(mo.group(2).split()) > 25 or not opts and not re.match(r"^\s*1\.", l)):
            mo = None                                            # a numbered sentence inside the question, not an option list
        if mo:
            lab = mo.group(mo.re.groups)
            code = mo.group(1) if mo.re.groups == 2 else ""
            mn = RE_OPTNAME_HC.match(lab)
            if mn:
                lab = mn.group(1); optnames.append(mn.group(2))
            mg = re.search(r"\s*\(?((?:GA (?:VERDER |DOOR )?)?(?:MET|NAAR)(?: VRAAG)?\s+\d+[a-z]?)\)?\s*$", lab, re.I)
            if mg:
                routing.append(f"{code or len(opts) + 1} -> {mg.group(1)}"); lab = re.sub(r"[\s>→\-]+$", "", lab[: mg.start()])
            opts.append((code, lab)); continue
        body = squeeze(l)
        if re.fullmatch(r"[A-Z][A-Z0-9_]{3,}", body) and opts and len(optnames) == len(opts) - 1:
            optnames.append(body); continue                      # variable name of the previous option wrapped to its own line
        if not opts and RE_NAMES_HC.match(l):
            cur["names"] += _hc_names(RE_NAMES_HC.match(l).group(1)); continue
        if re.match(r"^(\(?ENQ\.?:|\(?Enq\.?:|\(?ENQ:|INDIEN|Indien|ALS |TOON |GA VERDER|GA DOOR|GA NAAR|Toelichting)", body):
            routing.append(body)
            in_instr = body.count("(") > body.count(")")         # '(ENQ.: ... ' wrapped onto the next line(s)
            continue
        if RE_SCRIPT_HC.match(body):
            routing.append(body); continue                        # 'IF [ Q9001 , 1 TO 4 ] PUT IN "in Nederland"': fill instruction
        if RE_FORMAT_HC.match(body) and len(body.split()) <= 6:
            fmt.append(re.sub(r"[.…]+", " ", body).strip(" :")); continue   # 'Jaar', 'Aantal jaren.....', 'Weet niet': response fields of an open question
        if opts:
            c, t = opts[-1]; opts[-1] = (c, squeeze(t + " " + body))
        else:
            qtext.append(body)
    names = cur["names"]
    if optnames and len(optnames) == len(opts):           # one dummy per option: the option names are the item names
        names = names + [n for n in optnames if n not in names]
        subitems = "; ".join(f"{c} {n} {t}" for (c, t), n in zip(opts, optnames))
    else:                                                 # one name per option (plus at most one for the question itself)
        subitems = "; ".join(f"{c} {n} {t}" for (c, t), n in zip(opts, names)) if len(opts) > 1 and len(opts) <= len(names) <= len(opts) + 1 else ""
    return {
        "survey": survey, "instrument": instrument, "qid": cur["qid"], "qnames": ";".join(names),
        "block": "", "split_half": "", "routing": squeeze("; ".join(routing))[:600], "randomization": "",
        "question_text": squeeze(" ".join(qtext)), "answer_options": "; ".join(f"{c}={t}" if c else t for c, t in opts),
        "subitems": subitems, "intro": "", "format": squeeze("; ".join(dict.fromkeys(fmt))),
        "block_text": join_block(cur["pre"] + cur["lines"]),
    }


# ----------------------------------------------------------------- Veldkamp CAPI script printouts (SIM 2006, SING 2009)
# Blocks start with 'QUESTION n [MULTIPLE|FORM QUESTION]' (SIM 2006) or 'VRAAG n [MEERVOUDIG|FORMULIER]' (SING 2009), then
# script lines (IF [...], INDIEN [...], ONLY DISPLAY ..., PUT IN ..., CONTINUE AT ...), the display line '- VRAAG n' / 'Vr. n',
# the question text and the options '   1   label'.  Repeated blocks with the same number are battery items (the item text is
# part of the block); variable names are not printed, the data labels carry the question number ('Vraag 965: ...').
RE_QBLOCK = re.compile(r"^\s*(?:QUESTION|VRAAG)\s+(\d+)\s*(MULTIPLE|FORM QUESTION|MEERVOUDIG|FORMULIER|OPEN|NUMERIC)?\s*$")
RE_QDISP = re.compile(r"^\s*(?:-\s*VRAAG|Vr\.)\s+(\d+)\s*$")
RE_SCRIPT = re.compile(r"^\s*(IF\s*\[|INDIEN\s*\[|ONLY DISPLAY|TOON HELPSCHERM|PUT IN\b|ADD TO\b|COUNT ANSWERS|CONTINUE AT|GA VERDER|GA NAAR|GA DOOR|DUMMY|COMPUTE|RANDOM|ROTATE|FILL\b)")
RE_OPT_VK = re.compile(r"^\s{3,}(\d{1,3})\s{2,}(\S.*?)\s*$")
RE_FOOT_VK = re.compile(r"(Veldkamp Amsterdam|Velkdamp Amsterdam|^\s*V\d{4}\s*\|)")


def parse_vk_script(text, survey, instrument):
    items, cur, pending_fills, open_fill = [], None, [], False
    for raw in text.split("\n"):
        line = raw.rstrip("\f")
        if RE_FOOT_VK.search(line):
            continue
        if open_fill:                                           # wrapped 'PUT IN ... "...' continues on the next line(s)
            pending_fills[-1] = squeeze(pending_fills[-1] + " " + line.strip())
            open_fill = line.count('"') % 2 == 0
            continue
        mb = RE_QBLOCK.match(line)
        if mb:
            if cur:
                items.append(finish_vk_script(cur, survey, instrument))
            cur = {"qid": "VRAAG " + mb.group(1), "type": mb.group(2) or "", "lines": [], "fills": pending_fills}
            pending_fills = []
            continue
        if cur is None:
            continue
        if "PUT IN" in line and any(RE_OPT_VK.match(x) for x in cur["lines"]):
            pending_fills.append(squeeze(line)); open_fill = line.count('"') % 2 == 1; continue       # fills printed after the options of the previous block
        if RE_QDISP.match(line):
            continue
        cur["lines"].append(line)
    if cur:
        items.append(finish_vk_script(cur, survey, instrument))
    return items


def finish_vk_script(cur, survey, instrument):
    qtext, opts, routing, rand, fills = [], [], [], [], list(cur.get("fills", []))
    seen_text, in_enq, open_quote = False, False, False
    for l in cur["lines"]:
        s = l.strip()
        if not s:
            continue
        if open_quote:                                       # continuation of a wrapped script line ('PUT IN txt[ 6] "... geld te' / 'verdienen."')
            if fills: fills[-1] = squeeze(fills[-1] + " " + s)
            open_quote = s.count('"') % 2 == 0               # still open until the closing quote arrives
            continue
        if RE_SCRIPT.match(s) and s.count('"') % 2 == 1:
            open_quote = True
        if in_enq and not RE_OPT_VK.match(l) and not RE_SCRIPT.match(s) and not s.endswith("?") \
                and not (s[:1].isupper() and re.search(r"[.!\"]$", routing[-1])):   # continuation of a wrapped 'Enq.: ...' instruction
            routing[-1] = squeeze(routing[-1] + " " + s)
            in_enq = routing[-1].count("(") > routing[-1].count(")") or (s[:1].islower() and not re.search(r"[.?!)]$", s))
            continue
        in_enq = False
        if RE_SCRIPT.match(s):
            if re.match(r"^(IF|INDIEN)\s*\[", s) or s.startswith(("ONLY DISPLAY", "CONTINUE AT", "GA ")):
                routing.append(squeeze(s))
            if "PUT IN" in s:                                 # group-dependent fill of a '<?>' placeholder
                fills.append(squeeze(s))
            if re.search(r"\bRANDOM|ROTATE", s, re.I):
                rand.append(squeeze(s))
            continue
        mo = RE_OPT_VK.match(l)
        if mo and (seen_text or opts or routing):             # options may follow an interviewer instruction alone ('noteer stilzwijgend geslacht')
            opts.append((mo.group(1), mo.group(2))); continue
        if re.match(r"^\(?(ENQ|Enq)\.?:", s):
            routing.append(squeeze(s)); in_enq = s.count("(") > s.count(")") or not re.search(r"[.?!)]$", s); continue
        if opts:
            if re.match(r"^\(", s) or s.startswith("ENQ"):
                routing.append(squeeze(s))
            else:
                c, t = opts[-1]; opts[-1] = (c, squeeze(t + " " + s))
            continue
        seen_text = True
        qtext.append(squeeze(s))
    multi = cur["type"] in ("MULTIPLE", "MEERVOUDIG")
    question = squeeze(" ".join(qtext))
    if "<?>" in question and fills:                           # the printout replaced the fill variable by '<?>': keep the script's values
        routing.append("fill <?>: " + "; ".join(dict.fromkeys(f.replace("PUT IN", "PUT IN").strip() for f in fills))[:300])
    return {
        "survey": survey, "instrument": instrument, "qid": cur["qid"], "qnames": "",
        "block": cur["type"], "split_half": "", "routing": squeeze("; ".join(routing))[:600], "randomization": "; ".join(rand),
        "question_text": question, "answer_options": "; ".join(f"{c}={t}" for c, t in opts),
        "subitems": "; ".join(f"{c} {t}" for c, t in opts) if multi else "",
        "intro": "", "format": "",
        "block_text": join_block(cur["lines"]),
    }


PARSERS = {"tns": parse_tns, "spvn": parse_spvn, "spva": parse_spva, "vk_hc": parse_vk_hc, "vk_script": parse_vk_script}


RE_LEADIN = re.compile(r"^(.*?\b(?:in hoeverre bent u het (?:daar ?)?(?:mee )?eens[^?]*\?|wat vindt u van de volgende uitspraa?k[^?]*\??|bent u het (?:hier ?)?(?:mee )?eens[^?]*\?|"
                       r"kunt u (?:mij )?zeggen in hoeverre u het[^?]*\?|de volgende uitspra(?:ak|ken)[^?:]*[?:]|ik lees u (?:nu )?(?:een aantal |enkele )?uitspraken voor[^?:]*[?:.]))\s*(.+)$", re.I | re.S)


def split_leadin(r):
    """Hardcopy and script formats print the agreement lead-in and the item statement as one question text; the TNS/SPVN
    grids keep them apart (question_text + subitems).  Store the statement in 'proposition' so that batteries are
    compared at the same level in every format; 'question_text' keeps the full printed text."""
    q = r.get("question_text", "")
    if r.get("subitems") or not q or "?" not in q:
        return
    m = RE_LEADIN.match(q)
    if not m:
        return
    stem, tail = m.group(1).strip(), m.group(2).strip()
    if len(tail.split()) < 3 or tail.endswith("?") and len(tail.split()) < 6:
        return
    r["intro"] = squeeze((r.get("intro", "") + " " + stem).strip())
    r["proposition"] = squeeze(tail)


def is_heading(r):
    """A section heading printed beside a coded variable (SPVA 'B1. Opleidingen buiten Nederland'), not a spoken question."""
    q = r.get("question_text", "")
    return (r["survey"] in ("spva2002", "spvn2003") and not r.get("answer_options") and not r.get("subitems") and "?" not in q
            and len(q.split()) <= 6 and bool(re.fullmatch(r"[A-Z]\d{1,2}", r["qid"])))


def build_questionnaire_items():
    rows = []
    for k, d in CONSTRUCTED_MANUAL.items():
        CONSTRUCTED.setdefault(k, {}).update(d)
    for survey, instrument, rel, parser, span in SOURCES:
        pdf = os.path.join(ROOT, rel)
        if not os.path.exists(pdf):
            print(f"  [questionnaires] missing {rel} - skipped")
            continue
        txt = os.path.join(OUT_TXT, f"{survey}_{instrument}.txt")
        text = pdf_to_text(pdf, txt)
        if span:
            ms = re.search(span[0], text, re.M); me = re.search(span[1], text, re.M)
            text = text[ms.start() if ms else 0: me.start() if me else len(text)]
        items = PARSERS[parser](text, survey, instrument)
        print(f"  [questionnaires] {survey} {instrument}: {len(items)} question blocks")
        rows += items
    for r in rows:
        r.setdefault("intro", ""); r.setdefault("format", ""); r.setdefault("proposition", ""); r.setdefault("kind", "question")
        split_leadin(r)
        if is_heading(r):
            r["kind"] = "heading"
    # make question ids unique within survey x instrument (repeated grid blocks, repeated VRAAG numbers)
    seen, first = {}, {}
    for r in rows:
        k = (r["survey"], r["instrument"], r["qid"])
        seen[k] = seen.get(k, 0) + 1
        if seen[k] > 1:
            r["qid"] = f"{r['qid']} ({seen[k]})"
            if re.match(r"^\(vervolg\)", r["question_text"], re.I) and k in first:     # continuation grid: repeat the lead-in
                r["question_text"] = squeeze(first[k]["question_text"] + " (vervolg)")
        else:
            first[k] = r
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLS})
    with open(OUT_CONSTR, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["survey", "source_var", "description"])
        for k, d in sorted(CONSTRUCTED.items()):
            for nm, desc in sorted(d.items()):
                w.writerow([k, nm, desc])
    print(f"  [questionnaires] constructed variables listed in the codebooks: " + ", ".join(f"{k} {len(d)}" for k, d in sorted(CONSTRUCTED.items())))
    return rows


if __name__ == "__main__":
    build_questionnaire_items()
