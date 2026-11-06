# -*- coding: utf-8 -*-
"""
IMPD crosswalk — LAS 2004/05, SIM 2006, SING 2009 and SIM 2011 (v0.4.0).

Four flat person-sample surveys added to the registry built by variables.py (SPVA 2002 / SPVN 2003) and
variables_sim.py (SIM 2015 / SIM 2020).  Every source variable of each file is either attached to an existing
target (A), declared as a new target (V), or deliberately skipped (SKIP, listed in crosswalks/source_skipped.csv).

Conventions (see docs/decisions.md section 8):
- codes identical to the target's value set are taken as-is; everything else is an explicit value-map row;
- survey-specific missing codes are handled by the rules in build.py (missing_rules), not here;
- 'B' versions of split items that are empty in the DANS deposit (mixed-mode experiment not deposited) are skipped.
"""
from declare import V, M, W, L, U, A, SKIP, find, VARS, VMAP
from valuesets import VALUESETS

S04, S06, S09, S11 = "las2004", "sim2006", "sing2009", "sim2011"


def MM(target, survey, src, pairs, note=""):
    for a, b in pairs:
        M(target, survey, src, a, b, note)


# ====================================================================================================== SIM 2011
U11 = "All respondents (SIM 2011)"
U11M = "Respondents with a migration background (SIM 2011)"
U11P = "Respondents with a partner (SIM 2011)"
U11E = "Employees (SIM 2011)"
U11W = "Employed respondents (SIM 2011)"
U11N = "Respondents without paid work (SIM 2011)"
U11C = "Respondents with children (SIM 2011)"
U11K = "Respondents with a co-resident child aged 0-17 selected for the parenting module (SIM 2011)"
U11R = "Religious respondents (SIM 2011)"
U11MU = "Muslim respondents (SIM 2011)"
U11I = "Respondents who followed a civic integration programme (SIM 2011)"
U11Y = "Respondents aged 15-17 whose parent answered the parent questions (SIM 2011)"

# ---- survey administration
A("svy_mode", S11, "METHODE")                                          # 2 = CAPI for every record
V("svy_fw_phase", "svy", "Fieldwork phase (SIM 2011: 1 = main phase, 2 = re-approach of non-respondents)", s11="FASE", type="cat",
  valueset="phase2", universe=U11)
V("svy_dur_min", "svy", "Interview duration in minutes (SIM 2011, as logged)", s11="TIJDSDUUR", type="num", universe=U11,
  notes="SIM 2015 logs seconds (svy_dur_sec).")
A("svy_lang_q", S11, "TAAL_CAWI", pairs=[(-5, ".c")], note="CAWI not in this deposit: all -5")
SKIP(S11, "ONDERZOEK", "constant: all records belong to the main survey (the mixed-mode experiment is not deposited)")
A("svy_wgt", S11, "weegtot")
V("svy_wgt_grp", "svy", "Survey weight within origin group (SIM 2006/2011: weegherk)", s11="weegherk", type="num", universe=U11,
  notes="Weights to the population of each origin group separately; svy_wgt (weegtot) weights to the five groups together.")
V("svy_wgt_raise", "svy", "Raising factor to population totals (SIM 2006/2011: ophtot)", s11="ophtot", type="num", universe=U11)
A("svy_fw_mo", S11, "intmaand")
A("svy_fw_yr_n", S11, "intjaar")
V("svy_eval01", "svy", "Opinion of the interview: interesting / enjoyable (mentioned)", s11="V1500C1", valueset="mentioned", universe=U11)
V("svy_eval02", "svy", "Opinion of the interview: annoying (mentioned)", s11="V1500C2", valueset="mentioned", universe=U11)
V("svy_eval03", "svy", "Opinion of the interview: too long (mentioned)", s11="V1500C3", valueset="mentioned", universe=U11)
V("svy_eval04", "svy", "Opinion of the interview: too difficult (mentioned)", s11="V1500C4", valueset="mentioned", universe=U11)
V("svy_eval05", "svy", "Opinion of the interview: invasion of privacy (mentioned)", s11="V1500C5", valueset="mentioned", universe=U11)
V("svy_eval06", "svy", "Opinion of the interview: other (mentioned)", s11="V1500C6", valueset="mentioned", universe=U11)
V("svy_remarks", "svy", "Respondent gave additional remarks at the end of the interview", s11="OPEN", valueset="yesno", universe=U11)
M("svy_remarks", S11, "OPEN", 1, 1); M("svy_remarks", S11, "OPEN", 2, 0)
V("svy_fup3", "svy", "Willing to take part in follow-up research (yes / maybe / no)", s11="HERHAAL", valueset="willing3", universe=U11,
  notes="SPVA 2002 asked yes/no (svy_fup).")
V("svy_parent_q", "svy", "Parent asked to join for the parent questions (respondents aged 15-17)", s11="VROUDER", valueset="parent_q3",
  universe="Respondents aged 15-17 (SIM 2011)")
V("svy_incentive5", "svy", "Importance of the promised reward for taking part", s11="TIENEURO", valueset="important5", universe=U11)
V("svy_incentive_pref", "svy", "Preferred form of the reward", s11="BON", valueset="incentive2", universe=U11)
V("svy_charity", "svy", "Charity chosen for the reward", s11="GOEDDOEL", valueset="charity4", universe="Respondents who gave the reward to charity (SIM 2011)")
V("svy_addr_change", "svy", "Address details changed (interviewer check)", s11="ADRESWIJZ", valueset="yesno", universe=U11)
M("svy_addr_change", S11, "ADRESWIJZ", 1, 0); M("svy_addr_change", S11, "ADRESWIJZ", 2, 1)
A("svy_lang_hh", S11, "TAALINT", pairs=[(6, ".d")], u=U11M, note="'anders' cannot be placed on the Dutch/other-language scale")
V("svy_lang_oth", "svy", "Other language used in the interview", s11="TAALINT2", valueset="other_language",
  universe="Interviews (partly) in another language than Dutch (SIM 2011)")
MM("svy_lang_oth", S11, "TAALINT2", [(1, 11), (2, 21), (3, 22), (6, 96)])
V("svy_understood4", "svy", "How well the respondent understood the questions (interviewer rating)", s11="INTBEGR", valueset="good4", universe=U11)
V("svy_others_present", "svy", "Others present during the interview and their influence (interviewer rating)", s11="ALLEEN", valueset="presence4", universe=U11)
A("id_src", S11, "volgnummer")

# ---- demography
V("dem_gen_reg", "dem", "Migrant generation according to the population register (GBA)", s11="GENGBA", valueset="generation", universe=U11,
  notes="dem_gen is based on the respondent's own answers in SIM 2006/2011; this is the register classification.")
M("dem_gen_reg", S11, "GENGBA", -5, 0, "native Dutch sample")
A("dem_sex", S11, "GESLACHT", pairs=[("'1'", 1), ("'2'", 2)], note="string-coded after CBS protection")
A("dem_has_chd", S11, "KINDEREN", yn12=True)
A("dem_nchd", S11, "AANTKIND", u=U11C)
A("dem_nchd_home", S11, "INWKIND", u=U11C)
A("dem_has_prtnr", S11, "PARTNER", yn12=True)
A("dem_prtnr_cores", S11, "INWPART", yn12=True, u=U11P)
A("hh_size", S11, "HHOMV")
A("dem_livsit", S11, "GEZPOS", pairs=[(5, 98)], u="Respondents not living alone (SIM 2011)")
A("dem_prtnr_sex", S11, "GESLPART", u=U11P)
A("dem_prtnr_brthcntry", S11, "geblpart_ned", pairs=[(1, 5022), (2, 6043), (3, 7011), (4, 5007), (5, 6030), (6, 9999)], u=U11P)
A("dem_prtnr_res", S11, "PARTNL", pairs=[(1, 1), (2, 2), (3, 6)], u="Respondents whose partner does not live in the same house (SIM 2011)")
A("dem_prtnr_mar", S11, "HUWPART", yn12=True, u=U11P)
A("dem_mar_yr", S11, "HUWJAAR", u="Respondents with a partner (year of marriage / registered partnership / moving in together), SIM 2011")
A("dem_nchd_away", S11, "NIETINWKIND", u=U11C)
A("dem_chd_res", S11, "KINDNL", u="Respondents with children not (all) living at home (SIM 2011)")
V("dem_prtnr_emp", "dem", "Partner currently has paid work", s11="PARTWERK", valueset="yesno", universe=U11P, yn12=True)
V("dem_prtnr_hrs", "dem", "Partner's contractual working hours per week", s11="PARTUREN", type="num", universe="Respondents whose partner has paid work (SIM 2011)")
A("dem_prtnr_act", S11, "PARTHFDA", pairs=[(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 98)],
  u="Respondents whose partner has no paid work (SIM 2011; partners with paid work: see dem_prtnr_emp)")
V("dem_age_cat5y", "dem", "Age in 5-year classes (CBS-protected surveys)", s11="CATLFT5JR", valueset="age_cat5y", universe=U11,
  notes="SIM 2011 and LAS 2004/05 deliver age in classes only; 70+ is one class in SIM 2011.")
MM("dem_age_cat5y", S11, "CATLFT5JR", [(f"'{i:02d}'", i) for i in range(1, 13)])
A("dem_age_cat", S11, "CATLFT5JR", pairs=[("'01'", 1), ("'02'", 1), ("'03'", 2), ("'04'", 2), ("'05'", 3), ("'06'", 3), ("'07'", 4), ("'08'", 4),
                                          ("'09'", 5), ("'10'", 5), ("'11'", 6), ("'12'", 8)],
  note="70+ cannot be split into 65-74 / 75+: code 8")
V("dem_prtnr_age_cat5y", "dem", "Partner's age in 5-year classes", s11="CATLFT5JRPART", valueset="age_cat5y", universe=U11P)
MM("dem_prtnr_age_cat5y", S11, "CATLFT5JRPART", [(f"'{i:02d}'", i) for i in range(1, 13)] + [("'00'", ".c")])
A("dem_eth", S11, "etngrp", pairs=[(5, 90)])
A("dem_gen", S11, "generat", pairs=[(-9, 0)])
W("dem_eth", "SIM 2006/2011: origin group based on the respondent's own answers on countries of birth (etngrp), not on the register.")

# ---- migration, nationality, return, transnational ties
A("mig_reason", S11, "REDMIGR", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 14), (8, 15), (9, 8), (10, 13), (11, 17), (12, 10)],
  u="First-generation respondents (SIM 2011)")
A("mig_yr_arr", S11, "MIGRJAAR", u="First-generation respondents (SIM 2011)")
A("mig_reason_prtnr", S11, "REDMI_P", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 14), (8, 15), (9, 8), (10, 13), (11, 17), (12, 10)],
  u="Respondents whose partner was born abroad (SIM 2011)")
V("mig_yr_arr_prtnr", "mig", "Year the partner first came to live in the Netherlands", s11="MIGRVA_P", type="year",
  universe="Respondents whose partner was born abroad (SIM 2011)")
A("nat_orig", S11, "NATIONAL", yn12=True, u=U11M)
A("nat_nl", S11, "NATIONNL", yn12=True, u=U11M)
V("nat_nl_always", "nat", "Has always had Dutch nationality", s11="NLALTIJD", valueset="yesno", yn12=True,
  universe="Respondents with a migration background and Dutch nationality (SIM 2011)")
V("nat_nl_reason", "nat", "Main reason for choosing Dutch nationality", s11="NLKIES", valueset="nat_reason9",
  universe="Respondents who acquired Dutch nationality (SIM 2011)")
A("ret_wish", S11, "WILTERUG", pairs=[(1, 1), (2, 3), (-3, 2)], u=U11M)
V("ret_reason", "ret", "Main reason for wanting to return to the country of origin", s11="WELTRUG", valueset="ret_reason13",
  universe="Respondents who want to return (SIM 2011)")
A("ret_poss", S11, "MOGTERUG", pairs=[(1, 1), (2, 3)], u="Respondents who want to return (SIM 2011)")
A("ret_noreason", S11, "NIETTRUG", pairs=[(1, 1), (2, 4), (3, 6), (4, 9), (5, 11), (6, 7), (7, 12), (8, 5), (9, 3), (10, 13), (11, 2), (12, 8), (13, 10)],
  u="Respondents who do not want to return (SIM 2011)")
A("trn_house", S11, "HUISBUI", yn12=True, u=U11M)
V("trn_cont_fam3", "trn", "Contact with family in the country of origin (much / sometimes / never)", s11="CONTHERK", valueset="freq3", universe=U11M,
  notes="SIM 2015 asked a 5-point frequency (trn_cont_fam).")
M("trn_cont_fam3", S11, "CONTHERK", 4, ".c", "no family in the country of origin")
V("trn_visit_yearly", "trn", "Visits family or friends in the country of origin every year", s11="BEZOEHER", valueset="visit3", universe=U11M)
M("trn_visit_yearly", S11, "BEZOEHER", 4, ".c", "not applicable")
A("trn_visit12m", S11, "BEZ2010HER", yn12=True, u=U11M)
A("trn_visit_dur", S11, "BEZ2010LANG", u="Respondents who visited the country of origin in 2010 (SIM 2011)")
V("trn_homesick", "trn", "Homesick for the country of origin (often / sometimes / never)", s11="HEIMWEE", valueset="freq3", universe=U11M)
A("trn_remit", S11, "GELDHERK", yn12=True, u=U11M)
V("trn_remit01", "trn", "Money or goods sent to: partner / spouse / fiance(e) (mentioned)", s11="GELDPART", valueset="mentioned",
  universe="Households that sent money or goods to the country of origin (SIM 2011)")
V("trn_remit02", "trn", "Money or goods sent to: children (mentioned)", s11="GELDKIND", valueset="mentioned", universe="Households that sent money or goods (SIM 2011)")
V("trn_remit03", "trn", "Money or goods sent to: parents (mentioned)", s11="GELDOUD", valueset="mentioned", universe="Households that sent money or goods (SIM 2011)")
V("trn_remit04", "trn", "Money or goods sent to: other family members (mentioned)", s11="GELDFAM", valueset="mentioned", universe="Households that sent money or goods (SIM 2011)")
V("trn_remit05", "trn", "Money or goods sent to: others (mentioned)", s11="GELDAND", valueset="mentioned", universe="Households that sent money or goods (SIM 2011)")
V("trn_remit06", "trn", "Money or goods sent to: organisations (mentioned)", s11="GELDORG", valueset="mentioned", universe="Households that sent money or goods (SIM 2011)")

# ---- civic integration
A("int_crs", S11, "INBCURUS", pairs=[(1, 1), (2, 1), (3, 0)], u=U11M)
A("int_crs_st", S11, "INBCURUS", u=U11M)
V("int_crs_noreason", "int", "Main reason for not following a civic integration programme", s11="REDGEINB", valueset="inb_noreason",
  universe="Respondents with a migration background who did not follow a civic integration programme (SIM 2011)")
V("int_crs_yr", "int", "Year the civic integration programme started", s11="JRINBST", type="year", universe=U11I)
A("int_exam", S11, "EXAMINBA", pairs=[(1, 1), (2, 3)], u="Respondents who completed a civic integration programme in or after 2007 (SIM 2011)")
V("int_nt2_state", "int", "Passed the NT2 state examination (Dutch as a second language)", s11="NT2EX", valueset="yesno", yn12=True,
  universe="Respondents who completed a civic integration programme in or after 2007 (SIM 2011)")
A("int_crs_dipl", S11, "DIPLINBA", pairs=[(1, 1), (2, 0)], u="Respondents who completed a civic integration programme before 2007 (SIM 2011)")
A("int_nt2", S11, "NT2CERT", yn12=True, u="Respondents who completed a civic integration programme before 2007 (SIM 2011)")
A("int_crs_sat", S11, "TEVRINB", u=U11I)
V("int_eff01", "int", "Civic integration programme improved my Dutch (agreement)", s11="INBTAAL", valueset="agree5", universe=U11I)
V("int_eff02", "int", "Thanks to the programme it is easier to find work (agreement)", s11="INBWERK", valueset="agree5", universe=U11I)
V("int_eff03", "int", "Thanks to the programme I got to know more people (agreement)", s11="INBSOC", valueset="agree5", universe=U11I)
V("int_eff04", "int", "Thanks to the programme it is easier to start an education (agreement)", s11="INBOPL", valueset="agree5", universe=U11I)
V("int_eff05", "int", "Thanks to the programme I gained self-confidence (agreement)", s11="INBZELF", valueset="agree5", universe=U11I)
V("int_eff06", "int", "I learned Dutch faster in daily life than in the programme (agreement)", s11="NL", valueset="agree5", universe=U11I)
M("int_eff06", S11, "NL", 6, ".a", "weet (nog) niet")
A("int_nlcrs", S11, "NLCURS", pairs=[(1, 1), (2, 1), (3, 0), (4, 0)], u=U11M)
A("int_nlcrs_det", S11, "NLCURS", u=U11M)

# ---- labour market
A("lab_emptype", S11, "ZELFST", pairs=[(1, 1), (2, 2)], u=U11W)
A("lab_occ", S11, "BEROEP", u=U11E)
W("lab_occ", "SIM 2011: Standaard Beroepenclassificatie 1992 codes (5 digits, first digit = skill level); SPVA/SPVN: SBC-1992 as coded by ISEO.")
A("lab_ind", S11, "BEDRIJF", u=U11E)
A("lab_tenure", S11, "ERVBEDR_JR", u=U11E)
V("lab_tenure_mo", "lab", "Months with current employer (in addition to the years)", s11="ERVBEDR_MND", type="num", universe=U11E)
V("lab_sup", "lab", "Supervises other people in the current job", s11="LEIDING", valueset="yesno", yn12=True, universe=U11E)
A("lab_nsup", S11, "NLEIDING", pairs=[(7777, ".d")], u="Employees who supervise others (SIM 2011)", note="'meer dan 1000'")
A("lab_match", S11, "ONDERBEN", u=U11E)
A("lab_train", S11, "CURSUSBD", pairs=[(1, 1), (2, 1), (3, 0)], u=U11E)
A("lab_perm", S11, "VASTWERK", u=U11E)
A("lab_coll_bal", S11, "CONTACTW", u=U11E)
A("lab_se_type", S11, "ZELFFREE", u="Self-employed respondents (SIM 2011)")
V("lab_se_occ", "lab", "Occupation of the self-employed (SBC-1992 code)", s11="BEROEP2", type="num", universe="Self-employed respondents (SIM 2011)")
A("lab_se_nemp", S11, "NPERS", pairs=[(7777, ".d")], u="Self-employed respondents (SIM 2011)")
A("lab_hrs_se", S11, "URENWRKZ", u="Self-employed respondents (SIM 2011)")
A("lab_coll_bal_se", S11, "CONTACWZ", u="Self-employed respondents (SIM 2011)")
A("lab_exp", S11, "ARBERV_JR", u=U11W)
A("lab_exp_mo", S11, "ARBERV_MND", u=U11W)
V("lab_unemp_ever", "lab", "Has ever been unemployed", s11="WERKL", valueset="yesno", yn12=True, universe=U11W)
A("lab_everwork", S11, "WERKNL", yn12=True, u=U11N)
A("lab_exp_prev", S11, "ARBERV_W_JR", u="Respondents without paid work who ever worked (SIM 2011)")
A("lab_exp_prev_mo", S11, "ARBERV_W_MND", u="Respondents without paid work who ever worked (SIM 2011)")
A("lab_nowork_yrs", S11, "NWRKDUUR_JR", u="Respondents without paid work who ever worked (SIM 2011)")
A("lab_nowork_mo", S11, "NWRKDUUR_MND", u="Respondents without paid work who ever worked (SIM 2011)")
A("lab_prev_occ", S11, "BEROEPV", u="Respondents without paid work who ever worked (SIM 2011)")
A("lab_left_how", S11, "ONTSLAG", u="Respondents without paid work who ever worked (SIM 2011)")
A("lab_dism_reason", S11, "REDONTSL", pairs=[(10, 11), (11, 10)], u="Respondents dismissed from their last job (SIM 2011)")
A("lab_act", S11, "HFDACT", pairs=[(-1, ".c"), (5, 5), (6, 5), (7, 6)], u=U11N, note="-1 = has paid work (not asked)")
A("lab_want", S11, "WIL12UUR", pairs=[(1, 1), (2, 3), (3, 3), (4, 1), (7, 2)], u=U11N,
  note="codes as in SIM 2015 wilw12uv2: 1 yes 12+, 2 no, 3 no not now, 4 already found work, 7 yes <12 hours (labels partly missing in the deposit)")
V("lab_lf3", "lab", "Labour force status (SCP classification bb_ned)", s11="bb_ned", valueset="lf3", universe=U11)
A("lab_lf", S11, "bb_ned", pairs=[(1, 1), (2, 1), (3, 0)])
V("lab_hrs_cat5", "lab", "Working hours per week in classes (SCP: urencat)", s11="urencat", type="cat", valueset="hours_cat5", universe=U11)
M("lab_hrs_cat5", S11, "urencat", -1, ".c", "no paid work")

# ---- income
V("hh_inc_band", "hh", "Net monthly income of respondent and partner, 500-euro bands (SIM 2011; excludes co-resident children's income and child benefit)", s11="HHINK", valueset="hh_income_band8", scope="household",
  universe="Respondents who are head or partner of the household (SIM 2011)",
  notes="Household income definitions differ between surveys and are kept apart: SIM 2011 HHINK = respondent + partner, explicitly excluding earning children's income and child benefit (VRAAG 615); LAS 2004/05 GEZINK = respondent + partner + co-resident children with own income (VRAAG 77), kept in hh_inc_band16; SPVA/SPVN hh_inc = household income as reported by the head (hh_inc_cat bands). No common household-income measure can be derived from the delivered bands.")
V("inc_change5", "inc", "Financial situation of the household compared with 12 months ago", s11="FINSUBJ", valueset="change5",
  universe="Respondents who are head or partner of the household (SIM 2011)")
V("inc_rel_nl5", "inc", "Standard of living compared with other people in the Netherlands", s11="LVSTNL", valueset="relative5",
  universe="Respondents who are head or partner of the household (SIM 2011)")
V("inc_ben_yrs01", "inc", "Years receiving social assistance (bijstand)", s11="UITKDUUR_BIJSTAND_JR", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_mo01", "inc", "Months receiving social assistance (in addition to years)", s11="UITKDUUR_BIJSTAND_MND", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_yrs02", "inc", "Years receiving unemployment benefit (WW)", s11="UITKDUUR_WWUITK_JR", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_mo02", "inc", "Months receiving unemployment benefit (in addition to years)", s11="UITKDUUR_WWUITK_MND", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_yrs03", "inc", "Years receiving disability benefit (WAO/WIA)", s11="UITKDUUR_WAOUITK_JR", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_mo03", "inc", "Months receiving disability benefit (in addition to years)", s11="UITKDUUR_WAOUITK_MND", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_yrs04", "inc", "Years receiving pension / AOW / early retirement", s11="UITKDUUR_AOWUITK_JR", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_mo04", "inc", "Months receiving pension (in addition to years)", s11="UITKDUUR_AOWUITK_MND", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_yrs05", "inc", "Years receiving a student grant", s11="UITKDUUR_STUDIEF_JR", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_mo05", "inc", "Months receiving a student grant (in addition to years)", s11="UITKDUUR_STUDIEF_MND", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_yrs07", "inc", "Years receiving alimony", s11="UITKDUUR_ALIMEN_JR", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_mo07", "inc", "Months receiving alimony (in addition to years)", s11="UITKDUUR_ALIMEN_MND", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_yrs06", "inc", "Years receiving another benefit", s11="UITKDUUR_ANDUITK_JR", type="num", universe="Recipients of the benefit (SIM 2011)")
V("inc_ben_mo06", "inc", "Months receiving another benefit (in addition to years)", s11="UITKDUUR_ANDUITK_MND", type="num", universe="Recipients of the benefit (SIM 2011)")
V("hh_inc_band_par", "hh", "Net household income band reported by the parent of a 15-17-year-old respondent", s11="HHINK2", valueset="hh_income_band8",
  scope="household", universe=U11Y)
V("inc_change5_par", "inc", "Financial situation compared with 12 months ago, reported by the parent", s11="FINSUBJ2", valueset="change5", universe=U11Y)
V("inc_rel_nl5_par", "inc", "Standard of living compared with others, reported by the parent", s11="LVSTNL2", valueset="relative5", universe=U11Y)
V("trn_remit_par", "trn", "Household sent money or goods to the country of origin, reported by the parent", s11="GELDHERK2", valueset="yesno", yn12=True, universe=U11Y)
V("trn_remit_par_to", "trn", "Recipient of the money or goods, reported by the parent", s11="V1515", valueset="remit_to6",
  universe="Parents who reported remittances (SIM 2011)")

# ---- language
A("lang_nl_prtnr", S11, "TAALPART", u=U11P)
A("lang_nl_chd", S11, "TAALKIND", u=U11C)
A("lang_prob_spk", S11, "TAALGESP", pairs=[(1, 4), (2, 1), (3, 2), (4, 3)], u=U11M)
A("lang_prob_read", S11, "TAALKRAN", u=U11M)
A("lang_prob_write", S11, "TAALPEN", u=U11M)
A("lang_orig_follow", S11, "ETNIGESP", u=U11M)
A("lang_other", S11, "ETNITAAL", pairs=[(1, 21), (2, 22), (3, 11), (4, 12), (5, 13), (6, 31), (7, 31), (8, 32), (9, 32), (10, 32), (11, 34), (12, 33),
                                        (13, 35), (14, 36), (15, 96)],
  u="Respondents who can follow a conversation in a language of the country of origin (SIM 2011)")
