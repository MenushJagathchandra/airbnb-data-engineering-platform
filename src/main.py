import os
import argparse
import logging
from pathlib import Path
from src.config import ensure_directories, GOLD_DATA_DIR
from src.ingest import ingest_all
from src.clean import clean_all
from src.model import build_star_schema
from src.analyze import run_analysis_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Expernetic Airbnb Data Pipeline")
    parser.add_argument("--mock", action="store_true", help="Run with mock data (offline mode / testing).")
    parser.add_argument("--db-path", type=str, default=str(GOLD_DATA_DIR / "airbnb_dw.duckdb"), help="Path to the DuckDB database file.")
    parser.add_argument("--out-dir", type=str, default=str(GOLD_DATA_DIR), help="Output directory for reports and plots.")
    
    args = parser.parse_args()
    
    logger.info("=========================================")
    logger.info("Starting Expernetic Airbnb Data Pipeline")
    logger.info(f"Mode: {'MOCK' if args.mock else 'PRODUCTION (Live Download)'}")
    logger.info("=========================================")
    
    ensure_directories()
    
    # 1. Ingest
    logger.info("STEP 1: Ingestion...")
    ingest_all(force_mock=args.mock)
    
    # 2. Clean
    logger.info("STEP 2: Data Cleaning & Validation...")
    clean_all()
    
    # 3. Model
    logger.info("STEP 3: Dimensional Modeling (DuckDB)...")
    db_path = Path(args.db_path)
    build_star_schema(db_path)
    
    # 4. Analyze & Report
    logger.info("STEP 4: Statistical Analysis, AI Sentiment, and Reporting...")
    out_dir = Path(args.out_dir)
    run_analysis_pipeline(db_path, out_dir)
    
    logger.info("=========================================")
    logger.info("Pipeline Execution Completed Successfully!")
    logger.info(f"Database: {db_path}")
    logger.info(f"Report & Plots: {out_dir}")
    logger.info("=========================================")

if __name__ == "__main__":
    main()
