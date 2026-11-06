# IMPD — Integrated Migrant Panel Dataset: public (DANS) component

Harmonization of eight Dutch surveys of persons with a migration background (SPVA 2002 to SIM 2020), archived at DANS, into one
person-level file with English, theme-stemmed variable names, reproducible in **R** and in **Stata**
from the DANS zip files and a set of CSV crosswalks.

Version 0.4.8 — **SPVA 2002** (DANS P1684), **SPVN 2003** (refugee-group SPVA, DANS P1753), **LAS 2004/05** (easy-dataset:40215), **SIM 2006** (easy-dataset:40304), **SING 2009** (easy-dataset:51530, CBS-protected partial release), **SIM 2011** (easy-dataset:67677, V3), **SIM 2015** (easy-dataset:239464, CCF) and **SIM 2020** (easy-dataset:259562, CCF): 55,157 persons x 1,642 harmonized variables, every variable of every deposit harmonized. Development history is in `docs/decisions.md`.

> **Repeated cross-sections, not a panel.** The public component stacks independent cross-sectional surveys with different target populations, age ranges and weights; `id_person` identifies a record within one survey and does not follow persons across surveys. Codebook section 1 lists, per survey, who was eligible and which weight applies. Identifiers are built from the immutable `svy_key` (fieldwork year), so they do not change when a survey is added.

> **Access note.** SPVA 2002 and SPVN 2003 are open-access deposits; the six SCP surveys (LAS 2004/05, SIM 2006, SING 2009, SIM 2011, SIM 2015, SIM 2020) are DANS *request permission* deposits under the DANS licence. The built data file therefore cannot be shared openly: the public deliverable is this repository (code, crosswalks, codebook), and every user rebuilds the data from the eight DANS deposits placed in `Surveys/`.

```
IMPD_public/
├── Surveys/                 DANS zip deposits, as downloaded (never modified)
├── External/                classifications and price indices (country, municipality, occupation, industry, CPI); Sources.txt
├── crosswalks/              the harmonization, as data (read by both pipelines)
│   ├── surveys.csv            survey registry: ids, years, DANS ids, access, structure (hh_pp_ro / flat), file names, encodings, weights
│   ├── variable_map.csv       target variable -> source variable per survey, label, theme, scope, universe, notes
│   ├── valuesets.csv          harmonized value labels
│   ├── value_map.csv          survey code -> harmonized code (or tagged missing), one row per code/range
│   ├── missing_rules.csv      missing-value conventions per survey
│   ├── source_labels.csv / source_variables.csv / source_missing.csv / source_values.csv   source-file metadata
│   ├── wording.csv / wording_notes.csv / universes.csv   question wording per survey (from the questionnaires), curated notes, who was asked
│   ├── asked_to.csv           household surveys: items in the questionnaire of one respondent type only (the other type is .e)
│   ├── routing_rules.csv / routing_exceptions.csv   printed routing conditions -> harmonized gate variables; printed conditions the data contradict
│   ├── acquisition_overrides.csv / acquisition_review.csv   declared acquisition cases (interviewer-completed, sample-frame fields); rows the rules could not settle
│   ├── comparability_review.csv   reviewer overrides of the mechanical comparability classes (docs/comparability.csv)
│   ├── label_approvals.csv    signed readings of value-map rows that the label check cannot read by itself, bound to the value that was read (docs/value_map_review.csv is the full table)
│   ├── merge_exceptions.csv   household surveys: declared cases where a file's system-missing code yields to a less detailed file in the merge
│   ├── questionnaire_items.csv / questionnaire_constructed.csv / questionnaire_design.csv   parsed questionnaire blocks; variables the codebooks list as constructed; modes, versions, split-half and randomisation per survey
│   ├── municipalities.csv     survey municipality code -> CBS gemeentecode
│   ├── name_glossary.csv      abbreviations and battery prefixes used in variable names
│   └── cpi.csv                CPI index, 2015 = 100
├── code/
│   ├── crosswalk_builder/     Python: how the crosswalks were authored (valuesets.py, variables.py, variables_sim.py, variables_2004_2011.py, variables_links.py, glossary_*.py) and generated (build.py, questionnaires.py, declare.py)
│   ├── R/                     00_setup 00a_source_metadata 01_import 02_harmonize 03_derive 04_build 05_codebook 99_checks run_all; impd_tools.R (impd_sample helper for analyses)
│   └── Stata/                 00_setup 01_import 02_harmonize 03_derive 04_build 05_codebook 99_checks run_all; impd_tools.do (impd_sample)
│   ├── examples/              example_analysis.R / .do and their logs: the worked example of docs/example_analysis.md
│   └── tools/                 value_map_review.py: every value-map row read with its source label against the target label (last step of the builder; check 16); md_to_word.py: Word copies of the Markdown documents (docs/word/), run at the end of run_all.R when pandoc is installed
├── data/
│   ├── raw/                   unzipped deposits (created by the pipeline)
│   ├── interim/               plain copies of the source files (.rds/.dta) and intermediate builds
│   └── derived/               impd_public_v0_4_8.{dta,rds,csv}, impd_public_v0_4_8_source_<survey>.{dta,rds}
└── docs/                    codebook.html (with variable finder) / codebook.md / codebook_variables.csv, comparability.csv, value_map_review.csv, routing_check.csv, example_analysis.md, harmonization.md (how the harmonization works, for collaborators), decisions.md, run_log.md, BUILD_ID; word/ holds Word copies of the Markdown documents (derived, not build outputs)
```

