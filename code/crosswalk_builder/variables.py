# -*- coding: utf-8 -*-
"""
IMPD crosswalk builder — variable map and value maps.

Every harmonized (target) variable is declared once with V(...).  The declaration
records, for each source survey, which source variable feeds the target, which value
set labels it, the universe (who was asked), and free-text harmonization notes.

Value-level recodes are declared with M(...) (one row per source code or code range) and
written to value_map.csv.  Codes NOT listed in value_map pass through unchanged (after the
missing-value rules in missing_rules.csv have been applied).

Surveys declared here: "spva2002" (DANS P1684), "spvn2003" (DANS P1753).  SIM 2015 / SIM 2020
(DANS CCF deposits) are declared in variables_sim.py, which re-uses the targets defined here.
"""
from valuesets import VALUESETS, vs
from declare import V, M, W, L, U, ASKED, VARS, VMAP, WORDING_NOTES, WORDING_LINKS, SURVEY_KEYS

S02, S03 = "spva2002", "spvn2003"
U_HEAD = "Heads of household (main questionnaire)"
U_INT = "All interviewed persons aged 12+ (main and mini questionnaire)"
U_ALL = "All household members (roster)"
U_HEAD03 = "Heads of household (main questionnaire), SPVN 2003 only"
U_HEAD02 = "Heads of household (main questionnaire), SPVA 2002 only"
U_INT02 = "All interviewed persons, SPVA 2002 only"
U_INT03 = "All interviewed persons, SPVN 2003 only"

# ============================================================== country code list
# Harmonized country codes follow the Dutch GBA/BRP "Landentabel" (Tabel 34, RVIG), see
# External/Country codes/landentabel34.csv.  Project-specific codes: 9901 other Africa,
# 9902 other Asia, 9903 other Europe, 9998 unidentifiable name in source, 9999 other country.
COUNTRY = {
    6030: "Netherlands", 6043: "Turkey", 5022: "Morocco", 5007: "Suriname", 7011: "Netherlands Antilles / Aruba / Caribbean Netherlands (aggregate)",
    6023: "Afghanistan", 5043: "Iraq", 5012: "Iran", 6045: "Yugoslavia (former)", 6013: "Somalia",
    7054: "United Arab Emirates", 6047: "Algeria", 5097: "Azerbaijan", 5057: "Bahrain", 5010: "Belgium", 7024: "Bulgaria",
    5001: "Canada", 6022: "China", 5040: "Cyprus", 5015: "Denmark", 9087: "Djibouti", 6029: "Germany", 7014: "Egypt",
    6039: "United Kingdom", 9003: "Eritrea", 5020: "Ethiopia", 5002: "France", 6003: "Greece", 5017: "Hungary", 7046: "India",
    6034: "Israel", 7044: "Italy", 5030: "Ivory Coast", 7035: "Japan", 5048: "Yemen", 6042: "Jordan", 5099: "Kazakhstan",
    7002: "Kenya", 7045: "Kuwait", 5051: "Croatia", 7043: "Lebanon", 6006: "Libya", 5100: "Macedonia", 7026: "Malaysia",
    5104: "Montenegro", 5013: "New Zealand", 6027: "Norway", 6038: "Ukraine", 6050: "Uzbekistan", 5009: "Austria",
    7020: "Pakistan", 7028: "Poland", 9037: "Qatar", 7047: "Romania", 5053: "Russia", 5018: "Saudi Arabia", 5103: "Serbia",
    5037: "Singapore", 5049: "Slovenia", 7034: "Sudan", 6037: "Spain", 7009: "Syria", 6057: "Tajikistan", 7031: "Tanzania",
    6066: "Czech Republic", 6063: "Turkmenistan", 6014: "United States", 5028: "Zambia", 5039: "Sweden", 5003: "Switzerland",
    5054: "Armenia", 7036: "Hong Kong", 6024: "Indonesia", 6021: "Kyrgyzstan", 6020: "Mauritania", 6000: "Moldova",
    7042: "Thailand", 5050: "Zaire (Congo-Kinshasa)", 6036: "South Korea", 6065: "Bosnia and Herzegovina", 5027: "Philippines",
    7066: "Lithuania", 6018: "Luxembourg", 5098: "Belarus", 6067: "Slovakia",
    9901: "Other Africa", 9902: "Other Asia", 9903: "Other Europe", 9998: "Unidentifiable country name in source", 9999: "Other country (unspecified)",
}
vs("country", sorted(COUNTRY.items()))

# Dutch name (as spelled in the SPVN 2003 transit-country code lists) -> Landentabel code
NL2CODE = {
    "Verenigde Arabische Emiraten": 7054, "Afghanistan": 6023, "Algerije": 6047, "Azerbeidjan": 5097, "Bahrein": 5057,
    "Bakestan": 9998, "Belgie": 5010, "Bulgarije": 7024, "Canada": 5001, "China": 6022, "Cyprus": 5040, "Denemarken": 5015,
    "Djibouti": 9087, "Duitsland": 6029, "Egypte": 7014, "Engeland": 6039, "Eritrea": 9003, "Ethiopie": 5020, "Frankrijk": 5002,
    "Griekenland": 6003, "Hongarije": 5017, "India": 7046, "Irak": 5043, "Iran": 5012, "Israel": 6034, "Italie": 7044,
    "Ivoorkust": 5030, "Japan": 7035, "Jemen": 5048, "Joegoslavie": 6045, "Jordanie": 6042, "Kazachstan": 5099, "Kenia": 7002,
    "Koeweit": 7045, "Kroatie": 5051, "Libanon": 7043, "Libie": 6006, "Macedonie": 5100, "Maleisie": 7026, "Marokko": 5022,
    "Montenegro": 5104, "Nieuw-Zeeland": 5013, "Noorwegen": 6027, "Oekraine": 6038, "Oezbekistan": 6050, "Oostenrijk": 5009,
    "Pakistan": 7020, "Polen": 7028, "Quatar": 9037, "Roemenie": 7047, "Rusland": 5053, "Saoedi-Arabie": 5018, "Servie": 5103,
    "Singapore": 5037, "Slovenie": 5049, "Soedan": 7034, "Somalie": 6013, "Spanje": 6037, "Syrie": 7009, "Tajikistan": 6057,
    "Tanzania": 7031, "Tsjechie": 6066, "Turkije": 6043, "Turkmenistan": 6063, "Verenigde Staten": 6014, "Zambia": 5028,
    "Zweden": 5039, "Zwitserland": 5003, "Armenie": 5054, "Hong Kong": 7036, "Indonesie": 6024, "Kirgizie": 6021,
    "Mauretanie": 6020, "Moldavie": 6000, "Thailand": 7042, "Zaire": 5050, "Zuid-Korea": 6036, "Bosnie": 6065,
    "Filipijnen": 5027, "Litouwen": 7066, "Luxemburg": 6018, "Wit-Rusland": 5098, "Slowakije": 6067,
    "Overig Afrika": 9901, "Overig Azie": 9902, "Overig Europa": 9903, "Onbekend": ".d",
}

def country_map(target, survey, src, pairs):
    for code, tgt in pairs:
        M(target, survey, src, code, tgt)

BC02 = [(1, 6043), (2, 5022), (3, 5007), (4, 7011), (5, 6030), (8, 9999)]
BC03 = [(1, 6023), (2, 5043), (3, 5012), (4, 6045), (5, 6013), (6, 6030), (7, 9999)]
ETH02 = [(1, 1), (2, 2), (3, 3), (4, 4), (6, 90), (9, 99)]
ETH03 = [(1, 5), (2, 6), (3, 7), (4, 8), (5, 9), (6, 90), (9, 99)]

# ============================================================== id_ / svy_
V("id_person", "id", "Unique person identifier (svy_key*1e11 + source person/record number; household samples: id_hh*100 + member number)", type="id",
  universe=U_ALL, derive="id_person", notes="Constructed; unique across surveys and unchanged when a survey is added (svy_key = fieldwork year, never renumbered; surveys.csv). Stored as double.")
V("id_hh", "id", "Unique household identifier (svy_key*1e9 + source household number)", type="id", universe=U_ALL,
  derive="id_hh", notes="Constructed; unique across surveys and unchanged when a survey is added. Stored as double.")
V("id_hh_src", "id", "Household number as in source file", "HHNUMMER", "HHNUMMER", type="id", universe=U_ALL,
  notes="Source household number; not unique across surveys - use id_hh.")
V("id_mem", "id", "Household member number within household", "GEZLIDNR", "GEZLIDNR", "member_number", universe=U_ALL,
  notes="0 = head, 1-9 = children by age rank, 10 = partner, 11-18 = other members.")

V("svy_id", "svy", "Survey (wave) identifier", valueset="survey", universe=U_ALL, derive="svy_id",
  notes="Numbered chronologically; the registry of surveys is crosswalks/surveys.csv.")
V("svy_name", "svy", "Survey (wave) name", type="str", universe=U_ALL, derive="svy_name")
V("svy_year", "svy", "Fieldwork year", type="num", universe=U_ALL, derive="svy_year",
  notes="SPVA 2002 fieldwork ran 2002-2003; SPVN 2003 fieldwork 2003.")
V("svy_routing_mig", "svy", "Received the migrant-background routing of the CAPI script (person samples)", valueset="yesno", universe="Individually sampled respondents (LAS 2004/05, SIM 2006, SING 2009, SIM 2011, SIM 2015, SIM 2020)", derive="routing_mig",
  notes="Derived: 1 when any of the gate items asked only to persons with a migration background carries an answer (lang_prob_spk, lang_prob_read, iden_scale, iden_orig5, int_crs, int_nlcrs, trn_house, med_krant_orig_cat; items that some survey asks to natives, such as ret_wish in SING 2009 or iden_nl5 in SIM 2020, are not gates), 0 otherwise. "
        "The scripts route on the sample-frame origin group, which the deposits do not deliver; dem_eth is the self-reported group (SCP construction from the respondent's and parents' countries of birth). Self-reported natives with routing 1 were sampled in a migrant group (LAS 24, SIM 2011 23, SING 3); their answers are kept. The universe check uses this flag instead of a tolerance.")
V("svy_resptype", "svy", "Respondent type", valueset="resptype", universe=U_ALL, derive="svy_resptype",
  notes="1 if present in the heads file, 2 if present in the interviewed-persons file but not head, 3 if roster only.")
V("svy_wgt", "svy", "Survey weight (as supplied by ISEO/SCP)", "WEEG", "WEEG", type="num", universe=U_ALL,
  notes="SPVA 2002: WEEG missing for 2,063 roster-only persons; weights constructed on demographic population data (see DANS documentation 2.8.3). Weights are survey-specific and not comparable across surveys.")
V("svy_proxy", "svy", "Who answered the (mini) questionnaire", "WIEGESPR", "WIEGESPR", "proxy", universe=U_INT,
  notes="SPVA 2002 code 8 (unlabelled in source) = no mini questionnaire, only the cultural-integration module (one child aged 15+ per household), per DANS documentation.")
V("svy_lang_hh", "svy", "Language of the interview with the head of household", "TAALINT", "TAALINTA", "lang_interview", universe=U_HEAD,
  notes="SPVA 2002: 5-point Dutch/own-language mix (0 = partner not interviewed, kept). SPVN 2003: Dutch/English/French/own language mapped to 1/6/7/5.")
