# How the harmonization works

This note explains, step by step, how the IMPD public component turns eight survey files into one harmonized person-level file. It is written for collaborators joining the project: read it before changing a crosswalk or the code. Users who only want to analyse the data need the codebook (`docs/codebook.html`), not this note.

## The principle

Every survey answer is translated into a common target variable by **an explicit, written rule**. No step is done by hand on the data. Every decision is a row in a table (a *crosswalk*), and two independent programs, one in R and one in Stata, carry out those tables. To change a decision you change a row and rebuild; the data are never edited directly.

The work therefore has three layers:

1. **What we want**: the target variables, their categories and the missing-value scheme.
2. **How each survey maps onto them**: the crosswalks.
3. **Executing and checking the mapping**: the R and Stata pipelines and the checks.

```
DANS deposits + questionnaires + external classifications
        |
        v
Python declarations (code/crosswalk_builder/variables*.py) + questionnaire parsing
        |   build.py (refuses to finish on unread or unclaimed rows)
        v
CSV crosswalks (crosswalks/)
        |   read identically by
        v
R pipeline (code/R/)            Stata pipeline (code/Stata/)
01 import -> 02 harmonize -> 03 derive -> 04 build -> 05 codebook -> 99 checks
        |                                   |
        +----------- cell-by-cell comparison (cf) ----------+
        v
harmonized file + source companions + codebook + build identity
```

## 1. Inputs

- **The eight DANS deposits** (`Surveys/*.zip`; sources in `Surveys/Sources.txt`): data files and questionnaires. SPVA 2002 and SPVN 2003 are household surveys delivered as three linked files: household heads (`hh`), interviewed persons (`pp`) and the household roster (`ro`). The six SCP surveys (LAS 2004/05 to SIM 2020) have one person file each.
- **External classifications** (`External/`, sources in `External/Sources.txt`): CBS/RVIG country codes, municipality codes per year, occupation and industry classifications and their conversion tables, and the CPI used to express amounts in constant euros.

## 2. Defining the targets

Before any survey is mapped, the harmonized file is defined:

- **Target variables** (1,671; 1,642 in the main file), named `theme_concept` in English. The stem gives the theme (`dem_` demography, `mig_` migration, `lab_` labour market, `att_` attitudes ...); the name glossary is `crosswalks/name_glossary.csv`.
- **Value sets** (342, `crosswalks/valuesets.csv`): the agreed categories with English labels, such as `yesno`, `edu3` (low/middle/high) or `ethgroup`.
- **One missing-value scheme for all surveys**: `.a` don't know, `.b` refusal, `.c` not applicable (the person was routed past the question), `.d` no information, `.e` not collected (the survey, or this person's questionnaire, did not contain the item).
- **Detail versus comparability.** Where the surveys measure a concept in more or less detail, there are two variables rather than one compromise: `_cat` holds the harmonized classes every survey can fill, and `_det` keeps the survey-specific detail.

## 3. Declaring the mapping, survey by survey

