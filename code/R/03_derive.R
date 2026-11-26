# 03_derive.R : derived variables that are not simple recodes.  Every rule is named in the `derive` column of
# crosswalks/variable_map.csv and implemented identically here and in code/Stata/03_derive.do.
#   create rules (target built from scratch):
#     id_hh, id_person                 unique identifiers across surveys (hh_pp_ro: household x member; flat: person number)
#     municipality / municipality_name CBS gemeentecode via crosswalks/municipalities.csv (hh_pp_ro surveys)
#     cpi2015:<base>                   CPI-deflated euro amounts (2015 = 100), crosswalks/cpi.csv
#   post-processing rules (target harmonized in 02, then completed/modified here):
#     fill0_interviewed   system-missing -> 0 for interviewed persons (indicator items)
#     age_cat             dem_age_cat cut from dem_age where the target is .e (SPVA/SPVN)
#     brthcntry_group     dem_brthcntry from dem_eth x dem_gen (CBS definition) where .e (SIM)
#     cit_nl_orig         nat_cit from nat_nl x nat_orig where .e (SIM)
#     mode_video          svy_mode = 3 where svy_video == 1 (SIM 2020)
#     split_random        svy_split from the eight random_* source variables (SIM 2020)
#     rel_merge20         rel_den_det: SIM 2020 second group list (religie2_kl, target rel_den_det20b) merged in
#     rel_cat20           rel_den_cat from rel_den_det for SIM 2020
#     plus_months:<mo>    durations in fractional years: years + months/12; months-only (.c year) -> months/12 (s. 34)
#     las_vol_union       soc_volunteer LAS 2004/05 from the whole V229/V231 block (s. 34)
#     cultural_only_e     SPVA svy_proxy 8: mini-questionnaire targets (crosswalks/cultural_only_e.csv) -> .e (s. 34)
#   final pass: remaining system-missing values get the survey's sysmis_tag (surveys.csv): .d or .c
#   after it: spvn_applicable_gaps - known-applicable blanks (hh_size, hh_comp) and known recipients/members with a
#   system-missing type -> .d (s. 34)
source(file.path(Sys.getenv("IMPD_ROOT", unset = getwd()), "code", "R", "00_setup.R"))

all <- readRDS(P("data", "interim", "harmonized_all.rds"))
flat_ids <- INCLUDED$svy_id[INCLUDED$structure == "flat"]
is_flat <- all$svy_id %in% flat_ids
is_e <- function(x) is.na(x) & is_tagged_na(x, "e")

# ---- identifiers
# svy_key (surveys.csv) is the immutable per-survey key: it never changes when a wave is inserted, so id_person and
# id_hh do not change when a survey is added (svy_id is only the chronological order)
svy_key <- INCLUDED$svy_key[match(all$svy_id, INCLUDED$svy_id)]
all$id_hh     <- ifelse(is_flat, tagged_na("e"), svy_key * 1e9 + all$HHNUMMER)
all$id_person <- ifelse(is_flat, svy_key * 1e11 + all$PERSNR, all$id_hh * 100 + all$GEZLIDNR)
stopifnot(!anyDuplicated(all$id_person))

# ---- municipality (needs the survey-internal GEMEENTE code from the source frames of hh_pp_ro surveys)
src_mun <- map_dfr(seq_len(nrow(INCLUDED)), function(i) {
  key <- str_to_lower(INCLUDED$svy_name[i])
  if (INCLUDED$structure[i] == "flat") return(NULL)
  d <- readRDS(P("data", "interim", paste0("source_", key, ".rds")))
  tibble(svy_id = INCLUDED$svy_id[i], HHNUMMER = d$HHNUMMER, GEZLIDNR = d$GEZLIDNR, gem = as.numeric(d$GEMEENTE), survey = key)
})
all <- all %>% left_join(src_mun, by = c("svy_id", "HHNUMMER", "GEZLIDNR"))
mun <- MUNIS %>% transmute(survey, gem = source_code, cbs_code = as.numeric(cbs_code), cbs_name)
all <- all %>% left_join(mun, by = c("survey", "gem"))
unmatched <- all %>% filter(!is.na(gem) & gem >= 0 & is.na(cbs_code)) %>% count(survey, gem)
if (nrow(unmatched)) stop("municipality codes without CBS match: ", paste(unmatched$survey, unmatched$gem, collapse = "; "))
all$geo_mun_cbs  <- ifelse(is_flat, tagged_na("e"), ifelse(is.na(all$gem) | all$gem < 0, tagged_na("d"), all$cbs_code))
all$geo_mun_name <- all$cbs_name
all <- all %>% select(-gem, -cbs_code, -cbs_name, -survey)

