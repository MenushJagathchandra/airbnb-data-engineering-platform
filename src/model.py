import os
import logging
from pathlib import Path
import duckdb
from src.config import load_config, CLEANED_DATA_DIR, GOLD_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def build_star_schema(db_path: Path):
    """
    Builds the Star Schema in DuckDB using Parquet files from clean data.
    """
    logger.info(f"Initializing DuckDB at {db_path}...")
    
    # Ensure parent dir exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # If database exists, delete to ensure clean build (idempotent ETL)
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete existing db file: {e}")

    con = duckdb.connect(str(db_path))
    config = load_config()

    try:
        # 1. Load Staging Tables from Parquet
        logger.info("Loading staging tables...")
        
        listings_glob = str(CLEANED_DATA_DIR / "*" / "listings.parquet")
        calendar_glob = str(CLEANED_DATA_DIR / "*" / "calendar.parquet")
        reviews_glob = str(CLEANED_DATA_DIR / "*" / "reviews.parquet")
        
        con.execute(f"CREATE TABLE stg_listings AS SELECT * FROM read_parquet('{listings_glob}', union_by_name=True)")
        
        # Calendar and Reviews may be empty or missing for some runs; check and load
        has_calendar = False
        has_reviews = False
        
        try:
            con.execute(f"CREATE TABLE stg_calendar AS SELECT * FROM read_parquet('{calendar_glob}', union_by_name=True)")
            has_calendar = True
            logger.info("Staging table stg_calendar created.")
        except Exception as e:
            logger.warning(f"Could not load calendar parquet: {e}. Staging empty calendar.")
            con.execute("""
                CREATE TABLE stg_calendar (
                    listing_id BIGINT,
                    date TIMESTAMP,
                    available BOOLEAN,
                    price DOUBLE,
                    validation_errors VARCHAR,
                    is_valid BOOLEAN,
                    city VARCHAR
                )
            """)
            
        try:
            con.execute(f"CREATE TABLE stg_reviews AS SELECT * FROM read_parquet('{reviews_glob}', union_by_name=True)")
            has_reviews = True
            logger.info("Staging table stg_reviews created.")
        except Exception as e:
            logger.warning(f"Could not load reviews parquet: {e}. Staging empty reviews.")
            con.execute("""
                CREATE TABLE stg_reviews (
                    listing_id BIGINT,
                    id BIGINT,
                    date TIMESTAMP,
                    reviewer_id BIGINT,
                    reviewer_name VARCHAR,
                    comments VARCHAR,
                    validation_errors VARCHAR,
                    is_valid BOOLEAN,
                    city VARCHAR
                )
            """)

        # 2. Create and Populate Landmarks Dimension
        logger.info("Creating dim_landmarks...")
        con.execute("""
            CREATE TABLE dim_landmarks (
                landmark_key VARCHAR PRIMARY KEY,
                city VARCHAR,
                name VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE,
                type VARCHAR
            )
        """)
        
        for city_conf in config["cities"]:
            city_name = city_conf["name"]
            for lm in city_conf.get("landmarks", []):
                lm_name = lm["name"]
                lm_lat = lm["latitude"]
                lm_lon = lm["longitude"]
                lm_type = lm["type"]
                lm_key = f"{city_name}_{lm_name.replace(' ', '_').lower()}"
                
                con.execute("""
                    INSERT INTO dim_landmarks (landmark_key, city, name, latitude, longitude, type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (lm_key, city_name, lm_name, lm_lat, lm_lon, lm_type))

        # 3. Create Date Dimension
        logger.info("Creating dim_date...")
        con.execute("""
            CREATE TABLE dim_date AS
            SELECT
                (strftime(d, '%Y%m%d'))::INTEGER AS date_key,
                d AS date,
                year(d) AS year,
                month(d) AS month,
                monthname(d) AS month_name,
                day(d) AS day,
                dayofweek(d) AS day_of_week,
                dayname(d) AS day_name,
                CASE WHEN dayofweek(d) IN (6, 0) THEN TRUE ELSE FALSE END AS is_weekend
            FROM (
                SELECT range::DATE AS d
                FROM range(DATE '2024-01-01', DATE '2026-12-31', INTERVAL '1 day')
            )
        """)

        # 4. Create Host Dimension
        logger.info("Creating dim_hosts...")
        con.execute("""
            CREATE TABLE dim_hosts AS
            WITH ranked_hosts AS (
                SELECT
                    md5(concat_ws('||', host_id::VARCHAR, city)) AS host_key,
                    host_id,
                    host_name,
                    host_since,
                    host_is_superhost,
                    row_number() OVER (
                        PARTITION BY host_id, city 
                        ORDER BY host_since DESC, host_is_superhost DESC
                    ) AS rn
                FROM stg_listings
                WHERE host_id IS NOT NULL
            )
            SELECT host_key, host_id, host_name, host_since, host_is_superhost
            FROM ranked_hosts
            WHERE rn = 1
        """)

        # 5. Create Listings Dimension
        logger.info("Creating dim_listings...")
        con.execute("""
            CREATE TABLE dim_listings AS
            SELECT DISTINCT
                md5(concat_ws('||', id::VARCHAR, city)) AS listing_key,
                id AS listing_id,
                city,
                name,
                description,
                latitude,
                longitude,
                room_type,
                property_type
            FROM stg_listings
        """)

        # 6. Create Location Dimension
        logger.info("Creating dim_locations...")
        con.execute("""
            CREATE TABLE dim_locations AS
            SELECT DISTINCT
                md5(concat_ws('||', city, neighbourhood_cleansed)) AS location_key,
                neighbourhood_cleansed AS neighbourhood,
                city,
                CASE WHEN city = 'amsterdam' THEN 'North Holland' ELSE 'Veneto' END AS state,
                CASE WHEN city = 'amsterdam' THEN 'The Netherlands' ELSE 'Italy' END AS country
            FROM stg_listings
        """)

        # 7. Create Listing Landmark Distance Bridge Table
        logger.info("Creating dim_listing_landmark_distance...")
        con.execute("""
            CREATE TABLE dim_listing_landmark_distance AS
            SELECT
                md5(concat_ws('||', l.id::VARCHAR, l.city)) AS listing_key,
                lm.landmark_key,
                -- Haversine formula
                6371 * 2 * asin(sqrt(
                    pow(sin(radians(lm.latitude - l.latitude) / 2), 2) +
                    cos(radians(l.latitude)) * cos(radians(lm.latitude)) *
                    pow(sin(radians(lm.longitude - l.longitude) / 2), 2)
                )) AS distance_km
            FROM stg_listings l
            JOIN dim_landmarks lm ON l.city = lm.city
        """)

        # 8. Create Nearest Landmark Helper View
        con.execute("""
            CREATE VIEW v_nearest_landmark AS
            WITH ranked_distances AS (
                SELECT
                    listing_key,
                    landmark_key,
                    distance_km,
                    row_number() OVER (PARTITION BY listing_key ORDER BY distance_km) AS rn
                FROM dim_listing_landmark_distance
            )
            SELECT 
                r.listing_key,
                r.landmark_key AS nearest_landmark_key,
                lm.name AS nearest_landmark_name,
                lm.type AS nearest_landmark_type,
                r.distance_km AS distance_to_nearest_landmark_km
            FROM ranked_distances r
            JOIN dim_landmarks lm ON r.landmark_key = lm.landmark_key
            WHERE r.rn = 1
        """)

        # 9. Create Fact Listings Table
        logger.info("Creating fact_listings...")
        # Parse bathrooms text to float inside SQL if not already done
        con.execute("""
            CREATE TABLE fact_listings AS
            SELECT
                md5(concat_ws('||', l.id::VARCHAR, l.city)) AS listing_key,
                md5(concat_ws('||', l.host_id::VARCHAR, l.city)) AS host_key,
                md5(concat_ws('||', l.city, l.neighbourhood_cleansed)) AS location_key,
                l.city,
                l.price,
                l.accommodates,
                l.bedrooms,
                l.beds,
                -- Parse bathrooms from bathrooms_text
                CASE 
                    WHEN lower(l.bathrooms_text) LIKE '%half-bath%' THEN 0.5
                    ELSE CAST(nullif(regexp_extract(l.bathrooms_text, '([0-9.]+)', 1), '') AS DOUBLE)
                END AS bathrooms,
                l.minimum_nights,
                l.maximum_nights,
                l.number_of_reviews,
                l.review_scores_rating,
                n.nearest_landmark_key,
                n.nearest_landmark_name,
                n.nearest_landmark_type,
                n.distance_to_nearest_landmark_km,
                -- We will update sentiment score during analysis if available
                CAST(NULL AS DOUBLE) AS average_sentiment_score
            FROM stg_listings l
            LEFT JOIN v_nearest_landmark n ON md5(concat_ws('||', l.id::VARCHAR, l.city)) = n.listing_key
        """)

        # 10. Create Fact Calendar Table
        logger.info("Creating fact_calendar...")
        con.execute("""
            CREATE TABLE fact_calendar AS
            SELECT
                md5(concat_ws('||', c.listing_id::VARCHAR, c.city, c.date::VARCHAR)) AS calendar_key,
                md5(concat_ws('||', c.listing_id::VARCHAR, c.city)) AS listing_key,
                (strftime(c.date, '%Y%m%d'))::INTEGER AS date_key,
                c.available,
                c.price
            FROM stg_calendar c
        """)

        # 11. Create Fact Reviews Table
        logger.info("Creating fact_reviews...")
        con.execute("""
            CREATE TABLE fact_reviews AS
            SELECT
                md5(concat_ws('||', r.id::VARCHAR, r.city)) AS review_key,
                md5(concat_ws('||', r.listing_id::VARCHAR, r.city)) AS listing_key,
                (strftime(r.date, '%Y%m%d'))::INTEGER AS date_key,
                r.id AS review_id,
                r.reviewer_id,
                r.reviewer_name,
                r.comments,
                CAST(NULL AS DOUBLE) AS sentiment_score
            FROM stg_reviews r
        """)

        # 12. Run Sanity Checks / Integrity Validation
        logger.info("Running dimensional integrity tests...")
        
        # Check listings mapping
        missing_listings = con.execute("""
            SELECT COUNT(*) FROM fact_listings f
            LEFT JOIN dim_listings d ON f.listing_key = d.listing_key
            WHERE d.listing_key IS NULL
        """).fetchone()[0]
        
        # Check locations mapping
        missing_locations = con.execute("""
            SELECT COUNT(*) FROM fact_listings f
            LEFT JOIN dim_locations d ON f.location_key = d.location_key
            WHERE d.location_key IS NULL
        """).fetchone()[0]
        
        logger.info(f"Integrity check completed. Missing dim_listings matches: {missing_listings}. Missing dim_locations matches: {missing_locations}.")

    except Exception as e:
        logger.error(f"Error building star schema: {e}")
        raise e
    finally:
        con.close()

if __name__ == "__main__":
    db_path = GOLD_DATA_DIR / "airbnb_dw.duckdb"
    build_star_schema(db_path)
