import os
import time
import urllib.request
import requests
from pathlib import Path
import logging
from src.config import load_config, RAW_DATA_DIR, ensure_directories

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: Path, max_retries: int = 5, backoff_factor: float = 2.0) -> bool:
    """
    Downloads a file with streaming and exponential backoff retry logic.
    """
    if dest_path.exists():
        logger.info(f"File already exists at {dest_path}. Skipping download.")
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".tmp")

    retries = 0
    delay = 1.0

    while retries < max_retries:
        try:
            logger.info(f"Downloading {url} to {dest_path} (Attempt {retries + 1}/{max_retries})...")
            
            # Use requests stream to save RAM
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            # Rename temp file to final destination on success
            temp_path.rename(dest_path)
            logger.info(f"Successfully downloaded {dest_path.name}")
            return True

        except Exception as e:
            retries += 1
            logger.warning(f"Error downloading {url}: {e}. Retrying in {delay} seconds...")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            time.sleep(delay)
            delay *= backoff_factor

    logger.error(f"Failed to download {url} after {max_retries} attempts.")
    return False

def generate_mock_listings(dest_path: Path, city: str):
    """
    Generates synthetic listings data in case we are running offline or in testing.
    """
    import gzip
    import pandas as pd
    import numpy as np

    logger.info(f"Generating mock listings data for {city}...")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n_records = 100

    # Neighborhoods depending on city
    if city == "amsterdam":
        neighs = ["Centrum-West", "Centrum-Oost", "Zuid", "De Pijp", "Oud-West", "Noord"]
        lat_base, lon_base = 52.37, 4.89
    else:
        neighs = ["San Marco", "Cannaregio", "Castello", "Dorsoduro", "San Polo", "Santa Croce"]
        lat_base, lon_base = 45.43, 12.33

    data = {
        "id": range(1000, 1000 + n_records),
        "name": [f"Beautiful Apartment in {city} - {i}" for i in range(n_records)],
        "description": [f"This is a wonderful place to stay in {city}." for _ in range(n_records)],
        "host_id": np.random.randint(2000, 3000, size=n_records),
        "host_name": [f"Host {i}" for i in range(n_records)],
        "host_since": list(pd.date_range(start="2015-01-01", periods=n_records).strftime("%Y-%m-%d")),
        "host_is_superhost": list(np.random.choice(["t", "f", None], size=n_records, p=[0.3, 0.6, 0.1])),
        "neighbourhood_cleansed": np.random.choice(neighs, size=n_records),
        "neighbourhood_group_cleansed": [None] * n_records,
        "latitude": lat_base + np.random.normal(0, 0.02, size=n_records),
        "longitude": lon_base + np.random.normal(0, 0.02, size=n_records),
        "property_type": np.random.choice(["Entire rental unit", "Private room in rental unit", "Entire loft"], size=n_records),
        "room_type": np.random.choice(["Entire home/apt", "Private room", "Shared room"], size=n_records),
        "accommodates": np.random.randint(1, 6, size=n_records),
        "bathrooms_text": np.random.choice(["1 bath", "1.5 baths", "2 baths", None], size=n_records),
        "bedrooms": np.random.choice([1, 2, 3, None], size=n_records),
        "beds": np.random.choice([1, 2, 3, 4, None], size=n_records),
        "price": [f"${np.random.randint(50, 500)}.00" for _ in range(n_records)],
        "minimum_nights": np.random.choice([1, 2, 3, 7], size=n_records),
        "maximum_nights": [1125] * n_records,
        "number_of_reviews": np.random.randint(0, 300, size=n_records),
        "review_scores_rating": np.random.uniform(3.0, 5.0, size=n_records)
    }

    # Inject some corrupt rows for data quality checks
    # Row 0: Negative price
    data["price"][0] = "-$50.00"
    # Row 1: Null price
    data["price"][1] = None
    # Row 2: Invalid host_since date format
    data["host_since"][2] = "invalid-date"
    # Row 3: Superhost invalid value
    data["host_is_superhost"][3] = "invalid"
    
    df = pd.DataFrame(data)
    with gzip.open(dest_path, "wt", encoding="utf-8") as f:
        df.to_csv(f, index=False)
    logger.info(f"Mock listings written to {dest_path}")

