# Manual de operación

Para quien opera el proyecto sin ser técnico: qué pasa solo, qué hay que revisar y qué hacer si algo falla. El panel muestra este archivo en «Manual».

## Qué pasa cada martes

El job semanal (`.github/workflows/semanal.yml`) corre solo cada martes a las 12:00 UTC: las 09:00 en el horario de verano de Chile y las 08:00 en el de invierno. También se puede lanzar a mano desde GitHub o con el botón «Ejecutar pipeline ahora» de «DevOps y seguridad» → «Centro de operación». Hace, en orden:

1. **Prepara el entorno:** descarga el código del repositorio e instala Python y las librerías.
2. **Recupera los años cerrados de la caché** (D-047): los archivos de años anteriores no cambian y se guardan en la caché de GitHub Actions.
3. **Ingesta:** el agente de ingesta (`agent/agent.py`) descarga de ODEPA el año en curso, y los años cerrados que no estén en la caché. Revisa que cada archivo tenga las columnas esperadas.
4. **ETL** (`etl/etl.py`): copia los archivos a la capa bronce (`raw.db`), los limpia, aplica las reglas de negocio y pasa los data quality checks. Si un check falla, no carga nada.
5. **Tests:** corre todos los tests contra la base nueva.
6. **Guarda el data warehouse:** hace un commit «Weekly data update» con `etl/datos.db` y `agent/downloads/manifest.json`. El panel publicado lo lee uno o dos minutos después.
7. **Publica el informe:** crea un issue «Informe semanal AAAA-MM-DD» con el estado de la carga y las alertas de la semana.

Si un paso falla, los siguientes no se ejecutan: el data warehouse del repositorio queda como estaba y no se publica informe (D-034).

## Qué es real en el diagrama del pipeline

«Pipeline y arquitectura» muestra el recorrido completo y la infraestructura en una sola
ubicación, con una versión vertical del pipeline para pantallas estrechas. El dashboard
muestra resultados y no contiene diagramas. Los estados y cifras provienen de la última
respuesta disponible; las conexiones representan la estructura del sistema.

| Real: se lee en cada visita | Representación: no cambia sola |
|---|---|
| La línea «Estado de la última ejecución (fecha y hora) · se actualiza al recargar la página»: la fecha es el inicio de la última ejecución del workflow en GitHub o, si GitHub no responde, de la última carga guardada en `etl_run`. | La estructura: qué pasos hay, en qué orden y por qué flecha pasan los datos. Se dibujó a partir del código (`semanal.yml`, `agent.py`, `etl.py`) y se actualiza a mano si el código cambia. |
| El punto de color de cada paso: verde (OK), azul (en curso), rojo (falla). Un paso sin estado conocido no lleva punto. | Las capas (bronce, plata, oro) y las bandas de orquestación y observabilidad: agrupan los pasos para explicarlos. |
| Las cifras bajo los pasos: años cargados, filas leídas y rechazadas, precios semanales, última semana, próxima ejecución. | Las etiquetas de las flechas (`CSV`, `manifest`, `raw_*`, `plata`, `SQL`): el tipo de dato que pasa, no un contador. |
| El estado «En curso» y el pulso de sus nodos identifican una ejecución real en progreso. | El movimiento de puntos por las conexiones ilustra el recorrido. Se activa por defecto y se puede pausar con «Animar el recorrido de los datos»; no significa que haya una carga en curso. |

El diagrama no se refresca solo: muestra el estado del momento en que se abrió la página. Para ver un cambio, se recarga la página.

La sección «Pipeline y arquitectura» dibuja también la infraestructura por plataforma: cada recuadro es un lugar donde corre algo (ODEPA, tu computador, GitHub, Streamlit Community Cloud y los usuarios) y dentro están sus componentes; cada línea dice cómo se comunican (HTTPS · CSV, git push, `st.secrets`, etc.). Sigue las mismas reglas. Son reales el tamaño de `datos.db`, el número de funciones de prueba, los precios de la última semana (lo que agregó el job semanal), la próxima ejecución, la hora de los datos y los puntos de estado de ODEPA, el job, Streamlit y el informe. «Pruebas (CI)» no lleva punto: el panel no consulta el workflow `pruebas.yml`. En pantallas angostas este diagrama se ajusta al ancho y se lee con zoom.

### Zoom en los diagramas

Los diagramas de «Pipeline y arquitectura» y «Modelo de datos» se abren ajustados al ancho y completos. Con dos dedos se acercan (pinch-zoom) y con un dedo, o el mouse, se arrastran dentro de su marco, sin mover el resto de la página. Los botones ＋, － y ⟲, bajo el marco a la derecha, acercan, alejan y vuelven al tamaño original. El zoom redibuja el diagrama a su nuevo tamaño, así que se ve nítido con cualquier acercamiento (hasta 6 veces). En el esquema estrella, al pasar el mouse sobre una tabla, o al tocarla en el celular, el panel de abajo explica qué guarda, cómo se une a `weekly_price` y cuántas filas tiene.

