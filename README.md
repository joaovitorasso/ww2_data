# WW2 Data Extraction Project

This project extracts and parses data from WW2DB website.

## Structure

- `config/`: Configuration files
- `data/`: Extracted data
  - `raw/`: Raw HTML files (optional)
  - `processed/`: Processed JSON data
- `src/`: Source code
  - `extract/`: Initial data extraction
  - `parse/`: Detailed parsing
  - `models/`: Data models
  - `pipelines/`: Pipeline orchestrators
  - `utils/`: Utility functions
- `tests/`: Test scripts

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run countries pipeline (generates `data/raw/countries.json` + `data/processed/countries_detailed.json`):
   ```bash
   python -B src/pipelines/countries.py
   ```
   If `data/processed/countries_detailed.json` already exists, the pipeline will only import it into SQLite.

3. Run persons pipeline (generates `data/raw/persons.json` + `data/processed/persons_detailed.json`):
   ```bash
   python -B src/pipelines/persons.py
   ```
   If `data/processed/persons_detailed.json` already exists, the pipeline will only import it into SQLite.

4. Run weapons pipeline (generates `data/raw/weapons.json` + `data/processed/weapons_detailed.json`):
   ```bash
   python -B src/pipelines/weapons.py
   ```

5. Test parsing:
   ```bash
   python -B tests/test_parsing.py
   python -B tests/test_person_details_html.py
   python -B tests/test_country_weapons_html.py
   python -B tests/test_weapon_details_html.py
   ```

## Usage

- `src/pipelines/countries.py`: Countries pipeline orchestrator
- `src/pipelines/persons.py`: Persons pipeline orchestrator
- `src/pipelines/weapons.py`: Weapons pipeline orchestrator
- `src/extract/countries.py`: Extract country list
- `src/parse/country_details.py`: Parse individual country details
