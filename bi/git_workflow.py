"""«Cambios e incidentes» (D-344): how a change travels from an idea to a live deployment, as a map of 15 stations.

The map follows docs/referencia/ciclo_git.html: three lanes in a zigzag (Prepare, Commit and verify, Publish), generic
icons, optional stations with a dashed border, checkpoints as yellow diamonds, «Deployed» in green. A click on a station
opens one side panel with what it does and why, its commands (each with a copy button), what to do if it fails, a real
example of GreenOcean and the occurrences of the failure register that happened at that station. Previous / Next, the
arrow keys and Escape walk and close the panel. The page is one HTML document for st.iframe; it needs its script.

The occurrences come from docs/calidad/plan_mitigacion.json. The professional reads date, occurrence, solution and
comment; the diagnosis goes in the page only for the author (D-345). The text is Spanish or English, as the reader chose.
"""

from __future__ import annotations

import html
import json
from typing import Any

from bi import charts, quality_metrics, static_files

# region Constants
LANES = (
    ("a", ("Preparar", "Prepare")),
    ("b", ("Guardar y verificar", "Commit and verify")),
    ("c", ("Publicar", "Publish")),
)
LABELS = {
    "optional": ("opcional", "optional"),
    "checkpoint": ("punto de control", "checkpoint"),
    "details": ("ⓘ detalle", "ⓘ details"),
    "station": ("Estación", "Station"),
    "commands": ("Comandos", "Commands"),
    "fails": ("Si falla", "If it fails"),
    "example": ("En GreenOcean", "In GreenOcean"),
    "register": ("En el registro de fallas", "In the failure register"),
    "none": ("Ninguna falla registrada en esta estación.", "No failure registered at this station."),
    "diagnosis": ("Diagnóstico", "Diagnosis"),
    "solution": ("Solución", "Solution"),
    "close": ("Cerrar", "Close"),
    "copy": ("Copiar", "Copy"),
    "copied": ("Copiado", "Copied"),
    "selected": ("Seleccionado", "Selected"),
    "previous": ("← Anterior", "← Previous"),
    "next": ("Siguiente →", "Next →"),
    "open": ("abierta", "open"),
    "solved": ("resuelta", "solved"),
    "legend_optional": ("se puede omitir en un repositorio pequeño", "skippable on a small repository"),
    "legend_checkpoint": ("el flujo se detiene hasta que se cumple", "the flow stops until it holds"),
    "legend_arrow": ("el camino del cambio", "the path of the change"),
    "title": ("Cambios e incidentes", "Cambios e incidentes"),
    "lede": (
        "Cómo viaja un cambio desde la idea hasta el despliegue en un proyecto de datos con CI. Cada estación dice "
        "quién actúa y el comando. Abre una para ver por qué existe y dónde ocurrió en GreenOcean.",
        "How a change travels from an idea to a live deployment in a data project with CI. Each station shows who acts "
        "and the command. Open any station to see why it exists and where it happened in GreenOcean.",
    ),
    "footer": (
        "Un push de avance simple solo agrega commits. Si git pide forzar, las ramas divergieron: se integra con "
        "git pull --rebase, nunca se sobrescribe con --force.",
        "A fast-forward push only adds commits. If git asks to force, the branches diverged: integrate with "
        "git pull --rebase, never overwrite with --force.",
    ),
}
WHO = {
    "human": ("Persona", "Human"),
    "tool": ("Herramienta", "Tool"),
    "tool_human": ("Herramienta → Persona", "Tool → Human"),
    "human_tool": ("Persona → Herramienta", "Human → Tool"),
    "ci": ("CI", "CI"),
    "platform": ("Plataforma", "Platform"),
}
# Generic line icons (no brand marks), 24 × 24.
ICONS = {
    "spark": '<path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6 5.6 18.4"/>',
    "clip": '<path d="M9 3h6v3H9z"/><path d="M7 4.5H5V21h14V4.5h-2"/><path d="M9 13l2 2 4-4"/>',
    "sync": '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4v5h-5"/>',
    "branch": '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="7" r="2"/><path d="M6 7v10M18 9c0 5-12 3-12 8"/>',
    "code": '<path d="M9 7l-5 5 5 5M15 7l5 5-5 5"/>',
    "commit": '<circle cx="12" cy="12" r="4"/><path d="M2 12h6M16 12h6"/>',
    "list": '<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>',
    "flask": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3M7.5 15h9"/>',
    "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "merge": '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="12" r="2"/><path d="M6 7v10M6 8c0 3 5 4 10 4"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.3-4.3"/>',
    "ff": '<path d="M3 6l8 6-8 6zM12 6l8 6-8 6z"/>',
    "up": '<path d="M12 16V4M7 9l5-5 5 5M4 20h16"/>',
    "gear": '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
}
# Each station: number, lane, icon, who, flags, commands (the same in both languages) and the texts as (es, en).
# «example» was read against the repository's history (git log, reflog, Actions) on 2026-10-29.
STATIONS: list[dict[str, Any]] = [
    {
        "n": 1,
        "lane": "a",
        "icon": "spark",
        "who": "human",
        "commands": ["goal · constraints · where to stop"],
        "title": ("Escribir el prompt", "Write the prompt"),
        "sub": ("Meta, límites, punto de parada", "Goal, limits, stop point"),
        "what": (
            "El trabajo empieza como una instrucción escrita con una meta clara, las reglas que no se pueden romper y el punto donde la herramienta debe parar e informar.",
            "The work starts as a written instruction with a clear goal, the rules that cannot be broken and the point where the tool must stop and report.",
        ),
        "example": (
            "El plan de calidad corrió como un solo prompt dividido en etapas 0 a 6; cada una cerraba con un informe de un párrafo y esperaba «continúa».",
            "The quality plan ran as one prompt split into stages 0 to 6, each ending with a one-paragraph briefing and a wait for «continúa».",
        ),
    },
    {
        "n": 2,
        "lane": "a",
        "icon": "clip",
        "who": "tool",
        "commands": ["git status"],
        "title": ("Revisar el árbol", "Check the tree"),
        "sub": ("Nada pendiente", "Nothing pending"),
        "what": (
            "Un árbol de trabajo limpio evita que ediciones sueltas se mezclen con el cambio nuevo.",
            "A clean working tree means no stray edits get mixed into the new change.",
        ),
        "example": (
            "Cada rama de GreenOcean se abrió desde un main limpio antes de medir o cambiar nada.",
            "Every GreenOcean branch was cut from a clean main before measuring or changing anything.",
        ),
    },
    {
        "n": 3,
        "lane": "a",
        "icon": "sync",
        "who": "tool",
        "commands": ["git switch main", "git pull"],
        "title": ("Sincronizar main", "Sync main"),
        "sub": ("Partir de lo último", "Start from the latest"),
        "what": (
            "Partir del main más reciente evita construir sobre una base vieja, la fuente más común de conflictos.",
            "Starting from the latest main avoids building on an old base, the most common source of conflicts.",
        ),
        "example": (
            "Cada rama de GreenOcean se cortó desde un main al día.",
            "Every branch in GreenOcean was cut from an up-to-date main.",
        ),
    },
    {
        "n": 4,
        "lane": "a",
        "icon": "branch",
        "who": "tool",
        "optional": True,
        "commands": ["git switch -c topic"],
        "title": ("Abrir una rama", "Open a topic branch"),
        "sub": ("Una rama por tema", "One branch per theme"),
        "what": (
            "Una rama aísla el trabajo hasta que está listo. En un repositorio de una sola persona se puede omitir, pero facilita la revisión.",
            "A branch isolates the work until it is ready. On a one-person repository it can be skipped, but it makes review easier.",
        ),
        "example": (
            "calidad-simple, eliminar-donde-comprar, usuario-nuevo, nombre-repositorio.",
            "calidad-simple, eliminar-donde-comprar, usuario-nuevo, nombre-repositorio.",
        ),
    },
    {
        "n": 5,
        "lane": "a",
        "icon": "code",
        "who": "tool",
        "commands": ["git diff"],
        "title": ("Hacer el cambio", "Make the change"),
        "sub": ("Editar y leer el diff", "Edit, then read the diff"),
        "what": (
            "Se hace el cambio y se lee como diff antes de guardar nada.",
            "The change is made and read back as a diff before anything is saved.",
        ),
        "example": (
            "docs/calidad/metas.json se amplió con el aceptable y el margen crítico de 12 indicadores.",
            "docs/calidad/metas.json was extended with acceptable limits and critical margins for 12 indicators.",
        ),
    },
    {
        "n": 6,
        "lane": "b",
        "icon": "commit",
        "who": "tool",
        "commands": ["git add -p", 'git commit -m "scope: what"'],
        "title": ("Preparar y confirmar", "Stage and commit"),
        "sub": ("Un cambio por commit", "One change per commit"),
        "what": (
            "Un cambio lógico por commit, para poder revertir cualquiera sin tocar los demás.",
            "One logical change per commit, so any single change can be reverted on its own.",
        ),
        "example": (
            "6ad674d (los 12 indicadores) y 785f1e2 (informes numerados) salieron cada uno con su decisión en docs/DECISIONES.md.",
            "6ad674d (the 12 indicators) and 785f1e2 (numbered reports) each landed with its decision in docs/DECISIONES.md.",
        ),
    },
    {
        "n": 7,
        "lane": "b",
        "icon": "list",
        "who": "tool",
        "optional": True,
        "commands": ["git log --oneline -5"],
        "title": ("Leer el historial", "Read the history"),
        "sub": ("Ver qué se guardó", "Check what was saved"),
        "what": (
            "Una mirada rápida confirma que los commits dicen lo que deben decir.",
            "A quick look confirms the commits say what they should.",
        ),
        "example": (
            "Sirvió para informar qué commits produjo cada etapa.",
            "Used to report which commits each stage produced.",
        ),
    },
    {
        "n": 8,
        "lane": "b",
        "icon": "flask",
        "who": "tool",
        "gate": True,
        "commands": ["pytest", "ruff check .", "ruff format --check .", "mypy"],
        "title": ("Correr todo el CI en local", "Run the whole suite"),
        "sub": ("Pruebas, lint, formato, tipos", "Tests, lint, format, types"),
        "what": (
            "Se revisa todo el proyecto, no solo los archivos tocados, con las mismas versiones de herramientas que usa el CI.",
            "The whole project is checked, not only the files touched, with the same tool versions CI uses.",
        ),
        "fail": (
            "Rojo: deshacer con git revert <sha> o git restore <archivo>, y volver a la estación 5. Nunca bajar un umbral ni saltar una prueba.",
            "Red: undo with git revert <sha> or git restore <file>, back to station 5. Never lower a threshold or skip a test.",
        ),
        "example": (
            "Pasaron 1038 pruebas y ruff format marcó un archivo de prueba sin formato; se corrigió en su propio commit 0020096 antes del push.",
            "1038 tests passed, and ruff format caught one unformatted test file, fixed in its own commit 0020096 before the push.",
        ),
    },
    {
        "n": 9,
        "lane": "b",
        "icon": "eye",
        "who": "tool_human",
        "commands": ["what changed · what was verified · what risk is left"],
        "title": ("Informar y revisar", "Report and review"),
        "sub": ("Una persona mira", "A human looks"),
        "what": (
            "La herramienta se detiene e informa; una persona revisa todo lo visible antes de aprobar. Un informe es una afirmación, no una evidencia.",
            "The tool stops and reports; a person reviews anything visible before approving. A report is a claim, not evidence.",
        ),
        "example": (
            "Un informe mostró un choque entre CLAUDE.md y la regla de idiomas; la persona decidió y quedó como D-338.",
            "A briefing surfaced a conflict between CLAUDE.md and the language rule; the human decided, and it became D-338.",
        ),
    },
    {
        "n": 10,
        "lane": "b",
        "icon": "merge",
        "who": "tool",
        "optional": True,
        "commands": ["git switch main", "git merge --ff-only topic"],
        "title": ("Integrar en main", "Fold into main"),
        "sub": ("Solo avance simple", "Fast-forward only"),
        "what": (
            "La rama entra en main sin inventar un commit de fusión. Si se niega, las ramas divergieron.",
            "The branch moves into main without inventing a merge commit. If it refuses, the branches diverged.",
        ),
        "example": (
            "main avanzó por avance simple hasta 843decd, igual a calidad-simple (16 commits desde eb6bce6), sin conflictos.",
            "main fast-forwarded to 843decd, identical to calidad-simple (16 commits since eb6bce6), with no conflicts.",
        ),
    },
    {
        "n": 11,
        "lane": "c",
        "icon": "search",
        "who": "tool",
        "commands": [
            "git log --oneline origin/main..HEAD",
            "git diff --stat origin/main..HEAD",
            'git log -S "value" --all',
        ],
        "title": ("Ver y buscar secretos", "Preview and scan"),
        "sub": ("Qué sale, y sin secretos", "What leaves, and no secrets"),
        "what": (
            "Se listan los commits exactos que se enviarían y se busca en todo el historial cualquier valor que nunca debe subirse.",
            "The exact commits that would be sent are listed, and the whole history is searched for any value that must never be committed.",
        ),
        "example": (
            "Antes de publicar la puerta del autor: 16 commits, 37 archivos y la clave de prueba en 0 commits.",
            "Before the author gate shipped: 16 commits, 37 files, and the test password found in 0 commits.",
        ),
    },
    {
        "n": 12,
        "lane": "c",
        "icon": "ff",
        "who": "tool",
        "gate": True,
        "commands": ["git push --dry-run"],
        "title": ("¿Avance simple?", "Fast-forward?"),
        "sub": ("Solo agrega commits", "Only adds commits"),
        "what": (
            "Un avance simple significa que el remoto es ancestro del local, así que el push no quita nada.",
            "A fast-forward means the remote is an ancestor of local, so the push removes nothing.",
        ),
        "fail": (
            "Si pide forzar: parar. Integrar con git pull --rebase y revisar otra vez. Nunca git push --force en una rama compartida.",
            "Force required: stop. Integrate with git pull --rebase and check again. Never push --force on a shared branch.",
        ),
        "example": (
            "91f9bb5..0020096 fue un avance simple. Una edición del README en el editor web de GitHub lo habría roto, así que se canceló.",
            "91f9bb5..0020096 was a fast-forward. A README edit made in the GitHub web editor would have broken it, so it was cancelled.",
        ),
    },
    {
        "n": 13,
        "lane": "c",
        "icon": "up",
        "who": "human_tool",
        "commands": ["git push", "git rev-parse HEAD origin/main"],
        "title": ("Aprobar y empujar", "Approve, then push"),
        "sub": ("Una aprobación por push", "One approval per push"),
        "what": (
            "El autor aprueba por escrito los commits listados; tras el push, los dos lados deben mostrar el mismo hash.",
            "The author approves the listed commits in writing; after the push both sides must show the same hash.",
        ),
        "example": (
            "main local y remoto quedaron ambos en 0020096 tras el push.",
            "main local and remote both at 0020096 after the push.",
        ),
    },
    {
        "n": 14,
        "lane": "c",
        "icon": "gear",
        "who": "ci",
        "gate": True,
        "commands": ["gh run list --limit 5", "gh run view --log-failed"],
        "title": ("¿CI en verde?", "CI checks green?"),
        "sub": ("Cada job en el remoto", "Every job on the remote"),
        "what": (
            "GitHub Actions corre las pruebas y la medición de calidad; Streamlit Community Cloud despliega desde main. Una insignia roja en main es lo primero que ve una visita.",
            "GitHub Actions runs the suite and the quality measure; Streamlit Community Cloud deploys from main. A red badge on main is the first thing a visitor sees.",
        ),
        "fail": (
            "Rojo: leer el final del log que falla, entregarlo y volver a la estación 5.",
            "Red: read the end of the failing log, hand it back, return to station 5.",
        ),
        "example": (
            "Lint pasó; pytest falló en 3.11 y 3.12 por una prueba de velocidad (F-10, D-341); calidad no podía abrir el pull request (F-11, ya resuelta).",
            "Lint passed; pytest failed on 3.11 and 3.12 on a speed test (F-10, D-341); quality could not open the pull request (F-11, since resolved).",
        ),
    },
    {
        "n": 15,
        "lane": "c",
        "icon": "check",
        "who": "platform",
        "end": True,
        "commands": ["check the live app, do not assume"],
        "title": ("Desplegado", "Deployed"),
        "sub": ("En vivo desde main", "Live from main"),
        "what": (
            "El panel publicado se reconstruye desde main. Se confirma en el sitio en vivo.",
            "The published app rebuilds from main. Confirm it on the live site.",
        ),
        "example": (
            "Streamlit Cloud se actualiza desde main: el 29-10 la app publicada mostró el menú nuevo e «Informe N° 4».",
            "Streamlit Cloud updates from main: on 29-10 the published app showed the new menu and «Report No. 4».",
        ),
    },
]
# endregion


