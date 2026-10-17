"""Read-only, server-paginated exploration of weekly aggregates (not raw rows)."""
from bi import queries

FIELDS = {'product_group': 'Grupo', 'product': 'Producto', 'variety': 'Variedad', 'quality': 'Calidad',
          'region': 'Región', 'channel': 'Canal', 'normalized_unit': 'Unidad', 'flag': 'Estado'}
LABELS = FIELDS | {'week_start': 'Semana', 'price': 'Precio ($)', 'previous_price': 'Precio anterior ($)',
                   'variation': 'Variación (%)', 'observation_count': 'Observaciones de origen',
                   'wholesale_price': 'Mayorista ($)', 'consumer_price': 'Consumidor ($)', 'margin': 'Brecha (%)'}
RAW = '''SELECT w.rowid AS record_id, w.week_start, p.product_group, p.product, p.variety, p.quality,
 r.region, c.channel, w.normalized_unit, w.price, w.observation_count,
 COALESCE(w.flag, 'SIN_MARCA') AS flag
 FROM weekly_price w JOIN dim_product p USING(product_id)
 JOIN dim_region r USING(region_id) JOIN dim_channel c USING(channel_id)'''

def base_sql(mode):
    if mode == 'Brecha mayorista / consumidor':
        return 'SELECT *, margin*100 AS percentage FROM (' + queries.read_query_body('k1_margin') + ')'
    if mode == 'Variación semanal':
        return '''SELECT w.rowid AS record_id, w.week_start, p.product_group, p.product, p.variety, p.quality,
 r.region, c.channel, w.normalized_unit, w.price, prev.price AS previous_price,
 CASE WHEN prev.price>0 THEN (w.price/prev.price-1)*100 END AS variation,
 w.observation_count, COALESCE(w.flag,'SIN_MARCA') AS flag
 FROM weekly_price w JOIN dim_product p USING(product_id) JOIN dim_region r USING(region_id)
 JOIN dim_channel c USING(channel_id)
 LEFT JOIN weekly_price prev ON prev.week_start=date(w.week_start,'-7 days')
 AND prev.product_id=w.product_id AND prev.region_id=w.region_id AND prev.channel_id=w.channel_id
 AND prev.normalized_unit=w.normalized_unit AND prev.flag IS NULL AND w.flag IS NULL'''
    if mode != 'Precios semanales':
        raise ValueError('Unknown data mode')
    return RAW

MODES = ['Precios semanales', 'Variación semanal', 'Brecha mayorista / consumidor']

def read_page(mode, filters=None, start=None, end=None, sort='week_start', descending=True,
              page=0, size=100, database_file=queries.DATABASE_FILE):
    """All values bound; identifiers allowlisted. Count and slice share one snapshot."""
    if not 8 <= size <= 100 or page < 0:
        raise ValueError('Invalid pagination')
    available = set(FIELDS) | {'week_start', 'price', 'record_id', 'observation_count', 'variation', 'previous_price'}
    if mode == MODES[2]:
        available = set(FIELDS)-{'flag'} | {'week_start','wholesale_price','consumer_price','margin','percentage'}
    if sort not in available:
        raise ValueError('Invalid sort')
    clauses, params = [], []
    for field, value in (filters or {}).items():
        if field not in available:
            raise ValueError('Invalid filter')
        if value is not None:
            clauses.append(f'"{field}" = ?'); params.append(value)
    for op, value in [('>=', start), ('<=', end)]:
        if value is not None:
            clauses.append(f'week_start {op} ?'); params.append(str(value))
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    base = '(' + base_sql(mode) + ')'
    tie = ['record_id'] if 'record_id' in available else ['week_start','product_group','product','variety','quality','region','channel','normalized_unit','wholesale_price','consumer_price']
    order = ', '.join([f'"{sort}" ' + ('DESC' if descending else 'ASC')] + [f'"{f}" ASC' for f in tie if f != sort])
    import pandas as pd
    from contextlib import closing
    with closing(queries.open_database(database_file)) as conn:
        conn.execute('BEGIN')
        count = conn.execute('SELECT COUNT(*) FROM '+base+where, params).fetchone()[0]
        page = min(page, max(0,(count-1)//size))
        rows = pd.read_sql_query('SELECT * FROM '+base+where+' ORDER BY '+order+' LIMIT ? OFFSET ?', conn,
                                 params=params+[size,page*size])
    return rows, count, page


def facets(database_file=queries.DATABASE_FILE):
    result = {}
    for field in FIELDS:
        rows = queries.run_sql('SELECT DISTINCT "'+field+'" AS value FROM ('+RAW+') WHERE "'+field+'" IS NOT NULL ORDER BY value', database_file)
        result[field] = rows['value'].tolist()
    span = queries.run_sql('SELECT MIN(week_start) first, MAX(week_start) last FROM weekly_price', database_file).iloc[0]
    return result, span['first'], span['last']
