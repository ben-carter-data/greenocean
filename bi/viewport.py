"""Viewport layout shared by every page; no browser measurement or zoom."""
from pathlib import Path
import re


def css():
    return '<style>' + Path(__file__).with_suffix('.css').read_text() + '</style>'


def frame(source, kind="diagram"):
    """Give a trusted embedded document the height of its iframe's grid cell."""
    source = contain_svg(source)
    style = Path(__file__).with_name('viewport_frames.css').read_text()
    geometry = re.search(r'<div class="(stage|oc-stage)"[^>]*>\s*<svg[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"', source)
    if geometry and kind == "diagram":
        stage, width, height = geometry.groups()
        ratio = float(width) / float(height)
        style += f"""
body[data-viewport] {{ --legend-room:0px; }}
body[data-viewport]:has(> .legend) {{ --legend-room:36px; }}
body[data-viewport] .{stage} {{ width:min(100vw,calc((100vh - var(--legend-room)) * {ratio}));
  height:auto; max-height:100%; aspect-ratio:{width}/{height}; justify-self:center; align-self:center;
  container-type:inline-size; }}
body[data-viewport] .stage .node {{ width:clamp(76px,15cqw,156px);margin-left:calc(clamp(76px,15cqw,156px) / -2); }}
body[data-viewport] .stage .file {{ max-width:100%;white-space:normal;overflow-wrap:anywhere;font-size:11px; }}
"""
    return source.replace('</head>', f'<style>{style}</style></head>').replace('<body', f'<body data-viewport="{kind}"', 1)


def contain_svg(source):
    """Declare the SVG fit contract without altering its geometry or labels."""
    return re.sub(r"<svg\b[^>]*>", lambda match: match[0] if 'viewBox=' not in match[0]
                  or 'preserveAspectRatio=' in match[0] else match[0][:-1] + ' preserveAspectRatio="xMidYMid meet">', source)


def pipeline_overview(states, figures, mode):
    """Nine readable stops in a serpentine SVG; full engineering details stay in the focused view."""
    import html
    from bi import charts, architecture
    p = charts.get_palette(mode)
    stages = [
        ('Fuentes', 'ODEPA e INE', 'Precios e IPC', 'sources'),
        ('Ingesta', 'Python · HTTPS', figures['last_run'], 'download'),
        ('Aterrizaje', 'SQLite · raw.db', 'Archivos originales', 'download'),
        ('Bronce', 'Parquet', 'Copia de las fuentes', 'etl'),
        ('Staging', 'dbt · tipos y textos', 'Reglas de entrada', 'etl'),
        ('Intermedio', 'dbt · reglas de negocio', 'Unidades y semanas', 'etl'),
        ('Marts y pruebas', 'Modelo estrella e IPC', 'Publicación validada', 'load'),
        ('Base de servicio', 'datos.duckdb', figures['weekly_prices'], 'load'),
        ('Consumo', 'Streamlit · SQL · GitHub', 'Panel e informe semanal', 'panel'),
    ]
    points = [(166,70),(500,70),(834,70),(834,210),(500,210),(166,210),(166,350),(500,350),(834,350)]
    parts = [f'<svg width="100%" height="100%" viewBox="0 0 1000 420" preserveAspectRatio="xMidYMid meet" role="img" '
             'aria-label="Recorrido de los datos de ODEPA al panel">',
             f'<defs><marker id="overview-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10" fill="{p["accent"]}"/></marker></defs>']
    for (x,y),(xx,yy) in zip(points, points[1:]):
        dx,dy = (1 if xx>x else -1 if xx<x else 0),(1 if yy>y else 0)
        parts.append(f'<path d="M{x+dx*153} {y+dy*48}L{xx-dx*157} {yy-dy*52}" '
                     f'stroke="{p["accent"]}" stroke-width="2" marker-end="url(#overview-arrow)"/>')
    for number, ((title, line, detail, state),(x,y)) in enumerate(zip(stages,points),1):
        color = architecture.STATE_COLORS.get(states.get(state), p['reference'])
        parts.append(f'<g><title>{html.escape(title+": "+line+" · "+detail)}</title>'
                     f'<rect x="{x-153}" y="{y-48}" width="306" height="96" rx="14" fill="{p["card"]}" stroke="{p["card_border"]}"/>'
                     f'<circle cx="{x-132}" cy="{y-26}" r="5" fill="{color}"/>'
                     f'<text x="{x}" y="{y-25}" text-anchor="middle" fill="{p["strong_text"]}" font-size="24" font-weight="600">{number} · {html.escape(title)}</text>'
                     f'<text x="{x}" y="{y+5}" text-anchor="middle" fill="{p["text"]}" font-size="24">{html.escape(line)}</text>'
                     f'<text x="{x}" y="{y+34}" text-anchor="middle" fill="{p["reference"]}" font-size="24">{html.escape(detail)}</text></g>')
    return ''.join(parts)+'</svg>'