W("lang_other", "SIM 2011: the origin-country language the respondent can follow best (Q656); SPVA 2002: other language usually spoken at home.")
V("lang_orig_prob_und", "lang", "Problems understanding the origin-country language (often / sometimes / never)", s11="ETNIVERS", valueset="freq3",
  universe="Respondents who can follow a conversation in a language of the country of origin (SIM 2011)")
A("lang_orig_prob", S11, "ETNISPRE", u="Respondents who can follow a conversation in a language of the country of origin (SIM 2011)")
V("lang_orig_vs_nl", "lang", "Speaks the origin-country language better, equally well or worse than Dutch", s11="TAALVGL", valueset="better3",
  universe="Respondents who can follow a conversation in a language of the country of origin (SIM 2011)")
V("lang_orig_read", "lang", "Problems reading the origin-country language", s11="ETNILEES", valueset="lang_prob4_rw",
  universe="Respondents who can follow a conversation in a language of the country of origin (SIM 2011)")
MM("lang_orig_read", S11, "ETNILEES", [(1, 4), (2, 1), (3, 2), (4, 3)])
V("lang_orig_write", "lang", "Problems writing the origin-country language", s11="ETNIPEN", valueset="lang_prob4_rw",
  universe="Respondents who can follow a conversation in a language of the country of origin (SIM 2011)")
MM("lang_orig_write", S11, "ETNIPEN", [(1, 4), (2, 1), (3, 2), (4, 3)])
A("lang_prob_eng", S11, "ENGFRDUI", pairs=[(1, 4), (2, 1), (3, 2), (4, 3)], u=U11M)
V("lang_nl_rated4", "lang", "Respondent's spoken Dutch as rated by the interviewer (4-point)", s11="TAALVAAR", valueset="good4", universe=U11M,
  notes="SPVA/SPVN used a 3-point rating (lang_nl_rated).")

# ---- identification
A("iden_nl5", S11, "VOELNL", u=U11M)
A("iden_orig5", S11, "VOELLVH", u=U11M)
A("iden_scale", S11, "ZELFIDEN", u=U11M)
V("iden_island5", "iden", "Feels (island group) - second identification item asked to the Antillean/Aruban group", s11="VOELANT", valueset="strength5",
  universe="Antillean/Aruban respondents (SIM 2011)")
A("iden_home_nl", S11, "THUISNL")
V("iden_fatherland_nl5", "iden", "Sees the Netherlands as his/her fatherland (strength)", s11="GOEDNL", valueset="strength5", universe=U11M)
V("iden_fatherland_orig5", "iden", "Sees the country of origin as his/her fatherland (strength)", s11="GOEDLVH", valueset="strength5", universe=U11M)
V("iden_allochtoon", "iden", "Sees him/herself as 'allochtoon'", s11="ZELFALL", valueset="yesno", yn12=True, universe=U11M)

# ---- social contacts and participation
V("soc_act01", "soc", "Attends meetings/activities of: sports club (mentioned)", s11="SPORTVER", valueset="mentioned", universe=U11)
V("soc_act02", "soc", "Attends meetings/activities of: leisure organisation (mentioned)", s11="VRIJVER", valueset="mentioned", universe=U11)
V("soc_act03", "soc", "Attends meetings/activities of: neighbourhood or tenants' association (mentioned)", s11="WIJKVER", valueset="mentioned", universe=U11)
V("soc_act04", "soc", "Attends meetings/activities of: trade union or professional organisation (mentioned)", s11="VAKBOND", valueset="mentioned", universe=U11)
V("soc_act05", "soc", "Attends meetings/activities of: organisation of or for migrants (mentioned)", s11="ALLVER", valueset="mentioned", universe=U11)
V("soc_act06", "soc", "Attends meetings/activities of: political party (mentioned)", s11="POLPART", valueset="mentioned", universe=U11)
V("soc_act07", "soc", "Attends meetings/activities of: religious organisation (mentioned)", s11="GODORG", valueset="mentioned", universe=U11)
V("soc_act08", "soc", "Attends meetings/activities of: nature, environment or international solidarity organisation (mentioned)", s11="NATUURVER", valueset="mentioned", universe=U11)
V("soc_act09", "soc", "Attends meetings/activities of: other organisation (mentioned)", s11="ANDORG", valueset="mentioned", universe=U11)
V("soc_act10", "soc", "Attends meetings/activities of: none of these (mentioned)", s11="GEENORG", valueset="mentioned", universe=U11)
V("soc_act_hrs", "soc", "Hours per week spent on associations and organisations", s11="UURWKVER", type="num", universe="Respondents who attend meetings or activities (SIM 2011)")
V("soc_act_ethn", "soc", "With whom the respondent has most contact in these associations", s11="ORGETNI", valueset="ethmix4",
  universe="Respondents who attend meetings or activities (SIM 2011)")
V("soc_cont_fam", "soc", "Frequency of contact with family members in the Netherlands outside the household", s11="CONTFAM", valueset="freq5_cont", universe=U11)
M("soc_cont_fam", S11, "CONTFAM", 9, ".c")
V("soc_cont_frnd", "soc", "Frequency of contact with friends or good acquaintances", s11="CONTVRIE", valueset="freq5_cont", universe=U11)
M("soc_cont_frnd", S11, "CONTVRIE", 9, ".c")
V("soc_cont_nbr", "soc", "Frequency of contact with neighbours", s11="CONTBUUR", valueset="freq5_cont", universe=U11)
M("soc_cont_nbr", S11, "CONTBUUR", 9, ".c")
A("soc_cont_frnd_org", S11, "CONTALL", pairs=[(9, ".c")], u=U11)
A("soc_cont_nbr_org", S11, "CONTBALL", pairs=[(9, ".c")], u=U11)
A("soc_cont_frnd_nl", S11, "CONTAUT", pairs=[(9, ".c")], u=U11)
A("soc_cont_nbr_nl", S11, "CONTBAUT", pairs=[(9, ".c")], u=U11)
V("soc_leis_oth", "soc", "Leisure contact with people from other minority groups (often / sometimes / never)", s11="VRTIJDAN", valueset="freq3", universe=U11M)
V("soc_grp_most", "soc", "Minority group the respondent has most contact with", s11="ANVEEL", valueset="grp_most6",
  universe="Respondents with leisure contact with other minority groups (SIM 2011)")
A("soc_visit_nl", S11, "BEZOEK", u="All respondents (SIM 2011; natives asked about visits from persons with a migration background)")
A("soc_leis_nl", S11, "VRTIJDNL", u="All respondents (SIM 2011; natives asked about persons with a migration background)")
A("soc_cont_bal", S11, "CONTACTV", u="Respondents with leisure contact with native Dutch and with the own group (SIM 2011)")
V("soc_bestfrnd_eth", "soc", "Origin of the best friend", s11="BESTVRIE", valueset="bestfriend4", universe=U11)
V("soc_bestfrnd_edu", "soc", "Highest completed education of the best friend", s11="OPLVRIE", valueset="edu_lvl10", universe="Respondents with a best friend (SIM 2011)")
A("soc_trust_gen", S11, "VERTROUW")
A("soc_sport5", S11, "FQSPORT")
V("soc_sport_comp", "soc", "Took part in competitions, tournaments or matches in the past 12 months", s11="SPORTTYP", valueset="yesno", yn12=True,
  universe="Respondents who practise a sport (SIM 2011)")
V("soc_sport_ethn", "soc", "With whom the respondent has most contact when practising sport", s11="SPORTPUB", valueset="ethmix4",
  universe="Respondents who practise a sport (SIM 2011)")
V("soc_sport_vol", "soc", "Active as a volunteer in a sports club", s11="SPORTVRW", valueset="active3", universe=U11)
_SPORTS = [("11", "athletics"), ("12", "motor sports"), ("13", "badminton"), ("14", "basketball"), ("15", "fitness / aerobics"), ("16", "golf"),
           ("17", "gymnastics"), ("18", "handball"), ("19", "hockey"), ("20", "korfball"), ("21", "horse riding"), ("22", "skating"),
           ("23", "inline skating"), ("24", "softball / baseball"), ("25", "squash"), ("26", "table tennis"), ("27", "tennis"), ("28", "cycling"),
           ("29", "jogging"), ("30", "martial arts"), ("31", "football"), ("32", "volleyball"), ("33", "walking"), ("34", "sailing / rowing / canoeing / surfing"),
           ("35", "swimming"), ("36", "other sport")]
for i, (c, nm) in enumerate(_SPORTS, start=1):
    V(f"soc_spt{i:02d}", "soc", f"Sport practised: {nm} (mentioned)", s11=f"SPORTSRTC{c}", valueset="mentioned", universe="Respondents who practise a sport (SIM 2011)")

# ---- attitudes
for t, src in [("att_chd_frnd_orig", "AFKVRIKI"), ("att_chd_prtnr_orig", "AFKPARKI"), ("att_gr03", "MANGELD"), ("att_gr06", "INKJONGS"),
               ("att_gr01", "MANAANKA"), ("att_gr07", "VRWSTOPW"), ("att_chd06", "INVLOUDF"), ("att_fam04", "THUISHUW"), ("att_fam19", "VERTRFAMA"),
               ("att_fam17", "KIBEZOUD"), ("att_fam10", "KINDZORG"), ("att_mor03", "EUTH"), ("att_hom01", "HOMOLEV"), ("att_hom02", "HOMOHUW"),
               ("att_hom03", "HOMOFAM"), ("att_soc01", "CULTDIV"), ("att_soc03", "ASIELMAKA"), ("att_soc04", "RECHTUIT"), ("att_soc05", "VEELALLO"),
               ("att_soc08", "SLECHTWK"), ("att_nl01", "KANSALLO"), ("att_nl03", "RESPRECH"), ("att_nl04", "NLGASTV"), ("att_nl08", "OPENCULTA"),
               ("att_rel04", "RELIGSCH"), ("att_rel02", "GEENRELD"), ("att_rel05", "RELPOL"), ("att_isl01", "MOSLLEEF"), ("att_isl02", "ISLNEGA"),
               ("att_sat_nl10", "TEVRNED"), ("att_therm01", "TEMPMAR"), ("att_therm02", "TEMPTUR"), ("att_therm03", "TEMPANT"),
               ("att_therm04", "TEMPSUR"), ("att_therm06", "TEMPAUT"), ("att_tens_grow", "SPANGROE"), ("att_fear_ext", "EXTREM"), ("att_fear_vio", "GEWELD")]:
    A(t, S11, src)
U("att_isl01", S11, "Non-Muslim respondents (SIM 2011)"); U("att_isl02", S11, U11MU)
for t in ["att_therm01", "att_therm02", "att_therm03", "att_therm04", "att_therm06"]:
    U(t, S11, "All respondents, own group last (SIM 2011)")
W("att_fam10", "SIM 2011: 'Kinderen moeten voor hun ouders zorgen als deze hulp nodig hebben'; SPVA 2002: 'kinderen zouden voor hun zieke ouders moeten zorgen'.")
W("att_mor03", "SIM 2011: self-determination to end life when terminally ill and in pain; SPVA 2002 wording differs (see table).")
SKIP(S11, "MANAANKB", "split version B of Q803: empty in this deposit (all -5)")
SKIP(S11, "VERTRFAMB", "split version B of Q807: empty in this deposit (all -5)")
SKIP(S11, "ASIELMAKB", "split version B of Q891: empty in this deposit (all -5)")
SKIP(S11, "OPENCULTB", "split version B of Q898: empty in this deposit (all -5)")
V("att_mor04", "att", "A woman should be able to have an abortion if she wishes (agreement)", s11="ABORTUS", valueset="agree5", universe=U11)
V("att_mor05", "att", "Good that the Netherlands no longer has the death penalty (agreement)", s11="DOODSTRA", valueset="agree5", universe=U11)
V("att_soc09", "att", "Migrants should give up their own culture and customs (agreement)", s11="ALLCUL", valueset="agree5", universe=U11)
V("att_int_effort", "att", "Most migrants do enough themselves to integrate", s11="ALLINT", valueset="effort4", universe=U11)
V("att_int_self", "att", "Considers him/herself well integrated", s11="INTEGRA", valueset="integrated3", universe=U11M)
V("att_isl03", "att", "Most Dutch people respect Islamic culture (agreement)", s11="NLRESP", valueset="agree5", universe=U11MU)
V("att_isl04", "att", "Western and Muslim ways of life are incompatible - asked to Muslims (agreement)", s11="WESTLEEF", valueset="agree5", universe=U11MU)
V("att_isl05", "att", "Dutch women have too much freedom (agreement)", s11="NLVROU", valueset="agree5", universe=U11MU)
V("att_isl06", "att", "Dutch children do not listen well enough to their parents (agreement)", s11="NLKIND", valueset="agree5", universe=U11MU)
V("att_isl07", "att", "Most Muslims in the Netherlands respect Dutch culture (agreement)", s11="MOSLRESP", valueset="agree5", universe="Non-Muslim respondents (SIM 2011)")
V("att_isl08", "att", "Muslim women have too little freedom (agreement)", s11="MOSLVRW", valueset="agree5", universe="Non-Muslim respondents (SIM 2011)")
V("att_isl09", "att", "Muslims in the Netherlands raise their children too strictly (agreement)", s11="MOSLKIND", valueset="agree5", universe="Non-Muslim respondents (SIM 2011)")
V("att_rel06", "att", "Religion is a private matter between a believer and God (agreement)", s11="MENSGOD", valueset="agree5", universe=U11)
V("att_rel07", "att", "Religion and politics should have nothing to do with each other (agreement)", s11="RELNIETPOL", valueset="agree5", universe=U11)
V("hlth_happy5", "hlth", "How happy the respondent considers him/herself", s11="GELUK", valueset="happy5", universe=U11)

# ---- politics
A("pol_trust_gov10", S11, "VERTRREG")
V("pol_trust_jus10", "pol", "Trust in the judges in the Netherlands (1 very little - 10 very much)", s11="VERTRJUS", type="num", universe=U11)
A("pol_trust_pol10", S11, "VERTRPOL")
V("pol_interest3", "pol", "Interest in politics", s11="POLINT", valueset="interest3", universe=U11)
V("pol_news_cat", "pol", "Follows news about Dutch politics (days per week, classes)", s11="VOLGNLPO", valueset="media_freq5", universe=U11)
A("pol_vote_int", S11, "STEMINT")
A("pol_party", S11, "STEMWS", pairs=[(1, 3), (2, 7), (3, 1), (4, 4), (5, 6), (6, 5), (7, 2), (8, 14), (9, 8), (10, 11), (11, 92), (12, 15), (13, 17)],
  u="Respondents who would (maybe) vote or were asked hypothetically (SIM 2011)")

# ---- media
V("med_krant_nl_cat", "med", "Reads Dutch newspapers or magazines (days per week, classes)", s11="KRTNED", valueset="media_freq5", universe=U11)
V("med_krant_orig_cat", "med", "Reads origin-group newspapers or magazines (days per week, classes)", s11="KRTEIG", valueset="media_freq5", universe=U11M)
A("med_tv_nl_cat", S11, "TVNED")
A("med_tv_orig_cat", S11, "TVEIG", u=U11M)
V("med_satellite", "med", "Has a satellite dish or receiver at home", s11="SATEL", valueset="yesno", yn12=True, universe=U11)
V("med_pc_internet", "med", "Has a computer with internet access", s11="BEZITPC", valueset="yesno", yn12=True, universe=U11)
V("med_web_cat", "med", "Visits internet sites (days per week, classes)", s11="INTNED", valueset="media_freq5", universe=U11)
A("med_web_orig_cat", S11, "INTEIG", u="Respondents with a migration background who use the internet (SIM 2011)")

# ---- discrimination
A("disc_perc", S11, "DISCALG", u=U11M)
A("disc_exp", S11, "DISCZELF", u=U11M)
V("disc_reason", "disc", "Perceived reason for the discrimination experienced", s11="DISCRED", valueset="disc_reason12",
  universe="Respondents who experienced discrimination (SIM 2011)")
V("disc_yn01", "disc", "Experienced discrimination at work (yes/no)", s11="DISCWERK", valueset="yesno", yn12=True,
  universe="Respondents who experienced discrimination (SIM 2011)")
V("disc_yn02", "disc", "Experienced discrimination when looking for a job (yes/no)", s11="DISCSOLL", valueset="yesno", yn12=True,
  universe="Respondents who experienced discrimination (SIM 2011)")
V("disc_yn03", "disc", "Experienced discrimination at official bodies (yes/no)", s11="DISCOFFI", valueset="yesno", yn12=True,
  universe="Respondents who experienced discrimination (SIM 2011)")
V("disc_yn04", "disc", "Experienced discrimination elsewhere, e.g. in the street or going out (yes/no)", s11="DISCUIT", valueset="yesno", yn12=True,
  universe="Respondents who experienced discrimination (SIM 2011)")
for t in ["disc_yn01", "disc_yn02", "disc_yn03", "disc_yn04"]:
    M(t, S11, find(t)["src_sim2011"], 9, ".c", "niet van toepassing")

# ---- housing and neighbourhood
A("hous_tenure", S11, "KOOPWON", pairs=[(1, 1), (2, 2), (3, 98)])
V("hous_nbhd_reason", "hous", "Main reason for coming to live in this neighbourhood", s11="BUURTRED", valueset="nbhd_reason10", universe=U11)
V("hous_nbhd01", "hous", "Feels at home in this neighbourhood (agreement)", s11="BRTTHUIS", valueset="agree5", universe=U11)
V("hous_nbhd02", "hous", "People in this neighbourhood treat each other pleasantly (agreement)", s11="BRTPRET", valueset="agree5", universe=U11)
V("hous_nbhd03", "hous", "Prefers to live in a neighbourhood with many people from the country of origin (agreement; natives: many native Dutch)", s11="BRTEIGEN", valueset="agree5", universe="All respondents (SIM 2011; natives were asked about a neighbourhood with many 'autochtone Nederlanders')")

# ---- religion
A("rel_any", S11, "GELOOFT", yn12=True)
A("rel_den_det", S11, "RELIGIE", pairs=[(1, 21), (2, 22), (3, 23), (4, 24), (5, 26), (6, 25), (7, 31), (8, 32), (9, 33), (10, 39), (11, 34), (12, 35),
                                        (13, 36), (14, 38), (15, 13), (16, 43), (17, 44), (18, 41), (19, 42), (20, 46), (21, 47), (22, 45), (23, 99)],
  u=U11R)
A("rel_attend", S11, "KERKBEZ", pairs=[(1, 4), (2, 4), (3, 3), (4, 2), (5, 1)], u=U11R)
A("rel_attend5", S11, "KERKBEZ", u=U11R)
V("rel_attend_fa5", "rel", "Father's attendance of religious meetings when the respondent was a child", s11="VADEREL", valueset="attendance5", universe=U11)
for t, src in [("rel_id01", "RELZELF"), ("rel_id02", "RELKWET"), ("rel_id03", "RELDENK"), ("rel_pray", "GEBED"), ("rel_ramadan", "RAMADAN"),
               ("rel_halal", "HALAL"), ("rel_rule", "ISREGEL"), ("rel_veil", "ZHFDDOEK")]:
    A(t, S11, src)
for t in ["rel_id01", "rel_id02", "rel_id03"]: U(t, S11, U11R)
for t in ["rel_pray", "rel_ramadan", "rel_halal", "rel_rule"]: U(t, S11, U11MU)
U("rel_veil", S11, "Muslim women (SIM 2011)")
M("rel_veil", S11, "ZHFDDOEK", 1, 1); M("rel_veil", S11, "ZHFDDOEK", 2, 0)
V("rel_koran_chd", "rel", "Went to Koran lessons as a child", s11="KORANLES", valueset="yes_no_sometimes", universe=U11MU)
V("rel_veil_should", "rel", "Muslim women should wear a headscarf when going out (agreement)", s11="HOOFDBUI", valueset="agree5", universe=U11MU)

# ---- health
A("hlth_self", S11, "GEZONDH", u=U11)
A("hlth_gp2m", S11, "HUISARTS", u=U11)
A("hlth_height_cm", S11, "LENGTE", u=U11)
A("hlth_weight_kg", S11, "GEWICHT", u=U11)
V("hlth_pa_winter", "hlth", "Days per week with at least 30 minutes of physical activity in winter", s11="SPORTWIN", type="num", universe=U11)
V("hlth_pa_summer", "hlth", "Days per week with at least 30 minutes of physical activity in summer", s11="SPORTZOM", type="num", universe=U11)

# ---- parenting module (one co-resident child selected)
V("fam_selchd_num", "fam", "Household member number of the child selected for the parenting module (source administration)", s11="SELECTKIND1", type="num",
  universe=U11K, include=0)
V("fam_selchd_sex", "fam", "Sex of the selected child", s11="SELECTKIND1_GESLACHT", valueset="sex", universe=U11K)
V("fam_selchd_age", "fam", "Age of the selected child", s11="SELECTKIND1_LEEFTIJD", type="num", universe=U11K)
V("fam_selchd_edu", "fam", "Current (or last completed) education of the selected child", s11="OPLKIND1", valueset="edu_chd8", universe="Selected children aged 4-17 (SIM 2011)")
V("fam_par01", "fam", "Parenting: once I have said 'no' I stick to it", s11="OPVGEDR1", valueset="freq5_par", universe=U11K)
V("fam_par02", "fam", "Parenting: I give my child a slap when it does something that is not allowed", s11="OPVGEDR2", valueset="freq5_par", universe=U11K)
V("fam_par03", "fam", "Parenting: I make sure my child lives by fixed rules", s11="OPVGEDR3", valueset="freq5_par", universe=U11K)
V("fam_par04", "fam", "Parenting: when I punish my child I usually explain why", s11="OPVGEDR4", valueset="freq5_par", universe=U11K)
M("fam_par04", S11, "OPVGEDR4", 6, ".c")
V("fam_par05", "fam", "Parenting: I ask my child where it has been when it comes home", s11="OPVGEDR5", valueset="freq5_par", universe="Selected children aged 10-17 (SIM 2011)")
V("fam_chdbeh01", "fam", "Child (past 6 months): is liked by most other children", s11="KINDGED1", valueset="true3", universe=U11K)
V("fam_chdbeh02", "fam", "Child (past 6 months): often complains of headaches, stomach aches or nausea", s11="KINDGED2", valueset="true3", universe=U11K)
V("fam_chdbeh03", "fam", "Child (past 6 months): often fights with other children", s11="KINDGED3", valueset="true3", universe="Selected children aged 4-17 (SIM 2011)")
V("fam_chdbeh04", "fam", "Child (past 6 months): often unhappy, sad or tearful", s11="KINDGED4", valueset="true3", universe=U11K)
V("fam_chdbeh05", "fam", "Child (past 6 months): has the wrong friends", s11="KINDGED5", valueset="true3", universe="Selected children aged 10-17 (SIM 2011)")
V("fam_par_att01", "fam", "I often find parenting very difficult (agreement)", s11="OPVBEL1", valueset="agree5", universe=U11K)
V("fam_par_att02", "fam", "My child does not listen well to me (agreement)", s11="OPVBEL2", valueset="agree5", universe=U11K)
V("fam_chd_rel5", "fam", "Quality of the relationship with the selected child", s11="RELAKIND", valueset="quality5", universe=U11K)
M("fam_chd_rel5", S11, "RELAKIND", 6, ".c", "no relationship with the child")
V("fam_val_rank01", "fam", "Rank (1 most - 5 least important) of: having an opinion of one's own", s11="OPVDOEL1", type="num", universe=U11K)
V("fam_val_rank02", "fam", "Rank (1 most - 5 least important) of: good school results", s11="OPVDOEL2", type="num", universe=U11K)
V("fam_val_rank03", "fam", "Rank (1 most - 5 least important) of: being a religious person", s11="OPVDOEL3", type="num", universe=U11K)
V("fam_val_rank04", "fam", "Rank (1 most - 5 least important) of: behaving properly", s11="OPVDOEL4", type="num", universe=U11K)
V("fam_val_rank05", "fam", "Rank (1 most - 5 least important) of: being considerate of others", s11="OPVDOEL5", type="num", universe=U11K)
V("fam_chd_higher_ed", "fam", "Importance that the child(ren) go to hbo or university", s11="BELHOGER", valueset="important5", universe=U11K)
V("fam_par_adv01", "fam", "Parenting advice in the past year from: parents or parents-in-law", s11="OPVOND1", valueset="freq3_adv", universe=U11K)
M("fam_par_adv01", S11, "OPVOND1", 7, ".c", "deceased / no contact")
V("fam_par_adv02", "fam", "Parenting advice in the past year from: neighbours, friends or acquaintances", s11="OPVOND2", valueset="freq3_adv", universe=U11K)
V("fam_par_adv03", "fam", "Parenting advice in the past year from: child care, playgroup or school", s11="OPVOND3", valueset="freq3_adv", universe=U11K)
M("fam_par_adv03", S11, "OPVOND3", 4, ".c", "child not in child care or school")
V("fam_par_adv04", "fam", "Parenting advice in the past year from: the youth health centre (CJG / consultatiebureau)", s11="OPVOND4", valueset="freq3_adv", universe=U11K)
V("fam_par_adv05", "fam", "Parenting advice in the past year from: social work or youth care", s11="OPVOND5", valueset="freq3_adv", universe=U11K)