# region Reading the changes and incidents
def pick(pair: tuple[str, str], language: str) -> str:
    return pair[1] if language == "en" else pair[0]


def read_failures() -> list[dict[str, Any]]:
    """Every occurrence of the failure register with its failure's id, title and station, newest first (D-342)."""
    plan = quality_metrics.read(quality_metrics.FOLDER / "plan_mitigacion.json").get("fallas", [])
    rows = [
        {"id": failure["id"], "falla": failure["falla"], **occurrence}
        for failure in plan
        for occurrence in failure.get("ocurrencias", [])
    ]
    return sorted(rows, key=lambda row: (row["fecha"], row["id"]), reverse=True)


def occurrences_of(station: int, failures: list[dict[str, Any]], language: str, author: bool) -> list[dict[str, str]]:
    """What the panel shows of the register for one station: the professional's four fields; the diagnosis, the author's."""
    shown = []
    for row in failures:
        if row["estacion"] != station:
            continue
        item = {
            "id": row["id"],
            "fecha": row["fecha"],
            "ocurrencia": pick(tuple(row["ocurrencia"]), language),  # type: ignore[arg-type]
            "solucion": pick(tuple(row["solucion"]), language),  # type: ignore[arg-type]
            "comentario": pick(tuple(row["comentario"]), language),  # type: ignore[arg-type]
            "estado": pick(LABELS["open"] if row["estado"] == "abierta" else LABELS["solved"], language),
        }
        if author:
            item["diagnostico"] = pick(tuple(row["diagnostico"]), language)  # type: ignore[arg-type]
        shown.append(item)
    return shown