## Cómo leer un aviso rojo

Hay cinco lugares donde se nota una falla:

| Dónde | Qué se ve |
|---|---|
| «Centro de operación» del panel | El logo del paso que falló queda en rojo con su explicación abierta; «Log del paso» abre en GitHub la línea exacta de ese paso. |
| Correo de GitHub | Llega un correo «Run failed: semanal» a la cuenta del autor. |
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
| «Centro de operación» dice «GitHub no respondió (…)» | El mensaje trae la causa real. La más común es «GitHub respondió 403: se agotó el límite de consultas sin clave»: GitHub permite 60 consultas por hora sin clave, compartidas por todas las apps del mismo servidor | Nada: el panel muestra la última respuesta guardada o, si no hay, los estados de la última carga guardada en la base, y vuelve a preguntar cada 5 minutos. Con la clave de «Ejecutar ahora» configurada el límite sube |
| Con un tema claro (Corporativo o Blue Light) las listas, tablas o bloques de código se ven oscuros, o al revés con Vantablack | El panel cambia el modo base de Streamlit solo, una vez por página; si una versión nueva de Streamlit cambió cómo guarda ese modo, el cambio no ocurre (D-052) | Elegir el modo a mano: ⋮ (arriba a la derecha) → Settings → Light para Corporativo y Blue Light, Dark para Vantablack |

## Tareas del autor y tareas automáticas

**Automáticas, sin intervención:** descarga, limpieza, reglas, data quality checks, tests, guardar el data warehouse, informe semanal, correo si algo falla, caché de los años cerrados y actualización del panel publicado.

**Del autor:**

- **Cada martes:** mirar el «Centro de operación» o el correo. Si está en verde, no hay nada que hacer.
- **Cada enero:** agregar a `agent/input.csv` las dos líneas del año nuevo (mayorista y consumidor), con la URL de descarga que publica ODEPA en las páginas de cada conjunto de datos (`DISENO.md`, sección 5).
- **Respaldar `agent/downloads`:** los CSV descargados no se suben al repositorio (D-020) y la caché de GitHub no es un respaldo, porque se borra si no se usa en 7 días. Conviene copiar esa carpeta a otro disco de vez en cuando.
- **Renovar la clave de GitHub** del botón «Ejecutar ahora» antes de que venza (D-038).

## Administración y enlaces

Los enlaces del proyecto están en la página GitHub, que abre el logo de GitHub al pie del menú, agrupados en código y operación (ejecuciones, informes, historial de cambios: el repositorio en sí ya se abre desde la cabecera de la página) y documentos (este MANUAL y las DECISIONES). Cada recurso tiene una descripción y se abre en una pestaña nueva. El explorador de archivos del panel se retiró: se navega el código directamente en el repositorio. Las fuentes (ODEPA e INE) tienen su propia tarjeta en el menú, «Fuentes».

En el «Centro de operación», «Acceso del autor» pide la clave de control (secreto `CONTROL_CODE` del panel) y se abre con Enter. Con la clave correcta aparecen el botón «Ejecutar pipeline ahora», el aviso «Tu token vence en X días» (destacado si faltan menos de 14) y «Enlaces del autor»: los tokens de GitHub y la administración de la app en Streamlit (reinicio, secretos, registros). El panel nunca muestra el token ni una parte de él.

**La clave ordena el acceso, pero no es la seguridad real.** Los enlaces de administración llevan a páginas de GitHub y Streamlit que piden su propio inicio de sesión: quien vea la tarjeta sin tener la cuenta del autor no puede cambiar nada. Lo que protege el proyecto es el inicio de sesión de GitHub y Streamlit (con verificación en dos pasos) y que el token tenga solo el permiso de lanzar el workflow de este repositorio. La clave sirve para que el botón «Ejecutar ahora» no lo use cualquier visitante del panel público.

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


## Recorrido del proyecto

El panel empieza por los datos y se recorre en cinco pasos:

1. **Dashboard**: precios de la semana, gráficos, filtros y ayudas contextuales.
2. **KPIs · Qué medimos**: las ocho medidas, sus fórmulas, ejemplos reales, límites y enlaces al resultado y SQL.
3. **Arquitectura y operación**: pipeline animado, arquitectura por plataforma, modelo estrella, DevOps y seguimiento de las cargas.
4. **Consultas SQL**: un estudio SQL de solo lectura: la tabla completa de precios con filtros por familia, producto, canal, región y año; cinco consultas para decidir (precio frente a la época, canal más barato, inflación frente al IPC, brecha mayorista y calendario de compra); el explorador con las tablas reales y un editor para consultas propias.
5. **Documentación**: una carpeta con tres vistas propias, una por perfil —Business Intelligence, Business Analyst e IT—, cada una con qué resuelve el proyecto, su misión, su alcance, sus indicadores o sus decisiones clave, según a quién le hable; sin SQL ni código.

