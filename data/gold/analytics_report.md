# Expernetic Airbnb Analytics Report
## Business Intelligence and Statistical Insights


### 1. Market Overview & Summary Statistics
#### City: Amsterdam
- **Total Listings Analyzed:** 5874
- **Average Listing Price:** $336.79
- **Median Listing Price:** $222.00
- **Average Rating:** 4.84/5.0
- **Average Sentiment Score:** 0.627

*Room Type Breakdown:*
  - **Entire Home/Apt:** 4532 listings, avg price: $336.18
  - **Hotel Room:** 38 listings, avg price: $5971.24
  - **Private Room:** 1274 listings, avg price: $175.73
  - **Shared Room:** 30 listings, avg price: $130.27


#### City: Venice
- **Total Listings Analyzed:** 7702
- **Average Listing Price:** $241.02
- **Median Listing Price:** $158.00
- **Average Rating:** 4.75/5.0
- **Average Sentiment Score:** 0.465

*Room Type Breakdown:*
  - **Entire Home/Apt:** 6147 listings, avg price: $263.69
  - **Hotel Room:** 45 listings, avg price: $163.13
  - **Private Room:** 1496 listings, avg price: $151.44
  - **Shared Room:** 14 listings, avg price: $107.86


### 2. Geographic Pricing Gradients & Infrastructure Impact
#### Proximity Premium in Amsterdam
- **<1km (Ultra-Core):** 836 listings (14.2%), avg price: $313.89 (median: $240.50)
- **1-2.5km (Core):** 2490 listings (42.4%), avg price: $286.17 (median: $234.00)
- **2.5-5km (Urban Ring):** 2182 listings (37.1%), avg price: $423.02 (median: $212.00)
- **5km+ (Peripheral):** 366 listings (6.2%), avg price: $219.29 (median: $153.00)
- **Correlation (Price vs. Distance):** 0.023
  - *Business Interpretation:* Weak or positive correlation. Proximity to configured landmarks has little direct linear impact on price, possibly due to suburban luxury listings or other local factors.

#### Proximity Premium in Venice
- **<1km (Ultra-Core):** 4045 listings (52.5%), avg price: $295.96 (median: $189.00)
- **1-2.5km (Core):** 1633 listings (21.2%), avg price: $231.29 (median: $160.00)
- **2.5-5km (Urban Ring):** 308 listings (4.0%), avg price: $193.56 (median: $150.00)
- **5km+ (Peripheral):** 1716 listings (22.3%), avg price: $129.28 (median: $89.00)
- **Correlation (Price vs. Distance):** -0.108
  - *Business Interpretation:* Mild negative correlation. Listings closer to central infrastructure show a slight price premium.

### 3. Temporal Seasonality & Occupancy Patterns
#### Seasonality in Amsterdam
*Monthly In-Season Pricing and Occupancy Peaks:*
  - **Month 1:** Avg Price: $304.26, Est. Occupancy: 100.0%
  - **Month 2:** Avg Price: $306.56, Est. Occupancy: 100.0%
  - **Month 3:** Avg Price: $303.84, Est. Occupancy: 100.0%
  - **Month 4:** Avg Price: $298.68, Est. Occupancy: 100.0%
  - **Month 5:** Avg Price: $303.20, Est. Occupancy: 100.0%
  - **Month 6:** Avg Price: $299.15, Est. Occupancy: 100.0%
  - **Month 7:** Avg Price: $296.92, Est. Occupancy: 100.0%
  - **Month 8:** Avg Price: $297.33, Est. Occupancy: 100.0%
  - **Month 9:** Avg Price: $299.01, Est. Occupancy: 100.0%
  - **Month 10:** Avg Price: $275.15, Est. Occupancy: 100.0%
  - **Month 11:** Avg Price: $256.84, Est. Occupancy: 100.0%
  - **Month 12:** Avg Price: $253.92, Est. Occupancy: 100.0%

*Day-of-Week (Weekend Premium) Analysis:*
  - **Day 0:** Avg Price: $290.43, Est. Occupancy: 100.0%
  - **Day 1:** Avg Price: $290.28, Est. Occupancy: 100.0%
  - **Day 2:** Avg Price: $292.66, Est. Occupancy: 100.0%
  - **Day 3:** Avg Price: $292.32, Est. Occupancy: 100.0%
  - **Day 4:** Avg Price: $291.08, Est. Occupancy: 100.0%
  - **Day 5:** Avg Price: $290.79, Est. Occupancy: 100.0%
  - **Day 6:** Avg Price: $291.37, Est. Occupancy: 100.0%


