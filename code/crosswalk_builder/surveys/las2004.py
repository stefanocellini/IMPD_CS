# -*- coding: utf-8 -*-
"""LAS 2004/05: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of LAS 2004/05 are in variables_2004_2011.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""
from ._shared import GEN, GENP, ETN, BB, OND

KW = "04"            # V(..., s04="SOURCEVAR", u04="universe text") in the declaration modules
LABEL = "LAS 2004/05"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=7, svy_name="LAS2004", svy_year=2004, status="included", key="las2004", structure="flat",
         title="Leefsituatie Allochtone Stedelingen 2004-2005 (LAS 2004/05)", dans_id="easy-dataset:40215", doi="10.17026/dans-zqg-uqn8", access="request_permission",
         groups="Turks; Moroccans; Surinamese; Antilleans/Arubans; native Dutch reference sample (50 largest municipalities)",
         fieldwork="Veldkamp with TNS NIPO interviewers (Oct 2004 - May 2005); SCP", mode="Face-to-face (CAPI); person sample 15-64 from the GBA of the 50 largest municipalities",
         zipfile="Surveys/LAS 2004 2005.zip", file_hh="", file_pp="", file_ro="", file_main="LAS Leefsituatie Allochtone Stedelingen 2004-2005/LAS 2005.por", encoding="latin1",
         id_var="INTNR", weight_var="WEEGTOT", sysmis_tag="c",
         missing_scheme="explicit codes -7 question block not asked, -5 not applicable (incl. system missing), -3 don't know, -2 refusal/no information, -9 'nvt: autochtoon'; 9/99 'weet niet/geen antwoord' in code lists")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "cb67573d71e1d645e41578f1811517a0ddd2d9e7b2d4a3b7ca8807ca0e93a0bc"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Persons aged 15-64 of Turkish, Moroccan, Surinamese, Antillean/Aruban and native Dutch origin in the 50 largest municipalities (GBA sample, CBS); 228 persons belong to an oversample of working men and women (svy_oversample)."
WEIGHTS = "svy_wgt (weegtot): Veldkamp/SCP weight to the population of the 50 largest municipalities; svy_wgt_grp (weegherk): weight within origin group (mean 1 per group); svy_wgt_raise (ophtot): raising factor to population totals. Diary analyses: tim_wgt / tim_wgt_corr."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    # LAS 2004/05 (Veldkamp .por): -7 block not asked, -5 nvt, -3 weet niet, -2 wil niet zeggen/geen informatie, -4 weet niet (education),
    # -9 'nvt: autochtoon'; positive 9/99/999 'weet niet / geen antwoord' codes caught by label; system-missing = routed (sysmis_tag = c)
    dict(rule_type="code", match="-7", target=".c", note="'vragenblok niet gesteld' (block not asked to this group / version)"),
    dict(rule_type="code", match="-5", target=".c", note="'niet van toepassing'"),
    dict(rule_type="code", match="-3", target=".a", note="'weet niet'"),
    dict(rule_type="code", match="-4", target=".a", note="'weet niet' (education variables)"),
    dict(rule_type="code", match="-2", target=".b", note="'wil niet zeggen, geen informatie'"),
    dict(rule_type="code", match="-9", target=".c", note="'nvt: autochtoon' (native Dutch sample)"),
    dict(rule_type="label", match="^weet niet", target=".a", note="positive 'weet niet (\\ geen antwoord)' codes (9, 99, 999, 9999) unless mapped"),
    dict(rule_type="label", match="^wil niet zeggen", target=".b", note="positive refusal codes (GEZINK 99, STEMWS 14) unless mapped: STEMINT 5 'wil niet zeggen' is a printed answer option and keeps code 5 of vote_int5"),
    dict(rule_type="label", match="geen informatie|^onbekend", target=".d", note="e.g. 99 'geen informatie' in the age classes, 99 'onbekend' in burgst"),
    dict(rule_type="label", match="^niet van toepassing|^nvt|niet gesteld|^sysmis|^volgt geen opleiding|^geen vragenlijst", target=".c", note=""),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    # LAS 2004/05: the questionnaire is appendix 1a of the fieldwork report (pp. 25-91), followed by the show cards and
    # the interviewer instructions (appendix 1b), which repeat the diary questions with form codes
    ("main", "data/raw/las2004/LAS Leefsituatie Allochtone Stedelingen 2004-2005/Bijlage 3 Veldwerkverslag LAS 2004-2005.pdf", "vk_hc",
     (r"^VRAAG 9001\b", r"^KAARTENBOEKJE BEHOREND BIJ")),
]

# constructed variables of the deposit without a questionnaire item (crosswalks/questionnaire_constructed.csv)
CONSTRUCTED = {
        "GEZINPO2": "position in the household (SCP recode of the household roster)", "GENERAT": GEN, "GENPART": GENP,
        "GEZSAMST": "household composition from the household roster", "SAMHSH": "household composition (CBS typology) from the household roster",
        "OPLBLNL": "country where education was followed (Netherlands / abroad / both) from the education history questions",
        "ONDPART": OND, "BERBEV": "labour-force membership from the questions on paid work and hours", "BB_NED": BB,
        "POSWRK": "position in the job (employee / self-employed / ...) from the employment questions", "BERNIV": "occupational level (SCP coding of the occupation description)",
        "URENWRK": "weekly working hours (recode of the hours questions)", "URENWERK": "total weekly working hours of all jobs",
        "MAATPOS": "societal position (SCP typology combining work, education, benefits and household care)",
        "VERDTYP": "earner type of the couple (single / one-and-a-half / dual earner ...) from the respondent's and partner's working hours",
        "GVERDTYP": "preferred earner type of the couple from the respondent's and partner's preferred working hours",
        "DAG": "day of the week covered by the time-use diary (fieldwork administration)",
        "WEEGDAG": "weighting factor for the time-use diary (SCP)", "WEEGDAGC": "weighting/correction factor for the time-use diary (SCP)",
    }

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="Face-to-face CAPI interviews (Veldkamp with TNS NIPO interviewers) with persons aged 15-64 sampled by CBS from the GBA of the 50 largest municipalities (Turks, Moroccans, Surinamese, Antilleans/Arubans, native Dutch); only the sampled person was interviewed. Fieldwork October 2004 - May 2005; corrected response 45% (Turks 47%, Moroccans 44%, Surinamese 38%, Antilleans 47%, natives 50%). An extra sample of working mothers with children under 12 was drawn in March 2005 in nine municipalities and the working partners of male Turkish, Moroccan and Antillean respondents with young children were asked a supplementary interview (47 cases; items marked '+ P' in the questionnaire, of which only dem_prtnr_flex survives as a separate variable); svy_oversample flags the resulting oversample of working men and women (228 cases)."),
    dict(aspect="order", text="Fixed block order A-X; no rotation or randomisation reported. Questions on the murder of Theo van Gogh were added about two weeks into the fieldwork (universe: respondents interviewed after that point)."),
    dict(aspect="routing", text="One programmed questionnaire with group routing (INDIEN ALLOCHTOON / AUTOCHTOON / TURK, MAROKKAAN / MOSLIM / NIET IN NEDERLAND GEBOREN); the native reference sample skips the migration, language, integration and Islam blocks (.c). The time-use diary (block X) was administered by the interviewer at the end of the interview, for 'yesterday', in 72 quarter-hour slots from 06:00 to 24:00 with a 43-code activity card (tim_slot01-72, tim_act01-43; day of the week in tim_weekday, diary weights tim_wgt and tim_wgt_corr); it was skipped when the interview had run long and completed by 74% of respondents (Turks 71%, Moroccans 65%, natives 87%)."),
    dict(aspect="languages", text="Written Turkish and Moroccan-Arabic translations (two independent translators, reconciled with SCP) supported interviews in Dutch; respondents with language problems were re-approached by 17 Turkish and Moroccan interviewers (128 interviews)."),
    dict(aspect="release", text="The DANS file holds the questionnaire variables, SCP constructs (societal position, earner type, labour-force status) and weights (svy_wgt, svy_wgt_grp, svy_wgt_raise); no registry linkage. The questionnaire itself is appendix 1a of the deposited fieldwork report."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    # pattern (case-insensitive regex on the routing text),                    gate,              allowed,     description, Q-references the rule consumes
    (r"INDIEN ALLOCHTOON",                                                   "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "9001"),
    (r"INDIEN AUTOCHTOON",                                                   "svy_routing_mig", "0",         "native reference sample (native routing)", "9001"),
    (r"INDIEN TURK, ?MAROKKAAN",                                             "dem_eth",         "1,2",       "Turkish and Moroccan respondents", ""),
    (r"INDIEN MOSLIM",                                                       "rel_den_cat",     "2",         "Muslims", ""),
    (r"INDIEN VROUW",                                                        "dem_sex",         "2",         "women", "35"),
    (r"INDIEN (BETAALD WERK|WERKEND)",                                       "lab_emp",         "1",         "persons with paid work", "500"),
    (r"INDIEN GEEN (BETAALD )?WERK",                                         "lab_emp",         "0",         "persons without paid work", ""),
    (r"INDIEN (?!NIET )(GEHUWD OF SAMENWONEND|PARTNER\b)",                   "dem_prtnr_st",    "1,2,3,4",   "persons with a partner - married, cohabiting or living apart together: the LAS data show the 'GEHUWD OF SAMENWONEND' items were asked to LAT partners as well", ""),
    (r"INDIEN NIET GEHUWD OF SAMENWONEND",                                   "dem_prtnr_st",    "0,4",       "persons without a co-resident partner", ""),
    (r"INDIEN (UITWONENDE |THUISWONENDE )?KINDEREN\b",                       "dem_has_chd",     "1",         "persons with children", ""),
    (r"INDIEN GODSDIENST/RELIGIE",                                           "rel_any",         "1",         "persons who belong to a religion", ""),
    (r"INDIEN NIET (IN NEDERLAND )?GEBOREN",                                 "dem_gen",         "1",         "first generation (born abroad)", "20"),
]

# how a value was obtained, where the automatic rules cannot tell (crosswalks/acquisition_overrides.csv):
# (source variable regex, acquisition, respondent-facing, supplied by, note, instruction text)
ACQ_OVERRIDES = [
    (r"^TAALINT$",  "interview administration", 0, "interviewer", "block instruction VRAAG 404-406: the questions must not be put to the respondent but answered by the interviewer",
     "ENQ.: De volgende vragen dienen niet aan de respondent gesteld te worden maar moeten door u beantwoord worden. In welke taal is het gesprek gevoerd met de respondent?"),
    (r"^DAT(DAG|MND)$", "interview administration", 0, "interviewer", "date of the interview noted by the interviewer", ""),
    (r"^ETNGRP$",   "registry/sample data", 0, "sample frame (origin group of the register-based sample)", "'Respondent behoort tot volgende groep' is the sample classification shown to the interviewer (the LAS samples were drawn by origin group from the municipal population registers, fieldwork report appendix 1a), not a question", ""),
]
