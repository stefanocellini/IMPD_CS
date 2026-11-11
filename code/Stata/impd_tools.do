* impd_tools.do : helpers for analyses of the IMPD-CS file (not part of the build).
*   do code/Stata/impd_tools.do
*   use data/derived/impd_cs_v0_4_6.dta, clear
*   impd_sample dem_sex dem_age_cat3 edu_dipl_hi_lvl3 lab_emp
*
* impd_sample varlist [, surveys(numlist) nostop]
*   Model-level eligibility report: per survey, the number of records with a valid value on every variable in varlist, and
*   why records drop out (variables not collected .e, not applicable .c, item non-response .a .b .d .).  Exits with error 459
*   when a survey ends with no complete record, unless nostop is given.  Results are left in r(): r(table) has one row per
*   survey (svy_id, n_records, n_complete).
capture program drop impd_sample
program define impd_sample, rclass
    syntax varlist(min=1) [, SURveys(numlist) noSTOP]
    tempvar ok
    quietly {
        if "`surveys'" == "" levelsof svy_id, local(surveys)
        gen byte `ok' = 1
        foreach v of varlist `varlist' {
            replace `ok' = 0 if missing(`v')
        }
    }
    tempname T
    local lost
    display as text _n "impd_sample: `: word count `varlist'' variable(s)"
    display as text %-10s "survey" %10s "records" %10s "complete" %8s "share" "  not collected"
    foreach s of local surveys {
        quietly count if svy_id == `s'
        local n = r(N)
        quietly count if svy_id == `s' & `ok'
        local nc = r(N)
        local nocol
        local det
        foreach v of varlist `varlist' {
            quietly count if svy_id == `s' & `v' == .e
            if r(N) == `n' & `n' > 0 local nocol "`nocol' `v'"
            quietly count if svy_id == `s' & !missing(`v')
            local nv = r(N)
            quietly count if svy_id == `s' & `v' == .c
            local ncc = r(N)
            quietly count if svy_id == `s' & `v' == .e
            local ne = r(N)
            local no = `n' - `nv' - `ncc' - `ne'
            local det "`det' `v': `nv' valid / `ncc' .c / `ne' .e / `no' other |"
        }
        local lab : label (svy_id) `s'
        local share = cond(`n' > 0, `nc' / `n', .)
        display as text %-10s "`lab'" as result %10.0f `n' %10.0f `nc' %8.3f `share' as text "  `nocol'"
        display as text "     `det'"
        capture confirm matrix `T'
        if _rc matrix `T' = (`s', `n', `nc')
        else matrix `T' = `T' \ (`s', `n', `nc')
        if `nc' == 0 local lost "`lost' `lab'"
    }
    matrix colnames `T' = svy_id n_records n_complete
    return matrix table = `T'
    return local lost "`lost'"
    if "`lost'" != "" {
        if "`stop'" != "nostop" {
            display as error "survey(s) with no complete record on `varlist':`lost'"
            exit 459
        }
        else display as text "warning: survey(s) with no complete record on `varlist':`lost'"
    }
end
