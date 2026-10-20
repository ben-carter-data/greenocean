"""«Auditoría» (D-196): where does one figure come from, and can anyone check it?

The reader picks a price (product, channel, region and series); the page draws its real
path, from the file ODEPA published to the panel: the file with its registered SHA-256, the
load that read it, the rules it passed, the dbt models that built it, the row in the served
database and where the panel shows it. Every step says what it holds and why, and what could
not be checked here is said so instead of shown as verified.

find_series() and read_trace() read the database; build_trace_steps() and build_trace_html()
are pure and drawn as one HTML document for st.iframe (CSS only, no script).
"""
import html
import hashlib
from pathlib import Path

from bi import quality_view, charts, database_map, queries

DOWNLOADS = Path(__file__).resolve().parent.parent / "agent" / "downloads"
# The dbt models a price goes through, in order; the first depends on the source.
MODELS = ["int_prices__units_normalized", "int_prices__outlier_flagged", "int_prices__validated", "int_prices__weekly"]
FLAG_TEXT = {None: "pasó todas las reglas y cuenta en los indicadores",
             "ATIPICO": "marcado como atípico para su serie: está en la base, fuera de los indicadores",
             "UNIDAD_NO_CONVERTIBLE": "su unidad no se pudo llevar a kilo o unidad: está en la base, fuera de los indicadores"}
SERIES_SQL = """SELECT p.product_group, p.variety, p.quality, c.channel, c.source, r.region, w.normalized_unit,
       max(w.week_start) AS last_week, count(*) AS weeks
FROM weekly_price AS w JOIN dim_product AS p USING (product_id) JOIN dim_region AS r USING (region_id)
JOIN dim_channel AS c USING (channel_id)
WHERE p.product = ? AND c.channel = ? AND r.region = ?
GROUP BY ALL ORDER BY weeks DESC, p.variety, p.quality"""
ROW_SQL = """SELECT w.week_start, p.product_group, p.product, p.variety, p.quality, c.channel, c.source, r.region,
       w.normalized_unit, w.price, w.volume, w.observation_count, w.flag
FROM weekly_price AS w JOIN dim_product AS p USING (product_id) JOIN dim_region AS r USING (region_id)
JOIN dim_channel AS c USING (channel_id)
WHERE p.product = ? AND p.variety = ? AND p.quality = ? AND c.channel = ? AND r.region = ? AND w.normalized_unit = ?
ORDER BY w.week_start DESC LIMIT 1"""


def find_series(product, channel, region, database_file=queries.DATABASE_FILE):
    """The series (variety, quality, unit) that match the three choices, longest first."""
    return queries.run_sql(SERIES_SQL, database_file, (product, channel, region))


def read_trace(product, variety, quality, channel, region, unit, database_file=queries.DATABASE_FILE):
    """The latest weekly price of one series, as a dict; None when there is none."""
    frame = queries.run_sql(ROW_SQL, database_file, (product, variety, quality, channel, region, unit))
    if frame.empty:
        return None
    row = frame.iloc[0].to_dict()
    row["flag"] = None if row["flag"] is None or str(row["flag"]) in ("None", "nan") else row["flag"]
    return row


def source_file_name(row):
    """The CSV that holds the row: source and year of its week, as the agent names them."""
    return f"{row['source']}_{str(row['week_start'])[:4]}.csv"


def check_file(name, entry, directory=DOWNLOADS):
    """(status, text) of the file against its registered SHA-256; honest when it is not here."""
    expected = entry.get("hash", "") if entry else ""
    path = Path(directory) / name
    if not expected:
        return "pending", "sin huella registrada"
    if not path.is_file():
        return "pending", "el archivo no está en este servidor: no se puede comprobar aquí"
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return ("ok", "la huella calculada coincide") if digest.hexdigest() == expected else ("fail", "la huella calculada NO coincide")


def money(value):
    return "$ " + charts.format_thousands(round(float(value)))


