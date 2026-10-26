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
                      'Lácteos - Huevos - Margarinas': 'Lácteos y huevos'}  # D-301: 33 of its 34 products are dairy or eggs
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
    for number_of, item in enumerate(region_layout(chile_regions_geometry())):
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
                      f'd="{item["path"]}" data-r="{number_of}"><title>{esc(hint)}</title></path></a>')
        rows_markup.append(
            f'<a class="mock-region-row {css}" href="{href}" data-r="{number_of}" target="_self" aria-label="{esc(hint)}"><title>{esc(hint)}</title>'
            f'<rect class="mock-region-hit" x="{LIST_LEFT - 4}" y="{y - 12:.1f}" width="{LIST_RIGHT - LIST_LEFT + 8}" height="24" rx="6"/>'
            f'<path class="mock-region-leader" d="M{ax:.1f},{ay:.1f}L{LIST_LEFT - 8},{y:.1f}"/>'
            f'<circle class="mock-region-dot" cx="{ax:.1f}" cy="{ay:.1f}" r="2.2"/>'
            f'<text class="mock-region-name" x="{LIST_LEFT + 2}" y="{y + 4:.1f}">{esc(short_region(region))}</text>'
            + badge + '</a>')
    legend = ('<span><i class="rise"></i>Subieron</span><span><i class="fall"></i>Bajaron</span>'
              '<span><i class="neutral"></i>Sin cambio claro</span><span><i class="nodata"></i>Sin dato</span>')
    scope = (f'Viendo: <b>{esc(short_region(selected_region))}</b> · <a href="{esc(region_link(None))}" target="_self">Ver todo Chile</a>'
             if selected_region else 'Viendo: <b>todo Chile</b> · clic en una región para ver solo esa')
    return ('<section class="mock-regional" id="pulso-regional"><span class="mock-kicker">Precios por región</span>'
            f'<p class="mock-scope">{scope}</p>'
            '<h2>¿Hacia dónde se movieron los precios?</h2>'
            '<p>% de precios comparables que siguió la dirección dominante. Mapa en proporción real; '
            'cada región se lee en su fila.</p>'
            f'<div class="mock-regional-legend">{legend}</div>'
            f'<svg class="mock-chile-map" preserveAspectRatio="xMidYMin meet" viewBox="0 0 {width} {height}" role="img" '
            'aria-label="Mapa de Chile con la dirección dominante de los precios por región">'
            '<defs><pattern id="mock-nodata" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="5" height="5" fill="#e3e8ee"/><rect width="1.1" height="5" fill="#b9c2ce"/></pattern></defs>'
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


QUESTION = '¿Qué familias de alimentos subieron y bajaron?'


def dashboard_bar(path, week_label, family_rows, regional_rows, region, compared=None, available=None):
    """The Resumen's only header (D-264): one thin bar with the path, the question and the week's figures as chips.
    Every figure comes from the same weekly model the charts below use; each chip says in full what it counts on hover.
    The «Volver» and price-alert buttons and the time of the load are Streamlit elements beside it."""
    place = short_region(region) if region else 'Todo Chile'
    section, _, page = path.rpartition(' › ')
    chips = [
        (f'Semana {week_label} · {place}',
         esc(week_label.rsplit(' ', 1)[0]) + (f' · {esc(place)}' if region else '')),
    ]  # D-316: the header keeps the essentials; the family and region counts live in their own panels
    question = (f'{QUESTION} Variación típica (mediana) por familia frente a la semana anterior · '
                f'semana {week_label} · {place}')
    return ('<div class="greenocean-mockup home-bar-main">'
            + (f'<span class="home-bar-path">{esc(section)} › <b>{esc(page)}</b></span>' if section
               else f'<span class="home-bar-path"><b>{esc(page)}</b></span>')
            # The page's heading stays for readers of screens and for the tests, but it takes no room in the bar (D-316).
            + f'<span class="home-bar-title" role="heading" aria-level="1" title="{esc(question)}">{esc(QUESTION)}</span>'
            + ''.join(f'<span class="home-chip" title="{esc(note)}">{value}</span>' for note, value in chips)
            + '</div>')


def dashboard_updated(updated, loaded):
    """The time of the latest load, at the end of the bar: a green dot, or red when it failed."""
    state = 'Actualizado' if loaded else 'Carga con falla'
    return (f'<span class="home-bar-updated" title="{state} {esc(updated)}"><i class="{"loaded" if loaded else "failed"}"></i>'
            f'{esc(updated)}</span>')


def family_movement(rows, family_link, selected_family, scope):
    """One clickable row per family: a diverging bar from zero, its change and its state."""
    summary = family_averages(rows)
    if not summary:
        return '<section class="mock-movement"><span class="mock-kicker">Variación por familia</span><h2>¿Qué familias subieron y cuáles bajaron?</h2><p class="mock-empty">Sin precios comparables para esta selección.</p></section>'
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
    place = scope[0].upper() + scope[1:]
    return ('<section class="mock-movement"><div class="mock-movement-heading"><div><span class="mock-kicker">Variación por familia</span><h2>¿Qué familias subieron y cuáles bajaron?</h2>'
            f'<p>Mediana de variaciones de precios comparables, {esc(scope)}.</p></div>'
            f'<span class="mock-place">Región: <b>{esc(place)}</b></span>'
            '</div><div class="mock-movement-row mock-movement-axis" aria-hidden="true"><i></i><span></span>'
            f'<span class="mock-movement-scale"><span>−{limit} %</span><span>0</span><span>+{limit} %</span></span>'
            '<span></span><span></span><span></span></div>'
            + ''.join(markup) + '</section>')


def products_heading(family, average, scope, shown=None, total=None):
    state = change_state(average) if average is not None else 'neutral'
    chip = '' if average is None else f'<span class="mock-products-chip {state}">{percent(average * 100, True)} mediana</span>'
    count = ('' if total is None else f'<span class="mock-products-count">{number(shown)} de {number(total)} precios</span>'
             if shown != total else f'<span class="mock-products-count">{number(total)} precios</span>')
    return (f'<div class="mock-products-heading"><div class="mock-products-top"><span class="mock-kicker">Detalle de productos</span>'
            f'<span class="mock-products-family">{esc(short_family(family))}</span></div>'
            f'<h2>¿Qué productos explican el cambio?</h2>{chip}'
            f'<span class="mock-products-scope">en {esc(scope)}</span>{count}</div>')


def products_table(rows, week_label, previous_label, query='', selected=None):
    """The comparable prices of one family; the last column counts regions up and down."""
    body = []
    for row in rows:
        change = row['variation'] * 100
        state = change_state(row['variation'])
        regions = row.get('_regions')
        regions_text = '—' if not regions else f'<b class="rise">{regions[0]} ↑</b> / <b class="fall">{regions[1]} ↓</b>'
        if regions and len(regions) > 2 and regions[2]:
            # D-304: which regions, in a box that opens at once on hover; the region chosen on the map comes marked.
            items = ''.join(
                f'<li class="{"rise" if change >= .05 else "fall" if change <= -.05 else ""}'
                f'{" chosen" if selected and region == short_region(selected) else ""}">'
                f'<span>{esc(region)}</span><b>{percent(change, True)}</b></li>' for region, change in regions[2])
            regions_text = f'<span class="mock-regions" tabindex="0">{regions_text}<ul class="mock-regions-tip">{items}</ul></span>'
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
            '<th class="num" title="Regiones donde el mismo producto y canal subió / bajó; haz clic en el conteo para ver cuáles">Regiones ↑ / ↓ · clic</th></tr></thead>'
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


def family_table_rows(rows, order):
    """The rows eligible for one family's table under the selected ranking."""
    if order == 'Subidas':
        return [row for row in rows if row['variation'] >= .0005]
    if order == 'Bajadas':
        return [row for row in rows if row['variation'] <= -.0005]
    if order == 'Inusuales':
        return [row for row in rows if row.get('is_alert')]
    return list(rows)


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
