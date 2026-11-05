# 02_harmonize.R : build one person-level frame per survey, apply the crosswalk
# (variable_map / value_map / missing_rules / valuesets), stack the surveys.
#
# Person frame construction depends on the survey structure (crosswalks/surveys.csv, column structure):
#   hh_pp_ro (SPVA/SPVN household samples)
#     * rows   = all household members in the roster file (ro)
#     * values = coalesce(heads file, interviewed-persons file, roster file) for every source variable,
#                i.e. the most detailed/self-reported source wins (hh > pp > ro)
#     * household-scope targets are taken from the head's record and merged onto every member
#     * svy_resptype = 1 head (in hh file), 2 interviewed member (in pp, not hh), 3 roster only
#   flat (SIM person samples)
#     * rows = the single person file; svy_resptype = 4; household-scope targets are the respondent's own values
#   * .e (not collected) is set for persons whose questionnaire did not contain the item: from file membership (an item
#     of the heads file is .e for other members, an item of the persons file is .e for roster-only rows) and from
#     crosswalks/asked_to.csv (items the persons file holds for both types but only one type was asked)
#   * multi-source feeds ('A|B' in variable_map): each source is recoded with its own value_map rows and missing
#     rules, then combined: a valid value wins over any tag, among tags the first that is not .c wins, else .c
source(file.path(Sys.getenv("IMPD_ROOT", unset = getwd()), "code", "R", "00_setup.R"))

KEYS_HH <- c("HHNUMMER", "GEZLIDNR")

build_person_frame <- function(key) {
  ro <- readRDS(P("data", "interim", paste0(key, "_ro.rds")))
  pp <- readRDS(P("data", "interim", paste0(key, "_pp.rds")))
  hh <- readRDS(P("data", "interim", paste0(key, "_hh.rds")))
  stopifnot(!anyDuplicated(ro[KEYS_HH]), !anyDuplicated(pp[KEYS_HH]), !anyDuplicated(hh[KEYS_HH]))
  per <- ro[KEYS_HH]
  per$svy_resptype <- ifelse(interaction(per$HHNUMMER, per$GEZLIDNR) %in% interaction(hh$HHNUMMER, hh$GEZLIDNR), 1L,
                      ifelse(interaction(per$HHNUMMER, per$GEZLIDNR) %in% interaction(pp$HHNUMMER, pp$GEZLIDNR), 2L, 3L))
  allvars <- setdiff(union(union(names(hh), names(pp)), names(ro)), KEYS_HH)
  j <- function(d) { idx <- match(interaction(per$HHNUMMER, per$GEZLIDNR), interaction(d$HHNUMMER, d$GEZLIDNR)); idx }
  ih <- j(hh); ip <- j(pp); ir <- j(ro)
  mx <- MERGE_EXC %>% filter(survey == key, rule == "valid_over_sysmis")   # declared: a file's system-missing code yields to a less detailed file
  for (v in allvars) {
    pick <- function(d, idx) if (v %in% names(d)) d[[v]][idx] else rep(NA, nrow(per))
    x <- pick(hh, ih); y <- pick(pp, ip); z <- pick(ro, ir)
    if (v %in% mx$source_var) { code <- as.numeric(mx$sysmis_code[mx$source_var == v][1]); x[!is.na(x) & x == code] <- NA; y[!is.na(y) & y == code] <- NA }
    if (is.character(x) || is.character(y) || is.character(z)) {
      x <- as.character(x); y <- as.character(y); z <- as.character(z)
      out <- coalesce(x, y, z); out <- str_trim(out); out[out == ""] <- NA_character_
    } else {
      out <- coalesce(as.numeric(x), as.numeric(y), as.numeric(z))
    }
    per[[v]] <- out
  }
  # head-reported vs self-reported conflicts (documentation only)
  conf <- character(0)
  for (v in intersect(names(pp), names(ro))) {
    if (v %in% KEYS_HH || is.character(pp[[v]])) next
    m <- match(interaction(pp$HHNUMMER, pp$GEZLIDNR), interaction(ro$HHNUMMER, ro$GEZLIDNR))
    a <- pp[[v]]; b <- ro[[v]][m]
    n <- sum(a != b & !is.na(a) & !is.na(b) & a >= 0 & b >= 0)
    if (n > 0) conf <- c(conf, sprintf("%s (%d)", v, n))
  }
  if (length(conf)) logmsg("%s: self-reported (pp) value preferred over roster value for %s persons: %s", key, "", paste(conf, collapse = ", "))
  list(per = per, hh = hh)
}

build_flat_frame <- function(key, id_var) {
  per <- readRDS(P("data", "interim", paste0(key, "_main.rds")))
  stopifnot(id_var %in% names(per), !anyDuplicated(per[[id_var]]))
  per$PERSNR <- as.numeric(per[[id_var]])
  per$HHNUMMER <- NA_real_; per$GEZLIDNR <- NA_real_
  per$svy_resptype <- 4L
  for (v in names(per)) if (is.character(per[[v]])) { per[[v]] <- str_trim(per[[v]]) }   # keep '' (mapped as such)
  list(per = per, hh = NULL)
}

not_asked <- function(files, scope, resptype) {
  if (scope == "household") return(rep(FALSE, length(resptype)))
  f <- str_split(files, ",")[[1]]
  if ("ro" %in% f || "main" %in% f) return(rep(FALSE, length(resptype)))
  if ("pp" %in% f) return(resptype == 3)
  resptype >= 2
}