M("svy_lang_hh", S03, "TAALINTA", 1, 1); M("svy_lang_hh", S03, "TAALINTA", 2, 6)
M("svy_lang_hh", S03, "TAALINTA", 3, 7); M("svy_lang_hh", S03, "TAALINTA", 4, 5)
V("svy_lang_prtnr", "svy", "Language of the interview with the partner", "TAALINTP", "TAALINPA", "lang_interview", universe=U_HEAD,
  notes="See svy_lang_interview.")
M("svy_lang_prtnr", S03, "TAALINPA", 1, 1); M("svy_lang_prtnr", S03, "TAALINPA", 2, 6)
M("svy_lang_prtnr", S03, "TAALINPA", 3, 7); M("svy_lang_prtnr", S03, "TAALINPA", 4, 5)
V("svy_lang_q", "svy", "Language version of questionnaire selected", None, "TAALSEL", "lang_questionnaire", universe=U_HEAD03)
V("svy_prtnr_avail", "svy", "Availability of partner at interview", "VRAGPART", None, "partner_avail", universe=U_HEAD02)
V("svy_fup", "svy", "Willing to take part in follow-up research", "VERVOLG", "VERVOLG", "yesno", universe=U_HEAD, yn12=True)
V("svy_panel1st", "svy", "First SPVA wave in which the person participated (panel component)", "PANEL", None, "panel_first", universe=U_INT02,
  notes="22% of SPVA 2002 respondents also took part in 1998 (DANS metadata).")
V("svy_selfsel", "svy", "Person recruited via the self-search (snowball) method", "ZELFZOEK", None, "yesno", universe=U_INT02,
  notes="Source codes 1 = via self-search method, else system-missing; system-missing set to 0 for interviewed persons (derive fill0_interviewed).",
  derive="fill0_interviewed")
M("svy_selfsel", S02, "ZELFZOEK", 1, 1)

# ============================================================== dem_
V("dem_sex", "dem", "Sex", "GESLACHT", "GESLACHT", "sex", universe=U_ALL)
V("dem_age", "dem", "Age in years", "LEEFTIJD", "LEEFTIJD", type="num", universe=U_ALL,
  notes="SPVN 2003: for 17 interviewed persons the roster (head-reported) age differs from the self-reported age; the self-report is used (see harmonization log).")
V("dem_age_c5", "dem", "Age in 5-year classes (source recode)", "LEEFTD1", "LEEFTD1", type="cat", universe=U_ALL, include=0,
  notes="Pure recode of dem_age - retained in source file only.")
V("dem_age_c1564", "dem", "Age classes 15-64 (source recode)", "LEEFTD2", "LEEFTD2", universe=U_ALL, include=0, notes="Pure recode of dem_age.")
V("dem_age_c15p", "dem", "Age classes 15+ (source recode)", "LEEFTD3", "LEEFTD3", universe=U_ALL, include=0, notes="Pure recode of dem_age.")
V("dem_poshh", "dem", "Position in the household", "POSHH", "POSHH", "pos_household", universe=U_ALL)
V("dem_posfam", "dem", "Position in the family", "GEZINPOS", "GEZINPOS", "pos_family", universe=U_ALL)
V("dem_eth", "dem", "Ethnic group (person level, survey target-group definition)", "ETNGRP", "ETNGRP", "ethgroup", universe=U_ALL,
  notes="Survey definitions: SPVA groups by country of birth of person/parents; code 90 = native Dutch partner / third generation.")
country_map("dem_eth", S02, "ETNGRP", ETH02); country_map("dem_eth", S03, "ETNGRP", ETH03)
V("dem_ethsex", "dem", "Ethnic group by sex (source combination)", "ETNGESL", "ETNGESL", universe=U_ALL, include=0,
  notes="Combination of dem_ethnic_group and dem_sex - source file only.")
V("dem_gen", "dem", "Migrant generation", "GENERAT", "GENERAT", "generation", universe=U_ALL,
  notes="SPVA 2002 / SPVN 2003 (ISEO definition): second generation includes those who arrived before age 6. LAS 2004/05, SIM 2006, SING 2009, SIM 2011 (SCP GENERAT): first generation = born abroad, second = born in the Netherlands, no age rule (SIM 2006 deposit: 3,199 = every migrant-group respondent born abroad, 1,018 = every one born in the Netherlands; LAS not checked separately). SIM 2015/2020: CBS definition from the sample frame.")
V("dem_brthcntry", "dem", "Country of birth", "GEBLAND", "GEBLAND", "country", universe=U_ALL,
  notes="Harmonized to Landentabel (Tabel 34) codes; survey lists only distinguish the target-group countries, NL and 'other'.")
country_map("dem_brthcntry", S02, "GEBLAND", BC02); country_map("dem_brthcntry", S03, "GEBLAND", BC03)
V("dem_brthcntry_src", "dem", "Provenance of dem_brthcntry: observed in the survey or inferred from origin group x generation", valueset="brthcntry_src", universe=U_ALL, derive="brthcntry_src",
  notes="1 = country of birth as collected (SPVA 2002, SPVN 2003 household roster); 2 = inferred under the CBS definition in the person samples (LAS 2004/05, SIM 2006, SING 2009, SIM 2011, SIM 2015, SIM 2020), whose public files contain no country of birth: first generation -> the country of the origin group (Chinese 6022, Caribbean 7011 aggregate), second generation and natives -> Netherlands; 'other'/unknown origin groups of the first generation are .d.")
V("dem_brthcntry_fa", "dem", "Country of birth of father", "GEBLPA", "GEBLPA", "country", universe=U_ALL)
country_map("dem_brthcntry_fa", S02, "GEBLPA", BC02); country_map("dem_brthcntry_fa", S03, "GEBLPA", BC03)
V("dem_brthcntry_ma", "dem", "Country of birth of mother", "GEBLMA", "GEBLMA", "country", universe=U_ALL)
country_map("dem_brthcntry_ma", S02, "GEBLMA", BC02); country_map("dem_brthcntry_ma", S03, "GEBLMA", BC03)
V("dem_mar", "dem", "Marital status", "BURGST", "BURGST", "marstat", universe=U_HEAD,
  notes="Code 5 (cohabiting, unmarried) only offered in SPVN 2003; in SPVA 2002 cohabitation is captured by dem_partner_status.")
V("dem_prtnr_st", "dem", "Partnership and co-residence status", "SAMPART", None, "partner_status", universe=U_HEAD02)
V("dem_prtnr_lat", "dem", "Has a partner living elsewhere (living-apart-together)", "LATPART", "SAMPARTA", "lat_partner", universe=U_HEAD,
  notes="SPVA 2002: asked only to persons not living alone without co-resident partner (n=757); singles not coded 0 - use dem_partner_status. SPVN 2003 includes 0 = single.")
V("dem_mar_yr", "dem", "Year of marriage (SPVN 2003: marriage or start of cohabitation)", "HUWJAAR", "HUWJAARA", type="year", universe=U_HEAD,
  notes="Concept differs slightly: SPVN 2003 also covers start of unmarried cohabitation.")
V("dem_mar_age", "dem", "Age at marriage", "LFTHUW", "LFTHUW", type="num", universe=U_HEAD)
V("dem_prtnr_age", "dem", "Age of partner", "LFTPART", "LFTPART", type="num", universe=U_HEAD)
V("dem_prtnr_brthcntry", "dem", "Country of birth of partner", "GEBLPART", "GEBLPART", "country", universe=U_HEAD)
country_map("dem_prtnr_brthcntry", S02, "GEBLPART", BC02); country_map("dem_prtnr_brthcntry", S03, "GEBLPART", BC03)
V("dem_prtnr_res", "dem", "Where the spouse lives", None, "WPPART", "partner_residence", universe=U_HEAD03)
V("dem_prtnr_reun", "dem", "Plans to bring spouse to the Netherlands", None, "KOMPART", "reunification_plan", universe=U_HEAD03)
V("dem_nchd", "dem", "Number of children", "AANTKIND", "AANTKIND", type="num", universe=U_HEAD)
V("dem_nchd_home", "dem", "Number of co-resident children", "INWKIND", "INWKIND", type="num", universe=U_HEAD)
V("dem_nchd_away", "dem", "Number of children living away from home", "NUITWKI", None, type="num", universe=U_HEAD02)
V("dem_chd_abroad", "dem", "Has children living outside the Netherlands", None, "KINDBL", "yesno", universe=U_HEAD03, yn12=True)
V("dem_chd_reun", "dem", "Plans to bring child(ren) to the Netherlands", None, "KOMKIND", "reunification_plan", universe=U_HEAD03)
V("dem_age_lefthome", "dem", "Age at leaving the parental home", "LFTVERLW", None, type="num", universe=U_HEAD02)

# ============================================================== hh_  (household scope: merged onto all members)
V("hh_eth", "hh", "Ethnic group of the household (head's group)", "ETNGROEP", "ETNGROEP", "ethgroup", scope="household", universe=U_ALL)
country_map("hh_eth", S02, "ETNGROEP", ETH02); country_map("hh_eth", S03, "ETNGROEP", ETH03)
V("hh_size", "hh", "Household size", "GEZOMV", "GEZOMV", type="num", scope="household", universe=U_ALL)
V("hh_comp", "hh", "Household composition", "GEZSAMST", "GEZSAMST", "hh_comp", scope="household", universe=U_ALL)
V("hh_noth", "hh", "Number of other (non-nuclear) persons in the household", "AANTAND", "AANTAND", type="num", scope="household", universe=U_ALL)
V("hh_inc", "hh", "Net household income per month (euro, nominal)", "GEZINK1", "GEZINK1", type="num", scope="household", universe=U_ALL,
  notes="Reported by head. Both surveys collected in euro.")
V("hh_inc_cat", "hh", "Net household income per month, classes", "GEZINK2", "GEZINK2", "income_cat9", scope="household", universe=U_ALL,
  notes="Classes have more cases than the exact amount (don't-know on amount still classified).")
V("hh_inc_15", "hh", "Net household income per month, constant 2015 euro (CPI-deflated)", type="num", scope="household", universe=U_ALL,
  derive="cpi2015:hh_inc", notes="hh_income_net x CPI(2015)/CPI(svy_year), CPI chained from CBS 70936ENG annual rates.")

# ============================================================== geo_
V("geo_mun_src", "geo", "Municipality of residence (survey code)", "GEMEENTE", "GEMEENTE", type="cat", universe=U_ALL, include=0,
  notes="Survey-internal codes differ between surveys; see geo_municipality_cbs.")
V("geo_mun_cbs", "geo", "Municipality of residence (CBS gemeentecode, 2006 list)", type="num", universe=U_ALL, derive="municipality",
  notes="Lookup crosswalks/municipalities.csv (survey code -> CBS code). Hoogezand-Sappemeer (0018) merged into Midden-Groningen in 2018.")
V("geo_mun_name", "geo", "Municipality of residence (name)", type="str", universe=U_ALL, derive="municipality_name")
V("geo_city4", "geo", "Four largest cities vs other survey municipalities", "GEMEENT1", "GEMEENT1", "city4", universe=U_ALL)
V("geo_pc4", "geo", "Postcode, 4-digit numeric part", "POSTCODE", None, type="num", universe=U_ALL + ", SPVA 2002 only")
V("geo_orig_settl", "geo", "Type of place of residence in origin country", None, "WPLVH", "origin_settlement", universe=U_HEAD03)

