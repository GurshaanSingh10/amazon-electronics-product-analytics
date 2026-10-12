# Amazon Electronics Product & Customer Review Analytics

A reproducible data analytics project that investigates product review activity, customer/reviewer engagement, category performance, and rating quality using Python, SQL, and an interactive Streamlit dashboard.

> **Data limitation:** the source is a ratings/reviews dataset. It does not contain order transactions, units sold, revenue, product-page views, add-to-cart events, or conversion events. Therefore, this project does **not** claim to measure sales, revenue, conversion, or causal product impact. Review count is treated only as review activity.

## Business questions

1. How does review activity vary over time, and how does average rating move alongside it?
2. Which categories have the highest review volume, and do they also have high average ratings?
3. Which categories have comparatively high low-rating shares (ratings 1–2)?
4. Which brands and products attract the most review activity, and how reliable are their rating comparisons given sample size?
5. How concentrated is reviewer activity among one-time, occasional, and frequent reviewers?
6. How do missing brand labels affect the interpretation of brand-level analysis?

## Dataset

- Source: Kaggle, [Amazon Electronics dataset](https://www.kaggle.com/datasets/edusanketdk/electronics)
- Local source file: `data/electronics.csv`
- Fields include item ID, user ID, rating, timestamp, category, brand, and other attributes.
- Historical coverage and field quality should be considered when interpreting findings. The current file has about 1.29 million records, 9,560 products, 1.16 million reviewer IDs, and substantial missingness in brand and user/model attributes.
- Follow the Kaggle dataset's current license and attribution requirements when redistributing or publishing the data.

## Project structure

```text
amazon_product_analytics/
├── data/electronics.csv              # source dataset
├── src/analysis_pipeline.py           # cleaning + repeatable KPI generation
├── sql/analysis_queries.sql           # analytical SQL examples (PostgreSQL syntax)
├── dashboard/app.py                  # interactive Streamlit dashboard
├── notebooks/product_review_analytics.ipynb
├── outputs/                           # precomputed metrics/tables for dashboard
├── docs/key_findings.md               # generated descriptive findings
├── requirements.txt
└── README.md
```

## Run it

Python 3.10+ is recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/analysis_pipeline.py
streamlit run dashboard/app.py
```

The pipeline regenerates the summary CSV files in `outputs/`. To use another local file:

```bash
python src/analysis_pipeline.py --input /path/to/your_dataset.csv
```

The dashboard reads the precomputed files under `outputs/`; after changing input data, rerun the pipeline.

## SQL

`sql/analysis_queries.sql` contains PostgreSQL queries for overall KPIs, monthly activity, category and brand scorecards, product rankings with minimum evidence thresholds, reviewer segmentation, and rating-risk investigation. Import the CSV into a table named `electronics_reviews` before running them. Ensure `timestamp` is parsed as a date/timestamp.

## Analytical methods

- Data validation: required-column checks, timestamp/rating parsing, valid 1–5 rating range, exact duplicate removal, missing brand labelling.
- KPIs: review records, unique products/reviewers, average rating, positive rating share, low-rating share.
- Product/category scorecards: review volume, average rating, product coverage, low-rating share.
- Reviewer activity segments: one-time, occasional (2–4), frequent (5+) reviewers.
- Evidence threshold: product rankings can filter to a minimum review count to reduce small-sample noise.

## Limitations

- Ratings/reviews are not equivalent to purchases or sales.
- Reviewer ID uniqueness does not guarantee one ID per real-world customer.
- No session ID is present, so conversion funnels cannot be measured.
- No product price/order line/revenue fields are present, so revenue and profitability cannot be calculated.
- The data is historical; do not frame findings as current marketplace behaviour.
- Category/brand differences are observational and should not be presented as causal.

## Resume description (edit after reviewing the final outputs)

**Amazon Electronics Product & Review Analytics | Python, SQL, Streamlit, Pandas, Plotly**
- Built a reproducible analytics pipeline for 1.29M+ historical product-rating records, validating data quality and generating product, category, monthly-trend, and reviewer-engagement scorecards.
- Developed SQL analyses and an interactive dashboard to compare review volume, rating distributions, low-rating share, and category/brand performance while accounting for missing metadata and small-sample effects.
- Translated descriptive patterns into investigation priorities and documented limitations to avoid conflating review activity with actual sales or revenue.

Only retain metrics and claims that you can reproduce and explain in an interview. Replace generic wording with the strongest actual findings after reviewing `docs/key_findings.md`.
