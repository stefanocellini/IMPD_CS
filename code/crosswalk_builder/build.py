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

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
CW = os.path.join(ROOT, "crosswalks")
os.makedirs(CW, exist_ok=True)

SURVEYS = [
    dict(svy_id=1, svy_name="SPVA1988", svy_year=1988, status="not yet included", title="Sociale Positie en Voorzieningengebruik Allochtonen 1988"),
    dict(svy_id=2, svy_name="SPVA1991", svy_year=1991, status="not yet included", title="Sociale Positie en Voorzieningengebruik Allochtonen 1991"),
    dict(svy_id=3, svy_name="SPVA1994", svy_year=1994, status="not yet included", title="Sociale Positie en Voorzieningengebruik Allochtonen 1994"),
    dict(svy_id=4, svy_name="SPVA1998", svy_year=1998, status="not yet included", title="Sociale Positie en Voorzieningengebruik Allochtonen 1998"),
    dict(svy_id=5, svy_name="SPVA2002", svy_year=2002, status="included", key="spva2002", structure="hh_pp_ro",
         title="Sociale positie en voorzieningengebruik van allochtonen 2002 (SPVA 2002)", dans_id="P1684", doi="10.17026/dans-xdt-cynn", access="open",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans", fieldwork="Veldkamp Marktonderzoek (2002-2003); SEOR/ISEO & SCP", mode="Face-to-face (PAPI), household sample",
         zipfile="Surveys/SPVA 2002.zip", file_hh="dat/p1684a.por", file_pp="dat/p1684b.por", file_ro="dat/p1684c.por", file_main="", encoding="cp1252",
         id_var="", weight_var="WEEG", sysmis_tag="",
         missing_scheme="system-missing + labelled codes 9/99/999/9999 'geen informatie', 7/97 'weet niet'"),
    dict(svy_id=6, svy_name="SPVN2003", svy_year=2003, status="included", key="spvn2003", structure="hh_pp_ro",
         title="Sociale positie en voorzieningengebruik van allochtonen 2003 - refugee groups (SPVA/SPVN 2003)", dans_id="P1753", doi="10.17026/dans-x7u-vkfm", access="open",
         groups="Afghans; Iraqis; Iranians; former Yugoslavs; Somalis", fieldwork="Veldkamp (2003); ISEO Erasmus University", mode="Face-to-face (CAPI), household sample",
         zipfile="Surveys/SPVN 2003.zip", file_hh="spvnhh.sav", file_pp="spvntt.sav", file_ro="spvnag.sav", file_main="", encoding="latin1",
         id_var="", weight_var="WEEG", sysmis_tag="",
         missing_scheme="explicit codes -7 sysmis, -4 missing, -3 don't know, -2 refusal; labelled 997/9997/0 'weet niet'; 'Onbekend' in code lists"),
    dict(svy_id=7, svy_name="LAS2004", svy_year=2004, status="included", key="las2004", structure="flat",
         title="Leefsituatie Allochtone Stedelingen 2004-2005 (LAS 2004/05)", dans_id="easy-dataset:40215", doi="10.17026/dans-zqg-uqn8", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; native Dutch reference sample (50 largest municipalities)",
         fieldwork="Veldkamp with TNS NIPO interviewers (Oct 2004 - May 2005); SCP", mode="Face-to-face (CAPI); person sample 15-64 from the GBA of the 50 largest municipalities",
         zipfile="Surveys/LAS 2004 2005.zip", file_hh="", file_pp="", file_ro="", file_main="LAS Leefsituatie Allochtone Stedelingen 2004-2005/LAS 2005.por", encoding="latin1",
         id_var="INTNR", weight_var="WEEGTOT", sysmis_tag="c",
         missing_scheme="explicit codes -7 question block not asked, -5 not applicable (incl. system missing), -3 don't know, -2 refusal/no information, -9 'nvt: autochtoon'; 9/99 'weet niet/geen antwoord' in code lists"),
    dict(svy_id=8, svy_name="SIM2006", svy_year=2006, status="included", key="sim2006", structure="flat",
         title="Survey Integratie Minderheden 2006 (SIM 2006)", dans_id="easy-dataset:40304", doi="10.17026/dans-2z9-6eqc", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; native Dutch reference sample",
         fieldwork="Veldkamp / TNS NIPO, ERC for Turkish and Moroccan interviews (Mar 2006 - Jan 2007); SCP", mode="Face-to-face (CAPI); nationwide person sample 15+ from the GBA (CBS, at least 10 addresses per municipality)",
         zipfile="Surveys/SIM 2006.zip", file_hh="", file_pp="", file_ro="", file_main="SIM Survey Immigration Minorities 2006/SIM2006_c1_dans230909 edit_1_beveiligd.sav", encoding="utf-8",
         id_var="impd_rownum", weight_var="WEEGTOT", sysmis_tag="c",
         missing_scheme="explicit codes -5 not applicable, -3 don't know, -2 refusal/no answer, -7 not in questionnaire, -8 wrongly unanswered, -1 (undocumented), -9 'nvt: autochtoon'; system missing = routing"),
    dict(svy_id=9, svy_name="SING2009", svy_year=2009, status="included", key="sing2009", structure="flat",
         title="Survey Integratie Nieuwe Groepen 2009 (SING 2009), CBS-protected public version", dans_id="easy-dataset:51530", doi="10.17026/dans-xnn-ky48", access="request_permission",
         groups="Afghans; Iraqis; Iranians; Somalis; Poles; Chinese; native Dutch reference sample",
         fieldwork="Veldkamp / TNS NIPO (Feb 2009 - Feb 2010); SCP; CBS sample and statistical protection", mode="Face-to-face (CAPI); person sample 15+ from the GBA; only the questions listed in the deposit's READ ME are released, years and durations in classes",
         zipfile="Surveys/SING 2009.zip", file_hh="", file_pp="", file_ro="", file_main="SINGDANS veilig.por", encoding="latin1",
         id_var="impd_rownum", weight_var="WEEGHERK", sysmis_tag="c",
         missing_scheme="system missing = routing / not released; labelled codes 7/97 'weet niet' or 'geen antwoord, wil niet zeggen', 8/9/98/99 'niet van toepassing'"),
    dict(svy_id=10, svy_name="SIM2011", svy_year=2011, status="included", key="sim2011", structure="flat",
         title="Survey Integratie Minderheden 2011 (SIM 2011), DANS version V3", dans_id="easy-dataset:67677", doi="10.17026/dans-2a2-77kp", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; native Dutch reference sample",
         fieldwork="GfK with Labyrinth interviewers (Nov 2010 - Apr 2011); SCP; CBS statistical protection (mu-Argus)", mode="Face-to-face (CAPI) main survey (the mixed-mode experiment is not in this deposit); person sample 15+ from the GBA",
         zipfile="Surveys/SIM 2011.zip", file_hh="", file_pp="", file_ro="", file_main="SIM 2011V3.sav", encoding="windows-1252",
         id_var="volgnummer", weight_var="weegtot", sysmis_tag="d",
         missing_scheme="explicit codes -5 not applicable, -3 don't know/no answer, -2 refusal, -4 missing, -1 (undocumented), -9 'nvt: autochtoon'; 9 'niet van toepassing' in some code lists"),
    dict(svy_id=11, svy_name="SIM2015", svy_year=2015, status="included", key="sim2015", structure="flat",
         title="Survey Integratie Minderheden 2015 (SIM 2015), CCF public version v4", dans_id="easy-dataset:239464", doi="10.17026/dans-x63-dq58", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; Somalis; Poles (1st generation, registered 2004+); native Dutch reference sample",
         fieldwork="TNS NIPO/Veldkamp and Labyrinth (Jan-Jul 2015); SCP", mode="Sequential mixed mode: CAWI, then CAPI; person sample 15+ from the BRP",
         zipfile="Surveys/SIM 2015.zip", file_hh="", file_pp="", file_ro="", file_main="Data/SIM2015_CCF_v4.sav", encoding="utf-8",
         id_var="volgnummer", weight_var="eindgewicht", sysmis_tag="d",
         missing_scheme="explicit codes -2 blanc (routing), -3 don't know/no answer, -5 not applicable, -1/98 refusal, -4 no education, -6/96 'diversen', -7 sysmis; label 2147483622 '[-2]Blanc' never occurs"),
    dict(svy_id=12, svy_name="SIM2020", svy_year=2020, status="included", key="sim2020", structure="flat",
         title="Survey Integratie Minderheden 2020 (SIM 2020), CCF public version v2", dans_id="easy-dataset:259562", doi="10.17026/dans-26h-xn4n", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Caribbean Dutch (incl. BES); Somalis; Poles (1st generation, registered 2004+); Iranians; native Dutch reference sample",
         fieldwork="Labyrinth Onderzoek & Advies (Mar 2020 - Jan 2021, during covid); SCP", mode="CAWI (90%) with CAPI follow-up for five groups (10%, incl. 15 video interviews); person sample 15+ from the BRP; split-half questionnaire",
         zipfile="Surveys/SIM 2020.zip", file_hh="", file_pp="", file_ro="", file_main="SIM2020 CCF v2.sav", encoding="utf-8-double",
         id_var="Volgnummer", weight_var="eindgewicht", sysmis_tag="d",
         missing_scheme="explicit codes -5 not applicable/routing, -3 don't know, -2 refusal, -4 no answer, -6 don't know/no answer, -1 Farsi questionnaire error; 9 'Anders/Refusal/Don't know' in coarsened (_kl) variables; 92 'anders'"),
]
INCLUDED = [s for s in SURVEYS if s["status"] == "included"]
# sha256 of the DANS zip files as downloaded (computed on the project laptop, 29 Oct 2026; recomputed when the zip is present)
ZIP_SHA256_KNOWN = {
    "spva2002": "91166a194661265f0efafc97828639a8f41b1ef930639adecb00b99794a9d10e", "spvn2003": "96556f53090b5e84fcd3d6aa29c43339391d9363c4b9984a5e2334147cd48011",
    "las2004": "cb67573d71e1d645e41578f1811517a0ddd2d9e7b2d4a3b7ca8807ca0e93a0bc", "sim2006": "5c666899708dcc2900dbfa1861bfaedcb9faa9ae2aac05974664491e61001d31",
    "sing2009": "b4d3aea4cf56a8e7671e1dc5203878cf3764b30024b29aeb4b664b25304bb774", "sim2011": "78d8bf29ef6378ed654429c13540994cf9d53e02e06363644c6827f81ed81baa",
    "sim2015": "5269492b473f786ed80effa7288bcf223feb20d4d1a65dccadf0dabf1ea3bde5", "sim2020": "cc4518f30693f382739982db33e76cc338fa05a339b1266f70d9aa8a8533ea95",
}
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
ELIG = {   # eligible sample / target population and weight guidance per survey (codebook section 1, README)
    "spva2002": ("Households of Turkish, Moroccan, Surinamese and Antillean/Aruban origin in 13 municipalities (ISEO; the native comparison sample is not in the DANS deposit). Rows: all roster members; interviewed persons = heads (main questionnaire) and members aged 12+ (mini); children and non-interviewed members are roster-only records with head-reported demography.",
                 "svy_wgt: ISEO design/post-stratification weight of the household (merged onto every member). Not a population weight across surveys; observations are clustered within households (id_hh)."),
    "spvn2003": ("Households of Afghan, Iraqi, Iranian, former-Yugoslav and Somali origin in 12 municipalities (ISEO). Same row structure as SPVA 2002.",
                 "svy_wgt: ISEO household weight; cluster on id_hh."),
    "las2004":  ("Persons aged 15-64 of Turkish, Moroccan, Surinamese, Antillean/Aruban and native Dutch origin in the 50 largest municipalities (GBA sample, CBS); 228 persons belong to an oversample of working men and women (svy_oversample).",
                 "svy_wgt (weegtot): Veldkamp/SCP weight to the population of the 50 largest municipalities; svy_wgt_grp (weegherk): weight within origin group (mean 1 per group); svy_wgt_raise (ophtot): raising factor to population totals. Diary analyses: tim_wgt / tim_wgt_corr."),
    "sim2006":  ("Persons aged 15+ of Turkish, Moroccan, Surinamese, Antillean/Aruban and native Dutch origin, nationwide GBA sample (CBS).",
                 "svy_wgt (weegtot): CBS weight to the national population of the five groups; svy_wgt_grp (weegherk): within origin group; svy_wgt_raise (ophtot): raising factor."),
    "sing2009": ("Persons aged 15+ of Afghan, Iraqi, Iranian, Somali, Chinese, Polish (short-stay, registered < 5 years) and native Dutch origin, nationwide two-stage GBA sample (CBS); partial release (see section 3).",
                 "svy_wgt = svy_wgt_grp (weegherk): within-origin-group weight, the only general weight in the deposit; svy_wgt_pool: separate weight for the short-stay Polish sample. No weight to a pooled national population is supplied."),
    "sim2011":  ("Persons aged 15+ of Turkish, Moroccan, Surinamese, Antillean/Aruban and native Dutch origin, nationwide GBA sample stratified by municipality size (CBS); main CAPI study only.",
                 "svy_wgt (weegtot): CBS weight to the national population (origin x sex, household size/marital status, municipality stratum, generation, age); svy_wgt_grp (weegherk): within origin group; svy_wgt_raise (ophtot): raising factor."),
    "sim2015":  ("Persons aged 15+ of Turkish, Moroccan, Surinamese, Antillean/Aruban, Somali, Polish (first generation registered 2004+) and native Dutch origin, nationwide BRP sample (CBS).",
                 "svy_wgt (eindgewicht): CBS calibration weight scaled to the population; svy_wgt_alt: alternative weighting model; svy_wgt_start: inverse selection probability."),
    "sim2020":  ("Persons aged 15+ of Turkish, Moroccan, Surinamese, Caribbean-Dutch, Somali, Polish (first generation registered 2004+), Iranian and native Dutch origin, nationwide BRP sample (CBS); split-half questionnaire (svy_split).",
                 "svy_wgt (eindgewicht): CBS calibration weight scaled to the population."),
}
for s_ in SURVEYS:
    s_["eligible"], s_["weights"] = ELIG.get(s_.get("key", ""), ("", ""))
