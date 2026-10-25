# Hito 4 · Automatización y publicación

Estado al 12-10-2026: **ejecución manual comprobada en GitHub y panel publicado.**
Pendientes: enlace en el CV a cargo del autor y observación de cuatro martes consecutivos (T-26).

## Qué se construyó

| Tarea | Estado | Resultado |
|---|---|---|
| T-22 | Comprobada en GitHub | `.github/workflows/semanal.yml`: agente → ETL → pruebas → guardar base → informe |
| T-23 | Comprobada en local y GitHub | Si un paso falla, los siguientes no corren y la base no cambia |
| T-24 | Comprobada | Panel publicado; ambos perfiles cargan y el enlace abre sin conexión en navegación privada |
| T-25 | README preparado; CV pendiente del autor | Enlace público agregado al README |
| T-25b | Terminada | `bi/alerts.py` (K6) y vista «Alertas» del panel |
| T-25c | Comprobada en GitHub | `bi/report.py` y paso del job que lo publica como issue |
| T-25d | Comprobada | El autor mostró el correo de GitHub de la falla forzada |
| T-26 | Pendiente | Observar cuatro ejecuciones semanales |

## Cómo comprobarlo en local

1. `pytest -q` → 77 pruebas en verde.
2. `python bi/report.py` → imprime el informe en Markdown.
3. `streamlit run bi/dashboard.py` → vista «Alertas» en el perfil del analista.
4. T-23: con la red cortada, `python agent/agent.py && python etl/etl.py` termina con error en el primer comando y `etl/datos.db` no cambia.

## Resultados reales en GitHub y Streamlit (12-10-2026)

- Repositorio público: [cben6514-boop/monitor-precios-hito1](https://github.com/cben6514-boop/monitor-precios-hito1), rama `main`.
- El workflow `pruebas` terminó en verde sobre el commit inicial `7a69210`, según la verificación de la passation. Permisos de Actions configurados en lectura y escritura.
- **T-23 / T-25d:** [ejecución 38224845969](https://github.com/cben6514-boop/monitor-precios-hito1/actions/runs/38224845969), con la casilla de falla forzada marcada (confirmado por el autor). El agente y el ETL terminaron; «Simulate a failure» falló y los pasos posteriores se omitieron, sin commit ni issue. El autor mostró el correo «Run failed: semanal» recibido en su cuenta.
- **T-22:** [ejecución 38226180308](https://github.com/cben6514-boop/monitor-precios-hito1/actions/runs/38226180308), sin la casilla marcada: `Success`, duración total de 57 segundos.
- Commit automático: [`ed08f4c`, «Weekly data update»](https://github.com/cben6514-boop/monitor-precios-hito1/commit/ed08f4c), de `github-actions[bot]`. Recuperado en local mediante Pull; el asistente comprobó que era el último commit local.
- **T-25c:** [issue #1, «Informe semanal 2026-10-12»](https://github.com/cben6514-boop/monitor-precios-hito1/issues/1), creado por GitHub Actions. El autor mostró el informe: 397.814 filas cargadas, 0 rechazadas, K7 131 de 168 y 43 alertas para la semana del 2026-10-05.
- **T-24:** [panel público](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app/), publicado desde `main`, archivo `bi/dashboard.py`. Se comprobaron las vistas Márgenes del perfil analista y Calidad de datos del perfil Equipo de datos. El autor mostró también el panel abierto en Chrome Incognito sin pedir conexión.
- La vista de calidad publicada mostró estado `LOADED`, fecha `2026-10-12T08:52:08`, 397.814 filas leídas y cargadas, 0 rechazadas y K7 131 de 168 (78,0 %).
- **T-25 / T-06b:** enlace del panel y sellos de `pruebas` y `semanal` preparados en el README; pendientes de commit y push aprobados por el autor.

## Resultados reales (en local, datos del 11-10-2026)

- Alertas K6: 1.655 series de precio; 43 alertas en la semana del 05-10-2026.
- Mayores movimientos de esa semana: lechuga española segunda en mayorista +49,9 %, pepino de ensalada segunda en feria +49,3 %, repollo morado segunda en mayorista +37,7 %.
- Informe: estado `LOADED`, 397.814 filas leídas, 0 rechazadas, K7 131 de 168.
- T-23 en local: con la descarga bloqueada, el agente terminó con código 1, el ETL no se ejecutó y el hash de `datos.db` fue el mismo antes y después.
- Tamaño: en una simulación con Git, agregar una semana a `datos.db` aumentó el repositorio en unos 0,7 MB.

## Qué quedó pendiente

- **T-26:** comprobar cuatro ejecuciones programadas consecutivas en verde, sin intervención. Fechas previstas de revisión: martes **13-10-2026, 20-10-2026, 27-10-2026 y 03-11-2026**. Ninguna se da por cumplida con la ejecución manual del 12-10-2026; registrar el enlace y resultado real de cada ejecución.
- **Día y hora del job:** martes 12:00 UTC. El diseño pide ajustarlo observando cuándo publica ODEPA.
- **T-25:** el autor agrega el enlace del panel al CV.
- **T-06b:** los sellos están preparados; no se ha realizado una prueba deliberadamente rota en GitHub para comprobar el cambio del sello a rojo. La ejecución correcta de `pruebas` sobre `7a69210` sí fue verificada en la passation.
- **Alertas en productos muy estables:** un cambio de 1 % puede ser alerta (por ejemplo marraqueta +0,9 %). Recalibrar es T-30, fuera de este cierre.
- **Hitos 5 y 6:** no iniciados; requieren confirmación del autor después de revisar el hito 4.