**GitHub** reúne el código completo, los registros de ejecución, las fuentes originales y los documentos (manual, decisiones). El explorador de archivos del panel se retiró: el código se navega en el repositorio. La navegación al pie de página sigue el orden del recorrido; las vistas de cada sección tienen enlaces directos.

El Dashboard es la página de inicio para todas las visitas. Al recargar se vuelve al resumen principal. El icono de sol o luna en la cabecera abre Apariencia: Corporativo, Vantablack, Blue Light y Dark Grey. Corporativo es la apariencia predeterminada. El botón Volver recupera el punto anterior del proyecto y sus filtros, sin abrir otra ventana. Los rankings de alzas y bajas se muestran juntos; Top N limita cada ranking por separado.

Las tablas y el código se abren bajo demanda. Las ayudas ⓘ se leen al pasar el mouse, enfocar con teclado o tocar el icono.

La administración (ejecutar el job, tokens y administración de la app publicada) queda en «DevOps y seguridad» → «Centro de operación», detrás de la clave de control.


### Calidad y trazabilidad

En **Ingeniería de datos → Calidad y auditoría**, el panel mide en cada carga once indicadores de calidad, cada uno bajo la etapa del pipeline donde se vigila, y muestra los controles de auditoría (origen de los archivos, integridad, paridad SQLite ↔ DuckDB, reconciliación y recálculo independiente); cada control abre su evidencia.

Las huellas SHA-256 solo se consideran verificadas cuando el archivo original está disponible y coincide con el manifiesto. Un archivo ausente queda pendiente. Los controles se actualizan al cambiar la base o los archivos y tienen una caché máxima de cinco minutos al consultar la vista.

La reconciliación de fuente a base, el recálculo independiente de todos los indicadores, la muestra auditada de pantalla y el contraste con otra fuente se identifican como pendientes. Superar los controles disponibles no certifica cada precio publicado por ODEPA.


### Lectura de los dashboards

El resumen y la vista **Esta semana** presentan primero los rankings de alzas y bajas. **Brecha de precio** presenta las diferencias entre consumidor y mayorista de la misma semana, región, producto y unidad. El deslizador **Top N** muestra entre 8 y 20 resultados; las diferencias superiores a +300 % siguen identificadas aparte según la regla de comparabilidad existente.

Bajo cada ranking se muestran los tres primeros resultados del mismo conjunto de datos, con sus precios o porcentajes. El detalle de producto se consulta después del ranking. En Regiones e Histórico se identifica el producto de las curvas o comparaciones antes del gráfico; los controles para cambiarlo quedan debajo. Se omiten los filtros que no afectan a esos gráficos.

Las opciones del header explican su función al pasar el cursor o al recibir foco con el teclado. Las palabras subrayadas de la guía y de las muestras también ofrecen una explicación breve.


### Proporciones y evolución cronológica

El anillo **¿Qué proporción subió o bajó?** cuenta todas las series nacionales comparables de la semana y del grupo seleccionado, sin limitarse al Top N ni ponderar por ventas. Una serie identifica producto, variedad, calidad, unidad y canal. Las series sin comparación con la semana anterior se indican aparte y no forman parte del denominador.

En **Histórico**, la evolución cronológica de los precios aparece antes de las comparaciones estacionales. Cada área representa el precio semanal de un canal del producto seleccionado: las áreas se superponen con transparencia, no se apilan ni se suman. El eje de precios parte de cero, las semanas sin dato interrumpen el trazo y no se muestra una predicción ni una regresión.

### Contexto del precio: qué significa «habitual»

La página «Contexto del precio» (en 01 · Dashboard) responde si el precio de esta semana es normal. **Habitual** es el rango entre el percentil 25 y el 75 del precio de la **misma semana ISO, y la semana antes y después, en los años anteriores** disponibles (hasta tres semanas por año); el año en curso no se usa. Si el precio supera ese rango, está «sobre lo habitual»; si queda por debajo, «bajo lo habitual». Cuando hay menos de dos años anteriores con un precio en esa ventana, la página dice «Sin historia suficiente» en vez de clasificar el precio. La diferencia entre canales solo se menciona en la frase de resumen cuando ella misma queda fuera de su propio rango habitual. «Qué suele pasar» resume el patrón de años anteriores, por canal; no es un pronóstico. «Otros productos … fuera de lo habitual» lista, con el mismo criterio, otros productos de la familia cuyo precio actual se sale de su rango. Para abrir la página con un producto, elígelo en el panel de productos del Resumen o en esa tabla.

