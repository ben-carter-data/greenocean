# GreenOcean · Registros de decisiones de arquitectura (ADR)

Las decisiones que dieron forma a la arquitectura entregada, una ficha por decisión, con su contexto, su decisión y sus consecuencias.

| Ficha del documento | |
|---|---|
| Alcance | Fuentes, almacenamiento, transformación, calidad, operación, seguridad y evolución |
| Versión | Arquitectura entregada al 19-10-2026 (decisiones hasta D-158) |
| Autoría | El autor |
| Fuente | El registro completo, `docs/DECISIONES.md`, con más de ciento cincuenta entradas; aquí queda solo lo que tiene peso arquitectónico |
| Convención | Cada ficha cita sus entradas D-xxx. Cuando el registro no guarda las alternativas o la fecha, se dice |

---

## Índice

| ADR | Decisión | Estado | Referencia |
|---|---|---|---|
| ADR-01 | Archivos oficiales, sin scraping | Aceptada | D-001, D-002 |
| ADR-02 | GitHub Actions y Streamlit Community Cloud, a costo cero | Aceptada; el motor, reemplazado por ADR-30 | D-012, D-019 |
| ADR-03 | Repositorio público con licencia MIT | Aceptada | D-013, D-036 |
| ADR-04 | Los datos crudos no se suben al repositorio | Aceptada | D-020, D-154 |
| ADR-05 | Clave exacta producto + variedad + calidad | Aceptada | D-007, D-030 |
| ADR-06 | Conversión de unidades por lectura literal del texto | Aceptada | D-008, D-026 |
| ADR-07 | Grano semanal por lunes, ponderado por volumen | Aceptada | D-006, D-027 |
| ADR-08 | Toda fila inválida se rechaza con motivo y se conserva | Aceptada | D-025 |
| ADR-09 | Atípicos marcados con una mediana por fuente | Aceptada | D-028 |
| ADR-10 | Carga idempotente por reconstrucción completa | Aceptada | D-024, D-154 |
| ADR-11 | Controles de calidad antes de publicar | Aceptada | D-029, D-154 |
| ADR-12 | Lista fija de huecos conocidos de la fuente | Aceptada | D-042 |
| ADR-13 | Unicidad garantizada por prueba, no por índice | Aceptada | D-046, D-154 |
| ADR-14 | Caché de años cerrados en GitHub Actions | Aceptada | D-047 |
| ADR-15 | El workflow semanal no guarda nada si un paso falla | Aceptada | D-017, D-034 |
| ADR-16 | Indicadores como consultas con nombre | Aceptada, ajustada por ADR-17 | D-031 |
| ADR-17 | El panel pide solo el producto elegido | Aceptada | D-050 |
| ADR-18 | K6 en Python con una versión SQL gemela | Aceptada | D-033, D-049 |
| ADR-19 | Modelo estrella con dimensión de fechas | Aceptada | D-023, D-095 |
| ADR-20 | Base en solo lectura y secretos fuera del código | Aceptada | D-038, D-041, D-053 |
| ADR-21 | Variación y alertas sobre las mismas regiones | Aceptada | D-144, D-145 |
| ADR-22 | Rango habitual P25–P75 por semana ISO ±1 | Aceptada | D-094, D-098, D-146 |
| ADR-23 | Solo conclusiones que se sostienen | Aceptada | D-146 |
| ADR-25 | Retiro del rezago K5 | Aceptada | D-146 |
| ADR-27 | GitHub es la fuente de verdad del código | Aceptada | D-143, D-148 |
| ADR-28 | Ejecución manual: el mismo workflow, tras una clave | Aceptada | D-038, D-149 |
| ADR-29 | Sin vigilante de archivos en el servidor publicado | Aceptada | D-109 |
| ADR-30 | Parquet, dbt Core y DuckDB, portables a otro motor | Aceptada e implementada | D-152, D-154 |
| ADR-31 | Un warehouse en la nube solo con datos de empresa | Aceptada | D-152 |
| ADR-32 | Sin comparación por cadena de supermercados | Aceptada | D-001, D-152 |
| ADR-33 | Precios reales con el IPC de alimentos del INE | Aceptada e implementada | D-155 |
| ADR-34 | Almacén de trabajo, base de servicio y respaldo con paridad | Aceptada e implementada | D-154 |

