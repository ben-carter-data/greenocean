"""Read-only, server-paginated exploration of weekly aggregates (not raw rows)."""

FIELDS = {
    'product_group': 'Grupo',
    'product': 'Producto',
    'variety': 'Variedad',
    'quality': 'Calidad',
    'region': 'Región',
    'channel': 'Canal',
    'normalized_unit': 'Unidad',
    'flag': 'Estado',
}
LABELS = FIELDS | {
    'week_start': 'Semana',
    'price': 'Precio ($)',
    'previous_price': 'Precio anterior ($)',
    'variation': 'Variación (%)',
    'observation_count': 'Observaciones de origen',
    'wholesale_price': 'Mayorista ($)',
    'consumer_price': 'Consumidor ($)',
    'margin': 'Brecha (%)',
}
