# Study Chinese CLI

`sc` is a standalone Python CLI for reviewing Chinese flashcards with an Anki-inspired spaced repetition loop.

## Features

- SQLite-backed local storage
- Three note types: `vocab`, `char`, `sentence`
- Generated cards for recognition, production, and sentence cloze review
- SM-2-like scheduling with `again`, `hard`, `good`, `easy`
- CSV import and interactive note creation/editing
- Review stats and due-card listings

## Conda Environment

`conda build recipe` is slow because it does full package-build work: it creates isolated build/test environments, runs packaging hooks, and validates an installable Conda artifact. That is useful for publishing a Conda package, but it is more machinery than this repo needs.

This repository now uses a minimal Conda environment spec in `environment.yml` instead. It creates a Python environment and installs this checkout with `pip -e .`.

### Create the environment

```bash
conda env create -f environment.yml
conda activate sc
```

After activation, initialize the database and start using the CLI:

```bash
sc init
sc add vocab
sc review
```

### Load the example curriculum

The repository includes sample CSVs in `sample_curriculum/`. Import them with:

```bash
sc import vocab sample_curriculum/vocab.csv
sc import char sample_curriculum/char.csv
sc import sentence sample_curriculum/sentence.csv
```

You can then inspect the imported notes and due cards with:

```bash
sc list notes
sc list due
```

## Development Setup

For development and tests, start from the base Conda environment and add dev dependencies:

```bash
conda env create -f environment.yml
conda activate sc
pip install -e ".[dev]"
```

Run the test suite with:

```bash
pytest
```

## Project Layout

- `src`: application source
- `tests`: automated test coverage
- `sample_curriculum`: example CSV inputs
- `environment.yml`: minimal Conda environment specification

## Saved Design Notes

The planning conversation that defined this project has been summarized in [docs/flashcards-plan.md](/Users/britton/shared/github/jbqubit/sc/docs/flashcards-plan.md).