# ---- education (SCP constructed)
A("edu_cntry", S11, "oplblnl")
A("edu_part", S11, "ondpart")
A("edu_dipl_all_det", S11, "maxdsch")
A("edu_dipl_all_cat5", S11, "maxdsch", pairs=[(0, 0), (1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (7, 4)])
A("edu_dipl_all_lvl3", S11, "maxdsch", pairs=[(0, 0), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
A("edu_dipl_hi_cat", S11, "maxdip1", u="Respondents not enrolled in education (SIM 2011)")
A("edu_dipl_all_cat", S11, "maxdsch1")
A("edu_dipl_cur_lvl3", S11, "maxdipnu", pairs=[(0, 0), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
V("edu_dipl_cur_det", "edu", "Highest diploma incl. current education of enrolled persons, 8 levels (SCP: maxdipnu)", s11="maxdipnu", valueset="edu8", universe=U11)
V("edu_dipl_cur_cat", "edu", "Highest diploma incl. current education of enrolled persons, 4 classes (SCP: maxdipn1)", s11="maxdipn1", valueset="edu4", universe=U11)
A("edu_abr_att_lvl3", S11, "MAXOPLBL", pairs=[(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3), (8, ".d")],
  u="Respondents who attended education abroad (SIM 2011)")
V("edu_abr_att_det", "edu", "Highest education attended abroad, 8 levels (0 = never went to school; LAS 2004/05, SIM 2011)", s11="MAXOPLBL", valueset="edu8",
  universe="Respondents who attended education abroad (SIM 2011)")
M("edu_abr_att_det", S11, "MAXOPLBL", 8, ".d", "anders")

# ---- neighbourhood composition (registry counts attached by SCP)
for i, (src, nm) in enumerate([("aantaut", "native Dutch"), ("aantmar", "Moroccan"), ("aantant", "Antillean/Aruban"), ("aantonw", "other non-western"),
                               ("aantow", "other western"), ("aantsur", "Surinamese"), ("aanttur", "Turkish")], start=1):
    V(f"geo_nbhd_n{i:02d}", "geo", f"Number of {nm} residents in the respondent's neighbourhood (registry count attached by SCP, SIM 2011)", s11=src, type="num",
      universe=U11, notes="Source documentation gives no definition of the area; use with care.")


# ====================================================================================================== SIM 2006
# Veldkamp CAPI survey (SCP), 5,250 respondents: Turks, Moroccans, Surinamese, Antilleans/Arubans and a native Dutch
# reference sample; no person identifier in the deposit (id = row number, impd_rownum); system-missing = routed past
# the question (surveys.csv sysmis_tag = c).  Several items were fielded as two variables - one for the migrant groups
# and one for the native sample (…_N) or two questionnaire versions (BURT_OUD/BURT_NEW) - and are fed as 'A|B'.
U06 = "All respondents (SIM 2006)"
U06M = "Respondents with a migration background (SIM 2006)"
U06N = "Native Dutch respondents (SIM 2006)"
U06G1 = "First-generation respondents (SIM 2006)"
U06P = "Respondents with a partner (SIM 2006)"
U06PC = "Respondents living with a partner (SIM 2006)"
U06C = "Respondents with children (SIM 2006)"
U06W = "Employed respondents (SIM 2006)"
U06E = "Employees (SIM 2006)"
U06NW = "Respondents without paid work (SIM 2006)"
U06R = "Religious respondents (SIM 2006)"
U06MU = "Muslim respondents (SIM 2006)"
U06TM = "Turkish and Moroccan respondents (SIM 2006)"
U06SAN = "Surinamese, Antillean/Aruban and native Dutch respondents (SIM 2006)"
U06K = "Respondents with a co-resident child of school age; one child chosen at random by the interview program (SIM 2006)"
REV5 = [(1, 5), (2, 4), (3, 3), (4, 2), (5, 1)]            # 1 never ... 5 every day  ->  freq5_cont (1 every day ... 5 never)

# ---- survey administration, weights, geography
A("svy_wgt", S06, "WEEGTOT")
A("svy_wgt_grp", S06, "WEEGHERK")
A("svy_wgt_raise", S06, "OPHTOT")
A("svy_incentive5", S06, "TIENEURO")
V("svy_incentive_pre", "svy", "Received a booklet of postage stamps with the introduction letter (SIM 2006 incentive experiment)", s06="V9907",
  valueset="yesno", universe="Respondents in the incentive experiment (SIM 2006)",
  notes="Part of the sample received a booklet of five stamps (2 euro) in advance; all respondents received a 10-euro gift voucher afterwards (fieldwork report 5.9).")
M("svy_incentive_pre", S06, "V9907", 1, 1); M("svy_incentive_pre", S06, "V9907", 2, 0)
A("geo_city4", S06, "GRPLS", pairs=[(3, 1), (4, 2), (5, 3), (6, 4), (1, 5), (2, 5)])
V("geo_size6", "geo", "Size class of the municipality of residence (SIM 2006: small / medium-sized / the four large cities)", s06="GRPLS", valueset="city_size6",
  universe=U06, notes="Sample stratification variable; the municipality itself is not in the deposit.")

# ---- demography and household
A("dem_sex", S06, "GESLACHT")
A("dem_age", S06, "LEEFTIJD")
A("dem_mar", S06, "BURGST")
V("dem_hhpos4", "dem", "Position in the household: head, partner of the head, co-resident child, other (SIM 2006)", s06="GEZINPOS", valueset="hhpos4", universe=U06,
  notes="SPVA/SPVN record the position in the family (dem_posfam), SIM 2011/2015 the living situation (dem_livsit); the SIM 2006 item is not reducible to either.")
A("hh_size", S06, "GEZOMV")
A("dem_prtnr_st", S06, "LATPART|SAMPART", pairs={"LATPART": [(1, 4), (2, 0)], "SAMPART": [(1, 1), (2, 3), (3, 2), (4, 0)]}, u=U06,
  note="LATPART (asked to the unmarried/non-cohabiting incl. one-person households) decides between 'partner elsewhere' and 'single'; SAMPART for the others")
A("dem_prtnr_lat", S06, "LATPART", pairs=[(1, 1), (2, 2)], u="Respondents not married or cohabiting, including one-person households (SIM 2006)")
A("dem_prtnr_res", S06, "PARTNL", pairs=[(1, 1), (2, 2), (3, 6)], u="Respondents with a partner living elsewhere (SIM 2006)")
A("dem_mar_yr", S06, "HUWJAAR", u="Respondents with a partner: year of marriage / registered partnership / moving in together (SIM 2006)")
A("dem_prtnr_sex", S06, "GESLPART", u=U06P)
A("dem_prtnr_age", S06, "LFTPART", u=U06P)
A("dem_prtnr_brthcntry", S06, "GEBLPART", pairs=[(1, 5022), (2, 6043), (3, 7011), (4, 5007), (5, 6030), (6, 9999)], u=U06P)
V("dem_prtnr_eth", "dem", "Origin group of the partner (SIM 2006: based on the respondent's answers)", s06="ETNPART", valueset="ethgroup", universe=U06P,
  notes="SIM 2006 (ETNPART): constructed by SCP from the partner's country of birth and the countries of birth of the partner's parents, as reported by the respondent (CBS origin definition: a partner born in the Netherlands takes a parent's country; a partner born abroad whose parents were both born in the Netherlands is Dutch). The parents' countries are not in the public deposit, so the construction cannot be retraced from it; in the public file 5 partners of Dutch origin (90) were born abroad (1 Antilles/Aruba, 4 other country). Checked against the CBS microdata by the restricted component, 5 Nov 2026.")
MM("dem_prtnr_eth", S06, "ETNPART", [(1, 2), (2, 1), (3, 4), (4, 3), (5, 90), (6, 95)])
V("dem_prtnr_gen", "dem", "Migrant generation of the partner (SIM 2006: based on the respondent's answers)", s06="GENPART", valueset="generation_prtnr",
  universe="Respondents with a migration background who have a partner, whatever the partner's origin (SIM 2006); partners of native Dutch respondents are not classed (.c)",
  notes="LAS 2004/05, SIM 2006, SING 2009 (GENPART, SCP construction): 1 = partner born abroad, 2 = partner born in the Netherlands, native Dutch partners included - the parents' clause of the generation definition is not applied (SIM 2006: all 629 partners coded 2 are born in the Netherlands, 418 of them of Dutch origin; SING 2009: code 2 = 1,324 against dem_prtnr_eth 90 = 1,192). Whose partners are classed differs: in LAS 2004/05 and SIM 2006 only the partners of respondents with a migration background (partners of native Dutch respondents are .c, whatever their origin); in SING 2009 the partners of native respondents too, by the same rule (of 949 native respondents, 42 partners born abroad = 1, 655 born in the Netherlands = 2). SPVA 2002 / SPVN 2003: the partner's own dem_gen through the roster link, where native members of migrant households also carry 2 (ISEO rule). The restricted component gives SIM 2006 the CBS definition (native partners 0). Established by the restricted component, 5 Nov 2026; scope corrected after the follow-up audit of v0.4.8.")
A("dem_nchd", S06, "AANTKIND", u=U06C)
A("dem_nchd_home", S06, "INWKIND", u="Respondents with children living in multi-person households (SIM 2006)")
A("dem_chd_res", S06, "KINDNL", u="Respondents with children not (all) living at home (SIM 2006)")
A("hh_noth", S06, "AANTAND", u=U06)
A("dem_eth", S06, "ETNGRP", pairs=[(5, 90)])
A("dem_gen", S06, "GENERAT|ETNGRP", pairs={"ETNGRP": [(5, 0), (1, ".c"), (2, ".c"), (3, ".c"), (4, ".c")]},
  note="GENERAT is defined for the four migrant groups only; the native sample gets 0 from ETNGRP")
A("dem_prtnr_emp", S06, "PARTWERK", yn12=True, u=U06PC)
A("dem_prtnr_hrs", S06, "PARTUREN", u="Respondents whose co-resident partner has paid work (SIM 2006)")
A("dem_prtnr_act", S06, "PARTHFDA", pairs=[(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 98)],
  u="Respondents whose co-resident partner has no paid work (SIM 2006; partners with paid work: see dem_prtnr_emp)")

# ---- migration, nationality, return, transnational ties
A("mig_reason", S06, "REDMIGR", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 14), (8, 8), (9, 13), (10, 17), (11, 10)], u=U06G1)
A("mig_yr_arr", S06, "MIGRJAAR", u=U06G1)
A("mig_reason_prtnr", S06, "REDMI_P", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 14), (8, 8), (9, 10)],
  u="Respondents whose partner was born abroad (SIM 2006)")
A("mig_yr_arr_prtnr", S06, "MIGRJA_P", u="Respondents whose partner was born abroad (SIM 2006)")
A("nat_cit", S06, "NATIONAL", pairs=[(1, 3), (2, 1), (3, 2), (4, 4)], u="Turkish, Moroccan and Surinamese respondents (SIM 2006; not asked to Antilleans/Arubans and natives)")
A("nat_nl", S06, "NATIONAL", pairs=[(1, 0), (2, 1), (3, 1), (4, ".d")], u="Turkish, Moroccan and Surinamese respondents (SIM 2006)")
A("nat_orig", S06, "NATIONAL", pairs=[(1, 1), (2, 0), (3, 1), (4, ".d")], u="Turkish, Moroccan and Surinamese respondents (SIM 2006)")
A("nat_nl_always", S06, "NLATIJD", yn12=True, u="Turkish, Moroccan and Surinamese respondents with Dutch nationality (SIM 2006)")
A("nat_nl_reason", S06, "NLKIES", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 9)], u="Respondents who acquired Dutch nationality (SIM 2006)")
A("ret_wish", S06, "WILTERUG", pairs=[(1, 1), (2, 3), (-3, 2)], u=U06M)
A("ret_poss", S06, "MOGTERUG", pairs=[(1, 1), (2, 3)], u="Respondents who want to return (SIM 2006)")
A("ret_noreason", S06, "NIETTRUG", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 13), (10, 12), (11, 10), (13, 9), (14, 11)],
  u="Respondents who do not want or cannot return (SIM 2006)")
A("ret_reason", S06, "WELTRUG", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 13), (12, 10), (13, 11)],
  u="Respondents who want to return (SIM 2006)")
A("trn_cont_fam3", S06, "CONTHERK", u=U06M)
A("trn_visit_yearly", S06, "BEZOEHER", u=U06M)
A("trn_visit12m", S06, "J2005HER", yn12=True, u=U06M)
W("trn_visit12m", "SIM 2006 asks about the calendar year 2005 (interviews autumn 2006 - January 2007); SIM 2011/2015 about 2010 / the past 12 months.")
A("trn_visit_dur", S06, "J2005LNG", u="Respondents who visited the country of origin in 2005 (SIM 2006)")
A("trn_homesick", S06, "HEIMWEE", u=U06M)
A("trn_house", S06, "HUISBUI", yn12=True, u=U06M)
A("trn_remit", S06, "V680", yn12=True, u="Respondents who are head or partner of the household (SIM 2006)")
W("trn_remit", "SIM 2006: 'in 2005 geld of goederen gestuurd naar het buitenland' (any country, calendar year 2005); SIM 2011/2015: to the country of origin in the past 12 months.")
for t, src in [("trn_remit02", "V682_1"), ("trn_remit01", "V682_2"), ("trn_remit03", "V682_3"), ("trn_remit04", "V682_4"), ("trn_remit06", "V682_5")]:
    A(t, S06, src, pairs=[(1, 1), (2, 0)], u="Households that sent money or goods abroad in 2005 (SIM 2006)")
W("trn_remit01", "SIM 2006: partner or ex-partner; SIM 2011: partner / spouse / fiance(e).")
W("trn_remit04", "SIM 2006: other family members or friends; SIM 2011: other family members (friends under 'others').")
V("trn_remit_amt", "trn", "Total value of money and goods sent abroad in 2005 (euro)", s06="V685", type="num", universe="Households that sent money or goods abroad in 2005 (SIM 2006)")
V("trn_remit_amt_15", "trn", "Total value of money and goods sent abroad in 2005, constant 2015 euro", type="num", universe="Households that sent money or goods abroad in 2005 (SIM 2006)", derive="cpi2015:trn_remit_amt@2005")
V("trn_remit_band", "trn", "Total value sent abroad in 2005, band (asked when no amount was given)", s06="V690", valueset="amount_band9",
  universe="Households that sent money or goods abroad in 2005 and gave no amount (SIM 2006)")
V("trn_dowry_paid", "trn", "Household contributed to a dowry (bruidsschat) in 2005", s06="V695", valueset="yesno", yn12=True,
  universe="Households that sent money or goods abroad in 2005 (SIM 2006)")
V("trn_dowry_paid_amt", "trn", "Value of the dowry contribution in 2005 (euro)", s06="V715", type="num", universe="Households that contributed to a dowry in 2005 (SIM 2006)")
V("trn_dowry_paid_amt_15", "trn", "Value of the dowry contribution in 2005, constant 2015 euro", type="num", universe="Households that contributed to a dowry in 2005 (SIM 2006)", derive="cpi2015:trn_dowry_paid_amt@2005")
V("trn_dowry_paid_band", "trn", "Value of the dowry contribution in 2005, band", s06="V720", valueset="amount_band9",
  universe="Households that contributed to a dowry in 2005 and gave no amount (SIM 2006)")
V("trn_recv", "trn", "Household received money or goods from abroad in 2005", s06="V725", valueset="yesno", yn12=True,
  universe="Respondents who are head or partner of the household (SIM 2006)")
V("trn_recv01", "trn", "Money or goods received from: partner or ex-partner (yes/no)", s06="V731_1", valueset="yesno", yn12=True, universe="Households that received money or goods from abroad in 2005 (SIM 2006)")
V("trn_recv02", "trn", "Money or goods received from: parents (yes/no)", s06="V731_2", valueset="yesno", yn12=True, universe="Households that received money or goods from abroad in 2005 (SIM 2006)")
V("trn_recv03", "trn", "Money or goods received from: other family members or friends (yes/no)", s06="V731_3", valueset="yesno", yn12=True, universe="Households that received money or goods from abroad in 2005 (SIM 2006)")
V("trn_recv04", "trn", "Money or goods received from: a study grant or other contribution of an organisation (yes/no)", s06="V731_4", valueset="yesno", yn12=True, universe="Households that received money or goods from abroad in 2005 (SIM 2006)")
V("trn_recv_amt", "trn", "Total value of money and goods received from abroad in 2005 (euro)", s06="V735", type="num", universe="Households that received money or goods from abroad in 2005 (SIM 2006)")
V("trn_recv_amt_15", "trn", "Total value of money and goods received from abroad in 2005, constant 2015 euro", type="num", universe="Households that received money or goods from abroad in 2005 (SIM 2006)", derive="cpi2015:trn_recv_amt@2005")
V("trn_recv_band", "trn", "Total value received from abroad in 2005, band", s06="V740", valueset="amount_band9", universe="Households that received money or goods from abroad in 2005 and gave no amount (SIM 2006)")
V("trn_inherit", "trn", "Received a dowry, an inheritance or part of one from abroad in 2005", s06="V745", valueset="yesno", yn12=True, universe="Households that received money or goods from abroad in 2005 (SIM 2006)")
V("trn_inherit_amt", "trn", "Value of the dowry / inheritance received in 2005 (euro)", s06="V750", type="num", universe="Households that received a dowry or inheritance from abroad in 2005 (SIM 2006)")
V("trn_inherit_amt_15", "trn", "Value of the dowry / inheritance received in 2005, constant 2015 euro", type="num", universe="Households that received a dowry or inheritance from abroad in 2005 (SIM 2006)", derive="cpi2015:trn_inherit_amt@2005")
V("trn_inherit_band", "trn", "Value of the dowry / inheritance received in 2005, band", s06="V755", valueset="amount_band9",
  universe="Households that received a dowry or inheritance from abroad in 2005 and gave no amount (SIM 2006)", notes="No respondent reached this question in the deposited data.")

# ---- education
A("edu_abr_yrs", S06, "ONDJRBL", u="Respondents who went to school outside the Netherlands (SIM 2006)")
A("edu_enr", S06, "SCHOOLG", yn12=True)
V("edu_prtnr_det10", "edu", "Highest completed education of the partner, 10 levels (SIM 2006)", s06="MAXDIPP", valueset="edu_lvl10", universe=U06P)
A("edu_prtnr_lvl3", S06, "MAXDIPP", pairs=[(1, 0), (2, 0), (3, 1), (4, 1), (5, 1), (6, 2), (7, 2), (8, 3), (9, 3), (10, ".d")], u=U06P)
V("edu_fa_det10", "edu", "Highest school diploma of the father, 10 levels (SIM 2006)", s06="MAXDIPPA", valueset="edu_lvl10", universe=U06)
V("edu_ma_det10", "edu", "Highest school diploma of the mother, 10 levels (SIM 2006)", s06="MAXDIPMA", valueset="edu_lvl10", universe=U06)
_P10_3 = [(1, 0), (2, 0), (3, 1), (4, 1), (5, 1), (6, 2), (7, 2), (8, 3), (9, 3), (10, ".d")]
_P10_4 = [(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3), (8, 4), (9, 4), (10, ".d")]
A("edu_fa_lvl3", S06, "MAXDIPPA", pairs=_P10_3); A("edu_ma_lvl3", S06, "MAXDIPMA", pairs=_P10_3)
A("edu_fa_cat", S06, "MAXDIPPA", pairs=_P10_4); A("edu_ma_cat", S06, "MAXDIPMA", pairs=_P10_4)
A("edu_part", S06, "ONDPART")
A("edu_dipl_hi_cat", S06, "MAXDIP1", u="Respondents not enrolled in education (SIM 2006)")
A("edu_dipl_cur_cat", S06, "MAXDIPN1")

# ---- labour market
A("lab_emptype", S06, "ZELFST", pairs=[(1, 1), (2, 2)], u=U06W)
A("lab_tenure", S06, "ERVBEDR", u=U06E)
W("lab_tenure", "SIM 2006: years with decimals (months / 12); SIM 2011: years and months in two variables (lab_tenure, lab_tenure_mo).")
A("lab_sup", S06, "LEIDING", yn12=True, u=U06E)
A("lab_nsup", S06, "NLEIDING", u="Employees who supervise others (SIM 2006)")
A("lab_match", S06, "ONDERBEN", u=U06E)
A("lab_train", S06, "CURSUSBD", pairs=[(1, 1), (2, 1), (3, 0)], u=U06E)
A("lab_prom_chance", S06, "KANSPRO1", yn12=True, u=U06E)
A("lab_prom_bar", S06, "BELPROM", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 9), (8, 10)], u="Employees who see no chance of promotion (SIM 2006)")
A("lab_perm", S06, "VASTWERK", u=U06E)
V("lab_sat01", "lab", "Work satisfaction: I have interesting work (agreement)", s06="INTWERK", valueset="agree5", universe=U06E)
V("lab_sat02", "lab", "Work satisfaction: the atmosphere at my work is pleasant (agreement)", s06="SFEERWER", valueset="agree5", universe=U06E)
V("lab_sat03", "lab", "Work satisfaction: I have good promotion opportunities at work (agreement)", s06="KANSPRO2", valueset="agree5", universe=U06E)
V("lab_sat04", "lab", "Work satisfaction: I can decide myself how I do my work (agreement)", s06="BESLISWE", valueset="agree5", universe=U06E)
V("lab_sat05", "lab", "Work satisfaction: I am paid too little for the work I do (agreement)", s06="GELDWERK", valueset="agree5", universe=U06E)
A("lab_found", S06, "HOEBAAN", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 12), (10, 9), (11, 10)], u=U06E)
W("lab_found", "SIM 2006 adds 'wervings- en selectiebureau' (mapped to 12, placement agency) and 'werd gevraagd' (9).")
A("lab_se_type", S06, "ZELFFREE", u="Self-employed respondents (SIM 2006)")
A("lab_se_nemp", S06, "NPERS", u="Self-employed respondents (SIM 2006)")
A("lab_frst_yr", S06, "JRWERKNL", u=U06W)
A("lab_exp", S06, "ARBERV", u=U06W)
W("lab_exp", "SIM 2006: years with decimals; SIM 2011/2015: years and months in two variables.")
A("lab_unemp_ever", S06, "WERKL", yn12=True, u=U06W)
A("lab_nunemp", S06, "NWERKL", u="Employed respondents who have been unemployed (SIM 2006)")
A("lab_everwork", S06, "WERKNL", yn12=True, u=U06NW)
V("lab_frst_yr_prev", "lab", "Year of first paid work in the Netherlands (persons not working now)", s06="JRWERK_W", type="year",
  universe="Respondents without paid work who ever worked (SIM 2006)", notes="Employed respondents: lab_frst_yr.")
A("lab_exp_prev", S06, "ARBERV_W", u="Respondents without paid work who ever worked (SIM 2006)")
A("lab_nowork_yrs", S06, "NWRKDUUR", u="Respondents without paid work who ever worked (SIM 2006)")
A("lab_left_how", S06, "ONTSLAG", u="Respondents without paid work who ever worked (SIM 2006)")
A("lab_dism_reason", S06, "REDONTSL", pairs=[(10, 11), (11, 10)], u="Respondents who left their last job (SIM 2006; incl. resignations)")
A("lab_act", S06, "HFDACT", pairs=[(5, 5), (6, 5), (7, 6)], u=U06NW)
V("lab_eq_chance", "lab", "Thinks he/she has the same chance of a job as a native Dutch person", s06="KANSWERK", valueset="yesno", yn12=True, universe=U06M)
V("lab_eq_chance_no", "lab", "Main reason for having less chance of a job than a native Dutch person", s06="KANSNEE", valueset="eq_chance_no8",
  universe="Respondents with a migration background who think they have less chance of a job (SIM 2006)")
V("lab_job_chance5", "lab", "Chance of finding a suitable job within three months", s06="KANSVIND", valueset="chance5",
  universe="Job seekers (SIM 2006)")
V("lab_accept01", "lab", "Would accept: a temporary job for six months", s06="WILTIJD", valueset="accept4", universe=U06)
V("lab_accept02", "lab", "Would accept: work with two hours of daily travel", s06="WILREIS", valueset="accept4", universe=U06)
V("lab_accept03", "lab", "Would accept: work below own level of education", s06="WILOPL", valueset="accept4", universe=U06)
V("lab_accept04", "lab", "Would accept: heavy and dirty work", s06="WILVUIL", valueset="accept4", universe=U06)
V("lab_accept05", "lab", "Would accept: work with a lot of stress", s06="WILSTRES", valueset="accept4", universe=U06)
V("lab_accept06", "lab", "Would accept: nice work that requires moving to another town", s06="WILVERHU", valueset="accept4", universe=U06)
V("lab_accept07", "lab", "Would accept: nice work without an increase in income", s06="WILINK", valueset="accept4", universe=U06)
A("lab_lf3", S06, "BB_NED")
A("lab_lf", S06, "BB_NED", pairs=[(1, 1), (2, 1), (3, 0)])
A("lab_hrs_cat5", S06, "URENCAT", pairs=[(-1, ".c")], note="-1 'geen werk'")
A("lab_coll_bal", S06, "CONTACTW", u=U06E)

# ---- income
A("inc_ben", S06, "UITKEER")
A("inc_ben_yrs", S06, "UITKDUUR", u="Benefit recipients (SIM 2006; longest-running benefit)")
V("inc_ease5", "inc", "How easily the household makes ends meet on its total income", s06="RONDKOM", valueset="ease5",
  universe="Respondents who are head or partner of the household (SIM 2006)")
A("inc_change5", S06, "FINSUBJ", u="Respondents who are head or partner of the household (SIM 2006)")
V("inc_tot_band", "inc", "Net monthly personal income in 16 bands (SIM 2006: SCP construct inkcat)", s06="INKCAT", valueset="inc_band16", universe=U06,
  notes="Built by SCP from the reported amounts (labour income, benefits) and the band cards; the amounts themselves are not deposited. A third source is likely: 326 respondents without paid work (ZELFST blank) and without a benefit (UITKEER 0) have a band - housewives 224, unemployed 39, students 10, pensioners 27 -, presumably from the household-income questions (gezink1/gezink2, Q660-661). INKCAT 99 merges 'not applicable' with 'weet niet / wil niet zeggen', so .d also covers respondents without any income source (restricted component, 5 Nov 2026). SPVA/SPVN: inc_tot_cat.")
