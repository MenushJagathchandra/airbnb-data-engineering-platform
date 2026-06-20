import os
import gzip
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from src.config import load_config, RAW_DATA_DIR, CLEANED_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def clean_price(price_val):
    """
    Standardizes price values, removing currency symbols and commas.
    Returns float or NaN.
    """
    if pd.isna(price_val) or price_val is None:
        return np.nan
    if isinstance(price_val, (int, float)):
        return float(price_val)
    
    price_str = str(price_val).strip()
    # Remove $, commas, spaces
    price_str = price_str.replace("$", "").replace(",", "").strip()
    try:
        val = float(price_str)
        return val
    except ValueError:
        return np.nan

def clean_boolean(val):
    """
    Normalizes Inside Airbnb boolean representation ('t'/'f') to true/false.
    """
    if pd.isna(val) or val is None:
        return False
    val_str = str(val).strip().lower()
    if val_str in ("t", "true", "1", "y", "yes"):
        return True
    return False

def clean_listings(df: pd.DataFrame, city: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cleans and validates the listings dataset.
    Returns (cleaned_df, quarantined_df).
    """
    logger.info(f"Cleaning listings for {city}. Initial shape: {df.shape}")
    
    # We will track validation errors in a column
    errors = []
    
    # Ensure raw types
    df = df.copy()
    
    # 1. Clean ID
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    id_null = df["id"].isna()
    
    # 2. Clean Prices
    df["price_clean"] = df["price"].apply(clean_price)
    price_invalid = df["price_clean"].isna() | (df["price_clean"] <= 0)
    
    # 3. Clean Coordinates
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    coord_invalid = (
        df["latitude"].isna() | 
        df["longitude"].isna() | 
        (df["latitude"] < -90) | (df["latitude"] > 90) |
        (df["longitude"] < -180) | (df["longitude"] > 180)
    )
    
    # 4. Host Since Date
    df["host_since_clean"] = pd.to_datetime(df["host_since"], errors="coerce")
    
    # 5. Normalize strings
    df["room_type"] = df["room_type"].astype(str).str.strip().str.title()
    df["property_type"] = df["property_type"].astype(str).str.strip()
    df["neighbourhood_cleansed"] = df["neighbourhood_cleansed"].astype(str).str.strip()
    
    # 6. Normalize superhost boolean
    df["host_is_superhost_clean"] = df["host_is_superhost"].apply(clean_boolean)
    
    # 7. Convert numeric features
    for col in ["accommodates", "bedrooms", "beds", "minimum_nights", "maximum_nights", "number_of_reviews"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            
    # Calculate error reason strings
    reasons = []
    for idx, row in df.iterrows():
        err_list = []
        if pd.isna(row["id"]):
            err_list.append("missing_or_invalid_id")
        if pd.isna(row["price_clean"]) or row["price_clean"] <= 0:
            err_list.append(f"invalid_price_value({row['price']})")
        if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
            err_list.append("missing_coordinates")
        elif not (-90 <= row["latitude"] <= 90) or not (-180 <= row["longitude"] <= 180):
            err_list.append("coordinates_out_of_bounds")
        
        reasons.append(";".join(err_list))
        
    df["validation_errors"] = reasons
    df["is_valid"] = df["validation_errors"] == ""
    df["city"] = city
    
    # Split
    cleaned_df = df[df["is_valid"]].drop(columns=["price", "host_since", "host_is_superhost"]).rename(columns={
        "price_clean": "price",
        "host_since_clean": "host_since",
        "host_is_superhost_clean": "host_is_superhost"
    })
    
    quarantine_df = df[~df["is_valid"]]
    
    logger.info(f"Listings clean complete: {cleaned_df.shape[0]} valid, {quarantine_df.shape[0]} quarantined.")
    return cleaned_df, quarantine_df

def clean_calendar(df: pd.DataFrame, city: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cleans and validates the calendar dataset.
    """
    logger.info(f"Cleaning calendar for {city}. Initial shape: {df.shape}")
    df = df.copy()
    
    df["listing_id"] = pd.to_numeric(df["listing_id"], errors="coerce")
    df["date_clean"] = pd.to_datetime(df["date"], errors="coerce")
    df["available_clean"] = df["available"].apply(clean_boolean)
    df["price_clean"] = df["price"].apply(clean_price)
    
    reasons = []
    for idx, row in df.iterrows():
        err_list = []
        if pd.isna(row["listing_id"]):
            err_list.append("missing_listing_id")
        if pd.isna(row["date_clean"]):
            err_list.append("invalid_date")
        if pd.isna(row["price_clean"]) and not row["available_clean"]:
            # If available is false, price can be null. Otherwise, it must be valid.
            pass
        elif pd.isna(row["price_clean"]) or row["price_clean"] <= 0:
            err_list.append(f"invalid_price({row['price']})")
            
        reasons.append(";".join(err_list))
        
    df["validation_errors"] = reasons
    df["is_valid"] = df["validation_errors"] == ""
    df["city"] = city
    
    cleaned_df = df[df["is_valid"]].drop(columns=["date", "available", "price", "adjusted_price"]).rename(columns={
        "date_clean": "date",
        "available_clean": "available",
        "price_clean": "price"
    })
    
    quarantine_df = df[~df["is_valid"]]
    
    logger.info(f"Calendar clean complete: {cleaned_df.shape[0]} valid, {quarantine_df.shape[0]} quarantined.")
    return cleaned_df, quarantine_df

def clean_reviews(df: pd.DataFrame, city: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cleans and validates the reviews dataset.
    """
    logger.info(f"Cleaning reviews for {city}. Initial shape: {df.shape}")
    df = df.copy()
    
    df["listing_id"] = pd.to_numeric(df["listing_id"], errors="coerce")
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["date_clean"] = pd.to_datetime(df["date"], errors="coerce")
    df["comments_clean"] = df["comments"].fillna("").astype(str).str.strip().str.replace("\n", " ").str.replace("\r", " ")
    
    reasons = []
    for idx, row in df.iterrows():
        err_list = []
        if pd.isna(row["listing_id"]):
            err_list.append("missing_listing_id")
        if pd.isna(row["id"]):
            err_list.append("missing_review_id")
        if pd.isna(row["date_clean"]):
            err_list.append("invalid_date")
            
        reasons.append(";".join(err_list))
        
    df["validation_errors"] = reasons
    df["is_valid"] = df["validation_errors"] == ""
    df["city"] = city
    
    cleaned_df = df[df["is_valid"]].drop(columns=["date", "comments"]).rename(columns={
        "date_clean": "date",
        "comments_clean": "comments"
    })
    
    quarantine_df = df[~df["is_valid"]]
    
    logger.info(f"Reviews clean complete: {cleaned_df.shape[0]} valid, {quarantine_df.shape[0]} quarantined.")
    return cleaned_df, quarantine_df

def clean_all(force: bool = False):
    config = load_config()
    
    for city_conf in config["cities"]:
        name = city_conf["name"]
        logger.info(f"Cleaning data for city: {name}")
        
        raw_dir = RAW_DATA_DIR / name
        cleaned_dir = CLEANED_DATA_DIR / name
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        
        # Listings
        listings_path = raw_dir / "listings.csv.gz"
        cleaned_listings_path = cleaned_dir / "listings.parquet"
        if listings_path.exists():
            if cleaned_listings_path.exists() and not force:
                logger.info(f"Cleaned listings already exist for {name}. Skipping.")
            else:
                df_list = pd.read_csv(listings_path, compression="gzip", low_memory=False)
                cleaned, quarantined = clean_listings(df_list, name)
                cleaned.to_parquet(cleaned_listings_path, index=False)
                quarantined.to_parquet(cleaned_dir / "listings_quarantine.parquet", index=False)
        else:
            logger.warning(f"Raw listings not found for {name}")
            
        # Calendar
        calendar_path = raw_dir / "calendar.csv.gz"
        cleaned_calendar_path = cleaned_dir / "calendar.parquet"
        if calendar_path.exists():
            if cleaned_calendar_path.exists() and not force:
                logger.info(f"Cleaned calendar already exists for {name}. Skipping.")
            else:
                df_cal = pd.read_csv(calendar_path, compression="gzip", low_memory=False)
                cleaned, quarantined = clean_calendar(df_cal, name)
                cleaned.to_parquet(cleaned_calendar_path, index=False)
                quarantined.to_parquet(cleaned_dir / "calendar_quarantine.parquet", index=False)
        else:
            logger.warning(f"Raw calendar not found for {name}")
            
        # Reviews
        reviews_path = raw_dir / "reviews.csv.gz"
        cleaned_reviews_path = cleaned_dir / "reviews.parquet"
        if reviews_path.exists():
            if cleaned_reviews_path.exists() and not force:
                logger.info(f"Cleaned reviews already exist for {name}. Skipping.")
            else:
                df_rev = pd.read_csv(reviews_path, compression="gzip", low_memory=False)
                cleaned, quarantined = clean_reviews(df_rev, name)
                cleaned.to_parquet(cleaned_reviews_path, index=False)
                quarantined.to_parquet(cleaned_dir / "reviews_quarantine.parquet", index=False)
        else:
            logger.warning(f"Raw reviews not found for {name}")

if __name__ == "__main__":
    clean_all()
