# 99_checks.R : consistency checks on the built files; writes docs/run_log.md (checks + step logs).
# Fails (stop) on structural errors; prints warnings for anything to look at.
source(file.path(Sys.getenv("IMPD_ROOT", unset = getwd()), "code", "R", "00_setup.R"))

out_base <- P("data", "derived", sprintf("impd_public_v%s", gsub("\\.", "_", IMPD_VERSION)))
d <- readRDS(paste0(out_base, ".rds"))
vm <- VARMAP %>% filter(include_main == 1)
res <- character(0); ok <- function(cond, msg, ...) { m <- sprintf(msg, ...); res <<- c(res, sprintf("%s %s", if (cond) "PASS" else "FAIL", m)); if (!cond) warning(m, call. = FALSE); invisible(cond) }
val <- function(v) as.vector(unclass(d[[v]]))

# 1. structure
base_file <- function(i) P("data", "interim", paste0(str_to_lower(INCLUDED$svy_name[i]), if (INCLUDED$structure[i] == "flat") "_main.rds" else "_ro.rds"))
ok(nrow(d) == sum(map_int(seq_len(nrow(INCLUDED)), ~ nrow(readRDS(base_file(.x))))), "row count equals the sum of roster/person rows (%d)", nrow(d))
ok(!anyDuplicated(val("id_person")), "id_person is unique")
ok(all(sort(names(d)) == sort(vm$target)), "variable set equals variable_map (include_main = 1): %d variables", ncol(d))
for (i in seq_len(nrow(INCLUDED))) {
  key <- str_to_lower(INCLUDED$svy_name[i]); sid <- INCLUDED$svy_id[i]
  rt <- val("svy_resptype")[val("svy_id") == sid]
  if (INCLUDED$structure[i] == "flat") {
    nm <- nrow(readRDS(P("data", "interim", paste0(key, "_main.rds"))))
    ok(all(rt == 4) && length(rt) == nm, "%s: %d individually sampled respondents (file %d), all svy_resptype = 4", INCLUDED$svy_name[i], length(rt), nm)
    ok(all(is_tagged_na(d$id_hh[val("svy_id") == sid], "e")), "%s: id_hh is .e (no household identifier in a person sample)", INCLUDED$svy_name[i])
  } else {
    nh <- nrow(readRDS(P("data", "interim", paste0(key, "_hh.rds")))); np <- nrow(readRDS(P("data", "interim", paste0(key, "_pp.rds"))))
    ok(sum(rt == 1) == nh && sum(rt <= 2) == np, "%s: heads = %d (file %d), interviewed = %d (file %d)", INCLUDED$svy_name[i], sum(rt == 1), nh, sum(rt <= 2), np)
  }
}
# 2. every categorical value is labelled; ranges of numeric variables
bad <- character(0)
for (i in seq_len(nrow(vm))) {
  r <- vm[i, ]; x <- d[[r$target]]
  if (r$valueset != "") { codes <- VALUESETS$code[VALUESETS$valueset == r$valueset]; v <- val(r$target); u <- unique(v[!is.na(v)]); if (any(!(u %in% codes))) bad <- c(bad, sprintf("%s: %s", r$target, paste(setdiff(u, codes), collapse = ","))) }
  if (r$type == "year") { v <- val(r$target); if (any(v < 1890 | v > 2021, na.rm = TRUE)) bad <- c(bad, sprintf("%s: year out of range", r$target)) }
}
ok(length(bad) == 0, "all categorical values are in their value set and years are in range%s", if (length(bad)) paste0(": ", paste(bad, collapse = "; ")) else "")
ok(all(val("dem_age") >= 0 & val("dem_age") <= 105, na.rm = TRUE), "dem_age within 0-105")
# 2b. every numeric variable carries value labels: valueset codes + the five missing tags
bad <- character(0)
for (i in seq_len(nrow(vm))) {
  r <- vm[i, ]; if (r$type == "str") next
  labs <- attr(d[[r$target]], "labels")
  need <- if (r$valueset != "") sum(VALUESETS$valueset == r$valueset) + 5 else 5
  if (is.null(labs) || length(labs) < need) bad <- c(bad, r$target)
}
ok(length(bad) == 0, "every numeric variable carries its value labels (codes + missing tags)%s", if (length(bad)) paste0(": ", paste(bad, collapse = ", ")) else "")
# 3. not-collected logic: head-only items are .e for non-heads and never .e for heads of a survey that has the item
bad <- character(0)
for (i in seq_len(nrow(vm))) {
  r <- vm[i, ]; if (r$type == "str" || r$scope == "household" || r$derive != "") next
  for (s in KEYS) {
    sid <- INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == s]; rows <- val("svy_id") == sid
    e <- is_tagged_na(d[[r$target]], "e") & rows
    if (r[[paste0("src_", s)]] == "") { if (!all(e[rows])) bad <- c(bad, sprintf("%s/%s not all .e", r$target, s)); next }
    f <- r[[paste0("files_", s)]]
    if (f == "main") { if (any(e[rows])) bad <- c(bad, sprintf("%s/%s: .e in a flat survey that has the item", r$target, s)); next }
    heads <- rows & val("svy_resptype") == 1; members <- rows & val("svy_resptype") == 2
    at <- ASKED_TO$asked_to[ASKED_TO$target == r$target & ASKED_TO$survey == s]
    if (length(at) && at == "members") { if (!all(e[heads])) bad <- c(bad, sprintf("%s/%s: mini-questionnaire item not .e for heads", r$target, s)) }
    else if (any(e[heads])) bad <- c(bad, sprintf("%s/%s: .e among heads", r$target, s))
    if (length(at) && at == "heads" && !all(e[members])) bad <- c(bad, sprintf("%s/%s: main-questionnaire-only item not .e for members", r$target, s))
    if (f == "hh" && !all(e[rows & val("svy_resptype") >= 2])) bad <- c(bad, sprintf("%s/%s: head-only item not .e for members", r$target, s))
  }
}
ok(length(bad) == 0, "not-collected (.e) assignment consistent%s", if (length(bad)) paste0(": ", paste(head(bad, 10), collapse = "; ")) else "")
# 4. household-scope variables constant within household
hhv <- vm$target[vm$scope == "household"]
hh_rows <- !is.na(val("id_hh"))
cst <- map_lgl(hhv, ~ { x <- val(.x)[hh_rows]; all(tapply(x, val("id_hh")[hh_rows], function(z) length(unique(z[!is.na(z)])) <= 1)) })
ok(all(cst), "household-scope variables are constant within households (%s)", paste(hhv, collapse = ", "))
# 5. CPI
for (t in vm$target[str_starts(vm$derive, "cpi2015:")]) {
  spec <- sub("cpi2015:", "", vm$derive[vm$target == t]); base <- sub("@.*$", "", spec)
  yr <- if (grepl("@", spec, fixed = TRUE)) as.integer(sub("^.*@", "", spec)) else val("svy_year")
  f <- 100 / CPI$cpi_2015[match(yr, CPI$year)]
  stopifnot(!is.null(d[[base]]))
  ok(all(abs(val(t) - val(base) * f) < 1e-6, na.rm = TRUE) && all(is.na(val(t)) == is.na(val(base))), "%s = %s x CPI factor", t, spec)
}
# 6. independent recount of exact value-map rows from the source frames
src <- map(seq_len(nrow(INCLUDED)), ~ readRDS(P("data", "interim", paste0("source_", str_to_lower(INCLUDED$svy_name[.x]), ".rds")))); names(src) <- str_to_lower(INCLUDED$svy_name)
hh_files <- map(seq_len(nrow(INCLUDED)), ~ if (INCLUDED$structure[.x] == "flat") NULL else readRDS(P("data", "interim", paste0(str_to_lower(INCLUDED$svy_name[.x]), "_hh.rds")))); names(hh_files) <- names(src)
flat_keys <- str_to_lower(INCLUDED$svy_name[INCLUDED$structure == "flat"])
mism <- character(0); nchecked <- 0
for (t in unique(VALUEMAP$target)) {
  r <- vm[vm$target == t, ]; if (!nrow(r)) next
  for (s in unique(VALUEMAP$survey[VALUEMAP$target == t])) {
    maps <- VALUEMAP %>% filter(target == t, survey == s)
    if (any(maps$source_value == "*") || any(grepl("-", maps$source_value)) || any(grepl("^'", maps$source_value))) next   # only exact numeric maps are recounted
    if (grepl("|", r[[paste0("src_", s)]], fixed = TRUE)) next                                   # multi-source feeds: combination, not a 1:1 recount
    sid <- INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == s]; rows <- val("svy_id") == sid
    sv <- maps$source_var[1]
    if (r$scope == "household" && !(s %in% flat_keys)) { hh <- hh_files[[s]]; xs <- as.numeric(hh[[sv]][match(src[[s]]$HHNUMMER, hh$HHNUMMER)]) } else xs <- suppressWarnings(as.numeric(src[[s]][[sv]]))
    dv <- str_remove(r$derive, "\\|?partner_copy:[a-z0-9_]+")             # partner copies only fill .e cells of the household surveys
    if (dv != "" && !dv %in% c("fill0_interviewed", "kl9_route", "rel_none", "has_prtnr_roster", "prtnr_cores_roster")) next
    if (dv == "kl9_route" || (s == "sim2020" && t == "rel_den_det") || (s %in% flat_keys && t %in% c("rel_den_det", "rel_den_cat"))) next
    # persons not asked are .e in the target; restrict the source count to persons who could answer
    f <- r[[paste0("files_", s)]]; rt <- src[[s]]$svy_resptype
    asked <- if (r$scope == "household" || grepl("ro|main", f)) rep(TRUE, length(xs)) else if (grepl("pp", f)) rt <= 2 else rt == 1
    for (tv in unique(maps$target_value[!grepl("^\\.", maps$target_value)])) {
      scodes <- as.numeric(maps$source_value[maps$target_value == tv])
      n_src <- sum(xs[asked] %in% scodes)
      # target code may also arise from passthrough of the same code value: add source rows equal to tv not consumed by the map
      mc <- missing_codes(s, sv)$code
      pass <- sum(xs[asked] == as.numeric(tv) & !(xs[asked] %in% as.numeric(maps$source_value)) & !(xs[asked] %in% mc), na.rm = TRUE)
      y <- val(t)[rows]; n_tgt <- sum(y == as.numeric(tv) & (!grepl("partner_copy:", r$derive) | !is.na(xs)), na.rm = TRUE)   # partner copies fill cells without a source value
      nchecked <- nchecked + 1
      if (n_src + pass != n_tgt) mism <- c(mism, sprintf("%s/%s code %s: source %d vs harmonized %d", t, s, tv, n_src + pass, n_tgt))
    }
  }
}
ok(length(mism) == 0, "independent recount of %d exact value-map cells matches%s", nchecked, if (length(mism)) paste0(": ", paste(head(mism, 12), collapse = "; ")) else "")

