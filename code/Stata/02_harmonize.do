* 02_harmonize.do : build one person-level frame per survey, apply the crosswalk, stack the surveys.
* Mirrors code/R/02_harmonize.R step by step.
*   hh_pp_ro surveys (SPVA/SPVN): rows = roster (ro); values = heads file > interviewed-persons file > roster file
*     (merge ... update replace; crosswalks/merge_exceptions.csv: declared system-missing codes blanked before the merge);
*     household-scope targets from the head's record; svy_resptype 1/2/3
*   flat surveys (SIM): rows = the single person file; svy_resptype = 4; PERSNR = source person number
*   .e (not collected) for persons whose questionnaire did not contain the item: from file membership and from
*   crosswalks/asked_to.csv (items the persons file holds for both respondent types but only one type was asked)
*   multi-source feeds ('A|B'): each source recoded separately, then combined with impd_coalesce_feed (00_setup.do)
frame cw_vm: local NV = _N

foreach s in $SURVEYS {
    display as text _n "==== harmonizing `s'"
    local flat = ("${STRUCT_`s'}" == "flat")
    if `flat' {
        use "$INT/`s'_main.dta", clear
        gen double PERSNR = ${IDVAR_`s'}       // impd_rownum (row number) is created by 01_import.R for deposits without an id
        isid PERSNR
        gen double HHNUMMER = .
        gen double GEZLIDNR = .
        gen byte svy_resptype = 4
    }
    else {
        * coalesced person frame with the declared merge exceptions (impd_hh_merge, 00_setup.do; shared with 04_build)
        impd_hh_merge `s'
        gen byte svy_resptype = cond(inlist(_m1, 3, 4, 5), 2, 3)
        quietly replace svy_resptype = 1 if inlist(_m2, 3, 4, 5)
        drop _m1 _m2
        gen double PERSNR = .
        * household-scope source variables from the head's record, suffixed _hhs
        frame cw_vm: quietly levelsof src_`s' if scope == "household" & include_main == 1 & src_`s' != "", local(hhsrc) clean
        tempfile hhvars
        preserve
            use HHNUMMER `hhsrc' using "$INT/`s'_hh.dta", clear
            foreach v of local hhsrc {
                rename `v' `v'_hhs
            }
            quietly save "`hhvars'"
        restore
        quietly merge m:1 HHNUMMER using "`hhvars'", nogen keep(master match)
    }
    * value labels must be (re)defined after `use`, which clears label definitions from memory
    impd_define_labels
    * string source variables: trim (empty strings are kept and can be mapped with the '' spec)
    quietly ds, has(type string)
    foreach v in `r(varlist)' {
        quietly replace `v' = strtrim(`v')
    }

    * ---- targets ---------------------------------------------------------------------------
    forvalues i = 1/`NV' {
        frame cw_vm: local target  = target[`i']
        frame cw_vm: local type    = type[`i']
        frame cw_vm: local scope   = scope[`i']
        frame cw_vm: local vset    = valueset[`i']
        frame cw_vm: local src     = src_`s'[`i']
        frame cw_vm: local files   = files_`s'[`i']
        frame cw_vm: local incl    = include_main[`i']
        frame cw_vm: local derive  = derive[`i']
        frame cw_vm: local vlabel  = label_en[`i']
        if `incl' != 1 continue
        * create-type derive rules are built in 03_derive; post-processing rules start from the harmonized value
        if inlist("`derive'", "id_person", "id_hh", "svy_id", "svy_name", "svy_year", "svy_resptype", "municipality", "municipality_name") continue
        if regexm("`derive'", "^cpi2015:") continue
        display as text "  `target'" _continue
        if "`type'" == "str" {
            if "`src'" == "" quietly gen str1 `target' = ""
            else quietly gen `target' = `src'
            local vlabel = usubstr(`"`vlabel'"', 1, 80)                                   // Unicode-aware: never cut inside a multi-byte character
            while strlen(`"`vlabel'"') > 80 {                                          // and within the 80-byte limit
                local vlabel = usubstr(`"`vlabel'"', 1, ustrlen(`"`vlabel'"') - 1)
            }
            label variable `target' `"`vlabel'"'
            continue
        }
        if "`src'" == "" {
            quietly gen double `target' = .e
        }
        else {
            local feeds : subinstr local src "|" " ", all
            local nfeed : word count `feeds'
            if `nfeed' == 1 {
                local srcvar "`src'"
                if "`scope'" == "household" & !`flat' local srcvar "`src'_hhs"
                impd_harmonize_var `target' `srcvar' `target' `s' `src'
            }
            else {
                * multi-source feed: harmonize every source separately, then combine (impd_coalesce_feed)
                local tmps ""
                local f = 0
                foreach sv of local feeds {
                    local ++f
                    local srcvar "`sv'"
                    if "`scope'" == "household" & !`flat' local srcvar "`sv'_hhs"
                    impd_harmonize_var _f`f' `srcvar' `target' `s' `sv'
                    local tmps "`tmps' _f`f'"
                }
                impd_coalesce_feed `target' `tmps'
                drop `tmps'
            }
            * not collected for this respondent type
            if "`scope'" != "household" & !regexm("`files'", "ro|main") {
                if regexm("`files'", "pp") quietly replace `target' = .e if svy_resptype == 3
                else quietly replace `target' = .e if svy_resptype >= 2
            }
            * item in the questionnaire of one respondent type only (crosswalks/asked_to.csv): the other type is .e
            if !`flat' {
                frame cw_asked: quietly count if target == "`target'" & survey == "`s'"
                if r(N) {
                    frame cw_asked: quietly levelsof asked_to if target == "`target'" & survey == "`s'", local(who) clean
                    local excl = cond("`who'" == "heads", 2, 1)
                    quietly count if svy_resptype == `excl' & !missing(`target')
                    if r(N) {
                        display as error "`target'/`s': asked_to = `who', but `r(N)' valid values in the other respondent type"
                        exit 459
                    }
                    quietly replace `target' = .e if svy_resptype == `excl'
                }
            }
        }
        if "`vset'" != "" label values `target' vs_`vset'
        else label values `target' vs_missing
        local vlabel = usubstr(`"`vlabel'"', 1, 80)                                   // Unicode-aware: never cut inside a multi-byte character
        while strlen(`"`vlabel'"') > 80 {                                          // and within the 80-byte limit
            local vlabel = usubstr(`"`vlabel'"', 1, ustrlen(`"`vlabel'"') - 1)
        }
        label variable `target' `"`vlabel'"'
    }
    gen byte  svy_id   = ${SVYID_`s'}
    gen str8  svy_name = "${SVYNAME_`s'}"
    gen int   svy_year = ${SVYYEAR_`s'}
    * keep only harmonized targets + keys (GEMEENTE is kept for the municipality lookup in 03_derive)
    capture rename GEMEENTE _GEMEENTE
    if _rc gen double _GEMEENTE = .
    frame cw_vm: quietly levelsof target if include_main == 1, local(targets) clean
    local keepvars "svy_id svy_name svy_year svy_resptype HHNUMMER GEZLIDNR PERSNR _GEMEENTE"
    foreach t of local targets {
        capture confirm variable `t'
        if !_rc local keepvars "`keepvars' `t'"
    }
    keep `keepvars'
    if `flat' display as text "`s': `=_N' persons (individual sample), `=c(k)' variables"
    else {
        quietly count if svy_resptype == 1
        local nh = r(N)
        quietly count if svy_resptype == 2
        local ni = r(N)
        display as text "`s': `=_N' persons (`nh' heads, `ni' other interviewed), `=c(k)' variables"
    }
    quietly save "$INT/harm_`s'_stata.dta", replace
}

* ---- stack ------------------------------------------------------------------------------
clear
foreach s in $SURVEYS {
    append using "$INT/harm_`s'_stata.dta"
}
quietly save "$INT/harmonized_all_stata.dta", replace
display as text "Stacked: `=_N' rows x `=c(k)' columns"
