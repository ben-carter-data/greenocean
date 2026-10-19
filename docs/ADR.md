# GreenOcean · Registros de decisiones de arquitectura (ADR)

El registro completo del proyecto, `docs/DECISIONES.md`, tiene más de ciento cuarenta entradas, muchas sobre presentación del panel. Aquí queda solo el subconjunto con peso arquitectónico: las decisiones que definen fuentes, almacenamiento, transformación, calidad, operación y seguridad. Cada ADR cita las entradas de origen; cuando el registro no anota alternativas, se dice. Cuando una entrada no tiene fecha, se indica el hito en que se tomó.

## Índice

| ADR | Título | Estado | Referencia |
|---|---|---|---|
| ADR-01 | Archivos oficiales de ODEPA, sin scraping | Aceptada | D-001, D-002 |
| ADR-02 | SQLite, GitHub Actions y Streamlit Community Cloud | Aceptada | D-012, D-019 |
| ADR-03 | Repositorio público con licencia MIT | Aceptada | D-013, D-036 |
| ADR-04 | Capas bronce y oro; los datos crudos no se suben | Aceptada | D-020, D-023 |
| ADR-05 | Clave exacta producto + variedad + calidad | Aceptada | D-007, D-030 |
| ADR-06 | Conversión de unidades por lectura literal del texto | Aceptada | D-008, D-026 |
| ADR-07 | Grano semanal por lunes, ponderado por volumen | Aceptada | D-006, D-027 |
| ADR-08 | Toda fila inválida se rechaza con motivo y se conserva | Aceptada | D-025 |
| ADR-09 | Atípicos marcados con una mediana por fuente | Aceptada | D-028 |
| ADR-10 | Carga idempotente por reconstrucción completa | Aceptada | D-024 |
| ADR-11 | Controles de calidad antes de cargar | Aceptada | D-029 |
| ADR-12 | Lista fija de huecos conocidos de la fuente | Aceptada | D-042 |
| ADR-13 | Sin índice único en la tabla de hechos | Aceptada | D-046 |
| ADR-14 | Caché de años cerrados en GitHub Actions | Aceptada | D-047 |
| ADR-15 | El workflow semanal no guarda nada si un paso falla | Aceptada | D-017, D-034 |
| ADR-16 | Indicadores como consultas con nombre | Reemplazada en parte por ADR-17 | D-031 |
| ADR-17 | El panel filtra en SQLite solo el producto elegido | Aceptada | D-050 |
| ADR-18 | K6 en Python con una versión SQL gemela | Aceptada | D-033, D-049 |
| ADR-19 | Modelo estrella con dimensión de fechas | Aceptada | D-023, D-095 |
| ADR-20 | Base en solo lectura y secretos fuera del código | Aceptada | D-038, D-041, D-053 |
| ADR-21 | Variación y alertas sobre las mismas regiones | Aceptada | D-144, D-145 |
| ADR-22 | Rango habitual P25–P75 por semana ISO ±1 | Aceptada | D-094, D-098, D-146 |
| ADR-23 | Revisión de pertinencia: solo conclusiones que se sostienen | Aceptada | D-146 |
| ADR-24 | K5, rezago descriptivo por región y canal | Retirada por ADR-25 | D-011, D-048 |
| ADR-25 | Retiro de K5 del producto | Aceptada | D-146 |
| ADR-26 | Consolas SQL y Python en el panel | Reemplazada por ADR-27 | D-126, D-135 |
| ADR-27 | GitHub es la fuente de verdad del código | Aceptada | D-143, D-148 |
| ADR-28 | Ejecución manual: el mismo workflow, tras una clave | Aceptada | D-038, D-149 |
| ADR-29 | Sin vigilante de archivos en el servidor publicado | Aceptada | D-109 |

---

## ADR-01 · Archivos oficiales de ODEPA, sin scraping

