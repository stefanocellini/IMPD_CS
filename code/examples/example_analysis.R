# example_analysis.R : worked example for docs/example_analysis.md (not part of the build).
#
# Question: how often do persons with a migration background spend leisure time with native Dutch, across the eight
# surveys (2002-2020), and how does this go together with problems speaking Dutch?  Descriptive and correlational,
# for illustration of the workflow in the codebook's "Start here" (steps 2-6); not a substantive analysis.
#
# Run from the project root:  Rscript code/examples/example_analysis.R   (output: code/examples/example_analysis_R.log)
suppressPackageStartupMessages({ library(haven); library(dplyr); library(tidyr); library(survey) })
options(width = 160, survey.lonely.psu = "adjust")
ROOT <- Sys.getenv("IMPD_ROOT", unset = getwd())
source(file.path(ROOT, "code", "R", "impd_tools.R"))
sink(file.path(ROOT, "code", "examples", "example_analysis_R.log"), split = TRUE)
f <- max(list.files(file.path(ROOT, "data", "derived"), "^impd_public_v[0-9_]+\\.rds$", full.names = TRUE))
cat("Data file:", basename(f), "\n")
d <- readRDS(f)
num <- function(x) as.vector(unclass(x))                                 # drop labels, keep tagged NA as NA

# ---- step 2/3: measures (see their codebook entries) ----------------------------------------------------------------
VARS <- c("soc_leis_nl", "lang_prob_spk", "dem_eth", "dem_gen", "dem_sex", "dem_age_cat3", "svy_wgt")
cat("\n== Eligibility statements (impd_universe) ==\n")
print(as.data.frame(impd_universe(c("soc_leis_nl", "lang_prob_spk"), ROOT))[, c("target", "universe_en")], right = FALSE)

# ---- step 4: population --------------------------------------------------------------------------------------------
# interviewed persons (no roster-only rows) of a known migrant origin group (dem_eth 1-11, which also drops the native
# household members of SPVA 2002 - weight 0 - and 266 SPVN 2003 members without an origin code), first or second
# generation, aged 15+ (dem_age_cat3 is valid in every survey)
a <- d %>% filter(num(svy_resptype) %in% c(1, 2, 4), num(dem_eth) %in% 1:11, num(dem_gen) %in% c(1, 2), !is.na(dem_age_cat3)) %>%
  mutate(survey = as.character(svy_name), year = svy_year)
cat("\nAnalysis population (interviewed, migrant origin group, 15+):\n"); print(table(a$survey))

# ---- step 5: joint sample per survey --------------------------------------------------------------------------------
cat("\n== impd_sample: descriptive variables ==\n")
s1 <- impd_sample(a, c("soc_leis_nl", "dem_eth", "dem_gen", "dem_sex", "dem_age_cat3", "svy_wgt"))
cat("\n== impd_sample: with lang_prob_spk (stops: SPVN 2003 did not collect it) ==\n")
r <- try(impd_sample(a, c("soc_leis_nl", "lang_prob_spk", "svy_wgt")), silent = TRUE); cat(r, "\n")
s2 <- impd_sample(a, c("soc_leis_nl", "lang_prob_spk", "dem_sex", "dem_age_cat3", "dem_gen", "svy_wgt"),
                  surveys = setdiff(unique(a$survey), "SPVN2003"), quiet = TRUE)

# ---- step 6: analysis ----------------------------------------------------------------------------------------------
a <- a %>% mutate(often = as.integer(num(soc_leis_nl) == 1),                    # 1 often/always vs 2 sometimes, 3 never
                  eth = as.character(as_factor(dem_eth)),
                  gen = c("1st generation", "2nd generation")[num(dem_gen)],
                  # lang_prob_spk 4 'does not speak Dutch' exists in SIM 2011/2015/2020 only; the earlier surveys fold it
                  # into 'often' (see the entry's note) - so recode 4 -> 1 explicitly (missing values stay missing) to get
                  # one three-class variable for all surveys
                  lang3 = factor(ifelse(num(lang_prob_spk) == 4, 1, num(lang_prob_spk)), 3:1, c("never", "sometimes", "often / does not speak Dutch")),
                  w = num(svy_wgt))
