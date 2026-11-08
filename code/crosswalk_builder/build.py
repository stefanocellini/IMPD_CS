# -*- coding: utf-8 -*-
"""
IMPD crosswalk builder.

Reads the raw DANS files (metadata only: variable names, labels, value labels), combines
them with the hand-authored declarations in variables.py / variables_sim.py / valuesets.py
and writes the crosswalk CSVs that drive both the R and the Stata pipelines:

  crosswalks/surveys.csv             survey registry (ids, years, DANS ids, structure, file names, weights)
  crosswalks/variable_map.csv        target variable -> source variable per survey, labels, universe, notes
  crosswalks/valuesets.csv           harmonized value labels (value set name, code, label)
  crosswalks/value_map.csv           survey-specific code -> harmonized code (or tagged missing)
  crosswalks/missing_rules.csv       survey-level missing-value conventions (code / label / declared rules)
  crosswalks/source_labels.csv       value labels of every source variable (label-based rules, codebook, *_source files)
  crosswalks/source_variables.csv    inventory of source variables and the files they occur in
  crosswalks/universes.csv           survey-specific universe text per target (codebook wording table)
  crosswalks/asked_to.csv            household surveys: respondent type whose questionnaire contained the item (the other type gets .e)
  crosswalks/wording.csv             target x survey: question text and answer options from the questionnaires
  crosswalks/wording_notes.csv       curated notes on wording / answer-scale changes
  crosswalks/questionnaire_items.csv question blocks parsed from the questionnaire PDFs (questionnaires.py)
  crosswalks/questionnaire_design.csv survey-level description of modes, versions, randomisation and split-half designs
  crosswalks/municipalities.csv      survey municipality code -> CBS gemeentecode
  crosswalks/cpi.csv                 CPI index 2015 = 100, chained from CBS 70936ENG annual rates

Run:  python code/crosswalk_builder/build.py   (from the IMPD root, after Rscript code/R/00a_source_metadata.R)
"""
import csv, os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import pyreadstat
import pandas as pd
from valuesets import VALUESETS, vs
import variables as VARDEF          # SPVA 2002 / SPVN 2003 declarations
import variables_sim                 # SIM 2015 / SIM 2020 declarations (extends the same registry)
import variables_2004_2011           # LAS 2004/05, SIM 2006, SING 2009, SIM 2011 (v0.4.0)
import variables_links               # relationship layer: partner link and copies for the household surveys (v0.4.2)
from declare import parts as src_parts, VARS, VMAP, WORDING_NOTES, WORDING_LINKS, UNIVERSES, ASKED_TO, SURVEY_KEYS, SKIPPED
import questionnaires
import surveys as SV                # one module per survey: surveys/<key>.py (registry, missing rules, questionnaire, routing ...)
for _declare in SV.DECLARE:          # declarations kept in a survey module (surveys added after the one-file-per-survey layout)
    _declare()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
CW = os.path.join(ROOT, "crosswalks")
os.makedirs(CW, exist_ok=True)

SURVEYS = SV.REGISTRY                # surveys/<key>.py: SURVEY (plus REGISTRY_ONLY rows of surveys not yet included)
INCLUDED = [s for s in SURVEYS if s["status"] == "included"]
ZIP_SHA256_KNOWN = SV.ZIP_SHA256      # sha256 of the DANS zips as downloaded (surveys/<key>.py: ZIP_SHA256)
# svy_key: immutable survey key used to build id_person / id_hh (the fieldwork year; fixed at first inclusion, never
# renumbered).  svy_id is the chronological display/order number and may shift when an earlier wave is inserted.
for s_ in SURVEYS:
    s_["svy_key"] = s_["svy_year"]
assert len({s_["svy_key"] for s_ in SURVEYS}) == len(SURVEYS), "svy_key must be unique"
# provenance of the deposited data files: sha256 of every source file read by the import step (row-number ids of
# SIM 2006 / SING 2009 are only meaningful for exactly these files)
import hashlib
import collections
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
for s_ in INCLUDED:
    files = [s_["file_main"]] if s_["structure"] == "flat" else [s_["file_ro"], s_["file_pp"], s_["file_hh"]]
    hashes = []
    for fn in files:
        fp = os.path.join(ROOT, "data", "raw", s_["key"], fn)
        hashes.append(_sha256(fp) if os.path.exists(fp) else "")
    s_["file_sha256"] = ";".join(hashes)
    zp = os.path.join(ROOT, s_["zipfile"])
    s_["zip_sha256"] = _sha256(zp) if os.path.exists(zp) else ZIP_SHA256_KNOWN.get(s_["key"], "")
ELIG = SV.ELIG                       # eligible sample / weights per survey (surveys/<key>.py: ELIGIBLE, WEIGHTS)
for s_ in SURVEYS:
    s_["eligible"], s_["weights"] = ELIG.get(s_.get("key", ""), ("", ""))
SLABEL = SV.LABEL                    # display names (surveys/<key>.py: LABEL)
for s_ in SURVEYS:                                                                   # display name travels with the registry (surveys.csv: label)
    s_["label"] = SLABEL.get(s_["svy_name"].lower(), re.sub(r"^([A-Z]+)(\d{4})$", r"\1 \2", s_["svy_name"]))
KEYS = [s["key"] for s in INCLUDED]
assert KEYS == SURVEY_KEYS, (KEYS, SURVEY_KEYS)
SURVEY_FILES = {s["key"]: ([("main", s["file_main"])] if s["structure"] == "flat" else [(l, s[f"file_{l}"]) for l in ("ro", "pp", "hh")]) for s in INCLUDED}


