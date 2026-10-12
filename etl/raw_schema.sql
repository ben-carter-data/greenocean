-- Raw tables: the files exactly as published, plus the file year and fingerprint.
-- Every source column is stored as text; types are applied later by the ETL.
CREATE TABLE IF NOT EXISTS raw_wholesale (
    file_year INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    price_date TEXT, region_id TEXT, region TEXT, market TEXT, subsector TEXT,
    product TEXT, variety TEXT, quality TEXT, sale_unit TEXT, origin TEXT,
    volume TEXT, min_price TEXT, max_price TEXT, avg_price TEXT
);

CREATE TABLE IF NOT EXISTS raw_consumer (
    file_year INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    year TEXT, month TEXT, week TEXT, week_start TEXT, week_end TEXT,
    region_id TEXT, region TEXT, sector TEXT, sales_channel TEXT,
    product_group TEXT, product TEXT, unit TEXT, min_price TEXT,
    max_price TEXT, avg_price TEXT
);

CREATE INDEX IF NOT EXISTS ix_raw_wholesale_year ON raw_wholesale (file_year);
CREATE INDEX IF NOT EXISTS ix_raw_consumer_year ON raw_consumer (file_year);
