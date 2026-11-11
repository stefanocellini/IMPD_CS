# IMPD-CS user guide

From the DANS deposits to a verified build and a first analysis, for anyone who wants to use IMPD-CS: the cross-sectional component of the Integrated Migrant Panel Dataset, which harmonizes eight Dutch surveys of persons with a migration background (SPVA 2002 to SIM 2020) into one person-level file. No knowledge of the pipeline is needed; where a step can go wrong, the guide says what you will see and what to do.

**What you get.** One file of 55,157 persons × 1,642 harmonized variables, in Stata (`.dta`), R (`.rds`) and CSV form, plus a companion file per survey with every original variable; a codebook with a variable finder; and a run log that proves the build. **What you do not get:** the data themselves. They are DANS deposits, six of them under a *request permission* licence, so you download them yourself and the pipeline rebuilds the file on your computer in about ten minutes. The built file stays with you: it may not be passed on, not even to a colleague, because it is still the DANS data.

**Repeated cross-sections, not a panel.** The surveys are independent samples with their own target populations, age ranges and weights. `id_person` identifies a record within one survey and nobody is followed across surveys. The panel in the project's name is IMPD-P, the registry-linked component built separately on the CBS microdata.

## 1. What you need

| | Required | Notes |
|---|---|---|
| **DANS access** | an account on the DANS Data Station Social Sciences and Humanities (institutional login via SURFconext, or a DANS account) | SPVA 2002 and SPVN 2003 are open access; the six SCP surveys need a *request permission* agreement each (section 2) |
| **R** | R 4.1 or later, with the packages `haven`, `dplyr`, `readr`, `stringr`, `tidyr`, `purrr`, `openssl`, `jsonlite` | the pipeline runs in R; `00_setup.R` stops and names any package that is missing. The worked example also needs `survey` |
| **Stata** | optional: Stata 16 or later (the worked example: 17) | the R build already writes a `.dta` that Stata reads; run the Stata pipeline only if you want the Stata-built twin and the cell-by-cell comparison |
| **Python 3** | optional | one of the 44 checks (the label review) runs a Python script and is skipped, with a notice, when Python is not found; the Word copies and the slide deck need it too |
| **pandoc** | optional | Word copies of the documents and the PowerPoint deck; skipped with a notice when absent |
| **Disk** | about 3 GB | deposits under 100 MB; unzipped and intermediate files 300 MB; built files 2 GB (the R-written `.dta` alone is 735 MB) |
| **Time** | R: about 10 minutes; Stata: about 25 minutes | |

Not needed: `pdftotext`, `pyreadstat`, `pandas`. They serve the crosswalk builder, which you never run as a user.

## 2. Get the deposits

The eight deposits, with the DANS page of each, are listed in `Surveys/Sources.txt`; the versions the crosswalks were built from are named there too. For each:

