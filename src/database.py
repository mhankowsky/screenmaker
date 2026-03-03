import sqlite3
import os
from pathlib import Path

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
            
            # Insert some default common tiles if the table is empty
            cursor.execute("SELECT COUNT(*) FROM led_tiles")
            if cursor.fetchone()[0] == 0:
                default_tiles = [
                    ('Absen Polaris 2.5', 200, 200, 500.0, 500.0, 2.5, 'Absen', 1200),
                    ('Roe Visual BP2', 176, 176, 500.0, 500.0, 2.8, 'Roe Visual', 1500),
                    ('Roe Visual CB5', 120, 120, 600.0, 600.0, 5.0, 'Roe Visual', 5000),
                    ('Unilumin Upad IV 2.6', 192, 192, 500.0, 500.0, 2.6, 'Unilumin', 1200),
                ]
                cursor.executemany('''
                    INSERT INTO led_tiles (name, pixel_width, pixel_height, physical_width, physical_height, pitch, brand, brightness)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', default_tiles)
            
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