def build_data(language: str, failures: list[dict[str, Any]], author: bool) -> dict[str, Any]:
    """The JSON the page's script reads: stations in the reader's language, with their register entries."""
    stations = []
    for item in STATIONS:
        stations.append(
            {
                "n": item["n"],
                "lane": item["lane"],
                "icon": ICONS[item["icon"]],
                "title": pick(item["title"], language),
                "sub": pick(item["sub"], language),
                "who": pick(WHO[item["who"]], language),
                "optional": bool(item.get("optional")),
                "gate": bool(item.get("gate")),
                "end": bool(item.get("end")),
                "commands": item["commands"],
                "what": pick(item["what"], language),
                "fail": pick(item["fail"], language) if "fail" in item else "",
                "example": pick(item["example"], language),
                "register": occurrences_of(item["n"], failures, language, author),
            }
        )
    return {"stations": stations, "labels": {key: pick(value, language) for key, value in LABELS.items()}}


# D-449: the map is a flowchart of fixed shape (like D-441, it never changes its form on a small screen): three swimlanes
# that snake left to right, right to left and left to right again, an arrow between every two stations and at each turn,
# and each checkpoint as a diamond with its two exits: the green one goes on, the red one says where the change goes back.
WIDTH, LANE_HEIGHT, LANE_GAP = 1305, 196, 12
COLUMNS = (262, 490, 718, 946, 1174)
TURN_RIGHT, TURN_LEFT = 1292, 140
TILE = 24  # half the side of a station's tile
GATE_EXITS = {
    8: (("verde", "green"), ("rojo → volver a 5", "red → back to 5")),
    12: (("sí", "yes"), ("pide forzar → parar", "asks to force → stop")),
    14: (("verde", "green"), ("rojo → volver a 5", "red → back to 5")),
}


