# -*- coding: utf-8 -*-
"""SIM 2015: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of SIM 2015 are in variables_sim.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""

KW = "15"            # V(..., s15="SOURCEVAR", u15="universe text") in the declaration modules
LABEL = "SIM 2015"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=11, svy_name="SIM2015", svy_year=2015, status="included", key="sim2015", structure="flat",
         title="Survey Integratie Minderheden 2015 (SIM 2015), CCF public version v4", dans_id="easy-dataset:239464", doi="10.17026/dans-x63-dq58", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; Somalis; Poles (1st generation, registered 2004+); native Dutch reference sample",
         fieldwork="TNS NIPO/Veldkamp and Labyrinth (Jan-Jul 2015); SCP", mode="Sequential mixed mode: CAWI, then CAPI; person sample 15+ from the BRP",
         zipfile="Surveys/SIM 2015.zip", file_hh="", file_pp="", file_ro="", file_main="Data/SIM2015_CCF_v4.sav", encoding="utf-8",
         id_var="volgnummer", weight_var="eindgewicht", sysmis_tag="d",
         missing_scheme="explicit codes -2 blanc (routing), -3 don't know/no answer, -5 not applicable, -1/98 refusal, -4 no education, -6/96 'diversen', -7 sysmis; label 2147483622 '[-2]Blanc' never occurs")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "5269492b473f786ed80effa7288bcf223feb20d4d1a65dccadf0dabf1ea3bde5"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Persons aged 15+ of Turkish, Moroccan, Surinamese, Antillean/Aruban, Somali, Polish (first generation registered 2004+) and native Dutch origin, nationwide BRP sample (CBS)."
WEIGHTS = "svy_wgt (eindgewicht): CBS calibration weight scaled to the population; svy_wgt_alt: alternative weighting model; svy_wgt_start: inverse selection probability."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    # SIM 2015 (TNS NIPO conventions)
    dict(rule_type="code", match="-7", target=".", note="Sysmis in SCP-constructed variables"),
    dict(rule_type="code", match="-2", target=".c", note="'blanc': question not presented (routing) - 314,198 cells"),
    dict(rule_type="code", match="-5", target=".c", note="Niet van toepassing"),
    dict(rule_type="code", match="-3", target=".a", note="Weet niet / geen antwoord"),
    dict(rule_type="code", match="-1", target=".b", note="Wil niet zeggen"),
    dict(rule_type="code", match="-4", target=".d", note="'Missing' in SCP-constructed variables; 'geen opleiding' in education items is mapped explicitly (.c)"),
    dict(rule_type="code", match="-6", target=".d", note="'Diversen' in SCP-constructed education variables (uncodable)"),
    dict(rule_type="label", match="^blanc$", target=".c", note=""),
    dict(rule_type="label", match="^wil niet zeggen$", target=".b", note="Code 98 in huisbui"),
    dict(rule_type="label", match="^weet niet", target=".a", note="Labelled don't-know codes incl. 'weet niet \\ niet van toepassing' (99)"),
    dict(rule_type="label", match="^niet van toepassing$", target=".c", note="Codes 4 (inburgering items) and 9 (conherk)"),
    dict(rule_type="label", match="^(sysmis)$", target=".", note=""),
    dict(rule_type="label", match="^missing$", target=".d", note=""),
    dict(rule_type="label", match="^diversen$", target=".d", note="Unless mapped explicitly to an 'other' category (value_map takes precedence)"),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    ("cawi", "data/raw/sim2015/Docu/SIM2015_Vragenlijst_CAWI.pdf", "tns", None),
    ("capi", "data/raw/sim2015/Docu/SIM2015_Vragenlijst_CAPI.pdf", "tns", None),
]
PREFER_INSTRUMENT = "cawi"     # parallel instruments: this one is the reference, the other's differences are kept

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="Sequential mixed mode: web (CAWI) invitation first, face-to-face (CAPI) follow-up of non-respondents by bilingual interviewers (TNS NIPO and Labyrinth); CAWI and CAPI questionnaires are parallel (questionnaire_items.csv holds both; wording.csv references the CAWI version with the CAPI question id in capi_qid)."),
    dict(aspect="order", text="Fixed block order with randomised item order within batteries: Q801-Q815 and Q813-Q817 (opinion statements), Q895-Q89801 (opinions on NL), Q770 contact with groups and Q859-Q865 feeling thermometers (groups presented in random order, own group always last; Jews never first)."),
    dict(aspect="routing", text="Many items asked only to respondents with a migration background (ASK ONLY IF not Q9001=7); the native reference sample gets mirrored wording ('allochtone' instead of 'autochtone' contacts)."),
    dict(aspect="languages", text="Questionnaire available in Dutch, Turkish, Moroccan Arabic, Polish and Somali (CAWI language choice; language variable not in the public file)."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    (r"ASK ONLY IF not Q9001 ?= ?7|not Q9001=7",                             "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    (r"ASK ONLY IF Q920 ?= ?1",                                              "rel_any",         "1",         "persons who belong to a religion", "920"),
    (r"ASK ONLY IF Q930 ?= ?1,2,3,4,5,6",                                    "rel_den_cat",     "2",         "Muslims", "930"),
    (r"ASK ONLY IF Q43 ?= ?1|IF Q43 ?= ?1",                                  "dem_has_prtnr",   "1",         "persons with a partner", "43"),
    (r"ASK ONLY IF Q500 ?= ?1",                                              "lab_emp",         "1",         "persons with paid work", "500"),
    (r"ASK ONLY IF Q35 ?= ?2",                                               "dem_sex",         "2",         "women", "35"),
    (r"not Q20 ?= ?5",                                                       "dem_gen",         "1",         "first generation (born abroad)", "20"),
]

# printed conditions the data contradict (crosswalks/routing_exceptions.csv): (source variable regex, gate, reason)
ROUTING_EXCEPTIONS = [
    (r"^anveel",                       "svy_routing_mig", "the script also prints 'Niet stellen indien (Q9001=7 AND Q766=5 AND Q765=5)', the data show the native reference sample was asked (about four in five natives have values)"),
    (r"^CATreligie$",                  "rel_any",      "CATreligie is a constructed category variable that codes respondents without a religion (Q920 = no) as 0 = none, the spoken question Q930 was asked to religious respondents only"),
    (r"^anveel",                       "soc_cont_nbr_org", "the printed 'ASK ONLY IF not Q766=5 and not Q765=5' is contradicted by the script's own 'Niet stellen indien (Q9001=7 AND Q766=5 AND Q765=5)' and by the data (about one in six values come from respondents with code 5)"),
    (r"^anveel",                       "soc_cont_frnd_org", "the printed 'ASK ONLY IF not Q766=5 and not Q765=5' is contradicted by the script's own 'Niet stellen indien (Q9001=7 AND Q766=5 AND Q765=5)' and by the data (about one in six values come from respondents with code 5)"),
]

# how a value was obtained, where the automatic rules cannot tell (crosswalks/acquisition_overrides.csv):
# (source variable regex, acquisition, respondent-facing, supplied by, note, instruction text)
ACQ_OVERRIDES = [
    (r"^etngba$",   "registry/sample data", 0, "sample frame / population register (GBA)", "the same sample-data field as SIM 2020 Q9001 (variable name etngba = origin group from the GBA; data label 'Respondent behoort tot volgende GROEP')", ""),
]