- **Estado:** Aceptada.
- **Fecha:** no registrada (diseño inicial).
- **Contexto:** los precios mayoristas y al consumidor ya existen como CSV anuales en el portal de datos abiertos de ODEPA, con licencia Creative Commons Atribución.
- **Decisión:** obtener los datos solo de esos archivos. La etapa 1 usa dos fuentes; comercio exterior queda para después.
- **Alternativas:** scraping de supermercados; registros públicos de salud; partir con tres fuentes.
- **Consecuencias:** ingesta estable y rápida, sin depender de la estructura de una página. No se responde de qué países proviene cada producto.
- **Referencia:** D-001, D-002.

## ADR-02 · SQLite, GitHub Actions y Streamlit Community Cloud

- **Estado:** Aceptada.
- **Fecha:** no registrada (diseño inicial).
- **Contexto:** el proyecto debe correr sin costo, sin servidor que mantener y poder clonarse y ejecutarse en cualquier equipo.
- **Decisión:** base en archivo SQLite, job programado en GitHub Actions y panel en Streamlit Community Cloud. No se agregan nube, contenedores ni modelos predictivos que no respondan mejor una pregunta.
- **Alternativas:** servidor propio; base en la nube; Power BI, que no se abre desde un enlace público sin licencia.
- **Consecuencias:** coste cero y una sola pieza de almacenamiento. Se renuncia a concurrencia y volumen, suficientes para datos semanales de este tamaño. PostgreSQL gestionado queda como alternativa documentada.
- **Referencia:** D-012, D-019.

## ADR-03 · Repositorio público con licencia MIT

- **Estado:** Aceptada.
- **Fecha:** no registrada (diseño inicial y cierre del hito 4).
- **Contexto:** el proyecto es un portafolio y su código debe poder revisarse y reutilizarse.
- **Decisión:** código, data warehouse y panel abiertos, con licencia MIT.
- **Alternativas:** repositorio privado o mixto; repositorio sin licencia.
- **Consecuencias:** la autoría queda en el historial y GitHub Actions es gratuito. Se pierde exclusividad, aunque todo puede rehacerse con los mismos datos abiertos.
- **Referencia:** D-013, D-036.

## ADR-04 · Capas bronce y oro; los datos crudos no se suben

- **Estado:** Aceptada.
- **Fecha:** no registrada (hitos 1 y 2).
- **Contexto:** cada CSV anual pesa entre 32 y 46 MB y la base cruda de un solo año 105 MB; GitHub rechaza archivos de más de 100 MB.
- **Decisión:** la capa bronce (`raw.db`, definida en `raw_schema.sql`) guarda las filas tal como llegan y se reconstruye en cada ejecución, fuera del repositorio. Solo se suben el data warehouse (`datos.db`, definido en `schema.sql`) y el registro de descargas. Cada base tiene su propio esquema.
- **Alternativas:** subir todo; almacenamiento de archivos grandes; un único archivo de esquema.
- **Consecuencias:** el repositorio se mantiene manejable. Quien clone el proyecto debe ejecutar la ingesta para tener los datos crudos, y la auditoría que los necesita se omite donde no están.
- **Referencia:** D-020, D-023.

## ADR-05 · Clave exacta producto + variedad + calidad

- **Estado:** Aceptada.
- **Fecha:** no registrada (diseño inicial y hito 2).
- **Contexto:** la prueba inicial mostró que mezclar calidades infla la diferencia entre mayorista y consumidor.
- **Decisión:** el margen solo se calcula entre filas con la misma clave exacta. La papa queda sin margen porque sus calidades no coinciden entre fuentes.
- **Alternativas:** cruzar solo por nombre de producto; una tabla manual de equivalencia de calidades (queda como mejora T-37).
- **Consecuencias:** márgenes comparables. Parte de las claves del consumidor queda sin margen; el criterio de aceptación 5 se cumple para cuatro de los cinco productos de prueba.
- **Referencia:** D-007, D-030.