# 7. stated universes vs the data (reported, not fatal): native reference samples of the flat surveys, SIM 2020 split half,
#    head-only items of the household surveys
tagv <- function(x) ifelse(is.na(x), ifelse(is_tagged_na(x), na_tag(x), "."), "v")
uni_issues <- character(0)
for (i in seq_len(nrow(vm))) {
  t <- vm$target[i]; if (vm$type[i] == "str") next
  x <- d[[t]]
  for (k in flat_keys) {
    sid <- INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == k]
    if (vm[[paste0("src_", k)]][i] == "") next
    u <- UNIVERSES$universe[UNIVERSES$target == t & UNIVERSES$survey == k]
    if (!length(u)) {                       # no survey-specific text: take the segment of the composed universe that names this survey (or a generic one)
      segs <- str_split(vm$universe_en[i], ";\\s+(?=[A-Z])")[[1]]
      u <- c(segs[grepl(INCLUDED$label[INCLUDED$svy_id == sid], segs, fixed = TRUE)], segs[!grepl("\\((SPVA|SPVN|LAS|SIM|SING)", segs)])[1]
      if (is.na(u)) next
    }
    rows <- val("svy_id") == sid; nat <- rows & val("dem_eth") == 90
    # self-reported natives (dem_eth 90) who received the migrant routing of the script (svy_routing_mig = 1; the script
    # routes on the sample-frame group, which is not delivered) may carry values in migrant-only items; natives with the
    # native routing may not - no tolerance.  Counts per survey are printed in the run log (03_derive).
    nat_ok <- nat & val("svy_routing_mig") %in% 1
    n_nat <- sum(tagv(x[nat & !nat_ok]) == "v"); n_all <- sum(tagv(x[rows]) == "v")
    if (n_nat > 0 && grepl("migration background", u) && !grepl("native|all respondents|natives|Muslim|religious|group itself", u, ignore.case = TRUE))
      uni_issues <- c(uni_issues, sprintf("%s/%s: universe '%s' but %d natives with native routing have values", t, k, str_trunc(u, 60), n_nat))
    if (n_nat == 0 && n_all > 0 && grepl("^All respondents", u) && !grepl("natives|derived|registry|group itself", u, ignore.case = TRUE))
      uni_issues <- c(uni_issues, sprintf("%s/%s: universe '%s' but the native reference sample has no values", t, k, str_trunc(u, 60)))
    if (k == "sim2020") {
      nA <- sum(tagv(x[rows & val("svy_split") == 1]) == "v"); nB <- sum(tagv(x[rows & val("svy_split") == 2]) == "v")
      kind <- if (nA > 0 && nB == 0) "A" else if (nB > 0 && nA == 0) "B" else "both"
      says <- if (grepl("group A", u, ignore.case = TRUE)) "A" else if (grepl("group B", u, ignore.case = TRUE)) "B" else "both"
      if (kind != says) uni_issues <- c(uni_issues, sprintf("%s: split half %s in the data, universe says %s", t, kind, says))
    }
  }
  for (k in setdiff(KEYS, flat_keys)) {
    sid <- INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == k]
    uk <- UNIVERSES$universe[UNIVERSES$target == t & UNIVERSES$survey == k]          # the survey's own text, else the composed one
    if (!length(uk)) {
      segs <- str_split(vm$universe_en[i], ";\\s+(?=[A-Z])")[[1]]
      uk <- c(segs[grepl(INCLUDED$label[INCLUDED$svy_id == sid], segs, fixed = TRUE)], segs[!grepl("\\((SPVA|SPVN|LAS|SIM|SING)", segs)], vm$universe_en[i])[1]
    }
    if (vm[[paste0("src_", k)]][i] == "" || !grepl("^Heads of household", uk) || grepl("partner", uk)) next
    n <- sum(tagv(x[val("svy_id") == sid & val("svy_resptype") != 1]) == "v")
    if (n > 0) uni_issues <- c(uni_issues, sprintf("%s/%s: heads-only universe but %d non-head values", t, k, n))
  }
}
ok(length(uni_issues) == 0, "stated universes agree with the data (native sample, split half, head-only items)%s", if (length(uni_issues)) paste0(": ", paste(uni_issues, collapse = "; ")) else "")

