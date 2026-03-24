# WW2 Data Extraction Project

This project extracts data from WW2DB, transforms it, and loads the results into JSON and SQLite.

## Project Structure

- `config/`: Configuration files
- `data/`:
  - `raw/`: Raw extracted link lists
  - `processed/`: Detailed transformed JSON files
  - `html/countries.html`: Cached HTML for `https://ww2db.com/country/` (always refreshed on countries pipeline run)
  - `html/*.html`: Cached country page HTML files (for example `germany.html`)
- `src/`:
  - `extract/`: Data collection
  - `transform/`: Data transformation/parsing
  - `load/`: Persistence layer (JSON + SQLite)
  - `pipelines/`: Domain orchestrators and global orchestrator
  - `database/`:
    - `schema.py`: Schema creation and migrations
    - `common.py`: Shared database helpers
    - `repositories/`: SQL by domain (`countries`, `persons`, `weapons`, `retry_queue`, etc.)
    - `db.py`: Compatibility facade for imports
  - `models/`: Dataclasses
  - `utils/`: Shared utilities
  - `parse/`: Backward-compatible wrappers around `transform/`
- `tests/`: Test scripts

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run countries pipeline (creates `data/raw/countries.json` and `data/processed/countries_detailed.json`):
   ```bash
   python -B src/pipelines/countries/pipeline.py
   ```
   - If `data/processed/countries_detailed.json` already exists, it is imported directly into SQLite.
   - `data/html/countries.html` is refreshed every run.
   - Country page HTML files (`data/html/*.html`) are fetched only when missing and then reused.

3. Run persons pipeline (creates `data/raw/persons.json` and `data/processed/persons_detailed.json`):
   ```bash
   python -B src/pipelines/persons/pipeline.py
   ```
   - If `data/processed/persons_detailed.json` already exists, it is imported into SQLite.
   - Country HTML cache is reused when available.

4. Run weapons pipeline (creates `data/raw/weapons.json` and `data/processed/weapons_detailed.json`):
   ```bash
   python -B src/pipelines/weapons/pipeline.py
   ```
   - If `data/processed/weapons_detailed.json` already exists, it is imported into SQLite.
   - Country HTML cache is reused when available.

5. Run all pipelines with dependency order (`countries -> persons -> weapons`):
   ```bash
   python -B src/pipelines/orchestrator/pipeline.py
   ```
   - If HTTP `429` happens during detail extraction, failed items are queued and retried using `retry_queue` settings in `config/configs.yaml`.

6. Run parsing tests:
   ```bash
   python -B tests/test_parsing.py
   python -B tests/test_person_details_html.py
   python -B tests/test_country_weapons_html.py
   python -B tests/test_weapon_details_html.py
   ```

## Usage

- `src/pipelines/countries/pipeline.py`: Countries pipeline orchestrator
- `src/pipelines/persons/pipeline.py`: Persons pipeline orchestrator
- `src/pipelines/weapons/pipeline.py`: Weapons pipeline orchestrator
- `src/pipelines/orchestrator/pipeline.py`: Global orchestrator
- `src/extract/*.py`: Link extraction
- `src/transform/*.py`: HTML parsing to dataclasses
- `src/load/*.py`: JSON and SQLite loading

## 429 Retry Queue

Retry queue tables in SQLite:
- `retry_countries`
- `retry_persons`
- `retry_weapons`

Behavior:
- If a payload has `details = null` and `error` contains `429`, it is stored in the corresponding retry table.
- After the normal pipeline execution, the retry queue is processed after the configured wait.
- On success, the retry row is removed.
- On failure, `retry_count` and `last_error` are updated.

## Pipeline Execution Log

Table: `pipeline_execution_log`

Stores one row per pipeline run (`countries`, `persons`, `weapons`) with:
- `started_at`
- `finished_at`
- `pipeline_type`
- `inserted_rows`
- `updated_rows`
- `deleted_rows`
- `affected_rows` (sum of insert/update/delete)
- `status` (`completed`, `failed`, `aborted`)

Running `python -B src/pipelines/orchestrator/pipeline.py` creates 3 rows (one per pipeline run).

## Country HTML Cache Log (SQL)

Table: `country_html_cache_log`

Columns:
- `data` (timestamp in Brasília time)
- `total`
- `cached`
- `fetched`
- `errors`

One row is inserted on each countries pipeline run after cache validation.
