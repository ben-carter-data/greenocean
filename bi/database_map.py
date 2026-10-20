"""«Mapa de la base» (D-189): where every table of the served database comes from.

One diagram, left to right, with the real names and row counts:
sources (ODEPA, INE) → landing in SQLite (raw.db) and bronze Parquet → dbt on a work
DuckDB (staging, intermediate, marts, tests) → the served file etl/datos.duckdb, whose
12 tables come from three places (dbt marts, the pipeline's load log, dbt's own trace)
→ what reads it (the panel's views, the panel). Under it, the SQLite backup datos.db and
the parity check that compares it with DuckDB. Every box explains its role on hover.

Nothing here reads data: bi/dashboard.py hands over the counts. The page is a full HTML
document for st.iframe (CSS only, no script), like the operation center.
"""
import html

from bi import charts

# The engine of each store, with its own mark color (fixed in every theme).
ENGINES = {
    "csv": ("CSV", "#94a3b8"),
    "api": ("API", "#94a3b8"),
    "sqlite": ("SQLite", "#3b9ae1"),
    "parquet": ("Parquet", "#52b788"),
    "duckdb": ("DuckDB", "#f4d03f"),
    "dbt": ("dbt", "#ff694b"),
    "streamlit": ("Streamlit", "#ff4b4b"),
    "python": ("Python", "#4b8bbe"),
}
# The three origins of the served tables.
ORIGINS = [
    ("marts", "Modelos dbt", "dbt", "Construidas y probadas por dbt en cada carga; el pipeline las copia tal cual.",
     ["weekly_price", "dim_product", "dim_region", "dim_channel", "dim_date", "rejection", "ipc_weekly",
      "ipc_monthly", "ine_ipc_source"]),
    ("log", "Registro de cargas", "pipeline", "La escribe el pipeline: una fila por ejecución real, con lo que "
     "leyó, cargó y rechazó. Una reconstrucción local no la toca.", ["etl_run"]),
    ("trace", "Trazas de dbt", "dbt", "La huella de la última construcción: cada modelo y prueba de dbt y su "
     "resultado. La usan el linaje y la página de calidad.", ["dbt_node", "dbt_result"]),
]


def thousands(value):
    return charts.format_thousands(value) if value is not None else "—"


def badge(engine):
    name, color = ENGINES[engine]
    return f'<span class="badge" style="--c:{color}">{name}</span>'


def node(title, subtitle, engine, tip, extra="", kind=""):
    """One box of the map: an engine badge, a name, a line, and its role on hover."""
    return (f'<div class="node {kind}" tabindex="0">{badge(engine)}<b>{html.escape(title)}</b>'
            f'<small>{html.escape(subtitle)}</small>{extra}'
            f'<span class="tip" role="tooltip">{html.escape(tip)}</span></div>')


def table_rows(names, counts):
    return "".join(f'<li><code>{html.escape(name)}</code><span>{thousands(counts.get(name))}</span></li>'
                   for name in names)


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    card, border, ink, text, muted = (palette["card"], palette["card_border"], palette["strong_text"],
                                      palette["text"], palette["reference"])
    raised = ("0 1px 0 rgba(255,255,255,.06) inset, 0 20px 40px -26px rgba(0,0,0,.9)" if dark
              else "0 1px 0 #fff inset, 0 20px 40px -28px rgba(15,27,45,.45), 0 4px 10px -8px rgba(15,27,45,.2)")
    glow = "0 0 0 1px color-mix(in srgb, #f4d03f 45%, transparent), 0 30px 60px -30px rgba(244,208,63,.45)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text};
  font:300 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.map {{ display:grid; grid-template-columns:.9fr 24px .95fr 24px 1.05fr 24px 2.15fr 24px .95fr; align-items:stretch;
  padding:10px 4px 6px; }}
