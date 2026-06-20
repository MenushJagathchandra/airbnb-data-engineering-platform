import pytest
import os
import shutil
from pathlib import Path
import duckdb
from src.config import RAW_DATA_DIR, CLEANED_DATA_DIR, GOLD_DATA_DIR
from src.ingest import generate_mock_listings, generate_mock_calendar, generate_mock_reviews
from src.clean import clean_all
from src.model import build_star_schema
from src.analyze import analyze_sentiment, run_analysis_pipeline

def test_sentiment_lexicon():
    # Test positive reviews
    pos_score = analyze_sentiment("This apartment is amazing, beautiful and very clean! We had a perfect stay.")
    assert pos_score > 0.0
    
    # Test negative reviews
    neg_score = analyze_sentiment("The place was dirty, noisy, and the host was unresponsive. A terrible experience.")
    assert neg_score < 0.0
    
    # Test neutral reviews
    neutral_score = analyze_sentiment("The apartment is in Amsterdam.")
    assert neutral_score == 0.0

def test_analysis_pipeline():
    # Setup test folder
    test_raw_dir = RAW_DATA_DIR / "amsterdam"
    test_raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate mock files
    generate_mock_listings(test_raw_dir / "listings.csv.gz", "amsterdam")
    generate_mock_calendar(test_raw_dir / "calendar.csv.gz", "amsterdam")
    generate_mock_reviews(test_raw_dir / "reviews.csv.gz", "amsterdam")
    
    clean_all()
    
    test_db_path = GOLD_DATA_DIR / "test_analysis.duckdb"
    build_star_schema(test_db_path)
    
    # Run analysis
    test_out_dir = GOLD_DATA_DIR / "test_out"
    if test_out_dir.exists():
        shutil.rmtree(test_out_dir)
        
    run_analysis_pipeline(test_db_path, test_out_dir)
    
    # Verify outputs
    report_path = test_out_dir / "analytics_report.md"
    assert report_path.exists(), "Analytics report was not generated!"
    
    # Check that plots exist
    plots_dir = test_out_dir / "plots"
    assert plots_dir.exists()
    assert len(list(plots_dir.glob("*.png"))) > 0, "No plots were generated!"
    
    # Clean up test outputs
    if test_db_path.exists():
        test_db_path.unlink()
    if test_out_dir.exists():
        shutil.rmtree(test_out_dir)
