# Study Chinese CLI

`sc` is a standalone Python CLI for reviewing Chinese flashcards with an Anki-inspired spaced repetition loop.

## Features

- SQLite-backed local storage
- Three note types: `vocab`, `char`, `sentence`
- Generated cards for recognition, production, and sentence cloze review
- SM-2-like scheduling with `again`, `hard`, `good`, `easy`
- CSV import and interactive note creation/editing
- Review stats and due-card listings

## Conda Package

This repository now includes a Conda recipe at `recipe/meta.yaml`.

### Build the package locally

```bash
conda create -n sc-build python=3.11 conda-build pytest -y
conda activate sc-build
conda build recipe
```

### Install the locally built package

```bash
conda activate sc-build
conda install --use-local study-chinese-cli
```

After installation, initialize the database and start using the CLI:

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

For editable development inside a Conda environment:

```bash
conda create -n sc-dev python=3.11 pytest -y
conda activate sc-dev
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
- `recipe`: Conda packaging files

## Saved Design Notes

The planning conversation that defined this project has been summarized in [docs/flashcards-plan.md](/Users/britton/shared/github/jbqubit/sc/docs/flashcards-plan.md).
