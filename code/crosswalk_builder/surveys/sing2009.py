# -*- coding: utf-8 -*-
"""SING 2009: survey setup - registry entry, missing-value conventions, questionnaire, routing and the
other survey-level declarations the crosswalk builder needs.  Collected by surveys/__init__.py; see
docs/harmonization.md, "Adding a survey".

The variable declarations of SING 2009 are in variables_2004_2011.py (written before the one-file-per-survey layout); a survey
added later keeps its declarations in this file, in declare() below."""
from ._shared import GEN, GENP, ETN, BB, OND

KW = "09"            # V(..., s09="SOURCEVAR", u09="universe text") in the declaration modules
LABEL = "SING 2009"

# registry entry (crosswalks/surveys.csv); svy_id is the chronological position
SURVEY = dict(svy_id=9, svy_name="SING2009", svy_year=2009, status="included", key="sing2009", structure="flat",
         title="Survey Integratie Nieuwe Groepen 2009 (SING 2009), CBS-protected public version", dans_id="easy-dataset:51530", doi="10.17026/dans-xnn-ky48", access="request_permission",
         groups="Afghans; Iraqis; Iranians; Somalis; Poles; Chinese; native Dutch reference sample",
         fieldwork="Veldkamp / TNS NIPO (Feb 2009 - Feb 2010); SCP; CBS sample and statistical protection", mode="Face-to-face (CAPI); person sample 15+ from the GBA; only the questions listed in the deposit's READ ME are released, years and durations in classes",
         zipfile="Surveys/SING 2009.zip", file_hh="", file_pp="", file_ro="", file_main="SINGDANS veilig.por", encoding="latin1",
         id_var="impd_rownum", weight_var="WEEGHERK", sysmis_tag="c",
         missing_scheme="system missing = routing / not released; labelled codes 7/97 'weet niet' or 'geen antwoord, wil niet zeggen', 8/9/98/99 'niet van toepassing'")

# sha256 of the DANS zip as downloaded (used when the zip is not present)
ZIP_SHA256 = "b4d3aea4cf56a8e7671e1dc5203878cf3764b30024b29aeb4b664b25304bb774"

# eligible sample / target population and weight guidance (codebook section 1, surveys.csv)
ELIGIBLE = "Persons aged 15+ of Afghan, Iraqi, Iranian, Somali, Chinese, Polish (short-stay, registered < 5 years) and native Dutch origin, nationwide two-stage GBA sample (CBS); partial release (see section 3)."
WEIGHTS = "svy_wgt = svy_wgt_grp (weegherk): within-origin-group weight, the only general weight in the deposit; svy_wgt_pool: separate weight for the short-stay Polish sample. No weight to a pooled national population is supplied."

# missing-value conventions of the source file (crosswalks/missing_rules.csv): rule_type 'code' (an explicit code),
# 'label' (a regex on the value label) or 'declared' (SPSS user-missing codes); target .a .b .c .d or '.' (plain missing)
MISSING_RULES = [
    # SING 2009 (Veldkamp .por, CBS-protected): positive labelled codes only
    dict(rule_type="label", match="^weet niet", target=".a", note="7/8/96 'weet niet' (also 'weet niet \\ geen antwoord')"),
    dict(rule_type="label", match="^geen antwoord|wil niet zeggen", target=".b", note="6/7/97/98/997/99997 'geen antwoord / wil niet zeggen'"),
    dict(rule_type="label", match="^niet van toepassing|^nvt", target=".c", note="8/9/98/99/998/999/9998/9999: routing and the native sample"),
]

# questionnaire PDF(s) parsed by questionnaires.py: (instrument, path relative to the project root, parser, (start, end) regexes or None)
QUESTIONNAIRES = [
    ("main", "data/raw/sing2009/SING09-VRAGENLIJST_LAATSTE VERSIE nov09.pdf", "vk_script", None),
]
LINK_BY_QNUM = True      # questionnaire without variable names: link by the question number in the data label

