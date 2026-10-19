-- Los canales; el mayorista es un canal más, así el margen compara dos canales.
select row_number() over (order by source, channel) as channel_id, channel, source
from (select distinct channel, source from {{ ref('int_prices__outlier_flagged') }})
