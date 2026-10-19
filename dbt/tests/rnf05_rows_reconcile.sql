-- RNF-05: cada fila leída queda cargada o rechazada exactamente una vez.
with read as (
    select (select count(*) from {{ source('bronze', 'odepa_wholesale') }})
         + (select count(*) from {{ source('bronze', 'odepa_consumer') }}) as rows
),
handled as (
    select count(*) filter (where reason is null) as loaded,
           count(*) filter (where reason is not null) as rejected
    from {{ ref('int_prices__validated') }}
)
select read.rows, handled.loaded, handled.rejected,
       (select count(*) from {{ ref('rejection') }}) as rejection_rows
from read, handled
where read.rows <> handled.loaded + handled.rejected
   or handled.rejected <> (select count(*) from {{ ref('rejection') }})
