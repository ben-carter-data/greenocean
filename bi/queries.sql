-- One named query per indicator of docs/DISENO.md, section 7.
-- Every query leaves out flagged prices: not convertible units (RN-05) and
-- outliers (RN-12). K7 lives in etl/etl.py because every ETL run prints it.

-- name: k1_margin
-- K1 (P1): margin between the wholesale price and each consumer channel.
-- RN-06: both prices must share week, region, product key and unit.
SELECT consumer.week_start,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, dim_region.region, consumer_channel.channel,
       consumer.normalized_unit,
       wholesale.price AS wholesale_price,
       consumer.price AS consumer_price,
       (consumer.price - wholesale.price) / wholesale.price AS margin
FROM weekly_price AS consumer
JOIN dim_channel AS consumer_channel
  ON consumer_channel.channel_id = consumer.channel_id
 AND consumer_channel.source = 'consumer'
JOIN weekly_price AS wholesale
  ON wholesale.week_start = consumer.week_start
 AND wholesale.product_id = consumer.product_id
 AND wholesale.region_id = consumer.region_id
 AND wholesale.normalized_unit = consumer.normalized_unit
JOIN dim_channel AS wholesale_channel
  ON wholesale_channel.channel_id = wholesale.channel_id
 AND wholesale_channel.source = 'wholesale'
JOIN dim_product ON dim_product.product_id = consumer.product_id
JOIN dim_region ON dim_region.region_id = consumer.region_id
WHERE consumer.flag IS NULL AND wholesale.flag IS NULL;

-- name: k2_channel_gap
-- K2 (P2): price of one consumer channel against another, same week, region,
-- product key and unit. gap = P_channel / P_reference_channel - 1.
SELECT price.week_start,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, dim_region.region, price.normalized_unit,
       channel.channel, reference_channel.channel AS reference_channel,
       price.price, reference.price AS reference_price,
       price.price / reference.price - 1 AS gap
FROM weekly_price AS price
JOIN dim_channel AS channel
  ON channel.channel_id = price.channel_id AND channel.source = 'consumer'
JOIN weekly_price AS reference
  ON reference.week_start = price.week_start
 AND reference.product_id = price.product_id
 AND reference.region_id = price.region_id
 AND reference.normalized_unit = price.normalized_unit
 AND reference.channel_id <> price.channel_id
JOIN dim_channel AS reference_channel
  ON reference_channel.channel_id = reference.channel_id
 AND reference_channel.source = 'consumer'
JOIN dim_product ON dim_product.product_id = price.product_id
JOIN dim_region ON dim_region.region_id = price.region_id
WHERE price.flag IS NULL AND reference.flag IS NULL;

-- name: k3_regional_index
-- K3 (P3): price of a region over the national price, where the national
-- price is the plain average of the regions with data that week.
WITH national AS (
    SELECT week_start, product_id, channel_id, normalized_unit,
           AVG(price) AS national_price
    FROM weekly_price
    WHERE flag IS NULL
    GROUP BY week_start, product_id, channel_id, normalized_unit
)
SELECT weekly_price.week_start,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, dim_channel.channel, dim_region.region,
       weekly_price.normalized_unit, weekly_price.price, national.national_price,
       weekly_price.price / national.national_price AS regional_index,
       weekly_price.observation_count
FROM weekly_price
JOIN national
  ON national.week_start = weekly_price.week_start
 AND national.product_id = weekly_price.product_id
 AND national.channel_id = weekly_price.channel_id
 AND national.normalized_unit = weekly_price.normalized_unit
JOIN dim_product ON dim_product.product_id = weekly_price.product_id
JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
JOIN dim_region ON dim_region.region_id = weekly_price.region_id
WHERE weekly_price.flag IS NULL;