# endregion


# region Layout
def lane_top(lane: str) -> int:
    return "abc".index(lane) * (LANE_HEIGHT + LANE_GAP) + 6


def place(item: dict[str, Any]) -> tuple[int, int]:
    """(x, y) of a station's tile: lane b runs right to left, so the path snakes."""
    index = (item["n"] - 1) % 5
    column = COLUMNS[4 - index] if item["lane"] == "b" else COLUMNS[index]
    return column, lane_top(item["lane"]) + 54


def fit(text: str, size: float, width: float, mono: bool = False) -> str:
    """The text cut with «…» where it would pass `width` pixels at `size`."""
    limit = int(width / (size * (0.61 if mono else 0.52)))
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def wrap(text: str, size: float, width: float) -> list[str]:
    limit, lines = int(width / (size * 0.55)), [""]
    for word in text.split():
        if lines[-1] and len(lines[-1]) + 1 + len(word) > limit:
            lines.append(word)
        else:
            lines[-1] = f"{lines[-1]} {word}".strip()
    return lines


# endregion


# region Drawing the map
def svg_station(item: dict[str, Any], station: dict[str, Any]) -> str:
    """One station: number, tile (a diamond for a checkpoint, a green circle for the end), title, line and command."""
    x, y = place(item)
    kind = "gate" if item.get("gate") else "end" if item.get("end") else "opt" if item.get("optional") else ""
    if kind == "gate":
        tile = f'<rect class="tile" x="{x - 21}" y="{y - 21}" width="42" height="42" rx="7" transform="rotate(45 {x} {y})"/>'
    elif kind == "end":
        tile = f'<circle class="tile" cx="{x}" cy="{y}" r="{TILE}"/>'
    else:
        tile = f'<rect class="tile" x="{x - TILE}" y="{y - TILE}" width="{2 * TILE}" height="{2 * TILE}" rx="12"/>'
    icon = (
        f'<svg class="ico" x="{x - 12}" y="{y - 12}" width="24" height="24" viewBox="0 0 24 24">{item_icon(item)}</svg>'
    )
    command = station["commands"][0] + (f" +{len(station['commands']) - 1}" if len(station["commands"]) > 1 else "")
    command = fit(command, 11, 196, mono=True)
    chip_width = min(206, int(len(command) * 11 * 0.61) + 18)
    badge = (
        f'<g class="badge"><rect x="{x + 18}" y="{y - 34}" width="22" height="16" rx="8"/>'
        f'<text x="{x + 29}" y="{y - 22}">{len(station["register"])}</text></g>'
        if station["register"]
        else ""
    )
    return (
        f'<g class="st {kind} {item["lane"]}" data-n="{item["n"]}" tabindex="0" role="button" '
        f'aria-label="{html.escape(station["label"])}">'
        f'<rect class="hit" x="{x - 108}" y="{y - 40}" width="216" height="168" rx="12"/>'
        f'<circle class="num" cx="{x - 30}" cy="{y - 28}" r="11"/><text class="numt" x="{x - 30}" y="{y - 24}">{item["n"]}</text>'
        f"{tile}{icon}{badge}"
        f'<text class="ttl" x="{x}" y="{y + 52}">{html.escape(fit(station["title"], 15, 220))}</text>'
        f'<text class="sub" x="{x}" y="{y + 70}">{html.escape(fit(station["sub"], 12, 220))}</text>'
        f'<rect class="chip" x="{x - chip_width / 2}" y="{y + 80}" width="{chip_width}" height="21" rx="6"/>'
        f'<text class="cmd" x="{x}" y="{y + 94.5}">{html.escape(command)}</text></g>'
    )


