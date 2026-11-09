# Slide decks

The decks are written as Markdown text and turned into PowerPoint files in the NIDI style each time the pipeline runs. Their numbers come from the build itself, so a deck never quotes a number the current build does not produce.

| File | What it is | Tracked by Git |
|---|---|---|
| `harmonization.md` | Source of the deck "How the IMPD harmonization works": the text, the tables and the speaker notes | yes |
| `harmonization.pptx` | The PowerPoint file built from it | no: rebuilt by every run |
| `template/NIDI_template.pptx` | NIDI's PowerPoint template, as received | yes |
| `template/nidi_reference.pptx` | The template prepared for pandoc, by `code/tools/make_slide_template.py` | yes |
| `../facts.csv` | Every number a deck may quote, computed from the repository at each build | yes |

## Changing a deck

Edit `harmonization.md`, not the PowerPoint file: the next build replaces the PowerPoint file. To rebuild only the deck, without running the pipeline:

```
python code/tools/make_deck.py
```

This needs Python 3 and pandoc, and no data: the facts are read from the crosswalks and the documents in the repository. `run_all.R` runs it at the end of every build.

A number from the build is written as a fact name in double braces, such as `{{n_persons}}` or `{{build_id}}`. The names, their current values and where each comes from are listed in `docs/facts.csv`. A name that is not a fact stops the deck from being built, so a deck never shows a placeholder or a stale figure. A new fact is one line in the `facts()` function of `code/tools/make_deck.py`.

## Excerpts from the repository

A slide can show rows of a crosswalk, a record, lines of the run log, a section of the decisions log or a codebook entry, read from the files at build time. An excerpt is a line of its own in the Markdown, with a kind, a colon, and options separated by `|`:

| Excerpt | Shows | Example |
|---|---|---|
| `table:` | rows of a CSV file, as a table | `{{table: crosswalks/value_map.csv \| target=mig_transit \| columns=survey,source_var,source_value,target_value}}` |
| `record:` | one row of a CSV file, as a Field / Value table | `{{record: crosswalks/surveys.csv \| svy_name=SING2009 \| columns=svy_name,zipfile,file_main}}` |
| `lines:` | lines of a text file, as a code block | `{{lines: docs/run_log.md \| match=^- PASS \| rows=12 \| strip=^-\s* \| width=64}}` |
| `section:` | the opening of a numbered section of the decisions log | `{{section: docs/decisions.md \| 15 \| chars=430}}` |
| `toc:` | the numbered sections of the decisions log, as a table | `{{toc: docs/decisions.md \| last=7}}` |
| `codebook:` | the header lines of a variable's codebook entry | `{{codebook: mig_transit \| keep=Theme,Universe,Availability,Recodes}}` |
| `codebook-freq:` | the frequency table of a variable's codebook entry | `{{codebook-freq: mig_transit \| columns=code,label,SPVN2003,SING2009}}` |

Options: `col=value` keeps the rows where a column equals the value, `col~regex` where it matches; `columns=` selects and orders the columns and `head=` renames them for display; `rows=` caps the rows (a last row says how many were left out); `cell=` caps the characters per cell; `labels` shows survey labels (SING 2009) in place of keys (sing2009); `transpose` turns a table on its side, the first column becoming the header. An excerpt that finds nothing stops the build, like an unknown fact. The full list is at the top of `code/tools/make_deck.py`.

On a 4:3 page a table in a column holds about five rows of short text at a readable size. The builder shares each table's width among its columns by their content and sets its text to the largest size at which the slide's columns fit (16 down to 9 points), so a long excerpt comes out small: prefer few columns, short cells (`cell=`) and few rows.

## How a slide is laid out

pandoc chooses the NIDI page from what a slide contains:

| In the Markdown | NIDI page |
|---|---|
| `## Title`, then text or bullets | white text page, with the nidi logo |
| `## Title`, one sentence, then a table | white wide page, sentence above the table |
| `## Title`, then `:::: columns` with two `::: column` blocks | white wide page, two columns |
| `# Title` alone | orange section page |
| The `title:`, `subtitle:` and `author:` lines at the top | orange title page |
| `::: notes` … `:::` | speaker notes |

The 4:3 pages hold less than a widescreen slide. Keep a column to about eight short bullets and code lines to about 45 characters. Text after a table on a full-width slide, or under a `#` section title, moves to a slide of its own. In a column, text and tables can alternate: the builder stacks them from the top in the order written.

If NIDI's template changes, put the new file in `template/NIDI_template.pptx` and run `python code/tools/make_slide_template.py` (needs the python-pptx package) to prepare it for pandoc again.
