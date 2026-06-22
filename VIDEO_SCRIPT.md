# Industrial-Grade Airbnb ETL Pipeline — 10-Minute Video Script

**Title**: Industrial-Grade Airbnb ETL Pipeline | Data Engineering Demo  
**Duration**: ~10 minutes  
**Audience**: Technical and non-technical stakeholders  
**Tone**: Professional, confident, clear  

---

## [0:00 - 1:00] INTRO & PROBLEM STATEMENT

**[VISUAL]**: Title card with project name "Airbnb ETL & Analytics Pipeline" and subtitle "Data Engineering Demo". Show Airbnb logo and Inside Airbnb data source.

**[NARRATION]**:
"Hi, I'm Sathush, and today I'm going to walk you through a production-grade data engineering pipeline I built to transform raw Airbnb data into actionable business intelligence.

The problem I solved: Inside Airbnb publishes massive CSV files — millions of rows of listings, calendars, and reviews — but this data is messy, inconsistent, and impossible to analyze directly. Companies and researchers need clean, structured data to make decisions about pricing, location, and market trends.

My solution: An automated pipeline that ingests raw data, cleans it, builds a data warehouse, runs statistical analysis, and uploads results to Azure for Power BI dashboards — all running automatically every Saturday."

---

## [1:00 - 2:30] WHAT THE PIPELINE DOES (HIGH-LEVEL)

**[VISUAL]**: Animated flowchart showing 4 stages:
1. **Ingest** → Download icon + "1MB chunks with retry logic"
2. **Clean** → Broom icon + "Validate, normalize, quarantine bad records"
3. **Model** → Database icon + "DuckDB Star Schema"
4. **Analyze** → Chart icon + "Statistics + Sentiment + Reports"

**[NARRATION]**:
"This pipeline follows a four-stage architecture:

**Stage 1: Ingestion**. The pipeline downloads gzipped CSV files from Inside Airbnb for multiple cities — currently Amsterdam and Venice. It uses chunked streaming with exponential backoff retries, so even if the network hiccups, it recovers gracefully. If files already exist, it skips the download — idempotent and efficient.

**Stage 2: Cleaning**. Raw CSVs are messy. Prices have dollar signs and commas. Booleans are 't' and 'f'. Coordinates might be missing or out of bounds. My cleaning engine normalizes all of this, validates geographic ranges, and quarantines invalid records into separate files with documented rejection reasons. We never silently drop data.

**Stage 3: Dimensional Modeling**. This is where the magic happens. I compile a DuckDB Star Schema Data Warehouse with 7 dimension tables and 3 fact tables. I use composite surrogate keys — hashing the listing ID plus city name — to guarantee zero collisions across multi-city datasets. I also deduplicate hosts using window functions, so each host appears exactly once in the dimension table.

**Stage 4: Analysis**. The pipeline runs statistical hypothesis tests — ANOVA, t-tests, Cohen's d effect sizes — and a lexicon-based sentiment analysis on 1.34 million reviews. It generates an analytics report and 13 publication-quality plots."

---

## [2:30 - 4:30] KEY FINDINGS (BUSINESS INSIGHTS)

**[VISUAL]**: Split screen showing 3-4 key charts from the report:
- Bar chart: Average price by city
- Scatter plot: Price vs. distance to landmark
- Table: Top neighborhoods
- Histogram: Host portfolio distribution

**[NARRATION]**:
"Let me share some of the most interesting findings from analyzing Amsterdam and Venice.

**Finding 1: Entire-home premium**. Entire homes command a 2.5 to 3x price premium over private rooms in both cities. This is statistically significant with p-values less than 1e-9 and large effect sizes. If you're a host, converting a private room to an entire unit is the single highest-impact decision you can make.

**Finding 2: Geographic pricing gradients**. Venice shows a clear proximity premium — listings within 1 kilometer of St. Mark's Square average $296 per night, while peripheral listings average $129. That's a 2.3x premium for walkability to the historic center. Amsterdam, interestingly, shows no such pattern. Urban-ring listings actually outprice the core, driven by large canal houses in premium residential neighborhoods.

**Finding 3: Superhost effect**. Superhosts achieve significantly higher ratings. In Venice, the effect is massive — Cohen's d of 0.81, meaning Superhosts rate nearly a full standard deviation higher. This validates the Superhost program as a credible quality signal.

