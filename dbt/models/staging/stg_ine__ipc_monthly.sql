-- IPC mensual de alimentos (división 1 del INE), con tipos; cada archivo tal como se publicó.
select
    file                                                   as ine_file,
    cast(year as integer)                                  as year,
    cast(month as integer)                                 as month,
    {{ decimal_text('index_value') }}                      as index_value,
    {{ decimal_text('monthly_change') }}                   as monthly_change,
    year as raw_year, month as raw_month, index_value as raw_index_value,
    monthly_change as raw_monthly_change
from {{ source('bronze', 'ine_ipc') }}
