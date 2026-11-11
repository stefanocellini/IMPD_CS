# 04_build.R : label, order and write the harmonized person-level file and the companion source file.
#   data/derived/impd_cs_v<version>.dta / .rds / .csv          harmonized variables (English stems)
#   data/derived/impd_cs_v<version>_source.dta / .rds          original source variables (src_ prefix, Dutch labels)
source(file.path(Sys.getenv("IMPD_ROOT", unset = getwd()), "code", "R", "00_setup.R"))

all <- readRDS(P("data", "interim", "derived_all.rds"))
vm <- VARMAP %>% filter(include_main == 1)
order_vars <- vm$target[vm$target %in% names(all)]
missing_from_build <- setdiff(vm$target, names(all))
if (length(missing_from_build)) stop("targets declared but not built: ", paste(missing_from_build, collapse = ", "))
main <- all[order_vars]

src_note <- function(r) {
  parts <- c()
  for (s in KEYS) {
    sv <- r[[paste0("src_", s)]]; nm <- INCLUDED$svy_name[str_to_lower(INCLUDED$svy_name) == s]
    parts <- c(parts, if (sv != "") sprintf("%s: %s (%s)", nm, sv, r[[paste0("srclabel_", s)]]) else if (r$derive == "") sprintf("%s: not collected", nm) else NULL)
  }
  if (r$derive != "") parts <- c(parts, paste0("Derived: ", r$derive))
  paste(parts, collapse = ". ")
}
for (i in seq_len(nrow(vm))) {
  r <- vm[i, ]; t <- r$target
  if (r$type == "str") { main[[t]] <- label_num(as.character(main[[t]]), r$label_en) }
  else {
    y <- as.numeric(main[[t]])
    # numeric variables carry labels for the missing tags only (so that tabulations read the tags)
    main[[t]] <- if (r$valueset != "") label_var(y, r$valueset, r$label_en) else label_var(y, "", r$label_en)
  }
  attr(main[[t]], "impd_source") <- src_note(r)            # kept in the .rds; haven does not write it to .dta
  attr(main[[t]], "impd_universe") <- r$universe_en
  if (r$notes != "") attr(main[[t]], "impd_notes") <- r$notes
}
# integer-valued categorical/id columns stay double (tagged NAs require doubles); nothing else to coerce.

ver <- gsub("\\.", "_", IMPD_VERSION)
out_base <- P("data", "derived", sprintf("impd_cs_v%s", ver))
attr(main, "label") <- sprintf("IMPD-CS v%s build %s - harmonized person-level file", IMPD_VERSION, BUILD_ID)
saveRDS(main, paste0(out_base, ".rds"))
write_dta(main, paste0(out_base, ".dta"), version = 14)
# CSV convenience export: numeric codes only; tagged missing types are not representable (use .dta/.rds)
csv <- main; for (v in names(csv)) if (!is.character(csv[[v]])) csv[[v]] <- as.numeric(zap_labels(csv[[v]]))
write_csv(csv, paste0(out_base, ".csv"), na = "")
logmsg("Main file: %d persons x %d variables -> %s.{dta,rds,csv}", nrow(main), ncol(main), basename(out_base))

# ---- companion source files (one per survey: source codes and labels are survey-specific) ----------------
SRCVARS <- read_cw("source_variables.csv")
for (i in seq_len(nrow(INCLUDED))) {
  key <- str_to_lower(INCLUDED$svy_name[i]); sid <- INCLUDED$svy_id[i]
  d <- readRDS(P("data", "interim", paste0("source_", key, ".rds")))
  if (INCLUDED$structure[i] == "flat") {
    ids <- all %>% filter(svy_id == sid) %>% select(id_person, id_hh, svy_id, svy_resptype, PERSNR)
    d <- ids %>% left_join(d %>% select(-svy_resptype, -HHNUMMER, -GEZLIDNR), by = "PERSNR") %>% select(-PERSNR)
  } else {
    ids <- all %>% filter(svy_id == sid) %>% select(id_person, id_hh, svy_id, svy_resptype, HHNUMMER, GEZLIDNR)
    d <- ids %>% left_join(d %>% select(-svy_resptype), by = c("HHNUMMER", "GEZLIDNR")) %>% select(-HHNUMMER, -GEZLIDNR)
  }
  src <- d[c("id_person", "id_hh", "svy_id", "svy_resptype")]
  for (v in setdiff(names(d), names(src))) {
    x <- d[[v]]
    lab_nl <- SRCVARS %>% filter(survey == key, source_var == v) %>% pull(label_nl) %>% first()
    if (is.na(lab_nl)) lab_nl <- ""
    if (is.character(x)) { attr(x, "label") <- substr(lab_nl, 1, 80); src[[paste0("src_", v)]] <- x; next }
    vl <- SRCLABELS %>% filter(survey == key, source_var == v, !is.na(code))
    x <- as.numeric(x)
    if (nrow(vl)) x <- labelled(x, labels = setNames(vl$code, make.unique(ifelse(vl$label_nl == "", "(no label)", str_trunc(vl$label_nl, 60)))))
    attr(x, "label") <- substr(lab_nl, 1, 80)
    src[[paste0("src_", v)]] <- x
  }
  src$svy_id <- labelled(as.numeric(src$svy_id), labels = setNames(VALUESETS$code[VALUESETS$valueset == "survey"], VALUESETS$label_en[VALUESETS$valueset == "survey"]))
  attr(src, "label") <- sprintf("IMPD-CS v%s build %s - %s source variables (Dutch labels)", IMPD_VERSION, BUILD_ID, INCLUDED$svy_name[i])
  saveRDS(src, sprintf("%s_source_%s.rds", out_base, key))
  write_dta(src, sprintf("%s_source_%s.dta", out_base, key), version = 14)
  logmsg("Source file %s: %d persons x %d variables -> %s_source_%s.{dta,rds}", INCLUDED$svy_name[i], nrow(src), ncol(src), basename(out_base), key)
}
# routing gates vs the data (needs the companion source files written above)
RC <- routing_eval(main, out_base)
write_csv(RC, P("docs", "routing_check.csv"))
logmsg("Routing gates checked against the data: %d source x gate pairs, %d hold, %d hold with exceptions (<= 10%% of values outside), %d do not hold -> docs/routing_check.csv",
       nrow(RC), sum(RC$verdict == "holds"), sum(RC$verdict == "holds with exceptions"), sum(RC$verdict == "does not hold"))
writeLines(LOG, P("data", "interim", "log_04_build.txt"))
