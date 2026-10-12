-- Indicator database (datos.db): weekly prices, small enough to commit.
-- The raw tables live in raw_schema.sql and raw.db, outside the repository.

CREATE TABLE IF NOT EXISTS dim_product (
    product_id INTEGER PRIMARY KEY,
    product_group TEXT NOT NULL,
    product TEXT NOT NULL,
    variety TEXT NOT NULL,
    quality TEXT NOT NULL,
    UNIQUE (product_group, product, variety, quality)
);

CREATE TABLE IF NOT EXISTS dim_region (
    region_id INTEGER PRIMARY KEY,
    region TEXT NOT NULL
);

-- The wholesale source is one more channel, so a margin is a comparison
-- between two channels of the same table.
CREATE TABLE IF NOT EXISTS dim_channel (
    channel_id INTEGER PRIMARY KEY,
    channel TEXT NOT NULL,
    source TEXT NOT NULL,
    UNIQUE (channel, source)
);

CREATE TABLE IF NOT EXISTS weekly_price (
    week_start TEXT NOT NULL,                -- Monday of the week (RN-08)
    product_id INTEGER NOT NULL REFERENCES dim_product (product_id),
    region_id INTEGER NOT NULL REFERENCES dim_region (region_id),
    channel_id INTEGER NOT NULL REFERENCES dim_channel (channel_id),
    normalized_unit TEXT,                    -- 'kilo', 'unidad', 'litro' or NULL (RN-05)
    price REAL,                              -- NULL when the unit is not convertible
    volume REAL,                             -- wholesale only
    observation_count INTEGER NOT NULL,      -- source rows behind this price
    flag TEXT                                -- NULL, 'UNIDAD_NO_CONVERTIBLE' or 'ATIPICO'
);

-- D-046: no unique index on the weekly price key. It took 40 % of the file
-- and no query got faster with it. One row per key is guaranteed by the ETL,
-- which rebuilds this table grouping by the key and stops if it finds a duplicate.
-- The DROP removes the index from databases created before this decision.
DROP INDEX IF EXISTS ux_weekly_price_key;

CREATE TABLE IF NOT EXISTS etl_run (
    run_id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    status TEXT NOT NULL,
    rows_read INTEGER NOT NULL,
    rows_loaded INTEGER NOT NULL,
    rows_rejected INTEGER NOT NULL,
    message TEXT
);

CREATE TABLE IF NOT EXISTS rejection (
    run_id INTEGER NOT NULL REFERENCES etl_run (run_id),
    source TEXT NOT NULL,
    reason TEXT NOT NULL,
    original_row TEXT NOT NULL
);
