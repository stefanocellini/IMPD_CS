# IMPD-CS — Integrated Migrant Panel Dataset, cross-sectional component (harmonized DANS deposits)
# 00_setup.R : paths, packages, helper functions shared by all steps.
#
# Run the whole pipeline from the IMPD root with:   Rscript code/R/run_all.R
# or set IMPD_ROOT to the folder that contains Surveys/, External/, crosswalks/.

# packages: the six loaded here, openssl (build identity, 00_setup) and jsonlite (variable finder of the HTML codebook, 05);
# all eight are checked up front so that a missing one stops the run before any step starts
IMPD_PACKAGES <- c("haven", "dplyr", "readr", "stringr", "tidyr", "purrr", "openssl", "jsonlite")
missing_pkgs <- IMPD_PACKAGES[!vapply(IMPD_PACKAGES, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_pkgs)) stop("install the missing R package(s) first: ", paste(missing_pkgs, collapse = ", "), "  (install.packages(c(", paste(sprintf('"%s"', missing_pkgs), collapse = ", "), ")))")
suppressPackageStartupMessages({
  library(haven); library(dplyr); library(readr); library(stringr); library(tidyr); library(purrr)
})
options(dplyr.summarise.inform = FALSE, warn = 1)
# the crosswalks and labels are UTF-8; a C/POSIX locale (Rscript without LANG) makes string functions fail on non-ASCII text
if (!isTRUE(l10n_info()[["UTF-8"]])) invisible(suppressWarnings(Sys.setlocale("LC_CTYPE", if (.Platform$OS.type == "windows") "English_United States.utf8" else "C.UTF-8")))

ROOT <- Sys.getenv("IMPD_ROOT", unset = getwd())
P <- function(...) file.path(ROOT, ...)
dir.create(P("data", "raw"), showWarnings = FALSE, recursive = TRUE)
dir.create(P("data", "interim"), showWarnings = FALSE, recursive = TRUE)
dir.create(P("data", "derived"), showWarnings = FALSE, recursive = TRUE)
dir.create(P("docs"), showWarnings = FALSE, recursive = TRUE)

IMPD_VERSION <- "0.5.1"
LOG <- character(0)
logmsg <- function(...) { m <- sprintf(...); message(m); LOG <<- c(LOG, m); invisible(m) }

# ---- crosswalks ----------------------------------------------------------------
read_cw <- function(name, ...) read_csv(P("crosswalks", name), show_col_types = FALSE, col_types = cols(.default = "c"), na = character(), ...)
SURVEYS   <- read_cw("surveys.csv") %>% mutate(svy_id = as.integer(svy_id), svy_year = as.integer(svy_year), svy_key = as.numeric(svy_key))
VARMAP    <- read_cw("variable_map.csv") %>% mutate(include_main = as.integer(include_main))
VALUESETS <- read_cw("valuesets.csv") %>% mutate(code = as.numeric(code))
VALUEMAP  <- read_cw("value_map.csv")
MISSRULES <- read_cw("missing_rules.csv")
SRCLABELS <- read_cw("source_labels.csv") %>% mutate(code = suppressWarnings(as.numeric(code)))   # string-coded labels (SIM registry vars) -> NA, handled by value_map
SRCMISS   <- read_cw("source_missing.csv") %>% mutate(lo = as.numeric(lo), hi = as.numeric(hi))
MUNIS     <- read_cw("municipalities.csv") %>% mutate(source_code = as.numeric(source_code))
UNIVERSES <- read_cw("universes.csv")
ASKED_TO  <- read_cw("asked_to.csv")       # household surveys: respondent type whose questionnaire contained the item
MERGE_EXC <- read_cw("merge_exceptions.csv") # household surveys: declared merge exceptions (02_harmonize, check 17)
# a Python interpreter that actually runs (Windows installs a Store alias named python3 that cannot be launched): the first
# candidate whose --version succeeds, as c(executable, extra args), or character(0) when none does (callers skip and say so)
find_python <- function() {
  for (cand in list("python3", "python", c("py", "-3"))) {
    exe <- Sys.which(cand[1]); if (!nzchar(exe)) next
    out <- tryCatch(suppressWarnings(system2(exe, c(cand[-1], "--version"), stdout = TRUE, stderr = TRUE)), error = function(e) NULL)
    if (!is.null(out) && (is.null(attr(out, "status")) || attr(out, "status") == 0) && any(grepl("^Python 3", out))) return(c(unname(exe), cand[-1]))
  }
  character(0)
}
WORDING   <- read_cw("wording.csv")
WORDNOTES <- read_cw("wording_notes.csv")
QDESIGN   <- read_cw("questionnaire_design.csv")
CPI       <- read_cw("cpi.csv") %>% mutate(year = as.integer(year), cpi_2015 = as.numeric(cpi_2015))
INCLUDED  <- SURVEYS %>% filter(status == "included")
KEYS      <- str_to_lower(INCLUDED$svy_name)
# derive rules that CREATE a target (02_harmonize skips them); all other derive rules post-process a harmonized target in 03_derive
CREATE_DERIVES <- c("id_person", "id_hh", "svy_id", "svy_name", "svy_year", "svy_resptype", "municipality", "municipality_name")
is_create_derive <- function(d) d %in% CREATE_DERIVES | str_starts(d, "cpi2015:")
survey_levels <- function(s) if (s$structure == "flat") "main" else c("ro", "pp", "hh")

