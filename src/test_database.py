from database import DatabaseManager
from settings import Settings
import os
from pathlib import Path

def test_database():
    print("Testing DatabaseManager...")
    db_path = "test_screenmaker.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    # Test Settings
    db.set_setting("test_key", "test_value")
    assert db.get_setting("test_key") == "test_value"
    print("✓ Settings persistence ok")
    
    # Test LED Tiles
    tiles = db.get_all_tiles()
    assert len(tiles) > 0
    print(f"✓ Default tiles loaded: {reversed([t['name'] for t in tiles])}")
    
    new_tile = {
        'name': 'Test Tile',
        'pixel_width': 100,
        'pixel_height': 100,
        'physical_width': 500.0,
        'physical_height': 500.0,
        'pitch': 5.0,
        'brand': 'TestBrand',
        'brightness': 1000
    }
    tile_id = db.add_tile(new_tile)
    assert tile_id is not None
    
    tiles = db.get_all_tiles()
    assert any(t['name'] == 'Test Tile' for t in tiles)
    print("✓ LED tile CRUD ok")
    
    os.remove(db_path)
    print("Database test complete.\n")

def test_settings_singleton():
    print("Testing Settings singleton...")
    s1 = Settings()
    s2 = Settings()
    assert s1 is s2
    
    s1.last_csv_path = "some/path.csv"
    assert s2.last_csv_path == "some/path.csv"
    print("✓ Settings singleton and properties ok")

if __name__ == "__main__":
    try:
        test_database()
        test_settings_singleton()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
