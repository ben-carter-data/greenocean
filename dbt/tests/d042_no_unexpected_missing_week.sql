-- D-029 y D-042: cada fuente tiene precio todas las semanas, salvo el hueco conocido de la
-- fuente (consumidor, semana del 2022-05-02).
with sources as (select distinct source from {{ ref('dim_channel') }}),
     priced as (
         select distinct weekly_price.week_start, dim_channel.source
         from {{ ref('weekly_price') }} join {{ ref('dim_channel') }} using (channel_id)
     )
select dim_date.week_start, sources.source
from {{ ref('dim_date') }} cross join sources
left join priced on priced.week_start = dim_date.week_start and priced.source = sources.source
where priced.week_start is null
  and not (sources.source = 'consumer' and dim_date.week_start = '2022-05-02')
