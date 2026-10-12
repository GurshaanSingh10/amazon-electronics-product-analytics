# Data dictionary

| Field | Meaning | Notes |
|---|---|---|
| `item_id` | Product identifier | Not a product name or SKU description. |
| `user_id` | Reviewer identifier | May be pseudonymous; do not assume a unique real-world person. |
| `rating` | Product rating | Numeric 1–5. |
| `timestamp` | Review timestamp | Parsed as datetime. |
| `category` | Product category | Used for category scorecards. |
| `brand` | Brand label | Substantial missingness; missing values labelled Unknown brand in the pipeline. |
| `model_attr` | Model/attribute field | Meaning and missingness depend on source schema. |
| `user_attr` | User attribute field | Substantial missingness; not required for core analysis. |
| `year` | Year field in source | Recomputed review year from timestamp for consistency. |
| `split` | Source split indicator | Preserved in raw data; not used as a business dimension. |

The pipeline adds `review_year`, `review_month`, and `rating_bucket`.
