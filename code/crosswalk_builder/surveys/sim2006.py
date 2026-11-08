# -*- coding: utf-8 -*-
"""SIM 2006: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of SIM 2006 are in variables_2004_2011.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""
from ._shared import GEN, GENP, ETN, BB, OND

KW = "06"            # V(..., s06="SOURCEVAR", u06="universe text") in the declaration modules
LABEL = "SIM 2006"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=8, svy_name="SIM2006", svy_year=2006, status="included", key="sim2006", structure="flat",
         title="Survey Integratie Minderheden 2006 (SIM 2006)", dans_id="easy-dataset:40304", doi="10.17026/dans-2z9-6eqc", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; native Dutch reference sample",
         fieldwork="Veldkamp / TNS NIPO, ERC for Turkish and Moroccan interviews (Mar 2006 - Jan 2007); SCP", mode="Face-to-face (CAPI); nationwide person sample 15+ from the GBA (CBS, at least 10 addresses per municipality)",
         zipfile="Surveys/SIM 2006.zip", file_hh="", file_pp="", file_ro="", file_main="SIM Survey Immigration Minorities 2006/SIM2006_c1_dans230909 edit_1_beveiligd.sav", encoding="utf-8",
         id_var="impd_rownum", weight_var="WEEGTOT", sysmis_tag="c",
         missing_scheme="explicit codes -5 not applicable, -3 don't know, -2 refusal/no answer, -7 not in questionnaire, -8 wrongly unanswered, -1 (undocumented), -9 'nvt: autochtoon'; system missing = routing")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "5c666899708dcc2900dbfa1861bfaedcb9faa9ae2aac05974664491e61001d31"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Persons aged 15+ of Turkish, Moroccan, Surinamese, Antillean/Aruban and native Dutch origin, nationwide GBA sample (CBS)."
WEIGHTS = "svy_wgt (weegtot): CBS weight to the national population of the five groups; svy_wgt_grp (weegherk): within origin group; svy_wgt_raise (ophtot): raising factor."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    # SIM 2006 (Veldkamp): explicit codes in some variables, system-missing for most routing (surveys.csv sysmis_tag = c)
    dict(rule_type="code", match="-5", target=".c", note="'niet van toepassing'"),
    dict(rule_type="code", match="-3", target=".a", note="'weet niet'"),
    dict(rule_type="code", match="-2", target=".b", note="'wil niet zeggen/geen opgave'"),
    dict(rule_type="code", match="-7", target=".c", note="'niet in vragenlijst': item not in the questionnaire version of this group"),
    dict(rule_type="code", match="-8", target=".d", note="'ten onrechte niet beantwoord' (interview program error)"),
    dict(rule_type="code", match="-4", target=".d", note="'missing'"),
    dict(rule_type="code", match="-9", target=".c", note="'nvt: autochtoon' (native Dutch sample)"),
    dict(rule_type="label", match="^niet van toepassing|^nvt", target=".c", note="Positive codes labelled not applicable (unless mapped)"),
    dict(rule_type="label", match="^weet niet", target=".a", note=""),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    ("main", "data/raw/sim2006/SIM Survey Immigration Minorities 2006/V3996 klvr 9 aug.pdf", "vk_script", None),
]
LINK_BY_QNUM = True      # questionnaire without variable names: link by the question number in the data label

# constructed variables of the deposit without a questionnaire item (crosswalks/questionnaire_constructed.csv)
CONSTRUCTED = {
        "ETNGRP": ETN, "GENERAT": GEN, "ETNPART": "partner's " + ETN, "GENPART": GENP,
        "GRPLS": "size class of the municipality of residence (CBS, from the sample address)", "ONDPART": OND,
        "MAXDIP1": "highest diploma obtained, 4 classes, respondents not in education (recode of the education questions)",
        "MAXDIPN1": "highest education level, 4 classes, including the current education of those still in education",
        "BB_NED": BB, "UITKEER": "receives a benefit (any of the benefit questions)", "URENCAT": "weekly working hours in categories (recode of the hours question)",
        "INKCAT": "monthly income in categories (recode of the income questions)",
    }

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="Face-to-face CAPI interviews (Veldkamp/TNS NIPO, with ERC interviewers for Turkish and Moroccan respondents) with persons aged 15+ sampled by CBS from the GBA nationwide (at least 10 addresses per municipality); a paper version existed for interviewers without a laptop. Fieldwork March 2006 - January 2007; corrected response 53% (Moroccans 50%, Turks 60%, Antilleans 54%, Surinamese 46%, natives 55%); 5,250 interviews. Part of the sample received two postage stamps with the invitation letter as an incentive experiment."),
    dict(aspect="order", text="Fixed block order A-P; no rotation or randomisation reported."),
    dict(aspect="routing", text="Only the sampled person answered (the partner could be present). Items on Islam were routed to Muslims by the script; a respondent counted as native Dutch when both parents were born in the Netherlands. Answer cards were collected in a card booklet and read out literally. The deposited questionnaire is the CAPI script printout, which carries no variable names: items are linked to the data through the question number in the data labels and the option order of multiple-response questions."),
    dict(aspect="languages", text="Turkish and Moroccan-Arabic written translations (one translator, independent check); first-generation Turks and Moroccans who arrived at 15 or older were assigned to co-ethnic interviewers where possible, with gender matching."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    (r"IF \[ (?!#)\s*Q9001 , 1 TO 4(?! ?,)",                                "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    (r"IF \[ # ?Q9001 , 5(?! ?,)",                                          "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    (r"IF \[ (?!#)\s*Q9001 , 5(?! ?,)",                                    "svy_routing_mig", "0",         "native reference sample (native routing)", "9001"),
    (r"IF \[ (?!#)\s*Q9001 , 1 , 2(?! ?,)",                                "dem_eth",         "1,2",       "Turkish and Moroccan respondents", "9001"),
    (r"IF \[ (?!#)\s*Q9001 , 3 , 4 , 5(?! ?,)",                            "dem_eth",         "3,4,90",    "Surinamese, Antillean and native Dutch respondents", "9001"),
    (r"IF \[ (?!#)\s*Q35 , 2(?! ?,)",                                      "dem_sex",         "2",         "women", "35"),
    (r"IF \[ (?!#)\s*Q43 , 1(?! ?,)",                                      "dem_prtnr_st",    "1,2,3,4",   "persons with a partner", "43"),
    (r"IF \[ (?!#)\s*Q500 , 1(?! ?,)",                                     "lab_emp",         "1",         "persons with paid work", "500"),
    (r"IF \[ (?!#)\s*Q920 , 1(?! ?,)",                                     "rel_any",         "1",         "persons who belong to a religion", "920"),
    (r"IF \[ (?!#)\s*Q930 , 1 TO 6(?! ?,)",                                "rel_den_cat",     "2",         "Muslims", "930"),
]