-- name: k4_seasonal_index
-- K4 (P4): national price of a week over the average of its year.
-- The year is the one of the Thursday of the week (ISO rule), so the week
-- that starts on 2025-12-29 belongs to 2026, like in the consumer source.
WITH national AS (
    SELECT week_start, product_id, channel_id, normalized_unit,
           strftime('%Y', week_start, '+3 days') AS price_year,
           AVG(price) AS national_price
    FROM weekly_price
    WHERE flag IS NULL
    GROUP BY week_start, product_id, channel_id, normalized_unit
),
yearly AS (
    SELECT product_id, channel_id, normalized_unit, price_year,
           AVG(national_price) AS yearly_price, COUNT(*) AS week_count
    FROM national
    GROUP BY product_id, channel_id, normalized_unit, price_year
)
SELECT national.week_start, national.price_year,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, dim_channel.channel, national.normalized_unit,
       national.national_price, yearly.yearly_price, yearly.week_count,
       national.national_price / yearly.yearly_price AS seasonal_index
FROM national
JOIN yearly
  ON yearly.product_id = national.product_id
 AND yearly.channel_id = national.channel_id
 AND yearly.normalized_unit = national.normalized_unit
 AND yearly.price_year = national.price_year
JOIN dim_product ON dim_product.product_id = national.product_id
JOIN dim_channel ON dim_channel.channel_id = national.channel_id;

-- name: k8_rejected_rows
-- K8: rows rejected in the latest run, by source and reason, over rows read.
SELECT rejection.source, rejection.reason,
       COUNT(*) AS rejected_rows,
       COUNT(*) * 1.0 / etl_run.rows_read AS rejected_share
FROM rejection
JOIN etl_run ON etl_run.run_id = rejection.run_id
GROUP BY rejection.source, rejection.reason, etl_run.rows_read;

-- name: quality_runs
-- Latest runs of the ETL, newest first.
SELECT run_id, started_at, status, rows_read, rows_loaded, rows_rejected, message
FROM etl_run
ORDER BY run_id DESC
LIMIT 10;

-- name: quality_flag_counts
-- Weekly prices by source and flag (no flag, not convertible unit, outlier).
SELECT dim_channel.source, COALESCE(weekly_price.flag, 'SIN_MARCA') AS flag,
       COUNT(*) AS weekly_prices
FROM weekly_price
JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
GROUP BY dim_channel.source, COALESCE(weekly_price.flag, 'SIN_MARCA');

-- name: quality_outliers
-- RN-12: the weekly prices flagged as outliers, kept but out of the indicators.
SELECT weekly_price.week_start, dim_channel.source, dim_channel.channel,
       dim_region.region, dim_product.product, dim_product.variety,
       dim_product.quality, weekly_price.normalized_unit, weekly_price.price,
       weekly_price.observation_count
FROM weekly_price
JOIN dim_product ON dim_product.product_id = weekly_price.product_id
JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
JOIN dim_region ON dim_region.region_id = weekly_price.region_id
WHERE weekly_price.flag = 'ATIPICO'
ORDER BY weekly_price.week_start DESC, dim_product.product;

-- name: quality_rejected_rows
-- RN-11: the rows rejected in the latest run, as they were read, with their reason.
SELECT source, reason, original_row
FROM rejection
ORDER BY source, reason;

-- name: quality_unconvertible_units
-- RN-05: weekly prices kept without a comparable price, by product and channel.
SELECT dim_channel.source, dim_channel.channel, dim_product.product,
       dim_product.variety, dim_product.quality, COUNT(*) AS weekly_prices
FROM weekly_price
JOIN dim_product ON dim_product.product_id = weekly_price.product_id
JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
WHERE weekly_price.flag = 'UNIDAD_NO_CONVERTIBLE'
GROUP BY dim_channel.source, dim_channel.channel, dim_product.product,
         dim_product.variety, dim_product.quality
ORDER BY weekly_prices DESC, dim_product.product;

