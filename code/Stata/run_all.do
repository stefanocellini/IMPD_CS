* run_all.do : run the complete IMPD-CS pipeline in Stata (16+).
*   cd to the IMPD root folder, then:   do code/Stata/run_all.do
* Prerequisite: data/interim/<survey>_<ro|pp|hh|main>.dta, the plain copies of the DANS files written once by
*   Rscript code/R/01_import.R (Stata cannot read SPSS portable files; see 01_import.do).
* Output: data/derived/impd_cs_v<version>_stata.dta and the source companions; docs/codebook_stata.txt;
*   docs/run_log_stata.txt (the whole run) and docs/run_log_stata.md (header and the verdicts of the checks, the
*   Stata counterpart of docs/run_log.md).  Each check prints PASS or FAIL; a FAIL stops the run.
clear all
set linesize 255                                         // verdict lines are kept whole in the log
capture log close impd
log using "docs/run_log_stata.txt", replace text name(impd)
do "code/Stata/00_setup.do"
display as text _n "IMPD-CS v$IMPD_VERSION - Stata run log (build $BUILD_ID)"
display as text "Stata `c(stata_version)' `c(edition_real)' on `c(os)', `c(current_date)' `c(current_time)'" _n
do "code/Stata/01_import.do"
do "code/Stata/02_harmonize.do"
do "code/Stata/03_derive.do"
do "code/Stata/04_build.do"
do "code/Stata/05_codebook.do"
do "code/Stata/99_checks.do"
display as result _n "Pipeline finished."
log close impd

* ---- docs/run_log_stata.md: the verdict lines of the run, for the record --------------------------------------------
tempname in out
file open `out' using "docs/run_log_stata.md", write text replace
file write `out' "# IMPD-CS v$IMPD_VERSION - Stata run log (build $BUILD_ID)" _n _n
file write `out' "Built `c(current_date)' `c(current_time)' with Stata `c(stata_version)' `c(edition_real)' on `c(os)'; " ///
    "full output in docs/run_log_stata.txt. Each line is the verdict of one check of code/Stata/99_checks.do; " ///
    "the last compares the Stata build with the R build cell by cell when the R build is present." _n _n
file open `in' using "docs/run_log_stata.txt", read text
file read `in' line
while r(eof) == 0 {
    if inlist(substr(`"`macval(line)'"', 1, 4), "PASS", "FAIL") file write `out' `"- `macval(line)'"' _n
    file read `in' line
}
file close `in'
file close `out'
display as text "Verdicts written: docs/run_log_stata.md"
