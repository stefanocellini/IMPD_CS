# IMPD-CS — Integrated Migrant Panel Dataset, cross-sectional component

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24141874.svg)](https://doi.org/10.5281/zenodo.24141874)

IMPD-CS harmonizes eight Dutch surveys of persons with a migration background, all archived at DANS — **SPVA 2002**, **SPVN 2003**, **LAS 2004/05**, **SIM 2006**, **SING 2009**, **SIM 2011**, **SIM 2015** and **SIM 2020** — into one person-level file: 55,157 persons × 1,642 variables with English, theme-stemmed names, shared value sets and one missing-value scheme, plus a companion file per survey with every original variable. The file is built from the DANS deposits by an R pipeline or a Stata pipeline that produce the same result. Version 0.5.1.

> **Repeated cross-sections, not a panel.** The surveys are independent samples with different target populations, age ranges and weights; `id_person` identifies a record within one survey and does not follow persons across surveys. The panel in the project's name is IMPD-P, the registry-linked component built separately on the CBS microdata.

> **The data are not in this repository and cannot be shared, not even between colleagues.** Six of the eight deposits are DANS *request permission* data. Every user downloads the deposits under the DANS conditions and rebuilds the file; the repository holds what makes the rebuild exact — the code, the crosswalks and the codebook.

## Get the data in three steps

1. **Get the deposits from DANS.** `Surveys/Sources.txt` links the eight DANS pages. For the six SCP surveys, click *Request access* and accept the DANS licence (SCP approves; allow days to weeks, so start here). Download each deposit as one zip and save it in the repository's `Surveys/` folder under exactly these names: `SPVA 2002.zip`, `SPVN 2003.zip`, `LAS 2004 2005.zip`, `SIM 2006.zip`, `SING 2009.zip`, `SIM 2011.zip`, `SIM 2015.zip`, `SIM 2020.zip`.
2. **Get the repository.** Download the latest release from the *Releases* page and unzip it (or `git clone https://github.com/stefanocellini/IMPD_CS.git`). Keep the folder outside OneDrive or Dropbox.
3. **Build.** From the repository folder, in **R** (packages haven, dplyr, readr, stringr, tidyr, purrr, openssl, jsonlite): `Rscript code/R/run_all.R`, about ten minutes. Or in **Stata 16+**: run `Rscript code/R/01_import.R` once (R reads the deposits for both engines, because three of them are SPSS portable files Stata cannot open; two minutes), then `do code/Stata/run_all.do`, about 25 minutes. Either build stops if a check fails and ends with a run log — `docs/run_log.md` (R) or `docs/run_log_stata.md` (Stata) — whose build identity must be the one of the release: `7069c412771c` for v0.5.1.

Your files are then in `data/derived/`: `impd_cs_v0_5_1.rds` / `.dta` (the harmonized file; `_stata.dta` from the Stata build) and `impd_cs_v0_5_1_source_<survey>` companions with every original variable.

**Every step in detail — what to install, how to verify the build, what can go wrong and what to do about it: [`docs/user_guide.md`](docs/user_guide.md).**

## Use the data

- **Find measures:** the variable finder in `docs/codebook.html`; the codebook's variable index (section 4); `docs/codebook_variables.csv` (the index as a table — filter the `avail_<survey>` columns); `docs/comparability.csv` (how comparable each variable is across surveys, and why).
- **Inspect a measure** in its codebook entry (section 5): how it was obtained, who reported it, the exact question per survey, categories and recodes, who was eligible, routing.
- **Define your study population:** codebook section 1 (survey coverage, populations, weights) together with each measure's eligibility statement; `svy_routing_mig`, `dem_eth`, `dem_gen` and `svy_resptype` are the variables to select on.
- **Check the joint sample before a model:** `impd_sample()` (`code/R/impd_tools.R`, `code/Stata/impd_tools.do`) reports, per survey, how many records have a valid value on every variable of the model and why the others drop out, and stops when a survey has no complete record — so that a survey never disappears from a pooled model unnoticed.
- **Report** the population, the weighting and pooling choice and the final sample by survey. `docs/example_analysis.md` does all of this on one question asked in all eight surveys, in R and in Stata (`code/examples/`).
- **Missing values** are Stata extended missings (tagged NAs in R): `.a` don't know, `.b` refusal, `.c` not applicable, `.d` no information, `.e` not collected.

## Citing IMPD-CS

Cite the version together with the build identity, and the DANS deposits of the surveys you use (below). `CITATION.cff` holds the metadata (GitHub: *Cite this repository*). Each release is archived on Zenodo with a DOI of its own; the concept DOI https://doi.org/10.5281/zenodo.24141874 covers all versions and resolves to the latest release.

> Cellini, S., van Tubergen, F., & Kalmijn, M. (2026). *IMPD-CS: harmonized cross-sections of Dutch migrant surveys, 2002–2020 (code, crosswalks and codebook)*, version 0.5.1, build `7069c412771c`. NIDI-KNAW. https://doi.org/10.5281/zenodo.24141875

For a later version, take the version, the build identity (`docs/BUILD_ID`) and the version DOI from that release's Zenodo record.

Authors: Stefano Cellini (NIDI-KNAW; cellini@nidi.nl), Frank van Tubergen (NIDI-KNAW, Utrecht University and University of Groningen; tubergen@nidi.nl) and Matthijs Kalmijn (NIDI-KNAW and University of Groningen; kalmijn@nidi.nl). NIDI-KNAW is the Netherlands Interdisciplinary Demographic Institute of the Royal Netherlands Academy of Arts and Sciences. For questions and problems, GitHub issues are preferred (they stay visible to every user; a free GitHub account is needed to open one); email for anything that does not belong in a public issue.

## Citing the sources

The eight deposits, in the versions the crosswalks were built from (`Surveys/Sources.txt`; the pipeline verifies each data file's checksum). Each DANS page gives the full citation of its deposit:

- Gijsberts, M. et al. / SEOR-ISEO & SCP (2005). *Sociale positie en voorzieningengebruik van allochtonen 2002 — SPVA 2002*, version 3.2. DANS. https://doi.org/10.17026/dans-xdt-cynn
- ISEO, Erasmus University Rotterdam (2009). *Sociale positie en voorzieningengebruik van allochtonen 2003 (vluchtelingengroepen)*, version 2.1. DANS. https://doi.org/10.17026/dans-x7u-vkfm
- Sociaal en Cultureel Planbureau. *Leefsituatie Allochtone Stedelingen 2004/2005 — LAS*, version 4.1. DANS. https://doi.org/10.17026/dans-zqg-uqn8
- Sociaal en Cultureel Planbureau. *Survey Integratie Minderheden 2006 — SIM 2006*, version 4.0. DANS. https://doi.org/10.17026/dans-2z9-6eqc
- Sociaal en Cultureel Planbureau. *Survey Integratie Nieuwe Groepen 2009 — SING 2009*, version 3.0 (CBS-protected public version). DANS. https://doi.org/10.17026/dans-xnn-ky48
- Sociaal en Cultureel Planbureau. *Survey Integratie Minderheden 2011 — SIM 2011*, version 2.0. DANS. https://doi.org/10.17026/dans-2a2-77kp
- Sociaal en Cultureel Planbureau (2022). *Survey Integratie Minderheden 2015 — SIM 2015*, version 2.0. DANS. https://doi.org/10.17026/dans-x63-dq58
- Sociaal en Cultureel Planbureau (2022). *Survey Integratie Minderheden 2020 — SIM 2020*, version 2.0. DANS. https://doi.org/10.17026/dans-26h-xn4n
- Fieldwork reports: TNS NIPO/Veldkamp (2015), *Veldwerkverslag SIM 2015*; Dagevos, J. & Kappelhof, J. (2022), *Survey integratie migranten 2020. Uitvoering van veldwerk ten tijde van corona* (SCP).
- Classifications: RVIG Landelijke Tabellen (Tabel 34 Landentabel); CBS gemeentelijke indelingen; CBS SBC-92/ISCO and SBI schakelschema's; CBS StatLine 70936ENG (CPI). URLs and retrieval dates in `External/Sources.txt`.

## Licence, questions, contributing

The code is MIT-licensed; the crosswalks, documents and citation file are CC BY 4.0 (`LICENSE`). Questions, problems and requests for a variable or a recode: GitHub issues, naming the version and the build identity. To change the harmonization, add a survey or make a release, read `CONTRIBUTING.md`; how the method works is in `docs/harmonization.md`, and every decision taken on the way in `docs/decisions.md`.
