# Industrial-Grade Airbnb ETL & Dimensional Warehousing Pipeline
**Expernetic Talent Assessment Program — Production-Grade Data Engineering Blueprint**

**Author**: Menush Jagathchandra | **GitHub**: [@MenushJagathchandra](https://github.com/MenushJagathchandra)

Menush is a configuration-driven, event-triggered, and fully containerized data engineering pipeline. It ingests, standardizes, models, and analyzes millions of rows of Inside Airbnb data for multiple cities (currently targeting Amsterdam and Venice). It compiles the processed data into a DuckDB Star Schema Data Warehouse and runs statistical modeling (ANOVA, Cohen's d, distance gradients) and lexicon-based sentiment analysis on customer reviews.

---

## 1. System Architecture & Component Blueprint

Below is the directory structure of what you currently have in your workspace:

```
.
├── config/
│   └── cities.yaml          # YAML-based configuration layer containing urls & landmark coordinates
├── data/                    # Dynamic data storage layer (git-ignored)
│   ├── raw/                 # Ingested raw gzipped CSV datasets from Inside Airbnb
│   ├── cleaned/             # Standardized Parquet files and quarantine logs
│   └── gold/                # Final DuckDB analytical database, markdown reports, and plots
├── src/
│   ├── config.py            # Path initialization and cities configuration parser
│   ├── ingest.py            # Low-memory chunked streaming downloader with exponential backoff retries
│   ├── clean.py             # Type parser, coordinate validator, and quarantine partitioner
│   ├── model.py             # DuckDB Star Schema compiler (composite surrogate keys, Haversine spatial math)
│   ├── analyze.py           # Hypothesis tests (H1-H5), ANOVA, Cohen's d, correlation matrix, sentiment, host portfolio analysis
│   └── main.py              # Orchestration entrypoint running stages 1 through 4
├── tests/                   # Full pytest integration and contract verification test suite
│   ├── test_ingest.py
│   ├── test_clean.py
│   ├── test_model.py
│   └── test_analyze.py
├── .gitignore               # Excludes data/, .venv/, __pycache__/ from version control
├── AI_USAGE_DISCLOSURE.md   # Mandatory AI tool usage disclosure (Section 10)
├── DECISION_LOG.md          # 10 architectural decisions with trade-off analysis (Section 03.6)
├── Dockerfile               # Reproducible slim Python container
├── docker-compose.yml       # Dev/test volume mapping with host user mapping (UID:GID 1000:1000)
└── .github/workflows/
    └── pipeline.yml         # CI/CD pipeline triggered by repository_dispatch webhooks (e.g., from Tines)
```

---

## 2. Operational Runbook: Step-by-Step Execution

Here is exactly what you should do, what happens when you do it, and how to verify the results at each step.

### Step 1: Run the Validation Test Suite
Before running the pipeline, verify that the environment, DDL logic, math calculations, and data contract checkers are functioning correctly.

*   **What to do**:
    ```bash
    PYTHONPATH=. .venv/bin/pytest
    ```
    *(To run inside the Docker container)*:
    ```bash
    docker-compose run pipeline pytest
    ```
*   **What happens**:
    1. Pytest collects 10 integration and unit tests from the `tests/` directory.
    2. It mocks the ingestion engine, ensuring no external network requests are made.
    3. It validates type cleaning rules, standardizations, coordinate boundaries, and quarantine partitioning.
    4. It constructs a mock DuckDB instance in memory, compiles the Star Schema DDLs, verifies key relationships (PK/FK), and validates the Haversine distance calculations.
    5. It runs the statistical routines to confirm ANOVA and Cohen's d calculate without division-by-zero errors.
*   **What you see**:
    `10 passed in xx.xx seconds` indicating 100% test coverage and validation.

### Step 2: Execute the Production ETL Pipeline
Execute the ingestion, cleaning, schema modeling, and statistical generation for live cities.

*   **What to do**:
    ```bash
    PYTHONPATH=. .venv/bin/python src/main.py
    ```
    *(To run inside the Docker container)*:
    ```bash
    docker-compose up --build
    ```
*   **What happens**:
    1. **Ingestion (`src/ingest.py`)**: Checks if raw files (`listings.csv.gz`, `calendar.csv.gz`, `reviews.csv.gz`) are already present in `data/raw/<city>`. If missing, it downloads them from Inside Airbnb in 1MB chunks with exponential backoff retries.
    2. **Cleaning & Quality (`src/clean.py`)**: Normalizes currency strings (removing symbols/commas), cleans booleans ('t'/'f' to True/False), parses dates, and checks geographical coordinate ranges. Valid listings are stored in Parquet format; invalid records are written to a quarantine file.
    3. **Star Schema Compilation (`src/model.py`)**: Connects to the DuckDB instance in `data/gold/airbnb_dw.duckdb`. It mounts the cleaned Parquet files, builds the staging tables using `union_by_name=True` to resolve schema mismatches, and compiles the dimensional model (`dim_listings`, `dim_hosts`, `dim_locations`, `dim_landmarks`, `dim_date`, `fact_listings`, `fact_calendar`, `fact_reviews`).
    4. **Analytics & AI Sentiment (`src/analyze.py`)**: Maps a Python-based sentiment lexicon over the comments of 1.34 million reviews, calculating scores from -1.0 to 1.0. It runs spatial proximity aggregations, seasonality occupancy calculations, and neighborhood-level ANOVA tests.
*   **What you see**:
    Logs detail the completion of each step. The final database is compiled at `data/gold/airbnb_dw.duckdb`, the analytics report is generated at `data/gold/analytics_report.md`, and visual charts are output to `data/gold/plots/`.

### Step 3: Query the Dimensional Warehouse
Query the data warehouse locally from your host machine.

*   **What to do**:
    Open a Python REPL:
    ```bash
    .venv/bin/python
    ```
    Execute the following queries:
    ```python
    import duckdb
    con = duckdb.connect('data/gold/airbnb_dw.duckdb')
    
    # 1. Inspect Compiled Dimensional Model Tables
    print(con.execute("SHOW TABLES").fetchall())
    
    # 2. Verify Multi-City Aggregations
    print(con.execute("SELECT city, COUNT(*) FROM fact_listings GROUP BY city").fetchall())
    
    # 3. View Spatial Distance Premium to Landmarks
    print(con.execute("""
        SELECT dl.name, fl.price, fl.distance_to_nearest_landmark_km, fl.nearest_landmark_name 
        FROM fact_listings fl
        JOIN dim_listings dl ON fl.listing_key = dl.listing_key
        ORDER BY fl.distance_to_nearest_landmark_km ASC 
        LIMIT 5
    """).fetchall())
    
    exit()
    ```
*   **What happens**:
    DuckDB opens the database file in read-write mode. It queries the columnar facts and dimensions, returning the exact record count per city and listings sorted by geographical proximity to landmarks.
*   **What you see**:
    The tables list (`fact_listings`, `dim_listings`, `dim_hosts`, etc.), the record distribution `[('amsterdam', 5874), ('venice', 7702)]`, and computed spatial query outputs.

---

## 3. Data Warehouse Star Schema & DWH Design

The warehouse is designed to maintain structural integrity while optimizing query speeds.

```
       [dim_hosts]                     [dim_listings]
            │                                │
            ├─────────────────┬──────────────┘
                              │
                      [fact_listings] ────────── [dim_locations]
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
     [fact_calendar]    [fact_reviews]   [dim_landmarks]
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                          [dim_date]
```

### Key Engineering Guardrails
1. **Composite Hashing for Surrogate Keys**: Hashing only the source ID (`md5(id)`) leads to primary key collisions in multi-city setups. Menush generates keys using `md5(concat_ws('||', id::VARCHAR, city))`, guaranteeing zero collisions.
2. **Host Deduplication**: Hosts with multiple listings may have conflicting metadata. We apply `row_number() OVER (PARTITION BY host_id, city ORDER BY host_since DESC)` to select a single, representative host record, preserving dimensional integrity.
3. **Vectorized Haversine Calculations**: Distances are calculated directly in SQL on DuckDB's vectorized execution engine using:
   ```sql
   2 * 6371 * asin(sqrt(
       sin(radians(lat2 - lat1) / 2) ^ 2 + 
       cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ^ 2
   ))
   ```
4. **Calendar Fallback Optimization**: Scraped calendar prices are often unpopulated. We apply `COALESCE(fc.price, fl.price)` to fall back to the listing's base price, allowing seasonality analysis to execute without generating `NaN` values.

---

## 4. Business Intelligence & Statistical Analysis

Menush calculates the following analytics:
1. **Market overview**: Nightly listing averages, medians, and ratings broken down by room type.
2. **Geographical proximity gradients**: Groups listings into distance bands (`<1km`, `1-2.5km`, `2.5-5km`, `5km+`) to evaluate premiums.
3. **ANOVA & Cohen's d**: Runs one-way ANOVA tests to determine if neighborhood pricing variances are statistically significant, calculating Cohen's d to measure the effect size between prime districts.
4. **Review sentiment correlation**: Computes the correlation between customer sentiment scores and overall listing ratings and prices.

---

## 5. CI/CD & Orchestration Blueprint

### GitHub Actions Automation (`.github/workflows/pipeline.yml`)
The workflow is configured to run tests and execute the ETL pipeline automatically. It triggers on:
- A `repository_dispatch` webhook event (type: `trigger_pipeline`) sent by external orchestrators.
- A manual `workflow_dispatch` trigger.

### Tines Webhook Integration Setup
To trigger the pipeline from Tines:
1. Create a HTTP Request Action in Tines.
2. Configure the payload to send a POST request to:
   ```
   POST https://api.github.com/repos/<owner>/<repo>/dispatches
   ```
3. Set the headers:
   - `Authorization: Bearer <GITHUB_PAT_TOKEN>`
   - `Accept: application/vnd.github.v3+json`
4. Set the body payload:
   ```json
   {
     "event_type": "trigger_pipeline"
   }
   ```

---

## 6. Azure Cloud Integration & Power BI Connectivity

### 6.1 Azure Blob Storage Setup

Menush supports uploading cleaned Parquet data directly to Azure Blob Storage for centralized data lake storage and Power BI consumption.

#### Prerequisites
- Azure Storage Account (Standard or Premium)
- Container created in the storage account (e.g., `airbnb-cleaned-data`)

#### Authentication Methods

**Option A: Connection String (Development/Testing)**
```bash
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
```

**Option B: Service Principal (Production)**
```bash
export AZURE_STORAGE_ACCOUNT_URL="https://<your-storage-account>.blob.core.windows.net"
export AZURE_TENANT_ID="<your-tenant-id>"
export AZURE_CLIENT_ID="<your-service-principal-app-id>"
export AZURE_CLIENT_SECRET="<your-service-principal-secret>"
```

**Option C: Managed Identity (Azure VMs/AKS)**
```bash
export AZURE_STORAGE_ACCOUNT_URL="https://<your-storage-account>.blob.core.windows.net"
# No additional credentials needed when running on Azure resources with managed identity enabled
```

#### Running the Pipeline with Azure Upload

```bash
# Install updated dependencies
pip install -r requirements.txt

# Run pipeline and upload cleaned data to Azure
PYTHONPATH=. .venv/bin/python src/main.py --upload-to-azure

# Also upload gold layer (DuckDB database, reports, plots)
PYTHONPATH=. .venv/bin/python src/main.py --upload-to-azure --upload-gold
```

#### Upload Structure in Azure Blob Storage

```
airbnb-cleaned-data (container)
├── cleaned/
│   ├── amsterdam/
│   │   ├── listings.parquet
│   │   ├── calendar.parquet
│   │   ├── reviews.parquet
│   │   ├── listings_quarantine.parquet
│   │   ├── calendar_quarantine.parquet
│   │   └── reviews_quarantine.parquet
│   └── venice/
│       ├── listings.parquet
│       ├── calendar.parquet
│       ├── reviews.parquet
│       ├── listings_quarantine.parquet
│       ├── calendar_quarantine.parquet
│       └── reviews_quarantine.parquet
└── gold/ (optional, if --upload-gold is used)
    ├── airbnb_dw.duckdb
    ├── analytics_report.md
    └── plots/
```

---

### 6.2 Power BI Connection Guide

#### Method 1: Direct Azure Blob Storage Connection (Recommended)

1. **Open Power BI Desktop** → Get Data → Azure → **Azure Blob Storage**

2. **Enter your storage account URL**:
   ```
   https://<your-storage-account>.blob.core.windows.net
   ```

3. **Authenticate**:
   - Organizational account (recommended for Service Principal / Managed Identity)
   - Or Account key (for connection string authentication)

4. **Navigate to the container** (`airbnb-cleaned-data`) → `cleaned` folder

5. **Select Parquet files**:
   - Power BI will automatically detect the Parquet schema
   - Select the desired files (e.g., `listings.parquet`, `calendar.parquet`, `reviews.parquet`)
   - Click **Load** or **Transform Data** to open Power Query Editor

6. **Combine Multiple City Files** (optional):
   - In Power Query, use **Combine Files** feature
   - Or append queries for Amsterdam and Venice datasets

#### Method 2: Using Azure Data Lake Storage Gen2 (Hierarchical Namespace)

If your storage account has Hierarchical Namespace enabled (ADLS Gen2):

1. Use **Azure Data Lake Storage Gen2** connector in Power BI
2. Navigate to the container and folder path
3. Parquet files are natively supported with schema preservation

#### Method 3: Download and Connect Locally

If you prefer to keep data local for Power BI:

```bash
# Download cleaned data from Azure (using Azure CLI)
az storage blob download-batch \
  --destination ./data/cleaned \
  --source airbnb-cleaned-data \
  --pattern "cleaned/*/*.parquet" \
  --account-name <your-storage-account>
```

Then connect Power BI to the local Parquet files.

---

### 6.3 Power BI Data Model Recommendations

#### Star Schema Alignment

The uploaded Parquet files align with the DuckDB Star Schema. In Power BI, you can recreate the dimensional model:

| Power BI Table | Source Parquet | Role |
|----------------|----------------|------|
| `dim_listings` | `listings.parquet` | Dimension table |
| `dim_hosts` | Derived from `listings.parquet` | Dimension table |
| `dim_locations` | Derived from `listings.parquet` | Dimension table |
| `dim_date` | Generated from calendar dates | Dimension table |
| `fact_listings` | `listings.parquet` | Fact table |
| `fact_calendar` | `calendar.parquet` | Fact table |
| `fact_reviews` | `reviews.parquet` | Fact table |

#### Calculated Columns / Measures

```dax
-- Distance to nearest landmark (if coordinates are loaded)
Distance_km = 
    var lat1 = SELECTEDVALUE('dim_listings'[latitude])
    var lon1 = SELECTEDVALUE('dim_listings'[longitude])
    var lat2 = 52.3791  -- Amsterdam Centraal
    var lon2 = 4.9003
    return
        6371 * 2 * ASIN(
            SQRT(
                SIN(RADIANS(lat2 - lat1) / 2) ^ 2 +
                COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
                SIN(RADIANS(lon2 - lon1) / 2) ^ 2
            )
        )

-- Average price by neighborhood
Avg_Price_By_Neighborhood = AVERAGE('fact_listings'[price])

-- Occupancy rate (from calendar)
Occupancy_Rate = 1 - AVERAGE('fact_calendar'[available])
```

#### Scheduled Refresh

1. In Power BI Service, configure **Scheduled Refresh** (e.g., daily/weekly)
2. Use **Azure Blob Storage** as the data source
3. Set up **Gateway** if using on-premises data sources alongside Azure

---

## 7. What to Do Next (Production Roadmap)

To deploy Menush into a production-grade environment, follow this roadmap:

1. **Configure Remote Storage Integration**:
   - Instead of storing raw data locally, configure `src/ingest.py` to stream files directly to an object store (e.g., AWS S3 or Google Cloud Storage).
   - Configure DuckDB to load Parquet files directly from S3 using the `httpfs` extension:
     ```sql
     INSTALL httpfs;
     LOAD httpfs;
     SELECT * FROM read_parquet('s3://my-bucket/cleaned/**/*.parquet');
     ```
2. **Implement Schema Evolution and Incremental Loads**:
   - Transition from full rebuilds to incremental loads (`UPSERT` / `MERGE`) based on the `scrape_date` or calendar date partitions to handle growing datasets efficiently.
3. **Setup Slack/PagerDuty Alerts**:
   - Add alert triggers to the pipeline. If a step fails, have the Python process send a webhook notification to Slack or Microsoft Teams.
4. **Configure Dashboard Tools**:
   - Connect BI tools (like Superset, PowerBI, or Tableau) directly to the DuckDB instance, or export tables to a PostgreSQL or Snowflake warehouse to serve dashboards.
