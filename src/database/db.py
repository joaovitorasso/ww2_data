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
    cursor.execute('''
        DELETE FROM bronze_countries
        WHERE raw_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM bronze_countries
              WHERE raw_id IS NOT NULL
              GROUP BY raw_id
          )
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bronze_countries_raw_id
        ON bronze_countries(raw_id)
        WHERE raw_id IS NOT NULL
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
    cursor.execute('''
        DELETE FROM silver_countries
        WHERE bronze_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM silver_countries
              WHERE bronze_id IS NOT NULL
              GROUP BY bronze_id
          )
    ''')
    cursor.execute('''
        DELETE FROM silver_countries
        WHERE id NOT IN (
            SELECT MIN(id) FROM silver_countries
            GROUP BY id_alliance, country_name, link
        )
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_countries_bronze_id
        ON silver_countries(bronze_id)
        WHERE bronze_id IS NOT NULL
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_countries_logical_key
        ON silver_countries(id_alliance, country_name, link)
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
    cursor.execute('''
        DELETE FROM bronze_persons
        WHERE raw_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM bronze_persons
              WHERE raw_id IS NOT NULL
              GROUP BY raw_id
          )
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bronze_persons_raw_id
        ON bronze_persons(raw_id)
        WHERE raw_id IS NOT NULL
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
    cursor.execute('''
        DELETE FROM silver_persons
        WHERE bronze_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM silver_persons
              WHERE bronze_id IS NOT NULL
              GROUP BY bronze_id
          )
    ''')
    cursor.execute('''
        DELETE FROM silver_persons
        WHERE id NOT IN (
            SELECT MIN(id) FROM silver_persons
            GROUP BY id_alliance, country_name, person_link
        )
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_persons_bronze_id
        ON silver_persons(bronze_id)
        WHERE bronze_id IS NOT NULL
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_persons_logical_key
        ON silver_persons(id_alliance, country_name, person_link)
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

    # Raw layer: raw extraction JSON payload (weapons)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER,
            country_name TEXT,
            country_link TEXT,
            weapon_name TEXT,
            weapon_link TEXT,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
            UNIQUE(id_alliance, country_name, weapon_link) ON CONFLICT IGNORE
        )
    ''')

    # Deduplicate old raw weapon data if any
    cursor.execute('''
        DELETE FROM raw_weapons
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_weapons
            GROUP BY id_alliance, country_name, weapon_link
        )
    ''')

    # Bronze layer: data parsed but not fully cleaned (weapons)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bronze_weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            id_alliance INTEGER,
            country_name TEXT,
            country_link TEXT,
            weapon_name TEXT,
            weapon_link TEXT,
            origin_country TEXT,
            weapon_type TEXT,
            caliber TEXT,
            capacity TEXT,
            length TEXT,
            barrel_length TEXT,
            weight TEXT,
            range_value TEXT,
            muzzle_velocity TEXT,
            img TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(raw_id) REFERENCES raw_weapons(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
    ''')
    cursor.execute('''
        DELETE FROM bronze_weapons
        WHERE raw_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM bronze_weapons
              WHERE raw_id IS NOT NULL
              GROUP BY raw_id
          )
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bronze_weapons_raw_id
        ON bronze_weapons(raw_id)
        WHERE raw_id IS NOT NULL
    ''')

    # Silver layer: cleaned/normalized data (weapons)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS silver_weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bronze_id INTEGER,
            id_alliance INTEGER,
            full_name TEXT,
            country_name TEXT,
            country_link TEXT,
            weapon_link TEXT,
            origin_country TEXT,
            weapon_type TEXT,
            caliber TEXT,
            capacity TEXT,
            length TEXT,
            barrel_length TEXT,
            weight TEXT,
            range_value TEXT,
            muzzle_velocity TEXT,
            img TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(bronze_id) REFERENCES bronze_weapons(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
    ''')
    cursor.execute('''
        DELETE FROM silver_weapons
        WHERE bronze_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM silver_weapons
              WHERE bronze_id IS NOT NULL
              GROUP BY bronze_id
          )
    ''')
    cursor.execute('''
        DELETE FROM silver_weapons
        WHERE id NOT IN (
            SELECT MIN(id) FROM silver_weapons
            GROUP BY id_alliance, country_name, weapon_link
        )
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_weapons_bronze_id
        ON silver_weapons(bronze_id)
        WHERE bronze_id IS NOT NULL
    ''')
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_weapons_logical_key
        ON silver_weapons(id_alliance, country_name, weapon_link)
    ''')

    # Gold layer: weapon aggregation metrics by alliance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gold_weapon_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER UNIQUE,
            weapon_count INTEGER,
            unknown_type_count INTEGER,
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
            INSERT OR IGNORE INTO bronze_countries (raw_id, id_alliance, country_name, link, full_name, military_deaths, civilian_deaths, civilian_holocaust_deaths, total_deaths, population, entry_date, flag)
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

        if cursor.lastrowid:
            bronze_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM bronze_countries
                WHERE raw_id = ?
                ORDER BY id LIMIT 1
            ''', (raw_id,))
            row = cursor.fetchone()
            bronze_id = row[0] if row else None

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
            INSERT OR IGNORE INTO silver_countries (bronze_id, id_alliance, country_name, link, full_name, military_deaths, civilian_deaths, civilian_holocaust_deaths, total_deaths, population, entry_date, flag)
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

        if cursor.lastrowid:
            silver_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM silver_countries
                WHERE bronze_id = ?
                ORDER BY id LIMIT 1
            ''', (bronze_id,))
            row = cursor.fetchone()
            silver_id = row[0] if row else None

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
            INSERT OR IGNORE INTO bronze_persons (
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

        if cursor.lastrowid:
            bronze_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM bronze_persons
                WHERE raw_id = ?
                ORDER BY id LIMIT 1
            ''', (raw_id,))
            row = cursor.fetchone()
            bronze_id = row[0] if row else None

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
            INSERT OR IGNORE INTO silver_persons (
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

        if cursor.lastrowid:
            silver_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM silver_persons
                WHERE bronze_id = ?
                ORDER BY id LIMIT 1
            ''', (bronze_id,))
            row = cursor.fetchone()
            silver_id = row[0] if row else None

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


