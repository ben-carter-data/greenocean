-- RN-11: las filas rechazadas de la última carga, tal como venían, con su motivo.
-- El número de carga lo asigna el orquestador al registrar la carga en etl_run.
select cast({{ var('run_id', 0) }} as integer) as run_id, source, reason, original_row
from {{ ref('int_prices__validated') }}
where reason is not null
