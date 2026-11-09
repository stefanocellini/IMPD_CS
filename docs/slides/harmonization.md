---
title: How the IMPD harmonization works
subtitle: From {{n_surveys}} survey deposits to one person-level file, and how the pipeline keeps itself honest
author:
- Stefano Cellini · NIDI
- "IMPD public component v{{version}} · build {{build_id}} · {{build_month}}"
---

<!--
Source of the slide deck "How the IMPD harmonization works".
Built by code/tools/make_deck.py (run_all.R calls it) into docs/slides/harmonization.pptx with the NIDI template.
A fact name in double braces is replaced by its value from docs/facts.csv, computed from the repository at every build.
Edit this file, not the PowerPoint copy. How pandoc lays out a slide (docs/slides/README.md):
  ## Title + text                      -> NIDI text page
  ## Title + one sentence + a table    -> NIDI wide page, sentence above the table
  ## Title + :::: columns ::::         -> NIDI wide page, two columns
  # Title alone                        -> orange section page
  ::: notes ... :::                    -> speaker notes
-->

## The IMPD in numbers

One harmonized person-level file from the public DANS versions of the Dutch migrant surveys.

| Count | What it counts |
|---:|---|
| {{n_surveys}} | surveys, {{year_first}}–{{year_last}}: SPVA 2002, SPVN 2003, LAS 2004/05, SIM 2006, SING 2009, SIM 2011, SIM 2015, SIM 2020 |
| {{n_persons}} | persons in the main file |
| {{n_vars_main}} | harmonized variables in the main file |
| {{n_source_vars}} | source variables in the deposits, every one mapped or skipped with a reason |
| {{n_crosswalks}} | crosswalk tables that hold every decision |
| {{n_checks}} | checks rerun on every build |

::: notes
The deck explains the method behind the public component of the IMPD: how {{n_surveys}} DANS deposits become one harmonized person-level file, and why the pipeline is built so that its own mistakes surface. Every number on these slides is computed from the repository at build {{build_id}}; the code examples are taken from the repository as it stands.
:::

# The problem and the principle

## {{n_surveys}} deposits, {{n_surveys}} sets of conventions

Different agencies, file structures, variable names, answer codes and missing-value conventions.

| Survey | Fieldwork and mode | Files | Missing values coded as |
|---|---|---|---|
| SPVA 2002 | Veldkamp / ISEO · PAPI, households | heads, persons, roster | system missing; labelled 9/99, 7/97 |
| SPVN 2003 | Veldkamp / ISEO · CAPI, households | heads, persons, roster | explicit -7 sysmis, -4, -3, -2 |
| LAS 2004/05 | Veldkamp–TNS NIPO / SCP · CAPI | one person file | explicit -7, -5, -3, -2, -9 |
| SIM 2006 | Veldkamp–TNS NIPO / SCP · CAPI | one person file | explicit -5 … -9; system missing = routing |
| SING 2009 | Veldkamp / SCP · CAPI · CBS-protected | one person file | labelled 7/97 don't know; 8/9/98/99 n.a. |
| SIM 2011 | GfK–Labyrinth / SCP · CAPI | one person file | explicit -5, -3, -2, -4, -1, -9 |
| SIM 2015 | TNS NIPO / SCP · CAWI, then CAPI | one person file | explicit -2, -3, -5, -1/98, -4, -6/96 |
| SIM 2020 | Labyrinth / SCP · CAWI, split half | one person file | explicit -5, -3, -2, -4, -6, -1; 9 in _kl |

::: notes
The point of the table is not the detail but the variety: {{n_survey_hh}} household surveys delivered as three linked files each, {{n_survey_flat}} person samples delivered as one file each, and no two deposits coding missing values the same way. {{n_source_vars}} source variables ({{n_skipped}} skipped as empty or constant) become {{n_vars_main}} harmonized variables for {{n_persons}} persons. Harmonization means that in the output the same thing has the same name, the same codes and the same missing scheme wherever it exists.
:::

## The harmonization is a set of tables, not a script

:::::: columns
::: column
Every decision is a row in a table, a **crosswalk**. Two independent programs, one in R and one in Stata, carry out those tables. To change a decision you change a row and rebuild; the data are never edited by hand.