## ADR-06 · Conversión de unidades por lectura literal del texto

- **Estado:** Aceptada.
- **Fecha:** no registrada (diseño inicial y hito 2).
- **Contexto:** el mayorista vende por caja, bandeja o malla; el consumidor compra por kilo, unidad o envase.
- **Decisión:** una unidad se convierte si empieza por kilo, unidad o litro, o si su texto trae un solo número seguido de una medida (kilos, unidades, gramos, ml o litros). La misma función se aplica a las dos fuentes. Lo que no declara cantidad se conserva sin precio comparable y con su marca.
- **Alternativas:** tabla manual de equivalencias; limitarse a kilo y unidad; interpretar envases con dos números; excluir esas filas; estimar pesos.
- **Consecuencias:** una sola regla revisable, con las 147 unidades reales del archivo 2026 en una prueba. Aparece una tercera unidad, litro. Atados, docenas, matas y rangos quedan sin margen.
- **Referencia:** D-008, D-026.

## ADR-07 · Grano semanal por lunes, ponderado por volumen

- **Estado:** Aceptada.
- **Fecha:** no registrada (diseño inicial y hito 2).
- **Contexto:** el mayorista es diario y el consumidor semanal.
- **Decisión:** cada día mayorista se asigna al lunes de su semana y se agrega con un promedio ponderado por la columna de volumen tal como se publica.
- **Alternativas:** repartir el precio semanal del consumidor en días; convertir el volumen a kilos antes de ponderar.
- **Consecuencias:** las dos fuentes comparten grano. Se pierde el detalle diario en los indicadores, y cuando una clave mezcla envases de distinto tamaño el grande pesa menos de lo que debería.
- **Referencia:** D-006, D-027.

## ADR-08 · Toda fila inválida se rechaza con motivo y se conserva

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 2).
- **Contexto:** un pipeline sin supervisión no puede borrar datos en silencio.
- **Decisión:** las filas con precio no positivo, mínimo sobre máximo, volumen no positivo, valor ilegible o fecha fuera del año van a `rejection` con su motivo y la fila original. Una semana pertenece al archivo si toca su año.
- **Alternativas:** validar solo por fecha de inicio; dar peso 1 a las filas sin volumen.
- **Consecuencias:** en cada carga, leídas = cargadas + rechazadas. Solo se guardan los rechazos de la última ejecución; de las anteriores queda su número en `etl_run`.
- **Referencia:** D-025, RN-11; D-024 para la retención.

## ADR-09 · Atípicos marcados con una mediana por fuente

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 2).
- **Contexto:** el precio al consumidor es sistemáticamente mayor que el mayorista; una mediana común marcaría como atípico un margen alto, que es lo que se quiere medir.
- **Decisión:** un precio cinco veces mayor o menor que la mediana del producto, unidad y semana dentro de su misma fuente se marca `ATIPICO`, se conserva y sale de los indicadores.
- **Alternativas:** mediana común a las dos fuentes; factor 3 o 10.
- **Consecuencias:** detecta errores evidentes. La mediana aún mezcla variedades y calidades y marca algunos precios probablemente reales.
- **Referencia:** D-028.

## ADR-10 · Carga idempotente por reconstrucción completa

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 2).
- **Contexto:** RN-14 exige que ejecutar dos veces la misma semana no duplique filas; la capa bronce ya se reconstruye entera.
- **Decisión:** cada carga borra y reescribe la tabla de hechos dentro de una transacción. Las dimensiones solo reciben filas nuevas, así sus identificadores no cambian.
- **Alternativas:** actualizar semana por semana con claves; acumular los rechazos de todas las ejecuciones.
- **Consecuencias:** imposible duplicar, y la semana que cruza dos años se resuelve sin lógica especial. Cada carga recalcula todo.
- **Referencia:** D-024.

