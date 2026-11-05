* 03_derive.do : derived variables (mirrors code/R/03_derive.R; every rule is named in variable_map.csv, column derive)
*   create rules:   id_hh, id_person | geo_mun_cbs / _name | *_15 CPI-deflated amounts
*   post-processing: fill0_interviewed | age_cat | brthcntry_group | cit_nl_orig | mode_video | split_random |
*                    kl9_route | rel_merge20 | rel_none | rel_cat20 | system-missing -> .d/.c per survey (sysmis_tag) in flat surveys
use "$INT/harmonized_all_stata.dta", clear
impd_define_labels
impd_flag_flat

* ---- identifiers
* svy_key (surveys.csv): immutable per-survey key (fieldwork year), so identifiers are stable across releases
gen double _svykey = .
foreach s in $SURVEYS {
    quietly replace _svykey = ${SVYKEY_`s'} if svy_id == ${SVYID_`s'}
}
gen double id_hh     = cond(_flat, .e, _svykey * 1e9 + HHNUMMER)
gen double id_person = cond(_flat, _svykey * 1e11 + PERSNR, id_hh * 100 + GEZLIDNR)
drop _svykey
label values id_hh vs_missing
label values id_person vs_missing
isid id_person

* ---- municipality: survey code -> CBS gemeentecode (crosswalks/municipalities.csv); hh_pp_ro surveys only
gen str8 survey = lower(svy_name)
frlink m:1 survey _GEMEENTE, frame(cw_muni survey source_code) gen(_mlink)
frget cbs_code cbs_name, from(_mlink)
quietly count if _GEMEENTE < . & _GEMEENTE >= 0 & _mlink == .
if r(N) > 0 {
    display as error "municipality codes without CBS match"
    list survey _GEMEENTE if _GEMEENTE < . & _GEMEENTE >= 0 & _mlink == ., sepby(survey)
    exit 459
}
gen double geo_mun_cbs = real(cbs_code)
quietly replace geo_mun_cbs = .d if _GEMEENTE == . | _GEMEENTE < 0
quietly replace geo_mun_cbs = .e if _flat
gen str30 geo_mun_name = cbs_name
label values geo_mun_cbs vs_missing
label variable geo_mun_cbs  "Municipality of residence (CBS gemeentecode, 2006 list)"
label variable geo_mun_name "Municipality of residence (name)"
drop _mlink cbs_code cbs_name survey _GEMEENTE

* ---- CPI deflation to constant 2015 euro (crosswalks/cpi.csv, 2015 = 100)
frlink m:1 svy_year, frame(cw_cpi year) gen(_cpil)
frget cpi_2015, from(_cpil)
gen double _f = 100 / cpi_2015
frame cw_vm: quietly levelsof rowid if regexm(derive, "^cpi2015:"), local(rows)
foreach r of local rows {
    frame cw_vm: local t = target[`r']
    frame cw_vm: local spec = subinstr(derive[`r'], "cpi2015:", "", 1)
    frame cw_vm: local vlabel = label_en[`r']
    local base `spec'
    local yr
    if strpos("`spec'", "@") {                                   // cpi2015:<base>@<year>: fixed reference year (SIM 2006 amounts refer to 2005)
        local base = substr("`spec'", 1, strpos("`spec'", "@") - 1)
        local yr = substr("`spec'", strpos("`spec'", "@") + 1, .)
    }
    if "`yr'" != "" {
        frame cw_cpi {
            quietly summarize cpi_2015 if year == `yr', meanonly
            local fy = 100 / r(mean)
        }
        gen double `t' = `base' * `fy'
    }
    else gen double `t' = `base' * _f
    quietly replace `t' = `base' if missing(`base')          // keep tagged missings
    label values `t' vs_missing
    local vlabel = usubstr(`"`vlabel'"', 1, 80)                                   // Unicode-aware: never cut inside a multi-byte character
    while strlen(`"`vlabel'"') > 80 {                                          // and within the 80-byte limit
        local vlabel = usubstr(`"`vlabel'"', 1, ustrlen(`"`vlabel'"') - 1)
    }
    label variable `t' `"`vlabel'"'
}
drop _cpil cpi_2015 _f

* ---- fill0_interviewed: system-missing -> 0 for interviewed persons
frame cw_vm: quietly levelsof target if derive == "fill0_interviewed", local(fills) clean
foreach t of local fills {
    quietly replace `t' = 0 if `t' == . & inlist(svy_resptype, 1, 2)
}

* ---- age_cat: classes 15-24 ... 75+ (0 = under 15) from dem_age where dem_age_cat is .e
quietly replace dem_age_cat = cond(dem_age < 15, 0, min(floor((dem_age - 15) / 10) + 1, 7)) if dem_age_cat == .e & dem_age < .
quietly replace dem_age_cat = dem_age if dem_age_cat == .e & !_flat & dem_age >= .     // carry the missing tag of dem_age

* ---- age_cat3: common 3-class age (15-24, 25-44, 45+) from dem_age_cat where dem_age_cat3 is .e (SING delivers it)
quietly replace dem_age_cat3 = cond(dem_age_cat == 0, .c, cond(dem_age_cat == 1, 1, cond(inlist(dem_age_cat, 2, 3), 2, 3))) if dem_age_cat3 == .e & dem_age_cat < .
quietly replace dem_age_cat3 = dem_age_cat if dem_age_cat3 == .e & dem_age_cat >= . & dem_age_cat != .e    // carries .a/.b/.d and a still-untagged blank (tagged per survey below)

* ---- brthcntry_group: SIM (CBS definition) first generation -> country of the origin group, otherwise Netherlands
quietly replace dem_brthcntry = 6030 if dem_brthcntry == .e & _flat & inlist(dem_gen, 0, 2)
foreach pair in "1 6043" "2 5022" "3 5007" "4 7011" "5 6023" "6 5043" "7 5012" "8 6045" "9 6013" "10 7028" "11 6022" "90 6030" {
    gettoken g c : pair
    quietly replace dem_brthcntry = `c' if dem_brthcntry == .e & _flat & dem_gen == 1 & dem_eth == `g'
}
quietly replace dem_brthcntry = .d if dem_brthcntry == .e & _flat & dem_gen == 1 & dem_eth < .    // 'other' / unknown origin group: country unknown
quietly replace dem_brthcntry = dem_gen if dem_brthcntry == .e & _flat & dem_gen >= . & dem_gen != .e   // generation unknown / not applicable: carry its tag
* brthcntry_src: provenance flag (1 observed in the household surveys, 2 inferred in the person samples)
quietly replace dem_brthcntry_src = cond(_flat, 2, cond(dem_brthcntry == .e, .e, 1))

* ---- routing_mig: did the CAPI script give this person the migrant-background routing?  (person samples)
quietly replace svy_routing_mig = 0 if _flat
foreach g in lang_prob_spk lang_prob_read iden_scale iden_orig5 int_crs int_nlcrs trn_house med_krant_orig_cat {
    capture confirm variable `g'
    if _rc continue
    quietly replace svy_routing_mig = 1 if _flat & (`g' < . | inlist(`g', .a, .b, .d))
}

* ---- cit_nl_orig: 1 Dutch only, 2 dual, 3 origin only, 4 neither; natives (not asked) .c
quietly replace nat_cit = 2  if nat_cit == .e & _flat & nat_nl == 1 & nat_orig == 1
quietly replace nat_cit = 1  if nat_cit == .e & _flat & nat_nl == 1 & nat_orig == 0
quietly replace nat_cit = 3  if nat_cit == .e & _flat & nat_nl == 0 & nat_orig == 1
quietly replace nat_cit = 4  if nat_cit == .e & _flat & nat_nl == 0 & nat_orig == 0
quietly replace nat_cit = .c if nat_cit == .e & _flat & dem_eth == 90

* ---- mode_video
quietly replace svy_mode = 3 if svy_video == 1

* ---- split_random: non-zero value of the eight random_* variables (SIM 2020 source file)
capture confirm file "$INT/sim2020_main.dta"
local has20 = (_rc == 0)
if `has20' {
    preserve
        use Volgnummer random_* using "$INT/sim2020_main.dta", clear
        gen double PERSNR = Volgnummer
        egen double _split = rowmax(random_*)
        quietly replace _split = .d if _split == 0 | _split == .
        gen byte svy_id = ${SVYID_sim2020}
        keep svy_id PERSNR _split
        tempfile split
        quietly save "`split'"
    restore
    quietly merge m:1 svy_id PERSNR using "`split'", nogen keep(master match)
    quietly replace svy_split = _split if svy_id == ${SVYID_sim2020}
    drop _split
}

* ---- kl9_route: SIM constructed/coarsened variables carry no routing code -> .c where the routing question says so
foreach rule in "dem_prtnr_bc_cbs dem_has_prtnr 0" "dem_prtnr_fa_bc_cbs dem_has_prtnr 0" "dem_prtnr_ma_bc_cbs dem_has_prtnr 0" ///
                "dem_prtnr_age_cat dem_has_prtnr 0" "edu_abr_att_lvl3 edu_abr 0" "edu_cur_lvl3 edu_enr 0" "edu_nl_att_lvl3 edu_nl 0" ///
                "lab_ind_sbi08 lab_emp 0" "svy_ncontact svy_mode 1" "mig_reg_days dem_gen 0" "mig_reg_days dem_gen 2" ///
                "mig_motive_ind_reg dem_gen 0" "mig_motive_ind_reg dem_gen 2" "edu_nl_att_lvl3 edu_nl c" "edu_abr_att_lvl3 edu_abr c" ///
                "edu_cur_lvl3 edu_enr c" "dem_prtnr_age_cat dem_prtnr_cores 0" "lab_ind_sbi08 lab_emptype 2" "lab_ind_sbi08 lab_emp c" {
    gettoken t rest : rule
    gettoken cv val : rest
    local val = strtrim("`val'")
    if "`val'" == "c" local hit "`cv' == .c"
    else local hit "`cv' == `val'"
    quietly replace `t' = .c if _flat & (`t' == . | `t' == .d) & `hit'
}
* CBS-derived motive ranks: system-missing = motive not among the presumed motives -> .c
foreach t in mig_mot_arb_reg mig_mot_asi_reg mig_mot_gez_reg mig_mot_stu_reg {
    quietly replace `t' = .c if _flat & `t' == .
}

