try:
    from src.database.common import get_connection
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_connection


def init_db() -> None:
    """Create or migrate database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    def _has_column(table_name: str, column_name: str) -> bool:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return any(row[1] == column_name for row in cursor.fetchall())

    def _table_exists(table_name: str) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            LIMIT 1
            """,
            (table_name,),
        )
        return cursor.fetchone() is not None

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alliances (
            id_alliance INTEGER PRIMARY KEY AUTOINCREMENT,
            alliance_name TEXT UNIQUE NOT NULL
        )
        """
    )

    cursor.execute(
        """
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
        """
    )
    cursor.execute(
        """
        DELETE FROM raw_countries
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_countries
            GROUP BY id_alliance, country_name, link
        )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_countries_logical_key_nn
        ON raw_countries(id_alliance, country_name, COALESCE(link, ''))
        """
    )

    cursor.execute(
        """
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
        """
    )
    cursor.execute(
        """
        DELETE FROM bronze_countries
        WHERE raw_id IS NULL
           OR raw_id NOT IN (SELECT id FROM raw_countries)
        """
    )
    cursor.execute(
        """
        DELETE FROM bronze_countries
        WHERE raw_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM bronze_countries
              WHERE raw_id IS NOT NULL
              GROUP BY raw_id
          )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bronze_countries_raw_id
        ON bronze_countries(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS silver_countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bronze_id INTEGER,
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
            FOREIGN KEY(bronze_id) REFERENCES bronze_countries(id) ON DELETE CASCADE,
            FOREIGN KEY(raw_id) REFERENCES raw_countries(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_countries
        WHERE bronze_id IS NULL
           OR bronze_id NOT IN (SELECT id FROM bronze_countries)
           OR raw_id IS NULL
           OR raw_id NOT IN (SELECT id FROM raw_countries)
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_countries
        WHERE bronze_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM silver_countries
              WHERE bronze_id IS NOT NULL
              GROUP BY bronze_id
          )
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_countries
        WHERE id NOT IN (
            SELECT MIN(id) FROM silver_countries
            GROUP BY id_alliance, country_name, link
        )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_countries_bronze_id
        ON silver_countries(bronze_id)
        WHERE bronze_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_countries_logical_key
        ON silver_countries(id_alliance, country_name, link)
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_countries_logical_key_nn
        ON silver_countries(id_alliance, country_name, COALESCE(link, ''))
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER,
            country_id INTEGER,
            country_name TEXT,
            country_link TEXT,
            person_name TEXT,
            person_link TEXT,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            UNIQUE(id_alliance, country_name, person_link) ON CONFLICT IGNORE
        )
        """
    )
    cursor.execute(
        """
        DELETE FROM raw_persons
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_persons
            GROUP BY id_alliance, country_name, person_link
        )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_persons_logical_key_nn
        ON raw_persons(id_alliance, country_name, COALESCE(person_link, ''))
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bronze_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            country_id INTEGER,
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
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
        """
    )
    cursor.execute(
        """
        DELETE FROM bronze_persons
        WHERE raw_id IS NULL
           OR raw_id NOT IN (SELECT id FROM raw_persons)
        """
    )
    cursor.execute(
        """
        DELETE FROM bronze_persons
        WHERE raw_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM bronze_persons
              WHERE raw_id IS NOT NULL
              GROUP BY raw_id
          )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bronze_persons_raw_id
        ON bronze_persons(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS silver_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bronze_id INTEGER,
            raw_id INTEGER,
            country_id INTEGER,
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
            FOREIGN KEY(raw_id) REFERENCES raw_persons(id) ON DELETE CASCADE,
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_persons
        WHERE bronze_id IS NULL
           OR bronze_id NOT IN (SELECT id FROM bronze_persons)
           OR raw_id IS NULL
           OR raw_id NOT IN (SELECT id FROM raw_persons)
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_persons
        WHERE bronze_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM silver_persons
              WHERE bronze_id IS NOT NULL
              GROUP BY bronze_id
          )
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_persons
        WHERE id NOT IN (
            SELECT MIN(id) FROM silver_persons
            GROUP BY id_alliance, country_name, person_link
        )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_persons_bronze_id
        ON silver_persons(bronze_id)
        WHERE bronze_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_persons_logical_key
        ON silver_persons(id_alliance, country_name, person_link)
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_persons_logical_key_nn
        ON silver_persons(id_alliance, country_name, COALESCE(person_link, ''))
        """
    )

    cursor.execute("DROP TABLE IF EXISTS gold_section_metrics")
    cursor.execute("DROP TABLE IF EXISTS gold_alliance_metrics")
    cursor.execute("DROP TABLE IF EXISTS gold_person_metrics")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alliance INTEGER,
            country_id INTEGER,
            country_name TEXT,
            country_link TEXT,
            weapon_name TEXT,
            weapon_link TEXT,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            UNIQUE(id_alliance, country_name, weapon_link) ON CONFLICT IGNORE
        )
        """
    )
    cursor.execute(
        """
        DELETE FROM raw_weapons
        WHERE id NOT IN (
            SELECT MIN(id) FROM raw_weapons
            GROUP BY id_alliance, country_name, weapon_link
        )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_weapons_logical_key_nn
        ON raw_weapons(id_alliance, country_name, COALESCE(weapon_link, ''))
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bronze_weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            country_id INTEGER,
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
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
        """
    )
    cursor.execute(
        """
        DELETE FROM bronze_weapons
        WHERE raw_id IS NULL
           OR raw_id NOT IN (SELECT id FROM raw_weapons)
        """
    )
    cursor.execute(
        """
        DELETE FROM bronze_weapons
        WHERE raw_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM bronze_weapons
              WHERE raw_id IS NOT NULL
              GROUP BY raw_id
          )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bronze_weapons_raw_id
        ON bronze_weapons(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS silver_weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bronze_id INTEGER,
            raw_id INTEGER,
            country_id INTEGER,
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
            FOREIGN KEY(raw_id) REFERENCES raw_weapons(id) ON DELETE CASCADE,
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL
        )
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_weapons
        WHERE bronze_id IS NULL
           OR bronze_id NOT IN (SELECT id FROM bronze_weapons)
           OR raw_id IS NULL
           OR raw_id NOT IN (SELECT id FROM raw_weapons)
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_weapons
        WHERE bronze_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id) FROM silver_weapons
              WHERE bronze_id IS NOT NULL
              GROUP BY bronze_id
          )
        """
    )
    cursor.execute(
        """
        DELETE FROM silver_weapons
        WHERE id NOT IN (
            SELECT MIN(id) FROM silver_weapons
            GROUP BY id_alliance, country_name, weapon_link
        )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_weapons_bronze_id
        ON silver_weapons(bronze_id)
        WHERE bronze_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_weapons_logical_key
        ON silver_weapons(id_alliance, country_name, weapon_link)
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_weapons_logical_key_nn
        ON silver_weapons(id_alliance, country_name, COALESCE(weapon_link, ''))
        """
    )

    cursor.execute("DROP TABLE IF EXISTS gold_weapon_metrics")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS retry_countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            section TEXT NOT NULL,
            country_name TEXT,
            link TEXT,
            payload TEXT NOT NULL,
            last_error TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(raw_id) REFERENCES raw_countries(id) ON DELETE CASCADE,
            UNIQUE(section, link)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS retry_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            country_id INTEGER,
            id_alliance INTEGER,
            country_name TEXT,
            person_name TEXT,
            person_link TEXT,
            payload TEXT NOT NULL,
            last_error TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(raw_id) REFERENCES raw_persons(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            UNIQUE(id_alliance, person_link)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS retry_weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            country_id INTEGER,
            id_alliance INTEGER,
            country_name TEXT,
            weapon_name TEXT,
            weapon_link TEXT,
            payload TEXT NOT NULL,
            last_error TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(raw_id) REFERENCES raw_weapons(id) ON DELETE CASCADE,
            FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
            FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
            UNIQUE(id_alliance, weapon_link)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_execution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_type TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            inserted_rows INTEGER DEFAULT 0,
            updated_rows INTEGER DEFAULT 0,
            deleted_rows INTEGER DEFAULT 0,
            affected_rows INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running'
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_execution_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_execution_id INTEGER,
            pipeline_type TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(current_execution_id) REFERENCES pipeline_execution_log(id) ON DELETE SET NULL
        )
        """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO pipeline_execution_state (id, current_execution_id, pipeline_type)
        VALUES (1, NULL, NULL)
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS country_html_cache_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total INTEGER NOT NULL,
            cached INTEGER NOT NULL,
            fetched INTEGER NOT NULL,
            errors INTEGER NOT NULL
        )
        """
    )

    if _table_exists("retry_persons") and _has_column("retry_persons", "alliance") and not _has_column("retry_persons", "id_alliance"):
        cursor.execute("ALTER TABLE retry_persons RENAME TO retry_persons_legacy")
        cursor.execute(
            """
            CREATE TABLE retry_persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_id INTEGER,
                country_id INTEGER,
                id_alliance INTEGER,
                country_name TEXT,
                person_name TEXT,
                person_link TEXT,
                payload TEXT NOT NULL,
                last_error TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(raw_id) REFERENCES raw_persons(id) ON DELETE CASCADE,
                FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
                FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
                UNIQUE(id_alliance, person_link)
            )
            """
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO retry_persons (
                raw_id, country_id, id_alliance, country_name, person_name, person_link,
                payload, last_error, retry_count, created_at, updated_at
            )
            SELECT
                rp.raw_id,
                rp.country_id,
                a.id_alliance,
                rp.country_name,
                rp.person_name,
                rp.person_link,
                rp.payload,
                rp.last_error,
                rp.retry_count,
                rp.created_at,
                rp.updated_at
            FROM retry_persons_legacy rp
            LEFT JOIN alliances a ON a.alliance_name = rp.alliance
            """
        )
        cursor.execute("DROP TABLE retry_persons_legacy")

    if _table_exists("retry_weapons") and _has_column("retry_weapons", "alliance") and not _has_column("retry_weapons", "id_alliance"):
        cursor.execute("ALTER TABLE retry_weapons RENAME TO retry_weapons_legacy")
        cursor.execute(
            """
            CREATE TABLE retry_weapons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_id INTEGER,
                country_id INTEGER,
                id_alliance INTEGER,
                country_name TEXT,
                weapon_name TEXT,
                weapon_link TEXT,
                payload TEXT NOT NULL,
                last_error TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(raw_id) REFERENCES raw_weapons(id) ON DELETE CASCADE,
                FOREIGN KEY(id_alliance) REFERENCES alliances(id_alliance) ON DELETE SET NULL,
                FOREIGN KEY(country_id) REFERENCES raw_countries(id) ON DELETE SET NULL,
                UNIQUE(id_alliance, weapon_link)
            )
            """
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO retry_weapons (
                raw_id, country_id, id_alliance, country_name, weapon_name, weapon_link,
                payload, last_error, retry_count, created_at, updated_at
            )
            SELECT
                rw.raw_id,
                rw.country_id,
                a.id_alliance,
                rw.country_name,
                rw.weapon_name,
                rw.weapon_link,
                rw.payload,
                rw.last_error,
                rw.retry_count,
                rw.created_at,
                rw.updated_at
            FROM retry_weapons_legacy rw
            LEFT JOIN alliances a ON a.alliance_name = rw.alliance
            """
        )
        cursor.execute("DROP TABLE retry_weapons_legacy")

    if _table_exists("country_html_cache_log") and not _has_column("country_html_cache_log", "id"):
        cursor.execute("ALTER TABLE country_html_cache_log RENAME TO country_html_cache_log_legacy")
        cursor.execute(
            """
            CREATE TABLE country_html_cache_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total INTEGER NOT NULL,
                cached INTEGER NOT NULL,
                fetched INTEGER NOT NULL,
                errors INTEGER NOT NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO country_html_cache_log (data, total, cached, fetched, errors)
            SELECT data, total, cached, fetched, errors
            FROM country_html_cache_log_legacy
            """
        )
        cursor.execute("DROP TABLE country_html_cache_log_legacy")

    # Migration for existing databases: add standardized ID columns when missing
    if not _has_column("silver_countries", "raw_id"):
        cursor.execute("ALTER TABLE silver_countries ADD COLUMN raw_id INTEGER")
    if not _has_column("silver_persons", "raw_id"):
        cursor.execute("ALTER TABLE silver_persons ADD COLUMN raw_id INTEGER")
    if not _has_column("silver_weapons", "raw_id"):
        cursor.execute("ALTER TABLE silver_weapons ADD COLUMN raw_id INTEGER")
    if not _has_column("retry_countries", "raw_id"):
        cursor.execute("ALTER TABLE retry_countries ADD COLUMN raw_id INTEGER")
    if not _has_column("retry_persons", "raw_id"):
        cursor.execute("ALTER TABLE retry_persons ADD COLUMN raw_id INTEGER")
    if not _has_column("retry_weapons", "raw_id"):
        cursor.execute("ALTER TABLE retry_weapons ADD COLUMN raw_id INTEGER")
    if not _has_column("retry_persons", "id_alliance"):
        cursor.execute("ALTER TABLE retry_persons ADD COLUMN id_alliance INTEGER")
    if not _has_column("retry_weapons", "id_alliance"):
        cursor.execute("ALTER TABLE retry_weapons ADD COLUMN id_alliance INTEGER")
    if not _has_column("raw_persons", "country_id"):
        cursor.execute("ALTER TABLE raw_persons ADD COLUMN country_id INTEGER")
    if not _has_column("bronze_persons", "country_id"):
        cursor.execute("ALTER TABLE bronze_persons ADD COLUMN country_id INTEGER")
    if not _has_column("silver_persons", "country_id"):
        cursor.execute("ALTER TABLE silver_persons ADD COLUMN country_id INTEGER")
    if not _has_column("retry_persons", "country_id"):
        cursor.execute("ALTER TABLE retry_persons ADD COLUMN country_id INTEGER")
    if not _has_column("raw_weapons", "country_id"):
        cursor.execute("ALTER TABLE raw_weapons ADD COLUMN country_id INTEGER")
    if not _has_column("bronze_weapons", "country_id"):
        cursor.execute("ALTER TABLE bronze_weapons ADD COLUMN country_id INTEGER")
    if not _has_column("silver_weapons", "country_id"):
        cursor.execute("ALTER TABLE silver_weapons ADD COLUMN country_id INTEGER")
    if not _has_column("retry_weapons", "country_id"):
        cursor.execute("ALTER TABLE retry_weapons ADD COLUMN country_id INTEGER")

    # Backfill standardized IDs from bronze -> silver relation
    cursor.execute(
        """
        UPDATE silver_countries
        SET raw_id = (
            SELECT bc.raw_id
            FROM bronze_countries bc
            WHERE bc.id = silver_countries.bronze_id
        )
        WHERE raw_id IS NULL
        """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO raw_countries (id_alliance, country_name, link, payload)
        SELECT rp.id_alliance, rp.country_name, rp.country_link, '{}'
        FROM raw_persons rp
        WHERE rp.id_alliance IS NOT NULL
          AND (rp.country_name IS NOT NULL OR rp.country_link IS NOT NULL)
        """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO raw_countries (id_alliance, country_name, link, payload)
        SELECT rw.id_alliance, rw.country_name, rw.country_link, '{}'
        FROM raw_weapons rw
        WHERE rw.id_alliance IS NOT NULL
          AND (rw.country_name IS NOT NULL OR rw.country_link IS NOT NULL)
        """
    )
    cursor.execute(
        """
        UPDATE raw_persons
        SET country_id = (
            SELECT rc.id
            FROM raw_countries rc
            WHERE rc.id_alliance = raw_persons.id_alliance
              AND (
                (raw_persons.country_link IS NOT NULL AND rc.link = raw_persons.country_link)
                OR (raw_persons.country_link IS NULL AND rc.country_name = raw_persons.country_name)
              )
            ORDER BY rc.id
            LIMIT 1
        )
        WHERE country_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE raw_weapons
        SET country_id = (
            SELECT rc.id
            FROM raw_countries rc
            WHERE rc.id_alliance = raw_weapons.id_alliance
              AND (
                (raw_weapons.country_link IS NOT NULL AND rc.link = raw_weapons.country_link)
                OR (raw_weapons.country_link IS NULL AND rc.country_name = raw_weapons.country_name)
              )
            ORDER BY rc.id
            LIMIT 1
        )
        WHERE country_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE bronze_persons
        SET country_id = (
            SELECT rp.country_id
            FROM raw_persons rp
            WHERE rp.id = bronze_persons.raw_id
        )
        WHERE country_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE bronze_weapons
        SET country_id = (
            SELECT rw.country_id
            FROM raw_weapons rw
            WHERE rw.id = bronze_weapons.raw_id
        )
        WHERE country_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE silver_persons
        SET raw_id = (
            SELECT bp.raw_id
            FROM bronze_persons bp
            WHERE bp.id = silver_persons.bronze_id
        )
        WHERE raw_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE silver_persons
        SET country_id = (
            SELECT bp.country_id
            FROM bronze_persons bp
            WHERE bp.id = silver_persons.bronze_id
        )
        WHERE country_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE silver_weapons
        SET raw_id = (
            SELECT bw.raw_id
            FROM bronze_weapons bw
            WHERE bw.id = silver_weapons.bronze_id
        )
        WHERE raw_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE silver_weapons
        SET country_id = (
            SELECT bw.country_id
            FROM bronze_weapons bw
            WHERE bw.id = silver_weapons.bronze_id
        )
        WHERE country_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE retry_countries
        SET raw_id = (
            SELECT rc.id
            FROM raw_countries rc
            JOIN alliances a ON a.id_alliance = rc.id_alliance
            WHERE a.alliance_name = retry_countries.section
              AND rc.link = retry_countries.link
            ORDER BY rc.id
            LIMIT 1
        )
        WHERE raw_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE retry_persons
        SET id_alliance = (
            SELECT rp.id_alliance
            FROM raw_persons rp
            WHERE rp.id = retry_persons.raw_id
        )
        WHERE id_alliance IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE retry_persons
        SET raw_id = (
            SELECT rp.id
            FROM raw_persons rp
            WHERE rp.id_alliance = retry_persons.id_alliance
              AND rp.person_link = retry_persons.person_link
            ORDER BY rp.id
            LIMIT 1
        )
        WHERE raw_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE retry_persons
        SET country_id = (
            SELECT rp.country_id
            FROM raw_persons rp
            WHERE rp.id = retry_persons.raw_id
        )
        WHERE country_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE retry_weapons
        SET id_alliance = (
            SELECT rw.id_alliance
            FROM raw_weapons rw
            WHERE rw.id = retry_weapons.raw_id
        )
        WHERE id_alliance IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE retry_weapons
        SET raw_id = (
            SELECT rw.id
            FROM raw_weapons rw
            WHERE rw.id_alliance = retry_weapons.id_alliance
              AND rw.weapon_link = retry_weapons.weapon_link
            ORDER BY rw.id
            LIMIT 1
        )
        WHERE raw_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE retry_weapons
        SET country_id = (
            SELECT rw.country_id
            FROM raw_weapons rw
            WHERE rw.id = retry_weapons.raw_id
        )
        WHERE country_id IS NULL
        """
    )

    # Retry queues should also guarantee one row per raw_id when available
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_retry_countries_raw_id
        ON retry_countries(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_countries_raw_id
        ON silver_countries(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_persons_raw_id
        ON silver_persons(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_weapons_raw_id
        ON silver_weapons(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_retry_persons_raw_id
        ON retry_persons(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        DELETE FROM retry_persons
        WHERE id_alliance IS NOT NULL
          AND person_link IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id)
              FROM retry_persons
              WHERE id_alliance IS NOT NULL
                AND person_link IS NOT NULL
              GROUP BY id_alliance, person_link
          )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_retry_persons_alliance_link
        ON retry_persons(id_alliance, person_link)
        WHERE id_alliance IS NOT NULL AND person_link IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_retry_weapons_raw_id
        ON retry_weapons(raw_id)
        WHERE raw_id IS NOT NULL
        """
    )
    cursor.execute(
        """
        DELETE FROM retry_weapons
        WHERE id_alliance IS NOT NULL
          AND weapon_link IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id)
              FROM retry_weapons
              WHERE id_alliance IS NOT NULL
                AND weapon_link IS NOT NULL
              GROUP BY id_alliance, weapon_link
          )
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_retry_weapons_alliance_link
        ON retry_weapons(id_alliance, weapon_link)
        WHERE id_alliance IS NOT NULL AND weapon_link IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_raw_persons_country_id
        ON raw_persons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bronze_persons_country_id
        ON bronze_persons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_silver_persons_country_id
        ON silver_persons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_retry_persons_country_id
        ON retry_persons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_raw_weapons_country_id
        ON raw_weapons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bronze_weapons_country_id
        ON bronze_weapons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_silver_weapons_country_id
        ON silver_weapons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_retry_weapons_country_id
        ON retry_weapons(country_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_execution_log_type_started
        ON pipeline_execution_log(pipeline_type, started_at)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pipeline_execution_log_status
        ON pipeline_execution_log(status)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_country_html_cache_log_data
        ON country_html_cache_log(data)
        """
    )
    cursor.execute("DROP TRIGGER IF EXISTS trg_pipeline_execution_gold_section_metrics_insert")
    cursor.execute("DROP TRIGGER IF EXISTS trg_pipeline_execution_gold_section_metrics_update")
    cursor.execute("DROP TRIGGER IF EXISTS trg_pipeline_execution_gold_section_metrics_delete")

    tracked_tables = [
        "alliances",
        "raw_countries",
        "bronze_countries",
        "silver_countries",
        "raw_persons",
        "bronze_persons",
        "silver_persons",
        "raw_weapons",
        "bronze_weapons",
        "silver_weapons",
        "retry_countries",
        "retry_persons",
        "retry_weapons",
    ]
    event_to_column = {
        "insert": "inserted_rows",
        "update": "updated_rows",
        "delete": "deleted_rows",
    }
    for table_name in tracked_tables:
        for event_name, metric_column in event_to_column.items():
            cursor.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS trg_pipeline_execution_{table_name}_{event_name}
                AFTER {event_name.upper()} ON {table_name}
                WHEN (SELECT current_execution_id FROM pipeline_execution_state WHERE id = 1) IS NOT NULL
                BEGIN
                    UPDATE pipeline_execution_log
                    SET {metric_column} = {metric_column} + 1,
                        affected_rows = affected_rows + 1
                    WHERE id = (SELECT current_execution_id FROM pipeline_execution_state WHERE id = 1);
                END;
                """
            )

    conn.commit()
    conn.close()