def item_icon(item: dict[str, Any]) -> str:
    return f'<g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[item["icon"]]}</g>'


def svg_paths(language: str) -> str:
    """The arrows: along each lane, the two turns, and the two exits of every checkpoint."""
    parts = []
    for item, after in zip(STATIONS, STATIONS[1:]):
        (x1, y1), (x2, y2) = place(item), place(after)
        lane = after["lane"]
        if item["lane"] == lane:
            step = 1 if x2 > x1 else -1
            start, end = x1 + step * (TILE + 6), x2 - step * (TILE + 10)
            parts.append(f'<path class="go {lane}" d="M{start} {y1} H{end}"/>')
            if item["n"] in GATE_EXITS:
                parts.append(
                    f'<text class="yes" x="{(start + end) / 2}" y="{y1 - 8}">{pick(GATE_EXITS[item["n"]][0], language)}</text>'
                )
        else:
            turn = TURN_RIGHT if x1 > WIDTH / 2 else TURN_LEFT
            side = 1 if turn > x1 else -1
            parts.append(
                f'<path class="go {lane}" d="M{x1 + side * (TILE + 6)} {y1} H{turn} V{y2} H{x2 + side * (TILE + 10)}"/>'
            )
    for number, (_, red) in GATE_EXITS.items():
        x, y = place(STATIONS[number - 1])
        parts.append(f'<text class="no" x="{x}" y="{y + 118}">↺ {html.escape(pick(red, language))}</text>')
    return "".join(parts)