# ---- tagged missing values -----------------------------------------------------
# .a don't know | .b refusal | .c not applicable | .d no information | .e not collected for this respondent/survey
MISS_TAGS <- c(a = "Don't know", b = "Refusal", c = "Not applicable", d = "No information", e = "Not collected (survey/questionnaire)")
tag_na <- function(t) if (t == ".") NA_real_ else tagged_na(sub("^\\.", "", t))
miss_labels <- function() setNames(map_dbl(names(MISS_TAGS), tagged_na), MISS_TAGS)

# ---- value maps ----------------------------------------------------------------
# A source_value spec is a number, a range "lo-hi" (either bound may be negative: "-9--1", "-3-9"), a quoted string 'H' for string
# sources ('' = empty string), or "*" (any other non-missing value).
match_spec <- function(x, spec) {
  if (grepl("^'.*'$", spec)) {
    v <- substr(spec, 2, nchar(spec) - 1); xs <- str_trim(as.character(x)); xs[is.na(xs)] <- ""
    return(xs == v)
  }
  if (is.character(x)) x <- suppressWarnings(as.numeric(x))
  if (spec == "*") return(!is.na(x))
  if (grepl("^-?[0-9.]+--?[0-9.]+$", spec)) {                       # "lo-hi", either bound may be negative ("-9--1")
    parts <- regmatches(spec, regexec("^(-?[0-9.]+)-(-?[0-9.]+)$", spec))[[1]]
    lo <- as.numeric(parts[2]); hi <- as.numeric(parts[3])
    return(!is.na(x) & x >= lo & x <= hi)
  }
  !is.na(x) & x == as.numeric(spec)
}
to_target <- function(tv) if (grepl("^\\.", tv)) tag_na(tv) else as.numeric(tv)

# Apply value_map rows (for one target × survey) to a numeric vector.
# Returns list(y = harmonized values, consumed = which positions were set by the map).
apply_value_map <- function(x, maps) {
  # string sources are only recoded through quoted value-map rows; unlisted strings stay missing (as in Stata)
  y <- if (is.character(x)) rep(NA_real_, length(x)) else as.numeric(x)
  consumed <- rep(FALSE, length(x))
  if (nrow(maps) == 0) return(list(y = y, consumed = consumed))
  maps <- maps[order(maps$source_value == "*"), ]           # '*' rows last
  for (i in seq_len(nrow(maps))) {
    sel <- !consumed & match_spec(x, maps$source_value[i])
    y[sel] <- to_target(maps$target_value[i]); consumed[sel] <- TRUE
  }
  list(y = y, consumed = consumed)
}

