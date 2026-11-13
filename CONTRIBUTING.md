# Contributing to IMPD-CS

This file is for collaborators: anyone who changes the harmonization, adds a survey, or makes a release. If you only want the data, the README and `docs/user_guide.md` are all you need.

Three documents divide the work: this file (the repository, its conventions, the release procedure), `docs/harmonization.md` (how the method works, *Making a change*, *Adding a survey*) and `docs/decisions.md` (every decision taken so far, numbered, with its reasons).

## Design in one paragraph

Harmonization is data, not code: both pipelines are thin engines that read the same crosswalks, so the R and Stata outputs agree by construction and every decision is a row a reviewer can audit. Each row of the output is a person: in the household samples (SPVA/SPVN) a household member listed in the roster, with `svy_resptype` separating heads (main questionnaire), other interviewed members (mini questionnaire) and roster-only members and `hh_*` variables merged from the head onto all members; in the person samples (LAS, SIM, SING) an individually sampled respondent (`svy_resptype` = 4), including the native Dutch reference samples. Question wording, answer options, battery items, routing and randomisation are documented per variable and survey from the questionnaire PDFs: every source variable is either linked to its question or documented as constructed, registry or administrative. Missing values use Stata extended missings / haven tagged NAs (`.a` don't know, `.b` refusal, `.c` not applicable, `.d` no information, `.e` not collected). Companion `*_source_<survey>` files keep every original variable.

## Layout of the repository

```
IMPD_CS/
├── Surveys/                 DANS zip deposits, as downloaded (never modified; never tracked); Sources.txt
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
│   ├── crosswalk_builder/     Python: how the crosswalks were authored (surveys/<key>.py, one setup file per survey; valuesets.py, variables.py, variables_sim.py, variables_2004_2011.py, variables_links.py, glossary_*.py) and generated (build.py, questionnaires.py, declare.py)
│   ├── R/                     00_setup 00a_source_metadata 01_import 02_harmonize 03_derive 04_build 05_codebook 99_checks run_all; impd_tools.R (impd_sample helper for analyses)
│   ├── Stata/                 00_setup 01_import 02_harmonize 03_derive 04_build 05_codebook 99_checks run_all; impd_tools.do (impd_sample)
│   ├── examples/              example_analysis.R / .do and their logs: the worked example of docs/example_analysis.md
│   └── tools/                 value_map_review.py (every value-map row read with its source label against the target label; last step of the builder and check 16); md_to_word.py (Word copies, docs/word/); make_deck.py (slide decks, docs/slides/); make_slide_template.py (prepares the NIDI PowerPoint template)
├── data/                    never tracked
│   ├── raw/                   unzipped deposits (created by the pipeline)
│   ├── interim/               plain copies of the source files (.rds/.dta) and intermediate builds
│   └── derived/               impd_cs_v<version>.{dta,rds,csv}, impd_cs_v<version>_source_<survey>.{dta,rds}; the Stata build's *_stata.dta
└── docs/                    codebook.html (with variable finder) / codebook.md / codebook_variables.csv, comparability.csv, value_map_review.csv, routing_check.csv, example_analysis.md, harmonization.md, user_guide.md, decisions.md, run_log.md (R) and run_log_stata.md (Stata), BUILD_ID, facts.csv (every number the slide decks quote, computed at each build); word/ (Word copies; derived, not tracked); slides/ (deck sources, the NIDI template, and the PowerPoint files built from them: see docs/slides/README.md)
```

## What enters the repository

- **Tracked:** `code/`, `crosswalks/`, `docs/` (without the Word copies, the PowerPoint files, the Stata codebook log and the full Stata run log), `External/` (public CBS and RVIG classification files, with their sources in `External/Sources.txt`), `Surveys/Sources.txt`, and the root files README, CONTRIBUTING, LICENSE, LICENSE-CC-BY-4.0.md and CITATION.cff.
- **Never tracked:** the DANS deposits (`Surveys/*.zip`), everything built from them (`data/`), and any working folder. `.gitignore` is an allow-list: a file enters only if its folder is listed there, and data formats (`.dta`, `.rds`, `.sav`, `.por`, `.zip`, …) are refused wherever they appear. A new root file or folder has to be added to the allow-list to be tracked.
- **Line endings:** `.gitattributes` switches off line-ending conversion, so every file is stored byte for byte (the crosswalk CSVs use CRLF, the code LF). The build identity is a hash over these bytes, so a converted checkout would report a different identity for the same content.
- **Build identity:** `docs/BUILD_ID` holds the sha256 of `crosswalks/*.csv` and `code/**/*.{R,do,py}`, first 12 hex digits, with the version and the time of the build. Any change to a crosswalk or to code — including a tool script — changes it; a change to a document does not. Every codebook, run log and dataset label carries it, and a clone of commit X rebuilds the identity recorded in X.

## Working rules

- **Change the declarations, not the outputs.** A harmonization change is made in the crosswalk builder (`code/crosswalk_builder/`: the survey's setup module in `surveys/`, the variable declarations, the value sets), then the crosswalks are rebuilt (below) and both engines are run. The engines are not edited for a content change; the crosswalk CSVs are never edited by hand. `docs/harmonization.md`, *Making a change*, walks through it; *Adding a survey* covers a new survey (one setup module per survey).
- **Both engines, every time.** A change is finished when the R build and the Stata build both pass their checks and the Stata build is identical to the R build cell by cell (the last Stata check; `docs/run_log_stata.md`).
- **Commit after a passing build**, with the version and the build identity in the commit message; the run logs and the codebook written by that build are part of the commit.
- **Record the decision.** Anything that changes what a user gets — a recode, a renamed variable, a changed population, a known limitation — is a numbered entry in `docs/decisions.md` with its reasons; the file is the project's memory and the release notes are written from it.
- **Between releases** the build identity tells revisions apart; a version number can cover several development builds.

## Rebuilding the crosswalks

Needed only when a declaration changes or a survey is added. Edit `code/crosswalk_builder/surveys/<key>.py` (survey setup), `variables.py` (SPVA/SPVN), `variables_sim.py` (SIM 2015/2020), `variables_2004_2011.py` (LAS, SIM 2006, SING, SIM 2011), `variables_links.py` (relationship layer) or `valuesets.py`; then run `Rscript code/R/00a_source_metadata.R` (source-file metadata from the deposits) and `python code/crosswalk_builder/build.py` (needs pyreadstat, pandas, openpyxl and `pdftotext` from poppler for the questionnaire PDFs). The builder refuses to build if a source variable is unclaimed, a target is unknown or a harmonized code is not in its value set; it warns when an observed source code would end up unlabelled; and its last step, the value-map review, stops on any value-map row whose source and target labels disagree and is not signed in `crosswalks/label_approvals.csv`.

## Running the pipelines

`Rscript code/R/run_all.R` (about ten minutes) and `do code/Stata/run_all.do` (about 25 minutes; needs `Rscript code/R/01_import.R` first, which the R pipeline includes) — both from the repository root; the user guide (section 4) describes each step and its outputs. The R pipeline also writes the Word copies of the Markdown documents (`docs/word/`, via `code/tools/md_to_word.py`) and the slide decks (`docs/slides/*.pptx`, via `code/tools/make_deck.py`) when Python and pandoc are installed; both are derived and not tracked. To change a deck, edit its Markdown source in `docs/slides/` — numbers and excerpts are filled from the repository at build time (`docs/slides/README.md`).

## Making a release

A release is a state meant for use outside the project. Zenodo archives every GitHub release and mints a DOI for it, so a release is made on GitHub's release page, never by pushing a tag alone.

1. **Finish the build.** Both engines pass, Stata identical to R; `docs/decisions.md` has an entry for everything that changed.
2. **Set the version** in `code/R/00_setup.R` (`IMPD_VERSION`) and `code/Stata/00_setup.do` (`global IMPD_VERSION`), and in `CITATION.cff` (`version`, `date-released`). Zenodo copies the title, authors, affiliations, keywords, abstract and licence from `CITATION.cff`, so check that it is current; spell affiliations as their ROR names (for example "Netherlands Interdisciplinary Demographic Institute", without a suffix), so that Zenodo links them. Rebuild in both engines — the version is in the file names, the dataset labels and the codebook — update the version line and the citation in the README, and commit.
3. **Write the release notes:** what changed since the previous release (data cells, variable names, codes, documents), the build identity, and the checks passed; the decisions log is the source.
4. **Publish on GitHub:** *Releases* → *Draft a new release* → tag `v<version>`, *Create new tag on publish*, target `main` → title `IMPD-CS v<version>` → paste the notes → *Publish release*. Within minutes Zenodo shows the new record (the DOI badge on zenodo.org → *GitHub*); the concept DOI 10.5281/zenodo.24141874 stays the same and resolves to the latest version.
5. **Record the DOI:** the new version DOI goes into `CITATION.cff` (`doi`, and an entry under `identifiers`) and the README (*Citing IMPD-CS*). Documents only, so the build identity is unchanged; commit and push.
6. **Check the Zenodo record** (creators, affiliations, licence, description). Its metadata can be edited after publication without creating a new version.

## Where things are documented

- `docs/harmonization.md`: the method, step by step, with a worked example; *Making a change*; *Adding a survey*.
- `docs/decisions.md`: every decision and known limitation, numbered, in the order they were taken.
- `docs/codebook.html` / `docs/codebook.md`: every variable, generated at each build from the crosswalks and the built data.
- `docs/run_log.md`, `docs/run_log_stata.md`: the checks of the last build, with the build identity.
- `docs/slides/README.md`: how the slide decks are written and built.
- `docs/user_guide.md`: the user's path from the deposits to a verified build.
