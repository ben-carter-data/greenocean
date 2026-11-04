-- D-522, RN-15: el cambio de cada semana contra la anterior, por región y solo en el mismo envase, entre precios válidos
-- de las dos semanas. Todo lo que muestra una variación lee esta tabla; weekly_price sigue siendo el nivel del precio.
select strftime(change.week_start, '%Y-%m-%d') as week_start,
       product.product_id, change.region_id, channel.channel_id, change.normalized_unit,
       change.price_now, change.price_before, change.quotes_now, change.quotes_before, change.packages
from {{ ref('int_prices__same_package') }} as change
join {{ ref('int_prices__outlier_flagged') }} as now
  on now.week_start = change.week_start and now.source = change.source and now.channel = change.channel
 and now.region_id = change.region_id and now.product_group = change.product_group and now.product = change.product
 and now.variety = change.variety and now.quality = change.quality and now.normalized_unit = change.normalized_unit
join {{ ref('int_prices__outlier_flagged') }} as before
  on before.week_start = change.week_start - 7 and before.source = change.source and before.channel = change.channel
 and before.region_id = change.region_id and before.product_group = change.product_group
 and before.product = change.product and before.variety = change.variety and before.quality = change.quality
 and before.normalized_unit = change.normalized_unit
join {{ ref('dim_product') }} as product
  on product.product_group = change.product_group and product.product = change.product
 and product.variety = change.variety and product.quality = change.quality
join {{ ref('dim_channel') }} as channel
  on channel.channel = change.channel and channel.source = change.source
where now.flag is null and before.flag is null
