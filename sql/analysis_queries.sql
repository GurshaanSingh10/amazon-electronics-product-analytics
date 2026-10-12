-- Amazon Electronics Product & Customer Review Analytics
-- Load data/electronics.csv into a table named electronics_reviews first.
-- This dataset contains review/rating events, not sales transactions.

-- 1. Data quality and coverage
SELECT COUNT(*) AS review_records,
       COUNT(DISTINCT item_id) AS unique_products,
       COUNT(DISTINCT user_id) AS unique_reviewers,
       MIN(timestamp) AS first_review,
       MAX(timestamp) AS last_review,
       AVG(rating) AS average_rating,
       100.0 * SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) / COUNT(*) AS low_rating_share_pct
FROM electronics_reviews;

-- 2. Monthly review activity and rating quality
SELECT DATE_TRUNC('month', timestamp)::date AS review_month,
       COUNT(*) AS review_count,
       ROUND(AVG(rating)::numeric, 2) AS average_rating,
       ROUND(100.0 * AVG(CASE WHEN rating <= 2 THEN 1.0 ELSE 0.0 END), 2) AS low_rating_share_pct,
       COUNT(DISTINCT user_id) AS unique_reviewers
FROM electronics_reviews
GROUP BY 1 ORDER BY 1;

-- 3. Category scorecard: compare volume and satisfaction together
SELECT category,
       COUNT(*) AS review_count,
       COUNT(DISTINCT item_id) AS products,
       ROUND(AVG(rating)::numeric, 2) AS average_rating,
       ROUND(100.0 * AVG(CASE WHEN rating <= 2 THEN 1.0 ELSE 0.0 END), 2) AS low_rating_share_pct,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS review_share_pct
FROM electronics_reviews
GROUP BY category
ORDER BY review_count DESC;

-- 4. Brand comparison, excluding missing brand labels
SELECT brand, COUNT(*) AS review_count,
       COUNT(DISTINCT item_id) AS products,
       ROUND(AVG(rating)::numeric, 2) AS average_rating,
       ROUND(100.0 * AVG(CASE WHEN rating <= 2 THEN 1.0 ELSE 0.0 END), 2) AS low_rating_share_pct
FROM electronics_reviews
WHERE brand IS NOT NULL AND TRIM(brand) <> ''
GROUP BY brand
HAVING COUNT(*) >= 100
ORDER BY review_count DESC;

-- 5. Product ranking with a minimum evidence threshold (avoid tiny-sample rankings)
SELECT item_id, category, brand, COUNT(*) AS review_count,
       ROUND(AVG(rating)::numeric, 2) AS average_rating,
       ROUND(100.0 * AVG(CASE WHEN rating <= 2 THEN 1.0 ELSE 0.0 END), 2) AS low_rating_share_pct
FROM electronics_reviews
GROUP BY item_id, category, brand
HAVING COUNT(*) >= 50
ORDER BY average_rating DESC, review_count DESC
LIMIT 100;

-- 6. Reviewer engagement segmentation (not cohort retention)
WITH reviewer_activity AS (
  SELECT user_id, COUNT(*) AS review_count,
         COUNT(DISTINCT item_id) AS distinct_products,
         COUNT(DISTINCT category) AS distinct_categories
  FROM electronics_reviews GROUP BY user_id
)
SELECT CASE WHEN review_count = 1 THEN 'One-time reviewer'
            WHEN review_count BETWEEN 2 AND 4 THEN 'Occasional reviewer (2-4)'
            ELSE 'Frequent reviewer (5+)' END AS reviewer_segment,
       COUNT(*) AS reviewers,
       SUM(review_count) AS total_reviews,
       ROUND(AVG(review_count)::numeric, 2) AS avg_reviews_per_reviewer
FROM reviewer_activity
GROUP BY 1 ORDER BY reviewers DESC;

-- 7. Category-rating risk: low average rating + meaningful review volume
SELECT category, COUNT(*) AS review_count,
       ROUND(AVG(rating)::numeric, 2) AS average_rating,
       ROUND(100.0 * AVG(CASE WHEN rating <= 2 THEN 1.0 ELSE 0.0 END), 2) AS low_rating_share_pct
FROM electronics_reviews GROUP BY category
HAVING COUNT(*) >= 1000
ORDER BY average_rating ASC, review_count DESC;
