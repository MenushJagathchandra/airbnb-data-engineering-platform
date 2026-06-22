# GitHub Secrets Setup for Automated Pipeline

This guide explains how to securely store your Azure credentials in GitHub so the automated pipeline can upload data to Azure Blob Storage every Saturday.

---

## Why GitHub Secrets?

The pipeline runs on GitHub's servers (not your computer), so it can't access your local `.env` file. GitHub Secrets securely stores sensitive data like connection strings, encrypted and only exposed to workflows during execution.

---

## Step 1: Get Your Azure Connection String

Follow the steps in `AZURE_SETUP.md` to create a Storage Account and get your connection string.

Example:
```
DefaultEndpointsProtocol=https;AccountName=menushstorage;AccountKey=abc123XYZ...==;EndpointSuffix=core.windows.net
```

---

## Step 2: Add Secret to GitHub Repository

1. **Go to your GitHub repository**: `https://github.com/YOUR_USERNAME/YOUR_REPO`

2. **Navigate to Settings**: Click **"Settings"** tab (top menu)

3. **Go to Secrets**: 
   - Left sidebar → **"Secrets and variables"** → **"Actions"**
   - Or directly: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`

4. **Click**: **"New repository secret"**

5. **Fill in the form**:

   | Field | Value |
   |-------|-------|
   | **Name** | `AZURE_STORAGE_CONNECTION_STRING` |
   | **Secret** | Paste your full connection string from Step 1 |

   **Important**: The name must be exactly `AZURE_STORAGE_CONNECTION_STRING` (case-sensitive) to match the workflow file.

6. **Click**: **"Add secret"**

---

## Step 3: Verify the Secret

After adding, you should see `AZURE_STORAGE_CONNECTION_STRING` in your secrets list. The value is hidden (shows as `***` for security).

---

## How It Works

In `.github/workflows/pipeline.yml`, the secret is referenced like this:

```yaml
env:
  AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}
```

When the workflow runs:
1. GitHub encrypts the secret and injects it as an environment variable
2. The pipeline uses it to authenticate with Azure Blob Storage
3. The secret never appears in logs or workflow history

---

## Step 4: Enable Workflow Permissions (If Needed)

By default, GitHub Actions can read secrets. If you have branch protection rules:

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **"Workflow permissions"**
3. Ensure **"Read and write permissions"** is selected (or at least "Read repository contents")
4. Check **"Allow GitHub Actions to create and approve pull requests"** if needed

---

## Step 5: Test the Automated Pipeline

### Option A: Manual Trigger (Recommended First Test)

1. Go to **Actions** tab in your GitHub repo
2. Select **"Airbnb ETL & Analytics Pipeline"** from the left sidebar
3. Click **"Run workflow"** → **"Run workflow"** (green button)
4. Watch the workflow execute in real-time

### Option B: Wait for Saturday

The pipeline is scheduled to run every Saturday at midnight UTC (cron: `0 0 * * 6`).

To check the schedule:
- Go to **Actions** → **"Airbnb ETL & Analytics Pipeline"**
- You'll see a clock icon with "This workflow runs every Saturday at 12:00 AM UTC"

---

## What Happens When the Pipeline Runs

### Summary

Every Saturday at midnight UTC, GitHub Actions automatically:

1. **Checks out your code** from the repository
2. **Sets up Python 3.11** environment
3. **Installs dependencies** from `requirements.txt`
4. **Runs tests** (`pytest`) to ensure code integrity
5. **Executes the ETL pipeline**:
   - Downloads latest Airbnb data for Amsterdam & Venice (if not cached)
   - Cleans and validates the data (removes invalid records)
   - Builds a DuckDB Star Schema data warehouse
   - Runs statistical analysis (ANOVA, Cohen's d, sentiment analysis)
   - Generates analytics report and plots
6. **Uploads to Azure Blob Storage**:
   - Cleaned Parquet files → `airbnb-cleaned-data/cleaned/`
   - DuckDB database + reports → `airbnb-cleaned-data/gold/` (optional)
7. **Archives outputs** as GitHub Actions artifacts (retained for 7 days)

### Timeline

| Step | Duration | What Happens |
|------|----------|--------------|
| Checkout | ~5 sec | Downloads code |
| Setup Python | ~10 sec | Installs Python 3.11 |
| Install deps | ~30 sec | Installs pandas, duckdb, azure SDK, etc. |
| Tests | ~2 min | Runs 10 pytest tests |
| Pipeline | ~5-10 min | Downloads, cleans, models, analyzes |
| Azure Upload | ~2-5 min | Uploads Parquet files to Azure |
| Archive | ~30 sec | Saves artifacts to GitHub |

**Total**: ~10-20 minutes per run

---

## Monitoring the Pipeline

### View Workflow Runs

1. Go to **Actions** tab
2. Click on a workflow run to see details
3. Each step shows:
   - ✅ (green check) = success
   - ❌ (red X) = failure
   - ⏸️ (yellow dot) = in progress

### View Logs

Click on any step to expand its logs. You'll see:
- Download progress
- Cleaning statistics (e.g., "Listings clean complete: 5874 valid, 23 quarantined")
- Azure upload confirmation (e.g., "Successfully uploaded: listings.parquet")
- Any errors if something fails

### Get Notifications

GitHub can email you if the workflow fails:

1. Go to **Settings** → **Notifications**
2. Under **"GitHub Actions"**, select **"Send notifications for failed runs only"**

---

## Troubleshooting

### Workflow doesn't trigger on Saturday

- Check the cron syntax: `0 0 * * 6` = midnight UTC on Saturday (day 6 = Saturday)
- Verify the workflow is enabled: Actions tab → ensure no "Disabled" badge
- Check repository is public or you have GitHub Actions enabled (private repos need GitHub Pro/Team)

### Azure upload fails

- Verify `AZURE_STORAGE_CONNECTION_STRING` secret is set correctly (no typos)
- Check Azure Storage Account exists and container name is `airbnb-cleaned-data`
- Review workflow logs for specific error messages

### Tests fail

- The pipeline stops if tests fail (no upload happens)
- Check the "Run Test Suite" step logs for details
- Fix the code locally, commit, and push to trigger a new run

---

## Cost Considerations

- **GitHub Actions**: Free for public repos. Private repos get 2,000 minutes/month free (this pipeline uses ~20 min/week = 80 min/month).
- **Azure Blob Storage**: ~$0.02/GB/month for Standard LRS. With ~100MB of Parquet files, cost is negligible (< $0.01/month).

---

## Next Steps

After the pipeline runs:
1. **Check Azure Portal**: Storage Account → Containers → `airbnb-cleaned-data` → `cleaned/`
2. **Connect Power BI**: Get Data → Azure Blob Storage → `https://YOUR_ACCOUNT.blob.core.windows.net`
3. **Build dashboards**: Use the Parquet files to create visualizations

See `AZURE_SETUP.md` for Power BI connection details.