-- name: k6_national_weekly_price
-- K6 (P6): national weekly price of each product key and channel. The weekly
-- variation and its usual range are computed in bi/alerts.py, because SQLite
-- has no standard deviation. D-144: the change against the week before uses only
-- the regions with a price in both weeks (same_region_*), so a region that starts
-- or stops reporting does not look like a price movement.
WITH same_regions AS (
    SELECT now.week_start, now.product_id, now.channel_id, now.normalized_unit,
           AVG(now.price) AS same_region_price, AVG(before.price) AS same_region_previous_price
    FROM weekly_price AS now
    JOIN weekly_price AS before
      ON before.product_id = now.product_id AND before.channel_id = now.channel_id
     AND before.normalized_unit = now.normalized_unit AND before.region_id = now.region_id
     AND before.week_start = date(now.week_start, '-7 days')
    WHERE now.flag IS NULL AND before.flag IS NULL
    GROUP BY now.week_start, now.product_id, now.channel_id, now.normalized_unit
)
SELECT weekly_price.week_start,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, dim_channel.channel, weekly_price.normalized_unit,
       AVG(weekly_price.price) AS national_price,
       same_regions.same_region_price, same_regions.same_region_previous_price
FROM weekly_price
JOIN dim_product ON dim_product.product_id = weekly_price.product_id
JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
LEFT JOIN same_regions
  ON same_regions.week_start = weekly_price.week_start
 AND same_regions.product_id = weekly_price.product_id
 AND same_regions.channel_id = weekly_price.channel_id
 AND same_regions.normalized_unit = weekly_price.normalized_unit
WHERE weekly_price.flag IS NULL
GROUP BY weekly_price.week_start, weekly_price.product_id, weekly_price.channel_id,
         weekly_price.normalized_unit;

-- name: k6_usual_range_sql
-- K6 (P6) in SQL, the alternative to bi/alerts.py (the version the dashboard
-- uses); a test checks that both give the same result (D-049). For each week:
-- the variation against the week before, and the average and the sample
-- variance of the 12 variations before it, with window functions.
-- SQLite has no standard deviation and SQRT is optional, so the rule
-- |variation - average| > 2 * deviation is written with squares:
-- (variation - average)^2 > 4 * variance.
WITH national AS (
    SELECT weekly_price.week_start, weekly_price.product_id, weekly_price.channel_id,
           weekly_price.normalized_unit, AVG(weekly_price.price) AS national_price
    FROM weekly_price
    WHERE weekly_price.flag IS NULL
    GROUP BY weekly_price.week_start, weekly_price.product_id, weekly_price.channel_id,
             weekly_price.normalized_unit
),
-- D-144: the weekly change over the regions with a price in both weeks; a week
-- without the one before has no such region, so a gap never yields a change.
same_regions AS (
    SELECT now.week_start, now.product_id, now.channel_id, now.normalized_unit,
           AVG(now.price) / AVG(before.price) - 1 AS variation
    FROM weekly_price AS now
    JOIN weekly_price AS before
      ON before.product_id = now.product_id AND before.channel_id = now.channel_id
     AND before.normalized_unit = now.normalized_unit AND before.region_id = now.region_id
     AND before.week_start = date(now.week_start, '-7 days')
    WHERE now.flag IS NULL AND before.flag IS NULL
    GROUP BY now.week_start, now.product_id, now.channel_id, now.normalized_unit
),
variations AS (
    SELECT national.*, same_regions.variation
    FROM national
    LEFT JOIN same_regions USING (week_start, product_id, channel_id, normalized_unit)
),
usual AS (
    SELECT variations.*,
           COUNT(variation) OVER previous_weeks AS previous_count,
           AVG(variation) OVER previous_weeks AS usual_variation,
           AVG(variation * variation) OVER previous_weeks AS usual_square
    FROM variations
    WINDOW previous_weeks AS (PARTITION BY product_id, channel_id, normalized_unit
                              ORDER BY week_start
                              ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING)
)
SELECT usual.week_start,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, dim_channel.channel, usual.normalized_unit,
       usual.national_price, usual.variation, usual.usual_variation,
       -- Sample variance (divided by n - 1 = 11), the same definition as pandas.
       (usual.usual_square - usual.usual_variation * usual.usual_variation) * 12.0 / 11
           AS variation_variance,
       -- D-146: unusual (2 deviations) and material (a change of at least 10 %).
       CASE WHEN (usual.variation - usual.usual_variation)
                 * (usual.variation - usual.usual_variation)
                 > 4 * (usual.usual_square - usual.usual_variation * usual.usual_variation)
                       * 12.0 / 11
             AND ABS(usual.variation) >= 0.10
            THEN 1 ELSE 0
       END AS is_alert
