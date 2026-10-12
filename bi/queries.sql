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
       weekly_price.price / national.national_price AS regional_index
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

-- name: k6_national_weekly_price
-- K6 (P6): national weekly price of each product key and channel. The weekly
-- variation and its usual range are computed in bi/alerts.py, because SQLite
-- has no standard deviation.
SELECT weekly_price.week_start,
       dim_product.product_group, dim_product.product, dim_product.variety,
       dim_product.quality, dim_channel.channel, weekly_price.normalized_unit,
       AVG(weekly_price.price) AS national_price
FROM weekly_price
JOIN dim_product ON dim_product.product_id = weekly_price.product_id
JOIN dim_channel ON dim_channel.channel_id = weekly_price.channel_id
WHERE weekly_price.flag IS NULL
GROUP BY weekly_price.week_start, weekly_price.product_id, weekly_price.channel_id,
         weekly_price.normalized_unit;
