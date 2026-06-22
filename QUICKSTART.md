# Quick Start Guide

## 1. Setup (One-time)

```bash
# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate  # Windows
# OR
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

## 2. Run Tests (Optional but Recommended)

```bash
PYTHONPATH=. pytest
```

## 3. Run the Pipeline

```bash
$env:PYTHONPATH="."; python src/main.py
```

That's it! The pipeline will:
1. Download Airbnb data for Amsterdam & Venice
2. Clean and validate the data
3. Build a DuckDB data warehouse
4. Generate analytics report and plots

## Outputs

- **Database**: `data/gold/airbnb_dw.duckdb`
- **Report**: `data/gold/analytics_report.md`
- **Plots**: `data/gold/plots/`

## Optional: Upload to Azure (for Power BI)

### Step 1: Set up Azure credentials

Create a file named `.env` in the project root (copy from `.env.example`):

```bash
# Copy the example file
copy .env.example .env
```

Edit `.env` and add your Azure Storage connection string:

```
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT_NAME;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=core.windows.net
```

**Where to get the connection string:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Storage Account
3. Go to **Access Keys** (or **Shared access signature**)
4. Copy the **Connection string** from key 1 or key 2
5. Paste it into `.env`

### Step 2: Run pipeline with Azure upload

```bash
# Run pipeline + upload cleaned data to Azure automatically
PYTHONPATH=. python src/main.py --upload-to-azure

# Also upload gold layer (DuckDB database + reports) for Power BI
PYTHONPATH=. python src/main.py --upload-to-azure --upload-gold
```

### Step 3: Connect Power BI to Azure

1. Open Power BI Desktop
2. **Get Data** → **Azure** → **Azure Blob Storage**
3. Enter your storage account URL: `https://YOUR_ACCOUNT_NAME.blob.core.windows.net`
4. Authenticate with your Azure account
5. Navigate to container `airbnb-cleaned-data` → `cleaned/` folder
6. Select the Parquet files and click **Load**

The `.env` file is automatically loaded by the pipeline — no need to set environment variables manually each time.

## Need Help?

See the full [README.md](README.md) for detailed documentation.