-- Las filas del INE tal como se leyeron, guardadas en la base publicada para reconstruir
-- la capa bronce si el INE no responde una semana (etl/pipeline.py).
select ine_file as file, raw_year as year, raw_month as month, raw_index_value as index_value,
       raw_monthly_change as monthly_change
from {{ ref('stg_ine__ipc_monthly') }}
