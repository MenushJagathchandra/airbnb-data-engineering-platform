import pytest
import pandas as pd
import numpy as np
from src.clean import clean_price, clean_boolean, clean_listings, clean_calendar, clean_reviews

def test_clean_price():
    assert clean_price("$100.00") == 100.0
    assert clean_price("1,250.50") == 1250.5
    assert clean_price(" $50 ") == 50.0
    assert clean_price(75.25) == 75.25
    assert clean_price(None) is np.nan
    assert np.isnan(clean_price("invalid"))
    assert np.isnan(clean_price("-$10.00")) or clean_price("-$10.00") == -10.0  # Either is handled by validation later

def test_clean_boolean():
    assert clean_boolean("t") is True
    assert clean_boolean("true") is True
    assert clean_boolean("1") is True
    assert clean_boolean("f") is False
    assert clean_boolean("false") is False
    assert clean_boolean(None) is False
    assert clean_boolean("invalid") is False

def test_clean_listings():
    # Construct a mock df representing raw dirty data
    data = {
        "id": [1, 2, 3, None], # row 3 has null id (should be quarantined)
        "price": ["$100.00", "-$50.00", "$0.00", "$200.00"], # row 1 negative, row 2 zero (both quarantined)
        "latitude": [52.37, 52.38, 95.0, 52.39], # row 2 out of bounds (quarantined)
        "longitude": [4.89, 4.90, 4.91, 200.0], # row 3 out of bounds (quarantined)
        "host_id": [101, 102, 103, 104],
        "host_name": ["Alice", "Bob", "Charlie", "Dave"],
        "host_since": ["2020-01-01", "2021-02-02", "2022-03-03", "invalid-date"],
        "host_is_superhost": ["t", "f", "t", None],
        "room_type": ["Entire home/apt", "Private room", "entire home/apt", "Private Room"],
        "property_type": ["Apartment", "House", "Condo", "Townhouse"],
        "neighbourhood_cleansed": ["Centrum", "Zuid", "Noord", "Oost"]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, quarantined_df = clean_listings(df, "amsterdam")
    
    # Assertions
    # Row 0: Valid. Should be in cleaned_df
    # Row 1: Price negative. Should be quarantined.
    # Row 2: Price zero & Latitude out of bounds. Should be quarantined.
    # Row 3: ID null & Longitude out of bounds. Should be quarantined.
    
    assert cleaned_df.shape[0] == 1
    assert quarantined_df.shape[0] == 3
    
    # Check cleaned output formats
    valid_row = cleaned_df.iloc[0]
    assert valid_row["id"] == 1
    assert valid_row["price"] == 100.0
    assert valid_row["host_is_superhost"] == True
    assert valid_row["room_type"] == "Entire Home/Apt"  # Normalized to Title Case
    
    # Check quarantine reasons
    row_1_err = quarantined_df[quarantined_df["id"] == 2.0]["validation_errors"].values[0]
    assert "invalid_price_value" in row_1_err
    
    row_2_err = quarantined_df[quarantined_df["id"] == 3.0]["validation_errors"].values[0]
    assert "invalid_price_value" in row_2_err or "coordinates_out_of_bounds" in row_2_err