1. Open the DANS page. For the six SCP surveys, click *Request access*, state your purpose and accept the DANS licence; SCP, the depositor, approves the request. This can take days to weeks, so request all six at once and before anything else.
2. Download the whole deposit as one zip file (the dataset page's download of all files, original format).
3. Save it in the `Surveys/` folder of the repository (section 3) under exactly the name in `crosswalks/surveys.csv`, column `zipfile`:

| Survey | File name | Access |
|---|---|---|
| SPVA 2002 | `Surveys/SPVA 2002.zip` | open |
| SPVN 2003 | `Surveys/SPVN 2003.zip` | open |
| LAS 2004/05 | `Surveys/LAS 2004 2005.zip` | request permission |
| SIM 2006 | `Surveys/SIM 2006.zip` | request permission |
| SING 2009 | `Surveys/SING 2009.zip` | request permission |
| SIM 2011 | `Surveys/SIM 2011.zip` | request permission |
| SIM 2015 | `Surveys/SIM 2015.zip` | request permission |
| SIM 2020 | `Surveys/SIM 2020.zip` | request permission |

Do not unzip, rename or edit anything inside. The pipeline unzips each deposit into `data/raw/<survey>/` and checks the checksum of the data file it needs against the one registered in `crosswalks/surveys.csv`, so a different version of a deposit is refused with a clear message rather than silently harmonized (section 7).

## 3. Get the repository

Either clone it with Git (`git clone https://github.com/stefanocellini/IMPD_public.git`, or GitHub Desktop), or download a release as a zip from the repository's *Releases* page and unzip it. Use a release (a tagged version such as `v0.5.0`) rather than an arbitrary commit: a release is a state meant for use, with release notes.

Keep the folder out of a synced cloud folder (OneDrive, Dropbox) if you can: the build writes 2 GB and the syncing has been seen to serve stale copies of files.

The folder you now have is the *project root*. Everything below is run from it.

## 4. Build the data

**R.** Open a terminal (Windows: Command Prompt or PowerShell; macOS: Terminal) in the project root and run

```
Rscript code/R/run_all.R
```

Windows: if `Rscript` is not found, use its full path, for example `"C:\Program Files\R\R-4.4.1\bin\Rscript.exe" code/R/run_all.R`. From R or RStudio instead: `Sys.setenv(IMPD_ROOT = "<project root>"); source("code/R/run_all.R")`.

The pipeline prints its steps: `01_import` (unzip and read the deposits), `02_harmonize` (apply the crosswalks), `03_derive`, `04_build` (write the files), `05_codebook`, `99_checks`, then the optional Word copies and slide deck. It stops at the first error with a message naming the cause. When it ends with `Pipeline finished in … minutes`, you have:

| File | Content |
|---|---|
| `data/derived/impd_cs_v0_5_0.dta` / `.rds` / `.csv` | the harmonized file (version in the name) |
| `data/derived/impd_cs_v0_5_0_source_<survey>.dta` / `.rds` | one companion per survey with every original variable, prefix `src_` |
| `docs/codebook.html`, `docs/codebook.md` | the codebook of this build |
| `docs/run_log.md`, `docs/BUILD_ID` | the checks and the build identity (section 5) |

**Stata (optional).** After the R build, in Stata: `cd` to the project root, then `do code/Stata/run_all.do`. It rebuilds the file from the same crosswalks, writes `data/derived/impd_cs_v0_5_0_stata.dta` (compressed, with a note per variable) and the Stata companions, and ends by comparing its build with the R build cell by cell. Stata cannot read the SPSS deposits itself: it reads the plain copies that the R step `01_import` wrote to `data/interim/`, so the R build (or at least `Rscript code/R/01_import.R`) comes first.

## 5. Verify the build

Three things say that your build is the one the release describes:

1. **`docs/BUILD_ID`** holds the build identity: a 12-character fingerprint of the crosswalks and the code, followed by the version and the time. It must equal the build identity stated in the release notes. If it does not, your copy of the repository differs from the release (section 7).
2. **`docs/run_log.md`** lists the checks, one line each, starting with `PASS`. All 44 must pass (43 and one `SKIP` when Python is not installed: the label review already ran when the crosswalks were built). A `FAIL` stops the pipeline before the files are written.
3. **The row and column counts** in the run log's first checks: 55,157 persons and 1,642 variables for version 0.5.0.

With Stata as well: the Stata log ends with `PASS Stata build identical to R build in every cell of every variable`.

The first time a new machine builds IMPD-CS, please report these three things in a GitHub issue (section 9), together with your operating system and R version: a build that reproduces on a machine the project never saw is the strongest check there is.

## 6. Use the data

Start with the codebook: open `docs/codebook.html` in a browser (it works offline). Its *Start here* section walks through an analysis in six steps and points to the reference sections; the variable finder at the top searches names and labels. In short:

- **Names** are English and theme-stemmed: `dem_` demography, `mig_` migration history, `lang_` language, `edu_` education, `lab_` work, `inc_` income, `hous_` housing, `hlth_` health, `soc_` social contacts, `fam_` family, `rel_` religion, `att_` attitudes, `iden_` identification, `disc_` discrimination, `svy_` survey design, `hh_` household, and so on (29 themes; codebook section 4 lists them); `src_` marks the original variables in the companions. `crosswalks/name_glossary.csv` explains the abbreviations.
- **Missing values** are Stata extended missings (haven tagged NAs in R): `.a` don't know, `.b` refusal, `.c` not applicable (routed past the question), `.d` no information, `.e` not collected (the survey never had the item, or not in this person's questionnaire).
- **Availability and comparability.** Not every variable exists in every survey, and a variable that exists everywhere may rest on different questions. Each codebook entry states the surveys that carry it, who was asked, the exact wording per survey and a comparability class; `docs/codebook_variables.csv` and `docs/comparability.csv` hold the same as tables.
- **Populations and weights.** Each survey has its own target population and its own weight, `svy_wgt`, which reproduces that population and nothing else; codebook section 1 lists them. Pooled estimates across surveys are a modelling choice to state, not a property of the data. `svy_routing_mig`, `dem_eth`, `dem_gen` and `svy_resptype` define the usual study populations.
- **Check the joint sample before a model.** `impd_sample()` (`code/R/impd_tools.R`, `code/Stata/impd_tools.do`) reports, per survey, how many records have a valid value on every variable of a model and why the others drop out, and stops when a survey has no complete record. Use it so that a survey never disappears from a pooled model unnoticed.
- **The worked example** `docs/example_analysis.md`, with its scripts in `code/examples/`, runs one question asked in all eight surveys through these steps in R and in Stata.

