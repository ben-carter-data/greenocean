-- RN-03, RN-04, RN-05: la unidad de venta leída como unidad común y cantidad (etl.convert_unit).
-- Una unidad sin una sola cantidad declarada queda sin precio comparable.
-- D-520: «cien» son 100 unidades; «12 canastillos 125 gramos» son 1,5 kilos; una docena de paquetes con unidades
-- queda sin precio, porque la fuente no la usa siempre igual.
-- D-521: volume_quantity es cuántos kilos o unidades trae cada unidad de Volumen: ODEPA cuenta envases, salvo que la
-- unidad diga «volumen en unidades»; el kilo en un envase cuenta ese envase.
with valid as (
    select * from {{ ref('int_prices__validated') }} where reason is null
),
units as (
    select distinct unit, lower(unit) as text from valid
),
parsed as (
    select
        unit,
        text,
        case when starts_with(text, '$/kilo') then 'kilo'
             when starts_with(text, '$/unidad') then 'unidad'
             when starts_with(text, '$/litro') then 'litro' end                     as prefix_unit,
        starts_with(text, '$/cien')                                                 as per_hundred,
        regexp_extract(text, '(\d+) canastillos (\d+(?:,\d+)?) ?(?:gramos|grs)\b', 1) as baskets,
        regexp_extract(text, '(\d+) canastillos (\d+(?:,\d+)?) ?(?:gramos|grs)\b', 2) as basket_grams,
        len(regexp_extract_all(text, '\d+(?:,\d+)?'))                              as number_count,
        regexp_extract(text, '(\d+(?:,\d+)?) ?(kilos?|unidades|gramos|grs|litros?|ml)\b', 1) as amount,
        regexp_extract(text, '(\d+(?:,\d+)?) ?(kilos?|unidades|gramos|grs|litros?|ml)\b', 2) as measure
    from units
),
converted as (
    select
        unit,
        text,
        prefix_unit,
        per_hundred,
        try_cast(baskets as double) * try_cast(replace(basket_grams, ',', '.') as double) * 0.001 as basket_kilos,
        number_count,
        contains(text, 'docena') and measure = 'unidades'                          as dozen_of_units,
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
             when per_hundred then 'unidad'
             when basket_kilos > 0 then 'kilo'
             when number_count = 1 and measure_unit is not null and measure_quantity > 0 and not dozen_of_units
                 then measure_unit end                                               as normalized_unit,
        case when prefix_unit is not null then 1.0
             when per_hundred then 100.0
             when basket_kilos > 0 then basket_kilos
             when number_count = 1 and measure_unit is not null and measure_quantity > 0 and not dozen_of_units
                 then measure_quantity end                                           as unit_quantity,
        text
    from converted
)
select valid.*, conversion.normalized_unit, conversion.unit_quantity,
       case when conversion.normalized_unit is null then null
            when contains(conversion.text, 'volumen en unidades') then 1.0
            when regexp_matches(conversion.text, '^\$/kilo \(en .*?(\d+) kilos')
                then try_cast(regexp_extract(conversion.text, '^\$/kilo \(en .*?(\d+) kilos', 1) as double)
            else conversion.unit_quantity end                                        as volume_quantity,
       valid.avg_price / conversion.unit_quantity as normalized_price
from valid
join conversion using (unit)
