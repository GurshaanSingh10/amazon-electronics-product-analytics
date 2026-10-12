# Optional Power BI implementation

The included Streamlit dashboard is runnable as-is. If you want to use Power BI instead, import `data/electronics.csv` into Power BI Desktop and build the report from the raw review table. The `power_bi/measures.dax` file includes starter measures.

## Suggested pages

1. **Executive overview:** Review Records, Unique Products, Unique Reviewers, Average Rating, Positive Rating Share, Low Rating Share.
2. **Category performance:** clustered bar for review records by category; scatter plot of review count vs average rating; table including low-rating share and unique products.
3. **Brand & product investigation:** top brands by review activity; product table with minimum 50-review filter; average rating and low-rating share.
4. **Review trends:** monthly review count and average rating, with year/month slicers.
5. **Data quality:** missing brand share, missing attribute fields, date range, duplicate checks.

## Model notes

- Set `timestamp` to Date/Time and `rating` to Whole Number or Decimal Number.
- Add a date table if you need robust time intelligence.
- Consider a product dimension with one row per `item_id` only if category/brand are consistent per item.
- Because the raw file has over 1.2 million rows, use Power BI's import mode on a capable machine, or import the aggregated CSVs from `outputs/` for a lightweight dashboard.
- Do not name review counts as sales, orders, or revenue. The dataset has no transaction or price fields.