### Modelo de datos

La página cabe en una pantalla (1920 × 1080). A la izquierda, el diagrama estrella: `weekly_price` al centro, `dim_date` arriba, `dim_product` a la izquierda, `dim_region` a la derecha, `dim_channel` abajo, y aparte, abajo a la derecha, la auditoría de cargas (`etl_run → rejection`). A la derecha, el detalle de la tabla elegida (con una consulta SQL real) y la lista completa de tablas; elegir una actualiza el detalle y resalta esa tabla en el diagrama.

### Navegación

El menú lateral es la única navegación del proyecto: todas las secciones y subpáginas están siempre desplegadas, sin pestañas ni expanders. Arriba de cada página hay su ruta («Arquitectura y operación › Modelo de datos»), el botón «Volver» y el selector de tema. La alerta de precio tiene su propio botón, fijo al final del menú.

### Mapa regional y disponibilidad

La vista principal del Dashboard cabe en una pantalla. A la izquierda, el mapa de Chile en proporción real: cada región tiene una fila con su nombre y su porcentaje, unida a la región por una línea. Al hacer clic en una región (o en su fila) se selecciona; las familias y la tabla de productos se recalculan para ella, y un segundo clic vuelve a todo Chile. Al hacer clic en una familia, la tabla muestra sus productos, con filtro de canal, orden y acceso al histórico. Para encontrar un producto, escribe el inicio de su nombre o de su variedad en el buscador del panel; no importan mayúsculas ni acentos. El orden «Inusuales» muestra solo las alertas nacionales.

El mapa muestra las 16 regiones con límites geográficos simplificados y nombres visibles. Los colores representan el cambio del mismo producto, variedad, calidad, unidad y canal frente a la semana anterior: rojo subió, azul bajó y gris sin cambio. Una región sin comparación queda sin relleno; esto no implica necesariamente ausencia de precio actual. El resumen diferencia regiones con precio actual y regiones con comparación semanal. La tabla presenta ambos precios, la variación y el motivo de ausencia de comparación para cada región. Cambiar el producto, canal o semana puede cambiar la cobertura; no se asignan precios regionales a ciudades.

### Lectura regional en el dashboard

Sin un producto seleccionado, el dashboard presenta todas las regiones con series comparables de la semana y grupo elegidos. Cada serie mantiene producto, variedad, calidad, unidad y canal constantes entre las dos semanas. El resumen cuenta alzas, bajas y precios iguales, y calcula la mediana de las variaciones individuales; no suma precios ni representa inflación o gasto.

Al elegir un producto, los precios actuales, anteriores y las variaciones regionales se muestran directamente en una tabla compacta. Se incluyen las regiones con precio actual aunque les falte comparación anterior, explicando la ausencia. El mapa completo con nombres queda como complemento dentro de «Ubicar estas regiones en el mapa de Chile».

La cobertura territorial de la base cargada es de nueve regiones con precios válidos en el histórico; las siete restantes no se representan como si tuvieran datos. Esta es la cobertura de los archivos incorporados al proyecto, no una afirmación sobre toda la oferta de datos de ODEPA. La evolución de 12 semanas solo se ofrece al elegir un producto y está dentro de un detalle desplegable; no se presenta una serie de referencia automática al seleccionar «Todos».

## Navegación y lectura de negocio

La cabecera ordena Dashboard, Datos, Alertas, Histórico, KPIs, Pipeline, Modelo y DevOps. Esta semana se integra en Dashboard; las direcciones antiguas de Brechas y Regiones llevan a Datos. Los cálculos canónicos se conservan.

Datos ofrece Precios semanales (incluidos los marcados), Variación semanal regional y Brecha mayorista/consumidor. Son vistas de agregados semanales, no de registros crudos. Comienza con 100 filas por página; admite de 8 a 100. Los filtros y el orden superior se aplican antes de LIMIT/OFFSET. El CSV explícito descarga únicamente la página visible. Ordenar una columna del visor solo reorganiza esa página.

Alertas mantiene K6 nacional: producto, variedad, calidad, unidad y canal, comparado con su rango previo de 12 semanas. No son alertas regionales ni una clasificación por precio absoluto alto. Top N admite de 8 a 100 y comienza en 20; el detalle completo conserva precio anterior, precio actual, regla y alcance.

KPIs muestra todo el recorrido de un indicador de una vez, sin pasos que avanzar: se elige la pregunta de negocio y una línea une 1 · Resultado (cifra grande y estado de la carga), 2 · Contexto (pestañas Alcance, Lógica y Límites) y 3 · Consulta (botón «Desplegar SQL», que abre la consulta en una capa, y enlace al catálogo). K1–K5 muestran una serie de referencia identificada; K6–K8 muestran el alcance operativo especificado. No se fijan metas empresariales inventadas.