# ---- CPI deflation to constant 2015 euro
deflate <- function(x, year) {
  f <- 100 / CPI$cpi_2015[match(year, CPI$year)]
  y <- x * f
  y[is.na(x)] <- x[is.na(x)]          # keep tagged missings
  y
}
cpi_targets <- VARMAP %>% filter(str_starts(derive, "cpi2015:"))
for (i in seq_len(nrow(cpi_targets))) {           # cpi2015:<base>[@<year>]: fixed reference year when the amount refers to a calendar year (SIM 2006: 2005)
  spec <- sub("^cpi2015:", "", cpi_targets$derive[i]); base <- sub("@.*$", "", spec)
  yr <- if (grepl("@", spec, fixed = TRUE)) rep(as.integer(sub("^.*@", "", spec)), nrow(all)) else all$svy_year
  all[[cpi_targets$target[i]]] <- deflate(all[[base]], yr)
}
logmsg("CPI factors applied: %s", paste(sprintf("%d -> x%.4f", INCLUDED$svy_year, 100 / CPI$cpi_2015[match(INCLUDED$svy_year, CPI$year)]), collapse = ", "))

# ---- plus_months:<mo> : durations in fractional years (audit 25 Nov 2026, decisions s. 34).  SIM 2011 records
#      years and months separately ('in addition to the years'); SIM 2015 lets the respondent answer in years OR
#      months (months-only answers left the year target .c).  Combined: years + months/12 where both are valid;
#      months/12 where the year is .c and the months are valid.  A year with unknown months keeps the year; any
#      other missing year keeps its tag.  Months above 11 (3 SIM 2011 cells) add more than one year, as recorded.
pm_targets <- VARMAP %>% filter(str_starts(derive, "plus_months:"))
for (i in seq_len(nrow(pm_targets))) {
  t <- pm_targets$target[i]; mo_t <- sub("^plus_months:", "", pm_targets$derive[i])
  if (!t %in% names(all) || !mo_t %in% names(all)) next
  x <- all[[t]]; mo <- all[[mo_t]]
  both <- !is.na(x) & !is.na(mo)
  x[both] <- x[both] + mo[both] / 12
  alt <- is.na(x) & is_tagged_na(x) & na_tag(x) == "c" & !is.na(mo)
  x[alt] <- mo[alt] / 12
  all[[t]] <- x
  logmsg("plus_months %s: %d year+month cells combined, %d months-only answers recovered", t, sum(both), sum(alt))
}

# ---- las_vol_union : soc_volunteer, LAS 2004/05 (audit 25 Nov 2026, decisions s. 34).  VRAAG 231 (VRWWAND) asks
#      about volunteering for ANOTHER organisation after VRAAG 229 collected nine organisation types (soc_vol01-09),
#      so the residual item alone understates volunteering.  Any volunteering: a yes in any component; definite no:
#      no yes, no unknown component, and VRWWAND = no; otherwise .a (some component unknown).
las <- all$svy_id == INCLUDED$svy_id[tolower(INCLUDED$svy_name) == "las2004"]
comp <- as.matrix(all[las, paste0("soc_vol0", 1:9)])
anyy <- rowSums(comp == 1, na.rm = TRUE) > 0
anyu <- rowSums(sapply(paste0("soc_vol0", 1:9), function(n) { x <- all[[n]][las]; !is.na(is_tagged_na(x)) & is_tagged_na(x) & na_tag(x) %in% "a" })) > 0
y <- all$soc_volunteer[las]
out <- y
out[!is.na(y) & y == 0 & anyy] <- 1
out[!is.na(y) & y == 0 & !anyy & anyu] <- tagged_na("a")
all$soc_volunteer[las] <- out
logmsg("las_vol_union: %d listed-organisation volunteers added to soc_volunteer, %d uncertain set .a (LAS 2004/05)",
       sum(!is.na(y) & y == 0 & anyy), sum(!is.na(y) & y == 0 & !anyy & anyu))