MM("inc_tot_band", S06, "INKCAT", [(f"'{i}'", i) for i in range(1, 17)] + [("'99'", ".d")])

# ---- language and civic integration
A("lang_nl_prtnr", S06, "TAALPART", u="Respondents with a migration background living with a partner (SIM 2006)")
A("lang_nl_chd", S06, "TAALKIND", u="Respondents with a migration background who have children (SIM 2006)")
A("lang_prob_spk", S06, "TAALGESP", pairs=[(1, 1), (2, 2), (3, 3)], u=U06M, note="'vaak moeite / spreekt geen Nederlands' is one category in SIM 2006")
W("lang_prob_spk", "SIM 2006 merges 'speaks no Dutch' with 'often' (code 1); SIM 2011/2015 have it as a separate category (4).")
V("lang_prob_spk_type", "lang", "Problems in Dutch conversation: mainly speaking, mainly understanding, or both", s06="TAALSPBE", valueset="prob_type3",
  universe="Respondents with (sometimes) problems in Dutch conversation (SIM 2006)")
A("lang_prob_read", S06, "TAALKRAN", u=U06M)
A("lang_prob_write", S06, "TAALPEN", u=U06M)
A("int_nlcrs", S06, "TAALCURS", yn12=True, u=U06G1)
W("int_nlcrs", "SIM 2006: 'wel eens een cursus gedaan om Nederlands te leren' (first generation); SIM 2011/2015 ask the same with more answer categories (int_nlcrs_det).")
V("int_nlcrs_dipl", "int", "Obtained a diploma at the end of the Dutch language course", s06="TAALDIPL", valueset="yesno", yn12=True,
  universe="Respondents who followed a Dutch language course (SIM 2006)")
A("lang_orig_follow", S06, "ETNIGESP", pairs=[(1, 1), (2, 3)], u=U06M)
W("lang_orig_follow", "SIM 2006: yes/no; SIM 2011/2015: yes / a little / no.")
A("lang_other", S06, "ETNITAAL", pairs=[(1, 21), (2, 22), (3, 11), (4, 12), (5, 13), (6, 31), (7, 32), (8, 34), (9, 33), (10, 35), (11, 36), (12, 96)],
  u="Respondents who can follow a conversation in a language of the country of origin (SIM 2006)")
A("lang_orig_prob_und", S06, "ETNIVERS", u="Respondents who can follow a conversation in a language of the country of origin (SIM 2006)")
A("lang_orig_prob", S06, "ETNISPRE", u="Respondents who can follow a conversation in a language of the country of origin (SIM 2006)")
A("lang_orig_read", S06, "ETNILEES", pairs=[(1, 1), (2, 2), (3, 3)], u="Respondents who can follow a conversation in a language of the country of origin and were asked about reading it (SIM 2006)")
A("lang_orig_write", S06, "ETNIPEN", pairs=[(1, 1), (2, 2), (3, 3)], u="Respondents who can follow a conversation in a language of the country of origin and were asked about writing it (SIM 2006)")
W("lang_orig_read", "SIM 2006 has no 'cannot read the language' category (SIM 2011: code 4).")
W("lang_orig_write", "SIM 2006 has no 'cannot write the language' category (SIM 2011: code 4).")

# ---- identification
A("iden_scale", S06, "ZELFIDEN", u=U06M)
A("iden_home_nl", S06, "THUISNL")
SKIP(S06, "THUISNIE", "open answer (why not at home in NL) removed from the deposit: empty")
SKIP(S06, "THUISWEL", "open answer (why at home in NL) removed from the deposit: empty")
A("iden_allochtoon", S06, "ZELFALL", yn12=True, u=U06M)

# ---- social contacts and participation
for t, src in [("soc_act01", "SPORTVER"), ("soc_act02", "VRIJVER"), ("soc_act03", "WIJKVER"), ("soc_act04", "VAKBOND"), ("soc_act05", "ALLVER"),
               ("soc_act06", "POLPART"), ("soc_act07", "GODORG"), ("soc_act08", "NATUURV"), ("soc_act09", "ANDORG"), ("soc_act10", "GEENORG")]:
    A(t, S06, src, u=U06)
V("soc_act11", "soc", "Attends meetings/activities of: library (mentioned)", s06="BIED", valueset="mentioned", universe=U06)
for t, src in [("soc_mem01", "SPORTLID"), ("soc_mem04", "VRIJLID"), ("soc_mem09", "BONDLID"), ("soc_mem10", "POLLID"), ("soc_mem11", "GODLID"), ("soc_mem07", "NATUURLI")]:
    A(t, S06, src, u=U06)
W("soc_mem04", "SIM 2006: 'vrijetijdsorganisatie (hobby, muziek, toneel, dans)'; SPVA 2002: 'hobbyvereniging'.")
V("soc_mem12", "soc", "Member of a neighbourhood or tenants' association", s06="WIJKLID", valueset="mentioned", universe=U06)
V("soc_mem13", "soc", "Member of an organisation of or for migrants", s06="ALLLID", valueset="mentioned", universe=U06)
V("soc_mem14", "soc", "Member of a library", s06="BIEDLID", valueset="mentioned", universe=U06)
V("soc_mem15", "soc", "Member of another organisation", s06="ANDLID", valueset="mentioned", universe=U06)
A("soc_mem", S06, "GEENLID", pairs=[(1, 0), (0, 1)], u=U06, note="'none of these' mentioned -> not a member")
W("soc_mem", "SIM 2006: derived from 'geen van deze' in the membership list (card with ten types of organisations); SPVA/SPVN asked a direct yes/no question.")
V("soc_act_most", "soc", "Organisation the respondent spends most time on", s06="ORGTIJD", valueset="org10",
  universe="Respondents who attend activities of or are a member of more than one type of organisation (SIM 2006)")
A("soc_act_ethn", S06, "ORGETNI", u="Respondents who attend activities of or are a member of an organisation (SIM 2006)")
A("soc_volunteer", S06, "VRIJWIL", yn12=True)
W("soc_volunteer", "SIM 2006: 'doet u op dit moment wel eens vrijwilligerswerk' (currently); SIM 2015: in the past 12 months.")
V("soc_vol_for", "soc", "For whom the voluntary work is mainly done", s06="VRIJVOOR", valueset="vol_for6", universe="Volunteers (SIM 2006)")
V("soc_cont_par", "soc", "Frequency of contact with parents (not in the household, living in the Netherlands)", s06="CONTOUD|CONTOU_N", valueset="freq5_cont",
  universe="Respondents with parents living in the Netherlands outside the household (SIM 2006)")
V("soc_cont_chd", "soc", "Frequency of contact with children living away from home (in the Netherlands)", s06="CONTKIND|CONTKIN", valueset="freq5_cont",
  universe="Respondents with children living away from home in the Netherlands (SIM 2006)")
V("soc_cont_sib", "soc", "Frequency of contact with brothers and sisters (not in the household, living in the Netherlands)", s06="CONTZUS|CONTZU_A", valueset="freq5_cont",
  universe="Respondents with siblings living in the Netherlands outside the household (SIM 2006)")
for t in ["soc_cont_par", "soc_cont_chd", "soc_cont_sib"]:
    for p in find(t)["src_sim2006"].split("|"):
        MM(t, S06, p, REV5)
A("soc_cont_frnd_org", S06, "CONTALL|CONTAL_N", pairs=REV5, u="All respondents (SIM 2006; natives asked about friends with a migration background, CONTAL_N)")
A("soc_cont_frnd_nl", S06, "CONTAUT|CONTAU_N", pairs=REV5, u=U06)
A("soc_cont_nbr_org", S06, "CONTBALL|CONTBALN", pairs=REV5, u="All respondents (SIM 2006; natives asked about neighbours with a migration background, CONTBALN)")
A("soc_cont_nbr_nl", S06, "CONTBAUT|CONTBAUN", pairs=REV5, u=U06)
for t in ["soc_cont_frnd_org", "soc_cont_frnd_nl", "soc_cont_nbr_org", "soc_cont_nbr_nl", "soc_cont_par", "soc_cont_chd", "soc_cont_sib"]:
    W(t, "SIM 2006 scale runs 1 never ... 5 every day (reversed to the harmonized order); the contact items were fielded as separate variables for the migrant groups (Q965) and the native sample (Q966).")
A("soc_visit_nl", S06, "BEZOEK|BEZOEK_N", u="All respondents (SIM 2006; natives asked about visits from friends or neighbours with a migration background, BEZOEK_N)")
A("soc_leis_nl", S06, "VRTIJDNL|VRTIJDN", u="All respondents (SIM 2006; natives asked about contact with persons with a migration background, VRTIJDN)")
A("soc_cont_bal", S06, "CONTACTV|CONTAC_A", u="Respondents with leisure contact with native Dutch and with the own group (SIM 2006; natives: own group vs persons with a migration background, CONTAC_A)")
A("soc_leis_oth", S06, "VRTIJDAN", u=U06M)
A("soc_grp_most", S06, "ANVEEL", u="Respondents with leisure contact with other minority groups (SIM 2006)")
A("soc_bestfrnd_eth", S06, "BESTVRIE", u="Respondents with a best friend (SIM 2006)")
A("soc_sport5", S06, "FQSPORT")
for i, (c, nm) in enumerate(_SPORTS, start=1):
    A(f"soc_spt{i:02d}", S06, f"V1530_{i}", u="Respondents who practise a sport (SIM 2006)")
A("soc_sport_comp", S06, "SPORTTYP", yn12=True, u="Respondents who practise a sport (SIM 2006)")
A("soc_sport_ethn", S06, "SPORTPUB", pairs=[(5, ".a")], u="Respondents who practise a sport (SIM 2006)")
A("soc_sport_vol", S06, "SPORTVRW", u=U06)
V("soc_sport_mun", "soc", "Takes part in sports activities offered by the community centre or the municipality", s06="SPORTGEM", valueset="yesno", yn12=True, universe=U06)
V("fam_chd_sport5", "fam", "Frequency of sport of the selected child in the past 12 months", s06="FQSPOR_K", valueset="sport5", universe=U06K)
for i, (c, nm) in enumerate(_SPORTS, start=1):
    V(f"fam_chd_spt{i:02d}", "fam", f"Sport practised by the selected child: {nm} (mentioned)", s06=f"V1570_{i}", valueset="mentioned",
      universe="Selected children who practise a sport (SIM 2006)")
V("fam_chd_sport_comp", "fam", "Selected child took part in competitions, tournaments or matches in the past 12 months", s06="SPORTY_K", valueset="yesno", yn12=True,
  universe="Selected children who practise a sport (SIM 2006)")
V("fam_chd_sport_mem", "fam", "Selected child is a member of a sports club for one of these sports", s06="SPORTLI", valueset="yesno", yn12=True,
  universe="Selected children who practise a sport (SIM 2006)")

# ---- attitudes
for t, src in [("att_chd_frnd_orig", "AFKVRIKI"), ("att_chd_prtnr_orig", "AFKPARKI"), ("att_gr02", "VRWHUISH"), ("att_gr03", "MANGELD"), ("att_gr06", "INKJONGS"),
               ("att_gr01", "MANAANK"), ("att_chd06", "INVLOUDF"), ("att_fam04", "THUISHUW"), ("att_fam19", "VERTRFAM"), ("att_fam17", "KIBEZOUD"),
               ("att_gr07", "VRWSTOPW"), ("att_soc01", "CULTDIV"), ("att_soc03", "ASIELMAK"), ("att_soc04", "RECHTUIT"), ("att_soc05", "VEELALLO"),
               ("att_soc08", "SLECHTWK"), ("att_nl01", "KANSALLO"), ("att_nl03", "RESPRECH"), ("att_nl04", "NLGASTV"), ("att_nl08", "OPENCULT"),
               ("att_soc09", "ALLCUL"), ("att_sat_nl10", "TEVRNED"), ("att_live_nl", "WONALGNL"), ("att_tens_grow", "SPANGROE"), ("att_fear_ext", "EXTREM"),
               ("att_fear_vio", "GEWELD"), ("att_int_effort", "ALLINT"), ("att_int_self", "INTEGRA"), ("att_rel04", "RELIGSCH"), ("att_rel02", "GEENRELD"),
               ("att_rel05", "RELPOL"), ("att_isl02", "ISLNEGA"), ("hlth_happy5", "GELUK")]:
    A(t, S06, src)
for t in ["att_chd_frnd_orig", "att_chd_prtnr_orig", "att_gr02", "att_gr03", "att_gr06", "att_gr01", "att_chd06", "att_fam04", "att_fam19", "att_fam17", "att_gr07",
          "att_soc01", "att_soc03", "att_soc04", "att_soc05", "att_soc08", "att_nl01", "att_nl03", "att_nl04", "att_nl08", "att_soc09", "att_sat_nl10", "att_live_nl",
          "att_tens_grow", "att_fear_ext", "att_fear_vio", "att_int_effort", "hlth_happy5"]:
    U(t, S06, U06)
U("att_int_self", S06, U06M); U("att_rel04", S06, U06R); U("att_rel02", S06, U06R); U("att_rel05", S06, U06R); U("att_isl02", S06, U06MU)
W("att_chd_frnd_orig", "SIM 2006 asks all respondents, with the fill 'stel dat u kinderen zou hebben' for those without children; natives are asked about friends with a migration background.")
V("att_soc10", "att", "Migrants must learn Dutch (agreement)", s06="ALLTAAL", valueset="agree5", universe=U06)
V("att_int_gov", "att", "The Dutch government does enough for the integration of migrants", s06="OVERHINT", valueset="integrated3", universe=U06)
V("att_int_pay", "att", "Who should pay for the civic integration and language courses organised by the government", s06="INBGELD", valueset="pay4", universe=U06)
V("att_cult_priv", "att", "Migrants in the Netherlands should keep their own culture in family life or adapt to Dutch culture", s06="CULPRIVE", valueset="culture4", universe=U06)
V("att_cult_pub", "att", "Migrants in the Netherlands should keep their own culture at school or work or adapt to Dutch culture", s06="CULWERK", valueset="culture4", universe=U06)
V("att_viol", "att", "Violence is not good, but sometimes the only way to achieve an ideal (agreement)", s06="V1176", valueset="agree5", universe=U06)
for t, src in [("att_therm01", "TEMPMAR"), ("att_therm02", "TEMPTUR"), ("att_therm03", "TEMPANT"), ("att_therm04", "TEMPSUR"), ("att_therm06", "TEMPAUT")]:
    A(t, S06, src, u="All respondents except the group itself (SIM 2006)")
V("att_therm08", "att", "Feeling thermometer towards migrants in the Netherlands in general (0 very negative - 100 very positive)", s06="TEMPALL", type="num", universe=U06)
V("att_therm09", "att", "Feeling thermometer towards asylum seekers (0 very negative - 100 very positive)", s06="TEMPASIE", type="num", universe=U06)
A("att_isl03", S06, "NLRESP", u=U06TM); A("att_isl04", S06, "WESTLEEF", u=U06TM); A("att_isl05", S06, "NLVROU", u=U06TM); A("att_isl06", S06, "NLKIND", u=U06TM)
A("att_isl07", S06, "MOSLRESP", u=U06SAN); A("att_isl01", S06, "MOSLLEEF", u=U06SAN); A("att_isl08", S06, "MOSLVRW", u=U06SAN); A("att_isl09", S06, "MOSLKIND", u=U06SAN)
W("att_isl03", "SIM 2006 routes the Islam items by origin group (Turks and Moroccans vs the other groups), SIM 2011 by religion (Muslims vs non-Muslims).")
V("att_isl12", "att", "Annoying when a cashier wearing a headscarf serves me (agreement)", s06="KASSA", valueset="agree5", universe=U06SAN)
V("att_isl10", "att", "Children of the origin group in the Netherlands should go to an Islamic school (agreement)", s06="ISLSCHL", valueset="agree5", universe=U06MU)
V("att_isl11", "att", "Muslims should convert people to Islam in the Netherlands too (agreement)", s06="ISLSPREI", valueset="agree5", universe=U06MU)
for t, src in [("att_dut01", "GEZELLIG"), ("att_dut02", "EERLIJK"), ("att_dut06", "GASTVRIJ"), ("att_dut07", "GIERIG")]:
    A(t, S06, src, u=U06)
V("att_dut13", "att", "Native Dutch are rude", s06="ONBELEE", valueset="trait4", universe=U06)
V("att_mar01", "att", "Moroccans are sociable", s06="GEZMAR", valueset="trait4", universe=U06N)
V("att_mar02", "att", "Moroccans are honest", s06="EERMAR", valueset="trait4", universe=U06N)
V("att_mar03", "att", "Moroccans are hospitable", s06="GASTMAR", valueset="trait4", universe=U06N)
V("att_mar04", "att", "Moroccans are stingy", s06="GIERMAR", valueset="trait4", universe=U06N)
V("att_mar05", "att", "Moroccans are rude", s06="ONBEMAR", valueset="trait4", universe=U06N)
V("att_sur01", "att", "Surinamese are sociable", s06="GEZSUR", valueset="trait4", universe=U06N)
V("att_sur02", "att", "Surinamese are honest", s06="EERSUR", valueset="trait4", universe=U06N)
V("att_sur03", "att", "Surinamese are hospitable", s06="GASTSUR", valueset="trait4", universe=U06N)
V("att_sur04", "att", "Surinamese are stingy", s06="GIERSUR", valueset="trait4", universe=U06N)
V("att_sur05", "att", "Surinamese are rude", s06="ONBESUR", valueset="trait4", universe=U06N)
V("saf_unsafe", "saf", "Sometimes feels unsafe", s06="ONVALG", valueset="yesno", yn12=True, universe=U06)
V("saf_unsafe_freq", "saf", "How often feels unsafe", s06="FQONV", valueset="unsafe_freq3", universe="Respondents who sometimes feel unsafe (SIM 2006)")
V("saf_unsafe_street", "saf", "How often feels unsafe walking in the street", s06="ONVSTRT", valueset="unsafe_freq3", universe=U06)
V("saf_unsafe_home", "saf", "How often feels unsafe in own home", s06="ONVHUIS", valueset="unsafe_freq3", universe=U06)

# ---- politics
A("pol_interest3", S06, "POLINT")
V("pol_interest_where", "pol", "Politics of which country the respondent is mainly interested in", s06="POLTYPE", valueset="pol_where4",
  universe="Respondents with a migration background who are interested in politics (SIM 2006)")
A("pol_vote_int", S06, "STEMINT")
A("pol_party", S06, "STEMWS", pairs=[(1, 3), (2, 7), (3, 1), (4, 4), (5, 18), (6, 6), (7, 5), (8, 8), (9, 11), (10, 92), (11, 15), (12, 17)],
  u="Respondents who would (maybe) vote (SIM 2006)")

# ---- media
V("med_krant_nl_days", "med", "Reads Dutch newspapers or magazines (days per week, 6 classes)", s06="KRTNED", valueset="media_days6", universe=U06)
V("med_krant_orig_days", "med", "Reads origin-group newspapers or magazines (days per week, 6 classes)", s06="KRTEIG", valueset="media_days6", universe=U06M)
V("med_tv_nl_days", "med", "Watches Dutch television channels (days per week, 6 classes)", s06="TVNED", valueset="media_days6", universe=U06)
V("med_tv_orig_days", "med", "Watches origin-group television channels (days per week, 6 classes)", s06="TVEIG", valueset="media_days6", universe=U06M)
_D6_F5 = [(6, 1), (5, 1), (4, 2), (3, 3), (2, 4), (1, 5)]
A("med_krant_nl_cat", S06, "KRTNED", pairs=_D6_F5, u=U06); A("med_krant_orig_cat", S06, "KRTEIG", pairs=_D6_F5, u=U06M)
A("med_tv_nl_cat", S06, "TVNED", pairs=_D6_F5, u=U06); A("med_tv_orig_cat", S06, "TVEIG", pairs=_D6_F5, u=U06M)
for t in ["med_krant_nl_cat", "med_krant_orig_cat", "med_tv_nl_cat", "med_tv_orig_cat"]:
    W(t, "SIM 2006 asked days per week in six classes (kept in the *_days variable); collapsed here: every day and 5-6 days -> (almost) every day, 3-4 days -> several times a week, 1-2 days -> once a week, less than 1 day -> less than once a week.")
A("med_satellite", S06, "SATEL", yn12=True)
A("med_pc_internet", S06, "BEZITPC", yn12=True)
V("med_email_month", "med", "Used the internet this month to e-mail or chat", s06="EMAIL", valueset="yesno", yn12=True, universe=U06)
V("med_email_ethn", "med", "Background of the people the respondent e-mails or chats with", s06="CHATPUB", valueset="ethmix4", universe="Respondents who e-mailed or chatted this month (SIM 2006)")
V("med_web_type", "med", "Type of internet sites visited most", s06="SITETYPE", valueset="web_type5", universe="Respondents with a migration background who e-mailed or chatted this month (SIM 2006)")

# ---- discrimination, housing and neighbourhood
A("disc_perc", S06, "DISCALG", u=U06M)
A("disc_exp", S06, "DISCZELF", u=U06M)
A("hous_nbhd_pleas4", S06, "FIJNBRT", u=U06)
A("hous_nbhd_forgn", S06, "AANTBL", u=U06)
A("hous_nbhd_reason", S06, "BURT_NEW|BURT_OUD", pairs={"BURT_OUD": [(9, 10)]}, u=U06,
  note="two questionnaire versions: the later one (BURT_NEW) added 'born here / lived here since childhood' (9)")
A("hous_tenure", S06, "KOOPWON", pairs=[(1, 1), (2, 2), (3, 98)])
A("hous_nbhd01", S06, "BRTTHUIS", u=U06)
A("hous_nbhd02", S06, "BRTPRET", u=U06)

# ---- religion
A("rel_any", S06, "GELOOFT", yn12=True)
A("rel_den_det", S06, "RELIGIE", pairs=[(1, 11), (2, 12), (3, 13), (4, 21), (5, 22), (6, 23), (7, 24), (8, 26), (9, 25), (10, 31), (11, 32), (12, 33), (13, 39),
                                        (14, 34), (15, 35), (16, 36), (17, 38), (18, 99)], u=U06R)
A("rel_den_cat", S06, "RELIGIE", pairs=[(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 3), (11, 3), (12, 3), (13, 3), (14, 3), (15, 3),
                                        (16, 3), (17, 3), (18, 4)], u=U06R)
A("rel_attend", S06, "KERKBEZ", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 4)], u=U06R)
A("rel_attend5", S06, "KERKBEZ", pairs=REV5, u=U06R)
W("rel_attend5", "SIM 2006 scale runs 1 never ... 5 every day (reversed here).")
V("rel_talk5", "rel", "Frequency of talking about the faith with friends or family", s06="PRAATREL", valueset="freq5_cont", universe=U06R)
V("rel_web5", "rel", "Frequency of looking for information about the faith on the internet", s06="NETRELI", valueset="freq5_cont", universe=U06R)
MM("rel_talk5", S06, "PRAATREL", REV5); MM("rel_web5", S06, "NETRELI", REV5)
V("rel_pray7", "rel", "Frequency of prayer, 7 categories (SIM 2006)", s06="GEBED", valueset="pray7", universe=U06MU)
A("rel_pray", S06, "GEBED", pairs=[(7, 1), (6, 2), (5, 3), (4, 3), (3, 4), (2, 5), (1, 6)], u=U06MU)
W("rel_pray", "SIM 2006 asked seven categories (kept in rel_pray7): 'once a week' and 'several times a week' are both mapped to 'every week'.")
A("rel_ramadan", S06, "RAMADAN", pairs=[(1, 4), (2, 3), (3, 2), (4, 1)], u=U06MU)
A("rel_halal", S06, "HALAL", pairs=[(1, 4), (2, 3), (3, 2), (4, 1)], u=U06MU)
W("rel_ramadan", "SIM 2006 scale runs 1 no ... 4 all days (reversed here).")
W("rel_halal", "SIM 2006 scale runs 1 no ... 4 all days (reversed here).")
A("rel_id01", S06, "RELZELF", u=U06R); A("rel_id02", S06, "RELKWET", u=U06R)
V("rel_id04", "rel", "Nobody may question my faith (agreement)", s06="RELTWIJF", valueset="agree5", universe=U06R)
A("rel_rule", S06, "ISREGEL", u=U06MU)
A("rel_veil_should", S06, "HOOFDBUI", u=U06MU)
A("rel_veil", S06, "ZHFDDOEK", pairs=[(1, 1), (2, 0)], u="Turkish and Moroccan women (SIM 2006)")
V("rel_veil_wife", "rel", "Wife wears a headscarf when going out", s06="VROUDOEK", valueset="yesno", yn12=True, universe="Turkish and Moroccan men with a partner (SIM 2006)")
V("rel_veil_why", "rel", "Main reason for wearing a headscarf (respondent or her/his wife)", s06="WELDOEK", valueset="veil_reason6",
  universe="Turkish and Moroccan respondents who (whose wife) wear(s) a headscarf (SIM 2006)")
V("rel_noveil_why", "rel", "Main reason for not wearing a headscarf (respondent or her/his wife)", s06="GEENDOEK", valueset="noveil_reason6",
  universe="Turkish and Moroccan respondents who (whose wife) do(es) not wear a headscarf (SIM 2006)")

