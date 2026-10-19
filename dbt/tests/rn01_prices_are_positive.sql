-- RN-01 y RN-11: ningún precio cargado es cero ni negativo.
select * from {{ ref('weekly_price') }} where price <= 0
