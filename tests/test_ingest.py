import pytest
from pathlib import Path
from src.config import load_config, RAW_DATA_DIR
from src.ingest import ingest_all

def test_load_config():
    config = load_config()
    assert "cities" in config
    assert len(config["cities"]) >= 2
    
    cities = [c["name"] for c in config["cities"]]
    assert "amsterdam" in cities
    assert "venice" in cities

def test_ingest_mock():
    # Run mock ingestion to generate test datasets
    ingest_all(force_mock=True)
    
    for city in ["amsterdam", "venice"]:
        city_raw_dir = RAW_DATA_DIR / city
        assert (city_raw_dir / "listings.csv.gz").exists()
        assert (city_raw_dir / "calendar.csv.gz").exists()
        assert (city_raw_dir / "reviews.csv.gz").exists()