Las decisiones ADR-24 (rezago K5 descriptivo) y ADR-26 (consolas SQL y Python en el panel) fueron reemplazadas; se resumen al final.

---

## ADR-01 · Archivos oficiales, sin scraping

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Diseño inicial | D-001, D-002 |

**Contexto.** Los precios mayoristas y al consumidor ya existen como archivos anuales en el portal de datos abiertos de ODEPA, con licencia Creative Commons Atribución.

**Decisión.** Obtener los datos solo de archivos oficiales descargables. La misma regla se aplicó después al IPC del INE.

**Alternativas.** Scraping de supermercados; registros públicos de salud; partir con tres fuentes.

**Consecuencias.** Ingesta estable, sin depender de la estructura de una página. No se responde de qué países proviene cada producto ni cómo varía el precio por cadena.

## ADR-02 · GitHub Actions y Streamlit Community Cloud, a costo cero

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada; el motor SQLite fue reemplazado por ADR-30 | Diseño inicial | D-012, D-019 |

**Contexto.** El proyecto debe correr sin costo, sin servidor que mantener y poder clonarse en cualquier equipo.

**Decisión.** Orquestación en GitHub Actions y panel en Streamlit Community Cloud. Nada de nube, contenedores ni modelos predictivos que no respondan mejor una pregunta.

**Alternativas.** Servidor propio; base en la nube; Power BI, que no se abre desde un enlace público sin licencia.

**Consecuencias.** Costo cero. Se renuncia a concurrencia y volumen, innecesarios para datos semanales de este tamaño.

## ADR-03 · Repositorio público con licencia MIT

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Diseño inicial y cierre del hito 4 | D-013, D-036 |

**Contexto.** El proyecto es un portafolio y su código debe poder revisarse y reutilizarse.

**Decisión.** Código, data warehouse y panel abiertos, con licencia MIT.

**Alternativas.** Repositorio privado o mixto; repositorio sin licencia.

**Consecuencias.** La autoría queda en el historial y GitHub Actions es gratuito. Se pierde exclusividad, aunque todo puede rehacerse con los mismos datos abiertos.

## ADR-04 · Los datos crudos no se suben al repositorio

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hitos 1 y 2; bronce en Parquet desde 2026-10-19 | D-020, D-023, D-154 |

**Contexto.** Cada archivo anual pesa entre 32 y 46 MB y GitHub rechaza archivos de más de 100 MB.

**Decisión.** La zona de aterrizaje y la capa bronce en Parquet se reconstruyen en cada ejecución, fuera del repositorio. Solo se suben la base de servicio, el respaldo SQLite y el registro de descargas.

**Alternativas.** Subir todo; almacenamiento de archivos grandes.

**Consecuencias.** El repositorio se mantiene manejable. Quien clone el proyecto debe ejecutar la ingesta para tener los datos crudos, y la auditoría que los necesita se omite donde no están.

## ADR-05 · Clave exacta producto + variedad + calidad

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Diseño inicial y hito 2 | D-007, D-030 |

**Contexto.** La prueba inicial mostró que mezclar calidades infla la diferencia entre mayorista y consumidor.

**Decisión.** El margen solo se calcula entre filas con la misma clave exacta.

**Alternativas.** Cruzar solo por nombre de producto; una tabla manual de equivalencia de calidades.

**Consecuencias.** Márgenes comparables. Parte de las claves del consumidor queda sin margen: 219 de 257 claves de frutas y verduras lo tienen, y la papa no.

## ADR-06 · Conversión de unidades por lectura literal del texto

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Diseño inicial y hito 2 | D-008, D-026 |

**Contexto.** El mayorista vende por caja, bandeja o malla; el consumidor compra por kilo, unidad o envase.

