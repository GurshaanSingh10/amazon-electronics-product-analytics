"""Reproducible analytics pipeline for Amazon Electronics review data.

The dataset contains review/rating records, not transactions. Review counts are not
sales, revenue, conversion, or market share.
"""
from pathlib import Path
import argparse
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "electronics.csv"
OUTPUT = ROOT / "outputs"


def load_and_clean(path: Path):
    """Load data, profile raw quality, then clean required analytical fields."""
    raw = pd.read_csv(path, low_memory=False)
    required = {"item_id", "user_id", "rating", "timestamp", "category", "brand"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Profile the raw data BEFORE dropping/normalising values.
    raw_quality = pd.DataFrame({
        "column": raw.columns,
        "raw_missing_count": [int(raw[c].isna().sum()) for c in raw.columns],
        "raw_missing_pct": [round(float(raw[c].isna().mean() * 100), 2) for c in raw.columns],
        "raw_distinct_values": [int(raw[c].nunique(dropna=True)) for c in raw.columns],
    })
    initial_rows = len(raw)
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], errors="coerce")
    raw["rating"] = pd.to_numeric(raw["rating"], errors="coerce")

    invalid_timestamp = int(raw["timestamp"].isna().sum())
    invalid_rating = int(raw["rating"].isna().sum() + (~raw["rating"].between(1, 5)).sum())
    missing_required = int(raw[["item_id", "user_id", "category"]].isna().any(axis=1).sum())
    # Keep an explicit cleaning audit so the README/dashboard can report decisions.
    clean = raw.dropna(subset=["item_id", "user_id", "rating", "timestamp", "category"]).copy()
    clean = clean[clean["rating"].between(1, 5)].copy()
    before_duplicates = len(clean)
    clean = clean.drop_duplicates().copy()
    duplicates_removed = before_duplicates - len(clean)

    clean["item_id"] = clean["item_id"].astype(str)
    clean["user_id"] = clean["user_id"].astype(str)
    clean["category"] = clean["category"].fillna("Unknown category").astype(str).str.strip()
    clean.loc[clean["category"].eq(""), "category"] = "Unknown category"
    clean["brand"] = clean["brand"].fillna("Unknown brand").astype(str).str.strip()
    clean.loc[clean["brand"].eq(""), "brand"] = "Unknown brand"
    clean["review_year"] = clean["timestamp"].dt.year
    clean["review_month"] = clean["timestamp"].dt.to_period("M").astype(str)
    clean["rating_bucket"] = np.select(
        [clean["rating"] <= 2, clean["rating"] == 3, clean["rating"] >= 4],
        ["Low (1-2)", "Neutral (3)", "Positive (4-5)"], default="Unknown"
    )

    audit = {
        "input_file": str(path),
        "raw_rows": int(initial_rows),
        "rows_after_required_field_and_rating_validation": int(len(raw) - int(
            raw[["item_id", "user_id", "rating", "timestamp", "category"]].isna().any(axis=1).sum()
        )),
        "invalid_timestamp_values": invalid_timestamp,
        "invalid_or_out_of_range_rating_rows_estimate": invalid_rating,
        "rows_before_exact_deduplication": int(before_duplicates),
        "exact_duplicate_rows_removed": int(duplicates_removed),
        "final_rows": int(len(clean)),
        "rows_removed_total": int(initial_rows - len(clean)),
    }
    raw_quality.to_csv(OUTPUT / "data_quality_raw.csv", index=False) if OUTPUT.exists() else None
    clean.attrs["cleaning_audit"] = audit
    clean.attrs["raw_quality"] = raw_quality
    return clean


