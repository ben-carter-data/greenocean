-- Una fila por semana, sin huecos, con su año y semana ISO, mes y estación (D-095).
with bounds as (
    select min(week_start) as first_week, max(week_start) as last_week
    from {{ ref('int_prices__outlier_flagged') }}
),
weeks as (
    select cast(unnest(generate_series(first_week, last_week, interval 7 day)) as date) as day
    from bounds
)
select strftime(day, '%Y-%m-%d')                                    as week_start,
       isoyear(day)                                                 as iso_year,
       weekofyear(day)                                              as iso_week,
       month(day)                                                   as month,
       ['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
        'septiembre','octubre','noviembre','diciembre'][month(day)] as month_name,
       year(day)                                                    as year,
       case when month(day) in (12, 1, 2) then 'verano'
            when month(day) in (3, 4, 5) then 'otoño'
            when month(day) in (6, 7, 8) then 'invierno'
            else 'primavera' end                                    as season
from weeks
