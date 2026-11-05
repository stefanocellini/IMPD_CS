# -*- coding: utf-8 -*-
"""
IMPD crosswalk builder — SIM 2015 and SIM 2020 (DANS CCF deposits).

Adds the SIM source variables to the targets declared in variables.py (same item asked in SPVA/SPVN)
and declares the SIM-only targets.  Conventions:
  * one V() per target; existing targets are extended with S(target, s15=..., s20=...) which also
    registers the SIM universe text and (optional) wording note;
  * all M() recodes are explicit; codes not listed pass through (after the survey's missing rules);
  * SIM 2015 'Diversen' (96 / -6) and SIM 2020 'anders, namelijk' (92) are substantive 'other' categories
    where the value set has one, otherwise .d;
  * registry-based (CBS) variables carry the suffix _reg.
Surveys: "sim2015" (DANS easy-dataset:239464, DOI 10.17026/dans-x63-dq58),
         "sim2020" (DANS easy-dataset:259562, DOI 10.17026/dans-26h-xn4n).
"""
from valuesets import VALUESETS, vs
from declare import V, M, W, L, U, VARS, VMAP, find, SURVEY_KEYS

S15, S20 = "sim2015", "sim2020"
U_SIM = "All respondents (SIM: persons aged 15+ sampled from the BRP)"
U_SIM15 = "All respondents (SIM 2015)"
U_SIM20 = "All respondents (SIM 2020)"
U_MIG = "Respondents with a migration background (not asked to the native Dutch reference sample)"
U_MIG15 = "Respondents with a migration background (SIM 2015)"
U_MIG20 = "Respondents with a migration background (SIM 2020)"
U_MIG20_G1 = "First-generation respondents with a migration background (SIM 2020: the script routed the second generation past the language and Dutch-course items)"
U_A = "Split-half group A (svy_split = 1), SIM 2020"
U_B = "Split-half group B (svy_split = 2), SIM 2020"
U_MIG_B = "Split-half group B, respondents with a migration background (SIM 2020)"
U_MUS = "Respondents who said they are Muslim (SIM 2015: Turkish, Moroccan, Somali group); not asked to others"


def S(target, s15=None, s20=None, u15="", u20="", wording=""):
    """Attach SIM sources to a target declared in variables.py."""
    r = find(target)
    assert not (s15 and r["src_sim2015"]) and not (s20 and r["src_sim2020"]), target
    if s15: r["src_sim2015"] = s15
    if s20: r["src_sim2020"] = s20
    if u15: U(target, S15, u15)
    if u20: U(target, S20, u20)
    if wording: W(target, wording)


def MM(target, survey, src, pairs, note=""):
    for a, b in pairs:
        M(target, survey, src, a, b, note)


def yn(target, survey, src):
    M(target, survey, src, 1, 1); M(target, survey, src, 2, 0)


def both(target, src15, src20, pairs15=None, pairs20=None, yn12=False):
    """Same recode for both SIM surveys (source names usually identical)."""
    if src15 and pairs15: MM(target, S15, src15, pairs15)
    if src20 and pairs20: MM(target, S20, src20, pairs20)
    if yn12:
        if src15: yn(target, S15, src15)
        if src20: yn(target, S20, src20)


# ============================================================== id_ / svy_
V("id_src", "id", "Person number as in the source file (flat person-sample surveys)", s15="volgnummer", s20="Volgnummer", type="id",
  universe="All respondents, SIM 2015 and SIM 2020", notes="SPVA/SPVN: household number and member number instead (id_hh_src, id_mem).")
S("svy_wgt", s15="eindgewicht", s20="eindgewicht",
  u15="All respondents; final weight ('eindgewicht', SIM 2010 weighting model re-applied: group x sex, age, generation, household, municipality size, income)",
  u20="All respondents; final weight ('eindgewicht', CBS calibration: migration background x sex, age, generation, household type and size, municipality size, personal income; natives also home ownership)",
  wording="Weights are population-scaled (sum = population size per survey) and survey-specific; SPVA/SPVN weights come from ISEO, SIM weights from CBS. Do not pool weighted estimates across surveys without rescaling.")
V("svy_wgt_start", "svy", "Start weight (inverse selection probability)", s15="startgewicht", type="num", universe=U_SIM15, include=1)
V("svy_wgt_corr", "svy", "Correction weight (non-response model, SIM 2010 weighting model)", s15="correctiegewicht", type="num", universe=U_SIM15, include=0,
  notes="eindgewicht = startgewicht x correctiegewicht. Source file only.")
V("svy_wgt_alt", "svy", "Final weight, alternative weighting model (SIM 2015)", s15="eindgewichtalt", type="num", universe=U_SIM15,
  notes="Alternative weighting model supplied with the file; not documented in the fieldwork report.")
V("svy_wgt_corr_alt", "svy", "Correction weight, alternative model (SIM 2015)", s15="correctiegewichtalt", type="num", universe=U_SIM15, include=0)
V("svy_complete", "svy", "Interview status (source administrative flag)", s15="status", type="cat", universe=U_SIM15, include=0,
  notes="All records = 1 'geslaagd' (completed). Source file only.")
V("svy_mode", "svy", "Interview mode", s15="bron", s20="kanaal", valueset="mode", universe="All respondents, SIM 2015 and SIM 2020",
  notes="SIM 2015: sequential mixed mode (CAWI first, CAPI follow-up; 52% CAWI). SIM 2020: CAWI 90%, CAPI 10% (CAPI only for Caribbean, Moroccan, Somali, Surinamese and Turkish groups because of covid); 15 CAPI interviews were held by video call (code 3, derived from svy_video).",
  derive="mode_video")
MM("svy_mode", S15, "bron", [(1, 1), (2, 2), (3, 2)]); MM("svy_mode", S20, "kanaal", [(1, 1), (2, 2)])
V("svy_agency", "svy", "Fieldwork agency that conducted the interview", s15="bron", valueset="agency", universe=U_SIM15,
  notes="SIM 2015 CAWI and part of CAPI by TNS NIPO/Veldkamp, remaining CAPI by Labyrinth. SIM 2020: all fieldwork by Labyrinth (not a variable).")
MM("svy_agency", S15, "bron", [(1, 1), (2, 1), (3, 2)])
V("svy_video", "svy", "CAPI interview conducted by video call (CAVI)", s20="manier", valueset="yesno", universe="SIM 2020 CAPI respondents",
  notes="Interviewer-recorded; CAWI respondents .c.")
MM("svy_video", S20, "manier", [(1, 0), (2, 1)])
V("svy_qversion", "svy", "Questionnaire script version (SIM 2020)", s20="versie", valueset="qversion", universe=U_SIM20,
  notes="Version numbers of the Labyrinth CAWI/CAPI script as delivered in the file; versions 1-3 are early CAWI interviews (March-April 2020), 5 covers 84% of interviews including all face-to-face CAPI, 6 is CAPI only. The fieldwork report does not document the content differences between versions.")
V("svy_split", "svy", "Split-half group (SIM 2020)", valueset="split_half", universe=U_SIM20, derive="split_random",
  notes="SIM 2020 randomly assigned respondents within each origin group to group A or B; some question blocks were asked only to A (political participation and trust, belonging at work/school/neighbourhood, media interest and positioning) and others only to B (opinions block 8.12, religion items bijbkor/korzelfint, mental health items 4 and 7-8, GP visits, pain, limitations in visiting, situational discrimination, Zwarte Piet). Derived as the non-zero value of the eight random_* source variables.")
for i, g in enumerate(["mar", "tur", "car", "sur", "poo", "som", "aut", "ira"], 1):
    V(f"svy_rnd{i:02d}", "svy", f"Randomisation flag, {g.upper()} group (SIM 2020)", s20=f"random_{g}", type="cat", universe=U_SIM20, include=0,
      notes="0 = not in this group, 1 = A, 2 = B. Source file only; combined into svy_split.")
S("svy_lang_q", s20="taal", u20="All respondents (language chosen for the questionnaire; Dutch, Turkish, Moroccan Arabic, Polish, Somali, Farsi offered depending on group)",
  wording="SPVN 2003: Dutch/English/French chosen by the interviewer with the respondent. SIM 2020: language version selected by the respondent (CAWI) or interviewer (CAPI).")
MM("svy_lang_q", S20, "taal", [(1, 1), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)])
V("svy_fw_mo", "svy", "Month of interview", s15="maand", valueset="month", universe=U_SIM15, type="cat",
  notes="SIM 2015 string month '01'-'07' converted. SPVA/SPVN and SIM 2020: interview date not in the public file.")
MM("svy_fw_mo", S15, "maand", [("'01'", 1), ("'02'", 2), ("'03'", 3), ("'04'", 4), ("'05'", 5), ("'06'", 6), ("'07'", 7)])
V("svy_fw_yr_src", "svy", "Year of interview as in source (string)", s15="jaar", type="str", universe=U_SIM15, include=0, notes="Always '2015'; use svy_year.")
V("svy_fw_yr_n", "svy", "Year of interview (numeric duplicate in source)", s15="jr", type="num", universe=U_SIM15, include=0, notes="Duplicate of svy_year; source file only.")
V("svy_fw_mo_n", "svy", "Month of interview (numeric duplicate in source)", s15="mnd", type="num", universe=U_SIM15, include=0, notes="Duplicate of svy_fw_mo; source file only.")
V("svy_dur_sec", "svy", "Interview duration in seconds", s15="duur", type="num", universe=U_SIM15,
  notes="Length of the CAWI/CAPI session as logged by the software; extreme values (> 1 day) are sessions left open.")
V("svy_ncontact", "svy", "Number of contact attempts (CAPI)", s15="countcontact", type="num", universe="SIM 2015 CAPI respondents (TNS NIPO fieldwork)",
  notes="Code 0 'LEEG' (empty) set to .d.")
M("svy_ncontact", S15, "countcontact", 0, ".d", "LEEG = empty")

# ============================================================== dem_
S("dem_sex", s15="geslacht", s20="geslachtsd", u20="All respondents; sex according to the sample (registry) data")
V("dem_age_cat", "dem", "Age in classes (15-24 ... 75+)", s15="leeftijd", s20="leeftijdsd_kl", valueset="age_cat7", universe="All persons; derived from dem_age where age in years is available",
  derive="age_cat",
  notes="SIM public files contain age only in classes (CCF coarsening): SIM 2015 self-reported classes 15-24 ... 75+; SIM 2020 registry age on 1-1-2020 in classes <18, 18-24, 25-34 ... 75+, collapsed here to 15-24 (the sample is 15+). For SPVA/SPVN the classes are cut from dem_age (derive age_cat). dem_age itself is .e in SIM.",
  wording="SIM 2015: 'Hoe oud bent U?' (self-report, classes). SIM 2020: registry age in classes; youngest class '<18' merged with 18-24.")
MM("dem_age_cat", S20, "leeftijdsd_kl", [(1, 1), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (7, 6), (8, 7)])
S("dem_eth", s15="etngba", s20="etngba",
  u15="All respondents; origin group from the CBS sample frame (BRP): 1st/2nd generation Turkish, Moroccan, Surinamese, Antillean/Aruban, Somali; Polish 1st generation registered 2004+; native Dutch reference sample",
  u20="All respondents; origin group from the CBS sample frame: as 2015 plus Iranian; 'Caribisch-Nederlands' = (former) Netherlands Antilles and Aruba incl. BES islands",
  wording="SPVA/SPVN: group by country of birth of the person and parents as established in the interview. SIM: group from the BRP sample frame (CBS herkomstgroepering). Code 4 covers Antillean/Aruban (SPVA, SIM 2015) and Caribbean-Dutch incl. Bonaire, Sint Eustatius and Saba (SIM 2020).")
MM("dem_eth", S15, "etngba", [(1, 2), (2, 1), (3, 3), (4, 4), (5, 9), (6, 10), (7, 90)])
MM("dem_eth", S20, "etngba", [(1, 2), (2, 1), (3, 4), (4, 3), (5, 10), (6, 9), (7, 90), (8, 7)])
S("dem_gen", s15="gengba", s20="generatiesd", u15="All respondents; generation from the sample frame (CBS definition)", u20="All respondents; generation from the sample frame (CBS definition)",
  wording="Definitions differ: SPVA/SPVN (ISEO) count arrival before age 6 as second generation; SIM (CBS) first generation = born abroad, second = born in NL with at least one parent born abroad. Code 0 = native Dutch reference sample (SIM only).")
