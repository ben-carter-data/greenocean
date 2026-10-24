# Manual de operación

Para quien opera el proyecto sin ser técnico: qué pasa solo, qué hay que revisar y qué hacer si algo falla. Se lee en GitHub, desde la página GitHub del panel.

## Qué pasa cada martes

El job semanal (`.github/workflows/semanal.yml`) corre solo cada martes a las 12:00 UTC: las 09:00 en el horario de verano de Chile y las 08:00 en el de invierno. También se puede lanzar a mano: desde «DevOps y seguridad» → «Centro de operación» con el botón «Ejecutar pipeline ahora» (pide la clave de control), o desde GitHub. Hace, en orden:

1. **Año vigente:** calcula el año en curso, que fija la clave de la caché.
2. **Caché:** recupera de la caché de GitHub Actions los CSV de los años cerrados, que ya no cambian (D-047).
3. **Descarga:** el agente de ingesta (`agent/agent.py`) baja de ODEPA el año en curso y los años cerrados que no estén en la caché, revisa que cada archivo traiga las columnas esperadas y anota su huella SHA-256 en `manifest.json`.
4. **ETL de respaldo:** `etl/etl.py` guarda las filas sin cambios en el aterrizaje (`etl/raw.db`) y construye el respaldo `etl/datos.db` con las reglas de negocio.
5. **dbt build:** `etl/pipeline.py` copia el aterrizaje al bronce en Parquet, descarga el IPC del INE y dbt construye y prueba todos los modelos. Solo si todo pasa, y si la carga leyó al menos el 90 % de las filas de la anterior, reemplaza `etl/datos.duckdb`.
6. **Falla simulada:** solo corre cuando una ejecución manual desde GitHub la pide, para comprobar que la base publicada no cambia.
7. **Pruebas:** corre todas las pruebas contra la base nueva, incluida la paridad entre el respaldo y la base servida.
8. **Guardar:** hace un commit «Weekly data update» con `etl/datos.db`, `etl/datos.duckdb` y `agent/downloads/manifest.json`. El panel publicado lo lee uno o dos minutos después.
9. **Informe:** crea un issue «Informe semanal AAAA-MM-DD» con el estado de la carga y las alertas de la semana.

Si un paso falla, los siguientes no se ejecutan: la base del repositorio queda como estaba y no se publica informe (D-034). El dibujo de estos pasos, con su línea en el workflow, está en «Centro de operación» → «CI/CD».

## Cómo leer un aviso rojo

| Dónde | Qué se ve |
|---|---|
| «Centro de operación» del panel | El logo del paso que falló queda en rojo con su explicación; «Log del paso» abre en GitHub la línea exacta de ese paso. |
| Correo de GitHub | Llega un correo «Run failed: semanal» a la cuenta del autor. |
| Informe semanal | Esa semana no aparece un issue nuevo. |
| «Calidad y auditoría» del panel | La última carga sigue siendo la de la semana anterior. |
| Log del paso que falló, en GitHub | El mensaje exacto. |

La tabla `etl_run` registra cada carga, pero una carga fallida queda escrita solo en la máquina de GitHub, que no se guarda. Por eso el mensaje de una falla se lee en el log del paso, no en el panel.

### Qué significa que falle cada paso y qué hacer

