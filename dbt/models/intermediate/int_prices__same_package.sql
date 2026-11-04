-- D-522, RN-15: el cambio de una semana compara solo los envases vendidos en las dos semanas, región por región.
-- Sin esto, una región que pasa de bandeja de 18 kilos a bandeja de 10 parece un alza o una baja del precio.
-- Dentro de un envase el volumen pesa como en RN-07 (es el mismo envase); entre envases, un promedio simple, para no
-- depender de cuánto trae cada uno. Sin un envase común en las dos semanas, el precio queda fuera de la comparación.
with rows as (
    select *, first_date - cast(isodow(first_date) - 1 as integer) as week_start
    from {{ ref('int_prices__units_normalized') }}
    where normalized_unit is not null
),
packages as (
    select week_start, source, channel, cast(region_id as integer) as region_id, product_group, product, variety,
           quality, normalized_unit, unit,
           case when source = 'wholesale' then sum(normalized_price * volume) / sum(volume)
                else avg(normalized_price) end as price,
           count(*) as quotes
    from rows
    group by week_start, source, channel, cast(region_id as integer), product_group, product, variety, quality,
             normalized_unit, unit
)
select now.week_start, now.source, now.channel, now.region_id, now.product_group, now.product, now.variety,
       now.quality, now.normalized_unit,
       avg(now.price) as price_now, avg(before.price) as price_before,
       cast(sum(now.quotes) as bigint) as quotes_now, cast(sum(before.quotes) as bigint) as quotes_before,
       string_agg(now.unit, ' · ' order by now.unit) as packages
from packages as now
join packages as before
  on before.week_start = now.week_start - 7
 and before.source = now.source and before.channel = now.channel and before.region_id = now.region_id
 and before.product_group = now.product_group and before.product = now.product and before.variety = now.variety
 and before.quality = now.quality and before.normalized_unit = now.normalized_unit and before.unit = now.unit
group by now.week_start, now.source, now.channel, now.region_id, now.product_group, now.product, now.variety,
         now.quality, now.normalized_unit
