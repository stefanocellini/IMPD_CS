# 01_import.R : unzip the DANS deposits (if needed) and read the six source files.
# Output: data/interim/<survey>_<level>.rds and .dta   (level: ro = roster, pp = interviewed persons, hh = heads;
#         main = the single person file of flat surveys such as SIM)
# All columns are stored as plain numeric/character with SPSS user-missing codes kept as values; value labels
# come from crosswalks/source_labels.csv.  The .dta copies are the input of the Stata pipeline (Stata cannot
# read SPSS portable files), so both pipelines start from identical values.
source(file.path(Sys.getenv("IMPD_ROOT", unset = getwd()), "code", "R", "00_setup.R"))

plain <- function(x) { x <- as.vector(unclass(x)); attributes(x) <- NULL; x }

for (i in seq_len(nrow(INCLUDED))) {
  s <- INCLUDED[i, ]
  rawdir <- P("data", "raw", s$svy_name %>% str_to_lower())
  if (!dir.exists(rawdir)) {
    dir.create(rawdir, recursive = TRUE)
    logmsg("Unzipping %s -> %s", s$zipfile, rawdir)
    unzip(P(s$zipfile), exdir = rawdir)
  }
  expected <- strsplit(s$file_sha256, ";", fixed = TRUE)[[1]]
  for (lvl in survey_levels(s)) {
    f <- file.path(rawdir, s[[paste0("file_", lvl)]])
    # provenance: the deposited file must be the one the crosswalks were built from (surveys.csv: file_sha256);
    # the row-number identifiers of SIM 2006 / SING 2009 are only meaningful for exactly that file
    j <- match(lvl, survey_levels(s)); h <- as.character(openssl::sha256(file(f)))
    if (length(expected) >= j && nzchar(expected[j]) && h != expected[j])
      stop(sprintf("%s %s: sha256 %s differs from the registered deposit (%s)", s$svy_name, basename(f), h, expected[j]))
    d <- read_raw(f, s$encoding)
    d <- as.data.frame(lapply(d, plain), stringsAsFactors = FALSE)
    # deposits without a person identifier (SIM 2006, SING 2009): the row number in the deposited file is the id
    if (lvl == "main" && s$id_var == "impd_rownum") d$impd_rownum <- seq_len(nrow(d))
    if (s$encoding == "cp1252") {                       # .por string columns
      for (v in names(d)) if (is.character(d[[v]])) d[[v]] <- fix_cp1252(d[[v]])
    }
    # text must be valid UTF-8 in every delivered format: haven does not always re-encode single-byte strings of the
    # source (SPVN 2003 municipality names and open answers came out as raw latin1/cp1252 bytes)
    for (v in names(d)) if (is.character(d[[v]])) {
      x <- d[[v]]; bad <- !is.na(x) & !validUTF8(x)
      if (any(bad)) {
        from <- if (tolower(s$encoding) %in% c("latin1", "windows-1252", "cp1252")) "CP1252" else "UTF-8"
        x[bad] <- iconv(x[bad], from = from, to = "UTF-8", sub = "?"); d[[v]] <- x
        logmsg("%s %s: %d values of %s re-encoded from %s to UTF-8", s$svy_name, lvl, sum(bad), v, from)
      }
    }
    saveRDS(d, P("data", "interim", sprintf("%s_%s.rds", str_to_lower(s$svy_name), lvl)))
    write_dta(d, P("data", "interim", sprintf("%s_%s.dta", str_to_lower(s$svy_name), lvl)), version = 14)
    logmsg("%s %s: %d rows x %d vars  (%s)", s$svy_name, lvl, nrow(d), ncol(d), basename(f))
  }
}