# ---- fill0_interviewed
for (t in VARMAP$target[VARMAP$derive == "fill0_interviewed"]) {
  x <- all[[t]]
  sel <- is.na(x) & !is_tagged_na(x) & all$svy_resptype %in% c(1L, 2L)
  x[sel] <- 0
  all[[t]] <- x
}

# ---- age_cat : classes 15-24 ... 75+ from dem_age where dem_age_cat is .e and age is known
x <- all$dem_age_cat; a <- all$dem_age
sel <- is_e(x) & !is.na(a)
x[sel] <- ifelse(a[sel] < 15, 0, pmin(floor((a[sel] - 15) / 10) + 1, 7))   # 0 = under 15 (SPVA/SPVN roster children)
sel2 <- is_e(x) & !is_flat & is.na(a)
x[sel2] <- a[sel2]                                                           # carry the missing tag of dem_age
all$dem_age_cat <- x

# ---- age_cat3 : common 3-class age (15-24, 25-44, 45+) from dem_age_cat where dem_age_cat3 is .e (SING delivers it)
x <- all$dem_age_cat3; c7 <- all$dem_age_cat
sel <- is_e(x) & !is.na(c7)
x[sel] <- ifelse(c7[sel] == 0, tagged_na("c"), ifelse(c7[sel] == 1, 1, ifelse(c7[sel] %in% 2:3, 2, 3)))   # 0 = under 15: outside the 15+ universe
sel2 <- is_e(x) & is.na(c7) & !is_tagged_na(c7, "e")
x[sel2] <- c7[sel2]                                                          # carry the age variable's missing status: .a/.b/.d, and a still-untagged
                                                                             # blank, which receives the survey's system-missing tag below (LAS: .c)
all$dem_age_cat3 <- x

# ---- brthcntry_group : SIM (CBS definition) first generation -> country of the origin group, otherwise Netherlands
GROUP_COUNTRY <- c(`1` = 6043, `2` = 5022, `3` = 5007, `4` = 7011, `5` = 6023, `6` = 5043, `7` = 5012, `8` = 6045, `9` = 6013, `10` = 7028, `11` = 6022, `90` = 6030)
x <- all$dem_brthcntry; eth <- all$dem_eth; gen <- all$dem_gen
sel <- is_e(x) & is_flat & !is.na(eth) & !is.na(gen)
x[sel & gen == 1] <- GROUP_COUNTRY[as.character(eth[sel & gen == 1])]
x[sel & gen == 1 & is.na(x)] <- tagged_na("d")                  # first generation of an 'other' or unknown origin group: country unknown
x[sel & gen %in% c(0, 2)] <- 6030
carry <- is_e(x) & is_flat & is.na(gen) & is_tagged_na(gen)      # generation unknown / not applicable: carry its tag
x[carry] <- gen[carry]
all$dem_brthcntry <- x
# brthcntry_src : provenance flag (1 observed in the household surveys, 2 inferred in the person samples)
all$dem_brthcntry_src <- ifelse(is_flat, 2, ifelse(is.na(all$dem_brthcntry) & is_tagged_na(all$dem_brthcntry, "e"), tagged_na("e"), 1))