# Missing codes for one source variable in one survey.  Precedence (first wins):
#   1. survey-wide code rules (e.g. SPVN -7/-4/-3/-2)
#   2. label rules (value label matches e.g. 'weet niet', 'geen informatie')
#   3. declared rules: SPSS user-defined missing values declared in the source file (source_missing.csv),
#      assigned a tag by code pattern (e.g. 7 -> .a, 9 -> .d)
# value_map rows are applied before any of these and take precedence over all of them.
missing_codes <- function(survey, srcvar) {
  rules <- MISSRULES %>% filter(survey == !!survey)
  out <- rules %>% filter(rule_type == "code") %>% transmute(code = as.numeric(match), target)
  labs <- SRCLABELS %>% filter(survey == !!survey, source_var == srcvar)
  if (nrow(labs)) {
    lr <- rules %>% filter(rule_type == "label")
    for (i in seq_len(nrow(lr))) {
      hit <- labs$code[str_detect(str_to_lower(str_trim(labs$label_nl)), regex(lr$match[i], ignore_case = TRUE))]
      if (length(hit)) out <- bind_rows(out, tibble(code = hit, target = lr$target[i]))
    }
  }
  decl <- SRCMISS %>% filter(survey == !!survey, source_var == srcvar)
  if (nrow(decl)) {
    dr <- rules %>% filter(rule_type == "declared")
    codes <- unlist(map2(decl$lo, decl$hi, ~ if (.y - .x <= 1000) seq(.x, .y) else c(.x, .y)))
    for (cd in unique(codes)) {
      hit <- which(str_detect(format(cd, scientific = FALSE, trim = TRUE), dr$match))
      if (length(hit)) out <- bind_rows(out, tibble(code = cd, target = dr$target[hit[1]]))
    }
  }
  distinct(out, code, .keep_all = TRUE) %>% filter(!is.na(code))
}

apply_missing <- function(x, y, consumed, survey, srcvar) {
  if (is.character(x)) return(y)                     # string sources: no numeric missing codes
  mc <- missing_codes(survey, srcvar)
  for (i in seq_len(nrow(mc))) {
    sel <- !consumed & !is.na(x) & x == mc$code[i]
    y[sel] <- tag_na(mc$target[i])
  }
  y
}

# Attach value labels (harmonized value set + missing tags) and a variable label.
label_var <- function(y, vsname, label) {
  labs <- miss_labels()
  if (!is.na(vsname) && vsname != "") {
    vsl <- VALUESETS %>% filter(valueset == vsname)
    labs <- c(setNames(vsl$code, vsl$label_en), labs)
  }
  y <- labelled(y, labels = labs)
  attr(y, "label") <- label
  y
}
label_num <- function(y, label) { attr(y, "label") <- label; y }

# Read one raw file with the right encoding; returns a data.frame of plain numeric/character columns
# plus the source value labels kept in attribute "src_labels" per column (Dutch), for the *_source file.
read_raw <- function(path, encoding) {
  if (grepl("\\.por$", path, ignore.case = TRUE)) {
    d <- read_por(path, user_na = TRUE)                 # keep SPVA user-missing codes as values
  } else {
    d <- read_sav(path, encoding = if (encoding == "utf-8-double") "UTF-8" else encoding, user_na = TRUE)
  }
  d
}
fix_cp1252 <- function(s) iconv(iconv(s, from = "UTF-8", to = "latin1"), from = "CP1252", to = "UTF-8")