## ADR-11 · Controles de calidad antes de cargar

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 2).
- **Contexto:** los archivos de un año solo crecen; una baja fuerte indica un archivo truncado.
- **Decisión:** la carga se detiene si las filas leídas bajan del 90 % de la última carga correcta, si falta una semana intermedia, o si aparece una región fuera de 1 a 16 o un canal desconocido. La ejecución queda como `FAILED` con su mensaje.
- **Alternativas:** un límite superior de filas; rangos fijos por semana.
- **Consecuencias:** no se necesitan cifras fijadas a mano. La primera ejecución no tiene con qué compararse y un archivo duplicado no se detecta por conteo.
- **Referencia:** D-029.

## ADR-12 · Lista fija de huecos conocidos de la fuente

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 5).
- **Contexto:** el archivo de consumidor 2022 no tiene la semana del 02-05-2022; dos descargas dieron la misma huella, así que el hueco es de la fuente. Sin excepción, el histórico no podía cargarse.
- **Decisión:** el control de semanas faltantes acepta una lista fija de huecos conocidos, hoy con esa única entrada. Cualquier otra semana faltante sigue deteniendo la carga.
- **Alternativas:** revisar huecos solo en el año en curso; quitar el control; rellenar con el promedio de las semanas vecinas.
- **Consecuencias:** queda escrito qué falta y por qué. Esa semana no tiene precio al consumidor ni margen, y ningún cálculo inventa un valor para ella.
- **Referencia:** D-042.

## ADR-13 · Sin índice único en la tabla de hechos

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 5).
- **Contexto:** con 2022–2026 cargados, `datos.db` pesaba 61,6 MB, sobre el aviso de 50 MB de GitHub; el índice ocupaba 24 MB y no aceleraba las consultas.
- **Decisión:** se elimina el índice único. El ETL agrega un control de claves duplicadas que detiene la carga, y cada carga correcta compacta el archivo.
- **Alternativas:** dejar el índice y aceptar el aviso; cargar menos años; adelantar la migración a PostgreSQL.
- **Consecuencias:** la base pesa unos 34 MB y el historial de Git crece la mitad. La base misma ya no rechaza un duplicado escrito por otro programa; la protección queda en el ETL.
- **Referencia:** D-046.

## ADR-14 · Caché de años cerrados en GitHub Actions

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 5).
- **Contexto:** descargar todos los años cada martes son unos 490 MB, aunque los años cerrados no cambian.
- **Decisión:** los CSV se guardan en la caché de Actions con una clave formada por el año en curso y la lista de recursos. La ingesta salta un año cerrado que ya está; si la caché venció, descarga todo sin fallar.
- **Alternativas:** descargar todo cada semana; cargar el histórico una vez y procesar solo el año en curso.
- **Consecuencias:** se baja solo el año en curso y el ETL no cambia. Algunas semanas se descarga todo, y una corrección de ODEPA en un año cerrado entra recién cuando la caché se renueva.
- **Referencia:** D-047.

## ADR-15 · El workflow semanal no guarda nada si un paso falla

- **Estado:** Aceptada.
- **Fecha:** no registrada (diseño inicial y hito 4).
- **Contexto:** la base del repositorio es lo que lee el panel; una carga a medias sería visible para todos.
- **Decisión:** el workflow ejecuta en orden ingesta, ETL, pruebas, commit de la base e informe. GitHub Actions se detiene en el primer paso que falla. El informe es un issue y el aviso de falla es el correo de GitHub.
- **Alternativas:** guardar la base en otra rama o como artefacto; correo propio o mensajería externa.
- **Consecuencias:** la base solo se reemplaza con una carga que pasó controles y pruebas, sin servidores ni claves externas. El historial de Git crece con cada commit semanal.
- **Referencia:** D-017, D-034.

## ADR-16 · Indicadores como consultas con nombre