# ---- routing_mig : did the CAPI script give this person the migrant-background routing?  (person samples)
GATES <- c("lang_prob_spk", "lang_prob_read", "iden_scale", "iden_orig5", "int_crs", "int_nlcrs", "trn_house", "med_krant_orig_cat")   # items never asked to the native routing in any person sample
answered <- function(v) !is.na(v) | (is.na(v) & is_tagged_na(v) & !is_tagged_na(v, "c") & !is_tagged_na(v, "e"))   # valid or .a/.b/.d
got <- Reduce(`|`, lapply(GATES[GATES %in% names(all)], function(g) answered(all[[g]])))
all$svy_routing_mig <- ifelse(is_flat, as.numeric(got), tagged_na("e"))
logmsg("Migrant routing in the person samples: %s", paste(sprintf("%s %d of %d (self-reported natives with migrant routing: %d)", INCLUDED$svy_name[INCLUDED$structure == "flat"],
       sapply(INCLUDED$svy_id[INCLUDED$structure == "flat"], function(i) sum(all$svy_routing_mig == 1 & all$svy_id == i, na.rm = TRUE)),
       sapply(INCLUDED$svy_id[INCLUDED$structure == "flat"], function(i) sum(all$svy_id == i)),
       sapply(INCLUDED$svy_id[INCLUDED$structure == "flat"], function(i) sum(all$svy_routing_mig == 1 & all$svy_id == i & all$dem_eth == 90, na.rm = TRUE))), collapse = "; "))

# ---- cit_nl_orig : 1 Dutch only, 2 dual, 3 origin only, 4 neither
x <- all$nat_cit; nl <- all$nat_nl; org <- all$nat_orig
sel <- is_e(x) & is_flat
nat_for_natives <- all$dem_eth == 90 & !is.na(all$dem_eth)
x[sel & nl %in% 1 & org %in% 1] <- 2
x[sel & nl %in% 1 & org %in% 0] <- 1
x[sel & nl %in% 0 & org %in% 1] <- 3
x[sel & nl %in% 0 & org %in% 0] <- 4
x[is_e(x) & is_flat & nat_for_natives] <- tagged_na("c")   # not asked to the native Dutch reference sample (natives who were routed to the questions keep their answer)
all$nat_cit <- x

# ---- mode_video
all$svy_mode[all$svy_video %in% 1] <- 3

# ---- split_random : non-zero value of the eight random_* variables (SIM 2020 source frame)
src20 <- INCLUDED %>% filter(svy_name == "SIM2020")
if (nrow(src20)) {
  d <- readRDS(P("data", "interim", "source_sim2020.rds"))
  rnd <- d[grep("^random_", names(d))]
  split <- apply(as.matrix(rnd), 1, function(r) { v <- r[!is.na(r) & r > 0]; if (length(v)) v[1] else NA })
  idx <- match(all$PERSNR[all$svy_id == src20$svy_id], d$PERSNR)
  sp <- split[idx]; sp[is.na(sp)] <- tagged_na("d")      # two records without a randomisation flag
  all$svy_split[all$svy_id == src20$svy_id] <- sp
}

# ---- kl9_route : SIM coarsened/constructed variables carry no routing code: SIM 2020 _kl variables use 9 both for
# 'other/refusal/don't know' and for persons routed past the question, SIM 2015 constructed variables are system-missing
# for them.  Where the routing question says 'not applicable', .d / system-missing becomes .c.
ROUTE <- list(c("dem_prtnr_bc_cbs", "dem_has_prtnr", 0), c("dem_prtnr_fa_bc_cbs", "dem_has_prtnr", 0), c("dem_prtnr_ma_bc_cbs", "dem_has_prtnr", 0),
              c("dem_prtnr_age_cat", "dem_has_prtnr", 0), c("edu_abr_att_lvl3", "edu_abr", 0), c("edu_cur_lvl3", "edu_enr", 0),
              c("edu_nl_att_lvl3", "edu_nl", 0), c("lab_ind_sbi08", "lab_emp", 0), c("svy_ncontact", "svy_mode", 1),
              c("mig_reg_days", "dem_gen", 0), c("mig_reg_days", "dem_gen", 2), c("mig_motive_ind_reg", "dem_gen", 0), c("mig_motive_ind_reg", "dem_gen", 2),
              c("edu_nl_att_lvl3", "edu_nl", "c"), c("edu_abr_att_lvl3", "edu_abr", "c"), c("edu_cur_lvl3", "edu_enr", "c"),
              c("dem_prtnr_age_cat", "dem_prtnr_cores", 0), c("lab_ind_sbi08", "lab_emptype", 2), c("lab_ind_sbi08", "lab_emp", "c"))
