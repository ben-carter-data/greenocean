-- RN-11: el motivo de rechazo de cada fila, o NULL si es válida (etl.validate_rows).
-- Una fila con varios problemas recibe el primero, así cada fila leída queda cargada
-- o rechazada exactamente una vez.
with rows as (
    select * from {{ ref('stg_odepa__wholesale') }}
    union all
    select * from {{ ref('stg_odepa__consumer') }}
)
select
    *,
    case
        when min_price is null or max_price is null or avg_price is null
          or first_date is null or last_date is null or region_id is null
            then 'UNREADABLE_VALUE'
        when min_price <= 0 or max_price <= 0 or avg_price <= 0
            then 'NON_POSITIVE_PRICE'
        when min_price > max_price
            then 'MINIMUM_ABOVE_MAXIMUM'
        -- La primera semana del consumidor empieza en diciembre del año anterior.
        when year(first_date) <> file_year and year(last_date) <> file_year
            then 'DATE_OUTSIDE_FILE_YEAR'
        -- Una fila mayorista sin volumen no entra al promedio ponderado (RN-07).
        when source = 'wholesale' and not coalesce(volume > 0, false)
            then 'NON_POSITIVE_VOLUME'
    end as reason
from rows