## Start here

Follow this path from the source deposits to an analysis; the codebook's numbered sections are the reference material behind each step.

- **Rebuild the data** (below); the built file is not redistributed.
- **Find measures:** the variable finder in `docs/codebook.html`, the codebook's variable index (section 4), `docs/codebook_variables.csv` (the index as a table; filter the `avail_<survey>` columns) and `docs/comparability.csv` (comparability class and basis per variable).
- **Inspect the measures** in their codebook entries (section 5): acquisition, reporter, subject, exact question or procedure per survey, categories and recodes, eligible records, routing in harmonized variables.
- **Define your study population:** codebook section 1 (survey coverage, populations, weights) alongside each measure's eligibility statement; `svy_routing_mig`, `dem_eth`, `dem_gen`, `svy_resptype`.
- **Check the joint sample** with `impd_sample()` and `impd_universe()` (`code/R/impd_tools.R`, `code/Stata/impd_tools.do`) so that no survey drops out of a model unnoticed.
- **Run and report the analysis,** stating the population, the weighting and pooling choice and the final sample by survey; `docs/example_analysis.md` follows this workflow on one question asked in all eight surveys, in R and Stata (`code/examples/`).

Every generated codebook and run log carries a **build identity** (`docs/BUILD_ID`: sha256 of the crosswalks and the code, first 12 hex digits). Cite it together with the version: revisions made during development can share a version number.

## The repository

This is a Git repository (private for now). It holds everything needed to rebuild and document the data, and none of the data:

- **Tracked:** `code/`, `crosswalks/`, `docs/` (codebook, decisions, run log, the value-map review table), `External/` (public CBS and RVIG classification files used by the crosswalks, with their sources in `External/Sources.txt`), `Surveys/Sources.txt` (where each DANS deposit comes from) and this README.
- **Never tracked:** the DANS deposits (`Surveys/*.zip`), everything built from them (`data/`), the Word copies in `docs/word/` (regenerated by `run_all.R`), and any working folder. `.gitignore` is an allow-list: a file enters only if its folder is listed there, and data formats (`.dta`, `.rds`, `.sav`, `.zip` ...) are refused wherever they appear.
- **To work with it:** clone the repository, download the eight deposits from DANS (`Surveys/Sources.txt`; six need a *request permission* agreement) into `Surveys/` under the file names in `crosswalks/surveys.csv` (column `zipfile`, e.g. `Surveys/SIM 2006.zip`), and run the pipeline below. The R build writes `docs/BUILD_ID`; a clone of commit X rebuilds the build identity recorded in that commit.
- **Line endings:** `.gitattributes` switches off line-ending conversion, so every file is stored byte for byte (the crosswalk CSVs use CRLF, the code LF). The build identity is a hash over these bytes, so a converted checkout would report a different identity for the same content.
- **Commits:** commit after a build whose checks pass (`docs/run_log.md`), with the version and build identity in the message; record substantive decisions in `docs/decisions.md` as before.

## Running

**R** (haven, dplyr, readr, stringr, tidyr, purrr, openssl, jsonlite; `00_setup.R` stops with the names of any that are missing): from the `IMPD_public` root, `Rscript code/R/run_all.R`.
Takes about ten minutes for the eight surveys (the codebook step is the slowest). Writes data/derived/, docs/codebook.*, docs/run_log.md and stops if a check fails. The questionnaire-text extraction needs `pdftotext` (poppler) and runs inside the crosswalk builder, not in the R pipeline.

