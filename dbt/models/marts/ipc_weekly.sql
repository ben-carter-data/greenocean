-- D-155: el deflactor de cada semana. La semana toma el IPC del mes de su lunes (el mes
-- de dim_date, RN-08). Los precios reales quedan en pesos del último mes publicado.
-- Una semana de un mes aún no publicado usa ese último mes y queda marcada provisional.
with latest as (
    select year, month, food_index from {{ ref('ipc_monthly') }}
    order by year desc, month desc limit 1
),
weeks as (
    select week_start, year, month from {{ ref('dim_date') }}
)
select weeks.week_start,
       coalesce(ipc.year, latest.year)                       as ipc_year,
       coalesce(ipc.month, latest.month)                     as ipc_month,
       coalesce(ipc.food_index, latest.food_index)           as food_index,
       latest.year                                           as reference_year,
       latest.month                                          as reference_month,
       latest.food_index / coalesce(ipc.food_index, latest.food_index) as real_factor,
       ipc.food_index is null                                as provisional
from weeks
cross join latest
left join {{ ref('ipc_monthly') }} as ipc
  on ipc.year = weeks.year and ipc.month = weeks.month