S("dem_brthcntry", u15="Derived from origin group and generation (CBS definition)", u20="Derived from origin group and generation (CBS definition)",
  wording="SIM public files do not contain country of birth (removed by DANS/SCP). Under the CBS definition the origin group of a first-generation person is his/her own country of birth and second-generation persons are born in the Netherlands, so dem_brthcntry is derived (derive brthcntry_group): first generation -> country of the origin group (Caribbean group -> 7011 aggregate), second generation and natives -> 6030 Netherlands.")
find("dem_brthcntry")["derive"] = "brthcntry_group"
find("dem_brthcntry")["notes"] += " SIM 2015/2020: derived from dem_eth x dem_gen (CBS definition), see wording note."
V("dem_eth_cbs_reg", "dem", "Migration background, CBS 3 classes (registry)", s20="etngrp_kl", valueset="cbs_origin3", universe=U_SIM20,
  notes="CBS 'herkomstgroepering' in classes (native / western / non-western), from the registry linkage; code 9 -> .d.")
M("dem_eth_cbs_reg", S20, "etngrp_kl", 9, ".d")
V("dem_mar_reg", "dem", "Marital status (registry: married/registered partnership vs not)", s15="burgerlijkestaat", s20="vrlgbaburgerlijkestaatnw_kl", valueset="marstat_reg",
  universe="All respondents, SIM 2015 (BRP 31-12-2014) and SIM 2020 (BRP, classes)",
  notes="SIM 2015 string 'H' (gehuwd) / 'O' (ongehuwd) converted; SIM 2020 1 = gehuwd, 2 = ongehuwd, 9 -> .d. Self-reported marital status: dem_mar (SPVA/SPVN).")
MM("dem_mar_reg", S15, "burgerlijkestaat", [("'H'", 1), ("'O'", 2), ("''", ".d")]); M("dem_mar_reg", S20, "vrlgbaburgerlijkestaatnw_kl", 9, ".d")
V("dem_has_chd", "dem", "Has children (including children living elsewhere)", s15="kinderen", s20="kinderen", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020",
  notes="SPVA/SPVN: see dem_nchd (0 = no children).")
both("dem_has_chd", "kinderen", "kinderen", yn12=True)
S("dem_nchd", s15="aantkind", s20="aantkind", u15="Respondents with children (SIM 2015)", u20="Respondents with children (SIM 2020)")
S("dem_nchd_home", s15="kindhuis", s20="kindhuis", u15="Respondents with children (SIM 2015)", u20="Respondents with children (SIM 2020)")
S("dem_nchd_away", s15="nietinwkind", u15="Respondents with children not (all) living at home (SIM 2015)")
V("dem_chd_res", "dem", "Where the children living away from home live", s15="kindnl", valueset="chd_residence", universe="Respondents with children living elsewhere, SIM 2015 only")
V("fam_chd_young_age", "fam", "Age of youngest child living at home, classes", s20="lftjong_kl", valueset="age_cat_chd4", universe="Respondents with children at home, SIM 2020 only",
  notes="Classes as delivered by DANS (CCF coarsening).")
V("dem_has_prtnr", "dem", "Has a partner", s15="partner", s20="partner", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020",
  notes="SPVA/SPVN: see dem_prtnr_st / dem_prtnr_lat.")
both("dem_has_prtnr", "partner", "partner", yn12=True)
V("dem_prtnr_mar", "dem", "Married to or in registered partnership with the partner", s15="huwpart", valueset="yesno", universe="Respondents with a partner, SIM 2015 only")
yn("dem_prtnr_mar", S15, "huwpart")
V("dem_prtnr_cores", "dem", "Partner lives in the same house", s15="parthuis", s20="parthuis", valueset="yesno", universe="Respondents with a partner, SIM 2015 and SIM 2020")
both("dem_prtnr_cores", "parthuis", "parthuis", yn12=True)
S("dem_prtnr_res", s15="partnl", u15="Respondents whose partner does not live in the same house (SIM 2015)",
  wording="SPVN 2003 distinguishes Western Europe from elsewhere; SIM 2015 asks Netherlands / country of origin / another country (code 6).")
MM("dem_prtnr_res", S15, "partnl", [(1, 1), (2, 2), (3, 6)])
V("dem_prtnr_sex", "dem", "Sex of partner", s15="geslpart", valueset="sex", universe="Respondents with a partner, SIM 2015 only")
V("dem_prtnr_age_cat", "dem", "Age of partner in classes", s15="lftpart", valueset="age_cat7", universe="Respondents with a partner, SIM 2015 only",
  notes="SPVA/SPVN: dem_prtnr_age in years. One unlabelled code 8 -> .d.")
M("dem_prtnr_age_cat", S15, "lftpart", 8, ".d")
V("dem_prtnr_act", "dem", "Main activity of partner", s15="parthfda", s20="parthfda", valueset="prtnr_activity", universe="Respondents with a partner, SIM 2015 and SIM 2020")
M("dem_prtnr_act", S15, "parthfda", 96, 98); MM("dem_prtnr_act", S20, "parthfda", [(92, 98), (10, ".b")])
V("dem_prtnr_bc_cbs", "dem", "Country of birth of partner, CBS 3 classes", s20="geblpart_kl", valueset="cbs_origin3", universe="Respondents with a partner, SIM 2020 only",
  notes="CCF coarsening of the partner's country of birth (autochtoon / westers / niet-westers); 9 = other/refusal/don't know -> .d, or .c for respondents without a partner (derive kl9_route). SPVA/SPVN: dem_prtnr_brthcntry (country code).")
V("dem_prtnr_fa_bc_cbs", "dem", "Country of birth of partner's father, CBS 3 classes", s20="geblpapa_kl", valueset="cbs_origin3", universe="Respondents with a partner, SIM 2020 only")
V("dem_prtnr_ma_bc_cbs", "dem", "Country of birth of partner's mother, CBS 3 classes", s20="geblpama_kl", valueset="cbs_origin3", universe="Respondents with a partner, SIM 2020 only")
for t, s in [("dem_prtnr_bc_cbs", "geblpart_kl"), ("dem_prtnr_fa_bc_cbs", "geblpapa_kl"), ("dem_prtnr_ma_bc_cbs", "geblpama_kl")]:
    M(t, S20, s, 9, ".d")
V("dem_livsit", "dem", "Living situation (self-reported)", s15="gezpos", valueset="livsit5", universe=U_SIM15,
  notes="SPVA/SPVN: household composition hh_comp (head-reported roster).")
M("dem_livsit", S15, "gezpos", 96, 98)

# ============================================================== hh_
V("hh_oth_pers", "hh", "Other persons (besides partner/children/parents) in the household", s15="huishoverig", valueset="yesno", universe=U_SIM15)
yn("hh_oth_pers", S15, "huishoverig")
S("hh_noth", s15="nhuisover", u15="Respondents with other persons in the household (SIM 2015)",
  wording="SPVA/SPVN: number of non-nuclear household members from the roster; SIM 2015: self-reported number of 'other people' in the household.")
V("hh_oth_rel", "hh", "Other household members are family", s15="overwie", valueset="oth_relation3", universe="Respondents with other persons in the household, SIM 2015 only")
for i, (src, lab) in enumerate([("woon_alleen", "Lives alone"), ("woon_kind", "Child(ren)"), ("woon_partner", "Partner"), ("woon_ouders", "Parent(s)"),
                                ("woon_andrfam", "Other family members"), ("woon_anders", "Other persons, not family")], 1):
    V(f"hh_cores{i:02d}", "hh", f"Lives with: {lab}", s20=src, valueset="mentioned", universe=U_SIM20)
V("hh_type_reg", "hh", "Household type (registry)", s15="typehuishouden", s20="vrltyphh_kl", valueset="hh_type_reg",
  universe="All respondents; SIM 2015 BRP 31-12-2014, SIM 2020 BRP in classes",
  notes="SIM 2020 class 7 merges other/institutional/unknown (code 9 here).")
M("hh_type_reg", S20, "vrltyphh_kl", 7, 9)
V("hh_pos_reg", "hh", "Position in the household (registry)", s15="plaatsinhuishouden", s20="vrlplhh_kl", valueset="hh_pos_reg",
  universe="All respondents; SIM 2015 BRP 31-12-2014, SIM 2020 BRP in classes", notes="SIM 2020 class 9 (reference person other hh / other member / institutional / unknown) = code 19.")
M("hh_pos_reg", S20, "vrlplhh_kl", 9, 19)
V("hh_nadult_reg", "hh", "Number of adult household members (registry)", s15="aantalmeerderjarigen", type="num", universe=U_SIM15)
V("hh_nminor_reg", "hh", "Number of minor household members (registry)", s15="aantalminderjarigen", type="num", universe=U_SIM15)
for src, lab in [("bo", "primary education (bo)"), ("vo", "secondary education (vo)"), ("ve", "adult/vocational education (ve)"),
                 ("mbo", "upper vocational education (mbo)"), ("hbo", "higher professional education (hbo)"), ("wo", "university (wo)")]:
    V(f"hh_nchd_{src}_reg", "hh", f"Number of children in the household enrolled in {lab} (registry 2014/15)", s15=f"aantalkinderenin{src}", type="num", universe=U_SIM15)

# ============================================================== geo_
V("geo_urb_reg", "geo", "Urbanisation of municipality of residence (registry, 5 classes)", s15="stedelijkheid", valueset="urban5", universe=U_SIM15,
  notes="CBS 'stedelijkheid' of the municipality of registration on 1-1-2015. Municipality itself not in the SIM public files.")

# ============================================================== mig_
S("mig_yr_arr", s15="migrjaar", s20="migrjaar", u15="First-generation respondents (SIM 2015)", u20="First-generation respondents (SIM 2020)")
S("mig_reason", s15="redmigr2", u15="First-generation respondents, SIM 2015 (main reason, single answer)",
  wording="SPVA 2002/SPVN 2003/SIM 2015: one main reason. SIM 2020 asks the same list as a multiple-response question (mig_rsn01-12). SIM adds reasons 12-15.")
MM("mig_reason", S15, "redmigr2", [(1, 1), (2, 2), (3, 3), (4, 4), (5, 11), (6, 12), (7, 6), (8, 8), (9, 13), (10, 14), (11, 15), (96, 10)])
V("mig_reason_prtnr", "mig", "Main reason partner migrated to the Netherlands", s15="redmi_p2", valueset="mig_reason", universe="Respondents with a foreign-born partner, SIM 2015 only")
MM("mig_reason_prtnr", S15, "redmi_p2", [(1, 1), (2, 2), (3, 3), (4, 4), (5, 11), (6, 12), (7, 6), (8, 8), (9, 13), (10, 14), (11, 15), (12, 16), (96, 10), (97, ".a")])
RSN20 = [("werk", "Work"), ("studie", "Study"), ("soczek", "Social security, benefits"), ("polred", "Political reasons / war / religious persecution"),
         ("armoed", "Poverty / famine"), ("intrek", "Moved in with parent(s) or partner already in NL"), ("hwlk", "Marriage"),
         ("gzheid", "Health / medical reasons"), ("toekkind", "Future / education of children"), ("ouders", "Came with parent(s)"),
         ("partner", "Came with partner"), ("anders", "Other reason")]
for i, (src, lab) in enumerate(RSN20, 1):
    V(f"mig_rsn{i:02d}", "mig", f"Reason for migrating to NL: {lab}", s20=f"redmigr_{src}", valueset="mentioned", universe="First-generation respondents, SIM 2020 only (multiple answers)")
V("mig_reg_days", "mig", "Days registered in the BRP on 1-1-2015 (registry)", s15="verblijfsduur", type="num", universe="First-generation respondents, SIM 2015 only",
  notes="Maximum 7398 days = registration since the start of the GBA (1 October 1994); longer stays are censored at that value.")
V("mig_motive_ind_reg", "mig", "Migration motive registered by the IND (registry)", s15="indmigratiemotief", valueset="ind_motive",
  universe="First-generation respondents with an IND record (data up to 1-1-2012), SIM 2015 only")