stopifnot(sum(num(a$lang_prob_spk) == 4, na.rm = TRUE) == sum(a$lang3 == "often / does not speak Dutch" & num(a$lang_prob_spk) == 4, na.rm = TRUE),   # every 4 landed in 'often'
          sum(!is.na(a$lang3)) == sum(!is.na(a$lang_prob_spk)))                                                                          # and nothing else moved
wpct <- function(x, w) round(100 * sum(w * x, na.rm = TRUE) / sum(w[!is.na(x)]), 1)

cat("\n== Table 1: weighted % often/always leisure time with native Dutch, by survey and origin group (n unweighted) ==\n")
t1 <- a %>% filter(!is.na(often), !is.na(w)) %>% group_by(survey, year, eth) %>%
  summarise(pct = wpct(often, w), n = n(), .groups = "drop") %>% filter(n >= 50) %>%
  mutate(cell = sprintf("%s (%d)", pct, n)) %>% select(-pct, -n) %>%
  pivot_wider(names_from = eth, values_from = cell) %>% arrange(year)
print(as.data.frame(t1), row.names = FALSE, na.print = "")

cat("\n== Table 2: weighted % often/always, by survey and generation ==\n")
t2 <- a %>% filter(!is.na(often), !is.na(w)) %>% group_by(survey, year, gen) %>%
  summarise(pct = wpct(often, w), n = n(), .groups = "drop") %>% mutate(cell = sprintf("%s (%d)", pct, n)) %>%
  select(-pct, -n) %>% pivot_wider(names_from = gen, values_from = cell) %>% arrange(year)
print(as.data.frame(t2), row.names = FALSE)

cat("\n== Table 3: weighted % often/always, by survey and problems speaking Dutch (7 surveys; SPVA 2002: heads only) ==\n")
t3 <- a %>% filter(!is.na(often), !is.na(w), !is.na(lang3)) %>% group_by(survey, year, lang3) %>%
  summarise(pct = wpct(often, w), n = n(), .groups = "drop") %>% mutate(cell = sprintf("%s (%d)", pct, n)) %>%
  select(-pct, -n) %>% pivot_wider(names_from = lang3, values_from = cell) %>% arrange(year)
print(as.data.frame(t3), row.names = FALSE)

cat("\n== Pooled logit: often ~ lang3 + sex + age + generation + origin group + survey (fixed effects) ==\n")
cat("Weights: svy_wgt rescaled to mean 1 within survey (each survey contributes in proportion to its analytic n).\n")
cat("Clusters: household (id_hh) in SPVA 2002, the person elsewhere.  Survey fixed effects: within-survey association.\n")
m <- a %>% filter(!is.na(often), !is.na(w), !is.na(lang3), !is.na(dem_sex)) %>%
  group_by(survey) %>% mutate(w1 = w / mean(w)) %>% ungroup() %>%
  mutate(clus = ifelse(is.na(id_hh), paste(survey, id_person), paste(survey, num(id_hh))),
         sex = as_factor(dem_sex), age3 = as_factor(dem_age_cat3), gen = factor(gen), survey = factor(survey))
cat("Analytic n:", nrow(m), "\n"); print(table(m$survey))
des <- svydesign(ids = ~clus, weights = ~w1, data = m)
fit <- svyglm(often ~ lang3 + sex + age3 + gen + eth + survey, design = des, family = quasibinomial())
co <- summary(fit)$coefficients
cat("Odds ratios (origin-group and survey fixed effects included, not shown):\n")
print(round(cbind(OR = exp(co[, 1]), `OR low` = exp(co[, 1] - 1.96 * co[, 2]), `OR high` = exp(co[, 1] + 1.96 * co[, 2]), p = co[, 4])[!grepl("^(eth|survey|\\(Int)", rownames(co)), ], 3))
sink()