- Anyone can read the mapping in a spreadsheet, without reading code
- Two engines applying the same tables can be compared cell by cell
- The checks and the codebook come from the same tables, so documentation and data cannot drift apart
:::
::: column
1. DANS deposits and questionnaire PDFs
2. Declarations, V() A() M(), and one settings file per survey
3. build.py writes {{n_crosswalks}} CSV crosswalks
4. The R engine and the Stata engine each apply them
5. The two builds are compared in every cell
6. Harmonized file, source companions, codebook, build identity
:::
::::::

::: notes
The usual way to harmonize surveys is a long recode script per survey. The IMPD does not do that: the substantive work is written as declarations that a builder turns into CSV tables, and the R and Stata programs are deliberately thin; they read the tables and apply them. Everything on the following slides follows from this choice.
:::

# Declaring the mapping

## Step 1 · Define the targets before mapping anything

:::::: columns
::: column
**Names**: theme_concept_qualifier, in English

`dem_sex` · `mig_yr_arr` · `edu_dipl_hi_lvl3` · `dem_prtnr_age_cat3`

Stems: dem, mig, lab, edu, rel, soc, lang, hlth, inc, att … {{n_vars_main}} variables in the main file; the glossary is crosswalks/name_glossary.csv.

**Value sets**: {{n_valuesets}} named code lists, shared across variables

```
vs("dur_cat4", [(1, "0-4 years"),
  (2, "5-9 years"), (3, "10-14 years"),
  (4, "15 years or more")])
```

Where surveys differ in detail, _cat holds the classes every survey can fill and _det keeps the survey's own detail.
:::
::: column
**Missing values**: one scheme for all surveys

- **.a** don't know
- **.b** refusal
- **.c** not applicable: routed past the question
- **.d** no information
- **.e** not collected: not in this survey, or not in this person's questionnaire

Each deposit's own codes are translated into these once, in its settings file (step 4).
:::
::::::

::: notes
Before any survey is mapped, the target is fixed: the naming pattern, the shared code lists, and the five-tag missing scheme. The value set is what makes a class like "5–9 years" mean the same thing wherever it appears; the missing scheme is what lets a user distinguish a routed-past cell from a refusal from an item the survey never had.
:::

## Step 2 · Declare a harmonized variable: V()

:::::: columns
::: column
From code/crosswalk_builder/variables.py:

```
V("dem_sex", "dem", "Sex",
  "GESLACHT", "GESLACHT",
  "sex", universe=U_ALL)

V("mig_transit", "mig",
  "Stayed in other countries
   between departure and
   arrival in NL",
  None, "ANDLAND", "yesno",
  universe=U_HEAD03,
  yn12=True)
```

**For a Stata user:** one V() line is the rename, recode and label lines for that variable in every survey, written once as a table row.
:::
::: column
- **"dem_sex", "dem"**: the target and its theme; unique, at most 32 characters, starting with its theme stem
- **"GESLACHT", "GESLACHT"**: the source variable in SPVA 2002 and SPVN 2003; None when a survey lacks the item. Later surveys: s15=, s20=, or sources={…}
- **"sex"**: the value set; every recode must land inside it
- **universe=**: who was asked; outside it a cell becomes .c
- **yn12=True**: source 1 = yes, 2 = no become 1/0
- **derive=, notes=, wording=**: a derivation rule in both engines; notes that reach the codebook and the data files
:::
::::::

::: notes
V() is the only way a harmonized variable comes into existence; everything the codebook later says about it (label, value set, universe, sources) traces back to this one declaration. The assertions inside V() are what makes it safe for a person: a typo in the stem, a duplicate name or an unknown value set stops the build with a message.
:::

## Step 3 · Attach a later survey to existing variables: A()

:::::: columns
::: column
From code/crosswalk_builder/variables_2004_2011.py:

```
A("svy_wgt", S11, "weegtot")
A("dem_has_chd", S11, "KINDEREN",
  yn12=True)
A("mig_transit", S09, "ANDLAND",
  pairs=[(1, 0), (2, 1)], u=U09G1,
  note="1 direct naar Nederland
  gekomen -> 0, 2 eerst elders
  gewoond -> 1")
SKIP(S11, "ONDERZOEK",
  "constant: all records belong
   to the main survey")
```
:::
::: column
- **pairs=**: the value map for this source: a code, a range lo-hi, a quoted string, or * for any other value, to a harmonized code or .a .b .c .d
- **u=**: this survey's universe, when it differs from the target's
- **SKIP()**: deliberately not harmonized, with the reason; nothing in a deposit is forgotten silently