# constructed variables of the deposit without a questionnaire item (crosswalks/questionnaire_constructed.csv)
CONSTRUCTED = {
        "ETNGRP": ETN, "GENERAT": GEN, "ETNGRPPA": "partner's " + ETN, "GENPART": GENP, "BB_NED": BB,
        "UURWRKC4": "contractual working hours in 4 categories (recode of the hours question)",
        "MAXDIPN1": "highest education level, including the current education of those still in education (recode of the education questions)",
        "VERBLIJF": "length of stay in the Netherlands (year of interview minus year of arrival)",
        "LFTCAT3": "age in 3 categories", "LFTPARTC": "partner's age in 3 categories",
        "BMI": "body mass index from self-reported height and weight, respondents 18 and over",
    }

# design features printed in codebook section 3.2 (crosswalks/questionnaire_design.csv)
DESIGN = [
    dict(aspect="mode", text="Face-to-face CAPI interviews (Veldkamp/TNS NIPO; 243 native and 60 bilingual interviewers) with persons aged 15+ sampled by CBS from the GBA in two stages (municipalities, then persons): Afghans, Iraqis, Iranians, Somalis, Chinese, Poles and a native Dutch reference sample. The Polish sample was redesigned after a pilot to short-stay Poles (less than five years registered), 532 of whom completed a Polish self-completion version on the interviewer's laptop. Fieldwork February 2009 - February 2010; corrected response 43% (Iranians 44%, Iraqis 48%, Afghans 49%, Somalis 38%, Chinese 38%, Poles 42%, natives 46%); 6,911 interviews."),
    dict(aspect="order", text="Fixed block order A-U; no rotation reported. One item, Q2630 (leisure-time contact with native Dutch, soc_leis_nl), was asked to a random half of the respondents with a migration background (CAPI script field exp2431 = 1); the deposit documents neither the split nor an indicator for it, so the half is visible only as .c on that variable (3,017 of 5,952 asked; the follow-up Q2640 went to both halves)."),
    dict(aspect="routing", text="Natives skip the migration-history and civic-integration blocks (shorter questionnaire, 40 instead of 56 minutes); Chinese respondents could skip the religion items. Respondents aged 15-17 were asked to call in a parent for the household-income questions (hh_inc_band_par). The deposited questionnaire is the CAPI script printout without variable names (linked via the question numbers in the data labels)."),
    dict(aspect="languages", text="Questionnaire, letter and folder translated into Farsi, Arabic, Dari, Somali, Chinese and Polish (DaVinci Vertalingen, checked by co-ethnic interviewers) and programmed in CAPI; short-stay respondents were approached by bilingual interviewers where possible."),
    dict(aspect="release", text="Partial release: the DANS file contains only the questions listed in the deposit's READ ME (the rest is available through CBS Remote Access), and years and durations are coarsened into classes: age and partner's age in 3 classes (15-24, 25-44, 45+), length of stay 0-5/5-10/10-15/15+ years, year of marriage and of first arrival in decade bands, contractual hours in 4 classes, education in 4 classes. The IMPD keeps these as the SING-only `_cat` variants (e.g. dem_age_cat3, mig_dur_nl_cat4). The release is also statistically protected: in some variables real values are replaced by 'don't know' / 'not applicable' / 'other' codes (sex for 2 respondents, marital status 71, origin group 85 - the 'unknown' group -, generation 29 besides the natives, year of marriage 39, small categories of the household-position items recoded to 98), household size and the number of children are top-coded at 6, and the BMI is delivered in classes; the resulting .d / unknown values are protection, not non-response. The CBS microdata hold the unprotected values."),
]

# printed routing conditions -> harmonized gate variables (crosswalks/routing_rules.csv):
# (pattern on the routing text, gate variable, allowed codes, description, question numbers the rule consumes)
ROUTING_RULES = [
    (r"INDIEN \[ # ?Q40 , 8(?! ?,)",                                        "svy_routing_mig", "1",         "persons with a migration background (migrant routing of the script)", "40,9001"),
    (r"INDIEN \[ (?!#)\s*Q80 , 2(?! ?,)",                                  "dem_sex",         "2",         "women", "80"),
    (r"INDIEN \[ (?!#)\s*Q860 , 1(?! ?,)",                                 "lab_emp",         "1",         "persons with paid work", "860"),
    (r"INDIEN \[ (?!#)\s*Q2990 , 1(?! ?,)",                                "rel_any",         "1",         "persons who belong to a religion", "2990"),
    (r"INDIEN \[ (?!#)\s*Q3000 , 1 TO 6(?! ?,)",                           "rel_den_cat",     "2",         "Muslims", "3000"),
]