def write(name, rows, fields):
    with open(os.path.join(CW, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"  {name:<26} {len(rows):>6} rows")


# the survey registry is written first: code/R/00a_source_metadata.R reads it before this script needs its output
write("surveys.csv", SURVEYS, ["svy_id", "svy_key", "svy_name", "svy_year", "status", "label", "title", "dans_id", "doi", "access", "groups", "fieldwork", "mode", "zipfile",
                               "structure", "file_hh", "file_pp", "file_ro", "file_main", "encoding", "id_var", "weight_var", "sysmis_tag", "missing_scheme",
                               "file_sha256", "zip_sha256", "eligible", "weights"])


def fix_cp1252(s):
    try:
        return s.encode("latin1").decode("cp1252")
    except Exception:
        return s


def fix_double_utf8(s):
    """SIM 2020 labels are UTF-8 text that was re-encoded as UTF-8 once more ('Ã©Ã©n' = 'één')."""
    try:
        return s.encode("latin1").decode("utf-8")
    except Exception:
        return s


FIX = {"cp1252": fix_cp1252, "utf-8-double": fix_double_utf8}


def por_label_repair(path):
    """SPSS portable files carry labels in the 7-bit portable character set; the few latin-1 bytes in these
    deposits (Iraniërs, categorieën, Curaçoaers) come out of the reader as U+FFFD.  Returns a function that
    restores them from the raw bytes by matching the ASCII context of each damaged label."""
    raw = open(path, "rb").read()
    cache = {}
    def fix(lab):
        if "\ufffd" not in lab:
            return lab
        if lab in cache:
            return cache[lab]
        out, parts = lab, lab.split("\ufffd")
        nl = b"(?:\r?\n)?"                                    # portable files break lines every 80 characters
        pat = (nl + b"(.)" + nl).join(nl.join(re.escape(bytes([c])) for c in x.encode("latin1", "replace")) for x in parts)
        m = re.search(pat, raw, re.S)
        if m:
            chars = [b.decode("latin1") for b in m.groups()]
            out = "".join(x + (chars[i] if i < len(chars) else "") for i, x in enumerate(parts))
        cache[lab] = out
        return out
    return fix


def read_meta(path, encoding):
    # user-missing codes are read as values where pyreadstat allows it (.sav); for .por files the declared
    # user-missing values come from crosswalks/source_missing.csv written by code/R/00a_source_metadata.R
    if path.endswith(".por"):
        df, m = pyreadstat.read_por(path)
        fx = por_label_repair(path)
    else:
        df, m = pyreadstat.read_sav(path, encoding="utf-8" if encoding.startswith("utf-8") else ("windows-1252" if encoding == "windows-1252" else "latin1"), user_missing=True)
        fx = FIX.get(encoding, lambda s: s)
    out = {}
    for v in m.column_names:
        lab = fx(m.column_names_to_labels.get(v) or "")
        vl = {k: fx(x) for k, x in m.variable_value_labels.get(v, {}).items()}
        is_str = (not pd.api.types.is_numeric_dtype(df[v])) or any(isinstance(k, str) for k in vl)
        vl = {(int(k) if not is_str and float(k).is_integer() else str(k).strip()): x for k, x in vl.items()}
        # label-only artefacts (SIM 2015 '2147483622 = [-2]Blanc') never occur in the data: drop
        vl = {k: x for k, x in vl.items() if is_str or abs(k) < 1e9}
        if is_str:
            values = set(str(x).strip() for x in df[v].dropna().unique().tolist())
        else:
            values = set(df[v].dropna().unique().tolist())
        out[v] = dict(label=lab, fmt=m.original_variable_types.get(v, ""), n=int(df[v].notna().sum()), vl=vl, values=values, is_str=is_str)
    return len(df), out


# ------------------------------------------------------------------ source metadata
DECLARED = {}        # (survey, var) -> [(lo, hi)]  from R/haven (code/R/00a_source_metadata.R)
OBSERVED = {}        # (survey, var) -> set of observed codes
with open(os.path.join(CW, "source_missing.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        DECLARED.setdefault((r["survey"], r["source_var"]), []).append((float(r["lo"]), float(r["hi"])))
with open(os.path.join(CW, "source_values.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        OBSERVED.setdefault((r["survey"], r["source_var"]), set()).add(float(r["code"]))
source_vars = {}     # (survey, var) -> dict(label, files, vl, ...)
nobs = {}
for s in INCLUDED:
    key = s["key"]
    for lvl, rel in SURVEY_FILES[key]:
        path = os.path.join(RAW, key, rel.replace("/", os.sep))
        n, meta = read_meta(path, s["encoding"])
        nobs[(key, lvl)] = n
        for v, info in meta.items():
            rec = source_vars.setdefault((key, v), dict(label=info["label"], fmt=info["fmt"], files=[], vl=info["vl"], n={}, values=set(), declared=[], is_str=info["is_str"]))
            rec["files"].append(lvl); rec["n"][lvl] = info["n"]
            rec["values"] |= info["values"] | (OBSERVED.get((key, v), set()) if not info["is_str"] else set())
            rec["declared"] = sorted(set(DECLARED.get((key, v), [])))
            if info["vl"]: rec["vl"] = info["vl"]      # hh file usually has the richest labels

# ------------------------------------------------------------------ generated value maps / value sets
# transit countries: source label -> Landentabel code
for i in range(1, 5):
    src = f"ANDLAND{i}"; tgt = f"mig_tr_cntry{i}"
    for code, lab in source_vars[("spvn2003", src)]["vl"].items():
        if code < 0 or re.match(r"^(weet niet|wil niet zeggen|sysmis|missing)$", lab.strip(), re.I):
            continue   # handled by missing_rules
        if lab not in VARDEF.NL2CODE:
            raise SystemExit(f"no country code for {src} label {lab!r}")
        VARDEF.M(tgt, "spvn2003", src, code, VARDEF.NL2CODE[lab], note="label->Landentabel")

# value sets generated from source labels (src_<variable>): asylum reception places (SPVN), SBI 2008 divisions (SIM 2015)
for row in VARS:
    if row["valueset"].startswith("src_"):
        src = row["valueset"][4:]
        key = next(k for k in KEYS if row[f"src_{k}"] == src)
        vl = source_vars[(key, src)]["vl"]
        vs(row["valueset"], [(c, l) for c, l in sorted(vl.items()) if c >= 0 and not re.match(r"^(onbekend|weet niet|missing|sysmis|diversen|wil niet)", l.strip(), re.I)])

# ------------------------------------------------------------------ missing rules (data, read by both engines)
missing_rules = SV.MISSING_RULES      # surveys/<key>.py: MISSING_RULES, in survey order
CODE_RULES = {k: set() for k in KEYS}
LABEL_RULES = {k: [] for k in KEYS}
for r in missing_rules:
    if r["rule_type"] == "code": CODE_RULES[r["survey"]].add(float(r["match"]))
    if r["rule_type"] == "label": LABEL_RULES[r["survey"]].append(r["match"])

# ------------------------------------------------------------------ checks
errors = []
claimed = {}
for row in VARS:
    for key in KEYS:
        for src in src_parts(row[f"src_{key}"]):
            if (key, src) not in source_vars:
                errors.append(f"{row['target']}: source {src} not found in {key}")
            claimed.setdefault((key, src), []).append(row["target"])
for (k, v), why in SKIPPED.items():
    if (k, v) not in source_vars:
        errors.append(f"SKIP refers to unknown source variable {k}:{v}")
    claimed.setdefault((k, v), []).append("(skipped: " + why + ")")
unclaimed = [(k, v) for (k, v) in source_vars if (k, v) not in claimed]
if unclaimed and os.environ.get("IMPD_PARTIAL"):         # while a survey's crosswalk is being written
    print(f"  WARNING (IMPD_PARTIAL): {len(unclaimed)} unclaimed source variables: " + ", ".join(f"{k}:{v}" for k, v in sorted(unclaimed))[:3000])
elif unclaimed:
    errors.append("unclaimed source variables: " + ", ".join(f"{k}:{v}" for k, v in sorted(unclaimed)))
targets = {r["target"] for r in VARS}
for m in VMAP:
    if m["target"] not in targets:
        errors.append(f"value_map refers to unknown target {m['target']}"); continue
    if (m["survey"], m["source_var"]) not in source_vars:
        errors.append(f"value_map {m['target']}: {m['survey']}:{m['source_var']} not in data"); continue
    row = next(r for r in VARS if r["target"] == m["target"])
    if m["source_var"] not in src_parts(row[f"src_{m['survey']}"]):
        errors.append(f"value_map {m['target']} {m['survey']}: source {m['source_var']} is not the declared source {row[f'src_{m['survey']}']!r}")
    tv = m["target_value"]
    if row["valueset"] and not tv.startswith("."):
        codes = {c for c, _ in VALUESETS[row["valueset"]]}
        if float(tv) not in codes:
            errors.append(f"value_map {m['target']} {m['survey']} {m['source_var']} {m['source_value']}->{tv}: code not in valueset {row['valueset']}")


RE_RANGE = re.compile(r"^(-?[0-9.]+)-(-?[0-9.]+)$")              # "lo-hi", either bound may be negative ("-9--1", "-3-9")
RE_SPEC = re.compile(r"^(-?[0-9.]+|-?[0-9.]+--?[0-9.]+|'.*'|\*)$")  # the whole value-map grammar (number, range, quoted string, *)


def in_range(code, spec):
    if spec == "*": return True
    if spec.startswith("'"): return False          # string spec, numeric code
    m = RE_RANGE.match(spec)
    if m:
        return float(m.group(1)) <= code <= float(m.group(2))
    return float(spec) == code


warnings = []
for row in VARS:
    if not row["valueset"] or not row["include_main"]:
        continue
    vset = {c for c, _ in VALUESETS[row["valueset"]]}
    for key in KEYS:
      for src in src_parts(row[f"src_{key}"]):
        rec = source_vars[(key, src)]
        maps = [m for m in VMAP if m["target"] == row["target"] and m["survey"] == key and m["source_var"] == src]
        if rec["is_str"]:
            for val in sorted(rec["values"]):
                if not any(m["source_value"] == f"'{val}'" for m in maps):
                    warnings.append(f"{row['target']} [{key}:{src}] observed string value {val!r} is not mapped")
            continue
        for code in sorted(rec["values"]):
            if any(in_range(code, m["source_value"]) for m in maps): continue
            if code in CODE_RULES[key]: continue
            if any(lo <= code <= hi for lo, hi in rec["declared"]): continue
            lab = rec["vl"].get(code, "")
            if any(re.search(p, lab.strip(), re.I) for p in LABEL_RULES[key]): continue
            if code not in vset:
                warnings.append(f"{row['target']} [{key}:{src}] observed code {code} ({lab!r}) is neither mapped, missing, nor in value set {row['valueset']}")
if warnings:
    print("WARNINGS (unlabelled codes):"); print("\n".join(warnings))
if errors:
    print("\n".join(errors)); raise SystemExit("crosswalk build failed")

# ------------------------------------------------------------------ write CSVs

vm_rows = []
for row in VARS:
    r = dict(row)
    for key in KEYS:
        ps = src_parts(row[f"src_{key}"])
        r[f"files_{key}"] = ",".join(sorted({f for p in ps for f in source_vars[(key, p)]["files"]}, key=["ro", "pp", "hh", "main"].index))
        r[f"srclabel_{key}"] = " | ".join(source_vars[(key, p)]["label"] for p in ps)
    vm_rows.append(r)
# universe summary: the generic text (written for the household surveys) plus the survey-specific universes, so that a
# statement such as 'SPVA 2002 only' never survives the addition of a later survey carrying the same item
SNAME = {s["key"]: SLABEL[s["key"]] for s in INCLUDED}
STRUCTURE = {s["key"]: s["structure"] for s in INCLUDED}
HH_GENERIC = {"All household members (roster)", "All interviewed persons aged 12+ (main and mini questionnaire)", "All interviewed persons",
              "Heads of household (main questionnaire)", "Heads of household"}
_SV = r"(?:" + "|".join(sorted({s_["label"].split(" ")[0] for s_ in SURVEYS})) + r") \d{4}(?:/\d{2})?"   # survey labels in universe texts: series names from the registry (SPVA, SPVN, LAS, SIM, SING)
_RE_SVLIST = re.compile(r"\s*\((" + _SV + r"(?:(?:,| and|;) " + _SV + r")*)\)\s*$")        # '... (SIM 2006, SIM 2011)' at the end
_RE_ONLY = re.compile(r",?\s*\b" + _SV + r"(?: and " + _SV + r")? only\s*$")             # legacy '..., SPVA 2002 only'
_RE_TRAIL = re.compile(r",\s*" + _SV + r"(?:(?:,| and) " + _SV + r")*\s*$")                 # legacy '..., SIM 2015 and SIM 2020'
# derive rules that only recode or fill the surveys listed (sources plus survey-specific universes) keep the per-survey
# composition; rules that create values in surveys without a source (rel_cat20, age_cat, cit_nl_orig, ...) keep the
# generic text, because the list of sources would understate where the variable exists
_COMPOSABLE = re.compile(r"^(kl9_route|partner_copy:[a-z0-9_]+|has_prtnr_roster|prtnr_cores_roster)(\|(kl9_route|partner_copy:[a-z0-9_]+))*$")
for r in vm_rows:
    srcs = [k for k in KEYS if r[f"src_{k}"]]
    specific = {k: UNIVERSES[(r["target"], k)] for k in KEYS if (r["target"], k) in UNIVERSES}
    keys_u = [k for k in KEYS if k in srcs or k in specific]
    base = r["universe_en"]
    if not keys_u or (r["derive"] and not _COMPOSABLE.match(r["derive"])):
        continue
    # one text per survey: the survey-specific universe if given, else the generic one; a trailing list of survey
    # names is stripped so that identical texts can be grouped and the names re-attached once
    groups = []                                                           # [(text, [keys])] in survey order
    for k in keys_u:
        t = specific.get(k, base)
        if k not in specific and STRUCTURE[k] == "flat" and t.strip() in HH_GENERIC:
            t = "All respondents"                                          # household-sample wording does not apply to a person sample
        t = _RE_ONLY.sub("", t).strip()
        t = _RE_TRAIL.sub("", t).strip()
        t = _RE_SVLIST.sub("", t).strip()
        if groups and groups[-1][0] == t:
            groups[-1][1].append(k)
        else:
            hit = next((g for g in groups if g[0] == t), None)
            (hit[1].append(k) if hit else groups.append([t, [k]]))
    parts = []
    for t, ks in groups:
        if not t:
            continue
        names = ", ".join(SNAME[k] for k in ks)
        parts.append(t if all(SNAME[k] in t for k in ks) else f"{t} ({names})")
    r["universe_en"] = "; ".join(parts) if parts else base
vm_fields = ["target", "theme", "label_en", "scope", "type", "valueset", "include_main", "derive"]
for key in KEYS:
    vm_fields += [f"src_{key}", f"files_{key}", f"srclabel_{key}"]
vm_fields += ["universe_en", "notes"]
# (variable_map.csv is written after the questionnaire linking: the subject/reporter/availability metadata need the links)

vs_rows = [dict(valueset=name, code=c, label_en=l) for name, pairs in VALUESETS.items() for c, l in pairs]
write("valuesets.csv", vs_rows, ["valueset", "code", "label_en"])
_bad_specs = [f"{m['target']}/{m['survey']}/{m['source_var']}: {m['source_value']!r}" for m in VMAP if not RE_SPEC.match(str(m["source_value"]).strip())]
assert not _bad_specs, "value_map source_value outside the supported grammar (number, lo-hi range, 'string', *): " + "; ".join(_bad_specs[:10])
write("value_map.csv", VMAP, ["target", "survey", "source_var", "source_value", "target_value", "note"])
write("missing_rules.csv", missing_rules, ["survey", "rule_type", "match", "target", "note"])

sl_rows = [dict(survey=k, source_var=v, code=c, label_nl=l) for (k, v), rec in sorted(source_vars.items())
           for c, l in sorted(rec["vl"].items(), key=lambda x: (str(type(x[0])), x[0]) if isinstance(x[0], str) else ("", float(x[0])))]
write("source_labels.csv", sl_rows, ["survey", "source_var", "code", "label_nl"])

sv_rows = [dict(survey=k, source_var=v, label_nl=rec["label"], format=rec["fmt"], files=",".join(rec["files"]),
                n_hh=rec["n"].get("hh", ""), n_pp=rec["n"].get("pp", ""), n_ro=rec["n"].get("ro", ""), n_main=rec["n"].get("main", ""),
                targets=";".join(claimed.get((k, v), []))) for (k, v), rec in sorted(source_vars.items())]
write("source_variables.csv", sv_rows, ["survey", "source_var", "label_nl", "format", "files", "n_hh", "n_pp", "n_ro", "n_main", "targets"])

uni_rows = [dict(target=t, survey=k, universe=txt) for (t, k), txt in sorted(UNIVERSES.items())]
write("universes.csv", uni_rows, ["target", "survey", "universe"])
# respondent type whose questionnaire contained the item (household surveys; 02_harmonize sets .e for the other type)
for (t, k), (who, note) in ASKED_TO.items():
    r = next((x for x in vm_rows if x["target"] == t), None)
    assert r is not None and r[f"src_{k}"] and r["scope"] == "person" and r["type"] != "str", f"asked_to: {t}/{k} must be a numeric person-scope target with a source in {k}"
    assert STRUCTURE[k] == "hh_pp_ro", f"asked_to: {t}/{k} is not a household survey"
    assert "pp" in r[f"files_{k}"].split(","), f"asked_to: {t}/{k} is not in the persons file (file membership already sets .e)"
write("asked_to.csv", [dict(target=t, survey=k, asked_to=who, note=note) for (t, k), (who, note) in sorted(ASKED_TO.items())], ["target", "survey", "asked_to", "note"])
write("source_skipped.csv", [dict(survey=k, source_var=v, reason=why) for (k, v), why in sorted(SKIPPED.items())], ["survey", "source_var", "reason"])
write("wording_notes.csv", [dict(target=t, note=n) for t, n in sorted(WORDING_NOTES.items())], ["target", "note"])

# ------------------------------------------------------------------ questionnaire items and wording table
print("  questionnaire text extraction:")
for (k, v) in source_vars:
    questionnaires.KNOWN_NAMES.setdefault(k, set()).add(v.upper())
qitems = questionnaires.build_questionnaire_items()
by_name = {}       # (survey, NAME upper) -> list of items  (question names and matrix sub-item names)
by_token = {}      # (survey, TOKEN) -> list of items (caps tokens in SPVA/SPVN blocks)
for it in qitems:
    k = it["survey"]
    for nm in re.split(r"[;,\s–-]+", it["qnames"].upper()):
        if nm: by_name.setdefault((k, nm), []).append(it)
    for m in re.finditer(r"\b(\d{3,6}) ([A-Z][A-Z0-9_]{2,}) ", it["subitems"] + " "):
        by_name.setdefault((k, m.group(2)), []).append(it)
    if STRUCTURE[k] != "flat":                                # household surveys: name tokens of the hh/pp/ro questionnaires
        for tok in it["qnames"].split(";"):
            if tok: by_token.setdefault((k, tok), []).append(it)
PREFER = SV.PREFER                      # surveys/<key>.py: PREFER_INSTRUMENT (SIM 2015: CAWI is the reference, CAPI differences in capi_qid)
NUM_LINK = SV.NUM_LINK                  # surveys/<key>.py: LINK_BY_QNUM - questionnaires without variable names: link by the question number in the data label


def _overlap(a, b):
    """Number of shared word tokens (>= 4 letters, lower case) between two texts."""
    ta = {w for w in re.findall(r"[a-zà-ü]{4,}", a.lower())}
    tb = {w for w in re.findall(r"[a-zà-ü]{4,}", b.lower())}
    return len(ta & tb)


def subitem_list(it):
    """[(code, name, text)] parsed from the subitems column."""
    out = []
    for part in [x for x in it["subitems"].split("; ") if x.strip()]:
        m = re.match(r"^(\d{1,6})?\s*([A-Z][A-Z0-9_]{1,})?\s*(.*)$", part.strip())
        if m: out.append((m.group(1) or "", m.group(2) or "", m.group(3)))
    return out


def link(key, src, target=""):
    """Questionnaire item(s) for a source variable: manual link > name match > token match > restricted prefix match (SIM only).
    Returns (items, how, subitem_index) where subitem_index (1-based) is set when the variable is one item of a battery.
    Variables that the codebooks list as constructed are not linked to a question text; registry (_reg), survey-administration
    (svy_) and identifier (id_) targets have no questionnaire item by construction."""
    if (key, src) in WORDING_LINKS:
        qid = WORDING_LINKS[(key, src)]
        if qid == "":
            return [], "none (registry/constructed)", 0
        qid, _, k = qid.partition("#")
        its = [it for it in qitems if it["survey"] == key and it["qid"] == qid]
        return its, "manual", int(k) if k else 0
    its = by_name.get((key, src.upper()), [])
    if its and all(it.get("kind") == "heading" for it in its):
        return its, "heading", 0                 # section heading printed beside the variable name: provenance, not a spoken question
    if its: return its, "name", 0
    its = by_token.get((key, src.upper()), [])
    if its: return its, "token", 0
    if key in NUM_LINK:                      # Veldkamp script printouts: the data label carries the question number ('Vraag 965: ...')
        lab = source_vars[(key, src)]["label"]
        m = re.match(r"^\s*Vraag\s+(\d+)(?:\.(\d+))?\b", lab, re.I)
        if m:
            n, k = m.group(1), int(m.group(2)) if m.group(2) else 0
            cands = [it for it in qitems if it["survey"] == key and (it["qid"] == f"VRAAG {n}" or it["qid"].startswith(f"VRAAG {n} ("))]
            if len(cands) == 1:
                return cands, "qnum", (k if k and cands[0]["subitems"] else 0)
            if cands:
                rest = re.sub(r"^\s*Vraag\s+\d+(?:\.\d+)?\s*[:\-]?\s*", "", lab)
                scored = [(_overlap(rest, it["question_text"]), -i, it) for i, it in enumerate(cands)]
                best = max(scored)
                if best[0] == 0 and k and k <= len(cands):
                    return [cands[k - 1]], "qnum", 0
                return [best[2]], "qnum", 0
    if target.endswith("_reg") or target.startswith(("svy_", "id_")):
        return [], "none (registry/administrative)", 0
    if src.upper() in questionnaires.DERIVED_AT.get(key, {}):     # coded/constructed variable printed after a question block
        qid = questionnaires.DERIVED_AT[key][src.upper()]
        blk = re.match(r"^[A-Z]\d+", qid)
        hdr = [it for it in qitems if it["survey"] == key and blk and it["qid"] == blk.group(0) and it["qid"] != qid
               and "?" not in it["question_text"] and not it["answer_options"]]        # sub-block header, e.g. 'B3. Afgesloten opleiding in Nederland'
        its = hdr or [it for it in qitems if it["survey"] == key and it["qid"] == qid]
        if its: return its, "derived", 0
    if src.upper() in questionnaires.CONSTRUCTED.get(key, {}):
        return [], "none (constructed)", 0
    su = src.upper()
    if len(su) >= 5 and key.startswith("sim"):   # prefix match: source name = questionnaire name + short suffix (arbervj -> ARBERV, maxoplbl_kl -> MAXOPLBL)
        cands = [(nm, v) for (k, nm), v in by_name.items() if k == key and len(nm) >= 5 and su.startswith(nm) and len(su) - len(nm) <= 6]
        if cands:
            nm, v = max(cands, key=lambda x: len(x[0]))
            return v, "prefix", 0
    return [], "none", 0


# printed routing text = routing/version conditions (INDIEN, IF, ASK ONLY IF, skips, fills) + interviewer instructions (ENQ.: ...);
# the two are kept in separate columns (routing / instruction) so that eligibility is not confused with how to record or assess
RE_INSTR_SEG = re.compile(r"^\(?(ENQ|Enq|INT|Int|Toelichting|Scripter notes|Help|Opmerking|opmerking|Noteer|NOTEER)")
RE_COND_SEG = re.compile(r"^(INDIEN\b|IF\b|ASK (ONLY )?IF\b|Ask only if|ASK ALL\b|Niet stellen indien|Alleen stellen|Stel alleen|Vraag alleen|ALS\b.*:$)", re.I)
RE_SKIP_SEG = re.compile(r"(\u21d0|->|\bGA (NAAR|DOOR|VERDER)\b|\bga naar\b|> ?naar\b|CONTINUE AT|\bEIND\b|overslaan)", re.I)
def split_routing(text):
    """Printed routing text -> (eligibility conditions, interviewer instructions, skip instructions, script/fill/other).
    Only the conditions say who was asked; skips ('2 -> naar 1519', 'CONTINUE AT QUESTION 505'), text fills ('PUT IN',
    'vul in'), display settings and parse debris are provenance (kept in wording.csv, not printed in the codebook table)."""
    cond, instr, skip, script = [], [], [], []
    for x in (x.strip() for x in re.split(r";\s*", text) if x.strip()):
        if RE_INSTR_SEG.match(x): instr.append(x)
        elif RE_SKIP_SEG.search(x): skip.append(x)
        elif RE_COND_SEG.match(x) and not re.search(r"vul in|PUT IN|inladen|invoegen|tonen", x, re.I): cond.append(x)
        else: script.append(x)
    return "; ".join(cond), "; ".join(instr), "; ".join(skip), "; ".join(script)

wording_rows, unlinked = [], []
for row in VARS:
    for key in KEYS:
      for src in src_parts(row[f"src_{key}"]):
        its, how, k = link(key, src, row["target"])
        pref = PREFER.get(key)
        main_items = [it for it in its if pref is None or it["instrument"] == pref] or its
        it = main_items[0] if main_items else None
        capi = [x for x in its if key == "sim2015" and x["instrument"] == "capi"]
        rec = source_vars[(key, src)]
        item_text = ""; split = it["split_half"] if it else ""
        if it:
            subs = subitem_list(it); ss = it.get("subitem_splits", "").split("|") if it.get("subitem_splits") else []
            if k and k <= len(subs):
                item_text = subs[k - 1][2]
                if ss and k <= len(ss): split = ss[k - 1]                   # marker inside the grid: the sub-item's own half
            else:
                hit = [(j, t) for j, (c, n, t) in enumerate(subs) if n and (n == src.upper() or src.upper().startswith(n))]
                if hit:
                    item_text = hit[0][1]
                    if ss and hit[0][0] < len(ss): split = ss[hit[0][0]]
        qtext = it["question_text"] if it else ""
        desc = questionnaires.CONSTRUCTED.get(key, {}).get(src.upper(), "")
        generic = desc.startswith("listed as constructed")
        # source definition (English metadata) for sources that are not questionnaire prompts: kept apart from the Dutch text
        srcdef = ""
        if how == "none (constructed)":
            srcdef = "Constructed variable (data producer's coding)" + (f" - codebook: {desc}" if desc else ""); qtext = ""
        elif how == "none (registry/administrative)":
            srcdef = "Registry (CBS microdata) or survey-administration field, no questionnaire item" + (f" - codebook: {desc}" if desc and not generic else ""); qtext = ""
        elif how == "none (registry/constructed)":
            srcdef = "Registry or constructed field, no questionnaire item" + (f" - codebook: {desc}" if desc else ""); qtext = ""
        elif how == "derived":
            where = f"at the end of block {it['qid']} ('{qtext}')" if "?" not in qtext else f"after question {it['qid']} ('{qtext[:120]}{'...' if len(qtext) > 120 else ''}')"
            srcdef = f"Coded/constructed variable{' - codebook: ' + desc if desc else ''}; not a question: its name is printed in the questionnaire {where}"; qtext = ""
        elif how == "heading":
            srcdef = f"Section heading '{it['qid']}. {qtext}' printed beside the variable name: a coded/constructed variable of that section{' - codebook: ' + desc if desc else ''}"; qtext = ""
        elif how == "none":
            srcdef = "No questionnaire item located for this source variable"
        spoken = bool(it) and how in ("name", "token", "manual", "qnum", "prefix") and it.get("kind", "question") == "question"
        if spoken and not item_text and it.get("proposition"):
            item_text = it["proposition"]        # statement of a battery item printed inside the question block (hardcopy/script formats)
        routing_txt, instr_txt, skip_txt, script_txt = split_routing(it["routing"]) if it else ("", "", "", "")
        wording_rows.append(dict(
            target=row["target"], survey=key, source_var=src, match=how, respondent_facing=int(spoken),
            instrument=it["instrument"] if it else "", qid=it["qid"] if it else "", capi_qid=capi[0]["qid"] if capi else "",
            block=it["block"] if it else "", split_half=split, routing=routing_txt, instruction=instr_txt, routing_skip=skip_txt, routing_script=script_txt,
            randomization=it["randomization"] if it else "",
            intro=it.get("intro", "") if spoken else "", question_text=qtext, item_text=item_text, format=it.get("format", "") if spoken else "",
            answer_options=it["answer_options"] if it and how not in ("derived", "heading") else "",
            subitems=it["subitems"] if it and how not in ("derived", "heading") else "",
            source_definition=srcdef,
            label_nl=rec["label"], value_labels_nl="; ".join(f"{c}={l}" for c, l in sorted(rec["vl"].items(), key=lambda x: str(x[0]))),
            block_text=it["block_text"] if it else ""))
        if how == "none" and row["include_main"]:
            unlinked.append(f"{key}:{src}")
# ------------------------------------------------------------------ routing rules: printed routing conditions -> harmonized gate variables
# The questionnaires route on source questions (Q9001 sample group, Q43 partner, Q35 sex, Q930 religion ...).  Each rule maps
# a printed condition (regex on the routing text of a question) to the harmonized variable that carries the same information
# and the values under which the question was asked; 99_checks.R verifies every linked variable against its gates in the data
# and the codebook prints the gates per survey.  (crosswalks/routing_rules.csv)
ROUTING_RULES = SV.ROUTING_RULES      # surveys/<key>.py: ROUTING_RULES (survey, pattern, gate, allowed, description, consumes)
assert not any(";" in e for *_, e, _ in ROUTING_RULES), "routing rule descriptions must not contain ';' (gate separator)"
write("routing_rules.csv", [dict(survey=a, pattern=b, gate=c, allowed=d, description=e, consumes=f) for a, b, c, d, e, f in ROUTING_RULES], ["survey", "pattern", "gate", "allowed", "description", "consumes"])
# printed conditions that do not gate the item they are printed with (sub-items of a grid share one routing block; the
# data show the item was asked more widely): the gate is not applied and the reason is printed in the codebook
ROUTING_EXCEPTIONS = SV.ROUTING_EXCEPTIONS   # surveys/<key>.py: ROUTING_EXCEPTIONS
write("routing_exceptions.csv", [dict(survey=a, source_var=b, gate=c, reason=d) for a, b, c, d in ROUTING_EXCEPTIONS], ["survey", "source_var", "gate", "reason"])
# household surveys (SPVA/SPVN): the merge takes a source variable from the most detailed file (heads > interviewed persons >
# roster), a file's explicit system-missing code included.  A declared exception lets a valid value of a less detailed file
# stand in where the more detailed file holds only the system-missing code (v0.4.8, follow-up audit of v0.4.7: one SPVN 2003
# generation code).  Not applied in general: the same code also marks derived not-applicable values that agree with the
# chosen self-report (the age bands of a member whose self-reported age is 12 against a roster age of 17; decisions 1).
MERGE_EXCEPTIONS = SV.MERGE_EXCEPTIONS       # surveys/<key>.py: MERGE_EXCEPTIONS
write("merge_exceptions.csv", [dict(survey=a, source_var=b, sysmis_code=c, rule=d, reason=e) for a, b, c, d, e in MERGE_EXCEPTIONS], ["survey", "source_var", "sysmis_code", "rule", "reason"])
_RE_FILL = re.compile(r"vul in|PUT IN|fill <\?>|Vraagtekst|inladen|tonen|Help-?(button|tekst)|[\u201c\u201d\"]|ADD TO|REMOVE FROM|SAVE IN|DISPLAY", re.I)   # text fills, option/display script and quoted alternative wordings, not routing
_RE_ALT = re.compile(r"\\|\bor\b|\bOF (INDIEN|IF|ALS)\b|\bOF\b(?=[^()]*\bQ ?\d)", re.I)      # alternatives between conditions: not decomposable into per-variable gates
_RE_NEGCONJ = re.compile(r"^(Niet stellen indien|NIET STELLEN|Not asked if).*\b(AND|EN)\b", re.I)   # negated conjunction: not decomposable either
# ---- automatic translation of question references in printed conditions (v0.4.3)
# 'IF [ Q60 , 1 , 2 , 3 ]', 'ASK ONLY IF not Q235=3', 'INDIEN PARTNER (Q43=1)': the referenced question is looked up in
# the same survey (wording rows: question id -> source variable -> harmonized target), its source codes are translated
# with the value map, and the gate is stated on the harmonized variable ('edu_cntry in {1,2}').  Negations take the
# complement within the value set; comparisons ('Q4201>0') are kept on numeric targets.  A condition that combines
# alternatives (\ / or) is not translated; references that a hand-written rule already covers are skipped.  Every gate,
# hand-written or translated, is verified against the data (docs/routing_check.csv).
QINDEX = {}
for w in wording_rows:
    m = re.match(r"^(?:VRAAG\s+|Q)?(\d+[A-Za-z]?)\s*(\(.*\))?$", w["qid"].strip()) if w["qid"] else None
    if m and w["match"] not in ("derived", "heading") and not w["match"].startswith("none"):
        QINDEX.setdefault((w["survey"], m.group(1).upper()), []).append(w)
VM_IDX = {}
for v in VMAP:
    VM_IDX.setdefault((v["target"], v["survey"], v["source_var"]), []).append((str(v["source_value"]), str(v["target_value"])))
VARS_BY_T = {r["target"]: r for r in VARS}
def _map_code(specs, code):
    """Harmonized code for a source code under the value-map specs (first match wins; '*' = passthrough)."""
    for spec, tv in specs:
        if spec.startswith("'"): continue
        if spec == "*": return code
        if re.fullmatch(r"-?\d+(\.\d+)?", spec):
            if float(spec) == float(code): return tv
        else:
            m = re.fullmatch(r"(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)", spec)
            if m and float(m.group(1)) <= float(code) <= float(m.group(2)): return tv
    return None if specs else code                     # no value map at all: codes pass through
RE_ATOM = re.compile(r"(?P<neg>\b(?:not|niet)\b\s*|#\s*)?\(?\s*Q?(?P<q>\d{1,5}[A-Za-z]?)\s*(?P<op>>=|<=|>|<|=|,|\bis\b(?:\s+(?P<neg2>not|niet)\b)?)\s*(?P<vals>\d+(?:\s*(?:,|TO|tot|to|-|\u2013)\s*\d+)*)", re.I)
def _expand(vals):
    out = []
    for part in re.split(r"\s*,\s*", vals.strip()):
        m = re.fullmatch(r"(\d+)\s*(?:TO|tot|to|-|\u2013)\s*(\d+)", part, re.I)
        if m: out.extend(range(int(m.group(1)), int(m.group(2)) + 1))
        elif re.fullmatch(r"\d+", part): out.append(int(part))
    return out
def missing_tag(key, src, code):
    """Harmonized missing tag ('.a' ...) of a source code under the survey's missing rules, or None for a valid code."""
    rec = source_vars.get((key, src))
    rules = [m for m in missing_rules if m["survey"] == key]
    for m in rules:
        if m["rule_type"] == "code" and float(m["match"]) == float(code): return m["target"]
    if rec and any(lo <= code <= hi for lo, hi in rec["declared"]):
        for m in rules:
            if m["rule_type"] == "declared" and re.fullmatch(m["match"], str(int(code)) if float(code).is_integer() else str(code)): return m["target"]
    lab = rec["vl"].get(code, "") if rec else ""
    for m in rules:
        if m["rule_type"] == "label" and lab and re.search(m["match"], lab.strip(), re.I): return m["target"]
    return None
def translate_condition(key, seg, consumed):
    """Gates (list of 'target in {codes} (desc)' / 'target > n (desc)' / 'target is {.a,.b} (desc)') for the Q-references
    of one printed condition.  Negations are taken at the source level (the observed codes of the source question minus
    the listed ones) before mapping; references to don't-know/refusal codes give a missing-tag gate."""
    if _RE_ALT.search(seg): return [], "alternatives"
    if _RE_NEGCONJ.search(seg): return [], "negated conjunction"
    gates = []
    for m in RE_ATOM.finditer(seg):
        q = m.group("q").upper(); op = m.group("op").lower().split()[0]; neg = bool(m.group("neg")) or bool(m.group("neg2"))
        if re.sub(r"[A-Z]$", "", q) in consumed or q in consumed: continue
        cands = QINDEX.get((key, q), [])
        srcs = list(dict.fromkeys(c["source_var"] for c in cands))
        if len(srcs) != 1: continue                            # unknown question, or a grid with several sub-items
        src = srcs[0]; qref = cands[0]["qid"]
        done = False
        for c in cands:
            t = c["target"]; r = VARS_BY_T.get(t)
            if not r or r["include_main"] != 1: continue
            specs = VM_IDX.get((t, key, src), [])
            if op in (">", "<", ">=", "<="):
                if r["type"] in ("num", "year") and all(sp == "*" for sp, _ in specs):
                    gates.append(f"{t} {op} {m.group('vals').strip()} (from {qref} `{src}` {op} {m.group('vals').strip()})"); done = True
                continue
            codes = _expand(m.group("vals"))
            if not codes: continue
            rec = source_vars.get((key, src))
            def _tag(c_):                                          # an explicit value-map entry takes precedence over the missing rules
                for spec, tv in specs:
                    if (re.fullmatch(r"-?\d+(\.\d+)?", spec) and float(spec) == float(c_)) or \
                       (re.fullmatch(r"(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)", spec) and float(spec.split("-")[0] or 0) <= float(c_)):
                        mm_ = re.fullmatch(r"(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)", spec)
                        if mm_ and not (float(mm_.group(1)) <= float(c_) <= float(mm_.group(2))): continue
                        return tv if str(tv).startswith(".") else None
                return missing_tag(key, src, c_)
            tags = [_tag(c_) for c_ in codes]
            if all(tags) and not neg:                              # 'INDIEN [ Q141 , 9997 , 9999 ]': asked when the amount was don't know / refused
                tg = sorted({x for x in tags if x != "."})
                if tg: gates.append(f"{t} is {{{','.join(tg)}}} (from {qref} `{src}` {m.group('vals').strip()}: missing-value codes)"); done = True
                break
            if any(tags): continue                                 # mixed valid and missing codes: not translated
            if neg:
                if not rec or rec.get("is_str"): continue
                universe = [c_ for c_ in rec["values"] if _tag(c_) is None]
                codes = [c_ for c_ in universe if c_ not in codes]
                if not codes: continue
            tr = [_map_code(specs, c_) for c_ in codes]
            if any(x is None for x in tr): continue
            tr = {str(int(float(x))) for x in tr if not str(x).startswith(".")}
            if not tr: continue
            gates.append(f"{t} in {{{','.join(sorted(tr, key=int))}}} (from {qref} `{src}` {'not ' if neg else ''}{m.group('vals').strip()})"); done = True
            break
    return gates, ""
# 'INDIEN JA:' / 'INDIEN NEE:' (SPVA, SPVN, LAS hardcopies) refer to the question printed immediately before: resolved
# through the document order of the parsed items and the option labels of that question
ORDER = {}
for it in qitems:
    ORDER.setdefault((it["survey"], it["instrument"]), []).append(it["qid"])
WROWS_BY_QID = {}
for w in wording_rows:
    if w["respondent_facing"] == 1 and w["qid"]:
        WROWS_BY_QID.setdefault((w["survey"], w["instrument"], w["qid"]), []).append(w)
QTEXT = {(it["survey"], it["instrument"], it["qid"]): it["question_text"] for it in qitems}
def translate_prev(w, seg):
    """Gates for 'INDIEN JA/NEE:' from the question printed before; a note when that question is not in the data file."""
    m = re.match(r"^INDIEN (JA|NEE)\s*:?\s*$", seg.strip(), re.I)
    if not m: return [], ""
    want = m.group(1).lower()
    seq = ORDER.get((w["survey"], w["instrument"]), [])
    if w["qid"] not in seq: return [], ""
    i = seq.index(w["qid"])
    for j in range(i - 1, max(-1, i - 4), -1):
        prev = WROWS_BY_QID.get((w["survey"], w["instrument"], seq[j]), [])
        srcs = list(dict.fromkeys(x["source_var"] for x in prev))
        if not prev:
            qt = QTEXT.get((w["survey"], w["instrument"], seq[j]), "")
            if qt and "?" in qt: return [], f"'{seg.strip()}' refers to the preceding question {seq[j]} ('{qt[:90]}'), which is not in the data file"
            continue
        if len(srcs) != 1: continue
        opts = dict(re.findall(r"(-?\d+)=([^;]+)", prev[0]["answer_options"]))
        code = next((c for c, l in opts.items() if re.match(r"^%s\b" % want, l.strip(), re.I)), None)
        if code is None: return []
        for x in prev:
            r = VARS_BY_T.get(x["target"])
            if not r or r["include_main"] != 1 or x["target"] == w["target"]: continue
            tv = _map_code(VM_IDX.get((x["target"], w["survey"], srcs[0]), []), float(code))
            if tv is None or str(tv).startswith("."): continue
            return [f"{x['target']} in {{{int(float(tv))}}} (from {seq[j]} `{srcs[0]}` {want})"], ""
        return [], ""
    return [], ""
n_auto = 0
for w in wording_rows:
    gates, notes_r, consumed = [], [], set()
    if w["respondent_facing"] == 1 and w["routing"]:
        segs = [x for x in re.split(r";\s*", w["routing"]) if x and not _RE_FILL.search(x)]
        plain = [x for x in segs if not _RE_ALT.search(x) and not _RE_NEGCONJ.search(x)]
        for svy, pat, gate, allowed, desc, cons in ROUTING_RULES:
            if svy == w["survey"] and gate != w["target"] and any(re.search(pat, x, re.I) for x in plain):
                exc = next((e for e in ROUTING_EXCEPTIONS if e[0] == svy and re.search(e[1], w["source_var"]) and e[2] == gate), None)
                if exc: notes_r.append(f"{gate} in {{{allowed}}} not applied: {exc[3]}")
                else: gates.append(f"{gate} in {{{allowed}}} ({desc})")
                consumed.update(x for x in cons.split(",") if x)
        auto_all = []
        for x in segs:
            auto, why = translate_condition(w["survey"], x, consumed)
            if not auto and not why:
                auto, pnote = translate_prev(w, x)
                if pnote: notes_r.append(pnote)
            auto = [g for g in auto if not g.startswith(w["target"] + " ")]        # a question does not gate itself
            for g in auto:
                v = g.split(" ", 1)[0]
                exc = next((e for e in ROUTING_EXCEPTIONS if e[0] == w["survey"] and re.search(e[1], w["source_var"]) and e[2] == v), None)
                if exc: notes_r.append(f"{v} gate not applied: {exc[3]}")
                else: auto_all.append(g)
            if why == "alternatives": notes_r.append(f"printed condition combines alternatives, not translated: {x[:120]}")
            if why == "negated conjunction": notes_r.append(f"printed condition is a negated conjunction, not translated: {x[:120]}")
        # the same variable referenced in several segments ('IF Q854,1,2; IF Q854,4'): alternative routes -> union of codes
        byvar = {}
        for g in auto_all:
            mm = re.match(r"^([a-z0-9_]+) in \{([0-9,]+)\} \(from (.*)\)$", g)
            if mm and mm.group(1) in byvar and byvar[mm.group(1)][0]:
                c0, f0 = byvar[mm.group(1)]
                byvar[mm.group(1)] = (sorted(set(c0) | set(mm.group(2).split(",")), key=int), f0 + " / " + mm.group(3))
            elif mm: byvar[mm.group(1)] = (mm.group(2).split(","), mm.group(3))
            else: byvar[g.split(" ", 1)[0]] = (None, g)
        for v, (codes_, src_) in byvar.items():
            g = f"{v} in {{{','.join(codes_)}}} (from {src_})" if codes_ else src_
            n_auto += 1; gates.append(g)
    seen = {}
    for g in gates:                                             # one gate per variable: the first (hand-written) wins
        v = g.split(" ", 1)[0]
        if v not in seen: seen[v] = g
    w["routing_gates"] = "; ".join(seen.values())
    w["routing_note"] = "; ".join(dict.fromkeys(notes_r))
print(f"  routing gates linked for {sum(1 for w in wording_rows if w['routing_gates'])} wording rows ({n_auto} translated from question references; {sum(1 for w in wording_rows if w['routing_note'])} rows with a note)")

# regression checks on the parsers (cases confirmed by the v0.4.0 wording audit, 29 Oct 2026)
def _w(key, src):
    return next((r for r in wording_rows if r["survey"] == key and r["source_var"] == src), None)
_fails = []
_nchecks = 0
def _expect(cond, msg):
    global _nchecks
    _nchecks += 1
    if not cond: _fails.append(msg)
r_ = _w("sim2006", "ZHFDDOEK");  _expect(r_ and r_["question_text"].startswith("Draagt u een hoofddoek") and "1=ja" in r_["answer_options"], "SIM 2006 Q1400 headscarf question and option 1 restored")
r_ = _w("sing2009", "ZHFDDOEK"); _expect(r_ and r_["question_text"].startswith("Draagt u een hoofddoek") and "1=ja" in r_["answer_options"], "SING Q3100 headscarf question and option 1 restored")
_expect(not any("VRAGENLIJST SIM" in r["question_text"] + r["item_text"] for r in wording_rows), "no SIM 2011 page footer in question or item text")
r_ = _w("sim2011", "HUWPART");   _expect(r_ and "1. Ja" not in r_["question_text"] and "1=Ja" in r_["answer_options"], "SIM 2011 VRAAG 67 dotted options parsed as options")
r_ = _w("sim2011", "HOMOFAM");   _expect(r_ and "vervelend vindt" not in r_["question_text"] + r_["item_text"] and "vervelend vindt" in r_["instruction"], "SIM 2011 Q815 wrapped ENQ instruction kept whole in the instruction column")
r_ = _w("sim2015", "aantkind");  _expect(r_ and "Max 10" not in r_["question_text"] and "Max 10" in r_["format"], "SIM 2015 Q42 numeric bound moved to format")
r_ = _w("sim2020", "huisarts");  _expect(r_ and "NUMBER" not in r_["question_text"], "SIM 2020 Q1005 numeric widget out of the question")
r_ = _w("sim2020", "taalpart");  _expect(r_ and "AND" not in r_["question_text"] and not r_["question_text"].startswith("[Inleiding"), "SIM 2020 Q650 wrapped condition and introduction out of the question")
r_ = _w("sim2020", "gelooft");   _expect(r_ and "GOTO" not in r_["question_text"] + r_["answer_options"], "SIM 2020 Q920 GOTO out of question and options")
# routing conditions printed before the header they govern (v0.4.2 routing-gate check)
r_ = _w("sim2015", "contactv");  _expect(r_ and "ASK ONLY IF not Q9001=7 and Q780=1,2" in r_["routing"], "SIM 2015 Q785 takes the 'ASK ONLY IF' printed before its header")
r_ = _w("sim2015", "vrtijdnl");  _expect(r_ and "ASK ONLY IF" not in r_["routing"], "SIM 2015 Q780 does not inherit the next question's 'ASK ONLY IF'")
r_ = _w("las2004", "PARTUREN");  _expect(r_ and r_["routing"].startswith("INDIEN PARTNER WERKT:") and "VRIJWILLIGERS" not in r_["routing"], "LAS VRAAG 75 takes the condition printed before its header")
r_ = _w("las2004", "VRIJWUUR");  _expect(r_ and "INDIEN PARTNER" not in r_["routing"], "LAS VRAAG 72 keeps only its own condition")
r_ = _w("sim2011", "KINDNL");    _expect(r_ and "of gelijk aan 1:" in r_["routing"] and "INDIEN ALLOCHTOON" in r_["routing"], "SIM 2011 VRAAG 115 takes the wrapped condition printed before its header")
r_ = _w("sim2011", "NIETINWKIND"); _expect(r_ and "INDIEN ALLOCHTOON" not in r_["routing"], "SIM 2011 VRAAG 101 does not inherit the next question's condition")
r_ = _w("sim2006", "GESLPART");  _expect(r_ and "1=man" in r_["answer_options"] and not r_["question_text"].startswith("1 man"), "SIM 2006 VRAAG 75 options after an interviewer instruction parsed as options")
r_ = _w("sim2020", "etngba");    _expect(r_ and "generatie" not in r_["answer_options"] and r_["answer_options"].count("=") == 8, "SIM 2020 Q9001 origin-group categories do not absorb the 9004 GENERATIE field")
r_ = _w("sim2006", "MANGELD");   _expect(r_ and r_["answer_options"].endswith("geen antwoord") and "verdienen" not in r_["answer_options"], "SIM 2006 VRAAG 1055 last category does not absorb the wrapped PUT IN line that follows")
_expect(not any(re.search(r'\w+\."$', r["answer_options"]) for r in wording_rows if r["survey"] in ("sim2006", "sing2009")), "no SIM 2006/SING category list ends with a stray quoted script fragment")
_expect(any(r["qid"] == "Q14041" for r in wording_rows if r["survey"] == "sim2020"), "SIM 2020 colon-free headers Q14041.. are separate blocks")
r_ = _w("spva2002", "OPLBLNL");  _expect(r_ and r_["match"] == "heading", "SPVA B1 heading linked as provenance, not as a spoken question")
_expect(all(r["respondent_facing"] == 0 for r in wording_rows if r["match"].startswith("none") or r["match"] in ("derived", "heading")), "constructed/registry/heading rows are not respondent-facing")
if _fails:
    print("  PARSER REGRESSION FAILURES:"); [print("    - " + f) for f in _fails]
    raise SystemExit("questionnaire parser regression checks failed")
print(f"  parser regression checks: {_nchecks - len(_fails)} of {_nchecks} pass")

# ------------------------------------------------------------------ subject / reporter / availability metadata (audit decision 2)
# subject: whom the variable describes; reporter_<survey>: who supplied the value; avail_<survey>: how the survey contributes.
# Rules are mechanical (name and label patterns, file levels, link types) with the overrides below; see docs/decisions.md section 10.
SUBJECT_OVERRIDE = {
    "lang_nl_prtnr": "self", "lang_nl_chd": "self", "lang_nl_rated_prtnr": "partner", "svy_lang_prtnr": "partner", "svy_prtnr_avail": "partner",
    "trn_sup_prtnr": "self", "trn_sup_chd": "self", "trn_n_chd": "self", "lab_red_chd": "self", "rel_koran_chd": "self",
    "dem_has_chd": "self", "dem_has_prtnr": "self", "dem_prtnr_lat": "self", "dem_prtnr_st": "self", "dem_prtnr_cores": "self",
    "dem_prtnr_reun": "self", "dem_chd_reun": "self", "dem_chd_abroad": "self", "dem_prtnr_reun_when": "self", "dem_prtnr_hrs_want": "self",
    "fam_chd_higher_ed": "self", "att_chd_frnd_orig": "self", "att_chd_prtnr_orig": "self", "dem_prtnr_mar": "self",
}
def subject_of(r):
    t, lab = r["target"], r["label_en"]
    if t in SUBJECT_OVERRIDE: return SUBJECT_OVERRIDE[t]
    if t.startswith("id_"): return "identifier"
    if t.startswith("svy_"): return "interview"
    if t.startswith("hh_") or r["scope"] == "household": return "household"
    if re.match(r"^(att_chd|att_fam|att_gr|fam_val|fam_par_att|fam_noleave|fam_frstchd|fam_futchd|fam_div|fam_care)", t): return "self"
    if "selchd" in t or re.match(r"^fam_chd(beh|_spt|_sport|_rel5|_sex|_byr|_res|_seen|_cont|_help|_adv)", t): return "selected child"
    if re.search(r"_prtnr(_|$)|prtnr_", t): return "partner"
    if re.search(r"_chd(_|$)|_nchd|chd_", t) and re.match(r"^(Sex|Age|Where|Number of children|Birth|Child|Has children)", lab): return "child"
    if re.search(r"_fa(_|$)|_ma(_|$)|_par(_|$)|parents?", t) and re.match(r"^(Country of birth of (father|mother)|Highest .* (father|mother)|Father|Mother|Parent)", lab): return "parent"
    if "Father" in lab[:8] or "Mother" in lab[:8] or "father" in lab[:30] or "mother" in lab[:30]: return "parent"
    return "self"
WMATCH = {(w["survey"], w["target"]): w["match"] for w in wording_rows}
HHKEYS = [s_["key"] for s_ in INCLUDED if s_["structure"] != "flat"]

# ------------------------------------------------------------------ acquisition metadata per source (v0.4.3, codebook-table review)
# How the value was obtained ('acquisition'), whether a prompt was shown or read to the respondent ('respondent_facing'),
# who supplied the information ('supplied_by') and whom it describes ('describes').  Linking a source to a questionnaire
# block does not establish that anything was asked: an interviewer who records sex silently, rates Dutch proficiency or
# notes the interview language supplies the information her/himself; [SAMPLE DATA] fields come from the sample frame;
# coded variables are processed from inputs.  Rules are phrase-based and deliberately narrow (an 'ENQ.:' note attached to a
# real question does not make the item interviewer-acquired); declared cases override them (ACQ_OVERRIDES, written to
# crosswalks/acquisition_overrides.csv).  Rows the rules cannot settle are listed in crosswalks/acquisition_review.csv.
ACQ_OVERRIDES = SV.ACQ_OVERRIDES             # surveys/<key>.py: ACQ_OVERRIDES
write("acquisition_overrides.csv", [dict(survey=a, source_var=b, acquisition=c, respondent_facing=d, supplied_by=e, note=f, instruction_text=g) for a, b, c, d, e, f, g in ACQ_OVERRIDES],
      ["survey", "source_var", "acquisition", "respondent_facing", "supplied_by", "note", "instruction_text"])
ACQ_PHRASES = [   # applied only when the row has no respondent prompt, or its prompt is itself an 'ENQ.:' instruction
    (r"stel vast hoe goed|hoe goed .{0,40}begrepen|stel vast in hoeverre",                          "interviewer assessment"),
    (r"stel vast of (de )?respondent .{0,30}hoofddoek",                                              "interviewer observation"),
    (r"in welke taal (is|wordt) het gesprek|dag en datum van het interview|dienen niet aan de respondent", "interview administration"),
    (r"(noteer|vul)( het)?( stilzwijgend)? geslacht|hoeft u niet te vragen|stilzwijgend",             "interviewer recording (not asked)"),
]
RE_NOASK = re.compile(r"stilzwijgend|hoeft u niet te vragen|stel vast hoe goed|\[SAMPLE DATA\]|dienen niet aan de respondent", re.I)
ACQ_REVIEW = []
def acquisition_of(w, subject):
    m = w["match"]; text = " ".join([w["question_text"], w["instruction"], w["intro"], w["routing"]])
    for svy, pat, acq, rf, sup, note, itext in ACQ_OVERRIDES:
        if svy == w["survey"] and re.search(pat, w["source_var"]):
            if itext: w["instruction"], w["question_text"] = itext, ""
            return acq, rf, sup
    if m == "none (registry/administrative)": return "registry/sample data", 0, "registry / survey administration"
    if m == "none (registry/constructed)" and re.search(r"sample ?data|\bGBA\b|\bBRP\b|registr|\bCBS\b|\bSSB\b", w["label_nl"], re.I):
        return "registry/sample data", 0, "sample frame / population register (according to the data label)"
    if m in ("none (constructed)", "none (registry/constructed)", "derived", "heading"): return "derived/coded", 0, "constructed by the data producer from survey or registry inputs (see source definition)"
    if m == "none": return "unknown (no questionnaire item located)", 0, ""
    if re.search(r"\[SAMPLE DATA\]", text): return "registry/sample data", 0, "sample frame / registry"
    no_prompt = not w["question_text"].strip() and not w["item_text"].strip()
    enq_prompt = bool(re.match(r"^\(?(ENQ|Enq)\.?:", w["question_text"].strip()))
    if no_prompt or enq_prompt:
        for pat, acq in ACQ_PHRASES:
            if re.search(pat, text, re.I): return acq, 0, "interviewer"
        if no_prompt: return "question text not located", 0, ""
        ACQ_REVIEW.append(dict(survey=w["survey"], source_var=w["source_var"], target=w["target"], question_text=w["question_text"][:200], instruction=w["instruction"][:200],
                               issue="prompt is an interviewer instruction without a classifying phrase; kept respondent-facing"))
    if subject in ("partner", "child", "selected child", "parent"): return f"proxy report (respondent about the {subject})", 1, "respondent"
    if subject == "household": return "respondent report (about the household)", 1, "respondent"
    return "respondent report", 1, "respondent"
def supplied_by_text(w, r, sup):
    key = w["survey"]
    if key not in HHKEYS or not sup or sup.startswith(("constructed", "registry", "sample")): return sup
    files = r[f"files_{key}"]
    if r["scope"] == "household": return f"{sup} (household questionnaire, head of household), merged onto all members"
    # the asked_to declaration decides before file membership (follow-up audit of v0.4.8: 74 of 75 declared items still
    # read 'main questionnaire for heads, mini questionnaire for other members' because the variable sits in the pp file)
    who = ASKED_TO.get((w["target"], key), ("",))[0]
    if who == "heads": return f"{sup} (main questionnaire: heads of household only; other members were not asked)"
    if who == "members": return f"{sup} (mini questionnaire: interviewed members other than the head only; heads were not asked)"
    if files == "hh": return f"{sup} (main questionnaire: heads of household)"
    if "ro" in files: return f"{sup} for the cited item; roster members not interviewed: the head of household's roster report; interviewed members: the mini questionnaire"
    if "pp" in files: return f"{sup} (main questionnaire for heads, mini questionnaire for other interviewed members)"
    return sup
VM_BY_T = {r["target"]: r for r in vm_rows}
for w in wording_rows:
    r = VM_BY_T[w["target"]]; subj = subject_of(r)
    acq, rf, sup = acquisition_of(w, subj)
    w["acquisition"], w["respondent_facing"], w["supplied_by"], w["describes"] = acq, rf, supplied_by_text(w, r, sup), subj
    if rf == 0 and w["question_text"]:
        if acq == "registry/sample data":                     # field label shown to the interviewer / in the script, not a prompt
            w["source_definition"] = "; ".join(x for x in [f"Printed field: '{w['question_text']}'", w["source_definition"]] if x)
        else:                                                 # the 'prompt' was an instruction: show it as such, once
            w["instruction"] = "; ".join(dict.fromkeys(x for x in [w["question_text"]] + re.split(r";\s*", w["instruction"]) if x))
        w["question_text"] = ""
    if acq == "registry/sample data" and w["source_definition"].startswith("Registry or constructed field"):
        w["source_definition"] = f"Sample/registry field according to the data label ('{w['label_nl']}'); no questionnaire item"
write("acquisition_review.csv", ACQ_REVIEW, ["survey", "source_var", "target", "question_text", "instruction", "issue"])
# ---- derived partner sources of the household surveys (v0.4.3 follow-up, points 1-2): the relationship layer fills the
# partner variables of SPVA/SPVN from the linked partner's own record; those surveys get a table column of their own that
# names the base field, the link operation, the applicable records and the limits, and inherits the base field's
# acquisition and reporter (an interviewer-recorded base field stays interviewer-recorded; a coded one stays coded).
WR_BY_TS = {}
for w in wording_rows: WR_BY_TS.setdefault((w["target"], w["survey"]), []).append(w)
LINK_RECORDS = ("heads of household and their co-resident partners (the other head/partner member of the roster, id_prtnr). .c = no co-resident partner record; "
                ".d = other household members (relationship not identifiable), and partners listed in the roster but not interviewed where the base item needs an "
                "interview - the base field's own missing tags are kept otherwise (roster demography such as sex, age and country of birth is available for roster-only partners)")
LINK_RULES = {"has_prtnr_roster": "co-resident link -> 1; LAT partner without a link (dem_prtnr_lat = 1) -> 1; identifiable head/partner without link or LAT partner -> 0; other household members -> .d",
              "prtnr_cores_roster": "co-resident link -> 1; LAT partner without a link (dem_prtnr_lat = 1) -> 0; identifiable head/partner without link or LAT partner -> .c; other household members -> .d"}
n_derived = 0
for r in vm_rows:
    d = r["derive"]; m = re.search(r"partner_copy:([a-z0-9_]+)", d)
    base = m.group(1) if m else None
    if not base and d not in ("has_prtnr_roster", "prtnr_cores_roster"): continue
    for key in HHKEYS:
        if r[f"src_{key}"]:
            for w in WR_BY_TS.get((r["target"], key), []):          # head-reported source exists: the copy fills the partner's row only
                w["source_definition"] = "; ".join(x for x in [w["source_definition"], f"partner's row: copied from the head's own `{base}` through the roster link id_prtnr (relationship layer)"] if x)
            continue
        if base:
            brows = WR_BY_TS.get((base, key), [])
            bsrc = r_base = VARS_BY_T.get(base)
            srcs = r_base[f"src_{key}"] if r_base else ""
            bacq = "; ".join(dict.fromkeys(b["acquisition"] for b in brows)) or "derived/coded"
            bsup = "; ".join(dict.fromkeys(b["supplied_by"] for b in brows)) or "see the base field"
            acq = f"linked partner record: {bacq}"
            sup = f"taken from the linked partner's record (id_prtnr); the base field's reporter applies: {bsup}"
            sdef = (f"Derived ({d}): the linked partner's own value of `{base}`" + (f" (source {' | '.join('`' + x + '`' for x in src_parts(srcs))} in this survey)" if srcs else "") +
                    f", copied through the roster link; no separate partner question was asked. Applicable records: {LINK_RECORDS}. Coding: that of `{base}`.")
            cats = "; ".join(dict.fromkeys(b["answer_options"] for b in brows if b["answer_options"]))
            vl = "; ".join(dict.fromkeys(b["value_labels_nl"] for b in brows if b["value_labels_nl"]))
        else:
            acq = "relationship-derived (roster link and the living-apart-together question)"
            sup = "computed from the household roster (link id_prtnr, head of household's listing) and the respondent's answer to the LAT question (dem_prtnr_lat); not copied from a partner record"
            sdef = (f"Derived ({d}): {LINK_RULES[d]}. Computed for heads of household and their partners from the roster link id_prtnr and dem_prtnr_lat, "
                    "including cases with no partner record; no separate question.")
            srcs, cats, vl = "", "", ""
        wording_rows.append(dict(target=r["target"], survey=key, source_var=(" | ".join(src_parts(srcs)) if srcs else "id_prtnr"), match="derived (partner record)", respondent_facing=0,
            acquisition=acq, supplied_by=sup, describes=subject_of(r), instrument="", qid="", capi_qid="", block="", split_half="", routing="", routing_gates="", routing_note="",
            routing_skip="", routing_script="", instruction="", randomization="", intro="", question_text="", item_text="", format="", answer_options=cats, subitems="",
            source_definition=sdef, label_nl="", value_labels_nl=vl, block_text=""))
        n_derived += 1
print(f"  derived partner-source rows for the household surveys: {n_derived}")
# ---- questionnaire codes vs data-file codes (v0.4.3 follow-up 12:37, point 1): the same number can mean different things in
# the printed categories and in the released value labels (SPVN BURGST: questionnaire 2 = 'ongehuwd samenwonend', data file
# 2 = 'gescheiden').  Harmonization always works from the data-file codes; the codebook must show both and say so.
def _norm_lab(x):
    x = re.sub(r"\(.*?\)", " ", x.lower()); x = re.sub(r"[^a-z0-9àâäéèêëïîôöùûüç ]+", " ", x)
    x = x.replace("mee oneens", "niet mee eens").replace("oneens", "niet mee eens")        # negated agreement wordings are equivalent
    return re.sub(r"\s+", " ", x).strip()
def _codes(txt):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"(?:^|;\s*)(-?\d+)=([^;]*)", txt)}
def _lmatch(a, b):
    """Lenient label match: equal, prefix (abbreviated data labels), or half the word stems in common."""
    if not a or not b: return False
    if a == b or (len(a) >= 5 and len(b) >= 5 and (a.startswith(b) or b.startswith(a))): return True
    ta, tb = {t[:5] for t in a.split()}, {t[:5] for t in b.split()}
    return len(ta & tb) / max(1, len(ta | tb)) >= 0.5
CODE_DIFFS = []
for w in wording_rows:
    if not w["answer_options"] or not w["value_labels_nl"] or w["match"] == "derived (partner record)": continue
    pc, dc = _codes(w["answer_options"]), _codes(w["value_labels_nl"])
    pn = {c: _norm_lab(l) for c, l in pc.items() if int(c) >= 0 and "<" not in l and "?" not in l}
    dn = {c: _norm_lab(l) for c, l in dc.items() if int(c) >= 0}
    diff = []
    for c in sorted(set(pn) & set(dn), key=lambda x: int(x)):
        if _lmatch(pn[c], dn[c]): continue
        # a different wording is harmless (abbreviations, 'genoemd'); a meaning that belongs to ANOTHER code is not:
        # the printed label re-appears under a different data-file code, or vice versa (permuted or shifted code lists)
        if any(c2 != c and _lmatch(pn[c], dn[c2]) for c2 in dn) or any(c2 != c and _lmatch(dn[c], pn[c2]) for c2 in pn):
            diff.append((c, pc[c], dc[c]))
    if diff:
        w["code_meaning_note"] = "codes " + ", ".join(c for c, _, _ in diff) + " mean something else in the data file than in the questionnaire (" + \
            "; ".join(f"{c}: questionnaire '{a[:40]}' vs data file '{b[:40]}'" for c, a, b in diff[:4]) + ("; ..." if len(diff) > 4 else "") + \
            "); the value map works from the data-file codes"
        CODE_DIFFS.extend(dict(target=w["target"], survey=w["survey"], source_var=w["source_var"], code=c, printed_label=a, data_label=b) for c, a, b in diff)
    else:
        w["code_meaning_note"] = ""
for w in wording_rows: w.setdefault("code_meaning_note", "")
write("code_meaning_differences.csv", CODE_DIFFS, ["target", "survey", "source_var", "code", "printed_label", "data_label"])
print(f"  questionnaire vs data-file code meanings: {len(CODE_DIFFS)} differing codes in {sum(1 for w in wording_rows if w['code_meaning_note'])} source rows -> crosswalks/code_meaning_differences.csv")
for _k, _v in (("spvn2003", "BURGST"), ("las2004", "ETNGRP"), ("las2004", "GEBED"), ("sim2006", "KANSNEE")):
    _expect(_w(_k, _v) is not None and _w(_k, _v)["code_meaning_note"] != "", f"{_k} {_v}: differing code meanings between questionnaire and data file are flagged")
if _fails:
    print("  CODE-MEANING CHECK FAILURES:"); [print("    - " + f) for f in _fails]
    raise SystemExit("code-meaning checks failed")
print("  acquisition:", dict(collections.Counter(w["acquisition"] for w in wording_rows)), f"; {len(ACQ_REVIEW)} rows for review")
# validations (review point 12): no-ask / assessment / sample-data phrases never remain respondent-facing; recording options
# survive instruction-only blocks; English source definitions never sit in the Dutch prompt
_bad = [f"{w['survey']}:{w['source_var']}" for w in wording_rows if w["respondent_facing"] == 1 and RE_NOASK.search(w["question_text"] + " " + (w["instruction"] if not w["question_text"].strip() else ""))]
_expect(not _bad, "items marked 'do not ask' / 'record silently' / 'interviewer assess' / 'SAMPLE DATA' are not respondent-facing: " + ", ".join(_bad[:10]))
for _k in ("sim2006", "sing2009", "las2004", "sim2011"):
    r_ = _w(_k, "GESLACHT"); _expect(r_ and r_["answer_options"].count("=") == 2 and r_["respondent_facing"] == 0, f"{_k} sex: both recording categories kept, not respondent-facing")
_expect(all(not re.match(r"^(No questionnaire item|Constructed variable|\[Coded|\[Section heading)", w["question_text"]) for w in wording_rows), "no English source description in the prompt column")
if _fails:
    print("  ACQUISITION CHECK FAILURES:"); [print("    - " + f) for f in _fails]
    raise SystemExit("acquisition metadata checks failed")
write("wording.csv", wording_rows, ["target", "survey", "source_var", "match", "respondent_facing", "acquisition", "supplied_by", "describes", "instrument", "qid", "capi_qid",
                                    "block", "split_half", "routing", "routing_gates", "routing_note", "routing_skip", "routing_script", "instruction", "randomization", "intro", "question_text", "item_text",
                                    "format", "answer_options", "subitems", "source_definition", "label_nl", "value_labels_nl", "code_meaning_note", "block_text"])

def reporter_of(r, key, subject):
    src = r[f"src_{key}"]; derive = r["derive"]
    if not src:
        if derive and (f"partner_copy" in derive or derive in ("has_prtnr_roster", "prtnr_cores_roster")) and key in HHKEYS:
            sups = [w["supplied_by"] for w in wording_rows if w["survey"] == key and w["target"] == r["target"] and w["match"] == "derived (partner record)"]
            return sups[0] if sups else "taken from the linked partner's record (id_prtnr)"
        if derive and key in HHKEYS and derive in ("id_prtnr",): return "constructed from the roster"
        if derive: return "constructed"
        return ""
    if r["target"].endswith("_reg") or r["target"].endswith("_cbs"): return "registry (CBS)"
    sups = list(dict.fromkeys(w["supplied_by"] for w in wording_rows if w["survey"] == key and w["target"] == r["target"] and w["supplied_by"]))
    if sups: return "; ".join(sups)
    m = WMATCH.get((key, r["target"]), "")
    if m.startswith("none (constructed") or m in ("derived", "heading") or m == "none (registry/constructed)": return "constructed (SCP/ISEO/CBS) from the respondent's answers"
    if m == "none (registry/administrative)": return "survey administration / registry"
    if re.search(r"interviewer|rated by the interviewer|observation", r["label_en"], re.I) and subject in ("self", "partner"): return "interviewer"
    if key in HHKEYS:
        files = r[f"files_{key}"]
        if r["scope"] == "household": return "head of household (household questionnaire), merged onto all members"
        if files == "hh": return "self (head of household; main questionnaire)"
        if "ro" in files: return "head of household (roster) for non-interviewed members; self for interviewed members"
        if subject in ("partner", "child", "selected child", "parent"): return "self (head or member) about the %s" % subject
        return "self"
    if subject in ("partner", "child", "selected child", "parent"): return "respondent (proxy report about the %s)" % subject
    return "self"
def avail_of(r, key):
    if r[f"src_{key}"]: return "collected"
    d = r["derive"]
    if not d: return "not collected"
    if d.startswith("cpi2015:"):
        base = re.sub(r"^cpi2015:|@.*$", "", d); br = next((x for x in vm_rows if x["target"] == base), None)
        return "derived (CPI-deflated base amount)" if br and br.get(f"src_{key}") else "not collected"
    if "partner_copy" in d or d in ("has_prtnr_roster", "prtnr_cores_roster", "id_prtnr"): return "derived from the roster link" if key in HHKEYS else "not collected"
    if d == "kl9_route": return "not collected"                                     # recode of the source only
    if d in ("id_person", "id_hh", "svy_id", "svy_name", "svy_year", "svy_resptype", "routing_mig", "brthcntry_src", "age_cat3"):
        return "derived"
    return "derived where the inputs exist"
for r in vm_rows:
    r["subject"] = subject_of(r)
    for key in KEYS:
        r[f"avail_{key}"] = avail_of(r, key)
        r[f"reporter_{key}"] = reporter_of(r, key, r["subject"]) if r[f"avail_{key}"] != "not collected" else ""
vm_fields += ["subject"] + [f"reporter_{k}" for k in KEYS] + [f"avail_{k}" for k in KEYS]
write("variable_map.csv", vm_rows, vm_fields)
print("  subject:", dict(collections.Counter(r["subject"] for r in vm_rows if r["include_main"] == 1)))
# plausibility of the automatic links: token overlap between the data label and the questionnaire text (printed for review)
def toks(x): return set(w for w in re.findall(r"[a-zà-ü]{4,}", x.lower()) if w not in {"vraag", "deze", "voor", "heeft", "hebt", "bent", "welke", "wordt", "worden", "over", "naar", "niet", "meer", "zich", "deel", "uw"})
weak = []
for r in wording_rows:
    if r["match"] in ("none", "manual") or r["match"].startswith("none"): continue
    a = toks(r["label_nl"]); b = toks(r["question_text"] + " " + r["item_text"] + " " + r["subitems"])
    if a and b and not (a & b):
        weak.append(f"{r['survey']}:{r['source_var']}->{r['qid']} [{r['match']}] label='{r['label_nl'][:50]}' q='{(r['question_text'] + ' ' + r['item_text'])[:60]}'")
print(f"  wording links with no word in common between data label and questionnaire text ({len(weak)}; review):")
for w in weak: print("    " + w)
print(f"  wording: {sum(1 for r in wording_rows if r['qid'])} of {len(wording_rows)} source variables linked to a questionnaire item, "
      f"{sum(1 for r in wording_rows if not r['qid'] and r['match'] != 'none')} documented as constructed/registry/administrative; "
      f"{len(unlinked)} unlinked (main-file targets): {', '.join(unlinked[:40])}{' ...' if len(unlinked) > 40 else ''}")

design = SV.DESIGN                   # surveys/<key>.py: DESIGN (codebook section 3.2)
write("questionnaire_design.csv", design, ["survey", "aspect", "text"])

# municipalities: survey code -> CBS code (2006 list, External/Municipality codes/2006-gemeenten-op-code.xls)
MUN = SV.MUNICIPALITIES              # surveys/<key>.py: MUNICIPALITIES
mun_rows = []
for (k, code), (cbs, name) in MUN.items():
    srclab = source_vars[(k, "GEMEENTE")]["vl"].get(code, "")
    mun_rows.append(dict(survey=k, source_code=code, source_label=srclab, cbs_code=cbs, cbs_name=name, code_list="CBS gemeenten 2006"))
write("municipalities.csv", mun_rows, ["survey", "source_code", "source_label", "cbs_code", "cbs_name", "code_list"])

# CPI: chain annual rates of change into an index with 2015 = 100
cpi_path = [os.path.join(ROOT, "External", "CPI", f) for f in os.listdir(os.path.join(ROOT, "External", "CPI")) if f.endswith(".csv")][0]
rates = {}
with open(cpi_path, encoding="utf-8-sig") as f:
    for row in csv.reader(f, delimiter=";"):
        if row and re.match(r"^\d{4}$", row[0]) and row[1] not in ("", None):
            rates[int(row[0])] = float(row[1])
years = sorted(rates)
idx = {years[0]: 100.0}
for y in years[1:]:
    idx[y] = idx[y - 1] * (1 + rates[y] / 100)
base = idx[2015]
cpi_rows = [dict(year=y, rate_pct=rates[y], cpi_2015=round(idx[y] / base * 100, 4)) for y in years]
write("cpi.csv", cpi_rows, ["year", "rate_pct", "cpi_2015"])

from renames_v020 import GLOSSARY, BATTERIES
from glossary_v030 import GLOSSARY_ADD, BATTERIES_ADD
from glossary_v040 import GLOSSARY_ADD as GLOSSARY_ADD4, BATTERIES_ADD as BATTERIES_ADD4
gl_rows = [dict(kind="abbreviation", key=k, description=v) for k, v in {**GLOSSARY, **GLOSSARY_ADD, **GLOSSARY_ADD4}.items()] + \
          [dict(kind="battery", key=k, description=v) for k, v in {**BATTERIES, **BATTERIES_ADD, **BATTERIES_ADD4}.items()]
write("name_glossary.csv", gl_rows, ["kind", "key", "description"])

# ---- value-map review (v0.4.7, from the restricted component): every value-map row read with its source label against the
# target label - two-valued targets, cross-survey copies with differing labels and range labels must be read and signed in
# crosswalks/label_approvals.csv (hand-maintained, like comparability_review.csv); exit status 1 stops the build here
import subprocess
print("\nvalue-map review (code/tools/value_map_review.py):")
rc = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "code", "tools", "value_map_review.py"), CW]).returncode
if rc != 0:
    sys.exit("crosswalk build stopped: the value-map review failed - read the rows it lists against their labels and sign them in crosswalks/label_approvals.csv")

print(f"\n{len(VARS)} target variables ({sum(r['include_main'] for r in VARS)} in main file), "
      f"{len(source_vars)} survey-specific source variables all claimed; {len(VMAP)} value-map rows; {len(VALUESETS)} value sets.")
print("CPI 2002:", round(idx[2002] / base * 100, 2), " 2003:", round(idx[2003] / base * 100, 2), " 2015: 100  2020:", round(idx[2020] / base * 100, 2) if 2020 in idx else "n/a")