**Finding 4: Market structure**. Venice is more commercially consolidated — 34% of hosts operate multiple listings, with the top 10 controlling 8.7% of supply. Amsterdam is fragmented, with 92% of hosts running just one listing. This has regulatory implications: cities may need to cap multi-listing portfolios to protect housing stock."

---

## [4:30 - 6:30] TECHNICAL DEEP DIVE (ENGINEERING HIGHLIGHTS)

**[VISUAL]**: Code snippets and architecture diagrams:
- Show `src/main.py` orchestrator
- Show DuckDB Star Schema diagram
- Show Azure Blob Storage container structure
- Show GitHub Actions workflow YAML

**[NARRATION]**:
"Let me highlight a few engineering decisions that make this pipeline production-grade.

**Composite Surrogate Keys**. In multi-city setups, listing IDs can overlap. If I just hash the ID, I get primary key collisions. My solution: hash the concatenation of ID and city — `md5(id || city)` — guaranteeing uniqueness across all cities.

**Vectorized Haversine Calculations**. Computing distances between listings and landmarks could be slow if done row-by-row in Python. Instead, I wrote the Haversine formula directly in DuckDB SQL, leveraging their vectorized execution engine. This processes millions of rows in seconds, not minutes.

**Quarantine Over Silent Drops**. When a record fails validation — missing ID, invalid price, out-of-bounds coordinates — I don't delete it. I write it to a quarantine file with a reason code. This ensures auditability and helps data engineers debug quality issues.

**Azure Integration**. The pipeline uploads cleaned Parquet files to Azure Blob Storage, organized by city. This enables Power BI connectivity — stakeholders can connect directly to Azure and build dashboards without database access. The upload happens automatically when you run the pipeline with a single flag: `--upload-to-azure`.

**Automation**. A GitHub Actions workflow runs every Saturday at midnight UTC. It installs dependencies, runs tests, executes the pipeline, uploads to Azure, and archives artifacts. The whole run takes about 10 to 20 minutes, and you get an email if anything fails."

---

## [6:30 - 8:00] AI/ML COMPONENT (SENTIMENT ANALYSIS)

**[VISUAL]**: Show sentiment scoring logic, then a scatter plot of sentiment vs. rating.

**[NARRATION]**:
"One of the most interesting components is the sentiment analysis engine. I processed 1.34 million guest reviews using a custom lexicon-based scorer — 21 positive words like 'amazing', 'clean', 'perfect', and 21 negative words like 'dirty', 'noisy', 'broken'.

Each review is tokenized, matched against the lexicon, and scored from -1.0 to +1.0. The entire corpus processes in 9 seconds on a single CPU thread — about 149,000 reviews per second.

Why a lexicon instead of a transformer model like BERT? Two reasons: speed and cost. A HuggingFace model would require a 1GB+ PyTorch dependency and hours of inference time without a GPU. For a weekly batch job, the lexicon is pragmatic and interpretable.

The results: sentiment correlates moderately with numeric ratings — around 0.34 to 0.39 — but shows near-zero correlation with price. This confirms a key business insight: guest satisfaction is driven by hospitality quality, not by how much they pay."

---

## [8:00 - 9:00] POWER BI DASHBOARD & DATA CONSUMPTION

**[VISUAL]**: Screen recording of Power BI Desktop:
- Connecting to Azure Blob Storage
- Loading Parquet files
- Building a bar chart and scatter plot
- Adding slicers for city and room type

**[NARRATION]**:
"The cleaned data isn't just sitting in a database — it's ready for business intelligence. I created a comprehensive guide for building Power BI dashboards directly from the Azure Blob Storage Parquet files.

The process is straightforward: connect Power BI to your storage account, navigate to the `airbnb-cleaned-data` container, select the Parquet files, and Power BI automatically detects the schema. You can then build visuals like price by city, price versus distance to landmarks, and neighborhood comparisons.

I've also set up slicers for city, room type, price range, and neighborhood, making the dashboard fully interactive. Stakeholders can filter, drill down, and explore the data without writing a single line of SQL."

---

## [9:00 - 9:45] FUTURE WORK & CALL TO ACTION

**[VISUAL]**: Roadmap slide with 3-4 future items:
- More cities (Barcelona, Paris, Rome, Lisbon, Berlin)
- AI Chatbot for natural language querying
- Predictive price models (XGBoost)
- Incremental ETL with MERGE logic

**[NARRATION]**:
"This project is far from done. The pipeline is already multi-city ready — I just need to add entries to a YAML config file. I plan to expand to 5+ European cities to create a pan-European short-term rental benchmark.