def build_svg(data: dict[str, Any], language: str) -> str:
    height = 3 * LANE_HEIGHT + 2 * LANE_GAP + 10
    lanes = []
    for key, name in LANES:
        top = lane_top(key)
        words = wrap(pick(name, language), 13, 100)
        label = "".join(
            f'<text class="ln" x="62" y="{top + LANE_HEIGHT / 2 - 8 * (len(words) - 1) + 16 * row + 4}">{html.escape(word)}</text>'
            for row, word in enumerate(words)
        )
        lanes.append(
            f'<g class="lane {key}"><rect x="4" y="{top}" width="{WIDTH - 8}" height="{LANE_HEIGHT}" rx="14"/>{label}</g>'
        )
    stations = "".join(svg_station(item, station) for item, station in zip(STATIONS, data["stations"]))
    heads = "".join(
        f'<marker id="h-{key}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 0 10 5 0 10z" class="hd {key}"/></marker>'
        for key, _ in LANES
    )
    return (
        f'<svg class="flow" viewBox="0 0 {WIDTH} {height}" role="group" aria-label="Cambios e incidentes">'
        f"<defs>{heads}</defs>{''.join(lanes)}{svg_paths(language)}{stations}</svg>"
    )


def build_css(palette: dict[str, str]) -> str:
    background = palette["background"].lstrip("#")
    dark = len(background) == 6 and sum(int(background[i : i + 2], 16) for i in (0, 2, 4)) < 3 * 128
    lanes = ("#3d8bfd", "#22c08a", "#8b6cf6") if dark else ("#1f6fe0", "#0f9a6c", "#6c4ee0")
    flag, stop, ok = ("#f2b53a", "#ff8775", "#2fbf6b") if dark else ("#e9a91f", "#c23b2b", "#1f9a55")
    chip = palette["field"]
    return static_files.style(
        "git_workflow.css",
        {
            'var(--go-background)': palette['background'],
            'var(--go-card)': palette['card'],
            'var(--go-chip)': chip,
            'var(--go-strong-text)': palette['strong_text'],
            'var(--go-text)': palette['text'],
            'var(--go-charts-legible-palette-reference-palette-backgro)': charts.legible(
                palette['reference'], palette['background']
            ),
            'var(--go-card-border)': palette['card_border'],
            'var(--go-lanes-0)': lanes[0],
            'var(--go-lanes-1)': lanes[1],
            'var(--go-lanes-2)': lanes[2],
            'var(--go-flag)': flag,
            'var(--go-stop)': stop,
            'var(--go-ok)': ok,
            'var(--go-dark-if-dark-else-light)': 'dark' if dark else 'light',
        },
    )


