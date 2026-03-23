import sqlite3
import os
import json

try:
    from src.models.country import Country
except ImportError:
    import sys
    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from models.country import Country


def get_db_path():
    """Get database path in project root/data folder."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_folder = os.path.join(project_root, 'data')
    os.makedirs(db_folder, exist_ok=True)
    return os.path.join(db_folder, 'ww2.db')


def init_db():
    """Initialize database and create tables."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Drop legacy countries table to avoid stale model mismatch
    cursor.execute('DROP TABLE IF EXISTS countries')

    # Create alliances table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alliances (
            id_alliance INTEGER PRIMARY KEY AUTOINCREMENT,
            alliance_name TEXT UNIQUE NOT NULL
        )
    ''')

    # Raw layer: raw extraction JSON payload
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER,
            country_name TEXT,
            link TEXT,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
            UNIQUE(id_alliance, country_name, link) ON CONFLICT IGNORE
        )
    ''')

    # Deduplicate old raw data if any
    cursor.execute('''
        DELETE FROM raw_countries
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_countries
            GROUP BY id_alliance, country_name, link
        )
    ''')

    # Bronze layer: data parsed but not fully cleaned
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bronze_countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            id_alliance INTEGER,
            country_name TEXT,
            link TEXT,
            full_name TEXT,
            military_deaths INTEGER,
            civilian_deaths INTEGER,
            civilian_holocaust_deaths INTEGER,
            total_deaths INTEGER,
            population INTEGER,
            entry_date TEXT,
            flag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(raw_id) REFERENCES raw_countries(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
    ''')

    # Silver layer: cleaned/normalized data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS silver_countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bronze_id INTEGER,
            id_alliance INTEGER,
            country_name TEXT,
            link TEXT,
            full_name TEXT,
            military_deaths INTEGER,
            civilian_deaths INTEGER,
            civilian_holocaust_deaths INTEGER,
            total_deaths INTEGER,
            population INTEGER,
            entry_date TEXT,
            flag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(bronze_id) REFERENCES bronze_countries(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
    ''')

    # Raw layer: raw extraction JSON payload (persons)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER,
            country_name TEXT,
            country_link TEXT,
            person_name TEXT,
            person_link TEXT,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
            UNIQUE(id_alliance, country_name, person_link) ON CONFLICT IGNORE
        )
    ''')

    # Deduplicate old raw person data if any
    cursor.execute('''
        DELETE FROM raw_persons
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_persons
            GROUP BY id_alliance, country_name, person_link
        )
    ''')

    # Bronze layer: data parsed but not fully cleaned (persons)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bronze_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            id_alliance INTEGER,
            country_name TEXT,
            country_link TEXT,
            person_name TEXT,
            person_link TEXT,
            given_name TEXT,
            surname TEXT,
            born TEXT,
            died TEXT,
            category TEXT,
            gender TEXT,
            img TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(raw_id) REFERENCES raw_persons(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
    ''')

    # Silver layer: cleaned/normalized data (persons)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS silver_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bronze_id INTEGER,
            id_alliance INTEGER,
            full_name TEXT,
            country_name TEXT,
            country_link TEXT,
            person_link TEXT,
            born TEXT,
            died TEXT,
            category TEXT,
            gender TEXT,
            img TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(bronze_id) REFERENCES bronze_persons(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
    ''')

    # Gold layer: aggregation metrics by alliance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gold_section_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER UNIQUE,
            country_count INTEGER,
            total_military_deaths INTEGER,
            total_civilian_deaths INTEGER,
            total_holocaust_deaths INTEGER,
            total_population INTEGER,
            average_population REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE CASCADE
        )
    ''')

    # Gold layer: person aggregation metrics by alliance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gold_person_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER UNIQUE,
            person_count INTEGER,
            male_count INTEGER,
            female_count INTEGER,
            unknown_gender_count INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


