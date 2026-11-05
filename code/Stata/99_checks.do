* 99_checks.do : structural checks on the Stata build and, when present, a cell-by-cell comparison with the R build.
use "$DER/impd_public_v${VERTAG}_stata.dta", clear
isid id_person
assert inlist(svy_resptype, 1, 2, 3, 4)
foreach s in $SURVEYS {
    if "${STRUCT_`s'}" == "flat" {
        quietly describe using "$INT/`s'_main.dta"
        local nm = r(N)
        quietly count if svy_id == ${SVYID_`s'}
        assert r(N) == `nm'
        quietly count if svy_id == ${SVYID_`s'} & svy_resptype != 4
        assert r(N) == 0
        quietly count if svy_id == ${SVYID_`s'} & id_hh != .e
        assert r(N) == 0
        display as text "PASS ${SVYNAME_`s'}: `nm' individually sampled respondents, svy_resptype = 4, id_hh = .e"
    }
    else {
        quietly describe using "$INT/`s'_hh.dta"
        local nh = r(N)
        quietly describe using "$INT/`s'_pp.dta"
        local np = r(N)
        quietly count if svy_id == ${SVYID_`s'} & svy_resptype == 1
        assert r(N) == `nh'
        quietly count if svy_id == ${SVYID_`s'} & svy_resptype <= 2
        assert r(N) == `np'
        display as text "PASS ${SVYNAME_`s'}: heads = `nh', interviewed = `np'"
    }
}
* household-scope variables constant within household (household samples only)
frame cw_vm: quietly levelsof target if scope == "household" & include_main == 1, local(hhv) clean
foreach v of local hhv {
    quietly bysort id_hh (`v'): assert `v' == `v'[1] if !missing(`v') & !missing(`v'[1]) & id_hh < .
}
display as text "PASS household-scope variables constant within households"
* every non-string variable carries a value label whose definition exists; categorical ones label all their codes
frame cw_vm: local NV = _N
local nolab ""
forvalues i = 1/`NV' {
    frame cw_vm: local t = target[`i']
    frame cw_vm: local incl = include_main[`i']
    frame cw_vm: local ty = type[`i']
    frame cw_vm: local vset = valueset[`i']
    if `incl' != 1 | "`ty'" == "str" continue
    local l : value label `t'
    capture label list `l'
    if "`l'" == "" | _rc local nolab "`nolab' `t'"
    else if "`vset'" != "" {
        frame cw_vs: quietly count if valueset == "`vset'"
        local ncodes = r(N)
        quietly label list `l'
        if r(k) < `ncodes' + 5 local nolab "`nolab' `t'(incomplete)"
    }
}
if "`nolab'" == "" display as text "PASS every numeric variable carries its value labels (codes + missing tags)"
else {
    display as error "FAIL variables without (complete) value labels:`nolab'"
    exit 459
}

* ---- comparison with the R build -------------------------------------------------------------
* value-map range grammar: either bound may be negative ("-9--1"); the same regular expression as impd_harmonize_var (00_setup.do)
local _g_ok = 1
foreach spec in "-9--1|-9|-1" "-3-9|-3|9" "1-5|1|5" "0.5-7|0.5|7" {
    gettoken sv rest : spec, parse("|")
    gettoken sep rest : rest, parse("|")
    gettoken lo rest : rest, parse("|")
    gettoken sep hi : rest, parse("|")
    if !regexm("`sv'", "^(-?[0-9.]+)-(-?[0-9.]+)$") local _g_ok = 0
    else if regexs(1) != "`lo'" | regexs(2) != "`hi'" local _g_ok = 0
}
if `_g_ok' display as text "PASS value-map range grammar recognises negative bounds on either side (-9--1, -3-9, 1-5, 0.5-7)"
else {
    display as error "FAIL value-map range grammar does not parse a documented range example"
    error 9
}

* cf compares every variable of the Stata build with the same-named variable of the R build, observation by
* observation (both sorted by id_person); tagged missing values compare equal only when the tag is the same.
capture confirm file "$DER/impd_public_v${VERTAG}.dta"
if _rc {
    display as text "R build not found - comparison skipped"
    exit
}
use "$DER/impd_public_v${VERTAG}.dta", clear
sort id_person
tempfile rbuild
quietly save "`rbuild'"
use "$DER/impd_public_v${VERTAG}_stata.dta", clear
sort id_person
capture noisily cf _all using "`rbuild'", all
local cf_rc = _rc
if `cf_rc' == 0 display as result "PASS Stata build identical to R build in every cell of every variable"
else {
    display as error "FAIL Stata and R builds differ - see the cf listing above (variables with a nonzero count)"
    error 9                                              // a failed equivalence check terminates the run (nonzero exit)
}