- **Estado:** Reemplazada en parte por ADR-17.
- **Fecha:** no registrada (hito 3).
- **Contexto:** cada cifra debe poder comprobarse ejecutando su consulta directamente en SQLite.
- **Decisión:** `bi/queries.sql` contiene una consulta por indicador, identificada por su nombre; el panel las lee por nombre. El precio nacional es el promedio simple de las regiones con dato. La parte que decía que el panel lee cada indicador completo y filtra en memoria fue reemplazada.
- **Alternativas:** consultas con parámetros por producto; ponderar regiones por población; vistas SQL dentro de la base.
- **Consecuencias:** una sola definición por indicador, legible y reproducible.
- **Referencia:** D-031.

## ADR-17 · El panel filtra en SQLite solo el producto elegido

- **Estado:** Aceptada.
- **Fecha:** no registrada (medido el 12-10-2026).
- **Contexto:** con cinco años cargados, la primera visita al panel publicado tardaba 30,8 s.
- **Decisión:** el panel pide primero la lista de productos y después solo las filas del elegido, con sus valores como parámetros. Las respuestas quedan en caché hasta que cambia la base.
- **Alternativas:** guardar resultados precalculados en tablas nuevas del data warehouse; usar la versión SQL de K6 en el panel.
- **Consecuencias:** en local, el Panel bajó de 6,8 s a 2,5 s. Cada cambio de producto hace una consulta nueva, y la primera visita tras publicar es más lenta.
- **Referencia:** D-050.

## ADR-18 · K6 en Python con una versión SQL gemela

- **Estado:** Aceptada.
- **Fecha:** no registrada (hito 4 y T-47); ajustada el 2026-10-18.
- **Contexto:** SQLite no trae desviación estándar.
- **Decisión:** la consulta entrega la serie nacional y `bi/alerts.py` calcula la alerta: variación a más de dos desviaciones estándar de sus 12 variaciones anteriores, en series sin huecos. Una versión SQL hace el mismo cálculo sin raíz cuadrada, y una prueba exige que ambas coincidan fila por fila. Desde D-146 la alerta exige además un cambio de al menos 10 %.
- **Alternativas:** alertas por región; banda centrada en cero; reemplazar Python por SQL en el panel.
- **Consecuencias:** dos implementaciones que se vigilan entre sí. La definición está escrita dos veces y cualquier cambio debe hacerse en ambas.
- **Referencia:** D-033, D-049, D-145, D-146.

## ADR-19 · Modelo estrella con dimensión de fechas

- **Estado:** Aceptada.
- **Fecha:** 2026-10-16 para `dim_date`; el resto, hito 2.
- **Contexto:** el rango habitual y el patrón de temporada necesitan semana ISO, mes y estación, y un calendario sin huecos.
- **Decisión:** una tabla de hechos, `weekly_price`, con dimensiones de producto, región, canal y fecha; el mayorista es un canal más. `dim_date` tiene una fila por semana, incluidas las semanas sin precios, con clave foránea real desde los hechos, y se reconstruye en cada carga. Tablas y columnas en inglés.
- **Alternativas:** no registradas para `dim_date`; para los nombres, los del diagrama en español del diseño.
- **Consecuencias:** el margen es una comparación entre dos canales de la misma tabla y los huecos del calendario quedan explícitos. Para agregar la clave foránea hubo que recrear la tabla de hechos, sin cambiar sus filas.
- **Referencia:** D-023, D-095.

## ADR-20 · Base en solo lectura y secretos fuera del código

- **Estado:** Aceptada.
- **Fecha:** no registrada (T-39, T-42, T-54).
- **Contexto:** el panel es público y una de sus funciones puede lanzar el workflow.
- **Decisión:** el panel abre `datos.db` en solo lectura. El token de GitHub, limitado al repositorio, y la clave de control viven en los secretos de Streamlit; el archivo local de secretos está excluido del repositorio. El panel nunca muestra el token.
- **Alternativas:** escribir la clave en el enlace; mostrar los últimos caracteres del token; un botón sin protección.
- **Consecuencias:** ninguna página puede cambiar los datos. La clave ordena el acceso pero no es la seguridad real, que está en las cuentas de GitHub y Streamlit.
- **Referencia:** D-038, D-041, D-053.