def build_trace_steps(row, manifest, run, build, file_status):
    """[(key, title, [lines], what, why, status)] for the six steps of one price."""
    name = source_file_name(row)
    entry = manifest.get(name) or {}
    status, status_text = file_status
    hash_text = (entry.get("hash", "")[:12] + "…") if entry.get("hash") else "—"
    downloaded = str(entry.get("downloaded_at", ""))[:10] or "—"
    size = f"{entry['bytes'] / 1_000_000:.0f} MB".replace(".", ",") if entry.get("bytes") else "—"
    flag_text = FLAG_TEXT.get(row["flag"], "marca de calidad: " + str(row["flag"]))
    source_model = "stg_odepa__" + str(row["source"])
    chain = " → ".join([source_model] + MODELS + ["weekly_price"])
    tests = f"{build['passing']} de {build['tests']} pruebas superadas" if build else "sin resultado de dbt"
    built = f" · construida el {build['built_at']}" if build and build.get("built_at") else ""
    return [
        ("file", "Archivo de origen",
         [name, f"{size} · descargado el {downloaded}", f"SHA-256 {hash_text} registrado", status_text],
         "El CSV que ODEPA publicó y que contiene esta fila. Su huella SHA-256 quedó anotada en manifest.json al descargarlo.",
         "Si el archivo cambia, aunque sea un byte, la huella ya no coincide: es la prueba de que se trabajó con lo publicado.", status),
        ("landing", "Aterrizaje",
         [f"Carga {run['run_id']} · {str(run['started_at'])[:10]}", f"leyó {charts.format_thousands(run['rows_read'])} filas del origen",
          "copia exacta, sin limpiar"],
         "La carga lleva las filas del CSV a raw.db tal como se publicaron, sin cambiar nada.",
         "Una copia fiel permite volver al origen y repetir todo el camino.", "ok"),
        ("rules", "Reglas de calidad",
         [f"unidad normalizada: {row['normalized_unit']}", f"promedio de {int(row['observation_count'])} observaciones de la semana", flag_text,
          f"{charts.format_thousands(run['rows_rejected'])} filas rechazadas en la carga"],
         "Cada precio se lleva a kilo o unidad y a su semana, se valida y se marca si es atípico. Las filas que no cumplen se apartan con su motivo.",
         "Ningún precio se corrige a mano ni se inventa: lo que no sirve se aparta y se cuenta.", "ok" if row["flag"] is None else "pending"),
        ("dbt", "Modelos de dbt",
         [chain, tests + built],
         "dbt aplica esas transformaciones como modelos SQL, uno tras otro, y corre sus pruebas sobre el resultado.",
         "Cada paso es SQL versionado y probado: cualquiera puede leerlo y repetirlo. Si una prueba falla, la base publicada no se reemplaza.",
         "ok" if build and build["ok"] else "pending"),
        ("served", "Base servida",
         [f"weekly_price · {row['week_start']}", f"{money(row['price'])} por {row['normalized_unit']}",
          "una fila por semana, producto, región, canal y unidad"],
         "La fila final en datos.duckdb: la que lee el panel. Su clave es semana, producto, región, canal y unidad.",
         "Es el punto de llegada: lo que se publica es exactamente esta fila.", "ok"),
        ("panel", "Panel",
         ["Resumen semanal", "Consultas SQL · Tabla completa", "solo lectura"],
         "El panel muestra esta fila en el Resumen y la devuelve en la consulta «Tabla completa», con su precio real según el IPC.",
         "Quien duda de una cifra puede buscarla en la consulta y repetir el camino hacia atrás.", "ok"),
    ]


VISIBLE = {"file": (0, 3), "landing": (0, 1), "rules": (2, 3), "dbt": (1,), "served": (0, 1), "panel": (0,)}
ABOUT = (("Propósito", "Demostrar de dónde sale una cifra y que cualquiera puede comprobarlo."),
         ("Cómo se lee", "Elige un precio arriba. El camino va de izquierda a derecha, del archivo que ODEPA publicó hasta el "
                         "panel. Pasa el cursor por cada paso y por cada control."),
         ("Quién la usa", "Quien debe rendir cuentas o revisar: un jefe, un revisor, alguien que duda de una cifra."))