# 8. multi-source feeds ('A|B'): exact, independent re-derivation.  Each source is recoded on its own from the value map
#    (exact numeric rows only), the survey's code/label/declared missing rules and passthrough; the per-source results are
#    then combined with the documented precedence (first source with a valid value wins; among tags the first non-.c wins;
#    otherwise .c) and compared cell by cell with the harmonized variable.  Rows where two sources carry different valid
#    values are reported as conflicts (informative) because the rule then takes the first source's value.
feed_issues <- character(0); feed_conf <- character(0); nfeeds <- 0; nfeed_cells <- 0
tagcode <- function(x) ifelse(is.na(x), ifelse(is_tagged_na(x), paste0(".", na_tag(x)), "."), as.character(x))
for (i in seq_len(nrow(vm))) {
  for (s in KEYS) {
    spec <- vm[[paste0("src_", s)]][i]
    if (!grepl("|", spec, fixed = TRUE) || vm$type[i] == "str") next
    nfeeds <- nfeeds + 1
    srcs <- str_split(spec, fixed("|"))[[1]]
    sid <- INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == s]; rows <- val("svy_id") == sid
    ys <- list(); exact <- TRUE
    for (sv in srcs) {
      xs <- suppressWarnings(as.numeric(src[[s]][[sv]]))
      mp <- VALUEMAP %>% filter(target == vm$target[i], survey == s, source_var == sv)
      if (any(mp$source_value == "*") || any(grepl("-", mp$source_value)) || any(grepl("^'", mp$source_value))) { exact <- FALSE; break }
      y <- rep(NA_character_, length(xs)); done <- rep(FALSE, length(xs))
      for (k in seq_len(nrow(mp))) {                                       # explicit map first (engine: consumed positions)
        sel <- !done & !is.na(xs) & xs == as.numeric(mp$source_value[k]); y[sel] <- mp$target_value[k]; done[sel] <- TRUE
      }
      mc <- missing_codes(s, sv)                                           # code / label / declared rules
      for (k in seq_len(nrow(mc))) { sel <- !done & !is.na(xs) & xs == mc$code[k]; y[sel] <- mc$target[k]; done[sel] <- TRUE }
      sel <- !done & !is.na(xs); y[sel] <- as.character(xs[sel]); done[sel] <- TRUE       # passthrough
      y[is.na(xs)] <- paste0(".", INCLUDED$sysmis_tag[INCLUDED$svy_id == sid])            # empty cell: survey system-missing tag
      ys[[sv]] <- y
    }
    if (!exact) next
    out <- ys[[1]]
    for (y in ys[-1]) {
      take <- grepl("^\\.", out) & !grepl("^\\.", y)
      take <- take | (out == ".c" & grepl("^\\.", y) & y != ".c")
      out[take] <- y[take]
    }
    # engine representation: plain '.' (system missing) appears only in household surveys; flat surveys tag it
    got <- tagcode(val(vm$target[i])[rows])
    got[got == "."] <- paste0(".", INCLUDED$sysmis_tag[INCLUDED$svy_id == sid])
    nfeed_cells <- nfeed_cells + length(out)
    n_bad <- sum(out != got)
    if (n_bad > 0) feed_issues <- c(feed_issues, sprintf("%s/%s: %d cells differ from the independent re-derivation", vm$target[i], s, n_bad))
    valid <- do.call(cbind, lapply(ys, function(y) !grepl("^\\.", y)))
    conf <- rowSums(valid) > 1 & apply(do.call(cbind, ys), 1, function(r) length(unique(r[!grepl("^\\.", r)])) > 1)
    if (any(conf)) feed_conf <- c(feed_conf, sprintf("%s/%s: %d rows with different valid values in two sources (first source kept)", vm$target[i], s, sum(conf)))
  }
}
ok(length(feed_issues) == 0, "multi-source feeds (%d; %s cells) re-derived independently with the documented precedence%s", nfeeds, format(nfeed_cells, big.mark = ","),
   if (length(feed_issues)) paste0(": ", paste(head(feed_issues, 10), collapse = "; ")) else "")
