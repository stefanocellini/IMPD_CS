# impd_tools.R : helpers for analyses of the IMPD public file (not part of the build).
#   source("code/R/impd_tools.R")
#   d <- readRDS("data/derived/impd_cs_v0_4_6.rds")
#   impd_sample(d, c("dem_sex", "dem_age_cat3", "edu_dipl_hi_lvl3", "lab_emp"))
#
# impd_sample(): model-level eligibility report.  For a set of analysis variables it shows, per survey, how many records
# have a valid (non-missing) value on every variable, and why records drop out: variables not collected in the survey (.e),
# routed past / not applicable (.c), item non-response (.a .b .d .) - so that a survey never disappears from a pooled model
# unnoticed.  With stop_on_dropout = TRUE (default) it stops when a survey that carries all variables ends with no
# complete record, or when any requested survey does not carry one of the variables.
suppressPackageStartupMessages({ library(haven); library(dplyr) })

impd_sample <- function(d, vars, surveys = NULL, stop_on_dropout = TRUE, quiet = FALSE) {
  stopifnot(all(vars %in% names(d)))
  if (is.null(surveys)) surveys <- unique(as.character(d$svy_name))
  d <- d[as.character(d$svy_name) %in% surveys, ]
  tag <- function(x) ifelse(is.na(x), ifelse(is_tagged_na(x), paste0(".", na_tag(x)), "."), "v")
  out <- lapply(surveys, function(s) {
    r <- d[as.character(d$svy_name) == s, ]
    st <- sapply(vars, function(v) tag(r[[v]]))
    if (is.null(dim(st))) st <- matrix(st, ncol = length(vars), dimnames = list(NULL, vars))
    complete <- rowSums(st == "v") == length(vars)
    not_collected <- vars[colSums(st == ".e") == nrow(r) & nrow(r) > 0]
    per_var <- sapply(vars, function(v) sprintf("%s valid / %s .c / %s .e / %s other", sum(st[, v] == "v"), sum(st[, v] == ".c"), sum(st[, v] == ".e"), sum(!st[, v] %in% c("v", ".c", ".e"))))
    tibble(survey = s, n_records = nrow(r), n_complete = sum(complete), share_complete = round(mean(complete), 3),
           not_collected = paste(not_collected, collapse = ", "), detail = paste(sprintf("%s: %s", vars, per_var), collapse = " | "))
  }) %>% bind_rows()
  if (!quiet) {
    cat(sprintf("impd_sample: %d variable(s), %d survey(s)\n", length(vars), nrow(out)))
    print(as.data.frame(out[c("survey", "n_records", "n_complete", "share_complete", "not_collected")]), row.names = FALSE)
    for (i in seq_len(nrow(out))) cat(sprintf("  %s: %s\n", out$survey[i], out$detail[i]))
  }
  lost <- out$survey[out$n_complete == 0]
  if (length(lost)) {
    msg <- sprintf("survey(s) with no complete record on %s: %s%s", paste(vars, collapse = ", "), paste(lost, collapse = ", "),
                   ifelse(any(out$not_collected[out$survey %in% lost] != ""), sprintf(" (not collected: %s)", paste(unique(out$not_collected[out$survey %in% lost]), collapse = "; ")), ""))
    if (stop_on_dropout) stop(msg, call. = FALSE) else warning(msg, call. = FALSE)
  }
  invisible(out)
}

# impd_universe(): the stated universe of a variable per survey (from the codebook metadata), for the eligibility statement
# of an analysis.
impd_universe <- function(vars, root = Sys.getenv("IMPD_ROOT", unset = getwd())) {
  vm <- readr::read_csv(file.path(root, "docs", "codebook_variables.csv"), show_col_types = FALSE, col_types = readr::cols(.default = "c"))
  vm %>% filter(target %in% vars) %>% select(target, universe_en, subject, starts_with("avail_"))
}
