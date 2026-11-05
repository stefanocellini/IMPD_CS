# 05_codebook.R : generate the codebook (Markdown + HTML) and the machine-readable variable index
# from the crosswalks and the built data.  Nothing in the codebook is typed by hand: labels, sources,
# notes and value maps come from crosswalks/, frequencies from data/derived/.
source(file.path(Sys.getenv("IMPD_ROOT", unset = getwd()), "code", "R", "00_setup.R"))

d  <- readRDS(P("data", "derived", sprintf("impd_public_v%s.rds", gsub("\\.", "_", IMPD_VERSION))))
d$svy_name <- factor(d$svy_name, levels = INCLUDED$svy_name)     # chronological survey order in every table
vm <- VARMAP %>% filter(include_main == 1, target %in% names(d))
SRCVARS <- read_cw("source_variables.csv")
svys <- INCLUDED$svy_name
THEMES <- c(id = "Identifiers", svy = "Survey design and interview", dem = "Demography and household position", hh = "Household characteristics (head-reported, merged onto all members)",
            geo = "Geography", mig = "Migration history", asy = "Asylum reception history", nat = "Nationality and legal status", int = "Civic integration",
            lang = "Language", edu = "Education", lab = "Labour market", inc = "Income and benefits", trn = "Transnational support to origin country",
            hous = "Housing and neighbourhood", hlth = "Health", soc = "Social contacts and participation", fam = "Family relations (NKPS module)",
            att = "Attitudes and values", pol = "Politics: voting, participation, institutional trust", med = "Media use",
            rel = "Religion", iden = "Ethnic identification", disc = "Discrimination", ret = "Return migration",
            cul = "Cultural and leisure participation", mob = "Mobility and transport", saf = "Safety and victimisation", tim = "Time use (LAS 2004/05 diary) and time orientation")
SKEY <- setNames(str_to_lower(svys), svys)        # survey name -> key
SLAB <- setNames(INCLUDED$label, str_to_lower(svys))                    # display names from the registry (surveys.csv)

esc <- function(s) { s <- gsub("&", "&amp;", s); s <- gsub("<", "&lt;", s); gsub(">", "&gt;", s) }
mdesc <- function(s) gsub("\\|", "\\\\|", s)
fmt_n <- function(x) format(x, big.mark = ",", trim = TRUE)
english_n <- function(n) if (n >= 1 && n <= 12) c("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve")[n] else as.character(n)

# ---- frequency / summary tables -------------------------------------------------------------
code_of <- function(x) ifelse(is_tagged_na(x), paste0(".", na_tag(x)), ifelse(is.na(x), ".", format(as.vector(unclass(x)), trim = TRUE, scientific = FALSE)))
freq_table <- function(v) {
  x <- d[[v]]; r <- vm[vm$target == v, ]
  codes <- code_of(x)
  tab <- as.data.frame(table(code = codes, survey = d$svy_name), stringsAsFactors = FALSE) %>%
    pivot_wider(names_from = survey, values_from = Freq, values_fill = 0)
  labs <- c(setNames(VALUESETS$label_en[VALUESETS$valueset == r$valueset], format(VALUESETS$code[VALUESETS$valueset == r$valueset], trim = TRUE, scientific = FALSE)),
            setNames(MISS_TAGS, paste0(".", names(MISS_TAGS))), "." = "System missing (not applicable / routed out)")
  tab$label <- labs[tab$code]; tab$label[is.na(tab$label)] <- ""
  tab$ord <- ifelse(grepl("^\\.", tab$code), 1e9 + match(tab$code, c(".", ".a", ".b", ".c", ".d", ".e")), suppressWarnings(as.numeric(tab$code)))
  tab %>% arrange(ord) %>% select(code, label, all_of(svys))
}
num_summary <- function(v) {
  x <- as.numeric(d[[v]])
  d %>% mutate(x = x) %>% group_by(survey = svy_name) %>%
    summarise(n = sum(!is.na(x)), mean = mean(x, na.rm = TRUE), sd = sd(x, na.rm = TRUE), min = suppressWarnings(min(x, na.rm = TRUE)),
              p25 = quantile(x, .25, na.rm = TRUE, names = FALSE), median = median(x, na.rm = TRUE), p75 = quantile(x, .75, na.rm = TRUE, names = FALSE),
              max = suppressWarnings(max(x, na.rm = TRUE)), .groups = "drop") %>%
    mutate(across(c(mean, sd, p25, median, p75), ~ round(.x, 2)), across(c(min, max), ~ ifelse(is.finite(.x), .x, NA)))
}
miss_summary <- function(v) {
  x <- d[[v]]
  tibble(survey = d$svy_name, code = code_of(x)) %>% filter(grepl("^\\.", code)) %>% count(survey, code) %>%
    pivot_wider(names_from = survey, values_from = n, values_fill = 0) %>% mutate(label = c(setNames(MISS_TAGS, paste0(".", names(MISS_TAGS))), "." = "System missing")[code])
}

