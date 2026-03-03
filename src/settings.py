from database import DatabaseManager
from pathlib import Path
import os
import platform

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.db = DatabaseManager()
        return cls._instance

    @property
    def last_csv_path(self):
        return self.db.get_setting('last_csv_path')

    @last_csv_path.setter
    def last_csv_path(self, value):
        self.db.set_setting('last_csv_path', value)

    @property
    def default_output_folder(self):
        saved_path = self.db.get_setting('default_output_folder')
        if saved_path:
            return saved_path
        
        # Safe defaults if no path is set
        home_docs = Path.home() / "Documents" / "ScreenMaker"
        
        # Ensure directory exists (optional, but good for UX so the dialog opens there)
        # We won't create it here, just return the path string
        return str(home_docs)

    @default_output_folder.setter
    def default_output_folder(self, value):
        self.db.set_setting('default_output_folder', value)

    def get_setting(self, key, default=None):
        return self.db.get_setting(key, default)

    def set_setting(self, key, value):
        self.db.set_setting(key, value)

    def get_all_tiles(self):
        return self.db.get_all_tiles()
