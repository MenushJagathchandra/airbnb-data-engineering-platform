import pytest
import os
import shutil
from pathlib import Path
import duckdb
from src.config import PROJECT_ROOT, RAW_DATA_DIR, CLEANED_DATA_DIR, GOLD_DATA_DIR
from src.ingest import generate_mock_listings, generate_mock_calendar, generate_mock_reviews
from src.clean import clean_all
from src.model import build_star_schema

@pytest.fixture(scope="module")
def setup_test_dw():
    # Setup directories
    test_raw_dir = RAW_DATA_DIR / "amsterdam"
    test_cleaned_dir = CLEANED_DATA_DIR / "amsterdam"
    test_gold_dir = GOLD_DATA_DIR
    
    test_raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate mock files
    generate_mock_listings(test_raw_dir / "listings.csv.gz", "amsterdam")
    generate_mock_calendar(test_raw_dir / "calendar.csv.gz", "amsterdam")
    generate_mock_reviews(test_raw_dir / "reviews.csv.gz", "amsterdam")
    
    # Clean all
    clean_all()
    
    # DB path
    test_db_path = test_gold_dir / "test_airbnb_dw.duckdb"
    
    # Build star schema
    build_star_schema(test_db_path)
    
    yield test_db_path
    
    # Cleanup database
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass

def test_dimensional_tables_exist(setup_test_dw):
    db_path = setup_test_dw
    con = duckdb.connect(str(db_path))
    
    tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
    
    expected_tables = [
        "dim_listings", 
        "dim_hosts", 
        "dim_locations", 
        "dim_landmarks", 
        "dim_date",
        "fact_listings", 
        "fact_calendar", 
        "fact_reviews",
        "dim_listing_landmark_distance"
    ]
    
    for t in expected_tables:
        assert t in tables, f"Expected table {t} was not found in DuckDB database."
        
    con.close()

def test_surrogate_key_uniqueness(setup_test_dw):
    db_path = setup_test_dw
    con = duckdb.connect(str(db_path))
    
    # Check dim_listings unique key
    dup_listings = con.execute("""
        SELECT listing_key, COUNT(*) 
        FROM dim_listings 
        GROUP BY listing_key 
        HAVING COUNT(*) > 1
    """).fetchall()
    assert len(dup_listings) == 0, "Duplicate listing_keys found in dim_listings!"
    
    # Check dim_hosts unique key
    dup_hosts = con.execute("""
        SELECT host_key, COUNT(*) 
        FROM dim_hosts 
        GROUP BY host_key 
        HAVING COUNT(*) > 1
    """).fetchall()
    assert len(dup_hosts) == 0, "Duplicate host_keys found in dim_hosts!"
    
    con.close()

def test_referential_integrity(setup_test_dw):
    db_path = setup_test_dw
    con = duckdb.connect(str(db_path))
    
    # Ensure all listings in fact_listings exist in dim_listings
    dangling_listings = con.execute("""
        SELECT COUNT(*) 
        FROM fact_listings f
        LEFT JOIN dim_listings d ON f.listing_key = d.listing_key
        WHERE d.listing_key IS NULL
    """).fetchone()[0]
    assert dangling_listings == 0, "Referential integrity failure: fact_listings has dangling keys!"
    
    # Ensure all locations in fact_listings exist in dim_locations
    dangling_locations = con.execute("""
        SELECT COUNT(*) 
        FROM fact_listings f
        LEFT JOIN dim_locations d ON f.location_key = d.location_key
        WHERE d.location_key IS NULL
    """).fetchone()[0]
    assert dangling_locations == 0, "Referential integrity failure: fact_listings has dangling location keys!"
    
    con.close()
