* IMPD-CS - Integrated Migrant Panel Dataset, cross-sectional component (harmonized DANS deposits)
* 00_setup.do : paths, crosswalk frames and helper programs shared by all steps.
*
* Run the whole pipeline from the IMPD root folder with:   do code/Stata/run_all.do
* (or set the global ROOT below).  Requires Stata 16 or later (frames).
* Input:  data/interim/<survey>_<ro|pp|hh|main>.dta - plain copies of the DANS files written by code/R/01_import.R
*         (Stata cannot read SPSS portable files; see docs/decisions.md section 6)
* The harmonization logic is identical to the R scripts in code/R and is driven only by the CSV files in crosswalks/.

version 16
clear all
set more off
set varabbrev off

if "$ROOT" == "" global ROOT "`c(pwd)'"
global CW   "$ROOT/crosswalks"
global INT  "$ROOT/data/interim"
global DER  "$ROOT/data/derived"
global DOCS "$ROOT/docs"
global IMPD_VERSION "0.5.1"
global VERTAG = subinstr("$IMPD_VERSION", ".", "_", .)
* build identity: sha256 over the crosswalks and the code, computed by the R side (00_setup.R) and written to docs/BUILD_ID
* by 01_import.R and 99_checks.R; Stata reads it to label its files and its run log with the identity of what it built from
global BUILD_ID "unknown"
capture {
    tempname fh
    file open `fh' using "$DOCS/BUILD_ID", read text
    file read `fh' line
    file close `fh'
    global BUILD_ID : word 1 of `line'
}
capture mkdir "$ROOT/data"
capture mkdir "$INT"
capture mkdir "$DER"
capture mkdir "$DOCS"

* ---- crosswalks into frames -------------------------------------------------------------
capture program drop impd_load_cw
program define impd_load_cw
    args name file
    capture frame drop `name'
    frame create `name'
    frame `name' {
        import delimited using "$CW/`file'", varnames(1) encoding("utf-8") stringcols(_all) clear
        quietly ds
        foreach v in `r(varlist)' {
            quietly replace `v' = "" if `v' == "NA"
            quietly replace `v' = subinstr(`v', char(96), "'", .)      // backticks in source labels (SIM 2011) would break macro expansion
        }
        gen long rowid = _n
    }
end

impd_load_cw cw_surveys   surveys.csv
impd_load_cw cw_vm        variable_map.csv
impd_load_cw cw_vs        valuesets.csv
impd_load_cw cw_vmap      value_map.csv
impd_load_cw cw_rules     missing_rules.csv
impd_load_cw cw_srclab    source_labels.csv
impd_load_cw cw_srcmiss   source_missing.csv
impd_load_cw cw_srcvars   source_variables.csv
impd_load_cw cw_muni      municipalities.csv
impd_load_cw cw_asked     asked_to.csv
impd_load_cw cw_mergex    merge_exceptions.csv
impd_load_cw cw_cpi       cpi.csv

frame cw_vs:    destring code, replace
frame cw_srclab: destring code, replace force      // string-coded labels (SIM registry variables) -> missing; handled by value_map
frame cw_srcmiss: destring lo hi, replace
frame cw_muni:  destring source_code, replace
frame cw_cpi:   destring year cpi_2015, replace
frame cw_vm:    destring include_main, replace
frame cw_vmap:  sort target survey source_var rowid
frame cw_vmap:  gen long vmrow = _n