* ---- rel_merge20: SIM 2020 second religion list (religie2_kl -> value map of target rel_den_det20b)
if `has20' {
    preserve
        use Volgnummer religie2_kl using "$INT/sim2020_main.dta", clear
        gen double PERSNR = Volgnummer
        impd_harmonize_var _rel2 religie2_kl rel_den_det20b sim2020
        gen byte svy_id = ${SVYID_sim2020}
        keep svy_id PERSNR _rel2
        tempfile rel2
        quietly save "`rel2'"
    restore
    quietly merge m:1 svy_id PERSNR using "`rel2'", nogen keep(master match)
    quietly replace rel_den_det = _rel2 if svy_id == ${SVYID_sim2020} & rel_den_det >= . & _rel2 < .
    drop _rel2
}
* ---- rel_none: SIM respondents without a religion -> 0 in rel_den_det / rel_den_cat
quietly replace rel_den_det = 0 if _flat & rel_any == 0
quietly replace rel_den_cat = 0 if _flat & rel_any == 0
* ---- rel_cat20: SIM 2020 categories from the detailed denomination
quietly replace rel_den_cat = 0 if svy_id == ${SVYID_sim2020} & rel_den_det == 0
quietly replace rel_den_cat = 1 if svy_id == ${SVYID_sim2020} & inrange(rel_den_det, 11, 19)
quietly replace rel_den_cat = 2 if svy_id == ${SVYID_sim2020} & inrange(rel_den_det, 21, 29)
quietly replace rel_den_cat = 3 if svy_id == ${SVYID_sim2020} & inrange(rel_den_det, 31, 39)
quietly replace rel_den_cat = 4 if svy_id == ${SVYID_sim2020} & (inrange(rel_den_det, 41, 98) | rel_den_det == 99)
quietly replace rel_den_cat = rel_den_det if svy_id == ${SVYID_sim2020} & rel_den_det >= .