**Decisión.** Una unidad se convierte si empieza por kilo, unidad o litro, o si su texto trae un solo número seguido de una medida. La misma regla se aplica a ambas fuentes. Lo que no declara cantidad se conserva con su marca y sin precio comparable.

**Alternativas.** Tabla manual de equivalencias; excluir esas filas; estimar pesos.

**Consecuencias.** Una sola regla revisable. Atados, docenas, matas y rangos quedan sin margen: 12.472 precios semanales.

## ADR-07 · Grano semanal por lunes, ponderado por volumen

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Diseño inicial y hito 2 | D-006, D-027 |

**Contexto.** El mayorista es diario y el consumidor semanal.

**Decisión.** Cada día mayorista se asigna al lunes de su semana y se agrega con un promedio ponderado por el volumen tal como se publica.

**Alternativas.** Repartir el precio semanal en días; convertir el volumen a kilos antes de ponderar.

**Consecuencias.** Ambas fuentes comparten grano. Cuando una clave mezcla envases de distinto tamaño, el grande pesa menos de lo que debería.

## ADR-08 · Toda fila inválida se rechaza con motivo y se conserva

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 2 | D-025 |

**Contexto.** Un pipeline sin supervisión no puede borrar datos en silencio.

**Decisión.** Las filas con precio no positivo, mínimo sobre máximo, volumen no positivo, valor ilegible o fecha fuera del año van a la tabla de rechazos con su motivo y la fila original.

**Alternativas.** Validar solo por fecha de inicio; dar peso 1 a las filas sin volumen.

**Consecuencias.** En cada carga, leídas = cargadas + rechazadas, y una prueba de dbt lo exige. Hoy son 201 rechazos, todos por precio no positivo.

## ADR-09 · Atípicos marcados con una mediana por fuente

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 2 | D-028 |

**Contexto.** El precio al consumidor es sistemáticamente mayor que el mayorista; una mediana común marcaría como atípico un margen alto, que es justamente lo que se quiere medir.

**Decisión.** Un precio cinco veces mayor o menor que la mediana de su producto, unidad y semana dentro de su misma fuente se marca atípico, se conserva y sale de los indicadores.

**Alternativas.** Mediana común a las dos fuentes; factor 3 o 10.

**Consecuencias.** Detecta errores evidentes (826 precios marcados). La mediana aún mezcla variedades y calidades.

## ADR-10 · Carga idempotente por reconstrucción completa

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 2; en dbt desde 2026-10-19 | D-024, D-154 |

**Contexto.** Ejecutar dos veces la misma semana no debe duplicar filas.

**Decisión.** Cada carga reconstruye todos los modelos desde la capa bronce y escribe una base de servicio nueva.

**Alternativas.** Cargas incrementales semana por semana; acumular los rechazos de todas las ejecuciones.

**Consecuencias.** Es imposible duplicar y la semana que cruza dos años no requiere lógica especial. Cada carga recalcula todo, lo que con DuckDB toma segundos.

## ADR-11 · Controles de calidad antes de publicar

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 2; como pruebas de dbt desde 2026-10-19 | D-029, D-154 |

**Contexto.** Los archivos de un año solo crecen; una baja fuerte indica un archivo truncado.

**Decisión.** La carga se detiene si una prueba de dbt falla (semanas faltantes, regiones o canales desconocidos, claves duplicadas, precios no positivos, filas sin conciliar) o si las filas leídas bajan del 90 % de la última carga correcta.

**Alternativas.** Un límite superior de filas; rangos fijos por semana.

**Consecuencias.** No se necesitan cifras fijadas a mano. La primera ejecución no tiene con qué compararse y un archivo duplicado no se detecta por conteo.

## ADR-12 · Lista fija de huecos conocidos de la fuente

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 5 | D-042 |

**Contexto.** El archivo de consumidor 2022 no tiene la semana del 02-05-2022; dos descargas dieron la misma huella, así que el hueco es de la fuente.