# The script is a raw string with no HTML tags in its texts (st.iframe runs it, D-173): the DOM is built with the DOM API.
# D-449: the stations are drawn in Python as one SVG; the script only opens and walks the side panel.
SCRIPT = static_files.read("git_workflow.js")


def build_map_html(palette: dict[str, str], language: str, author: bool) -> str:
    """The whole map as one HTML document for st.iframe: texts in the reader's language, diagnoses only for the author."""
    data = build_data(language, read_failures(), author)
    for station in data["stations"]:
        station["label"] = f'{data["labels"]["station"]} {station["n"]}: {station["title"]}'
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    labels = data["labels"]
    return (
        f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        + build_css(palette)
        + "</head><body><main>"
        f'<header><p class="lede">{html.escape(labels["lede"])}</p><ul class="legend">'
        f'<li><span class="k a"></span> {html.escape(labels["legend_arrow"])}</li>'
        f'<li><span class="k"></span> {html.escape(labels["optional"])}: {html.escape(labels["legend_optional"])}</li>'
        f'<li><span class="k g"></span> {html.escape(labels["checkpoint"])}: {html.escape(labels["legend_checkpoint"])}</li>'
        f'</ul></header><div class="map" id="map">{build_svg(data, language)}</div>'
        f"<footer>{html.escape(labels['footer'])}</footer></main>"
        '<div class="scrim" id="scrim" hidden></div>'
        '<aside class="drawer" id="drawer" hidden aria-modal="true" role="dialog" aria-labelledby="dt"></aside>'
        f'<script type="application/json" id="data">{payload}</script><script>{SCRIPT}</script></body></html>'
    )