SLABEL = {"spva2002": "SPVA 2002", "spvn2003": "SPVN 2003", "las2004": "LAS 2004/05", "sim2006": "SIM 2006", "sing2009": "SING 2009",
          "sim2011": "SIM 2011", "sim2015": "SIM 2015", "sim2020": "SIM 2020"}      # display names (codebook, notes)
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
missing_rules = [
    # SPVN 2003
    dict(survey="spvn2003", rule_type="code", match="-7", target=".", note="Sysmis (not applicable / routed out / not in questionnaire)"),
    dict(survey="spvn2003", rule_type="code", match="-4", target=".d", note="Missing / no information"),
    dict(survey="spvn2003", rule_type="code", match="-3", target=".a", note="Don't know"),
    dict(survey="spvn2003", rule_type="code", match="-2", target=".b", note="Refusal (wil niet zeggen)"),
    dict(survey="spvn2003", rule_type="label", match="^weet niet$", target=".a", note="Labelled don't-know codes (997, 9997, 0 in year/month variables)"),
    dict(survey="spvn2003", rule_type="label", match="^wil niet zeggen$", target=".b", note=""),
    dict(survey="spvn2003", rule_type="label", match="^onbekend$", target=".d", note="Unknown place/country in code lists (97, 997)"),
    dict(survey="spvn2003", rule_type="label", match="^(missing|geen informatie)$", target=".d", note=""),
    dict(survey="spvn2003", rule_type="label", match="^sysmis$", target=".", note=""),
    dict(survey="spvn2003", rule_type="declared", match="^(0|7|97|98|997|9997)$", target=".a", note="Declared user-missing codes that follow the ISEO don't-know convention (0 in year/month/amount items, 7, 97/997/9997, 98)"),
    dict(survey="spvn2003", rule_type="declared", match=".*", target=".d", note="Other declared user-missing codes (9/10/99/999 = no information)"),
    # SPVA 2002
    dict(survey="spva2002", rule_type="label", match="^geen informatie$", target=".d", note="Codes 9/99/999/9999/99999 where so labelled"),
    dict(survey="spva2002", rule_type="label", match="^weet niet$", target=".a", note="Codes 7/97 where so labelled"),
    dict(survey="spva2002", rule_type="declared", match="^(7|97)$", target=".a", note="SPSS user-missing codes declared in the file (source_missing.csv): ISEO convention 7/97 = don't know"),
    dict(survey="spva2002", rule_type="declared", match=".*", target=".d", note="Other declared user-missing codes (9/99/999/9999/99999 = geen informatie)"),
    # SIM 2015 (TNS NIPO conventions)
    dict(survey="sim2015", rule_type="code", match="-7", target=".", note="Sysmis in SCP-constructed variables"),
    dict(survey="sim2015", rule_type="code", match="-2", target=".c", note="'blanc': question not presented (routing) - 314,198 cells"),
    dict(survey="sim2015", rule_type="code", match="-5", target=".c", note="Niet van toepassing"),
    dict(survey="sim2015", rule_type="code", match="-3", target=".a", note="Weet niet / geen antwoord"),
    dict(survey="sim2015", rule_type="code", match="-1", target=".b", note="Wil niet zeggen"),
    dict(survey="sim2015", rule_type="code", match="-4", target=".d", note="'Missing' in SCP-constructed variables; 'geen opleiding' in education items is mapped explicitly (.c)"),
    dict(survey="sim2015", rule_type="code", match="-6", target=".d", note="'Diversen' in SCP-constructed education variables (uncodable)"),
    dict(survey="sim2015", rule_type="label", match="^blanc$", target=".c", note=""),
    dict(survey="sim2015", rule_type="label", match="^wil niet zeggen$", target=".b", note="Code 98 in huisbui"),
    dict(survey="sim2015", rule_type="label", match="^weet niet", target=".a", note="Labelled don't-know codes incl. 'weet niet \\ niet van toepassing' (99)"),
    dict(survey="sim2015", rule_type="label", match="^niet van toepassing$", target=".c", note="Codes 4 (inburgering items) and 9 (conherk)"),
    dict(survey="sim2015", rule_type="label", match="^(sysmis)$", target=".", note=""),
    dict(survey="sim2015", rule_type="label", match="^missing$", target=".d", note=""),
    dict(survey="sim2015", rule_type="label", match="^diversen$", target=".d", note="Unless mapped explicitly to an 'other' category (value_map takes precedence)"),
    # SIM 2020 (Labyrinth conventions + CCF coarsening)
    dict(survey="sim2020", rule_type="code", match="-5", target=".c", note="'nvt binnen vragenlijst': question not presented (routing, split half, group) - 476,736 cells"),
    dict(survey="sim2020", rule_type="code", match="-3", target=".a", note="Weet niet"),
    dict(survey="sim2020", rule_type="code", match="-2", target=".b", note="Wil niet antwoorden"),
    dict(survey="sim2020", rule_type="code", match="-4", target=".b", note="Geen antwoord"),
    dict(survey="sim2020", rule_type="code", match="-6", target=".a", note="Weet niet / geen antwoord / wil niet zeggen / neutraal (combined code)"),
    dict(survey="sim2020", rule_type="code", match="-1", target=".d", note="Wrong question or answer option in the Farsi questionnaire (unless mapped explicitly)"),
    dict(survey="sim2020", rule_type="label", match="refusal", target=".d", note="'Anders/Refusal/Don't know' (9) in CCF-coarsened _kl variables: other and missing cannot be separated"),
    dict(survey="sim2020", rule_type="label", match="^weet niet", target=".a", note=""),
    dict(survey="sim2020", rule_type="label", match="^niet van toepassing$", target=".c", note=""),
    # SIM 2011 (Veldkamp CAPI; CBS protection): explicit codes
    dict(survey="sim2011", rule_type="code", match="-5", target=".c", note="Niet van toepassing: question not asked (routing, group) - 537,139 cells"),
    dict(survey="sim2011", rule_type="code", match="-3", target=".a", note="Weet niet / geen antwoord"),
    dict(survey="sim2011", rule_type="code", match="-2", target=".b", note="Wil niet zeggen / geen antwoord"),
    dict(survey="sim2011", rule_type="code", match="-4", target=".d", note="Missing"),
    dict(survey="sim2011", rule_type="code", match="-1", target=".c", note="Undocumented code used where a question was not asked (persons with paid work in HFDACT/urencat; a few hours values)"),
    dict(survey="sim2011", rule_type="code", match="-9", target=".c", note="'nvt: autochtoon' (native Dutch sample)"),
    dict(survey="sim2011", rule_type="label", match="^niet van toepassing", target=".c", note="Positive codes labelled not applicable (unless mapped)"),
    dict(survey="sim2011", rule_type="label", match="^weet niet", target=".a", note=""),
    # SIM 2006 (Veldkamp): explicit codes in some variables, system-missing for most routing (surveys.csv sysmis_tag = c)
    dict(survey="sim2006", rule_type="code", match="-5", target=".c", note="'niet van toepassing'"),
    dict(survey="sim2006", rule_type="code", match="-3", target=".a", note="'weet niet'"),
    dict(survey="sim2006", rule_type="code", match="-2", target=".b", note="'wil niet zeggen/geen opgave'"),
    dict(survey="sim2006", rule_type="code", match="-7", target=".c", note="'niet in vragenlijst': item not in the questionnaire version of this group"),
    dict(survey="sim2006", rule_type="code", match="-8", target=".d", note="'ten onrechte niet beantwoord' (interview program error)"),
    dict(survey="sim2006", rule_type="code", match="-4", target=".d", note="'missing'"),
    dict(survey="sim2006", rule_type="code", match="-9", target=".c", note="'nvt: autochtoon' (native Dutch sample)"),
    dict(survey="sim2006", rule_type="label", match="^niet van toepassing|^nvt", target=".c", note="Positive codes labelled not applicable (unless mapped)"),
    dict(survey="sim2006", rule_type="label", match="^weet niet", target=".a", note=""),
    # LAS 2004/05 (Veldkamp .por): -7 block not asked, -5 nvt, -3 weet niet, -2 wil niet zeggen/geen informatie, -4 weet niet (education),
    # -9 'nvt: autochtoon'; positive 9/99/999 'weet niet / geen antwoord' codes caught by label; system-missing = routed (sysmis_tag = c)
    dict(survey="las2004", rule_type="code", match="-7", target=".c", note="'vragenblok niet gesteld' (block not asked to this group / version)"),
    dict(survey="las2004", rule_type="code", match="-5", target=".c", note="'niet van toepassing'"),
    dict(survey="las2004", rule_type="code", match="-3", target=".a", note="'weet niet'"),
    dict(survey="las2004", rule_type="code", match="-4", target=".a", note="'weet niet' (education variables)"),
    dict(survey="las2004", rule_type="code", match="-2", target=".b", note="'wil niet zeggen, geen informatie'"),
    dict(survey="las2004", rule_type="code", match="-9", target=".c", note="'nvt: autochtoon' (native Dutch sample)"),
    dict(survey="las2004", rule_type="label", match="^weet niet", target=".a", note="positive 'weet niet (\\ geen antwoord)' codes (9, 99, 999, 9999) unless mapped"),
    dict(survey="las2004", rule_type="label", match="^wil niet zeggen", target=".b", note="positive refusal codes (GEZINK 99, STEMWS 14) unless mapped: STEMINT 5 'wil niet zeggen' is a printed answer option and keeps code 5 of vote_int5"),
    dict(survey="las2004", rule_type="label", match="geen informatie|^onbekend", target=".d", note="e.g. 99 'geen informatie' in the age classes, 99 'onbekend' in burgst"),
    dict(survey="las2004", rule_type="label", match="^niet van toepassing|^nvt|niet gesteld|^sysmis|^volgt geen opleiding|^geen vragenlijst", target=".c", note=""),
    # SING 2009 (Veldkamp .por, CBS-protected): positive labelled codes only
    dict(survey="sing2009", rule_type="label", match="^weet niet", target=".a", note="7/8/96 'weet niet' (also 'weet niet \\ geen antwoord')"),
    dict(survey="sing2009", rule_type="label", match="^geen antwoord|wil niet zeggen", target=".b", note="6/7/97/98/997/99997 'geen antwoord / wil niet zeggen'"),
    dict(survey="sing2009", rule_type="label", match="^niet van toepassing|^nvt", target=".c", note="8/9/98/99/998/999/9998/9999: routing and the native sample"),
]
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
_SV = r"(?:SPVA|SPVN|LAS|SIM|SING) \d{4}(?:/\d{2})?"
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
    if k in ("spva2002", "spvn2003"):
        for tok in it["qnames"].split(";"):
            if tok: by_token.setdefault((k, tok), []).append(it)
