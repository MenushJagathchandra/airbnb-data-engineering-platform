# Architectural Decision Log

This document details the critical architectural decisions, engineering trade-offs, and design justifications made during the implementation of the Expernetic Talent Assessment Program pipeline.

---

## 1. Storage & Processing Engine: DuckDB
- **Decision:** Use **DuckDB** as the core analytical data warehouse engine.
- **Rationale:** 
  - *Vectorized Execution:* DuckDB is designed for high-performance analytical queries (OLAP) and executes operations in columnar vectors, running complex aggregations and spatial calculations on millions of rows in milliseconds.
  - *Serverless & Self-Contained:* It runs out-of-process inside the Python runtime with zero external server dependencies, meaning the entire environment can be spun up in Docker or GitHub Actions without configuring a separate Postgres, MySQL, or Snowflake instance.
  - *Parquet Integration:* DuckDB directly queries directory structures containing Parquet files using SQL (`read_parquet`), allowing us to cleanly decouple raw ingest, staging, and dimensional modeling.
- **Trade-offs:** Lacks support for concurrent multi-write connections, which is acceptable since our pipeline executes in a single-threaded orchestrator context.

---

## 2. Multi-City Surrogate Key Strategy
- **Decision:** Shifted surrogate key generation from single ID hashing (`md5(id::VARCHAR)`) to composite hashing (`md5(concat_ws('||', id::VARCHAR, city))`).
- **Rationale:** 
  - *ID Collisions:* While Inside Airbnb listing IDs are generally unique globally, synthetic datasets and cross-region integrations frequently reuse primary key domains.
  - *Data Warehouse Integrity:* In a centralized star schema, listing surrogate keys (`listing_key`) and host surrogate keys (`host_key`) must remain globally unique. Hashing the entity ID with the city name guarantees zero collision risk across parallel runs.

---

## 3. Host Deduplication via Window Functions
- **Decision:** Populated `dim_hosts` using a SQL window function (`row_number()`) rather than a simple `SELECT DISTINCT`.
- **Rationale:**
  - *One-to-Many Conflicting Attributes:* Listings belong to hosts. If a host has multiple listings in a city, their metadata (such as the `host_is_superhost` status or host name spelling) can vary slightly across raw listing records.
  - *Uniqueness Violations:* A simple `SELECT DISTINCT host_id, host_name, host_is_superhost` would produce multiple rows for the same host, violating the primary key constraint on `host_key`. 
  - *Etl Standard:* Using `row_number() OVER (PARTITION BY host_id, city ORDER BY host_since DESC, host_is_superhost DESC)` forces the engine to pick exactly one representative row for each host, ensuring target referential integrity.

---

## 4. Vectorized Spatial Distance Calculations in SQL
- **Decision:** Computed listing distances to central landmarks using the Haversine formula in DuckDB SQL during the model build, rather than calculating them row-by-row in Python.
- **Rationale:**
  - *Performance:* Running a loop over 15,000+ listings and calculating spherical distances in Python takes several seconds and increases CPU overhead.
  - *SQL Efficiency:* DuckDB's vectorized math functions (`sin`, `cos`, `asin`, `sqrt`) run calculations in parallel across columns, computing distances for all listings and landmarks in less than 5 milliseconds.

---

## 5. Lexicon Sentiment Scoring over Deep Learning
- **Decision:** Implemented a lightweight, word-matching lexicon scorer in Python (`analyze.py`) rather than a HuggingFace Transformer model (e.g., BERT).
- **Rationale:**
  - *Dependency Footprint:* Deep learning models require PyTorch, which is over 1GB in package size, significantly increasing Docker build and download times.
  - *Throughput:* Processing 1.34 million review comments through a deep neural network on a standard CPU would take hours. Our lexicon matcher scans and scores all 1.34 million records in **9 seconds** in a single thread, providing a robust proxy for customer satisfaction at a fraction of the compute cost.