In Stata, `use "data/derived/impd_cs_v0_5_0.dta", clear` is all it takes; the file written by R carries variable and value labels. The Stata-built twin, `impd_cs_v0_5_0_stata.dta`, is the same data compressed to a fifth of the size, with the codebook's notes attached to each variable (`notes dem_sex`).

## 7. When something goes wrong

| What you see | Why | What to do |
|---|---|---|
| `install the missing R package(s) first: …` | a package is not installed | run the `install.packages(...)` line the message gives, then start again |
| an error in `01_import` naming a zip or a data file that cannot be opened | a deposit is missing or misnamed | check the file names against the table in section 2, including the spaces |
| `SIM2006 …: sha256 … differs from the registered deposit` | the deposit is another version than the one the crosswalks were built from | download the version named in `Surveys/Sources.txt`; if DANS no longer offers it, open an issue: the crosswalks have to be checked against the new version before it can be used |
| the data file is not found after unzipping | the zip's internal folder structure differs from the one registered (`crosswalks/surveys.csv`, columns `file_main`, `file_hh`, `file_pp`, `file_ro`) | unzip by hand so that the data file sits at that path inside `data/raw/<survey>/`, then start again; the pipeline skips unzipping when the folder exists |
| `FAIL …` in the run log | a check found the build inconsistent | this should not happen with an unmodified release: open an issue with the run log attached |
| `SKIP value-map review: no working Python interpreter found` | Python 3 is not installed or not on the PATH | harmless for the data; install Python 3 to run the check yourself |
| `Word copies skipped` / `Slide decks skipped` | pandoc or Python is absent | harmless; the Markdown and HTML documents are the reference |
| `docs/BUILD_ID` differs from the release notes | your repository copy is not the release: a different commit, or a file changed, or line endings converted by Git on checkout | download the release zip, or `git checkout v0.5.0`; the project's `.gitattributes` prevents line-ending conversion, but a global Git setting can still override it |
| Stata: `file data/interim/… not found` | the R import has not run | run `Rscript code/R/01_import.R` (or the whole R pipeline) first |

## 8. Rules of use

- **No redistribution of the data**, in any form: not the deposits, not the built file, not a subset or an extract of microdata. Each user obtains the deposits from DANS under the licence they accept there. Tables and estimates you publish are yours.
- **Cite** IMPD-CS with its version and build identity (`CITATION.cff`; the release's Zenodo DOI) and the DANS deposits of the surveys you use (README, *Citing the sources*). The code is MIT-licensed, the crosswalks and documents CC BY 4.0 (`LICENSE`).
- **Pin the version.** Record the version and the build identity in your analysis code. Versions below 1.0 may still change variable names and codes; the release notes and `docs/decisions.md` say what changed.
- **Do not edit the crosswalks locally.** A changed crosswalk gives a build with another identity that nobody else can reproduce. If a recode or a label is wrong, or a variable is missing, open an issue (section 9) or a pull request; the change then reaches everyone in the next release, with its reasoning recorded in `docs/decisions.md`.

## 9. Questions, problems, requests

GitHub issues on the repository, naming the version and the build identity, and attaching `docs/run_log.md` when a build failed. Requests for a new harmonized variable, a different coding or an added survey go there too; `docs/harmonization.md` explains how the harmonization works and how a survey is added, for those who want to contribute.

## 10. Updating to a new version

Each release has notes that list what changed: data cells, variable names, codes, documentation. To update, pull the new release (or download its zip), keep your `Surveys/` folder, and run the pipeline again: the new files carry the new version in their names, and the old ones remain until you delete them. Between releases the build identity tells revisions apart; analysis code should name both.
