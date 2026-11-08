# -*- coding: utf-8 -*-
"""SIM 2020: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of SIM 2020 are in variables_sim.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""

KW = "20"            # V(..., s20="SOURCEVAR", u20="universe text") in the declaration modules
LABEL = "SIM 2020"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=12, svy_name="SIM2020", svy_year=2020, status="included", key="sim2020", structure="flat",
         title="Survey Integratie Minderheden 2020 (SIM 2020), CCF public version v2", dans_id="easy-dataset:259562", doi="10.17026/dans-26h-xn4n", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Caribbean Dutch (incl. BES); Somalis; Poles (1st generation, registered 2004+); Iranians; native Dutch reference sample",
         fieldwork="Labyrinth Onderzoek & Advies (Mar 2020 - Jan 2021, during covid); SCP", mode="CAWI (90%) with CAPI follow-up for five groups (10%, incl. 15 video interviews); person sample 15+ from the BRP; split-half questionnaire",
         zipfile="Surveys/SIM 2020.zip", file_hh="", file_pp="", file_ro="", file_main="SIM2020 CCF v2.sav", encoding="utf-8-double",
         id_var="Volgnummer", weight_var="eindgewicht", sysmis_tag="d",
         missing_scheme="explicit codes -5 not applicable/routing, -3 don't know, -2 refusal, -4 no answer, -6 don't know/no answer, -1 Farsi questionnaire error; 9 'Anders/Refusal/Don't know' in coarsened (_kl) variables; 92 'anders'")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "cc4518f30693f382739982db33e76cc338fa05a339b1266f70d9aa8a8533ea95"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Persons aged 15+ of Turkish, Moroccan, Surinamese, Caribbean-Dutch, Somali, Polish (first generation registered 2004+), Iranian and native Dutch origin, nationwide BRP sample (CBS); split-half questionnaire (svy_split)."
WEIGHTS = "svy_wgt (eindgewicht): CBS calibration weight scaled to the population."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    # SIM 2020 (Labyrinth conventions + CCF coarsening)
    dict(rule_type="code", match="-5", target=".c", note="'nvt binnen vragenlijst': question not presented (routing, split half, group) - 476,736 cells"),
    dict(rule_type="code", match="-3", target=".a", note="Weet niet"),
    dict(rule_type="code", match="-2", target=".b", note="Wil niet antwoorden"),
    dict(rule_type="code", match="-4", target=".b", note="Geen antwoord"),
    dict(rule_type="code", match="-6", target=".a", note="Weet niet / geen antwoord / wil niet zeggen / neutraal (combined code)"),
    dict(rule_type="code", match="-1", target=".d", note="Wrong question or answer option in the Farsi questionnaire (unless mapped explicitly)"),
    dict(rule_type="label", match="refusal", target=".d", note="'Anders/Refusal/Don't know' (9) in CCF-coarsened _kl variables: other and missing cannot be separated"),
    dict(rule_type="label", match="^weet niet", target=".a", note=""),
    dict(rule_type="label", match="^niet van toepassing$", target=".c", note=""),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    ("main", "data/raw/sim2020/documentatie/SIM2020 Vragenlijst.pdf", "tns", None),
]

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="CAWI (90%) with CAPI follow-up only for the Caribbean, Moroccan, Somali, Surinamese and Turkish groups (10%) because of covid; 15 CAPI interviews by video call (WhatsApp). Fieldwork 11 March 2020 - 17 January 2021 with CAPI suspended during lockdowns."),
    dict(aspect="split_half", text="Respondents randomly assigned within origin group to A or B (svy_split). Only A: political participation (POL_4, HERK_3), institutional trust (VERTWORG), belonging (CONTACTERBIJ, ORGANBIJ), media interest and positioning (NIEUWS_3, FREQNIEU, FREQAANT, POS_4). Only B: opinion statements STELL_8_12 and STELL_1_7_5, religion items BIJBKOR and KORZELFINT, mental health items MENTALGEZ_4_4, 8_3, 8_4, BEZOEKMOG, HUISARTS, PIJN, situational discrimination DISCZELF2, Zwarte Piet items."),
    dict(aspect="order", text="Fixed block order with randomised item order within batteries: Q801-Q804, Q813-Q817, Q895-Q89801, Q965-Q967."),
    dict(aspect="versions", text="Six script versions (svy_qversion); version differences are not documented in the fieldwork report. Early CAWI interviews ran on versions 1-3."),
    dict(aspect="languages", text="Dutch, Turkish, Moroccan Arabic, Polish, Somali, Farsi (svy_lang_q); a Farsi error in two items is flagged in the source (code -1)."),
    dict(aspect="wording", text="Group terms updated: 'allochtoon' -> 'persoon met een migratieachtergrond' in most items; 'autochtone Nederlanders' retained in contact items. Text fills per group (<HERKGRP>, <LVH>)."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    (r"IF NOT (Q)?9001 ?= ?7|Q9001 IS NOT 7",                               "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    (r"Q9004 ?, ?1\b|Q9004 ?= ?1\b|NOT Q9004 ?= ?2\b",                    "dem_gen",         "1",         "first generation (sample-data field GENERATIE: the language, Dutch-course and migration items of SIM 2020 went to the first generation only)", "9004"),
    (r"IF Q920 ?= ?1",                                                       "rel_any",         "1",         "persons who belong to a religion", "920"),
    (r"IF \[?Q43,1\]?",                                                    "dem_has_prtnr",   "1",         "persons with a partner", "43"),
    (r"IF \[?Q35,2",                                                        "dem_sex",         "2",         "women", "35"),
    (r"IF \[?Q500,1\]?|IF WERKZAAM",                                       "lab_emp",         "1",         "persons with paid work", "500"),
    (r"IF \[?Q930,1-5\]?|IF Q930 ?= ?1,2,3,4,5",                           "rel_den_cat",     "2",         "Muslims", "930"),
    (r"MOSLIM OF CHRISTEN",                                                   "rel_den_cat",     "2,3",       "Muslims and Christians", "930"),
    (r"IF SCHOOLGAAND",                                                       "edu_cur_lvl3",    "1,2,3",     "persons currently in education (any level)", ""),
]

# printed conditions the data contradict (crosswalks/routing_exceptions.csv): (source variable regex, gate, reason)
ROUTING_EXCEPTIONS = [
    # source variable (regex),        gate,       reason
    (r"^contacterbij_(studie|buurt)$", "lab_emp",      "the condition 'IF WERKZAAM' governs the sibling item contacterbij_baan (contacts at work), this item was asked regardless of employment"),
    (r"^contacterbij_(baan|buurt)$",   "edu_cur_lvl3", "the condition 'IF SCHOOLGAAND' governs the sibling item contacterbij_studie (contacts at school), this item was asked regardless of enrolment"),
    (r"^oplnl$",                      "edu_cntry",    "printed 'IF NOT Q235=1', the data show the question was asked to all respondents (1,355 values from respondents who reported education abroad only, 291 of them 'ja')"),
    (r"^stemherk2$",                  "dem_eth",      "stemherk2 is the Caribbean variant of Q8531 STEMHERK (linked by name prefix), the printed 'IF Q9001 IS NOT 3, 7' belongs to the origin-country variant, and the data show stemherk2 holds values for Antillean/Aruban respondents only (dem_eth = 4)"),
]

# how a value was obtained, where the automatic rules cannot tell (crosswalks/acquisition_overrides.csv):
# (source variable regex, acquisition, respondent-facing, supplied by, note, instruction text)
ACQ_OVERRIDES = [
    (r"^etngba$",   "registry/sample data", 0, "sample frame / population register (GBA)", "Q9001 is marked [SAMPLE DATA]", ""),
]
