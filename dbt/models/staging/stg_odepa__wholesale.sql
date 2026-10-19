-- Precios mayoristas diarios, limpios y con las columnas comunes (etl.clean, RN-01, RN-13).
-- Conserva las columnas originales para guardar tal cual cada fila rechazada (RN-11).
with raw as (
    select * from {{ source('bronze', 'odepa_wholesale') }}
)
select
    'wholesale'                                         as source,
    cast(file_year as integer)                          as file_year,
    try_cast(price_date as date)                        as first_date,
    try_cast(price_date as date)                        as last_date,
    try_cast(region_id as double)                       as region_id,
    {{ normalize_text('region') }}                      as region,
    'Mayorista'                                         as channel,
    case {{ normalize_text('subsector') }}
        when 'Hortalizas y tubérculos' then 'Hortalizas'
        else {{ normalize_text('subsector') }} end      as product_group,
    {{ normalize_text('product') }}                     as product,
    {{ normalize_text('variety') }}                     as variety,
    {{ normalize_text('quality') }}                     as quality,
    {{ normalize_text('sale_unit') }}                   as unit,
    {{ decimal_text('volume') }}                        as volume,
    {{ decimal_text('min_price') }}                     as min_price,
    {{ decimal_text('max_price') }}                     as max_price,
    {{ decimal_text('avg_price') }}                     as avg_price,
    to_json({
        'file_year': cast(file_year as integer), 'file_hash': file_hash, 'price_date': price_date,
        'region_id': region_id, 'region': region, 'market': market, 'subsector': subsector,
        'product': product, 'variety': variety, 'quality': quality, 'sale_unit': sale_unit,
        'origin': origin, 'volume': volume, 'min_price': min_price, 'max_price': max_price,
        'avg_price': avg_price
    })                                                  as original_row
from raw
