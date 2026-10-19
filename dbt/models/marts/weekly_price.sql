-- Hechos: un precio por semana, producto, región, canal y unidad.
select strftime(prices.week_start, '%Y-%m-%d') as week_start,
       product.product_id, prices.region_id, channel.channel_id,
       prices.normalized_unit, prices.price, prices.volume, prices.observation_count, prices.flag
from {{ ref('int_prices__outlier_flagged') }} as prices
join {{ ref('dim_product') }} as product
  using (product_group, product, variety, quality)
join {{ ref('dim_channel') }} as channel
  using (channel, source)