# ---- health
V("hlth_chronic", "hlth", "Has a long-term illness, condition or handicap", s06="HANDI", valueset="yesno", yn12=True, universe=U06)
V("hlth_lim3", "hlth", "Health complaints limit daily activities", s06="BELEM", valueset="limited3", universe="Respondents with a long-term illness, condition or handicap (SIM 2006)")
A("hlth_self", S06, "GEZONDH", u=U06)
A("hlth_gp2m", S06, "HUISARTS", u=U06)
A("hlth_spec", S06, "MEDSPEC", yn12=True, u=U06)
V("hlth_alcohol5", "hlth", "Days per week on which the respondent drinks alcohol (classes)", s06="ALCOHOL", valueset="alcohol5", universe=U06)
A("hlth_pa_summer", S06, "SPORTZOM", pairs=[(8, 0)], note="8 = no day")
A("hlth_pa_winter", S06, "SPORTWIN", pairs=[(8, 0)], note="8 = no day")


# ====================================================================================================== LAS 2004/05
# Leefsituatie Allochtone Stedelingen (SCP; fieldwork Veldkamp Oct 2004 - Jun 2005) in the 50 largest municipalities:
# Turks, Moroccans, Surinamese, Antilleans/Aruban and a native Dutch reference sample, 4,096 respondents, plus a
# time-use diary (one day) for 3,045 of them.  CBS-protected deposit: age in 5-year classes, no municipality, no
# household roster (K1…/AND1… variables), no occupation codes beyond level and class; the questionnaire is appendix 1a
# of the fieldwork report.  Missing codes -7 'vragenblok niet gesteld', -5 nvt, -3 weet niet, -2 wil niet zeggen;
# system-missing = routed past the question (sysmis_tag = c).
U04 = "All respondents (LAS 2004/05)"
U04M = "Respondents with a migration background (LAS 2004/05)"
U04N = "Native Dutch respondents (LAS 2004/05)"
U04TM = "Turkish and Moroccan respondents (LAS 2004/05)"
U04P = "Respondents with a partner (LAS 2004/05)"
U04PC = "Respondents living with a partner (LAS 2004/05)"
U04W = "Employed respondents (LAS 2004/05)"
U04E = "Employees (LAS 2004/05)"
U04NW = "Respondents without paid work (LAS 2004/05)"
U04D = "Respondents who completed the time-use diary (LAS 2004/05)"
U04C03 = "Respondents with a child aged 0-3 (LAS 2004/05)"
U04C411 = "Respondents with a child aged 4-11 (LAS 2004/05)"
U04WP = "Respondents with a child aged 0-11 who have (had) paid work (parental-leave block, LAS 2004/05)"
U04MU = "Muslim respondents (LAS 2004/05)"
U04R = "Religious respondents (LAS 2004/05)"
_MR = "wil niet zeggen / geen informatie"

# ---- survey administration, weights
A("id_src", S04, "INTNR")
A("svy_wgt", S04, "WEEGTOT", u=U04)
A("svy_wgt_grp", S04, "WEEGHERK", u=U04)
A("svy_wgt_raise", S04, "OPHTOT", u=U04)
V("svy_oversample", "svy", "Belongs to the oversample of working men and women (LAS 2004/05)", s04="OVERSAMP", valueset="yesno", universe=U04)
V("svy_voucher", "svy", "Gift voucher chosen as reward (LAS 2004/05)", s04="CADBON", valueset="voucher2", universe=U04)
A("svy_lang_hh", S04, "TAALINT", pairs=[(6, ".d")], u=U04, note="'anders' cannot be placed on the Dutch/other-language scale")
A("svy_others_present", S04, "ALLEEN", u=U04)
A("lang_nl_rated4", S04, "TAALVAAR", u=U04)
A("geo_urb_reg", S04, "STEDGEM", pairs=[(-1, ".d")], u=U04, note="postcode unknown")
W("geo_urb_reg", "LAS 2004/05: urbanisation of the municipality in five CBS classes, attached by SCP (the sample covers the 50 largest municipalities).")

# ---- demography and household
A("dem_eth", S04, "ETNGRP", pairs=[(5, 90)])
A("dem_gen", S04, "GENERAT", pairs=[(-9, 0)])
A("dem_sex", S04, "GESLACHT")
A("dem_age_cat5y", S04, "LEEFTIJD", u=U04)
A("dem_age_cat", S04, "LEEFTIJD", pairs=[(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3), (7, 4), (8, 4), (9, 5), (10, 5)], u=U04)
W("dem_age_cat5y", "LAS 2004/05 sampled persons aged 15-64 only.")
A("dem_mar", S04, "BURGST", pairs=[(1, 1), (2, 2), (3, 4), (4, 4)], u=U04, note="divorced and widowed are one category in LAS (mapped to 2)")
W("dem_mar", "LAS 2004/05 combines 'divorced' and 'widowed' (code 2 here = divorced or widowed).")
A("hh_size", S04, "GEZOMV", pairs=[(5, 5)], u=U04, note="5 = 5 or more in the deposit")
W("hh_size", "LAS 2004/05 (CBS-protected deposit): 5 = five or more persons.")
A("dem_prtnr_st", S04, "LATPART|SAMPART", pairs={"LATPART": [(1, 4), (2, 0)], "SAMPART": [(1, 1), (2, 3), (3, 2), (4, 0)]}, u=U04)
A("dem_prtnr_lat", S04, "LATPART", pairs=[(1, 1), (2, 2)], u="Respondents not married or cohabiting (LAS 2004/05)")
A("dem_mar_yr", S04, "HUWJAAR", pairs=[(0, ".d")], u="Married respondents (LAS 2004/05)", note="0 = age at marriage given instead")
A("dem_mar_age", S04, "HUWLFTD", pairs=[(0, ".d"), (-1984, ".d"), (-1980, ".d"), (-1962, ".d"), (-1958, ".d")], u="Married respondents (LAS 2004/05)",
  note="0 = year given instead; four records hold a (negative) year")
A("dem_prtnr_age_cat5y", S04, "LFTPART", u=U04P)
A("dem_prtnr_age_cat", S04, "LFTPART", pairs=[(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3), (7, 4), (8, 4), (9, 5), (10, 5)], u=U04P)
A("dem_prtnr_brthcntry", S04, "GEBLPART", pairs=[(1, 5022), (2, 6043), (3, 7011), (4, 5007), (5, 6030), (6, 9999)], u=U04P)
A("dem_prtnr_gen", S04, "GENPART", u="Respondents with a migration background who have a partner, whatever the partner's origin (LAS 2004/05); partners of native Dutch respondents are not classed (.c)")
A("dem_posfam", S04, "GEZINPO2", pairs=[(6, 9), (7, 10)], u=U04)
W("dem_posfam", "LAS 2004/05 does not separate children living with one or two parents (code 9) and adds children living with other relatives (10).")
A("hh_comp", S04, "GEZSAMST", pairs=[(8, 9), (9, 8)], u=U04)
V("hh_comp_cbs", "hh", "Household composition, CBS classification (LAS 2004/05)", s04="SAMHSH", valueset="hh_cbs7", universe=U04)
A("mig_reason", S04, "REDMIGR", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 14), (8, 10)], u="First-generation respondents (LAS 2004/05)")
A("mig_yr_arr", S04, "MIGRJAAR", u="First-generation respondents (LAS 2004/05)")
A("mig_age_arr", S04, "MIGROUD", u="First-generation respondents (LAS 2004/05)")

# ---- mobility
V("mob_licence", "mob", "Has a driving licence for a passenger car", s04="RYBEWYS", valueset="yesno", yn12=True, universe="Respondents aged 18 or older (LAS 2004/05)")
V("mob_ncar", "mob", "Number of passenger cars in the household", s04="NUMAUTO", type="num", universe=U04)
V("mob_nbike", "mob", "Number of bicycles in the household", s04="NUMFIETS", type="num", universe=U04)
V("mob_nmoped", "mob", "Number of mopeds in the household", s04="NUMBROMF", type="num", universe=U04)
V("mob_pass_local", "mob", "Has a season ticket or discount card for local / regional public transport", s04="ABSTSTR", valueset="yesno", yn12=True, universe=U04)
V("mob_pass_train", "mob", "Has a season ticket or discount card for the train", s04="ABNS", valueset="yesno", yn12=True, universe=U04)
V("mob_problem", "mob", "Most important problem in traffic", s04="PRBLVV", valueset="traffic8", universe=U04)

# ---- education
A("edu_abr_att_lvl3", S04, "MAXOPLBL", pairs=[(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3), (8, ".c")], u="Respondents who attended education abroad (LAS 2004/05)",
  note="8 'nooit naar school geweest' has no level")
A("edu_abr_att_det", S04, "MAXOPLBL", pairs=[(8, 0)], u="Respondents who attended education abroad (LAS 2004/05; 0 = never went to school)")
A("edu_abr_dipl", S04, "DIPLBL", yn12=True, u="Respondents who attended education abroad (LAS 2004/05)")
A("edu_abr_yrs", S04, "ONDJRBL", u="Respondents who attended education abroad (LAS 2004/05)")
A("edu_ft", S04, "VOLTOPL", yn12=True, u=U04)
A("edu_cur_lvl", S04, "HUIDOPL", u="Enrolled respondents (LAS 2004/05)")
A("edu_cur_lvl3", S04, "HUIDOPL", pairs=[(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)], u="Enrolled respondents (LAS 2004/05)")
A("edu_nl_att_hi", S04, "MAXOPLNL", u=U04)
A("edu_nl_att_lvl3", S04, "MAXOPLNL", pairs=[(-1, 0), (0, ".c"), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)], u=U04)
V("edu_nl_dipl_att", "edu", "Has a diploma of the highest education attended in the Netherlands", s04="DIPLNL", valueset="yesno", yn12=True,
  universe="Respondents who attended education in the Netherlands (LAS 2004/05)")
V("edu_prtnr_det", "edu", "Highest education attended by the partner, 8 levels (LAS 2004/05; 0 = never or only a few years at school)", s04="MAXDIPP", valueset="edu8", universe=U04P)
M("edu_prtnr_det", S04, "MAXDIPP", 8, 0)
A("edu_prtnr_lvl3", S04, "MAXDIPP", pairs=[(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3), (8, 0)], u=U04P)
A("edu_part", S04, "ONDPART")
A("edu_cntry", S04, "OPLBLNL")

# ---- labour market
V("lab_flex", "lab", "Can start work an hour later if needed", s04="FLEXW", valueset="flex3", universe=U04W)
V("dem_prtnr_flex", "dem", "Partner can start work an hour later if needed (answered by the partner in the supplementary partner interview)", s04="PFLEXW", valueset="flex3",
  universe="Working partners of male Turkish, Moroccan and Antillean respondents with children under 12 who took part in the supplementary partner interview (47 cases, LAS 2004/05)")
A("lab_perm", S04, "VASTWERK", u=U04E)
A("lab_want", S04, "WILWERK", pairs=[(1, 1), (2, 3), (3, 1), (4, 1)], u=U04NW, note="3 'reeds gevonden' and 4 'wil wel, maar kan niet' count as wanting work")
A("lab_want5", S04, "WILWERK", pairs=[(1, 1), (2, 3), (3, 4), (4, 5)], u=U04NW)
V("lab_avail4", "lab", "How soon the respondent could start working", s04="BESCHILB", valueset="avail4", universe="Respondents without paid work who want work (LAS 2004/05)")
A("lab_navail_reason", S04, "PERBEGIN", pairs=[(1, 4), (2, 3), (3, 1), (4, 2), (5, 5)], u="Respondents who need more than two weeks before they can start (LAS 2004/05)")
A("lab_seek", S04, "ZOEKWERK", yn12=True, u="Respondents without paid work who want work (LAS 2004/05)")
V("lab_seek4w", "lab", "Tried to find work in the past four weeks", s04="ZOEK4WK", valueset="seek3", universe="Respondents who looked for work in the past six months (LAS 2004/05)")
A("lab_act", S04, "HFDACT", u=U04NW)
V("soc_vol_hrs", "soc", "Hours per week spent on voluntary work (0 = less than one hour)", s04="VRIJWUUR", type="num", universe="Volunteers (LAS 2004/05)")
M("soc_vol_hrs", S04, "VRIJWUUR", 97, ".d", "varies strongly / irregular")
A("dem_prtnr_hrs", S04, "PARTUREN", u="Respondents whose partner has paid work (LAS 2004/05)")
A("dem_prtnr_act", S04, "PARTHFDA", pairs=[(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 98)], u="Respondents whose partner has no paid work (LAS 2004/05)")
V("lab_hrs_want", "lab", "Hours per week the respondent would like to work outside the home", s04="ZELFWERL", type="num",
  universe="Respondents who work, are unemployed, homemaker or work-disabled and live with a partner (LAS 2004/05)")
V("dem_prtnr_hrs_want", "dem", "Hours per week the respondent would like the partner to work outside the home", s04="PRTWERK", type="num",
  universe="Respondents who work, are unemployed, homemaker or work-disabled and live with a partner (LAS 2004/05)")
A("lab_hrs", S04, "URENWRK", pairs=[(-1, ".d")], u=U04W)
V("lab_hrs_tot", "lab", "Hours worked per week, all respondents (0 = no paid work; SCP construct urenwerk)", s04="URENWERK", type="num", universe=U04)
A("lab_lf3", S04, "BB_NED", u=U04)
A("lab_lf", S04, "BB_NED", pairs=[(1, 1), (2, 1), (3, 0)], u=U04)
A("lab_rel", S04, "BERBEV", pairs=[(1, 1), (2, 7), (3, 8)], u=U04, note="LAS 3 classes: working / non-working labour force / not in labour force")
W("lab_rel", "LAS 2004/05 has three classes (BERBEV): working labour force (1), non-working labour force (7) and not in the labour force (8).")
A("lab_occ_lvl", S04, "BERNIV", u=U04W)
W("lab_occ_lvl", "LAS 2004/05: skill level (beroepsniveau) of all working respondents, SBC-92 levels 1-5.")
V("lab_occ_class", "lab", "Occupational class (SBC-92 two-digit classes, LAS 2004/05)", s04="BEROEP2", valueset="occ_class_las", universe=U04W)
V("lab_occ_lvl_src", "lab", "Skill level of the occupation incl. 'unknown/other' (LAS 2004/05 source variable beroep1)", s04="BEROEP1", valueset="skill_level", universe=U04W, include=0)
M("lab_occ_lvl_src", S04, "BEROEP1", 7, ".d", "onbekend/overig")
V("lab_socpos", "lab", "Social position: main activity combined with occupational level (SCP construct)", s04="MAATPOS", valueset="socpos9", universe=U04)
A("lab_emptype", S04, "POSWRK", pairs=[(1, 1), (2, 2), (3, 3), (4, 3)], u=U04W)
V("lab_ind_sec", "lab", "Industry of current job, 14 sectors (LAS 2004/05)", s04="BEDRIJF", valueset="sector14", universe=U04W)
M("lab_ind_sec", S04, "BEDRIJF", 99, ".d", "onbekend")
V("lab_earner_type", "lab", "Earner type of the couple (SCP construct)", s04="VERDTYP", valueset="earner8", universe=U04PC)
V("lab_earner_type_pref", "lab", "Preferred earner type of the couple (from the desired hours of both partners)", s04="GVERDTYP", valueset="earner8", universe=U04PC)
V("lab_dom_help_work", "lab", "Works as a paid domestic help", s04="HLPBW", valueset="yesno", yn12=True, universe="Women (LAS 2004/05)")

# ---- income
V("hh_inc_band16", "hh", "Net monthly household income incl. co-resident children's income, 250-euro bands (LAS 2004/05)", s04="GEZINK", valueset="hh_band16_las", scope="household",
  universe="Respondents who are head or partner of the household (LAS 2004/05)",
  notes="LAS defines household income as respondent + partner + co-resident children with an income (VRAAG 77); SIM 2011 hh_inc_band excludes children's income, so the two are not collapsed into one variable.")
M("hh_inc_band16", S04, "GEZINK", 0, ".d", "amount given in euro (not deposited)")

# ---- division of household tasks, work and family
V("fam_div01", "fam", "Who does the shopping (groceries)", s04="BOODSCH1", valueset="who4", universe=U04PC)
V("fam_div02", "fam", "Who cooks", s04="KOKEN1", valueset="who4", universe=U04PC)
V("fam_div03", "fam", "Who does the laundry", s04="WASSEN1", valueset="who4", universe=U04PC)
V("fam_div04", "fam", "Who looks after the children", s04="VERZ1", valueset="who4", universe="Couples with children (LAS 2004/05)")
V("fam_div05", "fam", "Who takes the children to school", s04="BRENGEN1", valueset="who4", universe="Couples with school-age children (LAS 2004/05)")
V("fam_task_conflict", "fam", "Disagreements with the partner about the division of household tasks (frequency)", s04="HHTAKEN1", valueset="freq5_conf", universe=U04PC)
V("fam_task_conflict_why", "fam", "Nature of the disagreement about household tasks", s04="HHTAKEN2", valueset="task_conflict5",
  universe="Respondents who have disagreements about household tasks (LAS 2004/05)")
V("fam_frstchd_nl", "fam", "Lived in the Netherlands when expecting the first child", s04="ZWNED", valueset="yesno", yn12=True,
  universe="Mothers who worked when expecting their first child (LAS 2004/05)")
V("fam_frstchd_plan", "fam", "Plan to keep working after the birth of the first child (retrospective)", s04="ZWPLAN", valueset="plan5",
  universe="Mothers who worked in the Netherlands when expecting their first child (LAS 2004/05)")
M("fam_frstchd_plan", S04, "ZWPLAN", 9, ".a", "does not remember")
_ZW = "Mothers who worked in the Netherlands when expecting their first child (LAS 2004/05)"
V("fam_frstchd01", "fam", "At the time: felt that as a mother I should always be at home for my child (agreement)", s04="ZWTHUIS", valueset="agree5", universe=_ZW)
V("fam_frstchd02", "fam", "At the time: felt my world would become too small if I stopped working (agreement)", s04="ZWKLEIN", valueset="agree5", universe=_ZW)
V("fam_frstchd03", "fam", "At the time: felt I first had to be sure of good childcare (agreement)", s04="ZWOPV", valueset="agree5", universe=_ZW)
V("fam_frstchd04", "fam", "At the time: felt I had to keep working for the money (agreement)", s04="ZWGELD", valueset="agree5", universe=_ZW)
V("fam_frstchd05", "fam", "At the time: my partner found it important that I kept working (agreement)", s04="ZWPRT", valueset="agree5", universe=_ZW)
V("fam_frstchd06", "fam", "At the time: I always enjoyed my work very much (agreement)", s04="ZWPLEZ", valueset="agree5", universe=_ZW)
_TK = "Working women without children who may have children in future (LAS 2004/05)"
V("fam_futchd_plan", "fam", "Intention to keep working when having children", s04="TKSTOP", valueset="plan5", universe=_TK)
V("fam_futchd01", "fam", "A mother should always be at home for her child (agreement)", s04="TKTHUIS", valueset="agree5", universe=_TK)
V("fam_futchd02", "fam", "My world would become too small if I stopped working (agreement)", s04="TKKLEIN", valueset="agree5", universe=_TK)
V("fam_futchd03", "fam", "I first want to be sure of good childcare for my child (agreement)", s04="TKOPV", valueset="agree5", universe=_TK)
V("fam_futchd04", "fam", "It seems hard to me to work when I have children (agreement)", s04="TKZWAAR", valueset="agree5", universe=_TK)
V("fam_futchd05", "fam", "I have to keep working because of the money (agreement)", s04="TKGELD", valueset="agree5", universe=_TK)
V("fam_futchd06", "fam", "I enjoy my work very much (agreement)", s04="TKPLEZ", valueset="agree5", universe=_TK)
for i, (src, nm) in enumerate([("GRT0_3", "grandparents"), ("FAM0_3", "other family members"), ("VRND0_3", "friends / acquaintances"), ("OPPAS0_3", "a babysitter found oneself"),
                               ("KDVB0_3", "a day nursery"), ("GOP0_3", "a childminder scheme (gastouderproject)"), ("PSZ0_3", "a playgroup (peuterspeelzaal)")], start=1):
    V(f"fam_care03_{i:02d}", "fam", f"Entrusting a child aged 0-3 to: {nm}", s04=src, valueset="care_opt5", universe=U04C03)
V("fam_care03_use", "fam", "Regular use of childcare for a child aged 0-3", s04="OPV0_3", valueset="yesno", yn12=True, universe=U04C03)
for i, (src, nm) in enumerate([("V102_1", "playgroup / class"), ("V102_2", "day nursery"), ("V102_3", "childminder"), ("V102_4", "paid babysitter outside the home"),
                               ("V102_5", "paid babysitter at home"), ("V102_6", "the child's grandparents"), ("V102_7", "unpaid family"), ("V102_8", "unpaid friends"),
                               ("V102_9", "other")], start=1):
    V(f"fam_care03_t{i:02d}", "fam", f"Childcare used for a child aged 0-3: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Respondents using childcare for a child aged 0-3 (LAS 2004/05)")
for i, src in enumerate(["Q10401", "Q10402", "Q10403"], start=1):
    V(f"fam_care03_no{i}", "fam", f"Reason for not using childcare for a child aged 0-3 ({i}{'st' if i == 1 else 'nd' if i == 2 else 'rd'} reason coded)", s04=src, valueset="nocare14",
      universe="Respondents not using childcare for a child aged 0-3 (LAS 2004/05)")
V("fam_care411_lunch", "fam", "Child aged 4-11 stays at school over lunch", s04="OVER411", valueset="freq3", universe=U04C411)
W("fam_care411_lunch", "LAS 2004/05 answers: ja, regelmatig / ja, soms / nee, nooit.")
for i, (src, nm) in enumerate([("GRT411", "grandparents"), ("FAM411", "other family members"), ("VRND411", "friends / acquaintances"), ("OPPAS411", "a babysitter found oneself"),
                               ("BSO411", "out-of-school care (BSO)"), ("GOP411", "a childminder scheme (gastouderproject)")], start=1):
    V(f"fam_care411_{i:02d}", "fam", f"Entrusting a child aged 4-11 to: {nm}", s04=src, valueset="care_opt5", universe=U04C411)
V("fam_care411_use", "fam", "Use of childcare after school for a child aged 4-11", s04="OPV411", valueset="yesno", yn12=True, universe=U04C411)
for i, (src, nm) in enumerate([("V111_1", "out-of-school care"), ("V111_2", "childminder (child goes there)"), ("V111_3", "paid babysitter (child goes there)"),
                               ("V111_4", "paid babysitter at home"), ("V111_5", "the child's grandparents"), ("V111_6", "unpaid family"), ("V111_7", "unpaid friends"),
                               ("V111_8", "other")], start=1):
    V(f"fam_care411_t{i:02d}", "fam", f"After-school care used for a child aged 4-11: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Respondents using after-school care for a child aged 4-11 (LAS 2004/05)")
for i, src in enumerate(["Q11301", "Q11302", "Q11303"], start=1):
    V(f"fam_care411_no{i}", "fam", f"Reason for not using out-of-school care for a child aged 4-11 ({i}{'st' if i == 1 else 'nd' if i == 2 else 'rd'} reason coded)", s04=src,
      valueset="nocare14", universe="Respondents not using out-of-school care for a child aged 4-11 (LAS 2004/05)")
W("fam_care411_no1", "LAS 2004/05 code 10 reads 'child too old/young for out-of-school care or does not want it', 11 'already has other care, e.g. with friends'.")
V("fam_leave_paid", "fam", "Part of the wage was paid during parental leave", s04="LNDOOR", valueset="leave_paid3", universe="Respondents who took parental leave (LAS 2004/05)")
for i, (src, nm) in enumerate([("V118_1", "partner took parental leave"), ("V118_2", "did not want to lose income"), ("V118_3", "does not know what parental leave is"),
                               ("V118_4", "already worked part-time"), ("V118_5", "enough childcare available"), ("V118_6", "partner had no work"), ("V118_7", "no work"),
                               ("V118_8", "employer did not agree"), ("V118_9", "the work did not allow it"), ("V118_10", "bad for my career"), ("V118_11", "used days off"),
                               ("V118_12", "other reason")], start=1):
    V(f"fam_noleave{i:02d}", "fam", f"Reason for not taking parental leave: {nm} (mentioned)", s04=src, valueset="mentioned", universe=U04WP)
V("fam_noleave_main", "fam", "Main reason for not taking parental leave", s04="RDNVERL", valueset="noleave14", universe=U04WP)
M("fam_noleave_main", S04, "RDNVERL", 13, ".a"); M("fam_noleave_main", S04, "RDNVERL", 99, ".a")
V("fam_sickcare_wish", "fam", "Wanted to care for a sick family member in the past two years", s04="ZIEKKRT", valueset="yesno", yn12=True, universe=U04W)
V("fam_sickcare_leave", "fam", "Took leave to care for a sick family member in the past two years", s04="VERLKRT", valueset="yesno", yn12=True,
  universe="Employed respondents who wanted to care for a sick family member (LAS 2004/05)")
V("fam_sickcare_leave_n", "fam", "Number of times leave was taken for a sick family member in two years", s04="FQKRT", type="num",
  universe="Employed respondents who took leave for a sick family member (LAS 2004/05)")
V("fam_sickcare_leave_type", "fam", "Type of leave taken the last time (sick family member)", s04="SRTZIEK", valueset="leave_type4",
  universe="Employed respondents who took leave for a sick family member (LAS 2004/05)")
for i, (src, nm) in enumerate([("V125_1", "enough holiday / ADV days"), ("V125_2", "did not know the scheme"), ("V125_3", "other reason")], start=1):
    V(f"fam_sickcare_noleave{i:02d}", "fam", f"Reason for not taking leave for a sick family member: {nm} (mentioned)", s04=src, valueset="mentioned",
      universe="Employed respondents who did not take leave for a sick family member (LAS 2004/05)")
V("fam_sickcare_noleave_main", "fam", "Main reason for not taking leave for a sick family member", s04="RDN_KZ", valueset="noleave_kz3",
  universe="Employed respondents who gave several reasons for not taking leave (LAS 2004/05)")