if (length(feed_conf)) message("  note: feed conflicts (two valid sources disagree): ", paste(feed_conf, collapse = "; "))
res <- c(res, sprintf("NOTE feed conflicts (two sources with different valid values; the first source is kept): %s", if (length(feed_conf)) paste(feed_conf, collapse = "; ") else "none"))

# 9. every string column is valid UTF-8 in every delivered format (.rds, .dta re-read with haven, .csv)
chr <- names(d)[sapply(d, is.character)]
bad_rds <- chr[sapply(chr, function(v) any(!is.na(d[[v]]) & !validUTF8(d[[v]])))]
dta <- haven::read_dta(paste0(out_base, ".dta"), col_select = all_of(chr))
bad_dta <- chr[sapply(chr, function(v) any(!is.na(dta[[v]]) & !validUTF8(dta[[v]])))]
csvd <- readr::read_csv(paste0(out_base, ".csv"), col_select = all_of(chr), col_types = readr::cols(.default = "c"), show_col_types = FALSE, progress = FALSE)
bad_csv <- chr[sapply(chr, function(v) any(!is.na(csvd[[v]]) & !validUTF8(csvd[[v]])))]
ok(length(c(bad_rds, bad_dta, bad_csv)) == 0, "all %d string variables are valid UTF-8 in .rds, .dta and .csv%s", length(chr),
   if (length(c(bad_rds, bad_dta, bad_csv))) paste0(": ", paste(unique(c(bad_rds, bad_dta, bad_csv)), collapse = ", ")) else "")