for (r in ROUTE) {
  x <- all[[r[1]]]; cond <- all[[r[2]]]
  hit <- if (r[3] == "c") is.na(cond) & is_tagged_na(cond, "c") else !is.na(cond) & cond == as.numeric(r[3])
  sel <- is_flat & is.na(x) & (!is_tagged_na(x) | is_tagged_na(x, "d")) & hit
  x[sel] <- tagged_na("c"); all[[r[1]]] <- x
}
# CBS-derived motive ranks: system-missing = motive not among the presumed motives -> .c
for (t in grep("^mig_mot_.*_reg$", names(all), value = TRUE)) { x <- all[[t]]; x[is_flat & is.na(x) & !is_tagged_na(x)] <- tagged_na("c"); all[[t]] <- x }
# ---- rel_merge20 : second religion list of SIM 2020 (religie2_kl, value map of target rel_den_det20b)
if (nrow(src20)) {
  d <- readRDS(P("data", "interim", "source_sim2020.rds"))
  maps <- VALUEMAP %>% filter(target == "rel_den_det20b", survey == "sim2020")
  vm <- apply_value_map(as.numeric(d$religie2_kl), maps)
  y2 <- apply_missing(as.numeric(d$religie2_kl), vm$y, vm$consumed, "sim2020", "religie2_kl")
  idx <- match(all$PERSNR[all$svy_id == src20$svy_id], d$PERSNR)
  x <- all$rel_den_det[all$svy_id == src20$svy_id]
  y2 <- y2[idx]
  take <- is.na(x) & !is.na(y2)                         # list 1 not answered (9 -> .d), list 2 answered
  take[is.na(take)] <- FALSE
  x[take] <- y2[take]
  all$rel_den_det[all$svy_id == src20$svy_id] <- x
}
# ---- rel_none : SIM respondents who do not belong to a religion get 'No religion' (0) in rel_den_det / rel_den_cat
no_rel <- is_flat & !is.na(all$rel_any) & all$rel_any == 0
all$rel_den_det[no_rel] <- 0; all$rel_den_cat[no_rel] <- 0
if (nrow(src20)) {
  # ---- rel_cat20
  det <- all$rel_den_det; cat <- all$rel_den_cat
  s20 <- all$svy_id == src20$svy_id
  cat[s20 & !is.na(det) & det == 0] <- 0
  cat[s20 & !is.na(det) & det >= 11 & det <= 19] <- 1
  cat[s20 & !is.na(det) & det >= 21 & det <= 29] <- 2
  cat[s20 & !is.na(det) & det >= 31 & det <= 39] <- 3
  cat[s20 & !is.na(det) & (det >= 41 | det == 99)] <- 4
  cat[s20 & is.na(det)] <- det[s20 & is.na(det)]    # carry the missing tag
  all$rel_den_cat <- cat
}

# ---- cultural_only_e : SPVA persons with svy_proxy 8 received only the cultural-integration module, no mini
#      questionnaire.  The mini-questionnaire targets (crosswalks/cultural_only_e.csv, from the declared list in
#      surveys/spva2002.py) were never put to them: their blanks are .e, not routing (decisions s. 34).  Runs before the relationship
#      layer, so the partner copies of cultural-only partners propagate .e, and before the final pass, which
#      would otherwise tag these blanks .c.
for (i in seq_len(nrow(INCLUDED))) {
  ce <- CULT_E[CULT_E$survey == tolower(INCLUDED$svy_name[i]), ]
  if (!nrow(ce)) next
  rows <- all$svy_id == INCLUDED$svy_id[i] & !is.na(all$svy_proxy) & all$svy_proxy == 8
  n_e <- 0; n_val <- 0
  for (t in ce$target) {
    if (!t %in% names(all)) next
    x <- all[[t]]
    n_val <- n_val + sum(rows & !is.na(x))
    sel <- rows & is.na(x) & !is_tagged_na(x)
    if (any(sel)) { x[sel] <- tagged_na("e"); all[[t]] <- x; n_e <- n_e + sum(sel) }
  }
  if (n_val > 0) stop(sprintf("cultural_only_e %s: %d valid values in targets declared absent from the cultural-only instrument", tolower(INCLUDED$svy_name[i]), n_val))
  logmsg("cultural_only_e %s: %d cells set .e over %d targets for %d cultural-only respondents", tolower(INCLUDED$svy_name[i]), n_e, nrow(ce), sum(rows))
}

