# Hito 4 · Automatización y publicación

Estado al 11-10-2026: **construido y probado en local; falta ejecutarlo en GitHub.**
Las tareas que dependen de la cuenta del autor están marcadas como pendientes.

## Qué se construyó

| Tarea | Estado | Resultado |
|---|---|---|
| T-22 | Construida, sin ejecutar en GitHub | `.github/workflows/semanal.yml`: agente → ETL → pruebas → guardar base → informe |
| T-23 | Comprobada en local | Si un paso falla, los siguientes no corren y la base no cambia |
| T-24 | Pendiente del autor | Publicar el panel en Streamlit Community Cloud |
| T-25 | Pendiente del autor | Enlace en el README y en el CV |
| T-25b | Terminada | `bi/alerts.py` (K6) y vista «Alertas» del panel |
| T-25c | Construida, sin ejecutar en GitHub | `bi/report.py` y paso del job que lo publica como issue |
| T-25d | Pendiente de comprobar | Correo de GitHub ante una falla del job |
| T-26 | Pendiente | Observar cuatro ejecuciones semanales |

## Cómo comprobarlo en local

1. `pytest -q` → 77 pruebas en verde.
2. `python bi/report.py` → imprime el informe en Markdown.
3. `streamlit run bi/dashboard.py` → vista «Alertas» en el perfil del analista.
4. T-23: con la red cortada, `python agent/agent.py && python etl/etl.py` termina con error en el primer comando y `etl/datos.db` no cambia.

## Pasos del autor en GitHub

1. Crear el repositorio público y subir los commits (uno por tarea).
2. En el repositorio: Settings → Actions → General → Workflow permissions → «Read and write permissions».
3. Actions → `semanal` → Run workflow. Debe terminar en verde, crear un commit «Weekly data update» y un issue «Informe semanal AAAA-MM-DD» (T-22, T-25c).
4. Run workflow otra vez marcando «Forzar una falla después del ETL». Debe terminar en rojo, sin commit nuevo ni issue, y debe llegar un correo de GitHub (T-23, T-25d).
5. En share.streamlit.io: New app → elegir el repositorio, rama principal y archivo `bi/dashboard.py` (T-24).
6. Poner el enlace del panel y los sellos de estado en el README, y el enlace en el CV (T-25, T-06b). Los sellos tienen esta forma:
   `![pruebas](https://github.com/USUARIO/REPOSITORIO/actions/workflows/pruebas.yml/badge.svg)`
7. Revisar cada martes durante cuatro semanas que el job quede en verde (T-26).

## Resultados reales (en local, datos del 11-10-2026)

- Alertas K6: 1.655 series de precio; 43 alertas en la semana del 05-10-2026.
- Mayores movimientos de esa semana: lechuga española segunda en mayorista +49,9 %, pepino de ensalada segunda en feria +49,3 %, repollo morado segunda en mayorista +37,7 %.
- Informe: estado `LOADED`, 397.814 filas leídas, 0 rechazadas, K7 131 de 168.
- T-23 en local: con la descarga bloqueada, el agente terminó con código 1, el ETL no se ejecutó y el hash de `datos.db` fue el mismo antes y después.
- Tamaño: en una simulación con Git, agregar una semana a `datos.db` aumentó el repositorio en unos 0,7 MB.

## Qué quedó pendiente

- **Nada del job se ha ejecutado en GitHub.** El archivo `semanal.yml` es YAML válido y sus comandos se probaron uno por uno en local, pero los permisos, el `git push` y `gh issue create` solo se comprueban allí.
- **Día y hora del job:** martes 12:00 UTC (09:00 en Chile). El diseño pide ajustarlo observando cuándo publica ODEPA.
- **Alertas en productos muy estables:** un cambio de 1 % puede ser alerta (por ejemplo marraqueta +0,9 %). Recalibrar es T-30.
- **T-06b:** los sellos de estado necesitan la dirección del repositorio.
- **`datos.db` de esta entrega** se generó en una carpeta temporal y se copió a `etl/`. Ejecutar `python etl/etl.py` en el computador del autor lo confirma. `etl/datos.db-journal` (vacío) se puede borrar.