# 10. construct-specific universe: the 'highest diploma' family is defined for persons not in full-time education
#     (ISEO/SCP niet-schoolgaanden = edu_part 0), not for the non-enrolled; report values of full-time students per survey
dip <- vm$target[grepl("^edu_dipl_hi_", vm$target)]
ft <- val("edu_part") == 1 & !is.na(val("edu_part"))
dip_issues <- character(0)
for (t in dip) for (sn in levels(factor(val("svy_name")))) {
  n <- sum(!is.na(val(t)) & ft & val("svy_name") == sn)
  if (n > 0) dip_issues <- c(dip_issues, sprintf("%s/%s: %d full-time students with a value", t, sn, n))
}
res <- c(res, sprintf("NOTE highest-diploma universe (persons not in full-time education): %s", if (length(dip_issues)) paste(dip_issues, collapse = "; ") else "no full-time student has a value"))

# 11. routing gates vs the data: a spoken item may carry values only where its printed routing condition, mapped to a
#     harmonized gate variable (crosswalks/routing_rules.csv -> wording.csv routing_gates), is satisfied.  Evaluated per
#     source variable (routing_eval in 00_setup.R, recomputed here and compared with docs/routing_check.csv written by
#     04_build).  A gate with more than 10% of its values outside fails; smaller deviations are reported as exceptions.
RC <- routing_eval(d, out_base)
RC0 <- read_csv(P("docs", "routing_check.csv"), show_col_types = FALSE, col_types = cols(.default = "c"))
ok(nrow(RC) == nrow(RC0) && all(as.character(RC$n_outside) == RC0$n_outside) && all(RC$verdict == RC0$verdict),
   "routing-gate table recomputed from the released files equals docs/routing_check.csv (%d source x gate pairs)", nrow(RC))
bad <- RC %>% filter(verdict == "does not hold"); exc <- RC %>% filter(verdict == "holds with exceptions")
fmt_rc <- function(x) sprintf("%s/%s (%s): %d of %d values outside gate %s in {%s} [%s]", x$target, x$survey, x$source_var, x$n_outside, x$n_values, x$gate, x$allowed, x$outside_gate_values)
ok(nrow(bad) == 0, "routing gates hold in the data (%d of %d source x gate pairs without any value outside; %d with exceptions <= 10%%)%s",
   sum(RC$verdict == "holds"), nrow(RC), nrow(exc), if (nrow(bad)) paste0(": ", paste(head(fmt_rc(bad), 15), collapse = "; "), if (nrow(bad) > 15) sprintf(" ... (%d in total)", nrow(bad)) else "") else "")
