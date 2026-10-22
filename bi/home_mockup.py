"""Pixel-directed home dashboard. All geometry is derived from supplied real rows.

No raster charts, fabricated trend points, ETL changes, or remotely hosted assets.
"""
import html
import math
import statistics
import base64
import json
from functools import lru_cache
from pathlib import Path

RED = '#e62035'
BLUE = '#0783ff'
GRAY = '#555c65'
AMBER = '#af6700'

FAMILY_ART_FILES = {
    'Hortalizas': 'hortalizas.webp',
    'Frutas': 'frutas.webp',
    'Abarrotes y otros': 'abarrotes.webp',
    'Carne bovina': 'carne-bovina.webp',
    'Pan': 'pan.webp',
    'Lácteos - Huevos - Margarinas': 'lacteos-huevos-margarinas.webp',
    'Carne de Cerdo - Ave - Cordero': 'cerdo-ave-cordero.webp',
    'Cerdo, ave y cordero': 'cerdo-ave-cordero.webp',
}


@lru_cache(maxsize=None)
def family_art_data_uri(group):
    """Return a compact, self-contained family image for Streamlit HTML."""
    filename = FAMILY_ART_FILES.get(group)
    if not filename:
        return None
    path = Path(__file__).parent / 'assets' / 'families' / filename
    if not path.exists():
        return None
    return 'data:image/webp;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


def family_art(group, css_class, fallback='📦'):
    source = family_art_data_uri(group)
    if source:
        return (f'<img class="{css_class}" src="{source}" alt="" '
                'loading="eager" decoding="async" aria-hidden="true">')
    return f'<span class="{css_class} fallback" aria-hidden="true">{fallback}</span>'


def esc(value):
    return html.escape(str(value), quote=True)


def number(value, decimals=0):
    if value is None or not math.isfinite(float(value)):
        return '—'
    return f'{value:,.{decimals}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def percent(value, signed=False):
    return ('+' if signed and value > 0 else '−' if value < 0 else '') + number(abs(value), 1) + ' %'


def icon(kind):
    paths = {
        'up':'<path d="M12 20V4m-6 6 6-6 6 6"/>',
        'down':'<path d="M12 4v16m-6-6 6 6 6-6"/>',
        'equal':'<path d="M6 9h12M6 15h12"/>',
        'alert':'<path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v5m0 3v.2"/>',
        'home':'<path d="m3 10 9-7 9 7v11H3V10Z"/>',
        'bars':'<path d="M4 20V12m8 8V5m8 15V9"/>',
        'bell':'<path d="M4 17h16l-2-4V8a6 6 0 0 0-12 0v5l-2 4Zm6 4h4"/>',
        'clock':'<circle cx="12" cy="12" r="10"/><path d="M12 5v7l5 3"/>',
        'tree':'<circle cx="12" cy="4" r="2"/><circle cx="4" cy="20" r="2"/><circle cx="12" cy="20" r="2"/><circle cx="20" cy="20" r="2"/><path d="M12 6v12M4 18v-6h16v6"/>',
        'code':'<path d="m7 5-5 7 5 7m10-14 5 7-5 7M14 3l-4 18"/>',
        'document':'<path d="M5 2h10l4 4v16H5V2Zm10 0v5h4M8 11h8m-8 4h8m-8 4h6"/>',
    }
    return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths[kind]+'</svg>'


def style(mode, palette):
    css = Path(__file__).with_suffix('.css').read_text()
    dark = palette['base'] == 'dark'
    colors = {'BG': '#ffffff' if not dark else palette['background'],
              'PANEL': '#ffffff' if not dark else palette['card'],
              'INK': '#101827' if not dark else palette['strong_text'],
              'MUTED': '#64748b' if not dark else '#d4dae4',
              'ACCENT': palette['accent'],
              'BORDER': '#e0e6ee' if not dark else palette['card_border'],
              'SOFT': '#f5f8fc' if not dark else palette['grid']}
    for key, value in colors.items():
        css = css.replace('__'+key+'__', value)
    if dark:
        css += """
        .greenocean-mockup{--mock-rise:#ff8a96;--mock-fall:#83baff;}
        .greenocean-mockup .mock-metric:nth-child(1){--metric:#ff8a96!important;}
        .greenocean-mockup .mock-metric:nth-child(2){--metric:#83baff!important;}
        .greenocean-mockup .mock-metric:nth-child(3){--metric:#d4d8df!important;}
        .greenocean-mockup .mock-metric:nth-child(4){--metric:#eec16e!important;}
        .greenocean-mockup .mock-badge{background:#ff8a9620;}
        .greenocean-mockup .mock-badge.down{background:#83baff20;}
        .greenocean-mockup .mock-badge.equal{background:#d4d8df20;}
        .greenocean-mockup .mock-badge.alert{background:#eec16e20;}
        .greenocean-mockup .mock-table-link,.st-key-mock_data_link a{color:#83baff!important;}
        .greenocean-mockup .mock-last-price{fill:#83baff;}
        """
    return '<style>'+css+'</style>' 


def title(week_label, updated, loaded):
    return ('<header class="mock-intro"><div><h1>¿Qué familias de alimentos subieron y bajaron?</h1>'
            f'<p>Variación típica (mediana) por familia frente a la semana anterior · semana {esc(week_label)}</p></div>'
            f'<span class="mock-updated"><i class="{"loaded" if loaded else "failed"}"></i>'
            f'{"Actualizado" if loaded else "Carga con falla"} {esc(updated)}</span></header>')