| Paso | Qué suele significar | Qué hacer |
|---|---|---|
| Restore the closed-year files | Un problema de GitHub con la caché. | Volver a lanzar el job; si la caché no está, la descarga baja todos los años. |
| Download the ODEPA files | ODEPA no respondió (`DOWNLOAD_ERROR`) o cambió las columnas de un archivo (`UNEXPECTED_HEADER`). | Si es `DOWNLOAD_ERROR`, esperar unas horas y volver a lanzar. Si es `UNEXPECTED_HEADER`, ODEPA cambió el formato: hay que revisar el archivo y adaptar el código. |
| Run the ETL (SQLite backup) | Un control de calidad detuvo la carga: `TOO_FEW_ROWS` (archivo truncado), `MISSING_WEEKS` (falta una semana que no está entre los huecos conocidos, D-042), `UNKNOWN_REGION` o `UNKNOWN_CHANNEL` (ODEPA agregó una región o un canal) o `DUPLICATE_KEYS` (precios repetidos). | Revisar en ODEPA si el archivo cambió. Un canal o una región nuevos se agregan a las listas del ETL; una semana que falta en la fuente se agrega a los huecos conocidos con su decisión. |
| Build the data warehouse with dbt | Falló un modelo o una prueba de dbt, o la carga leyó menos del 90 % de la anterior (`TOO_FEW_ROWS`). | Leer en el log qué modelo o qué prueba falló; suele nombrar la tabla y la regla. |
| Run the tests against the new database | Los datos nuevos no cumplen algo que el código da por hecho, o el respaldo y la base servida no dan las mismas cifras. | Leer qué prueba falló en el log; suele indicar el producto o la semana. |
| Save the updated database | GitHub no aceptó el commit: permisos o un archivo demasiado grande. | Revisar Settings → Actions → Workflow permissions («Read and write») y el tamaño de las bases (ver límites). |
| Publish the weekly report | No se pudo crear el issue. | Revisar los permisos; los datos ya quedaron guardados. |

### Fallas del panel publicado

| Qué se ve | Qué significa | Qué hacer |
|---|---|---|
| Después de un push, una página muestra `AttributeError` en producción | Streamlit Cloud mezcló archivos nuevos con otros que tenía en memoria (ocurrió el 12-10-2026; el código en GitHub estaba bien). | Abrir el panel, «Manage app» (abajo a la derecha) → ⋮ → **Reboot**. Esperar uno o dos minutos. |
| «Centro de operación» dice «GitHub no respondió (…)» | El mensaje trae la causa real. La más común: GitHub permite 60 consultas por hora sin clave, compartidas por todas las apps del mismo servidor. | Nada: el panel muestra la última respuesta guardada o, si no hay, el estado de la última carga guardada en la base, y vuelve a preguntar cada 5 minutos. Con el token configurado el límite sube. |

## Tareas del autor y tareas automáticas

**Automáticas, sin intervención:** descarga, aterrizaje, construcción con dbt, controles de calidad, pruebas, guardar la base, informe semanal, correo si algo falla, caché de los años cerrados y actualización del panel publicado.

**Del autor:**

- **Cada martes:** mirar el «Centro de operación» o el correo. Si está en verde, no hay nada que hacer.
- **Cada enero:** agregar a `agent/input.csv` las dos líneas del año nuevo (mayorista y consumidor), con la URL de descarga que publica ODEPA en la página de cada conjunto de datos.
- **Respaldar `agent/downloads`:** los CSV descargados no se suben al repositorio (D-020) y la caché de GitHub no es un respaldo, porque se borra si no se usa en 7 días. Conviene copiar esa carpeta a otro disco de vez en cuando.
- **Renovar el token de GitHub** del botón «Ejecutar pipeline ahora» antes de que venza: el panel avisa cuando faltan menos de 14 días (D-038).

## Administración y enlaces

Los enlaces del proyecto están en la página GitHub, que abre el logo de GitHub al pie del menú: el código, las ejecuciones, los informes, el historial de cambios y los documentos (este manual y las decisiones). Las fuentes (ODEPA e INE) están en el menú, en «Fuentes de datos».

En el «Centro de operación», «Acceso del autor» pide la clave de control (secreto `CONTROL_CODE` del panel) y se abre con Enter. No hay límite de intentos: la clave solo evita ejecuciones accidentales (D-249). Con la clave correcta aparecen el botón «Ejecutar pipeline ahora», el aviso del vencimiento del token y los enlaces del autor (tokens de GitHub y administración de la app en Streamlit). El panel nunca muestra el token ni una parte de él.