def generate_mock_calendar(dest_path: Path, city: str):
    """
    Generates synthetic calendar data.
    """
    import gzip
    import pandas as pd
    import numpy as np

    logger.info(f"Generating mock calendar data for {city}...")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n_listings = 100
    dates = pd.date_range(start="2025-09-11", periods=30)  # 30 days of calendar data

    rows = []
    for l_id in range(1000, 1000 + n_listings):
        for date in dates:
            rows.append({
                "listing_id": l_id,
                "date": date.strftime("%Y-%m-%d"),
                "available": np.random.choice(["t", "f"], p=[0.7, 0.3]),
                "price": f"${np.random.randint(50, 500)}.00",
                "adjusted_price": f"${np.random.randint(50, 500)}.00",
                "minimum_nights": np.random.choice([1, 2, 3]),
                "maximum_nights": 1125
            })

    df = pd.DataFrame(rows)
    with gzip.open(dest_path, "wt", encoding="utf-8") as f:
        df.to_csv(f, index=False)
    logger.info(f"Mock calendar written to {dest_path}")

def generate_mock_reviews(dest_path: Path, city: str):
    """
    Generates synthetic reviews data.
    """
    import gzip
    import pandas as pd
    import numpy as np

    logger.info(f"Generating mock reviews data for {city}...")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n_reviews = 300
    comments_pool = [
        "Absolutely amazing stay! Highly recommend. Beautiful view and very central.",
        "The apartment was clean and comfortable, but a bit noisy at night.",
        "Terrible experience. The host was unresponsive and the place was dirty.",
        "Great location, easy check-in. The bed was comfortable.",
        "Wonderful host, very accommodating. We loved our time here!",
        "It was okay. Nothing special but met our needs.",
        "Disappointing. The heating did not work and it was cold.",
        "Perfect location! Walking distance to everything.",
        "Very clean, spacious, and modern. Host was friendly.",
        "Bad smell in the bathroom and the WiFi was extremely slow."
    ]

    data = {
        "listing_id": np.random.randint(1000, 1100, size=n_reviews),
        "id": range(5000, 5000 + n_reviews),
        "date": pd.date_range(start="2024-01-01", periods=n_reviews).strftime("%Y-%m-%d"),
        "reviewer_id": np.random.randint(10000, 20000, size=n_reviews),
        "reviewer_name": [f"Reviewer {i}" for i in range(n_reviews)],
        "comments": np.random.choice(comments_pool, size=n_reviews)
    }

    df = pd.DataFrame(data)
    with gzip.open(dest_path, "wt", encoding="utf-8") as f:
        df.to_csv(f, index=False)
    logger.info(f"Mock reviews written to {dest_path}")

def ingest_all(force_mock: bool = False):
    ensure_directories()
    config = load_config()
    
    for city_conf in config["cities"]:
        name = city_conf["name"]
        logger.info(f"Processing city: {name}")
        
        city_raw_dir = RAW_DATA_DIR / name
        city_raw_dir.mkdir(exist_ok=True)
        
        for file_type, url in city_conf["urls"].items():
            dest_path = city_raw_dir / f"{file_type}.csv.gz"
            
            if force_mock:
                if file_type == "listings":
                    generate_mock_listings(dest_path, name)
                elif file_type == "calendar":
                    generate_mock_calendar(dest_path, name)
                elif file_type == "reviews":
                    generate_mock_reviews(dest_path, name)
            else:
                success = download_file(url, dest_path)
                if not success:
                    logger.warning(f"Download failed for {name} - {file_type}. Generating mock fallback...")
                    if file_type == "listings":
                        generate_mock_listings(dest_path, name)
                    elif file_type == "calendar":
                        generate_mock_calendar(dest_path, name)
                    elif file_type == "reviews":
                        generate_mock_reviews(dest_path, name)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest data from Inside Airbnb.")
    parser.add_argument("--mock", action="store_true", help="Force mock data generation.")
    args = parser.parse_args()
    
    ingest_all(force_mock=args.mock)
