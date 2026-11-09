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

The 4:3 pages hold less than a widescreen slide. Keep a column to about eight short bullets and code lines to about 45 characters. Text after a table, or under a `#` section title, moves to a slide of its own. In a column, start with text and put a table last or on its own, otherwise pandoc changes the layout.

If NIDI's template changes, put the new file in `template/NIDI_template.pptx` and run `python code/tools/make_slide_template.py` (needs the python-pptx package) to prepare it for pandoc again.
