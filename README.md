# Housing Demand Forecasting & Supply Planning (Python)

An end-to-end analytics pipeline built with **pandas, NumPy, matplotlib and statsmodels**:

1. **Cleans** messy real-estate listing data for six Indian cities (28,500 clean listings).
2. **Profiles supply** - inventory size, price level, unit mix and locality concentration by city.
3. **Forecasts demand** - converts transaction records into a monthly series and compares a seasonal-naive baseline, a **Holt-Winters model written from scratch in NumPy**, and **SARIMA**, using a rolling back-test.
4. **Plans supply** - turns the forecast into a 6-month inventory plan (safety stock, target inventory, new-supply requirement) with low / base / high demand scenarios.

## Important: what is real and what is simulated

| Part | Data | Status |
|---|---|---|
| Steps 1-2: cleaning and supply analysis | Listing files for Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata | **Real** |
| Steps 3-5: demand forecast and supply plan | Transaction dates and monthly volumes | **Simulated** (fixed random seed) |

The listing files have **no dates**, so they cannot show how demand changes over time. To demonstrate the forecasting method, step 3 simulates 72 months of transactions (trend + yearly seasonality + random noise). The property attributes (city, locality, BHK, area, price) in that simulated history are sampled from the real cleaned listings.

**The forecast, MAPE and supply-plan numbers below therefore demonstrate the method - they are not findings about the real housing market.** To run the same pipeline on real dated transactions, see [Using your own data](#using-your-own-transaction-data).

Data source: publicly available housing-listing dataset for six Indian cities *(add the link to where you downloaded it)*.

## Pipeline

| Step | Script | What it does | Main outputs |
|---|---|---|---|
| 1 | `src/01_clean_listings.py` | Loads six city files, fixes text prices, unknown-value codes, duplicates, outliers | `data/processed/listings_clean.csv`, `outputs/tables/cleaning_log.csv` |
| 2 | `src/02_supply_analysis.py` | City summary, BHK mix, price bands, locality concentration (top-10 share, HHI) | `outputs/tables/*.csv`, charts 01-02 |
| 3 | `src/03_generate_demo_transactions.py` | Simulates 72 months of dated transactions (**demo data**) | `data/processed/transactions_simulated.csv` |
| 4 | `src/04_demand_forecast.py` | Monthly demand series, seasonality, back-test of 3 models, 6-month forecast | `forecast_next6.csv`, `model_comparison.csv`, charts 03-05 |
| 5 | `src/05_supply_plan.py` | Safety stock, target inventory, new-supply plan, scenarios, city split | `supply_plan_base.csv`, `scenario_summary.csv`, chart 06 |

## Data cleaning (real data)

Issues found while profiling the raw files and how they are handled:

- **Hyderabad prices stored as text** (`"? 69,68,000.00"`, Indian number format, corrupted rupee sign) - parsed to numbers. The parsed values match the separate clean Excel version of the file exactly (0 difference across 2,518 rows).
- **Junk last row** in the Hyderabad file (`Area = "avg"`) - removed.
- **Amenity columns use `9` as an apparent "not available" placeholder** (from 3% of cells in Hyderabad to 99% in Kolkata) - converted to missing rather than treated as "has the amenity". Because the amenity data is so sparse, it is not used in the later analysis.
- **Exact duplicate rows** - removed (for example 794 of 7,719 in Mumbai).
- **Extreme price-per-sqft values** - trimmed to the 1st-99th percentile within each city.
- **Bedroom counts above 5** (rare, suspicious) - excluded.

Rows kept: **28,504 of 32,964 (86%)**. Full step-by-step counts are in `outputs/tables/cleaning_log.csv`.

## Supply profile (real listings snapshot)

| City | Listings | Median price (Rs lakh) | Median price / sqft (Rs) | Resale share | Top-10 locality share |
|---|---|---|---|---|---|
| Mumbai | 6,779 | 95.0 | 10,625 | 63.6% | 42.9% |
| Delhi | 4,006 | 75.0 | 7,001 | 78.6% | 43.1% |
| Bangalore | 5,405 | 72.9 | 5,346 | 7.1% | 25.5% |
| Hyderabad | 1,955 | 78.5 | 5,112 | 26.0% | 38.9% |
| Chennai | 4,219 | 58.5 | 5,419 | 9.9% | 30.1% |
| Kolkata | 6,140 | 49.2 | 4,324 | 31.6% | 50.1% |

Observations:
- Mumbai's inventory is small-unit heavy: 1 BHK is 35.5% of listings, versus under 8% in every other city.
- Bangalore's supply is the most spread out (top-10 localities hold 25.5%); Kolkata's is the most concentrated (50.1%).
- Kolkata has the most affordable inventory: 51.5% of listings are under Rs 50 lakh.
- Resale dominates in Delhi (78.6%); new-launch supply dominates in Bangalore and Chennai.

![Inventory mix by BHK](outputs/charts/01_inventory_mix_by_bhk.png)
![Price per sqft by city](outputs/charts/02_price_per_sqft_by_city.png)

## Demand forecasting (simulated demo data)

The transaction records are aggregated into a monthly series (`resample("MS").size()`), then three models are compared with an **expanding-window back-test**: train on the first n-18 months and forecast 6, then n-12, then n-6, giving 18 forecast errors per model.

| Model | MAPE | MAE | RMSE |
|---|---|---|---|
| **Holt-Winters (additive, NumPy)** | **11.4%** | 8.9 | 11.7 |
| Seasonal naive (same month last year) | 12.9% | 10.9 | 15.3 |
| SARIMA (1,1,1)(0,1,1,12) | 18.6% | 14.2 | 17.1 |

Holt-Winters wins and is then refitted on all 72 months to forecast January-June 2025. Because monthly sales here are random counts (about 70 per month), a MAPE of roughly 11% is close to the noise floor - no model could do much better on this series.

![Trend and seasonality](outputs/charts/03_demand_trend_and_seasonality.png)
![Forecast](outputs/charts/05_demand_forecast_next_6_months.png)

## Supply planning (simulated demo data)

Business logic (S&OP-style inventory planning):

```
safety stock       = z x forecast error (RMSE) x sqrt(lead time)
target inventory   = cover months x forecast demand + safety stock
planned new supply = max(0, target inventory - (opening inventory - demand))
closing inventory  = opening inventory + planned new supply - demand
```

Assumptions (editable at the top of `05_supply_plan.py`): 2-month lead time, 95% service level (z = 1.645), 2 months of demand cover, opening inventory of 2.5 months of recent demand.

| Scenario | 6-month demand | New supply needed | Closing inventory (month 6) |
|---|---|---|---|
| Low demand (lower 90%) | 340 | 258 | 142 |
| **Base forecast** | **455** | **412** | **181** |
| High demand (upper 90%) | 570 | 566 | 219 |

The plan is also split by city using each city's share of the last 12 months of sales (`outputs/tables/supply_plan_by_city.csv`).

![Supply plan](outputs/charts/06_supply_plan.png)

## How to run

```bash
git clone <your-repo-url>
cd housing-demand-supply-planning
pip install -r requirements.txt
python run_all.py
```

Outputs appear in `outputs/tables/` and `outputs/charts/`. Each script can also be run on its own, in order.

## Using your own transaction data

If you have real dated transaction records (one row per sale, at least 36 months, ideally 5+ years):

```bash
python src/04_demand_forecast.py --input path/to/transactions.csv --date-col sale_date
python src/05_supply_plan.py     --input path/to/transactions.csv --date-col sale_date
```

Make sure the last month in the file is complete. If the file has a `city` column, the plan is also split by city. Replace the opening-inventory assumption in `05_supply_plan.py` with your actual stock.

## Limitations

- Steps 3-5 use simulated demand, so their numbers are illustrative.
- The listing snapshot shows supply only; without dates or sales volumes it cannot measure demand.
- Holt-Winters and SARIMA use fixed settings and a small parameter grid, not an exhaustive search.
- The supply plan uses simple assumptions (constant lead time and service level) and one aggregate inventory pool.
- Dropping exact duplicate rows may remove genuinely identical units in the same project.

## Tech stack

Python 3.9+, pandas, NumPy, matplotlib, statsmodels. See [`docs/CODE_WALKTHROUGH.md`](docs/CODE_WALKTHROUGH.md) for a line-by-line explanation of the code.