#### Seasonality in Venice
*Monthly In-Season Pricing and Occupancy Peaks:*
  - **Month 1:** Avg Price: $228.80, Est. Occupancy: 100.0%
  - **Month 2:** Avg Price: $230.71, Est. Occupancy: 100.0%
  - **Month 3:** Avg Price: $231.42, Est. Occupancy: 100.0%
  - **Month 4:** Avg Price: $228.90, Est. Occupancy: 100.0%
  - **Month 5:** Avg Price: $246.45, Est. Occupancy: 100.0%
  - **Month 6:** Avg Price: $222.67, Est. Occupancy: 100.0%
  - **Month 7:** Avg Price: $216.83, Est. Occupancy: 100.0%
  - **Month 8:** Avg Price: $217.96, Est. Occupancy: 100.0%
  - **Month 9:** Avg Price: $219.86, Est. Occupancy: 100.0%
  - **Month 10:** Avg Price: $227.68, Est. Occupancy: 100.0%
  - **Month 11:** Avg Price: $241.60, Est. Occupancy: 100.0%
  - **Month 12:** Avg Price: $229.17, Est. Occupancy: 100.0%

*Day-of-Week (Weekend Premium) Analysis:*
  - **Day 0:** Avg Price: $227.47, Est. Occupancy: 100.0%
  - **Day 1:** Avg Price: $226.90, Est. Occupancy: 100.0%
  - **Day 2:** Avg Price: $226.63, Est. Occupancy: 100.0%
  - **Day 3:** Avg Price: $226.73, Est. Occupancy: 100.0%
  - **Day 4:** Avg Price: $227.34, Est. Occupancy: 100.0%
  - **Day 5:** Avg Price: $228.18, Est. Occupancy: 100.0%
  - **Day 6:** Avg Price: $227.37, Est. Occupancy: 100.0%


### 4. Inferential Statistical Hypothesis Testing
#### Neighborhood Price Variance (ANOVA) - Amsterdam
- **F-Statistic:** 10.3805
- **p-value:** 5.258e-34
  - *Interpretation:* Reject Null Hypothesis (H0). The price differences across neighborhoods in Amsterdam are statistically highly significant. Neighborhood location is a strong driver of listing prices.
- **Pairwise Contrast (De Baarsjes - Oud-West vs. Centrum-West):**
  - **De Baarsjes - Oud-West mean price:** $271.28 (n=992)
  - **Centrum-West mean price:** $315.88 (n=770)
  - **Cohen's d Effect Size:** -0.1467
  - *Business Interpretation:* Negligible effect. This indicates that the average difference in pricing between these two top districts is 0.1 standard deviations, which represents a moderate pricing gap for operators targeting these submarkets.


#### Neighborhood Price Variance (ANOVA) - Venice
- **F-Statistic:** 4.3919
- **p-value:** 2.989e-18
  - *Interpretation:* Reject Null Hypothesis (H0). The price differences across neighborhoods in Venice are statistically highly significant. Neighborhood location is a strong driver of listing prices.
- **Pairwise Contrast (Cannaregio vs. Castello):**
  - **Cannaregio mean price:** $261.98 (n=1476)
  - **Castello mean price:** $248.16 (n=1380)
  - **Cohen's d Effect Size:** 0.0217
  - *Business Interpretation:* Negligible effect. This indicates that the average difference in pricing between these two top districts is 0.0 standard deviations, which represents a moderate pricing gap for operators targeting these submarkets.


### 4b. Additional Hypothesis Tests
#### City: Amsterdam
**H1: Entire-home listings command higher prices than private rooms.**
- Test: Welch's t-test (unequal variances assumed)
- Entire Home mean: $336.18 (n=4532), Private Room mean: $175.73 (n=1274)
- t-statistic: 5.9062, p-value: 3.712e-09
- Cohen's d: 0.1298
  - *Interpretation:* Reject H0. Entire-home listings are priced significantly higher than private rooms in Amsterdam. This confirms the structural premium that whole-unit rentals command, driven by higher capacity, privacy, and amenity access.

