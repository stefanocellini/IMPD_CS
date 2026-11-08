# -*- coding: utf-8 -*-
"""SPVA 2002: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of SPVA 2002 are in variables.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""

KW = "02"            # V(..., s02="SOURCEVAR", u02="universe text") in the declaration modules
LABEL = "SPVA 2002"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=5, svy_name="SPVA2002", svy_year=2002, status="included", key="spva2002", structure="hh_pp_ro",
         title="Sociale positie en voorzieningengebruik van allochtonen 2002 (SPVA 2002)", dans_id="P1684", doi="10.17026/dans-xdt-cynn", access="open",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans", fieldwork="Veldkamp Marktonderzoek (2002-2003); SEOR/ISEO & SCP", mode="Face-to-face (PAPI), household sample",
         zipfile="Surveys/SPVA 2002.zip", file_hh="dat/p1684a.por", file_pp="dat/p1684b.por", file_ro="dat/p1684c.por", file_main="", encoding="cp1252",
         id_var="", weight_var="WEEG", sysmis_tag="",
         missing_scheme="system-missing + labelled codes 9/99/999/9999 'geen informatie', 7/97 'weet niet'")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "91166a194661265f0efafc97828639a8f41b1ef930639adecb00b99794a9d10e"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Households of Turkish, Moroccan, Surinamese and Antillean/Aruban origin in 13 municipalities (ISEO; the native comparison sample is not in the DANS deposit). Rows: all roster members; interviewed persons = heads (main questionnaire) and members aged 12+ (mini); children and non-interviewed members are roster-only records with head-reported demography."
WEIGHTS = "svy_wgt: ISEO design/post-stratification weight of the household (merged onto every member). Not a population weight across surveys; observations are clustered within households (id_hh)."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    dict(rule_type="label", match="^geen informatie$", target=".d", note="Codes 9/99/999/9999/99999 where so labelled"),
    dict(rule_type="label", match="^weet niet$", target=".a", note="Codes 7/97 where so labelled"),
    dict(rule_type="declared", match="^(7|97)$", target=".a", note="SPSS user-missing codes declared in the file (source_missing.csv): ISEO convention 7/97 = don't know"),
    dict(rule_type="declared", match=".*", target=".d", note="Other declared user-missing codes (9/99/999/9999/99999 = geen informatie)"),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    # instrument, pdf path (relative to ROOT), parser, (start, end) regexes slicing the text to the questionnaire (or None)
    ("main", "data/raw/spva2002/dat/p1684.pdf", "spva", None),
]

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="Face-to-face interviews at home (paper questionnaires); main questionnaire for the head of household, mini questionnaire for other members aged 12+, cultural-integration module for one child aged 15+. Turkish/Arabic translated questionnaires available for the Turkish and Moroccan groups."),
    dict(aspect="order", text="Fixed question order (paper); no randomisation. Question blocks: general/household/migration, education, labour, income, health, language, group, social contacts, cultural integration, religion, imaging, family relations."),
    dict(aspect="versions", text="One questionnaire version per group; differences limited to the answer categories for mother tongue and ethnic subgroup."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    (r"INDIEN (NU )?(LOONDIENST|WERKEND|BETAALD WERK)",                      "lab_emp",         "1",         "persons with paid work", "500"),
    (r"INDIEN (UITWONENDE |THUISWONENDE )?KINDEREN\b",                       "dem_has_chd",     "1",         "persons with children", ""),
    (r"INDIEN GEHUWD",                                                       "dem_mar",         "1",         "married persons", ""),
    (r"INDIEN GODSDIENST/KERK/RELIGIE|INDIEN GELOVIG",                       "rel_any",         "1",         "persons who belong to a religion", "920"),
]

# municipality codes of the source -> CBS code and name, 2006 list (crosswalks/municipalities.csv)
MUNICIPALITIES = {
    1: ('0363', 'Amsterdam'),
    2: ('0599', 'Rotterdam'),
    3: ('0518', "'s-Gravenhage"),
    4: ('0344', 'Utrecht'),
    5: ('0772', 'Eindhoven'),
    6: ('0153', 'Enschede'),
    8: ('0034', 'Almere'),
    10: ('0484', 'Alphen aan den Rijn'),
    11: ('0748', 'Bergen op Zoom'),
    13: ('0018', 'Hoogezand-Sappemeer'),
    15: ('0503', 'Delft'),
    16: ('0505', 'Dordrecht'),
    17: ('0281', 'Tiel'),
}