**Decisión.** El control de semanas faltantes acepta una lista fija de huecos conocidos, hoy con esa única entrada. Cualquier otra semana faltante detiene la carga.

**Alternativas.** Quitar el control; rellenar con el promedio de las semanas vecinas.

**Consecuencias.** Queda escrito qué falta y por qué. Esa semana no tiene precio al consumidor ni margen, y ningún cálculo inventa un valor.

## ADR-13 · Unicidad garantizada por prueba, no por índice

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 5; como prueba de dbt desde 2026-10-19 | D-046, D-154 |

**Contexto.** En SQLite, el índice único ocupaba 24 MB de 61,6 MB y no aceleraba las consultas.

**Decisión.** La tabla de hechos no tiene índice único; una prueba de dbt exige una sola fila por semana, producto, región, canal y unidad.

**Alternativas.** Mantener el índice y aceptar el aviso de tamaño de GitHub; cargar menos años.

**Consecuencias.** Archivos pequeños. La base misma no rechaza un duplicado escrito por otro programa; la protección está en el pipeline, y el panel solo lee.

## ADR-14 · Caché de años cerrados en GitHub Actions

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 5 | D-047 |

**Contexto.** Descargar todos los años cada martes son unos 490 MB, aunque los años cerrados no cambian.

**Decisión.** Los archivos se guardan en la caché de Actions con una clave formada por el año en curso y la lista de recursos. La ingesta salta un año cerrado que ya está.

**Alternativas.** Descargar todo cada semana; cargar el histórico una sola vez.

**Consecuencias.** Se baja solo el año en curso. Si la caché venció se descarga todo, y una corrección de ODEPA en un año cerrado entra recién cuando la caché se renueva.

## ADR-15 · El workflow semanal no guarda nada si un paso falla

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Diseño inicial y hito 4 | D-017, D-034 |

**Contexto.** La base del repositorio es lo que lee el panel; una carga a medias sería visible para todos.

**Decisión.** El workflow ejecuta en orden ingesta, ETL de respaldo, construcción con dbt, pruebas, commit e informe. GitHub Actions se detiene en el primer paso que falla; el aviso es el correo de GitHub.

**Alternativas.** Guardar la base en otra rama o como artefacto; mensajería externa.

**Consecuencias.** La base solo se reemplaza con una carga que pasó todas las pruebas, sin servidores ni claves externas. El historial de Git crece con cada commit semanal.

## ADR-16 · Indicadores como consultas con nombre

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada, ajustada por ADR-17 | Hito 3 | D-031 |

**Contexto.** Cada cifra debe poder comprobarse ejecutando su consulta directamente en la base.

**Decisión.** Un archivo de consultas contiene una consulta por indicador, identificada por su nombre; el panel las lee por nombre. El precio nacional es el promedio simple de las regiones con dato.

**Alternativas.** Ponderar regiones por población; vistas dentro de la base.

**Consecuencias.** Una sola definición por indicador, legible y reproducible. Con la migración se adaptaron al dialecto de DuckDB sin cambiar ninguna cifra.

## ADR-17 · El panel pide solo el producto elegido

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Medido el 12-10-2026 | D-050 |

**Contexto.** Con cinco años cargados, la primera visita al panel publicado tardaba 30,8 s.

**Decisión.** El panel pide primero la lista de productos y después solo las filas del elegido. Las respuestas quedan en caché hasta que cambia la base.

**Alternativas.** Tablas precalculadas en el data warehouse.

**Consecuencias.** En local, el panel bajó de 6,8 s a 2,5 s, medido aún sobre SQLite. Cada cambio de producto hace una consulta nueva.

## ADR-18 · K6 en Python con una versión SQL gemela

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 4; ajustada el 18-10-2026 | D-033, D-049, D-145, D-146 |

**Contexto.** La alerta necesita una desviación estándar, que el motor original no traía.