# ---- markdown writer --------------------------------------------------------------------------
md <- character(0)
add <- function(...) { a <- list(...); md <<- c(md, if (length(a) == 1) a[[1]] else sprintf(...)) }   # single arg: literal (may exceed sprintf limits)
md_table <- function(df) {
  df[] <- lapply(df, function(c) mdesc(as.character(c)))
  c(paste0("| ", paste(names(df), collapse = " | "), " |"), paste0("|", paste(rep("---", ncol(df)), collapse = "|"), "|"),
    apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |")))
}
# ---- front matter: short visible text per section; reference detail in collapsible blocks (<details class='more'>),
#      rendered as such in the HTML, kept as plain paragraphs under a bold title in the Word copy (code/tools/md_to_word.py)
more_open  <- function(title) add(sprintf("\n<details class='more'><summary>%s</summary>\n\n", title))   # blank line after: Markdown inside the block
more_close <- function() add("\n</details>\n\n")
add("# IMPD public component — Codebook v%s", IMPD_VERSION)
add("\nThe **Integrated Migrant Panel Dataset (IMPD)**, public component, brings %s Dutch surveys of persons with a migration background, held between %s and %s, together in one harmonized person-level file: %s. It covers %s persons - the four largest origin groups (Turkish, Moroccan, Surinamese, Antillean/Aruban), refugee groups (Afghan, Iraqi, Iranian, former Yugoslav, Somali), Polish and Chinese migrants, and native Dutch reference samples - with %s variables on demography, migration history, language, education, work, income, housing, health, social contacts, family, attitudes, religion and identity. Every variable has an English name grouped by theme, one coding across the surveys, and missing-value codes that say why a value is missing. The surveys are repeated cross-sections: the same persons are not followed from one survey to the next. The file is rebuilt in R or Stata from the survey files archived at DANS; the survey data themselves are not redistributed.\n", english_n(nrow(INCLUDED)), min(INCLUDED$svy_year), max(INCLUDED$svy_year), paste(paste(head(INCLUDED$label, -1), collapse = ", "), "and", tail(INCLUDED$label, 1)), fmt_n(nrow(d)), fmt_n(nrow(vm)))
add("\nThis codebook documents that file: what it contains, how each variable was built from the source surveys, and how to use it. It serves two kinds of reader. **Researchers who want to analyse the data** should begin with *Start here*, which walks through the steps of an analysis and links to the reference sections. **Readers who want to check or reproduce a variable** will find the rules in sections 2-3 and the evidence per variable in section 5. Section 1 describes the surveys, sections 2-3 the conventions and the questionnaires; section 4 is the index of all variables; section 5 holds one collapsible entry per variable. The shaded *more detail* blocks open on a click; they hold the full rules and survey-by-survey specifics, so the visible text stays short.\n")
add("\n*Generated %s by `code/R/05_codebook.R` from the crosswalks in `crosswalks/` and the built data in `data/derived/`. **Build identity:** `%s` (sha256 of the crosswalks and the code, first 12 hex digits; also in `docs/run_log.md` and `docs/BUILD_ID`). Cite the build identity with the version: substantively different revisions can carry the same version number during development.*", format(Sys.time(), "%Y-%m-%d %H:%M %Z"), BUILD_ID)
add("\n## Start here\n")
add("For researchers who want to run an analysis with the IMPD: the six steps below take you from the DANS deposits to a reported result, and each points to the section that holds the reference material. `docs/example_analysis.md` follows the same steps on one question asked in all eight surveys, in R and Stata.\n")
add("- **Rebuild the data.** The built file cannot be redistributed: rebuild it from the DANS deposits with `code/R/run_all.R` or `code/Stata/run_all.do` (instructions in the README).")
add("- **Find measures.** Search the variable finder (HTML) or the [Variable index](#index) (section 4) and check that the measure exists in your surveys; `docs/codebook_variables.csv` is the same index as a table.")
add("- **Inspect the measures.** Open their [Variable descriptions](#descriptions) (section 5): the exact question per survey, how the value was obtained, the categories and recodes, who was eligible, and how comparable the surveys are. A comparability class is a reading aid, not a certification.")
add("- **Define your study population.** Section 1 ([What this dataset is](#what)) describes who was sampled in each survey; each measure's eligibility statement says who was asked. `svy_routing_mig`, `dem_eth`, `dem_gen` and `svy_resptype` identify the groups.")
add("- **Check the joint sample.** `impd_sample()` and `impd_universe()` (`code/R/impd_tools.R`, `code/Stata/impd_tools.do`) show per survey how many complete cases remain and why records drop out; they stop when a survey would disappear from the model unnoticed.")
add("- **Run and report the analysis.** State the population, the [weighting and pooling choice](#weights) and the final sample by survey.\n")
add("\n## 1. What this dataset is {#what}\n")
add("The public component covers the %s surveys below, in the versions archived at DANS. Two are **household samples** of migrant households in a set of municipalities, conducted by ISEO (SPVA 2002 and SPVN 2003, the latter for refugee groups); six are **person samples** drawn by CBS from the population register and conducted for SCP (LAS 2004/05 to SIM 2020), each with a native Dutch reference sample. This section lists the surveys, says what a row of the file is, and who was eligible in each survey and how it is weighted. The surveys covered:\n", english_n(nrow(INCLUDED)))
add(paste(md_table(INCLUDED %>% transmute(`svy_id` = svy_id, Survey = svy_name, Year = svy_year, Groups = groups, Access = sub("request_permission", "on request", access))), collapse = "\n"))
more_open("Survey design, deposit and fieldwork per survey")
add(paste(md_table(INCLUDED %>% transmute(`svy_id` = svy_id, Survey = svy_name, Year = svy_year, Design = mode, `DANS id` = dans_id, DOI = doi, Access = access, Fieldwork = fieldwork)), collapse = "\n"))
more_close()
add("\n### What a row is {#rows}\n")
add("\nEach row is a person (%s in total). In the two **household samples** (SPVA 2002, SPVN 2003) a row is a member listed in the household roster: the head of household (main questionnaire), another member aged 12+ (mini questionnaire), or a roster-only member who was not interviewed. In the six **person samples** (LAS 2004/05 to SIM 2020) a row is an individually sampled respondent; these surveys also include a **native Dutch reference sample** (`dem_eth` = 90), which skips the items asked only of persons with a migration background (`.c`). `svy_resptype` tells the record types apart:\n", fmt_n(nrow(d)))
GLOSS <- read_cw("name_glossary.csv")
rt_lab <- setNames(VALUESETS$label_en[VALUESETS$valueset == "resptype"], VALUESETS$code[VALUESETS$valueset == "resptype"])
add(paste(md_table(as.data.frame(table(Survey = d$svy_name, Type = rt_lab[as.character(as.vector(unclass(d$svy_resptype)))])) %>%
  pivot_wider(names_from = Type, values_from = Freq) %>% mutate(Total = rowSums(across(-Survey)))), collapse = "\n"))
more_open("Identifiers and household variables")
add("In the household samples (SPVA/SPVN) a row is a **household member listed in the survey roster**; `svy_resptype` distinguishes heads of household (main questionnaire), other members aged 12+ (mini questionnaire) and roster-only members (no interview; demographic information reported by the head), and household-level variables (`hh_*`) are taken from the head's record and merged onto every member. In the person samples (LAS, SIM, SING) every row is an **individually sampled respondent** (`svy_resptype` = 4) drawn from the population register; there is no household identifier (`id_hh` = `.e`) and the `hh_*` variables describe the respondent's own household (self-reported or from the registry, suffix `_reg`). These files include the **native Dutch reference samples** (`dem_eth` = 90, `dem_gen` = 0); items asked only to persons with a migration background are `.c` for them. `svy_id` numbers the surveys chronologically (SPVA 2002 = 5 ... SIM 2020 = 12; the numbering leaves room for surveys added later); `id_person` = `svy_key` x 10^11 + the record number of the deposit, where `svy_key` is the fieldwork year (immutable, so identifiers do not change when a survey is added); SIM 2006 and SING 2009 ship no respondent number and the row number of the deposited file is used. In the household samples `id_prtnr` links the head of household and the co-resident partner to each other's record (section 2).")
more_close()
add("\n### Eligibility and weights {#weights}\n")
add("\nThe IMPD public component is a set of **repeated cross-sections, not a panel**: the same person is not followed across surveys, and `id_person` identifies a record within one survey only (the 'panel' in the project name refers to the planned registry-linked component). Each survey has its own target population and its own weight, `svy_wgt`, which reproduces that population. The weights are therefore not comparable across surveys and are not a pooled population weight: when you pool surveys, decide how the waves contribute and say so (wave-specific estimates, or the wave as an explicit stratum, are often the clearer choice), and account for the clustering of household members in SPVA/SPVN (`id_hh`). Every analysis should state which surveys contribute, who was eligible in each, and which weight it uses.\n")
more_open("Eligible sample and weights per survey")
add(paste(md_table(INCLUDED %>% transmute(Survey = label, `Eligible sample / target population` = eligible, `Weights` = weights)), collapse = "\n"))
more_close()
more_open("Pooling, rescaling and design-based variances")
add("\nThe survey weights are survey-specific (different target populations, age ranges, designs and calibration models) and are not comparable across surveys: `svy_wgt` reproduces each survey's own target population and is not a pooled population weight. Within one survey the weight can be used as supplied. When surveys are pooled, the analyst decides how the waves contribute to the intended estimate and says so: rescaling the weights within survey (to equal sums, or to the sample sizes) only sets the relative contribution of the waves and does not define a common pooled population, because the target populations differ (section 1); wave-specific estimates, or the wave as an explicit stratum, are often the clearer choice. Account for the household clustering of SPVA/SPVN (`id_hh`) and the stratified designs of the person samples; no replicate or stratum variables are deposited, so design-based variances beyond the clustering are not available. The worked example in `docs/example_analysis.md` shows one such choice in full.\n")
more_close()
add("\n## 2. Conventions {#conventions}\n")
add("How variables are named and coded, what the missing-value codes mean, and what each variable entry in section 5 tells you. Subsections 2.1-2.3 are what most users need; 2.4-2.5 are reference.\n")
add("\n### 2.1 Variable names {#names}\n")
add("Names are `theme_concept` in English, built as `stem_[sub_]item[_suffix]`: the stem gives the theme (`dem_` demography, `lab_` labour market, `att_` attitudes ...), and items of a battery that share one question are numbered in questionnaire order (`att_gr01`, `lab_srch03`). The most frequent suffixes are `_cat` (harmonized classes) and `_det` (survey-specific detail), `_lvl3` (three education levels), `_15` (constant 2015 euro), `_reg` (registry-based) and `_txt` (open text). Every variable's label spells its name out.\n")
more_open("All theme stems, with the number of variables")
add(paste(md_table(tibble(Stem = names(THEMES), Theme = THEMES, Variables = map_int(names(THEMES), ~ sum(vm$theme == .x)))), collapse = "\n"))
more_close()
more_open("Naming rules and all suffixes")
add("Names are `stem_[sub_]item[_suffix]`, kept short with recurring abbreviations; items of a battery sharing one question stem are numbered in questionnaire order (e.g. `att_gr01`, `lab_srch03`) and the battery prefix says what the scale is. Suffixes: `_cat` harmonized classes, `_det` survey-specific detail, `_cat5` five classes incl. none, `_lvl3` three education levels (SCP laag/middel/hoog), `_15` constant 2015 euro, `_yr`/`_mo` year/month, `_yrs` duration in years, `_n` count, `_txt` open text, `_reg` registry-based (CBS) variable, `_cbs` CBS three-class migration background, a trailing number of points (`_4`, `_10`) the scale length where the same construct was asked on different scales.\n")
add("\nThe abbreviations used inside names are listed in `crosswalks/name_glossary.csv` (kind 'abbreviation'); every variable's label spells its name out.\n")
more_close()
more_open("Batteries: prefixes of numbered items")
add(paste(md_table(GLOSS %>% filter(kind == "battery") %>% transmute(Prefix = paste0("`", key, "`"), Items = map_int(key, ~ sum(map_int(str_split(.x, "\\s*/\\s*")[[1]], function(p) sum(str_detect(vm$target, paste0("^", p, "[0-9]+$")))))), Description = description)), collapse = "\n"))
more_close()
add("\n### 2.2 Codes and types {#codes}\n")
add("Where the surveys use incompatible detailed codings of the same concept, a variable ending in `_cat` holds the harmonized classes and one ending in `_det` keeps the survey-specific detail with the survey named in the value label (e.g. `edu_abr_hi_cat` / `edu_abr_hi_det`). Binary items are coded 1 = yes, 0 = no; multiple-response items 1 = mentioned, 0 = not mentioned; agreement items keep 1 = strongly agree … 5 = strongly disagree.\n")
add("Variable types: `cat` = coded categories with a value set (frequencies shown), `num` = quantity (summary statistics shown), `year` = calendar year, `str` = text, `id` = identifier: a dimensionless number that singles out a respondent, household or survey record; the codebook reports only coverage and uniqueness for identifiers, never descriptives.\n")
add("\n### 2.3 Missing values {#missing}\n")
add("Missing values carry a reason, as Stata extended missing values (R: `haven::tagged_na`) that survive the round trip between the `.dta` and `.rds` files. The distinction that matters most in analysis is between **`.c`** (the person was routed past the question) and **`.e`** (the survey, or this person's questionnaire, did not contain it):\n")
add(paste(md_table(tibble(Code = paste0(".", names(MISS_TAGS)), Meaning = MISS_TAGS, `In short` = c("The respondent did not know.", "The respondent refused or gave no answer.", "The question did not apply: the person was routed past it (including the native reference sample for items asked only of persons with a migration background, and the other half of the SIM 2020 split-half questionnaire).", "No information for another or unknown reason ('geen informatie', 'onbekend', unexplained empty cells).", "The variable is not in this survey, or the item was not in this person's questionnaire (e.g. roster-only members, or a heads-only item for other household members)."))), collapse = "\n"))
add("\nPlain system-missing (`.`) occurs only in SPVA/SPVN, whose files do not separate 'routed out' from 'not applicable'.\n")
more_open("Which source codes map to which missing tag, per survey")
add("The full assignment rules, survey by survey:\n")
add(paste(md_table(tibble(Code = paste0(".", names(MISS_TAGS)), Meaning = MISS_TAGS,
  `Assigned when` = c("Source code labelled 'weet niet' / declared don't-know code (SPVN: -3, 0 in year/month items, 7, 97/997/9997; LAS 2004/05: -3, -4, 999 'weet niet, geen informatie'; SIM 2006: -3; SING 2009: labelled 'weet niet'; SIM 2011: -3; SIM 2015: -3; SIM 2020: -3, -6)",
                      "Refusal / no answer: SPVN -2; LAS -2 and 'wil niet zeggen'; SIM 2006 -2; SING 'geen antwoord' / 'wil niet zeggen'; SIM 2011 -2; SIM 2015 -1 and 98 'wil niet zeggen'; SIM 2020 -2 'wil niet antwoorden' and -4 'geen antwoord'",
                      "Not applicable: routed past the question - LAS -5/-7/-9 and 'niet gesteld'; SIM 2006 -5, -7 'niet in vragenlijst', -9; SING 'niet van toepassing'; SIM 2011 -5, -9 'nvt: autochtoon' and -1 (undocumented, used where a question was not asked); SIM 2015 -2 'blanc' and -5; SIM 2020 -5 'nvt binnen vragenlijst'; SIM constructed/coarsened variables where the routing question says so (derive kl9_route); native reference sample for migrant-only items; SPVA/SPVN: explicit 'not applicable' codes only. In LAS 2004/05, SIM 2006 and SING 2009 every remaining system-missing value is .c (the files leave routed-out cells empty)",
                      "No information: source code labelled 'geen informatie'/'missing'/'onbekend', SPVN -4, SIM 2006 -4/-8, SIM 2011 -4, SPSS user-missing codes declared in the SPVA file (9/99/999/9999), SIM 2020 code 9 'Anders/Refusal/Don't know' of the coarsened (_kl) variables, SIM 2015 -4/-6 in constructed variables, and any remaining system-missing value in the SIM 2011, 2015 and 2020 files",
                      "Variable not in this survey, or item not in this respondent's questionnaire: in SPVA/SPVN a heads-file item for other members, any item for roster-only members, and the items of `crosswalks/asked_to.csv` that the persons file holds for both types but only one type was asked (main-questionnaire blocks L-M of SPVA 2002 for other members; mini-questionnaire items for heads). The split-half block of the other group in SIM 2020 is .c, not .e"))), collapse = "\n"))
add("\nPlain system-missing (`.`) occurs only in SPVA/SPVN and means the item was routed out or not applicable in the source (those files do not allow the two to be separated); in the person-sample surveys every missing value is tagged, with the survey-specific tag for untagged empty cells recorded in `crosswalks/surveys.csv` (`sysmis_tag`: .c for LAS 2004/05, SIM 2006 and SING 2009, whose files only leave routed-out cells empty; .d for SIM 2011-2020, where empty cells also arise from item non-response in constructed variables). Rules: `crosswalks/missing_rules.csv` (per survey: code rules, label rules, declared-code rules); the declared SPSS user-missing codes per variable: `crosswalks/source_missing.csv`; the routing rules for SIM constructed variables: `code/R/03_derive.R` (kl9_route).\n")
more_close()
add("\n### 2.4 What a variable entry tells you {#entries}\n")
add("Every entry in section 5 states whom the value describes (**Subject**: self, partner, child, household ...), who supplied it in each survey (**Reported by**: the respondent, the head of household, the interviewer, the registry ...), whether each survey collected or derived it (**Availability**), and a **Comparability** class over the surveys that carry it (exact, coarse or approximate match, mixed provenance, construct-defined, derived, wave-specific). The class is a reading aid, not a certification: it says whether the texts and codes agree, not whether mode, context or population do. A wording table then shows, survey by survey, the question and how it was asked (section 3.1).\n")
more_open("Subject, reporter, availability and comparability classes in full")
add("Every variable entry states whom the value describes (`Subject`: self, partner, child, selected child, parent, household, interview, identifier), who supplied it per survey (`Reported by`: the respondent; the head of household for roster members or household items; the partner's own record through the roster link `id_prtnr` in SPVA/SPVN; the interviewer; the sample frame or registry; the data producer for constructed variables), how each survey contributes (`Availability`: collected, derived, derived from the roster link, not collected) and a comparability class over the surveys that carry it (`Comparability`: exact match = same question and answer options in every respondent-facing source, or the same interviewer instruction and recording categories where the value is interviewer-acquired; coarse match = harmonized classes of finer survey-specific codings; approximate match = same construct with different wording or scales, read the wording table; mixed provenance = the information is obtained differently across surveys - a respondent report in some, an interviewer recording, a registry field or a constructed variable in others - so the measurements are not equivalent by wording; construct-defined = constructed/registry in every survey; derived; wave-specific; administrative). How each source was obtained is stated per source in the wording table (`How obtained`: respondent report, proxy report about a partner/child/parent, interviewer recording without asking, interviewer assessment, interviewer observation, interview administration, registry/sample data, derived/coded; `crosswalks/wording.csv` columns `acquisition`, `respondent_facing`, `supplied_by`, `describes`; declared cases in `crosswalks/acquisition_overrides.csv`). The class is seeded mechanically from the wording components and the variable's construction (`status` auto) and can be overridden by a reviewer in `crosswalks/comparability_review.csv` (`status` reviewed); the whole inventory is `docs/comparability.csv`. A class is a reading aid, not a certification: 'exact match' says the texts and codes agree, not that mode, context or population do.\n")
more_close()
more_open("Partner variables in the household samples (SPVA 2002, SPVN 2003)")
add("SPVA 2002 and SPVN 2003 interview the head of household and list the partner as a record of her/his own; `id_prtnr` links the two (the other head/partner member of the roster, `dem_poshh` 0/1; `.c` = no co-resident partner record, `.d` = other household members, whose partner is not identifiable). Two kinds of variable are derived from it. (a) The partner characteristics that the person samples ask as proxy questions (`dem_prtnr_sex`, `dem_prtnr_age*`, `dem_prtnr_brthcntry`, `dem_prtnr_eth`, `dem_prtnr_gen`, `edu_prtnr_lvl3`, `dem_prtnr_emp`, `dem_prtnr_hrs`, `mig_yr_arr_prtnr`, `mig_reason_prtnr`) are copied from the linked partner's own record where the survey did not ask them, so their acquisition and reporter are those of the base field (`dem_prtnr_sex` carries the interviewer's recording of the partner's sex, `edu_prtnr_lvl3` the coded diploma): `.c` = no co-resident partner; `.d` = other household members, and partners listed in the roster but not interviewed where the base item needs an interview - roster demography (sex, age, country of birth) is available for them, and the base field's own missing tags are kept. (b) The relationship indicators `dem_has_prtnr` and `dem_prtnr_cores` are computed from the link and the living-apart-together question, including for persons without a partner record: co-resident link -> 1/1, LAT partner without a link -> 1/0, identifiable head/partner without link or LAT partner -> 0/`.c`, other members -> `.d`. Each variable's wording table states its own rule. Children are not linked (the person samples describe one selected child or children in general; roster children are rows of their own, summarised by `hh_nchd*`).\n")
more_close()
more_open("Country codes, municipalities, occupations, industries and euro amounts")
add("**Country codes** (`dem_brthcntry*`, `dem_prtnr_brthcntry`, `mig_tr_cntry*`) follow the Dutch GBA/BRP *Landentabel* (Tabel 34, RVIG; `External/Country codes/landentabel34.csv`), with project codes 9901 other Africa, 9902 other Asia, 9903 other Europe, 9998 unidentifiable name, 9999 other country; 7011 is used as an aggregate for the (former) Netherlands Antilles, Aruba and the Caribbean Netherlands. In SIM the public files contain no country of birth: `dem_brthcntry` is derived from origin group x generation under the CBS definition (first generation = born in the origin country, second generation = born in the Netherlands). **Municipalities** carry the CBS gemeentecode of the 2006 list (SPVA/SPVN only; SIM gives urbanisation of the municipality, `geo_urb_reg`). **Occupations** are SBC-92 codes and **industries** SBI-93 codes as coded by ISEO; SIM 2015 industry is SBI 2008 (`lab_ind_sbi08`). **Euro amounts** are nominal as collected (SPVA/SPVN asked in euro); `*_15` versions are deflated with the CBS CPI (70936ENG, 2015 = 100; factors 2002: %.4f, 2003: %.4f, 2005: %.4f for the SIM 2006 transfer amounts that refer to calendar year 2005, 2009: %.4f). SIM incomes are registry income bands (`inc_*_reg`, nominal euro of the income year) or self-reported bands and are not deflated.\n",
    100 / CPI$cpi_2015[CPI$year == 2002], 100 / CPI$cpi_2015[CPI$year == 2003], 100 / CPI$cpi_2015[CPI$year == 2005], 100 / CPI$cpi_2015[CPI$year == 2009])
more_close()
add("\n### 2.5 Source files, access and reproducibility {#files}\n")
add("Alongside the harmonized file, each survey has a **companion source file** with every original variable (prefix `src_`, Dutch labels, original codes), keyed by `id_person`, so any harmonization step can be checked or redone. The harmonized file itself **cannot be redistributed**, because six of the eight deposits are DANS *request permission* files: the public deliverable is the code, the crosswalks and this codebook, from which anyone with access to the deposits rebuilds the data. Every rule lives in the CSV crosswalks and is executed identically by the R and Stata pipelines.\n")
more_open("Companion source files and weights")
add("**Companion source files** `impd_public_v%s_source_<survey>.dta/.rds` contain every original variable of each survey (prefix `src_`, Dutch labels, original codes) keyed by `id_person`, so any harmonization step can be audited or redone. In the household surveys a field that occurs in more than one deposit file (heads, interviewed persons, roster) is kept once, with the value of the most detailed file (heads > persons > roster); where the files disagree - in SPVN 2003, 37 roster-age cells of 17 persons - the companion holds the chosen value only, and the per-file frames in `data/interim/` are the place to study the disagreement. **Weights** (`svy_wgt`) are the survey-specific weights supplied with the files: ISEO/SCP design weights for SPVA/SPVN, CBS calibration weights scaled to the population for SIM (SIM 2015 also ships an alternative model, `svy_wgt_alt`); they are not comparable across surveys (section 1, weights).\n", gsub("\\.", "_", IMPD_VERSION))
more_close()
more_open("Access, redistribution and the SING 2009 partial release")
add("**Access and redistribution.** %s are open-access DANS deposits; %s are DANS *request permission* deposits (SCP/CBS files under the DANS licence); a harmonized file that contains their content therefore cannot be redistributed openly. The public deliverable of the IMPD is the code, the crosswalks and this codebook: anyone with access to the %d DANS deposits rebuilds the data file with `code/R/run_all.R` or `code/Stata/run_all.do`. SING 2009 is a partial release: the deposit contains only the questions listed in its READ ME, with years and durations coarsened into classes (hence the `_cat` variants that exist for SING only) and with statistical protection applied to some variables - real values replaced by 'don't know' / 'not applicable' / 'other' codes for a few respondents (sex, marital status, origin group, generation, year of marriage), household size and number of children top-coded at 6 - so that the resulting missing and 'unknown' values are protection, not non-response (section 3, release).\n",
    paste(INCLUDED$label[INCLUDED$access == "open"], collapse = " and "), paste(INCLUDED$label[INCLUDED$access != "open"], collapse = ", "), nrow(INCLUDED))
more_close()
more_open("Reproducibility and the value-map review")
add("**Reproducibility.** `code/R/run_all.R` (R) and `code/Stata/run_all.do` (Stata) rebuild everything from the DANS zip files in `Surveys/` using only the CSV crosswalks; `code/crosswalk_builder/` documents how the crosswalks themselves were authored. Every value-map row can be read with its source label against the target label in `docs/value_map_review.csv`; the rows that the automatic label check cannot read by itself (two-valued targets with a non-yes/no source label, rows copied across surveys whose labels differ, range labels) carry a signed reading in `crosswalks/label_approvals.csv`, bound to the value that was read, and the builder refuses a crosswalk set with an unsigned or changed row (`code/tools/value_map_review.py`; check 16). Decisions and known limitations are listed in `docs/decisions.md`; the run log in `docs/run_log.md`.\n")
more_close()
add("\n## 3. Survey designs, questionnaires and randomisation {#designs}\n")
add("Harmonization aligns codes, not questions: the same concept was asked in different words, modes and orders across the eight surveys. This section explains how to read the **wording tables** that document this per variable in section 5 (3.1), and describes the **design of each survey** - interview mode, question order and randomisation, routing, languages and what the deposit releases (3.2).\n")
add("\n### 3.1 Reading the wording tables {#wording}\n")
add("Each variable entry in section 5 has a wording table with one column per survey. It gives the source variable, **how the value was obtained** (respondent report, proxy report about a partner or child, interviewer recording, registry or derived), the **question or statement as shown or read to the respondent**, the answer options, who was eligible, and the **routing translated into harmonized variables** (e.g. `svy_routing_mig` in {1}), with a check of whether the data agree. Above the table, a `Wording` line compares the surveys component by component; 'differs' is a prompt to read the table, not a verdict that the measures are incomparable. The texts are parsed from the questionnaires in the DANS deposits.\n")
more_open("What the rows of the wording table contain")
add("Harmonization aligns codes, not questions: the per-variable **wording tables** in section 5 show, survey by survey, the source variable and its questionnaire reference, **how the value was obtained** (`How obtained`: respondent report; proxy report about a partner, child or parent; interviewer recording without asking; interviewer assessment; interviewer observation; interview administration; registry/sample data; derived/coded), who supplied the information and whom it describes, the introduction or lead-in, the **question or statement shown or read to the respondent** (the battery statement once, in its own row; for the formats that print the statement inside the question, the lead-in moves to the introduction row), the interviewer recording or assessment instruction (exact text, kept apart from the prompt), the response or recording categories, the response format, the source definition or derivation for registry and constructed sources, the value labels in the data file (the data label is printed as a gloss next to the source variable), the eligible records, the **routing in terms of harmonized variables** (the gate variable and the values under which the item was asked, with the empirical verdict; 'none printed' when the questionnaire prints no eligibility condition for the item; 'printed condition not mapped' when it prints one that no rule translates), and any split-half or randomisation note. The 'Response format' row holds numeric bounds, widgets and units, which are not spoken text. Curated notes flag changes that matter for comparability (e.g. 'allochtoon' -> 'persoon met een migratieachtergrond', changed answer scales).\n")
more_close()
more_open("Respondent-facing and interviewer-acquired sources")
add("A source is respondent-facing only when a prompt was shown or read to the respondent: an item the interviewer records silently ('noteer stilzwijgend geslacht'), rates ('stel vast hoe goed de respondent Nederlands spreekt'), observes or completes about the interview, a [SAMPLE DATA] field and a coded variable are not, and their prompt row says so explicitly ('Not applicable - ...'; 'Question text not located' is a different state). Those classifications are phrase-based and narrow - an 'ENQ.:' note attached to a real question leaves the question respondent-facing - with declared cases in `crosswalks/acquisition_overrides.csv` and assertions in the builder and the renderer (no 'do not ask' / 'record silently' / assessment / sample-data item is respondent-facing; recording categories survive instruction-only blocks; no procedure or English description is printed as a prompt; no statement is printed twice).\n")
more_close()
more_open("How routing conditions are translated and checked against the data")
add("The 'Routing (harmonized variables)' row translates the printed routing condition into the harmonized variable that carries the same information and the values under which the question was asked - by hand-written rules for the recurring conditions (`crosswalks/routing_rules.csv`: e.g. 'INDIEN ALLOCHTOON' -> `svy_routing_mig` in {1}, 'INDIEN MOSLIM' -> `rel_den_cat` in {2}) and automatically for conditions that reference a question number ('IF [ Q1450 , 1 ]', 'ASK ONLY IF not Q235=1', 'INDIEN JA:' after the preceding question): the referenced question is looked up in the same questionnaire, its codes are translated with the value map (negations taken over the observed source codes, don't-know/refusal codes as missing-tag gates, numeric comparisons kept), and the gate is stated on the harmonized variable; conditions that combine alternatives or compare two questions are not translated and say so; each gate is then verified against the data (per source variable, `docs/routing_check.csv`): 'holds in the data' means no value lies outside the gate, 'holds with exceptions' gives the count of values outside it (the data as delivered; e.g. a few second-generation respondents with a year of arrival), and a printed condition that the data contradict (a grid condition governing a sibling item, a constructed variable filled for everyone) is listed as 'not applied' with the reason (`crosswalks/routing_exceptions.csv`). A gate with more than 10% of its values outside fails the build (check 11), so users can reproduce the routing with variables of the harmonized file. The printed condition itself is not a table row: it is quoted inside the routing cell only when no rule translates it, and the full text (with skip instructions such as '2 -> naar 1519', text fills and display settings) stays as provenance in `crosswalks/wording.csv`, columns `routing`, `routing_skip`, `routing_script`. The same routing summary is given per variable above the table ('Routing (harmonized variables)'), survey by survey.\n")
more_close()
more_open("How the Wording line compares the surveys")
add("The `Wording` line compares the surveys that carry the item **by acquisition family and component**: over the respondent-facing sources the question or battery statement (compared at the same level in every format), the introduction/lead-in, the answer options, the instructions and the routing; over the interviewer-acquired sources the instruction and the recording categories ('Procedure/scale'); registry and constructed sources are named and compared through their definitions, not their wording; and when the families differ between surveys the line says that the measurements are not equivalent by wording. Each component is reported as identical, identical except group fill, differs (naming the surveys that share each version), none printed, or printed in one survey only. Case, punctuation and group fills (<groep>, <?>, '*? HERKOMST') are ignored; other parentheticals are kept, so a changed qualifier shows as a difference. 'differs' is a prompt to read the table: it signals that the texts are not the same, not that the measurement is incomparable, and 'identical' for the question does not certify equivalence when options, introduction or administration differ.\n")
more_close()
more_open("Where the question texts come from, and caveats per survey")
add("The texts are parsed from the questionnaire PDFs in the DANS deposits (`crosswalks/questionnaire_items.csv`; the full printed block of every item is kept as provenance in `crosswalks/wording.csv`, column `block_text`). Caveats: the SPVA 2002 texts are those of the Turkish-group main questionnaire deposited with the data (the Moroccan, Surinamese, Antillean and native versions differ only in the group fills, e.g. 'Turken' / 'Turkse'), and the SPVN 2003 texts those of the main questionnaire; the mini questionnaire for household members repeats the items marked '+G' in those codebooks. SIM 2015 texts are the CAWI version (the parallel CAPI question id is given). The LAS 2004/05 questionnaire is appendix 1a of the fieldwork report deposited with the data (`Bijlage 3 Veldwerkverslag`); the SIM 2011 questionnaire is the hardcopy of the CAPI script (appendix g). SIM 2006 and SING 2009 are deposited as Veldkamp CAPI script printouts that print no variable names: their items are linked to the data through the question number that the data labels carry ('Vraag 965: ...'), and for multiple-response questions through the option order (match 'qnum' / 'manual' in `crosswalks/wording.csv`). Coded and constructed variables (e.g. the SPVA/SPVN 'MAXDIP', 'BERBEV', 'INKOMEN2' family) and registry variables have no question text; where the codebook prints such a variable name after a question block, the table says so. The parse of the two-column SPVA 2002 codebook is less clean than that of the other three: grid scales appear as 'grid scale (labels in the data file)', and the printed answer codes of multi-line options were re-aligned by order. Fills such as <GROEP>, <land van herkomst> or <?> stand for text inserted per origin group by the survey software. Everything in the tables is data: `crosswalks/wording.csv`, `crosswalks/wording_notes.csv`, `crosswalks/universes.csv`, `crosswalks/questionnaire_constructed.csv`.\n")
more_close()
add("\n### 3.2 Survey designs {#surveydesign}\n")
add("All eight surveys were face-to-face interviews except SIM 2015 (web first, then face-to-face) and SIM 2020 (mostly web). Randomisation matters in three surveys: SING 2009 asked one item to a random half, SIM 2015 randomised the item order within some batteries, and SIM 2020 used a **split-half questionnaire** (`svy_split`: %s respondents in half A, %s in half B; items of the other half are `.c`) as well as randomised item order. Open a survey for its design features (`crosswalks/questionnaire_design.csv`).\n", fmt_n(sum(as.vector(unclass(d$svy_split)) == 1, na.rm = TRUE)), fmt_n(sum(as.vector(unclass(d$svy_split)) == 2, na.rm = TRUE)))
for (k in unique(QDESIGN$survey)) {
  more_open(sprintf("%s - %s", SLAB[[k]], sub(";.*$", "", INCLUDED$mode[str_to_lower(INCLUDED$svy_name) == k])))
  for (j in which(QDESIGN$survey == k)) add("- *%s*: %s", QDESIGN$aspect[j], QDESIGN$text[j])
  more_close()
}


add("\n## 4. Variable index {#index}\n")
for (th in names(THEMES)) {
  sub <- vm %>% filter(theme == th); if (!nrow(sub)) next
  add("\n### %s (`%s_`)\n", THEMES[[th]], th)
  tab <- sub %>% transmute(Variable = sprintf("[`%s`](#%s)", target, target), Label = label_en, Type = type)
  for (k in KEYS) tab[[SLAB[[k]]]] <- gsub("|", " | ", sub[[paste0("src_", k)]], fixed = TRUE)
  tab$Universe <- sub$universe_en
  add(paste(md_table(tab), collapse = "\n"))
}

# ---- wording table per variable ---------------------------------------------------------------
# normalisation for the component-wise wording comparison: case and punctuation are ignored, group fills (<groep>, <?>,
# *? HERKOMST, <andere>) are replaced by one fill token so that per-group versions compare equal, interviewer instructions in
# parentheses '(ENQ.: ...)' and bracketed script are removed; other parentheticals (qualifiers, definitions) are kept
norm_q <- function(x) {
  x <- str_to_lower(x)
  x <- gsub("\\((enq|int)\\.?:[^)]*\\)|\\[[^]]*\\]", " ", x)
  x <- gsub("<[^>]*>|\\*\\? ?herkomst(land)?|\\[\\?\\]", " <fill> ", x)
  x <- gsub("vraag [0-9]+[:.]", "", x)
  x <- gsub("[^a-z0-9<>]+", " ", x); str_squish(x)
}
norm_opts <- function(x) { x <- str_to_lower(x); x <- gsub("\\s*\\(enq[^)]*\\)", "", x); x <- gsub("[^a-z0-9;=]+", " ", x); str_squish(x) }
norm_i <- function(x) { x <- str_to_lower(x); x <- gsub("<[^>]*>|\\[\\?\\]", " <fill> ", x); x <- gsub("[^a-z0-9<>]+", " ", x); str_squish(x) }   # instructions: parentheses kept
# verdict on one component across the spoken-question rows: identical / identical except group fill / differs / n.a.
component_flag <- function(vals, surveys) {
  keep <- vals != ""
  if (sum(keep) < 2) return(NA_character_)
  v <- vals[keep]; sv <- surveys[keep]
  if (n_distinct(v) == 1) return("identical")
  v0 <- str_squish(gsub("<fill>", "", v))
  if (n_distinct(v0) == 1) return("identical except group fill")
  grp <- split(sv, v0); grp <- grp[order(-lengths(grp))]
  paste0(sprintf("differs (%s)", paste(map_chr(grp, ~ paste(unique(SLAB[.x]), collapse = "/")), collapse = " vs ")),
         if (any(grepl("<fill>", v))) "; contains an unresolved fill" else "")
}
# routing gates with their empirical verdict (docs/routing_check.csv, written by 04_build): 'holds' = no value outside the
# gate; 'holds with exceptions' = some values outside (counts given; data as delivered); a printed condition that does not
# gate the item (routing_note) is reported with its reason
RCHECK <- if (file.exists(P("docs", "routing_check.csv"))) read_csv(P("docs", "routing_check.csv"), show_col_types = FALSE, col_types = cols(.default = "c")) else tibble()
GATE_SEP <- regex(";\\s*(?=[a-z0-9_]+ (in \\{|is \\{|[<>]=? ))")     # a ';' inside a gate description is not a separator
gate_cell <- function(t, k, sv, gates, note, cond = "") {
  out <- character(0)
  if (!is.na(gates) && gates != "") {
    for (g in str_split(gates, GATE_SEP)[[1]]) {
      m <- str_match(g, "^([a-z0-9_]+) (in \\{[0-9,]+\\}|(?:>=|<=|>|<) -?[0-9.]+|is \\{[.a-e,]+\\}) \\((.*)\\)$")
      txt <- gsub("^([a-z0-9_]+) ", "`\\1` ", g)
      txt <- sub(" \\(from (VRAAG |Q)?([0-9A-Za-z() ]+?) `([^`]+)`[^)]*\\)", " (translated from the printed condition on `\\3`)", txt)
      rc <- if (nrow(RCHECK) && !is.na(m[1, 1])) RCHECK %>% filter(target == t, survey == k, source_var == sv, gate == m[1, 2]) else tibble()
      if (nrow(rc)) {
        v <- rc$verdict[1]
        gm <- suppressWarnings(as.integer(rc$n_gate_missing[1])); gm <- if (is.na(gm) || gm == 0) "" else sprintf("; %s of them from records without a value on the gate variable, which the printed condition admits", gm)
        txt <- paste0(txt, if (v == "holds") sprintf(" - holds in the data (%s values%s)", rc$n_values[1], gm)
                           else sprintf(" - holds with exceptions: %s of %s values outside the gate (gate values %s)%s", rc$n_outside[1], rc$n_values[1], rc$outside_gate_values[1], gm))
      }
      out <- c(out, txt)
    }
  }
  if (!is.na(note) && note != "") out <- c(out, gsub("([a-z0-9_]+) in \\{", "`\\1` in {", note))
  if (!length(out)) out <- if (is.na(cond) || cond == "") "none (no eligibility condition printed for this item)" else sprintf("printed condition not translated into a harmonized variable: '%s'", str_trunc(cond, 160))
  paste(out, collapse = "; ")
}
# per-variable summary of the routing gates by survey (the researcher's view: which harmonized variables reproduce the routing)
routing_summary <- function(t) {
  w <- WORDING %>% filter(target == t, as.integer(respondent_facing) == 1 | grepl("^interviewer|^interview", acquisition))
  if (!nrow(w)) return("")
  w <- w[order(match(w$survey, KEYS)), ]
  g <- map_chr(seq_len(nrow(w)), function(j) {
    gates <- str_split(w$routing_gates[j], GATE_SEP)[[1]]; gates <- gates[gates != ""]
    if (!length(gates)) return(if (w$routing[j] == "") "none printed" else "printed condition not translated")
    paste(gsub("^([a-z0-9_]+) (in \\{[0-9,]+\\}|(?:>=|<=|>|<) -?[0-9.]+|is \\{[.a-e,]+\\}).*$", "`\\1` \\2", gates), collapse = " & ")
  })
  lab <- ifelse(ave(seq_len(nrow(w)), w$survey, FUN = length) > 1, paste0(SLAB[w$survey], " `", w$source_var, "`"), SLAB[w$survey])   # several sources in one survey: name them
  grp <- split(lab, g); grp <- grp[order(match(names(grp), g))]
  paste(sprintf("%s (%s)", names(grp), sapply(grp, function(x) paste(unique(x), collapse = ", "))), collapse = "; ")
}
# acquisition families (crosswalks/wording.csv: acquisition / respondent_facing / supplied_by / describes, v0.4.3)
acq_family <- function(a) ifelse(grepl("^(respondent report|proxy report)", a), "respondent",
                          ifelse(grepl("^interviewer|^interview administration", a), "interviewer",
                          ifelse(grepl("^linked partner record", a), "linked partner record",
                          ifelse(grepl("^relationship-derived", a), "relationship-derived",
                          ifelse(grepl("^registry", a), "registry", ifelse(grepl("^derived", a), "constructed", "unknown"))))))
ACQ_ABSENT <- c("linked partner record" = "Not applicable - taken from the linked partner's own record (see the source definition row)",
                "relationship-derived (roster link and the living-apart-together question)" = "Not applicable - computed from the roster link and the LAT question (see the source definition row)",
                "interviewer recording (not asked)" = "Not applicable - recorded by the interviewer without asking (see the instruction row)",
                "interviewer assessment" = "Not applicable - interviewer assessment (see the instruction row)",
                "interviewer observation" = "Not applicable - interviewer observation (see the instruction row)",
                "interview administration" = "Not applicable - completed by the interviewer (interview administration; see the instruction row)",
                "registry/sample data" = "Not applicable - registry / sample-frame field (see the source definition row)",
                "derived/coded" = "Not applicable - coded/constructed variable (see the source definition row)",
                "question text not located" = "Question text not located in the questionnaire",
                "unknown (no questionnaire item located)" = "Question text not located (no questionnaire item for this source variable)")
# verdict on one component over a set of rows, saying so when the component is empty in some or all of them
component_flag2 <- function(vals, surveys) {
  keep <- vals != ""
  if (length(vals) < 2) return(NA_character_)
  if (!any(keep)) return("none printed")
  if (sum(keep) == 1) return(sprintf("printed in %s only", SLAB[[surveys[keep][1]]]))
  f <- component_flag(vals, surveys)
  if (any(!keep)) f <- paste0(f, sprintf("; none printed in %s", paste(unique(SLAB[surveys[!keep]]), collapse = ", ")))
  f
}
RENDER_FAILS <- character(0)
wording_block <- function(t) {
  w <- WORDING %>% filter(target == t)
  if (!nrow(w)) return(NULL)
  w <- w[order(match(w$survey, KEYS)), ]                 # one column per source variable; a multi-source feed gives several per survey
  rf <- as.integer(w$respondent_facing) == 1; fam <- acq_family(w$acquisition)
  # prompt shown or read to the respondent: the battery statement when the item is one, else the question; the lead-in
  # (question text minus the statement) joins the introduction row so that nothing is printed twice
  stmt <- ifelse(w$item_text != "", w$item_text, w$question_text)
  leadin <- map_chr(seq_len(nrow(w)), function(j) {
    if (w$item_text[j] == "" || w$question_text[j] == "" || w$question_text[j] == w$item_text[j]) return("")
    str_squish(gsub("[[:space:]\u2014\u2013:-]+$", "", sub(w$item_text[j], "", w$question_text[j], fixed = TRUE)))
  })
  introcell <- str_squish(ifelse(w$intro != "" & leadin != "" & w$intro != leadin, paste(w$intro, leadin, sep = " | "), ifelse(w$intro != "", w$intro, leadin)))
  sub <- ifelse(w$item_text == "" & w$subitems != "", paste0(" [battery items: ", str_trunc(w$subitems, 300), "]"), "")
  acq_key <- ifelse(grepl("^linked partner record", w$acquisition), "linked partner record", w$acquisition)   # relationship-derived keeps its own key
  prompt <- ifelse(rf, paste0(ifelse(stmt != "", stmt, "Question text not located in the questionnaire"), sub),
                   ifelse(acq_key %in% names(ACQ_ABSENT), ACQ_ABSENT[acq_key], paste0("Not applicable - ", w$acquisition)))
  uni <- map_chr(w$survey, ~ { u <- UNIVERSES$universe[UNIVERSES$target == t & UNIVERSES$survey == .x]
    if (length(u)) return(u[1])
    segs <- str_split(vm$universe_en[vm$target == t][1], ";\\s+(?=[A-Z])")[[1]]      # composed universe: the segment naming this survey, else the whole text
    hit <- segs[grepl(SLAB[[.x]], segs, fixed = TRUE)]
    if (length(hit)) hit[1] else vm$universe_en[vm$target == t][1] })
  sr <- str_squish(paste(ifelse(w$split_half != "", paste0("split half ", w$split_half, ";"), ""), ifelse(w$randomization != "", w$randomization, "")))
  rows <- tibble(Item = c("Source variable", "How obtained", "Information supplied by", "Person / entity described",
                          "Introduction / lead-in (questionnaire)", "Question / statement shown or read to respondent",
                          "Interviewer recording / assessment instruction (questionnaire)", "Response / recording categories (questionnaire codes)",
                          "Response format", "Source definition / derivation", "Value labels in the source data file (shown where codes or meanings differ from the questionnaire; the value map and the harmonized codes work from these)",
                          "Eligible records / population", "Routing (harmonized variables)", "Split-half / randomisation"))
  for (j in seq_len(nrow(w))) {
    srccell <- if (w$qid[j] != "") sprintf("`%s` (%s %s%s)", w$source_var[j], w$instrument[j], w$qid[j], ifelse(w$capi_qid[j] != "", paste0("; CAPI ", w$capi_qid[j]), "")) else sprintf("`%s` (%s)", w$source_var[j], sub("^none ?", "no questionnaire item ", w$match[j]))
    if (w$label_nl[j] != "") srccell <- paste0(srccell, " — *", str_trunc(str_squish(sub("^Vraag\\s*[0-9]+[A-Za-z]?\\s*[:-]\\s*", "", w$label_nl[j])), 80), "*")   # data label as a gloss (its own row was redundant with the prompt)
    colname <- if (sum(w$survey == w$survey[j]) > 1) sprintf("%s (%s)", SLAB[[w$survey[j]]], w$source_var[j]) else SLAB[[w$survey[j]]]
    vl_cell <- if (w$answer_options[j] == "") w$value_labels_nl[j] else {
      pc <- sort(unique(str_match_all(w$answer_options[j], "(?:^|;\\s*)(-?[0-9]+)=")[[1]][, 2]))
      vc <- str_match_all(w$value_labels_nl[j], "(?:^|;\\s*)(-?[0-9]+)=")[[1]][, 2]; vc <- sort(unique(vc[as.numeric(vc) >= 0]))
      if (identical(pc, vc) && w$code_meaning_note[j] == "") "" else w$value_labels_nl[j] }   # shown where the data carry other codes, or the same codes with other meanings
    if (w$code_meaning_note[j] != "") vl_cell <- paste0("**Coding differs from the questionnaire** - ", w$code_meaning_note[j], ". Data-file labels: ", vl_cell)
    rows[[colname]] <- c(srccell, w$acquisition[j], w$supplied_by[j], w$describes[j], introcell[j], prompt[j], w$instruction[j], w$answer_options[j],
                         w$format[j], w$source_definition[j], vl_cell, uni[j],
                         if (rf[j] || fam[j] == "interviewer") gate_cell(t, w$survey[j], w$source_var[j], w$routing_gates[j], w$routing_note[j], w$routing[j]) else "",
                         sr[j])
    # rendering assertions (review point 12): no English description or procedure in the prompt row of a non-respondent-facing
    # source; a battery statement is printed once (not again in the lead-in)
    if (!rf[j] && !grepl("^(Not applicable|Question text not located)", prompt[j])) RENDER_FAILS <<- c(RENDER_FAILS, sprintf("%s/%s: non-respondent-facing source rendered as a prompt", t, w$source_var[j]))
    if (w$item_text[j] != "" && nchar(w$item_text[j]) > 12 && grepl(w$item_text[j], introcell[j], fixed = TRUE)) RENDER_FAILS <<- c(RENDER_FAILS, sprintf("%s/%s: battery statement repeated in the lead-in", t, w$source_var[j]))
  }
  rows <- rows[rowSums(rows[-1] != "") > 0, ]
  # comparisons by acquisition family: wording over the respondent-facing rows, procedure and scale over the interviewer-
  # acquired rows, definitions for registry and constructed sources (named, not compared)
  parts <- character(0); comp <- NULL
  if (any(rf)) {
    ws <- w[rf, ]; svs <- unique(SLAB[ws$survey])
    if (n_distinct(ws$survey) == 1) parts <- c(parts, sprintf("Respondent-facing (%s): single survey", paste(svs, collapse = ", ")))
    else {
      lead <- ifelse(ws$item_text != "", ifelse(ws$intro != "", ws$intro, leadin[rf]), ws$intro)
      comp <- c(`question` = component_flag2(norm_q(stmt[rf]), ws$survey),
                `introduction` = component_flag2(norm_q(lead), ws$survey),
                `answer options` = component_flag2(norm_opts(ws$answer_options), ws$survey),
                `interviewer instruction` = component_flag2(norm_i(ws$instruction), ws$survey),
                `routing` = component_flag2(norm_i(ws$routing), ws$survey))
      comp <- comp[!is.na(comp)]
      shown <- comp[!(names(comp) %in% c("interviewer instruction", "routing") & comp == "none printed")]   # absent everywhere: nothing to say
      parts <- c(parts, sprintf("Respondent-facing (%s): %s", paste(svs, collapse = ", "), paste(sprintf("%s %s", names(shown), shown), collapse = "; ")))
    }
  }
  iv <- fam == "interviewer"
  if (any(iv)) {
    wi <- w[iv, ]; svs <- unique(SLAB[wi$survey])
    if (n_distinct(wi$survey) == 1) parts <- c(parts, sprintf("Interviewer-acquired, %s (%s): single survey", paste(unique(wi$acquisition), collapse = " / "), paste(svs, collapse = ", ")))
    else parts <- c(parts, sprintf("Interviewer-acquired, %s (%s): instruction %s; categories %s", paste(unique(wi$acquisition), collapse = " / "), paste(svs, collapse = ", "),
                                   component_flag2(norm_i(wi$instruction), wi$survey), component_flag2(norm_opts(wi$answer_options), wi$survey)))
  }
  if (any(fam %in% c("linked partner record", "relationship-derived"))) {
    wl <- w[fam %in% c("linked partner record", "relationship-derived"), ]
    parts <- c(parts, if (all(grepl("^relationship-derived", wl$acquisition))) sprintf("Relationship-derived (%s): computed from the roster link and the LAT question, no question", paste(unique(SLAB[wl$survey]), collapse = ", "))
                      else sprintf("Derived from the linked partner's record (%s): %s - no partner question, the base field's acquisition applies", paste(unique(SLAB[wl$survey]), collapse = ", "),
                                   paste(unique(sub("^linked partner record: ", "", wl$acquisition)), collapse = " / ")))
  }
  if (any(fam == "registry")) parts <- c(parts, sprintf("Registry/sample fields (%s): see the source definition row", paste(unique(SLAB[w$survey[fam == "registry"]]), collapse = ", ")))
  if (any(fam == "constructed")) parts <- c(parts, sprintf("Constructed sources (%s): see the source definition row", paste(unique(SLAB[w$survey[fam == "constructed"]]), collapse = ", ")))
  if (any(fam == "unknown")) parts <- c(parts, sprintf("No questionnaire item located (%s)", paste(unique(SLAB[w$survey[fam == "unknown"]]), collapse = ", ")))
  fams <- unique(fam[fam != "unknown"])
  if (length(fams) > 1) parts <- c(parts, sprintf("Acquisition differs between surveys (%s): %s", paste(fams, collapse = " vs "),
                                                   if (any(fams %in% c("respondent", "interviewer"))) "the measurements are not equivalent by wording" else "compare the definitions, not wording"))
  note <- WORDNOTES$note[WORDNOTES$target == t]
  list(table = rows, flag = paste(parts, collapse = ". "), note = if (length(note)) note[1] else "", components = comp, families = fams,
       n_rf = n_distinct(w$survey[rf]), n_other = n_distinct(w$survey[!rf]))
}

# ---- comparability inventory (audit decision 3): one class per target over the surveys that carry it, seeded from the
#      component verdicts of the wording comparison and the target's construction; reviewed judgements override the seed
#      (crosswalks/comparability_review.csv: target, class, note, reviewer, date).  Written to docs/comparability.csv.
REVIEW <- if (file.exists(P("crosswalks", "comparability_review.csv"))) read_cw("comparability_review.csv") else tibble(target = character(), class = character(), note = character(), reviewer = character(), date = character())
classify <- function(r, wb) {
  svy <- KEYS[sapply(KEYS, function(k) r[[paste0("avail_", k)]] != "not collected")]
  if (length(svy) < 2) return(c("wave-specific", "carried by one survey only"))
  comp <- wb$components
  flag <- if (is.null(wb)) "" else wb$flag
  coarse <- grepl("_(cat|cat3|cat4|cat5|cat5y|lvl3|cbs|band|band8|band16)$|_cat[0-9]*_|_lvl3_", r$target) || grepl("collapsed|harmonized classes|coarsened|in classes", r$notes, ignore.case = TRUE)
  if (grepl("^(id_|svy_)", r$target)) return(c("administrative", "identifier or survey-administration variable"))
  if (r$derive != "" && !grepl("^(fill0_interviewed|kl9_route|rel_none|partner_copy)", r$derive) && !grepl("cpi2015", r$derive))
    return(c("derived", sprintf("derived by rule '%s' in every survey where the inputs exist; see the variable note", r$derive)))
  fams <- if (is.null(wb)) character(0) else wb$families
  if (length(fams) > 1) return(c("mixed provenance", sprintf("the information is obtained differently across surveys (%s): see the 'How obtained' and 'Source definition' rows", paste(fams, collapse = " vs "))))
  if (length(fams) == 1 && fams == "constructed") return(c("construct-defined", "constructed/coded sources in every survey: comparability rests on the construct definitions, not on question wording"))
  if (length(fams) == 1 && fams == "registry") return(c("construct-defined", "registry/sample-frame sources in every survey: comparability rests on the field definitions and reference dates"))
  if (length(fams) == 1 && fams == "interviewer") {
    if (grepl("instruction identical(?!.*none printed)", flag, perl = TRUE) && grepl("categories identical", flag)) return(c(if (coarse) "coarse match" else "exact match", "same interviewer instruction and recording categories in every survey (procedure, not a respondent question)"))
    return(c(if (coarse) "coarse match" else "approximate match", "interviewer-acquired in every survey with a different instruction or scale: see the wording table"))
  }
  if (is.null(comp)) return(c("unclassified", "no component verdict available"))
  q <- if ("question" %in% names(comp)) comp[["question"]] else NA; o <- if ("answer options" %in% names(comp)) comp[["answer options"]] else NA
  o_same <- is.na(o) || grepl("^identical|^none printed|^printed in .* only", o)     # open/numeric entries: no printed categories, or a unit label in one survey
  if (!is.na(q) && grepl("^identical", q) && o_same) cls <- c(if (coarse) "coarse match" else "exact match", "same question and answer options in every respondent-facing source" )
  else if (!is.na(q) && grepl("^identical", q)) cls <- c(if (coarse) "coarse match" else "approximate match", "same question, different answer options or scales (harmonized codes): see the wording table")
  else cls <- c(if (coarse) "coarse match" else "approximate match", "question wording differs between surveys: see the wording table")
  if (grepl("unresolved fill", flag)) cls[2] <- paste0(cls[2], "; a group fill is unresolved in the script printout")
  if (coarse) cls[2] <- paste0("harmonized classes; ", cls[2])
  cls
}
COMPAT <- list()

add("\n## 5. Variable descriptions {#descriptions}\n")
for (i in seq_len(nrow(vm))) {
  r <- vm[i, ]
  add("\n---\n\n### `%s` {#%s}\n", r$target, r$target)
  add("**%s**\n", r$label_en)
  add("- Theme: %s (`%s`) · Scope: %s · Type: %s%s", THEMES[[r$theme]], r$theme, r$scope, r$type, ifelse(r$valueset != "", sprintf(" · Value set: `%s`", r$valueset), ""))
  add("- Universe: %s", r$universe_en)
  # sources in one line (the wording table below carries the labels and questionnaire references per source)
  srcl <- map_chr(KEYS, function(s) { src <- r[[paste0("src_", s)]]; if (src == "") return(NA_character_)
    sprintf("%s `%s` (%s)%s", SLAB[[s]], gsub("|", "` | `", src, fixed = TRUE), r[[paste0("files_", s)]], if (grepl("|", src, fixed = TRUE)) " - first non-missing in this order" else "") })
  srcl <- srcl[!is.na(srcl)]
  if (length(srcl)) add("- Sources (file level): %s", paste(srcl, collapse = "; "))
  if (r$derive != "") add("- Derived: `%s` (see `code/R/03_derive.R` / `code/Stata/03_derive.do`)", r$derive)
  if (r$notes != "") add("- Notes: %s", r$notes)
  # subject / reporter / availability (audit decision 2): per survey, who is described, who reported, how the survey contributes
  rep <- sapply(KEYS, function(k) r[[paste0("reporter_", k)]]); av <- sapply(KEYS, function(k) r[[paste0("avail_", k)]])
  repg <- split(names(rep)[rep != ""], rep[rep != ""])
  add("- Subject: %s · Reported by: %s", r$subject, if (length(repg)) paste(sprintf("%s (%s)", names(repg), sapply(repg, function(ks) paste(SLAB[ks], collapse = ", "))), collapse = "; ") else "n/a")
  avg <- split(names(av), av)
  add("- Availability: %s", paste(sprintf("%s: %s", names(avg), sapply(avg, function(ks) paste(SLAB[ks], collapse = ", "))), collapse = " · "))
  rsum <- routing_summary(r$target)
  if (rsum != "") add("- Routing (harmonized variables): %s", rsum)
  wb <- wording_block(r$target)
  cls <- classify(r, wb)
  rv <- REVIEW[REVIEW$target == r$target, ]
  status <- if (nrow(rv)) "reviewed" else "auto"
  if (nrow(rv)) cls <- c(rv$class[1], rv$note[1])
  COMPAT[[r$target]] <- tibble(target = r$target, surveys = paste(KEYS[av != "not collected"], collapse = ";"), class = cls[1], basis = cls[2], status = status,
                               reviewer = if (nrow(rv)) rv$reviewer[1] else "", date = if (nrow(rv)) rv$date[1] else "")
  add("- Comparability: **%s** (%s) — %s", cls[1], status, cls[2])
  if (!is.null(wb)) {
    add("- Wording and procedure: %s%s", wb$flag, ifelse(wb$note != "", paste0(". **Note:** ", wb$note), ""))
    add(paste(md_table(wb$table), collapse = "\n"))
  } else if (WORDNOTES$note[WORDNOTES$target == r$target] %>% length()) add("- Wording note: %s", WORDNOTES$note[WORDNOTES$target == r$target][1])
  maps <- VALUEMAP %>% filter(target == r$target)
  if (nrow(maps)) {
    # recodes that change a code (source code -> different harmonized code); identity maps, ranges to a single code and
    # missing-code maps are omitted here and stay in crosswalks/value_map.csv
    chg <- maps %>% filter(!str_starts(target_value, fixed(".")), source_value != target_value, !str_detect(source_value, "^'|\\*"))
    if (nrow(chg)) {
      byk <- chg %>% group_by(survey, source_var) %>% summarise(m = paste(sprintf("%s→%s", source_value, target_value), collapse = ", "), .groups = "drop")
      add("- Recodes (source code → harmonized code; full map incl. missing codes in `crosswalks/value_map.csv`): %s",
          paste(sprintf("%s `%s`: %s", SLAB[byk$survey], byk$source_var, byk$m), collapse = "; "))
    } else add("- Value map: codes kept as delivered (missing codes and string maps in `crosswalks/value_map.csv`)")
  }
  if (r$type == "id") {
    # identifiers: dimensionless numbers that single out a record - no descriptives, only coverage and uniqueness
    idt <- tibble(survey = svys,
                  `n non-missing` = map_int(svys, ~ sum(!is.na(d[[r$target]][d$svy_name == .x]))),
                  `n distinct` = map_int(svys, ~ n_distinct(d[[r$target]][d$svy_name == .x & !is.na(d[[r$target]])])),
                  `unique within survey` = ifelse(`n non-missing` == 0, "-", ifelse(`n non-missing` == `n distinct`, "yes", "no (repeated across household members)")))
    add("\nIdentifier (no descriptives: the values are labels, not quantities):\n"); add(paste(md_table(idt), collapse = "\n"))
    ms <- miss_summary(r$target); if (nrow(ms)) { add("\nMissing values:\n"); add(paste(md_table(ms %>% select(code, label, everything())), collapse = "\n")) }
  } else if (r$type == "str") {
    add("\nNon-empty values by survey: %s", paste(sprintf("%s %s", svys, fmt_n(map_int(svys, ~ sum(!is.na(d[[r$target]][d$svy_name == .x]))))), collapse = ", "))
  } else if (r$valueset != "") {
    add("\nFrequencies (unweighted):\n"); add(paste(md_table(freq_table(r$target)), collapse = "\n"))
  } else {
    add("\nSummary (unweighted, non-missing values):\n"); add(paste(md_table(num_summary(r$target)), collapse = "\n"))
    ms <- miss_summary(r$target); if (nrow(ms)) { add("\nMissing values:\n"); add(paste(md_table(ms %>% select(code, label, everything())), collapse = "\n")) }
  }
}
if (length(RENDER_FAILS)) stop("codebook rendering assertions failed: ", paste(head(RENDER_FAILS, 20), collapse = "; "))
# a table must be preceded by a blank line, or Markdown processors (pandoc, Word conversion) read it as list text
ml <- unlist(strsplit(md, "\n", fixed = TRUE)); is_tab <- grepl("^\\|", ml)
prev_text <- c(FALSE, nzchar(ml[-length(ml)]) & !is_tab[-length(ml)])
ins <- which(is_tab & prev_text)
if (length(ins)) ml <- unlist(lapply(seq_along(ml), function(i) if (i %in% ins) c("", ml[i]) else ml[i]))
md <- paste(ml, collapse = "\n")
writeLines(md, P("docs", "codebook.md"))

# ---- machine-readable index ------------------------------------------------------------------
compat <- bind_rows(COMPAT)
write_csv(compat, P("docs", "comparability.csv"), na = "")
message(sprintf("Comparability inventory: %s -> docs/comparability.csv", paste(sprintf("%s %d", names(table(compat$class)), table(compat$class)), collapse = ", ")))
idx <- vm %>% select(target, theme, label_en, scope, type, valueset, starts_with("src_"), starts_with("files_"), universe_en, derive, notes, subject, starts_with("reporter_"), starts_with("avail_"))
for (s in svys) idx[[paste0("n_", str_to_lower(s))]] <- map_int(idx$target, ~ sum(!is.na(d[[.x]][d$svy_name == s])))
write_csv(idx, P("docs", "codebook_variables.csv"), na = "")

# ---- HTML (self-contained, no pandoc needed) -------------------------------------------------
md_to_html <- function(lines) {
  out <- character(0); i <- 1; in_tab <- FALSE
  flush_tab <- function(rows) {
    hdr <- strsplit(gsub("^\\| | \\|$", "", rows[1]), " \\| ")[[1]]
    body <- rows[-(1:2)]
    h <- paste0("<tr>", paste0("<th>", esc(hdr), "</th>", collapse = ""), "</tr>")
    b <- vapply(body, function(r) paste0("<tr>", paste0("<td>", inline(esc(strsplit(gsub("^\\| | \\|$", "", r), " \\| ")[[1]])), "</td>", collapse = ""), "</tr>"), "")
    c("<table>", h, b, "</table>")
  }
  inline <- function(s) { s <- gsub("\\\\\\|", "|", s); s <- gsub("`([^`]+)`", "<code>\\1</code>", s); s <- gsub("\\*\\*([^*]+)\\*\\*", "<b>\\1</b>", s)
    s <- gsub("(?<![A-Za-z0-9_])\\*([^*\\s][^*]*?)\\*(?![A-Za-z0-9_])", "<i>\\1</i>", s, perl = TRUE)   # italics, but not a * inside a formula (svy_key*1e11)
    gsub("\\[([^]]+)\\]\\(#([^)]+)\\)", "<a href='#\\2'>\\1</a>", s) }
  tab <- character(0); in_var <- FALSE; skip_label <- FALSE
  for (idx in seq_along(lines)) {
    l <- lines[idx]
    if (grepl("^\\|", l)) { tab <- c(tab, l); next } else if (length(tab)) { out <- c(out, flush_tab(tab)); tab <- character(0) }
    if (skip_label) { skip_label <- FALSE; next }                       # the label line is already in the summary
    if (grepl("^### `([^`]+)` \\{#", l)) {                            # variable entry: collapsible, opened when linked to
      v <- sub("^### `([^`]+)`.*", "\\1", l)
      lab <- if (idx < length(lines) && grepl("^\\*\\*", lines[idx + 1])) gsub("^\\*\\*|\\*\\*$", "", lines[idx + 1]) else ""
      if (lab != "") skip_label <- TRUE
      out <- c(out, if (in_var) "</details>" else character(0),
               sprintf("<details class='var' id='%s'><summary><code>%s</code> <span class='lab'>%s</span> <a class='top' href='#top'>↑</a></summary>", v, v, esc(lab)))
      in_var <- TRUE
    }
    else if (grepl("^##+ ", l)) {                                        # section heading, optional trailing {#id}
      if (in_var) { out <- c(out, "</details>"); in_var <- FALSE }
      lev <- if (grepl("^### ", l)) "h3" else "h2"; txt <- sub("^##+ ", "", l)
      id <- if (grepl(" \\{#[^}]+\\}$", txt)) sub("^.* \\{#([^}]+)\\}$", "\\1", txt) else ""; txt <- sub(" \\{#[^}]+\\}$", "", txt)
      out <- c(out, sprintf("<%s%s>%s</%s>", lev, if (id != "") sprintf(" id='%s'", id) else "", inline(esc(txt)), lev))
      if (grepl("^## 4\\. Variable index", l)) out <- c(out, FINDER_HTML) }
    else if (grepl("^<details class='more'><summary>.*</summary>$", l))    # front-matter detail block (more_open)
      out <- c(out, sprintf("<details class='more'><summary>%s</summary>", inline(esc(sub("^<details class='more'><summary>(.*)</summary>$", "\\1", l)))))
    else if (l == "</details>" && !in_var) out <- c(out, "</details>")
    else if (grepl("^# ", l)) out <- c(out, sprintf("<h1 id='top'>%s</h1>", esc(sub("^# ", "", l))))
    else if (grepl("^- ", l)) out <- c(out, sprintf("<div class='li'>• %s</div>", inline(esc(sub("^- ", "", l)))))
    else if (grepl("^---$", l)) { if (!in_var) out <- c(out, "<hr>") }
    else if (nchar(trimws(l))) out <- c(out, sprintf("<p>%s</p>", inline(esc(l))))
  }
  if (length(tab)) out <- c(out, flush_tab(tab))
  if (in_var) out <- c(out, "</details>")
  out
}
# variable finder (HTML only): text search, theme and survey-availability filters over the variable index
FINDER_DATA <- vm %>% transmute(t = target, l = label_en, th = theme, sb = subject,
                                av = map_chr(seq_len(n()), function(i) paste(KEYS[sapply(KEYS, function(k) vm[[paste0("avail_", k)]][i] != "not collected")], collapse = " ")),
                                cl = map_chr(target, ~ { x <- compat$class[compat$target == .x]; if (length(x)) x[1] else "" }))
FINDER_HTML <- c("<div id='finder'><b>Variable finder</b> — <input id='fq' type='search' placeholder='name or label' size='28'> ",
                 "<select id='fth'><option value=''>all themes</option>", sprintf("<option value='%s'>%s (%s)</option>", names(THEMES), esc(THEMES), names(THEMES)), "</select> available in: ",
                 sprintf("<label><input type='checkbox' class='fsv' value='%s'> %s</label>", KEYS, SLAB[KEYS]),
                 " <span id='fn'></span><div id='fres'></div></div>",
                 sprintf("<script>const VARS=%s;</script>", jsonlite::toJSON(FINDER_DATA, auto_unbox = TRUE)),
                 "<script>
function ffind(){const q=document.getElementById('fq').value.toLowerCase(),th=document.getElementById('fth').value,sv=[...document.querySelectorAll('.fsv:checked')].map(x=>x.value);
 const hits=VARS.filter(v=>(!q||v.t.includes(q)||v.l.toLowerCase().includes(q))&&(!th||v.th===th)&&sv.every(s=>v.av.split(' ').includes(s)));
 document.getElementById('fn').textContent=(q||th||sv.length)?hits.length+' of '+VARS.length+' variables':'';
 document.getElementById('fres').innerHTML=(q||th||sv.length)?hits.slice(0,300).map(v=>'<div class=\"fr\"><a href=\"#'+v.t+'\"><code>'+v.t+'</code></a> '+v.l+' <span class=\"fm\">['+v.av+'] '+v.cl+'</span></div>').join('')+(hits.length>300?'<div class=fr>… (first 300 shown)</div>':''):'';}
['fq','fth'].forEach(i=>document.getElementById(i).addEventListener('input',ffind));document.querySelectorAll('.fsv').forEach(x=>x.addEventListener('change',ffind));
function openHash(){const h=location.hash.slice(1);if(!h)return;const e=document.getElementById(h);if(e&&e.tagName==='DETAILS'){e.open=true;e.scrollIntoView();}}
window.addEventListener('hashchange',openHash);window.addEventListener('load',openHash);
</script>")
css <- "body{font-family:Segoe UI,Helvetica,Arial,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;color:#222;line-height:1.45}
h1{border-bottom:3px solid #1f4e79}h2{color:#1f4e79;margin-top:2.2em}h3{margin-top:1.6em}code{background:#f3f5f8;padding:1px 4px;border-radius:3px}
table{border-collapse:collapse;margin:.6em 0;font-size:.9em;max-width:100%}th,td{border:1px solid #d8dde3;padding:3px 8px;text-align:left;vertical-align:top;word-break:normal}th{background:#eef2f7}
.li{margin:.15em 0 .15em 1em}a.top{font-size:.7em;color:#888;text-decoration:none;margin-left:.5em}hr{border:0;border-top:1px solid #ddd;margin:2em 0}
details.var{margin:.4em 0;border-left:3px solid #d8dde3;padding-left:.6em}details.var[open]{border-left-color:#1f4e79}details.var>summary{cursor:pointer;font-size:1.05em;margin:.3em 0}
details.var>summary .lab{color:#444}#finder{background:#f3f5f8;padding:.7em 1em;border-radius:6px;margin:1em 0}#finder label{margin-right:.6em;white-space:nowrap}
details.more{margin:.5em 0 .8em;padding:.25em .9em;background:#f7f9fb;border:1px solid #e3e8ee;border-radius:5px}details.more>summary{cursor:pointer;color:#1f4e79;font-weight:600;padding:.2em 0}
details.more[open]{background:#fff}details.more>summary::after{content:'  more detail';font-weight:normal;font-size:.85em;color:#888}
#fres{max-height:22em;overflow:auto;margin-top:.5em}.fr{font-size:.9em;margin:.15em 0}.fm{color:#777;font-size:.85em}"
html <- c("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>IMPD public component — Codebook</title>", sprintf("<style>%s</style>", css), "</head><body>",
          md_to_html(unlist(strsplit(md, "\n", fixed = TRUE))), "</body></html>")
writeLines(html, P("docs", "codebook.html"))
logmsg("Codebook written: docs/codebook.md, docs/codebook.html, docs/codebook_variables.csv (%d variables)", nrow(vm))