def build_outputs(df: pd.DataFrame, out_dir: Path = OUTPUT) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_quality = df.attrs.get("raw_quality")
    audit = df.attrs.get("cleaning_audit", {})
    if raw_quality is not None:
        raw_quality.to_csv(out_dir / "data_quality_raw.csv", index=False)
    pd.DataFrame([audit]).to_csv(out_dir / "cleaning_audit.csv", index=False)

    kpis = pd.DataFrame([{
        "review_records": int(len(df)),
        "unique_products": int(df.item_id.nunique()),
        "unique_reviewers": int(df.user_id.nunique()),
        "categories": int(df.category.nunique()),
        "known_brand_reviews": int((df.brand != "Unknown brand").sum()),
        "brand_missing_pct": round(float((df.brand == "Unknown brand").mean() * 100), 2),
        "average_rating": round(float(df.rating.mean()), 3),
        "positive_rating_share_pct": round(float((df.rating >= 4).mean() * 100), 2),
        "low_rating_share_pct": round(float((df.rating <= 2).mean() * 100), 2),
        "first_review_date": str(df.timestamp.min().date()),
        "last_review_date": str(df.timestamp.max().date()),
    }])
    kpis.to_csv(out_dir / "kpis.csv", index=False)

    monthly = df.groupby("review_month", as_index=False).agg(
        review_count=("rating", "size"), average_rating=("rating", "mean"),
        low_rating_share=("rating", lambda s: (s <= 2).mean() * 100),
        unique_reviewers=("user_id", "nunique"), unique_products=("item_id", "nunique")
    )
    monthly["average_rating"] = monthly.average_rating.round(3)
    monthly["low_rating_share"] = monthly.low_rating_share.round(2)
    monthly.to_csv(out_dir / "monthly_trends.csv", index=False)

    # Category-sliced monthly trends enable the category filter to work consistently.
    monthly_cat = df.groupby(["category", "review_month"], as_index=False).agg(
        review_count=("rating", "size"),
        average_rating=("rating", "mean"),
        low_rating_share=("rating", lambda s: (s <= 2).mean() * 100),
        unique_reviewers=("user_id", "nunique"),
        unique_products=("item_id", "nunique"),
    )
    monthly_cat["average_rating"] = monthly_cat.average_rating.round(3)
    monthly_cat["low_rating_share"] = monthly_cat.low_rating_share.round(2)
    monthly_cat.to_csv(out_dir / "monthly_trends_by_category.csv", index=False)

    category = df.groupby("category", as_index=False).agg(
        review_count=("rating", "size"), average_rating=("rating", "mean"),
        unique_products=("item_id", "nunique"), unique_reviewers=("user_id", "nunique"),
        low_rating_share=("rating", lambda s: (s <= 2).mean() * 100),
        positive_rating_share=("rating", lambda s: (s >= 4).mean() * 100)
    )
    category["review_share_pct"] = category.review_count / len(df) * 100
    for c in ["average_rating", "low_rating_share", "positive_rating_share", "review_share_pct"]:
        category[c] = category[c].round(2)
    category.sort_values("review_count", ascending=False).to_csv(out_dir / "category_performance.csv", index=False)

    brand = df.groupby("brand", as_index=False).agg(
        review_count=("rating", "size"), average_rating=("rating", "mean"),
        unique_products=("item_id", "nunique"),
        low_rating_share=("rating", lambda s: (s <= 2).mean() * 100),
        positive_rating_share=("rating", lambda s: (s >= 4).mean() * 100)
    )
    for c in ["average_rating", "low_rating_share", "positive_rating_share"]:
        brand[c] = brand[c].round(2)
    brand.sort_values("review_count", ascending=False).to_csv(out_dir / "brand_performance.csv", index=False)

    product = df.groupby(["item_id", "category", "brand"], as_index=False).agg(
        review_count=("rating", "size"), average_rating=("rating", "mean"),
        low_rating_share=("rating", lambda s: (s <= 2).mean() * 100),
        positive_rating_share=("rating", lambda s: (s >= 4).mean() * 100),
        unique_reviewers=("user_id", "nunique"),
        first_review=("timestamp", "min"), last_review=("timestamp", "max")
    )
    product["average_rating"] = product.average_rating.round(2)
    product["low_rating_share"] = product.low_rating_share.round(2)
    product["positive_rating_share"] = product.positive_rating_share.round(2)
    product.sort_values(["review_count", "average_rating"], ascending=[False, False]).to_csv(
        out_dir / "product_performance.csv", index=False
    )

    user = df.groupby("user_id", as_index=False).agg(
        review_count=("rating", "size"), average_rating=("rating", "mean"),
        distinct_products=("item_id", "nunique"), distinct_categories=("category", "nunique"),
        first_review=("timestamp", "min"), last_review=("timestamp", "max")
    )
    user["reviewer_segment"] = np.select(
        [user.review_count == 1, user.review_count.between(2, 4), user.review_count >= 5],
        ["One-time reviewer", "Occasional reviewer (2-4)", "Frequent reviewer (5+)"],
        default="Unknown"
    )
    user["average_rating"] = user.average_rating.round(2)
    user.to_csv(out_dir / "reviewer_segments.csv", index=False)
    segments = user.groupby("reviewer_segment", as_index=False).agg(
        reviewers=("user_id", "nunique"), total_reviews=("review_count", "sum"),
        avg_reviews_per_reviewer=("review_count", "mean"),
        avg_distinct_products=("distinct_products", "mean")
    )
    segments["reviewer_share_pct"] = segments.reviewers / user.user_id.nunique() * 100
    for c in ["avg_reviews_per_reviewer", "avg_distinct_products", "reviewer_share_pct"]:
        segments[c] = segments[c].round(2)
    segments.to_csv(out_dir / "reviewer_segments_summary.csv", index=False)

    # A reviewer can appear in multiple categories; these are reviewer-category appearances,
    # not unique people across categories. The dashboard labels these as within-selection shares.
    user_cat = df.groupby(["category", "user_id"], as_index=False).agg(
        review_count=("rating", "size")
    )
    user_cat["reviewer_segment"] = np.select(
        [user_cat.review_count == 1, user_cat.review_count.between(2, 4), user_cat.review_count >= 5],
        ["One-time reviewer", "Occasional reviewer (2-4)", "Frequent reviewer (5+)"],
        default="Unknown"
    )
    segments_cat = user_cat.groupby(["category", "reviewer_segment"], as_index=False).agg(
        reviewers=("user_id", "nunique")
    )
    segments_cat.to_csv(out_dir / "reviewer_segments_by_category.csv", index=False)

    rating_dist = df.groupby("rating", as_index=False).size().rename(columns={"size": "review_count"})
    rating_dist["review_share_pct"] = (rating_dist.review_count / len(df) * 100).round(2)
    rating_dist.to_csv(out_dir / "rating_distribution.csv", index=False)
    rating_cat = df.groupby(["category", "rating"], as_index=False).size().rename(columns={"size": "review_count"})
    rating_cat.to_csv(out_dir / "rating_distribution_by_category.csv", index=False)

    quality_clean = pd.DataFrame({
        "column": list(df.columns),
        "cleaned_missing_count": [int(df[c].isna().sum()) for c in df.columns],
        "cleaned_missing_pct": [round(float(df[c].isna().mean() * 100), 2) for c in df.columns],
        "distinct_values": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })
    quality_clean.to_csv(out_dir / "data_quality_cleaned.csv", index=False)

    top_cat = category.sort_values("review_count", ascending=False).iloc[0]
    low_cat = category.sort_values("average_rating").iloc[0]
    top_brand = brand[brand.brand != "Unknown brand"].sort_values("review_count", ascending=False).head(1)
    best_month = monthly.sort_values("review_count", ascending=False).head(1)
    insights = [
        f"Dataset contains {len(df):,} review records across {df.item_id.nunique():,} products and {df.user_id.nunique():,} reviewers.",
        f"Overall mean rating is {df.rating.mean():.2f}/5; {(df.rating >= 4).mean()*100:.1f}% of records have ratings of 4 or 5.",
        f"{top_cat['category']} has the largest review volume ({int(top_cat['review_count']):,}; {top_cat['review_share_pct']:.1f}% of records). This is review activity, not sales share.",
        f"{low_cat['category']} has the lowest average rating ({low_cat['average_rating']:.2f}/5); review volume and low-rating share should also be considered.",
        f"{(df.brand == 'Unknown brand').mean()*100:.1f}% of records have no brand label, limiting brand-level comparisons.",
    ]
    if not top_brand.empty:
        r = top_brand.iloc[0]
        insights.append(f"Among records with a brand label, {r['brand']} has the highest review count ({int(r['review_count']):,}); this does not establish highest sales.")
    if not best_month.empty:
        r = best_month.iloc[0]
        insights.append(f"Highest review-volume month is {r['review_month']} ({int(r['review_count']):,} records); this reflects review activity and historical coverage, not sales seasonality.")
    (out_dir / "key_findings.md").write_text(
        "# Key findings (descriptive, not causal)\n\n" + "\n".join(f"- {x}" for x in insights) + "\n",
        encoding="utf-8"
    )
    return {"rows": len(df), "products": int(df.item_id.nunique()),
            "reviewers": int(df.user_id.nunique()), "categories": int(df.category.nunique())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(f"Loading {args.input} ...")
    df = load_and_clean(args.input)
    result = build_outputs(df, args.output)
    print("Wrote outputs to", args.output)
    print(result)


if __name__ == "__main__":
    main()
