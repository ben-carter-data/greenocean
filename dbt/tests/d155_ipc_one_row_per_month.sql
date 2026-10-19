-- D-155: un solo índice por mes en la serie enlazada.
select year, month, count(*) from {{ ref('ipc_monthly') }} group by year, month having count(*) > 1
