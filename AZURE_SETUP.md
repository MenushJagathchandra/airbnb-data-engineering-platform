# Azure Blob Storage Setup Guide

This guide walks you through creating an Azure Storage Account and configuring the `.env` file for the Menush pipeline.

---

## Prerequisites

- An Azure account (free tier works: https://azure.microsoft.com/free/)
- Access to [Azure Portal](https://portal.azure.com)

---

## Step 1: Create a Storage Account

1. **Log in to Azure Portal**: https://portal.azure.com
2. **Create a resource**: Click **"Create a resource"** (top left)
3. **Search for**: `Storage account`
4. **Click**: **"Storage account"** → **"Create"**

### Fill in the basics:

| Field | Value |
|-------|-------|
| **Subscription** | Your Azure subscription |
| **Resource group** | Create new (e.g., `menush-rg`) or use existing |
| **Storage account name** | `menushstorage` (must be globally unique, lowercase, 3-24 chars) |
| **Region** | Choose closest to you (e.g., `East US`, `West Europe`) |
| **Performance** | `Standard` (sufficient for this project) |
| **Redundancy** | `Locally-redundant storage (LRS)` (cheapest option) |

5. **Click**: **"Review + create"** → **"Create"**
6. **Wait** for deployment to complete (~1-2 minutes)
7. **Click**: **"Go to resource"**

---

## Step 2: Create a Container

1. In your Storage Account, go to **"Containers"** (left menu, under "Data storage")
2. **Click**: **"+ Container"**
3. Fill in:

| Field | Value |
|-------|-------|
| **Name** | `airbnb-cleaned-data` |
| **Public access level** | `Private (no anonymous access)` |

4. **Click**: **"Create"**

---

## Step 3: Get Your Connection String

You need the connection string to authenticate the pipeline. There are two methods:

### Method A: Using Access Keys (Recommended for Development)

1. In your Storage Account, go to **"Access Keys"** (left menu, under "Security + networking")
2. You'll see **Key 1** and **Key 2** — either works
3. Under **Key 1**, click **"Show keys"**
4. Copy the **Connection string** value

It looks like this:
```
DefaultEndpointsProtocol=https;AccountName=menushstorage;AccountKey=abc123XYZ...==;EndpointSuffix=core.windows.net
```

### Method B: Using Shared Access Signature (SAS) (More Secure)

1. In your Storage Account, go to **"Shared access signature"** (left menu)
2. Configure:
   - **Allowed services**: Blob
   - **Allowed resource types**: Container, Object
   - **Permissions**: Read, Write, Create, List
   - **Start/Expiry**: Set appropriate dates
3. Click **"Generate SAS and connection string"**
4. Copy the **Connection string** (includes the SAS token)

---

## Step 4: Configure the `.env` File

1. **Copy the example file**:
   ```bash
   copy .env.example .env
   ```

2. **Open `.env`** in your text editor

3. **Replace the placeholder with your actual connection string**:

   ```env
   # Azure Blob Storage Configuration
   AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=menushstorage;AccountKey=abc123XYZ...==;EndpointSuffix=core.windows.net
   ```

   **Important**: Paste your actual connection string after the `=` sign. Do NOT include quotes.

4. **Save the file**

---

## Step 5: Verify the Setup

Run a quick test to ensure Azure connectivity:

```bash
# Activate your virtual environment first
.venv\Scripts\activate

# Test Azure upload
PYTHONPATH=. python src/azure_upload.py
```

You should see output like:
```
INFO - Using connection string for Azure Blob Storage authentication.
INFO - Container already exists: airbnb-cleaned-data
INFO - Uploading cleaned data from: data/cleaned
INFO - Successfully uploaded: listings.parquet -> cleaned/amsterdam/listings.parquet
...
INFO - Azure Upload Summary:
INFO -   Uploaded: 6
INFO -   Failed:   0
INFO -   Skipped:  0
```

---

## Step 6: Run the Full Pipeline with Azure Upload

```bash
# Run the complete pipeline + upload to Azure
PYTHONPATH=. python src/main.py --upload-to-azure

# Also upload DuckDB database and reports (for Power BI)
PYTHONPATH=. python src/main.py --upload-to-azure --upload-gold
```

---

## Alternative: Service Principal (For Production/CI-CD)

If you're running in production or CI/CD (not recommended for local development):

### 1. Create a Service Principal in Azure

```bash
az ad sp create-for-rbac --name "menush-pipeline-sp" --role "Storage Blob Data Contributor" --scopes "/subscriptions/YOUR_SUB_ID/resourceGroups/menush-rg/providers/Microsoft.Storage/storageAccounts/menushstorage"
```

This outputs:
```json
{
  "appId": "abc123...",
  "password": "xyz789...",
  "tenant": "def456..."
}
```

### 2. Fill `.env` with Service Principal credentials

```env
# Service Principal Authentication
AZURE_STORAGE_ACCOUNT_URL=https://menushstorage.blob.core.windows.net
AZURE_TENANT_ID=def456...
AZURE_CLIENT_ID=abc123...
AZURE_CLIENT_SECRET=xyz789...
```

**Note**: Remove or comment out `AZURE_STORAGE_CONNECTION_STRING` when using Service Principal.

---

## Troubleshooting

### Error: "Container does not exist"
- The pipeline auto-creates the container. If it fails, create it manually in Azure Portal (Step 2).

### Error: "Authentication failed"
- Double-check your connection string in `.env`
- Ensure there are no extra spaces or quotes
- Verify the Storage Account name is correct

### Error: "Network timeout"
- Check your internet connection
- Large files may take time to upload (the pipeline shows progress in logs)

### Files not appearing in Azure
- Check the container in Azure Portal: Storage Account → Containers → `airbnb-cleaned-data`
- Files are under the `cleaned/` folder

---

## Security Notes

- **NEVER** commit `.env` to git (it's in `.gitignore`)
- **NEVER** share your connection string publicly
- For production, use Service Principal or Managed Identity instead of access keys
- Rotate your access keys periodically (Azure Portal → Access Keys → Rotate keys)

---

## Next Steps

After uploading, connect Power BI to your Azure Blob Storage:

1. Open Power BI Desktop
2. **Get Data** → **Azure** → **Azure Blob Storage**
3. Enter: `https://menushstorage.blob.core.windows.net`
4. Authenticate with your Azure account
5. Navigate to `airbnb-cleaned-data` → `cleaned/`
6. Select Parquet files → **Load**

See `README.md` Section 6.2 for detailed Power BI setup instructions.