**Stata 16+**: from the `IMPD_public` root, `do code/Stata/run_all.do`. Needs the plain copies of the source files in
`data/interim/*.dta` (written by `Rscript code/R/01_import.R`; Stata cannot read SPSS portable files).
Writes `data/derived/*_stata.dta` (`compress`ed, hence smaller than the R `.dta`; with `notes` per variable) and, when the R build is present, compares the two builds cell by cell with `cf` (identical; see docs/run_log.md).

**Rebuilding the crosswalks** (only when adding a survey or changing a decision): edit
`code/crosswalk_builder/variables.py` (SPVA/SPVN), `variables_sim.py` (SIM 2015/2020), `variables_2004_2011.py` (LAS, SIM 2006, SING, SIM 2011), `variables_links.py` (relationship layer) or `valuesets.py`, then `Rscript code/R/00a_source_metadata.R` and
`python code/crosswalk_builder/build.py` (needs pyreadstat, pandas, openpyxl and pdftotext). The builder refuses to build if a source variable
is unclaimed, a target is unknown, or a harmonized code is not in its value set, and warns when an observed
source code would end up unlabelled.

## Analysis helpers

`source("code/R/impd_tools.R")` / `do code/Stata/impd_tools.do` provide `impd_sample()`: for a set of analysis variables it reports, per survey, how many records have a valid value on every variable and why records drop out (not collected `.e`, not applicable `.c`, item non-response), and stops when a survey has no complete record, naming the variables responsible. Use it before any pooled model so that a survey never disappears unnoticed; the codebook's `Availability`, `Reported by` and `Comparability` lines and `docs/comparability.csv` say in advance which surveys carry a variable and how comparable it is.

## Design in one paragraph

Harmonization is data, not code: both pipelines are thin engines that read the same crosswalks, so the R
and Stata outputs agree by construction and every decision is a row a reviewer can audit. Each row of the
output is a person: in the household samples (SPVA/SPVN) a household member listed in the roster, with
`svy_resptype` separating heads (main questionnaire), other interviewed members (mini questionnaire) and
roster-only members and `hh_*` variables merged from the head onto all members; in the person samples (LAS, SIM, SING)
an individually sampled respondent (`svy_resptype` = 4), including the native Dutch reference samples.
Question wording, answer options, battery items, routing and randomisation are documented per variable and survey from the questionnaire PDFs (wording tables in the codebook; every source variable is either linked to its question or documented as constructed/registry/administrative). Missing values use Stata extended missings / haven tagged NAs
(`.a` don't know, `.b` refusal, `.c` not applicable, `.d` no information, `.e` not collected). Companion
`*_source_<survey>` files keep every original variable. See `docs/decisions.md` for the decisions and
limitations and `docs/codebook.html` for every variable.

## Citing the sources

- Gijsberts, M. et al. / SEOR-ISEO & SCP (2005). *Sociale positie en voorzieningengebruik van allochtonen 2002 — SPVA 2002*. DANS. https://doi.org/10.17026/dans-xdt-cynn
- ISEO, Erasmus University Rotterdam (2009). *Sociale positie en voorzieningengebruik van allochtonen 2003 (vluchtelingengroepen)*. DANS. https://doi.org/10.17026/dans-x7u-vkfm
- Sociaal en Cultureel Planbureau (2022). *Survey Integratie Minderheden - SIM 2015 versie 3*. DANS. https://doi.org/10.17026/dans-x63-dq58
- Sociaal en Cultureel Planbureau (2022). *Survey Integratie Minderheden 2020 - SIM2020*. DANS. https://doi.org/10.17026/dans-26h-xn4n
- Fieldwork reports: TNS NIPO/Veldkamp (2015), *Veldwerkverslag SIM 2015*; Dagevos, J. & Kappelhof, J. (2022), *Survey integratie migranten 2020. Uitvoering van veldwerk ten tijde van corona* (SCP).
- Classifications: RVIG Landelijke Tabellen (Tabel 34 Landentabel); CBS gemeentelijke indelingen; CBS SBC-92/ISCO and SBI schakelschema's; CBS StatLine 70936ENG (CPI). URLs and retrieval dates in `External/Sources.txt`.