FROM usual
JOIN dim_product ON dim_product.product_id = usual.product_id
JOIN dim_channel ON dim_channel.channel_id = usual.channel_id
-- A week is judged only with its own variation and 12 previous ones.
WHERE usual.previous_count = 12 AND usual.variation IS NOT NULL;

-- name: k5_weekly_variations_sql
-- K5 (P5) in SQL, first half: the weekly changes of both prices, with LAG(),
-- for the series with at least 26 weeks with both prices (HAVING). The
-- correlation for each lag stays in bi/lag.py (D-049). A series is one product
-- key, unit, region and consumer channel with the pairs of k1_margin (D-048).
WITH pairs AS (
    SELECT consumer.week_start, consumer.product_id, consumer.region_id,
           consumer.channel_id, consumer.normalized_unit,
           wholesale.price AS wholesale_price, consumer.price AS consumer_price
    FROM weekly_price AS consumer
    JOIN dim_channel AS consumer_channel
      ON consumer_channel.channel_id = consumer.channel_id
     AND consumer_channel.source = 'consumer'
    JOIN weekly_price AS wholesale
      ON wholesale.week_start = consumer.week_start
     AND wholesale.product_id = consumer.product_id
     AND wholesale.region_id = consumer.region_id
     AND wholesale.normalized_unit = consumer.normalized_unit
    JOIN dim_channel AS wholesale_channel
      ON wholesale_channel.channel_id = wholesale.channel_id
     AND wholesale_channel.source = 'wholesale'
    WHERE consumer.flag IS NULL AND wholesale.flag IS NULL
),
long_series AS (
    SELECT product_id, region_id, channel_id, normalized_unit
    FROM pairs
    GROUP BY product_id, region_id, channel_id, normalized_unit
    HAVING COUNT(*) >= 26
),
ordered AS (
    SELECT pairs.*,
           julianday(pairs.week_start) - julianday(LAG(pairs.week_start) OVER series)
               AS days_since_previous_week,
           LAG(pairs.wholesale_price) OVER series AS previous_wholesale_price,
           LAG(pairs.consumer_price) OVER series AS previous_consumer_price
    FROM pairs
    JOIN long_series USING (product_id, region_id, channel_id, normalized_unit)
    WINDOW series AS (PARTITION BY pairs.product_id, pairs.region_id, pairs.channel_id,
                                   pairs.normalized_unit
                      ORDER BY pairs.week_start)
)
SELECT ordered.week_start,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, ordered.normalized_unit, dim_region.region,
       dim_channel.channel,
       CASE WHEN ordered.days_since_previous_week = 7
            THEN ordered.wholesale_price / ordered.previous_wholesale_price - 1
       END AS wholesale_variation,
       CASE WHEN ordered.days_since_previous_week = 7
            THEN ordered.consumer_price / ordered.previous_consumer_price - 1
       END AS consumer_variation
FROM ordered
JOIN dim_product ON dim_product.product_id = ordered.product_id
JOIN dim_region ON dim_region.region_id = ordered.region_id
JOIN dim_channel ON dim_channel.channel_id = ordered.channel_id;

-- name: quality_week_range
-- First and last week loaded in the data warehouse, and their years (ISO rule,
-- as K4): what the dashboard says about the years it covers.
SELECT MIN(week_start) AS first_week, MAX(week_start) AS last_week,
       strftime('%Y', MIN(week_start), '+3 days') AS first_year,
       strftime('%Y', MAX(week_start), '+3 days') AS last_year
FROM weekly_price;