M("fam_sickcare_noleave_main", S04, "RDN_KZ", 4, ".a"); M("fam_sickcare_noleave_main", S04, "RDN_KZ", 5, ".d")
V("fam_illcare", "fam", "Cared for a seriously ill person in the past two years", s04="ZIEKLNG", valueset="yesno", yn12=True, universe=U04W)
V("fam_illcare_2w", "fam", "Cared for the seriously ill person for more than two weeks", s04="DUURLNG", valueset="yesno", yn12=True,
  universe="Employed respondents who cared for a seriously ill person (LAS 2004/05)")
V("fam_illcare_leave", "fam", "Took leave to care for the seriously ill person", s04="VERLLANG", valueset="yesno", yn12=True,
  universe="Employed respondents who cared for a seriously ill person for more than two weeks (LAS 2004/05)")
V("fam_illcare_leave_n", "fam", "Number of times leave was taken to care for a seriously ill person", s04="FQLNG", type="num",
  universe="Employed respondents who took leave to care for a seriously ill person (LAS 2004/05)")
V("fam_illcare_leave_type", "fam", "Type of leave taken the last time (seriously ill person)", s04="JRTLNG", valueset="leave_type4",
  universe="Employed respondents who took leave to care for a seriously ill person (LAS 2004/05)")
M("fam_illcare_leave_type", S04, "JRTLNG", 5, ".a")
for i, (src, nm) in enumerate([("V133_1", "too few days off"), ("V133_2", "did not know the possibility"), ("V133_3", "other reason")], start=1):
    V(f"fam_illcare_noleave{i:02d}", "fam", f"Reason for not taking leave to care for a seriously ill person: {nm} (mentioned)", s04=src, valueset="mentioned",
      universe="Employed respondents who did not take leave to care for a seriously ill person (LAS 2004/05)")
V("fam_illcare_noleave_main", "fam", "Main reason for not taking leave to care for a seriously ill person", s04="RDN_VRY", valueset="noleave_vry3",
  universe="Employed respondents who gave several reasons for not taking care leave (LAS 2004/05)")
M("fam_illcare_noleave_main", S04, "RDN_VRY", 4, ".a"); M("fam_illcare_noleave_main", S04, "RDN_VRY", 5, ".d")

# ---- social contacts
V("soc_cont_frnd_m5", "soc", "Frequency of contact with friends or good acquaintances (seeing, telephone, letters)", s04="CONTVRIE", valueset="freq5_month", universe=U04,
  notes="SIM 2011 asked a different 5-point scale (soc_cont_frnd).")
V("soc_cont_fam_m5", "soc", "Frequency of contact with family members outside the household", s04="CONTFAM", valueset="freq5_month", universe=U04,
  notes="SIM 2011 asked a different 5-point scale (soc_cont_fam).")
A("soc_visit_nl", S04, "BEZOEK", u="All respondents (LAS 2004/05; natives asked about visits from friends or neighbours with a migration background)")
A("soc_leis_nl", S04, "VRTIJDNL|VRTIJDAL", u="All respondents (LAS 2004/05; natives asked about contact with persons with a migration background, VRTIJDAL)")
A("soc_cont_bal", S04, "CONTACTV", u="Respondents who spend leisure time with the other group (LAS 2004/05; natives were asked about contact with 'allochtone Nederlanders' vs native Dutch, so for them code 1 means more contact with persons of foreign origin)")
V("soc_frnd_nl_freq", "soc", "Frequency of contact in the past 12 months with a self-chosen native Dutch friend or acquaintance", s04="VRIENL", valueset="freq7_frnd", universe=U04)
V("soc_frnd_nl_help", "soc", "Received practical help from this native Dutch friend in the past three months", s04="NLHULP", valueset="yesno", yn12=True,
  universe="Respondents with a migration background who have a native Dutch friend or acquaintance (LAS 2004/05)")
V("soc_frnd_nl_advice", "soc", "Received good advice from this native Dutch friend in the past three months", s04="NLRAAD", valueset="yesno", yn12=True,
  universe="Respondents with a migration background who have a native Dutch friend or acquaintance (LAS 2004/05)")
V("soc_frnd_org_freq", "soc", "Frequency of contact in the past 12 months with a self-chosen friend or acquaintance of the own origin group", s04="VRIEALL", valueset="freq7_frnd",
  universe="All respondents (LAS 2004/05; natives with contact with persons with a migration background were asked about such a friend)")
V("soc_frnd_org_help", "soc", "Received practical help from this own-group friend in the past three months", s04="ALLHULP", valueset="yesno", yn12=True,
  universe="Respondents who have such a friend or acquaintance (LAS 2004/05)")
V("soc_frnd_org_advice", "soc", "Received good advice from this own-group friend in the past three months", s04="ALLRAAD", valueset="yesno", yn12=True,
  universe="Respondents who have such a friend or acquaintance (LAS 2004/05)")
A("soc_leis_oth", S04, "VRTIJDAN", u=U04M)
A("soc_grp_most", S04, "ANVEEL", u="Respondents with leisure contact with other minority groups (LAS 2004/05)")
A("iden_scale", S04, "ZELFID", u=U04M)
A("lang_nl_prtnr", S04, "TAALPART", u="Respondents with a migration background living with a partner (LAS 2004/05)")
A("lang_nl_chd", S04, "TAALKIND", u="Respondents with a migration background who have children (LAS 2004/05)")
A("lang_prob_spk", S04, "TAALGESP", pairs=[(1, 1), (2, 2), (3, 3)], u=U04M, note="'vaak moeite / spreekt geen Nederlands' is one category in LAS")
A("lang_prob_read", S04, "TAALKRAN", u=U04M)

# ---- attitudes
for t, src in [("att_chd_frnd_orig", "AFKVRIKI"), ("att_chd_prtnr_orig", "AFKPARKI"), ("att_gr02", "VRWHUISH"), ("att_gr03", "MANGELD"), ("att_gr06", "INKJONGS"),
               ("att_gr07", "VRWSTOPW"), ("att_rel04", "RELIGSCH"), ("att_rel02", "GEENRELD"), ("att_fam10", "OUDZRG"), ("att_sat_nl10", "TEVRNED"),
               ("hlth_happy5", "GELUK"), ("att_soc10", "ALLTAAL"), ("att_soc09", "ALLCUL"), ("att_isl02", "ISLNEGA"), ("att_isl10", "ISLSCHL"),
               ("att_isl11", "ISLSPREI"), ("att_hom02", "HOMHUW"), ("att_hom01", "HOMLEV"), ("rel_id01", "RELZELF"), ("rel_id02", "RELKWET"), ("rel_id04", "RELTWIJF"),
               ("rel_rule", "ISLREGEL"), ("rel_veil_should", "HOOFDBUI"), ("pol_vote_int", "STEMINT"), ("soc_trust_gen", "VERTW")]:
    A(t, S04, src)
M("pol_vote_int", S04, "STEMINT", 5, 5, "'Wil niet zeggen' is a printed answer option (VRAAG 286), kept as 5 'prefers not to say' like SIM 2020; generic refusal codes of other surveys are .b")
for t in ["att_chd_frnd_orig", "att_chd_prtnr_orig", "att_gr02", "att_gr03", "att_gr06", "att_gr07", "att_rel04", "att_rel02", "att_fam10", "att_sat_nl10", "hlth_happy5",
          "att_soc10", "att_soc09", "att_hom02", "att_hom01", "pol_vote_int", "soc_trust_gen"]:
    U(t, S04, U04)
for t in ["att_isl02", "att_isl10", "att_isl11", "rel_rule", "rel_veil_should"]:
    U(t, S04, U04MU)
for t in ["rel_id01", "rel_id02", "rel_id04"]:
    U(t, S04, U04R)
W("att_fam10", "LAS 2004/05: 'Kinderen horen hun ouders op leeftijd te verzorgen'.")
W("att_soc09", "LAS 2004/05: 'Allochtonen moeten niet te veel vasthouden aan hun eigen cultuur en gewoonten' (SIM 2006/2011: 'loslaten').")
W("rel_veil_should", "LAS 2004/05 questionnaire (VRAAG 300): 'Ik vind dat moslimvrouwen en -meisjes in Nederland buitenshuis een hoofddoek moeten dragen' (the data label shortens this to 'Moslimmeisjes'); SIM 2006/2011: 'moslimvrouwen ... als ze naar buiten gaan'.")
W("att_isl10", "LAS 2004/05 questionnaire (VRAAG 300): 'Ik vind dat <groep> kinderen in Nederland naar een islamitische school moeten' - the data label 'Mijn kinderen moeten naar Islamitische school kunnen' is a shortened label, not the question as printed; SIM 2006: '... naar een islamitische basisschool moeten gaan'. The remaining difference is 'school' vs 'basisschool', not 'my children' vs 'children of the group'.")
V("att_gr11", "att", "Men and women should work the same number of hours outside the home (agreement)", s04="URENID", valueset="agree5", universe=U04)
V("att_gr12", "att", "A woman should accept it if her husband does not want her to work (agreement)", s04="ACCNW", valueset="agree5", universe=U04)
V("att_gr13", "att", "Husband and wife should talk about the division of tasks (agreement)", s04="PRATEN", valueset="agree5", universe=U04)
V("att_fam20", "att", "Professional carers can never help as well as family (agreement)", s04="EIGFAM", valueset="agree5", universe=U04)
V("att_hom05", "att", "A problem if my child were taught by a homosexual teacher (agreement)", s04="HOMLER", valueset="agree5", universe=U04)
V("att_int_pace", "att", "How far most migrants in the Netherlands are integrated", s04="ALLINB", valueset="pace3", universe=U04)
V("att_admit01", "att", "Government should be strict in granting a residence permit to: political refugees", s04="VERBLPOL", valueset="strict3", universe=U04)
V("att_admit02", "att", "Government should be strict in granting a residence permit to: people coming for economic reasons", s04="VERBLEC", valueset="strict3", universe=U04)
V("att_admit03", "att", "Government should be strict in granting a residence permit to: a legal resident's wife from abroad", s04="VERBLVR", valueset="strict3", universe=U04)
V("att_admit04", "att", "Government should be strict in granting a residence permit to: someone with an occupation needed in NL", s04="VERBLBER", valueset="strict3", universe=U04)
V("att_asylum_expel", "att", "A rejected asylum seeker should be expelled from the country", s04="ASIELUIT", valueset="expel3", universe=U04)
V("att_asylum_stay", "att", "Main reason a rejected asylum seeker may stay", s04="ASIELBLI", valueset="asylum_stay7",
  universe="Respondents who think rejected asylum seekers may (sometimes) stay (LAS 2004/05)")
for t, src in [("att_therm01", "TEMPMAR"), ("att_therm02", "TEMPTUR"), ("att_therm03", "TEMPANT"), ("att_therm04", "TEMPSUR"), ("att_therm06", "TEMPAUT")]:
    A(t, S04, src, u="All respondents except the group itself (LAS 2004/05)")
V("att_therm10", "att", "Feeling thermometer towards the own cultural group (0 very negative - 100 very positive)", s04="TEMPALL", type="num", universe=U04)
A("att_isl03", S04, "NLRESP", u=U04TM); A("att_isl04", S04, "WESTLEEF", u=U04TM); A("att_isl05", S04, "NLVROU", u=U04TM); A("att_isl06", S04, "NLKIND", u=U04TM)
A("att_isl07", S04, "MOSLRESP", u=U04N); A("att_isl01", S04, "MOSLLEEF", u=U04N); A("att_isl08", S04, "MOSLVRW", u=U04N); A("att_isl09", S04, "MOSLKIND", u=U04N)
V("pol_interest4", "pol", "Interest in politics (4-point)", s04="POLINT", valueset="interest4_asc", universe=U04)
A("pol_interest_where", S04, "POLTYP1|POLTYP2", u="Respondents interested in politics (LAS 2004/05; natives: Dutch / international / both, POLTYP2)")
A("pol_news_cat", S04, "POLNWS", pairs=[(1, 1), (2, 2), (3, 4), (4, 4), (5, 5)], u=U04, note="'een of twee keer per maand' and 'minder vaak' -> less than once a week")
W("pol_news_cat", "LAS 2004/05 scale: every day / several times a week / once or twice a month / less often / never (no 'once a week' category).")
A("pol_party", S04, "STEMWS", pairs=[(1, 3), (2, 7), (3, 1), (4, 4), (5, 18), (6, 6), (7, 5), (8, 8), (9, 11), (10, 92), (11, 15), (12, 17), (13, 16), (14, ".b")],
  u="Respondents who would (maybe) vote (LAS 2004/05)")
V("pol_eff01", "pol", "People like me have no influence on the Dutch government (agreement)", s04="INVREG", valueset="agree5", universe=U04)
V("pol_eff02", "pol", "Ministers are mainly out for their own interests (agreement)", s04="MINBEL", valueset="agree5", universe=U04)
V("pol_eff03", "pol", "The Dutch government does enough for the prosperity of people like me (agreement)", s04="REGWELV", valueset="agree5", universe=U04)
V("pol_dem01", "pol", "Democracy is better than any other form of government (agreement)", s04="DEMO", valueset="agree5", universe=U04)
V("pol_dem02", "pol", "Better for NL if the government were left to a few strong leaders (agreement)", s04="LEIDERS", valueset="agree5", universe=U04)
V("att_vangogh", "att", "Started thinking differently because of the murder of Theo van Gogh (2 Nov 2004)", s04="TVGVERH", valueset="yesno", yn12=True,
  universe="Respondents interviewed after 2 November 2004 (LAS 2004/05)")
SKIP(S04, "TVGWAT", "open answer (consequences of the Van Gogh murder) removed from the deposit: empty")
SKIP(S04, "TVGHOE", "open answer (what changed) removed from the deposit: empty")
SKIP(S04, "TVGWELK", "open answer (consequences) removed from the deposit: empty")

# ---- cultural and leisure participation (past 12 months)
_CUL = "All respondents (LAS 2004/05)"
for t, src, nm in [("cul_theatre_n", "FQTONEEL", "theatre or dance performances"), ("cul_classical_n", "FQKLAS", "classical music or opera"), ("cul_cabaret_n", "FQCAB", "cabaret"),
                   ("cul_pop_n", "FQPOP", "pop, rock, blues, rai or jazz concerts"), ("cul_dance_n", "FQDANCE", "dance / house parties"), ("cul_musical_n", "FQMUSI", "musicals"),
                   ("cul_film_n", "FQFILM", "films (cinema)"), ("cul_party_music_n", "FQOPMUZ", "parties with performing musicians"),
                   ("cul_party_other_n", "FQOPAND", "parties with cabaret or dance performances"), ("cul_museum_n", "FQMUSE", "museums in NL"),
                   ("cul_sights_n", "FQGEBOUW", "notable buildings, towns or villages in NL"), ("cul_picnic_n", "FQPARK", "picnics or barbecues outdoors"),
                   ("cul_teahouse_n", "FQKOFFIE", "tea or coffee houses in NL"), ("cul_restaurant_n", "FQREST", "restaurants or cafes in NL")]:
    V(t, "cul", f"Number of visits in the past 12 months: {nm}", s04=src, type="num",
      universe="Turkish and Moroccan respondents (LAS 2004/05; VRAAG 189 'INDIEN TURKS, MAROKKAANS')" if t == "cul_teahouse_n" else _CUL)
    M(t, S04, src, 98, ".d", "more than 100 times"); M(t, S04, src, 998, ".d", "more than 1000 times"); M(t, S04, src, 99, ".a"); M(t, S04, src, 999, ".a")
V("cul_books_n", "cul", "Number of books read in leisure time in the past 12 months", s04="FQBOEK", type="num", universe=_CUL)
M("cul_books_n", S04, "FQBOEK", 998, ".d", "more than 1000"); M("cul_books_n", S04, "FQBOEK", 999, ".a")
V("cul_library_n", "cul", "Number of visits to a public library for oneself in the past 12 months", s04="FQBIBL", type="num", universe=_CUL)
M("cul_library_n", S04, "FQBIBL", 998, ".d", "more than 1000"); M("cul_library_n", S04, "FQBIBL", 999, ".a")
V("cul_film_type", "cul", "Character of the last film seen", s04="FILMTYP", valueset="ethmix5_las", universe="Respondents who went to the cinema (LAS 2004/05)")
V("cul_party_type", "cul", "Character of the performance at the last party", s04="FEESTTYP", valueset="ethmix5_las", universe="Respondents who went to a party with performances (LAS 2004/05)")
V("cul_party_pub", "cul", "Background of the audience at the last party", s04="FEESTPUB", valueset="ethmix5_las", universe="Respondents who went to a party with performances (LAS 2004/05)")
V("cul_museum_hist", "cul", "Visited a historical museum", s04="HISTMUSE", valueset="yesno", yn12=True, universe="Respondents who visited a museum (LAS 2004/05)")
V("cul_museum_art", "cul", "Visited an art museum", s04="KNSTMUSE", valueset="yesno", yn12=True, universe="Respondents who visited a museum (LAS 2004/05)")
V("cul_book_lang", "cul", "Language of the last book read", s04="TAALBOEK", valueset="lang3", universe="Turkish and Moroccan respondents who read books (LAS 2004/05)")
V("cul_library_lang", "cul", "Language of the material read at the library", s04="TAALBIBL", valueset="lang_mix6", universe="Respondents with a migration background who visit the library (LAS 2004/05)")
for stem, src_n, src_org, src_w, nm in [("draw", "FQHANDV", "HANDVTYP", "V185_1", "drawing, painting, sculpting"), ("music", "FQMUZ", "MUZTYP", "V185_2", "singing or playing a musical instrument"),
                                       ("drama", "FQDANS", "DANSTYP", "V185_3", "theatre, dance or ballet"), ("pc", "FQCOMP", "COMPTYP", "V185_4", "making music or graphic design on the computer")]:
    V(f"cul_{stem}_n", "cul", f"Number of times in the past 12 months: {nm} (own leisure activity)", s04=src_n, type="num", universe=_CUL)
    M(f"cul_{stem}_n", S04, src_n, 998, ".d", "more than 1000"); M(f"cul_{stem}_n", S04, src_n, 999, ".a")
    V(f"cul_{stem}_org", "cul", f"{nm.capitalize()}: alone or in an organised setting", s04=src_org, valueset="alone_org2", universe=f"Respondents who do this activity (LAS 2004/05)")
    for i, where in enumerate(["community centre", "mosque / church", "group of friends", "association", "school for the arts", "other"], start=1):
        V(f"cul_{stem}_w{i:02d}", "cul", f"{nm.capitalize()} in an organised setting: {where} (mentioned)", s04=f"{src_w}_{i}", valueset="mentioned",
          universe=f"Respondents who do this activity in an organised setting (LAS 2004/05)")
        M(f"cul_{stem}_w{i:02d}", S04, f"{src_w}_{i}", 9, ".a", "weet niet / geen antwoord (unlabelled in the pc items)")

# ---- neighbourhood, sport
A("hous_nbhd01", S04, "BRTTHUIS", u=U04)
A("hous_nbhd02", S04, "BRTPRET", u=U04)
V("hous_nbhd04", "hous", "I have a lot of contact with my direct neighbours (agreement)", s04="BRTBUUR1", valueset="agree5", universe=U04)
V("hous_nbhd05", "hous", "I have a lot of contact with other residents of the neighbourhood (agreement)", s04="BRTBUUR2", valueset="agree5", universe=U04)
V("soc_sport_n5", "soc", "Number of times practised sport in the past 12 months (classes, LAS 2004/05)", s04="FQSPORT", valueset="sport_n5", universe=U04)
A("soc_sport5", S04, "FQSPORT", pairs=[(0, 5), (1, 4), (2, 3), (3, 2), (4, 1)], u=U04, note="approximate: 12-59 times -> once a month, 60-119 -> once a week, 120+ -> twice a week or more")
W("soc_sport5", "LAS 2004/05 asked the number of times in the past 12 months in classes (soc_sport_n5); the mapping to the frequency scale is approximate.")
V("soc_sport_main", "soc", "Sport practised most", s04="SPORTSRT", valueset="sport26", universe="Respondents who practise a sport (LAS 2004/05)")
A("soc_sport_comp", S04, "SPORTTYP", yn12=True, u="Respondents who practise a sport (LAS 2004/05)")
W("soc_sport_comp", "LAS 2004/05: 'in competitie- of trainingsverband' (competition or training); SIM 2006/2011: competitions, tournaments or matches.")
V("soc_sport_mem5", "soc", "Membership for the main sport: none, sports club, sports school, fitness centre, other", s04="SPORTLID", valueset="sportmem5",
  universe="Respondents who practise a sport (LAS 2004/05)")
A("soc_sport_ethn", S04, "SPORTPUB", pairs=[(1, 2), (2, 1), (3, 3), (4, 4), (5, 5)], u="Members of a sports club (LAS 2004/05)")
W("soc_sport_ethn", "LAS 2004/05: background of the members of the sports club (voornamelijk westers / eigen groep / half-half / divers / anders).")

# ---- media and ICT
A("med_krant_nl_days", S04, "KRTNED", u=U04); A("med_krant_nl_cat", S04, "KRTNED", pairs=_D6_F5, u=U04)
A("med_krant_orig_days", S04, "NURTEIG", u=U04M); A("med_krant_orig_cat", S04, "NURTEIG", pairs=_D6_F5, u=U04M)
W("med_krant_nl_days", "LAS 2004/05 asks about newspapers only ('Nederlandse kranten'); SIM 2006 about newspapers or magazines.")
V("med_mag_nl_days", "med", "Reads Dutch magazines (days per week, 6 classes)", s04="TIJDNED", valueset="media_days6", universe=U04)
V("med_mag_orig_days", "med", "Reads origin-group magazines (days per week, 6 classes)", s04="TIJDEIG", valueset="media_days6", universe=U04M)
V("med_radio_pub_days", "med", "Listens to Dutch public radio (days per week, 6 classes)", s04="RADIOPUB", valueset="media_days6", universe=U04)
V("med_radio_com_days", "med", "Listens to Dutch commercial radio (days per week, 6 classes)", s04="RADIOCOM", valueset="media_days6", universe=U04)
V("med_radio_orig_days", "med", "Listens to origin-group radio stations (days per week, 6 classes)", s04="RADIO_OV", valueset="media_days6", universe=U04M)
V("med_tv_pub_days", "med", "Watches Dutch public television (days per week, 6 classes)", s04="TVPUB", valueset="media_days6", universe=U04)
V("med_tv_com_days", "med", "Watches Dutch commercial television (days per week, 6 classes)", s04="TVCOM", valueset="media_days6", universe=U04)
V("med_tv_loc_days", "med", "Watches local or regional television (days per week, 6 classes)", s04="TVLOK", valueset="media_days6", universe=U04)
A("med_tv_orig_days", S04, "TVEIGEN", u=U04TM); A("med_tv_orig_cat", S04, "TVEIGEN", pairs=_D6_F5, u=U04TM)
W("med_tv_orig_days", "LAS 2004/05 asked Turks and Moroccans only.")
for i, (src, nm) in enumerate([("NWS", "news"), ("FILM", "films"), ("SERIES", "television series"), ("SHOW", "shows"), ("CULT", "cultural programmes"), ("DISC", "talk shows")], start=1):
    V(f"med_ch{i:02d}", "med", f"Channels on which the respondent mostly watches {nm} (Dutch vs origin-group channels)", s04=src, valueset="channel7", universe=U04TM)
A("med_satellite", S04, "SATEL", pairs=[(1, 1), (2, 0), (3, ".a")], u=U04TM)
V("med_web_hrs_wk", "med", "Hours spent on internet / e-mail this week", s04="FQINTER", type="num", universe=U04)
M("med_web_hrs_wk", S04, "FQINTER", 98, 0, "never uses internet or e-mail"); M("med_web_hrs_wk", S04, "FQINTER", 97, ".d", "more than 100"); M("med_web_hrs_wk", S04, "FQINTER", 99, ".a")
V("med_pc_hrs_wk", "med", "Hours of other computer use this week", s04="FRQPC", type="num", universe=U04)
M("med_pc_hrs_wk", S04, "FRQPC", 98, 0, "never uses a computer"); M("med_pc_hrs_wk", S04, "FRQPC", 97, ".d", "more than 100"); M("med_pc_hrs_wk", S04, "FRQPC", 99, ".a")
V("med_pc", "med", "Has a personal computer in the household", s04="BEZITPC", valueset="yesno", yn12=True, universe=U04)
A("med_pc_internet", S04, "TOEGNIET", yn12=True, u="Respondents with a computer in the household (LAS 2004/05)")
W("med_pc_internet", "LAS 2004/05: 'mogelijkheid om thuis te internetten/e-mailen' (asked to households with a PC); SIM 2006: 'computer waarmee u kunt internetten'.")
V("med_nonet_reason", "med", "Main reason for having no computer or internet access at home", s04="NIETNET", valueset="nonet6", universe="Respondents without internet access at home (LAS 2004/05)")
M("med_nonet_reason", S04, "NIETNET", 7, ".a")
V("med_net_type", "med", "Type of internet connection at home", s04="NETTYP", valueset="nettype4", universe="Respondents with internet access at home (LAS 2004/05)")
M("med_net_type", S04, "NETTYP", 5, ".a")
for i, (src, nm) in enumerate([("V219_1", "no, not used elsewhere"), ("V219_2", "at work"), ("V219_3", "at school"), ("V219_4", "in an internet cafe"), ("V219_5", "in the library"),
                               ("V219_6", "in a community centre"), ("V219_7", "at family or friends"), ("V219_8", "in the mosque"), ("V219_9", "elsewhere")], start=1):
    V(f"med_pc_else{i:02d}", "med", f"Uses a computer elsewhere: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Respondents who use a computer (LAS 2004/05)")