# ============================================================== mig_
V("mig_yr_arr", "mig", "Year of migration to the Netherlands", "MIGRJAAR", "MIGRJAAR", type="year", universe=U_ALL,
  notes="SPVN 2003: 0 = don't know -> .a (rule). SPVA 2002: 9999 = no information -> .d.")
V("mig_yr_arr_cat", "mig", "Year of migration, classes (source recode)", "MIGRJR1", "MIGRJR1", universe=U_ALL, include=0, notes="Pure recode of mig_year_arrival.")
V("mig_mo_arr", "mig", "Month of migration to the Netherlands", None, "MIGRMND", "month", universe=U_INT03)
V("mig_yr_dep", "mig", "Year of departure from origin country", None, "JRLVH", type="year", universe=U_INT03)
V("mig_mo_dep", "mig", "Month of departure from origin country", None, "MNDLVH", "month", universe=U_INT03)
V("mig_dur_nl", "mig", "Years of residence in the Netherlands (source computation)", "VERBLIJF", "VERBLIJF", type="num", universe=U_ALL,
  notes="ISEO computation; SPVA 2002 with one decimal, SPVN 2003 integer years.")
V("mig_dur_nl_cat", "mig", "Years of residence, classes (source recode)", "VERBL1", "VERBL1", universe=U_ALL, include=0, notes="Pure recode of mig_duration_nl.")
V("mig_age_arr", "mig", "Age at migration", "LFTMIGR", "LFTMIGR", type="num", universe=U_ALL)
V("mig_age_arr_cat", "mig", "Age at migration, classes (source recode)", "LFTMIGR1", "LFTMIGR1", universe=U_ALL, include=0, notes="Pure recode of mig_age_arrival.")
V("mig_reason", "mig", "Main reason for migration", "REDMIGR", "REDMIGR", "mig_reason", universe=U_INT,
  notes="Code 3 only in SPVA 2002; code 11 only in SPVN 2003.")
V("mig_reason_nl", "mig", "Reason for choosing the Netherlands", None, "REDNL", "reason_nl", universe=U_HEAD03)
V("mig_transit", "mig", "Stayed in other countries between departure and arrival in NL", None, "ANDLAND", "yesno", universe=U_HEAD03, yn12=True)
for i in range(1, 5):
    V(f"mig_tr_cntry{i}", "mig", f"Transit country {i} (Landentabel code)", None, f"ANDLAND{i}", "country", universe=U_HEAD03,
      notes="Source code list differs per transit position; each source label mapped to a Landentabel code by the crosswalk builder (NL2CODE); 'Onbekend' -> .d.")
    V(f"mig_tr_mo{i}", "mig", f"Months stayed in transit country {i}", None, f"MNDLAND{i}", type="num", universe=U_HEAD03)

# ============================================================== asy_  (asylum reception history, SPVN 2003)
for src, tgt, lab in [("ACOPV", "asy_rec_ac", "Stayed in application centre (AC)"), ("OCOPV", "asy_rec_oc", "Stayed in investigation and reception centre (OC)"),
                      ("AZCOPV", "asy_rec_azc", "Stayed in asylum seekers' centre (AZC) / additional reception (AVO)"),
                      ("COAOPV", "asy_rec_coa", "Stayed in COA or (ex-)ROA dwelling"), ("ZELFOPV", "asy_rec_self", "Self-arranged lodging (boarding house, room)"),
                      ("FAMVROPV", "asy_rec_fam", "Stayed with family or friends"), ("GEENOPV", "asy_rec_none", "None of the reception types")]:
    V(tgt, "asy", lab, None, src, "mentioned", universe=U_HEAD03)
for src, tgt, lab in [("MNDAC", "asy_mo_ac", "Months in AC"), ("MNDOC", "asy_mo_oc", "Months in OC"), ("MNDAZC", "asy_mo_azc", "Months in AZC/AVO"),
                      ("MNDCOA", "asy_mo_coa", "Months in COA/ROA dwelling"), ("MNDZELF", "asy_mo_self", "Months in self-arranged lodging"),
                      ("MNDFAMVR", "asy_mo_fam", "Months with family or friends")]:
    V(tgt, "asy", lab, None, src, type="num", universe=U_HEAD03)
for src, tgt, lab in [("WPAC", "asy_pl_ac", "Place of AC"), ("WPOC", "asy_pl_oc", "Place of OC"), ("WPAZC", "asy_pl_azc", "Place of AZC/AVO"),
                      ("WPCOA", "asy_pl_coa", "Place of COA/ROA dwelling"), ("WPZELF", "asy_pl_self", "Place of self-arranged lodging"),
                      ("WPFAMVR", "asy_pl_fam", "Place of stay with family or friends")]:
    V(tgt, "asy", lab + " (survey place code)", None, src, "src_" + src, type="cat", universe=U_HEAD03,
      notes="Codes are survey-internal; the place-name value labels are generated from the source file (value set src_" + src + ").")

# ============================================================== nat_
V("nat_cit", "nat", "Citizenship (harmonized)", "NATIONAL", "NATIONAL", "citizenship", universe=U_INT,
  notes="SPVA 2002: 1 origin nationality -> 3, 2 Dutch -> 1, 3 both -> 2, 4 other -> 4. SPVN 2003: 1 -> 1, 11-24 -> 2, 111-124 -> 3.")
M("nat_cit", S02, "NATIONAL", 1, 3); M("nat_cit", S02, "NATIONAL", 2, 1); M("nat_cit", S02, "NATIONAL", 3, 2); M("nat_cit", S02, "NATIONAL", 4, 4)
M("nat_cit", S03, "NATIONAL", 1, 1); M("nat_cit", S03, "NATIONAL", "11-24", 2); M("nat_cit", S03, "NATIONAL", "111-124", 3)
V("nat_cit_det", "nat", "Citizenship, detailed (SPVN 2003 coding)", None, "NATIONAL", "citizenship_det", universe=U_INT03)
V("nat_yr", "nat", "Year Dutch nationality obtained", None, "JRNLNAT", type="year", universe=U_INT03,
  notes="Source value 3 (n=120; month field also 3 in 117 cases) is a keying artefact and set to .d rather than imputed as 2003.")
M("nat_yr", S03, "JRNLNAT", 3, ".d", "invalid year (keying artefact)")
V("nat_mo", "nat", "Month Dutch nationality obtained", None, "MNDNLNAT", "month", universe=U_INT03)
V("nat_perm_cat", "nat", "Residence document (harmonized categories)", "VERGUN", "VERGUNA", "permit_cat", universe=U_INT,
  notes="SPVA 2002 asked to non-Dutch nationals only (n=951). Mapping: see value_map; W-document and VVTV grouped as conditional/temporary.")
for c, t in [(1, 1), (2, 2), (3, 3), (4, 3), (5, 4), (6, 6), (7, 7)]: M("nat_perm_cat", S02, "VERGUN", c, t)
for c, t in [(1, 1), (2, 2), (3, 1), (4, 3), (5, 5), (6, 4), (7, 4), (8, 1), (9, 1), (10, 2), (11, 2), (12, 5), (13, 4), (14, 7)]: M("nat_perm_cat", S03, "VERGUNA", c, t)
V("nat_perm_det", "nat", "Residence document, detailed (survey-specific codes)", "VERGUN", "VERGUNA", "permit_det", universe=U_INT)
for c in range(1, 8): M("nat_perm_det", S02, "VERGUN", c, 100 + c)
for c in range(1, 15): M("nat_perm_det", S03, "VERGUNA", c, 200 + c)
V("nat_perm_yr", "nat", "Year current residence document obtained", None, "JRDOC", type="year", universe=U_INT03,
  notes="Source value 3 (n=85; month field also 3 in 83 cases) is a keying artefact and set to .d rather than imputed as 2003.")
M("nat_perm_yr", S03, "JRDOC", 3, ".d", "invalid year (keying artefact)")
V("nat_perm_mo", "nat", "Month current residence document obtained", None, "MNDDOC", "month", universe=U_INT03)

# ============================================================== int_  (civic integration)
V("int_crs", "int", "Participated in civic integration course (inburgeringscursus)", "INBCURS", "INBCURS", "yesno", universe=U_INT, yn12=True,
  notes="SPVA 2002: asked to recent arrivals only (n=1,138).")
V("int_crs_dipl", "int", "Completed civic integration course with certificate", "DIPLINB", "DIPLINBA", "course_diploma", universe=U_INT,
  notes="SPVN 2003 adds 'still in progress'.")
M("int_crs_dipl", S02, "DIPLINB", 1, 1); M("int_crs_dipl", S02, "DIPLINB", 2, 0)
M("int_crs_dipl", S03, "DIPLINBA", 1, 1); M("int_crs_dipl", S03, "DIPLINBA", 2, 0); M("int_crs_dipl", S03, "DIPLINBA", 3, 2)
V("int_crs_sat", "int", "Satisfaction with civic integration course", None, "TEVRINB", "satisfied5", universe=U_INT03)
V("int_crs_best", "int", "Most satisfied with which part of the course", None, "ONDMETEV", "course_best", universe=U_HEAD03)
V("int_crs_worst", "int", "Least satisfied with which part of the course", None, "ONDMITEV", "course_worst", universe=U_HEAD03)
V("int_roc", "int", "Followed education at a regional training centre (ROC)", None, "ONDROC", "yesno", universe=U_HEAD03, yn12=True)
V("int_labchance", "int", "Course improved chances on the labour market (yes/no)", None, "KANSARM", "yesno", universe=U_HEAD03, yn12=True,
  notes="Source label 'Kansen op arbeidsmarkt' (yes/no); question wording to be verified in questionnaire.")
V("int_nlcrs", "int", "Followed a Dutch language course", None, "NLCURS", "yesno", universe=U_INT03, yn12=True)
V("int_nt2", "int", "Obtained NT2 (Dutch as second language) certificate", None, "NT2CERT", "yesno", universe=U_INT03, yn12=True)

# ============================================================== lang_
V("lang_nl_prtnr", "lang", "Speaks Dutch with partner", "TAALPART", "TAALPART", "freq3", universe=U_HEAD)
V("lang_nl_chd", "lang", "Speaks Dutch with children", "TAALKIND", "TAALKIND", "freq3", universe=U_HEAD)
V("lang_prob_spk", "lang", "Problems speaking Dutch in conversation", "TAALGESP", None, "freq3", universe=U_HEAD02)
V("lang_prob_read", "lang", "Problems reading Dutch (newspapers, letters)", "TAALKRAN", None, "freq3", universe=U_HEAD02)
V("lang_read", "lang", "Can read Dutch newspapers, letters, leaflets", None, "TAALKRAA", "reading4", universe=U_HEAD03,
  notes="Different scale from lang_problems_reading (SPVA 2002); kept separate.")
V("lang_other", "lang", "Other language used besides Dutch", "ETNTAAL", None, "other_language", universe=U_HEAD02)
V("lang_nl_rated", "lang", "Respondent's spoken Dutch as rated by interviewer", "TAALVAAR", "TAALVAAR", "good3", universe=U_HEAD)
V("lang_nl_rated_prtnr", "lang", "Partner's spoken Dutch as rated by interviewer", "TAALVP", "TAALVP", "good3", universe=U_HEAD)
V("lang_nl_rated_cmb", "lang", "Spoken Dutch rated by interviewer (head and partner combined)", None, "TAALVTOT", "good3", universe=U_INT03)

