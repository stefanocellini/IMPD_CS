# run_all.R : run the complete IMPD public-component pipeline.
#   Rscript code/R/run_all.R          (from the IMPD root)
# Steps: 01 import -> 02 harmonize -> 03 derive -> 04 build -> 05 codebook -> 99 checks
ROOT <- Sys.getenv("IMPD_ROOT", unset = getwd())
steps <- c("01_import.R", "02_harmonize.R", "03_derive.R", "04_build.R", "05_codebook.R", "99_checks.R")
t0 <- Sys.time()
for (s in steps) {
  message(sprintf("\n==== %s ====", s))
  source(file.path(ROOT, "code", "R", s), local = new.env())
}
# Word copies of the Markdown documents (docs/word/): derived, for readers who prefer Word; needs python3 and pandoc
setup_env <- new.env(); source(file.path(ROOT, "code", "R", "00_setup.R"), local = setup_env)   # find_python()
py <- setup_env$find_python()
if (length(py) && nzchar(Sys.which("pandoc"))) {
  message("\n==== Word copies (code/tools/md_to_word.py) ====")
  system2(py[1], c(py[-1], "-I", shQuote(file.path(ROOT, "code", "tools", "md_to_word.py"))), env = paste0("IMPD_ROOT=", shQuote(ROOT)))
} else message("\nWord copies skipped: a working Python 3 and pandoc are needed for code/tools/md_to_word.py (the Markdown and HTML documents are the reference).")
message(sprintf("\nPipeline finished in %.1f minutes.", as.numeric(difftime(Sys.time(), t0, units = "mins"))))
