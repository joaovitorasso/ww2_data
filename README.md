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
  - `utils/`: Utility functions
- `scripts/`: Execution scripts

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run extraction:
   ```bash
   python -B scripts/run_extraction.py
   ```

3. Test parsing:
   ```bash
   python -B scripts/test_parsing.py
   ```

## Usage

- `src/main.py`: Main orchestrator
- `src/extract/countries.py`: Extract country list
- `src/parse/country_details.py`: Parse individual country details