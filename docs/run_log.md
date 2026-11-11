# IMPD-CS v0.5.1 — run log (build 7069c412771c)

Built 2026-11-11 15:58 with R 4.3.3 (x86_64-pc-linux-gnu) on Linux; packages: haven 2.5.4, dplyr 1.1.4, readr 2.1.5, stringr 1.5.1, tidyr 1.3.1, purrr 1.0.2, openssl 2.1.1, jsonlite 1.8.8.

Deposit zip files (sha256, first 12 hex digits; full hashes of zips and data files in crosswalks/surveys.csv): SPVA2002 91166a194661, SPVN2003 96556f53090b, LAS2004 cb67573d71e1, SIM2006 5c666899708d, SING2009 b4d3aea4cf56, SIM2011 78d8bf29ef63, SIM2015 5269492b473f, SIM2020 cc4518f30693.

## Checks

- PASS row count equals the sum of roster/person rows (55157)
- PASS id_person is unique
- PASS variable set equals variable_map (include_main = 1): 1642 variables
- PASS SPVA2002: heads = 4199 (file 4199), interviewed = 8321 (file 8321)
- PASS SPVN2003: heads = 3547 (file 3547), interviewed = 5594 (file 5594)
- PASS LAS2004: 4096 individually sampled respondents (file 4096), all svy_resptype = 4
- PASS LAS2004: id_hh is .e (no household identifier in a person sample)
- PASS SIM2006: 5250 individually sampled respondents (file 5250), all svy_resptype = 4
- PASS SIM2006: id_hh is .e (no household identifier in a person sample)
- PASS SING2009: 6911 individually sampled respondents (file 6911), all svy_resptype = 4
- PASS SING2009: id_hh is .e (no household identifier in a person sample)
- PASS SIM2011: 4125 individually sampled respondents (file 4125), all svy_resptype = 4
- PASS SIM2011: id_hh is .e (no household identifier in a person sample)
- PASS SIM2015: 6829 individually sampled respondents (file 6829), all svy_resptype = 4
- PASS SIM2015: id_hh is .e (no household identifier in a person sample)
- PASS SIM2020: 5323 individually sampled respondents (file 5323), all svy_resptype = 4
- PASS SIM2020: id_hh is .e (no household identifier in a person sample)
- PASS all categorical values are in their value set and years are in range
- PASS dem_age within 0-105
- PASS every numeric variable carries its value labels (codes + missing tags)
- PASS not-collected (.e) assignment consistent
- PASS household-scope variables are constant within households (hh_eth, hh_size, hh_comp, hh_noth, hh_inc, hh_inc_cat, hh_inc_15, hh_inc_band, hh_inc_band_par, hh_inc_band16)
- PASS hh_inc_15 = hh_inc x CPI factor
- PASS inc_lab_15 = inc_lab x CPI factor
- PASS inc_hrwage_15 = inc_hrwage x CPI factor
- PASS inc_ben_amt_15 = inc_ben_amt x CPI factor
- PASS inc_tot_15 = inc_tot x CPI factor
- PASS trn_remit_amt_15 = trn_remit_amt@2005 x CPI factor
- PASS trn_dowry_paid_amt_15 = trn_dowry_paid_amt@2005 x CPI factor
- PASS trn_recv_amt_15 = trn_recv_amt@2005 x CPI factor
- PASS trn_inherit_amt_15 = trn_inherit_amt@2005 x CPI factor
- PASS hous_cost_15 = hous_cost x CPI factor
- PASS independent recount of 1884 exact value-map cells matches
- PASS stated universes agree with the data (native sample, split half, head-only items)
- PASS multi-source feeds (18; 94,360 cells) re-derived independently with the documented precedence
- NOTE feed conflicts (two sources with different valid values; the first source is kept): dem_prtnr_st/las2004: 143 rows with different valid values in two sources (first source kept); dem_prtnr_st/sim2006: 176 rows with different valid values in two sources (first source kept); dem_prtnr_st/sing2009: 187 rows with different valid values in two sources (first source kept)
- PASS all 5 string variables are valid UTF-8 in .rds, .dta and .csv
- NOTE highest-diploma universe (persons not in full-time education): edu_dipl_hi_det/SPVA2002: 69 full-time students with a value; edu_dipl_hi_cat5/SPVA2002: 69 full-time students with a value; edu_dipl_hi_cat5/SPVN2003: 176 full-time students with a value; edu_dipl_hi_cat/SPVA2002: 69 full-time students with a value; edu_dipl_hi_cat/SPVN2003: 176 full-time students with a value; edu_dipl_hi_lvl3/SPVA2002: 69 full-time students with a value; edu_dipl_hi_lvl3/SPVN2003: 176 full-time students with a value
- PASS routing-gate table recomputed from the released files equals docs/routing_check.csv (697 source x gate pairs)
- PASS routing gates hold in the data (630 of 697 source x gate pairs without any value outside; 67 with exceptions <= 10%)
- NOTE routing-gate exceptions (values outside the printed condition, <= 10%; data as delivered): dem_mar_yr/spva2002 (HUWJAAR): 8 of 2175 values outside gate dem_mar in {1} [2=5 3=3]; dem_mar_age/spva2002 (LFTHUW): 7 of 2113 values outside gate dem_mar in {1} [2=4 3=3]; mig_yr_arr/las2004 (MIGRJAAR): 12 of 2610 values outside gate dem_gen in {1} [0=12]; mig_yr_arr/sim2011 (MIGRJAAR): 7 of 2243 values outside gate dem_gen in {1} [0=7]; mig_yr_arr/sim2011 (MIGRJAAR): 23 of 2243 values outside gate dem_prtnr_res in {1} [2=19 6=4]; mig_yr_arr/sim2015 (migrjaar): 70 of 4218 values outside gate dem_gen in {1} [2=70]; mig_yr_arr/sim2020 (migrjaar): 1 of 3191 values outside gate dem_gen in {1} [2=1]; mig_age_arr/las2004 (MIGROUD): 12 of 2663 values outside gate dem_gen in {1} [0=12]; mig_reason/las2004 (REDMIGR): 12 of 2663 values outside gate dem_gen in {1} [0=12]; mig_reason/sim2015 (redmigr2): 46 of 3965 values outside gate dem_gen in {1} [2=46]; int_crs/sim2015 (inbcurus): 27 of 2501 values outside gate dem_gen in {1} [2=27]; int_nlcrs/sim2020 (nlcurs): 1 of 3309 values outside gate dem_gen in {1} [2=1]; lang_prob_spk/sim2020 (taalgesp): 1 of 3309 values outside gate dem_gen in {1} [2=1]; lang_prob_read/sim2020 (taalkran): 1 of 3309 values outside gate dem_gen in {1} [2=1]; edu_abr_yrs/las2004 (ONDJRBL): 73 of 2040 values outside gate dem_gen in {1} [0=5 2=68]; edu_abr_yrs/sim2015 (ondjrbl): 9 of 3346 values outside gate edu_abr in {1} [0=9]; edu_abr_dipl/las2004 (DIPLBL): 73 of 2058 values outside gate dem_gen in {1} [0=5 2=68]; edu_abr_dipl/sim2015 (diplbl): 10 of 3397 values outside gate edu_abr in {1} [0=10]; edu_abr_dipl/sim2020 (diplbl): 1 of 2679 values outside gate edu_cntry in {1,2} [3=1]; edu_nl_att_dipl/sim2020 (diplnl1): 1 of 3304 values outside gate edu_nl in {1} [0=1]; mig_rsn01/sim2020 (redmigr_werk): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn02/sim2020 (redmigr_studie): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn03/sim2020 (redmigr_soczek): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn04/sim2020 (redmigr_polred): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn05/sim2020 (redmigr_armoed): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn06/sim2020 (redmigr_intrek): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn07/sim2020 (redmigr_hwlk): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn08/sim2020 (redmigr_gzheid): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn09/sim2020 (redmigr_toekkind): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn10/sim2020 (redmigr_ouders): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn11/sim2020 (redmigr_partner): 1 of 3309 values outside gate dem_gen in {1} [2=1]; mig_rsn12/sim2020 (redmigr_anders): 1 of 3309 values outside gate dem_gen in {1} [2=1]; int_crs_st/sim2015 (inbcurus): 27 of 2501 values outside gate dem_gen in {1} [2=27]; int_exam/sim2015 (inbexam): 17 of 1961 values outside gate dem_gen in {1} [2=17]; int_nlcrs_det/sim2020 (nlcurs): 1 of 3309 values outside gate dem_gen in {1} [2=1]; edu_abr_att_lvl3/las2004 (MAXOPLBL): 73 of 2054 values outside gate dem_gen in {1} [0=5 2=68]; edu_abr_where/sim2015 (ondlvh): 10 of 3397 values outside gate edu_abr in {1} [0=10]; edu_abr_where/sim2020 (ondlvh): 1 of 2679 values outside gate edu_cntry in {1,2} [3=1]; lang_prob_write/sim2020 (taalpen): 1 of 3309 values outside gate dem_gen in {1} [2=1]; lang_nl_self10/sim2020 (taalcijfer): 1 of 3309 values outside gate dem_gen in {1} [2=1]; soc_sh_edu01/sim2020 (contactopl_migr): 2 of 864 values outside gate edu_enr in {1} [0=2]; soc_sh_edu02/sim2020 (contactopl_autnl): 1 of 1001 values outside gate edu_enr in {1} [0=1]; soc_sh_edu03/sim2020 (contactopl_ander): 1 of 951 values outside gate edu_enr in {1} [0=1]; med_tv_orig_cat/las2004 (TVEIGEN): 7 of 1866 values outside gate dem_eth in {1,2} [3=3 4=1 90=3]; att_isl01/sim2006 (MOSLLEEF): 9 of 2953 values outside gate dem_eth in {3,4,90} [1=6 2=3]; rel_veil/sim2006 (ZHFDDOEK): 7 of 1104 values outside gate dem_eth in {1,2} [3=1 4=6]; rel_veil/sim2006 (ZHFDDOEK): 4 of 1104 values outside gate dem_sex in {2} [1=4]; rel_veil/sim2020 (zhfddoek): 2 of 1006 values outside gate dem_sex in {2} [1=2]; lang_orig_write/sing2009 (ETNIPEN): 445 of 5486 values outside gate lang_other in {12,13,36,41,43,44,46,47,48,49,50,51,52,53,54,96} [42=153 45=292]; att_isl03/las2004 (NLRESP): 6 of 1794 values outside gate dem_eth in {1,2} [3=2 4=1 90=3]; att_isl03/sim2006 (NLRESP): 9 of 2089 values outside gate dem_eth in {1,2} [3=1 4=8]; att_isl04/las2004 (WESTLEEF): 6 of 1790 values outside gate dem_eth in {1,2} [3=2 4=1 90=3]; att_isl04/sim2006 (WESTLEEF): 9 of 2074 values outside gate dem_eth in {1,2} [3=1 4=8]; att_isl05/las2004 (NLVROU): 6 of 1776 values outside gate dem_eth in {1,2} [3=2 4=1 90=3]; att_isl05/sim2006 (NLVROU): 9 of 2030 values outside gate dem_eth in {1,2} [3=1 4=8]; att_isl06/las2004 (NLKIND): 6 of 1711 values outside gate dem_eth in {1,2} [3=2 4=1 90=3]; att_isl06/sim2006 (NLKIND): 9 of 1933 values outside gate dem_eth in {1,2} [3=1 4=8]; att_isl07/sim2006 (MOSLRESP): 9 of 2835 values outside gate dem_eth in {3,4,90} [1=6 2=3]; att_isl08/sim2006 (MOSLVRW): 9 of 2836 values outside gate dem_eth in {3,4,90} [1=6 2=3]; att_isl09/sim2006 (MOSLKIND): 9 of 2695 values outside gate dem_eth in {3,4,90} [1=6 2=3]; med_satellite/las2004 (SATEL): 7 of 1865 values outside gate dem_eth in {1,2} [3=3 4=1 90=3]; edu_abr_att_det/las2004 (MAXOPLBL): 74 of 2071 values outside gate dem_gen in {1} [0=5 2=69]; att_isl12/sim2006 (KASSA): 9 of 3075 values outside gate dem_eth in {3,4,90} [1=6 2=3]; med_tv_orig_days/las2004 (TVEIGEN): 7 of 1866 values outside gate dem_eth in {1,2} [3=3 4=1 90=3]; rel_veil_wife/sim2006 (VROUDOEK): 9 of 730 values outside gate dem_sex in {1} [2=9]; cul_party_type/las2004 (FEESTTYP): 114 of 2283 values outside gate svy_routing_mig in {1} [0=114]; cul_party_pub/las2004 (FEESTPUB): 115 of 2286 values outside gate svy_routing_mig in {1} [0=115]
- PASS relationship layer follows its rules (has/cores indicators, 9 partner copies vs the linked partner's base value)
- PASS asked-to table (75 items in one respondent type's questionnaire only) holds, and no further item shows the pattern
- PASS SIM 2020 split-half annotations agree with the halves that carry values (251 source items)
- PASS value-map grammar (exact, ranges with negative bounds, quoted strings, wildcard) behaves as documented on synthetic input
- PASS value-map review (labels read against target labels; 165 approvals in crosswalks/label_approvals.csv): every two-valued mapping reads as a yes/no or is approved; every cross-survey reuse with differing labels is approved
- PASS household-survey merge: 1 declared exception(s) in crosswalks/merge_exceptions.csv took effect in the source companions; undeclared missing-code-over-valid cells kept by decision: SPVN2003 LEEFTD2 (1), SPVN2003 LEEFTD3 (1)

## Step logs

- SPVA2002 harmonized: 13504 persons (4199 heads, 4122 other interviewed, 5183 roster only), 1631 variables
- spvn2003: self-reported (pp) value preferred over roster value for  persons: LEEFTIJD (17), LEEFTD1 (8), LEEFTD2 (7), LEEFTD3 (5)
- SPVN2003 harmonized: 9119 persons (3547 heads, 2047 other interviewed, 3525 roster only), 1631 variables
- LAS2004 harmonized: 4096 persons (individual sample), 1631 variables
- SIM2006 harmonized: 5250 persons (individual sample), 1631 variables
- SING2009 harmonized: 6911 persons (individual sample), 1631 variables
- SIM2011 harmonized: 4125 persons (individual sample), 1631 variables
- SIM2015 harmonized: 6829 persons (individual sample), 1631 variables
- SIM2020 harmonized: 5323 persons (individual sample), 1631 variables
- CPI factors applied: 2002 -> x1.2386, 2003 -> x1.2131, 2004 -> x1.1987, 2006 -> x1.1659, 2009 -> x1.1062, 2011 -> x1.0675, 2015 -> x1.0000, 2020 -> x0.9302
- Migrant routing in the person samples: LAS2004 3454 of 4096 (self-reported natives with migrant routing: 24); SIM2006 4208 of 5250 (self-reported natives with migrant routing: 0); SING2009 5952 of 6911 (self-reported natives with migrant routing: 3); SIM2011 3310 of 4125 (self-reported natives with migrant routing: 23); SIM2015 5783 of 6829 (self-reported natives with migrant routing: 0); SIM2020 4552 of 5323 (self-reported natives with migrant routing: 0)
- Partner links in the household samples: SPVA2002 5098 linked persons, 1650 heads/partners without a co-resident partner, 0 in ambiguous rosters; SPVN2003 2454 linked persons, 2320 heads/partners without a co-resident partner, 0 in ambiguous rosters
- Main file: 55157 persons x 1642 variables -> impd_cs_v0_5_1.{dta,rds,csv}
- Source file SPVA2002: 13504 persons x 339 variables -> impd_cs_v0_5_1_source_spva2002.{dta,rds}
- Source file SPVN2003: 9119 persons x 285 variables -> impd_cs_v0_5_1_source_spvn2003.{dta,rds}
- Source file LAS2004: 4096 persons x 571 variables -> impd_cs_v0_5_1_source_las2004.{dta,rds}
- Source file SIM2006: 5250 persons x 377 variables -> impd_cs_v0_5_1_source_sim2006.{dta,rds}
- Source file SING2009: 6911 persons x 247 variables -> impd_cs_v0_5_1_source_sing2009.{dta,rds}
- Source file SIM2011: 4125 persons x 374 variables -> impd_cs_v0_5_1_source_sim2011.{dta,rds}
- Source file SIM2015: 6829 persons x 241 variables -> impd_cs_v0_5_1_source_sim2015.{dta,rds}
- Source file SIM2020: 5323 persons x 280 variables -> impd_cs_v0_5_1_source_sim2020.{dta,rds}
- Routing gates checked against the data: 697 source x gate pairs, 630 hold, 67 hold with exceptions (<= 10% of values outside), 0 do not hold -> docs/routing_check.csv