def build_css(palette):
    dark = palette["base"] == charts.BASE_DARK
    ink, text, muted, card, border, accent = (palette["strong_text"], palette["text"], palette["reference"], palette["card"],
                                              palette["card_border"], palette["accent"])
    shade = "rgba(0,0,0,.55)" if dark else "rgba(15,39,71,.22)"
    colors = {"ok": "#22b35a", "pending": "#d97706", "fail": "#d03b3b"}
    states = "".join(f".s-{key}{{--c:{color};}}" for key, color in colors.items())
    tip_shadow = "rgba(0,0,0,.5)" if dark else "rgba(0,0,0,.18)"
    return f"""<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; background:transparent; color:{text}; font:300 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
{states}
.top {{ display:flex; align-items:baseline; gap:4px 14px; margin:2px 0 4px; color:{ink}; }}
.top strong {{ font-size:19px; font-weight:500; }}
.top span {{ color:{muted}; font-size:12.5px; }}
.about {{ position:relative; margin-left:auto; flex:none; align-self:center; }}
.about > i {{ display:grid; place-items:center; width:20px; height:20px; border-radius:50%; border:1px solid {muted}; color:{muted}; font:500 12px/1 serif; cursor:default; }}
.about .tip {{ left:auto; right:0; top:calc(100% + 6px); width:330px; transform:none; text-align:left; }}
.about:hover .tip, .about:focus .tip {{ display:block; }}
.path {{ position:relative; display:grid; grid-template-columns:repeat(6, 1fr); gap:0 8px; padding:14px 0 2px; }}
.path::before {{ content:""; position:absolute; left:8%; right:8%; top:62px; height:2px; background:linear-gradient(90deg, color-mix(in srgb, {accent} 20%, transparent), {accent}); }}
.step {{ position:relative; text-align:center; outline:none; padding:0 4px; }}
.step .num {{ position:absolute; left:50%; top:-4px; transform:translateX(-48px); width:19px; height:19px; border-radius:50%; font-size:11px; font-weight:500;
  display:grid; place-items:center; color:var(--c); background:{palette['background']}; border:1.5px solid var(--c); z-index:2; }}
.logo {{ display:block; width:72px; height:72px; margin:0 auto; filter:drop-shadow(0 12px 10px {shade}); transition:transform .25s ease; position:relative; z-index:1; }}
.step:hover .logo, .step:focus .logo {{ transform:translateY(-5px) scale(1.05); }}
.mark {{ position:absolute; z-index:3; left:50%; top:52px; transform:translateX(16px); width:19px; height:19px; border-radius:50%; background:var(--c); color:#fff;
  font:700 11px/19px sans-serif; text-align:center; box-shadow:0 0 0 3px {palette['background']}; }}
.step b {{ display:block; margin-top:8px; font-size:14px; font-weight:500; color:{ink}; }}
.step p {{ margin:2px 0 0; font-size:11.5px; color:{muted}; line-height:1.35; overflow-wrap:anywhere; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.step p.warn {{ color:var(--c); }}
.tip {{ position:absolute; z-index:60; left:50%; top:calc(100% + 4px); width:290px; padding:12px 14px; border-radius:14px; text-align:left; background:{card};
  border:1px solid {border}; box-shadow:0 18px 40px {tip_shadow}; color:{text}; font-size:12.5px; line-height:1.45; display:none; pointer-events:none; transform:translateX(-50%); }}
.tip i {{ display:block; margin:8px 0 2px; font:500 10px/1 sans-serif; font-style:normal; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.tip i:first-child {{ margin-top:0; }}
.step:nth-child(1) .tip {{ left:0; transform:none; }} .step:nth-child(6) .tip {{ left:auto; right:0; transform:none; }}
.step:hover .tip, .step:focus .tip {{ display:block; }}
.step:hover, .step:focus {{ z-index:50; }}
.controls {{ display:flex; gap:6px 22px; flex-wrap:wrap; justify-content:center; margin-top:10px; padding-top:8px; border-top:1px solid color-mix(in srgb, {border} 70%, transparent); }}
.group h4 {{ margin:0 0 3px; text-align:center; font-size:10px; font-weight:500; letter-spacing:.1em; text-transform:uppercase; color:{muted}; }}
.group .row {{ display:flex; gap:10px; justify-content:center; }}
.ctl {{ position:relative; width:74px; text-align:center; outline:none; }}
.ctl .qa-icon {{ width:34px; height:34px; filter:drop-shadow(0 5px 5px {shade}); }}
.ctl .dot {{ position:absolute; top:0; left:calc(50% + 8px); width:10px; height:10px; border-radius:50%; background:var(--c); box-shadow:0 0 0 2px {palette['background']}; }}
.ctl small {{ display:block; font-size:10.5px; line-height:1.2; color:{muted}; margin-top:1px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.ctl .tip {{ top:auto; bottom:calc(100% + 4px); left:50%; }}
.ctl:hover .tip, .ctl:focus .tip {{ display:block; }}
.ctl:hover, .ctl:focus {{ z-index:50; }}
.legend {{ margin:6px 0 0; font-size:11px; color:{muted}; text-align:center; }}
@media (max-width:900px) {{ .path {{ grid-template-columns:repeat(2, 1fr); gap:16px 8px; }} .path::before {{ display:none; }} }}
</style>"""