def _get_id_alliance(cursor, section):
    cursor.execute('SELECT id_alliance FROM alliances WHERE alliance_name = ?', (section,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO alliances (alliance_name) VALUES (?)', (section,))
    return cursor.lastrowid


def insert_raw_country(raw_payload: dict, section: str):
    """Insert raw extracted JSON into raw_countries."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        cursor.execute('''
            INSERT OR IGNORE INTO raw_countries (id_alliance, country_name, link, payload)
            VALUES (?, ?, ?, ?)
        ''', (
            id_alliance,
            raw_payload.get('basic', {}).get('name'),
            raw_payload.get('basic', {}).get('link'),
            json.dumps(raw_payload, ensure_ascii=False)
        ))
        if cursor.lastrowid:
            raw_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM raw_countries
                WHERE id_alliance = ? AND country_name = ? AND link IS ?
                ORDER BY id LIMIT 1
            ''', (
                id_alliance,
                raw_payload.get('basic', {}).get('name'),
                raw_payload.get('basic', {}).get('link')
            ))
            row = cursor.fetchone()
            raw_id = row[0] if row else None

        conn.commit()
        return raw_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_bronze_country(raw_id: int, parsed_data: dict, section: str):
    """Insert parsed data into bronze layer."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        cursor.execute('''
            INSERT INTO bronze_countries (raw_id, id_alliance, country_name, link, full_name, military_deaths, civilian_deaths, civilian_holocaust_deaths, total_deaths, population, entry_date, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            raw_id,
            id_alliance,
            parsed_data['basic']['name'],
            parsed_data['basic']['link'],
            parsed_data['details'].get('full_name'),
            parsed_data['details'].get('millitary_deaths'),
            parsed_data['details'].get('civillian_deaths'),
            parsed_data['details'].get('civillian_holocaust_deaths'),
            parsed_data['details'].get('total_deaths'),
            parsed_data['details'].get('population'),
            parsed_data['details'].get('entry_date'),
            parsed_data['details'].get('flag')
        ))
        bronze_id = cursor.lastrowid
        conn.commit()
        return bronze_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_silver_country(bronze_id: int, parsed_data: dict, section: str):
    """Insert normalized data into silver layer."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)

        full_name = parsed_data['details'].get('full_name') or parsed_data['basic']['name']
        military = parsed_data['details'].get('millitary_deaths')
        civilian = parsed_data['details'].get('civillian_deaths')
        total = parsed_data['details'].get('total_deaths')
        if total is None and military is not None and civilian is not None:
            total = (military or 0) + (civilian or 0)

        cursor.execute('''
            INSERT INTO silver_countries (bronze_id, id_alliance, country_name, link, full_name, military_deaths, civilian_deaths, civilian_holocaust_deaths, total_deaths, population, entry_date, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bronze_id,
            id_alliance,
            parsed_data['basic']['name'],
            parsed_data['basic']['link'],
            full_name,
            military,
            civilian,
            parsed_data['details'].get('civillian_holocaust_deaths'),
            total,
            parsed_data['details'].get('population'),
            parsed_data['details'].get('entry_date'),
            parsed_data['details'].get('flag')
        ))
        silver_id = cursor.lastrowid
        conn.commit()
        return silver_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def refresh_gold_metrics(section: str):
    """Recalculate aggregation metrics for given section."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        cursor.execute('''
            SELECT
                COUNT(1),
                SUM(military_deaths),
                SUM(civilian_deaths),
                SUM(civilian_holocaust_deaths),
                SUM(population)
            FROM silver_countries
            WHERE id_alliance = ?
        ''', (id_alliance,))
        row = cursor.fetchone()
        country_count, sum_military, sum_civilian, sum_holocaust, sum_population = row
        avg_population = None
        if country_count and country_count > 0 and sum_population is not None:
            avg_population = sum_population / country_count

        cursor.execute('''
            INSERT INTO gold_section_metrics (id_alliance, country_count, total_military_deaths, total_civilian_deaths, total_holocaust_deaths, total_population, average_population, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id_alliance) DO UPDATE SET
                country_count=excluded.country_count,
                total_military_deaths=excluded.total_military_deaths,
                total_civilian_deaths=excluded.total_civilian_deaths,
                total_holocaust_deaths=excluded.total_holocaust_deaths,
                total_population=excluded.total_population,
                average_population=excluded.average_population,
                updated_at=CURRENT_TIMESTAMP
        ''', (
            id_alliance,
            country_count or 0,
            sum_military or 0,
            sum_civilian or 0,
            sum_holocaust or 0,
            sum_population or 0,
            avg_population
        ))
        conn.commit()
    finally:
        conn.close()


def insert_raw_person(raw_payload: dict, section: str):
    """Insert raw extracted JSON into raw_persons."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        cursor.execute('''
            INSERT OR IGNORE INTO raw_persons (id_alliance, country_name, country_link, person_name, person_link, payload)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            id_alliance,
            raw_payload.get('basic', {}).get('country_name'),
            raw_payload.get('basic', {}).get('country_link'),
            raw_payload.get('basic', {}).get('person_name'),
            raw_payload.get('basic', {}).get('person_link'),
            json.dumps(raw_payload, ensure_ascii=False)
        ))

        if cursor.lastrowid:
            raw_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM raw_persons
                WHERE id_alliance = ? AND country_name IS ? AND person_link = ?
                ORDER BY id LIMIT 1
            ''', (
                id_alliance,
                raw_payload.get('basic', {}).get('country_name'),
                raw_payload.get('basic', {}).get('person_link')
            ))
            row = cursor.fetchone()
            raw_id = row[0] if row else None

        conn.commit()
        return raw_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_bronze_person(raw_id: int, parsed_data: dict, section: str):
    """Insert parsed data into bronze_persons."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        details = parsed_data.get('details') or {}
        basic = parsed_data.get('basic') or {}

        cursor.execute('''
            INSERT INTO bronze_persons (
                raw_id, id_alliance, country_name, country_link, person_name, person_link,
                given_name, surname, born, died, category, gender, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            raw_id,
            id_alliance,
            basic.get('country_name'),
            basic.get('country_link'),
            basic.get('person_name'),
            basic.get('person_link'),
            details.get('name'),
            details.get('surname'),
            details.get('born'),
            details.get('died'),
            details.get('category'),
            details.get('gender'),
            details.get('img')
        ))

        bronze_id = cursor.lastrowid
        conn.commit()
        return bronze_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _split_basic_person_name(person_name: str):
    if not person_name:
        return None, None
    text = str(person_name).strip()
    if not text:
        return None, None
    if ',' in text:
        parts = [p.strip() for p in text.split(',', 1)]
        if len(parts) == 2:
            surname = parts[0] or None
            given_name = parts[1] or None
            return given_name, surname
    return text, None


