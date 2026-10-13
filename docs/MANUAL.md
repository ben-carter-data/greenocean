# Manual de operación

Para quien opera el proyecto sin ser técnico: qué pasa solo, qué hay que revisar y qué hacer si algo falla. El panel muestra este archivo en «Inicio» → «Cómo funciona».

## Qué pasa cada martes

El job semanal (`.github/workflows/semanal.yml`) corre solo cada martes a las 12:00 UTC: las 09:00 en el horario de verano de Chile y las 08:00 en el de invierno. También se puede lanzar a mano desde GitHub o con el botón «Ejecutar ahora» de «Operaciones» → «Ejecuciones». Hace, en orden:

1. **Prepara el entorno:** descarga el código del repositorio e instala Python y las librerías.
2. **Recupera los años cerrados de la caché** (D-047): los archivos de años anteriores no cambian y se guardan en la caché de GitHub Actions.
3. **Ingesta:** el agente de ingesta (`agent/agent.py`) descarga de ODEPA el año en curso, y los años cerrados que no estén en la caché. Revisa que cada archivo tenga las columnas esperadas.
4. **ETL** (`etl/etl.py`): copia los archivos a la capa bronce (`raw.db`), los limpia, aplica las reglas de negocio y pasa los data quality checks. Si un check falla, no carga nada.
5. **Tests:** corre todos los tests contra la base nueva.
6. **Guarda el data warehouse:** hace un commit «Weekly data update» con `etl/datos.db` y `agent/downloads/manifest.json`. El panel publicado lo lee uno o dos minutos después.
7. **Publica el informe:** crea un issue «Informe semanal AAAA-MM-DD» con el estado de la carga y las alertas de la semana.

Si un paso falla, los siguientes no se ejecutan: el data warehouse del repositorio queda como estaba y no se publica informe (D-034).

## Qué es real en el diagrama del pipeline

En «Inicio» («Pipeline en vivo») se ve la línea de estado y, en celular, el diagrama en cinco pasos; completo, en «Arquitectura» → «Pipeline». Cada diagrama tiene una sola pestaña en «Arquitectura» y no se repite en otra (D-054, D-056). Mezcla datos reales con un dibujo fijo:

| Real: se lee en cada visita | Representación: no cambia sola |
|---|---|
| La línea «Estado de la última ejecución (fecha y hora) · se actualiza al recargar la página»: la fecha es el inicio de la última ejecución del workflow en GitHub o, si GitHub no responde, de la última carga guardada en `etl_run`. | La estructura: qué pasos hay, en qué orden y por qué flecha pasan los datos. Se dibujó a partir del código (`semanal.yml`, `agent.py`, `etl.py`) y se actualiza a mano si el código cambia. |
| El punto de color de cada paso: verde (OK), azul (en curso), rojo (falla). Un paso sin estado conocido no lleva punto. | Las capas (bronce, plata, oro) y las bandas de orquestación y observabilidad: agrupan los pasos para explicarlos. |
| Las cifras bajo los pasos: años cargados, filas leídas y rechazadas, precios semanales, última semana, próxima ejecución. | Las etiquetas de las flechas (`CSV`, `manifest`, `raw_*`, `plata`, `SQL`): el tipo de dato que pasa, no un contador. |
| El movimiento: los puntos que recorren las flechas y las líneas punteadas solo se mueven mientras hay una ejecución en curso. El resto del tiempo el diagrama queda quieto. | |

El diagrama no se refresca solo: muestra el estado del momento en que se abrió la página. Para ver un cambio, se recarga la página.

La pestaña «DevOps y seguridad» dibuja la infraestructura por plataforma: cada recuadro es un lugar donde corre algo (ODEPA, tu computador, GitHub, Streamlit Community Cloud y los usuarios) y dentro están sus componentes; cada línea dice cómo se comunican (HTTPS · CSV, git push, `st.secrets`, etc.). Sigue las mismas reglas. Son reales el tamaño de `datos.db`, el número de funciones de prueba, los precios de la última semana (lo que agregó el job semanal), la próxima ejecución, la hora de los datos y los puntos de estado de ODEPA, el job, Streamlit y el informe. «Pruebas (CI)» no lleva punto: el panel no consulta el workflow `pruebas.yml`. En pantallas angostas este diagrama se ajusta al ancho y se lee con zoom.

### Zoom en los diagramas