* included surveys: globals SURVEYS (keys) and per-survey id/year/name/structure/id variable
frame cw_surveys {
    global SURVEYS ""
    global FLATIDS ""
    forvalues i = 1/`=_N' {
        if status[`i'] == "included" {
            local key = lower(svy_name[`i'])
            global SURVEYS "$SURVEYS `key'"
            global SVYID_`key'   = svy_id[`i']
            global SVYKEY_`key'  = svy_key[`i']
            global SVYYEAR_`key' = svy_year[`i']
            global SVYNAME_`key' = svy_name[`i']
            global STRUCT_`key'  = structure[`i']
            global IDVAR_`key'   = id_var[`i']
            global SYSMIS_`key'  = sysmis_tag[`i']
            if structure[`i'] == "flat" global FLATIDS "$FLATIDS `=svy_id[`i']'"
        }
    }
}
* levels (files) of a survey: ro pp hh for household samples, main for flat person samples
capture program drop impd_hh_merge
program define impd_hh_merge
    * household surveys: the coalesced person frame (heads > interviewed persons > roster), with the declared merge
    * exceptions (crosswalks/merge_exceptions.csv, rule valid_over_sysmis) applied - the system-missing code of a more
    * detailed file is blanked before the merge so that a valid value of a less detailed file stands.  Used by
    * 02_harmonize (main file) and 04_build (source companions), so both see the same merged source view.
    * Leaves _m1 (roster x persons) and _m2 (x heads) in memory.
    args s
    local ppfile "$INT/`s'_pp.dta"
    local hhfile "$INT/`s'_hh.dta"
    frame cw_mergex: quietly levelsof rowid if survey == "`s'" & rule == "valid_over_sysmis", local(mxrows)
    if "`mxrows'" != "" {
        tempfile pp_mx hh_mx
        foreach f in pp hh {
            capture frame drop tmp_mx
            frame create tmp_mx
            frame tmp_mx {
                use "$INT/`s'_`f'.dta", clear
                foreach r of local mxrows {
                    frame cw_mergex: local mxv = source_var[`r']
                    frame cw_mergex: local mxc = sysmis_code[`r']
                    capture confirm numeric variable `mxv'
                    if !_rc quietly replace `mxv' = . if `mxv' == `mxc'
                }
                save "``f'_mx'", replace
            }
            frame drop tmp_mx
            local `f'file "``f'_mx'"
        }
    }
    use "$INT/`s'_ro.dta", clear
    quietly merge 1:1 HHNUMMER GEZLIDNR using "`ppfile'", update replace gen(_m1)
    quietly merge 1:1 HHNUMMER GEZLIDNR using "`hhfile'", update replace gen(_m2)
end

capture program drop impd_levels
program define impd_levels, rclass
    args s
    if "${STRUCT_`s'}" == "flat" return local levels "main"
    else return local levels "ro pp hh"
end
* impd_coalesce_feed newvar v1 v2 ... : multi-source feed ('A|B' in variable_map): a valid value wins over any
* tag, among tags the first that is not .c wins, otherwise .c (mirrors coalesce_feed in code/R/02_harmonize.R)
capture program drop impd_coalesce_feed
program define impd_coalesce_feed
    gettoken newvar rest : 0
    gettoken first rest : rest
    quietly gen double `newvar' = `first'
    foreach v of local rest {
        quietly replace `newvar' = `v' if `newvar' >= . & `v' < .
        quietly replace `newvar' = `v' if `newvar' == .c & `v' >= . & `v' != .c
    }
end
* flat-survey indicator for the stacked file
capture program drop impd_flag_flat
program define impd_flag_flat
    capture drop _flat
    gen byte _flat = 0
    foreach id in $FLATIDS {
        quietly replace _flat = 1 if svy_id == `id'
    }
end

* ---- value labels: one Stata label per value set, plus the missing-value tags -----------------
* .a don't know | .b refusal | .c not applicable | .d no information | .e not collected
capture program drop impd_define_labels
program define impd_define_labels
    frame cw_vs {
        quietly levelsof valueset, local(sets)
    }
    foreach s of local sets {
        capture label drop vs_`s'
        frame cw_vs {
            quietly levelsof rowid if valueset == "`s'", local(rows)
        }
        foreach r of local rows {
            frame cw_vs: local c = code[`r']
            frame cw_vs: local l = label_en[`r']
            label define vs_`s' `c' `"`l'"', add
        }
        label define vs_`s' .a "Don't know" .b "Refusal" .c "Not applicable" .d "No information" .e "Not collected (survey/questionnaire)", add
    }
    * numeric variables carry the missing tags only, so that `tab x, missing` reads the tags
    capture label drop vs_missing
    label define vs_missing .a "Don't know" .b "Refusal" .c "Not applicable" .d "No information" .e "Not collected (survey/questionnaire)"
end

* ---- list of missing codes (code|tag) for one source variable in one survey -------------------
* precedence: survey code rules > label rules > declared SPSS user-missing (by code pattern)
capture program drop impd_missing_codes
program define impd_missing_codes, rclass
    args survey srcvar
    local out ""
    local seen ""
    * 1. code rules
    frame cw_rules: quietly levelsof rowid if survey == "`survey'" & rule_type == "code", local(rows)
    foreach r of local rows {
        frame cw_rules: local m = match[`r']
        frame cw_rules: local t = target[`r']
        local out "`out' `m'|`t'"
        local seen "`seen' `m'"
    }
    * 2. label rules
    frame cw_rules: quietly levelsof rowid if survey == "`survey'" & rule_type == "label", local(rows)
    foreach r of local rows {
        frame cw_rules: local pat = match[`r']
        frame cw_rules: local t = target[`r']
        frame cw_srclab: quietly levelsof code if survey == "`survey'" & source_var == "`srcvar'" & regexm(lower(strtrim(label_nl)), `"`pat'"'), local(codes)
        foreach c of local codes {
            if !`: list c in seen' {
                local out "`out' `c'|`t'"
                local seen "`seen' `c'"
            }
        }
    }
    * 3. declared user-missing values
    frame cw_srcmiss: quietly levelsof rowid if survey == "`survey'" & source_var == "`srcvar'", local(rows)
    if "`rows'" != "" {
        frame cw_rules: quietly levelsof rowid if survey == "`survey'" & rule_type == "declared", local(drows)
        foreach r of local rows {
            frame cw_srcmiss: local lo = lo[`r']
            frame cw_srcmiss: local hi = hi[`r']
            if `hi' - `lo' > 1000 local hi = `lo'
            forvalues c = `lo'/`hi' {
                if `: list c in seen' continue
                local cstr = string(`c', "%12.0g")
                foreach dr of local drows {
                    frame cw_rules: local pat = match[`dr']
                    frame cw_rules: local t = target[`dr']
                    if regexm("`cstr'", `"`pat'"') {
                        local out "`out' `c'|`t'"
                        local seen "`seen' `c'"
                        continue, break
                    }
                }
            }
        }
    }
    return local codes "`out'"
end

* ---- apply the value map and the missing codes of one target x survey to a source variable -----
* impd_harmonize_var newvar srcvar target survey [lookup] : newvar (double) = harmonized values of srcvar
*   (value_map rows and missing rules of source variable `lookup', default srcvar);
* lookup = name under which the source variable is registered in the crosswalks (default srcvar; e.g. GEZINK1 for GEZINK1_hhs).
* 1. value_map rows (exact code, range lo-hi with either bound possibly negative, quoted string 'H', or * = any other non-missing value); 2. missing codes.
* String sources are only recoded through quoted value-map rows; codes not listed stay system-missing.
capture program drop impd_harmonize_var
program define impd_harmonize_var
    args newvar srcvar target survey lookup
    if "`lookup'" == "" local lookup "`srcvar'"
    capture confirm string variable `srcvar'
    local isstr = (_rc == 0)
    if `isstr' quietly gen double `newvar' = .
    else quietly gen double `newvar' = `srcvar'
    quietly gen byte _c = 0
    frame cw_vmap: quietly summarize vmrow if target == "`target'" & survey == "`survey'" & source_var == "`lookup'", meanonly
    if r(N) > 0 {
        local j0 = r(min)
        local j1 = r(max)
        forvalues pass = 1/2 {
            forvalues j = `j0'/`j1' {
                frame cw_vmap: local sv = source_value[`j']
                frame cw_vmap: local tv = target_value[`j']
                if (`pass' == 1 & "`sv'" == "*") | (`pass' == 2 & "`sv'" != "*") continue
                if "`sv'" == "*" {
                    if `isstr' local cond `"`srcvar' != "" & _c == 0"'
                    else local cond "`srcvar' < . & _c == 0"
                }
                else if substr("`sv'", 1, 1) == "'" {
                    local val = substr("`sv'", 2, length("`sv'") - 2)
                    local cond `"strtrim(`srcvar') == "`val'" & _c == 0"'
                }
                else {
                    * ranges "lo-hi": regexs() must be read in a separate statement (macro expansion precedes execution)
                    if regexm("`sv'", "^(-?[0-9.]+)-(-?[0-9.]+)$") {           // either bound may be negative ("-9--1")
                        local lo = regexs(1)
                        local hi = regexs(2)
                        local cond "inrange(`srcvar', `lo', `hi') & _c == 0"
                    }
                    else local cond "`srcvar' == `sv' & _c == 0"
                }
                quietly replace `newvar' = `tv' if `cond'
                quietly replace _c = 1 if `cond'
            }
        }
    }
    if !`isstr' {
        impd_missing_codes `survey' `lookup'
        foreach ct in `r(codes)' {
            gettoken c t : ct, parse("|")
            local t = subinstr("`t'", "|", "", 1)
            quietly replace `newvar' = `t' if `srcvar' == `c' & _c == 0
        }
    }
    drop _c
end