## ADR-21 · Variación y alertas sobre las mismas regiones

- **Estado:** Aceptada.
- **Fecha:** 2026-10-18.
- **Contexto:** la auditoría de datos mostró que el precio nacional promediaba regiones distintas en dos semanas. En la semana del 05-10-2026, 99 de 734 comparaciones se desviaban más de 5 puntos, y 8 de 43 alertas venían probablemente de un cambio de regiones.
- **Decisión:** la variación nacional y las alertas K6 comparan solo las regiones con precio en ambas semanas, como una muestra emparejada. Una clave sin región en común no tiene comparación.
- **Alternativas:** no registradas. Se descartó un índice permanente para acelerar la consulta, porque agrandaría la base.
- **Consecuencias:** las familias del Resumen coinciden con un cálculo independiente. La consulta de K6 tarda unos 2 s en lugar de 0,8 s y queda en caché una vez por carga.
- **Referencia:** D-144, D-145.

## ADR-22 · Rango habitual P25–P75 por semana ISO ±1

- **Estado:** Aceptada.
- **Fecha:** 2026-10-16; ajustada el 2026-10-18.
- **Contexto:** el panel debía responder si el precio de esta semana es normal para la temporada, no mostrar años de historia sin lectura.
- **Decisión:** lo habitual es el rango entre los percentiles 25 y 75 del precio en la misma semana ISO y sus vecinas, en años anteriores; el año en curso nunca entra en su propia referencia. Con menos de dos años anteriores no hay comparación. Desde D-146 el rango usa solo la historia de las regiones con precio esta semana. El mismo criterio se aplica a la brecha entre canales y al margen.
- **Alternativas:** una sola semana ISO; la mediana de la brecha con una tolerancia.
- **Consecuencias:** un estado claro (bajo, dentro o sobre lo habitual) sin interpolar semanas faltantes. Los cálculos son funciones puras con pruebas, en caché por versión de la base.
- **Referencia:** D-094, D-098, D-146.

## ADR-23 · Revisión de pertinencia: solo conclusiones que se sostienen

- **Estado:** Aceptada.
- **Fecha:** 2026-10-18.
- **Contexto:** al medir el panel en la semana del 05-10-2026 aparecieron lecturas que no resistían revisión: un promedio de familia arrastrado por pocas series, un ranking dominado por cambios de una sola cotización, regiones pintadas sin distinguirse del azar y alertas al nivel que da el azar.
- **Decisión:** cada familia muestra la mediana; un cambio apoyado en una sola cotización va al final con su marca; una región se pinta solo si pasa una prueba de signos (p < 0,05); una alerta debe ser inusual y material; el patrón de meses siguientes se muestra solo si al menos tres años coinciden. Cada regla tiene su prueba en `tests/test_data_audit.py`.
- **Alternativas:** no registradas.
- **Consecuencias:** menos afirmaciones, todas sostenibles: las alertas de esa semana pasaron de 46 a 22. El contraste con otra fuente sigue pendiente, porque ODEPA es la única fuente oficial.
- **Referencia:** D-146.

## ADR-24 · K5, rezago descriptivo por región y canal

- **Estado:** Retirada por ADR-25.
- **Fecha:** no registrada (diseño inicial y hito 5).
- **Contexto:** la pregunta P5 buscaba cuántas semanas tarda el consumidor en seguir al mayorista.
- **Decisión:** el rezago se calculaba por región y canal como el desfase de 0 a 8 semanas con mayor correlación entre cambios semanales, mostrado solo si superaba un umbral basado en el número de pares y siempre como dato descriptivo.
- **Alternativas:** rezago nacional; mostrar siempre el desfase de correlación máxima; umbral fijo; modelos econométricos.
- **Consecuencias:** evitaba publicar ruido como resultado, pero dejaba la mayoría de las series sin respuesta.
- **Referencia:** D-011, D-048.