if (nrow(exc)) res <- c(res, sprintf("NOTE routing-gate exceptions (values outside the printed condition, <= 10%%; data as delivered): %s", paste(fmt_rc(exc), collapse = "; ")))

# 12. relationship layer (household surveys): the link, the two indicators and the partner copies follow their rules exactly
#     (decisions 10.1 / 11.3): co-resident link -> has 1, cores 1; LAT partner without link -> has 1, cores 0; identifiable
#     head/partner without link or LAT -> has 0, cores .c; other members -> .d; a copied value equals the partner's own base
#     value, or .d where the base value is .e on the partner's row
tagv2 <- function(x) ifelse(is.na(x), ifelse(is_tagged_na(x), paste0(".", na_tag(x)), "."), as.character(as.numeric(x)))
hh <- !(d$svy_name %in% INCLUDED$svy_name[INCLUDED$structure == "flat"])
link <- match(as.numeric(d$id_prtnr), as.numeric(d$id_person)); haslink <- hh & !is.na(link)
hp <- hh & as.numeric(d$dem_poshh) %in% c(0, 1); lat <- hh & as.numeric(d$dem_prtnr_lat) %in% 1
exp_has <- ifelse(haslink, "1", ifelse(lat, "1", ifelse(hp, "0", ".d"))); exp_cor <- ifelse(haslink, "1", ifelse(lat, "0", ifelse(hp, ".c", ".d")))
rel_bad <- c(sprintf("dem_has_prtnr: %d", sum(hh & tagv2(d$dem_has_prtnr) != exp_has)), sprintf("dem_prtnr_cores: %d", sum(hh & tagv2(d$dem_prtnr_cores) != exp_cor)))
pc <- VARMAP %>% filter(str_detect(derive, "partner_copy:"), !target %in% c("dem_prtnr_age", "dem_prtnr_brthcntry", "dem_prtnr_age_cat"))   # targets with a head-reported source keep it
for (i in seq_len(nrow(pc))) {
  t <- pc$target[i]; b <- sub("^.*partner_copy:", "", pc$derive[i])
  got <- tagv2(d[[t]]); base <- tagv2(d[[b]][link]); base[base == ".e"] <- ".d"
  n <- sum(haslink & got != base); if (n) rel_bad <- c(rel_bad, sprintf("%s: %d copies differ from the partner's %s", t, n, b))
  n2 <- sum(hp & !haslink & !(got %in% c(".c"))); if (n2) rel_bad <- c(rel_bad, sprintf("%s: %d heads/partners without a link are not .c", t, n2))
}
ok(all(grepl(": 0$", rel_bad[1:2])) && length(rel_bad) == 2, "relationship layer follows its rules (has/cores indicators, %d partner copies vs the linked partner's base value)%s", nrow(pc),
   if (!(all(grepl(": 0$", rel_bad[1:2])) && length(rel_bad) == 2)) paste0(": ", paste(rel_bad, collapse = "; ")) else "")

# 13. asked-to table (household surveys): every item listed in crosswalks/asked_to.csv has values in the respondent type
#     that was asked and only .e in the other; and no other numeric person-scope item shows the same pattern (one
#     respondent type without any valid value but with plain missings) - such a case would be a missing asked_to row
at_bad <- character(0); at_resid <- character(0)
for (k in setdiff(KEYS, flat_keys)) {
  sid <- INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == k]; rows <- val("svy_id") == sid
  heads <- rows & val("svy_resptype") == 1; members <- rows & val("svy_resptype") == 2
  for (i in seq_len(nrow(vm))) {
    r <- vm[i, ]; if (r$type == "str" || r$scope == "household" || r[[paste0("src_", k)]] == "" || r$derive != "") next
    x <- d[[r$target]]; tg <- tagv(x)
    at <- ASKED_TO$asked_to[ASKED_TO$target == r$target & ASKED_TO$survey == k]
    nh <- sum(tg[heads] == "v"); nm <- sum(tg[members] == "v")
    if (length(at)) {
      asked <- if (at == "heads") heads else members; other <- if (at == "heads") members else heads
      if (sum(tg[asked] == "v") == 0) at_bad <- c(at_bad, sprintf("%s/%s: no valid value among %s", r$target, k, at))
      if (!all(tg[other] == "e")) at_bad <- c(at_bad, sprintf("%s/%s: %d records of the other type are not .e", r$target, k, sum(tg[other] != "e")))
    } else if ((nh == 0 && nm > 0 && any(tg[heads] == ".")) || (nm == 0 && nh > 0 && any(tg[members] == ".")))
      at_resid <- c(at_resid, sprintf("%s/%s (%s valid: heads %d, members %d)", r$target, k, if (nh == 0) "heads none" else "members none", nh, nm))
  }
}
ok(length(at_bad) == 0 && length(at_resid) == 0, "asked-to table (%d items in one respondent type's questionnaire only) holds, and no further item shows the pattern%s",
   nrow(ASKED_TO), if (length(c(at_bad, at_resid))) paste0(": ", paste(c(at_bad, at_resid), collapse = "; ")) else "")