What the builder wrote to crosswalks/value_map.csv, read from the file:

{{table: crosswalks/value_map.csv | target=mig_transit | columns=survey,source_var,source_value,target_value}}
:::
::::::

::: notes
A() is the function written for adding a wave: it attaches one source variable of a later survey to a target that already exists, with its recodes and its universe in one call. Notice the mig_transit line: the SING 2009 answer options are not yes/no, so the pairs invert the codes, and the note says why. The four value_map rows are what the two engines actually read.
:::

## One variable, every table that mentions it

:::::: columns
::: column
The `mig_transit` row of crosswalks/variable_map.csv:

{{record: crosswalks/variable_map.csv | target=mig_transit | columns=target,theme,label_en,valueset,src_spvn2003,src_sing2009,universe_en | cell=80}}
:::
::: column
Its row in crosswalks/universes.csv, where a survey's universe differs from the target's:

{{table: crosswalks/universes.csv | target=mig_transit | columns=survey,universe | labels}}

And in docs/routing_check.csv, as the gate of the SING 2009 arrival-year item:

{{table: docs/routing_check.csv | target=mig_yr_arr_cat5 | survey=sing2009 | columns=source_var,gate,n_values,n_outside,verdict | head=item,gate,values,outside,verdict}}
:::
::::::

::: notes
Everything the pipeline knows about mig_transit is in these tables, and these tables are all that the R and Stata engines read. The slide is pulled from the files at build time: if a row changes, the slide changes with it.
:::

## Step 4 · One settings file per survey

:::::: columns
::: column
code/crosswalk_builder/surveys/sing2009.py, abridged:

```
KW = "09"
LABEL = "SING 2009"
SURVEY = dict(svy_id=9, key="sing2009",
  structure="flat",
  file_main="SINGDANS veilig.por", ...)
MISSING_RULES = [
  dict(rule_type="label",
       match="^weet niet", target=".a"),
  dict(rule_type="label",
       match="^niet van toepassing|^nvt",
       target=".c")]
QUESTIONNAIRES = [("main", "....pdf",
                   "vk_script", None)]
LINK_BY_QNUM = True
```
:::
::: column
- **Discovered, not registered.** The builder reads every module in the folder and refuses one with a missing part or a duplicate key, survey id or KW.
- **Three kinds of missing rule.** An explicit code (-3), a pattern on the value label (^weet niet), or the SPSS-declared user-missing codes.
- **In Stata terms:** a master do-file that includes one do-file per survey. Adding a wave means copying the most similar module and filling in the form.
:::
::::::

::: notes
Every survey-level fact lives in one module: the registry entry that becomes a row of surveys.csv, the zip hash, the eligibility and weight text, the missing-value conventions, the questionnaire PDF and its parser, and, where the survey has them, routing rules, acquisition overrides, constructed variables and merge exceptions. A survey added later also keeps its variable declarations in this file, in a declare() function at the bottom.
:::

## A survey's conventions, as the engines read them

:::::: columns
::: column
The SING 2009 row of crosswalks/surveys.csv:

{{record: crosswalks/surveys.csv | svy_name=SING2009 | columns=svy_name,svy_year,zipfile,file_main,id_var,weight_var,sysmis_tag,missing_scheme | cell=72}}
:::
::: column
Its rows in crosswalks/missing_rules.csv, in the order the engines apply them:

{{table: crosswalks/missing_rules.csv | survey=sing2009 | columns=rule_type,match,target,note | head=rule,match,tag,note | cell=34}}
:::
::::::

::: notes
The settings file of the previous slide becomes these rows. The engines never see the Python: they read surveys.csv to find the deposit, the identifier and the weight, and missing_rules.csv to translate the survey's own missing codes into the five tags. A pattern on the value label ('^weet niet') catches every variable that uses that label, whatever its code.
:::

# Reading the questionnaires

## Step 5 · Reading the questionnaires: layouts, not meaning

:::::: columns
::: column
**What the parser does**

- pdftotext keeps the column layout; a state machine walks the text line by line
- Regular expressions recognise the typography of each layout: question headers, answer options, routing, instructions, split-half and randomisation markers
- {{n_parsers}} parsers for {{n_parsers}} layouts
- Best effort by design: every block keeps its full text, so the exact wording can be read where the structured fields fall short
:::
::: column
**Linking each data variable to its question**

