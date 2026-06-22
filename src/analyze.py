import os
import logging
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import load_config, GOLD_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Simple sentiment dictionary
POSITIVE_WORDS = {
    "amazing", "beautiful", "clean", "perfect", "friendly", "great", "excellent", 
    "comfortable", "wonderful", "love", "spacious", "nice", "quiet", "easy", 
    "highly", "best", "superb", "charming", "awesome", "fantastic", "lovely"
}
NEGATIVE_WORDS = {
    "noisy", "dirty", "unresponsive", "terrible", "bad", "disappointing", "cold", 
    "smell", "slow", "broken", "worst", "uncomfortable", "rude", "poor", 
    "expensive", "disappointed", "avoid", "loud", "old", "small", "dusty"
}

def analyze_sentiment(text: str) -> float:
    """
    Computes a sentiment score between -1.0 and 1.0 based on lexicon matching.
    """
    if not isinstance(text, str) or not text:
        return 0.0
    words = text.lower().split()
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / float(total)

def run_analysis_pipeline(db_path: Path, output_dir: Path):
    """
    Executes the analytical pipeline, updates the DuckDB DW, and generates outputs.
    """
    logger.info("Starting analysis and statistics pipeline...")
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    con = duckdb.connect(str(db_path))
    
    try:
        # 1. Run Sentiment Analysis & Update DW
        logger.info("Computing sentiment scores for reviews...")
        df_reviews = con.execute("SELECT review_key, comments FROM fact_reviews WHERE comments IS NOT NULL").fetchdf()
        
        if not df_reviews.empty:
            df_reviews["sentiment_score"] = df_reviews["comments"].apply(analyze_sentiment)
            
            # Write sentiment back to fact_reviews using a temp table
            con.execute("CREATE TEMP TABLE temp_reviews AS SELECT * FROM df_reviews")
            con.execute("""
                UPDATE fact_reviews
                SET sentiment_score = temp_reviews.sentiment_score
                FROM temp_reviews
                WHERE fact_reviews.review_key = temp_reviews.review_key
            """)
            con.execute("DROP TABLE temp_reviews")
            logger.info("Updated sentiment_score in fact_reviews.")
            
            # Calculate and update average sentiment in fact_listings
            con.execute("""
                WITH avg_sentiment AS (
                    SELECT listing_key, AVG(sentiment_score) as avg_score
                    FROM fact_reviews
                    GROUP BY listing_key
                )
                UPDATE fact_listings
                SET average_sentiment_score = avg_sentiment.avg_score
                FROM avg_sentiment
                WHERE fact_listings.listing_key = avg_sentiment.listing_key
            """)
            logger.info("Updated average_sentiment_score in fact_listings.")

        # 2. Extract Data for Analysis
        logger.info("Extracting data frames for statistical modeling...")
        
        # Listings Data
        df_listings = con.execute("""
            SELECT 
                fl.listing_key,
                fl.city,
                fl.price,
                fl.accommodates,
                fl.bedrooms,
                fl.beds,
                fl.bathrooms,
                fl.number_of_reviews,
                fl.review_scores_rating,
                fl.distance_to_nearest_landmark_km,
                fl.nearest_landmark_name,
                fl.nearest_landmark_type,
                fl.average_sentiment_score,
                fl.host_key,
                dl.room_type,
                dl.property_type,
                loc.neighbourhood,
                dh.host_is_superhost
            FROM fact_listings fl
            JOIN dim_listings dl ON fl.listing_key = dl.listing_key
            JOIN dim_locations loc ON fl.location_key = loc.location_key
            LEFT JOIN dim_hosts dh ON fl.host_key = dh.host_key
        """).fetchdf()
        
        # Calendar Data
        df_calendar = con.execute("""
            SELECT 
                fc.listing_key,
                fc.date_key,
                fc.available,
                COALESCE(fc.price, fl.price) AS price,
                dd.month,
                dd.month_name,
                dd.day_of_week,
                dd.day_name,
                dd.is_weekend,
                fl.city
            FROM fact_calendar fc
            JOIN dim_date dd ON fc.date_key = dd.date_key
            JOIN fact_listings fl ON fc.listing_key = fl.listing_key
        """).fetchdf()

        # Reports Generation
        report_lines = []
        report_lines.append("# Expernetic Airbnb Analytics Report")
        report_lines.append("## Business Intelligence and Statistical Insights")
        report_lines.append("\n")

        # --- A. Summary Statistics ---
        report_lines.append("### 1. Market Overview & Summary Statistics")
        for city in df_listings["city"].unique():
            city_df = df_listings[df_listings["city"] == city]
            report_lines.append(f"#### City: {city.title()}")
            report_lines.append(f"- **Total Listings Analyzed:** {len(city_df)}")
            report_lines.append(f"- **Average Listing Price:** ${city_df['price'].mean():.2f}")
            report_lines.append(f"- **Median Listing Price:** ${city_df['price'].median():.2f}")
            report_lines.append(f"- **Average Rating:** {city_df['review_scores_rating'].mean():.2f}/5.0")
            report_lines.append(f"- **Average Sentiment Score:** {city_df['average_sentiment_score'].mean():.3f}")
            
            # Room type breakdown
            rt_df = city_df.groupby("room_type")["price"].agg(["count", "mean"]).reset_index()
            report_lines.append("\n*Room Type Breakdown:*")
            for _, row in rt_df.iterrows():
                report_lines.append(f"  - **{row['room_type']}:** {row['count']} listings, avg price: ${row['mean']:.2f}")
            report_lines.append("\n")

            # Price Distribution Histogram
            plt.figure(figsize=(10, 6))
            city_df["price"].clip(upper=city_df["price"].quantile(0.95)).hist(bins=50, edgecolor="black", alpha=0.7)
            plt.title(f"{city.title()}: Price Distribution (clipped at 95th percentile)")
            plt.xlabel("Price ($)")
            plt.ylabel("Frequency")
            plt.savefig(plots_dir / f"{city}_price_distribution.png")
            plt.close()

            # Price by Room Type Box Plot
            plt.figure(figsize=(10, 6))
            sns.boxplot(data=city_df[city_df["price"] < city_df["price"].quantile(0.95)], x="room_type", y="price")
            plt.title(f"{city.title()}: Price by Room Type")
            plt.xlabel("Room Type")
            plt.ylabel("Price ($)")
            plt.xticks(rotation=15)
            plt.tight_layout()
            plt.savefig(plots_dir / f"{city}_price_by_room_type.png")
            plt.close()

        # --- B. Geographic Pricing Gradients & Landmark Proximity ---
        report_lines.append("### 2. Geographic Pricing Gradients & Infrastructure Impact")
        
        # We define distance bands
        df_listings["distance_band"] = pd.cut(
            df_listings["distance_to_nearest_landmark_km"],
            bins=[0, 1, 2.5, 5, 100],
            labels=["<1km (Ultra-Core)", "1-2.5km (Core)", "2.5-5km (Urban Ring)", "5km+ (Peripheral)"]
        )
        
        for city in df_listings["city"].unique():
            city_df = df_listings[df_listings["city"] == city]
            report_lines.append(f"#### Proximity Premium in {city.title()}")
            
            band_stats = city_df.groupby("distance_band", observed=False)["price"].agg(["count", "mean", "median"]).reset_index()
            for _, row in band_stats.iterrows():
                report_lines.append(f"- **{row['distance_band']}:** {row['count']} listings ({row['count']/len(city_df)*100:.1f}%), avg price: ${row['mean']:.2f} (median: ${row['median']:.2f})")
            
            # Correlation
            corr_val = city_df["price"].corr(city_df["distance_to_nearest_landmark_km"])
            report_lines.append(f"- **Correlation (Price vs. Distance):** {corr_val:.3f}")
            
            # Business interpretation
            if corr_val < -0.2:
                interpret = "Strong negative correlation. Listings closer to major landmarks command a significant pricing premium, demonstrating that tourists value walkability and center-access above all."
            elif corr_val < 0:
                interpret = "Mild negative correlation. Listings closer to central infrastructure show a slight price premium."
            else:
                interpret = "Weak or positive correlation. Proximity to configured landmarks has little direct linear impact on price, possibly due to suburban luxury listings or other local factors."
            report_lines.append(f"  - *Business Interpretation:* {interpret}\n")
            
            # Create Plot
            plt.figure(figsize=(10, 6))
            sns.scatterplot(data=city_df, x="distance_to_nearest_landmark_km", y="price", hue="nearest_landmark_type", alpha=0.7)
            plt.title(f"{city.title()}: Listing Price vs Distance to Nearest Landmark")
            plt.xlabel("Distance to Nearest Landmark (km)")
            plt.ylabel("Price ($)")
            plt.savefig(plots_dir / f"{city}_price_vs_distance.png")
            plt.close()

        # --- C. Temporal Seasonality ---
        report_lines.append("### 3. Temporal Seasonality & Occupancy Patterns")
        
        if not df_calendar.empty:
            df_calendar["occupancy"] = (~df_calendar["available"]).astype(int)
            
            for city in df_calendar["city"].unique():
                city_cal = df_calendar[df_calendar["city"] == city]
                report_lines.append(f"#### Seasonality in {city.title()}")
                
                # Monthly stats
                monthly = city_cal.groupby("month").agg({"price": "mean", "occupancy": "mean"}).reset_index()
                report_lines.append("*Monthly In-Season Pricing and Occupancy Peaks:*")
                for _, row in monthly.iterrows():
                    report_lines.append(f"  - **Month {int(row['month'])}:** Avg Price: ${row['price']:.2f}, Est. Occupancy: {row['occupancy']*100:.1f}%")
                
                # Day of week stats
                dow = city_cal.groupby("day_of_week").agg({"price": "mean", "occupancy": "mean"}).reset_index()
                report_lines.append("\n*Day-of-Week (Weekend Premium) Analysis:*")
                # 0=Sunday, 1=Monday... or DuckDB format (usually 0=Sunday/Monday; let's list as indexes)
                for _, row in dow.iterrows():
                    report_lines.append(f"  - **Day {int(row['day_of_week'])}:** Avg Price: ${row['price']:.2f}, Est. Occupancy: {row['occupancy']*100:.1f}%")
                
                report_lines.append("\n")
                
                # Create Seasonality Plots
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
                sns.lineplot(data=monthly, x="month", y="price", marker="o", ax=ax1, color="blue")
                ax1.set_title(f"{city.title()} Price by Month")
                ax1.set_ylabel("Avg Price ($)")
                
                sns.barplot(data=dow, x="day_of_week", y="occupancy", ax=ax2, color="orange")
                ax2.set_title(f"{city.title()} Occupancy by Day of Week")
                ax2.set_ylabel("Occupancy Rate")
                plt.savefig(plots_dir / f"{city}_seasonality.png")
                plt.close()
        else:
            report_lines.append("No active calendar data processed. Temporal seasonality calculations skipped.\n")

        # --- D. Statistical Hypothesis Testing (ANOVA & Cohen's d) ---
        report_lines.append("### 4. Inferential Statistical Hypothesis Testing")
        
        for city in df_listings["city"].unique():
            city_df = df_listings[df_listings["city"] == city]
            report_lines.append(f"#### Neighborhood Price Variance (ANOVA) - {city.title()}")
            
            # Filter neighborhoods with at least 5 listings to get meaningful statistics
            neigh_counts = city_df["neighbourhood"].value_counts()
            active_neighs = neigh_counts[neigh_counts >= 5].index.tolist()
            
            if len(active_neighs) >= 2:
                groups = [city_df[city_df["neighbourhood"] == n]["price"].values for n in active_neighs]
                f_val, p_val = stats.f_oneway(*groups)
                
                report_lines.append(f"- **F-Statistic:** {f_val:.4f}")
                report_lines.append(f"- **p-value:** {p_val:.4g}")
                
                # Business interpretation of ANOVA
                if p_val < 0.05:
                    interpret = f"Reject Null Hypothesis (H0). The price differences across neighborhoods in {city.title()} are statistically highly significant. Neighborhood location is a strong driver of listing prices."
                else:
                    interpret = f"Fail to Reject Null Hypothesis (H0). Neighborhood differences in listing prices in {city.title()} are not statistically significant at 95% confidence."
                report_lines.append(f"  - *Interpretation:* {interpret}")
                
                # Pairwise Cohen's d between top 2 neighborhoods
                if len(active_neighs) >= 2:
                    n1_name, n2_name = active_neighs[0], active_neighs[1]
                    g1 = city_df[city_df["neighbourhood"] == n1_name]["price"].values
                    g2 = city_df[city_df["neighbourhood"] == n2_name]["price"].values
                    
                    mean1, mean2 = np.mean(g1), np.mean(g2)
                    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
                    len1, len2 = len(g1), len(g2)
                    
                    # Pooled standard deviation
                    pooled_sd = np.sqrt(((len1 - 1) * var1 + (len2 - 1) * var2) / (len1 + len2 - 2))
                    
                    if pooled_sd > 0:
                        cohens_d = (mean1 - mean2) / pooled_sd
                        report_lines.append(f"- **Pairwise Contrast ({n1_name} vs. {n2_name}):**")
                        report_lines.append(f"  - **{n1_name} mean price:** ${mean1:.2f} (n={len1})")
                        report_lines.append(f"  - **{n2_name} mean price:** ${mean2:.2f} (n={len2})")
                        report_lines.append(f"  - **Cohen's d Effect Size:** {cohens_d:.4f}")
                        
                        # Magnitude description
                        abs_d = abs(cohens_d)
                        if abs_d < 0.2:
                            mag = "Negligible effect"
                        elif abs_d < 0.5:
                            mag = "Small effect"
                        elif abs_d < 0.8:
                            mag = "Medium effect"
                        else:
                            mag = "Large effect"
                        report_lines.append(f"  - *Business Interpretation:* {mag}. This indicates that the average difference in pricing between these two top districts is {abs_d:.1f} standard deviations, which represents a {'substantial' if abs_d >= 0.5 else 'moderate'} pricing gap for operators targeting these submarkets.")
            else:
                report_lines.append("Insufficient listings per neighborhood to perform reliable ANOVA.\n")
            report_lines.append("\n")

        # --- D2. Additional Hypothesis Tests (H1, H2, H3, H5) ---
        report_lines.append("### 4b. Additional Hypothesis Tests")

        for city in df_listings["city"].unique():
            city_df = df_listings[df_listings["city"] == city]
            report_lines.append(f"#### City: {city.title()}")

            # H1: Entire-home vs Private Room prices
            entire = city_df[city_df["room_type"] == "Entire Home/Apt"]["price"].dropna()
            private = city_df[city_df["room_type"] == "Private Room"]["price"].dropna()
            if len(entire) > 1 and len(private) > 1:
                t_stat, p_val = stats.ttest_ind(entire, private, equal_var=False)
                d_h1 = (entire.mean() - private.mean()) / np.sqrt((entire.var() + private.var()) / 2)
                report_lines.append("**H1: Entire-home listings command higher prices than private rooms.**")
                report_lines.append(f"- Test: Welch's t-test (unequal variances assumed)")
                report_lines.append(f"- Entire Home mean: ${entire.mean():.2f} (n={len(entire)}), Private Room mean: ${private.mean():.2f} (n={len(private)})")
                report_lines.append(f"- t-statistic: {t_stat:.4f}, p-value: {p_val:.4g}")
                report_lines.append(f"- Cohen's d: {d_h1:.4f}")
                if p_val < 0.05:
                    report_lines.append(f"  - *Interpretation:* Reject H0. Entire-home listings are priced significantly higher than private rooms in {city.title()}. This confirms the structural premium that whole-unit rentals command, driven by higher capacity, privacy, and amenity access.")
                else:
                    report_lines.append(f"  - *Interpretation:* Fail to reject H0 at 95% confidence.")
                report_lines.append("")

            # H2: Superhost vs non-superhost ratings
            superhost_ratings = city_df[city_df["host_is_superhost"] == True]["review_scores_rating"].dropna()
            non_superhost_ratings = city_df[city_df["host_is_superhost"] == False]["review_scores_rating"].dropna()
            if len(superhost_ratings) > 1 and len(non_superhost_ratings) > 1:
                t_stat, p_val = stats.ttest_ind(superhost_ratings, non_superhost_ratings, equal_var=False)
                d_h2 = (superhost_ratings.mean() - non_superhost_ratings.mean()) / np.sqrt((superhost_ratings.var() + non_superhost_ratings.var()) / 2)
                report_lines.append("**H2: Superhost listings achieve higher review scores than non-superhost listings.**")
                report_lines.append(f"- Test: Welch's t-test")
                report_lines.append(f"- Superhost mean rating: {superhost_ratings.mean():.3f} (n={len(superhost_ratings)}), Non-superhost mean: {non_superhost_ratings.mean():.3f} (n={len(non_superhost_ratings)})")
                report_lines.append(f"- t-statistic: {t_stat:.4f}, p-value: {p_val:.4g}")
                report_lines.append(f"- Cohen's d: {d_h2:.4f}")
                if p_val < 0.05:
                    report_lines.append(f"  - *Interpretation:* Reject H0. Superhosts in {city.title()} achieve statistically higher review ratings. The Superhost badge serves as a credible quality signal for guests and correlates with measurably better guest experiences.")
                else:
                    report_lines.append(f"  - *Interpretation:* Fail to reject H0 at 95% confidence.")
                report_lines.append("")

            # H3: Listings with >10 reviews vs fewer
            high_rev = city_df[city_df["number_of_reviews"] > 10]["price"].dropna()
            low_rev = city_df[city_df["number_of_reviews"] <= 10]["price"].dropna()
            if len(high_rev) > 1 and len(low_rev) > 1:
                t_stat, p_val = stats.ttest_ind(high_rev, low_rev, equal_var=False)
                report_lines.append("**H3: Listings with >10 reviews have different prices than those with fewer.**")
                report_lines.append(f"- Test: Welch's t-test")
                report_lines.append(f"- >10 reviews mean price: ${high_rev.mean():.2f} (n={len(high_rev)}), ≤10 reviews mean: ${low_rev.mean():.2f} (n={len(low_rev)})")
                report_lines.append(f"- t-statistic: {t_stat:.4f}, p-value: {p_val:.4g}")
                if p_val < 0.05:
                    report_lines.append(f"  - *Interpretation:* Reject H0. Review volume is associated with a statistically significant price difference in {city.title()}, suggesting that established listings with booking history can sustain different pricing strategies.")
                else:
                    report_lines.append(f"  - *Interpretation:* Fail to reject H0 at 95% confidence.")
                report_lines.append("")

        # H5: Weekend vs Weekday pricing
        if not df_calendar.empty:
            report_lines.append("#### Weekend vs. Weekday Pricing (H5)")
            for city in df_calendar["city"].unique():
                city_cal = df_calendar[df_calendar["city"] == city]
                weekend_prices = city_cal[city_cal["is_weekend"] == True]["price"].dropna()
                weekday_prices = city_cal[city_cal["is_weekend"] == False]["price"].dropna()
                if len(weekend_prices) > 1 and len(weekday_prices) > 1:
                    t_stat, p_val = stats.ttest_ind(weekend_prices, weekday_prices, equal_var=False)
                    report_lines.append(f"**{city.title()}:**")
                    report_lines.append(f"- Weekend mean price: ${weekend_prices.mean():.2f} (n={len(weekend_prices):,}), Weekday mean: ${weekday_prices.mean():.2f} (n={len(weekday_prices):,})")
                    report_lines.append(f"- t-statistic: {t_stat:.4f}, p-value: {p_val:.4g}")
                    if p_val < 0.05:
                        report_lines.append(f"  - *Interpretation:* Reject H0. Weekend pricing is statistically different from weekday pricing in {city.title()}, confirming the weekend premium effect driven by leisure travel demand.")
                    else:
                        report_lines.append(f"  - *Interpretation:* Fail to reject H0 at 95% confidence. In this dataset the weekend premium is not statistically detectable, likely because the calendar prices use the listing base price as a fallback.")
                    report_lines.append("")

        report_lines.append("\n")

        # --- D3. Correlation Matrix ---
        report_lines.append("### 4c. Correlation Analysis")
        numeric_cols = ["price", "accommodates", "bedrooms", "beds", "bathrooms",
                        "number_of_reviews", "review_scores_rating", "distance_to_nearest_landmark_km",
                        "average_sentiment_score"]
        corr_df = df_listings[numeric_cols].corr()

        # Top price drivers
        price_corrs = corr_df["price"].drop("price").sort_values(key=abs, ascending=False)
        report_lines.append("**Strongest drivers of listing price (Pearson correlation):**")
        for feat, val in price_corrs.items():
            report_lines.append(f"- {feat}: **{val:.3f}**")
        report_lines.append("")

        # Correlation Heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True)
        plt.title("Feature Correlation Matrix")
        plt.tight_layout()
        plt.savefig(plots_dir / "correlation_matrix.png")
        plt.close()
        report_lines.append("\n")

        # --- D4. Host Portfolio Analysis ---
        report_lines.append("### 4d. Host Portfolio & Supply Concentration")
        for city in df_listings["city"].unique():
            city_df = df_listings[df_listings["city"] == city]
            host_counts = city_df.groupby("host_key").size().reset_index(name="listing_count")
            single = (host_counts["listing_count"] == 1).sum()
            multi = (host_counts["listing_count"] > 1).sum()
            top10_hosts = host_counts.nlargest(10, "listing_count")["listing_count"].sum()
            total = len(city_df)
            report_lines.append(f"#### {city.title()}")
            report_lines.append(f"- Single-listing hosts: **{single}** ({single/(single+multi)*100:.1f}%)")
            report_lines.append(f"- Multi-listing hosts: **{multi}** ({multi/(single+multi)*100:.1f}%)")
            report_lines.append(f"- Top 10 hosts control: **{top10_hosts}** listings ({top10_hosts/total*100:.1f}% of supply)")
            report_lines.append(f"  - *Business Interpretation:* {'Commercial operators dominate a significant share of supply.' if top10_hosts/total > 0.05 else 'The market is fragmented with individual hosts.'}")
            report_lines.append("")

            # Host portfolio distribution
            plt.figure(figsize=(10, 5))
            host_counts["listing_count"].clip(upper=20).hist(bins=20, edgecolor="black", alpha=0.7)
            plt.title(f"{city.title()}: Host Portfolio Size Distribution")
            plt.xlabel("Number of Listings per Host")
            plt.ylabel("Number of Hosts")
            plt.savefig(plots_dir / f"{city}_host_portfolio.png")
            plt.close()

        # --- E. AI/ML Sentiment Correlation ---
        report_lines.append("### 5. Sentiment Analysis & Customer Satisfaction Drivers")
        for city in df_listings["city"].unique():
            city_df = df_listings[(df_listings["city"] == city) & (df_listings["average_sentiment_score"].notna())]
            if not city_df.empty:
                report_lines.append(f"#### Sentiment Impact in {city.title()}")
                
                # Correlation
                corr_rating = city_df["average_sentiment_score"].corr(city_df["review_scores_rating"])
                corr_price = city_df["average_sentiment_score"].corr(city_df["price"])
                
                report_lines.append(f"- **Correlation (Sentiment vs. Review Rating):** {corr_rating:.3f}")
                report_lines.append(f"- **Correlation (Sentiment vs. Price):** {corr_price:.3f}")
                
                # Plot Sentiment vs Rating
                plt.figure(figsize=(10, 6))
                sns.regplot(data=city_df, x="average_sentiment_score", y="review_scores_rating", color="purple")
                plt.title(f"{city.title()}: Review Ratings vs Average Review Sentiment")
                plt.xlabel("Average Review Sentiment (-1.0 to 1.0)")
                plt.ylabel("Overall Review Rating (0-5)")
                plt.savefig(plots_dir / f"{city}_sentiment_vs_rating.png")
                plt.close()
            else:
                report_lines.append(f"No review sentiment details available for {city.title()}.\n")

        # Write report file
        with open(output_dir / "analytics_report.md", "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        logger.info(f"Analytics report written to {output_dir / 'analytics_report.md'}")

    except Exception as e:
        logger.error(f"Error in analysis pipeline: {e}")
        raise e
    finally:
        con.close()

if __name__ == "__main__":
    db = GOLD_DATA_DIR / "airbnb_dw.duckdb"
    run_analysis_pipeline(db, GOLD_DATA_DIR)
