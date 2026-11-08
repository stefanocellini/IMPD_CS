# -*- coding: utf-8 -*-
"""SPVN 2003: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of SPVN 2003 are in variables.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""

KW = "03"            # V(..., s03="SOURCEVAR", u03="universe text") in the declaration modules
LABEL = "SPVN 2003"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=6, svy_name="SPVN2003", svy_year=2003, status="included", key="spvn2003", structure="hh_pp_ro",
         title="Sociale positie en voorzieningengebruik van allochtonen 2003 - refugee groups (SPVA/SPVN 2003)", dans_id="P1753", doi="10.17026/dans-x7u-vkfm", access="open",
         groups="Afghans; Iraqis; Iranians; former Yugoslavs; Somalis", fieldwork="Veldkamp (2003); ISEO Erasmus University", mode="Face-to-face (CAPI), household sample",
         zipfile="Surveys/SPVN 2003.zip", file_hh="spvnhh.sav", file_pp="spvntt.sav", file_ro="spvnag.sav", file_main="", encoding="latin1",
         id_var="", weight_var="WEEG", sysmis_tag="",
         missing_scheme="explicit codes -7 sysmis, -4 missing, -3 don't know, -2 refusal; labelled 997/9997/0 'weet niet'; 'Onbekend' in code lists")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "96556f53090b5e84fcd3d6aa29c43339391d9363c4b9984a5e2334147cd48011"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Households of Afghan, Iraqi, Iranian, former-Yugoslav and Somali origin in 12 municipalities (ISEO). Same row structure as SPVA 2002."
WEIGHTS = "svy_wgt: ISEO household weight; cluster on id_hh."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    dict(rule_type="code", match="-7", target=".", note="Sysmis (not applicable / routed out / not in questionnaire)"),
    dict(rule_type="code", match="-4", target=".d", note="Missing / no information"),
    dict(rule_type="code", match="-3", target=".a", note="Don't know"),
    dict(rule_type="code", match="-2", target=".b", note="Refusal (wil niet zeggen)"),
    dict(rule_type="label", match="^weet niet$", target=".a", note="Labelled don't-know codes (997, 9997, 0 in year/month variables)"),
    dict(rule_type="label", match="^wil niet zeggen$", target=".b", note=""),
    dict(rule_type="label", match="^onbekend$", target=".d", note="Unknown place/country in code lists (97, 997)"),
    dict(rule_type="label", match="^(missing|geen informatie)$", target=".d", note=""),
    dict(rule_type="label", match="^sysmis$", target=".", note=""),
    dict(rule_type="declared", match="^(0|7|97|98|997|9997)$", target=".a", note="Declared user-missing codes that follow the ISEO don't-know convention (0 in year/month/amount items, 7, 97/997/9997, 98)"),
    dict(rule_type="declared", match=".*", target=".d", note="Other declared user-missing codes (9/10/99/999 = no information)"),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    ("main", "data/raw/spvn2003/SPVA2003 Codeboek.pdf", "spvn", None),
]

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="Face-to-face (CAPI) interviews; main questionnaire (15 blocks) for heads, mini questionnaire for members aged 12+, separate health and cultural-integration blocks for the partner and one child aged 15+; Dutch, English or French."),
    dict(aspect="order", text="Fixed question order; no randomisation."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    (r"INDIEN (UITWONENDE |THUISWONENDE )?KINDEREN\b",                       "dem_has_chd",     "1",         "persons with children", ""),
]

# printed conditions the data contradict (crosswalks/routing_exceptions.csv): (source variable regex, gate, reason)
ROUTING_EXCEPTIONS = [
    (r"^NLCURS$",                     "int_crs",      "printed 'INDIEN [ Q41 , 2 ]' (no inburgering course), the data show 672 of 3,246 values come from respondents who did follow an inburgering course (INBCURS = 1), so the routing was not applied as printed"),
    (r"^ARBINK2$",                    "inc_lab",      "printed 'INDIEN [ Q141 , 9997 , 9999 ]' (amount unknown or refused); the deposited ARBINK1 holds an amount for most respondents who answered the category question (round amounts, i.e. back-filled by the data producer), so the harmonized inc_lab is not missing for them"),
    (r"^UITKINK2$",                   "inc_ben_amt",  "printed 'INDIEN [ Q149 , 9997 , 9999 ]' (amount unknown or refused); the deposited UITKINK1 holds an amount for the respondents who answered the category question (back-filled by the data producer), so the harmonized inc_ben_amt is not missing for them"),
]

# household surveys: declared merge exceptions (crosswalks/merge_exceptions.csv): (source variable, system-missing code, rule, reason)
MERGE_EXCEPTIONS = [
    # source variable, system-missing code, rule,               reason
    ("GENERAT",       -7,                  "valid_over_sysmis", "the interviewed-persons file holds the system-missing code (-7) for one member whose roster record carries a valid generation code (2) consistent with the self-reported age (17) and country of birth; the construction failed in the self-report only - the roster value is the best available report"),
]

# how a value was obtained, where the automatic rules cannot tell (crosswalks/acquisition_overrides.csv):
# (source variable regex, acquisition, respondent-facing, supplied by, note, instruction text)
ACQ_OVERRIDES = [
    # source variable (regex), acquisition,                       respondent-facing, supplied by,  note, exact instruction text (wrapped lines rejoined from the PDF; '' = as parsed)
    (r"^TAALINTA$", "interview administration", 0, "interviewer", "block instruction P1a-P2b: the questions must not be put to the respondent(s) but answered by the interviewer",
     "Enq.: de volgende vragen dienen niet aan de respondent(en) gesteld te worden maar moeten door u zelf beantwoord worden. P1a. Enq.: in welke taal is het gesprek met de hoofdrespondent gevoerd?"),
]

# municipality codes of the source -> CBS code and name, 2006 list (crosswalks/municipalities.csv)
MUNICIPALITIES = {
    1: ('0363', 'Amsterdam'),
    2: ('0599', 'Rotterdam'),
    3: ('0518', "'s-Gravenhage"),
    4: ('0344', 'Utrecht'),
    5: ('0772', 'Eindhoven'),
    6: ('0153', 'Enschede'),
    7: ('0034', 'Almere'),
    8: ('0268', 'Nijmegen'),
    9: ('0503', 'Delft'),
    10: ('0080', 'Leeuwarden'),
    11: ('0855', 'Tilburg'),
    12: ('0014', 'Groningen'),
}