def insert_raw_weapon(raw_payload: dict, section: str):
    """Insert raw extracted JSON into raw_weapons."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        cursor.execute('''
            INSERT OR IGNORE INTO raw_weapons (id_alliance, country_name, country_link, weapon_name, weapon_link, payload)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            id_alliance,
            raw_payload.get('basic', {}).get('country_name'),
            raw_payload.get('basic', {}).get('country_link'),
            raw_payload.get('basic', {}).get('weapon_name'),
            raw_payload.get('basic', {}).get('weapon_link'),
            json.dumps(raw_payload, ensure_ascii=False)
        ))

        if cursor.lastrowid:
            raw_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM raw_weapons
                WHERE id_alliance = ? AND country_name IS ? AND weapon_link = ?
                ORDER BY id LIMIT 1
            ''', (
                id_alliance,
                raw_payload.get('basic', {}).get('country_name'),
                raw_payload.get('basic', {}).get('weapon_link')
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


def insert_bronze_weapon(raw_id: int, parsed_data: dict, section: str):
    """Insert parsed data into bronze_weapons."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        details = parsed_data.get('details') or {}
        basic = parsed_data.get('basic') or {}

        cursor.execute('''
            INSERT OR IGNORE INTO bronze_weapons (
                raw_id, id_alliance, country_name, country_link, weapon_name, weapon_link,
                origin_country, weapon_type, caliber, capacity, length, barrel_length,
                weight, range_value, muzzle_velocity, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            raw_id,
            id_alliance,
            basic.get('country_name'),
            basic.get('country_link'),
            basic.get('weapon_name'),
            basic.get('weapon_link'),
            details.get('country'),
            details.get('type'),
            details.get('caliber'),
            details.get('capacity'),
            details.get('lenght'),
            details.get('barrel_lenght'),
            details.get('weight'),
            details.get('range'),
            details.get('muzzle_velocity'),
            details.get('img')
        ))

        if cursor.lastrowid:
            bronze_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM bronze_weapons
                WHERE raw_id = ?
                ORDER BY id LIMIT 1
            ''', (raw_id,))
            row = cursor.fetchone()
            bronze_id = row[0] if row else None

        conn.commit()
        return bronze_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_silver_weapon(bronze_id: int, parsed_data: dict, section: str):
    """Insert normalized data into silver_weapons."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        details = parsed_data.get('details') or {}
        basic = parsed_data.get('basic') or {}

        basic_weapon_name = (basic.get('weapon_name') or '').strip() or None
        full_name = (details.get('name') or '').strip() or basic_weapon_name

        origin_country = (details.get('country') or '').strip() or None
        weapon_type = (details.get('type') or '').strip() or None
        caliber = (details.get('caliber') or '').strip() or None
        capacity = (details.get('capacity') or '').strip() or None
        length = (details.get('lenght') or '').strip() or None
        barrel_length = (details.get('barrel_lenght') or '').strip() or None
        weight = (details.get('weight') or '').strip() or None
        range_value = (details.get('range') or '').strip() or None
        muzzle_velocity = (details.get('muzzle_velocity') or '').strip() or None
        img = (details.get('img') or '').strip() or None

        cursor.execute('''
            INSERT OR IGNORE INTO silver_weapons (
                bronze_id, id_alliance, full_name, country_name, country_link, weapon_link,
                origin_country, weapon_type, caliber, capacity, length, barrel_length,
                weight, range_value, muzzle_velocity, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bronze_id,
            id_alliance,
            full_name,
            basic.get('country_name'),
            basic.get('country_link'),
            basic.get('weapon_link'),
            origin_country,
            weapon_type,
            caliber,
            capacity,
            length,
            barrel_length,
            weight,
            range_value,
            muzzle_velocity,
            img
        ))

        if cursor.lastrowid:
            silver_id = cursor.lastrowid
        else:
            cursor.execute('''
                SELECT id FROM silver_weapons
                WHERE bronze_id = ?
                ORDER BY id LIMIT 1
            ''', (bronze_id,))
            row = cursor.fetchone()
            silver_id = row[0] if row else None

        conn.commit()
        return silver_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def refresh_gold_weapon_metrics(section: str):
    """Recalculate weapon aggregation metrics for given section."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = _get_id_alliance(cursor, section)
        cursor.execute('''
            SELECT
                COUNT(1),
                SUM(CASE
                    WHEN weapon_type IS NULL OR TRIM(weapon_type) = '' THEN 1
                    ELSE 0
                END)
            FROM silver_weapons
            WHERE id_alliance = ?
        ''', (id_alliance,))
        row = cursor.fetchone()
        weapon_count, unknown_type_count = row

        cursor.execute('''
            INSERT INTO gold_weapon_metrics (id_alliance, weapon_count, unknown_type_count, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id_alliance) DO UPDATE SET
                weapon_count=excluded.weapon_count,
                unknown_type_count=excluded.unknown_type_count,
                updated_at=CURRENT_TIMESTAMP
        ''', (
            id_alliance,
            weapon_count or 0,
            unknown_type_count or 0
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
    cursor.execute('DELETE FROM raw_weapons')
    cursor.execute('DELETE FROM bronze_weapons')
    cursor.execute('DELETE FROM silver_weapons')
    cursor.execute('DELETE FROM gold_weapon_metrics')
    cursor.execute('DELETE FROM alliances')
    
    conn.commit()
    conn.close()