def platform_overview(mode, label="Despliegue de GreenOcean"):
    """Deployment responsibilities in four readable cells, for the document panel."""
    import html
    from bi import charts
    p = charts.get_palette(mode)
    cells = [('Fuentes públicas', 'ODEPA: precios · INE: IPC', 250, 100),
             ('GitHub Actions', 'Ingesta · dbt · pytest', 750, 100),
             ('Repositorio', 'Código · Parquet · datos.duckdb', 250, 310),
             ('Streamlit Cloud', 'Panel público de solo lectura', 750, 310)]
    parts = [f'<svg width="100%" height="100%" viewBox="0 0 1000 420" preserveAspectRatio="xMidYMid meet" role="img" aria-label="{html.escape(label)}">']
    for title, line, x, y in cells:
        parts.append(f'<rect x="{x-230}" y="{y-72}" width="460" height="144" rx="14" fill="{p["card"]}" stroke="{p["card_border"]}"/>'
                     f'<text x="{x}" y="{y-10}" text-anchor="middle" font-size="28" fill="{p["strong_text"]}">{html.escape(title)}</text>'
                     f'<text x="{x}" y="{y+30}" text-anchor="middle" font-size="24" fill="{p["text"]}">{html.escape(line)}</text>')
    parts.append(f'<path d="M480 100H520M750 172V238M520 310H480M250 238V172" stroke="{p["accent"]}" stroke-width="3" fill="none"/>')
    return ''.join(parts)+'</svg>'


def model_overview(row_counts, mode, label='Modelo de datos'):
    """Actual model relationships; column lists live in an adjacent scroll panel."""
    import html
    from bi import charts, er_diagram
    p = charts.get_palette(mode)
    names = ['dim_product','dim_date','dim_region','dim_channel','weekly_price','ipc_monthly','etl_run','rejection','ipc_weekly']
    positions = {name:(166+334*(i%3),70+140*(i//3)) for i,name in enumerate(names)}
    parts = [f'<svg width="100%" height="100%" viewBox="0 0 1000 420" preserveAspectRatio="xMidYMid meet" role="img" aria-label="{html.escape(label)}">']
    for child, _, parent, *_ in er_diagram.RELATIONS:
        x,y = positions[child]; xx,yy=positions[parent]
        parts.append(f'<path d="M{x} {y}L{xx} {yy}" stroke="{p["accent"]}" stroke-width="2" fill="none"><title>{html.escape(child+" → "+parent)}</title></path>')
    for name,(x,y) in positions.items():
        count=charts.format_thousands(row_counts.get(name,0))
        parts.append(f'<g><rect x="{x-142}" y="{y-46}" width="284" height="92" rx="12" fill="{p["card"]}" stroke="{p["card_border"]}"/>'
                     f'<text x="{x}" y="{y-7}" text-anchor="middle" font-size="24" fill="{p["strong_text"]}">{name}</text>'
                     f'<text x="{x}" y="{y+27}" text-anchor="middle" font-size="24" fill="{p["text"]}">{count} filas</text></g>')
    return ''.join(parts)+'</svg>'


def lineage_overview(nodes, results, mode):
    """The live DAG as readable lists per layer, with dependencies on each model."""
    import html
    from bi import lineage, charts
    p = charts.get_palette(mode)
    layers=lineage.order_layers(nodes)
    counts=lineage.tests_by_model(nodes,results)
    names=dict(zip(nodes['unique_id'],nodes['name']))
    groups=[]
    for key,title,_ in lineage.LAYERS:
        items=[]
        for node in layers[key]:
            total,passing=counts.get(node['unique_id'],(0,0))
            parents=', '.join(names.get(parent,parent) for parent in node['depends_on'])
            state=f'{passing}/{total} pruebas' if total else lineage.MATERIALIZED.get(node['materialized'],node['materialized'])
            items.append(f'<article title="Entradas: {html.escape(parents,quote=True)}"><code>{html.escape(node["name"])}</code><small>{html.escape(state)}</small></article>')
        groups.append(f'<section><h3>{title} →</h3><div class="lineage-models">'+''.join(items)+'</div></section>')
    return (f'<div class="lineage-overview" aria-label="Linaje dbt: de bronce a marts" style="--lineage-card:{p["card"]};--lineage-border:{p["card_border"]}">' + ''.join(groups)+'</div>')
