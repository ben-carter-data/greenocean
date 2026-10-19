-- Las regiones con datos, con su número oficial.
select distinct cast(region_id as integer) as region_id, region
from {{ ref('int_prices__validated') }}
where reason is null