PREFER = {"sim2015": "cawi"}            # SIM 2015: CAWI and CAPI questionnaires are parallel; CAWI is the reference, CAPI differences in capi_qid
NUM_LINK = {"sim2006", "sing2009"}      # questionnaires without variable names: link by the question number in the data label


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
ROUTING_RULES = [
    # survey,   pattern (case-insensitive regex on the routing text),                    gate,              allowed,     description, Q-references the rule consumes
    ("las2004",  r"INDIEN ALLOCHTOON",                                                   "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    ("las2004",  r"INDIEN AUTOCHTOON",                                                   "svy_routing_mig", "0",         "native reference sample (native routing)", "9001"),
    ("las2004",  r"INDIEN TURK, ?MAROKKAAN",                                             "dem_eth",         "1,2",       "Turkish and Moroccan respondents", ""),
    ("las2004",  r"INDIEN MOSLIM",                                                       "rel_den_cat",     "2",         "Muslims", ""),
    ("las2004",  r"INDIEN VROUW",                                                        "dem_sex",         "2",         "women", "35"),
    ("las2004",  r"INDIEN (BETAALD WERK|WERKEND)",                                       "lab_emp",         "1",         "persons with paid work", "500"),
    ("las2004",  r"INDIEN GEEN (BETAALD )?WERK",                                         "lab_emp",         "0",         "persons without paid work", ""),
    ("las2004",  r"INDIEN (?!NIET )(GEHUWD OF SAMENWONEND|PARTNER\b)",                   "dem_prtnr_st",    "1,2,3,4",   "persons with a partner - married, cohabiting or living apart together: the LAS data show the 'GEHUWD OF SAMENWONEND' items were asked to LAT partners as well", ""),
    ("las2004",  r"INDIEN NIET GEHUWD OF SAMENWONEND",                                   "dem_prtnr_st",    "0,4",       "persons without a co-resident partner", ""),
    ("las2004",  r"INDIEN (UITWONENDE |THUISWONENDE )?KINDEREN\b",                       "dem_has_chd",     "1",         "persons with children", ""),
    ("las2004",  r"INDIEN GODSDIENST/RELIGIE",                                           "rel_any",         "1",         "persons who belong to a religion", ""),
    ("las2004",  r"INDIEN NIET (IN NEDERLAND )?GEBOREN",                                 "dem_gen",         "1",         "first generation (born abroad)", "20"),
    ("sim2006",  r"IF \[ (?!#)\s*Q9001 , 1 TO 4(?! ?,)",                                "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    ("sim2006",  r"IF \[ # ?Q9001 , 5(?! ?,)",                                          "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    ("sim2006",  r"IF \[ (?!#)\s*Q9001 , 5(?! ?,)",                                    "svy_routing_mig", "0",         "native reference sample (native routing)", "9001"),
    ("sim2006",  r"IF \[ (?!#)\s*Q9001 , 1 , 2(?! ?,)",                                "dem_eth",         "1,2",       "Turkish and Moroccan respondents", "9001"),
    ("sim2006",  r"IF \[ (?!#)\s*Q9001 , 3 , 4 , 5(?! ?,)",                            "dem_eth",         "3,4,90",    "Surinamese, Antillean and native Dutch respondents", "9001"),
    ("sim2006",  r"IF \[ (?!#)\s*Q35 , 2(?! ?,)",                                      "dem_sex",         "2",         "women", "35"),
    ("sim2006",  r"IF \[ (?!#)\s*Q43 , 1(?! ?,)",                                      "dem_prtnr_st",    "1,2,3,4",   "persons with a partner", "43"),
    ("sim2006",  r"IF \[ (?!#)\s*Q500 , 1(?! ?,)",                                     "lab_emp",         "1",         "persons with paid work", "500"),
    ("sim2006",  r"IF \[ (?!#)\s*Q920 , 1(?! ?,)",                                     "rel_any",         "1",         "persons who belong to a religion", "920"),
    ("sim2006",  r"IF \[ (?!#)\s*Q930 , 1 TO 6(?! ?,)",                                "rel_den_cat",     "2",         "Muslims", "930"),
    ("sing2009", r"INDIEN \[ # ?Q40 , 8(?! ?,)",                                        "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "40,9001"),
    ("sing2009", r"INDIEN \[ (?!#)\s*Q80 , 2(?! ?,)",                                  "dem_sex",         "2",         "women", "80"),
    ("sing2009", r"INDIEN \[ (?!#)\s*Q860 , 1(?! ?,)",                                 "lab_emp",         "1",         "persons with paid work", "860"),
    ("sing2009", r"INDIEN \[ (?!#)\s*Q2990 , 1(?! ?,)",                                "rel_any",         "1",         "persons who belong to a religion", "2990"),
    ("sing2009", r"INDIEN \[ (?!#)\s*Q3000 , 1 TO 6(?! ?,)",                           "rel_den_cat",     "2",         "Muslims", "3000"),
    ("sim2011",  r"INDIEN (RESPONDENT )?ALLOCHTOON",                                     "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    ("sim2011",  r"INDIEN (RESPONDENT )?AUTOCHTOON",                                     "svy_routing_mig", "0",         "native reference sample (native routing)", "9001"),
    ("sim2011",  r"INDIEN MOSLIM",                                                       "rel_den_cat",     "2",         "Muslims", "930"),
    ("sim2011",  r"INDIEN (Q920 ?= ?1|GELOVIG)",                                         "rel_any",         "1",         "persons who belong to a religion", "920"),
    ("sim2011",  r"INDIEN VROUW",                                                        "dem_sex",         "2",         "women", "35"),
    ("sim2011",  r"INDIEN PARTNER \(Q43 ?= ?1\)",                                      "dem_has_prtnr",   "1",         "persons with a partner", "43"),
    ("sim2011",  r"INDIEN BETAALD WERK \(Q500 ?= ?1\)|INDIEN WERKEND",                 "lab_emp",         "1",         "persons with paid work", "500"),
    ("sim2011",  r"INDIEN GEEN BETAALD WERK",                                            "lab_emp",         "0",         "persons without paid work", "500"),
    ("sim2011",  r"INDIEN NIET IN NEDERLAND GEBOREN",                                    "dem_gen",         "1",         "first generation (born abroad)", "20"),
    ("sim2015",  r"ASK ONLY IF not Q9001 ?= ?7|not Q9001=7",                             "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    ("sim2015",  r"ASK ONLY IF Q920 ?= ?1",                                              "rel_any",         "1",         "persons who belong to a religion", "920"),
    ("sim2015",  r"ASK ONLY IF Q930 ?= ?1,2,3,4,5,6",                                    "rel_den_cat",     "2",         "Muslims", "930"),
    ("sim2015",  r"ASK ONLY IF Q43 ?= ?1|IF Q43 ?= ?1",                                  "dem_has_prtnr",   "1",         "persons with a partner", "43"),
    ("sim2015",  r"ASK ONLY IF Q500 ?= ?1",                                              "lab_emp",         "1",         "persons with paid work", "500"),
    ("sim2015",  r"ASK ONLY IF Q35 ?= ?2",                                               "dem_sex",         "2",         "women", "35"),
    ("sim2015",  r"not Q20 ?= ?5",                                                       "dem_gen",         "1",         "first generation (born abroad)", "20"),
    ("sim2020",  r"IF NOT (Q)?9001 ?= ?7|Q9001 IS NOT 7",                               "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    ("sim2020",  r"Q9004 ?, ?1\b|Q9004 ?= ?1\b|NOT Q9004 ?= ?2\b",                    "dem_gen",         "1",         "first generation (sample-data field GENERATIE: the language, Dutch-course and migration items of SIM 2020 went to the first generation only)", "9004"),
    ("sim2020",  r"IF Q920 ?= ?1",                                                       "rel_any",         "1",         "persons who belong to a religion", "920"),
    ("sim2020",  r"IF \[?Q43,1\]?",                                                    "dem_has_prtnr",   "1",         "persons with a partner", "43"),
    ("sim2020",  r"IF \[?Q35,2",                                                        "dem_sex",         "2",         "women", "35"),
    ("sim2020",  r"IF \[?Q500,1\]?|IF WERKZAAM",                                       "lab_emp",         "1",         "persons with paid work", "500"),
    ("sim2020",  r"IF \[?Q930,1-5\]?|IF Q930 ?= ?1,2,3,4,5",                           "rel_den_cat",     "2",         "Muslims", "930"),
    ("sim2020",  r"MOSLIM OF CHRISTEN",                                                   "rel_den_cat",     "2,3",       "Muslims and Christians", "930"),
    ("sim2020",  r"IF SCHOOLGAAND",                                                       "edu_cur_lvl3",    "1,2,3",     "persons currently in education (any level)", ""),
    ("spva2002", r"INDIEN (NU )?(LOONDIENST|WERKEND|BETAALD WERK)",                      "lab_emp",         "1",         "persons with paid work", "500"),
    ("spva2002", r"INDIEN (UITWONENDE |THUISWONENDE )?KINDEREN\b",                       "dem_has_chd",     "1",         "persons with children", ""),
    ("spvn2003", r"INDIEN (UITWONENDE |THUISWONENDE )?KINDEREN\b",                       "dem_has_chd",     "1",         "persons with children", ""),
    ("spva2002", r"INDIEN GEHUWD",                                                       "dem_mar",         "1",         "married persons", ""),
    ("spva2002", r"INDIEN GODSDIENST/KERK/RELIGIE|INDIEN GELOVIG",                       "rel_any",         "1",         "persons who belong to a religion", "920"),
]
assert not any(";" in e for *_, e, _ in ROUTING_RULES), "routing rule descriptions must not contain ';' (gate separator)"
write("routing_rules.csv", [dict(survey=a, pattern=b, gate=c, allowed=d, description=e, consumes=f) for a, b, c, d, e, f in ROUTING_RULES], ["survey", "pattern", "gate", "allowed", "description", "consumes"])
# printed conditions that do not gate the item they are printed with (sub-items of a grid share one routing block; the
# data show the item was asked more widely): the gate is not applied and the reason is printed in the codebook
ROUTING_EXCEPTIONS = [
    # survey,   source variable (regex),        gate,       reason
    ("sim2020", r"^contacterbij_(studie|buurt)$", "lab_emp",      "the condition 'IF WERKZAAM' governs the sibling item contacterbij_baan (contacts at work), this item was asked regardless of employment"),
    ("sim2020", r"^contacterbij_(baan|buurt)$",   "edu_cur_lvl3", "the condition 'IF SCHOOLGAAND' governs the sibling item contacterbij_studie (contacts at school), this item was asked regardless of enrolment"),
    ("sim2015", r"^anveel",                       "svy_routing_mig", "the script also prints 'Niet stellen indien (Q9001=7 AND Q766=5 AND Q765=5)', the data show the native reference sample was asked (about four in five natives have values)"),
    ("sim2015", r"^CATreligie$",                  "rel_any",      "CATreligie is a constructed category variable that codes respondents without a religion (Q920 = no) as 0 = none, the spoken question Q930 was asked to religious respondents only"),
    ("sim2011", r"^oplblnl$",                     "svy_routing_mig", "oplblnl is a constructed variable (the native reference sample is coded 3 = education in the Netherlands only), the spoken question Q235 was asked to migrants only"),
    ("sim2015", r"^anveel",                       "soc_cont_nbr_org", "the printed 'ASK ONLY IF not Q766=5 and not Q765=5' is contradicted by the script's own 'Niet stellen indien (Q9001=7 AND Q766=5 AND Q765=5)' and by the data (about one in six values come from respondents with code 5)"),
    ("sim2015", r"^anveel",                       "soc_cont_frnd_org", "the printed 'ASK ONLY IF not Q766=5 and not Q765=5' is contradicted by the script's own 'Niet stellen indien (Q9001=7 AND Q766=5 AND Q765=5)' and by the data (about one in six values come from respondents with code 5)"),
    ("spvn2003", r"^NLCURS$",                     "int_crs",      "printed 'INDIEN [ Q41 , 2 ]' (no inburgering course), the data show 672 of 3,246 values come from respondents who did follow an inburgering course (INBCURS = 1), so the routing was not applied as printed"),
    ("sim2020",  r"^oplnl$",                      "edu_cntry",    "printed 'IF NOT Q235=1', the data show the question was asked to all respondents (1,355 values from respondents who reported education abroad only, 291 of them 'ja')"),
    ("sim2020",  r"^stemherk2$",                  "dem_eth",      "stemherk2 is the Caribbean variant of Q8531 STEMHERK (linked by name prefix), the printed 'IF Q9001 IS NOT 3, 7' belongs to the origin-country variant, and the data show stemherk2 holds values for Antillean/Aruban respondents only (dem_eth = 4)"),
    ("spvn2003", r"^ARBINK2$",                    "inc_lab",      "printed 'INDIEN [ Q141 , 9997 , 9999 ]' (amount unknown or refused); the deposited ARBINK1 holds an amount for most respondents who answered the category question (round amounts, i.e. back-filled by the data producer), so the harmonized inc_lab is not missing for them"),
    ("spvn2003", r"^UITKINK2$",                   "inc_ben_amt",  "printed 'INDIEN [ Q149 , 9997 , 9999 ]' (amount unknown or refused); the deposited UITKINK1 holds an amount for the respondents who answered the category question (back-filled by the data producer), so the harmonized inc_ben_amt is not missing for them"),
]
write("routing_exceptions.csv", [dict(survey=a, source_var=b, gate=c, reason=d) for a, b, c, d in ROUTING_EXCEPTIONS], ["survey", "source_var", "gate", "reason"])
# household surveys (SPVA/SPVN): the merge takes a source variable from the most detailed file (heads > interviewed persons >
# roster), a file's explicit system-missing code included.  A declared exception lets a valid value of a less detailed file
# stand in where the more detailed file holds only the system-missing code (v0.4.8, follow-up audit of v0.4.7: one SPVN 2003
# generation code).  Not applied in general: the same code also marks derived not-applicable values that agree with the
# chosen self-report (the age bands of a member whose self-reported age is 12 against a roster age of 17; decisions 1).
MERGE_EXCEPTIONS = [
    # survey,    source variable, system-missing code, rule,               reason
    ("spvn2003", "GENERAT",       -7,                  "valid_over_sysmis", "the interviewed-persons file holds the system-missing code (-7) for one member whose roster record carries a valid generation code (2) consistent with the self-reported age (17) and country of birth; the construction failed in the self-report only - the roster value is the best available report"),
]
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
ACQ_OVERRIDES = [
    # survey,    source variable (regex), acquisition,                       respondent-facing, supplied by,  note, exact instruction text (wrapped lines rejoined from the PDF; '' = as parsed)
    ("spvn2003", r"^TAALINTA$", "interview administration", 0, "interviewer", "block instruction P1a-P2b: the questions must not be put to the respondent(s) but answered by the interviewer",
     "Enq.: de volgende vragen dienen niet aan de respondent(en) gesteld te worden maar moeten door u zelf beantwoord worden. P1a. Enq.: in welke taal is het gesprek met de hoofdrespondent gevoerd?"),
    ("las2004",  r"^TAALINT$",  "interview administration", 0, "interviewer", "block instruction VRAAG 404-406: the questions must not be put to the respondent but answered by the interviewer",
     "ENQ.: De volgende vragen dienen niet aan de respondent gesteld te worden maar moeten door u beantwoord worden. In welke taal is het gesprek gevoerd met de respondent?"),
    ("las2004",  r"^DAT(DAG|MND)$", "interview administration", 0, "interviewer", "date of the interview noted by the interviewer", ""),
    ("las2004",  r"^ETNGRP$",   "registry/sample data", 0, "sample frame (origin group of the register-based sample)", "'Respondent behoort tot volgende groep' is the sample classification shown to the interviewer (the LAS samples were drawn by origin group from the municipal population registers, fieldwork report appendix 1a), not a question", ""),
    ("sim2020",  r"^etngba$",   "registry/sample data", 0, "sample frame / population register (GBA)", "Q9001 is marked [SAMPLE DATA]", ""),
    ("sim2015",  r"^etngba$",   "registry/sample data", 0, "sample frame / population register (GBA)", "the same sample-data field as SIM 2020 Q9001 (variable name etngba = origin group from the GBA; data label 'Respondent behoort tot volgende GROEP')", ""),
]
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

design = [
    dict(survey="spva2002", aspect="mode", text="Face-to-face interviews at home (paper questionnaires); main questionnaire for the head of household, mini questionnaire for other members aged 12+, cultural-integration module for one child aged 15+. Turkish/Arabic translated questionnaires available for the Turkish and Moroccan groups."),
    dict(survey="spva2002", aspect="order", text="Fixed question order (paper); no randomisation. Question blocks: general/household/migration, education, labour, income, health, language, group, social contacts, cultural integration, religion, imaging, family relations."),
    dict(survey="spva2002", aspect="versions", text="One questionnaire version per group; differences limited to the answer categories for mother tongue and ethnic subgroup."),
    dict(survey="spvn2003", aspect="mode", text="Face-to-face (CAPI) interviews; main questionnaire (15 blocks) for heads, mini questionnaire for members aged 12+, separate health and cultural-integration blocks for the partner and one child aged 15+; Dutch, English or French."),
    dict(survey="spvn2003", aspect="order", text="Fixed question order; no randomisation."),
    dict(survey="las2004", aspect="mode", text="Face-to-face CAPI interviews (Veldkamp with TNS NIPO interviewers) with persons aged 15-64 sampled by CBS from the GBA of the 50 largest municipalities (Turks, Moroccans, Surinamese, Antilleans/Arubans, native Dutch); only the sampled person was interviewed. Fieldwork October 2004 - May 2005; corrected response 45% (Turks 47%, Moroccans 44%, Surinamese 38%, Antilleans 47%, natives 50%). An extra sample of working mothers with children under 12 was drawn in March 2005 in nine municipalities and the working partners of male Turkish, Moroccan and Antillean respondents with young children were asked a supplementary interview (47 cases; items marked '+ P' in the questionnaire, of which only dem_prtnr_flex survives as a separate variable); svy_oversample flags the resulting oversample of working men and women (228 cases)."),
    dict(survey="las2004", aspect="order", text="Fixed block order A-X; no rotation or randomisation reported. Questions on the murder of Theo van Gogh were added about two weeks into the fieldwork (universe: respondents interviewed after that point)."),
    dict(survey="las2004", aspect="routing", text="One programmed questionnaire with group routing (INDIEN ALLOCHTOON / AUTOCHTOON / TURK, MAROKKAAN / MOSLIM / NIET IN NEDERLAND GEBOREN); the native reference sample skips the migration, language, integration and Islam blocks (.c). The time-use diary (block X) was administered by the interviewer at the end of the interview, for 'yesterday', in 72 quarter-hour slots from 06:00 to 24:00 with a 43-code activity card (tim_slot01-72, tim_act01-43; day of the week in tim_weekday, diary weights tim_wgt and tim_wgt_corr); it was skipped when the interview had run long and completed by 74% of respondents (Turks 71%, Moroccans 65%, natives 87%)."),
    dict(survey="las2004", aspect="languages", text="Written Turkish and Moroccan-Arabic translations (two independent translators, reconciled with SCP) supported interviews in Dutch; respondents with language problems were re-approached by 17 Turkish and Moroccan interviewers (128 interviews)."),
    dict(survey="las2004", aspect="release", text="The DANS file holds the questionnaire variables, SCP constructs (societal position, earner type, labour-force status) and weights (svy_wgt, svy_wgt_grp, svy_wgt_raise); no registry linkage. The questionnaire itself is appendix 1a of the deposited fieldwork report."),
    dict(survey="sim2006", aspect="mode", text="Face-to-face CAPI interviews (Veldkamp/TNS NIPO, with ERC interviewers for Turkish and Moroccan respondents) with persons aged 15+ sampled by CBS from the GBA nationwide (at least 10 addresses per municipality); a paper version existed for interviewers without a laptop. Fieldwork March 2006 - January 2007; corrected response 53% (Moroccans 50%, Turks 60%, Antilleans 54%, Surinamese 46%, natives 55%); 5,250 interviews. Part of the sample received two postage stamps with the invitation letter as an incentive experiment."),
    dict(survey="sim2006", aspect="order", text="Fixed block order A-P; no rotation or randomisation reported."),
    dict(survey="sim2006", aspect="routing", text="Only the sampled person answered (the partner could be present). Items on Islam were routed to Muslims by the script; a respondent counted as native Dutch when both parents were born in the Netherlands. Answer cards were collected in a card booklet and read out literally. The deposited questionnaire is the CAPI script printout, which carries no variable names: items are linked to the data through the question number in the data labels and the option order of multiple-response questions."),
    dict(survey="sim2006", aspect="languages", text="Turkish and Moroccan-Arabic written translations (one translator, independent check); first-generation Turks and Moroccans who arrived at 15 or older were assigned to co-ethnic interviewers where possible, with gender matching."),
    dict(survey="sing2009", aspect="mode", text="Face-to-face CAPI interviews (Veldkamp/TNS NIPO; 243 native and 60 bilingual interviewers) with persons aged 15+ sampled by CBS from the GBA in two stages (municipalities, then persons): Afghans, Iraqis, Iranians, Somalis, Chinese, Poles and a native Dutch reference sample. The Polish sample was redesigned after a pilot to short-stay Poles (less than five years registered), 532 of whom completed a Polish self-completion version on the interviewer's laptop. Fieldwork February 2009 - February 2010; corrected response 43% (Iranians 44%, Iraqis 48%, Afghans 49%, Somalis 38%, Chinese 38%, Poles 42%, natives 46%); 6,911 interviews."),
    dict(survey="sing2009", aspect="order", text="Fixed block order A-U; no rotation reported. One item, Q2630 (leisure-time contact with native Dutch, soc_leis_nl), was asked to a random half of the respondents with a migration background (CAPI script field exp2431 = 1); the deposit documents neither the split nor an indicator for it, so the half is visible only as .c on that variable (3,017 of 5,952 asked; the follow-up Q2640 went to both halves)."),
    dict(survey="sing2009", aspect="routing", text="Natives skip the migration-history and civic-integration blocks (shorter questionnaire, 40 instead of 56 minutes); Chinese respondents could skip the religion items. Respondents aged 15-17 were asked to call in a parent for the household-income questions (hh_inc_band_par). The deposited questionnaire is the CAPI script printout without variable names (linked via the question numbers in the data labels)."),
    dict(survey="sing2009", aspect="languages", text="Questionnaire, letter and folder translated into Farsi, Arabic, Dari, Somali, Chinese and Polish (DaVinci Vertalingen, checked by co-ethnic interviewers) and programmed in CAPI; short-stay respondents were approached by bilingual interviewers where possible."),
    dict(survey="sing2009", aspect="release", text="Partial release: the DANS file contains only the questions listed in the deposit's READ ME (the rest is available through CBS Remote Access), and years and durations are coarsened into classes: age and partner's age in 3 classes (15-24, 25-44, 45+), length of stay 0-5/5-10/10-15/15+ years, year of marriage and of first arrival in decade bands, contractual hours in 4 classes, education in 4 classes. The IMPD keeps these as the SING-only `_cat` variants (e.g. dem_age_cat3, mig_dur_nl_cat4). The release is also statistically protected: in some variables real values are replaced by 'don't know' / 'not applicable' / 'other' codes (sex for 2 respondents, marital status 71, origin group 85 - the 'unknown' group -, generation 29 besides the natives, year of marriage 39, small categories of the household-position items recoded to 98), household size and the number of children are top-coded at 6, and the BMI is delivered in classes; the resulting .d / unknown values are protection, not non-response. The CBS microdata hold the unprotected values."),
    dict(survey="sim2011", aspect="mode", text="Face-to-face CAPI interviews at home (GfK with Labyrinth co-ethnic interviewers), no proxies, with persons aged 15+ sampled by CBS from the GBA stratified in six municipality strata (Turks, Moroccans, Surinamese, Antilleans/Arubans, native Dutch). Fieldwork from November 2010 for about five months; corrected response Turks 54%, Moroccans 50%, Surinamese 43%, Antilleans 48%, natives 55%; 4,125 interviews. A parallel mixed-mode experiment (web, then telephone, then face-to-face; 2,698 respondents, shortened web questionnaire) is NOT in the DANS deposit: all records have onderzoek = main study and methode = CAPI (svy_fw_phase records the two fieldwork phases, the second being a re-approach of non-respondents by another interviewer)."),
    dict(survey="sim2011", aspect="order", text="Fixed block order A-U; no rotation or randomisation reported. Ranking question Q1073 (fam_val_rank) asks for a 1-5 order of child-rearing values."),
    dict(survey="sim2011", aspect="routing", text="Group routing as in SIM 2006 (natives .c for migrant-only items; Islam items to Muslims). Partner items Q53-70, 225, 230 are proxy answers by the respondent. Respondents aged 15-17 were asked to call in a parent for the household questions (suffix _par). The deposit is statistically protected (mu-Argus on sex x 5-year age class) and version 3 removed the open-answer variables; the questionnaire is the hardcopy of the CAPI script (appendix g), which prints variable names next to the questions."),
    dict(survey="sim2011", aspect="languages", text="Turkish and Moroccan-Arabic translations (SIM 2006 versions reused, new items double-translated); Berber (138 interviews), Papiamento (121) and Surinamese languages (11) used orally as fallback (svy_lang_hh, svy_lang_oth). All Turkish and Moroccan respondents were interviewed by co-ethnic interviewers, Surinamese and Antilleans half by native interviewers."),
    dict(survey="sim2015", aspect="mode", text="Sequential mixed mode: web (CAWI) invitation first, face-to-face (CAPI) follow-up of non-respondents by bilingual interviewers (TNS NIPO and Labyrinth); CAWI and CAPI questionnaires are parallel (questionnaire_items.csv holds both; wording.csv references the CAWI version with the CAPI question id in capi_qid)."),
    dict(survey="sim2015", aspect="order", text="Fixed block order with randomised item order within batteries: Q801-Q815 and Q813-Q817 (opinion statements), Q895-Q89801 (opinions on NL), Q770 contact with groups and Q859-Q865 feeling thermometers (groups presented in random order, own group always last; Jews never first)."),
    dict(survey="sim2015", aspect="routing", text="Many items asked only to respondents with a migration background (ASK ONLY IF not Q9001=7); the native reference sample gets mirrored wording ('allochtone' instead of 'autochtone' contacts)."),
    dict(survey="sim2015", aspect="languages", text="Questionnaire available in Dutch, Turkish, Moroccan Arabic, Polish and Somali (CAWI language choice; language variable not in the public file)."),
    dict(survey="sim2020", aspect="mode", text="CAWI (90%) with CAPI follow-up only for the Caribbean, Moroccan, Somali, Surinamese and Turkish groups (10%) because of covid; 15 CAPI interviews by video call (WhatsApp). Fieldwork 11 March 2020 - 17 January 2021 with CAPI suspended during lockdowns."),
    dict(survey="sim2020", aspect="split_half", text="Respondents randomly assigned within origin group to A or B (svy_split). Only A: political participation (POL_4, HERK_3), institutional trust (VERTWORG), belonging (CONTACTERBIJ, ORGANBIJ), media interest and positioning (NIEUWS_3, FREQNIEU, FREQAANT, POS_4). Only B: opinion statements STELL_8_12 and STELL_1_7_5, religion items BIJBKOR and KORZELFINT, mental health items MENTALGEZ_4_4, 8_3, 8_4, BEZOEKMOG, HUISARTS, PIJN, situational discrimination DISCZELF2, Zwarte Piet items."),
    dict(survey="sim2020", aspect="order", text="Fixed block order with randomised item order within batteries: Q801-Q804, Q813-Q817, Q895-Q89801, Q965-Q967."),
    dict(survey="sim2020", aspect="versions", text="Six script versions (svy_qversion); version differences are not documented in the fieldwork report. Early CAWI interviews ran on versions 1-3."),
    dict(survey="sim2020", aspect="languages", text="Dutch, Turkish, Moroccan Arabic, Polish, Somali, Farsi (svy_lang_q); a Farsi error in two items is flagged in the source (code -1)."),
    dict(survey="sim2020", aspect="wording", text="Group terms updated: 'allochtoon' -> 'persoon met een migratieachtergrond' in most items; 'autochtone Nederlanders' retained in contact items. Text fills per group (<HERKGRP>, <LVH>)."),
]
write("questionnaire_design.csv", design, ["survey", "aspect", "text"])

# municipalities: survey code -> CBS code (2006 list, External/Municipality codes/2006-gemeenten-op-code.xls)
MUN = {("spva2002", 1): ("0363", "Amsterdam"), ("spva2002", 2): ("0599", "Rotterdam"), ("spva2002", 3): ("0518", "'s-Gravenhage"),
       ("spva2002", 4): ("0344", "Utrecht"), ("spva2002", 5): ("0772", "Eindhoven"), ("spva2002", 6): ("0153", "Enschede"),
       ("spva2002", 8): ("0034", "Almere"), ("spva2002", 10): ("0484", "Alphen aan den Rijn"), ("spva2002", 11): ("0748", "Bergen op Zoom"),
       ("spva2002", 13): ("0018", "Hoogezand-Sappemeer"), ("spva2002", 15): ("0503", "Delft"), ("spva2002", 16): ("0505", "Dordrecht"),
       ("spva2002", 17): ("0281", "Tiel"),
       ("spvn2003", 1): ("0363", "Amsterdam"), ("spvn2003", 2): ("0599", "Rotterdam"), ("spvn2003", 3): ("0518", "'s-Gravenhage"),
       ("spvn2003", 4): ("0344", "Utrecht"), ("spvn2003", 5): ("0772", "Eindhoven"), ("spvn2003", 6): ("0153", "Enschede"),
       ("spvn2003", 7): ("0034", "Almere"), ("spvn2003", 8): ("0268", "Nijmegen"), ("spvn2003", 9): ("0503", "Delft"),
       ("spvn2003", 10): ("0080", "Leeuwarden"), ("spvn2003", 11): ("0855", "Tilburg"), ("spvn2003", 12): ("0014", "Groningen")}
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
