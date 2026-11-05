* 01_import.do : check that the plain copies of the DANS files are available.
* They are written by code/R/01_import.R (haven reads SPSS portable and .sav files, keeping SPSS user-missing
* codes as values).  If you do not use R: for the .sav files `import spss` would work, but the SPVA 2002 .por
* files cannot be read by Stata - run `Rscript code/R/01_import.R` once, or ask DANS for a .sav version.
foreach s in $SURVEYS {
    impd_levels `s'
    foreach lvl in `r(levels)' {
        capture confirm file "$INT/`s'_`lvl'.dta"
        if _rc {
            display as error "missing $INT/`s'_`lvl'.dta - run Rscript code/R/01_import.R first (see header of this file)"
            exit 601
        }
        quietly describe using "$INT/`s'_`lvl'.dta"
        display as text "`s' `lvl': `r(N)' rows x `r(k)' vars"
    }
}
