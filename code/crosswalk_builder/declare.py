# -*- coding: utf-8 -*-
"""
IMPD crosswalk builder — declaration helpers shared by the variable files (variables*.py) and by the
declare() function a survey module (surveys/<key>.py) may define.

Each survey module carries a short code KW ("02", "15", ...).  V() takes the source variable for that survey as
s<KW>= and its universe as u<KW>= (or sources= / universes= keyed by survey key), so adding a survey needs no
change here.

V(...)  declares a harmonized (target) variable and, per survey, the source variable feeding it.
M(...)  declares a value-level recode (one row of value_map.csv).
W(...)  records a curated wording note for the codebook's wording table.
L(...)  links a (survey, source variable) to a questionnaire item when the automatic name match fails.

Multi-source feeds: a source given as "A|B" means the target is fed by the first non-missing of A, B (in that
order) after each has been recoded with its own value_map rows and missing rules.  Used when a deposit splits one
question over two variables (e.g. SIM 2006 asks the contact items separately to migrants, CONTOUD, and to the
native sample, CONTOU_N).  R and Stata implement the same precedence: a valid value beats any tag; among tags the
first that is not .c (not applicable) wins; otherwise .c.
"""
from valuesets import VALUESETS
import surveys as _surveys

# survey keys in the order of surveys.csv, from the survey modules (surveys/<key>.py); V() takes s<KW>= / u<KW>= for each
SURVEY_KEYS = list(_surveys.KEYS)
SRC_KW = {"s" + kw: key for kw, key in _surveys.KW.items()}

VARS = []            # variable_map rows
VMAP = []            # value_map rows
WORDING_NOTES = {}   # target -> curated note on wording / answer-scale changes across surveys
WORDING_LINKS = {}   # (survey, source_var) -> questionnaire qid (manual override of the name match)
UNIVERSES = {}       # (target, survey) -> survey-specific universe text (who was asked), codebook wording table
ASKED_TO = {}        # (target, survey) -> (respondent type whose questionnaire contained the item, note); household surveys only
SKIPPED = {}         # (survey, source_var) -> reason: source variables deliberately not harmonized (kept in the *_source file)
_seen = set()


def parts(src):
    """Source specification -> list of source variable names ('A|B' -> ['A', 'B']; '' -> [])."""
    return [p for p in (src or "").split("|") if p]


def V(target, theme, label, s02=None, s03=None, valueset=None, type="cat", scope="person",
      universe="", notes="", include=1, yn12=False, derive="", wording="", sources=None, universes=None, **per_survey):
    """Declare a harmonized variable.
    s<KW>=: source variable name in the survey whose module has that KW (s02 SPVA 2002, s03 SPVN 2003, s04 LAS 2004/05,
    s06 SIM 2006, s09 SING 2009, s11 SIM 2011, s15 SIM 2015, s20 SIM 2020; None if absent); u<KW>=: survey-specific
    universe text.  Equivalently sources={"sim2020": "VAR"} / universes={"sim2020": "text"} by survey key.  s02, s03 can
    also be given positionally (older declarations).
    yn12: source codes 1=yes 2=no -> harmonized 1=yes 0=no (value_map rows generated for every source).
    include: 1 = in main file; 0 = retained only in the *_source file (pure recode / duplicate).
    derive: name of a derivation rule implemented identically in R and Stata (03_derive).
    scope: 'person' or 'household' (household-scope items are taken from the head and merged onto members
           in hh/pp/ro surveys; in flat surveys they are simply the respondent's values).
    wording: curated note on wording or answer-scale differences between surveys (codebook wording table).
    """
    assert target not in _seen, f"duplicate target {target}"
    assert len(target) <= 32, f"name too long for Stata: {target}"
    assert target.startswith(theme + "_"), f"{target} does not start with its theme stem {theme}_"
    if valueset is not None and not valueset.startswith("src_"):
        assert valueset in VALUESETS, f"unknown valueset {valueset} for {target}"
    _seen.add(target)
    per_survey.update(s02=s02, s03=s03)
    src, univ = {k: "" for k in SURVEY_KEYS}, {}
    for name, val in per_survey.items():
        assert name[:1] in ("s", "u") and name[1:] in _surveys.KW, f"V({target}): unknown argument {name}"
        if val: (src if name[0] == "s" else univ)[_surveys.KW[name[1:]]] = val
    for k, val in (sources or {}).items():
        assert k in src, f"V({target}): unknown survey {k}"
        src[k] = val
    univ.update(universes or {})
    row = dict(target=target, theme=theme, label_en=label, scope=scope, type=type,
               valueset=valueset or "", universe_en=universe, notes=notes, include_main=include, derive=derive)
    for k in SURVEY_KEYS:
        row[f"src_{k}"] = src[k]
    VARS.append(row)
    if yn12:
        for k in SURVEY_KEYS:
            for p in parts(src[k]):
                M(target, k, p, 1, 1); M(target, k, p, 2, 0)
    if wording:
        WORDING_NOTES[target] = wording
    for k in SURVEY_KEYS:
        if univ.get(k):
            UNIVERSES[(target, k)] = univ[k]


