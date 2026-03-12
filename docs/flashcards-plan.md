# Flashcards Plan

This document captures the design decisions from the original planning conversation so a later Codex session can resume work without replaying the discussion.

## Product Scope

- Standalone Python CLI
- Single-user only
- No audio or TTS anywhere in the product
- Local-first SQLite storage
- Three note types:
  - `vocab`
  - `char`
  - `sentence`

## Core Commands

- `sc init [--db PATH]`
- `sc add vocab|char|sentence`
- `sc import vocab|char|sentence PATH [--delimiter ","]`
- `sc review [--type TYPE] [--tag TAG] [--limit N] [--new|--due]`
- `sc list notes [--type TYPE] [--tag TAG] [--limit N]`
- `sc list cards [--type TYPE] [--state STATE] [--due]`
- `sc list due [--type TYPE] [--tag TAG]`
- `sc show note NOTE_ID`
- `sc show card CARD_ID`
- `sc edit note NOTE_ID`
- `sc suspend card CARD_ID`
- `sc unsuspend card CARD_ID`
- `sc archive note NOTE_ID`
- `sc restore note NOTE_ID`
- `sc stats`
- `sc stats daily [--days N]`
- `sc stats cards`
- `sc stats notes`

## Note Schema

### Shared `notes`

- `id`
- `note_type`
- `tags`
- `source`
- `is_archived`
- `created_at`
- `updated_at`

### `vocab_notes`

- `hanzi`
- `pinyin`
- `english`
- `example_cn`
- `example_en`

### `char_notes`

- `hanzi`
- `pinyin`
- `english`
- `components`
- `mnemonic`
- `example_cn`
- `example_en`

### `sentence_notes`

- `sentence_cn`
- `sentence_pinyin`
- `sentence_en`
- `focus_term`
- `notes`

## Card Types

### `vocab`

- `hanzi_to_meaning`
- `english_to_hanzi`

### `char`

- `char_to_meaning`
- `meaning_to_char`

### `sentence`

- `sentence_to_meaning`
- `cloze_focus_term` when `focus_term` is present

## Scheduling Rules

- Learning steps: 1 minute, 10 minutes
- New cards behave like the first learning step
- Graduation:
  - `good` -> 1 day
  - `easy` -> 3 days
- Review states: `new`, `learning`, `review`, `relearning`
- Ease factor bounds: 1.3 to 3.0

### Review State Behavior

- `again`: move to relearning, interval reduced to `max(1, old_interval * 0.25)`, due in 10 minutes, lapses +1, ease -0.20
- `hard`: interval `max(old_interval + 1, old_interval * 1.2)`, ease -0.15
- `good`: interval `max(old_interval + 1, old_interval * ease_factor)`
- `easy`: interval `max(old_interval + 2, old_interval * ease_factor * 1.3)`, ease +0.15

### Relearning Behavior

- `again`: remain relearning, due in 10 minutes
- `hard`: return to review in 1 day
- `good`: return to review in `max(1, reduced_interval)` days
- `easy`: return to review in `max(2, reduced_interval * 1.3)` days

## Non-Goals

- No sync
- No external dictionary integrations
- No audio
- No GUI
- No fuzzy auto-grading