# ============================================================== edu_
V("edu_cntry", "edu", "Country where education was followed", "OPLBLNL", "OPLBLNL", "edu_cntry", universe=U_INT)
V("edu_abr", "edu", "Followed school education outside the Netherlands", None, "OPLBL", "yesno", universe=U_INT03, yn12=True)
V("edu_abr_yrs", "edu", "Years of education abroad", "ONDJRBL", "ONDJRBL", type="num", universe=U_INT)
V("edu_abr_dipl", "edu", "Obtained a diploma or certificate abroad", None, "DIPLBL", "yesno", universe=U_INT03, yn12=True)
V("edu_abr_hi_det", "edu", "Highest diploma obtained abroad, detailed (survey-specific levels)", "MAXDIPBL", "MAXDIPBA", "edu_abroad_det", universe=U_INT,
  notes="SPVA 2002 8 levels (0-7); SPVN 2003 5 levels, mapped 2->12, 3->13, 4->14.")
M("edu_abr_hi_det", S03, "MAXDIPBA", 2, 12); M("edu_abr_hi_det", S03, "MAXDIPBA", 3, 13); M("edu_abr_hi_det", S03, "MAXDIPBA", 4, 14)
V("edu_abr_hi_cat", "edu", "Highest diploma obtained abroad, 4 classes", "MAXDIPB1", "MAXDIPB1", "edu4", universe=U_INT)
V("edu_abr_fld", "edu", "Field of education abroad", None, "OPLRICBL", "field_det", universe=U_INT03)
for c in range(1, 11): M("edu_abr_fld", S03, "OPLRICBL", c, 10 + c)
V("edu_fdipl_eval", "edu", "Had foreign diploma evaluated in the Netherlands", None, "DIPLNLWA", "diploma_eval", universe=U_INT03)
M("edu_fdipl_eval", S03, "DIPLNLWA", 1, 1); M("edu_fdipl_eval", S03, "DIPLNLWA", 2, 0); M("edu_fdipl_eval", S03, "DIPLNLWA", 3, 2)
V("edu_fdipl_res", "edu", "Outcome of foreign diploma evaluation", None, "HOEWADIP", "diploma_eval_result", universe=U_INT03)
V("edu_enr", "edu", "Currently enrolled in education", "SCHOOLG", "SCHOOLG", "yesno", universe=U_INT, yn12=True)
V("edu_ft", "edu", "Enrolled in full-time day education", "VOLTOPL", "VOLTOPL", "yesno", universe=U_INT, yn12=True)
V("edu_cur_type", "edu", "Type of current education", "TYPEOPL", "TYPEOPL", "edu_type", universe=U_INT)
V("edu_part", "edu", "Full-time education participation (ISEO construct: full-time and main activity)", "ONDPART", "ONDPART", "participation", universe=U_INT)
V("edu_cur_lvl", "edu", "Level of current education", "HUIDOPL", "HUIDOPL", "edu_current", universe=U_INT, notes="Code 0 (bridge class) only in SPVA 2002.")
V("edu_cur_lvl_cat", "edu", "Level of current education, 4 classes", "HUIDOPL1", "HUIDOPL1", "edu4", universe=U_INT)
V("edu_cur_bridge", "edu", "Type of bridge class (brugklas)", "BRUGKLAS", None, "bridge_class", universe=U_INT02)
V("edu_cur_fld_cat", "edu", "Field of current education, 5 classes", "HUIDRICH", "HUIDRICA", "field_cat", universe=U_INT,
  notes="SPVN 2003 10 fields collapsed: general->1; economic/administrative/legal->2; technical/natural sciences->3; medical/paramedical and personal/social care->4; others->5.")
for c, t in [(1, 1), (2, 5), (3, 5), (4, 3), (5, 2), (6, 4), (7, 5), (8, 4), (9, 5), (10, 5)]: M("edu_cur_fld_cat", S03, "HUIDRICA", c, t)
V("edu_cur_fld_det", "edu", "Field of current education, detailed (survey-specific)", "HUIDRICH", "HUIDRICA", "field_det", universe=U_INT)
for c in range(1, 11): M("edu_cur_fld_det", S03, "HUIDRICA", c, 10 + c)
V("edu_cur_yr", "edu", "Year of study in current education", "HUIDLJR", "HUIDLJR", type="num", universe=U_INT)
V("edu_nl", "edu", "Followed education in the Netherlands", "OPLNL", "OPLNL", "yesno", universe=U_INT, yn12=True)
V("edu_nl_att_hi", "edu", "Highest education attended in the Netherlands", "MAXOPLNL", "MAXOPLNL", "edu_nl", universe=U_INT)
V("edu_nl_att_fld_cat", "edu", "Field of highest education attended in NL, 5 classes", "RICHTNL1", "RICHTN1A", "field_cat", universe=U_INT,
  notes="See edu_current_field_cat for the SPVN 2003 collapse.")
for c, t in [(1, 1), (2, 5), (3, 5), (4, 3), (5, 2), (6, 4), (7, 5), (8, 4), (9, 5), (10, 5)]: M("edu_nl_att_fld_cat", S03, "RICHTN1A", c, t)
V("edu_nl_att_fld_det", "edu", "Field of highest education attended in NL, detailed", "RICHTNL1", "RICHTN1A", "field_det", universe=U_INT)
for c in range(1, 11): M("edu_nl_att_fld_det", S03, "RICHTN1A", c, 10 + c)
V("edu_nl_att_dipl", "edu", "Diploma obtained for highest education attended in NL", "DIPLNL1", "DIPLNL1", "yesno", universe=U_INT, yn12=True)
V("edu_nl_dipl_enr", "edu", "Enrolled persons: has a Dutch diploma", None, "DIPLNL", "yesno", universe=U_INT03, yn12=True)
V("edu_nl_dipl_enr_lvl", "edu", "Enrolled persons: level of highest Dutch diploma", None, "OPLNL2", "edu7", universe=U_INT03)
V("edu_nl_dipl_fld_det", "edu", "Field of highest Dutch education with diploma, detailed", None, "RICHTN2A", "field_det", universe=U_INT03)
for c in range(1, 11): M("edu_nl_dipl_fld_det", S03, "RICHTN2A", c, 10 + c)
V("edu_nl_dipl_hi", "edu", "Highest diploma obtained in the Netherlands (not enrolled)", "MAXDIPNL", "MAXDIPNL", "edu_nl", universe=U_INT)
V("edu_nl_dipl_hi_cat", "edu", "Highest diploma obtained in NL, 4 classes (not enrolled)", "MAXDIPN1", "MAXDIPN1", "edu4", universe=U_INT)
V("edu_dipl_hi_det", "edu", "Highest diploma obtained (NL or abroad), 8 levels; persons not in full-time education", "MAXDIP", None, "edu8", universe=U_INT02,
  notes="SPVN 2003 only released the 5-class version (edu_highest_diploma_cat5).")
V("edu_dipl_hi_cat5", "edu", "Highest diploma obtained (NL or abroad), 5 classes incl. none; persons not in full-time education", "MAXDIP", "MAXDIPA", "edu5", universe=U_INT,
  notes="SPVA 2002 collapsed from 8 levels: 0->0, 1->1, 2-3->2, 4-5->3, 6-7->4.")
