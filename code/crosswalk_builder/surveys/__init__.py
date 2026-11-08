# -*- coding: utf-8 -*-
"""
IMPD crosswalk builder - the survey registry: one module per survey.

Every module in this folder whose name does not start with "_" is a survey module. It defines:

  SURVEY          registry entry (one row of crosswalks/surveys.csv): svy_id (chronological position), svy_name, svy_year,
                  status ("included"), key, structure ("flat" or "hh_pp_ro"), title, DANS id/doi/access, groups,
                  fieldwork, mode, zipfile and file names inside it, encoding, id_var, weight_var, sysmis_tag, missing_scheme
  KW              two-character suffix of the survey's keyword arguments in V(): s<KW>="SOURCEVAR", u<KW>="universe text"
  LABEL           display name ("SIM 2020")
  ELIGIBLE, WEIGHTS   eligible sample and weight guidance (codebook section 1)
  ZIP_SHA256      sha256 of the DANS zip as downloaded
  MISSING_RULES   the source file's missing-value conventions
  QUESTIONNAIRES  the questionnaire PDF(s) and the parser that reads them

and, where they apply,

  DESIGN, ROUTING_RULES, ROUTING_EXCEPTIONS, MERGE_EXCEPTIONS, ACQ_OVERRIDES, CONSTRUCTED, MUNICIPALITIES,
  PREFER_INSTRUMENT, LINK_BY_QNUM
  declare()       the survey's variable declarations (A(), V(), M(), U(), W(), L(), SKIP(), vs() ...), called by
                  build.py after the older declaration modules - so a survey added later is one file

A module may instead define only REGISTRY_ONLY (registry rows of surveys not yet included). Modules are ordered by
svy_id, which fixes the order of the surveys everywhere (columns of variable_map.csv, rows of every crosswalk).
See docs/harmonization.md, "Adding a survey".
"""
import importlib
import os
import pkgutil

_HERE = os.path.dirname(os.path.abspath(__file__))
_MODULES = [importlib.import_module(f"{__name__}.{m.name}") for m in sorted(pkgutil.iter_modules([_HERE]), key=lambda m: m.name)
            if not m.name.startswith("_")]

REQUIRED = ["SURVEY", "KW", "LABEL", "ELIGIBLE", "WEIGHTS", "ZIP_SHA256", "MISSING_RULES", "QUESTIONNAIRES"]
for _m in _MODULES:
    if hasattr(_m, "SURVEY"):
        _missing = [a for a in REQUIRED if not hasattr(_m, a)]
        assert not _missing, f"survey module {_m.__name__} lacks {_missing}"
        assert _m.SURVEY.get("key") == _m.__name__.rsplit(".", 1)[1], f"{_m.__name__}: SURVEY['key'] must equal the module name"
    else:
        assert hasattr(_m, "REGISTRY_ONLY"), f"{_m.__name__} defines neither SURVEY nor REGISTRY_ONLY"

MODULES = sorted([m for m in _MODULES if hasattr(m, "SURVEY") and m.SURVEY["status"] == "included"], key=lambda m: m.SURVEY["svy_id"])
KEYS = [m.SURVEY["key"] for m in MODULES]
BY_KEY = dict(zip(KEYS, MODULES))
KW = {m.KW: m.SURVEY["key"] for m in MODULES}                  # "20" -> "sim2020"
LABEL = {m.SURVEY["key"]: m.LABEL for m in MODULES}
REGISTRY = sorted([dict(m.SURVEY) for m in _MODULES if hasattr(m, "SURVEY")] +
                  [dict(r) for m in _MODULES for r in getattr(m, "REGISTRY_ONLY", [])], key=lambda s: s["svy_id"])
for _a, _what in ((KEYS, "key"), ([s["svy_id"] for s in REGISTRY], "svy_id"), ([m.KW for m in MODULES], "KW")):
    assert len(_a) == len(set(_a)), f"duplicate survey {_what}: {_a}"


def collect(attr):
    """Concatenate a per-survey list in survey order, prefixing each entry with the survey key."""
    out = []
    for k, m in BY_KEY.items():
        for e in getattr(m, attr, []):
            out.append(dict(survey=k, **e) if isinstance(e, dict) else (k,) + tuple(e))
    return out


ELIG = {k: (m.ELIGIBLE, m.WEIGHTS) for k, m in BY_KEY.items()}
ZIP_SHA256 = {k: m.ZIP_SHA256 for k, m in BY_KEY.items()}
MISSING_RULES = collect("MISSING_RULES")
QUESTIONNAIRES = collect("QUESTIONNAIRES")
DESIGN = collect("DESIGN")
ROUTING_RULES = collect("ROUTING_RULES")
ROUTING_EXCEPTIONS = collect("ROUTING_EXCEPTIONS")
MERGE_EXCEPTIONS = collect("MERGE_EXCEPTIONS")
ACQ_OVERRIDES = collect("ACQ_OVERRIDES")
CONSTRUCTED = {k: m.CONSTRUCTED for k, m in BY_KEY.items() if hasattr(m, "CONSTRUCTED")}
MUNICIPALITIES = {(k, code): v for k, m in BY_KEY.items() for code, v in getattr(m, "MUNICIPALITIES", {}).items()}
PREFER = {k: m.PREFER_INSTRUMENT for k, m in BY_KEY.items() if hasattr(m, "PREFER_INSTRUMENT")}
NUM_LINK = {k for k, m in BY_KEY.items() if getattr(m, "LINK_BY_QNUM", False)}
DECLARE = [m.declare for m in MODULES if hasattr(m, "declare")]