This is the substantive work. It is written in Python, using a few short declaration functions from `declare.py`. Each survey has its own setup file, `code/crosswalk_builder/surveys/<key>.py`. That file holds the registry entry, missing-value conventions, questionnaire and routing. The variable declarations of the eight current surveys are in `variables.py` (SPVA/SPVN), `variables_2004_2011.py` and `variables_sim.py`. A survey added later keeps its declarations in its own setup file instead (see [Adding a survey](#adding-a-survey)). The declaration functions are:

- `V(...)` declares a target: theme, label, value set, and the source variable in each survey.
- `M(...)` / `A(...)` give the **value map**: which source code becomes which target code (e.g. `ANDLAND` 1 -> 0, 2 -> 1).
- `U(...)` gives the **universe**: who was supposed to be asked. This decides whether an empty cell is `.c` (routed past) or a real missing value.
- `ASKED(...)` records that, in the household surveys, an item was in only one questionnaire (heads or other members); other persons get `.e`.
- `SKIP(...)` records a source variable deliberately left out, with the reason.
- Notes attached to a target carry what a user must know (CCF education boundaries, SING 2009 statistical protection, and so on); they appear in the codebook and inside the data files.

Alongside this, **the questionnaires are parsed** (`questionnaires.py`). For each item this extracts the question text as read or shown to the respondent, the answer options, the printed routing condition (e.g. `INDIEN [Q430, 2]`) and, in SIM 2020, the split-half assignment. This produces the wording tables of the codebook (`crosswalks/wording.csv`) and the routing rules that are later checked against the data.

## 4. Building the crosswalks

`python code/crosswalk_builder/build.py` turns the declarations into the 28 CSV files in `crosswalks/`. The central ones:

| File | What it holds |
|---|---|
| `variable_map.csv` | One row per target: label, value set, source variable per survey, universe, notes |
| `value_map.csv` | Source code -> target code, per target and survey (2,985 rows) |
| `valuesets.csv` | Codes and English labels of every value set |
| `missing_rules.csv`, `source_missing.csv` | Which source codes become `.a` / `.b` / `.d` |
| `universes.csv`, `routing_rules.csv`, `routing_exceptions.csv` | Who was asked; printed routing translated into harmonized variables; conditions the data contradict |
| `asked_to.csv` | Household surveys: items asked of heads only or of other members only |
| `merge_exceptions.csv` | Household surveys: declared exceptions to the file-precedence rule |
| `source_variables.csv`, `source_labels.csv`, `source_values.csv`, `source_skipped.csv` | Inventory of all 2,684 source variables, their labels and observed values |
| `comparability_review.csv`, `label_approvals.csv` | The two hand-maintained files: reviewed comparability verdicts, and signed readings of value-map rows |

The builder **refuses to finish** when:

- a source variable is neither used nor listed in `source_skipped.csv`, so nothing is silently forgotten;
- a value-map row does not follow the grammar (a code, a range `lo-hi`, a quoted string or `*`);
- **the value-map review fails** (`code/tools/value_map_review.py`). The review reads every value-map row with its source label next to its target label. A row it cannot read by itself must carry a signed approval in `label_approvals.csv`: a two-valued target whose source label is not a plain yes/no, a row copied between surveys whose labels differ, or overlapping range labels. The approval is bound to the exact value that was read, so a later change to the mapping fails until someone reads the row again.

## 5. Running the pipeline

`code/R/run_all.R` and `code/Stata/run_all.do` run the same six steps on the same crosswalks.

1. **Import** (`01_import`). Unzip the deposits and read every data file as delivered, keeping the original codes, user-missing codes included. The R step also writes `.dta` copies, which are the Stata pipeline's input (Stata cannot read the SPSS portable files), so `Rscript code/R/01_import.R` must run once before `run_all.do`, and both pipelines start from identical values.
2. **Harmonize** (`02_harmonize`), survey by survey:
   - In SPVA/SPVN, merge the three files into one row per roster member. Where the files hold the same variable, the most detailed file wins (heads > interviewed persons > roster), except in the declared merge exceptions.
   - Apply the **value map** to every target.
   - Apply the **missing rules**: source codes for don't know, refusal or 'unknown' become `.a`, `.b` or `.d`. Persons outside the universe become `.c`. Items absent from the survey, or not in this person's questionnaire, become `.e`.
3. **Derive** (`03_derive`). Variables built from other variables rather than read directly: age classes from age, the partner's characteristics copied through the roster link (household surveys), amounts deflated to 2015 euros with the CPI, country, municipality and occupation recodes through the external tables, and rules such as 'no religion' where the person belongs to none.
4. **Build** (`04_build`). Stack the eight surveys, order the variables, attach labels and notes, and write the main file (`.dta`, `.rds`, `.csv`). Write one **source companion** per survey with every original variable (prefix `src_`, original codes, keyed by `id_person`), so any harmonized value can be checked against the raw one.
5. **Codebook** (`05_codebook`). Generated from the crosswalks and the built data, never written by hand: index, one entry per variable with wording table, categories and counts per survey, eligibility and comparability class.
6. **Checks** (`99_checks`). 44 checks that re-derive results from the released files instead of trusting the pipeline: universes against the data, routing conditions against who actually answered, the missing-value rules, value labels, split-half assignments, the value-map review, the merge exceptions. The results go to `docs/run_log.md`. The Stata side ends by comparing its file with the R file cell by cell.

## 6. Layers of verification

Each layer catches a different kind of error. None replaces the others.

| Layer | Catches | Cannot catch |
|---|---|---|
| R vs Stata, cell by cell (`cf`) | Execution errors: a crosswalk row applied wrongly by one engine | A wrong rule, which both engines apply faithfully |
| The 44 checks | Rules that contradict the data: someone answering a question they should have been routed past, a missing code that does not exist | A plausible rule with the wrong meaning |
| The value-map review | Rules that contradict the labels: an inverted yes/no, a row copied from a survey where the same codes mean something else | A wrong mapping between categories whose labels look compatible |
| Independent reconstruction (the reviewer's assurance run; the restricted component against the CBS microdata) | Definition errors that every internal check reproduces | - |

## 7. Recording and versioning

- **`docs/decisions.md`** records every substantive choice and correction, with the evidence.
- **The build identity** (`docs/BUILD_ID`) is a hash of the crosswalks and the code. Two people with the same identity are using the same rules; cite it with the version number.
- **Git** keeps the history: every change is a visible, reversible commit. Commit after a build whose checks pass, with the version and build identity in the message.
- The data are never in the repository: anyone with access to the DANS deposits rebuilds them.

## A worked example: `mig_transit`

`mig_transit` records whether a migrant stayed in another country before arriving in the Netherlands.

- **SPVN 2003.** Source `ANDLAND` is a yes/no item ('after leaving, were you in other countries?': 1 yes, 2 no). Value map: 1 -> 1, 2 -> 0.
- **SING 2009.** A variable with the same name has different answer options: 1 'came directly to the Netherlands', 2 'lived elsewhere first'. The SPVN rows had been copied across by variable name and code list.

Every structural check passed: both codes are valid `yesno` values and the counts were plausible either way. The inversion was found by reading the labels (the restricted component, comparing with the CBS code lists). The fix was two value-map rows, 1 -> 0 and 2 -> 1, followed by a rebuild. The routing then confirmed it: the year of first arrival was asked only of those now coded 1. The case is why the value-map review exists. Since it was added, a row copied between surveys whose labels say different things cannot pass the build until someone reads it and signs it.

## Making a change

1. Edit the declaration in `code/crosswalk_builder/` (not the CSV files, which the builder regenerates; the two hand-maintained files are the exception).
2. Run `python code/crosswalk_builder/build.py`. If the value-map review lists rows, read each against its labels and sign it in `crosswalks/label_approvals.csv` with the value you read.
3. Run `code/R/run_all.R`, then `code/Stata/run_all.do`; check `docs/run_log.md` and the Stata comparison.
4. Record the decision in `docs/decisions.md`, then commit with the version and build identity in the message.


## Adding a survey

### In plain words

The crosswalk builder is the program that writes the tables in `crosswalks/`, which R and Stata then follow. For each survey it needs two kinds of information.

1. **Facts about the survey:**
   - what the deposit is called and where it comes from;
   - how it codes missing values (in SIM 2020, -5 means not asked and -3 don't know);
   - where the questionnaire is;
   - which printed routing rules apply.
2. **The variable mapping:** lines such as "the harmonized `dem_sex` comes from this survey's `geslacht`; code 1 stays 1, code 2 stays 2". These play the role of `rename` and `recode` lines in Stata, written down as a table instead of run as commands.

Each survey has its own settings file in the folder `code/crosswalk_builder/surveys/`. Think of it as a binder with one form per survey: `sim2020.py` is the SIM 2020 form, with labelled headings for each fact. When the builder runs, it reads every form in the folder. A form with a missing heading, or two forms claiming the same survey, stops it with a message. In Stata terms, it is a master do-file that `include`s every do-file in a folder, each one setting up one survey.

The forms are written in Python notation, so quotes, commas and brackets have to be right. Adding a survey is still form-filling, done by copying the form of a similar survey, not programming. The one exception is a questionnaire laid out differently from every earlier one (step 4 below).

What to do, and where, for a new survey (here a hypothetical SIM 2025 with key `sim2025`):

| What you do | Where | How |
|---|---|---|
| Put the DANS deposit in place | `Surveys/` | copy the zip |
| Create the survey's form | `code/crosswalk_builder/surveys/sim2025.py` | copy `sim2020.py` (or the most similar survey) and fill in the new survey's details |
| Map the variables | the same file, in `declare()` at the bottom | one line per variable: attach to a harmonized variable, create a new one, or skip with a reason |
| Add an answer scale no survey has used before (rare) | `code/crosswalk_builder/valuesets.py` | one `vs()` line |
| Register the survey | `code/crosswalk_builder/build.py` | run it once: `python code/crosswalk_builder/build.py`; it records the new survey and then stops, as expected |
| Read the deposit's metadata | `code/R/00a_source_metadata.R` | run it: `Rscript code/R/00a_source_metadata.R` (it unzips the deposit) |
| Build the crosswalks | `code/crosswalk_builder/build.py` | run it again; it lists what is still unmapped and stops until everything is mapped or skipped |
| Sign the value maps the builder cannot read by itself | `crosswalks/label_approvals.csv` | one row per item, with the value you read |
| Note where the question only approximately matches earlier waves | `crosswalks/comparability_review.csv` | one row per harmonized variable concerned |
| Derivation rules specific to the survey (rare) | `code/R/03_derive.R` and `code/Stata/03_derive.do` | the same rule in both |
| Build the data | `code/R/run_all.R`, then `code/Stata/run_all.do` | run both; check `docs/run_log.md` and the Stata comparison |
| Record the decision | `docs/decisions.md` | a new numbered section |
| Commit | the Git repository | GitHub Desktop, with the version and build identity in the message |

The import, harmonization, build and codebook code in R and Stata need no change: they read the survey from the crosswalks.

### Step by step

A new survey, such as a later SIM wave, is one file: `code/crosswalk_builder/surveys/<key>.py`. The builder finds every module in that folder, checks it, and collects its contents into the crosswalks. Nothing in `build.py`, `declare.py` or the R and Stata code has to be edited for a survey that uses an existing questionnaire layout.

**1. Put the deposit in place.** Copy the DANS zip into `Surveys/`. The pipeline unzips it into `data/raw/<key>/` the first time it runs.

**2. Create the survey file.** Copy the module of the most similar survey: `sim2020.py` for a flat CAWI/CAPI wave, `sim2006.py` for a deposit without a person identifier. Then edit each part. The builder refuses to run if a required part is missing, if two modules share a key, survey id or `KW`, or if the file name and `SURVEY["key"]` differ.

| Part | What it holds | Ends up in |
|---|---|---|
| `KW` | A short code, e.g. `"25"`. `V()` then takes `s25=` (source variable) and `u25=` (universe) for this survey | declarations |
| `LABEL` | Display name, e.g. `"SIM 2025"` | codebook, `surveys.csv` |
| `SURVEY` | Registry entry: `svy_id` (next chronological number), name, year, `status="included"`, `key`, `structure` (`"flat"` or household files), DANS identifiers, file names inside the zip, encoding, identifier and weight variables, missing-value scheme | `surveys.csv` |
| `ZIP_SHA256` | sha256 of the zip as downloaded | `surveys.csv` (provenance) |
| `ELIGIBLE`, `WEIGHTS` | Target population and weight guidance, one sentence each | codebook section 1 |
| `MISSING_RULES` | How the file codes missing values: explicit codes, label patterns, or SPSS-declared codes, each mapped to `.a`–`.d` | `missing_rules.csv` |
| `QUESTIONNAIRES` | The questionnaire PDF(s), the parser to read them with, and optionally the text span to read | wording and routing tables |

Optional parts, needed only when the survey has the feature: `DESIGN` (mode, split half, languages; codebook section 3.2), `ROUTING_RULES` and `ROUTING_EXCEPTIONS` (printed routing conditions and where the data contradict them), `ACQ_OVERRIDES` (how an item was collected, where the parser cannot tell), `CONSTRUCTED` (variables built by the data producer, with no question), `PREFER_INSTRUMENT` (parallel questionnaires, as in SIM 2015), `LINK_BY_QNUM` (a questionnaire without variable names, linked by question number, as in SIM 2006 and SING 2009), and for household surveys `MERGE_EXCEPTIONS` and `MUNICIPALITIES`.

**3. Read the source metadata.** Run the builder once: `python code/crosswalk_builder/build.py`. It writes the registry (`crosswalks/surveys.csv`) first and then stops with errors about the new survey, which has neither metadata nor declarations yet. That is expected. Then run `Rscript code/R/00a_source_metadata.R`: it unzips the deposit and reads the file's declared missing values and observed codes, which the builder needs.

**4. Check the questionnaire parser.** The existing parsers are `tns` (SIM 2015, SIM 2020), `spva`, `spvn`, `vk_hc` and `vk_script`. If the new questionnaire has a layout none of them reads, write a `parse_*` function in `questionnaires.py` and add it to `PARSERS`. This is the only change outside the survey file, and the parser regression checks in `build.py` show whether the old questionnaires still parse as before. Items that the automatic name match cannot link get an `L(survey, source_var, qid)` line.

**5. Declare the variables.** Write a `declare()` function in the survey file. In it, every source variable is either attached to a target or skipped with a reason:

Source variable names below are illustrative.

```python
def declare():
    from declare import A, V, M, U, W, L, SKIP
    A("dem_sex", "sim2025", "geslacht", pairs=[(1, 1), (2, 2)])     # existing target
    A("lab_emp", "sim2025", "WERK", yn12=True, u="aged 15-74")      # existing yes/no target, own universe
    V("dem_newitem", "dem", "Label of a new item", s25="NIEUW",
      u25="all respondents", valueset="yesno", yn12=True)            # new target
    SKIP("sim2025", "INTERVIEWER_ID", "fieldwork administration")
```

`A()` attaches the survey's variable to a target that already exists, with its value map (`pairs`) and universe (`u`). `V()` creates a new target. `M()` adds a single value-map row, `U()` a universe, `W()` a wording note. A new value set (`vs()` in `valuesets.py`) is needed only for an answer scale no survey has used before. While the declarations are incomplete, run the builder with `IMPD_PARTIAL=1`: it then lists the unclaimed source variables instead of stopping.

**6. Build and review.** Without `IMPD_PARTIAL`, the builder must run with no unclaimed source variable. Read each row of the value-map review against its labels and sign it in `crosswalks/label_approvals.csv` with the value you read (section 4). Where the new survey's question matches a target only approximately, classify the target in `crosswalks/comparability_review.csv` (class, note, reviewer, date).

**7. Run the engines.** R and Stata read the survey from the crosswalks, so the import, harmonize, build and codebook steps need no edit. Two places hold survey-specific rules: `03_derive.R`/`03_derive.do` (derivation rules such as the SIM 2020 split-half items) and `99_checks.R`. A new derivation needs the same rule in both engines. Then follow [Making a change](#making-a-change) steps 3 and 4: run R and Stata, record the decision in `docs/decisions.md`, commit.