def insert_silver_person(bronze_id: int, parsed_data: dict, section: str):
    """Insert normalized data into silver_persons."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        details = parsed_data.get('details') or {}
        basic = parsed_data.get('basic') or {}

        basic_person_name = (basic.get('person_name') or '').strip() or None

        given_name = (details.get('name') or '').strip() or None
        surname = (details.get('surname') or '').strip() or None
        if not given_name or not surname:
            fallback_given, fallback_surname = _split_basic_person_name(basic_person_name)
            given_name = given_name or fallback_given
            surname = surname or fallback_surname

        full_name = f"{given_name or ''} {surname or ''}".strip() or basic_person_name

        gender = details.get('gender')
        if gender is not None:
            gender = str(gender).strip() or None
            if gender:
                if gender.lower() == 'male':
                    gender = 'Male'
                elif gender.lower() == 'female':
                    gender = 'Female'

        cursor.execute('''
            INSERT INTO silver_persons (
                bronze_id, id_alliance, full_name, country_name, country_link, person_link,
                born, died, category, gender, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bronze_id,
            id_alliance,
            full_name,
            basic.get('country_name'),
            basic.get('country_link'),
            basic.get('person_link'),
            details.get('born'),
            details.get('died'),
            details.get('category'),
            gender,
            details.get('img')
        ))

        silver_id = cursor.lastrowid
        conn.commit()
        return silver_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def refresh_gold_person_metrics(section: str):
    """Recalculate person aggregation metrics for given section."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        cursor.execute('''
            SELECT
                COUNT(1),
                SUM(CASE WHEN LOWER(COALESCE(gender, '')) = 'male' THEN 1 ELSE 0 END),
                SUM(CASE WHEN LOWER(COALESCE(gender, '')) = 'female' THEN 1 ELSE 0 END),
                SUM(CASE
                    WHEN gender IS NULL OR TRIM(gender) = '' THEN 1
                    WHEN LOWER(gender) NOT IN ('male', 'female') THEN 1
                    ELSE 0
                END)
            FROM silver_persons
            WHERE id_alliance = ?
        ''', (id_alliance,))
        row = cursor.fetchone()
        person_count, male_count, female_count, unknown_count = row

        cursor.execute('''
            INSERT INTO gold_person_metrics (id_alliance, person_count, male_count, female_count, unknown_gender_count, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id_alliance) DO UPDATE SET
                person_count=excluded.person_count,
                male_count=excluded.male_count,
                female_count=excluded.female_count,
                unknown_gender_count=excluded.unknown_gender_count,
                updated_at=CURRENT_TIMESTAMP
        ''', (
            id_alliance,
            person_count or 0,
            male_count or 0,
            female_count or 0,
            unknown_count or 0
        ))
        conn.commit()
    finally:
        conn.close()


def get_all_alliances():
    """Fetch all alliances."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM alliances ORDER BY alliance_name')
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_silver_countries_by_alliance(alliance_name: str):
    """Fetch silver countries in a specific alliance."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT sc.*
        FROM silver_countries sc
        JOIN alliances a ON sc.id_alliance = a.id_alliance
        WHERE a.alliance_name = ?
        ORDER BY sc.country_name
    ''', (alliance_name,))
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_gold_metrics_by_alliance(alliance_name: str):
    """Fetch gold metrics for an alliance."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT gm.*
        FROM gold_section_metrics gm
        JOIN alliances a ON gm.id_alliance = a.id_alliance
        WHERE a.alliance_name = ?
    ''', (alliance_name,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_silver_persons_by_alliance(alliance_name: str):
    """Fetch silver persons in a specific alliance."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT sp.*
        FROM silver_persons sp
        JOIN alliances a ON sp.id_alliance = a.id_alliance
        WHERE a.alliance_name = ?
        ORDER BY sp.full_name
    ''', (alliance_name,))
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_gold_person_metrics_by_alliance(alliance_name: str):
    """Fetch gold person metrics for an alliance."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT gpm.*
        FROM gold_person_metrics gpm
        JOIN alliances a ON gpm.id_alliance = a.id_alliance
        WHERE a.alliance_name = ?
    ''', (alliance_name,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def clear_db():
    """Clear all data from database."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM raw_countries')
    cursor.execute('DELETE FROM bronze_countries')
    cursor.execute('DELETE FROM silver_countries')
    cursor.execute('DELETE FROM gold_section_metrics')
    cursor.execute('DELETE FROM raw_persons')
    cursor.execute('DELETE FROM bronze_persons')
    cursor.execute('DELETE FROM silver_persons')
    cursor.execute('DELETE FROM gold_person_metrics')
    cursor.execute('DELETE FROM alliances')
    
    conn.commit()
    conn.close()
