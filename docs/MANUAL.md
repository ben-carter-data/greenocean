# Manual de operación

Para quien opera el proyecto sin ser técnico: qué pasa solo, qué hay que revisar y qué hacer si algo falla. El panel muestra este archivo en «El proyecto» → «Cómo funciona».

## Qué pasa cada martes

El job semanal (`.github/workflows/semanal.yml`) corre solo cada martes a las 12:00 UTC: las 09:00 en el horario de verano de Chile y las 08:00 en el de invierno. También se puede lanzar a mano desde GitHub o con el botón «Ejecutar ahora» del Centro de control. Hace, en orden:

1. **Prepara el entorno:** descarga el código del repositorio e instala Python y las librerías.
2. **Recupera los años cerrados de la caché** (D-047): los archivos de años anteriores no cambian y se guardan en la caché de GitHub Actions.
3. **Ingesta:** el agente de ingesta (`agent/agent.py`) descarga de ODEPA el año en curso, y los años cerrados que no estén en la caché. Revisa que cada archivo tenga las columnas esperadas.
4. **ETL** (`etl/etl.py`): copia los archivos a la capa bronce (`raw.db`), los limpia, aplica las reglas de negocio y pasa los data quality checks. Si un check falla, no carga nada.
5. **Tests:** corre todos los tests contra la base nueva.
6. **Guarda el data warehouse:** hace un commit «Weekly data update» con `etl/datos.db` y `agent/downloads/manifest.json`. El panel publicado lo lee uno o dos minutos después.
7. **Publica el informe:** crea un issue «Informe semanal AAAA-MM-DD» con el estado de la carga y las alertas de la semana.

Si un paso falla, los siguientes no se ejecutan: el data warehouse del repositorio queda como estaba y no se publica informe (D-034).

## Cómo leer un aviso rojo

Hay cinco lugares donde se nota una falla:

| Dónde | Qué se ve |
|---|---|
| Centro de control del panel | La última ejecución aparece como «Falla»; «detalle» abre la ejecución en GitHub. |
| Correo de GitHub | Llega un correo «Run failed: semanal» a la cuenta de la autora. |
| Informe semanal | Esa semana no aparece un issue nuevo. |
| Calidad de datos del panel | La fecha de la última carga sigue siendo la de la semana anterior. |
| Log del paso que falló, en GitHub | El mensaje exacto. Si falló el ETL, empieza con «Quality checks failed, nothing was loaded». |

La tabla `etl_run` registra cada ejecución, pero una ejecución con falla queda escrita solo en la base del servidor de GitHub, que no se guarda. Por eso el mensaje de una falla se lee en el log del paso, no en el panel.

### Qué significa que falle cada paso y qué hacer

| Paso | Qué suele significar | Qué hacer |
|---|---|---|
| Restore the closed-year files | Un problema de GitHub con la caché. | Volver a lanzar el job; si la caché no está, la ingesta descarga todo. |
| Download the ODEPA files | ODEPA no respondió (`DOWNLOAD_ERROR`) o cambió las columnas de un archivo (`UNEXPECTED_HEADER`). | Si es `DOWNLOAD_ERROR`, esperar unas horas y volver a lanzar. Si es `UNEXPECTED_HEADER`, ODEPA cambió el formato: hay que revisar el archivo y adaptar el código. |
| Run the ETL | Un data quality check detuvo la carga. El mensaje dice cuál: `TOO_FEW_ROWS` (archivo truncado), `MISSING_WEEKS` (falta una semana que no está en la lista de huecos conocidos, D-042), `UNKNOWN_REGION`, `UNKNOWN_CHANNEL` (ODEPA agregó una región o un canal) o `DUPLICATE_KEYS` (precios repetidos). | Revisar en ODEPA si el archivo cambió. Un canal o región nuevos se agregan a las listas del ETL; una semana que falta en la fuente se agrega a los huecos conocidos con su decisión. |
| Run the tests against the new database | Los datos nuevos no cumplen algo que el código da por hecho. | Leer qué test falló en el log; suele indicar el producto o la semana. |
| Save the updated database | GitHub no aceptó el commit: permisos o un archivo demasiado grande. | Revisar Settings → Actions → Workflow permissions («Read and write») y el tamaño de `datos.db` (ver límites). |
| Publish the weekly report | No se pudo crear el issue. | Revisar los permisos; los datos ya quedaron guardados. |

## Tareas de la autora y tareas automáticas

**Automáticas, sin intervención:** descarga, limpieza, reglas, data quality checks, tests, guardar el data warehouse, informe semanal, correo si algo falla, caché de los años cerrados y actualización del panel publicado.

**De la autora:**

- **Cada martes:** mirar el Centro de control o el correo. Si está en verde, no hay nada que hacer.
- **Cada enero:** agregar a `agent/input.csv` las dos líneas del año nuevo (mayorista y consumidor), con la URL de descarga que publica ODEPA en las páginas de cada conjunto de datos (`DISENO.md`, sección 5).
- **Respaldar `agent/downloads`:** los CSV descargados no se suben al repositorio (D-020) y la caché de GitHub no es un respaldo, porque se borra si no se usa en 7 días. Conviene copiar esa carpeta a otro disco de vez en cuando.
- **Renovar la clave de GitHub** del botón «Ejecutar ahora» antes de que venza (D-038).

## Límites conocidos

- **Tamaño de `datos.db`:** GitHub avisa cuando un archivo pasa de 50 MB y lo rechaza sobre 100 MB. Con 2022 a 2026 cargados, medido en una copia el 12-10-2026, la base pesa 33,9 MB sin el índice único (D-046); con el índice pesaba 61,6 MB.
- **Historial de Git:** cada commit semanal del data warehouse agrega unos 5 MB comprimidos al repositorio, según una simulación de cinco semanas: unos 275 MB al año. GitHub recomienda repositorios de menos de 1 GB.
- **Cuándo pasar a PostgreSQL (T-36):** si `datos.db` se acerca a 50 MB o el repositorio a 1 GB, conviene mover el data warehouse a una base gestionada y dejar de guardarlo en Git.
- **Caché de GitHub:** se borra si no se usa en 7 días; algunas semanas el job descargará todos los años. Funciona igual, solo tarda más.

## Glosario

| Término | Qué es en este proyecto |
|---|---|
| Pipeline | El flujo completo de cada martes, de ODEPA al panel. |
| Workflow / job semanal | El archivo `semanal.yml` de GitHub Actions que ejecuta el pipeline. |
| Cron | La programación del job semanal: cada martes a las 12:00 UTC. |
| Ejecución (run) | Una pasada completa del job semanal. |
| Ingesta / agente de ingesta | `agent/agent.py`: descarga y valida los archivos de ODEPA. |
| ETL | `etl/etl.py`: limpieza, reglas de negocio y carga. |
| Staging / capa bronce | `raw.db`: los archivos tal como llegan, sin cambios. Se reconstruye en cada ejecución y no se sube al repositorio. |
| Data warehouse / modelo estrella | `datos.db`: los precios semanales listos para analizar. |
| Data quality checks | Los controles que detienen la carga si algo no cuadra. |
| Alertas / notificaciones | Las alertas K6 de precios y el correo de GitHub ante una falla. |
| Tests / CI | Las pruebas automáticas; `pruebas.yml` las corre en cada cambio subido al repositorio. |