# 14. split-half annotations (SIM 2020): the half printed with each respondent-facing source item in wording.csv (A, B or
#     both) must be the half that carries values in the released file - a marker printed before a grid does not govern
#     sub-items that both halves answered (MENTALGEZ: the MHI-5 items went to both halves, the three extras to B only)
WD <- read_cw("wording.csv") %>% filter(survey == "sim2020", respondent_facing == "1")
s20 <- d[val("svy_id") == INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == "sim2020"], ]; sp <- as.numeric(unclass(s20$svy_split))
sh_bad <- character(0); n_sh <- 0
for (i in seq_len(nrow(WD))) {
  t <- WD$target[i]; if (!t %in% names(s20)) next
  x <- s20[[t]]; valid <- if (is.character(x)) !is.na(x) & x != "" else !is.na(x)
  nA <- sum(valid & sp == 1, na.rm = TRUE); nB <- sum(valid & sp == 2, na.rm = TRUE)
  kind <- if (nA > 0 && nB == 0) "A" else if (nB > 0 && nA == 0) "B" else if (nA > 0 && nB > 0) "both" else next
  n_sh <- n_sh + 1; meta <- if (WD$split_half[i] == "") "both" else WD$split_half[i]
  if (kind != meta) sh_bad <- c(sh_bad, sprintf("%s (%s): annotated %s, values in %s (A %d, B %d)", t, WD$source_var[i], meta, kind, nA, nB))
}
ok(length(sh_bad) == 0, "SIM 2020 split-half annotations agree with the halves that carry values (%d source items)%s", n_sh, if (length(sh_bad)) paste0(": ", paste(sh_bad, collapse = "; ")) else "")

# 15. value-map grammar on synthetic input: exact codes, ranges with negative bounds on either side ("-9--1"), quoted
#     strings and the wildcard behave as documented in 00_setup.R (no current map uses a negative upper bound)
gx <- c(-10, -9, -5, -1, 0, 3, 7, NA)
gram <- list(c("-9--1", "-9,-5,-1"), c("-3-9", "-1,0,3,7"), c("1-5", "3"), c("-5", "-5"), c("*", "-10,-9,-5,-1,0,3,7"), c("0.5-7", "3,7"))
g_bad <- character(0)
for (g in gram) { got <- paste(gx[match_spec(gx, g[1])], collapse = ","); if (got != g[2]) g_bad <- c(g_bad, sprintf("%s -> {%s}, expected {%s}", g[1], got, g[2])) }
if (!identical(match_spec(c("H", " H ", "", NA), "'H'"), c(TRUE, TRUE, FALSE, FALSE)) || !identical(match_spec(c("H", "", NA), "''"), c(FALSE, TRUE, TRUE))) g_bad <- c(g_bad, "quoted string specs")
ok(length(g_bad) == 0, "value-map grammar (exact, ranges with negative bounds, quoted strings, wildcard) behaves as documented on synthetic input%s", if (length(g_bad)) paste0(": ", paste(g_bad, collapse = "; ")) else "")

# 16. value-map review (code/tools/value_map_review.py; from the restricted component, 4 Nov 2026): every value-map row is
#     read with its source label against the target label - two-valued targets whose source label is not a plain yes/no,
#     cross-survey copies of a row whose labels do not say the same, and overlapping range labels must be read and signed
#     in crosswalks/label_approvals.csv.  The crosswalk builder runs it as its last step; it is run again here on the
#     crosswalks as they are, so that a hand edit after the build is read too (skipped when python3 is not installed)
py <- find_python()
if (length(py)) {
  vmr <- suppressWarnings(system2(py[1], c(py[-1], "-I", shQuote(P("code", "tools", "value_map_review.py")), shQuote(P("crosswalks"))), stdout = TRUE, stderr = TRUE))
  vmr_rc <- attr(vmr, "status"); vmr_last <- if (length(vmr)) tail(vmr, 1) else "no output"
  ok(is.null(vmr_rc) || vmr_rc == 0, "value-map review (labels read against target labels; %d approvals in crosswalks/label_approvals.csv): %s",
     nrow(read_cw("label_approvals.csv")), sub("^(PASS|FAIL) value-map review: ", "", vmr_last))
} else res <- c(res, "SKIP value-map review: no working Python interpreter found - the crosswalk builder runs code/tools/value_map_review.py as its last step")