# ---- relationship layer (household surveys): id_prtnr link, partner_copy:<target>, has_prtnr_roster, prtnr_cores_roster
#      (see code/crosswalk_builder/variables_links.py for the definitions)
hhs <- !is_flat
is_hp <- hhs & all$dem_poshh %in% c(0, 1)                                  # head of household or partner of the head
hkey <- paste(all$svy_id, all$HHNUMMER)
link <- rep(NA_integer_, nrow(all)); amb <- rep(FALSE, nrow(all))
for (idx in split(which(is_hp), hkey[is_hp])) {
  if (length(idx) == 2) link[idx] <- rev(idx) else if (length(idx) > 2) amb[idx] <- TRUE
}
has_link <- !is.na(link)
x <- ifelse(is_flat, tagged_na("e"), tagged_na("d"))                      # other members / ambiguous rosters: not identifiable
x[is_hp & !has_link & !amb] <- tagged_na("c")                               # head/partner without a second head/partner record
x[has_link] <- all$id_person[link[has_link]]
all$id_prtnr <- x
logmsg("Partner links in the household samples: %s", paste(sprintf("%s %d linked persons, %d heads/partners without a co-resident partner, %d in ambiguous rosters",
       INCLUDED$svy_name[INCLUDED$structure != "flat"],
       sapply(INCLUDED$svy_id[INCLUDED$structure != "flat"], function(i) sum(has_link & all$svy_id == i)),
       sapply(INCLUDED$svy_id[INCLUDED$structure != "flat"], function(i) sum(is_hp & !has_link & !amb & all$svy_id == i)),
       sapply(INCLUDED$svy_id[INCLUDED$structure != "flat"], function(i) sum(amb & all$svy_id == i))), collapse = "; "))
pc <- VARMAP %>% filter(str_detect(derive, "partner_copy:"))
for (i in seq_len(nrow(pc))) {
  t <- pc$target[i]; src <- sub("^.*partner_copy:", "", pc$derive[i])
  x <- all[[t]]; fill <- hhs & is_e(x)                                     # only cells not collected in the survey
  y <- all[[src]][link]                                                     # the partner's own value
  y[is.na(y) & is_tagged_na(y, "e")] <- tagged_na("d")                      # partner not interviewed: no information
  x[fill & has_link] <- y[fill & has_link]
  plain <- hhs & is.na(x) & !is_tagged_na(x)                                 # untagged sysmis of a head-reported source (no partner)
  x[(fill | plain) & !has_link & is_hp & !amb] <- tagged_na("c")             # no co-resident partner
  x[fill & !has_link & !(is_hp & !amb)] <- tagged_na("d")                    # other members / ambiguous
  all[[t]] <- x
}
# dem_has_prtnr / dem_prtnr_cores from the link and the LAT question
lat <- all$dem_prtnr_lat
for (t in c("dem_has_prtnr", "dem_prtnr_cores")) {
  x <- all[[t]]; fill <- hhs & is_e(x)
  v <- ifelse(has_link, 1, ifelse(lat %in% 1, if (t == "dem_has_prtnr") 1 else 0, ifelse(is_hp & !amb, if (t == "dem_has_prtnr") 0 else tagged_na("c"), tagged_na("d"))))
  x[fill] <- v[fill]; all[[t]] <- x
}

