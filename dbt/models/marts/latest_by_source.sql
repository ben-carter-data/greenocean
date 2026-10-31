-- D-365: las dos últimas semanas de cada fuente, sin el corte de D-356, para la página «Último dato
-- por canal». El Panorama y los indicadores siguen con la semana completa en ambas fuentes; aquí cada
-- fuente muestra su propia última semana. RN-12 se aplica igual: un precio a más de 5 veces, o a menos
-- de 1/5, de la mediana de su producto esa semana y fuente queda ATIPICO.
with weeks as (
    select source, week_start
    from (select distinct source, week_start from {{ ref('int_prices__weekly') }})
    qualify row_number() over (partition by source order by week_start desc) <= 2
),
recent as (
    select prices.*,
           quantile_cont(prices.price, 0.5) over (
               partition by prices.week_start, prices.source, prices.product_group, prices.product,
                            prices.normalized_unit
           ) as median_price
    from {{ ref('int_prices__weekly') }} as prices
    join weeks using (source, week_start)
)
select strftime(recent.week_start, '%Y-%m-%d') as week_start, recent.source, recent.channel,
       recent.region_id, region.region, recent.product_group, recent.product, recent.variety,
       recent.quality, recent.normalized_unit, recent.price, recent.observation_count,
       case when recent.normalized_unit is not null
             and (recent.price > recent.median_price * 5 or recent.price < recent.median_price / 5) then 'ATIPICO'
            else recent.unit_flag end as flag
from recent
left join {{ ref('dim_region') }} as region on region.region_id = recent.region_id
