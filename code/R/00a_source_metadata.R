# 00a_source_metadata.R : extract from the source files what the Python builder cannot see:
#   source_missing.csv    survey, variable, SPSS user-defined missing values (lo-hi) declared in the file
#   source_values.csv     survey, variable, observed code, count (discrete variables only, <= 300 distinct codes)
# (labels and variable inventories are extracted by code/crosswalk_builder/build.py with pyreadstat, which keeps
#  the original byte encoding of the .por labels; haven reads the user-missing declarations of .por files.)
# Run before code/crosswalk_builder/build.py.
suppressPackageStartupMessages({ library(haven); library(dplyr); library(readr); library(stringr); library(purrr); library(tidyr) })
ROOT <- Sys.getenv("IMPD_ROOT", unset = getwd()); P <- function(...) file.path(ROOT, ...)
SURVEYS <- read_csv(P("crosswalks", "surveys.csv"), show_col_types = FALSE, na = character()) %>% filter(status == "included")
fix_cp1252 <- function(s) { out <- iconv(iconv(s, from = "UTF-8", to = "latin1"), from = "CP1252", to = "UTF-8"); ifelse(is.na(out), s, out) }

vars <- list(); labs <- list(); miss <- list(); vals <- list()
for (i in seq_len(nrow(SURVEYS))) {
  s <- SURVEYS[i, ]; key <- str_to_lower(s$svy_name)
  rawdir <- P("data", "raw", key)
  if (!dir.exists(rawdir)) { dir.create(rawdir, recursive = TRUE); unzip(P(s$zipfile), exdir = rawdir) }
  levels <- if (s$structure == "flat") "main" else c("ro", "pp", "hh")
  for (lvl in levels) {
    f <- file.path(rawdir, s[[paste0("file_", lvl)]])
    enc <- if (s$encoding == "utf-8-double") "UTF-8" else s$encoding
    d <- if (grepl("\\.por$", f)) read_por(f, user_na = TRUE) else read_sav(f, encoding = enc, user_na = TRUE)
    for (v in names(d)) {
      x <- d[[v]]
      lab <- attr(x, "label"); if (is.null(lab)) lab <- ""
      vl <- attr(x, "labels")
      if (s$encoding == "cp1252") { lab <- fix_cp1252(lab); if (!is.null(vl)) names(vl) <- fix_cp1252(names(vl)) }
      fmt <- attr(x, "format.spss"); if (is.null(fmt)) fmt <- ""
      plain <- as.vector(unclass(x)); attributes(plain) <- NULL
      vars[[length(vars) + 1]] <- tibble(survey = key, source_var = v, label_nl = lab, format = fmt, file = lvl,
                                         n_nonmissing = if (is.character(plain)) sum(!is.na(plain) & str_trim(plain) != "") else sum(!is.na(plain)))
      if (lvl %in% c("hh", "main") || !(v %in% map_chr(labs, ~ paste(.x$survey[1], .x$source_var[1])) %in% paste(key, v))) {
        if (!is.null(vl) && length(vl)) labs[[paste(key, v)]] <- tibble(survey = key, source_var = v, code = as.numeric(vl), label_nl = names(vl))
      }
      nv <- attr(x, "na_values"); nr <- attr(x, "na_range")
      # keyed by file level too: the head and member files of a survey can declare different codes (SPVN NUWERK: 7 and 97
      # in the member file, 97 only in the head file); the union is kept, with the declaring files as provenance
      if (!is.null(nv)) miss[[paste(key, v, lvl, "v")]] <- tibble(survey = key, source_var = v, lo = as.numeric(nv), hi = as.numeric(nv), file = lvl)
      if (!is.null(nr)) miss[[paste(key, v, lvl, "r")]] <- tibble(survey = key, source_var = v, lo = as.numeric(nr[1]), hi = as.numeric(nr[2]), file = lvl)
      if (!is.character(plain)) {
        u <- unique(plain[!is.na(plain)])
        if (length(u) <= 300) {
          tb <- as.data.frame(table(plain), stringsAsFactors = FALSE)
          vals[[paste(key, v, lvl)]] <- tibble(survey = key, source_var = v, file = lvl, code = as.numeric(tb$plain), n = as.integer(tb$Freq))
        }
      }
    }
  }
}
sm <- bind_rows(miss) %>% group_by(survey, source_var, lo, hi) %>% summarise(files = paste(sort(unique(file)), collapse = ","), .groups = "drop") %>% arrange(survey, source_var, lo)
write_csv(sm, P("crosswalks", "source_missing.csv"), na = "")
# observed codes: a person appears in several files; keep the count from the file where it is largest
so <- bind_rows(vals) %>% group_by(survey, source_var, code) %>% summarise(n_max_file = max(n), files = paste(file, collapse = ","), .groups = "drop") %>%
  arrange(survey, source_var, code)
write_csv(so, P("crosswalks", "source_values.csv"), na = "")
message(sprintf("source_missing %d | source_values %d rows", nrow(sm), nrow(so)))