def metrics(counts, alert_count, alert_delta, regional=False, examples=None):
    notes = [
        'combinaciones de producto y canal cuyo precio subió',
        'combinaciones de producto y canal cuyo precio bajó',
        'combinaciones de producto y canal con el mismo precio',
    ]
    examples = examples or {}
    change = ('Sin comparación anterior' if alert_delta is None else
              f'{abs(alert_delta)} '+('menos' if alert_delta < 0 else 'más' if alert_delta > 0 else 'de diferencia')+' que la semana anterior')
    entries = [('up','Precios que subieron',counts[0],notes[0],RED),
               ('down','Precios que bajaron',counts[1],notes[1],BLUE),
               ('equal','Precios sin cambio',counts[2],notes[2],GRAY),
               ('alert','Alertas nacionales' if regional else 'Cambios inusuales para revisar',alert_count,
                'combinaciones fuera de su rango habitual · '+change,AMBER)]
    result=[]
    for kind,label,value,note,color in entries:
        hint = 'Cambios nacionales fuera de su comportamiento habitual; no son errores confirmados.' if kind=='alert' else 'Cada comparación conserva producto, variedad, calidad, unidad y canal. No cuenta productos únicos ni dinero.'
        example_text = examples.get(kind, [])
        example_markup = (f'<p class="mock-metric-examples"><span>Ejemplos: </span>{esc(" · ".join(example_text))}</p>'
                          if example_text else '')
        result.append(f'<div class="mock-metric" style="--metric:{color}" title="{esc(hint)}">'
                      f'<span class="mock-badge {kind}">{icon(kind)}</span><div><div class="mock-metric-label">{label}</div>'
                      f'<strong aria-label="cantidad">{number(value)}</strong><p>{esc(note)}</p>{example_markup}</div></div>')
    return ('<section class="mock-metrics" aria-label="Cantidades de comparaciones y alertas">'+''.join(result)+
            '</section><p class="mock-count-note">Para comparar de forma justa, seguimos el mismo producto, variedad, calidad, unidad y canal en las dos semanas. Así no mezclamos, por ejemplo, una manzana por kilo con otra variedad o con otro canal. Cada número cuenta comparaciones de precios; no productos únicos ni dinero.'+
            (' Las alertas son nacionales, aunque hayas elegido una región.' if regional else '')+'</p>')


def product_label(row, full=False):
    parts=[str(row['product'])]
    for field in ('variety','quality') if full else ('variety',):
        if row.get(field) and row[field] != 'Sin especificar':
            parts.append(str(row[field]))
    return ' · '.join(parts)


def previous_price(row):
    value = row.get('_previous_price')
    if value is not None and math.isfinite(float(value)):
        return float(value)
    return None


ORDERS = ('Mayores cambios', 'Subidas', 'Bajadas', 'Inusuales')


def compare_week(current, previous, keys):
    """Join two explicitly chosen consecutive weeks; never infer a missing price."""
    rows = current.merge(previous[keys+['national_price']].rename(
        columns={'national_price':'_previous_price'}), on=keys, how='left', validate='one_to_one')
    valid = rows['_previous_price'].gt(0) & rows['national_price'].notna()
    rows['variation'] = (rows['national_price']/rows['_previous_price']-1).where(valid)
    rows['change_amount'] = (rows['national_price']-rows['_previous_price']).where(valid)
    return rows


def order_movements(rows, count, order):
    """Top N is a limit on a deterministic ranking, not a page size."""
    ranked = rows[rows.variation.notna() & rows.variation.abs().lt(float('inf'))].copy()
    ranked['_magnitude'] = ranked.variation.abs()
    if order == 'Subidas':
        ranked = ranked[ranked.variation > 0]
    elif order == 'Bajadas':
        ranked = ranked[ranked.variation < 0]
    elif order == 'Inusuales':
        ranked = ranked[ranked.is_alert]
    primary = ['_severity', '_magnitude'] if order == 'Inusuales' else ['_magnitude']
    ties = ['product', 'variety', 'quality', 'normalized_unit', 'channel']
    return ranked.sort_values(primary+ties, ascending=[False]*len(primary)+[True]*len(ties)).head(count)


def money(value, signed=False):
    if value is None or not math.isfinite(float(value)):
        return '—'
    sign = ('+' if value > 0 else '−' if value < 0 else '') if signed else ''
    return sign+'$'+number(abs(value) if signed else value)


def row_key(row):
    return tuple(row.get(field) for field in ('product_group','product','variety','quality','normalized_unit','channel'))


def family_anchor(group):
    return 'familia-' + base64.urlsafe_b64encode(group.encode('utf-8')).decode('ascii').rstrip('=')




def table(rows, focus_link, data_link, selected=None, scope='Promedio nacional', order='Mayores cambios', count=8):
    """A readable ranking with real prices, in-cell bars and exact-series links."""
    body=[]
    maximum=max([abs(r['variation']) for r in rows if r.get('variation') is not None and math.isfinite(r['variation'])] or [1]) or 1
    for row in rows:
        previous=previous_price(row)
        variation=row.get('variation')
        valid=variation is not None and math.isfinite(variation)
        state='neutral' if not valid or variation==0 else 'rise' if variation>0 else 'fall'
        mark='=' if valid and variation==0 else '▲' if valid and variation>0 else '▼'
        change=money(row.get('change_amount'),True) if valid else '—'
        signal='Sin comparación' if not valid else 'Cambio inusual' if row.get('is_alert') else 'Subió' if variation>0 else 'Bajó' if variation<0 else 'Sin cambio'
        selected_attr=' class="selected"' if selected is not None and row_key(row)==row_key(selected) else ''
        changed = '<span class="mock-coverage-change">Variación sobre las regiones de ambas semanas</span>' if row.get('_coverage_changed') else ''
        bar=(f'<span class="mock-change-value">{mark} {percent(variation*100,True)}</span>'
             f'<span class="mock-change-track"><span style="width:{abs(variation)/maximum*100:.3f}%"></span></span>') if valid else 'Sin comparación'
        body.append(f'<tr{selected_attr}><td><a class="mock-product-link" href="{esc(focus_link(row))}" target="_self"'
                    f' aria-label="Ver evolución de {esc(product_label(row,True))}, {esc(row["channel"])}">{esc(product_label(row))}</a>'
                    f'<span class="mock-cell-note">Calidad: {esc(row.get("quality","Sin especificar"))}</span></td>'
                    f'<td>{esc(row["channel"])}<span class="mock-cell-note">{esc(scope)} · por {esc(row["normalized_unit"])}</span>{changed}</td>'
                    f'<td>{money(previous)}</td><td><strong>{money(row["national_price"])}</strong></td>'
                    f'<td class="{state}">{change}</td><td class="{state}">{bar}</td>'
                    f'<td class="mock-signal">{esc(signal)}<a href="{esc(data_link(row))}" target="_self">Ver datos ↗</a></td></tr>')
    return ('<section class="mock-panel mock-price-table"><h2>Productos con mayores cambios</h2>'
            f'<p class="mock-panel-subtitle">Top {count} · {esc(order)}'+
            (' · mayor distancia del rango habitual' if order=='Inusuales' else ' · ordenados por tamaño del cambio porcentual')+
            '</p><p class="mock-table-instruction">Selecciona un producto para ver su evolución. Precios en pesos chilenos.</p>'
            '<div class="mock-table-scroll" tabindex="0" role="region" aria-label="Ranking de precios y cambios"><table>'
            '<thead><tr><th scope="col">Producto y variedad</th><th scope="col">Mercado y unidad</th><th scope="col">Anterior</th>'
            '<th scope="col">Actual</th><th scope="col">Cambio $</th><th scope="col">Cambio %</th><th scope="col">Señal</th></tr></thead>'
            '<tbody>'+(''.join(body) or '<tr><td colspan="7">No hay movimientos para este orden y estos filtros.</td></tr>')+
            '</tbody></table></div></section>')