1. A manual link, L()
2. The variable name printed in the questionnaire
3. A token match on the name
4. The question number in the data label
5. Constructed and registry variables: no question by design

SIM 2006: {{link_sim2006_qnum}} by number, {{link_sim2006_manual}} by hand · LAS: {{link_las2004_name}} by name, {{link_las2004_manual}} by hand · SIM 2020: {{link_sim2020_name}} by name, {{link_sim2020_manual}} by hand, {{link_sim2020_prefix}} by prefix.
:::
::::::

::: notes
Nothing here understands a question. The parser recognises the typography of a layout; the linker matches names and numbers. Every link whose data label and question text share no word of four letters or more is printed for a person to read. What this buys is that the wording of every item, in every survey, ends up in a table next to the harmonized variable, so the judgement about whether two items measure the same thing is made with both wordings in view, and recorded.
:::

## Same variable name, different question: mig_transit

The wording of one variable in crosswalks/wording.csv, parsed from the questionnaires, surveys in columns:

{{table: crosswalks/wording.csv | target=mig_transit | columns=survey,source_var,qid,question_text,answer_options | head=Survey,Source variable,Question number,Question read to the respondent,Answer options | labels | transpose | cell=150}}

::: notes
This is the standing documentation requirement made concrete: for every harmonized item whose wording changed across surveys, a table with surveys in columns. Here it shows why the SING 2009 mapping has to be inverted relative to SPVN 2003: the first option is the direct route, not "yes". The routing check two slides back confirms the mapping against the data: the arrival-year question went only to those now coded 1 ({{sing_transit_values}} values, {{sing_transit_outside}} outside the gate).
:::

## The codebook entry, generated: mig_transit

:::::: columns
::: column
From docs/codebook.md:

{{codebook: mig_transit | keep=Theme,Universe,Availability,Recodes | strip=\s*\(source code → harmonized code;[^)]*\) | cell=100}}
:::
::: column
Its frequency table, for the two surveys that carry it:

{{codebook-freq: mig_transit | columns=code,label,SPVN2003,SING2009}}
:::
::::::

::: notes
The entry is assembled from the tables of the previous slides and the built data: label and value set from variable_map, the universes, the availability per survey, the comparability class, the recodes from value_map, and the counts from the data. The full entry also carries the wording table and the per-survey reporter. Not collected (.e) is the count for the six surveys without the item; .c marks the SING 2009 respondents routed past it (the second generation).
:::

# Checking

## Step 6 · The builder refuses to finish when …

- **a source variable is unclaimed**: neither mapped by V() or A() nor listed by SKIP() with a reason
- **a target or a code is unknown**: a value-map row names a target that does not exist, or produces a code outside the value set
- **a row breaks the grammar**: a source value must be a code, a range lo-hi, a quoted string or *
- **a survey module is incomplete**: a required part is missing, or two modules share a key, survey id or KW
- **the label review fails** (step 9)

While a survey's crosswalk is being written, `IMPD_PARTIAL=1` turns the unclaimed-variable error into a list of what is still to map.

::: notes
The refusals are what make the declaration layer safe for a person rather than for a careful machine. Most of the time a mistake in a declaration is caught here, before any data are built, with a message naming the row.
:::

## Step 7 · Two engines, one set of tables

:::::: columns
::: column
R, code/R/00_setup.R (abridged):

```
apply_value_map <- function(x, maps) {
  star <- maps$source_value == "*"
  maps <- maps[order(star), ]
  for (i in seq_len(nrow(maps))) {
    sel <- !consumed &
      match_spec(x, maps$source_value[i])
    y[sel] <- to_target(maps$target_value[i])
    consumed[sel] <- TRUE
  }
}
```

Each engine reads value_map.csv and missing_rules.csv and knows nothing about any survey: first matching row wins, * rows last.
:::
::: column
Stata, code/Stata/00_setup.do (abridged):