Los tres diagramas de «Arquitectura» (pipeline, modelo de datos e infraestructura) se abren ajustados al ancho y completos. Con dos dedos se acercan (pinch-zoom) y con un dedo, o el mouse, se arrastran dentro de su marco, sin mover el resto de la página. Los botones ＋, － y ⟲, bajo el marco a la derecha, acercan, alejan y vuelven al tamaño original. El zoom redibuja el diagrama a su nuevo tamaño, así que se ve nítido con cualquier acercamiento (hasta 6 veces). En el esquema estrella, al pasar el mouse sobre una tabla, o al tocarla en el celular, el panel de abajo explica qué guarda, cómo se une a `weekly_price` y cuántas filas tiene.

## Cómo leer un aviso rojo

Hay cinco lugares donde se nota una falla:

| Dónde | Qué se ve |
|---|---|
| «Operaciones» → «Ejecuciones» del panel | La última ejecución aparece como «Falla»; «detalle» abre la ejecución en GitHub. |
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

### Fallas del panel publicado

| Qué se ve | Qué significa | Qué hacer |
|---|---|---|
| Después de un push, una página muestra `AttributeError` en producción | Streamlit Cloud mezcló archivos nuevos con otros que tenía en memoria (ocurrió el 12-10-2026; el código en GitHub estaba bien) | Abrir el panel, «Manage app» (abajo a la derecha) → ⋮ → **Reboot**. Esperar uno o dos minutos |
| «Operaciones» → «Ejecuciones» dice «No se pudo consultar GitHub: …» | El mensaje trae la causa real. La más común es «GitHub respondió 403: se agotó el límite de consultas sin clave»: GitHub permite 60 consultas por hora sin clave, compartidas por todas las apps del mismo servidor | Nada: el panel muestra la última respuesta guardada o, si no hay, los estados de la última carga guardada en la base, y vuelve a preguntar cada 5 minutos. Con la clave de «Ejecutar ahora» configurada el límite sube |
| Con un tema claro (Corporativo o Claro) las listas, tablas o bloques de código se ven oscuros, o al revés con Vantablack | El panel cambia el modo base de Streamlit solo, una vez por página; si una versión nueva de Streamlit cambió cómo guarda ese modo, el cambio no ocurre (D-052) | Elegir el modo a mano: ⋮ (arriba a la derecha) → Settings → Light para Corporativo y Claro, Dark para Vantablack |

## Tareas de la autora y tareas automáticas

**Automáticas, sin intervención:** descarga, limpieza, reglas, data quality checks, tests, guardar el data warehouse, informe semanal, correo si algo falla, caché de los años cerrados y actualización del panel publicado.

**De la autora:**

- **Cada martes:** mirar «Operaciones» → «Ejecuciones» o el correo. Si está en verde, no hay nada que hacer.
- **Cada enero:** agregar a `agent/input.csv` las dos líneas del año nuevo (mayorista y consumidor), con la URL de descarga que publica ODEPA en las páginas de cada conjunto de datos (`DISENO.md`, sección 5).
- **Respaldar `agent/downloads`:** los CSV descargados no se suben al repositorio (D-020) y la caché de GitHub no es un respaldo, porque se borra si no se usa en 7 días. Conviene copiar esa carpeta a otro disco de vez en cuando.
- **Renovar la clave de GitHub** del botón «Ejecutar ahora» antes de que venza (D-038).

## Administración y enlaces

Los enlaces del proyecto están en un solo lugar: «Operaciones» → «Enlaces» (código, ejecuciones, informes, historial de cambios, las dos fuentes de ODEPA, este MANUAL y las DECISIONES). Cada uno se abre en una pestaña nueva y tiene un botón «Copiar enlace».

La tarjeta «🔒 Administración» de «Operaciones» → «Ejecuciones» se abre con la clave de control (secreto `CONTROL_CODE` del panel). Muestra: administrar la app en Streamlit (Reboot, secretos, registros), lanzar el workflow en GitHub, crear un token, ver los tokens, el aviso «Tu token vence en X días» (destacado si faltan menos de 14) y el botón «Ejecutar ahora». El panel nunca muestra el token ni una parte de él.

**La clave ordena el acceso, pero no es la seguridad real.** Los enlaces de administración llevan a páginas de GitHub y Streamlit que piden su propio inicio de sesión: quien vea la tarjeta sin tener la cuenta de la autora no puede cambiar nada. Lo que protege el proyecto es el inicio de sesión de GitHub y Streamlit (con verificación en dos pasos) y que el token tenga solo el permiso de lanzar el workflow de este repositorio. La clave sirve para que el botón «Ejecutar ahora» no lo use cualquier visitante del panel público.

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