**Decisión.** La consulta entrega la serie nacional y Python calcula la alerta: variación a más de dos desviaciones estándar de sus 12 anteriores y de al menos 10 %. Una versión SQL hace el mismo cálculo y una prueba exige que ambas coincidan fila por fila.

**Alternativas.** Alertas por región; reemplazar Python por SQL en el panel.

**Consecuencias.** Dos implementaciones que se vigilan entre sí; cualquier cambio debe hacerse en ambas.

## ADR-19 · Modelo estrella con dimensión de fechas

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | Hito 2; dimensión de fechas el 16-10-2026 | D-023, D-095 |

**Contexto.** El rango habitual y la temporada necesitan semana ISO, mes y estación, y un calendario sin huecos.

**Decisión.** Una tabla de hechos con dimensiones de producto, región, canal y fecha; el mayorista es un canal más. La dimensión de fechas tiene una fila por semana, incluidas las semanas sin precios, y relaciones probadas desde los hechos. El IPC semanal se une por la misma semana.

**Alternativas.** No registradas para la dimensión de fechas.

**Consecuencias.** El margen es una comparación entre dos canales de la misma tabla y los huecos del calendario quedan explícitos.

## ADR-20 · Base en solo lectura y secretos fuera del código

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | T-39, T-42, T-54 | D-038, D-041, D-053 |

**Contexto.** El panel es público y una de sus funciones puede lanzar el workflow.

**Decisión.** El panel abre la base de servicio en solo lectura. El token de GitHub, limitado al repositorio, y la clave de control viven en los secretos de Streamlit; el panel nunca muestra el token.

**Alternativas.** Escribir la clave en el enlace; un botón sin protección.

**Consecuencias.** Ninguna página puede cambiar los datos. La seguridad real está en las cuentas de GitHub y Streamlit.

## ADR-21 · Variación y alertas sobre las mismas regiones

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | 18-10-2026 | D-144, D-145 |

**Contexto.** El precio nacional promediaba regiones distintas en dos semanas: en la semana del 05-10-2026, 99 de 734 comparaciones se desviaban más de 5 puntos.

**Decisión.** La variación nacional y las alertas comparan solo las regiones con precio en ambas semanas. El precio que se muestra es siempre el nacional de la semana, igual en todas las páginas (D-153).

**Alternativas.** No registradas.

**Consecuencias.** Las familias del Resumen coinciden con un cálculo independiente, y cuando las regiones cambian, la fila lo dice.

## ADR-22 · Rango habitual P25–P75 por semana ISO ±1

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | 16-10-2026; ajustada el 18-10-2026 | D-094, D-098, D-146 |

**Contexto.** El panel debía responder si el precio de esta semana es normal para la temporada.

**Decisión.** Lo habitual es el rango entre los percentiles 25 y 75 en la misma semana ISO y sus vecinas, en años anteriores y sobre las regiones con precio esta semana. Con menos de dos años anteriores no hay comparación. En modo Real, el rango se calcula sobre precios reales.

**Alternativas.** Una sola semana ISO; la mediana con una tolerancia.

**Consecuencias.** Un estado claro —bajo, dentro o sobre lo habitual— sin interpolar semanas faltantes.

## ADR-23 · Solo conclusiones que se sostienen

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | 18-10-2026 | D-146 |

**Contexto.** Al medir el panel aparecieron lecturas que no resistían revisión: promedios arrastrados por pocas series, rankings dominados por una sola cotización, regiones pintadas sin distinguirse del azar.

**Decisión.** Cada familia muestra la mediana; un cambio apoyado en una sola cotización va al final con su marca; una región se pinta solo si pasa una prueba de signos; una alerta debe ser inusual y material; el patrón de temporada exige acuerdo de al menos tres años.

**Alternativas.** No registradas.

**Consecuencias.** Menos afirmaciones, todas sostenibles: las alertas de esa semana pasaron de 46 a 22, y a 13 cuando una alerta pasó a exigir al menos dos cotizaciones en cada semana (D-158).

## ADR-25 · Retiro del rezago K5

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada; reemplaza a ADR-24 | 18-10-2026 | D-146 |

