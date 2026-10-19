-- RN-03, RN-04, RN-05: la unidad de venta leída como unidad común y cantidad (etl.convert_unit).
-- Una unidad sin una sola cantidad declarada queda sin precio comparable.
with valid as (
    select * from {{ ref('int_prices__validated') }} where reason is null
),
units as (
    select distinct unit, lower(unit) as text from valid
),
parsed as (
    select
        unit,
        case when starts_with(text, '$/kilo') then 'kilo'
             when starts_with(text, '$/unidad') then 'unidad'
             when starts_with(text, '$/litro') then 'litro' end                     as prefix_unit,
        len(regexp_extract_all(text, '\d+(?:,\d+)?'))                              as number_count,
        regexp_extract(text, '(\d+(?:,\d+)?) ?(kilos?|unidades|gramos|grs|litros?|ml)\b', 1) as amount,
        regexp_extract(text, '(\d+(?:,\d+)?) ?(kilos?|unidades|gramos|grs|litros?|ml)\b', 2) as measure
    from units
),
converted as (
    select
        unit,
        prefix_unit,
        number_count,
        case measure when 'kilo' then 'kilo' when 'kilos' then 'kilo' when 'gramos' then 'kilo'
                     when 'grs' then 'kilo' when 'unidades' then 'unidad' when 'litro' then 'litro'
                     when 'litros' then 'litro' when 'ml' then 'litro' end         as measure_unit,
        try_cast(replace(amount, ',', '.') as double)
            * case when measure in ('gramos', 'grs', 'ml') then 0.001 else 1 end    as measure_quantity
    from parsed
),
conversion as (
    select
        unit,
        case when prefix_unit is not null then prefix_unit
             when number_count = 1 and measure_unit is not null and measure_quantity > 0
                 then measure_unit end                                               as normalized_unit,
        case when prefix_unit is not null then 1.0
             when number_count = 1 and measure_unit is not null and measure_quantity > 0
                 then measure_quantity end                                           as unit_quantity
    from converted
)
select valid.*, conversion.normalized_unit, conversion.unit_quantity,
       valid.avg_price / conversion.unit_quantity as normalized_price
from valid
join conversion using (unit)
