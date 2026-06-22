# Power BI Dashboard Guide

This guide shows you how to create a simple Power BI dashboard using your cleaned Airbnb data from Azure Blob Storage.

---

## Prerequisites

- Power BI Desktop installed (free download: https://powerbi.microsoft.com/desktop/)
- Data uploaded to Azure Blob Storage (run `python src/main.py --upload-to-azure` first)
- Azure Storage Account name and connection details

---

## Step 1: Connect Power BI to Azure Blob Storage

1. **Open Power BI Desktop**

2. **Get Data**:
   - Click **"Get Data"** → **"Azure"** → **"Azure Blob Storage"**
   - Or: **Home** → **Get Data** → **More...** → **Azure** → **Azure Blob Storage**

3. **Enter your storage account URL**:
   ```
   https://YOUR_STORAGE_ACCOUNT_NAME.blob.core.windows.net
   ```
   Example: `https://menushstorage.blob.core.windows.net`

4. **Authenticate**:
   - Select **"Organizational account"** (recommended)
   - Sign in with your Azure account
   - Click **"Connect"**

5. **Navigate to your data**:
   - Select your container: `airbnb-cleaned-data`
   - Navigate to folder: `cleaned`
   - You'll see city folders: `amsterdam/` and `venice/`

---

## Step 2: Import Parquet Files

### Option A: Import All Files at Once (Recommended)

1. In the Navigator window, expand `cleaned` → `amsterdam`
2. Select these files (hold Ctrl to multi-select):
   - `listings.parquet`
   - `calendar.parquet`
   - `reviews.parquet`
3. Click **"Combine"** → **"Combine & Load"**
4. Repeat for `venice` folder
5. Power BI will automatically append the data

### Option B: Import One City at a Time

1. Select `listings.parquet` from `amsterdam/`
2. Click **"Load"**
3. Repeat for `venice/listings.parquet`
4. In Power Query, append the two queries:
   - **Home** → **Append Queries** → **Append Queries as New**
   - Select both Amsterdam and Venice tables

---

## Step 3: Prepare Data in Power Query

After loading, Power Query Editor opens. Do these transformations:

### For Listings Table:

1. **Remove unnecessary columns**:
   - Keep: `id`, `name`, `price`, `room_type`, `property_type`, `neighbourhood`, `latitude`, `longitude`, `city`, `host_is_superhost`, `accommodates`, `bedrooms`, `bathrooms`, `number_of_reviews`, `review_scores_rating`, `distance_to_nearest_landmark_km`, `nearest_landmark_name`, `average_sentiment_score`

2. **Change data types**:
   - `price` → Decimal Number
   - `latitude` / `longitude` → Decimal Number
   - `review_scores_rating` → Decimal Number
   - `distance_to_nearest_landmark_km` → Decimal Number
   - `average_sentiment_score` → Decimal Number

3. **Rename columns** (optional, for clarity):
   - `neighbourhood` → `Neighborhood`
   - `review_scores_rating` → `Rating`
   - `distance_to_nearest_landmark_km` → `Distance to Landmark (km)`

4. **Click "Close & Apply"**

### For Calendar Table (if using):

1. Keep: `listing_id`, `date`, `available`, `price`, `city`
2. Change `date` to Date type
3. Change `available` to True/False
4. Create a relationship: `calendar.listing_id` → `listings.id`

---

## Step 4: Create Data Model (Star Schema)

Go to **Model** view (left sidebar, third icon):

### Create Dimension Tables

1. **Dim City**:
   - From `listings` table, right-click `city` column
   - **Create new** → **Dimension**
   - Name it `Dim City`

2. **Dim Room Type**:
   - Right-click `room_type` → **Create new** → **Dimension**
   - Name it `Dim Room Type`

3. **Dim Neighborhood**:
   - Right-click `neighbourhood` → **Create new** → **Dimension**
   - Name it `Dim Neighborhood`

### Create Relationships

Drag columns to connect tables:
- `listings[city]` → `Dim City[city]`
- `listings[room_type]` → `Dim Room Type[room_type]`
- `listings[neighbourhood]` → `Dim Neighborhood[neighbourhood]`

---

## Step 5: Build Dashboard Visuals

Go to **Report** view (left sidebar, first icon):

### Visual 1: Price by City (Bar Chart)

1. Select **Clustered bar chart**
2. **Axis**: `Dim City[city]`
3. **Values**: `listings[price]` → set aggregation to **Average**
4. **Title**: "Average Listing Price by City"
5. **Format**: 
   - Data labels: On
   - Y-axis: Currency format ($)

### Visual 2: Price Distribution (Histogram)

1. Select **Histogram** (or use a clustered column chart)
2. **X-axis**: `listings[price]`
3. **Y-axis**: Count of `listings[id]`
4. **Title**: "Price Distribution"
5. **Filter**: Exclude outliers (price < $500 or use 95th percentile)

### Visual 3: Room Type Breakdown (Pie Chart)

1. Select **Pie chart**
2. **Legend**: `Dim Room Type[room_type]`
3. **Values**: Count of `listings[id]`
4. **Title**: "Listings by Room Type"

### Visual 4: Top Neighborhoods (Table)

1. Select **Table**
2. Add columns:
   - `Dim Neighborhood[neighbourhood]`
   - `listings[price]` (Average)
   - `listings[review_scores_rating]` (Average)
   - Count of `listings[id]`
3. Sort by Average Price (descending)
4. **Title**: "Top Neighborhoods by Price"

### Visual 5: Price vs Distance to Landmark (Scatter Chart)

1. Select **Scatter chart**
2. **X-axis**: `listings[distance_to_nearest_landmark_km]`
3. **Y-axis**: `listings[price]`
4. **Details**: `listings[name]`
5. **Title**: "Price vs Distance to Landmark"
6. **Insight**: Shows if listings closer to landmarks cost more

### Visual 6: Sentiment Score Distribution (Card or Gauge)

1. Select **Card** visual
2. **Fields**: `listings[average_sentiment_score]` (Average)
3. **Title**: "Average Review Sentiment"
4. Range: -1.0 (negative) to 1.0 (positive)

### Visual 7: Occupancy by Month (Line Chart) - If using calendar data

1. Select **Line chart**
2. **X-axis**: `calendar[date]` → set to `date` hierarchy (Month)
3. **Y-axis**: Average of `calendar[available]` (invert: 1 - available = occupancy)
4. **Legend**: `Dim City[city]`
5. **Title**: "Estimated Occupancy by Month"

---

## Step 6: Add Filters (Slicers)

Add these slicers to make the dashboard interactive:

1. **City Slicer**:
   - Visual: **Slicer**
   - Field: `Dim City[city]`
   - Place at the top

2. **Room Type Slicer**:
   - Visual: **Slicer**
   - Field: `Dim Room Type[room_type]`

3. **Price Range Slicer**:
   - Visual: **Slicer**
   - Field: `listings[price]`
   - Type: **Slider**

4. **Neighborhood Slicer**:
   - Visual: **Slicer**
   - Field: `Dim Neighborhood[neighbourhood]`

---

## Step 7: Format and Polish

### Theme
- **View** → **Themes** → Choose a theme (e.g., "Executive", "City Park")
- Or customize colors to match your brand

### Layout
- Arrange visuals in a grid:
  - Top: Title + City slicer
  - Row 1: Price by City (bar) + Room Type (pie)
  - Row 2: Price Distribution (histogram) + Top Neighborhoods (table)
  - Row 3: Price vs Distance (scatter) + Sentiment (card)

### Tooltips
- Enable tooltips for interactive exploration:
  - Select a visual → **Format** → **Tooltip** → **On**
  - Add fields like `neighbourhood`, `room_type`, `price`

---

## Step 8: Publish to Power BI Service (Optional)

To share your dashboard online:

1. **Save your report**: `File` → `Save` → `Airbnb_Dashboard.pbix`

2. **Publish**:
   - **Home** → **Publish**
   - Sign in with your Microsoft account
   - Choose a workspace (or create "My Workspace")
   - Click **Publish**

3. **Set up Scheduled Refresh** (if connected to Azure):
   - Go to https://app.powerbi.com
   - Find your dataset → **Settings** → **Scheduled refresh**
   - Set frequency: **Weekly** on **Saturday** (to match your pipeline)
   - Connect to Azure Blob Storage as the data source

---

## Sample Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  Airbnb Analytics Dashboard          [Amsterdam] [Venice]│
├────────────────────┬────────────────────────────────────┤
│  Avg Price by City │  Listings by Room Type (Pie)      │
│  [Bar Chart]       │                                    │
├────────────────────┴────────────────────────────────────┤
│  Price Distribution (Histogram)                         │
├────────────────────┬────────────────────────────────────┤
│  Price vs Distance │  Top Neighborhoods (Table)        │
│  to Landmark       │                                    │
├────────────────────┴────────────────────────────────────┤
│  Average Sentiment: 0.15  [Card]                        │
└─────────────────────────────────────────────────────────┘
```

---

## Key Insights Your Dashboard Can Show

1. **Price Premium**: How much more expensive are listings near landmarks?
2. **Best Value**: Which neighborhoods offer the best price-to-rating ratio?
3. **Seasonality**: When are prices highest/lowest (if using calendar data)?
4. **Host Quality**: Do superhosts have higher ratings and prices?
5. **Market Distribution**: What room types dominate each city?

---

## Troubleshooting

### "Can't connect to Azure Blob Storage"
- Verify storage account URL is correct
- Check you're signed in with the right Azure account
- Ensure the container `airbnb-cleaned-data` exists

### "Parquet files not showing"
- Power BI supports Parquet, but you may need to enable it:
  - **File** → **Options and settings** → **Options** → **Preview features**
  - Check **"Parquet support"** → Restart Power BI

### "Data is slow"
- Use **Import mode** instead of DirectQuery (faster for small datasets)
- Filter to only needed columns during import
- Consider aggregating data in Azure (e.g., pre-calculate neighborhood averages)

### "Relationship errors"
- Ensure primary keys are unique (e.g., `listings[id]`)
- Use **Manage Relationships** → **Auto-detect** to fix

---

## Next Steps

1. **Start simple**: Create 3-4 basic visuals first
2. **Iterate**: Add more visuals and slicers as you explore the data
3. **Publish**: Share with stakeholders via Power BI Service
4. **Automate**: Set up scheduled refresh every Saturday after the pipeline runs

See `README.md` Section 6.2 for more Power BI connection details.