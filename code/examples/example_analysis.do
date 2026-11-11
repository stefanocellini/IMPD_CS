* example_analysis.do : worked example for docs/example_analysis.md (not part of the build).  Stata twin of example_analysis.R:
* leisure-time contact with native Dutch across the eight surveys (2002-2020) and its association with problems speaking
* Dutch.  Descriptive and correlational, for illustration of the workflow in the codebook's "Start here" (steps 2-6).
*
* Run from the project root:  do code/examples/example_analysis.do   (output: code/examples/example_analysis_Stata.log)
version 17
clear all
set linesize 160
set more off
capture log close _all
log using "code/examples/example_analysis_Stata.log", replace text
do "code/Stata/impd_tools.do"
local files : dir "data/derived" files "impd_cs_v?_?_?.dta"
local files : list sort files
local f : word `: word count `files'' of `files'
display as text "Data file: `f'"
use "data/derived/`f'", clear

* ---- step 2/3: measures (codebook entries soc_leis_nl, lang_prob_spk; eligibility statements in docs/codebook_variables.csv)

* ---- step 4: population -----------------------------------------------------------------------------------------------
* interviewed persons (no roster-only rows) of a known migrant origin group (dem_eth 1-11, which also drops the native
* household members of SPVA 2002 - weight 0 - and 266 SPVN 2003 members without an origin code), first or second generation,
* aged 15+ (dem_age_cat3 is valid in every survey), who received the migrant routing of the person-sample questionnaires
* (svy_routing_mig 1; .e in the household surveys): 9 SIM 2006 respondents with a migrant origin code were routed as
* natives and answered the natives' mirror question, which soc_leis_nl also holds
keep if inlist(svy_resptype, 1, 2, 4) & inrange(dem_eth, 1, 11) & inlist(dem_gen, 1, 2) & !missing(dem_age_cat3) & svy_routing_mig != 0
display as text _n "Analysis population (interviewed, migrant origin group, 15+):"
tabulate svy_name

* ---- step 5: joint sample per survey ----------------------------------------------------------------------------------
display as text _n "== impd_sample: descriptive variables =="
impd_sample soc_leis_nl dem_eth dem_gen dem_sex dem_age_cat3 svy_wgt
display as text _n "== impd_sample: with lang_prob_spk (stops: SPVN 2003 did not collect it) =="
capture noisily impd_sample soc_leis_nl lang_prob_spk svy_wgt
display as error "r(`=_rc')"
quietly levelsof svy_id if svy_name != "SPVN2003", local(s7)
impd_sample soc_leis_nl lang_prob_spk dem_sex dem_age_cat3 dem_gen svy_wgt, surveys(`s7')

* ---- step 6: analysis --------------------------------------------------------------------------------------------------
generate byte often = soc_leis_nl == 1 if !missing(soc_leis_nl)                // 1 often/always vs 2 sometimes, 3 never
* lang_prob_spk 4 'does not speak Dutch' exists in SIM 2011/2015/2020 only; the earlier surveys fold it into 'often' (see the
* entry's note) - so recode 4 -> 1 explicitly (missing values stay missing) to get one three-class variable for all surveys
* (1 often/does not speak, 2 sometimes, 3 never)
generate byte lang3 = cond(lang_prob_spk == 4, 1, lang_prob_spk) if !missing(lang_prob_spk)
assert lang3 == 1 if lang_prob_spk == 4                                      // every 4 landed in 'often'
assert missing(lang3) == missing(lang_prob_spk)                              // and nothing else moved
label define lang3 1 "often / does not speak Dutch" 2 "sometimes" 3 "never"
label values lang3 lang3

display as text _n "== Table 1: weighted % often/always leisure time with native Dutch, by survey and origin group =="
table (svy_year) (dem_eth) if !missing(often, svy_wgt) [pweight = svy_wgt], statistic(mean often) statistic(count often) nformat(%5.3f mean) nototals
display as text _n "== Table 2: weighted % often/always, by survey and generation =="
table (svy_year) (dem_gen) if !missing(often, svy_wgt) [pweight = svy_wgt], statistic(mean often) statistic(count often) nformat(%5.3f mean) nototals
display as text _n "== Table 3: weighted % often/always, by survey and problems speaking Dutch (7 surveys; SPVA 2002: heads only) =="
table (svy_year) (lang3) if !missing(often, svy_wgt, lang3) [pweight = svy_wgt], statistic(mean often) statistic(count often) nformat(%5.3f mean) nototals

display as text _n "== Pooled logit: often ~ lang3 + sex + age + generation + origin group + survey (fixed effects) =="
display as text "Weights: svy_wgt rescaled to mean 1 within survey (each survey contributes in proportion to its analytic n)."
display as text "Clusters: household (id_hh) in SPVA 2002, the person elsewhere.  Survey fixed effects: within-survey association."
keep if !missing(often, svy_wgt, lang3, dem_sex)
bysort svy_id: egen double w1 = mean(svy_wgt)
replace w1 = svy_wgt / w1
generate double clus = cond(missing(id_hh), id_person, id_hh)        // id_hh is .e in the person samples
tabulate svy_name
logit often ib3.lang3 i.dem_sex i.dem_age_cat3 i.dem_gen i.dem_eth i.svy_id [pweight = w1], vce(cluster clus) or
log close