# combine the harmonized vectors of a multi-source feed (see header)
coalesce_feed <- function(ys) {
  if (length(ys) == 1) return(ys[[1]])
  out <- ys[[1]]
  for (y in ys[-1]) {
    take <- is.na(out) & !is.na(y)                                   # valid value beats any tag
    take <- take | (is.na(out) & is.na(y) & is_tagged_na(out, "c") & !is_tagged_na(y, "c"))   # .a/.b/.d beat .c
    out[take] <- y[take]
  }
  out
}

harmonize_survey <- function(s) {
  key <- str_to_lower(s$svy_name)
  flat <- s$structure == "flat"
  pf <- if (flat) build_flat_frame(key, s$id_var) else build_person_frame(key)
  per <- pf$per; hh <- pf$hh
  n <- nrow(per)
  out <- tibble(.rows = n)
  hh_idx <- if (flat) NULL else match(per$HHNUMMER, hh$HHNUMMER)        # head's record for every member
  srccol <- paste0("src_", key); filecol <- paste0("files_", key)
  unmapped <- character(0)
  for (i in seq_len(nrow(VARMAP))) {
    r <- VARMAP[i, ]
    if (r$include_main != 1 || is_create_derive(r$derive)) next
    src <- r[[srccol]]
    srcs <- str_split(src, fixed("|"))[[1]]; srcs <- srcs[srcs != ""]
    if (r$type == "str") {
      y <- if (src == "") rep(NA_character_, n) else if (length(srcs) == 1) as.character(per[[src]]) else
           coalesce(!!!map(srcs, ~ { v <- as.character(per[[.x]]); v[!is.na(v) & v == ""] <- NA_character_; v }))
      out[[r$target]] <- label_num(y, r$label_en)
      next
    }
    if (src == "") {                                   # variable not collected in this survey
      y <- rep(tagged_na("e"), n)
    } else {
      ys <- map(srcs, function(sv) {
        x <- if (r$scope == "household" && !flat) hh[[sv]][hh_idx] else per[[sv]]
        maps <- VALUEMAP %>% filter(target == r$target, survey == key, source_var == sv)
        if (!is.character(x)) x <- as.numeric(x)
        vm <- apply_value_map(x, maps)
        apply_missing(x, vm$y, vm$consumed, key, sv)
      })
      y <- coalesce_feed(ys)
      y[not_asked(r[[filecol]], r$scope, per$svy_resptype)] <- tagged_na("e")
      at <- ASKED_TO[ASKED_TO$target == r$target & ASKED_TO$survey == key, ]     # item in one respondent type's questionnaire only
      if (nrow(at) && !flat) {
        excl <- per$svy_resptype == if (at$asked_to[1] == "heads") 2L else 1L
        if (any(!is.na(y[excl]))) stop(sprintf("%s/%s: asked_to = %s, but %d valid values in the other respondent type", r$target, key, at$asked_to[1], sum(!is.na(y[excl]))))
        y[excl] <- tagged_na("e")
      }
      if (r$valueset != "") {                          # report codes that end up unlabelled
        vsl <- VALUESETS %>% filter(valueset == r$valueset)
        bad <- unique(y[!is.na(y) & !(y %in% vsl$code)])
        if (length(bad)) unmapped <- c(unmapped, sprintf("%s[%s]: %s", r$target, src, paste(bad, collapse = ",")))
      }
    }
    out[[r$target]] <- if (r$valueset != "") label_var(y, r$valueset, r$label_en) else label_num(y, r$label_en)
  }
  if (length(unmapped)) logmsg("%s: codes without label: %s", key, paste(unmapped, collapse = "; "))
  out$svy_id <- s$svy_id; out$svy_name <- s$svy_name; out$svy_year <- s$svy_year
  out$svy_resptype <- per$svy_resptype
  out$HHNUMMER <- per$HHNUMMER; out$GEZLIDNR <- per$GEZLIDNR
  out$PERSNR <- if (flat) per$PERSNR else NA_real_
  if (flat) {
    logmsg("%s harmonized: %d persons (individual sample), %d variables", s$svy_name, n, ncol(out))
  } else {
    logmsg("%s harmonized: %d persons (%d heads, %d other interviewed, %d roster only), %d variables", s$svy_name, n,
           sum(per$svy_resptype == 1), sum(per$svy_resptype == 2), sum(per$svy_resptype == 3), ncol(out))
  }
  saveRDS(per, P("data", "interim", paste0("source_", key, ".rds")))
  out
}

harm <- map(seq_len(nrow(INCLUDED)), ~ harmonize_survey(INCLUDED[.x, ]))
# stacking: labelled columns must share labels -> bind on plain values, re-label afterwards in 04_build
strip <- function(d) { for (v in names(d)) { a <- attributes(d[[v]]); d[[v]] <- as.vector(unclass(d[[v]])); attributes(d[[v]]) <- NULL }; d }
all <- bind_rows(map(harm, strip))
saveRDS(all, P("data", "interim", "harmonized_all.rds"))
writeLines(LOG, P("data", "interim", "log_02_harmonize.txt"))
logmsg("Stacked: %d rows x %d columns", nrow(all), ncol(all))