for i, (src, nm) in enumerate([("NETINFO", "looking for information"), ("NETBEST", "ordering or buying"), ("NETBANK", "internet banking"), ("NETSURF", "just surfing"),
                               ("NETMAIL", "e-mail"), ("NETCHAT", "chatting")], start=1):
    V(f"med_web_use{i:02d}", "med", f"Uses the internet for: {nm}", s04=src, valueset="yesno", yn12=True, universe="Internet users (LAS 2004/05)")
A("med_email_ethn", S04, "CHATPUB", pairs=[(1, 2), (2, 1), (3, 3), (4, 4), (5, 5)], u="Respondents who e-mail or chat (LAS 2004/05)")
V("med_email_lang", "med", "Language used when e-mailing or chatting", s04="CHATTAAL", valueset="lang_mix7", universe="Respondents with a migration background who e-mail or chat (LAS 2004/05)")
A("med_web_type", S04, "SITETYPE", pairs=[(1, 1), (2, 2), (3, 3), (4, 5)], u="Internet users with a migration background (LAS 2004/05)")
V("med_digital_outsider", "med", "Feels an outsider when people talk about computers (agreement)", s04="DIGIBEET", valueset="agree5", universe=U04)

# ---- associations, voluntary work, charity
for i, (src, nm) in enumerate([("SPORTACT", "sports club"), ("VRIJTACT", "leisure organisation"), ("BRTACT", "neighbourhood or tenants' association"),
                               ("VAKACT", "trade union or professional organisation"), ("ALLOACT", "organisation of or for migrants"), ("POLACT", "political party or organisation"),
                               ("GELACT", "religious organisation"), ("NATACT", "nature, environment or solidarity organisation")], start=1):
    V(f"soc_mem_act{i:02d}", "soc", f"How active as a member of the {nm}", s04=src, valueset="active3", universe=f"Members of a {nm} (LAS 2004/05)")
    M(f"soc_mem_act{i:02d}", S04, src, 4, ".a")
for i, (src, nm) in enumerate([("V229_1", "sports club"), ("V229_2", "leisure organisation"), ("V229_3", "neighbourhood or tenants' association"),
                               ("V229_4", "trade union or professional organisation"), ("V229_5", "organisation of or for migrants"), ("V229_6", "political party or organisation"),
                               ("V229_7", "religious organisation"), ("V229_8", "nature, environment or solidarity organisation"), ("V229_9", "other organisation")], start=1):
    V(f"soc_vol{i:02d}", "soc", f"Does voluntary work for: {nm} (mentioned)", s04=src, valueset="mentioned", universe=U04)
for i, (src, nm) in enumerate([("V230_1", "board member"), ("V230_2", "committee member"), ("V230_3", "training / coaching"), ("V230_4", "referee / jury member"),
                               ("V230_5", "helping at events"), ("V230_6", "helping in the canteen"), ("V230_7", "cleaning"), ("V230_8", "other activities")], start=1):
    V(f"soc_vol_sport{i:02d}", "soc", f"Voluntary work for the sports club: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Volunteers at a sports club (LAS 2004/05)")
A("soc_volunteer", S04, "VRWWAND", yn12=True, u=U04)
V("soc_vol_ethn", "soc", "Background of the people among whom the voluntary work is done", s04="VRWWPUB", valueset="ethmix5_las", universe="Volunteers (LAS 2004/05)")
A("soc_act_ethn", S04, "BETROK", pairs=[(1, 2), (2, 1), (3, 3), (4, 4), (5, 5)], u="Respondents involved in an organisation (LAS 2004/05; organisation they are most involved in)")
V("soc_charity", "soc", "Gives money to charity (often / sometimes / never)", s04="GDOEL", valueset="freq3", universe=U04)

# ---- safety and victimisation
A("saf_unsafe", S04, "ONVALG", yn12=True, u=U04)
A("saf_unsafe_freq", S04, "FQONV", u="Respondents who sometimes feel unsafe (LAS 2004/05)")
A("saf_unsafe_street", S04, "ONVSTRT", u=U04); A("saf_unsafe_home", S04, "ONVHUIS", u=U04)
W("saf_unsafe_street", "LAS 2004/05 third category: 'zelden/nooit'; SIM 2006: 'zelden'.")
V("saf_burglary_risk", "saf", "Perceived chance of a burglary in own home", s04="KANSINB", valueset="risk3", universe=U04)
for stem, s5, s12, nm in [("burglary", "INB", "FQINB", "burglary"), ("assault", "AANV", "FQAANV", "assault / maltreatment"), ("threat", "BEDR", "FQBEDR", "threat"),
                          ("biketheft", "FIE", "FQFIE", "bicycle theft"), ("cartheft", "AUT", "FQAUT", "theft from a car"), ("pickpocket", "TAS", "FQTAS", "theft from bag or clothing"),
                          ("vandalism", "VERN", "FQVERN", "vandalism")]:
    V(f"saf_vic_{stem}5y", "saf", f"Victim of {nm} in the past five years", s04=s5, valueset="yesno", yn12=True, universe=U04 if stem != "cartheft" else "Respondents aged 18 or older (LAS 2004/05)")
    V(f"saf_vic_{stem}12m", "saf", f"Victim of {nm} in the past 12 months", s04=s12, valueset="yesno", yn12=True, universe=f"Victims of {nm} in the past five years (LAS 2004/05)")

# ---- informal care and health
V("hlth_care_willing", "hlth", "Willing to give long-term help to close family members", s04="HLPG", valueset="willing4", universe=U04)
V("hlth_care_give_hrs", "hlth", "Hours of unpaid help given per week", s04="UURHLPG", type="num", universe="Respondents who give unpaid help (LAS 2004/05)")
M("hlth_care_give_hrs", S04, "UURHLPG", 98, ".d", "more than 100"); M("hlth_care_give_hrs", S04, "UURHLPG", 99, ".a")
for i, (src, nm) in enumerate([("V249_1", "co-resident partner"), ("V249_2", "other household members"), ("V249_3", "parents living elsewhere"), ("V249_4", "other family living elsewhere"),
                               ("V249_5", "others")], start=1):
    V(f"hlth_care_give_to{i:02d}", "hlth", f"Gives unpaid help to: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Respondents who give unpaid help (LAS 2004/05)")
for i, (src, nm) in enumerate([("V250_1", "domestic help"), ("V250_2", "personal care"), ("V250_3", "guidance, running the household"), ("V250_4", "administration, filling in forms")], start=1):
    V(f"hlth_care_give_type{i:02d}", "hlth", f"Type of unpaid help given: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Respondents who give unpaid help (LAS 2004/05)")
V("hlth_care_rcv_reg", "hlth", "Regularly receives unpaid help", s04="HLPO", valueset="yesno", yn12=True, universe="Respondents in multi-person households (LAS 2004/05)")
for i, (src, nm) in enumerate([("V253_1", "parents or parents-in-law"), ("V253_2", "other family members"), ("V253_3", "neighbours"), ("V253_4", "friends")], start=1):
    V(f"hlth_care_rcv_from{i:02d}", "hlth", f"Receives unpaid help from: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Respondents who receive unpaid help (LAS 2004/05)")
V("hlth_care_rcv_hrs", "hlth", "Hours of unpaid help received per week", s04="HLPOUUR", type="num", universe="Respondents who receive unpaid help (LAS 2004/05)")
M("hlth_care_rcv_hrs", S04, "HLPOUUR", 98, ".d", "more than 100"); M("hlth_care_rcv_hrs", S04, "HLPOUUR", 99, ".a")
for i, (src, nm) in enumerate([("V255_1", "cleaning"), ("V255_2", "washing and/or ironing"), ("V255_3", "cooking"), ("V255_4", "shopping"), ("V255_5", "other")], start=1):
    V(f"hlth_care_rcv_type{i:02d}", "hlth", f"Type of unpaid help received: {nm} (mentioned)", s04=src, valueset="mentioned", universe="Respondents who receive unpaid help (LAS 2004/05)")
    M(f"hlth_care_rcv_type{i:02d}", S04, src, 9, ".a", "weet niet / geen antwoord (unlabelled)")
V("hlth_dom_help_paid", "hlth", "Has a paid domestic help", s04="HLBO", valueset="yesno", yn12=True, universe="Respondents in multi-person households (LAS 2004/05)")
A("hlth_chronic", S04, "HANDI", yn12=True, u=U04)
A("hlth_lim3", S04, "BELEM", u="Respondents with a long-term condition or handicap (LAS 2004/05)")
A("hlth_self", S04, "GEZONDH", u=U04)

# ---- religion
A("rel_any", S04, "RELIGIE", pairs=[(-5, 0)] + [(c, 1) for c in range(1, 18)], u=U04, note="-5 = does not belong to a religion")
W("rel_any", "LAS 2004/05: derived from the denomination question (code 'niet van toepassing' = no religion).")
A("rel_den_det", S04, "RELIGIE", pairs=[(-5, 0), (1, 11), (2, 12), (3, 13), (4, 21), (5, 22), (6, 23), (7, 24), (8, 25), (9, 31), (10, 32), (11, 33), (12, 39), (13, 34), (14, 35),
                                        (15, 36), (16, 38), (17, 99)], u=U04)
A("rel_den_cat", S04, "RELIGIE", pairs=[(-5, 0), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 3), (10, 3), (11, 3), (12, 3), (13, 3), (14, 3), (15, 3), (16, 3), (17, 4)], u=U04)
A("rel_attend", S04, "KERKBEZ", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 4), (6, 4)], u=U04R)
A("rel_attend5", S04, "KERKBEZ", pairs=[(1, 5), (2, 4), (3, 3), (4, 2), (5, 2), (6, 1)], u=U04R)
V("rel_attend6", "rel", "Attendance of religious meetings, 6 categories (LAS 2004/05)", s04="KERKBEZ", valueset="attendance6", universe=U04R)
A("rel_pray", S04, "GEBED", pairs=[(1, 6), (2, 5), (3, 4), (4, 3), (5, 3), (6, 2), (7, 2), (8, 1)], u=U04MU)
A("rel_pray7", S04, "GEBED", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 6), (8, 7)], u=U04MU, note="'elke dag' and 'in elk geval iedere dag' both -> every day")
A("rel_ramadan", S04, "RAMADAN", pairs=[(1, 4), (2, 3), (3, 2), (4, 1)], u=U04MU)
A("rel_veil", S04, "ZHFDDOEK", pairs=[(1, 1), (2, 0)], u="Women with a migration background (LAS 2004/05; observed by the interviewer)")
W("rel_veil", "LAS 2004/05: interviewer observation ('respondent draagt hoofddoek'); SIM: self-report.")

# ---- time use: attitudes and the one-day diary
for i, (src, nm) in enumerate([("LEV5JR", "I have a clear picture of what my life will look like in five years"), ("PLANACT", "I like to plan my activities in advance"),
                               ("LEEFNK", "I live in the present and do not think too much about the future"), ("HORLOGE", "I could not do without my watch"),
                               ("TELAAT", "I get annoyed when someone is a quarter of an hour late for an appointment"), ("TDTKORT", "I am always short of time"),
                               ("VASTET", "I have a fixed moment for many things"), ("VRIJBEP", "I want to decide myself when I do something"),
                               ("WINKZON", "It is good if shops are open on Sundays too"), ("WINKLANG", "Shops, hairdressers and banks should be open longer")], start=1):
    V(f"tim_att{i:02d}", "tim", f"Time orientation: {nm} (agreement)", s04=src, valueset="agree5", universe=U04)
V("tim_date_day", "tim", "Diary day: day of the month", s04="DATDAG", type="num", universe=U04D)
V("tim_date_month", "tim", "Diary day: month (October-December 2004 or January-June 2005)", s04="DATMND", valueset="month", universe=U04D)
V("tim_weekday", "tim", "Diary day: day of the week", s04="DAG", valueset="weekday7", universe=U04D)
M("tim_weekday", S04, "DAG", 0, ".c")        # 0 = no diary completed
V("tim_short", "tim", "Felt short of time yesterday (diary day)", s04="TEKORT", valueset="time_short3", universe=U04)
V("tim_wgt", "tim", "Weight for the diary respondents", s04="WEEGDAG", type="num", universe=U04D)
V("tim_wgt_corr", "tim", "Correction weight for the diary respondents (weekday distribution)", s04="WEEGDAGC", type="num", universe=U04D)
for i in range(1, 73):
    h0, m0 = divmod(6 * 60 + (i - 1) * 15, 60); h1, m1 = divmod(6 * 60 + i * 15, 60)
    V(f"tim_slot{i:02d}", "tim", f"Diary: main activity {h0:02d}:{m0:02d}-{h1:02d}:{m1:02d}", s04=f"K{i:02d}01", valueset="act43", universe=U04D)
_ACT = [l for _, l in VALUESETS["act43"]]
for i in range(1, 44):
    V(f"tim_act{i:02d}", "tim", f"Diary: hours spent on {_ACT[i - 1][0].lower() + _ACT[i - 1][1:]} (06:00-24:00)", s04=f"AKT{i:02d}", type="num", universe=U04D)


# ====================================================================================================== SING 2009
# Survey Integratie Nieuwe Groepen (SCP/Veldkamp, 2009): Afghans, Iraqis, Iranians, Somalis, Poles, Chinese and a native
# Dutch reference sample, 6,911 respondents.  The DANS file is the CBS-protected public version: 242 of the questionnaire
# variables, years and durations in classes, no identifier (impd_rownum).  Missing codes are positive and labelled per
# variable (6/7/96/97 'geen antwoord / wil niet zeggen', 7/8/96 'weet niet', 8/9/98/99/998/999 'niet van toepassing',
# 9 = native sample for migrant-only items); they are caught by label rules.  System-missing = routed (sysmis_tag = c).
U09 = "All respondents (SING 2009)"
U09M = "Respondents with a migration background (SING 2009)"
U09G1 = "First-generation respondents (SING 2009)"
U09R = "Refugee groups: Afghan, Iraqi, Iranian and Somali respondents (SING 2009)"
U09P = "Respondents with a partner (SING 2009)"
U09PC = "Respondents living with a partner (SING 2009)"
U09W = "Employed respondents (SING 2009)"
U09REL = "Religious respondents (SING 2009)"
U09MU = "Muslim respondents (SING 2009)"
_YR5 = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]

# ---- survey administration, weights
A("svy_wgt", S09, "WEEGHERK", u="All respondents (SING 2009; weight within origin group, the only weight in the deposit)")
A("svy_wgt_grp", S09, "WEEGHERK", u=U09)
V("svy_wgt_pool", "svy", "Weight for the sample of short-stay Poles (SING 2009)", s09="WEEGPOOL", type="num", universe="Short-stay Polish respondents (SING 2009)")
A("svy_parent_q", S09, "VROUDER", u="Respondents aged 15-17 (SING 2009)")

# ---- demography and household
A("dem_eth", S09, "ETNGRP", pairs=[(1, 5), (2, 6), (3, 7), (4, 9), (5, 10), (6, 11), (7, 90), (9, 99)])
A("dem_gen", S09, "GENERAT|ETNGRP", pairs={"GENERAT": [(9, ".d")], "ETNGRP": [(7, 0), (1, ".c"), (2, ".c"), (3, ".c"), (4, ".c"), (5, ".c"), (6, ".c"), (9, ".c")]},
  note="GENERAT 9 'niet van toepassing' covers the native sample (-> 0 via ETNGRP) and 42 migrants without generation information (-> .d)")
V("mig_dur_nl_cat4", "mig", "Years of residence in the Netherlands, 4 classes (SING 2009)", s09="VERBLIJF", valueset="dur_cat4", universe=U09G1)
A("dem_sex", S09, "GESLACHT", pairs=[(9, ".d")])
V("dem_age_cat3", "dem", "Age in 3 classes (15-24, 25-44, 45+): common coarse age variable of all surveys", s09="LFTCAT3", valueset="age_cat3", universe="All persons aged 15 or older (SING 2009: as delivered; other surveys: derived from dem_age_cat; persons under 15 in the SPVA/SPVN rosters are .c)", derive="age_cat3",
  notes="SING 2009 delivers age in these three classes only; for the other surveys the classes are cut from dem_age_cat (itself from exact age or the delivered 5-/10-year classes), so every survey has this coarse control while dem_age / dem_age_cat keep the finer detail where it exists.")
M("dem_age_cat3", S09, "LFTCAT3", 9, ".d")   # 11 unlabelled 9s (age unknown)
A("dem_mar", S09, "BURGST", pairs=[(9, ".d")])
A("geo_urb_reg", S09, "STED", pairs=[(9, ".d")], u=U09)
A("lab_lf3", S09, "BB_NED", pairs=[(9, ".d")], u=U09)
A("lab_lf", S09, "BB_NED", pairs=[(1, 1), (2, 1), (3, 0), (9, ".d")], u=U09)
A("edu_dipl_cur_cat", S09, "MAXDIPN1", pairs=[(9, ".d")], u=U09)
A("hh_size", S09, "GEZOMV", pairs=[(99, ".d")], u=U09, note="6 = six or more")
W("hh_size", "SING 2009 (CBS-protected deposit): 6 = six or more persons.")
A("dem_prtnr_st", S09, "LATPART|SAMPART", pairs={"LATPART": [(1, 4), (2, 0)], "SAMPART": [(1, 1), (2, 3), (3, 2), (4, 0)]}, u="Respondents in multi-person households (SING 2009)")
V("dem_hhpos3", "dem", "Position in the household: head (male or female), co-resident child, other (SING 2009)", s09="POSGEZIN", valueset="hhpos3",
  universe="Respondents in multi-person households (SING 2009)")
A("dem_prtnr_lat", S09, "LATPART", pairs=[(1, 1), (2, 2)], u="Respondents not married or cohabiting (SING 2009)")
A("dem_prtnr_reun", S09, "KOMPART", u="Respondents whose partner lives abroad (SING 2009)")
V("dem_prtnr_reun_when", "dem", "Expected time until the partner will live in the Netherlands", s09="KOMPADU", valueset="when5", universe="Respondents who plan to bring their partner to the Netherlands (SING 2009)")
M("dem_prtnr_reun_when", S09, "KOMPADU", 5, ".a")
V("dem_mar_yr_cat", "dem", "Year of marriage / registered partnership, classes (SING 2009 public file)", s09="HUWJAARC", valueset="yr_cat7_mar", universe="Married respondents (SING 2009)")
M("dem_mar_yr_cat", S09, "HUWJAARC", 9999, ".d")
V("dem_prtnr_age_cat3", "dem", "Age of the partner in 3 classes (SING 2009 public file)", s09="LFTPARTC", valueset="age_cat3", universe=U09P)
M("dem_prtnr_age_cat3", S09, "LFTPARTC", 9, ".d")
A("dem_prtnr_eth", S09, "ETNGRPPA", pairs=[(1, 5), (2, 6), (3, 7), (4, 9), (5, 10), (6, 11), (7, 90), (8, 95), (9, ".d")], u=U09P)
A("dem_prtnr_gen", S09, "GENPART", u="Respondents with a partner (SING 2009; partners of native Dutch respondents are coded by the same rule, so a native partner born in the Netherlands appears as second generation)")
A("dem_nchd", S09, "AANTKIND", u="Respondents with children (SING 2009)", note="6 = six or more")
A("dem_nchd_home", S09, "INWKIND", u="Respondents with children (SING 2009)", note="6 = six or more")
A("dem_chd_res", S09, "KINDNL", u="Respondents with children not (all) living at home (SING 2009)")
A("dem_chd_reun", S09, "KOMKIND", u="Respondents with children living abroad (SING 2009)")
A("hh_noth", S09, "AANTAND", pairs=[(99, ".d")], u=U09)
for i in range(1, 9):
    V(f"hh_oth_rel{i:02d}", "hh", f"Relation to the respondent of other household member {i} (not partner or child)", s09=f"AND{i}POS", valueset="oth_rel11",
      universe="Respondents with other persons in the household (SING 2009)")

# ---- migration history, asylum reception, residence status
V("mig_yr_dep_cat", "mig", "Year of leaving the country of origin, classes (SING 2009 public file)", s09="JRLVHC", valueset="yr_cat5", universe=U09G1)
A("mig_reason", S09, "REDMIGR", pairs=[(1, 4), (2, 4), (3, 4), (4, 19), (5, 18), (6, 14), (7, 6), (8, 5), (9, 11), (10, 1), (11, 11), (12, 2), (13, 8), (98, 10)], u=U09G1)
W("mig_reason", "SING 2009 distinguishes political reasons, war and conscription (all mapped to 4), religious persecution (19) and invitation by the Dutch government (18).")
A("mig_transit", S09, "ANDLAND", pairs=[(1, 0), (2, 1)], u=U09G1, note="1 direct naar Nederland gekomen -> 0, 2 eerst elders gewoond -> 1 (not a yes/no item: the first option is the direct route)")
V("mig_yr_arr_cat5", "mig", "Year of first arrival in the Netherlands, classes (SING 2009 public file; asked when not directly from the origin country)", s09="MIGRJAAC", valueset="yr_cat5",
  universe="First-generation respondents who lived elsewhere before coming to the Netherlands (SING 2009)")
V("asy_rec_ever", "asy", "Ever lived in a reception centre for asylum seekers", s09="OPVANG", valueset="yesno", yn12=True, universe=U09R)
V("asy_n_centres", "asy", "Number of reception centres lived in (10 = ten or more)", s09="AANTOPVC", type="num", universe="Refugee-group respondents who lived in a reception centre (SING 2009)")
MM("asy_n_centres", S09, "AANTOPVC", [(i, i - 1) for i in range(1, 12)])
V("asy_dur_cat", "asy", "Total time in reception centres, classes", s09="DUUROPVC", valueset="months_cat6", universe="Refugee-group respondents who lived in a reception centre (SING 2009)")
V("mig_prev_nl", "mig", "Lived in the Netherlands before for a period of more than three months", s09="EERDERNL", valueset="yesno", yn12=True,
  universe="Polish respondents (SING 2009)")
V("mig_prev_nl_n", "mig", "Number of earlier periods in the Netherlands", s09="AANTXNL", type="num", universe="Polish respondents who lived in the Netherlands before (SING 2009)")
for i in range(1, 11):
    V(f"mig_prev_dur{i:02d}", "mig", f"Length of earlier stay {i} in the Netherlands (as recorded)", s09=f"NL{i}DUUR", type="num", universe="Polish respondents who lived in the Netherlands before (SING 2009)")
    V(f"mig_prev_yr{i:02d}", "mig", f"Year of earlier stay {i} in the Netherlands", s09=f"NL{i}JAAR", type="year", universe="Polish respondents who lived in the Netherlands before (SING 2009)")
V("mig_prev_weur", "mig", "Lived in another Western European country for more than three months", s09="ANDWEUR", valueset="yesno", yn12=True, universe="Polish respondents (SING 2009)")
A("mig_reason_prtnr", S09, "REDMI_PA", pairs=[(1, 4), (2, 4), (3, 4), (4, 19), (5, 18), (6, 14), (7, 6), (8, 5), (9, 11), (10, 1), (11, 11), (13, 8), (14, 10), (97, 10)],
  u="Respondents whose partner was born abroad (SING 2009)")
V("mig_yr_arr_prtnr_cat", "mig", "Year the partner came to the Netherlands, classes (SING 2009 public file)", s09="MIGRVAPC", valueset="yr_cat6_prtnr",
  universe="Respondents whose partner was born abroad (SING 2009)")
V("nat_perm_yr_cat", "nat", "Year the current residence document was obtained, classes (SING 2009 public file)", s09="JRDOCC", valueset="yr_cat5_doc",
  universe="Refugee-group respondents with a residence document (SING 2009)")
V("nat_perm_first", "nat", "Current status is the first status / residence permit in the Netherlands", s09="STATUS1", valueset="yesno", yn12=True,
  universe="Refugee-group respondents with a residence document (SING 2009)")
V("nat_perm1_yr_cat", "nat", "Year of the first status / residence permit, classes (SING 2009 public file)", s09="JRSTAT1C", valueset="yr_cat5_stat",
  universe="Refugee-group respondents (SING 2009)")

# ---- civic integration
A("int_crs", S09, "INBCURUS", pairs=[(1, 1), (2, 1), (3, 0)], u=U09M)
A("int_crs_st", S09, "INBCURUS", u=U09M)
A("int_crs_noreason", S09, "REDGEINB", pairs=[(7, 8)], u="Respondents with a migration background who did not follow a civic integration programme (SING 2009)")
A("int_crs_yr", S09, "JRINBST", u="Respondents who followed a civic integration programme (SING 2009)")
A("int_crs_sat", S09, "TEVRINB", u="Respondents who followed a civic integration programme (SING 2009)")
A("int_eff01", S09, "INBTAAL", u="Respondents who followed a civic integration programme (SING 2009)")
A("int_eff02", S09, "INBWERK", u="Respondents who followed a civic integration programme (SING 2009)")
A("int_eff03", S09, "INBSOC", u="Respondents who followed a civic integration programme (SING 2009)")
V("int_eff07", "int", "Thanks to the programme I know better how things work in the Netherlands (agreement)", s09="INBNL", valueset="agree5",
  universe="Respondents who followed a civic integration programme (SING 2009)")
A("int_eff06", S09, "NL", u="Respondents who followed a civic integration programme (SING 2009)")
V("int_crs_end_yr", "int", "Year the civic integration programme was completed / stopped", s09="JRINBEI", type="year", universe="Respondents who completed a civic integration programme (SING 2009)")
A("int_crs_dipl", S09, "DIPLINBA", pairs=[(1, 1), (2, 0)], u="Respondents who completed a civic integration programme (SING 2009)")
A("int_nt2", S09, "NT2CERT", yn12=True, u="Respondents who followed a civic integration programme (SING 2009)")
A("int_nlcrs", S09, "NLCURS", pairs=[(1, 1), (2, 1), (3, 0), (4, 0)], u=U09M)
A("int_nlcrs_det", S09, "NLCURS", u=U09M)