def product_scope(product_name, family):
    """Visible scope reminder when a product narrows the family result."""
    return ('<div class="mock-product-scope" role="status">'
            '<span class="mock-product-scope-kicker">Vista de producto</span>'
            f'<strong>{esc(product_name)}</strong><span>Familia: {esc(family)}. '
            'El porcentaje usa solo este producto; no representa el cambio de toda la familia.</span></div>')


def active_scope(region, family, product_filter=None):
    """Compact reminder after the map replaces the three permanent selectors."""
    place = 'Todo Chile' if region == 'Todas' else region.replace('Región de ', '').replace('Región del ', '')
    family_label = 'Todas las familias' if family == 'Todas' else family
    product = 'Todos los productos'
    if product_filter:
        _, name, variety = product_filter
        product = name if variety == 'Sin especificar' else f'{name} · {variety}'
    return ('<div class="mock-active-scope" role="status"><span class="mock-scope-label">Selección actual</span>'
            f'<span><b>Región</b>{esc(place)}</span><i></i>'
            f'<span><b>Familia</b>{esc(family_label)}</span><i></i>'
            f'<span><b>Producto</b>{esc(product)}</span></div>')


def movement_icon(state):
    """Dimensional bars and arrow; the adjacent word carries the meaning."""
    return (f'<span class="mock-movement-icon {state}" aria-hidden="true">'
            '<i></i><i></i><i></i><b></b></span>')


def family_summary(rows, detail_link=None, product_filter=None):
    """Seven-family overview and diverging chart from actual weekly changes."""
    family_icons = {
        'Frutas': '🍎', 'Hortalizas': '🥬', 'Carne bovina': '🥩',
        'Carne de Cerdo - Ave - Cordero': '🍗', 'Lácteos - Huevos - Margarinas': '🥚',
        'Abarrotes y otros': '🥫', 'Pan': '🍞',
    }
    valid = [row for row in rows if row.get('variation') is not None and
             math.isfinite(float(row['variation']))]
    groups = {}
    for row in valid:
        group = str(row.get('product_group') or 'Sin grupo')
        groups.setdefault(group, []).append(row)
    summary = [(group, sum(float(row['variation']) for row in members) / len(members), members)
               for group, members in groups.items()]
    summary.sort(key=lambda item: (-item[1], item[0]))
    scale = max((abs(average) for _, average, _ in summary), default=1) or 1
    selected_name = None
    if product_filter:
        _, product, variety = product_filter
        selected_name = product if variety == 'Sin especificar' else f'{product} · {variety}'
    gallery = []
    chart_rows = []
    for group, average, members in summary:
        # A value that rounds to 0.0% must not be described as a fall or rise.
        state = 'neutral' if abs(average * 100) < .05 else 'rise' if average > 0 else 'fall'
        word = {'rise': 'Subió', 'fall': 'Bajó', 'neutral': 'Sin variación'}[state]
        displayed_change = '0,0 %' if state == 'neutral' else percent(average * 100, True)
        size = min(50, abs(average) / scale * 50)
        bar = (f'<span class="mock-family-bar {state}" style="width:{size:.2f}%"></span>'
               if state != 'neutral' else '<span class="mock-family-zero"></span>')
        detail = (f'<a href="{esc(detail_link(group))}" target="_self">Ver detalle →</a>'
                  if detail_link else '')
        display_name = selected_name or group
        card_content = (f'<span class="mock-family-product" aria-hidden="true">'
                        f'{family_art(group, "mock-family-product-image", family_icons.get(group, "📦"))}</span>'
                        f'<strong class="mock-family-tile-name">{esc(display_name)}</strong>'
                        + (f'<span class="mock-family-tile-family">{esc(group)}</span>' if selected_name else '')
                        + f'<span class="mock-family-tile-change">{word} <b>{displayed_change}</b></span>'
                        '<span class="mock-family-tile-action">Ver detalle →</span>')
        if detail_link:
            gallery.append(f'<a class="mock-family-tile {state}" href="{esc(detail_link(group))}" target="_self"'
                           f' aria-label="Ver detalle de {esc(group)}: {word.lower()} {displayed_change}">{card_content}</a>')
        else:
            gallery.append(f'<div class="mock-family-tile {state}">{card_content}</div>')
        chart_rows.append(f'<div class="mock-family-row {state}">'
                     f'<span class="mock-family-name">{family_art(group, "mock-family-row-image", family_icons.get(group, "📦"))}'
                     f'<strong>{esc(display_name)}</strong></span>'
                     f'<span class="mock-family-track" role="img" aria-label="{esc(group)}: {word.lower()} {displayed_change}">{bar}</span>'
                     f'<span class="mock-family-value">{displayed_change}</span>'
                     f'<span class="mock-family-state">{movement_icon(state)}<span>{word}</span></span>{detail}'
                     '</div>')
    single = len(summary) == 1
    overview_title = (f'Resultado de {esc(selected_name)}' if selected_name else
                      'Familia seleccionada' if single else f'Las {len(summary)} familias de alimentos')
    overview_note = ('Cambios de este producto en las series con precio en ambas semanas.' if selected_name else
                     'Revisa los productos de esta familia más abajo.' if single else
                     'Ordenadas desde la mayor subida hasta la mayor baja. Selecciona una para ver sus productos.')
    chart_title = 'Cambio del producto seleccionado' if selected_name else 'Movimiento por familia'
    chart_note = ('Promedio simple de los cambios de este producto por calidad, unidad y canal.' if selected_name else
                  'Promedio simple de las variaciones de precios comparables frente a la semana anterior.')
    empty_note = ('Este producto no tiene precios en ambas semanas con los filtros elegidos.' if selected_name else
                  'No hay familias con precio en ambas semanas.')
    # Built apart: a backslash inside an f-string expression needs Python 3.12, and CI runs 3.11.
    empty = f'<p class="mock-empty">{empty_note}</p>'
    gallery_html = ''.join(gallery) or empty
    single_class = ' is-single' if single else ''
    return ('<section class="mock-family-summary" id="familias">'
            f'<div class="mock-family-overview"><div class="mock-family-overview-heading"><h2>{overview_title}</h2>'
            f'<p>{overview_note}</p></div>'
            f'<div class="mock-family-gallery{single_class}">{gallery_html}</div></div>'
            f'<div class="mock-family-chart"><div class="mock-family-heading"><div><h2>{chart_title}</h2>'
            f'<p>{chart_note}</p></div>'
            '<span class="mock-family-legend"><i></i> Subida <i></i> Bajada</span></div>'
            '<div class="mock-family-rows">'
            + (''.join(chart_rows) or empty)
            + '</div></div></section>')


