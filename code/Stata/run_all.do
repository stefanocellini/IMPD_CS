* run_all.do : run the complete IMPD public-component pipeline in Stata (16+).
*   cd to the IMPD root folder, then:   do code/Stata/run_all.do
* Prerequisite: data/interim/<survey>_<ro|pp|hh>.dta written once by Rscript code/R/01_import.R (see 01_import.do).
clear all
do "code/Stata/00_setup.do"
do "code/Stata/01_import.do"
do "code/Stata/02_harmonize.do"
do "code/Stata/03_derive.do"
do "code/Stata/04_build.do"
do "code/Stata/05_codebook.do"
do "code/Stata/99_checks.do"
display as result _n "Pipeline finished."