V("mig_motive_pub_reg", "mig", "Migration motive, CBS published classification after imputation (registry)", s20="nieteumigratiemotiefpubl", valueset="ind_motive_pub",
  universe="First-generation respondents, SIM 2020 only", notes="String codes in source converted.")
MM("mig_motive_pub_reg", S20, "nieteumigratiemotiefpubl", [("'9'", 9), ("'10'", 10), ("'11'", 11), ("'20'", 20), ("'30'", 30), ("'31'", 31), ("'40'", 40), ("'50'", 50), ("''", ".c")])
V("mig_motive_nw_reg", "mig", "Migration motive, condensed IND classification without imputation (registry)", s20="migratiemotiefindnw", valueset="ind_motive_nw",
  universe="First-generation respondents, SIM 2020 only", notes="String codes in source converted; 99 'onbekend / niet ingevuld' -> .d.")
MM("mig_motive_nw_reg", S20, "migratiemotiefindnw", [("'9'", 9), ("'10'", 10), ("'11'", 11), ("'31'", 31), ("'32'", 32), ("'33'", 33), ("'34'", 34), ("'35'", 35),
                                                     ("'40'", 40), ("'49'", 49), ("'51'", 51), ("'61'", 61), ("'71'", 71), ("'81'", 81), ("'91'", 91), ("'99'", ".d"), ("''", ".c")])
for src, lab in [("arbeid", "labour"), ("asiel", "asylum"), ("gezin", "family"), ("studie", "study")]:
    V(f"mig_mot_{src[:3]}_reg", "mig", f"Rank of {lab} among the presumed migration motives (CBS derivation, registry)", s15=f"cbsmigratiemotief{src}", valueset="motive_rank",
      universe="First-generation respondents for whom CBS derived this motive (data to 31-12-2014), SIM 2015 only")

# ============================================================== nat_ / int_
V("nat_orig", "nat", "Has the nationality of the country of origin", s15="national", s20="national", valueset="yesno", universe=U_MIG)
both("nat_orig", "national", "national", yn12=True)
V("nat_nl", "nat", "Has Dutch nationality", s15="nationnl", s20="nationnl", valueset="yesno", universe=U_MIG,
  notes="Not asked to the native Dutch reference sample (.c).")
both("nat_nl", "nationnl", "nationnl", yn12=True)
S("nat_cit", u15="Derived from nat_nl and nat_orig", u20="Derived from nat_nl and nat_orig",
  wording="SPVA/SPVN: one question on nationality. SIM: two yes/no questions (Dutch nationality; origin-country nationality) combined (derive cit_nl_orig): 1 Dutch only, 2 dual, 3 origin only, 4 neither/other.")
find("nat_cit")["derive"] = "cit_nl_orig"
V("int_crs_st", "int", "Civic integration programme: followed / ongoing / not", s15="inbcurus", valueset="inb_course3", universe="First-generation respondents, SIM 2015 only")
M("int_crs_st", S15, "inbcurus", 4, ".c")
S("int_crs", s15="inbcurus", u15="First-generation respondents (SIM 2015); 'currently following' counted as yes")
MM("int_crs", S15, "inbcurus", [(1, 1), (2, 1), (3, 0), (4, ".c")])
V("int_exam", "int", "Passed the civic integration exam", s15="inbexam", s20="inbexam", valueset="inb_exam3", universe="First-generation respondents, SIM 2015 and SIM 2020")
M("int_exam", S15, "inbexam", 4, ".c")
V("int_nlcrs_det", "int", "Dutch language course: followed / certified / planned / not", s15="nlcurs", s20="nlcurs", valueset="nl_course5", universe=U_MIG)
U("int_nlcrs_det", S20, U_MIG20_G1)
S("int_nlcrs", s15="nlcurs", s20="nlcurs", u15="Respondents with a migration background (SIM 2015)", u20=U_MIG20_G1,
  wording="SIM: 'followed, with or without certificate, or currently following' = yes; 'no' and 'planning to' = no (detail in int_nlcrs_det).")
both("int_nlcrs", "nlcurs", "nlcurs", [(1, 1), (2, 1), (3, 0), (4, 0), (5, 1)], [(1, 1), (2, 1), (3, 0), (4, 0), (5, 1)])

# ============================================================== edu_
S("edu_cntry", s15="oplblnl", s20="oplbl", u15="All respondents (SIM 2015 derived variable incl. 'no education')",
  u20="All respondents (SIM 2020); 'no' to education abroad is coded 3 'Netherlands only' and includes persons without any education",
  wording="SPVA/SPVN/SIM 2015: constructed variable with a separate 'no education' code. SIM 2020: direct question 'Heeft u buiten Nederland een opleiding gevolgd?' (1 only abroad, 2 both, 3 no).")
M("edu_cntry", S15, "oplblnl", -7, ".")
S("edu_abr", s15="oplbl", s20="oplbl", u15=U_MIG15, u20="All respondents (SIM 2020), incl. the native reference sample")
both("edu_abr", "oplbl", "oplbl", [(1, 1), (2, 1), (3, 0)], [(1, 1), (2, 1), (3, 0)])
V("edu_abr_att_lvl3", "edu", "Highest education attended abroad, 3 levels", s15="maxoplbl", s20="maxoplbl_kl", valueset="edu3_att", universe="Respondents who attended education abroad, SIM 2015 and SIM 2020",
  notes="SCP classification Laag/Middel/Hoog as delivered (CCF coarsening). SIM 2020 code 9 -> .d, or .c for respondents without education abroad (derive kl9_route). SPVA/SPVN: highest diploma abroad (edu_abr_hi_det/_cat), attendance not asked.")
MM("edu_abr_att_lvl3", S15, "maxoplbl", [(-4, ".c"), (-6, ".d"), (96, ".d")]); M("edu_abr_att_lvl3", S20, "maxoplbl_kl", 9, ".d")
S("edu_abr_dipl", s15="diplbl", s20="diplbl", u15="Respondents who attended education abroad (SIM 2015)", u20="Respondents who attended education abroad (SIM 2020)")
both("edu_abr_dipl", "diplbl", "diplbl", yn12=True)
V("edu_abr_where", "edu", "Education abroad was in the country of origin or elsewhere", s15="ondlvh", s20="ondlvh", valueset="edu_where2", universe="Respondents who attended education abroad, SIM 2015 and SIM 2020")
S("edu_abr_yrs", s15="ondjrbl", u15="Respondents who attended education abroad (SIM 2015; 99 -> .a)")
M("edu_abr_yrs", S15, "ondjrbl", 99, ".a")
V("edu_abr_yrs_der", "edu", "Years of education abroad (SIM 2015 derived variable)", s15="jaarblopl", type="num", universe="Respondents who attended education abroad, SIM 2015 only", include=0,
  notes="Duplicate of edu_abr_yrs with 99 set to missing; source file only.")
V("edu_abr_dipl_lvl3", "edu", "Highest diploma obtained abroad, 3 levels (SIM 2015 derived)", s15="maxdiplbl", valueset="edu3", universe=U_SIM15,
  notes="Source codes: -9 did not study abroad / -6 diploma in NL only -> .c; -8 diploma, still studying -> .d; -3/-2/-1 no diploma -> 0; -4 -> .a; -7 -> .")
MM("edu_abr_dipl_lvl3", S15, "maxdiplbl", [(-9, ".c"), (-8, ".d"), (-7, "."), (-6, ".c"), (-4, ".a"), (-3, 0), (-2, 0), (-1, 0)])
S("edu_enr", s15="schoolg", s20="schoolg", u15="All respondents (SIM 2015)", u20="All respondents (SIM 2020)")
both("edu_enr", "schoolg", "schoolg", yn12=True)
S("edu_ft", s15="voltopl", s20="voltopl", u15="Enrolled respondents (SIM 2015)", u20="Enrolled respondents (SIM 2020)")
both("edu_ft", "voltopl", "voltopl", yn12=True)
V("edu_cur_lvl3", "edu", "Level of current education, 3 levels", s02="HUIDOPL", s03="HUIDOPL", s15="huidopl", s20="huidopl_kl", valueset="edu3_att",
  universe="Enrolled persons; SIM in classes as delivered, SPVA/SPVN recoded from the detailed level (edu_cur_lvl)",
  notes="SCP levels: low = primary/vbo/mavo (vmbo), middle = mbo/havo/vwo, high = hbo/wo. SPVA 2002 bridge class (0) -> low. SIM 2020 code 9 -> .d, or .c for persons not enrolled (derive kl9_route).")
