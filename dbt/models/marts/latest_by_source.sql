-- D-365: las dos últimas semanas de cada fuente, sin el corte de D-356, para la página «Último dato
-- por canal». El Dashboard y los indicadores siguen con la semana completa en ambas fuentes; aquí cada
-- fuente muestra su propia última semana. RN-12 se aplica igual: un precio a más de 5 veces, o a menos
-- de 1/5, de la mediana de su producto esa semana y fuente queda ATIPICO. D-522: cada fila trae también su cambio en el
-- mismo envase contra la semana anterior, para comparar como el resto del panel.
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
       change.price_now as same_package_now, change.price_before as same_package_before,
       change.quotes_now as same_package_quotes_now, change.quotes_before as same_package_quotes_before,
       change.packages as same_packages,
       case when recent.normalized_unit is not null
             and (recent.price > recent.median_price * 5 or recent.price < recent.median_price / 5) then 'ATIPICO'
            else recent.unit_flag end as flag
from recent
left join {{ ref('dim_region') }} as region on region.region_id = recent.region_id
left join {{ ref('int_prices__same_package') }} as change
  on change.week_start = recent.week_start and change.source = recent.source and change.channel = recent.channel
 and change.region_id = recent.region_id and change.product_group = recent.product_group
 and change.product = recent.product and change.variety = recent.variety and change.quality = recent.quality
 and change.normalized_unit = recent.normalized_unit
