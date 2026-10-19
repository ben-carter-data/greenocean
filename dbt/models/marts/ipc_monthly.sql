-- D-155: una sola serie mensual del IPC de alimentos en base 2023 = 100.
-- Desde enero 2024 es la serie base 2023 del INE. Antes, la serie empalmada de
-- divisiones del INE (otra base) se enlaza por la variación oficial de enero 2024:
-- diciembre 2023 queda en el valor desde el cual enero 2024 sube exactamente lo que
-- publicó el INE, y toda la serie anterior se escala por el mismo factor.
with base_2023 as (
    select year, month, index_value, monthly_change
    from {{ ref('stg_ine__ipc_monthly') }} where ine_file = 'base_2023'
),
spliced as (
    select year, month, index_value
    from {{ ref('stg_ine__ipc_monthly') }} where ine_file = 'divisiones_empalmadas'
),
link as (
    select (select index_value / (1 + monthly_change / 100) from base_2023 where year = 2024 and month = 1)
         / (select index_value from spliced where year = 2023 and month = 12) as factor
)
select year, month, index_value as food_index, 'INE · base 2023' as origin
from base_2023
union all
select spliced.year, spliced.month, spliced.index_value * link.factor,
       'INE · serie empalmada, enlazada en enero 2024'
from spliced, link
where spliced.year * 100 + spliced.month < 202401