.lane {{ display:flex; flex-direction:column; gap:10px; min-width:0; }}
.lane h3 {{ margin:0 0 2px; font-size:10px; font-weight:500; line-height:1.2; letter-spacing:.08em; text-transform:uppercase;
  color:{muted}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.lane h3 i {{ font-style:normal; color:{ink}; margin-right:5px; }}
.arrow {{ position:relative; }}
.arrow::before {{ content:""; position:absolute; left:2px; right:6px; top:50%; height:2px; border-radius:2px;
  background:linear-gradient(90deg, color-mix(in srgb, {palette['accent']} 15%, transparent), {palette['accent']}); }}
.arrow::after {{ content:""; position:absolute; right:1px; top:calc(50% - 5px); border:6px solid transparent;
  border-left:8px solid {palette['accent']}; border-right:0; }}
.node {{ position:relative; display:flex; flex-direction:column; gap:3px; padding:10px 12px; border-radius:14px;
  background:linear-gradient(180deg, color-mix(in srgb, {card} 90%, {'#fff' if not dark else '#000'}), {card});
  border:1px solid {border}; box-shadow:{raised}; transition:transform .2s ease, box-shadow .2s ease; cursor:default; }}
.node:hover, .node:focus {{ transform:translateY(-3px); z-index:20; outline:none; }}
.node b {{ font-weight:500; color:{ink}; font-size:13px; }}
.node small {{ color:{muted}; font-size:11.5px; }}
.node code, .served code {{ font:400 11.5px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; color:{ink}; }}
.badge {{ align-self:flex-start; padding:1px 8px; border-radius:999px; font-size:10px; font-weight:500; letter-spacing:.04em;
  color:var(--c); background:color-mix(in srgb, var(--c) {'16%' if dark else '12%'}, transparent);
  box-shadow:inset 0 0 0 1px color-mix(in srgb, var(--c) 40%, transparent); }}
.layers {{ display:flex; flex-direction:column; gap:4px; margin-top:4px; }}
.layers span {{ display:flex; justify-content:space-between; gap:8px; padding:3px 8px; border-radius:8px; font-size:11.5px;
  background:color-mix(in srgb, #ff694b {'10%' if dark else '7%'}, transparent); color:{ink}; }}
.layers span em {{ font-style:normal; color:{muted}; }}
.served {{ position:relative; padding:12px 12px 10px; border-radius:18px; border:1px solid color-mix(in srgb, #f4d03f 55%, {border});
  background:linear-gradient(180deg, color-mix(in srgb, #f4d03f {'7%' if dark else '5%'}, {card}), {card}); box-shadow:{glow}; }}
.served-head {{ display:flex; flex-wrap:wrap; align-items:center; gap:4px 8px; margin-bottom:8px; }}
.served-head b {{ font-weight:500; color:{ink}; font-size:14px; }}
.served-head small {{ flex-basis:100%; color:{muted}; font-size:11px; }}
.origin {{ position:relative; margin-top:7px; padding:7px 9px; border-radius:11px; border:1px dashed {border};
  background:color-mix(in srgb, {card} 70%, transparent); }}
.origin:hover {{ border-style:solid; z-index:20; }}
.origin-head {{ display:flex; align-items:center; gap:6px; margin-bottom:4px; font-size:11.5px; color:{ink}; font-weight:500; }}
.origin-head .count {{ margin-left:auto; font-weight:400; color:{muted}; }}
.origin ul {{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:1fr 1fr; gap:2px 16px; }}
.origin li {{ display:flex; justify-content:space-between; gap:6px; font-size:10.5px; color:{muted}; min-width:0; }}
.origin li code {{ font-size:10.5px !important; }}
.origin li code {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.tip {{ position:absolute; z-index:30; left:50%; top:calc(100% + 8px); width:250px; padding:10px 12px; border-radius:12px;
  background:{card}; border:1px solid {border}; box-shadow:0 18px 36px -16px rgba(0,0,0,.55); color:{text};
  font-size:12px; line-height:1.45; opacity:0; pointer-events:none; transform:translate(-50%, 6px); transition:opacity .15s ease, transform .15s ease; }}
.node:hover > .tip, .node:focus > .tip, .origin:hover > .tip {{ opacity:1; transform:translate(-50%, 0); }}
.backup-row {{ display:grid; grid-template-columns:.9fr 24px .95fr 24px 1.05fr 24px 2.15fr 24px .95fr; margin-top:14px; padding:0 4px; }}
.backup {{ grid-column:3 / 6; }}
.parity {{ grid-column:7 / 10; display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:14px;
  border:1px dashed {border}; color:{text}; font-size:12px; position:relative; }}
.parity b {{ font-weight:500; color:{ink}; }}
.parity::before {{ content:"⇅"; font-size:18px; color:{palette['accent']}; }}
.legend {{ display:flex; flex-wrap:wrap; gap:6px 14px; margin:12px 4px 2px; font-size:11px; color:{muted}; }}
</style>"""


def build_map_html(palette, counts, layers, tests):
    """The whole map as one HTML document. counts: {table: rows} of the served file;
    layers: {"staging": n, "intermediate": n, "marts": n}; tests: dbt tests in the build."""
    served_total = sum(counts.get(name, 0) for _, _, _, _, names in ORIGINS for name in names)
    sources = (node("ODEPA · mayoristas", "CSV por año, precios de frutas y hortalizas", "csv",
                    "Precios mayoristas publicados por ODEPA. El agente los descarga y registra su huella SHA-256 "
                    "en manifest.json.")
               + node("ODEPA · consumidor", "CSV por año, siete familias de alimentos", "csv",
                      "Precios al consumidor por región y canal. Mismo agente y mismo registro de huellas.")
               + node("INE · IPC de alimentos", "Índice mensual", "api",
                      "El IPC de alimentos del INE: convierte los precios a pesos reales."))
    landing = (node("etl/raw.db", "Aterrizaje: filas tal como se publican", "sqlite",
                    "Base de aterrizaje en SQLite. Copia exacta de los CSV, sin limpiar. No se sube al repositorio "
                    "(unos 665 MB); se reconstruye en cada carga.")
               + node("Capa bronce", "Las mismas filas en Parquet, una por fuente y año", "parquet",
                      "Formato estándar de data lake: dbt lee desde aquí, y cualquier otro warehouse podría hacerlo."))
    layer_rows = "".join(f'<span>{label}<em>{layers.get(key, 0)} modelos</em></span>'
                         for key, label in (("staging", "staging"), ("intermediate", "intermedio"), ("marts", "marts")))
    transform = node("dbt sobre DuckDB", "Base de trabajo warehouse_build.duckdb", "dbt",
                     f"dbt limpia, valida, normaliza unidades, marca atípicos y arma el modelo estrella. Corre "
                     f"{tests} pruebas; si una falla, la base publicada no se reemplaza.",
                     extra=f'<div class="layers">{layer_rows}<span>pruebas<em>{tests}</em></span></div>')
    origins = "".join(
        f'<div class="origin"><div class="origin-head">{badge("python" if engine == "pipeline" else engine)}'
        f'{html.escape(title)}<span class="count">{len(names)} tabla{"s" if len(names) > 1 else ""}</span></div>'
        f'<ul>{table_rows(names, counts)}</ul><span class="tip" role="tooltip">{html.escape(tip)}</span></div>'
        for _, title, engine, tip, names in ORIGINS)
    served = (f'<div class="served"><div class="served-head">{badge("duckdb")}<b>etl/datos.duckdb</b>'
              f'<small>12 tablas · {thousands(served_total)} filas</small></div>{origins}</div>')
    consumers = (node("Vistas del panel", "8 vistas en español, creadas al conectar", "duckdb",
                      "precios, semanas, productos, ipc_semanal… No se guardan en la base: el panel las crea en cada "
                      "conexión, sobre las tablas, con columnas legibles.")
                 + node("Panel GreenOcean", "Lee la base en solo lectura", "streamlit",
                        "Streamlit abre datos.duckdb en solo lectura: el panel nunca escribe en la base."))
    lanes = [("1", "Fuentes", sources), ("2", "Aterrizaje", landing), ("3", "Transformación", transform),
             ("4", "Base servida", served), ("5", "Consumo", consumers)]
    body = '<div class="arrow"></div>'.join(f'<section class="lane"><h3><i>{number}</i>{title}</h3>{content}</section>'
                                            for number, title, content in lanes)
    backup = ('<div class="backup-row"><div class="backup">'
              + node("etl/datos.db", "Respaldo: el mismo resultado calculado con el ETL en Python", "sqlite",
                     "El ETL de respaldo (etl/etl.py) lee raw.db y calcula los mismos precios semanales en SQLite. "
                     "No lo lee el panel: solo sirve para comprobar el resultado de dbt.", kind="backup-node")
              + '</div><div class="parity"><span><b>Paridad SQLite ↔ DuckDB.</b> Mismos precios, mismos rechazos y '
                'misma suma en las dos bases; la página Calidad y auditoría lo comprueba en cada carga.</span></div></div>')
    legend = ('<div class="legend"><span>Pasa el cursor por cada caja para ver su papel.</span>'
              + "".join(badge(engine) for engine in ("sqlite", "parquet", "dbt", "duckdb", "python", "streamlit")) + '</div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">' + build_css(palette)
            + f'</head><body><div class="map" aria-label="Mapa de la base de datos">{body}</div>{backup}{legend}</body></html>')
