# IMPD-CS v0.5.2 - Stata run log (build 63208c421151)

Built 13 Nov 2026 18:04:20 with Stata 19.5 SE on Windows; full output in docs/run_log_stata.txt. Each line is the verdict of one check of code/Stata/99_checks.do; the last compares the Stata build with the R build cell by cell when the R build is present.

- PASS SPVA2002: heads = 4199, interviewed = 8321
- PASS SPVN2003: heads = 3547, interviewed = 5594
- PASS LAS2004: 4096 individually sampled respondents, svy_resptype = 4, id_hh = .e
- PASS SIM2006: 5250 individually sampled respondents, svy_resptype = 4, id_hh = .e
- PASS SING2009: 6911 individually sampled respondents, svy_resptype = 4, id_hh = .e
- PASS SIM2011: 4125 individually sampled respondents, svy_resptype = 4, id_hh = .e
- PASS SIM2015: 6829 individually sampled respondents, svy_resptype = 4, id_hh = .e
- PASS SIM2020: 5323 individually sampled respondents, svy_resptype = 4, id_hh = .e
- PASS household-scope variables constant within households
- PASS every numeric variable carries its value labels (codes + missing tags)
- PASS value-map range grammar recognises negative bounds on either side (-9--1, -3-9, 1-5, 0.5-7)
- PASS household-survey merge exceptions applied in the Stata source companions (1 cell(s))
- PASS Stata build identical to R build in every cell of every variable
