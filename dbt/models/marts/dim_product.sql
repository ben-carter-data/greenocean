-- Cada clave de producto: grupo, producto, variedad y calidad.
select row_number() over (order by product_group, product, variety, quality) as product_id,
       product_group, product, variety, quality
from (select distinct product_group, product, variety, quality
      from {{ ref('int_prices__outlier_flagged') }})
