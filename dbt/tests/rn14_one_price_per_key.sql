-- RN-14: una sola fila por semana, producto, región, canal y unidad.
select week_start, product_id, region_id, channel_id, normalized_unit, count(*) as rows
from {{ ref('weekly_price') }}
group by week_start, product_id, region_id, channel_id, normalized_unit
having count(*) > 1
