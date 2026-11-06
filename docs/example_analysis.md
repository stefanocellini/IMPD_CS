# Worked example: leisure-time contact with native Dutch, 2002-2020

A walk through the workflow of the codebook's "Start here" - from finding the measures to reporting the analysis - on one question that every survey asked: how often do persons with a migration background spend their leisure time with native Dutch (`soc_leis_nl`), and how does this go together with problems speaking Dutch (`lang_prob_spk`)? The analysis is descriptive and correlational and is here to show the workflow - what the codebook entries tell you before you compute anything, what `impd_sample()` reveals about the joint sample, and how the weighting and pooling choices are stated - not to make a substantive claim.

The scripts are `code/examples/example_analysis.R` and `code/examples/example_analysis.do` (run from the project root; they take the newest `data/derived/impd_public_v*` file; the R script also needs the `survey` package, the Stata script Stata 17 or later). Their logs, `example_analysis_R.log` and `example_analysis_Stata.log`, are kept next to them: every cell and count below is identical in both engines, and the model coefficients agree to four decimals (the standard errors differ in the fourth decimal through the finite-sample correction of Stata's `vce(cluster)`).

## Find the measures

`docs/codebook_variables.csv` filtered on the `avail_*` columns, or the finder in `docs/codebook.html`, gives:

| Variable | What it is | Available |
|---|---|---|
| `soc_leis_nl` | Spends leisure time with native Dutch (often/always, sometimes, never) | all 8 surveys |
| `lang_prob_spk` | Problems speaking Dutch in conversation | 7 surveys (not SPVN 2003) |
| `dem_eth`, `dem_gen`, `dem_sex`, `dem_age_cat3` | origin group, generation, sex, age in three classes | all 8 (`dem_age_cat3` is the coarse age variable derived for every survey) |
| `svy_wgt`, `svy_resptype`, `id_hh` | survey weight, respondent type, household identifier | all 8 (`id_hh` is `.e` in the person samples) |

The comparability class of both measures is *approximate match*: the same construct, with wording differences that the entries list. That is a reading aid; the entries are what to read.

## Inspect the measures

The entries of `soc_leis_nl` and `lang_prob_spk` (codebook section 5) say five things that shape the analysis.

1. **Wording.** The question is the same three-way frequency item in every survey, but the object changes with the vocabulary of the time: *(blanke) Nederlanders* (SPVA 2002), *Nederlanders* (SPVN 2003), *(witte) Nederlanders* (LAS 2004/05), *autochtone Nederlanders* (SIM 2006 - SIM 2015), *Nederlanders zonder migratieachtergrond* via a text fill (SIM 2020). SPVA/SPVN/LAS/SIM 2006 offered *ja, vaak / ja, soms / nee, nooit*, SING 2009 onwards *vaak / soms / nooit*; SPVN 2003 also printed *weet niet* (code 7, harmonized to `.a`). Nothing here prevents a comparison, but the entry is where a reader checks that the harmonized label *Often/always* stands for *vaak* everywhere.
2. **Natives were asked a mirror question** about contact with persons with a migration background (LAS 2004/05 and SIM 2006 as separate source variables `VRTIJDAL`/`VRTIJDN`, SIM 2011 onwards through the fill in one variable). `soc_leis_nl` therefore holds two different questions for the two populations; the analysis below keeps persons with a migration background only.
3. **SPVN 2003 asked the item in the mini questionnaire only** (entry note and eligibility statement; source label *alleen mini's*): heads of household never saw it and are `.e` (`crosswalks/asked_to.csv`). The SPVN 2003 figures describe the other interviewed household members aged 12+, not heads - a different population from the other seven surveys, and the reason the SPVN 2003 rows below are read apart.
4. **SING 2009 asked a random half** of the respondents with a migration background (script condition `exp2431 = 1`; the deposit carries no split indicator, so the harmonized routing row prints only `svy_routing_mig in {1}` and the half shows up as `.c` in the data). The estimate is unbiased for the SING population if the split is random, with half the sample size.
5. **`lang_prob_spk` differs in who answered and in its categories.** SPVA 2002 asked heads of household only (main questionnaire); SPVN 2003 did not ask it; SIM 2020 asked it to the first generation only (routing row `dem_gen in {1}`, from the script's `Q9004,1`); one second-generation respondent nonetheless has an answer, a routing exception the scripts keep, so the SIM 2020 rows of Table 3 and the model hold 3,308 first-generation respondents and this one. SIM 2011/2015/2020 have a separate code 4 *does not speak Dutch* that the earlier surveys fold into *often* (entry note; SIM 2006's source label *ja, vaak moeite / spreekt geen Nederlands*). The scripts recode 4 to 1 explicitly - `ifelse(x == 4, 1, x)`, `cond(x == 4, 1, x)` - and assert that every 4 landed there, so that one three-class variable - never / sometimes / often or does not speak Dutch - has the same meaning in all seven surveys.

## Define the study population

Interviewed persons (`svy_resptype` 1, 2 or 4: no roster-only rows) of a known migrant origin group (`dem_eth` 1-11), first or second generation (`dem_gen` 1 or 2), aged 15 or older (`dem_age_cat3` valid), and - in the person samples - routed through the migrant version of the questionnaire (`svy_routing_mig` = 1; `.e` in SPVA/SPVN, which have no such routing). The routing condition matters because the item follows the route, not the origin code: 9 SIM 2006 respondents with a migrant origin code were routed as natives and answered the natives' mirror question (point 2 above); without the condition they enter Table 1 with an answer to a different question. The origin-group condition also drops two groups of household members that would otherwise sit in the file: the native Dutch members of SPVA 2002 migrant households (207 interviewed persons aged 15+ with `dem_eth` = 90 and `dem_gen` = 2; their household weight is 0) and 231 SPVN 2003 members without an origin-group code (plain missing in the source).

Who that population is differs by survey (codebook section 1): households of four origin groups in 13 municipalities (SPVA 2002) and of five refugee groups in 12 municipalities (SPVN 2003); persons aged 15-64 in the 50 largest municipalities (LAS 2004/05); national samples aged 15+ (SIM 2006 onwards, SING 2009). The per-survey estimates are estimates for these populations, weighted with each survey's own `svy_wgt`.

## Check the joint sample

```r
impd_sample(a, c("soc_leis_nl", "dem_eth", "dem_gen", "dem_sex", "dem_age_cat3", "svy_wgt"))
```

| survey | n_records | n_complete | share_complete |
|---|---|---|---|
| SPVA2002 | 7464 | 7184 | 0.962 |
| SPVN2003 | 5077 | 1586 | 0.312 |
| LAS2004 | 3424 | 3424 | 1.000 |
| SIM2006 | 4203 | 4201 | 1.000 |
| SING2009 | 5830 | 2953 | 0.507 |
| SIM2011 | 3287 | 3287 | 1.000 |
| SIM2015 | 5783 | 5783 | 1.000 |
| SIM2020 | 4552 | 4552 | 1.000 |

The detail lines explain the two low shares: SPVN 2003 has 3,488 records with `.e` on `soc_leis_nl` (the heads, point 3 above), SING 2009 has 2,868 `.c` (the other random half, point 4). Adding `lang_prob_spk` makes the function stop - `survey(s) with no complete record on soc_leis_nl, lang_prob_spk, svy_wgt: SPVN2003 (not collected: lang_prob_spk)` - which is the intended behaviour: a survey cannot silently drop out of a pooled model. Rerun without SPVN 2003 the shares are 0.546 for SPVA 2002 (heads only) and 0.727 for SIM 2020 (first generation only), as the entries predicted.

## Run and report the analysis

**Per-survey estimates** use `svy_wgt` as supplied. Cells are the weighted percentage answering *often/always*; the unweighted n is in brackets; cells with fewer than 50 respondents are not shown.

Table 1. By survey and origin group

| survey | Turkish | Moroccan | Surinamese | Antillean/Aruban | Afghan | Iraqi | Iranian | Former Yugoslav | Somali | Polish | Chinese |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPVA 2002 | 16.8 (2282) | 19.5 (1978) | 49.7 (1714) | 54.7 (1211) | | | | | | | |
| SPVN 2003 (members, not heads) | | | | | 37.2 (408) | 35.9 (383) | 52.0 (322) | 56.8 (335) | 40.4 (138) | | |
| LAS 2004/05 | 28.8 (946) | 37.0 (914) | 55.5 (760) | 55.4 (804) | | | | | | | |
| SIM 2006 | 18.5 (1124) | 24.8 (1030) | 46.5 (1055) | 49.1 (992) | | | | | | | |
| SING 2009 (random half) | | | | | 38.8 (515) | 33.0 (508) | 43.8 (469) | | 31.5 (475) | 42.3 (501) | 29.7 (486) |
| SIM 2011 | 16.2 (815) | 12.2 (829) | 35.8 (780) | 43.1 (863) | | | | | | | |
| SIM 2015 | 24.4 (920) | 25.5 (951) | 45.5 (1045) | 49.2 (1112) | | | | | 22.8 (626) | 33.6 (1129) | |
| SIM 2020 | 30.4 (696) | 34.3 (570) | 48.0 (638) | 45.7 (592) | | | 37.0 (855) | | 24.1 (519) | 26.4 (682) | |

Table 2. By survey and generation

| survey | 1st generation | 2nd generation |
|---|---|---|
| SPVA 2002 | 25.8 (5471) | 47.2 (1714) |
| SPVN 2003 (members, not heads) | 39.6 (1473) | 79.0 (113) |
| LAS 2004/05 | 36.7 (2646) | 60.5 (778) |
| SIM 2006 | 26.2 (3187) | 49.9 (1014) |
| SING 2009 (random half) | 33.8 (2763) | 71.9 (191) |
| SIM 2011 | 18.6 (2269) | 35.6 (1018) |
| SIM 2015 | 28.9 (4228) | 42.2 (1555) |
| SIM 2020 | 30.8 (3309) | 46.8 (1243) |

The generation definition itself differs (entry of `dem_gen`): SPVA/SPVN count persons who arrived before age 6 as second generation, the later surveys count those born in the Netherlands. The shares of Tables 2 and 3 pool the origin groups of a survey; where a survey's weight is calibrated within origin groups (SING 2009), such a pooled share describes the survey's mixture of groups rather than a population total.

Table 3. By survey and problems speaking Dutch (seven surveys)

| survey | never | sometimes | often / does not speak Dutch |
|---|---|---|---|
| SPVA 2002 (heads only) | 49.7 (2219) | 15.9 (1202) | 10.1 (652) |
| LAS 2004/05 | 53.7 (2105) | 22.8 (858) | 22.9 (461) |
| SIM 2006 | 41.7 (2889) | 15.3 (818) | 6.3 (494) |
| SING 2009 (random half) | 57.8 (1110) | 25.4 (1195) | 14.1 (649) |
| SIM 2011 | 31.0 (2323) | 9.0 (544) | 7.1 (420) |
| SIM 2015 | 40.3 (3389) | 21.0 (1412) | 17.2 (982) |
| SIM 2020 (first generation only) | 44.0 (1386) | 21.5 (1081) | 14.8 (842) |

**A pooled model, with the pooling choice spelled out.** Logit of *often/always* on the three-class language variable, sex, age class and generation, with origin-group and survey fixed effects, on the 27,029 complete records of the seven surveys. Weights: `svy_wgt` rescaled to mean 1 within each survey, so that every survey contributes in proportion to its analytic n and no survey's population size drives the estimate (the weights reproduce each survey's own population, not a pooled one - codebook section 1). Standard errors clustered on the household (`id_hh`) in SPVA 2002 and on the person elsewhere. With survey fixed effects the coefficients are within-survey associations averaged over the surveys; they say nothing about change over time.

| | odds ratio | 95% interval |
|---|---|---|
| problems speaking Dutch: sometimes (vs never) | 0.38 | 0.35 - 0.41 |
| problems speaking Dutch: often / does not speak (vs never) | 0.26 | 0.23 - 0.29 |
| female (vs male) | 0.96 | 0.90 - 1.03 |
| age 25-44 (vs 15-24) | 0.84 | 0.77 - 0.92 |
| age 45+ (vs 15-24) | 0.81 | 0.73 - 0.90 |
| second generation (vs first) | 1.75 | 1.60 - 1.92 |

R: `svyglm(often ~ lang3 + sex + age3 + gen + eth + survey, design = svydesign(ids = ~clus, weights = ~w1), family = quasibinomial())`. Stata: `logit often ib3.lang3 i.dem_sex i.dem_age_cat3 i.dem_gen i.dem_eth i.svy_id [pweight = w1], vce(cluster clus) or`.

## What to take from it

- The entries, not the availability table, decide the design: three of the eight surveys measure `soc_leis_nl` on a different population than the label suggests (SPVN 2003 members only, SING 2009 a random half, natives a mirror question), and `lang_prob_spk` changes respondents twice (SPVA 2002 heads, SIM 2020 first generation). `impd_sample()` makes each of these visible as a count before any estimate is made.
- A pooled coefficient is only as good as its stated pooling rule. Rescaling the weights to mean 1 within survey is one rule among several; the per-survey tables are the estimates that need no such rule.
- Differences between surveys in the tables combine population, wording, generation definition and group composition; none of them is a trend.
