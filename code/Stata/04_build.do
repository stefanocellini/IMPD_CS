* 04_build.do : order and write the harmonized file and the companion source files (mirrors code/R/04_build.R).
*   data/derived/impd_public_v<version>_stata.dta              harmonized variables
*   data/derived/impd_public_v<version>_source_<survey>_stata.dta   original source variables (src_ prefix)
* The "_stata" suffix keeps the Stata build apart from the R build so that 99_checks.do can compare them.
use "$INT/derived_all_stata.dta", clear
impd_define_labels

frame cw_vm: quietly levelsof target if include_main == 1, local(targets) clean
local ordered ""
foreach t of local targets {
    capture confirm variable `t'
    if _rc {
        display as error "target `t' declared in variable_map.csv but not built"
        exit 111
    }
}
* keep the declared order of variable_map.csv
frame cw_vm: local NV = _N
forvalues i = 1/`NV' {
    frame cw_vm: local t = target[`i']
    frame cw_vm: local incl = include_main[`i']
    if `incl' == 1 local ordered "`ordered' `t'"
}
keep `ordered'
order `ordered'
* notes: sources per survey, universe and harmonization note (read with: notes varname)
forvalues i = 1/`NV' {
    frame cw_vm: local t = target[`i']
    frame cw_vm: local incl = include_main[`i']
    if `incl' != 1 continue
    frame cw_vm: local u = universe_en[`i']
    frame cw_vm: local nt = notes[`i']
    frame cw_vm: local dv = derive[`i']
    local srcnote ""
    foreach s in $SURVEYS {
        frame cw_vm: local sv = src_`s'[`i']
        frame cw_vm: local sl = srclabel_`s'[`i']
        if "`sv'" != "" local srcnote `"`srcnote' ${SVYNAME_`s'}: `sv' (`sl')."'
        else if "`dv'" == "" local srcnote `"`srcnote' ${SVYNAME_`s'}: not collected."'
    }
    if "`dv'" != "" local srcnote `"`srcnote' Derived: `dv'."'
    notes `t': Source -`srcnote'
    notes `t': Universe - `u'
    if `"`nt'"' != "" notes `t': `nt'
    notes `t': IMPD v$IMPD_VERSION; crosswalks/variable_map.csv, value_map.csv; docs/codebook.html
}
compress
label data "IMPD public v$IMPD_VERSION - harmonized person-level file (SPVA/SPVN/SIM)"
save "$DER/impd_public_v${VERTAG}_stata.dta", replace
display as text "Main file: `=_N' persons x `=c(k)' variables -> impd_public_v${VERTAG}_stata.dta"

* ---- companion source files (one per survey) ---------------------------------------------------
foreach s in $SURVEYS {
    use id_person id_hh svy_id svy_resptype HHNUMMER GEZLIDNR PERSNR if svy_id == ${SVYID_`s'} using "$INT/derived_all_stata.dta", clear
    tempfile ids
    quietly save "`ids'"
    if "${STRUCT_`s'}" == "flat" {
        use "$INT/`s'_main.dta", clear
        gen double PERSNR = ${IDVAR_`s'}
        quietly merge 1:1 PERSNR using "`ids'", nogen keep(match)
    }
    else {
        * the coalesced person frame of this survey, exactly as in 02_harmonize (impd_hh_merge: hh > pp > ro, with
        * the declared merge exceptions - before v0.4.9 the companions were built without them)
        impd_hh_merge `s'
        drop _m1 _m2
        quietly merge 1:1 HHNUMMER GEZLIDNR using "`ids'", nogen keep(match)
    }
    impd_define_labels
    quietly ds id_person id_hh svy_id svy_resptype HHNUMMER GEZLIDNR PERSNR, not
    foreach v in `r(varlist)' {
        frame cw_srcvars: quietly levelsof label_nl if survey == "`s'" & source_var == "`v'", local(lab) clean
        rename `v' src_`v'
        local lab = usubstr(`"`lab'"', 1, 80)                                   // Unicode-aware: never cut inside a multi-byte character
        while strlen(`"`lab'"') > 80 {                                          // and within the 80-byte limit
            local lab = usubstr(`"`lab'"', 1, ustrlen(`"`lab'"') - 1)
        }
        label variable src_`v' `"`lab'"'
        capture confirm numeric variable src_`v'
        if !_rc {
            frame cw_srclab: quietly levelsof rowid if survey == "`s'" & source_var == "`v'", local(rows)
            if "`rows'" != "" {
                capture label drop src_`v'
                foreach r of local rows {
                    frame cw_srclab: local c = code[`r']
                    if "`c'" == "." continue
                    frame cw_srclab: local l = label_nl[`r']
                    if `"`l'"' == "" local l "(no label)"
                    local l = usubstr(`"`l'"', 1, 60)                                   // Unicode-aware: never cut inside a multi-byte character
                    while strlen(`"`l'"') > 60 {                                          // and within the 60-byte limit
                        local l = usubstr(`"`l'"', 1, ustrlen(`"`l'"') - 1)
                    }
                    label define src_`v' `c' `"`l'"', modify
                }
                label values src_`v' src_`v'
            }
        }
    }
    drop HHNUMMER GEZLIDNR PERSNR
    order id_person id_hh svy_id svy_resptype
    label values svy_id vs_survey
    compress
    label data "IMPD public v$IMPD_VERSION - ${SVYNAME_`s'} source variables (Dutch labels)"
    save "$DER/impd_public_v${VERTAG}_source_`s'_stata.dta", replace
    display as text "Source file ${SVYNAME_`s'}: `=_N' persons x `=c(k)' variables"
}