**Contexto.** En el 57 % de las 1.215 series no había relación clara entre mayorista y consumidor, y el 18 % daba «la misma semana», que datos semanales no pueden separar.

**Decisión.** K5 sale del producto. En su lugar vuelve el margen del consumidor sobre el mayorista, frente a su rango habitual.

**Alternativas.** No registradas.

**Consecuencias.** El panel deja de mostrar una cifra que casi nunca significa nada. El cálculo sigue en el repositorio.

## ADR-27 · GitHub es la fuente de verdad del código

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada; reemplaza a ADR-26 | 18-10-2026 | D-143, D-148 |

**Contexto.** Las consolas del panel y la página de código repetían lo que ya está en GitHub y exponían un mecanismo de ejecución al público.

**Decisión.** Se retiran las consolas, su ejecutor y la página de código. Los enlaces a una consulta abren su línea en GitHub.

**Alternativas.** No registradas.

**Consecuencias.** Un mecanismo menos que mantener y defender; el panel no ejecuta texto de un visitante.

## ADR-28 · Ejecución manual: el mismo workflow, tras una clave

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | 18-10-2026; el mecanismo, T-39 | D-038, D-149 |

**Contexto.** El autor necesita lanzar el pipeline sin esperar al martes y ver si terminó bien.

**Decisión.** El botón «Ejecutar pipeline ahora» pide la clave de control, lanza el mismo workflow semanal en GitHub, muestra los pasos en vivo y termina con un mensaje claro. Sin secretos, aparece desactivado con su motivo.

**Alternativas.** Ejecutar la carga dentro del servidor del panel, lo que daría dos versiones de la base.

**Consecuencias.** Un solo workflow y una sola fuente de verdad. Depende de que GitHub responda y de un token que vence.

## ADR-29 · Sin vigilante de archivos en el servidor publicado

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | 17-10-2026 | D-109 |

**Contexto.** El panel publicado no arrancaba: el vigilante de archivos de Streamlit agotaba los recursos del contenedor.

**Decisión.** Desactivar el vigilante en la configuración del panel.

**Alternativas.** No registradas.

**Consecuencias.** El panel arranca. Nadie edita archivos en el servidor, así que no se pierde ninguna función.

## ADR-30 · Parquet, dbt Core y DuckDB, portables a otro motor

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada e implementada | 19-10-2026 | D-152, D-154 |

**Contexto.** SQLite cumplía con el volumen, pero se usa poco como data warehouse y las transformaciones vivían en Python y consultas sueltas. Las nuevas fuentes (IPC, clima) se integran mejor en un modelo por capas con pruebas declaradas.

**Decisión.** Capa bronce en Parquet, transformaciones en dbt Core (staging, intermedio y marts, con las reglas como pruebas de datos) y motor DuckDB. El motor se elige en la configuración de dbt; el panel se conecta en un solo punto. El panel cambió de motor solo cuando la auditoría dio cifras idénticas.

**Alternativas.** BigQuery en modo sandbox (las tablas vencen a los 60 días: el panel quedaría vacío si el pipeline se detiene); Snowflake y Redshift (solo periodos de prueba); Databricks (sobredimensionado); PostgreSQL gratuito (algunos planes pausan proyectos inactivos).

**Consecuencias.** 16 modelos y 31 pruebas de datos; bronce de 16 MB frente a 644 MB de la zona de aterrizaje; base de servicio de unos 13 MB frente a 34 MB; pipeline completo en 16 s en vez de unos 4 minutos. Costo cero y sin vencimientos. dbt solo se instala en el workflow, no en el panel publicado.

## ADR-31 · Un warehouse en la nube solo con datos de empresa

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | 19-10-2026 | D-152 |

**Contexto.** Se evaluó llevar el proyecto a un warehouse en la nube para mostrar esa competencia.