**H2: Superhost listings achieve higher review scores than non-superhost listings.**
- Test: Welch's t-test
- Superhost mean rating: 4.865 (n=1459), Non-superhost mean: 4.825 (n=3759)
- t-statistic: 6.4799, p-value: 1.008e-10
- Cohen's d: 0.1718
  - *Interpretation:* Reject H0. Superhosts in Amsterdam achieve statistically higher review ratings. The Superhost badge serves as a credible quality signal for guests and correlates with measurably better guest experiences.

**H3: Listings with >10 reviews have different prices than those with fewer.**
- Test: Welch's t-test
- >10 reviews mean price: $257.32 (n=3054), ≤10 reviews mean: $422.84 (n=2820)
- t-statistic: -3.0726, p-value: 0.002142
  - *Interpretation:* Reject H0. Review volume is associated with a statistically significant price difference in Amsterdam, suggesting that established listings with booking history can sustain different pricing strategies.

#### City: Venice
**H1: Entire-home listings command higher prices than private rooms.**
- Test: Welch's t-test (unequal variances assumed)
- Entire Home mean: $263.69 (n=6147), Private Room mean: $151.44 (n=1496)
- t-statistic: 9.6399, p-value: 8.76e-22
- Cohen's d: 0.2237
  - *Interpretation:* Reject H0. Entire-home listings are priced significantly higher than private rooms in Venice. This confirms the structural premium that whole-unit rentals command, driven by higher capacity, privacy, and amenity access.

**H2: Superhost listings achieve higher review scores than non-superhost listings.**
- Test: Welch's t-test
- Superhost mean rating: 4.870 (n=3266), Non-superhost mean: 4.640 (n=3838)
- t-statistic: 35.1751, p-value: 9.651e-242
- Cohen's d: 0.8104
  - *Interpretation:* Reject H0. Superhosts in Venice achieve statistically higher review ratings. The Superhost badge serves as a credible quality signal for guests and correlates with measurably better guest experiences.

**H3: Listings with >10 reviews have different prices than those with fewer.**
- Test: Welch's t-test
- >10 reviews mean price: $200.41 (n=5635), ≤10 reviews mean: $351.71 (n=2067)
- t-statistic: -6.7021, p-value: 2.604e-11
  - *Interpretation:* Reject H0. Review volume is associated with a statistically significant price difference in Venice, suggesting that established listings with booking history can sustain different pricing strategies.

#### Weekend vs. Weekday Pricing (H5)
**Amsterdam:**
- Weekend mean price: $290.90 (n=354,316), Weekday mean: $291.42 (n=885,017)
- t-statistic: -0.1499, p-value: 0.8808
  - *Interpretation:* Fail to reject H0 at 95% confidence. In this dataset the weekend premium is not statistically detectable, likely because the calendar prices use the listing base price as a fallback.

**Venice:**
- Weekend mean price: $227.42 (n=308,568), Weekday mean: $227.17 (n=755,077)
- t-statistic: 0.2261, p-value: 0.8212
  - *Interpretation:* Fail to reject H0 at 95% confidence. In this dataset the weekend premium is not statistically detectable, likely because the calendar prices use the listing base price as a fallback.



### 4c. Correlation Analysis
**Strongest drivers of listing price (Pearson correlation):**
- bathrooms: **0.078**
- bedrooms: **0.074**
- accommodates: **0.070**
- beds: **0.053**
- number_of_reviews: **-0.039**
- review_scores_rating: **-0.037**
- distance_to_nearest_landmark_km: **-0.026**
- average_sentiment_score: **0.014**



### 4d. Host Portfolio & Supply Concentration
#### Amsterdam
- Single-listing hosts: **4657** (92.3%)
- Multi-listing hosts: **388** (7.7%)
- Top 10 hosts control: **161** listings (2.7% of supply)
  - *Business Interpretation:* The market is fragmented with individual hosts.

#### Venice
- Single-listing hosts: **2286** (65.6%)
- Multi-listing hosts: **1200** (34.4%)
- Top 10 hosts control: **673** listings (8.7% of supply)
  - *Business Interpretation:* Commercial operators dominate a significant share of supply.

### 5. Sentiment Analysis & Customer Satisfaction Drivers
#### Sentiment Impact in Amsterdam
- **Correlation (Sentiment vs. Review Rating):** 0.343
- **Correlation (Sentiment vs. Price):** -0.017
#### Sentiment Impact in Venice
- **Correlation (Sentiment vs. Review Rating):** 0.393
- **Correlation (Sentiment vs. Price):** 0.064