def comparison_context(week_label, previous_label, scope, updated):
    """Tell readers which observations can be compared and where they came from."""
    return ('<section class="mock-comparison-context"><h2>¿Qué estamos comparando?</h2>'
            '<div class="mock-comparison-facts">'
            '<div><span class="mock-fact-icon what" aria-hidden="true">?</span><strong>Qué</strong>'
            '<span>El precio de cada alimento.</span></div>'
            '<div><span class="mock-fact-icon when" aria-hidden="true"></span><strong>Cuándo</strong>'
            f'<span>Semana {esc(previous_label)} → semana {esc(week_label)}</span></div>'
            '<div><span class="mock-fact-icon where" aria-hidden="true"></span><strong>Dónde</strong>'
            f'<span>{esc(scope)} · por tipo de comercio, no por tienda</span></div>'
            '<div><span class="mock-fact-icon source" aria-hidden="true"></span><strong>Fuente</strong>'
            f'<span>ODEPA · actualizado {esc(updated)}</span></div>'
            '</div><p>Mostramos alimentos con precio en ambas semanas. El cambio de cada familia '
            'es la mediana de esos cambios: lo que hizo el producto típico.</p></section>')


@lru_cache(maxsize=1)
def chile_regions_geometry():
    """Local, simplified administrative geometry; prices are joined at runtime."""
    path = Path(__file__).parent / 'assets' / 'chile-regions.geojson'
    return json.loads(path.read_text(encoding='utf-8'))


def _geometry_points(geometry):
    """Yield every lon/lat pair from Polygon or MultiPolygon coordinates."""
    coordinates = geometry['coordinates']
    polygons = coordinates if geometry['type'] == 'MultiPolygon' else [coordinates]
    for polygon in polygons:
        for ring in polygon:
            yield from ring


def _geometry_paths(geometry, project):
    """Convert GeoJSON rings to compact SVG paths while preserving holes."""
    coordinates = geometry['coordinates']
    polygons = coordinates if geometry['type'] == 'MultiPolygon' else [coordinates]
    paths = []
    for polygon in polygons:
        for ring in polygon:
            if len(ring) < 3:
                continue
            points = [project(lon, lat) for lon, lat in ring]
            paths.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in points) + 'Z')
    return ''.join(paths)


def _ring_centroid(ring):
    """Area-weighted centroid of one closed lon/lat ring."""
    area_twice = 0.0
    longitude_sum = 0.0
    latitude_sum = 0.0
    for first, second in zip(ring, ring[1:] + ring[:1]):
        cross = first[0] * second[1] - second[0] * first[1]
        area_twice += cross
        longitude_sum += (first[0] + second[0]) * cross
        latitude_sum += (first[1] + second[1]) * cross
    if abs(area_twice) < 1e-9:
        return (sum(point[0] for point in ring) / len(ring),
                sum(point[1] for point in ring) / len(ring))
    return longitude_sum / (3 * area_twice), latitude_sum / (3 * area_twice)


# The overview of the Dashboard (D-092): a real-proportion map of Chile whose regions
# each lead to their own row, the movement by family and the products of one family.
REGION_SHORT_NAMES = {
    'Región de Arica y Parinacota': 'Arica y Parinacota', 'Región de Tarapacá': 'Tarapacá',
    'Región de Antofagasta': 'Antofagasta', 'Región de Atacama': 'Atacama',
    'Región de Coquimbo': 'Coquimbo', 'Región de Valparaíso': 'Valparaíso',
    'Región Metropolitana de Santiago': 'Metropolitana',
    "Región del Libertador Bernardo O'Higgins": "O'Higgins", 'Región del Maule': 'Maule',
    'Región de Ñuble': 'Ñuble', 'Región del Biobío': 'Biobío', 'Región de La Araucanía': 'La Araucanía',
    'Región de Los Ríos': 'Los Ríos', 'Región de Los Lagos': 'Los Lagos',
    'Región de Aysén del Gral.Ibañez del Campo': 'Aysén',
    'Región de Magallanes y Antártica Chilena': 'Magallanes',
}
FAMILY_SHORT_NAMES = {'Carne de Cerdo - Ave - Cordero': 'Cerdo · Ave · Cordero',
                      'Lácteos - Huevos - Margarinas': 'Lácteos · Huevos · Margarinas'}
# Map drawing, in SVG units: the country on the left, one row per region on the right.
MAP_VIEW = (318, 620)
MAP_BOX = (6, 8, 612)          # left edge, top and bottom of the country
LIST_LEFT, LIST_RIGHT = 142, 314
STATE_WORDS = {'rise': 'subieron', 'fall': 'bajaron', 'neutral': 'quedaron sin cambio',
               'mixed': 'no tienen una dirección clara (subidas y bajadas parejas)', 'missing': 'no tienen comparación'}
