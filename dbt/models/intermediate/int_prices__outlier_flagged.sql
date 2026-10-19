-- RN-12: un precio a más de 5 veces, o a menos de 1/5, de la mediana de su producto
-- esa semana, dentro de la misma fuente, se marca ATIPICO y no entra a los indicadores.
with weekly as (
    select *,
           quantile_cont(price, 0.5) over (
               partition by week_start, source, product_group, product, normalized_unit
           ) as median_price
    from {{ ref('int_prices__weekly') }}
)
select week_start, source, channel, region_id, product_group, product, variety, quality,
       normalized_unit, price, volume, observation_count,
       case when normalized_unit is not null
             and (price > median_price * 5 or price < median_price / 5) then 'ATIPICO'
            else unit_flag end as flag
from weekly
