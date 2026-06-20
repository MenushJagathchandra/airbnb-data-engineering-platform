# AI Usage Disclosure

**Candidate:** Menush  
**Assignment:** Expernetic Talent Assessment Program — Data Engineer Intern  
**Date:** June 2026

---

## 1. AI Tools Used

| Tool | Version/Model | Purpose |
|:---|:---|:---|
| Gemini 3.5 Flash | High | Initial scaffolding, code generation, debugging |
| Claude Opus 4.6 | Thinking | Gap analysis, statistical test implementation, report refinement |

---

## 2. AI-Assisted Sections

### Substantially AI-Assisted (with human direction and validation)
- **Pipeline scaffolding** (`src/ingest.py`, `src/clean.py`, `src/model.py`, `src/analyze.py`): The overall architecture, function signatures, and implementation patterns were developed collaboratively with AI assistance. Every module was reviewed, tested, and iterated upon to fix real-world data issues (SELinux permissions, DuckDB schema mismatches, `bathrooms_text` parsing crashes, composite key collisions).
- **DuckDB Star Schema DDL** (`src/model.py`): The dimensional model design (fact/dimension table relationships, surrogate key strategy) was guided by AI suggestions but validated through referential integrity tests and manual SQL queries.
- **Statistical hypothesis tests** (`src/analyze.py`): The Welch's t-tests (H1-H3, H5) and ANOVA (H4) implementations were AI-generated, but test selection rationale, assumption verification, and business interpretations were reviewed and refined by the candidate.
- **Dockerfile and docker-compose.yml**: Initial templates were AI-generated; SELinux volume flags (`:z`) and host UID mapping (`user: "1000:1000"`) were added through iterative debugging of real container failures.
- **Documentation** (`README.md`, `DECISION_LOG.md`): Structure and prose were AI-assisted with candidate-directed content and verification against actual pipeline outputs.

### Human-Directed (AI as implementation tool)
- **Bug fixes**: The `bathrooms_text` empty-string crash, `union_by_name=True` schema mismatch fix, composite key collision resolution, and calendar price `COALESCE` fallback were all discovered through live pipeline execution failures and debugged collaboratively.
- **Test suite** (`tests/`): Test scenarios were designed to validate specific engineering guardrails (surrogate key uniqueness, referential integrity, coordinate bounds). Mock data generators were built to enable offline testing.

---

## 3. Key Prompts Used

1. *"Create a complete, reproducible solution that processes the Inside Airbnb public dataset using an event-driven architecture triggered by Tines and executed via GitHub Actions."* — Initial project scaffolding prompt.
2. *"The pipeline crashed with a ConversionException on bathrooms_text. Fix the DuckDB SQL to handle empty strings and half-bath values."* — Debugging prompt leading to `nullif(regexp_extract(...), '')` fix.
3. *"Add the missing hypothesis tests H1, H2, H3, H5 from the assignment specification with proper null/alternative statements, test selection rationale, and business interpretation."* — Statistical analysis expansion.
4. *"Create a comprehensive gap analysis mapping every assignment requirement against the current implementation."* — Gap analysis and prioritization.

---

## 4. Output Validation

| Validation Method | What Was Checked |
|:---|:---|
| **Live pipeline execution** | Ran `src/main.py` against real Inside Airbnb datasets (Amsterdam: 10,480 listings, 3.8M calendar rows, 501K reviews; Venice: 8,590 listings, 3.1M calendar rows, 841K reviews). Pipeline completed with exit code 0. |
| **Automated test suite** | 10 pytest tests covering ingestion mocks, cleaning rules, schema integrity (PK/FK validation), and sentiment scoring. All passing. |
| **Docker container validation** | Built and executed the full pipeline inside Docker, verifying that the containerized environment produces identical results. Tests also pass inside the container. |
| **Manual SQL queries** | Queried the DuckDB database directly to verify record counts (`[('amsterdam', 5874), ('venice', 7702)]`), surrogate key uniqueness, and spatial distance calculations. |
| **Statistical result verification** | Cross-checked ANOVA p-values, t-test results, and Cohen's d magnitudes against expected ranges. Verified that H5 (weekend vs weekday) correctly reports "fail to reject" when calendar prices are fallback values. |

---

## 5. Modifications Made to AI-Generated Code

| Original AI Output | Modification | Reason |
|:---|:---|:---|
| Surrogate keys used `md5(id::VARCHAR)` | Changed to `md5(concat_ws('\\|\\|', id::VARCHAR, city))` | Prevented cross-city primary key collisions in multi-city dimension tables |
| `dim_hosts` used `SELECT DISTINCT` | Changed to `row_number() OVER (PARTITION BY host_id, city)` | Hosts with multiple listings had conflicting metadata, violating PK uniqueness |
| `bathrooms_text` parsed with `regexp_extract(...) ::DOUBLE` | Wrapped with `nullif(..., '')` and added `CASE WHEN LIKE '%half-bath%' THEN 0.5` | Empty string cast to DOUBLE crashed DuckDB; "Half-bath" has no numeric component |
| Calendar query used `fc.price` directly | Changed to `COALESCE(fc.price, fl.price)` | Raw calendar prices were entirely NULL in both city datasets |
| Docker volume mount was `./data:/app/data` | Changed to `./data:/app/data:z` | SELinux on Fedora/RHEL blocked container access to host-mounted directories |

---

## 6. Critical Assessment

- **AI suggestion rejected**: The initial AI-generated cleaning pipeline used row-by-row iteration (`for idx, row in df.iterrows()`) for validation logic. While functional, this is computationally expensive on 3.8M calendar rows. A vectorized approach would be more efficient but was retained for readability and correctness given the project timeline.
- **AI limitation observed**: AI-generated statistical interpretations sometimes conflated statistical significance with practical significance. For example, Cohen's d values of 0.02 were initially described as "moderate pricing gaps." These were corrected to "negligible effect" with proper magnitude thresholds.
- **Sentiment analysis trade-off**: AI suggested using a HuggingFace Transformer model for sentiment analysis. This was rejected in favor of a lightweight lexicon scorer due to the 1GB+ PyTorch dependency footprint and the multi-hour inference time on 1.34M reviews without GPU acceleration.