---

## 6. Seasonality Price Fallback
- **Decision:** Applied a `COALESCE(fc.price, fl.price)` fallback in our seasonal analytics query.
- **Rationale:**
  - *Raw Scrape Limitation:* In the Inside Airbnb Venice and Amsterdam crawls, the `price` column in the calendar file was entirely null or missing for all dates.
  - *Graceful Degradation:* Falling back to the listing's base price from `fact_listings` ensures that monthly and day-of-week seasonality aggregations remain fully functional and informative, instead of outputting blank/NaN fields in our reports.

---

## 7. Statistical Test Selection: Welch's t-test over Student's t-test
- **Decision:** Used Welch's t-test (`scipy.stats.ttest_ind(equal_var=False)`) for all pairwise hypothesis comparisons (H1-H3, H5).
- **Rationale:**
  - *Unequal Variance Assumption:* Airbnb listing prices exhibit highly unequal variances across room types, host categories, and review volume segments. The standard Student's t-test assumes equal variances, which would inflate Type I error rates.
  - *Robustness:* Welch's approximation is strictly more robust than the pooled-variance t-test and produces identical results when variances happen to be equal, making it the safer default choice.
- **Trade-offs:** Slightly reduced statistical power compared to Student's t-test when variances are truly equal, but the safety margin against false positives outweighs this cost.

---

## 8. Quarantine Strategy over Silent Drops
- **Decision:** Invalid records are written to a separate quarantine Parquet file (`*_quarantine.parquet`) rather than silently discarded.
- **Rationale:**
  - *Auditability:* In production data pipelines, silently dropping records creates invisible data loss. Quarantined records can be reviewed by data stewards to identify upstream data quality issues.
  - *Transparency:* The quarantine file includes a `validation_errors` column documenting exactly why each record was rejected (e.g., `missing_or_invalid_id`, `invalid_price_value($0.00)`, `coordinates_out_of_bounds`).
  - *Recovery:* If cleaning rules are later determined to be too aggressive, quarantined records can be reprocessed without re-downloading raw data.

---

## 9. Idempotent Pipeline Design
- **Decision:** Both ingestion and cleaning stages check for pre-existing output files and skip processing if they already exist.
- **Rationale:**
  - *Developer Velocity:* Processing 7M+ calendar rows and 1.3M+ reviews takes 2-3 minutes. Skipping completed stages reduces re-run time from ~4 minutes to ~15 seconds during development and debugging.
  - *CI/CD Compatibility:* In GitHub Actions, cached artifacts between runs can be used to avoid redundant downloads and cleaning, reducing compute costs.
  - *Override Mechanism:* The `force=True` parameter on `clean_all()` and file deletion on `build_star_schema()` allow a full rebuild when needed.

---

## 10. Prioritization Rationale
- **Decision:** Focused on data engineering depth (ingestion, cleaning, modeling, containerization) and statistical analysis (5 hypothesis tests, correlation analysis, host segmentation) over data science modeling (price prediction, clustering) and advanced AI (topic modeling, RAG).
- **Rationale:**
  - *Rubric Alignment:* The evaluation weights Problem Solving (30%) and Data Engineering Quality (25%) as the two highest dimensions. Statistical Thinking (20%) and Analytical Storytelling (20%) are tied for third. Data Science & ML (15%) and AI/ML Experimentation (10%) carry lower weights.
  - *Assignment Philosophy:* The specification states: *"A candidate who completes two sections with exceptional depth will outperform one who attempts all sections superficially."* We chose to execute Sections 02-05 with rigor rather than attempting Sections 06-08 at surface level.
  - *What Was Deprioritized:* Price prediction models (§6.1), demand forecasting (§6.2), listing clustering (§6.3), topic modeling (§7.1), and RAG systems (§7.2) were not implemented. With additional time, price prediction using gradient boosting (XGBoost) with SHAP explainability would be the highest-value next addition.