STATE_SYMBOLS = {'rise': '↑', 'fall': '↓', 'neutral': '=', 'mixed': '=', 'missing': ''}


def short_region(region):
    return REGION_SHORT_NAMES.get(region, str(region).replace('Región de ', '').replace('Región del ', ''))


def short_family(family):
    return FAMILY_SHORT_NAMES.get(family, family)


def real_projection(geometry):
    """Equirectangular projection corrected by the cosine of the mean latitude: Chile
    keeps its real proportions, so its shape is the one people know."""
    points = [point for feature in geometry['features'] for point in _geometry_points(feature['geometry'])]
    west, east = min(p[0] for p in points), max(p[0] for p in points)
    south, north = min(p[1] for p in points), max(p[1] for p in points)
    left, top, bottom = MAP_BOX
    scale = (bottom - top) / (north - south)
    aspect = math.cos(math.radians((north + south) / 2))
    def project(lon, lat):
        return left + (lon - west) * aspect * scale, top + (north - lat) * scale
    return project, left + (east - west) * aspect * scale


def _inside_rings(x, y, rings):
    inside = False
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def region_anchor(rings, y):
    """A point certainly inside the region: middle of its widest stretch at height y."""
    for offset in (0, 1.5, -1.5, 3, -3, 5, -5, 8, -8):
        line = y + offset
        crossings = sorted(x1 + (line - y1) * (x2 - x1) / (y2 - y1)
                           for ring in rings for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])
                           if (y1 - line) * (y2 - line) < 0)
        stretches = [(a, b) for a, b in zip(crossings[::2], crossings[1::2]) if b > a]
        if stretches:
            left, right = max(stretches, key=lambda pair: pair[1] - pair[0])
            if _inside_rings((left + right) / 2, line, rings):
                return (left + right) / 2, line
    xs, ys = [x for ring in rings for x, _ in ring], [y for ring in rings for _, y in ring]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def region_layout(geometry):
    """For each region, north to south: its SVG path, its anchor and its row height."""
    project, _ = real_projection(geometry)
    regions = []
    for feature in geometry['features']:
        coordinates = feature['geometry']['coordinates']
        polygons = coordinates if feature['geometry']['type'] == 'MultiPolygon' else [coordinates]
        rings = [[project(lon, lat) for lon, lat in ring] for polygon in polygons for ring in polygon
                 if len(ring) >= 3]
        largest = max(rings, key=len)
        _, centre_y = _ring_centroid(largest)
        anchor = region_anchor(rings, centre_y)
        path = ''.join('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in ring) + 'Z' for ring in rings)
        regions.append({'region': feature['properties']['region'], 'path': path, 'rings': rings,
                        'anchor': anchor})
    regions.sort(key=lambda item: item['anchor'][1])
    _, top, bottom = MAP_BOX
    step = (bottom - top - 12) / (len(regions) - 1)
    for index, item in enumerate(regions):
        item['row'] = top + 6 + index * step
    return regions


def regional_map(rows, region_link, week_label, previous_label, selected_region=None):
    """Chile in real proportions; a line from a dot inside each region to its row.

    The badge is the share of comparable price series in the dominant direction,
    never a price average, consumption basket, or inflation estimate.
    """
    indexed = {str(row['region']): row for row in rows}
    shapes, rows_markup = [], []
    width, height = MAP_VIEW
    for item in region_layout(chile_regions_geometry()):
        region = item['region']
        row = indexed.get(region, {'state': 'missing', 'share': None, 'up': 0,
                                   'down': 0, 'stable': 0, 'total': 0, 'missing': 0})
        state = row.get('state', 'missing')
        share = row.get('share')
        if state == 'missing':
            summary = 'Sin precios comparables entre ambas semanas.'
        elif state == 'mixed':
            summary = 'Sin dirección clara: subidas y bajadas no se distinguen del azar.'
        else:
            summary = f'{number(share)} % de los precios comparables {STATE_WORDS[state]}.'
        detail = (f'{row.get("down", 0)} bajaron · {row.get("up", 0)} subieron · '
                  f'{row.get("stable", 0)} sin cambio · {row.get("total", 0)} comparados')
        selected = region == selected_region
        hint = (f'{region}\n{summary}\n{detail}\nSemana {previous_label} → {week_label}\n'
                + ('Volver a todo Chile' if selected else 'Ver las familias de esta región'))
        css = state + (' selected' if selected else '')
        href = esc(region_link(None if selected else region))
        ax, ay = item['anchor']
        y = item['row']
        badge = ('<text class="mock-region-empty" x="{0}" y="{1:.1f}" text-anchor="end">sin dato</text>'
                 .format(LIST_RIGHT - 4, y + 4) if share is None else
                 f'<rect class="mock-region-pill {state}" x="{LIST_RIGHT - 46}" y="{y - 9:.1f}" width="46" height="18" rx="4"/>'
                 f'<text class="mock-region-pill-text" x="{LIST_RIGHT - 23}" y="{y + 4:.1f}" text-anchor="middle">'
                 f'{number(share)} % {STATE_SYMBOLS[state]}</text>')
        shapes.append(f'<a href="{href}" target="_self" aria-label="{esc(hint)}"><path class="mock-region-shape {css}" '
                      f'd="{item["path"]}"><title>{esc(hint)}</title></path></a>')
        rows_markup.append(
            f'<a class="mock-region-row {css}" href="{href}" target="_self" aria-label="{esc(hint)}"><title>{esc(hint)}</title>'
            f'<rect class="mock-region-hit" x="{LIST_LEFT - 4}" y="{y - 12:.1f}" width="{LIST_RIGHT - LIST_LEFT + 8}" height="24" rx="6"/>'
            f'<path class="mock-region-leader" d="M{ax:.1f},{ay:.1f}L{LIST_LEFT - 8},{y:.1f}"/>'
            f'<circle class="mock-region-dot" cx="{ax:.1f}" cy="{ay:.1f}" r="2.2"/>'
            f'<text class="mock-region-name" x="{LIST_LEFT + 2}" y="{y + 4:.1f}">{esc(short_region(region))}</text>'
            + badge + '</a>')
    legend = ('<span><i class="rise"></i>Subieron</span><span><i class="fall"></i>Bajaron</span>'
              '<span><i class="neutral"></i>Sin dato o sin dirección clara</span>')
    return ('<section class="mock-regional" id="pulso-regional"><span class="mock-kicker">Lectura territorial</span>'
            '<h2>¿En qué dirección se movieron los precios?</h2>'
            '<p>% de precios comparables que siguió la dirección dominante. Mapa en proporción real; '
            'cada región se lee en su fila.</p>'
            f'<div class="mock-regional-legend">{legend}</div>'
            f'<svg class="mock-chile-map" preserveAspectRatio="xMidYMin meet" viewBox="0 0 {width} {height}" role="img" '
            'aria-label="Mapa de Chile con la dirección dominante de los precios por región">'
            '<g class="mock-region-land">' + ''.join(shapes) + '</g>'
            '<g class="mock-region-rows">' + ''.join(rows_markup) + '</g></svg></section>')


def family_averages(rows):
    """[(family, typical change, rows)], highest rise first, from comparable series only.

    The typical change is the median (D-146): a few thin series moving ±50 % pulled
    the mean far from what most products did (Frutas: mean +1,7 %, median +0,02 %).
    """
    groups = {}
    for row in rows:
        value = row.get('variation')
        if value is not None and math.isfinite(float(value)):
            groups.setdefault(str(row.get('product_group') or 'Sin grupo'), []).append(row)
    summary = [(group, statistics.median(float(r['variation']) for r in members), members)
               for group, members in groups.items()]
    return sorted(summary, key=lambda item: (-item[1], item[0]))


def change_state(value):
    """A change that rounds to 0.0 % is neither a rise nor a fall."""
    return 'neutral' if abs(value) < .0005 else 'rise' if value > 0 else 'fall'


def dashboard_header(week_label, updated, loaded, family_rows, regional_rows, region,
                     compared=None, available=None, alerts=None):
    """Title, then four KPI tiles of equal width (D-150): every figure comes from the
    same weekly model the charts below use, so the strip and the charts agree."""
    states = [change_state(average) for _, average, _ in family_averages(family_rows)]
    regions = [row.get('state') for row in regional_rows]
    rise, fall, mixed = regions.count('rise'), regions.count('fall'), regions.count('mixed')
    missing = len(REGION_SHORT_NAMES) - rise - fall - mixed
    tiles = [('Precios comparados', f'{number(compared)} <small>de {number(available)}</small>'
              if compared is not None else '—', 'con precio en ambas semanas'),
             ('Familias', f'<b class="rise">{states.count("rise")} ↑</b> · <b class="fall">{states.count("fall")} ↓</b>'
                          f' · {states.count("neutral")} =', 'variación típica (mediana)'),
             ('Regiones', f'<b class="rise">{rise} ↑</b> · <b class="fall">{fall} ↓</b>',
              f'{mixed} sin dirección clara · {missing} sin dato'),
             ('Alertas de precio', f'<b class="alert">{number(alerts)}</b>' if alerts is not None else '—',
              'inusuales y de al menos 10 %')]
    place = esc(short_region(region) if region else 'Todo Chile')
    return ('<header class="mock-intro"><div><h1>¿Qué familias de alimentos subieron y bajaron?</h1>'
            f'<p>Variación típica (mediana) por familia frente a la semana anterior · semana {esc(week_label)} · {place}</p></div>'
            '<div class="mock-head-side"><span class="mock-updated"><i class="'
            + ('loaded' if loaded else 'failed') + f'"></i>{"Actualizado" if loaded else "Carga con falla"} {esc(updated)}</span>'
            '</div></header><div class="mock-kpis">'
            + ''.join(f'<div class="mock-kpi"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>'
                      for label, value, note in tiles)
            + '</div>')


def family_movement(rows, family_link, selected_family, scope):
    """One clickable row per family: a diverging bar from zero, its change and its state."""
    summary = family_averages(rows)
    if not summary:
        return '<section class="mock-movement"><h2>Movimiento por familia</h2><p class="mock-empty">Sin precios comparables para esta selección.</p></section>'
    limit = max(1, math.ceil(max(abs(average) for _, average, _ in summary) * 100))
    markup = []
    for group, average, members in summary:
        state = change_state(average)
        word = {'rise': 'Subió', 'fall': 'Bajó', 'neutral': 'Sin cambio'}[state]
        size = min(50, abs(average) * 100 / limit * 50)
        side = 'left:50%' if average >= 0 else f'left:{50 - size:.2f}%'
        selected = ' selected' if group == selected_family else ''
        markup.append(
            f'<a class="mock-movement-row {state}{selected}" href="{esc(family_link(group))}" target="_self"'
            f' title="{esc(group)}: mediana de {len(members)} precios comparables · {esc(scope)}">'
            f'{family_art(group, "mock-movement-art")}<strong>{esc(short_family(group))}</strong>'
            f'<span class="mock-movement-track"><span class="mock-movement-bar" style="{side};width:{size:.2f}%"></span></span>'
            f'<b class="mock-movement-value">{"0,0 %" if state == "neutral" else percent(average * 100, True)}</b>'
            f'<span class="mock-movement-state">{word}</span><span class="mock-movement-chevron">›</span></a>')
    return ('<section class="mock-movement"><div class="mock-movement-heading"><div><h2>Movimiento por familia</h2>'
            f'<p>Mediana de las variaciones de precios comparables: lo que hizo el producto típico · {esc(scope)}. Selecciona una familia para ver sus productos.</p></div>'
            '</div><div class="mock-movement-row mock-movement-axis" aria-hidden="true"><i></i><span></span>'
            f'<span class="mock-movement-scale"><span>−{limit} %</span><span>0</span><span>+{limit} %</span></span>'
            '<span></span><span></span><span></span></div>'
            + ''.join(markup) + '</section>')


def products_heading(family, average, scope, shown=None, total=None):
    state = change_state(average) if average is not None else 'neutral'
    chip = '' if average is None else f'<span class="mock-products-chip {state}">{percent(average * 100, True)} mediana</span>'
    count = ('' if total is None else f'<span class="mock-products-count">{number(shown)} de {number(total)} precios</span>'
             if shown != total else f'<span class="mock-products-count">{number(total)} precios</span>')
    return (f'<div class="mock-products-heading"><h2>Productos · {esc(short_family(family))}</h2>{chip}'
            f'<span class="mock-products-scope">en {esc(scope)}</span>{count}</div>')


def products_table(rows, week_label, previous_label, query=''):
    """The comparable prices of one family; the last column counts regions up and down."""
    body = []
    for row in rows:
        change = row['variation'] * 100
        state = change_state(row['variation'])
        regions = row.get('_regions')
        regions_text = '—' if not regions else f'<b class="rise">{regions[0]} ↑</b> / <b class="fall">{regions[1]} ↓</b>'
        body.append('<tr>'
                    f'<td><strong>{esc(product_label(row))}</strong>'
                    + (f'<small>{esc(row["quality"])} · $/{esc(row["normalized_unit"])}'
                       + (' · 1 cotización' if row.get('_single_quote') else '')
                       + (f' · variación sobre {int(row["_same_regions"])} regiones comunes'
                          if row.get('_coverage_changed') and row.get('_same_regions') == row.get('_same_regions') else '')
                       + '</small>' if row.get('quality') else '')
                    + f'</td><td>{esc(row["channel"])}</td>'
                    f'<td class="num">{money(previous_price(row))}</td><td class="num">{money(row["national_price"])}</td>'
                    f'<td class="num {state}"><b>{"0,0 %" if state == "neutral" else percent(change, True)}</b></td>'
                    f'<td class="num">{regions_text}</td></tr>')
    if not body:
        empty = (f'Ningún producto empieza por «{esc(query)}» en esta familia.' if query else
                 'No hay productos con precio en ambas semanas para esta selección.')
        body = [f'<tr><td colspan="7" class="mock-empty">{empty}</td></tr>']
    return ('<div class="mock-products-table" role="region" tabindex="0" aria-label="Productos de la familia"><table><thead><tr>'
            f'<th>Producto</th><th>Canal</th><th class="num">Precio {esc(previous_label[:5])}</th>'
            f'<th class="num">Precio {esc(week_label[:5])}</th><th class="num">Variación</th>'
            '<th class="num" title="Regiones donde el mismo producto y canal subió / bajó">Regiones ↑ / ↓</th></tr></thead>'
            '<tbody>' + ''.join(body) + '</tbody></table></div>')


def coverage_note(model, quality_link, methodology_link, family=None):
    """What the figures cover, in one line under the table, with its two references.
    The first figures are those of the family the table shows, so «288 precios» above
    and the note below count the same rows; the whole week follows for scale."""
    links = (f'<a href="{esc(quality_link)}" target="_self">Calidad</a> · '
             f'<a href="{esc(methodology_link)}" target="_self">Metodología</a>')
    total_missing = number(model["missing"])
    week = (f'Toda la semana, {len(model.get("family_coverage", {})) or "todas las"} familias: '
            f'{number(model["available"])} precios, {total_missing} sin comparación válida.')
    stats = model.get('family_coverage', {}).get(family)
    if stats and model['national']:
        detail = (f'<strong>Cobertura · {esc(short_family(family))}:</strong> {number(stats["available"])} precios '
                  f'esta semana; {number(stats["comparable"])} con comparación válida, los de la tabla. '
                  f'Cada variación compara las mismas regiones en ambas semanas; en {number(stats["coverage_changed"])} '
                  f'se dejaron fuera regiones con precio en una sola. {number(stats["single_quote"])} cambios apoyados '
                  'en una sola cotización van al final del orden con la marca «1 cotización». ')
    else:
        coverage = ('Cada variación nacional compara las mismas regiones en ambas semanas; '
                    f'en {model["coverage_changed"]} se dejaron fuera regiones con precio en una sola. '
                    f'{model.get("single_quote", 0)} cambios apoyados en una sola cotización van al final del orden y llevan la marca «1 cotización».' if model['national'] else
                    'Comparación de la misma región, producto, variedad, calidad, unidad y canal.')
        detail = (f'<strong>Cobertura:</strong> {number(model["available"])} precios disponibles · '
                  f'{total_missing} sin comparación válida. {esc(coverage)} ')
        week = ''
    return (f'<p class="mock-coverage-note">{detail}{esc(week)} '
            f'Precios nominales de ODEPA, redondeados; cambios calculados antes de redondear. {links}</p>')


def history_chart(rows, subtitle, scope, history_link):
    """Exact weekly points; gaps split paths. No smoothing or fabricated values."""
    import pandas as pd
    data=rows.dropna(subset=['national_price']).sort_values('week_start')
    if data.empty:
        graphic='<p class="mock-empty">No hay historia comparable para esta selección.</p>'
    else:
        width,height=520,168
        left,right,top,bottom=49,14,16,30
        start,end=data.week_start.min(),data.week_start.max()
        days=max((end-start).days,7)
        low,high=float(data.national_price.min()),float(data.national_price.max())
        span=max(high-low,high*.1,1)
        low=max(0,math.floor((low-span*.2)/100)*100)
        high=math.ceil((high+span*.2)/100)*100
        span=max(high-low,1)
        x=lambda day:left+(day-start).days/days*(width-left-right)
        y=lambda price:top+(high-price)/span*(height-top-bottom)
        svg=[f'<svg class="mock-history-svg" viewBox="0 0 {width} {height}" role="img" aria-label="Evolución semanal del precio; los cortes indican semanas sin dato">']
        for tick in (low,(low+high)/2,high):
            yy=y(tick)
            svg.append(f'<path d="M{left} {yy}H{width-right}" class="mock-grid-line"/><text x="{left-9}" y="{yy+4}" text-anchor="end" class="mock-axis">{number(tick)}</text>')
        segments=[];segment=[];last=None
        for row in data.to_dict('records'):
            if last is not None and (row['week_start']-last).days!=7:
                segments.append(segment);segment=[]
            segment.append((x(row['week_start']),y(row['national_price']),row))
            last=row['week_start']
        if segment:segments.append(segment)
        for seg in segments:
            coords=' '.join(f'{xx:.2f},{yy:.2f}' for xx,yy,_ in seg)
            svg.append(f'<polygon points="{seg[0][0]},{height-bottom} {coords} {seg[-1][0]},{height-bottom}" fill="{BLUE}" opacity=".11"/>')
            svg.append(f'<polyline points="{coords}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
            for xx,yy,row in seg:
                svg.append(f'<circle cx="{xx}" cy="{yy}" r="3" fill="{BLUE}"><title>{row["week_start"]:%d-%m-%Y}: ${number(row["national_price"])}</title></circle>')
        for day in [start]+[t for t in pd.date_range(start,end,freq='MS') if (t-start).days>7]:
            svg.append(f'<text x="{x(day)}" y="{height-7}" text-anchor="middle" class="mock-axis">'+['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'][day.month-1]+'</text>')
        last=data.iloc[-1]
        svg.append(f'<circle cx="{x(last.week_start)}" cy="{y(last.national_price)}" r="6" fill="{BLUE}" stroke="white" stroke-width="2"/>')
        svg.append(f'<text x="{width-right}" y="{max(12,y(last.national_price)-15)}" text-anchor="end" class="mock-last-price">${number(last.national_price)}</text></svg>')
        graphic=''.join(svg)
    return ('<section class="mock-history"><h3>Evolución · últimas 12 semanas</h3>'
            f'<p class="mock-panel-subtitle mock-history-title">{esc(subtitle)}</p>'+graphic+
            f'<p class="mock-history-note">Últimas 12 semanas · {esc(scope)}</p></section>')


def family_table_rows(rows, order):
    """The rows eligible for one family's table under the selected ranking."""
    if order == 'Subidas':
        return [row for row in rows if row['variation'] >= .0005]
    if order == 'Bajadas':
        return [row for row in rows if row['variation'] <= -.0005]
    if order == 'Inusuales':
        return [row for row in rows if row.get('is_alert')]
    return list(rows)


def family_table_limit(rows, order):
    """Largest family table available under the current filters and order."""
    groups = {}
    for row in rows:
        groups.setdefault(str(row['product_group']), []).append(row)
    return max((len(family_table_rows(group_rows, order)) for group_rows in groups.values()), default=0)


def family_tables(model, count, order):
    """Collapsed family tables with genuine comparable series."""
    groups = {}
    for row in model['family_rows']:
        groups.setdefault(str(row['product_group']), []).append(row)
    ranked_groups = sorted(groups, key=lambda group: (-sum(r['variation'] for r in groups[group]) / len(groups[group]), group))
    sections = []
    for group in ranked_groups:
        rows = family_table_rows(groups[group], order)
        rows = sorted(rows, key=lambda row: (-abs(row['variation']), str(row['product']), str(row['channel'])))
        body = []
        for row_number, row in enumerate(rows[:count], start=1):
            change = row['variation'] * 100
            state = 'neutral' if abs(change) < .05 else 'rise' if change > 0 else 'fall'
            word = {'rise': 'Subió', 'fall': 'Bajó', 'neutral': 'Sin cambio'}[state]
            displayed_change = '0,0 %' if state == 'neutral' else percent(change, True)
            body.append('<tr>'
                        f'<td class="mock-row-number">{row_number}</td>'
                        f'<td><strong>{esc(row["product"])}</strong></td>'
                        f'<td>{esc(row["variety"])}</td><td>{esc(row["quality"])}</td>'
                        f'<td>$/{esc(row["normalized_unit"])}</td><td>{esc(row["channel"])}</td>'
                        f'<td>{money(previous_price(row))}</td><td>{money(row["national_price"])}</td>'
                        f'<td class="{state}"><strong>{displayed_change}</strong></td>'
                        f'<td class="{state}">{word}</td></tr>')
        note = f'Mostrando {min(count, len(rows))} de {len(rows)} precios con datos en ambas semanas'
        sections.append(f'<details class="mock-family-detail" name="family-prices" id="{family_anchor(group)}">'
                        f'<summary><strong>{esc(group)}</strong><span>{note}</span></summary>'
                        '<div class="mock-family-table-scroll" role="region" tabindex="0"'
                        f' aria-label="Precios de {esc(group)}"><table><thead><tr>'
                        '<th scope="col" class="mock-row-number">N.º</th>'
                        '<th>Producto</th><th>Variedad o corte</th><th>Calidad</th><th>Unidad</th>'
                        f'<th>Canal</th><th>Anterior · {esc(model["previous_label"])}</th>'
                        f'<th>Actual · {esc(model["week_label"])}</th><th>Cambio</th><th>Estado</th>'
                        '</tr></thead><tbody>' + (''.join(body) or '<tr><td colspan="10">No hay productos para este orden.</td></tr>')
                        + '</tbody></table></div></details>')
    title = 'Detalle del producto' if model.get('product_filter') else 'Productos por familia'
    return (f'<section class="mock-family-tables"><h2>{title}</h2>'
            '<p>Abre una familia para ver sus alimentos, sus precios y cuánto cambiaron.</p>'
            + (''.join(sections) or '<p class="mock-empty">No hay productos con precio en ambas semanas para estos filtros.</p>') + '</section>')


def panels(model, scope, focus_link, data_link, history_link, order, count, quality_link, methodology_link):
    coverage=('Cada variación nacional compara las mismas regiones en ambas semanas; '
              f'en {model["coverage_changed"]} se dejaron fuera regiones con precio en una sola. '
              f'{model.get("single_quote", 0)} cambios apoyados en una sola cotización van al final del orden y llevan la marca «1 cotización».'
              if model['national'] else 'Comparación de la misma región, producto, variedad, calidad, unidad y canal.')
    return (family_tables(model,count,order)+
            f'<footer class="mock-footer"><span><strong>Cobertura:</strong> {model["available"]} precios disponibles · {model["missing"]} sin comparación válida. {esc(coverage)}</span>'
            f'<span>Fuente: ODEPA · precios nominales · valores redondeados; cambios calculados antes de redondear. '
            f'<a href="{esc(quality_link)}" target="_self">Calidad</a> · <a href="{esc(methodology_link)}" target="_self">Metodología</a></span></footer>')