# ---- final pass: remaining system-missing values, tagged per survey (surveys.csv, sysmis_tag) - .d where the file
# codes routing explicitly so that a blank carries no information (SIM 2011/2015/2020), .c where a blank is the
# file's way of saying 'routed past the question or not applicable' (SIM 2006, LAS 2004/05, SING 2009, and - since
# v0.5.3, decisions s. 31 - SPVA 2002/SPVN 2003, whose files code every informative kind of missing explicitly).
# Runs last because the relationship layer above reads untagged system-missing in the household surveys.
for (i in which(INCLUDED$sysmis_tag != "")) {
  rows <- all$svy_id == INCLUDED$svy_id[i]; tg <- INCLUDED$sysmis_tag[i]
  for (t in VARMAP$target[VARMAP$include_main == 1 & VARMAP$type != "str"]) {
    if (!t %in% names(all)) next
    x <- all[[t]]; sel <- rows & is.na(x) & !is_tagged_na(x)
    if (any(sel)) { x[sel] <- tagged_na(tg); all[[t]] <- x }
  }
}

# ---- spvn_applicable_gaps (audit 25 Nov 2026, decisions s. 34).  Runs after the final pass, which tagged the
#      cells .c.  (a) hh_size / hh_comp apply to every household, so a blank cannot be routing: known gaps are .d.
#      (b) A benefit recipient or association member whose type item is system-missing keeps 'unknown', not 'no':
#      the type variable becomes .d and the type indicator dummies that the wildcard made 0 become .d too (the
#      explicit -3/-4 codes are handled in the value map; this covers the sysmis residual).
spvn <- all$svy_id == INCLUDED$svy_id[tolower(INCLUDED$svy_name) == "spvn2003"]
for (t in c("hh_size", "hh_comp")) {
  x <- all[[t]]; sel <- spvn & is_tagged_na(x) & na_tag(x) %in% "c"
  if (any(sel)) { x[sel] <- tagged_na("d"); all[[t]] <- x }
  logmsg("spvn_applicable_gaps: %s %d cells .c -> .d", t, sum(sel))
}
gap_sets <- list(list(par = "inc_ben", typ = "inc_ben_type", dums = sprintf("inc_ben%02d", 1:6)),
                 list(par = "soc_mem", typ = "soc_mem_type", dums = sprintf("soc_mem%02d", c(1, 2, 4, 6, 8, 9, 10))))
for (g in gap_sets) {
  par <- all[[g$par]]; typ <- all[[g$typ]]
  sel <- spvn & !is.na(par) & par == 1 & is.na(typ)
  if (!any(sel)) next
  tt <- typ; tt[sel & is_tagged_na(typ) & na_tag(typ) %in% "c"] <- tagged_na("d")
  all[[g$typ]] <- tt
  for (dmt in g$dums) {
    x <- all[[dmt]]
    dsel <- sel & !is.na(x) & x == 0      # the -3/-4 codes are already .a/.d via the value map; this is the sysmis residual
    if (any(dsel)) { x[dsel] <- tagged_na("d"); all[[dmt]] <- x }
  }
  logmsg("spvn_applicable_gaps: %s==1 with %s missing: %d person(s), dummies retagged", g$par, g$typ, sum(sel))
}
# (c) Unknown receipt/membership (parent .a) cannot establish non-receipt of any type: the zeros the wildcard wrote
#     into the type dummies become .a.  The type variable stays .c (the type question was never reached).
#     Audit of v0.5.5, 25 Nov 2026 (decisions s. 35).
for (g in gap_sets) {
  par <- all[[g$par]]
  sel_a <- spvn & is.na(par) & is_tagged_na(par) & na_tag(par) %in% "a"
  if (!any(sel_a)) next
  n_cells <- 0L
  for (dmt in g$dums) {
    x <- all[[dmt]]
    dsel <- sel_a & !is.na(x) & x == 0
    if (any(dsel)) { x[dsel] <- tagged_na("a"); all[[dmt]] <- x; n_cells <- n_cells + sum(dsel) }
  }
  logmsg("spvn_applicable_gaps: %s==.a: %d person(s), %d dummy zeros -> .a", g$par, sum(sel_a), n_cells)
}

saveRDS(all, P("data", "interim", "derived_all.rds"))
writeLines(LOG, P("data", "interim", "log_03_derive.txt"))
logmsg("Derived variables added: %d rows x %d columns", nrow(all), ncol(all))