**La clave evita ejecuciones accidentales; no es la barrera principal.** Con el botón, lo máximo que se puede hacer es lanzar el workflow. Los enlaces de administración llevan a páginas de GitHub y de Streamlit que piden el inicio de sesión del autor: quien vea la tarjeta sin esa cuenta no puede cambiar nada. Lo que protege el proyecto es ese inicio de sesión (con verificación en dos pasos) y que el token tenga solo el permiso de lanzar el workflow de este repositorio. La arquitectura completa está en «Arquitectura de seguridad».

## Límites conocidos

- **Tamaño de las bases:** GitHub avisa cuando un archivo pasa de 50 MB y lo rechaza sobre 100 MB. El tamaño real de `etl/datos.duckdb` y de `etl/datos.db` se ve en «Modelo de datos» → «Dónde viven los datos».
- **Historial de Git:** cada commit semanal agrega al historial una versión nueva de las dos bases. GitHub recomienda repositorios de menos de 1 GB.
- **Cuándo cambiar de arquitectura:** con datos públicos, semanales y de pocos megabytes, no se usa un data warehouse en la nube (ADR-31). La página «Escalabilidad» dice qué umbrales lo justificarían.
- **Caché de GitHub:** se borra si no se usa en 7 días; algunas semanas el job descargará todos los años. Funciona igual, solo tarda más.

## Glosario

| Término | Qué es en este proyecto |
|---|---|
| Pipeline | El flujo completo de cada martes, de ODEPA al panel. |
| Workflow / job semanal | El archivo `semanal.yml` de GitHub Actions que ejecuta el pipeline. |
| Cron | La programación del job semanal: cada martes a las 12:00 UTC. |
| Ejecución (run) | Una pasada completa del job semanal. |
| Ingesta / agente de ingesta | `agent/agent.py`: descarga y valida los archivos de ODEPA. |
| ETL | `etl/etl.py`: limpieza y reglas de negocio para el respaldo `etl/datos.db`. |
| Bronce, plata, oro | Las capas: aterrizaje en `etl/raw.db` y bronce en Parquet; plata en los modelos staging e intermedio de dbt; oro en los marts, el modelo estrella. |
| Data warehouse / modelo estrella | `etl/datos.duckdb`: la base servida, con los precios semanales listos para analizar. |
| Data quality checks | Los controles que detienen la carga si algo no cuadra. |
| Alertas / notificaciones | Las alertas K6 de precios y el correo de GitHub ante una falla. |
| Tests / CI | Las pruebas automáticas; `pruebas.yml` las corre en cada cambio subido al repositorio. |

## Recorrido del proyecto

El menú lateral reúne las páginas en cinco grupos:

1. **Negocio · BI:** «Resumen semanal» (qué se movió esta semana y qué es inusual) y «Precios e inflación» (qué familias de alimentos subieron más o menos que el IPC de alimentos del INE).
2. **Ingeniería de datos:** «Pipeline y linaje» (el recorrido por capas y el linaje de dbt), «Modelo de datos» (modelo estrella, entidad-relación, dónde viven los datos y cruces entre bases), «Calidad y auditoría» (los once indicadores, las puertas de calidad y los controles de auditoría), «Consultas SQL» (un estudio SQL de solo lectura con consultas de ejemplo) y «SAD · Arquitectura».
3. **DevOps y seguridad:** «Centro de operación» (despliegue, operación, CI/CD y monitoreo), «Arquitectura de seguridad» y «Plan de pruebas de seguridad».
4. **Stack y evidencia:** el diagrama de arquitectura del stack (qué es cada herramienta, cuándo actúa y con cuáles se conecta) y las cifras que lo respaldan.
5. **Análisis de negocio · BA:** «PRD · Requisitos del producto», «ADR · Decisiones de arquitectura» y «Escalabilidad».

Al pie del menú están «Apariencia» (Corporativo, Vantablack, Blue Light y Dark Grey) y el logo de GitHub. Cada documento tiene el botón «Imprimir o guardar como PDF», que imprime la página tal como se ve. Las ayudas ⓘ y las explicaciones de los diagramas se leen al pasar el cursor.