**Decisión.** No hacerlo mientras el alcance sea público. Con una base de unos 13 MB, carga semanal y un solo panel de lectura, la nube agregaría costo, secretos y riesgos de vencimiento sin beneficio, incluso al sumar el clima. Se adoptaría si una empresa sumara sus propios datos (ventas, costos, inventario) con varios GB, varios equipos, permisos o cargas frecuentes; los criterios están en la sección Escalabilidad del SAD.

**Alternativas.** Agregar BigQuery como segundo destino de dbt solo para demostrarlo; queda como opción declarada, nunca como dependencia del panel.

**Consecuencias.** El proyecto se dimensiona según su necesidad real. La configuración de dbt ya documenta, sin activar, los destinos BigQuery, Snowflake y PostgreSQL.

## ADR-32 · Sin comparación por cadena de supermercados

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada | 19-10-2026 | D-001, D-152 |

**Contexto.** Se evaluó comparar precios por cadena o indicar dónde conviene comprar.

**Decisión.** No hacerlo. ODEPA publica por canal y región, no por cadena; no se conoce una fuente abierta oficial por cadena, y el scraping contradice ADR-01. Una vista «dónde comprar» serviría al consumidor, que no es el usuario del producto.

**Alternativas.** Scraping de supermercados en línea; vista para el consumidor por canal.

**Consecuencias.** El producto sigue centrado en decisiones profesionales; se revisaría si apareciera una fuente oficial por cadena.

## ADR-33 · Precios reales con el IPC de alimentos del INE

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada e implementada | 19-10-2026 | D-155 |

**Contexto.** Comparar el precio de hoy con su rango de años anteriores sin descontar la inflación hace parecer caro lo que solo subió con el nivel general de precios. El INE publica el IPC de alimentos en dos series de bases distintas: si se pegan sin más, aparece un salto de −33,7 %.

**Decisión.** Se usa la división «Alimentos y bebidas no alcohólicas» del INE. Las dos series se enlazan en enero 2024 con la variación mensual oficial de +1,0 %, y toda la serie anterior se escala por el mismo factor. Cada semana toma el IPC del mes de su lunes; los precios reales quedan en pesos del último mes publicado. Una semana de un mes aún no publicado usa ese último mes y se marca provisional.

**Alternativas.** Pegar las series sin enlazar, descartado por el salto de −33,7 %. Otras alternativas no están registradas.

**Consecuencias.** Selector Nominal / Real en Contexto de precios. El precio de esta semana es igual en ambos modos, así que ninguna cifra cambia entre páginas. El deflactor es nacional y de toda la división, no de cada producto. Si el INE no responde, la carga sigue con el IPC ya publicado. Una auditoría lo recalcula sin dbt desde el texto del INE.

## ADR-34 · Almacén de trabajo, base de servicio y respaldo con paridad

| Estado | Fecha | Referencia |
|---|---|---|
| Aceptada e implementada | 19-10-2026 | D-154 |

**Contexto.** dbt deja en su base vistas, tablas intermedias y metadatos que el panel no necesita, y una construcción a medias no debe llegar nunca al panel.

**Decisión.** dbt construye y prueba en un almacén de trabajo que no se sube. El orquestador copia solo las tablas del panel a un archivo nuevo y compacto, registra la carga y reemplaza la base publicada de una sola vez. El SQLite anterior se sigue construyendo como respaldo, y una prueba compara ambas bases fila a fila cada semana.

**Alternativas.** Que el panel lea directamente el almacén de dbt; retirar SQLite el mismo día de la migración.

**Consecuencias.** Base publicada pequeña y siempre completa. La paridad inicial dio 811.578 precios iguales, con una diferencia máxima de 4,9 × 10⁻¹⁶. Mientras el autor no retire el respaldo, cada carga escribe dos bases.

---

## Decisiones reemplazadas

| ADR | Decisión original | Qué pasó |
|---|---|---|
| ADR-24 | Rezago K5 descriptivo por región y canal, mostrado solo sobre un umbral | Retirado del producto por ADR-25 |
| ADR-26 | Consolas SQL y Python de solo lectura en el panel | Retiradas por ADR-27 |