for c, t in [(0, 0), (1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (7, 4)]: M("edu_dipl_hi_cat5", S02, "MAXDIP", c, t)
V("edu_dipl_hi_cat", "edu", "Highest diploma obtained (NL or abroad), 4 classes; persons not in full-time education", "MAXDIP1", "MAXDIP1", "edu4", universe=U_INT)
V("edu_dipl_all_det", "edu", "Highest diploma obtained so far (incl. enrolled), 8 levels", "MAXDSCH", None, "edu8", universe=U_INT02)
V("edu_dipl_all_cat5", "edu", "Highest diploma obtained so far (incl. enrolled), 5 classes incl. none", "MAXDSCH", "MAXDSCHA", "edu5", universe=U_INT,
  notes="SPVA 2002 collapsed as edu_highest_diploma_cat5.")
for c, t in [(0, 0), (1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (7, 4)]: M("edu_dipl_all_cat5", S02, "MAXDSCH", c, t)
V("edu_dipl_all_cat", "edu", "Highest diploma obtained so far (incl. enrolled), 4 classes", "MAXDSCH1", "MAXDSCH1", "edu4", universe=U_INT)
V("edu_fld_cat", "edu", "Field of highest diploma, 5 classes", "MAXRICH", "MAXRICHA", "field_cat", universe=U_INT)
for c, t in [(1, 1), (2, 5), (3, 5), (4, 3), (5, 2), (6, 4), (7, 5), (8, 4), (9, 5), (10, 5)]: M("edu_fld_cat", S03, "MAXRICHA", c, t)
V("edu_fld_det", "edu", "Field of highest diploma, detailed", "MAXRICH", "MAXRICHA", "field_det", universe=U_INT)
for c in range(1, 11): M("edu_fld_det", S03, "MAXRICHA", c, 10 + c)
V("edu_dropout", "edu", "Dropout from Dutch secondary education", "DROPOUT", "DROPOUT", "dropout", universe=U_INT)
V("edu_fa_det", "edu", "Highest diploma of father, detailed (survey-specific levels)", "MAXDIPPA", "MAXDIPAA", "edu_parent_det", universe=U_INT,
  notes="SPVA 2002 8 levels; SPVN 2003 5 levels mapped 2->12, 3->13, 4->14.")
for c, t in [(2, 12), (3, 13), (4, 14)]: M("edu_fa_det", S03, "MAXDIPAA", c, t)
V("edu_fa_cat", "edu", "Highest diploma of father, 4 classes", "MAXDIPP1", "MAXDIPP1", "edu4", universe=U_INT)
V("edu_ma_det", "edu", "Highest diploma of mother, detailed (survey-specific levels)", "MAXDIPMA", "MAXDIMAA", "edu_parent_det", universe=U_INT)
for c, t in [(2, 12), (3, 13), (4, 14)]: M("edu_ma_det", S03, "MAXDIMAA", c, t)
V("edu_ma_cat", "edu", "Highest diploma of mother, 4 classes", "MAXDIPM1", "MAXDIPM1", "edu4", universe=U_INT)

# ============================================================== lab_
V("lab_rel", "lab", "Relation to the labour market (ISEO 8-category construct)", "BERBEV", "BERBEV", "lab_rel", universe=U_INT)
V("lab_lf", "lab", "In the labour force (CCS-91 definition)", "BB", "BB", "in_lf", universe=U_INT)
V("lab_regunemp", "lab", "Registered unemployed (CCS-91)", "GWL", "GWL", "reg_unemp", universe=U_INT)
V("lab_notwork", "lab", "Not working (labour force)", "NWP", "NWP", "not_working", universe=U_INT)
V("lab_emp", "lab", "Currently has paid work", "NUWERK", "NUWERK", "yesno", universe=U_INT, yn12=True)
V("lab_act", "lab", "Main daily activity", "HFDACT", "HFDACT", "main_activity", universe=U_INT, notes="Code 7 only in SPVN 2003.")
V("lab_frst_yr", "lab", "Year of first job in the Netherlands", "JRWERKNL", "JRWERKNL", type="year", universe=U_INT)
V("lab_frst_occ", "lab", "First occupation in NL (SBC-92, 5 digits)", "BEROEP1", "BEROEP1", type="num", universe=U_INT,
  notes="CBS Standaard Beroepenclassificatie 1992; ISCO-08 mapping planned via External/Occupational codes.")
V("lab_frst_lvl", "lab", "Skill level of first occupation in NL", "FUNCNIV1", "FUNCNIV1", "skill_level", universe=U_INT)
V("lab_frst_ind", "lab", "Industry of first job in NL (SBI-93, 2 digits)", "BEDRIJF1", "BEDRIJF1", type="num", universe=U_INT)
V("lab_frst_ind_cat", "lab", "Industry of first job in NL, 9 sectors", "BEDRTAK1", "BEDRTAK1", "industry9", universe=U_INT)
V("lab_exp", "lab", "Years of work experience in the Netherlands", "ARBERV", "ARBERV", type="num", universe=U_INT)
V("lab_exp_cat", "lab", "Work experience in NL, classes (source recode)", "ARBERV1", "ARBERV1", universe=U_INT, include=0, notes="Pure recode of lab_experience_nl.")
V("lab_nunemp", "lab", "Number of times unemployed in the Netherlands", "NWERKL", "NWERKL", type="num", universe=U_INT)
V("lab_emptype", "lab", "Employee, self-employed or freelance", "ZELFST", "ZELFST", "employment_type", universe=U_INT)
V("lab_occ", "lab", "Current occupation (SBC-92, 5 digits)", "BEROEP", "BEROEP", type="num", universe=U_INT)
V("lab_occ_lvl", "lab", "Skill level of current occupation", "FUNCNIV", "FUNCNIV", "skill_level", universe=U_INT)
V("lab_ind", "lab", "Industry of current job (SBI-93, 2 digits)", "BEDRIJF", "BEDRIJF", type="num", universe=U_INT)
V("lab_ind_cat", "lab", "Industry of current job, 9 sectors", "BEDRTAK", "BEDRTAK", "industry9", universe=U_INT)
V("lab_match", "lab", "Job matches level of education", None, "WENIVOPL", "job_match", universe=U_INT03)
V("lab_tenure", "lab", "Years with current employer", "ERVBEDR", "ERVBEDR", type="num", universe=U_INT)
V("lab_prev_st", "lab", "Situation before current job", "WERKV", None, "prev_status", universe=U_HEAD02)
V("lab_lvl_vs_prev", "lab", "Level of current job compared with previous job", "BAANNIV", None, "job_level_vs_prev", universe=U_HEAD02)
V("lab_chg_reason", "lab", "Reason for changing jobs", "REDRUIL", None, "reason_job_change", universe=U_HEAD02)
V("lab_nsup", "lab", "Number of persons supervised", "NLEIDING", "NLEIDING", type="num", universe=U_INT)
V("lab_sector", "lab", "Employer sector: government, non-profit, private", "OVERHEID", None, "sector", universe=U_HEAD02)
V("lab_found", "lab", "How current job was found", "HOEBAAN", "HOEBAAN", "job_found", universe=U_INT)
V("lab_train", "lab", "Followed training with current employer", "CURSUSBD", None, "yesno", universe=U_INT02, yn12=True)
V("lab_prom_want", "lab", "Would like to be promoted", "PROMOTIE", None, "yesno", universe=U_INT02, yn12=True)
V("lab_prom_chance", "lab", "Thinks he/she has a chance of promotion", "KANSPROM", None, "yesno", universe=U_INT02, yn12=True)
V("lab_prom_bar", "lab", "Main barrier to promotion", "BELPROM", None, "promotion_barrier", universe=U_INT02)
V("lab_oth_consider", "lab", "Considering working elsewhere", "ANDWERK", None, "yesno", universe=U_INT02, yn12=True)
V("lab_oth_reason", "lab", "Reason for wanting to work elsewhere", "REDANDW", None, "reason_other_job", universe=U_INT02)
V("lab_oth_applied", "lab", "Has applied for jobs elsewhere", "GESOLL", None, "yesno", universe=U_INT02, yn12=True)
V("lab_perm", "lab", "Permanent or temporary employment", "VASTWERK", "VASTWERK", "contract_perm", universe=U_INT)
V("lab_contr", "lab", "Type of employment contract", "ARBOVK", "ARBOVK", "contract_type", universe=U_INT)
V("lab_hrs", "lab", "Contractual working hours per week", "URENWERK", "URENWERK", type="num", universe=U_INT)
V("lab_hrs_cat", "lab", "Contractual hours, classes (source recode)", "URENWRK1", "URENWRK1", universe=U_INT, include=0, notes="Pure recode of lab_hours_contract.")
V("lab_hrs_act", "lab", "Actual working hours per week (persons working 12+ hours)", "FEITUREN", "FEITUREN", type="num", universe=U_INT)
V("lab_12h", "lab", "Works 12 hours or more per week (mini questionnaire)", None, "W12UPW", "hours12", universe=U_INT03)
V("lab_se_ind", "lab", "Type of own business (SBI-93, 5 digits)", "BEDRIJFZ", None, type="num", universe=U_INT02)
V("lab_se_yr", "lab", "Year own business started", "STARTJR", None, type="year", universe=U_INT02)
V("lab_se_nemp", "lab", "Number of employees in own business", "NWERKN", None, type="num", universe=U_INT02)
V("lab_se_ethn", "lab", "Ethnicity of employees in own business", "ETNWERKN", None, "employee_ethnicity", universe=U_INT02)
V("lab_se_prior", "lab", "Situation before starting own business", "HFDACTVR", None, "prior_status_selfemp", universe=U_HEAD02)
V("lab_everwork", "lab", "Not working: ever had paid work in the Netherlands", "WERKNL", "WERKNL", "yesno", universe=U_INT, yn12=True)
V("lab_nowork_yrs", "lab", "Years without work (not working persons)", "NWRKDUUR", "NWRKDUUR", type="num", universe=U_INT)
V("lab_prev_occ", "lab", "Occupation of previous/last job (SBC-92)", "BEROEPV", "BEROEPVA", type="num", universe=U_INT,
  notes="SPVA 2002: previous job of all; SPVN 2003: last job of persons not working.")
V("lab_prev_lvl", "lab", "Skill level of previous/last job", "FUNCNIVV", "FUNCNVVA", "skill_level", universe=U_INT)
V("lab_prev_ind", "lab", "Industry of previous/last job (SBI-93, 2 digits)", "BEDRIJFV", "BEDRFVA", type="num", universe=U_INT)
V("lab_prev_ind_cat", "lab", "Industry of previous/last job, 9 sectors", "BEDRTAKV", "BEDRTAVA", "industry9", universe=U_INT)
V("lab_left_how", "lab", "How the last job ended", "ONTSLAG", "ONTSLAG", "how_left", universe=U_INT)
V("lab_dism_reason", "lab", "Reason for dismissal", "REDONTSL", "REDONTSL", "reason_dismissal", universe=U_INT)
V("lab_reg", "lab", "Registered at the employment office", "INGGAB", "INGGAB", "yesno", universe=U_INT, yn12=True)
V("lab_reg_yrs", "lab", "Years registered at the employment office", "GABDUUR", "GABDUUR", type="num", universe=U_INT)
V("lab_reg_visit", "lab", "Last visit to the employment office", "LAATGAB", None, "last_visit", universe=U_INT02)
V("lab_want", "lab", "Wants paid work", "WILWERK", "WILWERK", "wants_work", universe=U_INT)
V("lab_seek", "lab", "Wants work (12+ hours) and is actively searching", "ZOEKWERK", "ZOEKWERK", "yesno", universe=U_INT, yn12=True)
V("lab_seek_yrs", "lab", "Years searching for work", "ZOEKDUUR", "ZOEKDUUR", type="num", universe=U_INT)
V("lab_unemp_yrs", "lab", "Years of registered unemployment", "GWLDUUR", "GWLDUUR", type="num", universe=U_INT)
V("lab_unemp_yrs_cat", "lab", "Registered unemployment duration, classes (source recode)", "GWLDUUR1", "GWLDUUR1", universe=U_INT, include=0, notes="Pure recode of lab_unemp_years.")
for s, t, lab in [("ZKARBBUR", "lab_srch01", "Searches via employment office"), ("ZKUITZ", "lab_srch02", "Searches via temp agencies"),
                  ("ZKFAMVR", "lab_srch03", "Searches via family and friends"), ("ZKADVERT", "lab_srch04", "Searches via advertisements"),
                  ("ZKZELF", "lab_srch05", "Searches by approaching employers directly"), ("ZKSCHOOL", "lab_srch06", "Searches via school"),
                  ("ZKANDERS", "lab_srch08", "Searches in another way")]:
    V(t, "lab", lab, s, s, "mentioned", universe=U_INT)
V("lab_srch07", "lab", "Searches via refugee organisations (VluchtelingenWerk, Emplooi, UAF)", None, "ZKVLUCHT", "mentioned", universe=U_INT03)
V("lab_avail2w", "lab", "Can start work within two weeks", "BESCH2W", "BESCH2W", "yesno", universe=U_INT, yn12=True)
V("lab_navail_reason", "lab", "Reason not available within two weeks", "NIETBES", "NIETBES", "not_available_reason", universe=U_INT)
V("lab_avail3m", "lab", "Can start work within three months", "BESCH3M", "BESCH3M", "yesno", universe=U_INT, yn12=True)
V("lab_noseek_reason", "lab", "Reason for not wanting or seeking work", "NIETZOEK", "NIETZOEK", "reason_not_seeking", universe=U_INT,
  notes="Codes 11-14 only in SPVN 2003.")
V("lab_cmb_study", "lab", "Combines job with education of 10+ hours", "COMBOPL", None, "yesno", universe=U_INT02, yn12=True)
V("lab_cmb_care", "lab", "Combines job with care tasks", "COMBZORG", None, "yesno", universe=U_INT02, yn12=True)
V("lab_red_chd", "lab", "Would work less or stop to care for children", "STOPKIND", None, "yesno", universe=U_INT02, yn12=True,
  notes="Source code 7 'weet niet' -> .a (rule).")
V("lab_red_sick", "lab", "Would work less or stop to care for a sick relative", "STOPZIEK", None, "yesno", universe=U_INT02, yn12=True)
V("lab_red_edu", "lab", "Would work less or stop for education", "STOPOND", None, "yesno", universe=U_INT02, yn12=True)
V("lab_plan_edu", "lab", "Plans to combine job with education", "PLANOPL", None, "yesno", universe=U_INT02, yn12=True)
V("lab_plan_care", "lab", "Plans to combine job with care tasks", "PLANZORG", None, "yesno", universe=U_INT02, yn12=True)
V("lab_fut5y", "lab", "Expected situation in five years", None, "TOEK5JR", "future5", universe=U_HEAD03)
V("lab_fut5y_txt", "lab", "Expected job in five years (open text)", None, "FUNC5JR", type="str", universe=U_HEAD03)
V("lab_orig_work", "lab", "Had paid work in the country of origin", None, "WERKBL", "yesno", universe=U_INT03, yn12=True)
V("lab_orig_occ", "lab", "Occupation in country of origin (SBC-92)", None, "BEROEPBL", type="num", universe=U_INT03)
V("lab_orig_lvl", "lab", "Skill level of occupation in country of origin", None, "FUNCNIVB", "skill_level", universe=U_INT03)

# ============================================================== inc_
V("inc_lab", "inc", "Net monthly labour income (euro, nominal)", "ARBINK1", "ARBINK1", type="num", universe=U_INT)
V("inc_lab_cat", "inc", "Net monthly labour income, classes", "ARBINK2", "ARBINK2", "income_cat10", universe=U_INT)
V("inc_lab_15", "inc", "Net monthly labour income, constant 2015 euro", type="num", universe=U_INT, derive="cpi2015:inc_lab")
V("inc_hrwage", "inc", "Net hourly wage (employed labour force, euro nominal)", "UURLOON", "UURLOON", type="num", universe=U_INT)
V("inc_hrwage_15", "inc", "Net hourly wage, constant 2015 euro", type="num", universe=U_INT, derive="cpi2015:inc_hrwage")
V("inc_ben", "inc", "Receives any social benefit", "UITKERIN", "UITKERIN", "yesno", universe=U_INT, yn12=True)
for s02, code03, t, lab in [("BIJSTAND", 1, "inc_ben01", "Receives social assistance (bijstand)"),
                            ("WWUITK", 2, "inc_ben02", "Receives unemployment benefit (WW)"),
                            ("WAOUITK", 3, "inc_ben03", "Receives disability benefit (WAO)"),
                            ("AOWUITK", 4, "inc_ben04", "Receives old-age pension / AOW / early retirement"),
                            ("STUDIEF", 5, "inc_ben05", "Receives student grant"),
                            ("UITKAND", 6, "inc_ben06", "Receives other benefit")]:
    V(t, "inc", lab, s02, "SRTUITK", "mentioned", universe=U_INT,
      notes="SPVA 2002: multiple-response item; SPVN 2003 derived from single-response benefit type (SRTUITK).")
    M(t, S03, "SRTUITK", code03, 1); M(t, S03, "SRTUITK", "*", 0)
V("inc_ben_type", "inc", "Type of (main) benefit", None, "SRTUITK", "benefit_type", universe=U_INT03)
V("inc_ben_amt", "inc", "Net monthly benefit amount (euro, nominal)", "UITKINK1", "UITKINK1", type="num", universe=U_INT)
V("inc_ben_amt_cat", "inc", "Net monthly benefit amount, classes", "UITKINK2", "UITKINK2", "income_cat10", universe=U_INT)
V("inc_ben_amt_15", "inc", "Net monthly benefit amount, constant 2015 euro", type="num", universe=U_INT, derive="cpi2015:inc_ben_amt")
V("inc_ben_yrs", "inc", "Years receiving the benefit", "UITKDUUR", "UITKDUUR", type="num", universe=U_INT)
V("inc_tot", "inc", "Total net personal income per month (euro, nominal)", "INKOMEN1", "INKOMEN1", type="num", universe=U_INT)
V("inc_tot_cat", "inc", "Total net personal income per month, classes", "INKOMEN2", "INKOMEN2", "income_cat8", universe=U_INT)
V("inc_tot_15", "inc", "Total net personal income per month, constant 2015 euro", type="num", universe=U_INT, derive="cpi2015:inc_tot")
V("inc_worry", "inc", "Money worries in the past three months", "GELDZORG", "GELDZORG", "money_worries", universe=U_HEAD)

# ============================================================== trn_  (transnational support to persons in origin country)
V("trn_sup_prtnr", "trn", "Financially supports partner in country of origin", "VERZPART", "VERZPARA", "yesno", universe=U_HEAD,
  notes="SPVA 2002 source is a count (0/1); SPVN 2003 mentioned/not mentioned.")
M("trn_sup_prtnr", S02, "VERZPART", "1-9", 1); M("trn_sup_prtnr", S02, "VERZPART", 99, ".d", "unlabelled 99 (n=48) = no information")
V("trn_sup_chd", "trn", "Financially supports children in country of origin", "VERZKIND", "VERZKINA", "yesno", universe=U_HEAD,
  notes="SPVA 2002: count recoded to 1 if >=1; count kept in trn_n_children_supported.")
M("trn_sup_chd", S02, "VERZKIND", "1-99", 1)
V("trn_n_chd", "trn", "Number of children in origin country supported", "VERZKIND", None, type="num", universe=U_HEAD02)
V("trn_sup_par", "trn", "Financially supports parents in country of origin", "VERZOUD", "VERZOUDA", "yesno", universe=U_HEAD)
M("trn_sup_par", S02, "VERZOUD", "1-9", 1)
V("trn_n_par", "trn", "Number of parents in origin country supported", "VERZOUD", None, type="num", universe=U_HEAD02)
V("trn_sup_fam", "trn", "Financially supports other family in country of origin", "VERZFAM", "VERZFAMA", "yesno", universe=U_HEAD)
M("trn_sup_fam", S02, "VERZFAM", "1-99", 1)
V("trn_n_fam", "trn", "Number of other family members in origin country supported", "VERZFAM", None, type="num", universe=U_HEAD02)
V("trn_sup_oth", "trn", "Financially supports other persons in country of origin", "VERZAND", "VERZANDA", "yesno", universe=U_HEAD)
M("trn_sup_oth", S02, "VERZAND", "1-99", 1)
V("trn_n_oth", "trn", "Number of other persons in origin country supported", "VERZAND", None, type="num", universe=U_HEAD02)
V("trn_n_tot", "trn", "Total number of persons in origin country supported", "VERZTOT", "VERZTOT", type="num", universe=U_HEAD)
V("trn_sup_who", "trn", "Whom the respondent supports in the country of origin", "VERZORG", "VERZORG", "support_who", universe=U_HEAD)

# ============================================================== hous_  (SPVN 2003 housing block; SPVA 2002 neighbourhood items)
V("hous_indep_yr", "hous", "Year first moved into independent housing", None, "JRZELFST", type="year", universe=U_HEAD03,
  notes="Source label 9996 = 'no independent dwelling yet' -> .c, but the code does not occur in the data (118 cases are -7 sysmis).")
M("hous_indep_yr", S03, "JRZELFST", 9996, ".c")
V("hous_indep_mun", "hous", "Municipality of first independent dwelling (open text)", None, "WPZELFST", type="str", universe=U_HEAD03)
V("hous_same_addr", "hous", "Still at the address of first independent dwelling", None, "ZELFDADR", "yesno", universe=U_HEAD03, yn12=True)
V("hous_mv_reason", "hous", "Main reason for (last) move", None, "VERHRED", "move_reason", universe=U_HEAD03)
V("hous_nbhd_pleas4", "hous", "Pleasant to live in this neighbourhood (SPVA 2002, 4-point)", "FIJNBRT", None, "nbhd_pleasant4", universe=U_HEAD02)
V("hous_nbhd_pleas5", "hous", "Pleasant to live in this neighbourhood (SPVN 2003, 5-point)", None, "FIJNBRTA", "nbhd_pleasant5", universe=U_HEAD03,
  notes="Scales differ (4 vs 5 points, different wording); kept as separate variables.")
V("hous_nbhd_forgn", "hous", "Opinion on number of foreigners in the neighbourhood", "AANTBL", None, "nbhd_foreigners", universe=U_HEAD02)
V("hous_nbhd_dutch", "hous", "Opinion on number of native Dutch in the neighbourhood", None, "NLBRT", "nbhd_dutch", universe=U_HEAD03)
V("hous_seek", "hous", "Currently looking for another dwelling", None, "ZOEKAWON", "yesno", universe=U_HEAD03, yn12=True)
for s, t, lab in [("VERHEIWO", "hous_mv01", "Wants a dwelling of one's own"), ("VERHGRWO", "hous_mv02", "Wants a larger or better dwelling"),
                  ("VERHHKOP", "hous_mv03", "Wants to buy a house"), ("VERHGKWO", "hous_mv04", "Wants a cheaper dwelling"),
                  ("VERHBUUR", "hous_mv05", "Dislikes current neighbourhood"), ("VERHWERK", "hous_mv06", "Move for (better chances of) work"),
                  ("VERHOND", "hous_mv07", "Move for education"), ("VERHCOFV", "hous_mv08", "Move for contacts with compatriots/family"),
                  ("VERHMED", "hous_mv09", "Move for medical reasons"), ("VERHAND", "hous_mv10", "Move for other reasons")]:
    V(t, "hous", "Reason for seeking another dwelling: " + lab, None, s, "mentioned", universe=U_HEAD03)
V("hous_mv_dest", "hous", "Preferred destination if moving", None, "VERHWP", "move_destination", universe=U_HEAD03)

# ============================================================== hlth_
V("hlth_self", "hlth", "Self-rated health", "GEZONDH", "GEZONDH", "health5", universe="Heads of household; SPVN 2003 also the partner (separate health block)")
V("hlth_gp2m", "hlth", "Number of GP visits in the past two months", "HUISARTS", "HUISARTS", type="num", universe=U_INT,
  notes="SPVA 2002: 99 = no information -> .d.")
V("hlth_spec", "hlth", "Contact with medical specialist", "MEDSPEC", "MEDSPEC", "yesno", universe=U_HEAD, yn12=True)
V("hlth_hosp", "hlth", "Admitted to hospital", "OPNZIEKH", "OPNZIEKH", "yesno", universe=U_HEAD, yn12=True)
V("hlth_4w01", "hlth", "Felt calm and peaceful in the past four weeks", None, "G4KALM", "yes_no_sometimes", universe=U_HEAD03)
V("hlth_4w02", "hlth", "Felt very energetic in the past four weeks", None, "G4ENERG", "yes_no_sometimes", universe=U_HEAD03)
V("hlth_4w03", "hlth", "Felt downhearted and gloomy in the past four weeks", None, "G4NEERS", "yes_no_sometimes", universe=U_HEAD03)
V("hlth_4w04", "hlth", "Felt nervous in the past four weeks", None, "G4ZENUW", "yes_no_sometimes", universe=U_HEAD03)

# ============================================================== soc_
V("soc_mem", "soc", "Member of an association or club", "LIDVER", "LIDVER", "yesno", universe=U_INT, yn12=True)
V("soc_mem_type", "soc", "Type of association (single response)", None, "WELKVER", "member_type", universe=U_HEAD03)
for s02, code03, t, lab in [("SPORTVER", 1, "soc_mem01", "Member of a sports club"), ("GEZVER", 7, "soc_mem02", "Member of a social club"),
                            ("HOBBYVER", 4, "soc_mem04", "Member of a hobby club"), ("ONDVER", 5, "soc_mem06", "Member of an education/school association"),
                            ("MAATSCH", 3, "soc_mem08", "Member of an organisation with a social goal"),
                            ("VAKBOND", 2, "soc_mem09", "Member of a trade union"), ("POLPART", 6, "soc_mem10", "Member of a political party")]:
    V(t, "soc", lab, s02, "WELKVER", "mentioned", universe=U_INT,
      notes="SPVA 2002: multiple-response item (members only); SPVN 2003 derived from single-response type of association (heads only).")
    M(t, S03, "WELKVER", code03, 1); M(t, S03, "WELKVER", "*", 0)
for s, t, lab in [("ZANGVER", "soc_mem03", "Member of a choir / singing society"), ("JEUGDVER", "soc_mem05", "Member of a youth association"),
                  ("NATUURV", "soc_mem07", "Member of a nature association"), ("GODORG", "soc_mem11", "Member of a religious organisation")]:
    V(t, "soc", lab, s, None, "mentioned", universe=U_INT02)
V("soc_mem_ethsh", "soc", "Share of own ethnic group among association members", "ETNLID", None, "ethnic_share", universe=U_INT02)
V("soc_assoc_eth", "soc", "Association is for a specific ethnic group", "ETNVER", None, "yesno", universe=U_INT02, yn12=True)
V("soc_assoc_focus", "soc", "Activities of the association focus on", "ACTVER", None, "assoc_focus", universe=U_INT02)
V("soc_frnd_nl", "soc", "Has native Dutch friends or acquaintances", "NEDVR", "NEDVR", "yesno", universe=U_INT, yn12=True)
V("soc_frnd_nl_want", "soc", "Would like to have native Dutch friends", "WILNEDVR", "WILNEDVR", "wants_friends4", universe=U_INT)
V("soc_visit_nl", "soc", "Receives visits from native Dutch friends or neighbours", "BEZOEK", None, "freq3", universe=U_INT02)
V("soc_leis_nl", "soc", "Spends leisure time with native Dutch", "VRTIJDNL", "VRTIJDNL", "freq3", universe=U_INT,
  notes="SPVN 2003: asked in the mini questionnaire only.")
V("soc_cont_bal", "soc", "More contact with native Dutch or with own group", "CONTACTV", "CONTACTV", "contact_balance", universe=U_INT)

# ============================================================== fam_  (SPVA 2002 family-relations module, NKPS component)
V("fam_chd_sex", "fam", "Sex of (selected) child living away from home", "GSLUITWK", None, "sex", universe=U_HEAD02)
V("fam_chd_byr", "fam", "Birth year of child living away from home", "JRUITWK", None, type="year", universe=U_HEAD02)
V("fam_chd_res", "fam", "Where the child living away lives", "WPKIND", None, "residence4", universe=U_HEAD02)
V("fam_chd_seen", "fam", "Frequency of seeing child in past 12 months", "ZIENKIND", None, "freq7_contact", universe=U_HEAD02)
V("fam_chd_cont", "fam", "Frequency of other contact with child in past 12 months", "TELEKIND", None, "freq7_contact", universe=U_HEAD02)
V("fam_chd_help_fr", "fam", "Received help from child", "HULPVKI", None, "freq3_help", universe=U_HEAD02)
V("fam_chd_adv_fr", "fam", "Received advice from child", "ADVVKI", None, "freq3_help", universe=U_HEAD02)
V("fam_chd_help_to", "fam", "Gave help to child", "HULPAKI", None, "freq3_help", universe=U_HEAD02)
V("fam_chd_adv_to", "fam", "Gave advice to child", "ADVAKI", None, "freq3_help", universe=U_HEAD02)
V("fam_par_alive", "fam", "Parents still alive", "LEEFOUD", None, "parents_alive", universe=U_HEAD02)
V("fam_par_which", "fam", "Parent the following questions refer to", "OUDGESP", None, "parent_asked", universe=U_HEAD02)
V("fam_par_byr", "fam", "Birth year of parent", "JROUD", None, type="year", universe=U_HEAD02)
V("fam_par_res", "fam", "Where the parent lives", "WPOUD", None, "residence4", universe=U_HEAD02)
V("fam_par_seen", "fam", "Frequency of seeing parent in past 12 months", "ZIENOUD", None, "freq7_contact", universe=U_HEAD02)
V("fam_par_cont", "fam", "Frequency of other contact with parent in past 12 months", "TELEOUD", None, "freq7_contact", universe=U_HEAD02)
V("fam_par_help_fr", "fam", "Received help from parent", "HULPVOUD", None, "freq3_help", universe=U_HEAD02)
V("fam_par_adv_fr", "fam", "Received advice from parent", "ADVVOUD", None, "freq3_help", universe=U_HEAD02)
V("fam_par_help_to", "fam", "Gave help to parent", "HULPAOUD", None, "freq3_help", universe=U_HEAD02)
V("fam_par_adv_to", "fam", "Gave advice to parent", "ADVAOUD", None, "freq3_help", universe=U_HEAD02)
V("fam_oblig", "fam", "Feels obliged to do things for family", "VERPLFAM", None, "freq3_nso", universe=U_HEAD02)
V("fam_affect", "fam", "Does things for family out of affection", "GEEFFAM", None, "freq3_nso", universe=U_HEAD02)

# ============================================================== att_  (attitudes and values)
V("att_ideal01", "att", "Ideal age for a woman to leave the parental home", "IDLFTUIT", None, type="num", universe=U_INT02, notes="99 = no information -> .d.")
V("att_ideal02", "att", "Ideal age for a woman to marry", "IDLFTHUW", None, type="num", universe=U_INT02)
V("att_ideal03", "att", "Ideal age to have a first child", "IDLFTMOE", None, type="num", universe=U_INT02)
V("att_ideal04", "att", "Ideal number of children for a family", "IDNKIND", None, "ideal_children", universe=U_INT02)
V("att_task01", "att", "Who should stay home when a child is ill", "WIETHUIS", None, "stay_home6", universe=U_INT02)
V("att_task02", "att", "Who should care for the children", "WIEKIND", "WIEKIND", "who3", universe=U_INT)
V("att_task03", "att", "Who should do the shopping", "WIEBOODS", None, "who3", universe=U_INT02)
V("att_task04", "att", "Who should cook", "WIEKOKEN", "WIEKOKEN", "who3", universe=U_INT)
V("att_task05", "att", "Who should earn the money", "WIEGELDV", "WIEGELDV", "who3", universe=U_INT)
V("att_task06", "att", "Who should manage the finances", "WIEADMIN", None, "who3", universe=U_INT02)
AGREE = [
    ("att_gr01", "MANAANK", None, "Man best decides on large purchases"),
    ("att_gr02", "VRWHUISH", "VRWHUISH", "Woman is best responsible for the household"),
    ("att_gr03", "MANGELD", "MANGELD", "Man is best responsible for money"),
    ("att_gr04", "OPLJONGS", "OPLJONGS", "Education is more important for boys"),
    ("att_gr05", "VRWZKIND", None, "A woman can be happy without children"),
    ("att_gr06", "INKJONGS", None, "Own income is more important for boys"),
    ("att_gr07", "VRWSTOPW", "VRWSTOPW", "A woman should stop working when she has a child"),
    ("att_fam01", "MVSAMENW", None, "A man and a woman may live together unmarried"),
    ("att_fam02", "SCHJKIND", None, "Divorce is not acceptable with young children"),
    ("att_fam03", "STDGEZIN", "STDGEZIN", "The best family form is married with children"),
    ("att_fam04", "THUISHUW", "THUISHUW", "Children should live at home until marriage"),
    ("att_fam05", "INWOUDER", None, "Elderly parents should live with their children"),
    ("att_fam06", "KINDINW", None, "Parents should take adult children into their home"),
    ("att_chd01", "ZELFWOND", None, "A 17-year-old daughter may live independently"),
    ("att_chd02", "ZELFWONZ", None, "A 17-year-old son may live independently"),
    ("att_chd03", "ZELFHUW", None, "A child may decide whom to marry"),
    ("att_chd04", "INVLKEUS", None, "Parents' opinion plays an important role in choice of spouse"),
    ("att_chd05", "RESPOUD", "RESPOUD", "Parents should always be respected"),
    ("att_chd06", "INVLOUDF", None, "Older family members have more influence"),
    ("att_mor01", "MVTEVRIJ", None, "Interaction between men and women is too free"),
    ("att_mor02", "MINDSEKS", "MINDSEKS", "Openness about sex is wrong"),
    ("att_mor03", "ZELFEUTH", None, "In pain, one should decide about one's own death"),
    ("att_rel01", "GEENONTK", None, "It is a pity that secularisation takes place"),
    ("att_rel02", "GEENRELD", None, "Annoying if daughter marries someone of another faith"),
    ("att_rel03", "GEENRELZ", None, "Annoying if son marries someone of another faith"),
    ("att_rel04", "RELIGSCH", None, "Child's school should match the family's religion"),
    ("att_soc01", "CULTDIV", None, "Good that society consists of different cultures"),
    ("att_soc02", "BEHCULT", None, "Hard to keep one's culture and be accepted"),
    ("att_soc03", "ASIELMAK", None, "It should be easier to obtain asylum"),
    ("att_soc04", "RECHTUIT", None, "Foreigners should have the same rights as Dutch"),
    ("att_soc05", "VEELALLO", None, "Too many migrants live in the Netherlands"),
    ("att_soc06", "NACCALLO", None, "Migrants are not accepted in the Netherlands"),
    ("att_soc07", "ECONAFH", None, "The economy depends on migrants"),
    ("att_soc08", "SLECHTWK", None, "A neighbourhood does not improve with many migrants"),
    ("att_nl01", "KANSALLO", "KANSALLO", "As a foreigner you get every chance"),
    ("att_nl02", "NLVIJAND", None, "The Netherlands is hostile to foreigners"),
    ("att_nl03", "RESPRECH", "RESPRECH", "Rights of foreigners are respected"),
    ("att_nl04", "NLGASTV", "NLGASTV", "The Netherlands is hospitable"),
    ("att_nl05", "ONVERSCH", None, "People are indifferent to foreigners"),
    ("att_nl06", "RECHTVNL", None, "As a foreigner you are treated fairly"),
    ("att_nl07", "BEPERKNL", None, "There are many restrictions for foreigners"),
    ("att_nl08", "OPENCULT", "OPENCULT", "The Netherlands is open to foreign cultures"),
    ("att_fam07", "FAMHECHT", None, "Family ties are close"),
    ("att_fam08", "GEBFAM", None, "Family members keep each other informed"),
    ("att_fam09", "EIGGANG", None, "Everyone in the family goes their own way"),
    ("att_fam10", "ZORGOUD", None, "Children should care for sick parents"),
    ("att_fam11", "OPPASKK", None, "Grandparents should look after grandchildren"),
    ("att_fam12", "FAMSTEUN", None, "Family should stand by you in times of worry"),
    ("att_fam13", "PROBFAM", None, "Prefer to discuss problems with family"),
    ("att_fam14", "OUDGELD", None, "Normal for parents to give money to children"),
    ("att_fam15", "REKFAM", None, "You must always be able to count on family"),
    ("att_fam16", "LIEVERVR", None, "Prefer friends over family visiting"),
    ("att_fam17", "KIBEZOUD", None, "Children should visit parents once a week"),
    ("att_fam18", "KLAARFAM", None, "Family members should be there for each other"),
    ("att_fam19", "VERTRFAM", None, "Trust family more than friends"),
]
for t, s02, s03, lab in AGREE:
    V(t, "att", lab + " (agreement)", s02, s03, "agree5", universe=U_INT if s03 else U_INT02)
V("att_chd_val1", "att", "Most important quality for a 17-year-old", "BELKIND1", "BELKIND1", "child_value", universe=U_INT)
V("att_chd_val2", "att", "Second most important quality for a 17-year-old", "BELKIND2", "BELKIND2", "child_value", universe=U_INT)
V("att_chd_frnd_orig", "att", "Opinion on child having friends of other origin", "AFKVRIKI", "AFKVRIKI", "annoy5", universe=U_INT)
V("att_chd_prtnr_orig", "att", "Opinion on child having a partner of other origin", "AFKPARKI", "AFKPARKI", "annoy5", universe=U_INT)
V("att_nbr_choice", "att", "Preferred neighbour: compatriot or Dutch", "KEUSBUUR", "KEUSBUUR", "neighbour_choice", universe=U_HEAD)
V("att_live_nl", "att", "Feeling about living in the Netherlands", "WONALGNL", "WONALGNL", "living_nl5", universe=U_INT)
V("att_safe_nl", "att", "Feels safe in the Netherlands", None, "VEILIGNL", "safe5", universe=U_HEAD03)
V("att_dut_par", "att", "Opinion on how Dutch parents raise children", "OPVOEDNL", None, "parenting4", universe=U_HEAD02)
V("att_ease_dut", "att", "Feels at ease among native Dutch", "GEMAKNL", None, "at_ease4", universe=U_HEAD02)
for s, t, lab in [("GEZELLIG", "att_dut01", "sociable"), ("EERLIJK", "att_dut02", "honest"), ("GESLOTEN", "att_dut03", "reserved"),
                  ("BELEEFD", "att_dut04", "polite"), ("BEMOEIZ", "att_dut05", "meddlesome"), ("GASTVRIJ", "att_dut06", "hospitable"),
                  ("GIERIG", "att_dut07", "stingy"), ("NETJES", "att_dut08", "neat"), ("VERDRAAG", "att_dut09", "tolerant"),
                  ("HULPV", "att_dut10", "helpful"), ("WANTROUW", "att_dut11", "distrustful"), ("VRIENDL", "att_dut12", "friendly")]:
    V(t, "att", f"Native Dutch are {lab}", s, None, "trait4", universe=U_HEAD02)

# ============================================================== rel_
V("rel_den_det", "rel", "Religious denomination, detailed (harmonized list)", "RELIGIE0", "RELIGIE0", "religion_det", universe=U_INT)
for c, t in [(0, 0), (1, 11), (2, 12), (3, 13), (4, 21), (5, 22), (6, 23), (7, 24), (8, 25), (9, 31), (10, 32), (11, 33), (12, 34), (13, 35), (14, 36), (15, 38), (16, 99)]:
    M("rel_den_det", S02, "RELIGIE0", c, t)
for c, t in [(0, 0), (1, 21), (2, 22), (3, 23), (4, 24), (5, 25), (6, 41), (7, 42), (8, 43), (9, 44), (10, 13), (11, 38), (12, 37), (13, 31), (14, 99)]:
    M("rel_den_det", S03, "RELIGIE0", c, t)
V("rel_den_cat", "rel", "Religious denomination, 5 categories", "RELIGIE", "RELIGIEA", "religion_cat", universe=U_INT,
  notes="SPVN 2003: 1 Islam -> 2, 2 Christianity -> 3, 3 other -> 4 (no Hindu category offered).")
M("rel_den_cat", S03, "RELIGIEA", 1, 2); M("rel_den_cat", S03, "RELIGIEA", 2, 3); M("rel_den_cat", S03, "RELIGIEA", 3, 4)
V("rel_same", "rel", "Same religion as raised in", "ZELFDREL", None, "same_religion", universe=U_INT02)
V("rel_raised_det", "rel", "Religion raised in, detailed (harmonized list)", "RELIGOV0", None, "religion_det", universe=U_INT02)
for c, t in [(0, 0), (1, 11), (2, 12), (3, 13), (4, 21), (5, 22), (6, 23), (7, 24), (8, 25), (9, 31), (10, 32), (11, 33), (12, 34), (13, 35), (14, 36), (15, 38), (16, 99)]:
    M("rel_raised_det", S02, "RELIGOV0", c, t)
V("rel_raised_cat", "rel", "Religion raised in, 5 categories", "RELIGOPV", None, "religion_cat", universe=U_INT02)
V("rel_attend", "rel", "Attendance of religious meetings", "KERKBEZ", "KERKBEZ", "attendance4", universe=U_INT)

# ============================================================== iden_
V("iden_prim", "iden", "Self-identification: own group or Dutch", "ZELFIDEN", None, "iden_prim", universe=U_HEAD02)
V("iden_scale", "iden", "Feels more Dutch or more own group (5-point)", "ZELFID", None, "iden_scale5", universe=U_HEAD02)
V("iden_oth", "iden", "Considers him/herself part of another population group", None, "ZELFIDEN", "iden_oth", universe=U_HEAD03,
  notes="Different question from iden_primary (SPVA 2002).")
V("iden_sub", "iden", "Ethnic subgroup", "SUBGROEP", "ETNIDEN", "ethsubgroup", universe=U_ALL,
  notes="SPVA 2002: ISEO construct from self-identification and language (all household members, 13 codes). SPVN 2003: self-reported question (heads). Codes combined in one list; documented doc/data label discrepancy for SPVA 2002 (data labels used).")
for c, t in [(0, 41), (1, 21), (2, 22), (3, 23), (4, 24), (5, 25), (6, 26), (7, 27), (9, 29), (10, 30), (11, 31), (12, 32), (13, 33), (14, 34),
             (15, 35), (16, 36), (17, 37), (18, 38), (19, 39), (20, 40), (21, 20), (98, 98)]:
    M("iden_sub", S03, "ETNIDEN", c, t)
M("iden_sub", S03, "ETNIDEN", -4, 98, "source -4 labelled 'anders: namelijk' with free text in ETNIDENA (n=373): substantive, not missing")
V("iden_sub_txt", "iden", "Ethnic subgroup, other (open text)", None, "ETNIDENA", type="str", universe=U_HEAD03)

# ============================================================== disc_
V("disc_perc", "disc", "Perceived frequency of discrimination against own group", "DISCALG", "DISCALG", "freq5_disc", universe=U_HEAD)
V("disc_exp", "disc", "Personally experienced discrimination", "DISCZELF", "DISCZELF", "freq5_disc", universe=U_HEAD)

# ============================================================== ret_
V("ret_wish", "ret", "Wishes to return permanently to country of origin", "WILTERUG", "WILTERUG", "return3", universe=U_HEAD,
  notes="'Don't know' is a substantive category (2) in both surveys: SPVA 2002 code 2; SPVN 2003 code 3 'weet niet' (n=658, consistent with TERUGK) mapped to 2; 'no' is 3 (2002) and 2 (2003) -> 3.")
M("ret_wish", S02, "WILTERUG", 2, 2, "'weet niet' is an answer category here, not a missing code")
M("ret_wish", S03, "WILTERUG", 1, 1); M("ret_wish", S03, "WILTERUG", 3, 2, "code 3 = weet niet (n=658, matches TERUGK)"); M("ret_wish", S03, "WILTERUG", 2, 3)
V("ret_poss", "ret", "Sees possibilities to return to country of origin", "MOGTERUG", "MOGTERUG", "return3", universe=U_HEAD,
  notes="Same treatment of don't know as ret_wish.")
M("ret_poss", S02, "MOGTERUG", 2, 2, "'weet niet' is an answer category here, not a missing code")
M("ret_poss", S03, "MOGTERUG", 1, 1); M("ret_poss", S03, "MOGTERUG", 3, 2, "code 3 = weet niet (n=406)"); M("ret_poss", S03, "MOGTERUG", 2, 3)
V("ret_wishposs", "ret", "Return wish and possibilities combined (ISEO construct)", "TERUGK", "TERUGK", "return_combined", universe=U_HEAD,
  notes="Code 3 'weet niet' is substantive in both surveys and kept.")
M("ret_wishposs", S02, "TERUGK", 3, 3); M("ret_wishposs", S03, "TERUGK", 3, 3)
V("ret_noreason", "ret", "Main reason for not wanting to return", "NIETTRUG", "NIETTRUG", "reason_not_return", universe=U_HEAD,
  notes="SPVN 2003 code 9 = other -> 10.")
M("ret_noreason", S03, "NIETTRUG", 9, 10)

# ============================================================== questionnaire links the name match cannot make (names misprinted or absent in the codebooks)
L(S03, "WENIVOPL", "VRAAG 106 (E4f)")     # printed as WENIVOP
L(S03, "ZELFDADR", "VRAAG 163 (G1c)")     # printed as ZELFADR
L(S03, "RELIGIEA", "VRAAG 212 (L1b)")     # recode of RELIGIE0
L(S03, "ETNIDENA", "VRAAG 222 (M1b)")     # open answer of ETNIDEN
L(S03, "LFTPART", "")                     # constructed from the roster
L(S03, "GEBLPART", "")                    # constructed from the roster
L(S03, "LFTHUW", "")                      # constructed from HUWJAARA and age
L(S02, "KLAARFAM", "M5b (2)#2")           # printed as KLAAARFAM in the second M5b grid
L(S02, "MAXRICH", "")                     # constructed: field of the highest diploma (from B1c/B3 richting items); not printed in the questionnaire
L(S02, "UURLOON", "")                     # constructed: net hourly wage from income and hours
L(S03, "UURLOON", "")                     # constructed: net hourly wage from income and hours

# ---- respondent types whose questionnaire did not contain an item (household surveys) --------------------------------
# The persons file of SPVA 2002 holds heads and other interviewed members, but blocks L (Beeldvorming) and M
# (Familierelaties) of the main questionnaire were not in the mini questionnaire (which ends with block E, social
# contacts): no other member has a value on these items.  The reverse holds for the bridge-class item of the mini
# questionnaire (B2f) and, in SPVN 2003, for three items the deposit labels 'alleen mini's'.  02_harmonize sets .e for the
# type that was not asked (after checking that it has no valid value); the universe texts say the same.
_HEADS_ONLY_02 = (
    ["hous_nbhd_pleas4", "hous_nbhd_forgn", "att_nbr_choice", "att_live_nl", "att_dut_par", "att_ease_dut", "disc_perc", "disc_exp"]
    + [f"att_soc{i:02d}" for i in range(1, 9)] + [f"att_nl{i:02d}" for i in range(1, 9)] + [f"att_fam{i:02d}" for i in range(7, 20)]
    + [f"att_dut{i:02d}" for i in range(1, 13)]
    + ["dem_nchd_away", "fam_oblig", "fam_affect", "fam_par_alive", "fam_par_which", "fam_par_byr", "fam_par_res", "fam_par_seen", "fam_par_cont",
       "fam_par_help_fr", "fam_par_adv_fr", "fam_par_help_to", "fam_par_adv_to", "fam_chd_sex", "fam_chd_byr", "fam_chd_res", "fam_chd_seen",
       "fam_chd_cont", "fam_chd_help_fr", "fam_chd_adv_fr", "fam_chd_help_to", "fam_chd_adv_to"])
for _t in _HEADS_ONLY_02:
    ASKED(_t, S02, "heads", "main-questionnaire block L (Beeldvorming) or M (Familierelaties); the mini questionnaire ends with block E and the persons file holds no answer of another member",
          universe="Heads of household (main questionnaire)")
ASKED("edu_cur_bridge", S02, "members", "mini questionnaire B2f (type of bridge class); the main questionnaire has no such item",
      universe="Other interviewed household members aged 12+ who follow a bridge class (mini questionnaire)")
for _t in ["soc_leis_nl", "svy_proxy", "lab_12h"]:
    ASKED(_t, S03, "members", "mini questionnaire only (source label 'alleen mini's'); heads were not asked",
          universe="Other interviewed household members aged 12+ (mini questionnaire; heads of household were not asked)")