# 17. household-survey merge (SPVA/SPVN): the declared merge exceptions (crosswalks/merge_exceptions.csv) took effect - where
#     the more detailed file holds the system-missing code and a less detailed file a valid value, the delivered source
#     companion carries the valid value; undeclared cases of the same pattern are counted and reported (kept by decision 1)
mx_bad <- character(0); mx_rest <- character(0)
for (key in INCLUDED$svy_key[INCLUDED$structure == "hh_pp_ro"]) {
  s <- INCLUDED[INCLUDED$svy_key == key, ]; k <- tolower(s$svy_name)         # file key (spva2002, spvn2003); svy_key is the id prefix
  ro <- readRDS(P("data", "interim", paste0(k, "_ro.rds"))); pp <- readRDS(P("data", "interim", paste0(k, "_pp.rds")))
  comp <- readRDS(P("data", "derived", sprintf("impd_public_v%s_source_%s.rds", gsub("\\.", "_", IMPD_VERSION), k)))
  kk <- function(d) interaction(d$HHNUMMER, d$GEZLIDNR)
  m_pp <- match(kk(pp), kk(ro)); ex <- MERGE_EXC[MERGE_EXC$survey == k, ]
  id_pp <- (key * 1e9 + pp$HHNUMMER) * 100 + pp$GEZLIDNR                     # id_person of the household surveys (03_derive)
  for (v in setdiff(intersect(names(pp), names(ro)), c("HHNUMMER", "GEZLIDNR"))) {
    if (is.character(pp[[v]]) || !(paste0("src_", v) %in% names(comp))) next
    a <- pp[[v]]; b <- ro[[v]][m_pp]
    hit <- which(!is.na(a) & a < 0 & !is.na(b) & b >= 0)                    # detailed file: a missing code; roster: a valid value
    if (!length(hit)) next
    if (v %in% ex$source_var) {
      code <- as.numeric(ex$sysmis_code[ex$source_var == v][1])
      got <- as.numeric(unclass(comp[[paste0("src_", v)]][match(id_pp[hit], as.numeric(comp$id_person))])); want <- ifelse(a[hit] == code, b[hit], a[hit])
      if (!isTRUE(all.equal(got, want))) mx_bad <- c(mx_bad, sprintf("%s %s", s$svy_name, v))
    } else mx_rest <- c(mx_rest, sprintf("%s %s (%d)", s$svy_name, v, length(hit)))
  }
}
ok(length(mx_bad) == 0, "household-survey merge: %d declared exception(s) in crosswalks/merge_exceptions.csv took effect in the source companions%s; undeclared missing-code-over-valid cells kept by decision: %s",
   nrow(MERGE_EXC), if (length(mx_bad)) paste0(" - NOT for ", paste(mx_bad, collapse = ", ")) else "", if (length(mx_rest)) paste(mx_rest, collapse = ", ") else "none")

# ---- run log --------------------------------------------------------------------------------
logs <- map(c("log_02_harmonize.txt", "log_03_derive.txt", "log_04_build.txt"), ~ if (file.exists(P("data", "interim", .x))) readLines(P("data", "interim", .x)) else character(0))
pkgs <- IMPD_PACKAGES
env <- paste(sprintf("%s %s", pkgs, sapply(pkgs, function(p) as.character(packageVersion(p)))), collapse = ", ")
hashes <- paste(sprintf("%s %s", INCLUDED$svy_name, substr(INCLUDED$zip_sha256, 1, 12)), collapse = ", ")
writeLines(sprintf("%s v%s %s", BUILD_ID, IMPD_VERSION, format(Sys.time(), "%Y-%m-%d %H:%M %Z")), P("docs", "BUILD_ID"))
run <- c(sprintf("# IMPD public component v%s — run log (build %s)", IMPD_VERSION, BUILD_ID),
         sprintf("\nBuilt %s with R %s (%s) on %s; packages: %s.\n", format(Sys.time(), "%Y-%m-%d %H:%M"), getRversion(), R.version$platform, Sys.info()[["sysname"]], env),
         sprintf("Deposit zip files (sha256, first 12 hex digits; full hashes of zips and data files in crosswalks/surveys.csv): %s.\n", hashes),
         "## Checks\n", paste0("- ", res), "\n## Step logs\n", paste0("- ", unlist(logs)))
writeLines(run, P("docs", "run_log.md"))
cat(paste(res, collapse = "\n"), "\n")
if (any(grepl("^FAIL", res))) stop("checks failed - see docs/run_log.md")
