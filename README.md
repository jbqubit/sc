# Study Chinese CLI

`sc` is a standalone Python CLI for reviewing Chinese flashcards with an ANKI-inspired spaced repetition loop.

## Features

- SQLite-backed local storage
- Three note types: `vocab`, `char`, `sentence`
- Generated cards for recognition, production, and sentence cloze review
- SM-2-like scheduling with `again`, `hard`, `good`, `easy`
- CSV import and interactive note creation/editing
- Review stats and due-card listings

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
sc init
sc add vocab
sc review
```

## Saved Design Notes

The planning conversation that defined this project has been summarized in [docs/flashcards-plan.md](/workspace/docs/flashcards-plan.md).