* ---- remaining system-missing values in flat surveys: tagged per survey (surveys.csv sysmis_tag): .d where the
* file codes routing explicitly (SIM 2011/2015/2020), .c where a blank means 'routed past the question' (SIM 2006, LAS, SING)
frame cw_vm: quietly levelsof target if include_main == 1 & type != "str", local(numt) clean
foreach s in $SURVEYS {
    if "${STRUCT_`s'}" != "flat" | "${SYSMIS_`s'}" == "" continue
    foreach t of local numt {
        capture confirm variable `t'
        if _rc continue
        quietly replace `t' = .${SYSMIS_`s'} if svy_id == ${SVYID_`s'} & `t' == .
    }
}

* ---- relationship layer (household surveys): id_prtnr link, partner_copy:<target>, has_prtnr_roster, prtnr_cores_roster
*      (definitions: code/crosswalk_builder/variables_links.py)
gen byte _hp = !_flat & inlist(dem_poshh, 0, 1)                           // head of household or partner of the head
bysort svy_id HHNUMMER: egen double _nhp = total(_hp)
bysort svy_id HHNUMMER: egen double _sumid = total(cond(_hp, id_person, 0))
quietly replace id_prtnr = cond(_flat, .e, .d)                            // (created as .e in 02) other members / ambiguous rosters: not identifiable
quietly replace id_prtnr = .c if _hp & _nhp == 1                          // head/partner without a second head/partner record
quietly replace id_prtnr = _sumid - id_person if _hp & _nhp == 2          // the other head/partner member's id (exact in double)
gen byte _haslink = id_prtnr < .
gen byte _amb = _hp & _nhp > 2
label values id_prtnr vs_missing
* partner's own values via a frame keyed by id_person
frame cw_vm: quietly levelsof rowid if regexm(derive, "partner_copy:"), local(prows)
local psrcs ""
foreach r of local prows {
    frame cw_vm: local dv = derive[`r']
    if regexm("`dv'", "partner_copy:([a-z0-9_]+)") local src = regexs(1)
    local psrcs "`psrcs' `src'"
}
local psrcs : list uniq psrcs
tempname pf
frame put id_person `psrcs', into(`pf')
frame `pf' {
    foreach v of local psrcs {
        rename `v' _p_`v'
    }
}
quietly frlink m:1 id_prtnr, frame(`pf' id_person) gen(_pfl)
foreach v of local psrcs {
    quietly frget _p_`v' = _p_`v', from(_pfl)
    quietly replace _p_`v' = .d if _p_`v' == .e & _haslink              // partner not interviewed: no information
}
foreach r of local prows {
    frame cw_vm: local t = target[`r']
    frame cw_vm: local dv = derive[`r']
    if regexm("`dv'", "partner_copy:([a-z0-9_]+)") local src = regexs(1)
    quietly replace `t' = _p_`src' if !_flat & `t' == .e & _haslink
    quietly replace `t' = .c if !_flat & inlist(`t', .e, .) & !_haslink & _hp & !_amb    // incl. untagged sysmis of a head-reported source
    quietly replace `t' = .d if !_flat & `t' == .e & !_haslink & !(_hp & !_amb)
}
* dem_has_prtnr / dem_prtnr_cores from the link and the LAT question
quietly replace dem_has_prtnr = cond(_haslink, 1, cond(dem_prtnr_lat == 1, 1, cond(_hp & !_amb, 0, .d))) if !_flat & dem_has_prtnr == .e
quietly replace dem_prtnr_cores = cond(_haslink, 1, cond(dem_prtnr_lat == 1, 0, cond(_hp & !_amb, .c, .d))) if !_flat & dem_prtnr_cores == .e
frame drop `pf'
drop _hp _nhp _sumid _haslink _amb _pfl _p_*

* ---- svy_* labels
label variable id_hh       "Unique household identifier (svy_key*1e9 + source household number)"
label variable id_prtnr    "id_person of the co-resident partner (household samples; relationship layer)"
label variable id_person   "Unique person identifier (svy_key*1e11 + person number; hh samples: id_hh*100 + member no.)"
label variable svy_id      "Survey (wave) identifier"
label variable svy_name    "Survey (wave) name"
label variable svy_year    "Fieldwork year"
label variable svy_resptype "Respondent type"
label values svy_id vs_survey
label values svy_resptype vs_resptype
label values svy_year vs_missing
drop _flat

quietly save "$INT/derived_all_stata.dta", replace
display as text "Derived variables added: `=_N' rows x `=c(k)' columns"