# ---- labour market and income
A("lab_emptype", S09, "ZELFST", pairs=[(1, 1), (2, 2)], u=U09W)
A("lab_hrs_cat5", S09, "UURWRKC4", pairs=[(1, 1), (2, 2), (3, 3), (4, 4), (9, ".c")], u="Employees (SING 2009)", note="SING classes <12 / 12-20 / 20-35 / 35+")
W("lab_hrs_cat5", "SING 2009: contractual hours of employees in classes <12, 12-20, 20-35, 35+ (no 'zero hours' class).")
A("lab_12h_se", S09, "URENWR2X", pairs=[(9, ".c")], u="Self-employed respondents (SING 2009)")
A("lab_unemp_ever", S09, "WERKL", yn12=True, u=U09W)
A("dem_prtnr_emp", S09, "PARTWERK", yn12=True, u=U09PC)
V("inc_lab_band", "inc", "Net monthly labour income in 250-euro bands (SING 2009)", s09="ARBINK1", valueset="inc_band14", universe=U09W, notes="SPVA/SPVN: inc_lab_cat (other bands).")
V("dem_prtnr_inc_band", "dem", "Net monthly income of the partner in 250-euro bands (SING 2009)", s09="INKPART2", valueset="inc_band14", universe=U09PC)
A("inc_change5", S09, "FINSUBJ", u="Respondents who are head or partner of the household (SING 2009)")
V("inc_enough4", "inc", "Household income is more than enough / enough / too little / far too little to live on", s09="RONDKOM2", valueset="enough4",
  universe="Respondents who are head or partner of the household (SING 2009)")
A("inc_rel_nl5", S09, "LVSTNL", u=U09)
V("inc_rel_grp5", "inc", "Standard of living compared with other households of the own origin group in the Netherlands", s09="LVSTLVH", valueset="relative5", universe=U09M)
V("inc_rel_orig5", "inc", "Standard of living in the country of origin before migration, compared with others there", s09="LVSTLVHR", valueset="relative5", universe=U09G1)

# ---- language
A("lang_nl_prtnr", S09, "TAALPART", u="Respondents with a migration background living with a partner (SING 2009)")
A("lang_nl_chd", S09, "TAALKIND", u="Respondents with a migration background who have children (SING 2009)")
V("lang_nl_par", "lang", "Speaks Dutch with parents (often / sometimes / never)", s09="TAALOUD", valueset="freq3", universe="Respondents with a migration background living with their parents (SING 2009)")
A("lang_prob_spk", S09, "TAALGESP", pairs=[(1, 1), (2, 2), (3, 3)], u=U09M, note="'vaak moeite / spreekt geen Nederlands' is one category")
A("lang_prob_read", S09, "TAALKRAN", u=U09M)
A("lang_prob_write", S09, "TAALPEN", u=U09M)
A("lang_orig_follow", S09, "ETNIGESP", u=U09M)
A("lang_other", S09, "ETNITAAL", pairs=[(1, 41), (2, 42), (3, 43), (4, 96), (5, 44), (6, 45), (7, 46), (8, 47), (9, 13), (10, 96), (11, 48), (12, 49), (13, 12), (14, 44), (16, 13),
                                        (17, 96), (18, 50), (19, 44), (20, 36), (21, 96), (22, 51), (23, 96), (24, 52), (25, 53), (26, 54), (97, 96)],
  u="Respondents who can follow a conversation in a language of the country of origin (SING 2009)")
W("lang_other", "SING 2009: group-specific language lists (Afghan, Iraqi, Iranian, Somali, Polish, Chinese groups) mapped to one list.")
A("lang_orig_prob_und", S09, "ETNIVERS", u="Respondents who can follow a conversation in a language of the country of origin (SING 2009)")
A("lang_orig_prob", S09, "ETNISPRE", u="Respondents who can follow a conversation in a language of the country of origin (SING 2009)")
A("lang_orig_read", S09, "ETNILEES", pairs=[(4, 5)], u="Respondents who can follow a conversation in a language of the country of origin (SING 2009)")
A("lang_orig_write", S09, "ETNIPEN", pairs=[(4, 5)], u="Respondents who can follow a conversation in a language of the country of origin (SING 2009)")
V("lang_foreign", "lang", "Also speaks English, German or French", s09="ENGFRDUI", valueset="foreign4", universe=U09M)
V("lang_foreign_vs_nl", "lang", "Speaks that foreign language better, equally well or worse than Dutch", s09="EFDNL", valueset="better3",
  universe="Respondents with a migration background who speak English, German or French (SING 2009)")

# ---- housing
A("hous_indep_yr", S09, "WJRSTART", u=U09)
A("hous_tenure", S09, "KOOPWON", pairs=[(1, 1), (2, 2), (6, 98)], u=U09)
V("hous_shared_n", "hous", "Number of other persons living in the dwelling (shared housing)", s09="WNPERS", type="num", universe="Respondents in shared housing, a room at work, a boarding house or similar (SING 2009)")
V("hous_shared_room", "hous", "Has a room of one's own or shares a room", s09="DEELKAM", valueset="share2", universe="Respondents in shared housing (SING 2009)")
V("hous_shared_kitchen_n", "hous", "Number of persons the kitchen is shared with", s09="DEELKEUK", type="num", universe="Respondents in shared housing (SING 2009)")
V("hous_shared_bath_n", "hous", "Number of persons the toilet and bathroom are shared with", s09="DEELSANI", type="num", universe="Respondents in shared housing (SING 2009)")
V("hous_cost", "hous", "Monthly rent or mortgage payment (euro, net)", s09="HUURHYP", type="num", universe="Respondents who are head or partner of the household (SING 2009)")
V("hous_cost_15", "hous", "Monthly rent or mortgage payment, constant 2015 euro", type="num", universe="Respondents who are head or partner of the household (SING 2009)", derive="cpi2015:hous_cost")
V("hous_sat5", "hous", "Satisfaction with the current dwelling", s09="WONTEVR", valueset="satisfied5", universe=U09)
A("trn_house", S09, "HUISBUI", yn12=True, u=U09M)
A("hous_nbhd01", S09, "BRTTHUIS", u=U09); A("hous_nbhd02", S09, "BRTPRET", u=U09); A("hous_nbhd03", S09, "BRTTLVH", u="All respondents (SING 2009; natives were asked about a neighbourhood with many native Dutch)")

# ---- health, identification, transnational ties, return
A("hlth_self", S09, "GEZONDH", u=U09)
V("hlth_bmi_cat", "hlth", "Body mass index in 4 classes (respondents aged 18+; SING 2009 public file)", s09="BMI", valueset="bmi4", universe="Respondents aged 18 or older (SING 2009)")
M("hlth_bmi_cat", S09, "BMI", 8, ".c", "younger than 18"); M("hlth_bmi_cat", S09, "BMI", 9, ".d", "height or weight unknown")
A("hlth_pa_winter", S09, "SPORTWIN", pairs=[(8, 0), (9, ".d"), (10, ".b")], u=U09, note="8 never -> 0 days; 9 'wisselt sterk'")
A("soc_sport5", S09, "FQSPORT", u=U09)
A("iden_nl5", S09, "VOELNL", u=U09M); A("iden_orig5", S09, "VOELLVH", u=U09M); A("iden_scale", S09, "ZELFIDEN", u=U09M)
A("trn_cont_fam3", S09, "CONTHERK", pairs=[(8, ".c")], u=U09M, note="8 = no family in the country of origin")
A("trn_visit_yearly", S09, "BEZOEHER", u=U09M)
A("trn_homesick", S09, "HEIMWEE", u=U09M)
A("ret_wish", S09, "WILTERUG", pairs=[(1, 1), (2, 3), (6, 2)], u="All respondents (SING 2009; natives asked about living in another country)")
A("ret_poss", S09, "MOGTERUG", pairs=[(1, 1), (2, 3)], u="Respondents who want to return (SING 2009)")
A("ret_noreason", S09, "NIETTRUG", pairs=[(1, 1), (2, 3), (3, 4), (4, 9), (5, 11), (6, 2), (7, 13), (8, 6), (9, 5), (10, 12), (11, 7), (12, 8), (96, 10)],
  u="Respondents who do not want or cannot return (SING 2009)")
A("ret_reason", S09, "WELTERUG", pairs=[(96, 13)], u="Respondents who want to return (SING 2009)")
V("ret_when", "ret", "When the respondent expects to be able to return to the country of origin", s09="WANNTRUG", valueset="when6_ret", universe="Respondents who want to return (SING 2009)")
V("ret_other_cntry", "ret", "Would like to live permanently in a country other than the Netherlands or the country of origin", s09="WILANDLA", valueset="yesno", yn12=True, universe=U09M)
A("ret_fut5y", S09, "WOONNL5J", pairs=[(1, 1), (2, 3), (3, 4)], u=U09)
W("ret_fut5y", "SING 2009: 'Denkt u dat u over 5 jaar nog in Nederland woont?' (yes, certainly / probably back in the origin country / probably in another country).")
A("trn_remit", S09, "V680X", yn12=True, u=U09M)
W("trn_remit", "SING 2009 asks about the calendar year 2008 (money or goods sent to the country of origin).")
for t, src in [("trn_remit01", "V682_2"), ("trn_remit02", "V682_1"), ("trn_remit03", "V682_3"), ("trn_remit04", "V682_4"), ("trn_remit05", "V682_6"), ("trn_remit06", "V682_5")]:
    A(t, S09, src, u="Households that sent money or goods to the country of origin in 2008 (SING 2009)")

# ---- social contacts and participation
for t, src in [("soc_act01", "SPORTVER"), ("soc_act02", "VRIJVER"), ("soc_act03", "WIJKVER"), ("soc_act04", "VAKBOND"), ("soc_act05", "ALLVER"),
               ("soc_act06", "POLPART"), ("soc_act07", "GODORG"), ("soc_act08", "NATUURV"), ("soc_act09", "ANDORG"), ("soc_act10", "GEENORG")]:
    A(t, S09, src, u=U09)
A("soc_act_hrs", S09, "UURWKVER", u="Respondents who attend meetings or activities (SING 2009)")
A("soc_act_ethn", S09, "ORGETNI", pairs=[(1, 1), (2, 2), (3, 4)], u="Respondents who attend meetings or activities (SING 2009)", note="1 'vooral allochtonen' (not own group specifically)")
W("soc_act_ethn", "SING 2009 answer categories: vooral allochtonen / vooral autochtone Nederlanders / allerlei bevolkingsgroepen (no 'half-half').")
A("soc_cont_fam", S09, "CONTFAM", pairs=[(8, ".c")], u=U09)
A("soc_cont_frnd", S09, "CONTVRIE", pairs=[(8, ".c")], u=U09)
A("soc_cont_nbr", S09, "CONTBUUR", pairs=[(8, ".c")], u=U09)
A("soc_cont_frnd_org", S09, "CONTALL", pairs=[(8, ".c")], u="Respondents with a migration background (SING 2009; asked about friends with a migration background in general, not the own group)")
A("soc_cont_nbr_org", S09, "CONTBALL", pairs=[(8, ".c")], u="Respondents with a migration background (SING 2009; neighbours with a migration background in general)")
A("soc_cont_frnd_nl", S09, "CONTAUT", pairs=[(8, ".c")], u=U09M)
A("soc_cont_nbr_nl", S09, "CONTBAUT", pairs=[(8, ".c")], u=U09M)
A("soc_leis_nl", S09, "VRTIJDNL", u="A random half of the respondents with a migration background (SING 2009: CAPI script field exp2431 = 1; no split indicator delivered, the other half is .c)")
_r = find("soc_leis_nl"); _r["notes"] = (_r["notes"] + " " if _r["notes"] else "") + "SING 2009: asked to a random half of the respondents with a migration background - the CAPI script gates Q2630 on 'exp2431 = 1', the only item of SING 2009 with such a field; the deposit (READ ME, fieldwork report) does not document the split and delivers no indicator; 3,017 of 5,952 were asked, balanced across origin group, sex and age class."
A("soc_cont_bal", S09, "CONTACTV", u="Respondents with a migration background who did not answer 'never' to Q2630 (SING 2009): the random half not asked Q2630 (soc_leis_nl .c) was asked this item too")
_r = find("soc_cont_bal"); _r["notes"] = (_r["notes"] + " " if _r["notes"] else "") + "SING 2009: the printed condition 'not Q2630 = 3' also admits the random half of the migrant respondents who were never asked Q2630 (soc_leis_nl .c), so the item has 5,144 answers against 2,364 respondents with leisure contact often/sometimes."
A("lab_coll_bal", S09, "CONTACTW", u="Employed respondents with a migration background (SING 2009)")
A("soc_leis_oth", S09, "VRTIJDAN", u=U09)
A("soc_grp_most", S09, "ANVEEL", u="Respondents with leisure contact with other minority groups (SING 2009)")
A("soc_bestfrnd_eth", S09, "BESTVRIE", u=U09M)
V("soc_vwn_contact", "soc", "Contact with VluchtelingenWerk (Dutch Council for Refugees), now or in the past", s09="VWCONTAC", valueset="contact_vw3", universe=U09M)
V("soc_vwn_freq", "soc", "Frequency of contact with VluchtelingenWerk", s09="VWVAAKCO", valueset="freq5_cont", universe="Respondents with (past) contact with VluchtelingenWerk (SING 2009)")
V("soc_vwn_imp01", "soc", "Importance of VluchtelingenWerk for: getting to know Dutch society", s09="VWBELNL", valueset="important5", universe="Respondents with (past) contact with VluchtelingenWerk (SING 2009)")
V("soc_vwn_imp02", "soc", "Importance of VluchtelingenWerk for: learning Dutch", s09="VWBELTA", valueset="important5", universe="Respondents with (past) contact with VluchtelingenWerk (SING 2009)")
V("soc_vwn_imp03", "soc", "Importance of VluchtelingenWerk for: finding work", s09="VWBELWRK", valueset="important5", universe="Respondents with (past) contact with VluchtelingenWerk (SING 2009)")
V("soc_vwn_imp04", "soc", "Importance of VluchtelingenWerk for: making Dutch friends and acquaintances", s09="VWBELSOC", valueset="important5", universe="Respondents with (past) contact with VluchtelingenWerk (SING 2009)")

# ---- attitudes, media, politics
for t, src in [("att_chd_frnd_orig", "AFKVRIKI"), ("att_chd_prtnr_orig", "AFKARKI"), ("att_gr02", "VRWHUISH"), ("att_fam04", "THUISHUW"), ("att_fam19", "VERTRFAM"),
               ("att_gr07", "VRWSTOPW"), ("att_chd06", "INVLOUDF"), ("att_gr06", "INKJONGS"), ("att_hom01", "HOMOLEV"), ("att_soc01", "CULTDIV"), ("att_soc03", "ASIELMAK"),
               ("att_soc04", "RECHTUIT"), ("att_soc05", "VEELALLO"), ("att_soc08", "SLECHTWK"), ("att_nl01", "KANSALLO"), ("att_nl03", "RESPRECH"), ("att_nl04", "NLGASTV"),
               ("att_nl08", "OPENCULT"), ("att_rel04", "RELIGSCH"), ("att_rel02", "GEENRELD"), ("hlth_happy5", "GELUK"), ("soc_trust_gen", "VERTROUW"),
               ("att_safe_nl", "VEILIGNL"), ("iden_home_nl", "THUISNL"), ("pol_interest3", "POLINT"), ("pol_vote_int", "STEMINT")]:
    A(t, S09, src, u=U09)
W("att_chd_prtnr_orig", "SING 2009: '<groep> als partner' - for migrants an 'autochtoon', for natives an 'allochtoon' partner.")
V("att_soc11", "att", "All those other cultures in the Netherlands are a threat to our own culture (agreement)", s09="CULBEDR", valueset="agree5", universe=U09)
A("att_therm01", S09, "TEMPMAR", u="All respondents (SING 2009)")
A("att_therm05", S09, "TEMPPOOL", u="All respondents except the Polish group (SING 2009)")
V("att_therm12", "att", "Feeling thermometer towards Chinese (0 very negative - 100 very positive)", s09="TEMPCHIN", type="num", universe="All respondents except the Chinese group (SING 2009)")
A("att_therm10", S09, "TEMPEIG", u=U09)
V("att_therm_oth", "att", "Feeling thermometer towards the other side: native Dutch (asked to migrants) or migrants (asked to natives)", s09="V2880", type="num", universe=U09)
A("att_sat_nl10", S09, "TEVRNED", u=U09)
V("iden_proud_nl5", "iden", "Proud to be Dutch (strength)", s09="TROTSNL", valueset="strength5", universe=U09)
V("iden_proud_orig5", "iden", "Proud to belong to the own origin group (strength)", s09="TROTSLVH", valueset="strength5", universe=U09M)
A("iden_allochtoon", S09, "ZELFALL", yn12=True, u=U09M)
A("disc_perc", S09, "DISCALG", u=U09); A("disc_exp", S09, "DISCZELF", u=U09)
A("disc_reason", S09, "DISCRED", pairs=[(1, 1), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (95, 12)], u="Respondents who experienced discrimination (SING 2009)")
for t, src in [("disc_yn01", "DISCWERK"), ("disc_yn02", "DISCSOLL"), ("disc_yn03", "DISCOFFI"), ("disc_yn04", "DISCSTRA")]:
    A(t, S09, src, yn12=True, u="Respondents who experienced discrimination (SING 2009)")
W("disc_yn04", "SING 2009: 'op straat'; SIM 2011: elsewhere, e.g. in the street or going out.")
_R6 = [(1, 6), (2, 5), (3, 4), (4, 3), (5, 2), (6, 1)]
_R6_F5 = [(1, 1), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5)]
A("med_krant_nl_days", S09, "KRTNED", pairs=_R6, u=U09); A("med_krant_nl_cat", S09, "KRTNED", pairs=_R6_F5, u=U09)
A("med_tv_nl_days", S09, "TVNED", pairs=_R6, u=U09); A("med_tv_nl_cat", S09, "TVNED", pairs=_R6_F5, u=U09)
A("med_tv_orig_days", S09, "TVEIG", pairs=_R6, u=U09M); A("med_tv_orig_cat", S09, "TVEIG", pairs=_R6_F5, u=U09M)
W("med_tv_orig_days", "SING 2009 scale runs 1 every day ... 6 never (reversed here); asked as '<?> zenders' with the group filled in.")
A("med_pc", S09, "BEZITPC", yn12=True, u=U09)
A("med_email_month", S09, "EMAIL", yn12=True, u=U09)
A("med_email_ethn", S09, "CHATPUB", pairs=[(1, 1), (2, 2), (3, 4), (4, ".a")], u="Respondents who e-mailed or chatted this month (SING 2009)")
V("pol_news_days", "pol", "Follows news about Dutch politics (days per week, 6 classes)", s09="VOLGNLPO", valueset="media_days6", universe=U09)
MM("pol_news_days", S09, "VOLGNLPO", _R6)
A("pol_news_cat", S09, "VOLGNLPO", pairs=_R6_F5, u=U09)
A("pol_party", S09, "STEMWS", pairs=[(1, 3), (2, 7), (3, 1), (4, 4), (5, 6), (6, 5), (7, 2), (8, 14), (9, 8), (10, 11), (11, 92), (12, 15), (13, 17), (96, 16)],
  u="Respondents who would (maybe) vote (SING 2009)")

# ---- religion
A("rel_any", S09, "GELOOFT", yn12=True, u=U09)
A("rel_den_det", S09, "RELIGIE", pairs=[(1, 21), (2, 22), (3, 23), (4, 24), (5, 26), (6, 25), (7, 41), (8, 42), (9, 43), (10, 44), (11, 13), (12, 31), (13, 32), (14, 33), (15, 39),
                                        (16, 34), (17, 35), (18, 36), (19, 38), (20, 46), (21, 47), (22, 45), (23, 99)], u=U09REL)
A("rel_den_cat", S09, "RELIGIE", pairs=[(c, 2) for c in range(1, 7)] + [(7, 4), (8, 4), (9, 4), (10, 4), (11, 1)] + [(c, 3) for c in range(12, 20)] + [(20, 4), (21, 4), (22, 4), (23, 4)],
  u=U09REL)
A("rel_attend", S09, "KERKBEZ", pairs=[(1, 4), (2, 4), (3, 3), (4, 2), (5, 1)], u=U09REL)
A("rel_attend5", S09, "KERKBEZ", u=U09REL)
A("rel_web5", S09, "NETRELI", u=U09REL)
A("rel_id01", S09, "RELZELF", u=U09REL); A("rel_id02", S09, "RELKWET", u=U09REL); A("rel_id04", S09, "RELTWIJF", u=U09REL)
A("rel_pray", S09, "GEBED", u=U09MU); A("rel_ramadan", S09, "RAMADAN", u=U09MU); A("rel_halal", S09, "HALAL", u=U09MU)
A("rel_rule", S09, "ISREGEL", u=U09MU); A("rel_veil_should", S09, "HOOFDBUI", u=U09MU); A("att_isl02", S09, "ISLNEGA", u=U09MU)
A("rel_veil", S09, "ZHFDDOEK", pairs=[(1, 1), (2, 0)], u="Muslim women (SING 2009)")

# ---- parent questions (respondents aged 15-17)
A("hh_inc_band_par", S09, "GEZINK3", pairs=[(1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (7, 4), (8, 5), (9, 5), (10, 6), (11, 6), (12, 7), (13, 7), (14, 8)],
  u="Respondents aged 15-17 whose parent answered the parent questions (SING 2009)", note="250-euro bands collapsed to 500-euro bands")


# =====================================================================================================================
# Manual questionnaire links for variables whose data name differs from the name printed in the questionnaire, or whose
# label carries no question number (SIM 2006 script printout, SIM 2011 multi-coded questions).  'qid#k' = k-th option of
# a multiple-response question.  SCP constructs (ETNGRP, GENERAT, BB_NED, MAXDIP*, ...) are documented in
# questionnaires.CONSTRUCTED_MANUAL and need no link.
# ---- LAS 2004/05 (hardcopy, appendix 1a of the fieldwork report)
L(S04, "HUIDOPL", "VRAAG 47")              # printed as HUISOPL
L(S04, "PFLEXW", "VRAAG 55")               # FLEXW as answered in the supplementary partner interview ('+ P' marks the items of that interview)
L(S04, "ISLREGEL", "VRAAG 300")            # printed as ISREGEL
for src, q in [("BOODSCH1", 80), ("KOKEN1", 81), ("WASSEN1", 82), ("VERZ1", 84), ("BRENGEN1", 85)]:
    L(S04, src, f"VRAAG {q}")              # division of household tasks: printed without the trailing 1
for q in (104, 113):                       # up to three reasons for not using childcare / after-school care, coded Q104nn / Q113nn
    for k in (1, 2, 3):
        L(S04, f"Q{q}0{k}", f"VRAAG {q}")
L(S04, "VRIJTACT", "VRAAG 227 (2)")        # printed as VRIJACT; second block numbered 227 (the first is SPORTACT)
for i in range(1, 44):                     # hours spent on activity i over the diary day, summed from the 72 quarter-hour slots K0101-K7201
    L(S04, f"AKT{i:02d}", "VRAAG 501")
W("tim_act01", "LAS 2004/05 diary: the day runs from 6:00 to 24:00 in 72 quarter-hour slots (tim_slot01-72, activity codes act43); "
               "tim_act01-43 are the hours spent on each activity summed by SCP over the 72 slots.")

# ---- SIM 2006 (CAPI script printout, no variable names; labels of these batteries carry no question number)
_ORG06 = ["SPORT", "VRIJ", "WIJK", "VAKBOND", "ALL", "POLPART", "GODORG", "NATUURV", "BIED", "ANDORG", "GEENORG"]   # option order of kaart 11
for k, (att, mem) in enumerate(zip(["SPORTVER", "VRIJVER", "WIJKVER", "VAKBOND", "ALLVER", "POLPART", "GODORG", "NATUURV", "BIED", "ANDORG", "GEENORG"],
                                   ["SPORTLID", "VRIJLID", "WIJKLID", "BONDLID", "ALLLID", "POLLID", "GODLID", "NATUURLI", "BIEDLID", "ANDLID", "GEENLID"]), 1):
    L(S06, att, f"VRAAG 925#{k}")          # attends meetings/activities of organisation k
    L(S06, mem, f"VRAAG 926#{k}")          # member of organisation k
for k in range(1, 27):
    L(S06, f"V1530_{k}", f"VRAAG 1530#{k}")   # sports practised by the respondent (option codes 11-36)
    L(S06, f"V1570_{k}", f"VRAAG 1570#{k}")   # sports practised by the selected child

# ---- SIM 2011 (hardcopy): names printed per option, or under a different name
L(S11, "INWKIND", "VRAAG 42A")
L(S11, "INWPART", "VRAAG 43A")
L(S11, "NL", "VRAAG 441")
for b in ["WAOUITK", "AOWUITK", "STUDIEF", "ALIMEN", "ANDUITK"]:
    L(S11, f"UITKDUUR_{b}_JR", "VRAAG 610"); L(S11, f"UITKDUUR_{b}_MND", "VRAAG 610")   # header: 'UITKDUUR_BIJSTAND, UITKDUUR_WWUITK, etc.'
L(S11, "SELECTKIND1_GESLACHT", "VRAAG 1050"); L(S11, "SELECTKIND1_LEEFTIJD", "VRAAG 1050")
for k in range(1, 6):
    L(S11, f"OPVDOEL{k}", f"VRAAG 1073#{k}")