MM("edu_cur_lvl3", "spva2002", "HUIDOPL", [(0, 1), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
MM("edu_cur_lvl3", "spvn2003", "HUIDOPL", [(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3), (9, ".a")])
M("edu_cur_lvl3", S15, "huidopl", 96, ".d"); M("edu_cur_lvl3", S20, "huidopl_kl", 9, ".d")
S("edu_nl", s15="oplnl", s20="oplnl", u15="All respondents (SIM 2015)", u20="All respondents (SIM 2020)")
both("edu_nl", "oplnl", "oplnl", yn12=True)
V("edu_nl_att_lvl3", "edu", "Highest education attended in the Netherlands, 3 levels", s02="MAXOPLNL", s03="MAXOPLNL", s15="maxoplnl", s20="maxoplnl_kl", valueset="edu3",
  universe="Persons who attended education in NL; SPVA/SPVN recoded from edu_nl_att_hi, SIM as delivered",
  notes="SPVA/SPVN code -1 (no education at all) -> 0, code 0 (education abroad only) -> .c. SIM 2020 code 9 -> .d, or .c for persons without education in NL (derive kl9_route).")
for k in ("spva2002", "spvn2003"):
    MM("edu_nl_att_lvl3", k, "MAXOPLNL", [(-1, 0), (0, ".c"), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
MM("edu_nl_att_lvl3", S15, "maxoplnl", [(-4, ".c"), (-6, ".d"), (96, ".d")]); M("edu_nl_att_lvl3", S20, "maxoplnl_kl", 9, ".d")
S("edu_nl_att_dipl", s15="diplnl1", s20="diplnl1", u15="Respondents who attended education in NL (SIM 2015)", u20="Respondents who attended education in NL (SIM 2020)")
both("edu_nl_att_dipl", "diplnl1", "diplnl1", [(1, 1), (2, 0), (-4, ".c")], [(1, 1), (2, 0), (-3, ".c"), (-6, ".a")])
V("edu_nl_dipl_lvl3", "edu", "Highest diploma obtained in the Netherlands, 3 levels", s02="MAXDIPNL", s03="MAXDIPNL", s15="maxdiplnl", valueset="edu3",
  universe="Persons not enrolled (SPVA/SPVN); all respondents (SIM 2015 derived variable)",
  notes="SPVA/SPVN: -1 no diploma -> 0, 0 diploma abroad only -> .c. SIM 2015: -1/-2/-3 no Dutch diploma -> 0, 0 diploma abroad only -> .c, -5 in full-time education -> .c, -4 -> .a, -6 -> .d.")
for k in ("spva2002", "spvn2003"):
    MM("edu_nl_dipl_lvl3", k, "MAXDIPNL", [(-1, 0), (0, ".c"), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
MM("edu_nl_dipl_lvl3", S15, "maxdiplnl", [(-7, "."), (-6, ".d"), (-5, ".c"), (-4, ".a"), (-3, 0), (-2, 0), (-1, 0), (0, ".c")])
V("edu_dipl_hi_lvl3", "edu", "Highest diploma obtained (NL or abroad), 3 levels incl. none; persons not in full-time education", s02="MAXDIP", s03="MAXDIPA", s15="maxdip", valueset="edu3",
  universe="Persons not in full-time education as their main activity (ISEO/SCP 'niet-schoolgaanden' = edu_part 0; persons enrolled part-time or alongside another main activity are included)",
  notes="SPVA 2002 recoded from 8 levels, SPVN 2003 from 4 classes, SIM 2015 as delivered (SCP Laag/Middel/Hoog; the source label 'inc schoolgaanden' is a copy of maxdsch's, the variable is -5 for full-time students); -4 -> .d. "
        "The universe is the SCP/ISEO definition of 'not in education' (full-time education as main activity), not 'not enrolled': SPVA 324 and SIM 2015 314 enrolled persons (edu_enr = 1) have a value because their education is not their main activity. Highest diploma including full-time students: edu_dipl_all_lvl3.")
MM("edu_dipl_hi_lvl3", "spva2002", "MAXDIP", [(0, 0), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
MM("edu_dipl_hi_lvl3", "spvn2003", "MAXDIPA", [(0, 0), (1, 1), (2, 1), (3, 2), (4, 3)])
MM("edu_dipl_hi_lvl3", S15, "maxdip", [(-7, "."), (-4, ".d")])
V("edu_dipl_all_lvl3", "edu", "Highest diploma obtained so far (incl. enrolled), 3 levels incl. none", s02="MAXDSCH", s03="MAXDSCHA", s15="maxdsch", valueset="edu3",
  universe="All interviewed persons (SPVA/SPVN), all respondents (SIM 2015)")
MM("edu_dipl_all_lvl3", "spva2002", "MAXDSCH", [(0, 0), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
MM("edu_dipl_all_lvl3", "spvn2003", "MAXDSCHA", [(0, 0), (1, 1), (2, 1), (3, 2), (4, 3)])
MM("edu_dipl_all_lvl3", S15, "maxdsch", [(-7, "."), (-4, ".d")])
V("edu_dipl_cur_lvl3", "edu", "Highest diploma incl. level of current education, 3 levels (SIM 2015 derived)", s15="maxdipnu", valueset="edu3", universe=U_SIM15,
  notes="SCP construct: enrolled persons get the level of the education they are currently following.")
MM("edu_dipl_cur_lvl3", S15, "maxdipnu", [(-7, "."), (-4, ".d")])
S("edu_part", s15="ondpart", u15="All respondents (SIM 2015 derived variable)")
V("edu_prtnr_lvl3", "edu", "Highest completed education of partner, 3 levels incl. none", s15="maxdipp", valueset="edu3", universe="Respondents with a partner, SIM 2015 only")
MM("edu_prtnr_lvl3", S15, "maxdipp", [(1, 0), (2, 1), (3, 2), (4, 3), (96, ".d")])
V("edu_fa_lvl3", "edu", "Highest diploma of father, 3 levels incl. none", s02="MAXDIPPA", s03="MAXDIPAA", s15="maxdippa", s20="maxdippa", valueset="edu3",
  universe="All respondents; SPVA/SPVN recoded from the detailed parental level",
  wording="Answer categories: SPVA 2002 Dutch levels (8); SPVN 2003 4 levels; SIM 2015 'nooit naar school / laag / middel / hoog'; SIM 2020 'geen onderwijs / lagere school / middelbare school / hoger onderwijs' (secondary school = middle, see edu_fa_det4).")
V("edu_ma_lvl3", "edu", "Highest diploma of mother, 3 levels incl. none", s02="MAXDIPMA", s03="MAXDIMAA", s15="maxdipma", s20="maxdipma", valueset="edu3",
  universe="All respondents; SPVA/SPVN recoded from the detailed parental level")
for t, v02, v03 in [("edu_fa_lvl3", "MAXDIPPA", "MAXDIPAA"), ("edu_ma_lvl3", "MAXDIPMA", "MAXDIMAA")]:
    MM(t, "spva2002", v02, [(0, 0), (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3)])
    MM(t, "spvn2003", v03, [(0, 0), (1, 1), (2, 1), (3, 2), (4, 3), (7, ".a")])
    src = "maxdippa" if t == "edu_fa_lvl3" else "maxdipma"
    MM(t, S15, src, [(1, 0), (2, 1), (3, 2), (4, 3), (96, ".d")])
    MM(t, S20, src, [(1, 0), (2, 1), (3, 2), (4, 3), (92, ".d")])
V("edu_fa_det4", "edu", "Highest school diploma of father, SIM 2020 categories", s20="maxdippa", valueset="edu_parent4", universe=U_SIM20)
V("edu_ma_det4", "edu", "Highest school diploma of mother, SIM 2020 categories", s20="maxdipma", valueset="edu_parent4", universe=U_SIM20)
M("edu_fa_det4", S20, "maxdippa", 92, ".d"); M("edu_ma_det4", S20, "maxdipma", 92, ".d")
V("edu_enr_type_reg", "edu", "Type of education enrolled in (registry 2014/15 resp. classes)", s15="onderwijssoort", s20="onderwijssoort_kl", valueset="enr_type_reg",
  universe="Respondents enrolled in education according to the registry", notes="SIM 2015 string codes VO/MBO/HBO/WO/VE; empty = not enrolled (.c). SIM 2020 classes middel/hoog; 9 = not enrolled or unknown -> .c.")
MM("edu_enr_type_reg", S15, "onderwijssoort", [("'VO'", 1), ("'MBO'", 2), ("'HBO'", 3), ("'WO'", 4), ("'VE'", 5), ("''", ".c")])
MM("edu_enr_type_reg", S20, "onderwijssoort_kl", [(1, 6), (2, 7), (9, ".c")])

# ============================================================== lab_
S("lab_emp", s15="nuwerk", s20="nuwerk", u15="All respondents (SIM 2015)", u20="All respondents (SIM 2020)")
both("lab_emp", "nuwerk", "nuwerk", yn12=True)
S("lab_emptype", s15="zelfst", u15="Employed respondents (SIM 2015): employee vs not; self-employed/family business/freelance detail in lab_se_type",
  wording="SIM 2015 asks 'Werkt u als werknemer in loondienst?' (yes / 'diversen'); the self-employment detail comes from a follow-up (lab_se_type). Code 2 here = not an employee.")
MM("lab_emptype", S15, "zelfst", [(1, 1), (2, 2)])
V("lab_se_type", "lab", "Self-employed: own business, family business or freelance", s15="zelffree", valueset="selfemp3", universe="Employed respondents not in paid employment, SIM 2015 only")
V("lab_ind_sbi08", "lab", "Industry of current job (SBI 2008, 2-digit division)", s15="bedrijf_cod", valueset="src_bedrijf_cod", universe="Employed respondents, SIM 2015 only",
  notes="Labels from the source file (SBI 2008 divisions 1-99; 101 = 'anders namelijk'). SPVA/SPVN use SBI-93 (lab_ind). Code 100 'weet niet' -> .a.")
S("lab_hrs", s15="urenwrk1", s20="urenwrk1", u15="Employees (SIM 2015): contractual hours", u20="Employed respondents (SIM 2020): contractual hours")
V("lab_hrs_se", "lab", "Working hours per week, self-employed (approximate)", s15="urenwrkz", type="num", universe="Self-employed respondents, SIM 2015 only")
S("lab_12h", s15="urenwr1x", u15="Employees who did not report contractual hours (SIM 2015)")
V("lab_12h_se", "lab", "Works 12 hours or more per week (self-employed, when hours not reported)", s15="urenwr2x", valueset="hours12", universe="Self-employed respondents who did not report hours, SIM 2015 only")
S("lab_match", s15="onderben", u15="Employed respondents (SIM 2015)")
S("lab_perm", s15="vastwerk", u15="Employees (SIM 2015)")
V("lab_coll_bal", "lab", "At work more contact with native Dutch or with own group (employees)", s15="contactw", valueset="contact_balance", universe="Employees, SIM 2015 only (natives asked about contact with persons with a migration background vs native Dutch)")
M("lab_coll_bal", S15, "contactw", 99, ".a")
V("lab_coll_bal_se", "lab", "At work more contact with native Dutch or with own group (self-employed)", s15="contacwz", valueset="contact_balance", universe="Self-employed respondents, SIM 2015 only (natives as for lab_coll_bal)")
M("lab_coll_bal_se", S15, "contacwz", 99, ".a")
for i, (src, lab) in enumerate([("gevwerk", "dangerous work"), ("zwaarwerk", "physically heavy work"), ("snelwerk", "working very fast")], 1):
    V(f"lab_cond{i:02d}", "lab", f"Working conditions: how often {lab}", s15=src, valueset="freq4_av", universe="Employed respondents, SIM 2015 only")
S("lab_exp", s15="arbervj", u15="Employed respondents (SIM 2015): total years worked in NL (months in lab_exp_mo)")
V("lab_exp_mo", "lab", "Months of work experience in addition to lab_exp", s15="arbervm", type="num", universe="Employed respondents, SIM 2015 only")
V("lab_exp_prev", "lab", "Years of work experience in NL (persons not working now)", s15="arberv_wj", type="num", universe="Respondents not working now who ever worked in NL, SIM 2015 only")
V("lab_exp_prev_mo", "lab", "Months of work experience in addition to lab_exp_prev", s15="arberv_wm", type="num", universe="Respondents not working now who ever worked in NL, SIM 2015 only")
S("lab_everwork", s15="werknl", u15="Respondents not working now (SIM 2015)")
yn("lab_everwork", S15, "werknl")
S("lab_nowork_yrs", s15="nrwrkduurj", u15="Respondents not working now who ever worked (SIM 2015): years since last job")
V("lab_nowork_mo", "lab", "Months since last job in addition to lab_nowork_yrs", s15="nrwrkduurm", type="num", universe="Respondents not working now who ever worked, SIM 2015 only")
S("lab_act", s15="hfdact", s20="hfdact", u15="Respondents without paid work (SIM 2015)", u20="Respondents without paid work (SIM 2020)",
  wording="SPVA/SPVN include 'working 12 hours or more' (code 0); SIM asks the question only to persons without paid work.")
MM("lab_act", S15, "hfdact", [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 5), (96, 6)])
MM("lab_act", S20, "hfdact", [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 5), (92, 6)])
V("lab_want5", "lab", "Would like paid work now (5 categories)", s15="wilw12uv2", valueset="wants_work5", universe="Respondents without paid work, SIM 2015 only")
S("lab_want", s15="wilw12uv2", u15="Respondents without paid work (SIM 2015); codes 4 'already found work' -> 1 and 5 'would like to but cannot' -> 3 (detail in lab_want5)")
MM("lab_want", S15, "wilw12uv2", [(1, 1), (2, 2), (3, 3), (4, 1), (5, 3)])
V("lab_srch2m", "lab", "Did something in the past two months to find work", s15="zoek2m", valueset="yesno", universe="Respondents without paid work who want work, SIM 2015 only")
yn("lab_srch2m", S15, "zoek2m")

# ============================================================== inc_
V("inc_pers_reg", "inc", "Personal income, bands (registry; 2013 for SIM 2015, 2019 for SIM 2020)", s15="CATpersinkomen", s20="inppersink_kl", valueset="inc_band",
  universe="All respondents, SIM 2015 and SIM 2020", notes="Each survey uses its own bands (codes 1-6 vs 11-15); nominal euro of the income year, not deflated.")
MM("inc_pers_reg", S15, "CATpersinkomen", [(9, 99)]); MM("inc_pers_reg", S20, "inppersink_kl", [(1, 11), (2, 12), (3, 13), (4, 14), (5, 15), (9, 90)])
V("inc_hh_std_reg", "inc", "Standardised disposable household income, bands (registry; 2013 resp. 2019)", s15="CATgestbesthhinkomen", s20="inhgestinkh_kl", valueset="inc_band",
  universe="All respondents, SIM 2015 and SIM 2020", notes="SIM 2020 top band 4 = 75,000 or more (code 16).")
MM("inc_hh_std_reg", S15, "CATgestbesthhinkomen", [(9, 99)]); MM("inc_hh_std_reg", S20, "inhgestinkh_kl", [(1, 11), (2, 12), (3, 13), (4, 16), (9, 90)])
V("inc_hh_pct_reg", "inc", "Disposable household income, percentile group (registry 2019)", s20="inhp100hbest_kl", valueset="pct_band5", universe=U_SIM20)
V("inc_sec_reg", "inc", "Socio-economic category, main income source (registry 2019)", s20="inpsecj_kl", valueset="sec_reg4", universe=U_SIM20)

# ============================================================== trn_
V("trn_remit", "trn", "Household sent money to the country of origin in the past 12 months", s15="geldherk", valueset="yesno", universe=U_MIG15)
yn("trn_remit", S15, "geldherk")
V("trn_house", "trn", "Respondent (or parents) owns a house in the country of origin", s15="huisbui", valueset="yesno", universe=U_MIG15)
MM("trn_house", S15, "huisbui", [(1, 1), (2, 0), (98, ".b")])
V("trn_cont_fam", "trn", "Frequency of contact with family in the country of origin", s15="conherk", valueset="freq5_cont", universe=U_MIG15)
M("trn_cont_fam", S15, "conherk", 9, ".c")
V("trn_visit12m", "trn", "Visited the country of origin in the past 12 months", s15="bez2010her", valueset="yesno", universe=U_MIG15)
yn("trn_visit12m", S15, "bez2010her")
V("trn_visit_dur", "trn", "Length of (last) visit to the country of origin", s15="bez2010lang", valueset="visit_dur3", universe="Respondents who visited the country of origin, SIM 2015 only")
V("trn_doctor", "trn", "Went to the country of origin for a doctor or hospital in the past year", s15="dokland", valueset="yesno", universe=U_MIG15)
yn("trn_doctor", S15, "dokland")
V("trn_gov01", "trn", "Origin-country government should not interfere with group in NL (agreement)", s15="inmengfout", valueset="agree5", universe=U_MIG15)
V("trn_gov02", "trn", "Good if origin-country government engages with group in NL (agreement)", s15="inmengok", valueset="agree5", universe=U_MIG15)

# ============================================================== hous_
V("hous_tenure", "hous", "Tenure of dwelling (self-reported)", s15="koopwon", valueset="tenure3", universe=U_SIM15)
M("hous_tenure", S15, "koopwon", 3, 98)
V("hous_tenure_reg", "hous", "Tenure of dwelling (registry)", s15="koopofhuurwoning", s20="typeeigendom", valueset="tenure_reg", universe="All respondents, SIM 2015 (2014) and SIM 2020",
  notes="String codes E (eigen) / H (huur) / O (onbekend) converted; empty -> .d.")
MM("hous_tenure_reg", S15, "koopofhuurwoning", [("'E'", 1), ("'H'", 2), ("''", ".d")]); MM("hous_tenure_reg", S20, "typeeigendom", [("'E'", 1), ("'H'", 2), ("'O'", 9), ("''", ".d")])
V("hous_landlord", "hous", "From whom the dwelling is rented", s15="wiehuur", valueset="landlord", universe="Tenants, SIM 2015 only")
M("hous_landlord", S15, "wiehuur", 7, 98)
V("hous_dw_type", "hous", "Type of dwelling", s15="soorthuis", valueset="dwelling_type", universe=U_SIM15)
M("hous_dw_type", S15, "soorthuis", 7, 98)
V("hous_share_kit_n", "hous", "Number of persons the kitchen is shared with", s15="keukdeel", type="num", universe="Respondents in shared accommodation, SIM 2015 only")
V("hous_share_bath_n", "hous", "Number of persons the toilet/bathroom is shared with", s15="wcdeel", type="num", universe="Respondents in shared accommodation, SIM 2015 only")
V("hous_sat", "hous", "Satisfaction with current dwelling", s15="tevrhuis", valueset="satisfied5", universe=U_SIM15)

# ============================================================== lang_
S("lang_nl_prtnr", s15="taalpart", s20="taalpart", u15="Respondents with a partner, migration background (SIM 2015)", u20="Respondents with a partner, migration background (SIM 2020)")
S("lang_nl_chd", s15="taalkind", s20="taalkind", u15="Respondents with children, migration background (SIM 2015)", u20="Respondents with children, migration background (SIM 2020)")
find("lang_prob_spk")["valueset"] = "lang_prob4"
S("lang_prob_spk", s15="taalgesp", s20="taalgesp", u15=U_MIG15, u20=U_MIG20_G1,
  wording="SPVA 2002: often/sometimes/never. SIM adds 'ik spreek geen Nederlands' (code 4).")
both("lang_prob_spk", "taalgesp", "taalgesp", [(1, 4), (2, 1), (3, 2), (4, 3)], [(1, 4), (2, 1), (3, 2), (4, 3)])
S("lang_prob_read", s15="taalkran", s20="taalkran", u15=U_MIG15, u20=U_MIG20_G1)
V("lang_prob_write", "lang", "Problems writing Dutch", s15="taalpen", s20="taalpen", valueset="freq3", universe=U_MIG)
U("lang_prob_write", S20, U_MIG20_G1)
V("lang_orig_follow", "lang", "Can follow a conversation in a language of the country of origin", s15="etnigesp", valueset="yes_bit_no", universe=U_MIG15)
V("lang_orig_prob", "lang", "Problems speaking the origin-country language", s15="etnispre", valueset="freq3", universe="Respondents who can follow a conversation in the origin language, SIM 2015 only")
V("lang_prob_eng", "lang", "Problems in a conversation in English", s15="engfrdui", s20="engtaal", valueset="lang_prob4", universe="SIM 2015: respondents with a migration background; SIM 2020: all respondents", u15=U_MIG15, u20=U_SIM20)
both("lang_prob_eng", "engfrdui", "engtaal", [(1, 4), (2, 1), (3, 2), (4, 3)], [(1, 4), (2, 1), (3, 2), (4, 3)])
V("lang_nl_self10", "lang", "Self-rated spoken Dutch (1 none - 10 very good)", s20="taalcijfer", type="num", universe=U_MIG20_G1)

# ============================================================== iden_ / ret_
V("iden_nl5", "iden", "Feels Dutch (strength)", s15="voelnl", s20="voelnl", valueset="strength5", universe="SIM 2015: respondents with a migration background; SIM 2020: all respondents", u15=U_MIG15, u20=U_SIM20)
V("iden_orig5", "iden", "Feels member of the origin group (strength)", s15="voellvh", s20="voellvh", valueset="strength5", universe=U_MIG)
V("iden_mun5", "iden", "Feels inhabitant of own town/village (strength)", s20="voelgemeente", valueset="strength5", universe=U_SIM20)
S("iden_scale", s15="zelfiden", u15=U_MIG15, wording="Same 5-point scale; SIM 2015 question text 'Voelt u zich: meer (herkomst) of meer Nederlander of beide evenveel?'")
V("iden_home_nl", "iden", "Feels at home in the Netherlands", s15="thuisnl", s20="thuisnl", valueset="home3", universe="All respondents, SIM 2015 and SIM 2020")
S("ret_wish", s15="wilterug", u15=U_MIG15, wording="SIM 2015 offers yes/no with 'weet niet' recorded as -3 (mapped to code 2).")
MM("ret_wish", S15, "wilterug", [(1, 1), (2, 3), (-3, 2)])
V("ret_fut5y", "ret", "Expected country of residence in five years", s15="toekherk", s20="toekherk", valueset="future_res4", universe=U_MIG)

# ============================================================== soc_
S("soc_visit_nl", s15="bezoek", s20="bezoek", u15="All respondents (SIM 2015; natives asked about visits from persons with a migration background)",
  u20="All respondents (SIM 2020; natives asked about visits from persons with a migration background)",
  wording="SPVA 2002: 'autochtone Nederlandse vrienden'. SIM: text filled per group - migrants asked about 'autochtone Nederlandse' visitors, the native reference sample about 'allochtone' (2015) / 'personen met een migratieachtergrond' (2020). Interpret for natives as contact with the other group.")
S("soc_leis_nl", s15="vrtijdnl", s20="vrtijdnl", u15="All respondents (SIM 2015; natives: leisure contact with persons with a migration background)", u20="All respondents (SIM 2020; same)")
S("soc_cont_bal", s15="contactv", s20="contactv", u15=U_MIG15, u20=U_MIG20)
for t, s, lab in [("soc_cont_nbr_org", "contball", "neighbours / local people of own origin group"), ("soc_cont_frnd_org", "contall", "friends or acquaintances of own origin group"),
                  ("soc_cont_frnd_nl", "contaut", "native Dutch friends or acquaintances"), ("soc_cont_nbr_nl", "contbaut", "native Dutch neighbours / local people")]:
    V(t, "soc", f"Frequency of contact with {lab}", s15=s, s20=s, valueset="freq5_cont",
      universe="All respondents, SIM 2015 and SIM 2020 (for the native reference sample the own-group items were asked about persons with a migration background)")
V("soc_cont_want", "soc", "Would like more contact with the other group", s15="contwens", valueset="want_contact3", universe=U_SIM15)
for i, (g, lab) in enumerate([("mar", "Moroccans"), ("tur", "Turks"), ("ant", "Antilleans/Arubans"), ("sur", "Surinamese"), ("pol", "Poles"), ("aut", "native Dutch")], 1):
    V(f"soc_grp{i:02d}", "soc", f"Frequency of contact with {lab}", s15=f"anveel{g}", valueset="freq4_vrsn", universe="All respondents, SIM 2015 only; own group asked last (randomised order)")
V("soc_trust_gen", "soc", "Generalised trust: most people can be trusted", s15="vertrouw", valueset="trust2", universe=U_SIM15)
V("soc_volunteer", "soc", "Did voluntary work in the past 12 months", s15="vrijw", s20="vrijw", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020")
both("soc_volunteer", "vrijw", "vrijw", yn12=True)
V("soc_sport5", "soc", "Frequency of sport in the past 12 months", s15="fqsport", s20="fqsport", valueset="sport5", universe="All respondents, SIM 2015 and SIM 2020",
  notes="SIM 2020 code -1 = Farsi questionnaire offered 'once a year' instead of 'a few times a year' -> 4.")
M("soc_sport5", S20, "fqsport", -1, 4)
V("soc_meet12m", "soc", "Attended meetings of associations or organisations in the past 12 months", s20="organ", valueset="yesno", universe=U_SIM20)
yn("soc_meet12m", S20, "organ")
for i, (s, lab) in enumerate([("migr", "own origin group"), ("autnl", "native Dutch background"), ("ander", "another migration background")], 1):
    V(f"soc_meet_sh{i:02d}", "soc", f"Share of people at these meetings with {lab}", s20=f"organ_{s}", valueset="share5", universe="Respondents who attended meetings, SIM 2020 only" + (" (migration background only)" if i == 1 else ""))
V("soc_belong_assoc", "soc", "Feels a sense of belonging at meetings of own associations (agreement)", s20="organbij", valueset="agree5", universe="Group A respondents who attended meetings, SIM 2020 only")
for i, (s, lab) in enumerate([("baan", "colleagues in current job"), ("studie", "fellow students at school"), ("buurt", "people in the neighbourhood")], 1):
    V(f"soc_belong{i:02d}", "soc", f"Feels a sense of belonging among {lab} (agreement)", s20=f"contacterbij_{s}", valueset="agree5", universe=U_A)
for pre, lab in [("frnd", "good friends"), ("acq", "acquaintances"), ("col", "colleagues at work"), ("edu", "people in education/study"), ("nbh", "people in the neighbourhood")]:
    src = {"frnd": "contactvriend", "acq": "contactken", "col": "contactcol", "edu": "contactopl", "nbh": "contactbuurt"}[pre]
    for i, (s, who) in enumerate([("migr", "own origin group"), ("autnl", "native Dutch background"), ("ander", "another migration background")], 1):
        V(f"soc_sh_{pre}{i:02d}", "soc", f"Share of {lab} with {who}", s20=f"{src}_{s}", valueset="share5",
          universe=("Respondents with a migration background, SIM 2020" if i == 1 else "All respondents, SIM 2020") + ("; only persons with colleagues / in education" if pre in ("col", "edu") else ""))

# ============================================================== med_ (media use)
for t, s15, s20, lab in [("med_tv_nl", "tvned", None, "Dutch television channels"), ("med_tv_orig", "tveig", None, "origin-group television channels"),
                         ("med_web_orig", "inteig", None, "origin-group websites")]:
    V(f"{t}_cat", "med", f"Use of {lab} (frequency classes)", s15=s15, valueset="media_freq5", universe=U_SIM15 if t == "med_tv_nl" else U_MIG15)
for i, (s, lab) in enumerate([("tv", "television"), ("radio", "radio"), ("krant", "newspapers"), ("tijdsch", "magazines"), ("boek", "books or e-books"),
                              ("socmed", "social media"), ("media_nvt", "none of these")], 1):
    V(f"med_use{i:02d}", "med", f"Media used in a normal week: {lab}", s20=s, valueset="mentioned", universe=U_SIM20)
DAYS = [("tvpub", "Dutch public television"), ("tvcom", "Dutch commercial television"), ("tvherk", "origin-group television channels"),
        ("tvstream", "streaming services (films, series)"), ("tvarab", "Arabic-language foreign television"), ("tvbuit", "other foreign television"),
        ("radnl", "Dutch radio"), ("radherk", "origin-country radio"), ("radstream", "audio streaming services"), ("radarab", "Arabic-language radio"),
        ("radeng", "other foreign radio"), ("krantnl", "Dutch newspapers"), ("sitesnl", "Dutch news websites/apps"), ("krantherk", "origin-group newspapers"),
        ("siteherk", "origin-group news websites/apps"), ("sitearab", "other Arabic-language newspapers/news sites"), ("sitebuit", "other foreign newspapers/news sites"),
        ("tijdsnl", "Dutch magazines"), ("tijdsherk", "origin-group magazines"), ("tijdsbuit", "other foreign magazines"), ("boeknl", "Dutch-language books"),
        ("boekherk", "origin-language books"), ("boekbuit", "books in another language"), ("socmedge", "social media (incl. blogs, vlogs)")]
for i, (s, lab) in enumerate(DAYS, 1):
    V(f"med_d{i:02d}", "med", f"Days per week: {lab}", s20=s, type="num", universe="SIM 2020 respondents who use the medium (routing from med_use01-06); origin/Arabic items by group")
for i, (s, lab) in enumerate([("intnl", "domestic news / news about NL"), ("intherk", "news about the country of origin"), ("intbuit", "other foreign news")], 1):
    V(f"med_int{i:02d}", "med", f"Interest in {lab}", s20=s, valueset="interest4", universe=U_A + (" (migration background only)" if i == 2 else ""))
V("med_amt01", "med", "Opinion on the amount of news about the country of origin in Dutch media", s20="freqnieu", valueset="amount3", universe=U_A + " (migration background only)")
V("med_amt02", "med", "Opinion on the number of persons with a migration background on Dutch TV", s20="freqaant", valueset="amount3", universe=U_A)
for i, (s, lab) in enumerate([("posherk", "the country of origin"), ("posland", "persons with own origin background"), ("posmig", "persons with a migration background"), ("posmos", "Muslims")], 1):
    V(f"med_pos{i:02d}", "med", f"Reporting in Dutch media about {lab} is negative/positive", s20=s, valueset="positive5", universe="Group A respondents with a migration background, SIM 2020 only")

# ============================================================== att_
S("att_gr01", s15="manaanka", s20="manaanka", u15=U_SIM15, u20=U_SIM20)
S("att_gr03", s15="mangeld", s20="mangeld", u15=U_SIM15, u20=U_SIM20)
S("att_gr06", s15="inkjongs", s20="inkjongs", u15=U_SIM15, u20=U_SIM20)
S("att_gr07", s15="vrwstopw", s20="vrwstopw", u15=U_SIM15, u20=U_SIM20)
V("att_gr08", "att", "Men and women should share housework equally (agreement)", s20="mvhuish", valueset="agree5", universe=U_B)
V("att_hom01", "att", "Gay men and lesbian women should be free to live as they wish (agreement)", s15="homolev", s20="homolev", valueset="agree5", universe="All respondents, SIM 2015 and SIM 2020")
V("att_hom02", "att", "Good that homosexuals may marry each other (agreement)", s15="homohuw", s20="homohuw", valueset="agree5", universe="All respondents, SIM 2015 and SIM 2020")
V("att_hom03", "att", "Problem if own child had a steady partner of the same sex (agreement, SIM 2020)", s20="homofam", valueset="agree5", universe=U_SIM20,
  wording="SIM 2015 asked the same situation on a 'problematic' scale (att_hom03_prb); SIM 2020 as an agree/disagree statement.")
V("att_hom03_prb", "att", "Child with a steady same-sex partner: how problematic (SIM 2015)", s15="homofam", valueset="problem5", universe=U_SIM15)
V("att_hom04", "att", "Offensive when two men walk hand in hand in the street (agreement)", s15="homoacc", s20="homoacc", valueset="agree5", universe="All respondents, SIM 2015 and SIM 2020")
V("att_free01", "att", "Everyone free to say what they think, even if it offends a religion (agreement)", s20="vruitgod", valueset="agree5", universe=U_B)
V("att_free02", "att", "Everyone free to say what they think, even if it is hurtful (agreement)", s20="vruitkwet", valueset="agree5", universe=U_B)
V("att_sat_nl10", "att", "Opinion of Dutch society (1 very dissatisfied - 10 very satisfied)", s15="tevrned", s20="tevrned", type="num", universe="All respondents, SIM 2015 and SIM 2020")
for i, (s, lab) in enumerate([("tempmar", "Moroccans"), ("temptur", "Turks"), ("tempant", "Antilleans"), ("tempsur", "Surinamese"), ("temppol", "Poles"),
                              ("tempaut", "native Dutch"), ("tempjod", "Jews")], 1):
    V(f"att_therm{i:02d}", "att", f"Feeling thermometer towards {lab} (0 very negative - 100 very positive)", s15=s, type="num",
      universe="All respondents, SIM 2015 only; groups in randomised order, own group last, Jews never first")
V("att_rel05", "att", "Religion should play an important role in politics (agreement)", s15="relpol", valueset="agree5", universe=U_SIM15)
V("att_isl01", "att", "Western and Muslim ways of life are incompatible (agreement)", s15="moslleef", valueset="agree5", universe=U_SIM15)
V("att_isl02", "att", "People in the Netherlands are far too negative about Islam (agreement)", s15="islnega", s20="islnega", valueset="agree5", universe="Respondents with a migration background (SIM 2015: Muslim respondents; SIM 2020: migration background)", u15=U_MUS, u20=U_MIG20)
S("att_soc01", s15="cultdiv", s20="cultdiv", u15=U_SIM15, u20=U_SIM20)
S("att_rel02", s15="geenreld", s20="geenreld", u15=U_SIM15, u20=U_SIM20)
S("att_soc05", s15="veelallo", u15=U_SIM15, wording="SPVA 2002 and SIM 2015 'allochtonen'; not asked in SIM 2020.")
S("att_soc08", s15="slechtwk", u15=U_SIM15)
S("att_nl01", s15="kansallo", s20="kansallo", u15="All respondents (SIM 2015), incl. the native reference sample", u20="All respondents (SIM 2020), incl. the native reference sample",
  wording="Wording of the subject changed: SPVA/SPVN 'buitenlander/allochtoon', SIM 2015 'allochtoon', SIM 2020 'persoon met een migratieachtergrond'.")
S("att_nl03", s15="resprech", s20="resprech", u15="All respondents (SIM 2015), incl. the native reference sample", u20="All respondents (SIM 2020), incl. the native reference sample", wording="Subject term changed as for att_nl01.")
S("att_nl04", s15="nlgastv", s20="nlgastv", u15="All respondents (SIM 2015), incl. the native reference sample", u20="All respondents (SIM 2020), incl. the native reference sample", wording="Subject term changed as for att_nl01.")
S("att_nl08", s15="openculta", s20="openculta", u15="All respondents (SIM 2015), incl. the native reference sample", u20="All respondents (SIM 2020), incl. the native reference sample", wording="SPVA/SPVN 'buitenlandse culturen', SIM 2015 'allochtone culturen', SIM 2020 'andere culturen'.")
V("att_nl09", "att", "I will never become Dutch in the eyes of most Dutch people (agreement)", s20="nooitnl", valueset="agree5", universe=U_MIG20)
V("att_grp01", "att", "Within the origin community people keep a close eye on each other (agreement)", s15="soccon", valueset="agree5", universe=U_MIG15)
V("att_grp02", "att", "Within the origin community there is often pressure on you (agreement)", s15="normconf", valueset="agree5", universe=U_MIG15)
V("att_grp03", "att", "My family has (had) much influence on my choice of partner (agreement)", s15="huwdwang", valueset="agree5", universe=U_MIG15)
S("att_chd_frnd_orig", s15="afkvriki", u15="All respondents, SIM 2015 (natives asked about friends with a migration background)")
S("att_chd_prtnr_orig", s15="afkparki", s20="afkparki", u15="All respondents, SIM 2015 (natives asked about a partner with a migration background)", u20="All respondents, SIM 2020 (same)")
V("att_tens10", "att", "Perceived tension between natives and migrants in NL (1 none - 10 very much)", s15="wrijving", type="num", universe=U_SIM15)
V("att_tens_grow", "att", "Expects tensions between natives and migrants to grow", s15="spangroe", valueset="tension3", universe=U_SIM15)
V("att_piet01", "att", "Zwarte Piet is hurtful (agreement)", s15="kwetspiet", s20="kwetspiet", valueset="agree5", universe="All respondents SIM 2015; group B SIM 2020")
V("att_piet02", "att", "Zwarte Piet may be changed (agreement)", s15="sintfeest", valueset="agree5", universe=U_SIM15)
V("att_piet03", "att", "Good that the appearance of Zwarte Piet is being changed (agreement)", s20="pietaanpas", valueset="agree5", universe=U_B)
V("att_fear_ext", "att", "Afraid of violence by Muslim extremists in NL", s15="extrem", valueset="fear4", universe=U_SIM15)
V("att_fear_vio", "att", "Afraid of violence against Muslims in NL", s15="geweld", valueset="fear4", universe=U_SIM15)
V("att_viol01", "att", "Understanding for young people who leave NL to join IS", s15="issteun", valueset="understand3", universe=U_SIM15)
V("att_viol02", "att", "Understanding for people who use violence for their faith", s15="geweldgeloof", valueset="understand3", universe=U_SIM15)

# ============================================================== pol_ (politics)
V("pol_trust_gov10", "pol", "Trust in the Dutch government (1 very little - 10 very much)", s15="vertrreg", type="num", universe=U_SIM15)
V("pol_trust_pol10", "pol", "Trust in the police (1-10)", s15="vertrpol", type="num", universe=U_SIM15)
V("pol_trust_hlth10", "pol", "Trust in health care (1-10)", s15="vertrzorg", type="num", universe=U_SIM15)
for t, s, lab in [("pol_trust_jus4", "vertrjus", "Dutch judges"), ("pol_trust_pol4", "vertrpol", "the Dutch police"), ("pol_trust_gov4", "vertreg", "the Dutch government"),
                  ("pol_trust_orig4", "vertrher", "the government of the country of origin"), ("pol_trust_hlth4", "vertrgez", "Dutch health care")]:
    V(t, "pol", f"Trust in {lab} (4-point)", s20=s, valueset="trust4", universe=U_A if t != "pol_trust_orig4" else "Group A respondents with a migration background, SIM 2020 only")
V("pol_rep01", "pol", "Interests of people like me are well represented in parliament (agreement)", s20="belparl", valueset="agree5", universe=U_B)
V("pol_rep02", "pol", "Good if more persons with a migration background were in parliament (agreement)", s20="migtk", valueset="agree5", universe=U_B)
V("pol_vote_nl", "pol", "Voted in the last Dutch parliamentary election (2017)", s20="stemtk", valueset="voted3", universe=U_SIM20)
V("pol_vote_int", "pol", "Would vote if parliamentary elections were held now", s20="stemint", valueset="vote_int5", universe=U_SIM20)
V("pol_party", "pol", "Party the respondent would probably vote for", s20="stempart", valueset="party_nl", universe="Respondents who would (maybe) vote, SIM 2020 only",
  notes="Codes as in the source (13 FvD, 15 blank, 16 does not know yet, 92 other party).")
for i, (s, lab) in enumerate([("polpart", "contacted a political party or politician"), ("polbijeen", "attended a political meeting or hearing"),
                              ("polprot", "took part in a protest or demonstration"), ("poldisc", "took part in political discussion or action online")], 1):
    V(f"pol_part{i:02d}", "pol", f"Political participation in NL (past 2 years): {lab}", s20=s, valueset="yesno", universe=U_A)
    yn(f"pol_part{i:02d}", S20, s)
for i, (s, lab) in enumerate([("herkdisc", "political discussion or action online"), ("herkpart", "contacted a political party or politician"), ("herkprot", "protest or demonstration")], 1):
    V(f"pol_orig{i:02d}", "pol", f"Political participation concerning the country of origin (past 2 years): {lab}", s20=s, valueset="yesno", universe="Group A respondents with a migration background, SIM 2020 only")
    yn(f"pol_orig{i:02d}", S20, s)
V("pol_vote_orig", "pol", "Voted in the last national election of the country of origin", s20="stemherk", valueset="voted3", universe="Respondents with a migration background (not Caribbean), SIM 2020 only")
V("pol_vote_carib", "pol", "Voted in the last election of one of the Caribbean islands", s20="stemherk2", valueset="voted3", universe="Caribbean-Dutch respondents, SIM 2020 only")

# ============================================================== disc_
S("disc_perc", s15="discalg", s20="discalg", u15=U_MIG15, u20="All respondents (SIM 2020), incl. the native reference sample",
  wording="SPVA 2002: discrimination of own group. SIM: 'allochtonen' (2015) / 'personen met een migratieachtergrond' (2020) in general; own group asked separately (disc_perc_grp).")
V("disc_perc_grp", "disc", "Perceived frequency of discrimination against own origin group by native Dutch", s15="discalg2", s20="discalg2", valueset="freq5_disc", universe=U_MIG)
S("disc_exp", s15="disczelf", s20="disczelf", u15=U_MIG15, u20=U_MIG20)
for i, (s, lab) in enumerate([("discsoll", "when applying for a job or internship"), ("discwerk", "at work"), ("discopl", "at school, in class"),
                              ("discstraat", "in the street, shops, public transport"), ("discclub", "at a club or sports association"), ("discuit", "when going out")], 1):
    V(f"disc_sit{i:02d}", "disc", f"Experienced discrimination {lab}", s20=s, valueset="freq4_disc", universe="Group B respondents with a migration background who ever experienced discrimination, SIM 2020 only")

# ============================================================== rel_
V("rel_any", "rel", "Belongs to a religion", s15="gelooft", s20="gelooft", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020")
both("rel_any", "gelooft", "gelooft", yn12=True)
S("rel_den_det", s15="CATreligie", u15="Religious respondents (SIM 2015; categories as delivered)",
  wording="SIM 2015 delivered denomination in condensed categories; SIM 2020 in two coarsened class lists (rel_den_det from religie_kl for Turkish/Moroccan/Somali/Iranian groups and religie2_kl for the others).")
MM("rel_den_det", S15, "CATreligie", [(0, ".d"), (1, 34), (4, 38), (5, 35), (6, 39), (7, 31), (8, 13), (9, 25), (11, 22), (12, 99)])
M("rel_den_cat", S15, "CATreligie", 0, ".d")
# CATreligie 0 covers two groups: respondents without a religion (gelooft 2; the derive rule rel_none sets them to 0 from
# rel_any) and 40 respondents who belong to a religion but whose denomination is unknown (gelooft 1, blank in the CBS
# detail): the latter stay .d (restricted component, 3 Nov 2026)
_r = find("rel_den_det"); _r["notes"] += " SIM 2015: CATreligie 0 is .d in the value map and becomes 0 'No religion' through the rule rel_none only for respondents who say they belong to no religion (rel_any 0); the 40 respondents with a religion but no denomination (gelooft 1, blank denomination) stay .d. CATreligie 4 'Christelijk: Overig' also holds open 'other religion' answers that the SCP coded into the classes, so the DANS and CBS (restricted component) distributions of the other-religion codes differ by design."
_r = find("rel_den_cat"); _r["notes"] += " SIM 2015: CATreligie 0 -> .d, then 0 through rel_none for respondents without a religion; 40 respondents with a religion but no denomination stay .d."
S("rel_den_det", s20="religie_kl", u20="Religious respondents (SIM 2020): religie_kl for the Turkish/Moroccan/Somali/Iranian groups, merged with religie2_kl for the other groups (derive rel_merge20)")
find("rel_den_det")["derive"] = "rel_merge20"
find("rel_den_det")["notes"] += " SIM 2020 (CCF classes): religie_kl 1 Shia -> 21, 2 Sunni -> 22, 3 other Islam -> 25, 4 Christian -> 38, 9 -> .d; religie2_kl 1 Islam -> 25, 2 RC -> 31, 3 Hervormd -> 32, 4 PKN -> 39, 5/6 Christian general/other -> 38, 7 Hindu -> 13, 9 -> .d."
MM("rel_den_det", S20, "religie_kl", [(1, 21), (2, 22), (3, 25), (4, 38), (9, ".d")])
V("rel_den_det20b", "rel", "Religious denomination, SIM 2020 second group list (AUT/CAR/SUR/POO; merged into rel_den_det)", s20="religie2_kl", valueset="religion_det",
  universe="Religious respondents of the AUT/CAR/SUR/POO groups, SIM 2020", include=0)
MM("rel_den_det20b", S20, "religie2_kl", [(1, 25), (2, 31), (3, 32), (4, 39), (5, 38), (6, 38), (7, 13), (9, ".d")])
S("rel_den_cat", s15="CATreligie", u15="Religious respondents (SIM 2015)", u20="Religious respondents (SIM 2020, derived from rel_den_det20 by derive rel_cat20)")
MM("rel_den_cat", S15, "CATreligie", [(1, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 1), (9, 2), (11, 2), (12, 4)])
find("rel_den_cat")["derive"] = "rel_cat20"
S("rel_attend", s15="kerkbez", s20="kerkbez", u15="Religious respondents (SIM 2015)", u20="Religious respondents (SIM 2020)",
  wording="SPVA/SPVN 4 categories (never / few times a year / few times a month / weekly+). SIM 5 categories (daily / weekly / monthly / few times a year / never): daily and weekly -> weekly+, monthly -> few times a month. Detail in rel_attend5.")
both("rel_attend", "kerkbez", "kerkbez", [(1, 4), (2, 4), (3, 3), (4, 2), (5, 1)], [(1, 4), (2, 4), (3, 3), (4, 2), (5, 1)])
V("rel_attend5", "rel", "Attendance of religious meetings, 5 categories", s15="kerkbez", s20="kerkbez", valueset="attendance5", universe="Religious respondents, SIM 2015 and SIM 2020")
V("rel_id01", "rel", "My faith is an important part of myself (agreement)", s15="relzelf", s20="relzelf", valueset="agree5", universe="Religious respondents, SIM 2015 and SIM 2020")
V("rel_id02", "rel", "It hurts when someone says something bad about my faith (agreement)", s15="relkwet", s20="relkwet", valueset="agree5", universe="Religious respondents, SIM 2015 and SIM 2020")
V("rel_id03", "rel", "Being (religion) is something I often think about (agreement)", s15="reldenk", s20="reldenk", valueset="agree5", universe="Religious respondents, SIM 2015 and SIM 2020")
V("rel_pray", "rel", "Frequency of prayer", s15="gebed", s20="gebed", valueset="pray6", universe="Religious respondents, SIM 2015 and SIM 2020")
V("rel_read", "rel", "Frequency of reading the Koran / Bible", s20="bijbkor", valueset="read5", universe="Religious respondents in group B, SIM 2020 only")
V("rel_ramadan", "rel", "Fasted during the last Ramadan", s15="ramadan", s20="ramadan", valueset="observe4", universe="Muslim respondents, SIM 2015 and SIM 2020")
V("rel_halal", "rel", "Eats halal", s15="halal", s20="halal", valueset="observe4", universe="Muslim respondents, SIM 2015 and SIM 2020")
V("rel_rule", "rel", "Believers must live by the rules of Islam / the Bible (agreement)", s15="isregel", s20="isregel", valueset="agree5", universe="SIM 2015: Muslim respondents; SIM 2020: religious respondents (Muslims and Christians)",
  wording="SIM 2015: 'Ik vind dat moslims helemaal volgens de regels van de islam moeten leven'. SIM 2020 generalised: 'Elke <moslim/christen> moet leven volgens de regels van de <islam/bijbel>'.")
V("rel_interp", "rel", "Every believer may interpret the Koran / Bible as he wishes (agreement)", s20="korzelfint", valueset="agree5", universe="Religious respondents in group B, SIM 2020 only")
V("rel_veil", "rel", "Wears a headscarf when going out", s15="zhfddoek", s20="zhfddoek", valueset="yesno", universe="Muslim women, SIM 2015 and SIM 2020")
both("rel_veil", "zhfddoek", "zhfddoek", yn12=True)

# ============================================================== hlth_
S("hlth_self", s15="gezond", s20="gezond", u15=U_SIM15, u20=U_SIM20,
  wording="SPVA 2002 'uitstekend/goed/neutraal/slecht/zeer slecht'; SIM 'zeer goed/goed/gaat wel/slecht/zeer slecht'.")
V("hlth_lim_eff", "hlth", "Difficulty with strenuous activities because of health", s15="bezig", s20="bezig", valueset="difficulty3", universe="All respondents, SIM 2015 and SIM 2020")
V("hlth_lim_stairs", "hlth", "Difficulty climbing a few flights of stairs because of health", s15="trap", s20="trap", valueset="difficulty3", universe="All respondents, SIM 2015 and SIM 2020")
V("hlth_role01", "hlth", "Past 4 weeks: achieved less than wanted because of physical health", s15="licbereikt", valueset="yesno", universe=U_SIM15)
V("hlth_role02", "hlth", "Past 4 weeks: could not do certain work/activities because of physical health", s15="licnietdoen", s20="licnietdoen", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020")
V("hlth_role03", "hlth", "Past 4 weeks: achieved less than wanted because of emotional problems", s15="emobereikt", valueset="yesno", universe=U_SIM15)
V("hlth_role04", "hlth", "Past 4 weeks: did work/activities less carefully because of emotional problems", s15="emonietdoen", s20="emonietdoen", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020")
for t, s15, s20 in [("hlth_role01", "licbereikt", None), ("hlth_role02", "licnietdoen", "licnietdoen"), ("hlth_role03", "emobereikt", None), ("hlth_role04", "emonietdoen", "emonietdoen")]:
    both(t, s15, s20, yn12=True)
V("hlth_pain", "hlth", "Past 4 weeks: pain interfered with normal activities", s15="pijn", s20="pijn", valueset="pain4", universe="All respondents SIM 2015; group B SIM 2020")
for i, (s, lab) in enumerate([("kalm", "felt calm and peaceful"), ("somber", "felt downhearted and gloomy"), ("energie", "had a lot of energy")], 1):
    V(f"hlth_mh4_{i:02d}", "hlth", f"Past 4 weeks: {lab} (4-point)", s15=s, valueset="freq4_mh", universe=U_SIM15)
MHI = [("zenuw", "felt very nervous"), ("neersl", "felt downhearted and gloomy"), ("kalm", "felt calm and peaceful"), ("energ", "had a lot of energy"),
       ("depr", "felt so down that nothing could cheer you up"), ("geluk", "felt happy"), ("slaap", "slept well"), ("eenz", "felt lonely")]
for i, (s, lab) in enumerate(MHI, 1):
    V(f"hlth_mhi{i:02d}", "hlth", f"Past 4 weeks: {lab} (6-point)", s20=f"mental_{s}", valueset="freq6_mhi",
      universe=U_B if i in (4, 7, 8) else U_SIM20)
V("hlth_soc_lim", "hlth", "Past 4 weeks: health or emotional problems hampered visiting family/friends", s15="bezoekmog", s20="bezoekmog", valueset="freq4_lim", universe="All respondents SIM 2015; group B SIM 2020")
S("hlth_gp2m", s15="huisarts", s20="huisarts", u15=U_SIM15, u20=U_B)
V("hlth_spec_last", "hlth", "Last contact with a medical specialist", s15="conspec", valueset="last_contact3", universe=U_SIM15)
S("hlth_spec", s20="arts_medspec", u20="All respondents (SIM 2020): contact in the past 12 months")
yn("hlth_spec", S20, "arts_medspec")
S("hlth_hosp", s15="ziekhuis", u15="All respondents (SIM 2015): admitted in the past 12 months, day or overnight (detail in hlth_hosp3)")
MM("hlth_hosp", S15, "ziekhuis", [(1, 1), (2, 1), (3, 0)])
V("hlth_hosp3", "hlth", "Hospital admission in the past 12 months: day / overnight / no", s15="ziekhuis", valueset="hospital3", universe=U_SIM15)
V("hlth_psych", "hlth", "Contact with a psychologist/psychiatrist in the past 12 months", s15="psycho", s20="arts_psych", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020")
both("hlth_psych", "psycho", "arts_psych", yn12=True)
V("hlth_altmed", "hlth", "Contact with an alternative healer in the past 12 months", s15="altgen", valueset="yesno", universe=U_SIM15)
yn("hlth_altmed", S15, "altgen")
V("hlth_gp12m", "hlth", "Contact with a GP in the past 12 months", s20="arts_huisarts", valueset="yesno", universe=U_SIM20)
yn("hlth_gp12m", S20, "arts_huisarts")
V("hlth_dent12m", "hlth", "Contact with a dentist in the past 12 months", s20="arts_tandarts", valueset="yesno", universe=U_SIM20)
yn("hlth_dent12m", S20, "arts_tandarts")
V("hlth_care_rcv3", "hlth", "Received help or care because of health in the past 12 months", s15="mantel", valueset="care_rcv3", universe=U_SIM15)
for i, (s, lab) in enumerate([("fam", "from partner, family, friends, acquaintances or neighbours"), ("prof", "professional help (home care, municipality, district nursing)"),
                              ("btld", "from a self-paid domestic help"), ("anders", "from someone else"), ("nee", "no help received"), ("wn", "don't know")], 1):
    V(f"hlth_care_rcv{i:02d}", "hlth", f"Help/care received in the past 12 months: {lab}", s20=f"mantel_{s}", valueset="mentioned", universe=U_SIM20)
V("hlth_care_from", "hlth", "Relation to the person from whom most help was received", s20="hulpvanwie", valueset="relation8", universe="Respondents who received informal help, SIM 2020 only")
V("hlth_care_need", "hlth", "Needs (more) help because of health", s20="hulpmant", valueset="yesno", universe="Respondents who received help, SIM 2020 only")
yn("hlth_care_need", S20, "hulpmant")
V("hlth_care_need2", "hlth", "Needs help because of health (persons who received none)", s20="hulpmant2", valueset="yesno", universe="Respondents who received no help, SIM 2020 only")
yn("hlth_care_need2", S20, "hulpmant2")
BAR = [("wistkonniet", "does not know how to arrange it"), ("nietaanmer", "thinks he/she is not eligible"), ("teduur", "thinks it costs too much"),
       ("slechteerv", "bad experiences (own or others')"), ("niethelp", "thinks family cannot help"), ("profhelp", "thinks professionals cannot give the help needed"),
       ("orgkrijgniet", "applied but has not (yet) received the help"), ("hulpanders", "other reason")]
for i, (s, lab) in enumerate(BAR, 1):
    V(f"hlth_care_bar{i:02d}", "hlth", f"Reason for not getting (more) help: {lab}", s20=s, valueset="yesno", universe="Respondents who received help and need more, SIM 2020 only")
    yn(f"hlth_care_bar{i:02d}", S20, s)
    V(f"hlth_care_bar{i+10:02d}", "hlth", f"Reason for not getting help (persons who received none): {lab}", s20=f"{s}2", valueset="yesno", universe="Respondents who received no help and need it, SIM 2020 only")
    yn(f"hlth_care_bar{i+10:02d}", S20, f"{s}2")
V("hlth_care_give", "hlth", "Gave informal help or care in the past 12 months", s15="manthlp", s20="manthlp", valueset="yesno", universe="All respondents, SIM 2015 and SIM 2020")
both("hlth_care_give", "manthlp", "manthlp", yn12=True)
V("hlth_care_to", "hlth", "Relation to the person to whom most help was given", s20="hulpaanwie", valueset="relation8", universe="Respondents who gave help, SIM 2020 only",
  notes="Code -1 (wrong question in the Farsi version) -> .d.")
V("hlth_height_cm", "hlth", "Height in cm", s15="lengte", s20="lengte", type="num", universe="All respondents, SIM 2015 and SIM 2020", notes="SIM 2015: 0 -> .d; SIM 2020: values >= 990 -> .a.")
V("hlth_weight_kg", "hlth", "Weight in kg", s15="gewicht", s20="gewicht", type="num", universe="All respondents, SIM 2015 and SIM 2020", notes="SIM 2015: 0 -> .d; SIM 2020: values >= 990 -> .a.")
for t, s in [("hlth_height_cm", "lengte"), ("hlth_weight_kg", "gewicht")]:
    M(t, S15, s, 0, ".d"); M(t, S20, s, "990-999", ".a")

# derive flags for the SIM 2020 code-9 routing rule and the 'no religion' rule (post-processing in 03_derive)
for t in ("dem_prtnr_bc_cbs", "dem_prtnr_fa_bc_cbs", "dem_prtnr_ma_bc_cbs", "dem_prtnr_age_cat", "edu_abr_att_lvl3", "edu_cur_lvl3",
          "edu_nl_att_lvl3", "lab_ind_sbi08", "svy_ncontact", "mig_reg_days", "mig_motive_ind_reg",
          "mig_mot_arb_reg", "mig_mot_asi_reg", "mig_mot_gez_reg", "mig_mot_stu_reg"):
    find(t)["derive"] = "kl9_route"
    find(t)["notes"] += " Persons routed past the question (system-missing or code 9 in the source) are .c (derive kl9_route)."
find("rel_den_det")["notes"] += " SIM: respondents without a religion (rel_any = 0) are coded 0 (derive rel_none)."

# ============================================================== questionnaire links that the name match cannot make
# (format "Qid#k" = k-th item of a battery block; "" = registry / administrative variable without a questionnaire item)
for v in ("geslachtsd", "leeftijdsd_kl", "kanaal", "versie", "manier", "Volgnummer", "eindgewicht", "generatiesd", "etngrp_kl"):
    L(S20, v, "")
for v in ("bron", "status", "jaar", "maand", "jr", "mnd", "duur", "countcontact", "volgnummer", "gengba", "etngba", "oplblnl",
          "startgewicht", "correctiegewicht", "eindgewicht", "correctiegewichtalt", "eindgewichtalt", "ondpart", "maxdiplnl", "maxdiplbl", "maxdsch", "maxdip", "maxdipnu"):
    L(S15, v, "")
L(S15, "verblijfsduur", "")               # registry: days registered in the BRP
L(S15, "CATreligie", "Q930")
L(S20, "engtaal", "Q662")
for i, v in enumerate(["woon_alleen", "woon_kind", "woon_partner", "woon_ouders", "woon_andrfam", "woon_anders"], 1):
    L(S20, v, f"Q100#{i}")
for v in ("redmigr_werk", "redmigr_studie", "redmigr_soczek", "redmigr_polred", "redmigr_armoed", "redmigr_intrek", "redmigr_hwlk",
          "redmigr_gzheid", "redmigr_toekkind", "redmigr_ouders", "redmigr_partner", "redmigr_anders"):
    L(S20, v, "Q200")
for v in ("organ_migr", "organ_autnl", "organ_ander"):
    L(S20, v, "Q1401")
for v in ("contacterbij_baan", "contacterbij_studie", "contacterbij_buurt"):
    L(S20, v, "Q1403")
# share of contacts by origin: five settings printed as five blocks (Q1404 friends; Q14041 acquaintances; Q14042 colleagues;
# Q14043 fellow students; Q14044 neighbourhood), three items each
for q, vs_ in [("Q1404", ["contactvriend_migr", "contactvriend_autnl", "contactvriend_ander"]), ("Q14041", ["contactken_migr", "contactken_autnl", "contactken_ander"]),
               ("Q14042", ["contactcol_migr", "contactcol_autnl", "contactcol_ander"]), ("Q14043", ["contactopl_migr", "contactopl_autnl", "contactopl_ander"]),
               ("Q14044", ["contactbuurt_migr", "contactbuurt_autnl", "contactbuurt_ander"])]:
    for i, v in enumerate(vs_, 1):
        L(S20, v, f"{q}#{i}")
L(S20, "tv", "Q950"); L(S20, "media_nvt", "Q950#7"); L(S20, "radnl", "Q961"); L(S20, "radarab", "Q961#4"); L(S20, "krantherk", "Q962#2")   # items printed without number/name in the PDF
for v in ("discsoll", "discwerk", "discopl", "discstraat", "discclub", "discuit"):
    L(S20, v, "Q902")
for i, v in enumerate(["mental_zenuw", "mental_neersl", "mental_kalm", "mental_energ"], 1):
    L(S20, v, f"Q160061#{i}")
for i, v in enumerate(["mental_depr", "mental_geluk", "mental_slaap", "mental_eenz"], 1):
    L(S20, v, f"Q160062#{i}")
for v in ("arts_huisarts", "arts_medspec", "arts_psych", "arts_tandarts"):
    L(S20, v, "Q16014")
L(S20, "mantel_anders", "Q1016")
for v in ("wistkonniet", "nietaanmer", "teduur", "slechteerv", "niethelp", "profhelp", "orgkrijgniet", "hulpanders"):
    L(S20, v, "Q101622"); L(S20, v + "2", "Q10163")
L(S20, "stemherk2", "Q8531")
W("pol_vote_carib", "SIM 2020: the Caribbean-Dutch group was asked the same question (Q8531) about the elections of their island instead of a national parliament.")

# ---- CCF education classes of SIM 2015 / SIM 2020: boundaries differ from the harmonized three-level definition --------
# Established by the restricted component from the CBS microdata code lists (3 Nov 2026; decisions.md section 14): every
# DANS class count equals the sum of a set of detailed CBS levels, and the sets show which levels the CCF classes combine.
# The public files hold the classes only, so the values stay as delivered; the notes and a reviewed comparability verdict
# (crosswalks/comparability_review.csv) say where they are not comparable with the other surveys.
_CCF_NOTE = {
    "edu_abr_att_lvl3": "SIM 2015 and SIM 2020 deliver the CCF classes, whose boundaries differ from the harmonized definition: SIM 2015 counts mavo as middle; SIM 2020 counts mavo as middle and havo/vwo as high. At those boundaries the cells are not comparable with the other surveys (counts per detailed level from the CBS microdata: decisions.md section 14); the restricted component re-derives the classes from the detailed levels.",
    "edu_nl_att_lvl3": "SIM 2015 and SIM 2020 deliver the CCF classes, whose boundaries differ from the harmonized definition: SIM 2015 counts mavo as middle; SIM 2020 counts mavo as middle and havo/vwo as high. At those boundaries the cells are not comparable with the other surveys (decisions.md section 14); the restricted component re-derives the classes from the detailed levels.",
    "edu_fa_lvl3": "SIM 2015 delivers the CCF classes, which count mavo as middle (harmonized definition: low) and an uncompleted primary school as low (harmonized: none); not comparable with the other surveys at those boundaries (decisions.md section 14).",
    "edu_ma_lvl3": "SIM 2015 delivers the CCF classes, which count mavo as middle (harmonized definition: low) and an uncompleted primary school as low (harmonized: none); not comparable with the other surveys at those boundaries (decisions.md section 14).",
    "edu_prtnr_lvl3": "SIM 2015 delivers the CCF classes, which count mavo as middle (harmonized definition: low) and an uncompleted primary school as low (harmonized: none); not comparable with the other surveys at those boundaries (decisions.md section 14).",
    "edu_cur_lvl3": "SIM 2020 delivers the CCF classes: vmbo-t counts as middle and havo/vwo as high, and primary and vmbo-b/k sit in code 9 together with other answers and refusals, so SIM 2020 has no identifiable 'low' class (.d, or .c by kl9_route); decisions.md section 14.",
}
for _t, _n in _CCF_NOTE.items():
    _r = find(_t); _r["notes"] = (_r["notes"] + " " if _r["notes"] else "") + _n

# ---- registry marital status: 'Ongehuwd' means not married, not never married (restricted component, 3 Nov 2026) --------
_r = find("dem_mar_reg"); _r["notes"] = _r["notes"] + " SIM 2015 / SIM 2020: the source category 'Ongehuwd' (O, 2) includes divorced and widowed persons - the CBS microdata distinguish never married (O), divorced (S) and widowed (W), which the DANS files merge; code 2 therefore means 'not married', as labelled, not 'never married'."
