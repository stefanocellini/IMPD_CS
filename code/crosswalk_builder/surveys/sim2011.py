# -*- coding: utf-8 -*-
"""SIM 2011: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of SIM 2011 are in variables_2004_2011.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""
from ._shared import GEN, GENP, ETN, BB, OND

KW = "11"            # V(..., s11="SOURCEVAR", u11="universe text") in the declaration modules
LABEL = "SIM 2011"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=10, svy_name="SIM2011", svy_year=2011, status="included", key="sim2011", structure="flat",
         title="Survey Integratie Minderheden 2011 (SIM 2011), DANS version V3", dans_id="easy-dataset:67677", doi="10.17026/dans-2a2-77kp", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; native Dutch reference sample",
         fieldwork="GfK with Labyrinth interviewers (Nov 2010 - Apr 2011); SCP; CBS statistical protection (mu-Argus)", mode="Face-to-face (CAPI) main survey (the mixed-mode experiment is not in this deposit); person sample 15+ from the GBA",
         zipfile="Surveys/SIM 2011.zip", file_hh="", file_pp="", file_ro="", file_main="SIM 2011V3.sav", encoding="windows-1252",
         id_var="volgnummer", weight_var="weegtot", sysmis_tag="d",
         missing_scheme="explicit codes -5 not applicable, -3 don't know/no answer, -2 refusal, -4 missing, -1 (undocumented), -9 'nvt: autochtoon'; 9 'niet van toepassing' in some code lists")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "78d8bf29ef6378ed654429c13540994cf9d53e02e06363644c6827f81ed81baa"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Persons aged 15+ of Turkish, Moroccan, Surinamese, Antillean/Aruban and native Dutch origin, nationwide GBA sample stratified by municipality size (CBS); main CAPI study only."
WEIGHTS = "svy_wgt (weegtot): CBS weight to the national population (origin x sex, household size/marital status, municipality stratum, generation, age); svy_wgt_grp (weegherk): within origin group; svy_wgt_raise (ophtot): raising factor."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    # SIM 2011 (Veldkamp CAPI; CBS protection): explicit codes
    dict(rule_type="code", match="-5", target=".c", note="Niet van toepassing: question not asked (routing, group) - 537,139 cells"),
    dict(rule_type="code", match="-3", target=".a", note="Weet niet / geen antwoord"),
    dict(rule_type="code", match="-2", target=".b", note="Wil niet zeggen / geen antwoord"),
    dict(rule_type="code", match="-4", target=".d", note="Missing"),
    dict(rule_type="code", match="-1", target=".c", note="Undocumented code used where a question was not asked (persons with paid work in HFDACT/urencat; a few hours values)"),
    dict(rule_type="code", match="-9", target=".c", note="'nvt: autochtoon' (native Dutch sample)"),
    dict(rule_type="label", match="^niet van toepassing", target=".c", note="Positive codes labelled not applicable (unless mapped)"),
    dict(rule_type="label", match="^weet niet", target=".a", note=""),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    ("main", "data/raw/sim2011/Bijlagen/Bijlage_g_-_Hardcopy_vragenlijst.pdf", "vk_hc", None),
]

# constructed variables of the deposit without a questionnaire item (crosswalks/questionnaire_constructed.csv)
CONSTRUCTED = {
        "ETNGRP": ETN, "GENERAT": GEN, "ONDPART": OND, "BB_NED": BB,
        "MAXDIP1": "highest diploma obtained, 4 classes, respondents not in education (recode of the education questions)",
        "MAXDSCH": "highest diploma obtained so far, including those in education (detailed)", "MAXDSCH1": "highest diploma obtained so far, including those in education, 4 classes",
        "MAXDIPNU": "highest education level including the current education (detailed)", "MAXDIPN1": "highest education level including the current education, 4 classes",
        "URENCAT": "weekly working hours in categories (recode of the hours question)",
        "CATLFT5JR": "age in 5-year classes", "CATLFT5JRPART": "partner's age in 5-year classes",
        **{f"AANT{k}": f"number of residents of {v} origin in the respondent's neighbourhood (CBS neighbourhood count attached by SCP to the sample address)"
           for k, v in [("AUT", "Dutch"), ("MAR", "Moroccan"), ("ANT", "Antillean"), ("ONW", "other non-western"), ("OW", "other western"), ("SUR", "Surinamese"), ("TUR", "Turkish")]},
    }

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="Face-to-face CAPI interviews at home (GfK with Labyrinth co-ethnic interviewers), no proxies, with persons aged 15+ sampled by CBS from the GBA stratified in six municipality strata (Turks, Moroccans, Surinamese, Antilleans/Arubans, native Dutch). Fieldwork from November 2010 for about five months; corrected response Turks 54%, Moroccans 50%, Surinamese 43%, Antilleans 48%, natives 55%; 4,125 interviews. A parallel mixed-mode experiment (web, then telephone, then face-to-face; 2,698 respondents, shortened web questionnaire) is NOT in the DANS deposit: all records have onderzoek = main study and methode = CAPI (svy_fw_phase records the two fieldwork phases, the second being a re-approach of non-respondents by another interviewer)."),
    dict(aspect="order", text="Fixed block order A-U; no rotation or randomisation reported. Ranking question Q1073 (fam_val_rank) asks for a 1-5 order of child-rearing values."),
    dict(aspect="routing", text="Group routing as in SIM 2006 (natives .c for migrant-only items; Islam items to Muslims). Partner items Q53-70, 225, 230 are proxy answers by the respondent. Respondents aged 15-17 were asked to call in a parent for the household questions (suffix _par). The deposit is statistically protected (mu-Argus on sex x 5-year age class) and version 3 removed the open-answer variables; the questionnaire is the hardcopy of the CAPI script (appendix g), which prints variable names next to the questions."),
    dict(aspect="languages", text="Turkish and Moroccan-Arabic translations (SIM 2006 versions reused, new items double-translated); Berber (138 interviews), Papiamento (121) and Surinamese languages (11) used orally as fallback (svy_lang_hh, svy_lang_oth). All Turkish and Moroccan respondents were interviewed by co-ethnic interviewers, Surinamese and Antilleans half by native interviewers."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    (r"INDIEN (RESPONDENT )?ALLOCHTOON",                                     "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    (r"INDIEN (RESPONDENT )?AUTOCHTOON",                                     "svy_routing_mig", "0",         "native reference sample (native routing)", "9001"),
    (r"INDIEN MOSLIM",                                                       "rel_den_cat",     "2",         "Muslims", "930"),
    (r"INDIEN (Q920 ?= ?1|GELOVIG)",                                         "rel_any",         "1",         "persons who belong to a religion", "920"),
    (r"INDIEN VROUW",                                                        "dem_sex",         "2",         "women", "35"),
    (r"INDIEN PARTNER \(Q43 ?= ?1\)",                                      "dem_has_prtnr",   "1",         "persons with a partner", "43"),
    (r"INDIEN BETAALD WERK \(Q500 ?= ?1\)|INDIEN WERKEND",                 "lab_emp",         "1",         "persons with paid work", "500"),
    (r"INDIEN GEEN BETAALD WERK",                                            "lab_emp",         "0",         "persons without paid work", "500"),
    (r"INDIEN NIET IN NEDERLAND GEBOREN",                                    "dem_gen",         "1",         "first generation (born abroad)", "20"),
]

# printed conditions the data contradict (crosswalks/routing_exceptions.csv): (source variable regex, gate, reason)
ROUTING_EXCEPTIONS = [
    (r"^oplblnl$",                     "svy_routing_mig", "oplblnl is a constructed variable (the native reference sample is coded 3 = education in the Netherlands only), the spoken question Q235 was asked to migrants only"),
]
