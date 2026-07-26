import sqlite3
import os
import json
from pathlib import Path

SEED_FILE = Path(__file__).parent / 'data' / 'led_tiles.json'

# Names seeded by an earlier version of this file from unverified web research.
# Removed once verified sources were unavailable for these brands; deleted here
# so databases that already picked them up get cleaned up too.
_RETRACTED_TILE_NAMES = [
    'Roe Visual BP2', 'Roe Visual CB5', 'Roe Visual Ruby RB2.6',
    'Roe Visual Diamond DM2.6', 'Roe Visual Diamond DM3.9',
    'Roe Visual Carbon CB3 MK II Half', 'Roe Visual Carbon CB8 MK II Half',
    'Roe Visual Black Quartz BQ3.9 Half', 'Roe Visual Vanish V4ST-Q',
    'Roe Visual Black Marble BM5I',
    'INFiLED ARmk2 P2.97 Indoor', 'INFiLED ARmk2 P3.91 Indoor',
    'INFiLED ARmk2 P4.81 Indoor', 'INFiLED ARmk2 P4.63 Outdoor',
    'INFiLED DBmk2 P1.56', 'INFiLED DBmk2 P1.95', 'INFiLED DBmk2 P2.6',
    'INFiLED AR Series P3.91 Ceiling',
    'Yestech Mwall M1.9', 'Yestech Mwall M2.6', 'Yestech Mwall M2.9',
    'Yestech Mwall M3.9', 'Yestech Mwall M4.8',
    'Gloshine MV2.3', 'Gloshine MV2.6', 'Gloshine 3.9mm Rental',
    'Gloshine Legend P3.91',
]


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default database location in user's home directory or app data
            app_data = Path(os.getenv('APPDATA', str(Path.home()))) / "ScreenMaker"
            app_data.mkdir(parents=True, exist_ok=True)
            self.db_path = app_data / "screenmaker.db"
        else:
            self.db_path = Path(db_path)
        
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # User Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # LED Tiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS led_tiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    pixel_width INTEGER,
                    pixel_height INTEGER,
                    physical_width REAL,
                    physical_height REAL,
                    pitch REAL,
                    brand TEXT,
                    brightness INTEGER
                )
            ''')

            # Migrate older databases that predate the `source` column
            cursor.execute("PRAGMA table_info(led_tiles)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            if 'source' not in existing_cols:
                cursor.execute("ALTER TABLE led_tiles ADD COLUMN source TEXT")

            # Drop previously-seeded entries that turned out to be unverified
            if _RETRACTED_TILE_NAMES:
                cursor.executemany(
                    "DELETE FROM led_tiles WHERE name = ?",
                    [(n,) for n in _RETRACTED_TILE_NAMES],
                )

            # Seed default tiles from the JSON catalog, skipping any name
            # already present so re-runs (and older databases) pick up
            # newly added catalog entries without duplicating rows.
            with open(SEED_FILE, 'r', encoding='utf-8') as f:
                default_tiles = json.load(f)

            cursor.execute("SELECT name FROM led_tiles")
            existing_names = {row[0] for row in cursor.fetchall()}
            new_tiles = [t for t in default_tiles if t['name'] not in existing_names]
            if new_tiles:
                cursor.executemany('''
                    INSERT INTO led_tiles
                        (name, pixel_width, pixel_height, physical_width, physical_height, pitch, brand, brightness, source)
                    VALUES
                        (:name, :pixel_width, :pixel_height, :physical_width, :physical_height, :pitch, :brand, :brightness, :source)
                ''', new_tiles)

            conn.commit()

    # Settings CRUD
    def get_setting(self, key, default=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (key, value)
                VALUES (?, ?)
            ''', (key, str(value)))
            conn.commit()

    # LED Tiles CRUD
    def get_all_tiles(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM led_tiles ORDER BY brand, name")
            return [dict(row) for row in cursor.fetchall()]

    def add_tile(self, tile_data):
        """tile_data: dict containing keys matching column names"""
        columns = ', '.join(tile_data.keys())
        placeholders = ', '.join(['?'] * len(tile_data))
        sql = f"INSERT INTO led_tiles ({columns}) VALUES ({placeholders})"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, list(tile_data.values()))
            conn.commit()
            return cursor.lastrowid

    def delete_tile(self, tile_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM led_tiles WHERE id = ?", (tile_id,))
            conn.commit()
