-- Precios al consumidor semanales, limpios y con las columnas comunes (etl.clean, RN-01, RN-02, RN-13).
with raw as (
    select *, {{ normalize_text('product') }} as clean_product from {{ source('bronze', 'odepa_consumer') }}
),
split as (
    select *, string_split(clean_product, '|') as parts from raw
)
select
    'consumer'                                          as source,
    cast(file_year as integer)                          as file_year,
    try_cast(week_start as date)                        as first_date,
    try_cast(week_end as date)                          as last_date,
    try_cast(region_id as double)                       as region_id,
    {{ normalize_text('region') }}                      as region,
    {{ normalize_text('sales_channel') }}               as channel,
    {{ normalize_text('product_group') }}               as product_group,
    -- RN-02: «Producto|Variedad|Calidad»; sin tres partes, variedad y calidad sin especificar.
    case when len(parts) = 3 then trim(parts[1]) else clean_product end         as product,
    case when len(parts) = 3 then trim(parts[2]) else 'Sin especificar' end     as variety,
    case when len(parts) = 3 then trim(parts[3]) else 'Sin especificar' end     as quality,
    {{ normalize_text('unit') }}                        as unit,
    cast(null as double)                                as volume,
    {{ decimal_text('min_price') }}                     as min_price,
    {{ decimal_text('max_price') }}                     as max_price,
    {{ decimal_text('avg_price') }}                     as avg_price,
    to_json({
        'file_year': cast(file_year as integer), 'file_hash': file_hash, 'year': "year",
        'month': "month", 'week': week, 'week_start': week_start, 'week_end': week_end,
        'region_id': region_id, 'region': region, 'sector': sector,
        'sales_channel': sales_channel, 'product_group': product_group, 'product': product,
        'unit': unit, 'min_price': min_price, 'max_price': max_price, 'avg_price': avg_price
    })                                                  as original_row
from split