```
program define impd_harmonize_var
  forvalues j = `j0'/`j1' {
    frame cw_vmap: local sv = ///
      source_value[`j']
    frame cw_vmap: local tv = ///
      target_value[`j']
    local c "`srcvar'==`sv' & _c==0"
    quietly replace `newvar'=`tv' if `c'
    quietly replace _c = 1 if `c'
  }
end
```

**PASS** Stata build identical to R build in every cell of every variable: {{n_cells}} cells. Agreement proves the tables were *executed* correctly, not that they are right.
:::
::::::

::: notes
Both excerpts are abridged from the real functions. The point is the symmetry: the same CSV rows, read by two programs written independently in two languages, and a cell-by-cell comparison at the end of every build.
:::

## Step 8 · Checks that re-derive from the released files

:::::: columns
::: column
**{{n_checks}} checks** on every build, computed from the output and the crosswalks, not from the pipeline's internal state:

- every value-map cell recounted from the source files
- universes against the data
- items asked of one respondent type only
- SIM 2020 split-half annotations against the half that carries values
- household-merge exceptions in both engines
- the label review, run again on the released crosswalks
- **routing gates against the data**: an item may carry values only where its printed condition holds
:::
::: column
| Routing check: source × gate pairs | |
|---|---:|
| tested | {{routing_pairs}} |
| hold exactly | {{routing_hold}} |
| hold with ≤ 10% exceptions, each listed | {{routing_exc}} |
| fail (above 10% the build stops) | {{routing_fail}} |
:::
::::::

::: notes
The checks deliberately start from the released files rather than from the build's own objects, so a bug in the pipeline cannot vouch for itself. The routing check is the one place where the questionnaire text is confronted with the data; it found parser mistakes (conditions printed before the header they govern) and it confirmed the mig_transit correction. The full table is docs/routing_check.csv.
:::

## What the run log says

The first lines of docs/run_log.md for build {{build_id}}, as the checks wrote them:

{{lines: docs/run_log.md | match=^- PASS | rows=12 | strip=^-\s* | width=64}}

::: notes
The run log is written by 99_checks.R from the released files, one line per check, and it is where a failed check would appear. These lines are read from the file at build time, so the deck shows the log of the build it names.
:::

## Step 9 · Reading every mapping against its labels

:::::: columns
::: column
**Why it exists**

SING 2009 ANDLAND had been given SPVN's rows: 1 → 1, 2 → 0. Both codes were valid, the counts plausible, R and Stata agreed, and every structural check passed. The inversion was found by reading the labels.

{{n_vmap_rows}} value-map rows read, both labels side by side · {{n_approvals}} signed approvals · any FAIL stops the build.
:::
::: column
**What it refuses**

- **POLARITY**: a negation on the affirmative code of a two-valued target, or the reverse
- **APPROVAL**: a two-valued target it cannot read, until a person signs it
- **REUSE**: the same source name mapped alike in two surveys whose labels differ
- **OVERLAP**: overlapping numeric range labels within a value set
- **CHANGED · ORPHANED · UNBOUND**: an approval is bound to the value read; if the mapping changes or disappears, the build fails again
:::
::::::

::: notes
This step was written in the restricted-component work and adopted by the public component in v0.4.7, then hardened in v0.4.8 and v0.4.9. It is the one check that does not rely on the data: it reads the mapping against the printed labels, and it exists so that an error of the mig_transit kind is prevented by the pipeline rather than found by review. The full reading table is docs/value_map_review.csv; approvals are signed in crosswalks/label_approvals.csv.
:::

## The label review, as recorded: mig_transit

:::::: columns
::: column
Its rows in docs/value_map_review.csv, source label beside target label:

{{table: docs/value_map_review.csv | target=mig_transit | columns=survey,source_value,source_label,target_value,target_value_label | head=Survey,Code,Source label,→,Label | labels | cell=45}}

The SING 2009 rows read as inverted yes/no: a POLARITY finding until a person signs them.
:::
::: column
The signed rows in crosswalks/label_approvals.csv:

{{table: crosswalks/label_approvals.csv | target=mig_transit | columns=source_value,target_value,reason,date | head=Code,→,Reason,Date | cell=70}}
:::
::::::

::: notes
The review table is the whole value map with both labels side by side; these four rows are the mig_transit part. The approval rows carry the value that was read, so if the mapping were changed again the approval would no longer match and the build would fail (CHANGED), and if the row were deleted the approval would be ORPHANED.
:::

## Three layers of trust

Each layer catches what the others cannot.

| Layer | Catches | Cannot catch |
|---|---|---|
| R against Stata, cell by cell | Execution errors: a crosswalk row applied wrongly by one engine | A wrong rule, which both engines apply faithfully |
| The {{n_checks}} checks | Rules that contradict the data: answers where the routing says there should be none | A plausible rule with the wrong meaning |
| The label review | Rules that contradict the labels: an inverted yes/no; a row copied from a survey where the codes mean something else | A wrong mapping between categories whose labels look compatible |
| Independent reconstruction | Definition errors that every internal check reproduces | — |

::: notes
The important column is the last one: what a layer cannot catch. Engine agreement cannot validate definitions, because a wrong table is reproduced faithfully by both. That is why independent reconstruction is part of the method rather than an extra: the reviewer's assurance run on v0.4.4 found zero valid-value differences over 90.6 million cells against its own reader of the eight deposits, and the restricted component rebuilds the variables from the CBS microdata.
:::

## Step 10 · Documentation generated, build identified

:::::: columns
::: column
**The codebook is generated** from the crosswalks and the built data, never written by hand: per variable the wording table, the universe per survey, the routing verdict, the comparability class, the recodes and the frequencies. HTML with a variable finder; Markdown and Word copies from the same source.

**Decisions and provenance.** docs/decisions.md records every substantive choice and correction with its evidence (§1–{{n_decisions}}). One source companion per survey keeps every original variable.
:::
::: column
**Every build has an identity**: a hash over the code and the crosswalks, printed in the codebook, the run log and this deck.

```
v{{version}} · build {{build_id}}
```

Cite the version together with the build identity. The data never enter the repository: anyone with the DANS deposits rebuilds them.
:::
::::::

::: notes
Because the SIM deposits are request-permission, the public deliverable is code, crosswalks and codebook rather than a data file. That makes the generated documentation and the build identity the things a user actually receives, and the reason the codebook cannot be allowed to drift from the data. This deck follows the same rule: its numbers come from docs/facts.csv, computed at every build.
:::

## Every correction is a numbered decision

:::::: columns
::: column
{{section: docs/decisions.md | 15 | chars=430}}
:::
::: column
The most recent sections of docs/decisions.md:

{{toc: docs/decisions.md | last=7 | cell=52}}
:::
::::::

::: notes
The decisions log is the narrative record: what was found, by whom, what changed and by how many cells. The excerpt is the opening of the section that recorded the mig_transit inversion; the table of contents is read from the file's headings. The log has {{n_decisions}} numbered sections at this build.
:::

# In practice

## Adding a survey is filling in a form, not writing a program

:::::: columns
::: column
1. Copy the DANS zip into Surveys/
2. Copy the most similar module to surveys/sim2025.py and fill in the form
3. Run build.py once (it registers the survey and stops), then 00a_source_metadata.R
4. A known questionnaire layout parses as it is; a new layout needs a parser, the one step that is programming
5. Write declare(): A(), V() or SKIP() for every source variable
6. Run build.py until nothing is unmapped; sign what the label review cannot read
7. run_all.R, then run_all.do; a section in decisions.md; commit
:::
::: column
```
# surveys/sim2025.py
# source names illustrative
def declare():
    from declare import A, V, SKIP
    A("dem_sex", "sim2025",
      "geslacht",
      pairs=[(1, 1), (2, 2)])
    A("lab_emp", "sim2025", "WERK",
      yn12=True, u="aged 15-74")
    V("lab_remote", "lab",
      "Working from home",
      s25="THUISWERK",
      valueset="remote4")
    SKIP("sim2025", "Volgnummer_oud",
      "duplicate id")
```

No change to the R or Stata code: they read the new survey from the crosswalks.
:::
::::::

::: notes
A new wave is one file in surveys/. The seven steps are the ones documented in docs/harmonization.md, which also has a plain-language introduction and a what-to-do-where table for collaborators who do not program.
:::

## What the code decides, and what it never does

:::::: columns
::: column
**The pipeline guarantees**

- Every source variable is mapped or skipped with a reason
- Every recode lands inside its value set
- R and Stata agree in every cell
- The printed routing holds in the data
- Each mapping agrees with its printed labels
- Documentation and data come from the same tables
:::
::: column
**The researcher decides**

- Whether two items, read side by side, measure the same thing
- How their answer options line up, and when they do not
- What is comparable, and how closely
- Which readings to sign in the label review

Read next: docs/harmonization.md · docs/codebook.html · docs/decisions.md
:::
::::::

::: notes
The closing point for co-authors: the machinery removes whole classes of error and makes every decision inspectable, but the substantive judgement, whether a 2025 item is the same as a 2020 item, is still made by a person, with the evidence laid out. That is the division of labour the design is built around.
:::

# Thank you
