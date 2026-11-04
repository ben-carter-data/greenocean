-- RN-07 a RN-10: un precio por semana, producto, región, canal y unidad (etl.aggregate_weekly).
with rows as (
    -- RN-08: la semana se identifica por su lunes.
    select *, first_date - cast(isodow(first_date) - 1 as integer) as week_start
    from {{ ref('int_prices__units_normalized') }}
),
wholesale as (
    -- RN-07, D-521: precio semanal mayorista = precios diarios ponderados por los kilos o unidades que trae su volumen.
    select week_start, source, channel, region_id, product_group, product, variety, quality,
           normalized_unit,
           case when normalized_unit is not null then price_times_quantity / quantity end as price,
           volume, observation_count
    from (
        select week_start, source, channel, cast(region_id as integer) as region_id, product_group,
               product, variety, quality, normalized_unit,
               sum(normalized_price * volume * volume_quantity) as price_times_quantity,
               sum(volume * volume_quantity) as quantity,
               sum(volume) as volume,
               count(*) as observation_count
        from rows where source = 'wholesale'
        group by week_start, source, channel, cast(region_id as integer), product_group,
                 product, variety, quality, normalized_unit
    )
),
consumer as (
    -- RN-09: precio semanal al consumidor = promedio simple; RN-10: el punto de venta
    -- «Mercado Mayorista» es un canal más.
    select week_start, source, channel, cast(region_id as integer) as region_id, product_group,
           product, variety, quality, normalized_unit,
           avg(normalized_price) as price,
           cast(null as double) as volume,
           count(*) as observation_count
    from rows where source = 'consumer'
    group by week_start, source, channel, cast(region_id as integer), product_group,
             product, variety, quality, normalized_unit
)
select *,
       case when normalized_unit is null then 'UNIDAD_NO_CONVERTIBLE' end as unit_flag
from (select * from wholesale union all select * from consumer)