LOG_LABEL = {
    "diagnosis": ("Diagnóstico", "Diagnosis"),
    "solution": ("Mitigación o solución", "Mitigation or solution"),
    "comment": ("Comentario", "Comment"),
}


# endregion


# region The incident log
def log_summary(row: dict[str, Any], language: str) -> str:
    """The one line of an incident: date, id, what happened and its state."""
    state = pick(LABELS["open"] if row["estado"] == "abierta" else LABELS["solved"], language)
    return f"{row['fecha']} · {row['id']} · {pick(tuple(row['ocurrencia']), language)} · {state}"  # type: ignore[arg-type]


def log_detail(row: dict[str, Any], language: str, author: bool) -> str:
    """What an incident shows when it opens: mitigation or solution and comment for the professional; the diagnosis
    too for the author (D-345)."""
    fields = [("solution", "solucion"), ("comment", "comentario")]
    if author:
        fields.insert(0, ("diagnosis", "diagnostico"))
    items = "".join(
        f"<li><b>{html.escape(pick(LOG_LABEL[name], language))}:</b> "
        f"{html.escape(pick(tuple(row[key]), language))}</li>"  # type: ignore[arg-type]
        for name, key in fields
    )
    station = f"{pick(LABELS['station'], language)} {row['estacion']}"
    ref = f" · {html.escape(row['referencia'])}" if row["referencia"] and row["referencia"] != "desconocido" else ""
    return f'<ul class="cr-detail">{items}<li><b>{html.escape(station)}</b>{ref}</li></ul>'


# endregion
