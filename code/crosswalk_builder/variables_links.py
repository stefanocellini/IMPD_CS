# -*- coding: utf-8 -*-
"""Relationship layer for the household surveys (v0.4.2, audit decision 1).

SPVA 2002 and SPVN 2003 interview the head of household and list every household member in the roster; the partner of
the head is a record of her/his own (interviewed with the mini questionnaire when aged 12+).  The SIM/SING/LAS person
samples instead ask the respondent about the partner (proxy report).  So that the partner variables of the person samples
are not simply 'not collected' in SPVA/SPVN, the partner is linked through the roster and her/his own harmonized values
are copied onto the focal person's row:

- id_prtnr: id_person of the co-resident partner = the other 'head/partner' member (dem_poshh 0 or 1) of the same
  household when exactly one exists; .c no co-resident partner (head/partner without a second head/partner record);
  .d not identifiable (other members, or a roster with more than two head/partner records); .e person samples.
- partner_copy:<target>: for rows with a link, the partner's own value of <target> where the partner variable is not
  collected in the survey (.e); a partner who was not interviewed (roster-only, 'not collected' on her/his own row) gives
  .d.  Heads/partners without a link get .c, other members .d.  Existing head-reported values (dem_prtnr_brthcntry,
  dem_prtnr_age in SPVA/SPVN) are kept; the copy only fills empty cells.
- dem_has_prtnr / dem_prtnr_cores: from the link and the LAT question (dem_prtnr_lat).

The reporter of a copied value is the partner (self-report, or head-reported roster demography for roster-only
partners); the codebook's reporter metadata records this per survey.  Children are not linked: the SIM child modules
describe one selected child or children in general and have no roster counterpart; SPVA/SPVN children remain rows of
their own (dem_poshh 2) and household counts (hh_nchd*) summarise them.
"""
from declare import V, U, W, find, VARS

S02, S03 = "spva2002", "spvn2003"
HH = (S02, S03)

V("id_prtnr", "id", "Identifier (id_person) of the co-resident partner's own record in the household roster", type="id",
  universe="Heads of household and their partners in the household samples (SPVA 2002, SPVN 2003); person samples .e", derive="id_prtnr",
  notes="Link of the relationship layer: the other head/partner member (dem_poshh 0 or 1) of the same household when exactly one exists. "
        ".c = no co-resident partner record; .d = not identifiable (other household members; no roster in the DANS files has more than two head/partner records). Stored as double.")
VARS.insert(VARS.index(find("id_hh")) + 1, VARS.pop())        # keep the identifiers together at the top of the file

# partner variables of the person samples filled from the linked partner's own record in SPVA/SPVN
PCOPY = {
    "dem_prtnr_sex": "dem_sex", "dem_prtnr_age": "dem_age", "dem_prtnr_age_cat": "dem_age_cat", "dem_prtnr_age_cat3": "dem_age_cat3",
    "dem_prtnr_brthcntry": "dem_brthcntry", "dem_prtnr_eth": "dem_eth", "dem_prtnr_gen": "dem_gen",
    "edu_prtnr_lvl3": "edu_dipl_hi_lvl3", "dem_prtnr_emp": "lab_emp", "dem_prtnr_hrs": "lab_hrs",
    "mig_yr_arr_prtnr": "mig_yr_arr", "mig_reason_prtnr": "mig_reason",
}
for t, src in PCOPY.items():
    r = find(t)
    assert r["derive"] in ("", "kl9_route"), (t, r["derive"])
    r["derive"] = f"partner_copy:{src}" if r["derive"] == "" else r["derive"] + f"|partner_copy:{src}"   # 'kl9_route|partner_copy:...' for dem_prtnr_age_cat
    for s in HH:
        if r[f"src_{s}"]:   # head-reported source exists: the copy fills the partner's row from the head's own record
            U(t, s, "Heads of household (own report about the partner) and their co-resident partners (copied from the head's own record via id_prtnr) "
                    "(SPVA 2002, SPVN 2003): .c no co-resident partner, .d other household members")
        else:
            U(t, s, "Heads of household and their co-resident partners (SPVA 2002, SPVN 2003), from the partner's own record via id_prtnr: "
                    ".c no co-resident partner; .d other household members, and partners listed in the roster but not interviewed where the base item needs an interview (roster demography is available for them)")
    r["notes"] = (r["notes"] + " " if r["notes"] else "") + \
        f"SPVA 2002 / SPVN 2003: filled from the linked partner's own {src} (relationship layer, id_prtnr); the person samples hold the respondent's proxy report."

for t, rule in [("dem_has_prtnr", "has_prtnr_roster"), ("dem_prtnr_cores", "prtnr_cores_roster")]:
    r = find(t)
    assert r["derive"] == "", (t, r["derive"])
    r["derive"] = rule
    for s in HH:
        U(t, s, "Heads of household and their partners (SPVA 2002, SPVN 2003): from the roster link (id_prtnr) and the living-apart-together question (dem_prtnr_lat); "
                + ("co-resident link -> 1; LAT partner without a link -> 1; head/partner without link or LAT partner -> 0" if t == "dem_has_prtnr" else
                   "co-resident link -> 1; LAT partner without a link -> 0; head/partner without link or LAT partner -> .c") + "; .d other household members (relationship not identifiable)")
    r["notes"] = (r["notes"] + " " if r["notes"] else "") + "SPVA 2002 / SPVN 2003: derived from the roster link and dem_prtnr_lat (relationship layer, rule " + rule + ")."