def build_logo(key):
    if key == "file":
        return database_map.source_logo("odepa")
    if key == "landing":
        return database_map.brand_logo("sqlite", "-trace")
    if key == "rules":
        return database_map.source_logo("etl")
    if key == "dbt":
        return database_map.brand_logo("dbt", "-trace")
    if key == "served":
        return database_map.brand_logo("duckdb", "-trace")
    return database_map.source_logo("panel")


def build_controls_html(columns):
    """The controls that hold the chain up, as small icons with their status: [(step, [(icon, title, status, detail, why)])]."""
    kinds = {"ok": "ok", "pending": "pending", "fail": "fail"}
    groups = []
    for step, cards in columns:
        items = "".join(
            f'<div class="ctl s-{kinds[quality_view.classify(status)]}" tabindex="0">{quality_view.build_icon_svg(icon)}'
            f'<span class="dot"></span><small>{html.escape(title)}</small><span class="tip" role="tooltip"><i>{html.escape(status)}</i>'
            f'{html.escape(detail)}<i>Qué comprueba</i>{html.escape(why)}</span></div>' for icon, title, status, detail, why in cards)
        groups.append(f'<div class="group"><h4>{html.escape(step)}</h4><div class="row">{items}</div></div>')
    return '<div class="controls">' + "".join(groups) + "</div>"


def build_trace_html(palette, row, steps, controls=None):
    """The whole view: the chosen price, the six steps as logos and, under them, the controls that hold the chain up."""
    about = ('<div class="about" tabindex="0"><i>i</i><span class="tip" role="tooltip">'
             + "".join(f"<i>{title}</i>{html.escape(text)}" for title, text in ABOUT) + "</span></div>")
    figure = (f'<div class="top"><strong>{html.escape(money(row["price"]))} por {html.escape(str(row["normalized_unit"]))}</strong>'
              f'<span>{html.escape(str(row["product"]))} · {html.escape(str(row["variety"]))} · {html.escape(str(row["quality"]))} · '
              f'{html.escape(str(row["channel"]))} · {html.escape(str(row["region"]))} · semana {html.escape(str(row["week_start"])[:10])}</span>{about}</div>')
    marks = {"ok": "✓", "pending": "!", "fail": "✕"}
    body = []
    for number, (key, title, lines, what, why, status) in enumerate(steps, start=1):
        shown = "".join(f'<p class="{"warn" if status != "ok" and index == len(lines) - 1 else ""}">{html.escape(lines[index])}</p>'
                        for index in VISIBLE[key] if index < len(lines))
        detail = "<br>".join(html.escape(line) for line in lines)
        body.append(f'<div class="step s-{status}" tabindex="0"><span class="num">{number}</span>{build_logo(key)}'
                    f'<span class="mark">{marks[status]}</span><b>{html.escape(title)}</b>{shown}'
                    f'<span class="tip" role="tooltip"><i>Qué hace en la cadena</i>{html.escape(what)}<i>Por qué</i>{html.escape(why)}'
                    f'<i>Detalle de esta fila</i>{detail}</span></div>')
    note = '<p class="legend">✓ comprobado aquí · ! no se puede comprobar en este servidor o tiene una observación · nada se muestra como verificado sin comprobarse.</p>'
    extra = build_controls_html(controls) if controls else ""
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + build_css(palette) + f'</head><body>{quality_view.DEFS}{figure}<div class="path">{"".join(body)}</div>{extra}{note}</body></html>')