## ADR-25 · Retiro de K5 del producto

- **Estado:** Aceptada.
- **Fecha:** 2026-10-18.
- **Contexto:** en el 57 % de las 1.215 series no había relación clara y el 18 % daba «la misma semana», que datos semanales no pueden separar.
- **Decisión:** K5 y la pregunta P5 salen del producto. En su lugar vuelve P1: el margen del consumidor sobre el mayorista, frente a su rango habitual.
- **Alternativas:** no registradas.
- **Consecuencias:** el panel deja de mostrar una cifra que en la mayoría de los casos no significa nada. El código del cálculo sigue en el repositorio.
- **Referencia:** D-146.

## ADR-26 · Consolas SQL y Python en el panel

- **Estado:** Reemplazada por ADR-27.
- **Fecha:** 2026-10-17.
- **Contexto:** se buscaba que el panel mostrara las preguntas como en un motor de base de datos y con el código que las responde.
- **Decisión:** una consola SQL de solo lectura, con autorizador, una sola sentencia de lectura, tope de filas y de tiempo; y una consola de Python con scripts fijos donde solo cambiaban parámetros elegidos de listas cerradas.
- **Alternativas:** no registradas.
- **Consecuencias:** un mecanismo de ejecución expuesto al público que había que mantener y defender.
- **Referencia:** D-126, D-135.

## ADR-27 · GitHub es la fuente de verdad del código

- **Estado:** Aceptada.
- **Fecha:** 2026-10-18.
- **Contexto:** las consolas mostraban identificadores que no dicen nada al lector y repetían código que ya está en GitHub; la página «Código Python y SQL» hacía lo mismo.
- **Decisión:** se retiran las dos consolas, su ejecutor de SQL y la página de código. Los enlaces a una consulta abren su línea en GitHub. Se eliminan funciones sin uso del panel.
- **Alternativas:** no registradas.
- **Consecuencias:** un mecanismo menos que mantener y defender; el panel no ejecuta texto de un visitante. `bi/dashboard.py` pasa de 8.474 a unas 7.500 líneas.
- **Referencia:** D-143, D-148.

## ADR-28 · Ejecución manual: el mismo workflow, tras una clave

- **Estado:** Aceptada.
- **Fecha:** 2026-10-18 para el botón actual; el mecanismo, T-39.
- **Contexto:** el autor necesita lanzar el pipeline sin esperar al martes y ver si terminó bien; en Ejecuciones no se veía dónde hacerlo.
- **Decisión:** el botón «Ejecutar pipeline ahora» pide la clave de control, lanza el mismo `semanal.yml` en GitHub, muestra los pasos en vivo y termina con un mensaje claro de éxito o falla. Sin secretos, aparece desactivado con su motivo.
- **Alternativas:** ejecutar el agente y el ETL dentro del servidor de Streamlit, lo que daría dos versiones de la base; un botón sin protección.
- **Consecuencias:** un solo workflow y una sola fuente de verdad. Depende de que GitHub responda y de un token que vence.
- **Referencia:** D-038, D-149.

## ADR-29 · Sin vigilante de archivos en el servidor publicado

- **Estado:** Aceptada.
- **Fecha:** 2026-10-17.
- **Contexto:** el panel publicado no arrancaba: el vigilante de archivos de Streamlit agotaba los recursos del contenedor y reintentaba sin fin.
- **Decisión:** desactivar el vigilante de archivos en la configuración del panel.
- **Alternativas:** no registradas.
- **Consecuencias:** el panel arranca. Nadie edita archivos en el servidor, así que no se pierde ninguna función.
- **Referencia:** D-109.