I'm also building an AI chatbot that lets non-technical users ask questions in plain English — like 'What's the average price of entire homes near Dam Square in June?' — and get instant answers with auto-generated charts. This democratizes data access without requiring Power BI or SQL knowledge.

On the modeling side, I'd like to add XGBoost price prediction with SHAP explainability, and transition from full rebuilds to incremental MERGE operations for efficient longitudinal tracking.

The code, documentation, and this report are all open-source and available on GitHub. I've included detailed setup guides for Azure, Power BI, and GitHub Actions so you can reproduce this end-to-end.

Thanks for watching — I'm happy to take questions."

---

## [9:45 - 10:00] OUTRO

**[VISUAL]**: End card with:
- Project name: Airbnb ETL & Analytics Pipeline
- GitHub repo link (placeholder)
- LinkedIn/contact info (placeholder)
- "Built for Expernetic Talent Assessment Program"

**[NARRATION]**:
"Thanks for watching. Feel free to reach out if you'd like to discuss the architecture, the statistical findings, or potential collaborations."

---

## PRODUCTION NOTES

### Recording Tips
- **Screen recording**: Use OBS Studio or Camtasia. Record at 1080p, 30fps.
- **Voiceover**: Record narration in a quiet room with a decent microphone (Blue Yeti, Samson Q2U). Speak clearly, moderate pace (~150 words/minute).
- **Editing**: Use DaVinci Resolve (free) or Premiere Pro. Add zoom-in effects when showing code. Use smooth transitions between sections.

### Visual Assets Needed
1. `title_card.png` — Project name + tagline
2. `flowchart_4stage.png` — Animated pipeline diagram
3. `chart_price_by_city.png` — Bar chart from report
4. `chart_price_vs_distance.png` — Scatter plot
5. `chart_neighborhoods.png` — Top neighborhoods table
6. `chart_host_portfolio.png` — Host distribution histogram
7. `code_snippet_keys.png` — Screenshot of composite key logic
8. `code_snippet_haversine.png` — Screenshot of SQL distance calculation
9. `azure_container.png` — Screenshot of Azure Blob Storage structure
10. `github_actions.png` — Screenshot of workflow run
11. `sentiment_scatter.png` — Sentiment vs. rating plot
12. `power_bi_demo.mp4` — 30-second screen recording of Power BI connection
13. `roadmap.png` — Future work slide
14. `end_card.png` — Outro with contact info

### Timing Checklist
- [ ] Intro: 0:00 - 1:00 (60 sec)
- [ ] Pipeline overview: 1:00 - 2:30 (90 sec)
- [ ] Key findings: 2:30 - 4:30 (120 sec)
- [ ] Technical deep dive: 4:30 - 6:30 (120 sec)
- [ ] Sentiment analysis: 6:30 - 8:00 (90 sec)
- [ ] Power BI dashboard: 8:00 - 9:00 (60 sec)
- [ ] Future work: 9:00 - 9:45 (45 sec)
- [ ] Outro: 9:45 - 10:00 (15 sec)

### Delivery Tips
- Start with the business problem, not the technology.
- Use analogies: "Think of the pipeline as a factory that takes raw ore (CSV files) and produces refined gold (clean Parquet files in a data warehouse)."
- Emphasize production qualities: error handling, monitoring, automation.
- Show, don't just tell — use screen recordings for Power BI and Azure demos.
- End with a clear call to action: check the GitHub repo, try the pipeline, connect on LinkedIn.

---

## ALTERNATE: SHORT-FORM VERSION (3 Minutes)

If you need a shorter version for LinkedIn or Twitter:

**[0:00 - 0:30]**: Problem + Solution  
"Inside Airbnb data is messy and impossible to analyze directly. I built an automated pipeline that cleans, models, and analyzes millions of rows in 10 minutes."

**[0:30 - 1:30]**: Key Findings (2-3 bullets with charts)  
"Venice listings near St. Mark's Square command a 2.3x price premium. Superhosts rate 0.8 standard deviations higher. Entire homes cost 3x more than private rooms."

**[1:30 - 2:30]**: Tech Stack + Demo  
"Built with Python, DuckDB, Azure Blob Storage, and GitHub Actions. Here's the Power BI dashboard..."

**[2:30 - 3:00]**: Call to Action  
"Full report and code on GitHub. Link in bio. Thanks for watching!"

---

**END OF SCRIPT**