# ---- routing gates vs the data (v0.4.2) -----------------------------------------
# For every spoken questionnaire item whose printed routing condition maps to a harmonized gate variable
# (crosswalks/routing_rules.csv -> wording.csv routing_gates), count the harmonized values that come from that source
# variable (the source is non-missing and the target is valid) and fall outside the gate.  Rows where the gate itself is
# missing are reported separately.  Verdict: 'holds' (no value outside), 'holds with exceptions' (at most 10% outside),
# 'does not hold' (more).  04_build writes the table to docs/routing_check.csv; 05_codebook prints it per variable;
# 99_checks recomputes it and fails on a gate that does not hold.
routing_eval <- function(d, out_base) {
  RG <- WORDING %>% filter(!is.na(routing_gates), routing_gates != "") %>% distinct(target, survey, source_var, routing_gates)
  srcf <- list(); out <- list()
  for (i in seq_len(nrow(RG))) {
    t <- RG$target[i]; k <- RG$survey[i]; sv <- RG$source_var[i]
    if (!t %in% names(d)) next
    if (is.null(srcf[[k]])) { f <- sprintf("%s_source_%s.rds", out_base, k); if (!file.exists(f)) next; srcf[[k]] <- readRDS(f) }
    s <- srcf[[k]]; if (!paste0("src_", sv) %in% names(s)) next
    sid <- INCLUDED$svy_id[str_to_lower(INCLUDED$svy_name) == k]; rows <- which(as.numeric(d$svy_id) == sid)
    xs <- s[[paste0("src_", sv)]][match(as.numeric(d$id_person[rows]), as.numeric(s$id_person))]
    if (is.numeric(xs)) {                                                   # source codes that are missing values (-5 n.a., 9 DK, ...)
      mc <- suppressWarnings(c(missing_codes(k, sv)$code, as.numeric(VALUEMAP$source_value[VALUEMAP$target == t & VALUEMAP$survey == k & VALUEMAP$source_var == sv & str_starts(VALUEMAP$target_value, fixed("."))])))
      xs[xs %in% mc[!is.na(mc)]] <- NA
    }
    has <- !is.na(d[[t]][rows]) & !is.na(xs)
    for (g in str_split(RG$routing_gates[i], regex(";\\s*(?=[a-z0-9_]+ (in \\{|is \\{|[<>]=? ))"))[[1]]) {   # ';' inside a description is not a separator
      m <- str_match(g, "^([a-z0-9_]+) in \\{([0-9,]+)\\} \\((.*)\\)$")
      mc2 <- str_match(g, "^([a-z0-9_]+) (>=|<=|>|<) (-?[0-9.]+) \\((.*)\\)$")          # numeric gate: 'hh_size > 1'
      if (!is.na(m[1, 1]) && m[1, 2] %in% names(d)) {
        gv <- as.numeric(d[[m[1, 2]]][rows]); allowed <- as.numeric(str_split(m[1, 3], ",")[[1]])
        known <- !is.na(gv); outside <- has & known & !(gv %in% allowed); gate_v <- m[1, 2]; allowed_txt <- m[1, 3]; desc <- m[1, 4]
      } else if (!is.na(mc2[1, 1]) && mc2[1, 2] %in% names(d)) {
        gv <- as.numeric(d[[mc2[1, 2]]][rows]); thr <- as.numeric(mc2[1, 4])
        known <- !is.na(gv); gate_ok <- switch(mc2[1, 3], ">" = gv > thr, "<" = gv < thr, ">=" = gv >= thr, "<=" = gv <= thr)
        outside <- has & known & !gate_ok; gate_v <- mc2[1, 2]; allowed_txt <- paste(mc2[1, 3], mc2[1, 4]); desc <- mc2[1, 5]
      } else if (!is.na((mc3 <- str_match(g, "^([a-z0-9_]+) is \\{([.a-e,]+)\\} \\((.*)\\)$"))[1, 1]) && mc3[1, 2] %in% names(d)) {
        x <- d[[mc3[1, 2]]][rows]; tags <- sub("^\\.", "", str_split(mc3[1, 3], ",")[[1]])       # gate: the referenced item was don't know / refused
        gv <- ifelse(is.na(x), ifelse(is_tagged_na(x), paste0(".", na_tag(x)), "."), "v")
        known <- rep(TRUE, length(x)); outside <- has & !(gv %in% paste0(".", tags)); gate_v <- mc3[1, 2]; allowed_txt <- paste("is", mc3[1, 3]); desc <- mc3[1, 4]
      } else next
      tb <- table(gv[outside]); share <- if (sum(has)) sum(outside) / sum(has) else 0
      out[[length(out) + 1]] <- tibble(target = t, survey = k, source_var = sv, gate = gate_v, allowed = allowed_txt, description = desc,
        n_values = sum(has), n_gate_missing = sum(has & !known), n_outside = sum(outside), share_outside = round(share, 4),
        outside_gate_values = paste0(names(tb), "=", as.integer(tb), collapse = " "),
        verdict = if (sum(outside) == 0) "holds" else if (share <= 0.10) "holds with exceptions" else "does not hold")
    }
  }
  bind_rows(out)
}

# ---- build identity: sha256 over the crosswalks and the code (sorted paths), first 12 hex digits ----------------------
build_id <- function() {
  files <- c(list.files(P("crosswalks"), pattern = "\\.csv$", full.names = TRUE),
             list.files(P("code"), pattern = "\\.(R|do|py)$", full.names = TRUE, recursive = TRUE))
  files <- sort(files[!grepl("__pycache__", files)])
  h <- vapply(files, function(f) as.character(openssl::sha256(file(f))), character(1))
  substr(as.character(openssl::sha256(charToRaw(paste(basename(files), h, collapse = "\n")))), 1, 12)
}
BUILD_ID <- build_id()