def M(target, survey, source_var, source_value, target_value, note=""):
    """Declare a value-level recode.  source_value: number, 'lo-hi' range, a quoted string for string
    sources, or '*' (any other non-missing value).  target_value: number, or '.a' '.b' '.c' '.d' for
    tagged missing."""
    VMAP.append(dict(target=target, survey=survey, source_var=source_var,
                     source_value=str(source_value), target_value=str(target_value), note=note))


def W(target, note):
    """Curated wording note (appended to any note given in V(..., wording=))."""
    WORDING_NOTES[target] = (WORDING_NOTES.get(target, "") + " " + note).strip()


def L(survey, source_var, qid):
    """Manual link from a source variable to a questionnaire item id (crosswalks/questionnaire_items.csv)."""
    WORDING_LINKS[(survey, source_var)] = qid


def U(target, survey, text):
    """Survey-specific universe text for an existing target."""
    UNIVERSES[(target, survey)] = text


def ASKED(target, survey, who, note, universe=None):
    """Household surveys (SPVA/SPVN): the item was in the questionnaire of one respondent type only - 'heads' (main
    questionnaire) or 'members' (mini questionnaire) - although the persons file holds both types.  02_harmonize sets .e
    (not collected) for the other type after verifying that it has no valid value; crosswalks/asked_to.csv."""
    assert who in ("heads", "members"), (target, survey, who)
    ASKED_TO[(target, survey)] = (who, note)
    if universe:
        U(target, survey, universe)


def find(target):
    return next(r for r in VARS if r["target"] == target)


def SKIP(survey, source_var, reason):
    """Declare that a source variable is deliberately left out of the main file (empty in the deposit, pure
    administration, or a duplicate of another source); it stays in the *_source file and is listed in
    crosswalks/source_skipped.csv with the reason."""
    SKIPPED[(survey, source_var)] = reason


def A(target, survey, src, pairs=None, u="", yn12=False, note=""):
    """Attach a source variable of a later-added survey to an existing target.
    src: source variable name, or "A|B" for a multi-source feed (see module docstring).
    pairs: list of (source_value, target_value) recodes applied to every source, or a dict {source: pairs};
    yn12: 1/2 -> 1/0 for every source; u: survey-specific universe text."""
    r = find(target)
    assert not r[f"src_{survey}"], f"{target} already has a {survey} source ({r[f'src_{survey}']})"
    r[f"src_{survey}"] = src
    for p in parts(src):
        pp = pairs.get(p, []) if isinstance(pairs, dict) else (pairs or [])
        for a, b in pp:
            M(target, survey, p, a, b, note)
        if yn12:
            M(target, survey, p, 1, 1); M(target, survey, p, 2, 0)
    if u:
        UNIVERSES[(target, survey)] = u
