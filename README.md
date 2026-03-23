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

2. Run countries pipeline (gerenates `countries.json` + `countries_detailed.json`):
   ```bash
   python -B src/pipelines/countries.py
   ```

3. Run persons pipeline (generates `persons.json` + `persons_detailed.json`):
   ```bash
   python -B src/pipelines/persons.py
   ```

4. Test parsing:
   ```bash
   python -B tests/test_parsing.py
   python -B tests/test_person_details_html.py
   ```

## Usage

- `src/pipelines/countries.py`: Countries pipeline orchestrator
- `src/pipelines/persons.py`: Persons pipeline orchestrator
- `src/extract/countries.py`: Extract country list
- `src/parse/country_details.py`: Parse individual country details
