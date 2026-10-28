# Registro de decisiones

Una entrada por decisión: qué se decidió, por qué, qué se descartó y qué se pierde.

## D-001 · Descargar archivos oficiales en vez de hacer scraping

- **Decisión:** obtener los datos desde los CSV del portal de datos abiertos de ODEPA.
- **Por qué:** la información requerida ya existe como archivo. Es más estable, más rápido y no depende de la estructura de una página.
- **Descartado:** scraping de supermercados; registros públicos de salud.
- **Se pierde:** el proyecto no muestra navegación web. Esa habilidad queda respaldada por la experiencia laboral.

## D-002 · Dos fuentes en la etapa 1

- **Decisión:** precios mayoristas y precios al consumidor. Comercio exterior queda para la etapa 2.
- **Por qué:** el riesgo está en el cruce principal; conviene validarlo antes de sumar una fuente mensual con otra codificación.
- **Descartado:** partir con tres fuentes.
- **Se pierde:** no se responde de qué países proviene cada producto.

## D-003 · Tema: cadena de precios de alimentos

- **Decisión:** analizar precios y márgenes entre mayorista y consumidor.
- **Por qué:** datos abiertos, cruce verificado, preguntas reconocibles para pricing y abastecimiento.
- **Descartado:** prestadores de salud acreditados (poco valor al cruzar), monitor de precios de supermercados (condiciones de uso inciertas), ofertas de empleo.
- **Se pierde:** cercanía temática con el rubro salud.

## D-004 · Enfoque de negocio, no de consumidor

- **Decisión:** el usuario principal es un analista de pricing, compras o abastecimiento.
- **Por qué:** es un portafolio dirigido a empresas.
- **Descartado:** un comparador para el público general como vista principal.
- **Se pierde:** inmediatez para quien no es del rubro. Se compensa con un perfil consumidor de prioridad baja.

## D-005 · Selector de perfil sin inicio de sesión

- **Decisión:** el panel pregunta quién consulta y adapta las vistas.
- **Por qué:** muestra los mismos datos según la necesidad de cada usuario sin sumar infraestructura.
- **Descartado:** usuarios con cuenta; paneles separados.
- **Se pierde:** personalización persistente.

## D-006 · Cruce por semana

- **Decisión:** agregar el precio mayorista diario a semana (lunes de inicio), ponderado por volumen.
- **Por qué:** la fuente de consumidor es semanal.
- **Descartado:** repartir el precio semanal del consumidor en días.
- **Se pierde:** detalle diario del mayorista en los indicadores (se conserva en la tabla cruda).

## D-007 · Clave exacta producto + variedad + calidad

- **Decisión:** calcular el margen solo entre filas con la misma clave.
- **Por qué:** mezclar calidades infla la diferencia; la prueba inicial lo mostró.
- **Descartado:** cruzar solo por nombre de producto.
- **Se pierde:** 22 de 168 claves del consumidor quedan sin margen en 2026.

## D-008 · Unidades no convertibles se conservan sin margen

- **Decisión:** comparar por kilo o por unidad cuando ambas fuentes lo permiten; el resto se muestra sin margen y con motivo.
- **Por qué:** una equivalencia inventada (peso de un atado) daría márgenes falsos.
- **Descartado:** excluir esas filas; estimar pesos.
- **Se pierde:** margen en productos vendidos por atado o docena.

## D-009 · Histórico desde 2022 (propuesta)

- **Decisión:** cargar 2022 a 2026, sujeto a validar el formato de cada año.
- **Por qué:** varios años permiten estacionalidad; más atrás aumenta el riesgo de cambios de formato y el efecto de la inflación.
- **Descartado:** solo 2026; toda la serie desde 2008.
- **Se pierde:** tendencias de largo plazo.

## D-010 · Precios nominales en la etapa 1

- **Decisión:** no ajustar por inflación al inicio.
- **Por qué:** los indicadores principales comparan precios de la misma semana, donde la inflación no afecta.
- **Descartado:** integrar el IPC desde el inicio.
- **Se pierde:** comparaciones entre años en términos reales. Queda señalado en el panel.

## D-011 · El rezago de precios es descriptivo

- **Decisión:** K5 se presenta como desfase observado, sin afirmar causa.
- **Por qué:** con datos semanales y sin controlar otros factores no se puede probar causalidad.
- **Descartado:** modelos econométricos.
- **Se pierde:** una respuesta concluyente sobre transmisión de precios.

## D-012 · SQLite, GitHub Actions y Streamlit Community Cloud

- **Decisión:** base en archivo, job programado y panel publicado en servicios gratuitos.
- **Por qué:** sin costo, sin servidor que mantener, y cualquiera puede clonar y ejecutar.
- **Descartado:** servidor propio; base en la nube; Power BI (no se puede abrir desde un enlace público sin licencia).
- **Se pierde:** concurrencia y volumen. Suficiente para datos semanales de este tamaño.

## D-013 · Repositorio público

- **Decisión:** código, datos y panel abiertos.
- **Por qué:** el objetivo es que un reclutador pueda verlo; la autoría queda en el historial.
- **Descartado:** repositorio privado o mixto.
- **Se pierde:** exclusividad. Lo publicado se puede rehacer con los mismos datos abiertos.

## D-014 · Agente en un solo archivo

- **Decisión:** `agent.py` contiene el flujo completo con funciones nombradas por lo que hacen.
- **Por qué:** se lee de arriba abajo y es replicable para otra fuente cambiando la configuración.
- **Descartado:** dividir el agente en varios módulos desde el inicio.
- **Se pierde:** separación fina de responsabilidades; se divide si crece.

## D-015 · Código propio, sin material del empleador

- **Decisión:** todo el código se escribe desde cero con librerías públicas.
- **Por qué:** evitar cualquier uso de propiedad de terceros.
- **Descartado:** traducir plantillas o usar librerías internas.
- **Se pierde:** nada.

## D-016 · Pruebas y controles de calidad visibles desde la primera versión

- **Decisión:** las pruebas corren solas en cada cambio y cada carga pasa controles de calidad antes de actualizar la base.
- **Por qué:** un sistema que corre sin supervisión debe detectar solo cuando algo sale mal.
- **Descartado:** agregar las pruebas al final.
- **Se pierde:** tiempo al inicio.

## D-017 · Informe semanal y avisos con las herramientas de GitHub

- **Decisión:** el job publica un informe semanal en el repositorio y GitHub avisa por correo si falla.
- **Por qué:** no requiere servidor de correo, claves ni servicios externos.
- **Descartado:** correo propio; mensajería externa.
- **Se pierde:** un canal más cómodo para un usuario de negocio. Se puede agregar después.

## D-018 · Los hallazgos se publican solo si se pueden reproducir

- **Decisión:** cada hallazgo va con su consulta SQL y sus límites.
- **Por qué:** una cifra llamativa que no resiste una revisión resta credibilidad a todo el proyecto.
- **Descartado:** publicar las cifras de la prueba inicial, que mezclaban calidades.
- **Se pierde:** titulares más vistosos.

## D-019 · Sin tecnologías agregadas para aparentar

- **Decisión:** no sumar nube, contenedores ni modelos predictivos en esta versión.
- **Por qué:** no responden mejor ninguna pregunta y habría que defenderlos en entrevista.
- **Descartado:** esas tres.
- **Se pierde:** palabras clave en el CV.

## D-020 · Los datos crudos no se suben al repositorio

- **Decisión:** los CSV descargados y la base cruda (`raw.db`) se reconstruyen en cada ejecución y quedan fuera del repositorio. Solo se suben la base de indicadores (`datos.db`, agregada por semana) y el registro de descargas (`manifest.json`).
- **Por qué:** al construir el hito 1 se midió el tamaño real: 32 MB y 46 MB por archivo anual, y 105 MB la base cruda de un solo año. GitHub rechaza archivos de más de 100 MB y el repositorio crecería en cada ejecución.
- **Descartado:** subir todo; usar almacenamiento de archivos grandes.
- **Se pierde:** quien clone el repositorio debe ejecutar el agente para tener los datos crudos. Los indicadores sí vienen incluidos.

## D-021 · Código en inglés, documentación en español

- **Decisión:** nombres de archivos, funciones, variables, tablas, comentarios y mensajes de log en inglés. Los documentos del proyecto y los textos del panel en español. Los nombres de columnas y valores de ODEPA se conservan tal como vienen.
- **Por qué:** el inglés es la convención del código; el público del proyecto es chileno; traducir los valores de la fuente rompería la trazabilidad.
- **Descartado:** todo en español; todo en inglés.
- **Se pierde:** quien no lee inglés depende de la documentación para seguir el código.

## D-022 · Convenciones de código

- **Decisión:** estilo PEP 8; funciones con nombre de verbo que dice lo que hacen (`download_all_resources`, `validate_downloaded_file`); booleanos con prefijo `is_`; sin abreviaturas; constantes en mayúsculas en vez de textos repetidos; cada archivo dividido en secciones con `# region` y `# endregion`, que VS Code y PyCharm permiten plegar.
- **Por qué:** el código debe entenderse sin esfuerzo y cada parte debe ubicarse rápido, igual que las regiones de un proyecto .NET.
- **Descartado:** nombres cortos del flujo original (`navigation`, `load_input`), por ser menos descriptivos.
- **Se pierde:** nombres algo más largos.

## D-023 · Tablas y columnas en inglés; un esquema por base (hito 2)

- **Decisión:** las tablas de `datos.db` se llaman `dim_product`, `dim_region`, `dim_channel`, `weekly_price`, `etl_run` y `rejection`, con columnas en inglés. `etl/schema.sql` define `datos.db` y `etl/raw_schema.sql` define `raw.db`.
- **Por qué:** D-021 pide tablas en inglés y el hito 1 ya lo hizo así con las tablas crudas. Con un solo archivo de esquema cada base quedaba con las tablas vacías de la otra.
- **Descartado:** los nombres en español del diagrama de `DISENO.md` 8.3 (`precio_semanal`, `ejecucion`, `rechazo`); un único `schema.sql`.
- **Se pierde:** el diagrama del diseño ya no coincide letra por letra con la base. La equivalencia está en `docs/hito-2.md`.

## D-024 · Los precios semanales se reconstruyen completos en cada ejecución (hito 2)

- **Decisión:** para cumplir RN-14, `load()` borra y vuelve a escribir `weekly_price` dentro de una transacción. Las dimensiones solo reciben filas nuevas, así sus identificadores no cambian. `etl_run` guarda una línea por ejecución y `rejection` solo los rechazos de la última.
- **Por qué:** `raw.db` ya se reconstruye en cada ejecución (D-020), así que recalcular todo es lo más simple y no puede duplicar. Además una semana que cruza dos años (29-12-2025) junta filas de dos archivos sin lógica especial.
- **Descartado:** actualizar semana por semana con claves; acumular los rechazos de todas las ejecuciones.
- **Se pierde:** el historial de rechazos de ejecuciones anteriores (queda solo su número en `etl_run`).

## D-025 · RN-11: una semana pertenece al archivo si toca su año (hito 2)

- **Decisión:** la fecha se considera fuera del año del archivo solo si ni el inicio ni el término de la semana caen en ese año. Se agregan dos motivos de rechazo: valor ilegible (`UNREADABLE_VALUE`) y fila mayorista sin volumen (`NON_POSITIVE_VOLUME`).
- **Por qué:** la semana 1 del consumidor 2026 empieza el 29-12-2025; con RN-11 literal se rechazaban sus 4.382 filas válidas. Una fila mayorista sin volumen no puede entrar en el promedio ponderado de RN-07.
- **Descartado:** validar solo por `Fecha inicio`; dar peso 1 a las filas sin volumen.
- **Se pierde:** nada medido: en 2026 ninguna fila cae en los motivos nuevos.

## D-026 · Conversión de unidades por lectura literal del texto (hito 2)

- **Decisión:** una unidad se convierte si empieza con `$/kilo`, `$/unidad` o `$/litro`, o si su texto trae un solo número seguido de una medida: kilos, unidades, gramos (a kilo) o ml y litros (a litro). La misma función se aplica a las dos fuentes. Por eso `$/docena de atados (6 kilos)` se convierte dividiendo por 6 (1.470 filas mayoristas) y `$/botella 900 ml` pasa a precio por litro.
- **Por qué:** es la lectura directa de RN-03 a RN-05 y una sola regla es más fácil de revisar; las 147 unidades reales están en `tests/wholesale_units_2026.csv` con su conversión. Sin gramos ni litros, 13.188 filas de abarrotes y lácteos (aceite, leche, yogur) quedaban fuera de P2 a P4, que el alcance sí incluye.
- **Descartado:** una tabla manual de equivalencias (T-33); limitarse a kilo y unidad como decía el diseño original; convertir envases con dos números (`$/bandeja 12 canastillos 125 gramos`), porque obliga a interpretar el texto.
- **Se pierde:** 7.931 filas mayoristas (5,46 %) siguen sin convertir: atados, docenas, matas y rangos. Aparece una tercera unidad normalizada, `litro`, que el diseño no tenía.

## D-027 · RN-07 pondera por el volumen tal como se publica (hito 2)

- **Decisión:** el peso de cada precio diario es la columna `Volumen` sin transformar.
- **Por qué:** es la regla escrita. El volumen viene en la unidad de comercialización (cajas, bins, mallas), y convertirlo a kilos exige interpretar también unidades como `$/kilo (en caja de 17 kilos)`.
- **Descartado:** convertir el volumen a kilos antes de ponderar.
- **Se pierde:** cuando una misma clave y semana mezcla envases de distinto tamaño, el envase grande pesa menos de lo que debería.

## D-028 · RN-12: mediana por producto, unidad, semana y fuente, con factor 5 (hito 2)

- **Decisión:** la mediana se calcula sobre los precios semanales del producto en esa semana y unidad, dentro de una misma fuente (mayorista por un lado, consumidor por otro), mezclando variedades, calidades, regiones y canales. El factor 5 del diseño se mantiene.
- **Por qué:** el precio al consumidor es sistemáticamente mayor que el mayorista; una mediana común marcaba como atípico un margen alto, que es justo lo que el proyecto quiere medir. Con 2026 marca 193 de 129.164 precios (0,15 %) y sigue detectando errores evidentes (poroto a $3 el kilo).
- **Descartado:** mediana común a las dos fuentes (346 marcados); factor 3 o 10.
- **Se pierde:** la mediana aún mezcla variedades y calidades. Quedan marcados 49 precios de arándano en consumidor y 71 de limón mayorista (variedades Sutil y Tahití a unos $2.000 el kilo) que probablemente son precios reales.

## D-029 · Controles de calidad antes de cargar (hito 2)

- **Decisión:** la carga se detiene si las filas leídas bajan de 90 % de la última carga correcta, si falta una semana intermedia en alguna fuente, o si aparece una región fuera de 1 a 16 o un canal desconocido. La ejecución queda en `etl_run` como `FAILED` con el mensaje.
- **Por qué:** los archivos de un año solo crecen, así que una baja fuerte indica un archivo truncado. Comparar con la carga anterior no requiere fijar cifras a mano.
- **Descartado:** un límite superior de filas, porque cargar el histórico (hito 5) multiplica las filas de forma legítima; rangos fijos por semana.
- **Se pierde:** la primera ejecución no tiene con qué compararse, y un archivo duplicado no se detecta por conteo.

## D-030 · La papa queda sin margen en la etapa 1 (hito 2)

- **Decisión:** se mantiene la clave exacta de D-007 también para la papa, que por eso no tiene margen (K1) en ninguna región. Sí aparece en canales, regiones y estacionalidad.
- **Por qué:** el consumidor publica la papa con calidad «Primera» o «Segunda» y el mayorista con «1a (cosecha)», «1a (guarda)», «1a nueva(o)», «1a (cosecha lavada)», etc. Unirlas mezclaría papa nueva, de guarda y lavada, que tienen precios distintos: el mismo error que D-007 y D-018 quieren evitar.
- **Descartado:** una tabla de equivalencia de calidades hecha a mano en esta etapa (queda como mejora T-37).
- **Se pierde:** el criterio 5 de `DISENO.md` 11 se cumple para cuatro de los cinco productos de la prueba (tomate, limón, palta, cebolla), no para la papa.

## D-031 · Indicadores como consultas con nombre y cálculo simple (hito 3)

- **Decisión:** `bi/queries.sql` contiene una consulta por indicador, cada una precedida por una línea `-- name:`; el panel las lee por nombre y filtra el resultado con pandas. El precio nacional de K3 y K4 es el promedio simple de las regiones con dato. El año de K4 es el del jueves de la semana (regla ISO). La unidad normalizada forma parte de la clave que se elige en el panel.
- **Por qué:** una consulta por indicador se puede copiar y ejecutar tal cual en SQLite para comprobar una cifra. El promedio simple no exige ponderadores que las fuentes no publican. Con la regla ISO, la semana que empieza el 29-12-2025 cuenta en 2026, igual que en el archivo del consumidor.
- **Descartado:** consultas con parámetros por producto; ponderar regiones por población; vistas SQL dentro de la base.
- **Se pierde:** el panel carga cada indicador completo en memoria (hasta unas 129.000 filas con un año). Con varios años puede convenir filtrar en SQL.

## D-032 · Streamlit 1.36 o superior (hito 3)

- **Decisión:** `requirements.txt` pide `streamlit>=1.36` en vez de `>=1.30`.
- **Por qué:** las barras horizontales (`horizontal=True`) existen desde la 1.36 y dejan leer los nombres de las regiones.
- **Descartado:** barras verticales con nombres cortados; agregar una librería de gráficos.
- **Se pierde:** nada práctico; es la misma librería.

## D-033 · K6 se calcula sobre el precio nacional, con pandas (hito 4)

- **Decisión:** la serie de cada alerta es el precio nacional semanal de una clave (producto + variedad + calidad), canal y unidad. Hay alerta cuando la variación de la semana se aleja más de 2 desviaciones estándar de la media de sus 12 variaciones anteriores. Solo se evalúan series con 13 semanas seguidas. La consulta SQL entrega la serie y `bi/alerts.py` hace el cálculo móvil.
- **Por qué:** SQLite no tiene desviación estándar. Trabajar a nivel nacional da series más largas y menos ruido que por región. Excluir la semana evaluada de su propio rango evita que un salto grande se esconda a sí mismo.
- **Descartado:** alertas por región; banda centrada en cero; escribir la desviación estándar a mano en SQL.
- **Se pierde:** un movimiento que ocurre en una sola región puede no verse. En productos de precio muy estable, un cambio de 1 % ya es alerta; el umbral se recalibra en T-30.

## D-034 · Job semanal: nada se guarda si un paso falla (hito 4)

- **Decisión:** `semanal.yml` ejecuta en orden agente, ETL, pruebas, guardar `datos.db` y `manifest.json`, y publicar el informe como issue. Tiene una opción manual `simulate_failure` que falla después del ETL. El aviso de falla es el correo que GitHub envía por defecto al autor.
- **Por qué:** GitHub Actions detiene el job en el primer paso que falla, así que la base del repositorio solo se reemplaza por una carga que pasó los controles y las pruebas. La opción manual permite demostrar T-23 y T-25d sin esperar un error real. Medido en una simulación: agregar una semana hace crecer el repositorio unos 0,7 MB, no los 10 MB del archivo, porque Git guarda la diferencia.
- **Descartado:** guardar la base en una rama aparte o como artefacto; un servicio de mensajería para los avisos (D-017).
- **Se pierde:** el historial de Git crece unos 35 MB por año con un solo año cargado, y más al cargar el histórico.

## D-035 · Tres archivos nuevos en `bi/` con nombre en inglés (hito 4)

- **Decisión:** el informe semanal vive en `bi/report.py` (el diseño lo llamaba `informe.py`), las alertas en `bi/alerts.py` y el acceso a datos compartido en `bi/queries.py`.
- **Por qué:** D-021 pide nombres de archivo en inglés. El panel y el informe usan las mismas tres funciones de lectura y el mismo cálculo de alertas; duplicarlos sería peor.
- **Descartado:** todo dentro de `dashboard.py`, que obligaría al informe a importar Streamlit.
- **Se pierde:** dos archivos más que los previstos en el diseño.

## D-036 · Licencia MIT y un commit inicial para los hitos 1 a 4 (cierre del hito 4)

- **Decisión:** el código lleva licencia MIT. El repositorio parte con un solo commit que reúne T-01 a T-25d tal como quedaron construidas; desde ahí, un commit por tarea. `run_download.command` se conserva en el repositorio como lanzador opcional para macOS. Los commits los puede hacer el asistente, siempre después de mostrar su contenido y recibir la aprobación del autor.
- **Por qué:** MIT es la licencia más simple y permite que cualquiera revise y reutilice el código, como busca D-013. Los hitos 1 a 4 se escribieron antes de que la carpeta fuera un repositorio y las tareas comparten archivos: separarlas después daría commits artificiales. El lanzador no estorba y ayuda a quien use macOS.
- **Descartado:** reconstruir un commit por tarea de los hitos 1 a 4; dejar el repositorio sin licencia, que en la práctica no permite reutilizar el código; borrar el lanzador.
- **Se pierde:** el historial no muestra el avance de los hitos 1 a 4 tarea por tarea; ese detalle queda en `docs/hito-1.md` a `docs/hito-4.md`.

## D-037 · Panel con aspecto de producto: modo oscuro y claro, tarjetas y Altair (T-38)

- **Decisión:** el panel se organiza como un producto de análisis: navegación lateral con íconos, una página «Panel» en una sola pantalla (filtros arriba, cuatro cifras clave con su cambio semanal y mini curva, y tarjetas con precio por semana, margen por canal, regiones y alertas) y las páginas de detalle en el mismo formato. Tiene dos modos de color en `.streamlit/config.toml`: negro profundo y beige claro; el lector cambia de modo en el menú del panel y los gráficos lo siguen. Los gráficos se dibujan con Altair (`bi/charts.py`); cada canal conserva su color, tomado de una paleta comprobada para daltonismo en ambos modos. Los números se escriben como en Chile (1.234 y 12,5 %).
- **Por qué:** el autor pidió un panel de aspecto profesional, de tipo SaaS, fondo oscuro con un modo claro beige y gráficos simples de leer. Una primera versión en forma de informe de arriba abajo se descartó por parecer un reporte. Altair viene instalado con Streamlit: no se agrega ninguna dependencia. Las cifras de la página principal son resultados de las consultas existentes, no hallazgos publicados (D-018, hito 6).
- **Descartado:** la charte de una empresa (riesgo con D-015); Matplotlib, que dibuja imágenes fijas sin información al pasar el cursor; una librería de componentes externa.
- **Se pierde:** el código del panel es más largo (estilos y tarjetas). El cambio de modo está en el menú del panel, no en un botón propio.

## D-038 · Centro de control del pipeline dentro del panel (T-39)

- **Decisión:** una página «Centro de control» muestra el estado del job semanal (última ejecución, próxima ejecución automática, historial con éxito o falla) leyendo la API pública de GitHub, y un botón «Ejecutar ahora» que lanza el mismo workflow `semanal.yml` y muestra sus pasos en directo. El botón exige una clave de GitHub limitada a este repositorio y un código de acceso, ambos guardados por el autor en los secretos de Streamlit, nunca en el código. Sin esos secretos, el botón se reemplaza por un enlace a GitHub.
- **Por qué:** el autor necesita ver y controlar la automatización desde un solo lugar, como en una consola de orquestación, sin entrar a GitHub. Lanzar el mismo workflow mantiene un solo workflow y una sola fuente de verdad. El código de acceso evita que cualquier visitante del panel público lance el pipeline.
- **Descartado:** ejecutar el agente y el ETL dentro del servidor de Streamlit (los datos no quedarían guardados en el repositorio y habría dos versiones de la base); un botón sin protección.
- **Se pierde:** el botón depende de que GitHub responda y de una clave que vence y hay que renovar. Los datos nuevos aparecen en el panel cuando Streamlit recibe la base guardada, normalmente uno o dos minutos después.

## D-039 · Página «Pipeline»: el recorrido de los datos en vivo (T-40)

- **Decisión:** el panel muestra el pipeline como un recorrido por capas (fuentes, ingesta, bronce, limpieza, reglas, calidad, oro y consumo), con la orquestación arriba, la cuarentena de filas rechazadas y la observabilidad abajo. Cada paso tiene un punto con su estado real (última ejecución del job semanal y base actual) y sus cifras del momento; por las flechas viajan puntos animados. Se dibuja como imagen SVG (`bi/architecture.py`).
- **Por qué:** el autor necesita entender y mostrar la arquitectura sin abrir GitHub, en el mismo estilo del panel. Solo aparecen las piezas que el proyecto usa de verdad, para poder defenderlas en una entrevista.
- **Descartado:** dibujar tecnologías que el proyecto no usa (Kafka, S3, Spark); un diagrama fijo sin estados; `st.html`, que elimina los dibujos SVG.
- **Se pierde:** la capa «plata» no se guarda como tabla; aparece como etiqueta en una flecha. Los textos del diagrama no cambian de tamaño con la pantalla.

## D-040 · Explicaciones al pasar el mouse y página «El proyecto» (T-41)

- **Decisión:** cada tarjeta tiene un ⓘ que, al pasar el mouse, explica en palabras simples cómo leer el gráfico; cada barra y cada flecha ▲▼ dice qué significa su número («46 % más caro que el promedio nacional», «Bajó 0,4 % frente a la semana anterior»). Una página «El proyecto» presenta el problema, para quién es, las seis preguntas de negocio con dónde se responde cada una y su estado, por qué se eligió el tema, los datos y los límites.
- **Por qué:** el autor y cualquier visitante deben poder interpretar cada número sin preguntar. Un reclutador busca primero qué problema resuelve el proyecto. Los textos salen de `DISENO.md` y de este registro, sin agregar afirmaciones nuevas.
- **Descartado:** un botón «Cómo leer» que había que abrir; una guía larga aparte.
- **Se pierde:** nada importante: en teléfonos el ⓘ y las flechas se tocan en lugar de pasar el mouse, y la explicación aparece en la parte de abajo de la pantalla.

## D-041 · Página «Consultas»: constructor de consultas por clics (T-42)

- **Decisión:** una página «Consultas» deja armar una consulta en cuatro pasos, solo con clics: vista (precios semanales, márgenes o alertas), agrupación (producto, región, canal, y semana o mes), filtros con los valores reales de la base y un rango de semanas, y medida (promedio, mediana, mínimo o máximo). Muestra hasta 1.000 filas, un gráfico con la paleta del panel, descarga el resultado completo en CSV y tiene un desplegable «Ver SQL». La lógica vive en `bi/explorer.py`. Vistas, agrupaciones, filtros y medidas salen de listas fijas; los valores elegidos viajan siempre como parámetros `?`, nunca dentro del texto SQL, y la base se abre en solo lectura. Los precios se filtran con SQL generado; márgenes y alertas parten de `k1_margin` y de `bi/alerts.py` y se filtran con pandas. La agrupación y la medida se calculan siempre con pandas. En precios la unidad se agrega siempre a la agrupación; las alertas no tienen región porque usan el precio nacional (D-033).
- **Por qué:** un analista quiere responder preguntas propias sin escribir SQL, como en las vistas de las herramientas de BI de empresa. SQLite no tiene mediana, así que agrupar con pandas da un solo camino para las cuatro medidas. Reusar `k1_margin` y `find_price_alerts` evita tener dos definiciones del margen o de la alerta. Las listas fijas y los parámetros impiden que un texto elegido en el panel cambie la consulta.
- **Descartado:** un motor de base de datos completo; una consola SQL abierta al público; un acordeón con las tablas del modelo (el recorrido de los datos ya está en la página «Pipeline»).
- **Se pierde:** «Producto» junta todas las variedades y calidades, así que su promedio puede diferir de las páginas que separan cada clave (D-007): por ejemplo, la mediana del margen del tomate en feria de la Región Metropolitana da 51,9 % en Consultas y 60,1 % para Larga vida Primera en Márgenes. No se pueden combinar vistas ni guardar consultas.

## D-042 · La semana del 02-05-2022 falta en la fuente y se registra como hueco conocido (T-27)

- **Decisión:** el control de semanas faltantes (D-029) acepta una lista fija de huecos conocidos de la fuente, con una sola entrada por ahora: la semana del 02-05-2022 del archivo de consumidor. Cualquier otra semana faltante sigue deteniendo la carga. Se aplica en T-28, al cargar el histórico.
- **Por qué:** al validar 2022-2025 (T-27), `consumer_2022.csv` pasa de la semana 17 (25 a 29-04-2022) a la 19 (09 a 13-05-2022): no hay ninguna fila con fecha entre el 02 y el 06-05-2022 y la semana 18 es la única ausente entre la 1 y la 52. El archivo se descargó dos veces desde ODEPA el 12-10-2026 con la misma huella (`51fed28d…`), así que el hueco viene de la fuente y no del agente ni del ETL. Sin esta excepción el histórico no se puede cargar. Una lista fija es transparente: deja escrito qué falta y por qué, y el control sigue vigilando todo lo demás.
- **Descartado:** revisar huecos solo en el año en curso, porque el job semanal vuelve a descargar los años cerrados cada semana y un archivo truncado de esos años pasaría sin aviso; quitar el control de semanas; rellenar la semana con un promedio de las vecinas (sería un precio inventado).
- **Se pierde:** esa semana no tiene precio al consumidor en 2022, así que tampoco margen. Las alertas K6 ya ignoran variaciones que cruzan un hueco (D-033), y K4 promedia el año con 51 semanas en vez de 52.

## D-046 · Sin índice único en `weekly_price`; el ETL controla los duplicados (T-28)

- **Decisión:** `etl/schema.sql` deja de crear el índice único `ux_weekly_price_key` y lo borra de las bases que ya lo tenían. Cada carga correcta termina con `VACUUM`, que compacta el archivo. Un data quality check nuevo (`DUPLICATE_KEYS`) detiene la carga si dos precios semanales comparten semana, fuente, canal, región, producto y unidad.
- **Por qué:** con 2022-2026 cargados (2.512.298 filas leídas, 811.578 precios semanales), `datos.db` pesaba 61,6 MB, sobre el aviso de 50 MB de GitHub; el índice ocupaba 24 de esos MB. Sin índice y compactada pesa 33,9 MB, y las consultas del panel tardan lo mismo (K1 0,8 s, K2 1,4 s, K3 1,6 s, medido en una copia). En una simulación de cinco ejecuciones semanales con commit, el historial de Git creció unos 5 MB por semana sin índice y unos 9 MB con él: unos 275 MB al año. La unicidad que daba el índice ya la garantiza el ETL, que reconstruye la tabla entera agrupando por la clave en cada ejecución (D-024, prueba de RN-14), y ahora además la revisa antes de cargar.
- **Descartado:** dejar el índice y aceptar el aviso de GitHub (el límite de 100 MB llegaría en unos tres años); cargar menos años; adelantar la migración a PostgreSQL (T-36).
- **Se pierde:** la base misma ya no rechaza una fila duplicada escrita por otro programa; la protección queda en el ETL. Cada ejecución reescribe el archivo completo al compactarlo.

## D-047 · Los archivos de años cerrados se guardan en la caché de GitHub Actions (T-28)

- **Decisión:** `agent/input.csv` incluye 2022 a 2026. En el job semanal, un paso guarda los CSV en la caché de GitHub Actions con una clave formada por el año en curso y el contenido de `input.csv`. La ingesta salta un año cerrado cuyo archivo ya está y descarga siempre el año en curso. Si la caché venció, descarga todos los años, sin fallar, y la caché se vuelve a guardar.
- **Por qué:** los años cerrados no cambian y descargarlos cada martes son unos 490 MB. Con la caché se baja solo el año en curso. El ETL sigue reconstruyendo todo desde los archivos (D-024), así que no cambia ninguna regla. El año en la clave obliga a descargar completo, una vez en enero, el año que acaba de cerrar; sin él se reutilizaría una copia de mitad de año, y el control de filas (D-029) no lo notaría porque la diferencia es pequeña frente al total.
- **Descartado:** descargar todo cada martes (más carga para ODEPA y más tiempo de ejecución); cargar el histórico una sola vez y que el ETL procese solo el año en curso (obliga a anular D-024, a tratar aparte la semana que cruza dos años y no recoge correcciones de ODEPA en años cerrados).
- **Se pierde:** GitHub borra la caché que no se usa en 7 días y el job corre cada 7 días, así que algunas semanas se descargará todo. Si ODEPA corrige un año cerrado a mitad de año, el cambio entra recién cuando la caché se renueva. Si en la primera ejecución de enero ODEPA aún no publica los últimos días de diciembre, esos días faltarán hasta que la caché se renueve.

## D-048 · K5 por región y canal, y solo cuando la correlación se distingue de cero (T-29)

- **Decisión:** el rezago se calcula sobre los pares de K1 (misma clave, unidad, región y semana), una serie por región y canal del consumidor. Para cada desfase de 0 a 8 semanas se mide la correlación entre el cambio semanal del precio al consumidor y el del mayorista de ese número de semanas antes; los cambios solo se miden entre semanas consecutivas, como en K6. El rezago es el desfase con la correlación más alta, y se muestra solo si supera 2/√pares (aproximación usual de 95 % de confianza); si no, el panel dice «Sin relación clara» y muestra igual las correlaciones. Se ve en la página Márgenes con al menos 26 semanas con ambos precios, junto a la nota de que es descriptivo (D-011). El cálculo vive en `bi/lag.py`.
- **Por qué:** por región se evita que el promedio nacional cambie solo porque esa semana informaron otras regiones. Con los datos de 2026, el tomate Larga vida Primera de la Región Metropolitana muestra en feria una correlación de 0,66 sin desfase, pero en supermercado todas las correlaciones quedan entre −0,17 y 0,14: la más alta (3 semanas, 0,14) apenas supera a la de 1 semana (0,13) y está bajo el umbral de 0,33 que dan 37 pares. Elegir «la más alta» sin ese filtro publicaría ruido como si fuera un resultado. El umbral sale del número de datos, no de una cifra elegida a mano.
- **Descartado:** un rezago nacional; mostrar siempre el desfase de correlación máxima; un umbral fijo de correlación; modelos econométricos (D-011, D-019).
- **Se pierde:** 2/√pares es una aproximación y con nueve desfases probados alguno puede superarlo por azar; por eso el indicador sigue siendo descriptivo. Una relación negativa nunca se informa como rezago.

## D-049 · Versiones SQL de K6 y K5 verificadas contra Python; K4 sin versión doble (T-47)

- **Decisión:** `bi/queries.sql` suma dos consultas alternativas: `k6_usual_range_sql`, que calcula con funciones de ventana la variación semanal, el promedio y la varianza muestral de las 12 variaciones anteriores y la marca de alerta; y `k5_weekly_variations_sql`, que calcula con `LAG()` los cambios semanales de ambos precios solo para las series con al menos 26 semanas (`HAVING`). Python sigue siendo la versión que usa el panel (`bi/alerts.py` y `bi/lag.py`). Un test por indicador compara las dos versiones fila por fila sobre la base real. La correlación de K5 se queda en Python. K4 no tiene versión doble.
- **Por qué:** mostrar el mismo cálculo en SQL y en Python, y probar que coinciden, da confianza en ambos. SQLite no trae desviación estándar y `SQRT` es opcional según cómo se compiló, así que la consulta calcula la varianza muestral como (promedio de los cuadrados − cuadrado del promedio) × 12/11, la misma definición que pandas (n − 1), y escribe la regla |variación − promedio| > 2 × desviación como (variación − promedio)² > 4 × varianza, sin raíz. La correlación de K5 necesitaría en SQL un cruce de la serie consigo misma para cada uno de los nueve desfases y fórmulas de sumas de productos difíciles de leer; pandas la da en una línea. K4 ya se calcula solo en SQL (`k4_seasonal_index`): no hay versión en Python con qué compararla, y crear una solo para el ejercicio no aporta. Con 2022-2026, en una copia de la base, las dos versiones coincidieron en las 113.450 semanas evaluadas por K6 (10.987 alertas, ninguna distinta; diferencia máxima 4 × 10⁻¹⁵) y en los 137.234 cambios semanales de las 1.215 series de K5 (diferencia 0).
- **Descartado:** reemplazar Python por SQL en el panel; calcular la correlación de K5 en SQL; una versión en Python de K4.
- **Se pierde:** la definición de K6 y de las series de K5 está escrita dos veces; los tests de reconciliación avisan si una cambia sin la otra.

## D-043 · «El proyecto» como centro de documentación, en pirámide invertida (T-43)

- **Decisión:** la página «El proyecto» abre con una tarjeta «Empieza aquí» y sigue con 8 pestañas. La tarjeta va en orden de pirámide invertida: arriba un diagrama pequeño del pipeline con el estado real de la última ejecución y las cifras reales de la base, luego el resumen en tres frases y las cifras principales, y al final tres recorridos guiados (gerente, analista, técnico). Las pestañas son: Idea de negocio, Fuentes y cruces, Modelo de datos, KPI y cálculos, Reglas de calidad, Cómo funciona, Decisiones y método, y Código. Los textos se leen de `docs/PROYECTO.md`, `docs/MANUAL.md`, `docs/DISENO.md`, `docs/DECISIONES.md`, `README.md` y `bi/queries.sql`; las cifras se calculan desde `datos.db` en cada visita. La pestaña activa y el perfil viajan en la dirección (`?seccion=…`, `?perfil=…`), así cada gráfico del panel tiene un enlace «¿Cómo se calcula?» que abre la tarjeta de su indicador. Toda animación muestra un dato real: en el diagrama del pipeline los puntos viajan por las flechas solo mientras hay una ejecución en curso.
- **Por qué:** un visitante (reclutador, gerente, analista o técnico) debe entender el proyecto sin pedir explicaciones, y cada cifra debe poder rastrearse hasta su consulta. Una sola fuente por texto evita que el panel y los documentos digan cosas distintas. Las reglas (RN), los indicadores (K) y las preguntas (P) se leen de las tablas de `DISENO.md`; la lista de archivos, del árbol del README; las etiquetas de cláusulas SQL se detectan en el texto de cada consulta, sin agregar ninguna. Los puntos que viajaban siempre por las flechas (D-039) eran decorativos.
- **Descartado:** páginas nuevas para cada tema; copiar los textos dentro del código; una consola SQL abierta; animaciones permanentes.
- **Se pierde:** la página hace más consultas al abrirse (los ejemplos de K1 a K8 y la evidencia de las reglas). Algunas reglas (RN-01, RN-03, RN-13) se explican con un ejemplo documentado de los CSV, porque `datos.db` no guarda el texto original. Cambiar el título de una pestaña rompe los enlaces que apuntan a ella.

## D-050 · El panel lee de la base solo el producto elegido (T-52)

- **Decisión:** las páginas que muestran un producto (Panel, Márgenes, Canales y regiones, Estacionalidad y los ejemplos de «El proyecto») ya no cargan cada indicador completo: piden a SQLite primero la lista de productos para los filtros y después solo las filas del producto elegido, con sus valores como parámetros (`bi/queries.py`: `list_query_keys` y `run_query_for_key`). Ambas respuestas quedan en caché hasta que cambia la base. Esto reemplaza la parte de D-031 que decía «el panel lee cada indicador completo y filtra con pandas». Además: las alertas K6 calculan el rango habitual de una sola pasada sobre toda la columna; la cobertura K7, los conteos de tablas, los ejemplos de los KPI y cada resultado de la página Consultas también quedan en caché; y los años que muestra el panel salen de las semanas cargadas en `weekly_price`, no del registro de descargas.
- **Por qué:** con 2022-2026 cargados, en el panel publicado la primera visita tardó 30,8 s en mostrar el Panel y 18,4 s en «El proyecto», y Consultas tardaba de 6 a 9 s en cada uso (medido el 12-10-2026). K3 traía 798.280 filas para mostrar un producto; filtrado en SQLite trae 7.114 (tomate Larga vida Primera, $/kilo). El cálculo de K6 bajó de 2,13 s a 0,06 s con exactamente las mismas 10.987 alertas (diferencia máxima 2 × 10⁻¹⁴; los tests de reconciliación de D-049 siguen en verde). En local, con la base de 5 años y sin caché, el Panel pasó de 6,8 s a 2,5 s y «El proyecto» de 11,9 s a 5,3 s. D-031 ya anticipaba que con varios años convendría filtrar en SQL.
- **Descartado:** guardar resultados precalculados en tablas nuevas del data warehouse; reemplazar la versión Python de K6 por la SQL (D-049 mantiene Python como versión oficial).
- **Se pierde:** cada cambio de producto hace una consulta nueva a la base (unos 0,35 s la primera vez). La primera visita después de publicar el panel sigue siendo más lenta que las siguientes, porque el servidor arma su caché.

## D-051 · «El proyecto» es la portada y la página Pipeline pasa a la pestaña «Arquitectura»

- **Decisión:** «El proyecto» abre el panel en los dos perfiles. Arriba muestra el pipeline en vivo (un solo diagrama, de ODEPA al panel) con la línea «Estado de la última ejecución (fecha y hora) · se actualiza al recargar la página»; después, las tres frases, las cifras y los recorridos. El diagrama detallado por capas, DevOps, Seguridad, Observabilidad e Informes pasan a una pestaña «Arquitectura»; sus tablas se leen de `docs/PROYECTO.md`. La página Pipeline sale del menú. Sus direcciones viejas siguen funcionando: `/pipeline` abre la pestaña Arquitectura y `/el-proyecto` abre la portada, en ambos casos con los parámetros del enlace. En los diagramas, los puntos que recorren las flechas y las líneas punteadas solo se mueven mientras hay una ejecución en curso; el resto del tiempo el diagrama queda quieto y solo hablan sus puntos de estado. En pantallas de menos de 1000 px el diagrama detallado se dibuja de arriba abajo.
- **Por qué:** quien llega al panel sin guía necesita ver primero qué es el proyecto y si los datos están al día; el pipeline aparecía dos veces (en la portada y en su propia página). Un diagrama que se mueve sin que nada ocurra sugiere actividad que no existe: el movimiento solo tiene sentido si muestra algo real (D-043). Con el diagrama horizontal reducido a un celular, su texto no se podía leer.
- **Descartado:** dejar Pipeline como página aparte del menú; refrescar el diagrama solo cada pocos segundos (consultaría GitHub sin necesidad y gastaría el límite de 60 consultas por hora sin clave).
- **Se pierde:** el diagrama detallado queda un clic más lejos (en una pestaña). El estado no se actualiza solo: hay que recargar la página.

## D-052 · Tres temas: Vantablack (por defecto), Corporativo y Claro (T-44)

- **Decisión:** el lector elige el tema en la barra lateral («Tema»); Vantablack abre por defecto. **Vantablack:** negro profundo con acento cian (#2fd3f0) en el enlace activo del menú, la pestaña elegida, los enlaces y un brillo fino en el borde de las tarjetas. **Corporativo:** menú azul marino, página gris azulada, tarjetas blancas y azul de negocio. **Claro:** blanco y grises fríos, sin beige. Cada tema se apoya en uno de los dos modos base de Streamlit (Vantablack en el oscuro; Corporativo y Claro en el claro), porque las listas, tablas y bloques de código de Streamlit solo siguen ese modo. Streamlit no tiene una función de Python para cambiarlo: el panel escribe la elección en el mismo lugar del navegador que usa su menú ⋮ → Settings (`localStorage`, clave `stActiveTheme-<ruta>-v2`) y recarga la página una sola vez. Los colores de los canales no cambian: son los validados para daltonismo de cada modo base (D-037), y se volvieron a validar contra las tarjetas nuevas (`#0b0c0f` y `#ffffff`): pasan todos los controles; en blanco, tres canales siguen bajo 3:1 de contraste, como en el tema claro anterior, y por eso sus gráficos llevan etiquetas o tabla. Esto reemplaza la parte de D-037 que dejaba el cambio entre modo oscuro y claro al menú ⋮ → Settings.
- **Por qué:** el panel debe verse bien para públicos distintos: Vantablack para lucir el producto, Corporativo para quien espera un tablero sobrio de empresa y Claro para leer de día o imprimir. El beige del tema claro anterior se parecía al estilo genérico de muchas herramientas de IA.
- **Descartado:** dibujar los tres temas solo con CSS sobre un modo fijo (las tablas de Streamlit quedarían oscuras en un tema claro); cambiar también los colores de los canales por tema (habría que validar paletas nuevas y el lector perdería los colores que ya aprendió).
- **Se pierde:** al pasar de Vantablack a un tema claro, o al revés, la página se recarga una vez. El cambio de modo base usa una clave interna de Streamlit: si una versión futura la cambia, el tema se sigue aplicando a la página, el menú y los gráficos, pero las listas y tablas quedan en el modo anterior hasta que el lector lo cambie en ⋮ → Settings (MANUAL, «Fallas del panel publicado»). El intento se hace una sola vez por página, así que la página nunca se recarga en bucle.

## D-053 · Enlaces del proyecto en cada página y administración tras la clave de control (T-54)

- **Decisión:** una sola lista en el código (`PROJECT_LINKS`, `bi/project.py`) con los enlaces del proyecto: código, ejecuciones, informes semanales, historial de cambios, las dos fuentes de ODEPA, MANUAL y DECISIONES; el video y el post de LinkedIn ya tienen su lugar y aparecen cuando tengan dirección. Se muestran al pie de cada página y, en el Centro de control, en una tarjeta propia (ahí el pie no los repite). Cada enlace es nombre, ícono y una línea de descripción, se abre en una pestaña nueva y tiene un botón «Copiar enlace» que copia la dirección sin mostrarla, con `st.html` y una línea de JavaScript (sin librerías nuevas). La tarjeta «🔒 Administración» reemplaza a «Ejecutar ahora»: sin la clave de control solo dice «Requiere clave de control»; con ella muestra la administración de Streamlit, el workflow en GitHub, crear y ver tokens, el vencimiento del token (leído de la cabecera `GitHub-Authentication-Token-Expiration` de `/rate_limit`, que no gasta el límite de consultas) y el botón «Ejecutar ahora». `.streamlit/secrets.toml` queda en `.gitignore`.
- **Por qué:** quien llega al panel debe poder ir al código, a los informes y a las fuentes sin buscar el repositorio; el autor necesita sus accesos de administración en un solo lugar y saber a tiempo cuándo vence el token (si vence, «Ejecutar ahora» deja de funcionar sin aviso). Una dirección larga escrita como texto no se lee ni se toca bien en un celular.
- **Descartado:** escribir la clave en el enlace (quedaría en el historial del navegador y se filtraría al compartirlo); mostrar los últimos caracteres del token para reconocerlo; una librería de portapapeles.
- **Se pierde:** la clave de control no es un inicio de sesión: ordena el acceso, pero la seguridad real está en las cuentas de GitHub y Streamlit (MANUAL, «Administración y enlaces»). Abrir la administración con la clave dura lo que dura la sesión del navegador.

## D-054 · Cada diagrama en su propia pestaña de «Diagramas y pipeline»

- **Decisión:** «El proyecto» describe el proyecto y muestra el pipeline en cinco pasos con la línea «Estado de la última ejecución (fecha y hora) · se actualiza al recargar la página», sin enlace a la arquitectura. Los diagramas completos pasan a una página nueva, «Diagramas y pipeline», segunda en el menú de los dos perfiles, con una pestaña por diagrama: «Pipeline» (el recorrido completo por capas, sin cambios), «Esquema estrella» (el modelo de `datos.db` con sus filas reales) y «Arquitectura y DevOps» (diagrama nuevo de infraestructura por plataforma, estilo C4: un recuadro por plataforma con sus componentes dentro, ODEPA, tu computador con VS Code y Claude Code, GitHub con repositorio, job semanal, pruebas, caché, Issues y permisos, Streamlit Community Cloud con la app y sus secretos, y los usuarios; cada conexión dice cómo se comunican las piezas, por ejemplo HTTPS · CSV, git push, `st.secrets`; ninguna línea cruza otra. Le siguen las tablas DevOps, Seguridad, Observabilidad e Informes). El diagrama nuevo sigue las reglas de D-043 y D-051: cifras reales (tamaño de `datos.db`, funciones de prueba, precios de la última semana, próxima ejecución), punto de color solo con un estado real, movimiento solo con una ejecución en curso. Las direcciones viejas siguen funcionando: `/pipeline` abre la pestaña «Pipeline»; `?seccion=Arquitectura` y `?seccion=Modelo de datos` en la portada abren su nueva pestaña. Reemplaza la parte de D-051 que ponía el diagrama detallado en la pestaña «Arquitectura» de «El proyecto».
- **Por qué:** el mismo diagrama aparecía dos veces en una página (portada y pestaña), lo que confunde y alarga la portada. Con una pestaña por diagrama, cada uno tiene un solo lugar y un enlace propio, y la portada se lee en segundos.
- **Descartado:** un diagrama de arquitectura dibujado como flujo de izquierda a derecha (se leía como un segundo pipeline, no como infraestructura); el diagrama completo en la portada (repetía el de la pestaña); ocultarlo según la pestaña abierta (Streamlit no vuelve a ejecutar la página al cambiar de pestaña, así que la página no sabe cuál está abierta); el estado del workflow `pruebas.yml` en el diagrama (una consulta más a GitHub por visita, con un límite de 60 por hora sin clave).
- **Se pierde:** la portada ya no muestra el diagrama completo; hay que abrir la página «Diagramas y pipeline». En celular el mini tiene texto pequeño. El diagrama de arquitectura global no tiene versión vertical: en pantallas angostas se ajusta al ancho y se acerca con zoom (D-055).

## D-055 · Modelo estrella dibujado como estrella y zoom en los diagramas (T-59)

- **Decisión:** el esquema estrella se dibuja como una estrella de cuatro puntas en SVG con `viewBox`: `weekly_price` al centro y una dimensión en cada punta (Semana arriba, con borde punteado y «mejora: dim_date»; `dim_product` a la izquierda, `dim_region` a la derecha y `dim_channel` abajo), con conectores punteados cian. Cada tabla muestra sus columnas reales, leídas de `etl/schema.sql`; PK y FK van en cian y, en `weekly_price`, las medidas (`price`, `volume`, `observation_count`) van aparte al pie. En Vantablack, tarjetas negras (#000) sobre un marco #0b0b0d con bordes cian (#22d3ee); en los temas claros, un cian más oscuro (#0e7490) para que el texto se lea. Debajo, un panel del mismo ancho explica la tabla bajo el mouse, o la tocada en el celular, con su JOIN y sus cifras reales (filas, semanas, hora de los datos); la nota «etl_run → rejection» queda fuera de la estrella. El panel no usa JavaScript: cada tabla se puede enfocar y el CSS elige el panel con `:has()`. Los tres diagramas de la página (pipeline, estrella y arquitectura) se abren ajustados al ancho y tienen zoom: dos dedos acercan, un dedo o el mouse arrastran dentro del marco, y tres botones (＋ － ⟲) bajo el marco, a la derecha, para que nunca tapen el diagrama. El zoom ensancha el diagrama en vez de agrandar una imagen, así el navegador lo redibuja y se ve nítido; nunca cambia su forma. Es un script propio, sin librerías nuevas. En celular el pipeline sigue usando su versión vertical (D-051), ahora también con zoom.
- **Por qué:** el gráfico de Graphviz no mostraba columnas ni claves, y su forma no se parecía a una estrella. En celular cualquier diagrama ancho queda pequeño; el zoom lo hace legible sin dibujar otra versión.
- **Descartado:** una librería de zoom (agrega una dependencia para unas 100 líneas de JavaScript); agrandar con `transform: scale` (el navegador puede escalar una imagen ya dibujada y el texto se ve borroso); un iframe de componentes (altura fija y el panel quedaría aislado de la página).
- **Se pierde:** el panel y el zoom dependen de `:has()` y de los eventos de puntero, disponibles en los navegadores actuales; en uno antiguo la estrella se ve igual, pero el panel se queda en `weekly_price` y no hay zoom. El script del zoom usa `st.html` con JavaScript, igual que «Copiar enlace» (D-053).

## D-056 · Panel organizado por tipo de contenido: cinco entradas con pestañas

- **Decisión:** el menú tiene cinco entradas, iguales para todos, y cada una sus pestañas. **Inicio:** portada corta (línea de estado del pipeline y, en celular, el pipeline en cinco pasos; tres frases, cifras y los recorridos «Soy gerente / analista / técnico») y la documentación en pestañas: Idea de negocio (con Fuentes y cruces al final), KPI y cálculos, Reglas de calidad, Cómo funciona, Decisiones y método y Glosario. **Análisis:** todos los gráficos (Esta semana, Brecha de precio, Canales y regiones, Estacionalidad, Alertas), con los filtros de grupo, producto, variedad, región y canal una sola vez arriba; valen para todas las pestañas y se recuerdan al volver a la página. **Arquitectura:** todos los diagramas (Pipeline, Modelo de datos, DevOps y seguridad). **Datos y código:** Consulta por clics, Queries y Código. **Operaciones:** Ejecuciones (estado, historial y, con la clave de control, «Ejecutar ahora» y los enlaces de administración), Calidad de datos y Enlaces, el único lugar con los enlaces del proyecto. Nada se repite entre secciones. Las direcciones viejas (`/panel`, `/margenes`, `/canales-y-regiones`, `/estacionalidad`, `/alertas`, `/consultas`, `/centro-de-control`, `/calidad-de-datos`, `/pipeline`, `/el-proyecto`) abren su nueva pestaña, y las pestañas que salieron de la portada (Fuentes y cruces, Arquitectura, Modelo de datos, Código) también. El glosario se lee de `docs/PROYECTO.md` (T-46b). Reemplaza la organización de D-054 (página «Diagramas y pipeline») y la ubicación de los enlaces de D-053 (al pie de cada página).
- **Por qué:** con una página por gráfico y los enlaces al pie de todas, el visitante se dispersaba y veía lo mismo en varios lugares. Agrupar por tipo (documentación, gráficos, diagramas, datos y código, operación) da a cada cosa un solo lugar y deja la portada en lo esencial.
- **Descartado:** mantener el selector «¿Quién consulta?» (con un solo menú para todos ya no cambia nada; los recorridos guían a cada perfil); un filtro por pestaña (obligaba a elegir el mismo producto varias veces); dejar los enlaces al pie de cada página.
- **Se pierde:** Alertas muestra todos los productos y Canales y regiones todos los canales y regiones del producto: ahí los filtros de región o canal no aplican, y la página lo dice. La pestaña «Esta semana» muestra el resumen actual; el Top N de T-58 se agregará cuando exista. Los enlaces con `?perfil=` siguen abriendo el panel, pero el parámetro ya no hace nada.

## D-057 · Secciones de texto en bloques: título y frase, tarjetas, pasos y detalles plegados

- **Decisión:** cada sección de texto del panel empieza con un título y una frase que dice para qué sirve, y ordena su contenido de lo más útil a los detalles (o en orden cronológico cuando describe un proceso). Los temas independientes van en tarjetas dentro de una grilla que pone las tarjetas lado a lado cuando caben y las apila en pantallas angostas (ancho mínimo de 260 px por tarjeta: nunca se comprime una columna). Las secuencias van en pasos numerados; las tablas quedan solo para comparaciones reales. Los detalles técnicos (archivos, tablas, reglas, SQL) se pliegan en «Ver detalles». Los enlaces dicen su destino («Ver en Análisis › Brecha de precio») y no se repite una explicación entre páginas. Los textos largos siguen en `docs/PROYECTO.md` y el panel los lee de ahí. Se aplica sección por sección, empezando por «Idea de negocio». En pantallas de menos de 1024 px (tabletas y ventanas angostas) el menú lateral se pliega una vez por visita para dejar todo el ancho al contenido; si el lector lo abre, queda abierto.
- **Por qué:** con columnas fijas, en tableta y celular los párrafos quedaban de dos o tres palabras por línea y las tablas se salían de la pantalla; varias páginas repetían la misma explicación. Una portada que se recorre en bloques permite entender lo esencial primero y abrir el detalle solo cuando hace falta.
- **Descartado:** una librería de componentes (agrega una dependencia para lo que resuelve una grilla CSS); reducir el texto borrando límites, fórmulas o fuentes; columnas de Streamlit para las tarjetas (no se apilan antes de 640 px y comprimen el texto en tableta).
- **Se pierde:** las tarjetas son HTML dentro de Markdown, así que su texto no admite todo Markdown: solo **negrita** y `código`, que es lo que usan los documentos.

## D-058 · Los enlaces del proyecto tienen su propia entrada en el menú

- **Decisión:** los enlaces públicos del proyecto pasan de la pestaña «Enlaces» de «Operaciones» a una sexta entrada del menú, «Enlaces», agrupados en código y operación, fuentes de datos y documentos, con el mismo diseño de tarjetas y «Copiar enlace» (D-053). Es el único lugar del panel con esos enlaces: la tabla de archivos y la pestaña «DevOps y seguridad» remiten a esa página en vez de repetir un enlace. La tarjeta «🔒 Administración», con «Ejecutar ahora» y los enlaces de administración, queda en «Operaciones» → «Ejecuciones», junto al historial de ejecuciones. La dirección vieja (`/operaciones?seccion=Enlaces`) abre la página nueva. Modifica la ubicación de los enlaces de D-056.
- **Por qué:** dentro de «Operaciones» los enlaces quedaban escondidos detrás de una pestaña; quien busca el código o las fuentes los encuentra antes en el menú, que siempre está a la vista.
- **Descartado:** mover también la administración a «Enlaces» (separaría «Ejecutar ahora» del historial que muestra su resultado).
- **Se pierde:** una entrada más en el menú (seis en vez de cinco).

## D-059 · La forma de cada gráfico de «Análisis» depende de su pregunta

- **Decisión:** línea solo para «¿cómo evolucionó?», con una o dos líneas por gráfico; barras para comparar o rankear; número grande para «¿cuánto esta semana?». **Esta semana:** tarjetas de precio con número grande, variación ▲▼ y una línea pequeña de las últimas 12 semanas, y un ranking de las mayores variaciones de la semana en barras horizontales ordenadas (▲▼, color y número) para el grupo y los canales elegidos. **Brecha de precio:** un gráfico de pesas (dumbbell) con el precio mayorista y el de cada canal unidos, y la evolución de la brecha en una sola línea por canal (52 semanas). **Canales y regiones:** barras horizontales ordenadas con la línea de referencia nombrada («Promedio nacional» o el canal de comparación). **Estacionalidad:** un calendario de calor meses × años por canal, más oscuro = más caro, con leyenda. **Alertas:** una lista con semáforo (ícono y etiqueta: ● moderada, ▲ alta, ◆ muy alta) y una barra que mide cuántas desviaciones estándar se alejó el cambio de su rango habitual, con el límite de 2 marcado. El histórico largo de cada pestaña va en «Ver evolución histórica». Cada gráfico explica en su ⓘ qué muestra y cómo leerlo. Colores: los de canal ya validados; el calendario usa una rampa de un solo tono, cian en Vantablack y azul en los temas claros, y el semáforo los colores de estado de referencia, siempre con ícono y etiqueta. Las rampas pasaron el validador de paletas (`validate_palette.js --ordinal`) contra la tarjeta de cada tema.
- **Por qué:** tres o más líneas superpuestas de cinco años se leían como ruido; la mayoría de las preguntas del panel no son de evolución sino de comparación o de «cuánto ahora».
- **Descartado:** quitar el histórico (se pliega, no se borra); una escala común para los calendarios de varios canales (cada canal tiene su propio rango; el índice ya es relativo a su año); el margen mediano por canal (el gráfico de pesas lo reemplaza con el dato de la semana).
- **Se pierde:** «Esta semana» ya no repite el índice regional ni la lista de alertas: están en «Canales y regiones» y en «Alertas». El ranking es de la última semana y del grupo elegido; el Top N de todos los grupos (T-58) queda pendiente.

## D-060 · Portafolio desde el resultado, con navegación directa y código abierto

- **Decisión:** el inicio muestra primero el dashboard con rankings Top N de la última semana disponible, sin exigir filtros de producto; siguen el pipeline vivo y la arquitectura por plataforma en la misma página. La barra lateral organiza el recorrido en Portafolio, Construcción, Operación y Documentación, con entradas directas a negocio (BA), indicadores (BI), modelo, datos y SQL, código, DevOps, monitoreo y ejecuciones. Análisis abre con el panorama general y después ofrece filtros para profundizar. El código Python se presenta por carpeta y archivo en orden del flujo, con propósito, entradas, salidas, problema resuelto y fuente real; los acordeones están abiertos por defecto. Sigue SQL, con esquemas y consultas explicadas. Los enlaces se presentan como listas agrupadas.
- **Por qué:** un portafolio debe permitir apreciar primero el resultado y después comprobar cómo se construyó. Pedir un producto antes de mostrar datos o esconder la operación tras varias pestañas dificultaba ese recorrido.
- **Perfil y temas:** un diálogo inicial solicita el perfil antes de mostrar datos. El perfil sugiere un recorrido y no limita acceso; se conserva en la sesión y en los enlaces internos para no repetir la pregunta al navegar o cambiar de tema. Solo se ofrecen Vantablack y Corporativo; los enlaces antiguos a Claro pasan a Corporativo. Vantablack conserva el fondo negro, con tarjetas y campos en tonos pizarra y texto contrastado. Los hints explican el gráfico y los identificadores K en contexto.
- **Criterio de datos:** variaciones semanales calculadas solo entre semanas consecutivas; las brechas conservan semana, producto, región, canal y unidad comparables. Top N no significa todos los productos ni utilidad del comercio. El visitante puede cambiar N, separar alzas y bajas y descargar el ranking.
- **Se pierde:** el menú tiene más entradas visibles y el código ocupa más espacio vertical. El orden del código representa el flujo de datos, no afirma una cronología de commits. Se actualiza la organización de D-056, D-058 y la selección de temas de D-052. No cambia las reglas de negocio del ETL.

## D-061 · Una ubicación por contenido, con enlaces desde el resto del recorrido

- **Decisión:** el panorama nacional Top N, el pipeline y la arquitectura por plataforma viven solo en Dashboard. Análisis contiene el análisis filtrado y enlaza al panorama; DevOps conserva sus explicaciones y enlaza a la arquitectura. Las alertas detalladas viven en Análisis; Dashboard conserva su cifra resumen. El catálogo de queries vive solo en Datos y SQL → Queries. Los indicadores conservan su fórmula y ejemplo real, con un enlace a la consulta original; la query solicitada aparece primero, sin copiarla. Código Python y SQL muestra los archivos Python y los dos esquemas SQL una vez; enlaza al catálogo de queries. Modelo de datos y Queries enlazan a los esquemas. Las versiones Python de una query enlazan al archivo Python completo en vez de copiar sus funciones. El estado y la leyenda del pipeline se presentan una vez en Dashboard.
- **Por qué:** el autor pide que nada esté duplicado. Repetir bloques alarga el recorrido y genera varias ubicaciones que parecen ser la fuente del mismo contenido.
- **Alcance:** una referencia o un enlace no copia el contenido. Una vista filtrada sobre una selección distinta conserva su propósito analítico; las representaciones alternativas de un mismo ranking en móvil y escritorio son excluyentes según el ancho. Se modifica la ubicación de contenidos de D-060.
- **Se pierde:** para ver el código SQL desde un indicador o la arquitectura desde DevOps se sigue un enlace interno. Se conserva el contexto mediante el nombre de la consulta solicitada.

## D-062 · Proyecto operativo, navegación directa y representación por función

- **Decisión:** el sistema se presenta como Monitor de precios de alimentos. Tras elegir cualquier perfil se abre siempre Dashboard, que contiene resultados y no diagramas. Pipeline y arquitectura es su ubicación única, dentro de Definición y diseño; el modelo de datos mantiene su sección propia. El marco de negocio se redacta con misión, visión, objetivo, alcance, exclusiones, stakeholders, requisitos, entregables y criterios de aceptación. Se eliminan las pestañas internas: cada análisis, la consulta de datos y el catálogo SQL tienen acceso directo en el menú lateral.
- **Recorrido:** Resultados → Definición y diseño → Análisis BI → Datos e implementación → Operación → Documentación. Todas las páginas ofrecen Anterior y Siguiente al inicio y al final, en el mismo orden que el menú. Los enlaces antiguos a pestañas abren su destino actual. El perfil y el tema se conservan durante la navegación.
- **Movimiento y estado:** la animación ilustra el recorrido de datos de fuente a BI, se activa por defecto y se puede pausar. Los colores y estados siguen basados en la ejecución real; la animación no afirma que haya una carga ejecutándose. Se respeta la preferencia de movimiento reducido. Actualiza la restricción de animación de D-043.
- **Lenguaje visual:** los componentes se distinguen por función: escudos para seguridad, cilindros para datos, flechas y nodos para automatización, ejes para indicadores y documentos/editor para código e informes. Las formas conservan el texto legible y se adaptan al ancho; no sustituyen las etiquetas ni los estados.
- **Por qué:** el autor pide una presentación de resolución de un problema real, con acceso directo a cada parte y un recorrido continuo. Actualiza D-060 y D-061 en ubicación y navegación, manteniendo la regla de una ubicación por contenido.
- **Se pierde:** el menú lateral incluye más destinos directos y necesita desplazamiento en pantallas pequeñas. Las formas indican la función de un componente; no añaden capacidades operativas ni medidas nuevas.

## D-063 · Fondo alimentario y paneles flotantes para el dashboard

- **Decisión:** Dashboard incorpora un fondo ilustrativo de productos de mercado, guardado en el repositorio, y superficies elevadas con sombras, bordes suaves y transparencia controlada. Los cuatro indicadores tienen superficies individuales; los rankings conservan sus gráficos Altair, detalles al pasar el mouse, controles y descarga. El fondo y los cambios de superficie se limitan al dashboard. Vantablack y Corporativo tienen velos y superficies propios para conservar el contraste; los paneles se apilan cuando falta ancho.
- **Interacción:** los controles Top N, alzas y bajas preceden los gráficos. Todos los acordeones de todas las páginas abren por defecto y el visitante puede cerrarlos; incluye históricos, documentos, archivos y datos, actualizando los detalles plegados de D-057 y D-059. El estado de ejecución sigue abierto al terminar. No se duplican datos, diagramas ni consultas.
- **Por qué:** la usuaria solicita una presentación ligada al producto, inspirada en paneles flotantes sobre una fotografía, manteniendo la exploración real de datos.
- **Alcance:** el fondo es una imagen generada y decorativa, sin afirmar una ubicación real ni pertenencia a ODEPA. Archivo y prompt en bi/assets. Los gráficos y controles son componentes independientes de la imagen.
- **Se pierde:** se añade un recurso JPEG de aproximadamente 376 KiB; las páginas con todos sus detalles abiertos requieren más desplazamiento vertical.

## D-064 · Variedad de gráficos y exploración territorial en 3D

- **Decisión:** Dashboard combina un anillo de observaciones válidas por grupo, curvas con área de precios nacionales de las últimas 12 semanas, una escena territorial 3D y los rankings existentes en barras. La escena usa región, canal e índice de precio regional como tres ejes reales; se puede girar, acercar y consultar cada punto. «Mapa 2D» reemplaza la escena con una matriz de los mismos valores. Se conserva la paleta de canales y el fondo de D-063, con dominante visual Vantablack y superficies pizarra.
- **Datos:** se reutilizan las consultas canónicas K3 y K6. Se elige inicialmente la clave con más observaciones válidas de la última semana, con desempate estable; el selector conserva grupo, producto, variedad, calidad y unidad. El índice 100 corresponde al promedio nacional de ese mismo canal. El anillo cuenta observaciones, sin mezclar precios ni presentarlas como participación de mercado. Las curvas no apilan precios y dejan vacías las semanas sin datos.
- **Por qué:** la usuaria solicita diversidad visual y 3D, manteniendo la interactividad. Cada tipo responde a una pregunta distinta y la alternativa 2D facilita leer cifras o usar dispositivos sin WebGL.
- **Implementación:** Plotly se añade a requirements.txt; bi/market_charts.py genera las figuras. La integración mantiene abiertas las secciones y evita mostrar simultáneamente 2D y 3D del mismo índice. Referencias: [Scatter3d de Plotly](https://plotly.com/python/reference/scatter3d/) y [st.plotly_chart de Streamlit](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart).
- **Se pierde:** una dependencia adicional y más altura en el dashboard; la perspectiva 3D dificulta comparaciones exactas, para las que se ofrece el mapa 2D.

## D-065 · Seis ventanas por tema; las vistas cambian dentro de la ventana

- **Decisión:** el menú lateral tiene seis ventanas numeradas: 01 · Dashboard, 02 · Proyecto y negocio, 03 · Arquitectura, 04 · Datos y código, 05 · Operación y 06 · Documentación. Cada ventana tiene solo su tema, y sus vistas se cambian con un selector y botones ◀ ▶, sin cambiar de página ni de ventana. Todos los gráficos de datos están en Dashboard, de lo más importante a lo menos: Dashboard (resumen), Esta semana, Brecha de precio, Canales y regiones, Alertas, Histórico y estacionalidad, y Vista 3D. El pipeline, el modelo de datos y DevOps quedan en Arquitectura: son diagramas del sistema, no gráficos de los datos. La Vista 3D suma dos gráficos en tres dimensiones a la vista territorial: la brecha por canal como cintas a lo largo de 26 semanas y la estacionalidad como superficie mes × año; cada uno con su versión plana, porque el valor exacto se lee mejor en 2D. La elección de perfil se ofrece una vez por sesión y ya no es obligatoria. Las direcciones antiguas (de las 21 páginas de D-060 a D-064 y de antes) abren su ventana en la misma vista.
- **Por qué:** con una página por gráfico el lector tenía que saltar entre páginas para ver un mismo tema; una ventana por tema, con sus vistas a un clic, deja todo el análisis en un lugar.
- **Descartado:** subsecciones en acordeón para todas las ventanas (Streamlit dibuja el contenido de todos los desplegables, aun cerrados, y la página se vuelve lenta; el selector dibuja solo la vista elegida); gestos de deslizar (los botones ◀ ▶ bastan y funcionan con mouse y teclado).
- **Se pierde:** una vista no se ve junto a otra de la misma ventana. El 3D necesita WebGL; sin él, cada gráfico ofrece su versión plana.

## D-066 · El perfil ordena las ventanas; no se muestra después de entrar

- **Decisión:** el perfil elegido al entrar ordena las mismas seis ventanas según quien visita, las numera en ese orden y abre la primera. Reclutamiento: Dashboard, Arquitectura, Datos y código, Proyecto y negocio, Operación, Documentación. Negocio / gerencia: Dashboard, Proyecto y negocio, Documentación, Operación, Arquitectura, Datos y código. Analista BI: Dashboard, Datos y código, Proyecto y negocio, Arquitectura, Operación, Documentación. Ingeniería de datos: Arquitectura, Operación, Datos y código, Dashboard, Proyecto y negocio, Documentación. Sin perfil, el orden por defecto (Dashboard primero). El perfil ya no aparece en la barra lateral ni tiene botón para cambiarlo; queda en la dirección (`?perfil=…`), así un enlace compartido abre el mismo orden.
- **Por qué:** hasta ahora el perfil solo agregaba una frase bajo las cifras; no organizaba nada. Ordenar sin ocultar deja toda la información a todos y pone primero lo que cada visitante viene a ver.
- **Descartado:** mostrar u ocultar ventanas según el perfil (alguien de negocio que quiera ver el código no debe buscarlo en otro lado); mostrar el perfil en la barra (ocupa espacio sin aportar después de entrar).
- **Se pierde:** para cambiar de perfil hay que abrir de nuevo el panel sin `?perfil=` en la dirección.

## D-067 · Cada vista del Dashboard cabe en una pantalla, como una página de informe

- **Decisión:** las siete vistas del Dashboard se leen completas en una pantalla de 1440 × 900 sin desplazarse, como una página de Looker o Power BI. El título y la fecha van en una sola línea (la frase explicativa queda al pasar el mouse sobre el título); en la vista principal los controles (Top N, orden y producto) comparten esa línea como barra de filtros; las cifras van en una línea cada una; los gráficos se ordenan en una grilla de dos filas con una altura fija por tarjeta (255 px). Esta semana: tarjetas de precio 2 × 2 y el ranking al lado. Brecha de precio: pesas arriba y una línea por canal debajo. Alertas: las 8 más lejanas. Histórico y Vista 3D: dos gráficos lado a lado. El enlace a cada KPI se acorta a «K6 ↗» (la pregunta completa al pasar el mouse) para no empujar el gráfico una línea. Lo secundario queda debajo y se alcanza desplazándose: la tabla del ranking (con pesos, porcentajes y fechas en formato chileno), el rezago K5, la evolución histórica y la tabla de alertas, plegados. Las demás ventanas (documentación, código, arquitectura) siguen como páginas de lectura.
- **Por qué:** un dashboard que obliga a desplazarse para ver sus propios gráficos no se lee de un vistazo; el lector debe ver la respuesta completa y bajar solo para el detalle.
- **Descartado:** reducir todos los gráficos a miniaturas (se leen peor); una vista por gráfico (vuelve a dispersar el análisis); desplazamiento interno dentro de las tarjetas (esconde datos).
- **Se pierde:** los gráficos son más bajos que antes; en pantallas de menos de 900 px de alto, o en celular, la grilla se apila y vuelve el desplazamiento.

## D-068 · Dashboard claro para un visitante: brechas comparables y cifras de negocio

- **Decisión:** las brechas sobre +300 % salen del ranking «Top · brechas» y de la brecha mediana, y se listan aparte («Brechas excluidas del ranking») con su precio mayorista, su precio al consumidor y su unidad; no se borran de la base y siguen en «Brecha de precio». Arriba del Dashboard va una frase de resumen calculada con los datos de la semana («Esta semana subieron N precios y bajaron M; K productos subieron más de 10 %; la mayor alza fue …»). Las cifras pasan a ser de negocio, cada una con su cambio frente a la semana anterior en palabras y flecha: cambio típico de los precios (la mediana de las variaciones semanales), precios que suben / bajan, brecha mediana mayorista–consumidor (solo pares comparables) y alertas activas. Las cifras técnicas (semana, series comparadas, precios semanales históricos) quedan en una línea pequeña de contexto. El pulso de precios muestra tres canales (Mayorista, Feria libre, Supermercado) y el resto se elige en un selector, con un máximo de tres. El anillo de composición se reemplaza por «¿Qué grupo subió más?» (cambio típico de cada grupo). El mapa de territorio muestra solo los canales y regiones con datos en al menos la mitad del otro eje. Se quita la foto de fondo (fondo liso y paneles livianos). Las barras usan un nombre corto (producto y canal) y el detalle (variedad, calidad, región, unidad, precio) va en la ayuda al pasar el mouse.
- **Por qué:** la frutilla aparecía con +836 % y la naranja con +700 %. Una consulta a los archivos de ODEPA mostró que no es un error de unidades (ambas fuentes están en $/kilo y la conversión es correcta), sino de formato: el mayorista vende a granel (frutilla en «$/bandeja 7 kilos», unos $1.000 el kilo; naranja en «$/bins (400 kilos)», unos $350 el kilo) y el supermercado envasado ($9.600 y $2.650 el kilo). En la feria libre, que vende a granel como el mayorista, el 99 % de las brechas queda bajo +253 %; en el supermercado el 16 % supera +300 %. Esas brechas no comparan lo mismo. Un precio promedio de todos los productos mezclaría pesos por kilo y por unidad, por eso la cifra de precios es el cambio típico.
- **Descartado:** corregir la brecha en el ETL (cambiaría K1 en todo el panel por un problema de formato que solo se nota en los extremos); excluir por canal completo (el supermercado tiene brechas comparables); un umbral sin datos.
- **Se pierde:** una brecha real de un formato envasado no aparece en el ranking aunque sea la mayor; queda en la lista de excluidas.

## D-069 · Dashboard interactivo como Looker o Power BI: filtro cruzado, bajada por categoría y una barra de filtros

- **Decisión:** el Dashboard se filtra con clics. Un clic en una barra de «Top · cambios» o de «Top · brechas» elige ese producto (con su variedad, calidad y unidad) y todos los gráficos lo siguen: el pulso de 12 semanas, el mapa por región y canal y las brechas; arriba aparece el chip «Filtro: Lechuga Española ✕», que lo quita. Un clic en «¿Qué grupo subió más?» baja a esa categoría, con migas «Todas › Frutas › Producto» para volver a subir. Un clic en una región del mapa filtra las brechas por esa región (chip «Región: … ✕»). Toda la fila de una barra recibe el clic, no solo la barra (una barra de +0,1 % es casi invisible); doble clic suelta la selección. Una sola barra de filtros (categoría, región y semana, de las últimas 26) va en la cabecera, junto a la página y ◀ ▶, y se mantiene al cambiar de vista; en las demás vistas la categoría y la región quedan fijas «desde la barra del informe». La cabecera, el título y los controles del ranking ocupan una línea cada uno, y la vista vuelve a caber en 1440 × 900 (el último gráfico termina a 842 px). El título de cada tarjeta va en una línea con «Cómo se calcula ↗» a la derecha (si no cabe, el título se acorta con «…» y se lee completo al pasar el mouse). En tablet la cabecera pasa a dos filas; en celular ◀ ▶ quedan al lado de la página, compactos, y los filtros van de a dos. Antes del primer clic, el pulso y el mapa muestran el primer producto del ranking que tiene precio en dos regiones o más. El mapa escribe el índice sin decimales (102, no 102,05) con tinta oscura o blanca según el color de la celda. Un cambio que redondea a 0,0 % dice «Sin cambio», no «Bajó 0,0 %».
- **Por qué:** en Looker o Power BI el lector pregunta con el mouse: hace clic en lo que le llama la atención y el resto del informe responde. Las respuestas toman menos de un segundo (0,46 a 0,77 s medidos en el navegador) porque los precios nacionales, las brechas y el índice regional de cada semana se leen una vez y se filtran en memoria.
- **Descartado:** un selector de producto aparte (obliga a buscar lo que ya está a la vista en el ranking); filtros dentro de cada vista (se pierden al cambiar de vista); Plotly para el mapa (Altair devuelve el clic al panel sin otra librería).
- **Se pierde:** el producto elegido filtra por su clave completa: un producto con precio solo mayorista no tiene brecha ni mapa, y la tarjeta lo dice en vez de mostrar un gráfico vacío.

## D-070 · Recorrido de portafolio: El proyecto → Dashboard → Código y resultados → Detalle técnico

- **Decisión:** el menú pasa de seis ventanas por tema a un recorrido de cuatro pasos numerados, como un CV con sus evidencias: «El proyecto» (definición, indicadores explicados, reglas de calidad, decisiones y glosario), «Dashboard» (las vistas de análisis), «Código y resultados» (consultas SQL, código Python y SQL; la consulta por clics sigue aquí hasta su retiro) y «Detalle técnico» (pipeline y arquitectura con el diagrama original, modelo de datos, monitoreo, ejecuciones, DevOps y manual). «Fuentes y enlaces» queda aparte, como referencia. Al pie de cada paso, «← Volver» y «Siguiente →» abren la sección vecina en la misma ventana y dicen qué muestra el paso siguiente. Cada sección cambia de vista con ◀ [vista ▾] ▶ en la cabecera, igual que el Dashboard, también en celular. El tema se guarda en la sesión y se escribe en la dirección en cada ejecución; Streamlit recuerda la base de sus controles por dirección, así que el tema se registra para todas las secciones a la vez y pasar de una sección a otra ya no recarga la página (una recarga abría una sesión nueva y borraba los filtros). La ventana flotante de perfil se reemplaza por una elección opcional dentro de «El proyecto»: el perfil decide por dónde empieza la visita (Reclutamiento: el proyecto; Negocio / gerencia y Analista BI: el dashboard; Ingeniería de datos: el detalle técnico) y qué vista abre primero en cada sección; no oculta nada. Se retira la Vista 3D. Todas las direcciones del proyecto, incluidas las de administración, quedan en `bi/project.py`; cada enlace externo dice adónde lleva («Ver el código en GitHub ↗», «Abrir fuente ODEPA: …») y se abre en la misma ventana; el MANUAL y las DECISIONES se leen dentro del panel, con el original en GitHub a un clic. Los enlaces internos usan «→» y los externos «↗». Las direcciones anteriores (`/operacion`, `/documentacion`, `/arquitectura`, `/datos-y-codigo`, `/vista-3d`, `?seccion=…`) abren su contenido en la nueva ubicación. El autor se nombra en masculino en el panel y los documentos.
- **Por qué:** un reclutador debe entender el valor del trabajo en el primer paso y poder seguir, volver o saltar a cualquier sección sin perder el tema ni los filtros. La Vista 3D repetía datos que los gráficos planos muestran mejor y no respondía una pregunta propia. Una ventana flotante interrumpía la entrada; el perfil solo es útil si cambia algo del recorrido.
- **Descartado:** reordenar el menú por perfil (el recorrido deja de ser uno solo); abrir los enlaces en pestañas nuevas automáticamente (el visitante decide); cargar GitHub o ODEPA dentro de marcos.
- **Se pierde:** las direcciones de las ventanas anteriores ya no aparecen en el menú (siguen funcionando); la 3D ya no está disponible.

## D-071 · Cuatro temas, con Corporativo por defecto

- **Decisión:** el panel ofrece exactamente cuatro temas: Corporativo (por defecto: fondo claro neutro, texto oscuro y azul de negocio), Vantablack (negro profundo con cian), Blue Light (fondo azul muy claro, paneles blancos, texto oscuro y acentos azules) y Dark Grey (gris carbón; reemplaza a Grafito y toma el cian del proyecto, el mismo que Streamlit da a sus propios controles en la base oscura, en vez del verde anterior). Los enlaces con un nombre retirado abren el tema más cercano (Grafito → Dark Grey; Claro → Corporativo). Streamlit arranca en su base clara, la de Corporativo, así que la primera visita no recarga la página. Cada tema tiene su rampa de calor validada como rampa ordinal contra el color de sus tarjetas; la de Dark Grey se aclaró porque su primer paso se perdía en el gris (1,07:1). En los temas claros, la tinta de referencia (líneas punteadas y bordes de campos) se oscureció de 2,6:1 a 3,6:1 para superar el mínimo de 3:1 de los elementos gráficos. El modelo estrella usa el cian claro en los temas oscuros y el oscuro en los claros. Todos los textos superan 4,5:1 en los cuatro temas.
- **Por qué:** un tema claro por defecto se lee mejor en una primera visita y en una pantalla compartida; dos temas oscuros y dos claros cubren las preferencias sin multiplicar paletas que mantener.
- **Descartado:** un acento verde propio para Dark Grey (chocaba con el cian de los controles nativos, que Streamlit fija por base y no por tema).
- **Se pierde:** Grafito con su verde.

## D-073 · Destinos explícitos, preferencias en cabecera y mapa regional

- **Fecha:** 2026-10-14.
- **Decisión:** por solicitud del autor, separar «Preguntas y resultados SQL» de «Código del proyecto». El recorrido tiene cinco pasos: El proyecto, Dashboard, Preguntas y resultados SQL, Código del proyecto y Arquitectura y operación. Documentación y enlaces queda como referencia. Cada vista de una sección tiene un enlace visible en el menú; las antiguas direcciones siguen redirigiendo al contenido correspondiente.
- **Perfil y tema:** el perfil se elige al entrar. Después, perfil y tema se cambian en una cabecera común, sin repetir el selector inicial en la portada. El perfil adapta la explicación y la vista inicial; no oculta contenido ni modifica los cálculos. Los filtros del dashboard se conservan al cambiar de perfil. Se mantienen los cuatro temas y Corporativo por defecto.
- **Código:** carpetas y archivos cerrados por defecto, con nombres funcionales y código real. SQL, esquemas, configuración, pruebas y workflows se pueden leer dentro del panel. Las preguntas tienen su resultado antes del SQL, que se abre opcionalmente.
- **Diagramas:** se conservan el pipeline animado, la arquitectura por plataforma, el modelo estrella y el ciclo DevOps. Su destino es Arquitectura y operación; no se duplican en el dashboard.
- **Geografía:** el resumen incorpora un mapa 2D de Chile continental, por un canal a la vez, y un ranking con valores visibles. Usa el índice regional existente (100 = promedio del canal). Las regiones sin dato quedan grises. Geometría local simplificada de geoBoundaries / BCN / OCHA, con licencia y metadatos en bi/assets/CHILE_MAP.md; no requiere servicio externo en cada visita.
- **Límite:** esta revisión cambia navegación y presentación, no ingesta, ETL, bases, reglas ni fórmulas. No constituye una auditoría adicional de calidad de los datos.

## D-074 · Ayudas contextuales y detalle replegado

- **Fecha:** 2026-10-14.
- **Decisión:** las explicaciones y respuestas breves viven en el icono ⓘ de cada gráfico, al pasar el mouse o enfocar/tocar el icono. No añaden párrafos visibles. Se calculan con las mismas filas y filtros: variación semanal, precios de los canales elegidos e índice regional. El anillo aclara que cuenta registros, no ventas. «Definiciones y método» queda como ayuda secundaria.
- **Detalle:** tablas de resultados, alertas, calidad, modelo e historial y bloques de código se abren bajo demanda, cerrados por defecto. Los datos, exportaciones y fuentes siguen disponibles. Se conserva la interacción de los gráficos y sus cálculos.


## D-075 · Primero los datos, después implementación y documentación

- **Fecha:** 2026-10-14.
- **Decisión:** el recorrido del menú y los botones anterior/siguiente siguen Dashboard → Arquitectura y operación → Código del proyecto → Preguntas y resultados SQL → El proyecto. Documentación y enlaces permanece como referencia.
- **Por qué:** mostrar primero resultados, después arquitectura y buenas prácticas de implementación. La lectura extensa del proyecto queda al final. Todos los perfiles empiezan en Dashboard y siguen teniendo acceso a todas las secciones.
- **Compatibilidad:** los enlaces anteriores con una vista del proyecto en la raíz se redirigen a esa misma vista; se conservan tema y perfil, sin sustituir el destino solicitado por el nuevo inicio.


## D-076 · KPIs como sección visible después del dashboard

- **Fecha:** 2026-10-14.
- **Decisión:** «KPIs · Qué medimos» es el segundo paso del recorrido. Reúne las ocho medidas existentes, sus tarjetas con definición, fórmula, limitaciones, ejemplos reales y enlaces al resultado y SQL. Los ejemplos están replegados, salvo el indicador solicitado por un enlace desde un gráfico.
- **Sin duplicación:** la vista «Indicadores explicados» deja de pertenecer a El proyecto; los enlaces anteriores abren la misma vista en la nueva sección. El dashboard conserva los gráficos y sus cifras. No se crean nuevos KPIs ni se cambian los cálculos.

## D-077 · Resumen alineado y tres gráficos en una cuadrícula

- **Fecha:** 2026-10-15.
- **Decisión:** tomar de la referencia del autor la jerarquía y alineación: filtros arriba, banda de cifras y calidad, y tres paneles de análisis alineados (variaciones semanales, evolución de precios y mapa regional). No copiar las métricas de recursos humanos ni imponer un tipo de gráfico que no corresponda a los datos.
- **Detalle:** el ranking y la tabla regional quedan en un desplegable cerrado bajo el mapa. Se conservan las ayudas ⓘ, filtros, Top N, selección de producto, canales, exportación y cálculos. La orientación por perfil del dashboard queda en la ayuda del selector Perfil; las demás secciones conservan su contexto.
- **Adaptación:** los paneles se apilan en pantallas estrechas, con altura natural y sin desplazamiento horizontal. No se fuerza que todos los detalles quepan en una pantalla a costa de la lectura. Verificado a 1440 × 900 y 390 × 844.
- **Validación:** 130 pruebas de dashboard y gráficos correctas; sin cambios de ingesta, ETL ni fórmulas.

## D-078 · El dashboard es la portada pública

- **Fecha:** 2026-10-15.
- **Decisión:** la entrada directa sin parámetros abre Dashboard con Corporativo por defecto, sin diálogo obligatorio de perfil. El visitante puede elegir su perfil en la cabecera y navegar a todas las secciones. Los enlaces que piden expresamente otro tema o destino se conservan.
- **Presentación:** reducir la altura de la banda superior y simplificar la leyenda de calidad. Los enlaces de cálculo repetidos dejan de aparecer junto a cada título del resumen; las ayudas ⓘ, Definiciones y método y la sección KPIs conservan el acceso a las explicaciones. Se mantienen las métricas, filtros y tres visualizaciones, sin añadir indicadores de ventas que no existen en este proyecto.

## D-079 · Catálogo compacto de ocho KPIs

- **Fecha:** 2026-10-15.
- **Decisión:** sustituir las tarjetas extensas y la segunda lista de ejemplos por una cuadrícula de ocho tarjetas: cuatro columnas en escritorio, dos en pantallas intermedias y una en móvil. Cada tarjeta presenta un símbolo funcional, un nombre sencillo y una frase breve.
- **Detalle:** cada indicador reúne su definición completa, fórmula, límite, resultado ilustrativo real y enlaces a visualización y consulta dentro de su desplegable. Cerrado por defecto; un enlace con kpi abre el indicador solicitado primero. No se eliminan medidas ni cambian cálculos.
- **Jerarquía:** un solo encabezado de KPIs. El contexto por perfil sigue disponible en la ayuda del selector de perfil, sin repetir un párrafo sobre el catálogo.
- **Verificación visual:** ocho tarjetas visibles a 1440 × 900; sin desbordamiento horizontal a 390 × 844. Los iconos reutilizan el sistema SVG local y las tarjetas usan la paleta del tema activo.

## D-080 · Criterios SMART sin metas inventadas

- **Fecha:** 2026-10-15.
- **Decisión:** cada detalle de KPI incluye una ficha SMART: específico, medible, alcanzable, relevante y temporal. Se conservan la cuadrícula compacta y los detalles cerrados por defecto.
- **Alcance:** se documentan las unidades, utilidad y ventanas reales de cada cálculo. La capacidad de calcular una medida no demuestra que una meta de negocio sea alcanzable. Como no se han acordado metas y fechas objetivo, ambas se indican pendientes; la frecuencia de medición no se presenta como un plazo de cumplimiento. No se afirma que los ocho indicadores sean objetivos SMART completos.

## D-081 · Iconos sin fondo y un único panel de lectura KPI

- **Fecha:** 2026-10-15.
- **Decisión:** por solicitud del autor, los ocho KPIs se seleccionan mediante botones de icono transparentes, con nombre, ayuda y subrayado para la selección. No son tarjetas ni despliegan texto entre los iconos. El orden permanece estable al cambiar de indicador.
- **Lectura:** un solo espacio a todo el ancho debajo del selector cambia con el KPI activo. Tres pestañas separan Qué mide, Criterios SMART y Ejemplo y consulta. Se conservan definición, fórmula, límites, ejemplos reales y enlaces internos; ningún cálculo cambia.
- **Enlaces:** kpi en la dirección selecciona directamente el indicador, y cada clic actualiza ese parámetro. Sin parámetro, se conserva la selección de la visita o se muestra Brecha de precio.
- **Accesibilidad y adaptación:** controles nativos con teclado, foco visible, ayuda y nombre textual. Se respeta la reducción de movimiento. Verificación visual a 1440 × 1000 y sin desbordamiento horizontal a 390 × 844.

## D-082 · Relieve vectorial discreto para los iconos KPI

- **Fecha:** 2026-10-15.
- **Decisión:** inspirarse en la claridad del selector de productos mostrado por el autor: símbolos aislados sin tarjeta, tipografía de sistema más ligera y espacio entre elementos. Los SVG locales tienen un relieve 2,5D sencillo mediante capas, gradiente y sombra de apoyo transparente; no son modelos 3D interactivos.
- **Continuidad:** se conserva el selector nativo accesible, sus nombres y ayudas, el indicador activo y el panel inferior compartido. La paleta procede del tema actual y se respeta la reducción de movimiento. No se incorporan imágenes, fuentes ni servicios externos, ni cambia ningún cálculo.

## D-083 · Contornos KPI más nítidos

- **Fecha:** 2026-10-15.
- **Decisión:** retirar el gradiente metálico alternado que hacía los símbolos visualmente borrosos. Usar un trazo frontal uniforme, una profundidad de un píxel aproximado y una sombra de apoyo mucho más tenue. Se conserva la tipografía ligera, la paleta activa y toda la interacción del selector.

## D-084 · Cabecera común con acceso directo a gráficos

- **Fecha:** 2026-10-15.
- **Decisión:** añadir en todas las secciones una navegación horizontal ligera, inspirada en la referencia del autor. Orden: Dashboard, Esta semana, Brechas, Regiones, Alertas, Histórico, KPIs, Pipeline, Modelo y DevOps. La vista activa queda indicada con color y subrayado. GreenOcean vuelve al resumen del Dashboard.
- **Continuidad:** el lateral conserva el recorrido completo, código y referencias. Perfil y tema siguen accesibles bajo la fila de enlaces, con el contexto de la sección. Se conserva tema y perfil al seguir cada enlace; todos los destinos permanecen dentro del proyecto y en la misma ventana.
- **Estilo:** tipografía de sistema ligera compartida con los enlaces laterales, sin tarjetas ni iconos decorativos en la cabecera. Los enlaces se redistribuyen en varias líneas en móvil, sin forzar desplazamiento horizontal.

## D-085 · Marca independiente en la esquina izquierda

- **Fecha:** 2026-10-15.
- **Decisión:** retirar GreenOcean de los enlaces de gráficos y mostrarlo como marca mediante el logo nativo de Streamlit, arriba a la izquierda. Green aparece en verde y Ocean en azul. Se usan versiones claras u oscuras según el fondo del lateral y del encabezado cuando el lateral está cerrado. SVG local transparente; no requiere fuentes ni imágenes externas. La navegación conserva todos sus destinos.

## D-086 · Cabecera más cerca del borde superior

- **Fecha:** 2026-10-15.
- **Decisión:** eliminar del flujo los bloques invisibles que solo inyectan CSS, reducir el margen superior del contenido y el relleno vertical de la navegación. Mantener espacio para el logo nativo cuando el lateral está cerrado. No se cambian los destinos ni el orden de los enlaces.

## D-087 · Clics de cabecera, recarga al resumen y legibilidad

- **Fecha:** 2026-10-15.
- **Corrección:** el contenedor transparente de la barra nativa de Streamlit interceptaba los clics de la navegación compacta. La capa y sus envoltorios dejan pasar los clics; sus botones y enlaces reales conservan interacción.
- **Recarga:** una recarga del documento vuelve al resumen principal del Dashboard, conservando tema y perfil. La comprobación ocurre una sola vez por documento y distingue una recarga de un clic normal; navegar a una vista continúa funcionando. La selección de filtros sin recargar no se reinicia.
- **Legibilidad:** títulos de paneles pueden pasar a otra línea; etiquetas largas del comparador de canales se separan en líneas con altura suficiente. Se corrige la compensación de margen de Markdown que hacía que la leyenda de alcance del resumen quedase debajo de los paneles.
- **Validación:** clics reales desde la cabecera y recargas desde Brechas y Regiones al resumen. Pruebas de dashboard y gráficos: 132 correctas. Se conserva la estructura y las fórmulas de cada vista; el ejemplo financiero guía la organización visual, no aporta indicadores ni datos al proyecto.
- **Histórico:** los gráficos históricos adicionales quedan replegados por defecto para dar prioridad a los calendarios y cifras principales. El eje de índices conserva dos decimales: se evita mostrar distintas fracciones repetidas como «1» por redondeo a enteros. Es un cambio de formato, no de cálculo.

## D-088 · Ficha KPI en tabla a todo el ancho

- **Fecha:** 2026-10-15.
- **Decisión:** el panel inferior del KPI activo presenta una tabla visible con dos columnas, Aspecto y Explicación. Reúne indicador, pregunta, significado, utilidad, medida, fórmula, periodo y límites. Cambiar de icono sustituye la ficha; no crea tarjetas adicionales ni listas de texto dispersas.
- **Detalle:** SMART usa la misma tabla para sus cinco criterios; el ejemplo real se presenta paso a paso en tabla con su enlace a la consulta canónica. Se mantienen las tres pestañas y todos los enlaces internos.
- **Espacio:** selector en una fila de ocho iconos en escritorio, cuatro columnas en pantallas intermedias y dos en móvil. La tabla ajusta líneas a su ancho en lugar de requerir desplazamiento horizontal. La ficha solicitada por el usuario queda visible por defecto, como excepción expresa a la regla anterior de tablas replegadas.
- **Validación:** 112 pruebas del dashboard correctas; comprobación visual de cambio de indicador y tabla.

## D-089 · Recorrido único, Dashboard de doble ranking y documentación independiente

- **Fecha:** 2026-10-15.
- **Decisión:** retirar la segmentación por perfil y mantener un único recorrido público. Las direcciones antiguas con perfil siguen funcionando, pero el parámetro se elimina y no cambia el contenido ni el orden de las vistas.
- **Dashboard:** los rankings de alzas y bajas se muestran simultáneamente, con Top N aplicado a cada dirección. La exportación y la tabla reúnen ambas selecciones. Los ceros y valores no finitos no se presentan como alzas ni bajas. Se conserva la selección de producto desde cualquier barra, el histórico de precios, el mapa regional y el anillo de calidad. El estado de carga dispone de espacio propio antes de los filtros.
- **Apariencia:** un icono de sol o luna abre las cuatro paletas, con nombres explícitos y acceso por teclado. Se retira el desplegable permanente de tema; Corporativo continúa siendo la paleta predeterminada.
- **Navegación:** Volver recupera el destino anterior y la selección de datos. El historial se limita al origen del proyecto, se conserva en la sesión del navegador y restaura únicamente un conjunto validado de filtros. Una recarga sigue abriendo el resumen principal. Los enlaces sin modificadores se abren en la misma ventana; los clics deliberados con Ctrl o Cmd conservan el comportamiento del navegador. Las ejecuciones ya pueden consultarse en Arquitectura y operación; no se añade una segunda integración con GitHub.
- **Contenido:** El proyecto describe el trabajo desarrollado, sus destinatarios operativos, trazabilidad y capacidad de reutilización sin atribuciones ambiguas. Se distingue entre componentes reutilizables y adaptaciones necesarias para fuentes o dominios nuevos; no se presenta la implementación ODEPA como plantilla de sustitución automática.
- **Documentación:** manual, registro de decisiones y glosario tienen una sección propia, sin tarjetas de presentación. Enlaces reúne repositorio, registros públicos y fuentes externas. La descripción de coste y capacidad permanece en Arquitectura y operación. Se conservan las direcciones anteriores y el registro histórico de decisiones.
- **Validación:** 326 pruebas del proyecto correctas. Comprobación visual del retorno Dashboard → KPIs → Volver con Frutas seleccionado, de ambos rankings y del menú de apariencia.

## D-090 · KPIs como recorrido horizontal de tres estaciones

- **Fecha:** 2026-10-16.
- **Problema:** la vista KPIs era un registro de ocho filas con texto denso, un selector y un desplegable debajo; obligaba a desplazarse y no destacaba ningún resultado.
- **Decisión:** un solo módulo con todo el recorrido a la vista, sin botón «Continuar» ni pasos ocultos. Cabecera de una línea (KPIs, frase, actualización y estado). Debajo, la pregunta de negocio en un desplegable y una línea luminosa que va de «Inicio» a «Detalle técnico» pasando por tres nodos numerados a distinta altura. Cada nodo se apoya en el borde superior de su tarjeta: **1 · Resultado** (la cifra grande, su significado, el estado de la carga, la semana y la anterior), **2 · Contexto** (pestañas Alcance, Lógica y Límites) y **3 · Consulta** (nombre, botón «Desplegar SQL» y enlace al catálogo). El tramo hacia la parte técnica es discontinuo.
- **Geometría:** columnas de 30 %, 36 % y 28 % con separaciones de 3 %; los nodos se dibujan en la misma capa que la línea, en el centro de cada columna, para que siempre coincidan.
- **Referencia visual:** una maqueta de recorrido guiado con línea brillante y tarjetas escalonadas. Se descartaron antes una versión de tarjetas con un paso a paso pequeño y otra de hoja de ruta con pines, porque no se leían como un camino.
- **Sin scroll:** en 1440 × 900 el módulo completo cabe en pantalla.
- **SQL:** la consulta se abre en una capa superpuesta al pulsar el botón y se lee del mismo archivo que el catálogo (`read_catalog_sql`); la página no muestra SQL por defecto, de modo que el catálogo sigue siendo su único lugar visible (D-061).
- **Pantallas pequeñas:** las tres tarjetas se apilan en el mismo orden con su número en el título; la línea se oculta.
- **Se retira:** la tabla de ocho filas y el desplegable de fórmula y SMART en esta vista. Los resultados por indicador se consultan cambiando la pregunta; SMART sigue en `build_kpi_smart_html` para la ficha anterior.

## D-091 · Mapa de Chile grande, con el nombre sobre cada región, junto a las familias

- **Fecha:** 2026-10-16.
- **Problema:** el mapa ocupaba todo el ancho pero se dibujaba pequeño en el centro, con márgenes vacíos; las regiones eran demasiado estrechas para hacer clic con seguridad y sus nombres estaban en una columna aparte, unidos por líneas de referencia difíciles de seguir.
- **Decisión:** el mapa ocupa la columna izquierda y las familias (galería y movimiento) la derecha, de modo que la vista principal se lee de una vez en 1440 × 900. Cada región lleva encima su nombre y su porcentaje; región y nombre forman un solo enlace. No hay líneas de referencia.
- **Mapa esquemático:** cada región conserva su contorno y su orden de norte a sur. La latitud se reparte por región (78 % de la altura a partes iguales, el resto según su extensión real) y cada latitud recibe su propia escala horizontal, de modo que las regiones del norte se ensanchan. Ambas transformaciones dependen solo de la latitud: los bordes compartidos siguen compartidos y ninguna región se superpone a otra. Los contornos se suavizan y los islotes de menos de 6 px² no se dibujan. El mapa lo declara como esquemático; no es una referencia de límites.
- **Precisión:** una prueba comprueba que el nombre de cada una de las 16 regiones queda dentro del contorno de su propia región, en orden de norte a sur y con al menos 20 px entre nombres; otra, que cada región dispone de al menos 24 px de alto.
- **Clic:** al hacer clic en una región se abre un único paso: elegir la familia (o todas), con su número de precios. Un clic aplica región y familia. La búsqueda de un producto concreto queda como opción debajo. Se retiran el selector segmentado y los botones «Aplicar».

## D-092 · Dashboard en una pantalla: mapa real, movimiento por familia y productos

- **Fecha:** 2026-10-16.
- **Sustituye:** el mapa esquemático y el diálogo de familias de D-091. El mapa esquemático hacía perder la forma de Chile; la galería de familias y el diálogo repartían la lectura en varios pasos.
- **Decisión:** la vista principal sigue la maqueta aprobada y se lee sin desplazarse (verificada en 1920 × 1080 y 1440 × 900). Cabecera: título y tres resúmenes (familias que subieron y bajaron, regiones por dirección dominante, región seleccionada). Columna izquierda: mapa de Chile en proporción real. Columna derecha: movimiento por familia y, debajo, los productos de la familia seleccionada.
- **Mapa:** proyección equirectangular corregida por el coseno de la latitud media. Cada región tiene una fila con su nombre y su porcentaje en una etiqueta de color; una línea recta une un punto situado dentro de la región con su fila. Las filas siguen el orden norte–sur de esos puntos, de modo que las líneas no se cruzan. Pruebas: el punto de cada una de las 16 líneas está dentro del contorno de su región, ningún par de líneas se cruza y la proporción alto/ancho del país es la real.
- **Clics:** región (forma o fila) → selecciona la región; las familias y la tabla se recalculan para ella. Un segundo clic en la región seleccionada vuelve a todo Chile. Familia → la tabla muestra sus productos. La tabla filtra por canal y ordena por mayor cambio, subidas, bajadas o nombre; «Ver histórico» y la flecha de cada fila abren el histórico del producto.
- **Regiones ↑ / ↓:** para el mismo producto, variedad, calidad, unidad y canal, número de regiones donde subió y donde bajó entre las dos semanas.
- **Se conserva:** «Explorar productos y tablas por familia», debajo de la vista principal. **Se retiran:** la galería de familias con imágenes, el diálogo de región y sus funciones auxiliares.

## D-093 · Un buscador en el panel de productos; se retira «Explorar productos y tablas por familia»

- **Fecha:** 2026-10-16.
- **Problema:** el desplegable final repetía lo que ya hace el panel «Productos · {familia}»: tablas por familia, orden por cambio, subidas y bajadas, y acceso al histórico.
- **Decisión:** se retiran el desplegable y su control de filas (Top N). El panel gana un buscador por nombre en la misma fila que Canal, Orden y «Ver histórico». La búsqueda no distingue mayúsculas ni acentos y busca al inicio de cualquier palabra del producto o su variedad: «lech» encuentra «Lechuga», «esp» encuentra «Lechuga · Española» y «aji» encuentra «Ají»; varias palabras deben coincidir todas. El encabezado indica cuántos precios quedan («26 de 291 precios») y la tabla lo dice cuando no hay coincidencias.
- **Se conserva lo que solo estaba abajo:** el orden «Inusuales» (alertas nacionales, el cambio más inusual primero) pasa al selector Orden, solo con todo Chile; la nota de cobertura y los enlaces a Calidad y Metodología quedan en una línea bajo la tabla.

## D-094 · «Histórico y estacionalidad» pasa a «Contexto del precio»

- **Fecha:** 2026-10-16.
- **Problema:** el dashboard se usa para decidir semana a semana, pero la página mostraba cuatro años de precio con áreas y no respondía si el precio de esta semana es normal.
- **Decisión:** una sola pantalla (1920 × 1080, sin desplazamiento) que responde tres preguntas: ¿es normal el precio de esta semana?, ¿dónde conviene comprar? y ¿qué suele pasar en las próximas semanas? Arriba, migas «Resumen › familia › producto», «Volver al resumen», el título, una frase de respuesta calculada y los selectores familia, producto y calidad · unidad. A la izquierda, las últimas 52 semanas frente a lo habitual y el patrón de temporada; a la derecha, precio de esta semana, brecha entre canales y meses siguientes.
- **«Habitual»:** rango entre el percentil 25 y el 75 del precio de la misma semana ISO en los años anteriores disponibles; el año en curso nunca entra en su propia referencia. Sobre el P75 es «sobre lo habitual»; bajo el P25, «bajo lo habitual»; entre ambos, «dentro». Con menos de dos años anteriores para esa semana se muestra «Sin historia suficiente».
- **Brecha:** (precio supermercado / precio feria − 1) × 100, solo en semanas con ambos precios. Se compara con la mediana de la brecha del mismo mes en años anteriores.
- **Patrón de temporada:** índice estacional K4 (100 = promedio del año) por mes; primero el promedio de cada mes en cada año y luego el de los años, sin el año en curso. «Qué suele pasar» es el cambio de ese índice de feria del mes actual a los dos siguientes, presentado como patrón, no como pronóstico.
- **Datos:** semanas sin precio quedan como hueco; no se interpola. Precios nominales. Cálculos en `bi/price_context.py` (funciones puras, con pruebas) y cacheados por versión de la base, de modo que cada carga semanal los renueva.
- **Navegación:** «Histórico» sale de las pestañas superiores y queda en 01 · Dashboard como «Contexto del precio». El panel de productos del Resumen abre la página con el producto elegido ya seleccionado; las direcciones antiguas con la vista «Histórico y estacionalidad» siguen funcionando. Se retiran el gráfico de áreas, «Comparar meses y años por canal», «Detalle semanal del índice estacional» y «Cambiar el producto del análisis»; la serie completa y los datos (con el índice semanal) se abren en diálogos.

## D-095 · Dimensión de fechas dim_date

- **Fecha:** 2026-10-16.
- **Decisión:** nueva dimensión `dim_date` (week_start, iso_year, iso_week, month, month_name, year, season), una fila por semana desde la primera hasta la última semana de `weekly_price`, sin huecos: las semanas sin precios también existen. La estación sigue el hemisferio sur según el mes de week_start (verano = dic–feb, otoño = mar–may, invierno = jun–ago, primavera = sep–nov). El año ISO puede diferir del calendario: 2024-12-30 es la semana 1 de 2025.
- **Carga:** cada ejecución del ETL reconstruye `dim_date` dentro de la misma transacción, antes de insertar los precios.
- **Relación:** `weekly_price.week_start` referencia `dim_date.week_start` con una clave foránea real. SQLite no permite añadirla a una tabla existente, así que `weekly_price` se recrea con la restricción y sus filas se copian sin cambios; es seguro porque el ETL ya reconstruye esa tabla en cada carga. La base actual se migró así: mismas 811.578 filas, mismas sumas de precio y observaciones, mismas marcas, `etl_run` sin cambios y ninguna violación de clave foránea.
- **Uso:** «Contexto del precio» toma la semana ISO y el mes de `dim_date` para el rango habitual, la brecha habitual y el patrón por mes. El mes del patrón pasa a ser el de week_start (antes, el del jueves de la semana).
- **Pruebas:** semanas consecutivas sin huecos, semana ISO en los cambios de año, estación en los meses límite, migración de una base antigua e integridad `weekly_price → dim_date` en la base real.

## D-096 · Navegación única por menú lateral, sin pestañas

- **Fecha:** 2026-10-16.
- **Decisión:** se retira la barra de pestañas superior (Dashboard, Histórico, Pipeline, Modelo, DevOps); el menú lateral es la única navegación. Arriba de cada página: la ruta («Arquitectura y operación › Modelo de datos»), el botón «Volver» y el selector de tema, sin excepción para el Resumen (antes tenía su propia cabecera sin ruta ni Volver).
- **Menú lateral:** todas las secciones y subpáginas van desplegadas todo el tiempo, sin expanders ni flechas. «Recorrido», «Referencias» y los títulos numerados de sección («01 · Dashboard», «02 · Arquitectura y operación») no son enlaces; solo sus subpáginas lo son. Estructura: 01 · Dashboard (Resumen de la semana, Contexto del precio, Datos), 02 · Arquitectura y operación (Pipeline y arquitectura, Modelo de datos, DevOps y seguridad, Calidad y trazabilidad, Ejecuciones), 03 · Código del proyecto, 04 · Preguntas y resultados SQL, 05 · El proyecto (Portada, Definición del proyecto, Reglas de calidad); Referencias: Documentación (Documentación general, Manual, Glosario), Enlaces. La página actual se marca con fondo resaltado.
- **Alerta de precio:** botón fijo al final del menú, separado de la navegación, con el conteo real de alertas de la semana; debajo, la nota de fuente. Al pulsarlo abre el mismo diálogo que antes, ahora disponible desde cualquier página, no solo el Resumen.
- **Se retira:** `build_graph_navigation_html`, `GRAPH_NAVIGATION`, el `home_header` especial del Resumen y el `home_mockup.sidebar` propio del Resumen con su imagen de alerta animada.
- **Validación:** 401 pruebas. Revisión visual en Corporativo y Vantablack, en 1920 × 1080 y en móvil (390 px), con el menú plegado automáticamente en pantallas angostas.

## D-097 · Modelo de datos en una sola pantalla, con clic en lugar de hover

- **Fecha:** 2026-10-16.
- **Decisión:** la página se lee entera en 1920 × 1080, sin desplazamiento. Cabecera: título, una frase y tres indicadores reales a la derecha (filas de weekly_price; cargas en etl_run y filas en rejection; fecha y estado de la última carga). Columna izquierda: la frase «1 fila de weekly_price = …» y el diagrama estrella. Columna derecha: «Detalle de la tabla seleccionada» (nombre, rol, filas, descripción y una consulta SQL real) y «Tablas de datos.db», siempre visible, sin desplegable.
- **dim_date como dimensión real:** sustituye la antigua caja punteada «Semana» (D-095). Queda en la punta superior de la estrella, con sus siete columnas reales. `dim_date` se agrega a `project.TABLE_NAMES` y `DIMENSION_TABLES`, y a las definiciones del modelo en `docs/PROYECTO.md`.
- **Posiciones calculadas, no fijas:** `star_model.compute_layout` ubica las cinco tarjetas a partir del número real de columnas de cada tabla, de modo que el diagrama nunca se superpone aunque una tabla gane o pierda columnas. Una prueba lo verifica agregando columnas de más a `dim_date`.
- **Auditoría de cargas:** el grupo `etl_run → rejection` queda separado de la estrella, abajo a la derecha del diagrama, con una flecha y `run_id (FK)`.
- **Selección por clic, no por mouse encima:** la tabla elegida se guarda en `st.session_state` (un `st.radio` siempre desplegado) y actualiza la tarjeta de detalle; en el diagrama, la tarjeta elegida se resalta con un trazo más grueso y resplandor. Reemplaza el sistema anterior basado en CSS `:hover`/`:focus`, que no funcionaba igual en celulares.
- **Se retira:** el envoltorio de zoom (controles «+ − ⟲») y los paneles de explicación fijados por CSS bajo el diagrama; `bi/zoom.py` sigue en uso en Pipeline y DevOps. `list_star_panels` y `show_star_schema_tab` se eliminan.
- **Validación:** 404 pruebas, incluida una de no superposición del layout y otra del clic que cambia la tabla seleccionada. Revisión visual en Corporativo y Vantablack, en 1920 × 1080 y 1440 × 900, sin desplazamiento en ninguno.

## D-098 · Contexto del precio: estado final

- **Fecha:** 2026-10-16.
- **Cabecera:** se retira la barra genérica «ruta · Volver» en esta página; solo queda su propia ruta «Resumen › familia › producto» con «Volver al resumen». El selector de tema sigue disponible, arriba a la derecha.
- **Suavizado ±1 semana ISO:** lo habitual (P25–P75) usa ahora la semana ISO objetivo y sus dos vecinas (hasta 3 semanas por año anterior), en vez de una sola semana. En los bordes del calendario (semana 1, última semana del año) la ventana tiene 2 semanas en lugar de 3, sin adivinar el número de semanas de otro año. El mismo criterio se aplica a la brecha entre canales.
- **Gráfico:** sin etiquetas de texto sobre la línea; el estado ya está en la frase y en «Precio esta semana».
- **Frase de resumen:** el estado de feria se colorea en azul `#2563C9` y el de supermercado en naranja `#D9622B`, iguales a las líneas del gráfico. La brecha entre canales solo se menciona cuando queda fuera de su propio rango habitual (mismo criterio P25–P75); si está dentro, no se menciona.
- **Se retiran:** la tarjeta «¿Dónde conviene comprar?» con su mini gráfico, y «Patrón de temporada» (barras + selector Feria/Supermercado). `brecha_habitual` (mediana) y `describe_gap_comparison` (tolerancia) se reemplazan por `brecha_rango_habitual`, que reutiliza `estado_precio`.
- **«Qué suele pasar en las próximas semanas»:** se conserva y gana una franja compacta de 3 meses × 2 canales (feria y supermercado, antes solo feria), con flecha y % de cambio frente al mes actual.
- **Nueva tarjeta «Otros productos de {familia} fuera de lo habitual»:** productos de la misma familia cuyo precio de esta semana, en cualquier canal, queda fuera de su propio P25–P75 (misma ventana). Hasta 6 filas, ordenadas por qué tan lejos están del límite; un clic en un producto recarga esta misma página con ese producto. La tabla tiene su propio scroll acotado (230 px) para que la página quepa en 1920 × 1080 sin desplazamiento, cualquiera sea el número de filas.
- **Subtítulos largos → ⓘ:** se reemplazan por el ícono de ayuda ya usado en el resto del proyecto (`build_hint_icon`), con el texto completo como tooltip.
- **Validación:** 406 pruebas. Revisión visual en Corporativo y Vantablack, en 1920 × 1080, sin desplazamiento.

## D-099 · El cambio de tema ya no regresa al Resumen

- **Fecha:** 2026-10-16.
- **Problema:** cambiar de paleta (por ejemplo a Vantablack) dispara una recarga del navegador para sincronizar el modo base de los widgets nativos de Streamlit. Un script separado, pensado para detectar cuando el visitante presiona recargar en el navegador, interpretaba esa misma recarga como un refresco real y enviaba al Resumen, perdiendo la página en la que estaba.
- **Decisión:** antes de recargar por el cambio de tema, se guarda una marca en `sessionStorage` (`greenoceanThemeReload`). El script que decide si volver al Resumen la revisa primero: si está presente, la borra y no hace nada más, de modo que la recarga deja al visitante exactamente donde estaba, con el tema nuevo aplicado.

## D-100 · El estilo de la ventana de alertas se carga en todas las páginas

- **Fecha:** 2026-10-16.
- **Problema:** desde D-096 el botón «Alerta de precio» vive en el pie del menú lateral, visible en cualquier página. Su CSS (formas, leyenda, colores) seguía viviendo en `home_mockup.style()`, que solo se inyecta al dibujar el Resumen. Al abrir la ventana desde otra página (por ejemplo Contexto del precio o Modelo de datos), se veía sin estilo: botones planos en una fila, sin las formas de color ni el espaciado de la leyenda.
- **Decisión:** `show_sidebar_footer()` inyecta `home_mockup.style(...)` de forma incondicional, en cualquier página, antes de dibujar el botón. Las reglas son inertes fuera del Dashboard (dependen de clases que solo existen en su propio marcado), así que no afectan a las demás páginas.
- **Validación:** 407 pruebas; una nueva comprueba que el CSS de la ventana está presente y que la ventana se abre con el mismo marcado desde una página distinta al Resumen. Revisión visual en Corporativo y Vantablack, abierta desde Contexto del precio y desde Modelo de datos.

## D-101 · El menú lateral se lee como un árbol de archivos

- **Fecha:** 2026-10-16.
- **Decisión:** cada grupo con subpáginas («01 · Dashboard», «02 · Arquitectura y operación», «05 · El proyecto», «Documentación») lleva ahora su propio ícono, el mismo que ya tenía asignado en `WINDOW_ICONS`, al mismo tamaño y en la misma posición que los íconos de página. Sus páginas quedan unidas por una guía vertical fina, como las ramas de un árbol de archivos (VS Code). Las entradas sueltas sin subpáginas (03 · Código del proyecto, 04 · Preguntas y resultados SQL) comparten el mismo margen e indentación que los grupos, en vez de un margen distinto como antes.
- No cambia el comportamiento: todo sigue desplegado todo el tiempo (D-096); esto es una limpieza puramente visual de alineación e iconografía.
- **Validación:** 407 pruebas sin cambios. Revisión visual en Corporativo y Vantablack.

## D-102 · El menú lateral pliega y despliega de verdad, como VS Code

- **Fecha:** 2026-10-16.
- **Decisión:** cada carpeta del menú (grupo con subpáginas) tiene ahora una flecha real (▾ desplegada, ▸ plegada) que la pliega al hacer clic, igual que el panel Explorer de VS Code. Por defecto todas empiezan desplegadas, cumpliendo la regla original de D-096; plegar una es una acción explícita del visitante, no el estado inicial.
- **La carpeta de la página actual no se puede plegar:** mientras se está viendo una página de un grupo, su flecha queda deshabilitada y el grupo permanece abierto, para no esconder nunca la página en pantalla. Al salir de ese grupo, su estado plegado o desplegado anterior se respeta.
- **Implementación:** el estado de cada grupo vive en `st.session_state` (`nav_open_<ruta>`), one `st.button` con el ícono de flecha hace de fila de carpeta en lugar del texto estático anterior (D-101); sus páginas se omiten del todo cuando el grupo está plegado.
- **Validación:** 409 pruebas; dos nuevas comprueban que un clic pliega y despliega un grupo sin afectar a los demás, y que el grupo de la página actual no se puede plegar.

## D-103 · Pastillas de tecnología real en cada paso del pipeline

- **Fecha:** 2026-10-17.
- **Decisión:** el diagrama del pipeline («Pipeline y arquitectura», diagrama horizontal y su versión angosta) gana, bajo cada paso que lo necesita, de 1 a 3 pastillas con la tecnología realmente usada: logo local cuando existe uno (Python, SQLite, Streamlit, GitHub, ya en `bi/assets/logos/`) o una pastilla de texto cuando no (HTTPS, CSV, pandas, requests, Markdown, SQL) en vez de inventar un logo. Sin red, sin CDN, sin cambiar el layout, los colores ni la estructura del diagrama aprobado.
- **Una sola fuente:** `PIPELINE_STACK` (nombre del paso → lista de tecnologías) y `TECH` (tecnología → etiqueta y logo), ambos en `bi/architecture.py`, con las mismas claves que ya usa `TOOLTIPS`.
- **Sin redundancia:** `visible_stack()` quita de la fila cualquier tecnología cuyo logo ya es el ícono del propio nodo (por ejemplo, «SQLite · raw.db» no repite el logo de SQLite que ya tiene). Cuando no queda nada nuevo que mostrar, el paso conserva su texto original sin cambios.
- **Auditoría:** cada tecnología listada corresponde a una dependencia real (`requirements.txt`) o a una llamada real del código (`requests.get` en `agent/agent.py`, `import pandas as pd` en `etl/etl.py`, `sqlite3.connect` en `etl/etl.py` y `bi/queries.py`, `gh issue create` en `.github/workflows/semanal.yml`); no se afirma ninguna «API REST» donde el código solo descarga CSV por HTTPS.
- **Validación:** 414 pruebas, 4 nuevas (`test_d103_*`) verifican que cada id de `PIPELINE_STACK` es una dependencia real, que `visible_stack()` evita la redundancia y que las pastillas nunca generan una imagen rota ni una referencia externa.

## D-103b · El cilindro tradicional en vez del logo de marca de SQLite

- **Fecha:** 2026-10-17.
- **Decisión:** los nodos «SQLite · raw.db», «SQLite · datos.db» y «Consultas SQL» dibujan el cilindro tradicional de base de datos (`draw_database_icon`, ya existente en el módulo) en vez del logo de marca de SQLite. El título de cada nodo ya dice «SQLite» en palabras; el cilindro se lee más claro que la tipografía del logo a ese tamaño.
- Se retiran de `PIPELINE_STACK` las entradas redundantes `"SQLite · raw.db": ["sqlite"]` y `"SQLite · datos.db": ["sqlite"]` (el título ya lo dice) y `"sqlite"` de la lista de «Consultas SQL» (queda solo `["sql"]`).
- **Validación:** 414 pruebas; se ajustan las que verificaban el logo de marca de SQLite para confirmar en cambio que ya no aparece en el diagrama del pipeline.

## D-104 · Dirección y lectura explícitas en «Arquitectura por plataforma»

- **Fecha:** 2026-10-17.
- **Decisión:** el diagrama «Arquitectura por plataforma» (`build_devops_svg`) gana seis mejoras de lectura, sin cambiar su estructura, colores, textos ni datos:
  1. Cada conexión dibuja una punta de flecha con la dirección real del flujo; «checkout · commit» (Job semanal.yml ↔ Repositorio) y «cache» (Job semanal.yml ↔ Caché de Actions) llevan punta en ambos extremos porque el flujo real va en los dos sentidos.
  2. «Permisos del job» gana una segunda línea («⤷ del Job semanal.yml») en vez de una línea nueva que cruzara otras tarjetas: queda clara la relación sin alargar el diagrama.
  3. Una leyenda pequeña («● = componente activo») se dibuja en el espacio libre entre GitHub y las plataformas de abajo.
  4. Los controles de zoom de este diagrama, únicamente (`.zoom-frame.diagram-devops`), se mueven a la esquina superior derecha —vacía en este diagrama— para que no tapen «Secretos».
  5. Los seis pasos del flujo semanal automático (Datos abiertos → Job semanal.yml → Repositorio → Pruebas CI → App Streamlit → Visitantes) llevan un número de 1 a 6 en su propio ícono.
  6. «Tu computador» dibuja un borde punteado y su nombre en tono más apagado, con la leyenda «· solo en desarrollo»: nunca corre en producción.
- **Alcance:** todo el cambio vive en `bi/architecture.py`; `bi/zoom.py` gana una regla CSS nueva, aplicable solo a la clase `diagram-devops` (no afecta el zoom de ningún otro diagrama).
- **Validación:** 414 pruebas existentes siguen pasando sin cambios; se verifica a mano que las puntas de flecha, la leyenda y el borde punteado no invaden ningún texto existente.

## D-105 · «El proyecto» y «Documentación» se fusionan en una sola vista

- **Fecha:** 2026-10-17.
- **Decisión:** las dos secciones del menú lateral «El proyecto» (Descripción general, Alcance del proyecto, Reglas de calidad) y «Documentación» (General, Manual, Glosario) —seis páginas en total— se fusionan en una sola entrada, «Documentación», que abre directo (sin carpeta que desplegar) a una única pantalla tipo dashboard.
- **Contenido de la pantalla:** qué resuelve el proyecto y para quién (del mismo texto breve que ya usaba la portada), alcance y límites, las reglas de calidad (resumen y orden, sin repetir la cifra real que ya vive en «Reglas de calidad»), cómo opera cada semana y qué hacer si algo falla, los límites conocidos y el tamaño del glosario. Cada tarjeta enlaza al documento completo solo si hace falta profundizar.
- **Lo que no se repite:** los documentos completos (manual, glosario, reglas con su detalle y evidencia, PRD, SAD) no se reescriben aquí; siguen existiendo como páginas propias, alcanzables por los enlaces de cada tarjeta, y el código y los documentos técnicos completos quedan a un clic en GitHub.
- **Por qué:** un BI o un BA necesita leer esto en segundos, no navegar seis páginas; quien quiera el documento completo ya sabe que vive en el código del repositorio.
- **Validación:** 414 pruebas (el único fallo, `test_every_decision_of_the_register_is_listed`, es previo a este cambio y no está relacionado); se ajusta `test_d096_sidebar_is_a_flat_explorer_with_every_section_closed_by_default` para reflejar que «Documentación» ahora es un enlace directo, no una carpeta.

## D-106 · «Código» se fusiona con «GitHub»; «Documentación» gana tres vistas por perfil

- **Fecha:** 2026-10-17.
- **Decisión:** la sección del menú «Código» (un explorador de archivos dentro del panel) se retira; su único contenido real —ver el código— ya estaba en «Enlaces», que se renombra a **GitHub** porque ahí vive todo lo real del proyecto: código, ejecuciones, informes y documentos completos (se agrega el grupo «Documentos», antes no visible en esta página). Nadie necesita leer archivos fuente dentro del panel cuando el repositorio real, con cada commit, está a un enlace.
- **«Documentación» se rediseña** (reemplaza el contenido de D-105): en vez de seis tarjetas genéricas, muestra tres tarjetas grandes, una por perfil de lector —**BI**, **BA**, **IT**— cada una como una página de resumen: BI ve los ocho indicadores y el alcance de los datos; BA ve misión, visión, objetivo y alcance en las palabras del marco de negocio; IT ve las decisiones de ingeniería clave y la operación semanal. Ninguna tarjeta muestra SQL ni código: ambos ya están completos en GitHub.
- **Indentación corregida:** «GitHub», igual que «Documentación», ahora es un destino directo sin hijos que desplegar, así que no hay fila hija que alinear ni desalinear.
- **Corrección de datos:** el enlace «DECISIONES» en `project.PROJECT_LINKS` apuntaba a una página interna («Decisiones») que nunca existió como ventana propia; se retira ese campo `page`, quedando como un enlace externo simple a GitHub.
- **Validación:** 414 pruebas (el único fallo, `test_every_decision_of_the_register_is_listed`, es previo y no está relacionado); se ajustan `test_d096_sidebar_is_a_flat_explorer_with_every_section_closed_by_default` y `test_code_sql_and_links_folders_reveal_real_destinations_without_tooltips` para reflejar la fusión.

## D-107 · «Preguntas y resultados SQL» se agrupa por tema y encabezado compacto

- **Fecha:** 2026-10-17.
- **Revisión de relevancia:** se auditaron las 15 preguntas del catálogo (7 de precios, 8 de calidad de datos); cada una corresponde a un indicador K real o a una evidencia de regla de calidad (RN) distinta. No se encontró ninguna redundante ni de relleno: ninguna se elimina.
- **Decisión:** la lista de preguntas, antes una sola columna de 15 radios sin agrupar, ahora se divide en dos grupos con su propio encabezado — «PRECIOS · 7» y «CALIDAD DE DATOS · 8» — para que se lea organizada en vez de como una pila plana. Elegir una pregunta en un grupo limpia la selección del otro, así solo una queda marcada a la vez.
- **Encabezado compacto:** la página pasa del encabezado largo de documento (título + subtítulo + franja de frescura) al mismo encabezado de una línea que usa el Dashboard (título y frescura juntos), para que la lista y el primer resultado se vean sin desplazarse por un título alto.
- **Alcance:** el detalle de cada pregunta (resultado, cómo leerlo, tabla completa, SQL, Python) no cambia: ya vivía en paneles plegados por defecto, compacto desde antes.
- **Validación:** 414 pruebas (el único fallo, previo y no relacionado); se ajustan cuatro pruebas que referenciaban la clave única `catalog_choice` para usar las nuevas claves por tema (`catalog_choice_Precios`, `catalog_choice_Calidad de datos`).

## D-108 · Cada pregunta del catálogo muestra sus filas reales, como un motor de base de datos

- **Fecha:** 2026-10-17.
- **Decisión:** cada opción de la lista ahora muestra, junto a la pregunta, el número real de filas que devuelve su consulta sin filtrar —toda la tabla, no el ejemplo filtrado que se grafica— y un ícono que dice si el resultado ya es un gráfico (📊) o solo una tabla (📋). Por ejemplo: «¿Dónde es más caro? · 798.280 filas 📊».
- **Por qué el conteo es real:** `read_catalog_row_counts()` corre cada consulta guardada sin filtro (la misma que ya usa el detalle), cacheada por versión de la base, igual que el resto de los indicadores: no es una cifra inventada ni aproximada.
- **Relevancia de cada pregunta:** de las 15, nueve ya terminan en gráfico (las siete de precios más «Cuántos precios entran en los indicadores» y «Qué precios no tienen unidad comparable»); las seis restantes son evidencia de auditoría (ejecuciones, filas rechazadas, atípicos, cobertura de semanas, brecha calculable) donde una tabla es más clara que un gráfico. Ninguna necesita convertirse: ya se marcan correctamente.
- **Validación:** 414 pruebas (el único fallo, previo y no relacionado).

## D-109 · El deploy se colgaba 20+ minutos por el file watcher, no por el código

- **Fecha:** 2026-10-17.
- **Síntoma:** el panel público quedaba en «Your app is in the oven» indefinidamente. El log de Streamlit Community Cloud mostraba, en loop desde el arranque: `OSError: [Errno 24] inotify instance limit reached` y luego `OSError: [Errno 28] inotify watch limit reached`, nunca la línea «You can now view your app».
- **Causa:** el *file watcher* de Streamlit (que vigila cambios de archivo para recargar en caliente) agotaba los watchers de `inotify` del contenedor y reintentaba sin parar, sin llegar nunca a ejecutar `bi/dashboard.py`. No es un error del código: la app corre sin problema en local (`streamlit run`, HTTP 200, sin trazas).
- **Decisión:** `[server] fileWatcherType = "none"` en `.streamlit/config.toml`. Nadie edita archivos en el servidor publicado, así que el watcher no cumple ninguna función ahí; solo consumía recursos y podía bloquear el arranque.
- **Validación:** `streamlit run bi/dashboard.py` arranca y responde HTTP 200 en local con la configuración nueva; 414 pruebas sin cambios (no es código de la app).

## D-110 · «Documentación» vuelve a ser una carpeta, con tres vistas por perfil

- **Fecha:** 2026-10-17.
- **Decisión:** «Documentación» deja de ser un enlace directo (D-105) y vuelve a ser una carpeta con chevron, igual que «Dashboard» o «Arquitectura», con tres hijos en verde: **Business Intelligence**, **Business Analyst** e **IT y operación**. Cada uno es ahora su propia página, no una columna dentro de una vista combinada: el contenido no cambió (misión y visión para BA, los ocho indicadores para BI, las decisiones clave para IT), solo dónde vive.
- **Por qué:** la versión anterior era la única sección «plana» del menú —sin chevron ni hijos—, lo que la hacía ver fuera de patrón frente al resto; y el subtítulo «en una vista para cada perfil: Business Intelligence, Business Analyst e IT» repetía algo que ya se nota con solo mirar las tres tarjetas, así que se retira.
- **Compatibilidad:** `PAGE_DOCUMENTATION` (la vista combinada de las tres, una al lado de la otra) se mantiene fuera del menú solo para no romper enlaces viejos (`/documentacion-general`, `/decisiones`); ya no es el destino que abre el menú.
- **Validación:** 418 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d110_documentation_folds_open_into_three_profile_views` comprueba el chevron, los tres hijos y que cada vista muestra su contenido propio sin SQL.

## D-111 · Tipografía de ficha técnica en las tres vistas de Documentación, y un párrafo que no se cortaba

- **Fecha:** 2026-10-17.
- **Problema reportado:** las tres vistas de perfil se veían como texto corrido genérico — etiqueta en negrita seguida del párrafo, sin jerarquía ni aire, muy lejos del estándar visual del resto del panel. Además, «Operación semanal» (perfil IT) terminaba en «…Hace, en orden:» sin la lista que ese dos puntos prometía: un párrafo cortado a mitad de idea.
- **Decisión:** cada campo (Misión, Alcance, cada decisión clave, cada indicador) pasa a tener su propia etiqueta como título corto, con el texto debajo en un tono más apagado, un ancho de lectura máximo de 720 px y una línea divisoria fina entre campos — la cadencia de una ficha técnica, no de un párrafo. `describe_weekly_run()` corta la oración antes de «. Hace, en orden:» en vez de mostrar el inicio de una lista que no está.
- **Alcance:** solo CSS y una función nueva (`build_doc_profile_css`, `build_doc_field_html`, `describe_weekly_run`); ningún dato ni fuente cambia — siguen siendo las mismas tablas y documentos reales de siempre.
- **Validación:** 419 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d111_the_weekly_run_sentence_never_ends_on_a_dangling_colon` y una verificación de que las clases CSS nuevas están presentes.

## D-112 · El perfil IT nombra qué se decidió, no solo su categoría

- **Fecha:** 2026-10-17.
- **Problema reportado:** «Arquitectura y costo. Qué se eligió para operar sin costo y dentro de los límites de GitHub.» no dice nada concreto — es la categoría, no la decisión. Las cuatro agrupaciones de `KEY_DECISIONS` solo mostraban su tema, nunca el contenido real de los doce D-ID que agrupan.
- **Decisión:** cada grupo conserva su categoría como entrada, pero ahora lista, debajo, la frase real de «Decisión:» de cada uno de sus D-ID, leída en vivo de `docs/DECISIONES.md` (`read_key_decision_sentences()`, vía `project.list_decisions()`). Por ejemplo, «Arquitectura y costo» pasa a mostrar **D-012.** Base en archivo, job programado y panel publicado en servicios gratuitos. **D-020.** Los CSV descargados y la base cruda quedan fuera del repositorio. **D-046.** `etl/schema.sql` deja de crear el índice único y lo borra de las bases que ya lo tenían.
- **Qué no cambia:** sigue sin mostrarse una consulta SQL completa ni código fuente; una decisión puede nombrar un archivo o una cláusula (`HAVING`, `LAG()`) al describir qué se decidió, que no es lo mismo que mostrar la consulta.
- **Validación:** 420 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d112_the_it_profile_names_what_was_decided_not_only_its_category` comprueba que cada D-ID tiene su propia frase real y que aparece en la página.

## D-113 · Los enlaces externos abren con un clic normal, no solo Cmd/Ctrl+clic

- **Fecha:** 2026-10-17.
- **Síntoma reportado:** el enlace «Ver el registro completo de decisiones» (y, por el mismo motivo, cualquier enlace externo del panel) solo abría GitHub con Cmd/Ctrl+clic; un clic normal mostraba «github.com refused to connect» — el error típico de un sitio que rechaza ser embebido en un iframe.
- **Causa:** un script global (`build_visit_history_script`) escuchaba todo clic de la página y forzaba `target="_self"` en cualquier enlace, sin distinguir uno interno (navegación propia del panel) de uno externo. Si el panel corre detrás de un iframe —como puede pasar en Streamlit Community Cloud—, forzar `_self` en un enlace externo intenta navegar ese iframe, y GitHub la rechaza. Cmd/Ctrl+clic funcionaba porque el script se salta la intercepción con esas teclas y el navegador abre una pestaña nueva de verdad.
- **Decisión:** el script ahora solo fuerza `_self` cuando el enlace apunta al mismo origen (`anchor.hostname === location.hostname`); todo enlace externo deja de ser interceptado y abre en una pestaña nueva con un clic normal. `build_external_link_html`, el enlace de GitHub de la portada y el nuevo `build_github_link_html` pasan de `target="_self"` a `target="_blank"`.
- **Además:** el enlace a las decisiones en el perfil IT ahora lleva el logo de GitHub (`build_github_link_html`, con el SVG de marca ya usado en los diagramas).
- **Validación:** 422 pruebas (el único fallo, previo y no relacionado); nuevas pruebas `test_d113_the_github_link_opens_a_new_tab_with_its_mark` y `test_d113_the_global_click_handler_only_forces_internal_links`.

## D-114 · BI muestra los ocho indicadores en línea, no un enlace a otra página

- **Fecha:** 2026-10-17.
- **Problema reportado:** el perfil BI enlazaba a la vieja página «KPIs» (el camino tipo roadmap de D-090) para ver el detalle — una página que ya no vive en el menú y que el usuario creía eliminada. No hacía falta: lo único que BI necesita de ahí son los ocho indicadores con su nombre e ícono real.
- **Decisión:** se retira el enlace «Ver cada indicador con su cálculo →»; los ocho indicadores (`KPI_PRESENTATION`, el mismo diccionario que ya usa la página KPIs) se muestran ahí mismo, cada uno en su propia fila con su ícono real (`build_component_symbol`, el mismo vocabulario visual que el resto del panel) y un color distinto — los ocho colores de capa que ya usan los diagramas del pipeline (`architecture.LAYER_COLORS`), para que la tabla se lea moderna y cada indicador se distinga de un vistazo.
- **Por qué esos colores:** son los mismos ocho tonos que el lector ya vio en «Arquitectura y operación»; reutilizar el lenguaje visual existente en vez de inventar una paleta nueva.
- **Validación:** 423 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d114_bi_shows_every_kpi_with_a_real_icon_and_its_own_color_inline` comprueba las 8 filas, sus íconos reales, 8 colores distintos y que el enlace viejo ya no está.

## D-114b · Los ocho indicadores pasan de lista plana a galería de tarjetas flotantes

- **Fecha:** 2026-10-17.
- **Decisión:** las filas de D-114, con fondo plano teñido del color del indicador, se reorganizan en una grilla (`auto-fill, minmax(230px, 1fr)`) de tarjetas blancas elevadas: borde propio, sombra de color del indicador en vez de fondo teñido, y un ícono dentro de una placa redondeada del mismo color. Cada tarjeta se levanta un poco más al pasar el mouse (sombra más amplia, se eleva 5 px), dando la sensación «casi 3D» pedida.
- **Alcance:** solo CSS (`.doc-kpi-grid`, `.doc-kpi-row`, `.doc-kpi-icon`); el ancho de columna del perfil BI crece a 960 px (antes 720, pensado para texto corrido) para que la galería respire, solo cuando la página tiene esa grilla.
- **Validación:** 423 pruebas sin cambios (el único fallo, previo y no relacionado); las pruebas de D-114 siguen pasando porque verifican clases y datos, no el layout visual.

## D-115 · BA muestra el marco de negocio completo, sin enlace a una página que lo repite

- **Fecha:** 2026-10-17.
- **Problema reportado:** el enlace «Leer el marco de negocio completo →» del perfil BA llevaba a `PAGE_BUSINESS`, una página que muestra la misma tabla «Marco de negocio» (Misión, Visión, Objetivo, Alcance, Fuera de alcance) que BA ya tenía en pantalla, más algunas secciones adicionales (preguntas, audiencia, fuentes). El lector llegaba a lo mismo que ya estaba viendo.
- **Decisión:** se retira el enlace, igual que en D-114 con BI; BA pasa a mostrar la tabla completa, agregando el campo que le faltaba —**Criterios de aceptación**— para que no quede nada relevante solo del otro lado de un clic.
- **Validación:** 424 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d115_ba_shows_the_whole_business_frame_without_a_link_to_a_repeat` comprueba los seis campos y que el enlace viejo ya no está.

## D-116 · La página GitHub se reorganiza: menos enlaces, logo real, se ve como un repo

- **Fecha:** 2026-10-17.
- **Problema reportado:** la página tenía enlaces redundantes («Consultar ejecuciones dentro del proyecto →» repetía «Ver las ejecuciones en GitHub»; MANUAL mostraba dos enlaces en la misma fila: «Leer MANUAL en el panel» y «ver el original en GitHub»), no se veía organizada (una lista `<ul>` plana) y cada nombre decía «en GitHub» o «Ver»/«Abrir» en vez de mostrar el logo.
- **Decisión:**
  1. Se retira «Consultar ejecuciones dentro del proyecto →» (ya está Monitoreo → Ejecuciones) y el doble enlace de MANUAL; un destino, un enlace.
  2. Los nombres se acortan («Ver el código en GitHub» → «Código», «Abrir fuente ODEPA: precios mayoristas» → «ODEPA: precios mayoristas»): el logo y el encabezado de la página ya dicen que es GitHub.
  3. Cada enlace a github.com muestra el logo real de GitHub (`build_github_icon_svg`, mismo SVG de marca que ya usan los diagramas) en vez de un ícono de Material Symbols; ODEPA, que no es GitHub, conserva su ícono propio.
  4. La lista `<ul class="resource-tree">` hecha a mano se reemplaza por la grilla de tarjetas ya existente (`show_link_cards` / `.link-grid`, la misma que usa la tarjeta de Administración), con un botón «Copiar enlace» en cada una.
  5. Arriba de todo, una franja estilo cabecera de repositorio de GitHub (logo + `owner/repo` en monoespaciada + «Abrir repositorio ↗»), para que la página se sienta como una vista previa de GitHub antes de salir de verdad.
- **De paso:** `build_link_card_html` (compartida con la tarjeta de Administración) pasa de abrir en la misma ventana (D-070) a abrir en una pestaña nueva — la misma corrección de D-113, porque el mismo patrón de enlace sin pestaña nueva produce el mismo «refused to connect» bajo un iframe.
- **Validación:** 425 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d116_every_github_link_shows_the_real_mark_and_opens_a_new_tab` comprueba el logo en cada enlace de GitHub, el ícono propio de ODEPA y que todos abren en pestaña nueva; se ajustan dos pruebas existentes a los nombres cortos y al nuevo marcado.

## D-117 · «GitHub» en el menú lateral es un logo, no una palabra

- **Fecha:** 2026-10-17.
- **Problema reportado:** la entrada «GitHub» del menú, al no tener hijos, se veía en el color de texto apagado del sidebar (`sidebar_text`) en vez del blanco nítido de las carpetas con chevron, y en temas claros casi no se distinguía. Como no tiene subpáginas, no necesita una etiqueta de texto: un logo alcanza.
- **Decisión:** esa entrada deja de ser un `st.page_link` con el texto «GitHub» y pasa a ser un enlace de marcado propio (`nav-github-link`) que muestra solo el logo real de GitHub (el mismo SVG de marca que ya usan los diagramas y la página GitHub), con su propio estado de hover y de «página actual» (color de acento) en vez de depender del color de texto genérico del sidebar.
- **Alcance:** solo esta entrada; el resto del menú (Dashboard, Arquitectura, Análisis SQL, Documentación) sigue usando `st.page_link` sin cambios.
- **Validación:** 426 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d117_the_sidebar_github_entry_is_a_logo_not_a_word` comprueba el logo, que la palabra «GitHub» ya no aparece como texto visible y que el enlace sigue apuntando a la página correcta; se ajustan dos pruebas que buscaban un `page_link` con esa etiqueta.

## D-118 · Fuentes a su propia carpeta, sin enlaces repetidos en GitHub, tarjetas flotantes

- **Fecha:** 2026-10-17.
- **Revisión de «Calidad de datos» y «Ejecuciones»:** se consultó si seguían aportando en el menú, dado que GitHub ya muestra ejecuciones. Se confirmó que no son redundantes: «Ejecuciones» tiene el botón admin «Ejecutar ahora» (protegido con clave) para lanzar el job a mano, y «Calidad de datos» corre verificaciones en vivo contra la base real — ninguno de los dos existe en GitHub. Se mantienen sin cambios.
- **Fuentes de datos sale de la página GitHub:** ODEPA no es GitHub, así que sus dos enlaces (precios mayoristas, precios al consumidor) se retiran de `PROJECT_LINKS` y pasan a una carpeta propia del menú lateral, **«Fuentes»**, con el mismo patrón de carpeta y dos hijos en verde que usa el resto del árbol — salvo que, al ser destinos externos, sus hijos son enlaces de marcado propio (`nav-source-link`) en vez de `st.page_link` a una vista interna.
- **Enlace repetido en GitHub:** el primer enlace de «Código y operación» («Código») llevaba al mismo repositorio que ya abre la franja de cabecera de arriba. Se retira: la cabecera cumple esa función; el grupo empieza directamente en «Ejecuciones».
- **Tarjetas flotantes:** `.link-card` (compartida por la página GitHub y la tarjeta de Administración) gana sombra elevada y un leve desplazamiento hacia arriba al pasar el mouse, el mismo lenguaje «casi 3D» de la galería de KPIs (D-114b), en vez del borde plano anterior.
- **Validación:** 427 pruebas (el único fallo, previo y no relacionado); nueva prueba `test_d118_sources_is_its_own_folder_with_two_external_children` comprueba la carpeta, sus dos hijos externos y que abren en pestaña nueva; se ajustan cuatro pruebas existentes a la nueva lista de `PROJECT_LINKS` y de carpetas del sidebar.

## D-119 · El logo de GitHub del menú se ajusta a su ícono

- **Fecha:** 2026-10-17.
- **Problema reportado:** en Corporativo el logo apenas se veía: el enlace usaba `display:flex`, que lo estiraba a todo el ancho del menú, y su fondo de hover/actual se leía como un botón ancho y desteñido, con el ícono atenuado (`opacity:.82`) a un costado.
- **Decisión:** `inline-flex` de 28 × 28 px, sin atenuación; el fondo de hover y de página actual abraza solo el ícono. Página actual: color de acento con un fondo tenue del mismo tono.
- **Validación:** pruebas de D-117 sin cambios.

## D-120 · «Calidad y trazabilidad» sin scroll largo: tarjetas de estado y pestañas

- **Fecha:** 2026-10-17.
- **Decisión:** se mantiene la página (sus verificaciones en vivo no existen en GitHub). La tabla de nueve controles pasa a una grilla de tarjetas flotantes, cada una con su estado en una insignia de color (verde cumplido, ámbar pendiente, rojo falla). Lo que antes se apilaba debajo —evidencia de archivos y la última carga— pasa a dos pestañas, una visible a la vez.
- **Validación:** la prueba de «no declara una auditoría completa» sigue pasando sin cambios: los textos y estados son los mismos.

## D-121 · «Análisis SQL»: Resultado, SQL y Python en pestañas separadas

- **Fecha:** 2026-10-17.
- **Decisión:** el detalle de cada pregunta deja de apilar resultado, un expander de SQL y otro de Python uno debajo del otro. Ahora son tres pestañas —**Resultado · SQL · Python**—, como el panel de resultados de un motor de base de datos: Python queda separado de SQL y solo uno se ve a la vez. La lista de preguntas vive en un panel de altura fija que se desplaza por dentro (como el explorador de objetos de una herramienta de base de datos), así la página no crece. Se retira la guía «1 Pregunta → 2 Resultado → 3 Código», que las pestañas reemplazan.
- **Validación:** se ajusta la prueba del catálogo para verificar las tres pestañas y el código Python.

## D-122 · «DevOps y seguridad»: pestañas por tema y tarjetas en grilla

- **Fecha:** 2026-10-17.
- **Decisión:** el expander «Ver coste, capacidad, seguridad y observabilidad», que al abrirse apilaba cinco secciones, pasa a cinco pestañas (Coste y capacidad, Seguridad, DevOps, Observabilidad, Informes). Dentro de cada una, las filas técnicas dejan de ser una lista vertical y pasan a una grilla de tarjetas flotantes, panorámica y simétrica.
- **Validación:** se ajustan dos pruebas: la de DevOps verifica las cinco pestañas, y la que prohibía pestañas en cualquier página ahora las permite solo donde reemplazan un scroll largo (KPIs, DevOps, Calidad, Análisis SQL).

## D-123 · Elegir una región o una familia en el Resumen ya no recarga la página

- **Fecha:** 2026-10-17.
- **Problema reportado:** al hacer clic en una región del mapa (o en una familia), la página se recargaba entera en vez de actualizarse en el lugar.
- **Causa:** el mapa y la lista de familias son SVG/HTML hechos a mano con enlaces `<a href>`; cada clic era una navegación del navegador, que en Streamlit abre una sesión nueva.
- **Decisión:** un componente `st.components.v2` de solo JavaScript (`HOME_LINKS_JS`) captura esos clics dentro de `.greenocean-mockup` cuando apuntan a la misma página, cancela la navegación y entrega los parámetros del enlace a Python (`apply_home_link_click`), que los escribe en `st.query_params`; el resto de la página los lee igual que antes. El componente se registra en cada ejecución, no al importar, porque cada runtime de Streamlit tiene su propio registro.
- **Validación:** comprobado en un navegador real (Chrome por CDP): tras el clic la página conserva su estado de JavaScript (no hubo recarga) y el Resumen muestra la región elegida.

## D-124 · El logo de GitHub pasa al pie del menú, sobre una pastilla clara

- **Fecha:** 2026-10-17.
- **Problema reportado:** dentro de la lista, el logo azul se perdía sobre el azul marino de Corporativo y se leía como una sección más, aunque no lo es.
- **Decisión:** sale del árbol del menú y queda en el pie, junto a «Apariencia», como una pastilla casi blanca con el logo casi negro; legible en cualquier tema. En la página GitHub, la pastilla muestra un contorno de acento.

## D-125 · El conteo de filas por consulta se calcula en SQLite

- **Fecha:** 2026-10-17.
- **Problema reportado:** «Análisis SQL» tardaba mucho en abrir.
- **Causa:** D-108 contaba las filas de las 15 consultas cargando cada resultado completo en pandas (la mayor, unas 800 mil filas).
- **Decisión:** se reemplazó por `COUNT(*)` y, con la consola de D-126, el conteo previo desaparece: como en un motor de base de datos, las filas se informan al ejecutar.

## D-126 · «Análisis SQL» pasa a ser una consola SQL

- **Fecha:** 2026-10-17.
- **Problema reportado:** la sección seguía viéndose como una lista de preguntas y respuestas, no como la interfaz de un motor de base de datos donde se escribe una consulta y se ve el resultado en una tabla.
- **Decisión:** la página se rehace con la forma de SQL Server Management Studio o DBeaver: a la izquierda un **explorador** (las tablas de `datos.db` con su número de filas y las 15 consultas guardadas por tema, con un filtro); a la derecha un **editor SQL**, el botón **Ejecutar**, una línea de estado (filas · milisegundos · solo lectura) y la **grilla de resultados** con descarga CSV. Una consulta guardada suma sus pestañas Gráfico, Cómo leerlo y Python, y el enlace a su línea en GitHub. Abre con `SELECT * FROM weekly_price LIMIT 100`; `?consulta=` sigue abriendo una consulta guardada.
- **Seguridad:** `queries.run_console_sql` ejecuta el texto del visitante sobre la conexión de solo lectura (`mode=ro`), acepta una sola sentencia que empiece con `SELECT` o `WITH`, aplica un autorizador de SQLite que niega todo salvo lectura (sin `ATTACH`, `PRAGMA` ni escritura), corta a las 1.000 filas y detiene la consulta a los 10 s.
- **Validación:** 431 pruebas; nuevas pruebas `test_d126_*` cubren el explorador, la carga de una consulta guardada, la ejecución de SQL escrito a mano, el rechazo de seis consultas peligrosas, el corte por tiempo y el tope de filas.

## D-127 · La consola carga al hacer clic y ejecuta solo con «Ejecutar»

- **Fecha:** 2026-10-17.
- **Problema reportado:** al hacer clic en una pregunta la consulta se ejecutaba sola, así que «Ejecutar» y «Restaurar» no servían para nada; las pestañas «Cómo leerlo» y «Python» no tenían lugar en una consola SQL; el editor era chico.
- **Decisión:** un clic en el explorador solo **carga** la consulta en el editor (la línea de estado pide pulsar «Ejecutar»); «Ejecutar» la corre. La primera visita y los enlaces con `?consulta=` sí ejecutan, para que la página no abra vacía. «Restaurar» aparece solo cuando el texto fue editado y vuelve a la consulta cargada. Se retiran las pestañas «Cómo leerlo» y «Python»: lo que compara la consulta pasa a una línea bajo su título, y el código Python vive en GitHub. «Gráfico» se muestra solo si lo ejecutado es la consulta guardada sin cambios. El editor pasa de 170 a 270 px.
- **Por qué Python salió:** mostraba las funciones que sirven cada pregunta en el panel (la que arma el resultado, el lector de la base y, en algunas, una versión equivalente que una prueba compara con el SQL, D-049). Es evidencia técnica que ya está completa en el repositorio; en la consola distraía.

## D-128 · «Alerta de precio» cierra la lista del menú, en rojo

- **Fecha:** 2026-10-17.
- **Problema reportado:** en el pie, la alerta quedaba pegada al logo de GitHub (D-124) y se podía apretar una por otra.
- **Decisión:** la alerta pasa a ser la última fila del árbol del menú, con la misma medida que las demás filas y el único color rojo de la lista; el pie queda solo con «Apariencia» y el logo de GitHub.

## D-129 · «Ejecuciones» con el ritmo del Dashboard; «GitHub Actions» en la página GitHub

- **Fecha:** 2026-10-17.
- **Problema reportado:** la página Ejecuciones se veía con números grandes y tarjetas poco elegantes; y la página GitHub tenía también una tarjeta «Ejecuciones», con el mismo nombre que la página del menú.
- **Decisión:** la página pasa a una cabecera de una línea (título y frescura, como el Dashboard y la Consola SQL, con `show_compact_page_header` compartida), una franja de cuatro cifras compactas (última ejecución, próxima, filas cargadas, duración), el historial a la vista como tabla limpia —antes estaba plegado detrás de «Ver historial»— y, al lado, una tarjeta simple de Administración con «Recargar datos del panel» adentro. La tarjeta de la página GitHub se llama ahora **«GitHub Actions»** («Logs completos de cada ejecución del workflow»): son contenidos distintos —los logs técnicos en GitHub frente al historial y el botón de administración del panel— y ya no comparten nombre.
- **Validación:** 434 pruebas; nuevas `test_d129_*`.

## D-123b · El botón «Contexto del precio» vuelve a funcionar

- **Fecha:** 2026-10-17.
- **Problema reportado:** el botón «Contexto del precio» del Resumen no hacía nada.
- **Causa:** D-123 capturaba todo clic a la misma ruta; Contexto del precio vive en esa misma ruta (otra vista), así que su enlace se tragaba como si fuera un clic del mapa.
- **Decisión:** la captura solo toma enlaces con `_home_region` y sin `_home_key` ni `vista`, es decir, los del mapa y de las familias; los de un producto navegan como antes.

## D-130 · «Datos» sale del menú

- **Fecha:** 2026-10-17.
- **Revisión:** la vista recorría las filas de la base con ocho filtros, tres modos (precios, variaciones, brecha) y paginación. Ningún elemento del panel enlazaba ya a ella, y lo que ofrece lo cubren mejor el buscador del Resumen y la Consola SQL (D-126), que lee las mismas tablas.
- **Decisión:** se retira del menú; su dirección sigue funcionando para enlaces viejos.

## D-131 · Las animaciones no tienen interruptor: se pausan solas

- **Fecha:** 2026-10-17.
- **Decisión:** se retira «Animar el ciclo DevOps» (el de Pipeline ya no existía). Todos los diagramas animan por defecto; un script global (`IDLE_ANIMATION_SCRIPT`) pausa las animaciones CSS y SVG tras 20 s sin mouse, teclado, toque ni desplazamiento, y las reanuda con el primer movimiento, para no gastar recursos en una pestaña olvidada.
- **Validación:** comprobado en Chrome por CDP: tras 22 s sin actividad la página queda en pausa y un movimiento del mouse la reanuda.

## D-132 · «DevOps y seguridad» en una pantalla: el ciclo y sus capas

- **Fecha:** 2026-10-17.
- **Decisión:** la página pasa a una cabecera de una línea, el ciclo DevOps animado a la izquierda y, a la derecha, cinco tarjetas —Seguridad, DevOps, Observabilidad, Informes, Coste y capacidad— que abren el detalle de cada capa en una ventana emergente, en vez de pestañas apiladas bajo el diagrama. La fila de seguridad que describía la vieja «Consulta de datos» con columnas fijas se reemplaza por la protección real de la Consola SQL.

## D-133 · El SQL de la consola se ve como código, con colores

- **Fecha:** 2026-10-17.
- **Decisión:** el cuadro de texto plano de la Consola SQL se reemplaza por un editor propio (componente `sql_editor`): palabras clave en azul, textos entre comillas en naranja, funciones, números y comentarios con su color, con paletas al estilo de VS Code para modo oscuro y claro. Tab inserta cuatro espacios y Ctrl/⌘ + Enter ejecuta.
- **Validación:** comprobado en Chrome; las pruebas leen y escriben el texto por `session_state`.

## D-134 · Las columnas JSON se abren y las columnas con código se explican

- **Fecha:** 2026-10-17.
- **Problema reportado:** en «¿Cómo venían las filas rechazadas?» la columna `original_row` se cortaba, y no se entendía qué era `source`.
- **Decisión:** toda columna de texto que trae objetos JSON se abre en una columna por campo (16 en `original_row`). Las columnas con nombre técnico (`source`, `reason`, `channel`, `flag`, `normalized_unit`…) muestran su significado al pasar el mouse por el encabezado; `source` es la fuente ODEPA: `wholesale` = precios mayoristas, `consumer` = precios al consumidor.

## D-135 · «Análisis con Python»: una consola de las preguntas que el proyecto responde en Python

- **Fecha:** 2026-10-17.
- **Decisión:** nueva carpeta del menú con su consola. Arriba, lo que hace Python en el proyecto (ingesta, ETL, indicadores, dashboard); abajo, seis preguntas reales —filas rechazadas (RN-11), conversión de unidades (RN-03 a RN-05), alertas K6, desfase K5, rango habitual y patrón estacional K4— cada una con el script corto que llama a las funciones de `etl/` y `bi/`. Como en la Consola SQL, un clic carga y **Ejecutar** corre; la pestaña «Funciones usadas» muestra el código real de cada función, con enlace a su línea en GitHub.
- **Seguridad:** el código no se edita. Ejecutar Python escrito por un visitante en un servidor público equivale a entregarle el servidor; solo cambian los parámetros, elegidos de listas cerradas o escritos como literal de Python (`repr`), de modo que un valor nunca puede ser código (`bi/python_console.py`).
- **Validación:** pruebas `test_d135_*`; comprobado en Chrome.

## D-136 · DevOps muestra la arquitectura por plataforma; Pipeline, solo el recorrido

- **Fecha:** 2026-10-17.
- **Problema reportado:** DevOps mostraba un ciclo animado y un enlace a Pipeline para ver la arquitectura; Pipeline repartía su espacio entre el recorrido, una miniatura «Estado de la última ejecución» (el mismo recorrido en pequeño, sin mostrar ninguna ejecución) y la arquitectura por plataforma.
- **Decisión:** «Arquitectura por plataforma» pasa completa y a todo el ancho a **DevOps y seguridad**, con las cinco capas como fila de tarjetas debajo; se retiran el ciclo y el enlace. **Pipeline** queda con un solo diagrama, el recorrido por capas, a tamaño completo y con zoom, sin galería ni vista «Ampliar». El estado de cada ejecución está en Ejecuciones y en GitHub Actions. Los botones de zoom van bajo el diagrama, sin tapar los puntos de estado.
- **Validación:** prueba `test_d136_*`; comprobado en Chrome.

## D-137 · Las capas de DevOps en tarjetas flotantes con el logo real de cada herramienta

- **Fecha:** 2026-10-17.
- **Problema reportado:** en las ventanas de cada capa (p. ej. Informes) las tarjetas dejaban mucho espacio vacío y llevaban todas el mismo ícono genérico.
- **Decisión:** tarjetas compactas y flotantes, con el mismo lenguaje de la galería de KPI (D-114b): el logo real de la herramienta detrás de cada fila (GitHub, SQLite, Streamlit, pytest, Python, Git) sobre un fondo de su color de marca, el título, qué hace y dónde vive. Se reparten a todo el ancho y la última fila se estira, sin huecos. La nota de Informes enlaza directo a los informes en GitHub en vez de a otra página del panel.

## D-138 · Encabezados en español en las consolas

- **Fecha:** 2026-10-17.
- **Problema reportado:** las tablas de resultado de las consolas mostraban encabezados en inglés (`week_start`, `product_id`…) en una aplicación en español.
- **Decisión:** cada columna conocida —de las tablas, de las consultas guardadas, de las preguntas de Python y de los campos de una fila rechazada— se muestra con su nombre en español (Semana, ID producto, Precio…). El nombre real sigue en el tooltip del encabezado, porque es el que hay que escribir en una consulta; la base y el SQL no cambian. La huella del archivo (64 caracteres) va angosta para no empujar las demás columnas.
- **Validación:** `test_d138_*` exige un encabezado en español para toda columna que las consolas pueden mostrar.

## D-139 · El menú lateral empieza abierto

- **Fecha:** 2026-10-17.
- **Decisión:** todas las carpetas del menú (Dashboard, Arquitectura, Fuentes, Análisis SQL, Análisis con Python, Documentación) empiezan abiertas, en vez de cerradas (D-096): el mapa completo de la aplicación se ve de un vistazo y cabe en una pantalla de 900 px de alto. Un clic en la carpeta la pliega. Los dos enlaces de Fuentes quedan alineados y con el mismo tamaño que los demás.

## D-140 · Una línea por entrada en los exploradores de las consolas

- **Fecha:** 2026-10-17.
- **Problema reportado:** las preguntas de los exploradores (Consola SQL y Consola Python) ocupaban dos o tres líneas y no se alineaban.
- **Decisión:** cada entrada lleva un nombre corto, de 30 caracteres como máximo (p. ej. «Precio por región (K3)», «Alertas de la semana (K6)»), en una sola línea, como los objetos de una herramienta de base de datos. La pregunta completa sigue como título de la consulta y al pasar el mouse; el filtro busca en ambos. El explorador es algo más ancho y se acortaron las preguntas de la Consola Python.
- **Validación:** `test_d140_*`.

## D-141 · Los códigos de la base se leen en español

- **Fecha:** 2026-10-17.
- **Problema reportado:** no se entendía qué era `wholesale` en las tablas.
- **Decisión:** en las grillas de las consolas, los valores codificados se muestran en español: fuente (`wholesale` → Mayorista, `consumer` → Consumidor), motivo de rechazo (`NON_POSITIVE_PRICE` → Precio cero o negativo…), marca (`ATIPICO` → Atípico), estado de la carga (`LOADED` → Cargada) y estado del precio. El SQL sigue usando los códigos reales (`WHERE source = 'wholesale'`); el tooltip del encabezado los indica. La página Calidad de datos muestra también el motivo en español.
- **Validación:** `test_d141_*`.

## D-142 · La vista previa de una tabla abre en sus filas más recientes

- **Fecha:** 2026-10-17.
- **Problema reportado:** la tabla `weekly_price` de la Consola SQL solo mostraba 2022.
- **Causa:** la vista previa era `SELECT * … LIMIT 100` sin `ORDER BY`; SQLite devuelve las filas en el orden en que se guardaron, y las primeras 100 eran de la primera semana de 2022.
- **Decisión:** las tablas con fecha se previsualizan de la más reciente a la más antigua (`weekly_price` y `dim_date` por `week_start`, `etl_run` por `started_at`, `rejection` por carga): la consola abre en la última semana cargada (60 ms sobre 811.578 filas). Una marca vacía se lee «Sin marca» (el precio entra en los indicadores) en vez de «None».
- **Validación:** `test_d142_*`.

## D-143 · Las consolas SQL y Python salen del proyecto

- **Fecha:** 2026-10-18.
- **Problema reportado:** las consolas mostraban tablas con identificadores (`product_id`, `region_id`) que no dicen nada al lector, y repetían en vivo código que ya está en GitHub.
- **Decisión:** se retiran las dos (D-126, D-135 y sus ajustes D-127, D-133, D-134, D-138, D-140 a D-142). Las respuestas ya están en el panel, mejor presentadas (Resumen, Contexto de precios, Calidad de datos, Ejecuciones); el código vive en GitHub, la fuente de verdad. Los enlaces a una consulta abren su línea en GitHub. Las direcciones viejas abren el Resumen. Con la consola se va también su ejecutor de SQL (autorizador, límite de filas y de tiempo): un mecanismo menos que mantener y defender.

## D-144 · Auditoría de datos y variación nacional sobre las mismas regiones

- **Fecha:** 2026-10-18.
- **Pedido:** antes de redactar la documentación, asegurar que los datos sean fiables, verificables y respeten la temporalidad semanal.
- **Auditoría:**
  - Seis invariantes, sin excepciones: cada semana es un lunes; el calendario `dim_date` tiene 249 semanas sin huecos; una sola fila por semana, producto, región, canal y unidad; ningún precio ≤ 0; todo producto tiene familia; en cada carga, filas leídas = cargadas + rechazadas (2.512.298 = 2.512.097 + 201).
  - La única semana sin precios es la del 02-05-2022 del consumidor, un hueco de la propia fuente ya registrado (D-042).
  - 400 precios semanales elegidos al azar se reconstruyeron desde las filas crudas de ODEPA (`raw.db`), con un cálculo independiente del ETL: los 400 coinciden exactamente (diferencia máxima 2,5 × 10⁻¹⁶).
- **Problema encontrado:** el precio nacional es el promedio de las regiones con dato esa semana, y la variación del Resumen comparaba dos promedios con regiones distintas. Un producto vendido en Arica y Santiago una semana y solo en Santiago la siguiente «cambiaba» sin que ningún precio regional se moviera. En la semana del 05-10-2026, 99 de 734 comparaciones se desviaban más de 5 puntos (Caigua Primera, Mayorista: +36 % frente a −5 % real) y Carne bovina aparecía «Subió» cuando bajó.
- **Decisión:** la variación nacional semanal promedia solo las regiones con precio en ambas semanas (muestra emparejada, como los índices de precios oficiales); los dos precios mostrados son los de esas regiones, y una clave sin región en común no tiene comparación. Las familias del Resumen coinciden ahora con el cálculo independiente.
- **Verificable:** `tests/test_data_audit.py` repite los invariantes y reconstruye 120 precios desde las filas crudas en cada ejecución de las pruebas (se omite donde no está `raw.db`, que no se sube al repositorio, D-020).
- **Pendiente:** las alertas K6 leen la misma serie nacional: 8 de las 43 alertas de la semana vienen probablemente de un cambio de regiones. Se corrige aparte, porque cambia el indicador, su versión SQL (D-049) y el informe semanal.

## D-145 · Las alertas K6 miden el cambio sobre las mismas regiones

- **Fecha:** 2026-10-18.
- **Problema:** lo pendiente de D-144. K6 comparaba el precio nacional de una semana con el de la anterior aunque las regiones con dato fueran otras; 8 de las 43 alertas de la semana del 05-10-2026 venían probablemente de ese cambio de composición y no de un movimiento de precio.
- **Decisión:** `k6_national_weekly_price` entrega, junto al precio nacional, el promedio de las regiones con precio en ambas semanas y el de esas mismas regiones la semana anterior; `bi/alerts.py` calcula la variación con ese par. La versión SQL (`k6_usual_range_sql`) hace lo mismo, y la prueba de D-049 sigue exigiendo que ambas den el mismo resultado. Una semana sin la anterior no tiene región en común, así que un hueco nunca produce un cambio, como antes.
- **Resultado:** 46 alertas en la semana del 05-10-2026, todas sobre movimientos de precios reales.
- **Costo:** la consulta tarda unos 2 s en vez de 0,8 s; el panel la guarda en caché una vez por carga semanal. Se descartó un índice permanente porque agrandaría `datos.db`, que se sube cada semana.

## D-146 · Revisión de pertinencia: solo conclusiones que se sostienen

- **Fecha:** 2026-10-18.
- **Pedido:** verificar cifras, KPI y preguntas, y quitar lo que no aporta, para no mostrar conclusiones insignificantes.
- **Medido en la semana del 05-10-2026 y corregido:**

| Lo que decía el panel | Lo que mostró la medición | Decisión |
|---|---|---|
| «Frutas subió +1,7 %» (promedio) | La mediana era +0,02 %: unas pocas series de una región en ±50 % arrastraban el promedio; Carne bovina y Pan cambiaban de signo | Cada familia muestra la **mediana**: lo que hizo el producto típico |
| Ranking «Mayor cambio» | 19 de los 20 primeros eran una sola región con una sola cotización | Un cambio apoyado en **una sola cotización** en alguna de las dos semanas va al final del orden, con la marca «1 cotización» (234 de 787 esta semana) |
| Mapa: región pintada con 52 % | 3 de 9 regiones no se distinguían del azar | Una región se pinta solo si pasa una **prueba de signos** (p < 0,05); si no, «sin dirección clara» |
| 46 alertas de precio (K6) | 8,6 % de las series alertaba cada semana, el nivel que da el azar | Una alerta debe ser inusual (2 desviaciones) **y** material (cambio ≥ 10 %): 22 alertas |
| Contexto: «sobre lo habitual» | 8 % de los estados cambiaba al comparar las mismas regiones | El rango habitual usa la historia de **las regiones con precio esta semana** |
| «Qué suele pasar en las próximas semanas» (K4) | Los años coincidían en la dirección de un mes solo el 35 % de las veces | Un mes se muestra solo si **al menos 3 años** coinciden; si no, «sin patrón» |

- **Preguntas:** vuelve **P1/K1**, el margen del consumidor sobre el mayorista, que el panel ya no mostraba y es lo que solo este proyecto puede calcular al cruzar las dos fuentes: Contexto de precios suma la tarjeta «Sobre el precio mayorista», por canal y frente a su rango habitual (Tomate en Feria libre: +29,7 % frente a +46,5 % a +57,1 % habitual; recalculado a mano por región). Se retira **P5/K5**, el rezago mayorista → consumidor: en el 57 % de las 1.215 series no hay relación clara y el 18 % da «la misma semana», que datos semanales no pueden separar. P2 queda cubierta por Contexto (Feria libre frente a Supermercado) y P3 por el mapa.
- **Calidad de datos:** la reconciliación fuente → base, el recálculo de indicadores y la concordancia con la pantalla pasan de «Pendiente» a verificados, con su evidencia; el contraste con otra fuente sigue pendiente, porque ODEPA es la única fuente oficial de estos precios.
- **Verificable:** cada regla tiene su prueba en `tests/test_data_audit.py`.

## D-147 · El modelo de datos es una sola vista panorámica

- **Fecha:** 2026-10-18.
- **Problema reportado:** si el modelo estrella ya muestra todas las tablas, ¿para qué elegir una en una lista?
- **Decisión:** se retiran la lista «Tablas de datos.db» y el panel «Detalle de la tabla seleccionada», que solo añadían una frase y una consulta SQL de ejemplo. El diagrama ocupa todo el ancho; cada tabla explica al pasar el mouse su papel (hechos, dimensión o auditoría), sus filas y para qué sirve. El enlace a `etl/schema.sql` abre GitHub, no una página fuera del menú.

## D-148 · «Código Python y SQL» sale; limpieza del código sin uso

- **Fecha:** 2026-10-18.
- **Problema reportado:** si GitHub tiene todo el código, ¿para qué una página que lo repite, con su enlace en la navegación? Y la leyenda del modelo de datos quedaba pegada al borde.
- **Decisión:** se retira la página «Código Python y SQL» (ventana «Código del proyecto»); su dirección vieja abre la página GitHub. La navegación «Siguiente» del pie ya no pasa por ella. Con la limpieza se quitan 73 funciones y constantes de `bi/dashboard.py` que ninguna página usaba, restos de páginas retiradas: el archivo pasa de 8.474 a unas 7.500 líneas. La leyenda del modelo de datos lleva su propio margen y una línea que la separa del diagrama, y todo cabe en una pantalla.

## D-149 · La ejecución manual es un botón visible, con su resultado

- **Fecha:** 2026-10-18.
- **Problema reportado:** en Ejecuciones no se veía dónde se ejecuta el pipeline a mano, ni si terminó bien. El único botón visible, «Recargar datos del panel», no ejecuta nada: solo vuelve a leer la base guardada. «Ejecutar ahora» existía, pero escondido detrás de la clave.
- **Decisión:** la tarjeta se llama «Ejecución manual» y explica que el pipeline corre solo cada martes a las 09:00 (Chile). El primer botón es **«Ejecutar pipeline ahora»**: un botón redondo de encendido, azul con brillo, anillo metálico y el símbolo de encendido en blanco, con su texto debajo; pide la clave de control en una ventana, muestra los pasos en vivo y termina con un mensaje claro, «Se ejecutó correctamente» o «No se ejecutó completamente: un paso falló», además de un aviso flotante. Sin la clave y el token en los secretos se ve desactivado, con su motivo. «Recargar datos del panel» queda como botón secundario y confirma «Datos recargados · base del …».
- **Error corregido:** al terminar una ejecución manual, el código limpiaba la caché de una función que no la tenía (`read_pipeline_runs.clear()`); toda ejecución manual exitosa terminaba con un error en pantalla. Ahora limpia `fetch_pipeline_runs`, la función guardada en caché.
- **Validación:** pruebas `test_d149_*` (clave equivocada, ejecución exitosa, ejecución fallida, sin secretos), sin llamar a GitHub.

## D-150 · Simetría y coherencia visual de todas las páginas

- **Fecha:** 2026-10-18.
- **Pedido:** tras la revisión página por página, que todas las correcciones sean simétricas, coherentes con los datos y sin espacios en blanco inútiles.
- **Resumen semanal:** cuatro indicadores de igual ancho bajo el título (precios comparados, familias, regiones y alertas), todos leídos del mismo modelo semanal que los gráficos. El mapa se estira a la altura de la columna derecha y ambas terminan en la misma línea (se midió en el navegador: 37 px de diferencia, antes 249). Filas de familia más compactas, tabla de productos de altura fija con desplazamiento interno, nota de cobertura a todo el ancho debajo, filtros sin cortes y botón «Ver contexto».
- **Contexto de precios:** el gráfico y las dos tarjetas de la semana («Precio esta semana», «Sobre el precio mayorista») empiezan y terminan en la misma línea (215 → 658 px, medido); «Qué suele pasar en las próximas semanas» pasa a una franja de ancho completo donde cada mes se lee en una línea.
- **Cabeceras:** Pipeline y Calidad de datos usan la misma cabecera de una línea con la frescura de los datos que el resto de las páginas técnicas.
- **Calidad de datos:** una sola columna de huella corta en vez de dos huellas idénticas de 64 caracteres; fechas legibles; se quita la línea técnica de la comprobación local.
- **Pipeline:** etiquetas un paso más grandes; se quitan dos fichas «HTTPS · CSV» que tapaban los nombres de las fuentes y repetían el encabezado de la columna.
- **Alertas de precio:** todas las familias con la misma tarjeta; el número de alertas está escrito, así que la forma y el color ya no representan una cantidad.
- **Textos:** la nota del pie explica que cada variación semanal compara las mismas regiones; la hoja de estilo opcional (`premium.css`) se carga solo si existe.

## D-151 · La documentación es el PRD, el SAD y el ADR

- **Fecha:** 2026-10-18.
- **Problema reportado:** las páginas Business Intelligence, Business Analyst e IT y operación eran resúmenes de texto que repetían lo que el panel ya muestra (y la de BI aún listaba K5, retirado en D-146).
- **Decisión:** la carpeta Documentación tiene tres documentos reales, escritos en español, sin código, con tablas y los diagramas del propio proyecto:
  - **PRD** (`docs/PRD.md`): problema, perfiles (marcados como hipótesis de diseño), preguntas P1–P6 con su estado final, alcance, requisitos funcionales y no funcionales trazados a reglas, KPI y pruebas, criterios de aceptación, limitaciones y riesgos. Declara que se reconstruyó después de construir el producto y muestra lo previsto frente a lo entregado.
  - **SAD** (`docs/SAD.md`): contexto, contenedores, flujo por capas, modelo de datos, escenarios de ejecución, despliegue, conceptos transversales, atributos de calidad y deuda técnica.
  - **ADR** (`docs/ADR.md`): 29 decisiones arquitectónicas en formato estándar (contexto, decisión, alternativas, consecuencias), cada una con su referencia D-xxx; cuando el registro no guarda las alternativas, lo dice.
- **Cómo se muestran:** el panel lee los archivos de `docs/`, así que muestra lo mismo que GitHub; cada `[[diagrama:…]]` se reemplaza por el diagrama vivo (plataforma, pipeline o modelo estrella). La navegación «Siguiente» termina en la documentación. Las direcciones viejas de los tres perfiles abren el PRD o el SAD. Se quitan las páginas de perfil y su código.

## D-152 · Evolución prevista: dbt, DuckDB, Parquet, IPC y clima; la nube solo con datos de empresa

- **Fecha:** 2026-10-19.
- **Decisión:** la próxima etapa usa solo tecnologías de código abierto o gratuitas sin vencimiento: Parquet (bronce), dbt Core (transformaciones y pruebas) y DuckDB (motor), portables a otro motor cambiando la configuración. Las nuevas fuentes previstas son el IPC del INE (precios reales) y el clima por región (contexto de las alertas). Un warehouse en la nube no se adopta en el alcance público: se justificaría solo si una empresa sumara sus propios datos. La comparación por cadena de supermercados queda fuera por falta de fuente oficial y por D-001.
- **Documentado en:** `docs/PROMPT_EVOLUCION.md` (plan por fases y reglas), PRD (sección 13 y RNF-10), SAD (sección 12) y ADR-30 a ADR-32. Todo marcado como previsto, no entregado.

## D-153 · Auditoría entre páginas: un solo precio por producto y semana

- **Fecha:** 2026-10-19.
- **Paso 1 de la refonte.** Se recalcularon y cruzaron las cifras de todas las páginas.
- **Coinciden:** 22 alertas en el menú, en el indicador del Resumen, en la ventana de alertas y en el informe semanal; 728 de 787 precios comparados en el indicador y en la nota de cobertura; 3.163 precios de la semana en el diagrama de DevOps; 811.578 precios, 2.512.298 filas leídas, 2.512.097 cargadas y 201 rechazadas en Pipeline, Ejecuciones, Calidad y PRD.
- **Contradicción encontrada:** 54 de 247 productos mostraban un precio de la semana distinto en el Resumen y en Contexto de precios (hasta 24 %, Naranja Lane Late en Supermercado: $1.332 frente a $1.761). Desde D-144 el Resumen mostraba el promedio de las regiones presentes en ambas semanas, y Contexto el de todas las regiones con precio esa semana.
- **Decisión:** el precio que se muestra es siempre el precio nacional de la semana (todas las regiones con precio), en todas las páginas; la variación sigue comparando las mismas regiones en ambas semanas (D-144). Cuando las regiones cambian, la fila lo dice: «variación sobre N regiones comunes».
- **Referencia para la migración:** `tests/fixtures/snapshot_2026-10-05.json` guarda las cifras clave de la semana (filas por fuente, suma de precios, marcas, rechazos, alertas, comparados, medianas por familia y estado de cada región); `tests/snapshot_figures.py` las calcula como el panel. La migración a DuckDB debe reproducirlas exactamente.
- **Validación:** `test_the_resumen_and_contexto_show_the_same_price_this_week` y `test_the_panel_reproduces_the_reference_figures_of_its_week`.

## D-154 · El data warehouse pasa a dbt Core, DuckDB y Parquet, con paridad exacta

- **Fecha:** 2026-10-19.
- **Paso 2 de la refonte (ADR-30, ahora aceptada).**
- **Capas:** `etl/raw.db` sigue siendo la zona de aterrizaje de los CSV; `etl/bronze.py` la copia a **Parquet** por fuente y año (16 MB frente a 644 MB). Un proyecto **dbt** (`dbt/`) traduce las reglas: staging (`stg_odepa__wholesale`, `stg_odepa__consumer`: RN-01, RN-02, RN-13), intermedio (`int_prices__validated` RN-11, `int_prices__units_normalized` RN-03 a RN-05, `int_prices__weekly` RN-07 a RN-10, `int_prices__outlier_flagged` RN-12) y marts (`dim_product`, `dim_region`, `dim_channel`, `dim_date`, `weekly_price`, `rejection`). Veinticinco pruebas de dbt cubren claves, relaciones, valores aceptados, precios positivos, la semana faltante conocida (D-042), la unicidad (RN-14) y la conciliación leídas = cargadas + rechazadas (RNF-05).
- **Dos archivos:** dbt construye en un almacén de trabajo que no se sube (`etl/warehouse_build.duckdb`); `etl/pipeline.py` copia las tablas del panel a un archivo nuevo y compacto, `etl/datos.duckdb` (12,6 MB frente a 34 MB de SQLite), registra la carga en `etl_run` y solo entonces reemplaza el publicado. Si un modelo o una prueba falla, nada cambia y la falla queda registrada.
- **Paridad:** antes de cambiar el panel se compararon fila a fila las dos bases: 811.578 precios con las mismas claves, marcas y observaciones; diferencia máxima de precio 4,9 × 10⁻¹⁶; dimensiones de regiones y fechas idénticas; los 201 rechazos iguales. La fotografía de D-153 se reproduce exacta. `tests/test_migration_parity.py` repite la comparación cada semana mientras SQLite siga escribiéndose como respaldo.
- **Panel:** `bi/queries.py` abre DuckDB en solo lectura, en un solo punto. Las consultas se adaptaron al dialecto (fechas, palabras reservadas y un `GROUP BY` que SQLite toleraba incompleto). Las pruebas pasan en 40 s en vez de 140 s y el pipeline completo tarda 16 s en vez de unos 4 minutos.
- **Operación:** el workflow semanal instala `requirements-pipeline.txt` (dbt-core, dbt-duckdb, pyarrow), corre el ETL de respaldo, luego `etl/pipeline.py`, luego las pruebas (con la paridad) y sube `datos.db` y `datos.duckdb`. El panel publicado solo agrega `duckdb`. En local, dbt corre en un entorno Python 3.12 aparte (`.venv-dbt`), porque aún no se instala en Python 3.14; GitHub Actions usa 3.11.
- **Historial:** `etl_run` conserva las cuatro cargas registradas; la construcción local de la migración no se publica como una carga nueva.

## D-155 · Precios reales con el IPC de alimentos del INE

- **Fecha:** 2026-10-19.
- **Paso 3 de la refonte (PRD «Evolución prevista»).**
- **Fuente:** dos archivos CSV oficiales del INE, leídos tal como se publican: la serie del IPC base 2023 = 100 (desde enero 2024) y la serie empalmada de divisiones (diciembre 2009 a diciembre 2023). Solo se usa la división 1, «Alimentos y bebidas no alcohólicas». `etl/ine.py` los descarga y los guarda en bronce (`bronze/ine_ipc`), con todas las columnas como texto.
- **Enlace de las series:** la serie empalmada está en otra base (salto de −33,7 % si se pegan sin más). Se enlaza con la variación mensual oficial de enero 2024 (+1,0 %): diciembre 2023 queda en el valor desde el cual enero 2024 sube exactamente lo publicado, y toda la serie anterior se escala por el mismo factor. Modelos dbt: `stg_ine__ipc_monthly`, `ipc_monthly`, `ipc_weekly`, y `ine_ipc_source` (las filas originales, para la auditoría).
- **Regla mes → semana:** cada semana toma el IPC del mes de su lunes (el mes de `dim_date`, RN-08). Precio real = nominal × IPC del último mes publicado ÷ IPC del mes de la semana: los precios reales quedan en pesos del último mes publicado. Una semana de un mes que el INE aún no publica usa ese último mes y queda marcada **provisional**; nunca se inventa un índice.
- **Panel:** Contexto agrega un control Nominal / Real. En Real, la serie, su rango habitual y su estado se calculan sobre precios reales; el precio nominal queda como línea gris fina detrás, y la nota indica el mes de referencia y las semanas provisionales. El precio de esta semana es el mismo en ambos modos (su factor es 1), así que no cambia ninguna cifra entre páginas; solo cambia con qué se compara.
- **Si el INE no responde:** la carga no se detiene. Se usa el bronce previo, o se reconstruye desde `ine_ipc_source` de la base publicada.
- **Auditoría:** `tests/test_ipc_audit.py` vuelve a enlazar las series y a calcular el factor de cada semana en Python, sin dbt, desde el texto publicado por el INE, con diferencia relativa < 10⁻¹². dbt prueba un solo IPC por mes.
- **Construcción local:** `python etl/pipeline.py --local` reconstruye la base sin registrar una carga nueva en `etl_run`.

## D-156 · Contexto: una sola búsqueda de producto

- **Fecha:** 2026-10-19.
- **Paso 5 de la refonte.**
- **Antes:** tres listas encadenadas (Familia, Producto, Calidad · unidad). Elegir un producto de otra familia pedía tres clics y la tercera lista no decía nada por sí sola.
- **Ahora:** un solo campo «Buscar producto» sobre los 332 productos con precio de feria o supermercado. Se escribe para filtrar, como en el Resumen. Cada opción se lee completa: «Tomate · Larga vida — Primera, kilo».
- **Por qué la calidad sigue visible:** 112 de los 193 productos tienen más de una calidad (Primera, Segunda), con precios distintos. Quitarla escondería datos, así que pasa a formar parte del nombre en lugar de ser una lista aparte.
- **La familia** queda en la ruta de navegación (Resumen › Hortalizas › …) y en el enlace de vuelta.
- **Fila del título:** la pregunta, la respuesta y la búsqueda en una línea; el control Nominal / Real (D-155) va en la cabecera del gráfico, donde actúa.

## D-157 · Ingeniería de datos en cuatro páginas, linaje dbt y documentos descargables

- **Fecha:** 2026-10-19.
- **Pasos 4, 6 y 7 de la refonte.**
- **Menú:** Dashboard (Resumen semanal, Contexto de precios) · Ingeniería de datos (Pipeline y linaje, Modelo de datos, Calidad y auditoría, Ejecuciones y DevOps) · Fuentes (ODEPA ×2 e INE) · Documentación (PRD, SAD, ADR, Escalabilidad). DevOps y seguridad se une a Ejecuciones como pestaña «Plataforma y seguridad»; su dirección antigua sigue funcionando.
- **Linaje leído, no dibujado a mano:** `etl/pipeline.py` copia el manifiesto y los resultados de la última construcción de dbt a la base servida (tablas `dbt_node` y `dbt_result`), porque `dbt/target` no se sube. Con ellas el panel dibuja el DAG (bronce → staging → intermedio → marts, cada modelo con sus pruebas superadas), la matriz «regla → pruebas dbt» de Calidad y auditoría y la insignia del pie de cada página. Un modelo o una prueba nueva aparece sola en la carga siguiente.
- **Calidad y auditoría:** dos evidencias nuevas, el resultado de las pruebas dbt y la paridad SQLite ↔ DuckDB (precios, rechazos y suma de precios), comprobada en vivo. La fila que hablaba de SQLite describe ahora la base DuckDB.
- **Diagramas:** el recorrido por capas, la plataforma DevOps y sus variantes describen la pila entregada: aterrizaje SQLite, bronce Parquet, dbt, DuckDB y el IPC del INE como segunda fuente.
- **Documentos:** PRD, SAD (C4) y ADR reescritos sobre la arquitectura entregada (ADR-30 aceptada; ADR-33, regla del deflactor; ADR-34, almacén de trabajo, base servida y respaldo con paridad). Cada uno se descarga en PDF con portada, índice y paginación (`bi/document_pdf.py`, reportlab), generado desde el mismo Markdown que muestra el panel y GitHub.
- **Escalabilidad:** página propia con la sección del SAD: clima previsto; nube solo con datos de una empresa (ADR-31), con los umbrales que la justificarían. Sin cifras inventadas.
- **Fuentes:** el INE se suma a la barra lateral y a la atribución del pie.

## D-158 · Una alerta necesita al menos dos cotizaciones en cada semana

- **Fecha:** 2026-10-19.
- **Problema:** el Resumen deja fuera de su tabla los cambios que descansan en una sola cotización en alguna de las dos semanas (D-146): un precio aislado no es un movimiento de mercado. La regla K6 no aplicaba ese filtro: 9 de las 22 alertas de la semana del 05-10-2026 descansaban en un solo precio. Esas filas sí estaban en la tabla de su familia, pero al final del orden con la marca «1 cotización», lejos de donde se las buscaba, y faltaban en el ranking de movimientos. Ejemplo que lo reveló: Pimiento Zafiro verde · Primera · Supermercado en Línea, +11,9 % con un solo precio en cada semana.
- **Decisión:** una alerta K6 es inusual (2 desviaciones), material (cambio ≥ 10 %) **y** descansa en al menos 2 cotizaciones en cada una de las dos semanas comparadas, contadas sobre las mismas regiones (D-144). Se aplica igual en `bi/alerts.py` y en su versión SQL (`k6_usual_range_sql`), que la prueba de D-049 sigue comparando. El rango habitual se sigue calculando con todas las variaciones; solo el juicio de la semana exige dos cotizaciones.
- **Resultado:** 13 alertas en la semana del 05-10-2026 (Hortalizas 6, Frutas 5, Carne de Cerdo - Ave - Cordero 2), y cada una aparece en el ranking y en la parte principal de la tabla de su familia.
- **Nota de cobertura del Resumen:** habla ahora de la familia que muestra la tabla (por ejemplo, Hortalizas: 322 precios esta semana, 288 con comparación válida, los de la tabla) y después de toda la semana (787 precios, 59 sin comparación válida). Antes mostraba solo el total de las siete familias bajo una tabla de una familia, y «288 precios» arriba parecía contradecir «787 precios» abajo. La fotografía de cifras de D-153 se actualiza solo en ese número.

## D-159 · Contexto de precios se explica solo, y dice cuándo la inflación cambia la respuesta

- **Fecha:** 2026-10-19.
- **Problema:** la página no se entendía a simple vista: la banda del gráfico solo se explicaba en un ícono ⓘ, el selector «Nominal / Real» no decía qué cambiaba y el aporte del IPC (D-155) pasaba desapercibido, aun cuando cambiaba la respuesta.
- **Decisión:** una línea de lectura bajo el título del gráfico («Línea: precio de cada semana · Banda: lo habitual en esa misma semana de años anteriores…»); el selector pasa a «Precios del día / Sin inflación», con una ayuda que nombra el IPC del INE; y una frase marcada «IPC» bajo la respuesta cuando, para algún canal, el estado (bajo, dentro o sobre lo habitual) es distinto con y sin inflación. Ejemplo real: el tomate larga vida en supermercado está sobre lo habitual con los precios del día y bajo lo habitual descontada la inflación de alimentos, porque subió menos que ella. Si la inflación no cambia nada, no se muestra.

## D-160 · El IPC de alimentos tiene su propio gráfico

- **Fecha:** 2026-10-19.
- **Problema:** el IPC del INE estaba en los datos (D-155) y en la frase de Contexto (D-159), pero ningún gráfico mostraba el índice mismo: no se podía ver cuánto subieron los alimentos ni con qué serie se calculan los precios sin inflación.
- **Decisión:** en Contexto de precios, «Ver el IPC →» abre la serie mensual del INE (división 1, base 2023 = 100) desde enero 2022, cuando empiezan los precios. Muestra la inflación acumulada del período y la de los últimos 12 meses, calculadas de la misma tabla `ipc_monthly` que usa el deflactor, y explica la regla mes → semana, el mes de referencia y el enlace de la serie empalmada. Sin área bajo la curva: anclaría el eje en 0 y aplanaría la subida.
- **Cifras al 19-10-2026:** de enero 2022 a septiembre 2026 los alimentos subieron +44,8 %; en los últimos 12 meses, +4,3 %.

## D-161 · Cuánto de una subida es inflación; meses completos en el eje; la tabla final no son las alertas

- **Fecha:** 2026-10-19.
- **Subida separada:** en «Precio esta semana», cada canal muestra cuánto cambió el precio desde la misma semana del año pasado y cómo se reparte: la parte que equivale a la inflación de alimentos (lo que habría subido el precio de entonces con el IPC del INE) y la parte propia del producto, con una barra de dos colores. Ejemplo real, tomate larga vida: en feria libre +$298 = inflación +$48 · propio +$250; en supermercado +$38 = inflación +$74 · propio −$37. Es una cuenta, no una causa, y lo dice la ayuda. Se mide sobre 12 meses porque de una semana a otra la inflación es despreciable.
- **Eje del gráfico:** cada mes lleva su etiqueta (nov 2025, dic, ene 2026 … oct). Antes solo aparecían «ene, abr, jul, oct» y la ventana de 52 semanas, de octubre a octubre, se leía como si empezara en enero y faltaran meses.
- **Tabla final de Contexto:** se titula «… con precio fuera de lo habitual para la época» y aclara que no son las alertas: una alerta (K6) es un cambio brusco de una semana a otra; esta tabla, un precio alto o bajo para esta época del año.

## D-162 · Consultas SQL sobre la capa oro, y el consumo del pipeline completo

- **Fecha:** 2026-10-19.
- **Problema:** el diagrama del pipeline mostraba «Consultas SQL» como un consumo de la capa oro, pero no había dónde consultar: su enlace no tenía flujo y nadie podía cruzar los datos. Para eso existe una capa oro.
- **Decisión:** página «Consultas SQL» en el Dashboard (`bi/sql_explorer.py`). Se escribe SQL de DuckDB sobre vistas con nombres legibles, sin ningún identificador: `precios`, `semanas`, `productos`, `ipc_semanal`, `ipc_mensual`, `cargas`, `rechazos`, `modelos_dbt`. Ocho ejemplos responden preguntas reales con cruces: margen por región, mayores subidas sobre regiones comunes, precio real frente a nominal con el IPC, evolución anual por familia, regiones más caras, rechazos por motivo, cobertura semanal y pruebas de dbt. El resultado se descarga en CSV (abre en Excel) o Parquet, y las tablas principales en CSV, para llevarlas a otra herramienta como Power BI o Excel.
- **Por qué no repite D-143:** aquella consola mostraba identificadores sin sentido y duplicaba el código de GitHub. Esta trabaja sobre vistas legibles y responde preguntas de negocio que el panel no muestra.
- **Seguridad:** cada consulta abre una conexión nueva de solo lectura, sin acceso a archivos ni a la red, con la configuración bloqueada y 1 GB de memoria. Solo se admite una sentencia SELECT (o WITH, DESCRIBE, SHOW, SUMMARIZE), envuelta con un límite de 5.000 filas y cortada a los 10 segundos.
- **Diagrama:** el enlace de la capa oro a «Consultas SQL» fluye como los demás, con la etiqueta «consultas», y su explicación nombra la página.
- **Fuera de alcance:** machine learning y modelos predictivos (D-019): con datos semanales públicos y sin una pregunta de predicción, no aportan.
- **requirements.txt:** `streamlit>=1.65`, porque las descargas usan funciones de esa versión.

## D-163 · «Precios e inflación»: una pregunta grande en vez de una página por producto

- **Fecha:** 2026-10-19.
- **Problema:** «Contexto de precios» reunía demasiado (banda habitual, tarjetas, próximos meses, tablas de datos, tabla de productos fuera de lo habitual) y nadie sabía por dónde empezar. Mostraba 52 semanas «de noviembre a octubre» sin explicar por qué, y lo individual ya está en el Resumen.
- **Decisión:** la página pasa a llamarse «Precios e inflación» y responde una sola pregunta: ¿qué alimentos subieron más que la inflación? Arriba, un gráfico con el índice mensual de cada familia (enero 2022 = 100, mediana de sus series de consumidor) frente al IPC de alimentos del INE, y al lado un ranking: cambio desde enero 2022, cambio en 12 meses y si subió más, menos o al ritmo de la inflación. Un solo selector, «Precios del día / Sin inflación», divide cada índice por el IPC: la canasta del INE queda en 100 y lo que está arriba subió más. Abajo, un buscador de producto con toda su historia semanal (enero 2022 a hoy), un gráfico por canal y la frase de los 12 meses separados en inflación y parte propia (D-161).
- **Cómo se calcula:** una serie cuenta solo si tiene precio en enero 2022 y en el último mes del IPC, para comparar siempre los mismos productos (409 series). El índice de una familia es la mediana de los índices de sus series. Todo son datos históricos reales, sin regresión ni predicción.
- **Resultado al 19-10-2026:** el IPC de alimentos subió +44,8 %. Subieron más: Lácteos, Huevos y Margarinas (+70,8 %), Hortalizas (+60,2 %) y Pan (+50,8 %). Menos: Abarrotes (+40,5 %), Frutas (+37,7 %), Carne bovina (+37,2 %) y Cerdo, Ave y Cordero (+30,7 %).
- **Límite dicho en la página:** el IPC de alimentos se calcula con precios de alimentos; subir con él no prueba que la inflación cause la subida de una familia.
- **Retirado:** la banda de lo habitual, las tarjetas de precio, margen y próximos meses, la tabla de productos fuera de lo habitual, y los diálogos de datos y de serie completa (la serie completa se ve de entrada). El código de los indicadores K4 sigue en el proyecto.

## D-164 · La descarga de ODEPA confía en la raíz emSign que certifi retiró

- **Fecha:** 2026-10-19.
- **Problema:** la ejecución manual del 19-10-2026 falló en «Download the ODEPA files» con `CERTIFICATE_VERIFY_FAILED`. El certificado de datos.odepa.gob.cl lo emite «emSign SSL CA - G1», que depende de la raíz «emSign Root CA - G1». La versión 2026.10.18 de certifi, la lista de raíces que usa Python, retiró las raíces emSign; la 2026.7.22 las tenía. GitHub Actions instala la última versión, así que la ejecución automática del martes habría fallado igual.
- **Decisión:** la raíz «emSign Root CA - G1» se guarda en `agent/certs/emsign_root_ca_g1.pem` y el agente la agrega a las raíces de certifi solo para sus descargas. El certificado de ODEPA se sigue verificando completo; nunca se desactiva la verificación (`verify=False`). Huella SHA-256 `40:F6:AF:03:46:A9:9A:A1:CD:1D:55:5A:4E:9C:CE:62:C7:F9:63:46:03:EE:40:66:15:83:3D:C8:C8:D0:03:67`, la misma en certifi 2026.7.22 y en el almacén de certificados de Ubuntu.
- **Por qué no fijar certifi a una versión antigua:** dejaría desactualizadas las raíces de todas las conexiones (GitHub, INE), no solo la de ODEPA.
- **Revisar:** cuando ODEPA cambie de emisor, este archivo deja de hacer falta y se retira.

## D-165 · Centro de operación: el recorrido del martes es su propia guía

- **Fecha:** 2026-10-19.
- **Problema:** la ejecución del 19-10 falló dos veces y encontrar la causa obligó a saltar entre el panel, GitHub Actions, los logs y la configuración de Streamlit. «Ejecuciones y DevOps» mostraba una tabla de ejecuciones y una lista de pasos a la que le faltaban la limpieza y dbt: sus nombres habían cambiado en `semanal.yml` (D-154).
- **Decisión:** la página pasa a llamarse «Centro de operación». El recorrido de cada martes se dibuja como nueve logos flotantes sobre una serpentina de tres filas: «Lanzar y descargar» (Lanzar, ODEPA, IPC del INE), «Transformar y probar» (Limpieza, dbt, Pruebas) y «Publicar» (Guardar, Informe, Panel). La luz bajo cada logo es el estado de su paso en la última ejecución: verde, rojo, azul que late (en curso) o gris (no corrió).
- **El recorrido es la guía:** no hay textos fijos. Al pasar el cursor, cada paso dice qué hace y da sus enlaces: el log de ese paso en GitHub, abierto en su línea exacta (`#step:N:1`), y lo que corresponde (fuentes de ODEPA, sitio del INE, commits, informes). El logo abre el log. El paso que falló, o el que está en curso, deja su explicación abierta.
- **Al lado:** próxima ejecución, semana publicada, última carga, el botón «Ejecutar pipeline ahora» y las últimas ejecuciones con su enlace.
- **Mientras corre una ejecución** la página vuelve a preguntar a GitHub cada 15 segundos con clave, o cada 60 sin ella (GitHub permite 60 consultas por hora sin clave).
- **Enlaces del autor:** los tokens de GitHub y la administración de la app en Streamlit solo aparecen después de escribir la clave de control.
- **El IPC** no tiene paso propio en el workflow: se prepara al comienzo del paso de dbt (`etl/pipeline.py`), así que su logo toma ese estado.
- **Lo que no se puede:** el texto de los logs no se lee dentro del panel. GitHub lo entrega recién al terminar la ejecución, y Streamlit no expone los suyos. Por eso cada paso lleva el enlace directo.
- **Los cuatro temas:** el dibujo toma los colores de cada uno. Va en su propio marco (`st.iframe`), como la página GitHub, porque st.html quita los degradados y las explicaciones al pasar el cursor.
- **Ajuste del mismo día:** la página cabe en una pantalla. Las últimas ejecuciones pasan debajo del recorrido, en una franja, y la ejecución manual queda compacta junto a las cifras: botón redondo con su nombre al lado y «Recargar datos» debajo. Antes, la columna derecha bajaba mucho más que el dibujo y dejaba un vacío grande a la izquierda. «Run workflow» se suma a los enlaces del autor, como en la administración (T-54).
- **«Volver» abre la cabecera de cada página, junto a la ruta:** en la app publicada, Streamlit Cloud dibuja su propia barra (Share, estrella, editar, GitHub) en la esquina superior derecha, encima de donde estaba «Volver».
- **Accesos del autor:** junto a «Recargar datos», un botón con candado abre, con la clave de control, los enlaces del autor: administrar la app en Streamlit (reinicio, secretos, registros), lanzar el workflow, crear un token y ver los tokens. Antes solo se veían después de ejecutar el pipeline.
- **Si GitHub no responde,** el aviso nombra el tipo de error y el detalle queda en el registro del servidor («Manage app» en Streamlit Cloud).

## D-166 · El panel se lee en horizontal en los teléfonos

- **Fecha:** 2026-10-19.
- **Problema:** en un teléfono en vertical el panel se apila en una columna larga y se pierde la vista de conjunto.
- **Decisión:** un teléfono en vertical (600 px de ancho o menos) ve una sola pantalla con el logo de GreenOcean, un teléfono que gira y «Gira tu teléfono». Ninguna página puede girar el teléfono; solo el lector, y el aviso desaparece solo al girar. Sin texto sobre el bloqueo de rotación: el público del panel sabe girar un teléfono.
- **En horizontal** (500 px de alto o menos) el panel se dibuja con el ancho de un computador y se reduce al de la pantalla: menú, pipeline e información a la vista, sin franja vacía arriba. Si el menú se plegó al abrir en vertical, se vuelve a abrir al girar.
- **Tablets y computadores** no cambian.
- **Límite:** las páginas con reglas propias para pantallas estrechas, como el Resumen, siguen viendo 844 px de ancho y conservan esas reglas. Todo cabe, pero algunas tarjetas van de dos en dos.

## D-167 · Precios e inflación: un gráfico por familia

- **Fecha:** 2026-10-19.
- **Problema:** las siete familias y el IPC en un solo gráfico se cruzaban y no se leían; el ranking de al lado repetía las cifras, y la historia semanal de un producto, debajo, no respondía la pregunta de la página.
- **Decisión:** un gráfico pequeño por familia, todos del mismo tamaño y con la misma escala, en una cuadrícula de cuatro columnas, ordenados de la que más subió sobre el IPC a la que menos. Cada uno lleva su línea frente al IPC de alimentos punteado, y su título dice la subida desde enero 2022 y el veredicto (más, menos o al ritmo de la inflación). La frase de arriba suma la inflación de 12 meses. El interruptor «Precios del día / Sin inflación» sigue igual.
- **Retirado:** el ranking lateral y la sección «toda su historia» de un producto, con su frase de inflación y parte propia (D-161; el cálculo `split_yearly_change` queda en el código, con su prueba). Con ella se van el botón «Ver contexto» y la flecha de cada fila de la tabla de productos del Resumen, que solo llevaban a esa sección.

## D-168 · Consultas SQL como un cliente SQL

- **Fecha:** 2026-10-19.
- **Problema:** la página apilaba un párrafo de explicación, un desplegable de tablas, los ejemplos en dos filas de botones grandes, el editor y, debajo, una sección de descargas: mucho desplazamiento para escribir una consulta.
- **Decisión:** la página se organiza como un cliente SQL simple. Arriba, los ejemplos como etiquetas en una sola fila. A la izquierda, la lista de tablas: cada nombre, con sus filas y columnas, y al pasar el cursor su descripción; un clic escribe `SELECT * FROM tabla LIMIT 100`. A la derecha, el editor con «Ejecutar» y el resultado debajo, con sus descargas en CSV y Parquet en la misma línea. Las tablas gold completas se descargan desde un botón «Descargar tablas», sin ocupar la página.

## D-169 · La alerta de precio vive arriba del Resumen

- **Fecha:** 2026-10-19.
- **Decisión:** el botón «▲ Alerta de precio · N» deja el menú lateral (D-096, D-128) y pasa a la esquina superior derecha del Resumen semanal, sobre la fecha de actualización, con el mismo diálogo por familia. La alerta es una cifra de la semana: va con las demás cifras de la semana, no con la navegación. Las otras páginas ya no cargan la hoja de estilos del diálogo (D-100).

## D-170 · Acabado tipográfico: pesos finos y botones de píldora

- **Fecha:** 2026-10-19.
- **Problema:** el panel abusaba de la negrita (pesos 650 a 800 en títulos, cifras, etiquetas y píldoras), y el conjunto se veía pesado frente a la referencia del autor: la tipografía de apple.com, fina y con aire.
- **Decisión:** un solo acabado tipográfico para todas las páginas. Los títulos pasan a peso 500 con interletrado negativo; las cifras grandes a 500; las negritas del texto a 600; las etiquetas en mayúsculas a 500 con interletrado amplio; el cuerpo queda en 400. Los botones y los desplegables toman la forma de píldora, con texto en peso normal. La fuente del panel sigue siendo la del sistema (San Francisco en Apple, Segoe UI en Windows), y los gráficos y diagramas SVG usan ahora la misma en vez de Source Sans Pro. Las páginas en su propio marco (GitHub, Centro de operación) llevan los mismos pesos.
- **Dónde:** `bi/premium.css` concentra las reglas compartidas; los pesos 650–800 de `bi/dashboard.py`, `bi/home_mockup.css`, `bi/quality_view.py`, `bi/github_page.py`, `bi/operation_center.py` y `bi/sql_explorer.py` bajan a 500–600.

## D-171 · Calidad y auditoría: cada tarjeta abre su evidencia

- **Fecha:** 2026-10-19.
- **Problema:** la página era una lámina fija. Mostraba que los datos se comprueban, pero no dejaba ver con qué ni volver a comprobar; el detalle estaba plegado en tres pestañas al final, y no se entendía su objetivo.
- **Decisión:** la página dice su objetivo (que cada cifra publicada se pueda recomprobar) y cada tarjeta se abre. Bajo el tablero, una fila de píldoras con las once tarjetas; elegir una abre un diálogo con qué comprueba, los datos que lo respaldan como tabla y el método: la consulta SQL que corre, o el enlace a la prueba automática en el repositorio y a su último resultado en GitHub Actions. «Volver a comprobar» descarta lo guardado y corre los controles de nuevo, con la hora.
- **Evidencia por tarjeta:** el manifiesto de descargas; las huellas SHA-256 registradas y calculadas (en Streamlit Cloud no hay CSV, y así se dice); las semanas cubiertas y las que faltan; las ejecuciones de `etl_run` con las filas excluidas y su motivo; las reglas del PRD y cada prueba de dbt con su estado; las tres comprobaciones de la base con su SQL; la paridad SQLite ↔ DuckDB cifra por cifra; y, para las auditorías automáticas, sus archivos de prueba. El contraste con otra fuente sigue pendiente y explica por qué.
- **Código:** `bi/quality_evidence.py` prepara las tablas; `bi/quality.py` expone las consultas que ya corría, para que el diálogo muestre exactamente lo que se ejecuta. Las tres pestañas plegadas desaparecen: su contenido vive en los diálogos.

## D-172 · El panel recarga solo los módulos que cambiaron

- **Fecha:** 2026-10-19.
- **Problema:** tras un push, Streamlit Cloud mostraba el menú nuevo con páginas viejas: recarga `bi/dashboard.py` en cada ejecución, pero conserva en memoria los módulos importados (`bi/sql_explorer.py`, `bi/inflation_view.py`…) hasta que alguien reinicia la app. Es la misma trampa anotada para el panel local.
- **Decisión:** en cada ejecución, el panel compara la fecha de cada módulo `bi/*` cargado con la que tenía al importarlo y recarga los que cambiaron, primero los que no dependen de otros. Un push se ve sin reiniciar. La recarga puntual de `home_mockup` en el Resumen sigue siendo válida y queda cubierta por esta regla general.
- **Corrección (mismo día):** la primera versión guardaba las fechas en una variable de `bi/dashboard.py`, y Streamlit vuelve a ejecutar ese archivo desde cero en cada ejecución, así que la lista empezaba vacía cada vez y nunca detectaba un cambio. Las fechas viven ahora en el paquete `bi`, que sí permanece en memoria. El vigilante de archivos de Streamlit sigue apagado (`fileWatcherType = "none"` en `.streamlit/config.toml`): esta regla es la única que recarga módulos, en local y en Streamlit Cloud.

## D-173 · Consultas SQL como un estudio SQL

- **Fecha:** 2026-10-19.
- **Problema:** el cliente simple de D-168 seguía siendo una lista de botones y un cuadro de texto. El autor pidió la disposición de SQL Server Management Studio —explorador de objetos, editor con números de línea y colores, Ejecutar, pestañas Resultados y Mensajes, barra de estado— en una versión premium, moderna y con relieve.
- **Decisión:** la página es un solo panel elevado. Arriba, la barra de herramientas: la conexión (`datos.duckdb`, DuckDB y su versión, solo lectura), el botón «Ejecutar» y los ejemplos como etiquetas. A la izquierda, el explorador de objetos: la base, la carpeta «Vistas» y cada vista con su ícono, sus filas y columnas, y su descripción al pasar el cursor; un clic escribe `SELECT * FROM vista LIMIT 100`. A la derecha, la pestaña `consulta.sql` con la pregunta del ejemplo, el editor con números de línea y colores (palabras clave, funciones, cadenas, números y comentarios, como en SSMS), y debajo las pestañas «Resultados» (la grilla con filas numeradas desde 1, y CSV y Parquet) y «Mensajes» («(N filas afectadas) · Consulta ejecutada correctamente · tiempo»). Abajo, la barra de estado: el veredicto, el motor, solo lectura, la base, el tiempo en hh:mm:ss.mmm y las filas. Ctrl + Enter ejecuta.
- **Cómo se pintan los colores:** el cuadro de texto de Streamlit no colorea. Un script dibuja detrás de él una capa con los mismos márgenes, fuente y desplazamiento, y la repinta en cada tecla; el texto del cuadro se vuelve transparente solo cuando la capa está activa, así que sin JavaScript el editor sigue siendo legible. Las reglas de CLAUDE.md se respetan: un solo script, sin etiquetas HTML en su texto, el DOM con `createElement`, y ningún nodo de Streamlit movido ni borrado.
- **Relieve:** el panel, la barra, las etiquetas y el botón se iluminan desde arriba (degradados y sombras en capas); el editor y los mensajes van hundidos. Las cuatro paletas tienen sus propios colores de código.
- **Trampa anotada:** el contenedor de `st.markdown` lleva un margen inferior de −1 rem que compensa el margen del párrafo final. Un bloque que termina en `div` no tiene ese margen y el elemento siguiente se le monta encima; dentro del estudio ese margen se anula.

## D-174 · Precios e inflación: una carta por familia

- **Fecha:** 2026-10-19.
- **Problema:** la cuadrícula de D-167 era un solo gráfico facetado: títulos en negrita, sin separación entre paneles y sin el acabado del resto del panel. El autor pidió cada gráfico como una carta elegante, casi en 3D, y letras finas como en la referencia de Apple.
- **Decisión:** una carta elevada por familia, cuatro por fila, con el mismo tamaño de gráfico y la misma escala vertical en todas (el rango se calcula una vez sobre todas las series y se comparte). El nombre de la familia va en peso 500 y, debajo, la subida y el veredicto en el color de la familia, en peso normal. La octava carta es el propio IPC de alimentos del INE: la canasta de referencia, con su subida, para que la cuadrícula quede completa y la referencia tenga su lugar. Las cartas se levantan al pasar el cursor. El título de la página y las negritas de la frase bajan a peso 500.
- **Código:** `inflation_view.draw_family_card` dibuja una familia frente al IPC (o el IPC solo) y `family_domain` fija la escala común; `draw_family_grid` desaparece.

## D-175 · La fuente del sistema, en pesos finos

- **Fecha:** 2026-10-19.
- **Problema:** después de D-170 el autor seguía viendo la letra gruesa y redonda frente a la referencia de Apple. La causa no eran los pesos: Streamlit escribe cada elemento con su propia Source Sans, y la familia declarada en `premium.css` no la alcanzaba. Además los títulos de los gráficos de inflación venían en negrita de Altair.
- **Decisión:** la fuente se fija en el tema de Streamlit (`.streamlit/config.toml`): la del sistema para texto y títulos —San Francisco en Apple, Segoe UI en Windows— y una pila monoespaciada para el código. Es la misma elección de apple.com y no descarga nada. Los títulos de página bajan a peso 400; las negritas del texto a 500. En Precios e inflación, la frase de respuesta y la lectura de la cuadrícula van en peso 300 y gris, como las notas de Apple; los nombres de familia en 400. Los enlaces de «Fuentes» del menú toman el mismo tamaño y peso que los demás.
- **Nota:** los pesos finos se ven en Mac y Windows; en un Linux sin esas fuentes el navegador usa Helvetica o Arial, un poco más anchas.

## D-176 · Calidad y auditoría cuenta la historia con un método: las seis dimensiones del DAMA-DMBOK

- **Fecha:** 2026-10-19.
- **Problema:** la página mostraba once tarjetas de controles, pero no contaba cómo se gestionó la calidad: ni la secuencia, ni las medidas, ni el método. El autor pidió una sola vista que lo explique de forma progresiva, con cada componente explicando su rol al pasar el cursor, y un método estándar que dé nombre a lo que se hace.
- **Método elegido:** las seis dimensiones de calidad de datos del DAMA-DMBOK (completitud, unicidad, validez, consistencia, exactitud y actualidad), el marco más extendido en ingeniería de datos, aplicadas a lo largo del pipeline con el ciclo prevenir → detectar → aislar → verificar → publicar. Cada dimensión se califica con la evidencia real (cumplida, pendiente o con falla) y, al pasar el cursor, dice qué significa y qué controles de este proyecto la miden.
- **La vista:** arriba, la franja del método con las seis dimensiones. Luego cuatro etapas en tarjetas elevadas —01 Fuentes (archivos identificados), 02 Transformación (reglas de calidad), 03 Warehouse (consistencia de la base), 04 Resultados (cálculos contrastados)—, cada una con su ilustración, su cifra real, su veredicto y, en pequeño, los controles que corre (las once tarjetas anteriores, ahora ilustraciones con su explicación al pasar el cursor). Al pasar el cursor por una etapa se lee su rol en la calidad. Bajo las etapas, el aviso de anomalías con los rechazos registrados, unido a la etapa 02 (aislar, no corregir: la fila que no cumple una regla se aparta con su motivo). Al pie, la barra de veredicto, que dice lo pendiente y recuerda que no hay segunda fuente oficial.
- **Se mantiene:** cada control abre su evidencia desde las píldoras (D-171), con sus datos, su método y «Volver a comprobar». Ninguna cifra nueva: todas salen de la misma evidencia; la cuenta de rechazos se lee de la tabla `rejection`.
- **Cómo se dibuja:** un solo bloque HTML con CSS, sin script; las explicaciones son tooltips CSS, y el elemento bajo el cursor sube de capa para que ningún vecino lo tape.

## D-177 · Ampliar una carta de inflación, con aire

- **Fecha:** 2026-10-19.
- **Problema:** el botón de pantalla completa que Streamlit pone sobre cada gráfico dejaba la carta en negro, porque los gráficos se ajustan al ancho de su carta. Además la frase y la lectura quedaban pegadas a las cartas.
- **Decisión:** se oculta esa barra de herramientas en las cartas y cada una lleva su botón «Ampliar»: muestra solo esa familia, grande y con la misma escala, y «Ver todas» vuelve a la cuadrícula. Los márgenes entre la frase, la lectura y las cartas suben, y los botones nuevos usan el peso fino de D-170.

## D-178 · Ejemplos de SQL que responden preguntas de gestión, por familia y producto

- **Fecha:** 2026-10-19.
- **Problema:** los ocho ejemplos describían (márgenes, rankings de una semana) pero no permitían concluir qué tiende a subir, y no seguían la unidad con que trabaja el panel: la familia.
- **Decisión:** ocho ejemplos nuevos. Por familia: cuál subió y cuál bajó más la última semana; evolución anual; brecha mayorista-consumidor (solo Frutas y Hortalizas tienen mayorista); regiones más caras. Por producto: los de más alzas que bajas en 2026 (probabilidad de subir de una semana a otra); los 100 que más subieron en 2026; los que subieron más que el IPC desde 2022; los más volátiles. Los años se cambian editando la consulta. Todos usan solo precios válidos, comparan semanas consecutivas de la misma serie y corren en menos de un segundo; las pruebas los ejecutan.
- **Límite dicho:** la mejor probabilidad de alza de 2026 ronda el 57 %: la mayoría de los productos sube y baja casi por igual de una semana a otra, y la consulta lo muestra en vez de ocultarlo.

## D-179 · Dos ejemplos para consultar un producto, sin importar su familia

- **Fecha:** 2026-10-19.
- **Decisión:** a los ocho ejemplos por familia de D-178 se suman dos que parten de un producto: «Ficha de un producto» (precio por canal de las últimas 4 semanas y de hace un año, alza en 12 meses y probabilidad de subir en 2026) e «Historia de un producto» (precio semanal nominal y real frente al IPC). El producto se elige editando la primera línea de la consulta; el nombre se busca por su inicio (por ejemplo «Asado», «Tomate», «Papa»), para que «Asado» no traiga «Pan amasado». Quedan diez ejemplos.

## D-180 · Un clic escribe y ejecuta la consulta, con producto, canal y año elegidos

- **Fecha:** 2026-10-19.
- **Problema:** para consultar otro producto u otro año había que editar el SQL a mano; un usuario de negocio no lo hace.
- **Decisión:** los diez ejemplos son plantillas con parámetros. Al elegir uno, el panel escribe en el editor el SQL completo, con sus alias y comentarios y con los valores ya puestos, y lo ejecuta: la respuesta y el código que la da aparecen juntos. Los ejemplos con parámetros muestran sobre el editor una fila «Parámetros» (como la de plantillas de SQL Server) con año, producto y canal; cambiar un valor vuelve a escribir y ejecutar la consulta. El canal ofrece solo los canales donde se vende el producto elegido. La vista del estudio (D-173) no cambia.
- **Diez preguntas:** familias de la semana; más alzas que bajas del año; los 100 que más subieron; sobre la inflación desde 2022; ficha de un producto; historia de un producto; evolución anual por familia; brecha mayorista-consumidor; productos más volátiles; regiones más caras por familia. La historia de un producto sigue una sola serie (la variedad, calidad y unidad con más precios) para no mezclar presentaciones.
- **Seguridad:** los valores vienen de listas leídas de la base y se escriben como literales SQL escapados; la consulta pasa por la misma validación de solo lectura de siempre.

## D-181 · Cinco preguntas para decidir; el resto, en el editor

- **Fecha:** 2026-10-19.
- **Criterio:** cada pregunta de ejemplo debe tener al menos 8 sobre 10 en pertinencia para tomar una decisión. Quedan las cinco mejor calificadas; quien quiera ir más lejos escribe su propia consulta sobre las vistas del explorador.
- **Las cinco:** «¿Está caro para la época?» (comprar ahora o esperar: compara las últimas 4 semanas con las mismas semanas de los años anteriores y da un veredicto); «Más que la inflación este año» (alza de cada producto en el año elegido frente al IPC de alimentos de las mismas fechas); «Sobre la inflación desde 2022»; «Ficha de un producto»; «Más alzas que bajas del año».
- **Rigor:** la comparación de época se hace en pesos reales (precio × factor_real). En pesos nominales, con un 45 % de inflación desde 2022, todo lo actual parecía «más caro que nunca». El veredicto tiene cinco niveles: más caro o más barato que cualquier año anterior, caro o barato (más de 10 % sobre o bajo el promedio) y normal. Con tres o cuatro años de historia, la época es orientativa.
- **Salen:** historia de un producto, los 100 que más subieron, evolución anual por familia, brecha mayorista-consumidor, productos más volátiles, regiones más caras y familias de la semana. La etiqueta «Ejemplos» pasa a «Preguntas».

## D-182 · El explorador muestra las tablas reales; la cabecera, nombres cortos

- **Fecha:** 2026-10-19.
- **Decisión:** como en SQL Server, el explorador de objetos muestra primero la carpeta «Tablas» con las tablas reales del data warehouse (`main.weekly_price`, `main.dim_product`, `main.dim_region`, …), leídas de `information_schema` con sus filas y columnas; un clic corre «SELECT * … LIMIT 100» sobre la tabla, con sus claves internas visibles. Debajo, la carpeta «Vistas» con las vistas de análisis de columnas legibles sobre las que corren las preguntas. Esto deja atrás, solo para el explorador, la regla de D-143 de no mostrar claves internas: quien abre una tabla real ve su estructura real.
- **Cabecera:** las preguntas toman nombres cortos (Precio vs. época, Inflación del año, Inflación desde 2022, Ficha de producto, Tendencia al alza). La pestaña del editor lleva el nombre de archivo de la consulta (por ejemplo `precio_vs_epoca.sql`) y un ícono «i» que, al pasar el cursor, muestra la pregunta completa; el texto largo ya no ocupa la cabecera.

## D-183 · Editor y resultados comparten la altura

- **Fecha:** 2026-10-19.
- **Decisión:** el editor y la grilla de resultados suman siempre la misma altura. Una consulta corta, como abrir una tabla, deja su espacio a las filas en vez de dejar un hueco bajo los resultados; una consulta larga conserva al menos 250 px de resultados. Si hay pocas filas, la grilla mide lo que ellas necesitan.

## D-184 · «Consultas», no «Preguntas», y en su propia fila

- **Fecha:** 2026-10-20.
- **Decisión:** en el estudio SQL, la fila de ejemplos se llama «Consultas», el término técnico del proyecto; «preguntas» queda para las preguntas de negocio del PRD. Las cinco consultas van en una fila propia, bajo la conexión y «Ejecutar», para que ninguna quede escondida en una segunda línea. El manual deja de nombrar la antigua sección «Preguntas y resultados SQL».

## D-185 · Primero la tabla completa; después cinco consultas elegidas por un consejo

- **Fecha:** 2026-10-20.
- **Problema:** el estudio partía de consultas sobre un producto (el tomate por defecto) en vez de partir del conjunto. En ingeniería de datos se parte de la tabla completa y luego se filtra y se especializa.
- **Decisión:** la primera consulta es «Tabla completa»: todos los precios semanales con familia, producto, variedad, calidad, canal, fuente, región, unidad, precio, precio real (cruce con el IPC de alimentos), índice IPC y marca de calidad. Sobre el editor, cinco filtros (familia, producto, canal, región y año, cada uno con «Todas»); el producto se acota por la familia y el canal por el producto. Cada filtro escribe su línea en el WHERE del SQL visible. Muestra las 5.000 semanas más recientes; el resto se alcanza filtrando.
- **Las cinco consultas:** las eligió un consejo de tres revisores independientes (perspectiva de política pública y consumidor, de analista de datos y de compras y precios), que calificaron quince candidatas de 1 a 10 por su utilidad para decidir. Quedaron: Precio vs. época (promedio 9,3), Canal más barato (9,0), Inflación vs IPC con período año o desde 2022 (8,3), Brecha mayorista (7,3) y Calendario de compra (propuesta nueva de dos de los tres). Salen la ficha de producto (la cubre la tabla completa) y la tendencia al alza: los tres revisores la calificaron con 3, porque una probabilidad de 50 a 57 % no se distingue del azar.
- **Reglas de rigor del consejo, aplicadas:** toda comparación se hace dentro de la misma serie (producto, variedad, calidad, canal, unidad y región) y luego se resume con la mediana, para que la mezcla de productos o regiones no sesgue el resultado; lo que compara tiempos usa pesos reales; la inflación se mide en las mismas dos semanas que el precio de cada serie; la brecha mayorista se rotula como brecha y no como margen, porque no incluye costos. Cada consulta de decisión termina con una columna «lectura» en palabras o con el ahorro.
- **Una sola base:** el explorador y todas las consultas leen `etl/datos.duckdb`, construida por dbt. El respaldo SQLite (`etl/datos.db`) no se consulta aquí: solo sirve para la paridad de la página de calidad (D-154).

## D-186 · Un color por sección del menú; Fuentes al final

- **Fecha:** 2026-10-20.
- **Decisión:** las páginas de cada sección del menú lateral tienen su propio color, para que se lea a qué sección pertenecen: verde para Dashboard, azul para Ingeniería de datos, violeta para Documentación y ámbar para Fuentes. Cada color tiene un tono claro para los menús oscuros y uno profundo para los claros, con contraste de 4,5:1 o más en todos los temas. El orden pasa a ser Dashboard, Ingeniería de datos, Documentación y Fuentes: las fuentes cierran el menú porque llevan fuera de la aplicación.

## D-187 · Las fuentes se ven como enlaces

- **Fecha:** 2026-10-20.
- **Decisión:** las fuentes del menú abren los sitios oficiales de ODEPA e INE en una pestaña nueva, como corresponde a una fuente pública: se ve de dónde vienen los datos y no depende de que esos sitios permitan mostrarse dentro de otra página. Para que se reconozcan como enlaces, toman el azul de enlace y un subrayado fino; Ingeniería de datos pasa al ámbar que tenían. Ninguna otra entrada del menú va subrayada, porque las demás no salen de la aplicación.

## D-188 · Colores del menú sin significado de estado

- **Fecha:** 2026-10-20.
- **Problema:** en la aplicación, el verde dice «verificado» y el ámbar «pendiente». Con Ingeniería de datos en ámbar, el menú podía leerse como una advertencia.
- **Decisión:** el Dashboard conserva el verde de la marca GreenOcean; Ingeniería de datos pasa a violeta; Documentación, a un gris pizarra discreto, porque son páginas de consulta; las Fuentes siguen en azul de enlace y subrayadas. Ningún color del menú coincide con un color de estado. Contraste de 5,7:1 o más en todos los temas.

## D-189 · Mapa de la base: de dónde viene cada tabla

- **Fecha:** 2026-10-20.
- **Problema:** el panel mostraba el modelo estrella y el pipeline completo, pero no respondía una pregunta directa: de dónde viene cada una de las 12 tablas de la base servida, y qué papel tiene SQLite ahora que el panel lee DuckDB.
- **Decisión:** la página Modelo de datos tiene dos vistas, con un selector arriba: «Mapa de la base» (por defecto) y «Modelo estrella» (la de D-147, sin cambios). El mapa recorre de izquierda a derecha las fuentes (ODEPA mayorista y consumidor, IPC del INE), el aterrizaje (SQLite `raw.db` y la capa bronce en Parquet), la transformación (dbt sobre una DuckDB de trabajo: modelos por capa y pruebas, leídos de `dbt_node`), la base servida `etl/datos.duckdb` con sus 12 tablas agrupadas por origen (9 modelos de dbt, `etl_run` escrita por el pipeline, `dbt_node` y `dbt_result` como traza de dbt), y el consumo (las 8 vistas que el panel crea al conectar, y el panel en solo lectura). Debajo, el respaldo SQLite `datos.db` y la paridad que lo compara con DuckDB. Cada caja explica su papel al pasar el cursor; las filas de cada tabla se leen de la base.
- **Cómo se dibuja:** un documento HTML propio en `st.iframe` (`bi/database_map.py`), solo con CSS, como el Centro de operación.

## D-190 · «Dónde viven los datos» con logos, y el modelo estrella al día

- **Fecha:** 2026-10-20.
- **Problema:** el «Mapa de la base» de D-189 usaba cajas de color y repetía el consumo, que ya está en Pipeline y linaje. El autor quería ver, con los logos de cada tecnología como en el pipeline, dónde se guarda cada tipo de dato, por qué y cómo se relacionan los almacenes. Además, el modelo estrella no dibujaba las tres tablas del IPC (`ipc_weekly`, `ipc_monthly`, `ine_ipc_source`) y se llamaba «datos.db», nombre del respaldo.
- **Decisión (vista «Dónde viven los datos»):** logos flotantes, sin tarjetas, en el estilo del Centro de operación: ODEPA y el INE como orígenes; SQLite (`raw.db`) como aterrizaje; Parquet como capa bronce; dbt con su DuckDB de trabajo; DuckDB (`datos.duckdb`) como base servida, con sus 12 tablas en tres grupos según quién las escribe (modelos dbt, el registro de cargas del pipeline en Python y las trazas de dbt); y GitHub, donde se publican los archivos. Debajo, el respaldo SQLite (`datos.db`), calculado por el ETL en Python, y la paridad que lo compara con DuckDB. Cada logo dice al pasar el cursor qué guarda y por qué; cada flecha dice qué le pasa a los datos. Sale la parte de consumo (las vistas y el panel): vive en Pipeline y linaje.
- **Decisión (modelo estrella):** se dibuja el grupo «IPC de alimentos (INE)» arriba a la izquierda, con la cadena `ine_ipc_source` → `ipc_monthly` → `ipc_weekly` y el vínculo por `week_start` con `dim_date`; el diagrama se llama ahora «Modelo estrella de datos.duckdb». Las tres tablas se cuentan desde la base real, y el título del subtítulo de `weekly_price` deja de tocar su separador. `etl/schema.sql` sigue siendo el del respaldo SQLite y no las incluye.
- **Textos:** donde «datos.db» decía la base que lee el panel, ahora dice `datos.duckdb` (reglas de calidad, módulos del proyecto); donde se refiere al respaldo, se conserva.
- **Robustez:** el conteo de filas que usa el modelo estrella lleva la lista de tablas en su clave de caché, porque una tabla nueva tras un despliegue chocaba con una cuenta guardada.

## D-191 · El diagrama de almacenamiento aprovecha el espacio y muestra el tamaño de los archivos

- **Fecha:** 2026-10-20.
- **Problema:** el diagrama de D-190 dejaba cerca de un tercio de la zona sin usar, con logos y textos pequeños frente al ancho de la página.
- **Decisión:** logos de 92 px (antes 76), textos más grandes y el respaldo SQLite más cerca de la fila principal; las flechas se calculan desde las posiciones de los almacenes, así que no se descuadran si se mueve uno. Cada almacén cuyo archivo existe muestra su tamaño real bajo el logo (`datos.duckdb`, `datos.db`); `raw.db` no está en el servidor del panel, y ahí se muestra el tamaño documentado (≈ 665 MB, D-020) con signo de aproximación. La base de trabajo de dbt y la capa Parquet no muestran tamaño porque tampoco están en el servidor: no se inventa ninguno.
- **Sin cilindros:** cada almacén lleva el logo de su tecnología, que dice qué es; un cilindro genérico habría vuelto iguales `raw.db` y `datos.duckdb`, justo lo que el diagrama distingue.

## D-192 · Un cilindro pequeño en los almacenes de datos

- **Fecha:** 2026-10-20.
- **Decisión:** a petición del autor, los cinco almacenes (`raw.db`, la capa Parquet, la base de trabajo de dbt, `datos.duckdb` y `datos.db`) llevan un cilindro miniatura en la esquina de su logo, el símbolo universal de «aquí se guardan datos». El logo de la tecnología sigue siendo lo principal: dice qué herramienta es. Las fuentes (ODEPA, INE) y GitHub no llevan cilindro, porque no son bases de datos. Esto corrige D-191, que los había dejado fuera por el motivo contrario: el cilindro solo, sin el logo, volvía iguales a `raw.db` y `datos.duckdb`; junto al logo no tiene ese problema.- **Flecha de paridad:** la línea punteada subía hasta el grupo «Modelos dbt» y parecía comparar el respaldo con una de las tres partes. Ahora rodea el grupo por la izquierda y termina bajo el logo de DuckDB, en el archivo entero, con punta en ambos extremos: la paridad compara dos bases completas.

## D-193 · Las tres fuentes se ven como tres

- **Fecha:** 2026-10-20.
- **Problema:** el diagrama dibujaba un solo CSV de ODEPA y el rótulo del INE quedaba pegado al logo de ODEPA, así que no se veía que el pipeline consume tres fuentes.
- **Decisión:** cada fuente tiene su logo y su nombre: «ODEPA consumidor» y «ODEPA mayorista», cada una con su hoja CSV, y «INE · IPC». Los dos CSV de ODEPA llegan a `raw.db`; el índice del INE va directo a la capa Parquet. El diagrama gana altura (más separación entre las tres fuentes) y las columnas se separan para que ninguna etiqueta de flecha toque un logo.

## D-194 · Paridad sin ambigüedad y el IPC que no pasa por SQLite

- **Fecha:** 2026-10-20.
- **Problema:** la línea de paridad terminaba en un hueco entre logos y no se sabía qué comparaba; y no se entendía por qué el IPC del INE va a Parquet sin pasar por SQLite como los CSV de ODEPA.
- **Decisión (paridad):** el respaldo SQLite pasa a estar justo bajo `datos.duckdb` y la paridad es una línea recta vertical entre los dos, con punta en cada extremo y su etiqueta en medio. El grupo de las tres procedencias de tablas cuelga sobre el archivo, con una flecha que baja a él: las tablas viven dentro de ese archivo. La flecha del ETL en Python va de `raw.db` al respaldo.
- **Decisión (IPC):** no es un paso saltado sino de diseño. `raw.db` es el aterrizaje de los CSV de ODEPA, que baja el agente; el IPC son dos CSV pequeños del INE que `etl/ine.py` escribe directo en Parquet. Si el INE no responde, el pipeline rehace ese Parquet desde `ine_ipc_source`, que se guarda en la base servida. La flecha del INE dice «directo a Parquet, sin pasar por SQLite» y su ayuda lo explica.

## D-195 · Modelo entidad-relación, en la notación clásica

- **Fecha:** 2026-10-20.
- **Problema:** lo que se conoce como modelo de datos en la universidad es el diagrama entidad-relación: cada tabla como una caja con sus columnas y tipos, sus claves y las relaciones con patas de gallo. La página tenía el modelo estrella y el mapa de almacenamiento, pero no ese diagrama.
- **Decisión:** el selector de la página Modelo de datos gana un tercer botón, «Entidad-relación», sin tocar los otros dos. Dibuja nueve tablas con cabecera, columna de claves (PK, FK, o ambas), nombre, tipo de DuckDB y filas, y una regla bajo las columnas de la clave primaria. Las relaciones llevan pata de gallo en el lado «muchos» y doble barra en el lado «uno»: `weekly_price` hacia `dim_date`, `dim_product`, `dim_region` y `dim_channel`; `rejection` hacia `etl_run`; `ipc_weekly` hacia `dim_date` (a lo más una por semana). Una línea punteada une `ipc_monthly` e `ipc_weekly` por el mes: es lógica, no una clave foránea.
- **Coherente con los datos:** los tipos y las columnas se leen de la base (`DESCRIBE`); las relaciones son las que prueba dbt en `schema.yml`, más la de `rejection` que comprueba la página de calidad; una prueba falla si el diagrama dibuja una que dbt no prueba o si dbt prueba una que no está dibujada. La clave primaria compuesta de `weekly_price` es la que comprueba la consulta de duplicados.
- **Fuera del diagrama, y dicho en la leyenda:** `ine_ipc_source` (copia cruda de los archivos del INE) y `dbt_node` y `dbt_result` (la traza de dbt): son almacenamiento y registro, no parte del modelo.


## D-196 · Calidad y auditoría rehechas: medir de verdad y demostrar el origen de cada cifra
- **Problema:** la página mostraba tarjetas con textos y figuras fijas (entre ellas una auditoría manual sin fecha). Parecía de adorno: no medía nada al abrir y no dejaba seguir una cifra hasta su origen.
- **Decisión:** la página se divide en dos vistas con un selector. **Calidad** mide en cada carga, sobre la base publicada, once indicadores en las seis dimensiones de DAMA-DMBOK (completitud, unicidad, validez, consistencia, oportunidad y trazabilidad). Cada cifra lleva al lado su umbral, que es un parámetro del proyecto, y un veredicto global; el historial de cargas y los rechazos y marcas se leen de `etl_run`, `rejection` y `weekly_price`. **Auditoría** elige un producto, un canal y una región, y sigue su último precio en seis pasos: archivo de origen, aterrizaje, reglas, dbt, base servida y panel.
- **Honestidad:** si el archivo CSV de origen no está en el servidor, el paso lo dice («no se puede comprobar aquí») en vez de mostrarlo como verificado. La cifra de la auditoría manual lleva su fecha (18-10-2026: 400 de 400).
- **Código:** `bi/quality_live.py` y `bi/audit_trace.py`; `bi/quality_view.py` conserva la vista de evidencias dentro de Auditoría.
- **Pruebas:** `tests/test_quality_audit.py` (umbrales, degradación, huella del archivo, traza de seis pasos) y las pruebas de página actualizadas.

## D-197 · Cruces entre bases: dónde dos bases se tocan
- **Problema:** el modelo estrella y el entidad-relación describen una sola base, `datos.duckdb`. Pero el proyecto tiene varias (raw.db, Parquet de bronce, la base de trabajo de dbt, `datos.duckdb` y el respaldo `datos.db`), y faltaba mostrar dónde se cruzan.
- **Decisión:** la página del modelo gana una cuarta pestaña, «Cruces entre bases», con los siete cruces reales: ODEPA → raw.db, raw.db → bronce, INE → bronce (directo, sin SQLite, por diseño), bronce → base de trabajo (donde se cruzan ODEPA e INE por semana), base de trabajo → `datos.duckdb` (ATTACH y CREATE TABLE AS), `datos.duckdb` ↔ `datos.db` (solo comparación de tres cifras) y el historial `etl_run` que pasa de una carga a la siguiente. Cada fila dice cómo pasa, qué viaja, con qué clave se cruzan y la comprobación de ahora.
- **Honestidad:** lo que no se puede medir en el servidor (raw.db) se marca «Pendiente» con su motivo; no se muestra como comprobado.
- **Código y pruebas:** `bi/database_crossings.py`, `tests/test_database_crossings.py`.

## D-198 · Calidad, auditoría y cruces como arquitectura, no como tarjetas
- **Problema:** las vistas de Calidad y de Auditoría usaban tarjetas grandes que obligaban a desplazarse y no daban el panorama en una mirada; Auditoría no dejaba partir por familia; «Cruces entre bases» era una lista que había que leer; el modelo estrella y el entidad-relación se veían chicos y había que hacer zoom.
- **Calidad:** el pipeline va en una línea (Fuentes → aterrizaje y bronce → dbt → datos.duckdb) y cada dimensión cuelga del punto donde se vigila, con su ícono, sus cifras y su umbral; el detalle de cómo se mide aparece al pasar el cursor. Lo apartado y el historial de cargas van abajo, en líneas cortas. Todo cabe en una pantalla.
- **Auditoría:** los filtros parten por **Familia** y luego Producto, Canal, Región y Serie. La cadena de seis pasos muestra solo lo esencial bajo cada logo; el resto va en el hover. Las tarjetas de controles se reemplazan por íconos pequeños con su estado (verde comprobado, naranja pendiente) agrupados por etapa; las píldoras siguen abriendo la evidencia.
- **Cruces entre bases:** pasa a ser un diagrama: cada base es un logo y cada cruce una flecha con su número, coloreado por su comprobación. Al pasar el cursor por el número se ve cómo pasa, qué viaja, con qué se cruzan y la comprobación; por el logo, qué guarda. Se agrega el cruce que faltaba: raw.db → datos.db, el ETL en Python (ocho cruces).
- **Modelo estrella y entidad-relación:** el alto máximo del diagrama sube un 20 % para leerlos sin zoom.
- **Plataforma y seguridad (revisión):** la flecha HTTPS entre la app y los visitantes va en los dos sentidos; se agrega la conexión «API de GitHub» entre la app y GitHub (el Centro de operación lee las ejecuciones y lanza el pipeline con la clave de los secretos); el hover del Job semanal dice que guarda también datos.db y el registro de descargas.

## D-199 · La clave de control resiste que la adivinen
- **Problema:** una revisión de seguridad (atacando el panel como lo haría un intruso) encontró dos debilidades en la clave de control que abre «Ejecutar pipeline ahora» y «Accesos del autor». No había límite de intentos: un script podía probar claves sin parar, abriendo sesiones nuevas. Y una clave escrita con ñ, tildes o emojis hacía fallar la comparación (`TypeError`) y mostraba un error en vez de «Clave incorrecta».
- **Decisión:** la comparación se hace en tiempo constante sobre bytes UTF-8, así que acepta cualquier carácter. Tras 5 claves incorrectas en 15 minutos, el acceso se bloquea 15 minutos, incluso para la clave correcta; cada error cuesta además un segundo de espera. El contador es uno solo para todos los visitantes del servidor (`st.cache_resource`), así que abrir otra sesión no lo reinicia. Mientras dura el bloqueo, el pipeline sigue corriendo cada martes y desde GitHub.
- **Lo que la revisión confirmó que ya estaba bien:** la página Consultas SQL resistió más de 20 ataques (leer archivos y secretos, escribir con COPY, ATTACH, instalar extensiones, cambiar la configuración): la doble barrera, el filtro y el motor sin acceso externo con la configuración bloqueada, los rechaza. Ningún secreto está en el historial de git. El token nunca se muestra, tampoco en los errores. El desbloqueo vive solo en la sesión del navegador.
- **Código y pruebas:** `control.LoginGuard`; `tests/test_control.py` y `tests/test_dashboard.py` (D-199).

## D-200 · Pestaña Seguridad: cada ataque, su barrera y su prueba
- **Problema:** la revisión de D-199 mostró que el proyecto es seguro, pero nada en el panel lo demostraba, y el SAD decía que el panel «no ejecuta texto de un visitante», algo que dejó de ser cierto con la página Consultas SQL.
- **Decisión:** el Centro de operación pasa a tener tres pestañas: Operación, Plataforma (el diagrama de siempre) y **Seguridad**. Seguridad es un diagrama en una vista: el visitante, las tres puertas que podrían tentar a un atacante (Consultas SQL, la clave de control y el código público), tres barreras por puerta y lo que protegen (datos.duckdb, el pipeline y los secretos). Cada barrera lleva su enlace a la prueba automática que la ataca en cada push; el detalle sale al pasar el cursor.
- **Publicarlo no ayuda a un atacante:** el código ya es público, y un sistema debe seguir siendo seguro aunque se sepa cómo está hecho (principio de Kerckhoffs). Nunca se publican los valores secretos ni un problema todavía sin corregir.
- **Pruebas:** los ataques de la revisión pasan a ser permanentes en `tests/test_security.py`: 19 intentos de leer secretos o escribir archivos a través del SQL, 9 órdenes directas al motor, la búsqueda de tokens en el repositorio, los permisos mínimos del workflow y que cada barrera del diagrama apunte a una prueba que existe.
- **SAD:** la fila Seguridad describe ahora las dos barreras del SQL y el límite de intentos de la clave.

## D-201 · Seguridad, su propia sección: la vista y el plan de pruebas
- **Problema:** la vista de D-200 quedó como tercera pestaña del Centro de operación, donde un revisor o un reclutador difícilmente la encuentra, y el método de la revisión no estaba escrito en ningún documento.
- **Decisión:** el menú gana la carpeta **Seguridad**, entre Ingeniería de datos y Documentación, con dos páginas: «Seguridad y vulnerabilidades» (la vista de D-200, que sale del Centro de operación; este vuelve a Operación y Plataforma) y «Plan de pruebas de seguridad», el documento nuevo `docs/SEGURIDAD.md`, que se lee y se descarga en PDF como el PRD, el SAD y el ADR. La carpeta lleva el nombre «Seguridad» y no un candado solo, para que se entienda sin explicación.
- **El documento:** objetivo y alcance, activos, superficie de ataque, el método en cinco pasos (inventario, ataque como intruso, corrección antes de publicar, cada ataque se vuelve prueba, repetición en cada push), nueve casos de prueba (diez desde D-202) con su categoría del OWASP Top 10 y su archivo de prueba, criterios de aceptación, resultados de la revisión del 20-10-2026, límites que dependen del autor y la política de divulgación.
- **Pruebas:** `tests/test_dashboard.py` (D-201) y las del menú y de la ruta, actualizadas.

## D-202 · Una sola puerta del autor: el botón del pipeline aparece solo tras la clave
- **Problema:** el botón «Ejecutar pipeline ahora» se veía siempre y pedía la clave al pulsarlo, mientras los enlaces de administración estaban detrás de otra entrada con la misma clave. El único control que de verdad necesita la clave (lanzar el pipeline con el token del servidor) estaba a la vista, y los enlaces, que de todas formas piden la sesión de GitHub o de Streamlit, estaban escondidos. Además, abrir una entrada abría la otra sin decirlo.
- **Decisión:** una sola puerta, «Acceso del autor». Antes de la clave, el visitante solo ve «Recargar datos» y esa puerta. Con la clave correcta aparecen juntos el botón del pipeline y «Enlaces del autor», con la nota de que cada enlace pide su propia sesión, y un botón «Cerrar acceso». La ventana de ejecución vuelve a pedir la clave si la sesión no está abierta (defensa en profundidad), y la clave sigue limitada a 5 intentos (D-199).
- **Seguridad:** la barrera «Desbloqueo por sesión» de la vista pasa a ser «Una sola puerta», y el plan de pruebas suma el caso S-10 (lanzar el pipeline sin la clave).
- **Pruebas:** `tests/test_dashboard.py` (D-202) y `tests/test_operation_center.py`.

## D-203 · El acceso del autor se abre con Enter
- **Problema:** después de escribir la clave había que pulsar además «Abrir», un paso de más.
- **Decisión:** la clave se comprueba al pulsar Enter en el campo, y el botón «Abrir» desaparece. El campo se vacía después de cada intento, correcto o no, para que la clave no quede en pantalla. El límite de 5 intentos (D-199) se aplica igual. La ventana de ejecución del pipeline conserva su botón «Ejecutar», porque ahí el botón es la confirmación de una acción real.
- **Pruebas:** `tests/test_dashboard.py` (D-202, con Enter en lugar del botón).

## D-204 · La sección Seguridad sin la palabra «vulnerabilidad»
- **Decisión:** la página «Seguridad y vulnerabilidades» pasa a llamarse **«Mapa de seguridad»**, y el plan de pruebas habla de «puntos débiles» y de «problemas sin corregir». La palabra sugería fallas abiertas, cuando la sección muestra justamente que están cerradas y probadas.
- **Pruebas:** las del menú, actualizadas.

## D-205 · Diagramas de los documentos con el estilo del pipeline y pantallas reales
- **Problema:** los diagramas del PRD y del SAD estaban hechos con cajas y no se parecían a los del panel; la «pantalla principal» del PRD era un boceto con rectángulos grises, sin un solo dato; el SAD no mostraba el recorrido del pipeline y el plan de seguridad no tenía su mapa. Los PDF no mostraban ninguna imagen. Además, una regla de estilo del zoom estiraba al 100 % los logos dentro de los diagramas del panel (Pipeline y linaje se veía con logos gigantes).
- **Decisión:** las vistas de los documentos se rehacen en `bi/doc_views.py` con el lenguaje del pipeline: mosaicos con borde del color de su capa, chips que dicen qué viaja, sin cajas y con explicación al pasar el cursor. Actores y casos de uso (PRD); contexto C4, contenedores C4 y la secuencia del martes (SAD). El boceto se reemplaza por cuatro capturas reales del panel en marcos de computador y teléfono, en cuatro temas: Resumen semanal (Vantablack), Precios e inflación (Claro), Consultas SQL (Corporativo) y el Resumen en un teléfono horizontal (Blue Light). El SAD suma el recorrido del pipeline y el plan de seguridad su mapa: los diagramas que ya existen en el panel se muestran también en los documentos.
- **PDF:** el PRD descargable incluye las cuatro capturas.
- **Corrección:** la regla del zoom solo da el ancho completo al diagrama, no a los logos que lleva dentro.
- **Pruebas:** `tests/test_doc_diagrams.py` y `tests/test_document_pdf.py` (D-205).

## D-206 · «Entorno local» en el diagrama de plataforma; el campo de la clave no invita a generar contraseñas
- **Decisión:** en el diagrama Plataforma, la zona de desarrollo se llama «Entorno local» en vez de «Tu computador», un nombre profesional para un portafolio. Los campos de la clave de control se marcan como código de un solo uso (`autocomplete="one-time-code"`), para que el navegador no ofrezca crear y guardar una contraseña nueva: la clave no es la de una cuenta.
- **Pruebas:** `tests/test_architecture.py`.

## D-207 · La clave de control ya no es un campo de contraseña
- **Problema:** desde que el acceso se abre con Enter (D-203), el campo de la clave quedó solo, sin usuario al lado, y Chrome lo tomó por un formulario de registro: ofrecía crear y guardar una contraseña nueva. Marcarlo como código de un solo uso (D-206) no bastó.
- **Decisión:** los dos campos de la clave son campos de texto comunes que muestran puntos en vez de letras (`-webkit-text-security`), sin autocompletar. El navegador ya no los reconoce como contraseña y no ofrece nada. La comprobación, el límite de 5 intentos y el vaciado del campo no cambian.
- **Pruebas:** `tests/test_dashboard.py` (D-202, D-207).

## D-208 · En el diagrama de actores, las consultas SQL las hace el autor
- **Problema:** el diagrama de actores del PRD unía al visitante (analista, compras, gerencia) con «Consultar con SQL». El panel es para usuarios de negocio, no para ingenieros de datos: un visitante no escribe consultas.
- **Decisión:** el caso pasa al autor como «Consultas SQL a pedido»: si alguien necesita un dato, el autor lo consulta y responde con un CSV. El visitante conserva las tres preguntas de negocio y la revisión de calidad y documentos, que es lo que mira un revisor técnico. El texto del PRD bajo el diagrama lo dice igual. El perfil «Equipo de datos» del PRD y de la página del proyecto pasa a «Revisor técnico» (por ejemplo, un reclutador), y en la tabla de evolución del PRD el responsable es «El autor».
- **Pruebas:** `tests/test_doc_diagrams.py`, `tests/test_document_pdf.py` y `tests/test_dashboard.py`, sin cambios.

## D-209 · Menú con íconos y perfiles «Ver como»
- **Problema:** el menú mostraba lo mismo a todos: un visitante de negocio veía consultas SQL, linaje dbt y el Centro de operación, y un reclutador no tenía un camino corto. Los nombres del menú no llevaban ícono. (D-208 ya estaba tomada; esta etapa queda como D-209.)
- **Decisión:** cada página del menú lleva un ícono pequeño a la izquierda, del color de su sección; las fuentes llevan el de enlace externo. Arriba del menú, un selector «Ver como» que no bloquea nada: **Visitante** (por defecto: Resumen semanal, Precios e inflación, Fuentes), **Analista de negocio** (lo del visitante más Calidad y auditoría, PRD y SAD), **Ingeniería de datos** (todo, con Documentación al final) y **Reclutador** (Resumen semanal; la página «Stack y evidencia» llega en una etapa siguiente). La app abre en el Resumen semanal como Visitante. El perfil queda en la sesión y en la dirección (`?ver=`), y cada enlace del menú lo conserva. Fuentes y Documentación empiezan plegadas.
- **Enlaces:** una dirección de una página que el perfil no muestra sigue abriéndose; el perfil solo decide el menú.
- **Pruebas:** `tests/test_dashboard.py` (D-209: el menú de cada perfil, la apertura como Visitante con íconos, una página fuera del menú y el cambio de perfil) y las del menú, actualizadas.

## D-210 · Documentos de dos páginas como máximo
- **Problema:** el PRD, el SAD, el ADR y el plan de seguridad sumaban más de mil líneas para un proyecto pequeño: nadie los leía enteros, repetían lo que ya está en este registro y sus PDF abrían con portada e índice. Los diagramas `contexto`, `contenedores` y `secuencia` del SAD eran débiles y repetían lo que el recorrido del pipeline muestra mejor.
- **Decisión:** cada documento cabe en dos páginas de PDF. **PRD:** problema con las cifras de la base actual, usuarios, preguntas de negocio, ocho requisitos clave, el diagrama de actores y las capturas reales. **SAD:** solo los diagramas vivos `pipeline`, `plataforma` y `modelo`, con un párrafo cada uno. **ADR:** una tabla con las diez decisiones que más pesan (decisión, motivo, alternativa descartada), con su número original. **Plan de seguridad:** puertas y barreras, su mapa, el método, los diez casos de prueba y los resultados. El detalle extenso queda en este registro.
- **Diagramas:** se quitan `contexto`, `contenedores` y `secuencia` de `bi/doc_views.py` y de los documentos. El diagrama `actores` se rehace con el estándar del pipeline: logos 3D en discos con brillo y sombra, sin cajas, flechas ortogonales con un chip de lo que viaja, lectura de izquierda a derecha (fuentes → GitHub Actions → repositorio → panel → visitante y autor) y explicación al pasar el cursor por cada logo y cada chip.
- **PDF:** sin portada ni índice: una franja con el título en la primera página y las capturas del PRD de dos en dos.
- **Escalabilidad:** la página del mismo nombre lee ahora la sección de abajo, que sale del SAD sin cambios.
- **Pruebas:** `tests/test_doc_diagrams.py` y `tests/test_document_pdf.py` (D-210: dos páginas como máximo, actores sin curvas y con explicación en cada chip, ADR de diez filas) y `tests/test_dashboard.py`.

### Escalabilidad

Desde D-279, el plan de capacidad y escalabilidad es un documento propio: `docs/ESCALABILIDAD.md`.

## D-211 · Página «Stack y evidencia» para el reclutador
- **Problema:** un reclutador tenía que recorrer varias páginas para saber con qué está hecho el proyecto y si funciona de verdad.
- **Decisión:** una página nueva, «Stack y evidencia», en el menú del perfil Reclutador (D-209) y en el de Ingeniería de datos. Muestra en una fila los logos 3D del stack, en el orden en que los datos los encuentran: Python, SQLite, Parquet, dbt, SQL, DuckDB, pytest, GitHub Actions y Streamlit. Al pasar el cursor, cada logo dice qué hace en el proyecto; un clic abre la página donde se ve en uso (por ejemplo, SQL → Consultas SQL, dbt → Pipeline y linaje, pytest → Calidad y auditoría, GitHub Actions → Centro de operación). Debajo, tres cifras reales: precios semanales procesados (`weekly_price`), pruebas automáticas (funciones de pytest del repositorio más las pruebas de dbt de `dbt_node`) y cargas semanales registradas (`etl_run`). Ninguna se escribe a mano.
- **Detalle técnico:** `st.html` quita los degradados de un SVG en línea, así que cada logo va como imagen `data:` que conserva el disco 3D.
- **Código y pruebas:** `bi/stack_page.py`; `tests/test_stack_page.py` y `tests/test_dashboard.py` (D-211, y el menú del Reclutador en D-209).

## D-212 · La explicación del stack no tapa las cifras; Proyecto con su color
- **Problema:** en «Stack y evidencia», la explicación que aparece al pasar el cursor por un logo tapaba la cifra de abajo. La carpeta «Proyecto» del menú no tenía color propio y usaba el verde general.
- **Decisión:** bajo los logos queda una franja reservada con la indicación «Pasa el cursor por un logo…»; la explicación se abre en esa franja, la indicación se oculta mientras tanto, y las cifras quedan siempre a la vista. La carpeta «Proyecto» usa un turquesa propio (5,6:1 de contraste en menús claros y 9,5:1 en oscuros), distinto de los colores de estado y de las otras secciones.
- **Pruebas:** `tests/test_stack_page.py` y `tests/test_dashboard.py` (D-212).

## D-213 · El menú en bloques de color, uno por tipo de lector
- **Problema:** «Ver como» (D-209) mostraba a todos la misma información y solo escondía partes del menú: agregaba un paso, ocultaba la amplitud del trabajo a quien no elegía el perfil correcto y el Centro de operación quedaba fuera de la vista del autor.
- **Decisión:** el selector sale. El menú pasa a ser una pila de bloques siempre visibles, abiertos por defecto y plegables con un clic, cada uno con su título en versalitas, una línea fina y su color: **Negocio · BI** (verde: Resumen semanal, Precios e inflación), **Análisis de negocio · BA** (gris pizarra: PRD, ADR, Escalabilidad), **Ingeniería de datos** (violeta: Pipeline y linaje, Modelo de datos, Calidad y auditoría, Consultas SQL, SAD), **DevOps y seguridad** (rosa: Centro de operación, Mapa de seguridad, Plan de pruebas de seguridad), **Stack y evidencia** (turquesa) y **Fuentes** (azul). Cada página aparece en un solo bloque, con su ícono (D-209). La app sigue abriendo en el Resumen semanal.
- **El autor:** no hay un bloque «Autor»: lo único suyo es la clave, que ya protege el botón del pipeline y los enlaces dentro del Centro de operación (D-199, D-202). Un bloque propio indicaría a cualquiera dónde está la puerta; el menú no protege nada, la clave sí.
- **Enlaces:** una dirección vieja con `?ver=` sigue abriendo su página; el parámetro se descarta.
- **Pruebas:** `tests/test_dashboard.py` (D-213: bloques en orden, cada página una vez, colores distintos, direcciones viejas) y las del menú, actualizadas; las de D-209 sobre perfiles se retiran con el selector.

## D-214 · PRD, SAD y ADR con redacción de documento de ingeniería
- **Problema:** los documentos de D-210 usaban un tono coloquial («no se pueden comparar sin trabajo», «lo hace solo») impropio de un documento técnico corporativo.
- **Decisión:** el PRD, el SAD y el ADR se reescriben en registro de ingeniería: propósito, partes interesadas, preguntas con identificador y requisitos con criterio de verificación (PRD); vistas de datos, despliegue y lógica (SAD); justificación y alternativa descartada por decisión (ADR). El objetivo y el alcance del plan de seguridad se ajustan al mismo registro. Las cifras siguen siendo las de la base y cada documento cabe en dos páginas de PDF.
- **Pruebas:** `tests/test_document_pdf.py` (encabezado de la tabla del ADR) sin otros cambios.

## D-215 · El menú en tarjetas de cuatro tonos; los documentos al final
- **Problema:** los bloques de D-213 eran solo títulos de color sobre el fondo del menú, y los documentos (bloque «Análisis de negocio · BA») aparecían arriba, antes que la ingeniería, la operación y el stack.
- **Decisión:** cada bloque es una tarjeta de estilo HUD: fondo en uno de los cuatro tonos del panel (azul, Vantablack, gris oscuro y gris claro), borde luminoso y corchetes en dos esquinas del color de acento del bloque, título en versalitas del mismo acento y páginas con su ícono en ese acento. Los tonos son fijos en todos los temas, así que cada tarjeta se lee igual en cualquiera. El orden sigue la pertenencia: Negocio · BI, Ingeniería de datos, DevOps y seguridad, Stack y evidencia, Análisis de negocio · BA y Fuentes; dentro de cada bloque, los documentos van al final (SAD en Ingeniería, el plan en DevOps). El margen interno del menú se reduce para que los nombres largos quepan en una línea y todo el menú quede sobre el pie en 1440 × 900.
- **Pruebas:** `tests/test_dashboard.py` (D-213, actualizada: orden de bloques, tonos y corchetes de cada tarjeta).

## D-216 · Tarjetas del menú solo en los cuatro tonos, con espacio entre ellas
- **Problema:** las tarjetas de D-215 usaban acentos verde, violeta y rosado, colores que no pertenecen a los cuatro tonos pedidos, y quedaban casi pegadas unas a otras.
- **Decisión:** el acento de cada tarjeta es un paso más claro u oscuro de su propio tono: azul claro en las azules, plata en la Vantablack, gris medio en la gris oscura y pizarra en las grises claras; la marca de la página actual usa ese mismo acento. Entre tarjetas queda un espacio de 12 px. El fondo del menú no cambia: sigue el tema elegido. Las tarjetas siguen abiertas por defecto y plegables con un clic.
- **Pruebas:** `tests/test_dashboard.py` (D-213: los acentos pertenecen solo a los cuatro tonos).

## D-217 · El PRD y el SAD, escritos como un equipo describe su producto
- **Problema:** el PRD hablaba de «perfiles de diseño (hipótesis, sin entrevistas)» y de lo que el sistema no es, y su redacción sonaba a plantilla. Un documento de producto describe qué es el sistema, qué hace, qué no hace y para quién, sin comentarios sobre el propio documento.
- **Decisión:** el PRD se ordena en contexto, visión y misión, alcance (qué hace y qué no hace), usuarios, preguntas de negocio, requisitos y pantallas, en frases directas. El SAD conserva sus tres diagramas con párrafos más simples. «El autor» pasa a «el administrador» en el PRD y en el plan de seguridad. Las cifras siguen siendo las de la base y cada documento cabe en dos páginas.
- **Pruebas:** `tests/test_document_pdf.py` y `tests/test_doc_diagrams.py`, sin cambios.

## D-218 · El ADR y el plan de seguridad, con el mismo tono que el PRD
- **Decisión:** el ADR y el plan de seguridad se reescriben en frases directas, sin jerga innecesaria («artefacto compacto», «sesgo inflacionario», «superficie expuesta»), igual que el PRD y el SAD de D-217. El contenido, las cifras y las referencias D-xxx no cambian.
- **Pruebas:** `tests/test_document_pdf.py` (encabezado de la tabla del ADR).
- **Corrección:** el SAD decía que el IPC del INE pasa por SQLite; va directo a Parquet (D-197).

## D-219 · El README y la portada, al día con la arquitectura actual
- **Problema:** el README, que es lo primero que ve un visitante en GitHub, describía el proyecto de los primeros hitos: un pipeline SQLite → consultas → panel, precios «sin ajuste por inflación», el rezago K5 (retirado en D-146), un estado al 12-10-2026 y un stack sin dbt, DuckDB ni Parquet. La portada antigua del panel repetía «precios nominales, sin ajuste por inflación». El diagrama de actores del PRD decía «El autor» mientras el texto decía «el administrador».
- **Decisión:** el README se reescribe con la arquitectura real (ingesta, aterrizaje, bronce, dbt sobre DuckDB, base servida), las tres preguntas de negocio, el stack completo, la tabla de documentos, los comandos actuales, el alcance y límites vigentes y las dos fuentes (ODEPA e INE); la sección «Estructura», que el panel lee, lista los archivos actuales. La portada habla de precios nominales y reales. El diagrama de actores dice «Administrador», igual que el texto.
- **Pruebas:** `tests/test_project.py` (cada ruta de «Estructura» existe y lo que no se sube no tiene enlace) y `tests/test_doc_diagrams.py`.

## D-220 · Calidad y auditoría en una sola vista ordenada, sin el filtro por producto
- **Problema:** la vista Calidad colgaba cuatro dimensiones sobre el pipeline y dos debajo, con las tablas de lo apartado y de las cargas sueltas en una esquina: el contenido era correcto, pero el ojo no encontraba un orden. La vista Auditoría pedía elegir familia, producto, canal, región y serie para seguir un solo precio por seis logos que repetían el pipeline de «Pipeline y linaje», sin decir qué se auditaba; la auditoría de los jobs ya está en el Centro de operación, que lee GitHub Actions.
- **Decisión:** la página es una sola vista, sin pestañas ni filtros. Arriba, el pipeline en una línea (Fuentes, Aterrizaje y bronce, dbt, datos.duckdb) con sus logos alineados; debajo de cada etapa, en su columna, las dimensiones que se vigilan ahí (Completitud; Actualidad; Validez y Pruebas dbt; Consistencia y Unicidad). Luego, a todo el ancho, «Qué se apartó y por qué» y «Cargas» lado a lado. Al final, los 11 **controles de auditoría** en sus cuatro grupos (fuentes, ejecución y dbt, warehouse, resultados), que no dependían del precio elegido: cada uno con su estado y su evidencia al hacer clic. Se retira la traza de un precio y su código (`audit_trace` conserva solo los controles).
- **Manual:** las rutas del menú se actualizan a las tarjetas de D-213 (Centro de operación en «DevOps y seguridad») y a la puerta única de la clave (D-202).
- **Pruebas:** `tests/test_quality_audit.py` (columnas en el orden del pipeline, controles al final) y `tests/test_dashboard.py` (D-220: una vista, sin selectores; la evidencia se abre igual).

## D-227 · DuckDB 2.0 queda fuera hasta revisar la consulta de brecha entre canales

- **Fecha:** 2026-10-21. Recuperación posterior a D-226; el CI quedó bloqueado 52 minutos y luego falló.
- **Problema confirmado:** `requirements.txt` pedía `duckdb>=1.1` sin versión máxima y el 21-10-2026 pip pasó a instalar DuckDB 2.0.0. Esa versión trae dos diferencias, medidas aquí contra DuckDB 1.5.6:
  - Una relación ya no tiene `fetchone()` ni `fetchmany()`: `test_d210_the_prd_figures_match_the_served_database` y `tests/test_stack_page.py` llamaban `connection.sql(...).fetchone()`. Afectaba solo a las pruebas; el panel y el pipeline usan `connection.execute(...)`, que devuelve el cursor y conserva `fetchone()`.
  - La consulta `k2_channel_gap` (auto-unión de `weekly_price` con `<>` entre canales) tarda 0,11 s en 1.5.6 y más de 60 s en 2.0.0. La usa el panel (diferencia entre canales y catálogo de consultas), así que un despliegue nuevo habría dejado esa página sin responder, y `test_every_named_query_runs_read_only_with_at_most_20_rows` dejaba colgado el CI.
- **Decisión:** las dos pruebas usan `connection.execute(...)`, que funciona igual en 1.x y 2.x y conserva la consulta y el significado del resultado. `requirements.txt` fija `duckdb>=1.1,<2`; `requirements-pipeline.txt` lo hereda, de modo que el CI, el workflow semanal y el despliegue instalan la misma versión. No se modificó ninguna consulta SQL ni ninguna prueba se omitió.
- **Pendiente:** subir el tope a 2.x cuando `k2_channel_gap` tarde segundos en esa versión (con una reescritura aprobada por el autor o una versión corregida de DuckDB).
- **Pruebas:** con DuckDB 1.5.6, 619 pasan y 3 se omiten; fallan 21 que necesitan red (20 descargan la extensión `sqlite_scanner` y 1 abre GitHub), que este entorno bloquea y que el CI sí puede hacer.

## D-229 · La app vuelve a la base de D-220, sin el ajuste de alto de D-221 a D-226 ni el menú de D-228

- **Fecha:** 2026-10-21. Recuperación a petición del autor.
- **Problema:** el ajuste «cada página cabe en la ventana» (D-222 a D-226) reemplazó vistas que funcionaban: el modelo estrella y la entidad-relación pasaron a un resumen genérico, y el estudio SQL, el Centro de operación y Precios e inflación quedaron con vacíos o con la tabla creciendo. `etl/`, `dbt/` y `agent/` no cambiaron entre D-220 y D-228; el daño está solo en `bi/`, las pruebas y los documentos.
- **Decisión:** el árbol de la app es el de `d1b6a53` (D-220) más dos cambios que no son de diseño: el ajuste del CI (`26f2ec0`) y D-227 (`duckdb<2`). Se hace con un commit que fija ese árbol sobre `main`, sin reescribir el historial: D-221 a D-228 siguen en Git, y el último `main` anterior es `85ca26b`.
- **Queda fuera, a propósito:** `bi/viewport.css`, `bi/viewport.py`, `bi/viewport_frames.css`, el menú plano de D-228 y `docs/diagnosticos/`. El ajuste de alto y el menú se aplicarán después sobre esta base, una pantalla a la vez y sin reemplazar vistas existentes.
- **Pruebas:** 613 pasan y 3 se omiten. Fallan 25 que necesitan red: 20 descargan la extensión `sqlite_scanner` de DuckDB y 5 abren enlaces de GitHub; el entorno de esta sesión las bloquea y el CI sí puede hacerlas. Son las mismas 25 antes y después de D-227.

## D-230 · Etapa 0: medición de las 15 páginas y prueba de no regresión de vistas

- **Problema:** D-226 escondió el modelo estrella y la entidad-relación en un botón y ninguna prueba lo notó; el ajuste de alto se hizo a ojo y rompió otras páginas.
- **Decisión:** antes de tocar el panel se mide. `tests/medicion/medir.cjs` (Playwright, fuera del proyecto) mide las 15 páginas en dos temas y cinco pantallas: alto natural, desplazamiento, vacío inferior, texto menor de 11 px, superposiciones y recortes. El informe y las capturas «golden» (1440 × 900, dos temas) quedan en `docs/diagnosticos/etapa-0/`. Resultado: ninguna página cumple en las tres pantallas; el detalle decide qué se toca en cada etapa.
- **Prueba:** `tests/test_view_regression.py` exige que el SVG de la estrella, de la entidad-relación y del pipeline esté abierto en su página (no dentro de un popover, expander o dialog). Falla en `85ca26b` y pasa en esta base.
- **No cambia** ningún comportamiento del panel, ni `etl/`, `dbt/` ni `agent/`.

## D-231 · Etapa 1: menú lateral plano, con ícono pequeño al plegarse

- **Problema:** el menú eran seis tarjetas de color con bordes brillantes, esquinas, sombras y degradados; al plegarlo, Streamlit usaba como ícono el logo completo (190 px) y se montaba sobre la ruta «Dashboard › Resumen semanal». Además la regla que dejaba espacio arriba al plegar buscaba `aria-expanded`, que el menú no tiene: Streamlit marca el estado con `data-collapsed`, así que nunca se aplicaba.
- **Decisión:** lista plana sobre fondo liso, sin tarjetas, bordes, sombras ni degradados. Rótulo de grupo pequeño en gris y en mayúsculas, con una línea fina entre grupos (unos 24 px de separación). Cada página con un ícono fino de línea y texto de 15 px en gris claro; la página actual, con fondo apenas más claro, esquinas redondeadas y barra azul a la izquierda; al pasar el cursor, un fondo más tenue. «Fuentes de datos» con el ícono de enlace externo. Apariencia y GitHub siguen fijos abajo. Si el menú no cabe, se desplaza solo el menú y su barra aparece al pasar el cursor. El ancho sigue en 300 px, así que el contenido no se mueve.
- **Plegado:** el ícono es un monograma «GO» con los colores del logo (`build_greenocean_icon`); el contenido baja 54 px para que nada se superponga a la ruta. Los selectores usan `data-collapsed`.
- **No cambia:** el nombre «GreenOcean», su logo, el orden ni el contenido de las secciones (D-213 a D-216), ni ninguna página.
- **Pruebas:** `tests/test_dashboard.py` ahora comprueba el menú plano (sin degradado ni sombra en las secciones, línea fina, barra de la página actual, texto de 15 px, un ícono distinto por página) y que los rótulos de grupo ya no llevan «⌄» ni «›». 633 pasan y 1 se omite. Contra las capturas «golden» el contenido tiene 0 píxeles distintos en Vantablack; en Blue Light solo cambia la franja donde el menú viejo proyectaba su sombra.
- **Medido:** a 1440 × 700 el menú tiene 1102 px de contenido y se desplaza solo (sin barra visible); texto mínimo del menú 11,04 px. Evidencia en `docs/diagnosticos/etapa-1/`.

## D-232 · Etapa 2: modelo estrella, entidad-relación y pipeline caben en la ventana

- **Problema:** a 1440 × 900 la estrella quedaba cortada (`dim_channel` bajo el borde) y el Pipeline pedía 994 px. La causa del recorte era una regla de `build_architecture_css`, `max-height: calc((100vh - 360px) * 1.2)`, que dejaba el SVG más alto que el espacio libre.
- **Decisión:** `build_star_svg`, `build_er_svg` y los dos diagramas del Pipeline (recorrido por capas y linaje dbt) se dibujan dentro del marco de zoom que ya existe (`bi/zoom.py`, con +, − y restablecer), con una clase propia de cada página (`fit-modelo`, `fit-pipeline`). El visor mide el ancho que el alto de la ventana permite, según la proporción del propio SVG (`--ratio`, leída de su `viewBox`): el diagrama siempre cabe completo, centrado, sin recortarse. Los botones de zoom pasan a la esquina del panel del Modelo, la leyenda se compacta, y en el Pipeline las cuatro cifras ocupan dos líneas. No cambia el contenido de ningún diagrama ni ninguna cifra, y `star_model.py`, `er_diagram.py` y `architecture.py` no se tocan.
- **Medido** (1440 × 900 / 1440 × 700 / 1920 × 1080, los dos temas): estrella, ER, recorrido por capas y linaje dbt: la ventana no se desplaza en ninguno (`scrollHeight` = `clientHeight`). Escala del diagrama a 1440 × 900: estrella 0,52, ER 0,72, recorrido 0,56.
- **Límite conocido, a decisión del autor:** la estrella mide 1000 × 925 unidades por diseño (fecha arriba, canal abajo), casi cuadrada, y el recorrido del pipeline 1560 × 720. En 900 px de alto caben a la mitad de su tamaño, con texto de 7 a 9 px en reposo; se leen con el zoom. Llegar a 11 px sin zoom exige un diseño más ancho (por ejemplo, `dim_channel` a la derecha de la estrella) y no se hizo porque cambia la forma de la estrella aprobada en D-190.
- **Queda fuera:** «Dónde viven los datos» y «Cruces entre bases» son iframes con un mapa de tamaño fijo; acortarlos recorta el dibujo (se probó y se revirtió). Necesitan escalado interno y siguen en 966 y 996 px de alto natural.
- **Pruebas:** `tests/test_view_regression.py` (estrella, ER y pipeline dentro del marco con `--ratio`, y el cálculo de la proporción). 645 pasan y 1 se omite.

## D-233 · Etapa 4: Precios e inflación y Consultas SQL se ajustan a la ventana

- **Medido antes (D-229):** Precios e inflación, 920 px fijos (20 de más a 900, 220 a 700, 21 % vacío a 1080); Consultas SQL, 1532 px: el explorador de objetos (lista larga) y un editor de hasta 290 px estiraban el estudio, más un pie de página de unos 340 px.
- **Precios e inflación:** las dos filas de tarjetas toman el alto que deja la ventana (`min-height` por tarjeta, con un piso de 165 px) y cada gráfico llena su tarjeta (`st.altair_chart(height="stretch")`, `height="container"` en el `draw_family_card`). Los ocho gráficos ya ocupaban todo el ancho. Resultado: a 1440 × 900 y a 1920 × 1080 la página cabe sin desplazarse, con 5 a 7 % libre abajo; a 1440 × 700 también, con gráficos de unos 85 px de alto (se amplían con «Ampliar»). Colores, valores, escala y botones no cambian.
- **Consultas SQL:** el explorador se desplaza solo (su barra aparece al pasar el cursor), el editor muestra de 6 a 8 líneas con su propio scroll, y la tabla de resultados toma el alto que queda (mínimo 200 px) con cabecera fija y scroll propio en horizontal y vertical, sin salirse de su columna (741 px). Se conservan el explorador, las consultas de ejemplo, las descargas y la protección de solo lectura; no se toca ninguna consulta ni los límites de `bi/sql_explorer.py`.
- **Pie compacto:** `COMPACT_FOOTER_VIEWS` (SQL, Calidad y auditoría, Centro de operación, Mapa de seguridad y Stack y evidencia) cierra con una fila de enlaces más la cita de la fuente, en vez de los dos pies largos (unos 340 px). Los documentos largos conservan el pie completo.
- **Límite conocido:** con resultados en pantalla el estudio pide unos 900 px solo para él (cabecera, filtros, editor, tabla y barra de estado), así que a 1440 × 900 la página aún se desplaza unos 270 px; la tabla muestra 8 filas a 900 y 13 a 1080 (el prompt pedía 12 a 900, que no cabe con el resto de la página). Para lograrlo habría que quitar la fila de filtros o la de consultas de ejemplo, y no se hizo.
- **Pruebas:** 646 pasan y 1 se omite.

## D-234 · Etapa 5: el recorrido del Centro de operación se escala a la ventana

- **Medido antes:** 1027 px a 1440 × 900 y 1440 × 700; el recorrido (iframe de 740 × 640) no se reducía y dejaba 127 px de más.
- **Decisión:** el iframe de la pestaña «Operación» toma el alto que deja la ventana (`max(100vh − 470 px, 225 px)`, con una marca `fit-centro` propia de la página) y el recorrido se escala dentro de él, centrado, con un script fijo (`operation_center.FIT_SCRIPT`: `min(1, ancho/740, alto/640)`). Conserva sus íconos, conexiones y las tres etapas. La pestaña «Plataforma» no se toca.
- **Pie compacto** (D-233): la insignia de dbt ya no se monta sobre el texto de la fuente (había un `margin-top` de 0 en el pie).
- **Medido después:** 900 / 900 y 1080 / 1080 en los dos temas; a 1440 × 700 sobran 8 a 18 px porque el piso de 225 px mantiene el recorrido legible.

## D-235 · Etapa 6: Calidad y auditoría con el alto de la ventana

- **Medido antes:** 1550 px; un iframe fijo de 830 px, y debajo el aviso, las píldoras de evidencia y «Volver a medir», fuera de la pantalla.
- **Decisión:** el iframe toma `max(100vh − 520 px, 360 px)` y su contenido se reduce con un zoom suave (`quality_live.FIT_SCRIPT`, nunca bajo 80 % para mantener el texto legible); lo que no cabe se desplaza dentro del propio panel. Los controles «Abrir la evidencia» y «Volver a medir» quedan visibles sin desplazar la página. No cambia ninguna cifra ni el contenido de la vista.
- **Hallazgo, no regresión:** en este equipo el aviso rojo «Se detectó una discrepancia en los controles locales» es real: `consumer_2026.csv` y `wholesale_2026.csv` locales (12-10) no coinciden con el SHA-256 del manifiesto versionado (descarga del 20-10). Antes quedaba fuera de pantalla. `python agent/agent.py` los vuelve a bajar.
- **Medido después:** 900 / 900 y 1080 / 1080; a 1440 × 700 no cabe (878).
- **Pruebas:** `tests/test_quality_audit.py` ahora acepta un único `<script>`, el zoom fijo, sin datos. 646 pasan y 1 se omite.
- **Queda pendiente de las etapas 5 y 6:** los diagramas nuevos D8 (CI/CD con logos reales) y D10 (puertas de calidad), y los textos de 11 px dentro de los iframes.

## D-236 · Modelo de datos: la estrella primero y «Dónde viven los datos» como arquitectura de almacenamiento

- **Pedido del autor:** el orden debe ser Modelo estrella, Entidad-relación, Dónde viven los datos y, opcional, Cruces entre bases. «Dónde viven los datos» debía verse como una arquitectura de alto nivel, con cilindros, qué relación tiene cada lugar con los otros, flechas rectas y precisas, sin parecer un pipeline ni el «Cruces entre bases», con aspecto de ingeniería.
- **Orden:** `MODEL_VIEWS` = estrella, entidad-relación, dónde viven, cruces. La página abre en la estrella.
- **Rehecho:** `bi/storage_map.py` dibuja cinco zonas: fuentes externas (ODEPA, INE), zona de trabajo fuera de Git (SQLite `raw.db`, Parquet, dbt + DuckDB), base servida versionada en Git (DuckDB con sus 12 tablas en tres grupos y el SQLite de respaldo, unidos por la comprobación de paridad), repositorio de GitHub (`datos.db`, `manifest.json`, `datos.duckdb`) y el panel en Streamlit. Cada base de datos es un cilindro con la marca de su motor; Parquet, que son archivos, se dibuja como una pila de hojas. Todas las líneas son segmentos rectos horizontales o verticales con su cabeza, rotulados por lo que hacen (descarga, copia a Parquet, dbt lee, ETL, publica, commit, despliega); la punteada con dos cabezas es una comprobación, no un flujo. Cada caja explica al pasar el cursor qué guarda, por qué y qué archivo del repositorio la produce.
- **Sin repetir:** el orden de los pasos sigue en «Pipeline y linaje» y los puntos donde dos bases se tocan, en «Cruces entre bases». `bi/database_map.py` queda como biblioteca de los almacenes y las marcas que usan los demás diagramas, sin el dibujo viejo (cadena de logos, flechas con codos y diagonal de la paridad).
- **Ajuste a la ventana:** el iframe toma el alto que deja la pantalla y el dibujo se escala dentro de él (`viewBox` y `preserveAspectRatio`), sin recortarse. Medido en Vantablack y Blue Light: 900 / 900, 700 / 700 y 1080 / 1080. El texto más chico del dibujo es de 12,5 unidades: 11 px o más a 1440 × 900.
- **Datos reales:** los tamaños y los conteos se leen de los archivos y de la base; el SQLite de 665 MB se muestra con «≈» cuando no está en este equipo.
- **Pruebas:** `tests/test_storage_map.py` reemplaza a `tests/test_database_map.py`: cada tienda con su archivo y su ayuda («Qué guarda», «Por qué», «Fuente»), cilindros solo en las bases de datos, cada línea recta, las 12 tablas en tres grupos, los tamaños sin inventar, que cada archivo fuente exista en el repositorio y el tamaño mínimo del texto. 644 pasan y 1 se omite.

## D-237 · «Cruces entre bases» como lectura guiada, no como un segundo diagrama de flechas

- **Problema (autor):** tras D-236 todo el Modelo de datos quedó como se esperaba, salvo «Cruces entre bases»: seguía siendo una cadena de logos con números, una flecha curva y otra en diagonal, parecida al pipeline y sin enseñar qué pasa en cada cruce (todo estaba escondido tras el cursor).
- **Decisión:** `bi/database_crossings.py` muestra los ocho cruces como ocho filas legibles de arriba hacia abajo, agrupadas en cuatro momentos: *Entra el dato* (ODEPA → raw.db, INE → Bronce, raw.db → Bronce), *Se transforma y se publica* (Bronce → dbt, dbt → datos.duckdb), *Se comprueba por otro camino* (ETL en Python → datos.db, paridad entre datos.duckdb y datos.db) y *Se recuerda* (datos.duckdb → próxima carga). Cada fila dice, sin hover: de qué almacén a cuál (con las mismas marcas, cilindros y carpetas de «Dónde viven los datos»), cómo pasa, qué viaja, por qué clave se cruzan los dos lados y la comprobación de ahora, con su color (comprobado, no medible aquí, dato). La flecha es una línea recta; la paridad es la única punteada con dos cabezas. El texto largo de cada cruce sigue en la tarjeta que aparece al pasar el cursor por la fila.
- **Sin repetir:** el dibujo de los almacenes vive solo en «Dónde viven los datos»; aquí cada cruce es una fila. Se retiran las posiciones de los logos, las flechas con codos y la curva de `etl_run`. Los cruces se renumeran en el orden de la historia (antes seguían el orden de la lista anterior).
- **Datos reales:** las comprobaciones se leen en vivo de la base (semanas con índice, tablas publicadas, cargas registradas, paridad de filas, rechazos y suma); lo que depende de `raw.db` dice «no medible aquí» cuando el archivo no está en el servidor, sin darlo por bueno.
- **Ajuste a la ventana:** el iframe toma el alto que deja la pantalla y la página se reduce con un zoom suave (`FIT_SCRIPT`, nunca bajo 90 %). A 1440 × 900 y a 1920 × 1080 entran los ocho cruces completos; a 1440 × 700 se desplaza dentro del propio panel.
- **Pruebas:** `tests/test_database_crossings.py` verifica los cuatro momentos y su orden, que cada fila trae mecanismo, qué viaja y clave compartida en el texto de la página, que solo la paridad apunta en los dos sentidos, que las marcas son las del mapa de almacenamiento y que el único script es el zoom fijo. 648 pasan y 1 se omite.

## D-238 · La estrella y el Pipeline usan todo el ancho de su tarjeta

- **Problema (autor):** tras D-232 el Pipeline y la estrella se veían muy chicos, con espacio de sobra a los lados, y el zoom recortaba parte del diagrama. El autor tenía razón: para no desplazar la ventana limité los diagramas por el alto y dejé sin usar el ancho de la tarjeta.
- **Pipeline y linaje:** el diagrama ocupa los 938 px de la tarjeta (antes 563 a 900 px de alto de ventana). Las pestañas «Recorrido por capas» y «Linaje dbt» pasan a la fila del título, que recupera 44 px, y el alto reservado baja de 510 a 440 px. A 1440 × 900 y a 1920 × 1080 cabe sin desplazar; solo cuando la ventana es más baja que el diagrama a ancho completo (1440 × 700) se reduce por alto y se acerca con el zoom.
- **Estrella:** `bi/star_model.py` ya no apila fecha, hecho y canal en vertical (1000 × 925, casi cuadrada). Ahora son tres columnas, de 1000 × 572 (proporción 1,75): el IPC sobre `dim_date` a la izquierda; `weekly_price` al centro con la auditoría de cargas debajo; `dim_product`, `dim_region` y `dim_channel` a la derecha, con los conectores desde el hecho. Se conservan todas las tablas, columnas, claves, medidas y cifras. Ocupa los 938 px de la tarjeta, con texto de 13 a 17 px (antes unos 7 a 9 px).
- **Encabezado de Modelo de datos:** el título y las tres cifras van en una fila y la descripción, de una línea, debajo (antes se superponían a la descripción larga). Los botones de zoom del modelo pasan a la fila de la leyenda y ya no tapan ninguna tabla.
- **Medido** (Vantablack y Blue Light): estrella 900 / 900 y 1080 / 1080 con 938 px de ancho a 900; recorrido 900 / 900 y 1080 / 1080 con 938 px; linaje igual. A 1440 × 700 se escalan por alto (la estrella, 594 px).
- **Pruebas:** `tests/test_star_model.py` reemplaza el supuesto vertical (fecha arriba, canal abajo) por el de tres columnas (el hecho al centro, `dim_date` a la izquierda, las otras tres a la derecha, el IPC sobre `dim_date`, proporción de al menos 1,6) y que ninguna tabla ni grupo se superponga.

## D-239 · «Cruces entre bases»: las bases en capas y las líneas entre sus tablas

- **Problema (autor):** la lectura guiada de D-237 era una tabla de filas: no se veía ningún cruce, y el nombre promete justo eso, varias bases organizadas como arquitectura y flechas que muestren por dónde se cruzan.
- **Decisión:** `bi/database_crossings.py` dibuja cada base como una capa con las tablas reales que participan: las fuentes (INE, ODEPA consumidor y mayorista), `raw.db` (`raw_consumer`, `raw_wholesale`), el bronce Parquet (`ine_ipc`, `odepa_consumer`, `odepa_wholesale`), la base de trabajo de dbt (`stg_*` y las marts `ipc_weekly` y `weekly_price`), `datos.duckdb` (las mismas más `etl_run` y `rejection`, y el resto de sus 12 tablas) y, a la derecha, `datos.db`. Una línea recta une la tabla de una base con la que alimenta o con la que se compara en otra, y lleva lo que las une: descarga, fuente y año, «dbt lee», publica, ETL, paridad, y `week_start` (por donde se cruzan ODEPA y el INE) y `run_id` (`etl_run` con `rejection`). El INE baja en línea recta por encima de `raw.db` sin tocar ninguna de sus tablas: se ve que no pasa por SQLite.
- **Los ocho cruces** siguen numerados en el orden de la historia, con su marca coloreada por la comprobación de ahora (verde comprobado, ámbar no medible aquí, gris dato). Al pasar el cursor por una marca aparece la tarjeta con cómo pasa, qué viaja, con qué se cruzan y la comprobación. Las comprobaciones se leen en vivo de la base; lo que depende de `raw.db` dice «No medible aquí».
- **Sin repetir:** el dibujo de los almacenes (zonas, Git, Streamlit) vive en «Dónde viven los datos»; aquí se ven las tablas y sus claves. Se retira la tabla de filas de D-237.
- **Ajuste a la ventana:** el iframe toma el alto que deja la pantalla y el dibujo se escala dentro de él. Medido en los dos temas: 900 / 900, 700 / 700 y 1080 / 1080. El texto más chico es de 12,5 unidades.
- **Pruebas:** `tests/test_database_crossings.py`: cada línea recta; el INE no coincide en columna con ninguna tabla de `raw.db`; cada tabla dibujada existe en el repositorio (el código de `etl/etl.py` y `etl/bronze.py`, los modelos de dbt y las tablas servidas); ocho marcas con su tarjeta y su comprobación; el texto mínimo. 650 pasan y 1 se omite.

## D-240 · Etapa 3: casos de uso, trazabilidad y requisitos medibles en el PRD

- **Decisión:** el PRD queda con el problema, el alcance, los usuarios, las preguntas de negocio y los requisitos. Se retira «Visión y misión» (no es problema, usuarios ni requisitos). El diagrama de contexto («actores») pasa al SAD como «1. Contexto», que es su lugar, y el PRD recibe el diagrama D2 de **casos de uso** (`[[diagrama:casos]]`, `bi/doc_views.py`): los cuatro perfiles de «3. Usuarios» a la izquierda, el sistema GreenOcean en el centro con sus casos, y a la derecha GitHub Actions (RF-01 a RF-04) y el administrador (consultas SQL puntuales, carga manual con la clave, mantener el código y los secretos). Bajo cada caso va la pantalla del menú que lo atiende; las líneas son rectas.
- **Trazabilidad:** «4. Preguntas de negocio» es una tabla pregunta → pantalla → evidencia. P-1 apunta al Resumen semanal; P-2 y P-3, a las consultas «Precio vs. época» y «Brecha mayorista» del estudio SQL, porque desde D-163 «Precios e inflación» responde otra pregunta.
- **Requisitos medibles:** «5. Requisitos» pasa de «cómo se verifica» a un criterio medible y la evidencia, con el archivo o la prueba. Los requisitos sin prueba automática se listan en `docs/diagnosticos/etapa-3/pendientes-para-el-autor.md`; no se rellenan.
- **Pruebas:** `tests/test_prd_traceability.py` comprueba que cada pantalla sea una página del menú, que cada consulta de ejemplo exista, que cada archivo y cada prueba que el PRD nombra exista, que los casos de uso salgan de los cuatro perfiles del PRD con la misma pantalla que su tabla, y que el workflow corra los martes a las 12:00 UTC (RF-01). El PRD se permite en 3 páginas de PDF (los demás, 2), a revisar en la Etapa 10. 656 pasan y 1 se omite.
- **Encabezados del PRD:** quedan numerados 1 a 6; las referencias a «Pantallas» (capturas) siguen igual.

## D-241 · Calidad y auditoría: sin huecos, con el aviso preciso y toda la evidencia a la vista

- **Problema (autor):** la página se veía rara. Quedaba un hueco grande bajo «Completitud» y «Actualidad»; una barra roja enorme («Se detectó una discrepancia en los controles locales») contradecía el «11 indicadores dentro de su umbral» y la «Carga correcta»; la fila «Abrir la evidencia de» se cortaba en el borde con píldoras fuera de vista; y D-235 había dejado los «Controles de auditoría» escondidos dentro del scroll del iframe.
- **Hueco:** «Qué se apartó y por qué» pasa a la columna de «Completitud» (filas leídas = cargadas + rechazadas) y «Cargas · filas leídas» a la de «Actualidad», en vez de ir debajo, a todo el ancho. Las columnas quedan parejas y la página se acorta.
- **Aviso:** la barra roja se vuelve un aviso ámbar que dice qué pasa y qué no: «En este equipo, consumer_2026.csv y wholesale_2026.csv no coincide con la huella SHA-256 de la última descarga (manifest.json). Los indicadores se miden en la base publicada y no cambian». Solo es rojo cuando la base publicada falla sus controles de integridad. En producción, sin los CSV, no aparece.
- **Evidencia:** las 11 píldoras de «Abrir la evidencia de» saltan de línea (3 filas) en vez de correr fuera del borde; los títulos pequeños suben a 11 px.
- **Alto:** el iframe vuelve a medir lo que su contenido (600 px) y ya no tiene scroll propio; los controles de auditoría se ven completos. A cambio la página se desplaza unos 250 px a 1440 × 900: preferimos no esconder controles a forzar el ajuste (esto reemplaza el criterio de alto de D-235).
- **Pruebas:** `tests/test_quality_audit.py` verifica que las dos listas estén dentro de las columnas 1 y 2 y que no exista el bloque inferior. 656 pasan y 1 se omite.

## D-242 · El SAD abre con un diagrama de contexto, no con un flujo de entrega

- **Problema (autor):** el «1. Contexto» del SAD era el antiguo diagrama «actores»: no tenía un nombre claro y parecía de DevOps más que de arquitectura global. Tenía razón. Mezclaba dos niveles: el contexto (quién usa el sistema y de qué sistemas externos depende) con el flujo de entrega (GitHub Actions → repositorio → panel, con `commit`, `main`, `git push` y `clave`). Yo lo pasé al SAD en D-240 sin revisarlo, aunque el plan advertía que cada nivel va en su propio diagrama.
- **Decisión:** `bi/doc_views.py` dibuja el **diagrama de contexto del sistema** (nivel 1 del modelo C4): GreenOcean como una sola caja, las personas que lo usan arriba (visitante y administrador) y los sistemas externos a los lados (ODEPA y el INE, de donde toma los datos; GitHub y Streamlit Community Cloud, donde vive). La flecha va de quien usa a quien es usado, con un verbo: «lee», «mantiene», «CSV», «IPC», «aloja», «publica». Nada de lo que hay dentro de la caja se dibuja ahí: el pipeline, la plataforma y el modelo de datos son las vistas siguientes del SAD.
- **El flujo de entrega** (Actions, repositorio, `main`, `git push`) no se pierde: es del diagrama de CI/CD de la página DevOps (la siguiente etapa) y del despliegue del SAD.
- **Nombre:** «Contexto» (marcador `[[diagrama:contexto]]`, antes `actores`). El texto del SAD dice qué es GreenOcean, qué lee y de qué servicios se apoya, sin repetir el diagrama.
- **Pruebas:** `tests/test_doc_diagrams.py` verifica que sea una sola caja con seis marcas (dos personas y cuatro sistemas), que cada flecha sea ortogonal y toque la caja, que cada marca y cada flecha se explique al pasar el cursor, y que ni «GitHub Actions», ni «Repositorio» ni «git push» aparezcan. 656 pasan y 1 se omite.

## D-243 · Etapa 5: diagrama de CI/CD con su definición, desde los workflows reales

- **Pedido (autor):** que en alguna parte se defina qué es CI/CD.
- **Decisión:** el Centro de operación (bloque «DevOps y seguridad») gana la pestaña **CI/CD**. Arriba, dos recuadros definen los términos en una frase cada uno: **CI, integración continua** («cada vez que alguien sube un cambio, un servidor lo prueba solo; si algo se rompe, se ve en el momento y no a fin de mes») y **CD, entrega continua** («lo que pasa todas las pruebas llega a producción sin pasos manuales; aquí, la base de cada martes y el panel que la muestra»). El glosario gana la entrada CD (la de CI ya existía).
- **Diagrama (`bi/devops.py`, sube de nivel el ciclo de seis etapas, que no se mostraba en ninguna página):** tres carriles con los logos reales de Git, GitHub, pytest, dbt, SQLite, Python y Streamlit. **CI** (`pruebas.yml`): cambio → GitHub Actions → `dbt parse` → `pytest` → resultado. **CD** (`semanal.yml`): disparo del martes a las 12:00 UTC o a mano → descarga de ODEPA → ETL de respaldo → `dbt build` (31 pruebas) → `pytest` contra la base nueva (marcada como **puerta**) → guardar con un commit → informe como issue. **Publicación:** rama `main` → Streamlit Cloud, esta última con borde punteado porque es una configuración de esa plataforma y no está en el repositorio. Debajo del carril CD, la frase del propio workflow: si un paso falla, los siguientes no corren y la base publicada no cambia. Cada caja explica al pasar el cursor qué hace y dónde está.
- **Solo lo que existe:** cada caja apunta a un texto del workflow (el nombre de su paso o su comando); no hay reintentos, colas ni otros workflows. Los dos workflows son los únicos de `.github/workflows/`.
- **Pruebas:** `tests/test_devops.py` verifica que cada caja nombre texto que exista en su workflow, que los disparadores dibujados sean los del archivo, que los pasos de la carga vayan en el orden del workflow y la puerta antes de guardar, que la definición diga qué son CI y CD, que haya una tarjeta y una ayuda por paso con logos reales y sin script, y que las líneas sean rectas. `tests/test_tech_glossary.py` deja de usar el ciclo viejo. Se retira el CSS del ciclo antiguo. 659 pasan y 1 se omite.

## D-244 · Sin código muerto, P-4 en el PRD y cada respuesta recalculada por otro camino

- **Pedido del autor:** el código que no se usa se borra («está haciendo ruido»); la pregunta que responde «Precios e inflación» entra al PRD como P-4; y lo más importante: que todo cuadre, sin desacuerdos entre el PRD, el panel, las consultas y los datos.
- **Código muerto:** un análisis de `bi/` encontró 70 funciones y 57 constantes que ninguna pantalla, ningún script del pipeline ni el agente usaban (los restos de la antigua página «Contexto del precio», de vistas retiradas, del explorador por clics y de catálogos de consultas). Se borran, junto con tres módulos que quedaron vacíos (`bi/market_charts.py`, `bi/market_style.py`, `bi/price_context.py`; los nombres de los meses salen del idioma de los gráficos) y las 78 pruebas que solo probaban ese código. Se borran también los imports sin uso. Dos pruebas que cayeron por usar un ayudante borrado pero protegían algo vivo se reponen sin él: las 14 consultas con nombre de `bi/queries.sql` corren sobre la base servida, y cada enlace del panel a GitHub apunta a un archivo que existe.
- **P-4:** «¿Qué alimentos subieron más que la inflación?» → Precios e inflación. El perfil Analista de pricing la incluye, y el diagrama de casos de uso le da su caso.
- **Cada respuesta del PRD se recalcula por otro camino:** P-2 («Precio vs. época») y P-3 («Brecha mayorista») se rehacen en pandas desde las vistas, sin la lógica del SQL, y coinciden con la consulta del estudio; P-4 se rehace en SQL desde las tablas y coincide con la página (cada familia, el IPC y el veredicto); P-1 se respalda con la prueba que calcula las alertas por dos caminos (SQL y Python). Así un error de cálculo en una consulta o en una página hace fallar una prueba.
- **Datos locales:** se volvieron a descargar los CSV de ODEPA (`agent/agent.py`). `wholesale_2026.csv` coincide con la huella de la carga publicada; `consumer_2026.csv` es una versión posterior que ODEPA publicó después del 20-10. El `manifest.json` versionado no se reemplaza, porque describe los archivos con que se construyó la base publicada. Se refrescó solo `raw.db` local, que estaba en el 12-10 y hacía fallar la auditoría que recalcula precios desde las filas crudas (ahora pasa). El aviso de Calidad dice ahora que el archivo «es de otra descarga o fue alterado», sin suponer que es anterior.
- **Pruebas:** 583 pasan y 1 se omite (eran 659: salen las 78 del código muerto y entran las de recálculo).

## D-245 · Etapa 6: las puertas de calidad sobre el recorrido, y RF-03 con su prueba

- **Diagrama D10, puertas de calidad (*quality gates*):** dónde se frena un dato malo. No se dibuja aparte, para no repetir el recorrido que la página Calidad y auditoría ya tiene: las tres puertas van sobre sus flechas. **Puerta 1 · el archivo** (Fuentes → Aterrizaje): un CSV vacío o con columnas distintas no se guarda; uno con muchas menos filas o una semana faltante detiene la carga. **Puerta 2 · cada fila** (Aterrizaje → dbt): un precio no positivo o con formato inválido se rechaza a la tabla `rejection` con su motivo; una unidad no convertible o un precio atípico se marca y queda fuera de los indicadores. **Puerta 3 · la base** (dbt → `datos.duckdb`): si falla una prueba de dbt, si la carga lee menos del 90 % de la anterior o si pytest falla sobre la base nueva, la base no se publica y la carga queda como fallida. Cada puerta muestra su cifra de esta carga (201 rechazadas · 13.347 marcadas; 31 de 31 pruebas dbt), leída de la base y con el color de su estado, y al pasar el cursor dice qué frena, qué pasa con el dato, dónde está y qué prueba lo respalda.
- **RF-03 con prueba:** `tests/test_pipeline_gate.py` comprueba que `etl/pipeline.py` no reemplaza la base publicada cuando `dbt build` falla ni cuando la carga lee menos del 90 % de la última buena, y que registra la carga fallida; y que una carga buena es la única que la reemplaza, con leídas = cargadas + rechazadas. El PRD lo cita como evidencia y sale de la lista de pendientes.
- **Coherencia:** `tests/test_quality_audit.py` verifica que las cifras de las puertas sean las mismas que las de los indicadores de la página. El PRD no tiene tope de páginas (el autor pone la coherencia por delante del largo).
- **Pruebas:** 587 pasan y 1 se omite.

## D-246 · Etapa 7: la orquestación del workflow semanal, dentro del diagrama de CI/CD

- **Decisión (autor):** el diagrama de orquestación (D7) se fusiona con el de CI/CD para no repetir el mismo recorrido en dos lugares. El carril «CD · entrega continua y orquestación» dibuja ahora los nueve pasos con nombre de `semanal.yml`, numerados y en su orden real, en dos filas (de izquierda a derecha y de vuelta): 1 · Año vigente, 2 · Caché de años cerrados, 3 · Descarga de ODEPA, 4 · ETL de respaldo SQLite, 5 · dbt build, 6 · Falla simulada, 7 · pytest contra la base nueva, 8 · Guardar con un commit y 9 · Informe.
- **Disparadores:** el cron del martes a las 12:00 UTC y la ejecución manual (desde el Centro de operación, con la clave de control, por la API de GitHub; o desde GitHub). La falla simulada se marca como **opcional** y con borde punteado: solo corre cuando una ejecución manual desde GitHub pide `simulate_failure`; el botón del panel nunca la pide (`bi/control.py` envía `False`). El CI tiene su propio disparador (push y pull request).
- **Puertas:** `pytest` en el CI, y `dbt build` y `pytest` contra la base nueva en el job semanal, antes de guardar. Salidas: la base servida en `main` (que publica el panel) y el informe como issue.
- **Cada paso apunta a su línea:** al pasar el cursor, cada caja dice qué hace, el nombre de su paso y en qué línea de su workflow está («semanal.yml, línea 46»). La línea se lee del archivo, así que no se desfasa si el workflow cambia.
- **No se dibuja** nada que los workflows no tengan: ni reintentos, ni colas, ni otros workflows.
- **Pruebas:** `tests/test_devops.py` verifica que cada paso con nombre de `semanal.yml` esté dibujado, numerado y en su orden; que cada caja nombre texto real de su workflow y su línea apunte a ese texto; que las puertas sean las tres de arriba; y que el panel nunca pida la falla simulada. 589 pasan y 1 se omite.

## D-247 · Etapa 9: el SAD por vistas, con contenedores (C4) y sin copiar diagramas

- **Decisión:** el SAD describe la arquitectura por vistas, cada una en un solo lugar. Vistas propias del SAD: **1. Contexto** (C4 nivel 1, D-242) y **2. Contenedores** (C4 nivel 2, nuevo, `bi/doc_views.py`): dos aplicaciones (la **carga semanal**, Python · requests · dbt Core · DuckDB, que es un solo contenedor porque agente, ETL y dbt corren en el mismo job; y el **panel web**, Streamlit) y tres almacenes (**archivos de trabajo**, **base servida** `etl/datos.duckdb` y **respaldo** `etl/datos.db`), con ODEPA, el INE, GitHub y las dos personas afuera. Cada caja dice su tecnología y sus archivos; cada flecha es un segmento recto que va de quien usa a quien es usado y dice qué hace («lee y escribe», «publica», «lee · solo lectura», «lanza el workflow · API REST», «ejecuta cada martes», «commit de la base»).
- **Vistas enlazadas, no copiadas:** **3. Datos** enlaza a Pipeline y linaje y a Modelo de datos; **4. Despliegue** describe dónde corre cada pieza y dónde vive `datos.duckdb`, y enlaza al diagrama de despliegue; **5. Seguridad** enlaza al Mapa de seguridad y al Plan de pruebas. El SAD ya no copia el recorrido del pipeline, la plataforma ni la estrella. **6. Componentes** (C4 nivel 3) se omite y el documento dice por qué: el panel es una sola aplicación y la carga ya se ve paso a paso en el CI/CD y en el linaje.
- **Despliegue:** el diagrama que la pestaña del Centro de operación llamaba «Plataforma» es un diagrama de despliegue (dónde corre cada pieza, con su estado en vivo). La pestaña toma su nombre estándar, «Despliegue», y es su único lugar; el SAD enlaza a ella. Esto se aparta del plan, que ponía el despliegue en el SAD, para no tener dos dibujos de lo mismo.
- **Enlaces de documento a página:** el marcador `[[vista:Página]]` se dibuja en el panel como enlace a esa página del menú y en el PDF como «Página» (página del panel). Una prueba exige que cada marcador nombre una página real del menú.
- **Tamaño:** los diagramas de los documentos usan todo el ancho de la tarjeta, de modo que su texto queda a tamaño real; el alto del marco se ajusta a su dibujo, sin franjas vacías.
- **Pruebas:** `tests/test_doc_diagrams.py` verifica el diagrama de contenedores (tipos de caja, dos aplicaciones, archivos que existen en el repositorio, una ayuda por caja, flechas rectas) y los enlaces de los documentos. 593 pasan y 1 se omite.

## D-248 · Etapa 10: documentos al estándar y el PDF es la página impresa

- **Descargas (decisión del autor: el archivo debe ser exactamente la página):** se elige la opción C. El botón «Imprimir o guardar como PDF» imprime la página misma con una hoja de estilos de impresión propia de las páginas de documentos (PRD, SAD, ADR, Plan de pruebas de seguridad y Escalabilidad): oculta solo el menú y la navegación, deja correr la página completa, conserva los colores del tema, imprime los diagramas y reduce la página a la hoja A4 desde su ancho de pantalla, para que el papel muestre las mismas líneas que la pantalla. Es idéntica por construcción, no depende de que corra un workflow y no agrega dependencias: al contrario, se retiran `bi/document_pdf.py`, reportlab y plotly (este último ya no lo usaba ningún módulo tras D-244).
- **Prueba de identidad:** `tests/medicion/imprimir.cjs` imprime cada documento con Chrome, comprueba que el menú no se imprima y que los títulos de sección y los diagramas visibles al imprimir sean los mismos, en el mismo orden, que en pantalla y que en su `.md`. Los cinco dan OK. `tests/test_documents.py` (reemplaza a `tests/test_document_pdf.py`) verifica la hoja de impresión, los diagramas de cada documento, las cifras del PRD contra la base, el formato del ADR y los tamaños de archivo que citan los documentos.
- **ADR:** pasa de una tabla a diez entradas con el formato estándar: estado, contexto, decisión, alternativas y consecuencias, cada una con su D-xxx. ADR-04 decía «hasta 46 MB» por CSV anual; el mayor pesa unos 65 MB. ADR-19 dice que no se registró una alternativa, en vez de inventarla.
- **PRD:** capturas nuevas de las páginas actuales, una por tema existente (Vantablack, Dark Grey, Corporativo y Blue Light en teléfono); la anterior M-2 usaba el tema «Claro», retirado. «Compras y abastecimiento» ya no dice «por canal», porque la consulta de P-3 compara por producto.
- **MANUAL y textos del panel (`docs/PROYECTO.md`):** se reescriben al estado actual: los nueve pasos del job con dbt, el aterrizaje en `raw.db`, el bronce en Parquet y la base servida en `datos.duckdb`, el bloqueo de la clave, el menú de hoy, y sin la recomendación de pasar a PostgreSQL (contraria a ADR-31) ni las guías de páginas retiradas. La hora del job se corrige en todas partes: 12:00 UTC son las 09:00 en Chile en horario de verano y las 08:00 en invierno (decían «09:00, horario estándar»).
- **CI/CD:** el carril CI dice ahora que su resultado avisa pero no detiene la publicación: Streamlit publica `main` sin esperarlo.
- **Tabla por documento:** `docs/diagnosticos/etapa-10/tabla-de-documentos.md`. Pruebas: 583 pasan y 1 se omite.

## D-249 · Etapa 8: la seguridad como proceso, su procedimiento y el monitoreo

- **Clave de control sin límite de intentos (decisión del autor):** se retira el bloqueo de D-199 (5 claves incorrectas en 15 minutos bloqueaban el acceso 15 minutos, con un segundo de espera por error). `bi/control.py` conserva la comparación en tiempo constante sobre bytes UTF-8 (`hmac.compare_digest`) y responde «Clave incorrecta.» cada vez. El riesgo queda aceptado y escrito, no escondido: la clave solo evita que alguien pulse «Ejecutar pipeline ahora» por accidente y, con ese botón, lo máximo que se puede hacer es lanzar el workflow. El caso S-05 pasa a comprobar que no hay bloqueo y que la comparación sigue siendo de tiempo constante.
- **Arquitectura de seguridad:** el «Mapa de seguridad» se reemplaza por un modelo de amenazas que se lee como un proceso, de izquierda a derecha: amenaza (con su categoría del OWASP Top 10 de 2021), mitigación, verificación y activo protegido. Seis amenazas y siete controles; cada control nombra sus archivos y sus pruebas, y la verificación muestra los casos S-xx del plan. Debajo, el ciclo de mejora continua: revisar, atacar, corregir, probar y repetir. Como pidió el autor el 21-10-2026, el estudio de Consultas SQL se dibuja como acceso público con sus límites (una sentencia de solo lectura, 10 segundos, 5.000 filas, 1 GB), y el inicio de sesión de GitHub y Streamlit Cloud con borde punteado: lo declara el autor y no se puede verificar desde el repositorio. La página toma ese nombre en el menú; su dirección sigue siendo `mapa-de-seguridad`, para no romper enlaces guardados.
- **Procedimiento de pruebas (SOP):** el Plan de pruebas de seguridad dibuja su procedimiento en cinco pasos (preparar, ejecutar, comprobar, registrar y decidir), con la vuelta al paso 2 cuando un caso falla, y cada paso explica cómo se hace al pasar el cursor. Cada caso S-01 a S-10 nombra su prueba exacta (`archivo::prueba`). El plan ya no repite las amenazas: enlaza a la página.
- **Monitoreo:** nueva pestaña del Centro de operación con las ocho señales que existen en el código: de dónde salen, el archivo que las produce, qué registran y dónde se leen (en el panel o por el autor). La banda de observabilidad de Pipeline y linaje muestra esas mismas señales sobre el recorrido, y la pestaña enlaza a ella en vez de repetirla.
- **Centro de operación:** las pestañas quedan en el orden pedido por el autor: Despliegue, CI/CD, Operación y Monitoreo. Despliegue muestra solo el diagrama de despliegue; se retiran las tarjetas por capa y su diálogo, que repetían ese diagrama.
- **Contexto del SAD:** la caja de GreenOcean muestra los logos de las herramientas que usa por dentro (Python, SQLite, Parquet, dbt, DuckDB y Streamlit), como pidió el autor.
- **Sin repetición:** `docs/PROYECTO.md` deja las secciones DevOps, Seguridad, Observabilidad e Informes, que repetían las páginas. Los documentos ya no dibujan diagramas vivos; enlazan a su página con `[[vista:…]]`, y se retira el código que los dibujaba.
- **Pruebas:** `tests/test_security.py` verifica las cuatro columnas, el ciclo y que cada prueba nombrada por un control exista; `tests/test_monitoring.py`, que cada señal nombre un archivo que existe y la produce, y que las tablas que lee el panel estén en la base servida; `tests/test_control.py`, la clave sin bloqueo. 588 pasan y 1 se omite. Impresión: los cinco documentos coinciden con su página (`tests/medicion/imprimir.cjs`). Capturas en los dos temas: `docs/diagnosticos/etapa-8/`.

## D-250 · Etapa 11: revisión global; la ruta de cada página y su pie siguen al menú

- **Medición final:** las 15 páginas del menú, en los dos temas, en tres pantallas de computador y dos de teléfono (`tests/medicion/medir.cjs`). Frente a la Etapa 0, el SAD pasa de 171 textos menores de 11 px a ninguno, la Arquitectura de seguridad de 1 a ninguno y el Plan de pruebas de seguridad de 8 a ninguno, sin sus 4 superposiciones. El informe, las tablas y las capturas están en `docs/diagnosticos/etapa-11/`.
- **Ruta y pie según el menú:** la ruta sobre cada página nombraba las secciones internas del panel («Dashboard › Consultas SQL», «Documentación › SAD · Arquitectura», «Seguridad › …»), que no son las del menú, y el pie llevaba a la sección anterior y a la siguiente de esa ruta interna («← Volver: Dashboard» en el Centro de operación). Ahora la ruta usa la sección y el nombre que muestra el menú («Ingeniería de datos › Consultas SQL»), y el pie lleva a la página anterior y a la siguiente del menú, con su ícono del menú («← Anterior: SAD · Arquitectura», «Siguiente: Arquitectura de seguridad →»). Si la página da nombre a su sección, la ruta muestra solo su nombre («Stack y evidencia»).
- **Resumen semanal frente a su captura de referencia de la Etapa 0:** idéntico salvo esa línea de la ruta, que dice «Negocio · BI» en vez de «Dashboard» (la diferencia de píxeles queda dentro de la franja de la ruta, en los dos temas).
- **Casos de uso del PRD:** el detalle de cada caso y el nombre de cada actor pasan de 10,3 px a 11,2 px, y los óvalos crecen para que quepa la línea más larga. El PRD queda sin texto menor de 11 px.
- **Medición:** `medir.cjs` sigue esperando cuando la primera carga redirige a la dirección de la primera página; antes se detenía.
- **README:** la lista de diagramas del panel incluye el monitoreo y la arquitectura de seguridad.
- **Una sola cuenta de pruebas:** «Stack y evidencia» y el diagrama de despliegue contaban las funciones de prueba con dos funciones iguales; ahora las dos usan `project.count_test_functions` (453 funciones de prueba más las 31 pruebas de dbt dan las 484 de «Stack y evidencia»).
- **Queda abierto, con su causa, en el informe:** los diagramas densos de Pipeline y linaje, Despliegue y Calidad y auditoría tienen textos de 8,7 a 10,9 px que se leen con su zoom; llevarlos a 11 px es rediseñarlos. Once vistas antiguas sin enlace desde el menú (27 funciones, 369 líneas) siguen abiertas para direcciones guardadas; retirarlas cambia adónde llegan esas direcciones y se deja a decisión del autor.
- **Pruebas:** `tests/test_dashboard.py::test_d250_the_path_and_the_footer_follow_the_menu`. 589 pasan y 1 se omite; los cinco documentos impresos coinciden con su página.

## D-251 · El pipeline, la estrella y la operación vuelven a como estaban en D-229

- **Problema (autor):** el pipeline y el modelo estrella estaban bien en D-229 y no se pidió cambiarlos. D-232 los metió en un marco que se ajusta al alto de la ventana: en una pantalla más baja que 1440 × 900 el pipeline se achicaba, y con el zoom se perdían partes del dibujo. D-238 cambió la estrella a tres columnas. En el Centro de operación, D-234 achicó el recorrido de la carga para que cupiera en la ventana, y D-249 dejó «Operación» en la tercera pestaña, de modo que al abrir la página ya no se veía «Acceso del autor» (la clave, el botón «Ejecutar pipeline ahora» y los enlaces del autor).
- **Decisión del autor: se restaura lo que estaba bien.**
  - **Pipeline y linaje:** vuelve el marco de zoom de D-229, a todo el ancho de la tarjeta, con las cifras y las pestañas como estaban. Se retiran las reglas `fit-pipeline` de D-232 y D-238.
  - **Modelo estrella:** vuelve el dibujo de D-229 (`bi/star_model.py` y `tests/test_star_model.py`), sin marco y con su tamaño de D-229. La entidad-relación, Dónde viven los datos, Cruces entre bases, el encabezado de la página y el orden de las vistas (la estrella primero, pedido del autor) no cambian.
  - **Centro de operación:** abre otra vez en «Operación», con el recorrido de la carga a su tamaño de D-229; siguen Despliegue, CI/CD y Monitoreo. Se retira el ajuste a la ventana de D-234 (`fit-centro` y el script que escalaba el recorrido). Se conserva la corrección de la hora de Chile en la ayuda del paso «Lanzar».
- **Comprobación:** contra D-229, ejecutado aparte con Playwright, en los dos temas. El pipeline queda en la misma posición y con el mismo tamaño a 1280 × 800, 1440 × 900, 1512 × 782 y 1920 × 1080; las únicas diferencias de píxeles (hasta 379) son los puntos animados del recorrido. La estrella es idéntica píxel a píxel en esos cuatro tamaños; solo empieza más arriba, porque el encabezado de Modelo de datos es más bajo. El recorrido de «Operación» es idéntico píxel a píxel a 1440 × 900 y 1512 × 782.
- **Lección:** una vista que el autor da por buena no se rediseña para cumplir una regla general del plan (caber en la ventana). Se pregunta antes.
- **Pruebas:** `tests/test_view_regression.py::test_d251_the_star_and_the_pipeline_are_drawn_as_in_d229`, `tests/test_star_model.py` (de D-229) y el orden de las pestañas en `tests/test_dashboard.py`. 588 pasan y 1 se omite.

## D-252 · Revisión de coherencia: requisitos, glosario, cifras y capturas que decían algo falso

- **RNF-02 del PRD era falso:** prometía que cada vista cabe en 1440 × 900, pero el Resumen, Calidad y auditoría, Consultas SQL y los documentos se desplazan, y desde D-251 también el pipeline y la estrella, por decisión del autor. Pasa a lo que sí se mide en todas las páginas: ninguna se desplaza a lo ancho entre 1440 × 700 y 1920 × 1080 ni en un teléfono en horizontal (844 × 390), y en vertical el panel pide girar el teléfono (D-166). Evidencia: `tests/medicion/medir.cjs` (D-250).
- **Glosario de `docs/PROYECTO.md`:** la columna «Dónde aparece» nombraba páginas que ya no existen («Monitoreo y Ejecuciones», «Arquitectura», «Datos y SQL», «Reglas de calidad», «Dashboard», «Análisis»). Ahora nombra páginas del menú y, si hace falta, su pestaña.
- **Monitoreo:** decía que la banda de observabilidad de Pipeline y linaje muestra «las mismas señales»; muestra cinco de las ocho. El texto dice ahora «resume cinco de ellas».
- **Capturas del PRD:** M-1, M-3 y M-4 mostraban la ruta y el pie anteriores a D-250; se vuelven a tomar las cuatro del panel actual.
- **Revisado sin cambios:** cada nombre de página o pestaña citado en los documentos existe en el menú; cada texto de la interfaz citado entre comillas existe en el código, el workflow o la base; el SAD coincide con su diagrama de contenedores (dos aplicaciones y tres almacenes), con la versión de Python y el sistema de las máquinas de GitHub Actions y con los permisos del job; todos los documentos dicen lo mismo de `datos.duckdb` (la base servida) y `datos.db` (el respaldo); los rangos RN-01 a RN-14 y K1 a K8 existen; los conteos del plan de seguridad (19 consultas y 9 órdenes) son los de sus pruebas.
- **Pendiente de decisión del autor:** el dibujo del pipeline, que se conserva como en D-229 (D-251), nombra la página de ejecuciones con su nombre antiguo, «Centro de control», en su banda de observabilidad.
- **Pruebas:** `tests/test_documents.py::test_d252_the_glossary_names_only_pages_and_tabs_that_exist` y `test_d252_the_security_plan_counts_the_attacks_its_tests_run`. 590 pasan y 1 se omite; los cinco documentos impresos coinciden con su página.

## D-253 · Pipeline y linaje: las cuatro cifras son solo el número, en 3D

- **Pedido del autor:** las cuatro tarjetas de arriba (filas leídas, filas cargadas, modelos dbt y pruebas dbt) pasan a ser únicamente el número, en tres dimensiones reales.
- **Decisión:** cada cifra es su número con volumen, hecho con CSS (sin dependencias ni imágenes): una cara con degradado iluminada desde arriba, un cuerpo extruido en siete capas y una sombra proyectada, inclinado hacia atrás. Al pasar el cursor el número gira (se desactiva con «reducir movimiento»). Cada una usa el color de su capa en el diagrama de abajo: ingesta (azul), oro (ámbar), staging e intermedio (violeta) y calidad (rosa). Debajo, una sola línea dice qué cuenta. Las cifras son las mismas de antes, leídas de la última carga y del último build de dbt; el diagrama del pipeline no se toca.
- **Código:** `build_pipeline_figure_html` reemplaza a `build_runs_metric_html` y se retiran sus estilos y los selectores que quedaban en `bi/premium.css`.
- **Pruebas:** `tests/test_view_regression.py::test_d253_the_pipeline_figures_are_3d_numbers_read_from_the_latest_load` y el texto de la franja en `tests/test_dashboard.py`.

## D-254 · Arquitectura de seguridad como diagrama de zonas de confianza

- **Pedido del autor:** el diagrama de seguridad (una tabla de cuatro columnas) era demasiado simple y parecía una tarjeta genérica. Debía parecerse a un diagrama de red de seguridad real, con el ejemplo que el autor mostró, pero con GreenOcean tal como es. Se rehace un diagrama por vez.
- **Decisión:** el dibujo pasa a ser una topología por zonas: Internet (el visitante, el administrador y el inicio de sesión externo, punteado); Streamlit Community Cloud, con su zona pública sin cuenta (panel web, filtro de consultas, motor DuckDB en solo lectura y `datos.duckdb`) y su zona del autor con clave (clave de control y secretos del panel); GitHub (repositorio público, `pruebas.yml` con pytest y el workflow semanal); y, abajo, el ciclo de mejora continua. Las flechas son las reales: consulta SQL del visitante, clave del administrador, API de GitHub que lanza el workflow, commit de la base y despliegue de `main`.
- **Cada elemento es de este proyecto:** las insignias verdes numeradas son los siete controles (`CONTROLS`); los triángulos T1 a T6 son las amenazas (`THREATS`, OWASP Top 10 2021) puestas en el camino donde actúan; bajo cada pieza están los casos S-01 a S-10 que la verifican. El inicio de sesión externo sigue punteado y dice que lo declara el autor y que no se puede verificar aquí. Al pasar el cursor, cada pieza muestra cómo protege, qué archivos usa y qué pruebas la verifican, y cada amenaza muestra su categoría OWASP y lo que la detiene.
- **Sin cambios:** los controles, las amenazas, el ciclo de mejora, `docs/SEGURIDAD.md` y las pruebas de seguridad.
- **Pruebas:** `tests/test_security.py::test_d254_*`: cada control es una insignia, cada amenaza tiene su marcador y su explicación, los casos que se dibujan existen en el plan y los archivos y workflows nombrados existen. 592 pasan y 1 se omite. Capturas en `docs/diagnosticos/etapa-12/`.

## D-255 · Despliegue como diagrama de despliegue real, y primero en el Centro de operación

- **Pedido del autor:** el Centro de operación debe abrir en el diagrama de despliegue, y este debe ser un diagrama de despliegue de verdad y fiel a la aplicación, no una lista de tarjetas.
- **Decisión:** nuevo `bi/deployment.py` con la notación de un diagrama de despliegue UML, en español. Los **nodos** son cajas 3D («dispositivo» o «plataforma»): ODEPA, INE, el computador del autor, GitHub, Streamlit Cloud y el navegador. Dentro, los **entornos de ejecución** (el runner `ubuntu-latest` con su Python 3.11, el repositorio de la rama `main`, la caché de Actions, los issues, el proceso de Streamlit y el entorno Python del autor) y, dentro de estos, los **artefactos** desplegados (`semanal.yml`, `pruebas.yml`, `datos.duckdb`, `datos.db`, `manifest.json`, `dashboard.py`, `st.secrets`, `raw.db`). Las líneas son las **rutas de comunicación**, rectas y con su protocolo: HTTPS desde ODEPA e INE, `git push` del autor y del runner, API REST (`workflow_dispatch`) desde el panel, despliegue de `main` y HTTPS del navegador.
- **Datos reales:** los servidores de ODEPA e INE salen de las direcciones del proyecto; el peso de `datos.duckdb` y de `raw.db` se lee de los archivos; la próxima ejecución, los precios de la última semana y la hora de los datos salen de la carga; el punto verde (o rojo) de ODEPA/INE, del runner y del panel es el estado real. Un estado desconocido no se dibuja. Al pasar el cursor, cada nodo y cada entorno explican qué corre ahí y cómo llegó.
- **Orden de la página:** Despliegue es la primera pestaña, seguida de Operación, CI/CD y Monitoreo. «Recargar datos» y «Acceso del autor» (la clave, «Ejecutar pipeline ahora» y los enlaces del autor) pasan sobre las pestañas, para que estén a un clic en todas.
- **Código retirado:** el dibujo anterior (`build_devops_svg`) y los 24 elementos que solo él usaba salen de `bi/architecture.py` (273 líneas), con sus pruebas. Sus comprobaciones útiles pasan a `tests/test_deployment.py`, que ahora compara el dibujo con los workflows (`workflow_dispatch`, `ubuntu-latest`, Python 3.11), los archivos del repositorio y los datos leídos.
- **Pruebas:** 593 pasan y 1 se omite. Capturas en `docs/diagnosticos/etapa-12/`.

## D-256 · Calidad y auditoría rehecha: seis dimensiones, tres puertas, y texto de tamaño normal

- **Pedido del autor (quinta vez):** la página seguía desordenada y con letra muy pequeña, y no se entendía cómo leerla. Si no se podía ordenar, se eliminaba. Se ordena, con un esquema de las seis dimensiones de la calidad como referencia.
- **Causa:** todo estaba apretado en un solo marco de alto fijo que se achicaba con zoom: textos de 9,5 a 10,4 px, dimensiones repartidas sin una secuencia y controles como íconos de 34 px.
- **Decisión:** la página fluye a su alto natural, sin marco fijo, sin zoom y con texto de 13 px o más, en cuatro secciones numeradas que siguen el camino del dato: **(1) Las seis dimensiones**, un esquema con «Datos sanos» al centro y Exactitud, Validez, Unicidad, Actualidad, Completitud y Consistencia alrededor, cada una con su estado y cuántas de sus medidas pasan; **(2) Las tres puertas** de D-245 (el archivo, cada fila y la base), cada una con lo que detiene y, debajo, los indicadores que la vigilan: completitud y actualidad en la primera, validez en la segunda, consistencia, unicidad y pruebas de dbt en la tercera; **(3) Lo que se apartó y las últimas cargas**, dos tablas: cada motivo con su código, si la fila se rechazó (queda fuera de la base) o se marcó (queda en la base, fuera de los indicadores) y cuántas son, y las cinco últimas cargas con sus filas y su cambio; **(4) Controles de auditoría**, una tabla por etapa con el estado de cada control.
- **Exactitud no se inventa:** no hay un indicador de exactitud, así que el eje se mide con los cuatro controles de auditoría de la etapa «Resultados» (reconciliación fuente → base, recálculo independiente, concordancia con la pantalla y contraste con otra fuente). Hoy 3 de 4 están verificados y el contraste con otra fuente sigue pendiente, de modo que el eje sale en ámbar. Sin controles, el eje no afirma nada.
- **Sin cambios:** los once indicadores, sus umbrales, el veredicto, las puertas, la evidencia de cada control (botones «Abrir la evidencia de») y el aviso por las huellas SHA-256 locales.
- **Código retirado:** `bi/audit_trace.py` (los íconos pequeños de los controles) y el dibujo anterior de `bi/quality_live.py`.
- **Pruebas:** `tests/test_quality_audit.py::test_d256_*`: el orden de las secciones, cada indicador bajo su puerta, las cifras de lo apartado y de las cargas contra la base, y la exactitud contra los controles. 592 pasan y 1 se omite. Capturas en `docs/diagnosticos/etapa-12/`.

## D-257 · Calidad y auditoría: el diagrama es la página, y cada pieza abre su detalle

- **Pedido del autor:** la página debía ser más simple y con menos texto: el diagrama mismo interactivo, donde cada componente, al pulsarlo, muestra su información en una ventana emergente; y lo que son fallas y cosas así, en otra pestaña.
- **Decisión:** la primera pestaña, **Calidad**, es solo el veredicto, el esquema de las seis dimensiones alrededor de «Datos sanos» y tres botones para las tres puertas. Cada eje, cada puerta y el centro abren una ventana emergente con su detalle: la pregunta que responde, cada indicador con su valor, su umbral y cómo se mide (con la consulta cuando la medida es una consulta), y de cada puerta lo que detiene, qué pasa si no pasa, dónde está y sus pruebas. Las ventanas son hojas CSS que se abren con `:target`, sin script; se cierran con la ✕ o pulsando fuera. El documento se ancla a sí mismo (`<base href="about:srcdoc">`): sin eso, el enlace `#…` dentro de un marco `srcdoc` se resolvía contra la página de afuera y cargaba la aplicación dentro del marco.
- **Pestañas:** **Auditoría** (los controles por etapa con su estado, el aviso de las huellas locales y los botones «Abrir la evidencia de») y **Rechazos y cargas** (lo que se rechazó o se marcó, con su motivo y su efecto, y las cinco últimas cargas). La falla de integridad de la base sigue mostrándose arriba de las tres pestañas.
- **Consistencia** cuenta ahora las pruebas de dbt junto con los indicadores de consistencia, para que un fallo de dbt se vea en el esquema y no solo en el veredicto. Exactitud sigue midiéndose con los cuatro controles de la etapa «Resultados».
- **Sin cambios:** los once indicadores, sus umbrales y el veredicto.
- **Corrección el mismo día:** la consulta que muestran los indicadores de validez caía en la columna angosta del punto de estado y se leía en vertical; ahora ocupa todo el ancho de la fila.
- **El número del veredicto se puede comprobar:** la frase «Los 11 indicadores medidos…» no enseñaba los once en ningún lugar, solo repartidos en las ventanas de cada eje. Ahora el centro del esquema muestra «11 indicadores» como un botón que abre «Los 11 indicadores», con todos juntos por dimensión y cómo leer los colores (el autor pidió que estuviera en el centro, donde el número se menciona, y no en un enlace a un lado). Una prueba exige que el número de la frase sea el de la lista y que haya una sola entrada.
- **Pruebas:** `tests/test_quality_audit.py::test_d257_*` y las pestañas en `tests/test_dashboard.py`: cada pieza enlaza a una ventana que existe y cada indicador está en ella; lo apartado y las cargas son las de la base. 592 pasan y 1 se omite. Capturas en `docs/diagnosticos/etapa-12/`.

## D-258 · Plan de pruebas de seguridad: los diez casos dentro de un diagrama, y el procedimiento como ciclo

- **Pedido del autor:** el diagrama del plan era lineal, simple y pequeño, y la tabla de casos hacía el documento muy largo. Los casos debían vivir en un diagrama interactivo: un clic en S-01, S-02… y se ve su ataque, su resultado, su OWASP y su prueba. El resumen del punto 5 se mantiene.
- **Decisión:** nuevo `bi/security_plan.py`. Los diez casos son nodos alrededor del candado del plan; cada uno abre una ventana (CSS `:target`, sin script) con su ataque, su resultado esperado, su categoría del OWASP Top 10 (2021), la amenaza de la arquitectura de seguridad que cubre y la prueba que lo verifica. El procedimiento pasa a ser un ciclo de cinco pasos (preparar, ejecutar, comprobar, registrar y decidir), con el camino de vuelta al paso 2 cuando un caso falla; cada paso abre cómo se hace. Texto de 14 px o más.
- **Una sola fuente:** la tabla larga de `docs/SEGURIDAD.md` se retira; los casos viven solo en `CASES`. El código del procedimiento anterior sale de `bi/doc_views.py`.
- **Amenazas:** la sección «Amenazas y controles» sigue enlazando a la Arquitectura de seguridad. Las seis amenazas cubren lo que se alcanza desde internet (D-249); no pretenden ser todas las que existen, y el alcance (sección 1) lo dice.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d258_*`: los diez casos tienen su ventana, cada prueba nombrada existe, cada amenaza de la arquitectura apunta a casos que existen y el ciclo dice que el CI avisa pero no detiene `main`. 597 pasan y 1 se omite.

## D-259 · Resumen semanal: encabezado fino con las cifras en 3D

- **Pedido del autor:** la parte de arriba ocupaba mucho espacio y obligaba a un desplazamiento más largo. Debía ser un encabezado más fino y más pequeño, donde lo único grande fueran los números, en 3D, pero no tan grandes, para que el panel de abajo se vea más completo.
- **Decisión:** el título pasa de 38 px a un máximo de 24 px y su subtítulo a 12,5 px. Las cuatro tarjetas (precios comparados, familias, regiones y alertas) se reemplazan por una sola franja con separadores finos, sin cajas: cada cifra es un número en 3D de 22 a 28 px, con su etiqueta y su nota en una línea debajo. La sombra de la extrusión sigue el color de la tinta del tema, así se ve limpia en Vantablack y en Blue Light. El botón «Alerta de precio» sube a la misma franja del título, en vez de ocupar una fila propia.
- **Resultado:** el panel de abajo empieza unos 14 px más arriba que con las tarjetas y la fila del botón, a 1440 × 900. Las cifras son las mismas y vienen del mismo modelo semanal que los gráficos.
- **Sin cambios:** el mapa, el movimiento por familia y la tabla de productos.

## D-260 · Plan de pruebas de seguridad: el logo de cada tecnología y líneas en ángulo recto

- **Pedido del autor:** cada círculo del esquema de casos debía mostrar el logo de la tecnología que involucra, y las líneas eran demasiado rectas (diagonales): debían doblar en ángulo, como en el diagrama entidad-relación.
- **Decisión:** cada caso lleva dentro el logo 3D de la tecnología que ataca: DuckDB en S-01 a S-03 (el motor SQL), Python en S-04 y S-05 (la comparación de la clave con `hmac.compare_digest`), Git en S-06, GitHub en S-07 y S-08 (la API y el workflow), pytest en S-09 y Streamlit en S-10. El código del caso y su categoría OWASP pasan a una línea junto al nombre, hacia afuera del esquema, y la ventana de cada caso dice su tecnología. El candado sigue al centro: es el plan, no una tecnología.
- **Líneas:** del candado sale un tronco horizontal a cada lado y de él una rama vertical hacia cada caso, con un punto donde se separa; solo hay tramos horizontales y verticales. En el ciclo del procedimiento, las flechas también doblan en ángulo recto: de Preparar a Ejecutar sale por el costado y baja; las demás son verticales u horizontales.
- **Sin cambios:** los diez casos, sus ventanas, el ciclo de cinco pasos y el camino de vuelta al paso 2.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d260_*`: cada caso tiene una tecnología con logo y la ventana la nombra, y ninguna línea de los dos diagramas es diagonal.

## D-261 · Pipeline y linaje: las cuatro cifras en una franja fina

- **Pedido del autor:** la parte de las cifras se veía demasiado grande. Debía ser minimalista y más baja, para que se vea más del diagrama de abajo, que es lo importante; los números se leen igual sin ser tan grandes.
- **Decisión:** los números pasan de 27 a 40 px a 18 a 22 px, con una extrusión 3D de tres capas en vez de siete y una sombra más corta; la leyenda baja a 11,5 px, pegada al número, y las cuatro cifras quedan separadas por líneas finas, sin cajas, como en el Resumen semanal (D-259). Los márgenes de arriba y de abajo se reducen.
- **Resultado:** la franja mide unos 42 px de alto a 1440 × 900, en lugar de unos 110, y la tarjeta del recorrido empieza unos 50 px más arriba.
- **Sin cambios:** las cuatro cifras, de dónde vienen (la última carga y el último dbt build), el color de cada una según su capa y el giro al pasar el cursor.

## D-262 · Consultas SQL: el cuadro aprovecha parte de los márgenes

- **Pedido del autor:** el cuadro de consultas está bien, pero los márgenes a los dos lados dejan espacio sin usar; debía verse solo un poco más grande.
- **Decisión:** en esta página, y en pantallas de 1024 px o más, el margen lateral de la página baja de 80 a 40 px por lado. El título se mueve con el cuadro, así siguen alineados.
- **Resultado:** a 1440 × 900 el cuadro pasa de 980 a 1060 px de ancho (un 8 % más); el editor y la tabla de resultados ganan ese ancho, y el comentario de la consulta «Tabla completa» cabe completo.
- **Sin cambios:** el contenido del cuadro, las otras páginas y los teléfonos (D-166).

## D-263 · Resumen semanal: el encabezado, aún más fino

- **Pedido del autor:** después de D-259 el encabezado seguía viéndose demasiado grande; debía ser una franja fina, para subir el contenido de abajo.
- **Decisión:** el título baja a un máximo de 20 px y su subtítulo a 12 px. En la franja, cada cifra es su número en 3D (17 a 21 px, con menos relieve) y, a su lado, la etiqueta y la nota en dos líneas pequeñas, en vez de debajo: la franja tiene el alto de un número. Cada cifra toma el ancho que necesita, así ninguna nota se corta a 1440 px; si no caben las cuatro en una fila, las que sobran pasan a una segunda fila. Al pasar el cursor, cada cifra muestra su etiqueta y su nota completas.
- **Resultado:** a 1440 × 900 el encabezado mide 72 px (38 del título y 34 de la franja) en vez de 120, y el mapa y el movimiento por familia empiezan unos 48 px más arriba.
- **Sin cambios:** las cuatro cifras y su origen, el botón «Alerta de precio» y la fecha de actualización.

## D-264 · Resumen semanal: el encabezado es una sola barra

- **Pedido del autor:** un boceto con todo el encabezado en una sola línea: volver, la ruta, la pregunta, la semana, las cifras como fichas, las alertas en rojo y la hora de la carga.
- **Decisión:** en el Resumen semanal, la ruta con «Volver», el título, la franja de cifras (D-259, D-263) y el botón de alertas se reemplazan por una barra de unos 54 px, dentro de un recuadro redondeado: la flecha de volver; «Negocio · BI › Resumen semanal»; la pregunta, que se corta con «…» cuando falta espacio; la semana; los precios comparados (719/772); las familias (FAM 3↑ 2↓ 2=); las regiones (REG 3↑ 1↓); las alertas de precio («▲ 17», en rojo, que siguen abriendo el detalle por familia), y un punto verde con la fecha de la carga, rojo si falló. Las otras páginas conservan su encabezado.
- **Nada se pierde:** al pasar el cursor, la pregunta muestra su subtítulo (la mediana, la semana y el lugar) y cada ficha dice en palabras lo que cuenta, también las regiones sin dirección clara y sin dato. Con una región elegida, la ficha de la semana la nombra.
- **Alertas:** la ficha cuenta las alertas nacionales de la semana que se muestra, la misma que abre el detalle; antes el botón contaba siempre la última semana. Su rojo sigue ahora el fondo de la página y no el del menú: en Corporativo el menú es oscuro y el rojo claro casi no se leía sobre la página clara.
- **Resultado:** a 1440 × 900 el mapa y el movimiento por familia empiezan en el píxel 84, en vez de unos 200. En pantallas angostas la pregunta pasa a su propia línea y las fichas se acomodan debajo; en el teléfono horizontal (D-166) cabe en dos líneas.
- **Código retirado:** `home_mockup.dashboard_header` y `home_mockup.title`, y los estilos de la franja anterior en `bi/premium.css` y `bi/home_mockup.css`.
- **Pruebas:** `tests/test_dashboard.py::test_d264_*`: una sola ruta y un solo «Volver», la pregunta como título de la página, cada nota en el texto de su ficha, la cuenta de alertas contra la base y la hora de la carga.

## D-265 · Resumen semanal: todo cabe en una pantalla

- **Pedido del autor:** reducir la altura de los bloques para que el Resumen se vea entero, sin desplazar la página.
- **Decisión:** las filas de «Movimiento por familia» bajan de unos 68 a 38 px, con imágenes de 38 px; las tarjetas tienen menos relleno (14 × 18 px), y el eje de la escala se acorta. La tabla de productos toma el alto que queda en la pantalla (todo lo demás suma 642 px) y se desplaza por dentro, con un mínimo de 150 px; el mapa sigue estirándose al alto de la columna derecha (D-150).
- **Resultado:** sin desplazar la página a 1440 × 800 (lo que deja el navegador en una pantalla de 1440 × 900), a 1440 × 900 y a 1920 × 1080: la barra, el mapa, las siete familias, la tabla de productos y la nota de cobertura. Antes, a 1440 × 900, la página medía 1000 px. En pantallas de menos de unos 790 px de alto, la página vuelve a desplazarse.
- **Sin cambios:** los datos, las siete familias, el orden y los filtros de la tabla.

## D-266 · Stack y evidencia: el stack como diagrama de arquitectura

- **Pedido del autor:** la fila de logos era demasiado simple y lineal: no mostraba la lógica entre las herramientas, el rol de cada una, cuándo actúa, para qué ni con cuáles se conecta, y un logo no decía qué tecnología es.
- **Decisión:** la página es un diagrama de alto nivel. El dato fluye de izquierda a derecha: ODEPA e INE → Python → SQLite → Parquet → dbt → DuckDB → Streamlit, y cada flecha dice qué viaja (CSV, IPC, filas crudas, por año, bronce, marts, solo lectura). Arriba, GitHub Actions lanza la carga cada martes y Python lanza dbt build; SQL, con línea discontinua, llega a dbt (modelos), DuckDB (lo ejecuta) y el panel (consultas). Abajo, pytest, lanzado en cada push y cada martes, recalcula cada precio desde SQLite y audita cada cifra de DuckDB. Bajo cada logo se lee qué es («Base de datos ligera», «Formato columnar»…) y su etapa (Ingesta, Aterrizaje, Capa bronce, Transformación, Data warehouse, Panel, Orquestación, Lenguaje común, Calidad). Una leyenda explica los cuatro tipos de línea.
- **Al pasar el cursor:** cada herramienta dice qué es, su rol en GreenOcean, cuándo actúa y con qué se conecta; esta última lista se lee de las flechas mismas, así que el texto y el dibujo no pueden contradecirse. Cada flecha explica lo que viaja. Un clic sigue abriendo la página donde la herramienta está en uso (D-211).
- **Detalle técnico:** las líneas van en una sola imagen `data:` (`st.html` quita los marcadores y degradados de un SVG en línea); solo tienen tramos horizontales y verticales, como en D-260. Las medidas escalan con el ancho (unidades de contenedor) y ningún texto baja de 10,5 px. La página cabe entera a 1440 × 900.
- **Sin cambios:** las nueve herramientas y sus páginas de destino, y las tres cifras leídas de la base y del repositorio (D-211).
- **Pruebas:** `tests/test_stack_page.py::test_d266_*` (definición, rol, cuándo y conexiones de cada herramienta, líneas en ángulo recto que llegan a su destino, la ventana de pytest se abre hacia arriba) y `tests/test_dashboard.py` (D-211).

## D-267 · Las páginas principales con una sola barra de encabezado; Precios e inflación con su lectura

- **Pedido del autor:** aplicar a las páginas principales el principio del Resumen semanal (D-264, D-265): un encabezado mínimo, con poco texto, para ver la página entera sin desplazarse. En Precios e inflación, quitar el párrafo largo de arriba, mostrar en la esquina derecha, en forma mínima, qué KPI y qué métrica usa la página, y que al ampliar una familia se vea una lectura dinámica, propia de sus datos.
- **Decisión:** Precios e inflación, Pipeline y linaje, Modelo de datos, Calidad y auditoría, Consultas SQL, Centro de operación, Arquitectura de seguridad y Stack y evidencia reemplazan la fila de la ruta con «Volver», el título, el subtítulo y las franjas de cifras por una barra de unos 44 px, como la del Resumen: volver, la ruta, el título (su explicación al pasar el cursor), las cifras de la página como fichas y la hora de la última carga, con su punto verde o rojo. Cuando el título es el nombre de la página, la ruta muestra solo su sección para no repetirlo.
- **Lo que pasa a la barra:** Pipeline y linaje, las cuatro cifras de la última carga y del build (filas leídas, cargadas, modelos y pruebas, cada número en el color de su capa; las rechazadas siguen en el diagrama y en la explicación de la ficha); Modelo de datos, weekly_price y la auditoría; Consultas SQL, DuckDB en solo lectura, el máximo de filas y el tiempo límite; Centro de operación, «Recargar datos» y «Acceso del autor» (D-255: siguen sobre las pestañas, a un clic); Arquitectura de seguridad, el enlace al plan de pruebas.
- **Precios e inflación:** el párrafo de respuesta pasa a la explicación del título; en la barra quedan el IPC de alimentos desde enero 2022 y cuántas familias subieron más y menos que él (al pasar el cursor, sus nombres). En la esquina derecha, «KPI · Variación vs IPC» y «Métrica · Índice ene 2022 = 100», cada uno con su definición al pasar el cursor. El selector «Precios del día / Sin inflación» sube a la línea del título de los gráficos.
- **Ampliar una familia:** junto al gráfico grande aparece «Lectura de los datos», calculada con el mismo índice mensual que dibuja la línea: cuánto subió desde enero 2022 y cuántos puntos más o menos que el IPC (la diferencia de las dos cifras redondeadas que muestran las tarjetas), los últimos 12 meses frente al IPC, su máximo y cuánto está bajo él, su mayor movimiento mensual, cuánto vale descontado el IPC y cuántas series la componen. Con «Sin inflación», el máximo y el movimiento se leen sobre la línea sin inflación, la que el gráfico dibuja entonces. El IPC ampliado dice cuántas familias subieron más, menos o a su ritmo.
- **Pie de página:** en las páginas que caben en la ventana (D-233), la atribución muestra su primera línea y se abre completa al pasar el cursor; al imprimir sale entera.
- **Altos:** el marco de Calidad baja de 590 a 560 px (la franja vacía bajo las tres puertas; las ventanas de detalle siguen cabiendo), el de seguridad de 690 a 680 px, el estudio SQL deja 44 px para el pie corto, y el modelo estrella crece con la ventana sin pasarla.
- **Resultado:** a 1440 × 900, 1440 × 800 y 1920 × 1080, las ocho páginas se ven enteras sin desplazar en su vista inicial, y también las cuatro vistas de Modelo de datos. Antes medían entre 900 y 1011 px a 1440 × 900. Las pestañas Operación, CI/CD y Monitoreo del Centro de operación todavía pasan la pantalla (960, 1123 y 939 px): bajaron unos 70 px, pero caber del todo pide cambiar su contenido, que no se tocó.
- **Sin cambios:** los diagramas, las tarjetas y las tablas de cada página, sus datos y sus pruebas.
- **Código:** `bi/page_bar.py` (nuevo), `show_page_bar` en `bi/dashboard.py`, `inflation_view.family_insights`. Se retiran la franja de cifras del pipeline (D-253, D-261) y las fichas de Modelo de datos (D-097).
- **Pruebas:** `tests/test_page_bar.py`: una sola barra y un solo «Volver» por página, sin el encabezado anterior; las fichas de Precios e inflación contra la base; cada frase de la lectura recalculada desde el índice, también sin inflación; «Ampliar» muestra el gráfico y su lectura. `tests/test_view_regression.py::test_d267_*`: las cifras del pipeline vienen de la última carga.

## D-268 · La barra de encabezado y Consultas SQL en tableta y en ventanas angostas

- **Pedido del autor:** dejar lo menor que no se nota, pero corregir todo lo que se vea mal en celular, tableta o computador.
- **Revisión:** las nueve páginas principales, en 1920 × 1080, 1440 × 900, 1280 × 800, tableta horizontal (1024 × 768) y vertical (768 × 1024), y teléfono horizontal (844 × 390), midiendo el desborde horizontal y si la barra recorta algo.
- **Lo que estaba mal y se corrige:**
  - a 1024 px, la barra pasaba a dos o tres líneas, el título «Centro de operación» quedaba debajo de sus botones y la ruta quedaba suelta bajo el título;
  - a 1280 px, la barra de Pipeline y linaje recortaba sus fichas;
  - a 1024 px, el selector «Precios del día / Sin inflación» quedaba cortado a la derecha;
  - en Consultas SQL (de antes de D-267), un filtro salía del marco del editor y el cronómetro de la barra de estado quedaba cortado.
- **Decisión:** el título y las fichas guardan al menos 240 px; si los botones, los términos o la hora no caben a su lado, pasan a una segunda línea alineados a la derecha, en vez de taparlo. Bajo 1320 px la ruta sale de la barra (el menú ya marca la página; la ruta sigue en la etiqueta accesible) y las fichas que no caben bajan bajo el título. El selector toma el ancho que necesita. En Consultas SQL, los filtros pasan de línea dentro del marco y, en ventanas angostas, la barra de estado deja el motor, el modo y el archivo (la barra de la página ya los dice) para que siempre se vean el tiempo y las filas.
- **Resultado:** ninguna página desborda a lo ancho y ninguna barra recorta texto en esas seis medidas. A 1440 × 900 y 1920 × 1080 todas las barras siguen en una línea y las páginas caben sin desplazar.
- **Se deja así (menor):** en pantallas más bajas que 900 px, las páginas con un diagrama de alto fijo (Calidad, seguridad, el Centro de operación) se desplazan un poco, y las pestañas Operación, CI/CD y Monitoreo del Centro de operación pasan la pantalla, como se informó en D-267.
- **Pruebas:** `tests/test_page_bar.py::test_d268_*`.

## D-269 · Los documentos, revisados contra el producto: PRD, SAD, ADR y Escalabilidad

- **Pedido del autor:** dejar los documentos impecables, porque los revisará gente importante: que cubran todo el producto creado, que sean rigurosos y coherentes con el proyecto, y que estén escritos de la forma más humana posible. La captura M-4 del PRD no representaba el panel. Las páginas de documentos no necesitan flecha de retorno, porque el menú está siempre a la vista.
- **Una afirmación falsa, corregida:** el PRD (RF-03) y el ADR-11 decían que una carga fallida «queda registrada como fallida». En producción no es así: `pipeline.py` anota la falla en su copia, pero el workflow se detiene antes de subirla, así que `etl_run` guarda solo las cargas publicadas. Los documentos dicen ahora dónde queda la falla: en el historial de GitHub Actions, que avisa al autor por correo y que el Centro de operación muestra paso a paso.
- **PRD:** objetivos nuevos; una quinta pregunta de negocio, la del revisor técnico («¿Puedo confiar en estas cifras?» → Calidad y auditoría); los requisitos pasan de 6 a 14. Se agregan, cada uno con su criterio medible y las pruebas que ya lo comprobaban: alertas de precio, consultas SQL de solo lectura con sus límites, carga manual protegida, informe semanal, trazabilidad de cada cifra, seguridad, calidad vigilada en cada cambio, lectura en tableta y una pantalla por página. Una sección nueva de supuestos y límites: el promedio simple de las regiones, la ausencia de predicciones y de causas, el IPC provisional, la dependencia de las fuentes y de los planes gratuitos.
- **Pantallas:** las cuatro capturas se retomaron de las páginas actuales. M-4 deja el Resumen en el teléfono por Calidad y auditoría (tema Blue Light), la pantalla del revisor técnico, así hay una por perfil del PRD. Se retira el marco de teléfono, que ya no usaba ninguna captura.
- **SAD:** cuatro secciones nuevas: los cinco principios que explican las decisiones, la vista de ejecución (la carga de cada martes paso a paso, con su compuerta y qué pasa si algo falla), calidad y observabilidad (las tres puertas, los once indicadores y los cuatro lugares donde queda el rastro de cada carga), y los riesgos técnicos con su mitigación actual. La sección de datos explica las capas en una frase cada una.
- **ADR:** además del ADR-11, el ADR-19 deja de decir «no se registró una alternativa» sin más: lo sigue reconociendo y nombra la opción obvia (una tabla ancha), sin inventar que se evaluó. El ADR-04 agrega su consecuencia real: la base servida y el respaldo se versionan en cada carga.
- **Escalabilidad:** decía que el proyecto crecía «cambiando configuración, no código», y su propia tabla agregaba modelos nuevos. Ahora dice lo que es: una fuente nueva entra con sus modelos sin tocar los existentes. Agrega qué cedería primero: el historial de Git (cada carga sube las dos bases; medido, cerca de 1 GB por año), la duración de la carga y los visitantes simultáneos, con qué se haría en cada caso.
- **Navegación:** las páginas de documentos (PRD, SAD, ADR, Escalabilidad y Plan de pruebas de seguridad) ya no tienen la fila de ruta con «Volver». Las vistas que los documentos enlazan conservan su «Volver» en la barra (D-267), así quien sigue un enlace puede regresar.
- **Coherencia:** el diagrama del pipeline llamaba «Centro de control» a la página que el menú llama «Centro de operación».
- **Sin cambios:** el Plan de pruebas de seguridad, revisado sin hallazgos.
- **Pruebas:** `tests/test_prd_traceability.py` (cinco preguntas y catorce requisitos, cada evidencia existe), `tests/test_doc_diagrams.py` (cada captura es una página del menú a 1440 × 900), `tests/test_documents.py::test_d269_*` (el número de indicadores y de dimensiones del PRD y el SAD es el que mide el panel; ningún documento dice que una falla queda registrada en la base).

## D-270 · La base servida vive en un release que cada carga reemplaza; git guarda solo su puntero

- **Problema:** cada martes la carga subía con un commit `etl/datos.duckdb` (unos 14 MB) y `etl/datos.db` (unos 34 MB). Git guarda cada versión para siempre: el historial ya pesaba 309 MB y crecía cerca de 1 GB por año (unos 19 MB comprimidos por carga), con copias que nadie lee, porque cada base nueva ya trae la historia completa (ADR-10). GitHub recomienda repositorios de menos de 1 GB, y clonar el proyecto, también para desplegar el panel, se hacía cada vez más lento.
- **Pedido del autor:** que la base se reemplace en vez de acumularse.
- **Decisión (ADR-35):** la base servida se publica como el archivo `datos.duckdb` del release «base-actual» de GitHub, que cada carga reemplaza (`gh release upload --clobber`). En git queda solo su puntero, `etl/datos.version`: la huella SHA-256, el tamaño y la hora de la base publicada. `bi/served_database.py` compara el archivo local con el puntero y descarga el del release cuando falta o es más antiguo; lo cambia de una vez y solo si su huella coincide. Una reconstrucción local más nueva que el puntero se conserva. El respaldo `etl/datos.db` deja de subirse: se rehace en la máquina de cada carga, que es donde corre la prueba de paridad.
- **Workflow semanal:** un paso nuevo, «Get the published database», trae al principio la base de la semana anterior, de la que salen el historial de cargas y la comparación del 90 %. El paso «Save the updated database» pasa a ser «Publish the database»: primero reemplaza el archivo del release y después sube el puntero y `manifest.json`, así el panel nunca ve un puntero cuyo archivo aún no está. `pruebas.yml` descarga la base antes de pytest.
- **Panel:** al arrancar descarga la base si falta o es más antigua, una vez por puntero. Si no puede, sigue con la que tiene y, si no tiene ninguna, lo dice.
- **Calidad:** el servidor ya no tiene el respaldo. Sin cambio, el centro del esquema de Calidad habría dicho «10 indicadores» y su lista «Los 11». Ahora la paridad se informa como comprobada en la carga publicada, que pasó la prueba de paridad en su máquina antes de publicarse; los once indicadores siguen medidos. Los cruces entre bases dicen que el respaldo no se publica.
- **Opciones consideradas con el autor el 24-10-2026:** dejar de versionar solo el respaldo SQLite (el crecimiento bajaba a unos 300 MB por año sin detenerse); almacenamiento de archivos grandes (Git LFS), que también conserva cada versión y tiene una cuota gratuita limitada; reescribir el historial cada cierto tiempo, que invalida las copias ya clonadas. Se eligió el release.
- **Lo que no se hizo:** las versiones anteriores siguen en el historial. Borrarlas exigiría reescribirlo y forzar el push, lo que rompe las copias ya clonadas; el historial simplemente deja de crecer.
- **Puesta en marcha (una vez, al hacer el push):** crear el release con la base que nombra el puntero: `gh release create base-actual etl/datos.duckdb`. Si la base local cambió desde el último puntero, escribirlo antes con `python bi/served_database.py --pointer` y hacer commit. Sin el release, el panel publicado y el workflow no encuentran la base.
- **Textos y diagramas actualizados:** CI/CD (diez pasos, el release y Streamlit), Despliegue, Dónde viven los datos, Arquitectura de seguridad, contenedores del SAD, Stack y evidencia, Operación, glosario, SAD, ADR-04, Escalabilidad, MANUAL, README y CLAUDE.md.
- **Pruebas:** `tests/test_served_database.py` (descarga si falta o es más antigua; conserva una reconstrucción local más nueva; rechaza un archivo cuya huella no coincide sin tocar la base; el workflow trae la base antes de construir y publica el archivo antes que su puntero; git guarda el puntero y ninguna de las dos bases). La suite pasa con y sin el respaldo local, como en GitHub.

## D-271 · Centro de operación, pestaña Operación: cabe en una pantalla y se adapta a la ventana

- **Pedido del autor:** que la pestaña Operación sea más adaptable y se vea entera, sin desplazarse.
- **Antes:** a 1440 × 900 medía 960 px: el recorrido tenía un alto fijo y la lista de las últimas ejecuciones iba debajo. A 1024 px, los logos del recorrido conservaban su tamaño en una escena más angosta y se montaban unos sobre otros.
- **Decisión:** las últimas ejecuciones pasan a la columna derecha, bajo los datos de la carga, una por línea (si la columna es angosta, se cortan con «…» y el puntero las muestra enteras). El recorrido conserva su proporción y nunca es más alto que lo que la ventana deja bajo las pestañas. Los logos, los nombres y los tiempos se achican con la escena, sin pasar nunca de su tamaño actual. En una tableta (ventana de menos de 1100 px), los datos pasan bajo el recorrido, que toma todo el ancho.
- **Resultado:** sin desplazarse a 1920 × 1080, 1440 × 900, 1280 × 800 y 1440 × 700. En la tableta horizontal la página se desplaza, porque las dos columnas se apilan, pero ya nada se monta.
- **Sin cambios:** el dibujo del recorrido (D-229), sus nueve pasos, sus estados, sus ventanas y los datos de la columna derecha.
- **Pruebas:** `tests/test_operation_center.py::test_d271_*`.

## D-272 · Calidad y auditoría: las tres pestañas caben en una pantalla

- **Pedido del autor:** aplicar a Calidad y auditoría lo mismo que a la pestaña Operación (D-271): que se adapte a la ventana y se vea entera.
- **Antes:** el marco del esquema de Calidad tenía un alto fijo de 560 px; en una ventana ancha el dibujo crecía y las tres puertas quedaban cortadas dentro del marco (a 1920 px medía 625 px). Auditoría medía 1.338 px en todas las pantallas: una sola tabla larga, once botones de evidencia en dos filas y la fila «Volver a medir» debajo.
- **Decisión:**
  - el marco del esquema toma el alto del dibujo, y el dibujo nunca es más ancho que lo que lo deja dentro de la ventana;
  - los controles de Auditoría se reparten en dos paneles lado a lado, en su orden, tan parejos como lo permiten sus filas, y las etiquetas largas de estado pasan a dos líneas para dejar el ancho a los títulos (bajo 640 px, un panel bajo el otro);
  - los once botones de evidencia esperan detrás de uno solo, «Abrir la evidencia de un control», sin volver a un selector (D-220);
  - «Volver a medir» sube a la barra de la página (D-267), con su explicación al pasar el cursor;
  - el aviso de un archivo local distinto de su huella, que solo aparece en el computador del autor, cabe en una línea.
- **Resultado:** a 1440 × 900 y 1920 × 1080, Calidad, Auditoría y Rechazos y cargas se ven sin desplazar (Auditoría, en el servidor, sin el aviso local). En pantallas de 800 px de alto o menos todavía se desplazan un poco.
- **Sin cambios:** los once indicadores, los controles y sus estados, las ventanas de detalle y la evidencia de cada control.
- **Pruebas:** `tests/test_quality_audit.py::test_d272_*` y `tests/test_dashboard.py::test_d220_*`.

## D-273 · Calidad: el esquema pasa a ser un pipeline de calidad, con el mismo funcionamiento

- **Pedido del autor:** conservar el funcionamiento de la pestaña Calidad (D-257) y cambiar su apariencia según un boceto: un «pipeline de calidad de datos» con tres puertas, seis dimensiones y un veredicto.
- **Decisión:** el centro con las seis dimensiones alrededor y la fila de puertas se reemplazan por un recorrido de izquierda a derecha. Origen (los CSV de ODEPA) → Puerta 1 · el archivo → Puerta 2 · cada fila → Puerta 3 · la base → Carga (la base, con sus precios semanales). Sobre cada tramo, las filas de la última carga publicada: 2.521.012 leídas hasta la puerta 2, 2.520.811 después de ella. Desde la puerta 2 sale hacia arriba el rechazo, con sus filas y su motivo en palabras («precio cero o negativo»). Bajo cada puerta, «Mide» con sus dimensiones, y las tres desembocan en el veredicto: «Datos sanos · 11 indicadores dentro de su umbral · 1 control pendiente: exactitud».
- **Las cifras del boceto no se copiaron:** eran de ejemplo. Todas se leen de la base (`etl_run`, `rejection` y `weekly_price`), y una prueba exige que las leídas sean las cargadas más las rechazadas.
- **Las dimensiones, donde de verdad se vigilan (D-245):** el boceto ponía Unicidad en la puerta 2, pero un precio repetido se busca en la base, así que va en la puerta 3. Exactitud también va en la puerta 3: sus controles corren en pytest sobre la base nueva, antes de publicarla. Queda: puerta 1, Completitud y Actualidad; puerta 2, Validez; puerta 3, Consistencia, Unicidad y Exactitud.
- **El mismo funcionamiento:** cada puerta, cada dimensión y el veredicto abren la misma ventana que antes; el rechazo abre la de la puerta 2, que explica qué se rechaza. El veredicto ya no dice siempre «Datos sanos»: dice «Datos a revisar» o «Datos con fallas» cuando corresponde. Las líneas y el borde de cada puerta usan el color de acento del tema, ámbar si algo está a revisar y rojo si falla.
- **Un texto falso, corregido:** la ventana de la puerta 3 decía que una carga fallida «queda en etl_run como fallida», y el glosario, que pipeline.py registra «también las fallidas». No es así desde siempre en producción (D-269): ahora dicen que la carga se detiene antes de publicarse y queda en el historial de GitHub Actions, que avisa al autor por correo.
- **Adaptable:** el dibujo es HTML y CSS, no una imagen que se encoge, así que las letras conservan su tamaño. Entre 760 y 960 px se compacta y bajo 760 px los tramos se apilan de arriba abajo. Cabe sin desplazar a 1440 × 900 y 1920 × 1080; a 1280 × 800 solo queda fuera la línea de créditos del pie. La captura M-4 del PRD se tomó de nuevo.
- **Pruebas:** `tests/test_quality_audit.py::test_d273_*` (las filas de cada tramo vienen de la última carga y cuadran; cada dimensión está en una sola puerta; ninguna puerta dice que una falla queda en etl_run; el veredicto cuenta los indicadores y nombra los controles de exactitud pendientes), además de las de D-257, que siguen pasando.

## D-274 · La medida es la ventana real del navegador (1440 × 790); Calidad y auditoría cabe en ella

- **Problema:** el autor vio la pestaña Calidad con desplazamiento. D-271 a D-273 se midieron a 1440 × 900, el tamaño de la pantalla; pero en un navegador quedan unos 1440 × 790 para la página (la barra de menús, las pestañas y la dirección se llevan el resto), la medida que ya usaba D-265 para el Resumen. A esa altura, Calidad sobraba 98 px, Arquitectura de seguridad 94, el Centro de operación 50, Pipeline y linaje 42 y Stack y evidencia 19.
- **Decisión:** desde ahora, «cabe en una pantalla» se mide a 1440 × 790. En Calidad y auditoría:
  - el esquema se compacta sin cambiar su forma: el rechazo va en una sola línea sobre la puerta 2, las puertas hacen preguntas cortas («¿Completo y al día?», «¿Cada fila es válida?», «¿Coherente y probada?»; la ventana y el cursor dan la pregunta completa), la indicación «pulsa cada pieza» se une a la línea del título y las líneas entre piezas son más cortas;
  - en Auditoría, cada control ocupa una línea (su hallazgo completo, al pasar el cursor) y las etiquetas de estado no pasan de dos líneas;
  - el aviso de un archivo local distinto de su huella pasa a una línea pequeña junto al botón de la evidencia.
- **Resultado:** las tres pestañas de Calidad y auditoría caben sin desplazar a 1440 × 790 y a 1920 × 1000, también en el computador del autor, con el aviso local. Las otras páginas que sobraban se corrigen en las decisiones siguientes.
- **Pruebas:** las de D-257, D-272 y D-273 siguen pasando.

## D-275 · Monitoreo: las señales cuelgan de la carga semanal, no de ocho cadenas iguales

- **Pedido del autor:** que la pestaña Monitoreo se vea entera, sin desplazar, y que su esquema sea menos lineal: eran ocho filas idénticas de flechas (origen → señal → qué registra → dónde se lee).
- **Decisión:** la carga semanal va por el medio, en cinco etapas: Descarga, Construcción, Pruebas, Publicación y Panel. Cada señal cuelga de la etapa donde nace. Arriba, lo que ve el panel (dbt_result, etl_run y el aviso de huellas); abajo, lo que solo ve el autor (el log del agente, el correo «Run failed», el issue del informe semanal y el aviso de vencimiento del token). Al pie, una banda para el estado y el log que GitHub Actions guarda de cada paso. Cada tarjeta dice qué es y dónde se lee; al pasar el cursor, qué registra y qué archivo la produce. La frase que la presentaba es ahora su subtítulo.
- **Sin cambios:** las ocho señales, sus archivos, sus lectores y la prueba que exige que cada una exista en el código.
- **Resultado:** cabe sin desplazar a 1440 × 790 y 1920 × 1000.
- **Pruebas:** `tests/test_monitoring.py::test_d275_*`: cada señal cuelga de su etapa, del lado de su lector.

## D-276 · CI/CD: una fila para la integración y cuatro fases para la entrega

- **Pedido del autor:** lo mismo para CI/CD: una vista sin desplazar y un esquema menos lineal. Medía 1.123 px: cinco cajas de CI, diez cajas de la carga en zigzag y la publicación, más dos tarjetas de definición arriba.
- **Decisión:** la CI ocupa una fila (cambio, GitHub Actions, dbt parse, pytest, resultado). La entrega, otra: el disparo y cuatro fases, cada una con sus pasos numerados como en `semanal.yml`: Preparar (1 a 3), Ingerir (4 y 5), Construir y probar (6 a 8, con las dos puertas y la falla simulada opcional) y Publicar (9 y 10). Bajo Publicar, el release y Streamlit Cloud. Lo que significan CI y CD va en el encabezado de su fila, y cada paso dice, al pasar el cursor, qué hace y en qué línea de su workflow está.
- **Sin cambios:** los dieciocho pasos, sus textos, sus puertas y la línea de cada uno, que siguen leyéndose de los workflows.
- **Resultado:** cabe sin desplazar a 1440 × 790 y 1920 × 1000.
- **Pruebas:** `tests/test_devops.py::test_d276_*`: las cuatro fases tienen cada paso una vez, en el orden del workflow; cada paso tiene su pieza y su texto al pasar el cursor.

## D-277 · Las demás páginas caben en la ventana real: Despliegue, Pipeline y linaje, Arquitectura de seguridad y Stack

- **Problema:** medidas a 1440 × 790 (D-274), la pestaña Despliegue sobraba 50 px, Pipeline y linaje 42, Arquitectura de seguridad 94 y Stack y evidencia 19.
- **Decisión, sin cambiar ningún dibujo:**
  - **Despliegue, Arquitectura de seguridad y Stack:** el dibujo conserva su proporción y nunca es más alto que lo que la ventana deja bajo el encabezado; su marco toma el alto del dibujo;
  - **Pipeline y linaje:** el selector «Recorrido por capas / Linaje dbt» sube a la línea del título de la tarjeta, que tenía espacio, y los cuatro colores del recorrido comparten una línea con lo que significan. El recorrido sigue como en D-229.
- **Resultado:** las nueve páginas principales, las cuatro pestañas del Centro de operación, las tres de Calidad y auditoría, las cuatro vistas de Modelo de datos, el linaje dbt y una familia ampliada de Precios e inflación se ven sin desplazar a 1440 × 790 y a 1920 × 1000.
- **Pruebas:** la suite completa pasa (633).

## D-278 · La documentación se separa de la historia del proyecto

- **Decisión del autor:** los textos con forma de instrucción o de bitácora de sesiones no son documentación de lectura. Se eliminan los dos prompts de trabajo (`PROMPT_EVOLUCION.md` y el del 24-10) y las capturas de medición de `docs/diagnosticos/` (unos 40 MB; siguen en el historial de git). Los hitos y el backlog pasan a `docs/historia/`, fuera de la documentación. `DISENO.md` se resolverá junto con el retiro de las vistas antiguas que lo leen.
- **Pruebas:** la suite completa pasa.

## D-279 · Documentación profesional: encabezado, índice, glosario e historial en cada documento

- **Pedido del autor:** que cada documento se lea como documentación de ingeniería de una empresa: sin formas de conversación, con nombres estándar, sin referencias que el lector no pueda seguir y con un formato verificable.
- **Decisión:**
  - **Formato común:** cada documento abre con una tabla de encabezado (proyecto, tipo, versión, fecha, estado, responsable, propósito, audiencia y documentos relacionados), sigue con un índice enlazado y termina con el glosario y el historial de versiones, cuyas fechas son las de los commits que cambiaron el archivo;
  - **PRD 2.0, SAD 2.0 (arc42 con C4), ADR 2.0 (MADR: estado, fecha, contexto, decisión, opciones consideradas y consecuencias), Plan de pruebas de seguridad 2.0 (amenazas, controles, entorno, procedimiento, casos con su prueba y criterios de aceptación) y Manual de operación 2.0 (runbook: una fila por paso del workflow, con síntoma, causa y acción);**
  - **documentos nuevos:** Plan de capacidad y escalabilidad (antes, una sección del registro de decisiones), Glosario (antes, una sección de la guía del proyecto), Diccionario de datos, Plan de pruebas e Índice de decisiones (las 62 decisiones que explican el sistema, por tema);
  - **el plan de seguridad vuelve a llevar la tabla de sus diez casos**, que D-258 había dejado solo en el esquema: un plan de pruebas sin la tabla de casos no se puede imprimir ni revisar. La tabla y el esquema leen los mismos casos, y una prueba exige que coincidan con `bi/security_plan.py`;
  - **el Manual se dibuja como los demás documentos**, desde `docs/MANUAL.md`, con sus enlaces internos;
  - **los enlaces entre documentos** abren la página del documento en el panel, o el archivo en GitHub si aún no tiene página, y llegan a la sección exacta.
- **Pruebas:** `tests/test_documents.py::test_d279_*`: la redacción, el encabezado, el índice, el historial contra el historial de git, los enlaces y sus secciones, el diccionario de datos contra la base servida y el plan de seguridad contra el código; `tests/test_project.py::test_d279_every_acronym_of_the_documents_is_in_the_glossary`. `tests/medicion/medir.cjs` mide por omisión a 1440 × 790 y 1920 × 1000. La suite completa pasa (666).

## D-280 · Diagramas y logos de los documentos sin fondo; el PDF siempre en hoja blanca

- **Pedido del autor:** que los diagramas de los documentos se integren con la hoja blanca del PDF y con el tema del panel, con los logos sin fondo y en su color propio, y que ningún diagrama parezca una foto pegada sobre un rectángulo negro.
- **Decisión:**
  - **logos planos:** en los diagramas de los documentos (contexto, contenedores, casos de uso, procedimiento y casos de seguridad) cada tecnología es su logo en su color, sin el disco iluminado. GitHub, cuyo logo es negro o blanco, toma el color del texto del tema. El núcleo del plan de seguridad es un borde con relleno translucido. Las vistas del panel (pipeline, mapa de seguridad, Monitoreo y Stack) conservan sus discos, como fueron aprobadas;
  - **PDF en hoja blanca:** desde un tema oscuro, «Imprimir o guardar como PDF» vuelve a abrir la página en el tema Corporativo, la imprime y regresa al tema del lector. El PDF tiene así el mismo aspecto desde cualquier tema;
  - **impresión limpia:** Chrome imprime una sombra difuminada como un rectángulo gris, así que en papel los diagramas no llevan sombras ni filtros. Una tabla larga se corta entre filas y repite su encabezado, en vez de dejar una página en blanco.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d280_*`: ningún diagrama de documento tiene un rectángulo de fondo que cubra su lienzo, en ninguno de los cuatro temas; los logos son planos; los archivos de logos no tienen fondo; el botón de impresión pasa al tema claro desde los oscuros, y en papel no hay sombras.

## D-281 · Un solo componente para botones y enlaces

- **Pedido del autor:** un solo componente fino y de aire moderno para las acciones de documento, «Anterior / Siguiente», los enlaces a GitHub, la impresión a PDF y los enlaces de las barras, legible en los cuatro temas.
- **Decisión:**
  - **definido una vez:** el aspecto vive en `bi/premium.css` (`.go-btn`): borde de 1 px, esquinas suaves, relleno casi transparente con un leve brillo de vidrio, ícono fino a la izquierda y, al pasar el cursor o con el foco del teclado, el borde y un halo en el color de acento del tema. `bi/buttons.py` escribe el marcado;
  - **variantes y tamaños:** principal (imprimir), secundario (GitHub, barras) y de texto (enlaces a GitHub dentro de una página); compacto para las barras y normal para las páginas. La misma regla viste los enlaces de página que Streamlit dibuja para «Anterior / Siguiente»;
  - **íconos como máscaras CSS:** `st.html` descarta el SVG en línea, así que cada ícono es una máscara pintada con el color del texto;
  - **se retiran** los estilos sueltos del botón de impresión y del enlace de la barra.
- **Pruebas:** `tests/test_buttons.py`: el componente se define una sola vez y no quedan estilos de enlace sueltos; cada variante y tamaño escribe el componente; las barras, los documentos y la impresión lo usan; cada ícono tiene su máscara; el texto, el acento y el borde cumplen el contraste AA en los cuatro temas.

## D-282 · Una sola carpeta «Documentos» en el menú

- **Pedido del autor:** todos los documentos en un solo lugar del menú, y solo documentos, presentados como archivos.
- **Decisión:**
  - **menú:** un bloque «Documentos» con una entrada, «Carpeta de documentos». El SAD sale de «Ingeniería de datos», el plan de pruebas de seguridad de «DevOps y seguridad», y el PRD, el ADR y Escalabilidad dejan «Análisis de negocio · BA», que queda vacío y se retira. Un documento abierto ilumina la carpeta en el menú;
  - **la carpeta** (`bi/documents_folder.py`) muestra los diez documentos de `docs/` (PRD, SAD, ADR, diccionario de datos, capacidad y escalabilidad, plan de pruebas, plan de pruebas de seguridad, manual de operación, índice de decisiones y glosario) en cuadrícula o en lista. Cada archivo muestra su nombre estándar, su propósito, su versión y fecha leídas de la tabla de encabezado del propio archivo y su tiempo de lectura, con tres acciones: Abrir, PDF (la impresión de D-248 en hoja blanca, D-280) y GitHub. Al pasar el cursor, una vista previa con el índice del documento. Encabezado con la ruta «GreenOcean / docs», el número de documentos y la fecha del último cambio. Cabe en una pantalla a 1440 × 790 y 1920 × 1000;
  - **dentro de un documento:** la ruta fina «Documentos / nombre» vuelve a la carpeta, y el pie lleva al anterior y al siguiente de la carpeta;
  - **el glosario, el índice de decisiones, el diccionario de datos y el plan de pruebas** se leen como los demás documentos, con su encabezado, su PDF y su ruta; la vista anterior del glosario por temas se retira;
  - **las direcciones antiguas siguen funcionando:** cada documento conserva su ventana y su nombre de vista.
- **Pruebas:** `tests/test_dashboard.py::test_d282_*`: la carpeta muestra los diez documentos con la versión y la fecha de su archivo; cada documento de `docs/` está en la carpeta y en ningún otro bloque del menú, y ningún bloque queda vacío; cada documento abre su página con su ruta, su PDF y sus vecinos; las direcciones antiguas siguen abriendo su documento; la acción PDF imprime en hoja blanca; cada vista previa muestra el índice de su documento. `tests/medicion/medir.cjs` e `imprimir.cjs` siguen el menú nuevo.

## D-283 · Español e inglés: el idioma se elige como el tema, y los documentos existen en las dos lenguas

- **Pedido del autor:** que el panel, tal como cambia de tema, se pueda leer entero en inglés, y que los documentos existan en las dos lenguas.
- **Decisión (primera capa: estructura, documentos y marco del panel):**
  - **el idioma** vive en la sesión y en la dirección (`?lang=en`), como el tema; el español es el idioma por omisión y no agrega nada a las direcciones, de modo que las antiguas siguen iguales. El selector «ES · EN» está junto a «Apariencia», con el componente de D-281;
  - **las traducciones** son un diccionario del proyecto (`bi/i18n.py`, sin dependencias): `tr` da el inglés de un texto cuando el lector eligió inglés. Los datos (productos, regiones y canales de ODEPA) no se traducen;
  - **los diez documentos** existen en `docs/en/` con los mismos nombres de archivo, la misma estructura, los mismos identificadores (RF, RNF, P, ADR, S, T, D) y las mismas cifras. Las fechas van en formato ISO (2026-10-25) y las cifras con el separador inglés (5,000). Los nombres siguen la tabla aprobada por el autor: Product Requirements Document (PRD), Software Architecture Document (SAD), Architecture Decision Records (ADR), Security Test Plan, Operations Runbook, Capacity and Scalability Plan, Decision Index, Data Dictionary, Test Plan y Glossary;
  - **el panel en inglés** muestra el documento en inglés, su ruta, sus acciones y su PDF en el idioma activo; la carpeta lee la versión y la fecha del archivo en inglés;
  - **traducido en esta capa:** el menú (secciones, páginas y fuentes), el pie del menú, la barra de cada página (ruta, título y descripción), el encabezado de los documentos, los pies «Anterior / Siguiente», la atribución de los datos, el sello de dbt, la carpeta y los diez documentos;
  - **pendiente (capas siguientes):** el contenido de cada página principal (tarjetas, gráficos, diagramas y sus textos al pasar el cursor) y los diagramas de los documentos.
- **Pruebas:** `tests/test_i18n.py`: cada texto que pasa por `tr` tiene su inglés; el menú, los documentos y el marco tienen su inglés; cada documento existe en inglés con la misma estructura, los mismos identificadores, los mismos marcadores de diagrama y las mismas cifras; cada documento en inglés tiene su encabezado, su índice, su glosario y su historial, con la versión y la fecha del documento en español; la redacción en inglés; cada enlace y cada entrada del índice en inglés llega a su sección; cada sigla está en el glosario en inglés; el glosario en inglés nombra páginas que existen; el idioma sigue a la dirección y el español deja las direcciones como estaban; un documento y la carpeta se abren en inglés.

## D-284 · Español e inglés, segunda capa: cada página se traduce al dibujarse

- **Pedido del autor:** el panel entero en inglés, no solo su marco (D-283).
- **Decisión:**
  - **traducción en el borde con Streamlit:** las páginas están escritas en español en muchos módulos. En vez de envolver cada texto, `bi/i18n.py` traduce lo que el panel dibuja: cada nodo de texto y cada atributo visible de un bloque HTML (también dentro de los marcos de los diagramas), cada etiqueta de un control, cada columna de una tabla y los títulos, las etiquetas y las series de cada gráfico. Los scripts conservan su código (solo se traducen sus textos enteros) y el código, el texto preformateado y los estilos no se tocan;
  - **un texto se traduce entero o no se traduce:** cada entrada de `bi/i18n_en.py` es un texto completo, o una plantilla cuyos huecos guardan un número (`{n}`), un mes (`{m}`), una fecha (`{d}`) o un dato (`{}`), nunca palabra por palabra. Una frase sin traducir queda entera en español en vez de quedar a medias;
  - **cifras y fechas en el formato de cada idioma:** 2,521,012 y 0.2 en inglés; 2026-10-05, «Oct 12–18, 2026» y «September 2026». Un número de versión (1.5.6) no se toca. Los gráficos usan el formato inglés de números y meses;
  - **los datos no se traducen:** productos, variedades, familias, regiones y canales de ODEPA quedan como los publica la fuente, igual que los nombres oficiales entre comillas;
  - **traducción en el origen** donde un texto se arma de varias partes que una plantilla no puede separar con seguridad: los errores de GitHub (`bi/control.py`), los mensajes del estudio SQL, las listas de familias («y» / «and»), el glosario técnico de los diagramas (`bi/tech_glossary.py`, con su entrada en inglés) y las frases que un diagrama corta en líneas (se traducen antes de cortarse);
  - **capturas en inglés:** el PRD en inglés muestra capturas de las páginas en inglés (`docs/img/en/`), una por tema;
  - **correcciones en español de paso:** las descripciones del modelo estrella ya no pierden sus mayúsculas («semana ISO», «D-095»).
- **Resultado:** las diez páginas del menú, las vistas que aparecen tras un selector (el linaje dbt y las cuatro vistas del modelo de datos), las once ventanas de evidencia de Calidad y auditoría y los diez documentos se leen enteros en inglés.
- **Pruebas:** `tests/test_i18n.py::test_d284_*`: cifras, fechas y versiones; un texto se traduce entero y el código queda igual; un gráfico nombra la misma serie en sus datos, su escala y sus condiciones; cada plantilla tiene los mismos huecos en las dos lenguas; ninguna pantalla muestra texto en español cuando el lector eligió inglés (`tests/i18n_audit.py`, que también se ejecuta a mano para listar lo que falta).

## D-285 · El mapa de la app: todo el sistema en una vista

- **Pedido del autor:** una página «Mapa de la app», junto a «Stack y evidencia», con todo el sistema en una sola vista interactiva que se explique sola; Stack queda como resumen de las nueve herramientas principales y enlaza al mapa.
- **Decisión** (`bi/app_map.py`):
  - **de izquierda a derecha,** las capas por las que pasan los datos: fuentes, ingesta, aterrizaje, bronce, transformación, data warehouse, publicación (el release «base-actual» y su puntero), panel y lectores. Arriba, la orquestación (el repositorio, GitHub Actions y la integración continua); debajo del flujo, la capa del navegador (HTML, CSS y JavaScript; Altair y Vega-Lite); abajo, lo que vigila el sistema: las puertas de calidad, la paridad, la seguridad, la observabilidad, los documentos y la medición de pantallas;
  - **cada tecnología es un nodo** con su logo sin fondo. Al pasar el cursor: qué es, su rol en GreenOcean, cuándo actúa y con qué se conecta; esa lista se lee de las líneas del propio dibujo. Un clic abre la página del panel donde trabaja;
  - **las tecnologías pequeñas** viven en el nodo de su función (requests, certifi y la raíz emSign, pyarrow, dbt-duckdb, pandas, hmac.compare_digest, Playwright y otras): nada de lo que el proyecto usa queda fuera;
  - **filtros por tema** (datos, orquestación, calidad, seguridad, observabilidad, navegador y apoyo) atenúan el resto; el camino de un nodo (sus entradas y salidas) se resalta al pasar el cursor; la leyenda nombra los cuatro tipos de línea;
  - **el nodo «Apoyo con IA»** dice que se usó Claude como apoyo para la revisión técnica, la revisión de la documentación y la elección de etiquetas, y que el contexto del proyecto vive en archivos Markdown con un enfoque parecido a la recuperación de contexto, pero sin RAG: no hay base vectorial ni embeddings. No forma parte del flujo de datos;
  - **una pantalla:** los nodos son HTML, de modo que la letra no encoge, y un script dibuja las líneas cuando los nodos ya tienen su lugar. Cabe sin desplazar a 1440 × 790 y 1920 × 1000 en los cuatro temas y en las dos lenguas; bajo 760 px de ancho se apila por capas. Sin dependencias nuevas.
- **Pruebas:** `tests/test_app_map.py`: toda dependencia de `requirements*.txt` está en el mapa; todo archivo y módulo que nombra existe; cada línea une dos nodos y ningún nodo queda solo; cada clic abre una página del menú; cada texto al pasar el cursor tiene sus cuatro partes, leídas de las líneas; las herramientas pequeñas viven en el nodo de su función; el nodo de IA dice exactamente lo que es y queda fuera del flujo; el mapa es HTML con logos como imagen y un script sin etiquetas; el mapa está junto a Stack y Stack enlaza a él. La auditoría de idioma (D-284) lo cubre en inglés.

## D-286 · La carpeta de documentos, más grande y siempre a la vista; las fuentes, plegadas

- **Pedido del autor:** la carpeta de documentos más abajo y más grande, como una carpeta, y las fuentes plegadas por omisión.
- **Decisión:** «Documentos» deja de ser una sección del menú y pasa al pie del menú, encima de «Apariencia», como una carpeta azul grande con su nombre: siempre a la vista, sin desplazar, y encendida con el borde de acento mientras hay un documento abierto. «Fuentes de datos» empieza plegada y se abre con un clic. Para dejar sitio, el selector de idioma pasa a la línea de «Apariencia» y GitHub. El menú se desplaza por encima del pie fijo: al abrir las fuentes, se mueve solo hasta que sus enlaces quedan a la vista, en cualquier alto de ventana (comprobado a 1024 × 700, 1280 × 650, 1366 × 600 y 1440 × 790).
- **Pruebas:** `tests/test_dashboard.py`: el menú termina con la carpeta en el pie; las fuentes empiezan plegadas y un clic las abre.

## D-287 · Las fuentes, un ícono propio junto a la carpeta

- **Pedido del autor:** «Fuentes de datos» quedaba muy pequeño; mejor un ícono propio y grande como la carpeta de documentos.
- **Decisión:** el pie del menú lleva dos fichas del mismo tamaño, lado a lado: la carpeta «Documentos» y «Fuentes», con un ícono de base de datos verde. Un clic en «Fuentes» abre un panel flotante con los tres archivos oficiales (ODEPA mayorista, ODEPA consumidor e IPC del INE), que se abren en una pestaña nueva; el panel no ocupa sitio en el menú, así que nada queda tapado en ninguna altura de ventana. La sección plegable «Fuentes de datos» y la línea «Fuente: ODEPA · actualización automática cada martes» salen del menú: la ficha las reemplaza.
- **Pruebas:** `tests/test_dashboard.py::test_d118_*`: las fuentes son una ficha del pie con sus tres enlaces externos; el menú ya no tiene la sección plegable.

## D-288 · Cada documento abre con su portada; tablas tipo tabla dinámica; la carpeta, en lista

- **Pedido del autor:** una presentación elegante, corporativa y casi futurista, en el panel y en el PDF; tablas elegantes, como una tabla dinámica de Excel; la carpeta de documentos abierta en lista.
- **Decisión:**
  - **portada:** cada documento abre con una portada leída de su tabla de encabezado: el proyecto, el tipo de documento, el título, el propósito, la versión, la fecha, el estado, el responsable, la audiencia y los documentos relacionados. En el panel, la tabla de encabezado ya no se repite debajo; en el PDF, la portada ocupa la primera página. El archivo conserva su tabla para que GitHub la muestre;
  - **tablas:** encabezado en una banda del color de acento, filas alternas y primera columna en negrita, que nombra la fila; igual en los cuatro temas y en el PDF;
  - **carpeta:** se abre en vista de lista; la cuadrícula sigue a un clic.
- **Pruebas:** `tests/test_documents.py::test_d288_*`: cada documento tiene su portada con su versión, fecha, estado, responsable y audiencia, y su cuerpo ya no repite la tabla; `tests/test_i18n.py`: la portada en inglés.

## D-289 · Los diagramas propios de los documentos: secuencias, columnas, líneas de tiempo y árboles

- **Pedido del autor:** más diagramas, sobre todo de secuencia; al menos tres por documento y cinco en el SAD; elegantes, sin fondo y coherentes con la app.
- **Decisión:** `bi/doc_figures.py` dibuja los diagramas propios de los documentos con seis formas: secuencia (actores con su logo, pasos numerados en una columna propia y la puerta de publicación como banda roja), columnas, línea de tiempo, árbol de decisiones, barras y comparación. Todos son transparentes, toman los colores del tema y se traducen con el idioma del panel. `bi/doc_diagrams.py` los registra junto a las vistas que ya existían (contexto, contenedores, casos, pantallas, procedimiento y casos de seguridad). Las barras del índice de decisiones se cuentan en las tablas del propio índice, así la figura nunca contradice al texto. Una etiqueta más ancha que su flecha nace donde nace la flecha, sin tapar los números de los pasos.
- **Pruebas:** `tests/test_doc_diagrams.py`: cada marcador nombra un diagrama que existe, ninguno se repite entre documentos y cada diagrama se usa; `tests/test_i18n.py`: ningún diagrama muestra español con el panel en inglés.

## D-290 · Siete documentos para todo lector: el SAD absorbe la escalabilidad y el diccionario; un solo plan de pruebas y seguridad

- **Pedido del autor:** documentos claros para quien no es técnico, «como un CV», de lo más importante a lo menos; el SAD como lugar de lo que estaba repartido; el plan de pruebas y el de seguridad en uno solo, con todos los actores (el autor, GitHub, Streamlit, la clave, el token); un índice de decisiones de alto nivel, sin códigos abstractos ni enlaces que no se entienden; ninguna contradicción entre documentos ni con la app.
- **Decisión:**
  - **carpeta:** PRD, SAD, ADR, Plan de pruebas y seguridad, Manual de operación, Índice de decisiones y Glosario. `ESCALABILIDAD.md` pasa a la sección 9 del SAD, «Capacidad y crecimiento»; `DICCIONARIO_DATOS.md`, a la sección 6, «Los datos»; `SEGURIDAD.md` se funde con `PLAN_PRUEBAS.md`. Las direcciones antiguas (`escalabilidad`, `diccionario-de-datos`, `plan-de-pruebas-de-seguridad` y sus títulos) abren el documento que las contiene. El plan vive en la sección Seguridad y la página «Arquitectura de seguridad» enlaza a él;
  - **orden de lectura:** cada documento abre con «En resumen» en lenguaje simple y sigue de lo más relevante a lo menos. PRD: problema, usuarios, preguntas y requisitos; SAD: contexto, contenedores, la carga y el panel en secuencia, los datos, el despliegue, la calidad y la seguridad, y el crecimiento; plan: qué se prueba, quién participa, amenazas, casos y las secuencias de una carga manual y de un cambio de código; manual: el calendario, el árbol de fallas y la recuperación;
  - **índice de decisiones:** cada fila dice primero qué se decidió, en una frase sin siglas internas; el registro de arquitectura se enlaza por su nombre y el código D-xxx queda al final, para buscarlo;
  - **tablas:** la primera columna puede ser una frase y se ajusta al ancho; un identificador como RF-01 no se corta en su guion;
  - **coherencia:** los enlaces entre documentos apuntan a las secciones nuevas, y las cifras, los casos S-01 a S-10, las amenazas y las tablas de la base siguen comprobadas contra el código y la base.
- **Pruebas:** `tests/test_documents.py`: cada documento tiene al menos tres diagramas y el SAD al menos cinco; los documentos fundidos ya no existen y sus direcciones abren el que los contiene; el diccionario dentro del SAD describe cada tabla y columna de la base servida; el plan lleva las amenazas y los casos del código; la historia de un documento fundido conserva las fechas de los que absorbió. `tests/test_prd_traceability.py` lee las secciones por su nombre; `tests/test_i18n.py`: las siete versiones en inglés con la misma estructura.

## D-291 · El mapa de la app: cada filtro muestra todas sus piezas y conexiones, y sin filtro solo el flujo de datos

- **Pedido del autor:** las flechas del mapa estaban muy mezcladas, y los filtros no mostraban de verdad cada función con sus conexiones: Seguridad mostraba solo al autor, cuando la seguridad pasa también por GitHub y por Streamlit, con la clave y el token. El mapa debe representar la app con precisión.
- **Decisión:**
  - **líneas con tema:** cada conexión declara sus temas. Un filtro dibuja todas las líneas de su tema, cada una con su etiqueta (qué viaja por ella), y enciende todos los nodos que esas líneas unen. Sin filtro se dibuja solo el flujo de datos; el cursor sobre un nodo dibuja sus propias conexiones;
  - **seguridad completa:** un nodo nuevo, «Secretos del panel» (CONTROL_CODE y GITHUB_TOKEN en Streamlit Community Cloud, con hmac.compare_digest). El filtro Seguridad muestra al autor que escribe la clave, el panel que la compara y usa el token para lanzar la carga en GitHub Actions, el visitante y su SQL con límites, el repositorio sin secretos, la base en solo lectura, el workflow con permisos mínimos y las pruebas S-01 a S-10 que corren en cada push;
  - **cada tema, preciso:** Orquestación suma el puntero y el informe que la carga deja en main y la carga manual desde el panel; Calidad, la puerta de publicación y la paridad que corre pytest; Observabilidad, el correo al autor si la carga falla y el estado de las ejecuciones que el panel lee de la API de GitHub;
  - **trazado:** pytest · CI pasa a la franja «Lo que vigila»; dos líneas entre los mismos nodos se separan, una línea que salta un nodo lo rodea hacia el centro del dibujo, y cada etiqueta busca a lo largo de su línea el lugar que menos tapa otras etiquetas, nodos y títulos. Se quita la línea redundante del repositorio a GitHub Actions;
  - las etiquetas de las líneas son texto de la página, así se traducen al inglés como el resto.
- **Pruebas:** `tests/test_app_map.py::test_d291_*`: cada filtro enciende los actores y las conexiones de su tema (Seguridad: autor, panel, secretos, GitHub Actions, repositorio, base, visitante, pruebas); cada línea une nodos encendidos; sin filtro solo se dibuja el flujo de datos y cada línea lleva su etiqueta. `tests/test_i18n.py`: el mapa en inglés sin textos en español.

## D-292 · Revisión de coherencia entre los documentos, sus diagramas y la app

- **Pedido del autor:** que no haya contradicción entre ningún documento, ni entre los documentos y la app.
- **Revisado contra el código:** el horario del workflow (`0 12 * * 2`), los permisos del job (contenido e issues), el aviso del token (14 días), los límites del estudio SQL (una sentencia, 10 s, 5.000 filas, 1 GB), la puerta del 90 % de filas, las 31 pruebas de dbt, los casos S-01 a S-10 y las tablas de la base servida.
- **Corregido:**
  - el diagrama «Qué se prueba y cuándo» decía que en cada push cada cifra se recalcula desde la fuente; la reconstrucción desde las filas crudas corre en cada carga, donde existen, y en cada push la auditoría compara las cifras del panel con la base;
  - el PRD y el SAD dicen que el administrador de los diagramas C4 y de la arquitectura de seguridad es el autor del proyecto, el mismo actor que nombran el plan, el manual y el mapa de la app;
  - el README enlaza los siete documentos actuales en lugar del plan de seguridad retirado.
- **Pruebas:** la suite completa en verde; las pruebas de documentos comprueban las cifras, los casos, las tablas y los enlaces entre documentos.

## D-293 · El mapa de la app es el funcionamiento real: cada línea nombra su código, y la descripción no tapa las líneas

- **Pedido del autor:** confirmar que el mapa cubre la arquitectura del proyecto y que muestra cómo funciona de verdad, no solo algo bonito; que la descripción de un nodo no tape sus líneas de conexión.
- **Revisión contra el código:** cada conexión se comparó con los workflows y los módulos. Se corrigió una línea inexacta (el agente solo descarga los CSV; `etl.load_raw_files` los carga en `raw.db`) y se sumaron dos que existían y faltaban: `semanal.yml` y `pruebas.yml` descargan la base del release antes de trabajar.
- **Decisión:**
  - **evidencia:** cada línea declara dónde ocurre (el archivo y el código que lo hace) o, si ningún archivo del proyecto puede mostrarlo, la plataforma que lo hace (GitHub o Streamlit Cloud: el despliegue de main, el correo de una falla, la cuenta del autor). La descripción de cada nodo muestra ese archivo junto a cada conexión;
  - **la descripción no tapa el dibujo:** con el menú lateral abierto, la descripción se muestra sobre el menú, donde no corre ninguna línea; con el menú cerrado, va al lugar del dibujo que tapa menos líneas y vecinos del nodo. No intercepta el cursor, así nunca bloquea otro nodo;
  - **sin filtro**, se dibujan el flujo de datos y lo que llega al lector; las descargas de la base por los workflows aparecen en Orquestación y Calidad.
- **Pruebas:** `tests/test_app_map.py::test_d293_*`: cada línea tiene su evidencia y el archivo contiene el código que nombra; la descripción se aparta de las líneas del nodo. Medido en el navegador: con el cursor sobre GitHub Actions y sobre Streamlit, la descripción no tapa ningún punto de sus líneas a 1440 × 790 ni a 1920 × 1000.

## D-294 · La familia ampliada muestra sus cifras sobre las líneas; el IPC vuelve a verse en inglés

- **Pedido del autor:** el gráfico ampliado de una familia describía bien, pero le faltaban cifras precisas sobre las líneas.
- **Decisión:** solo en la vista ampliada (las tarjetas pequeñas siguen sin cifras):
  - el último valor de cada línea, al final de la línea (la familia y el IPC de alimentos);
  - el máximo de la familia marcado con su valor, el mismo «Máximo» que nombra la lectura de al lado; si el máximo es el último mes, lo dice la etiqueta final;
  - al pasar el cursor, una regla vertical con el mes, los dos valores y la diferencia en puntos.
  Todas las cifras son valores de la serie dibujada.
- **Corregido en el camino:**
  - en inglés, la línea del IPC desaparecía de los gráficos de Precios e inflación: Streamlit entrega los datos del gráfico como Arrow, y la traducción renombraba la serie en la escala pero no en los datos. Ahora traduce también los datos, con la misma regla;
  - «Ver todas» y «Diferencia en puntos» tienen su inglés;
  - la lectura ampliada ocupa algo menos de alto, así la página en inglés cabe en 1440 × 790.
- **Pruebas:** `tests/test_inflation_view.py::test_d294_*` (las etiquetas finales y el máximo son valores de la serie; la regla usa el mes más cercano y la diferencia es la resta de los dos valores) y `tests/test_i18n.py::test_d294_*` (la serie del IPC se llama igual en los datos Arrow y en la escala).

## D-295 · Dos vistas al entrar: usuario y profesional, y el perfil profesional que va adelante

- **Pedido del autor:** una persona común ve solo lo que necesita; un perfil profesional ve todo, en el orden de lectura de un portafolio según el perfil que quiere poner adelante (Data Eng, BA, BI, DevOps, Seguridad). Se elige una vez al entrar, en una pantalla simple; adentro no se cambia: la vista de usuario abre el resto solo con la clave de la app.
- **Decisión:**
  - al entrar, una ventana que no se puede cerrar sin elegir pregunta «Elige tu vista»: «Vista de usuario», o «Vista profesional» con cinco opciones pequeñas (Data Eng · BA · BI · DevOps · Seguridad). La elección queda en la sesión y en la dirección (`?perfil=…&rol=…`): un enlace compartido abre la misma vista en una visita nueva, pero dentro de una visita la dirección ya no cambia la vista;
  - la vista de usuario muestra en el menú solo Negocio · BI y las fuentes; «Ver todo el proyecto» pide la clave de control de la app (comparada en tiempo constante) y, si es correcta, abre la vista profesional con el orden de BI;
  - la vista profesional muestra todo, con el perfil elegido adelante: Data Eng abre en Ingeniería de datos; BA y BI, en Negocio; DevOps, en DevOps y seguridad; Seguridad, en la Arquitectura de seguridad. Al elegir, el panel abre la primera página de ese orden;
  - una dirección antigua con un perfil retirado («Reclutamiento», «Analista BI») se limpia y la ventana pregunta. Reemplaza la entrada sin perfil de D-213.
- **Pruebas:** `tests/test_dashboard.py::test_d295_*`: la primera visita pregunta; la vista de usuario ve el negocio, la dirección no la cambia y solo la clave correcta abre el resto; cada perfil profesional ordena el menú como su portafolio. `tests/test_i18n.py`: la ventana en inglés.

## D-296 · Un dashboard de verdad: el mercado, la inflación y los datos, una pantalla por pestaña

- **Pedido del autor:** además del resumen, un dashboard digno de una herramienta de BI (tortas, barras, tablas de calor), premium, con el aire de Google Cloud, en una vista compacta y legible, inteligentemente interactivo; que deje claro qué muestra (la semana actual, las últimas semanas, las familias, las regiones) y que la cantidad de semanas se ajuste con un control deslizable.
- **Decisión:** la página «Dashboard», la primera de Negocio · BI, con tres pestañas:
  - **Mercado:** la semana actual en cinco indicadores (precios comparables, cuántos subieron, cuántos bajaron, alertas) y cuatro preguntas, una por gráfico: ¿cómo se movieron los precios esta semana? (dona), ¿qué familias subieron? (barras; un clic filtra), ¿en qué regiones? (de norte a sur, % que subió y que bajó) y ¿cómo vienen las últimas semanas? (tabla de calor; un control elige de 4 a 12 semanas). Arriba, la semana y la familia se eligen en la barra;
  - **Inflación:** el IPC de alimentos y cuántas familias subieron más, menos o a su ritmo; cuánto subió cada familia frente al IPC; la inflación de alimentos en 12 meses y cada año por familia;
  - **Datos y operación:** la última carga, las filas leídas y rechazadas, las pruebas de dbt y los indicadores de calidad; qué trajo cada carga, cuántos precios entran a los indicadores, de qué fuente vienen y cada indicador frente a su umbral.
  Cada cifra usa la misma definición que la página que resume: el cambio compara las mismas regiones en ambas semanas, una familia se mueve por la mediana de sus series, «sin cambio» es menos de 0,05 % y «al ritmo» es ± 2 puntos del IPC. Las tarjetas toman el alto de la ventana: cabe en 1440 × 790 y crece en 1920 × 1000.
- **Pruebas:** `tests/test_overview.py`: los precios, las comparaciones, las familias, las direcciones y las regiones son las del Resumen; los años de cada familia encadenan su alza total; cada gráfico responde una pregunta y las tarjetas crecen con la ventana. `tests/test_i18n.py`: el dashboard en inglés.

## D-297 · Los diagramas de los documentos: íconos sin fondo y flechas en ángulo recto; el código, sobrio

- **Pedido del autor:** ningún diagrama de tarjetas; diagramas con íconos y sin fondo, flechas rectas que, si giran, lo hacen en 90 grados; muy precisos y coherentes. El código dentro de los documentos, sobrio y fácil de leer, no un verde que cansa la vista.
- **Decisión:**
  - un solo constructor de diagramas (`bi/doc_figures.py`, `graph`): cada pieza es su logo o un ícono de línea, con su nombre y una nota debajo, sin caja; las líneas salen de un costado o de abajo y giran solo en ángulo recto; la etiqueta de cada línea va en su tramo propio (al final, o al inicio cuando dos líneas comparten el último tramo) y, cerca del borde, a la izquierda de la línea;
  - con él se redibujan las figuras que eran columnas de tarjetas, árboles de cajas y el antes y después (valor, requisitos, capas, despliegue, mapa de los ADR, ADR-35, niveles de prueba, actores de la seguridad, árbol de fallas, temas del índice, decisiones del índice y los tres esquemas del glosario), y también el contexto C4, los contenedores C4 y el procedimiento de seguridad; los encabezados de las secuencias ya no van en cajas. Los casos de uso (elipses UML) y los diez casos de seguridad (logos alrededor del candado) se conservan;
  - el código en línea usa el color del texto sobre un tono suave, en monoespaciada pequeña; un nombre largo se corta solo después de `_`, `/`, `.` o `::`, nunca en medio de una palabra.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d297_*`: el contexto y los contenedores nombran sus piezas y sus archivos reales; el procedimiento tiene sus cinco pasos; cada diagrama de íconos gira solo en ángulo recto y no tiene tarjetas.

## D-298 · Una carga fallida se avisa dentro del panel, en todas las páginas

- **Pedido del autor:** si la carga falla, algo dentro de la app debe llamar la atención casi de inmediato, además del correo y de GitHub.
- **Decisión:** el panel lee las ejecuciones de `semanal.yml` (las mismas del Centro de operación, guardadas 5 minutos). Si la última ejecución terminada falló de verdad (una falla simulada a pedido no cuenta, y una ejecución en curso no oculta el resultado de la anterior), arriba del menú de todas las páginas aparece un aviso rojo: «La carga del dd-mm falló · El panel muestra la última carga válida · Ver qué paso falló», con un enlace al Centro de operación; la primera página de la visita muestra además una notificación. Sin falla, no aparece nada. El Manual de operación lo nombra como la tercera vía de aviso.
- **Pruebas:** `tests/test_control.py::test_d298_*`: solo una falla real de la última carga terminada levanta el aviso; `tests/test_dashboard.py::test_d298_*`: con una falla, el aviso y su enlace están en el menú de cada página.

## D-299 · Un texto de los documentos nunca detiene la carga semanal

- **Problema confirmado:** las tres cargas manuales del 25-10-2026 fallaron en el paso «Run the tests against the new database». ODEPA ya había publicado la semana del 19-10, y `test_d210_the_prd_figures_match_the_served_database` exigía que el PRD dijera las cifras exactas de la base nueva (precios, semanas, filas). Con una semana más, el texto dejó de coincidir, pytest falló y la base no se publicó: la puerta de publicación funcionó, pero por un motivo que no es un error de los datos. Sin corrección, todas las cargas siguientes fallarían igual.
- **Decisión:** el PRD dice de qué carga son sus cifras («Con la carga del 20-10-2026…») y que la base crece cada martes. La prueba las compara cuando la base es esa carga y se omite, con su motivo, cuando la base es más nueva. El tamaño redondo del SAD («Unos 14 MB») se acepta con 2 MB de margen. Las cifras del día siguen en el panel, que las calcula de la base.
- **Pruebas:** `tests/test_documents.py::test_d210_*` y `test_d248_*` con la regla nueva.

## D-300 · El SAD completo y un ADR verificable

- **Pedido del autor:** el SAD debe cubrir lo que la app tiene y lo que un SAD debe tener (faltaban los componentes y los casos de uso, y los logos se veían chicos); el ADR se veía simple y poco sólido.
- **Decisión:**
  - **SAD 3.1:** «2.1 Escenarios clave» (vista de escenarios de 4+1: actor, escenario, requisito y contenedores que lo resuelven), «3.1 Componentes de la carga semanal» y «3.2 Componentes del panel» (C4, nivel 3, con los archivos reales); la sección del panel describe las vistas, el Dashboard, el aviso de carga fallida y los dos idiomas. Los íconos de las vistas C4 son más grandes. El SAD queda con nueve diagramas;
  - **ADR 3.1:** cada registro suma «Confirmación», la parte de MADR que dice cómo se comprueba la decisión: la prueba que la verifica en cada push. Dos pruebas nuevas cubren las que no tenían una (ADR-04, los datos crudos fuera de Git; ADR-31, ningún data warehouse en la nube como dependencia);
  - el glosario suma BA.
- **Pruebas:** `tests/test_documents.py::test_d300_*`, `test_adr04_*` y `test_adr31_*`; la lista de diagramas del SAD.

## D-301 · El Dashboard: tablas con logos a todo el ancho y una explicación en cada cifra

- **Pedido del autor:** más espacio para la tabla de las últimas semanas (números chicos), una tabla con el logo de cada familia, tarjetas y tortas más pequeñas, en todas las pestañas; al pasar el cursor por un indicador o un gráfico, una explicación breve de qué es, contra qué se compara y qué dice.
- **Decisión:** cada pestaña tiene una fila de tres gráficos compactos y una tabla a todo el ancho (Mercado: las últimas semanas; Inflación: cada año; Datos y operación: los indicadores de calidad con su dimensión y significado). Las tablas son HTML: logo y nombre de cada familia, celdas rojas o azules según el cambio, números de 13 px. Cada indicador y cada título de gráfico abre al pasar el cursor una explicación con las cifras del momento. «Lácteos - Huevos - Margarinas» se muestra como «Lácteos y huevos» (33 de sus 34 productos); el nombre oficial aparece al pasar el cursor.

## D-302 · La pestaña Insights: preguntas, KPIs e insights de cada carga

- **Pedido del autor:** una pestaña con las preguntas, los KPIs con su cálculo y por qué, y un insight destacado y dinámico, uno para quien compra y otro para un data architect.
- **Decisión:** a la izquierda, «Preguntas» (pregunta, quién la hace, el KPI que la responde y la respuesta de hoy) y «KPIs» (cómo se calcula y por qué); a la derecha, dos tarjetas calculadas de la base en cada carga: «Para quien compra» (qué bajó esta semana, las mayores bajas con dos cotizaciones, qué familias superan al IPC) y «Para quien diseña los datos» (qué trajo la carga, qué parte llega a los indicadores y dónde se pierde). Ninguna cifra se escribe a mano.

## D-304 · La tabla de productos dice qué regiones subieron y bajaron

- **Pedido del autor:** la columna «Regiones ↑ / ↓» cuenta regiones, pero no dice cuáles.
- **Decisión:** cada fila lleva, al pasar el cursor por su conteo (subrayado punteado), un cuadro propio que se abre al instante, hacia arriba, con las regiones de ese producto y canal y su cambio, de la mayor alza a la mayor baja, en rojo y azul; la región elegida en el mapa sale resaltada. No es una columna más: un producto puede subir en varias regiones y la lista llegaría a nueve nombres. Son las mismas cifras de las que sale el conteo. Cada fila es un producto: puede subir en la mayoría de las regiones mientras su familia, en conjunto, baja.
- **Pruebas:** `tests/test_home_mockup.py::test_d304_*`.

## D-305 · Resumen más compacto y la tabla de semanas del Dashboard, como una tabla de verdad

- **Pedido del autor:** la tabla de las últimas semanas no se entendía y no parecía una tabla; en el Resumen, las familias y los menús ocupaban demasiado y la lista de regiones no se veía como algo en lo que se puede hacer clic.
- **Decisión:** la tabla del Dashboard se titula «¿Qué familias vienen subiendo, semana a semana?», explica que cada fila es una familia y cada columna una semana, tiene celdas con bordes y se desplaza hacia los lados cuando hay muchas semanas. En el Resumen, las filas de familias y los menús de canal y orden son más bajos, la tabla de productos gana alto y el conteo de regiones se ve como un enlace («clic»).

## D-306 · Dónde se compra: los puntos que existen en cada región, solo como información

- **Pedido del autor:** para quien lee el panel, sin repeticiones: mostrar los puntos de compra que existen en cada región (en Santiago, Lo Valledor, la Vega Central…), sin precios por mercado. Los precios de los puntos de una misma ciudad se mueven juntos: si sube en una región, sube en todos sus mercados; la diferencia entre ellos es mínima.
- **Decisión:** el Dashboard, pestaña Mercado, deja de repetir el Resumen (se quitan la dona, las familias y las regiones, que ya dicen los indicadores y el Resumen) y muestra «¿Dónde se compra, región por región?»: una tarjeta por región, de norte a sur, con un ícono de volumen para cada mercado mayorista (con su nombre) y para cada tipo de punto de venta al consumidor que ODEPA registra, y en Santiago sus sectores; unas flechas pasan de a una región, de a tres tarjetas. Las tarjetas toman el alto de su contenido (sin espacio sobrante) y la tabla de semanas, el que necesita. Ninguna cifra ni precio. Los nombres salen de los archivos de ODEPA y se guardan en `bi/assets/points_of_sale.json`, que se regenera con `python etl/points_of_sale.py`; el modelo de datos y el pipeline no cambian.
- **Pruebas:** `tests/test_points_of_sale.py`: las regiones del archivo existen en la base, el archivo es lo que dicen los archivos descargados (cuando están) y el panel no muestra precios.

## D-307 · El Dashboard en palabras de todos los días: Inflación clara, sin pestaña de operación y Insights con preguntas reales

- **Pedido del autor:** que quien llega entienda de inmediato. La línea del «IPC en 12 meses» que baja parecía contradecir que la inflación siempre sube; las barras rojas y azules con signo «+» y la tarjeta «¿Cuántas subieron más que la inflación? 7» no se entendían; la pestaña «Datos y operación» no tenía razón de ser; las etiquetas «Para quien compra», «Compra por mayor» y «Diseña los datos» eran ambiguas.
- **Decisión:** la pestaña Inflación habla de la «canasta» (los alimentos en general, el IPC de alimentos del INE): «Alimentos desde 2022», «Alza en el último año» y cuántas familias subieron más, menos o igual que la canasta. Las barras dicen qué es el rojo (subió más que la canasta, línea punteada) y qué es el azul (subió, pero menos). La línea se titula «¿La inflación está bajando?» y explica que, mientras esté sobre cero, los precios siguen subiendo, solo que más lento. La tabla año por año incluye «Alimentos en general». Se quita la pestaña «Datos y operación»: su contenido de calidad vive en Calidad y auditoría y en el Centro de operación. Insights tiene seis preguntas con «Para quién» y «Dónde verlo», cada una con la respuesta de hoy calculada de la base; el lector se elige con tres íconos: persona común, comerciante mayorista y quien diseña los datos.
- **Pruebas:** `tests/test_overview.py` (cinco gráficos, cada uno con su pregunta), `tests/test_i18n.py` (todo texto con su inglés, también en el Dashboard).

## D-308 · Sin Dashboard: Panorama de precios, Dónde comprar e Insights; la falla de la carga, bajo llave

- **Pedido del autor:** el Dashboard repetía casi todo lo del Resumen semanal. «Dónde comprar» merecía una página propia, con casas más grandes y sin repetir «supermercado» en cada región; la tabla de semanas debía pasar al Resumen, tras un botón; la pestaña Inflación no aportaba; y la falla de la carga, en rojo, no debía verla nadie sin la llave, ni siquiera un reclutador.
- **Decisión:** se quita el Dashboard. El menú de Negocio es ahora «Panorama de precios» (antes «Resumen semanal», que se ve completo en una pantalla), «Dónde comprar» e «Insights». Dónde comprar muestra, región por región y de norte a sur, una casa por mercado mayorista con su nombre y una sola casa «Comercio al detalle» que agrupa los puntos de venta que ODEPA registra (supermercado, feria, carnicería, panadería…), nombrados al pasar el cursor; los sectores de Santiago siguen como texto. La barra del Panorama gana dos botones pequeños: «Semanas» abre en una ventana la tabla de familias por semana (la que estaba en el Dashboard) e «Inflación» abre Precios e inflación, que ya no tiene línea propia en el menú (`DOOR_PAGES`) pero conserva su dirección. Insights es una página propia. Se quitan la pestaña Inflación y sus cuadros. El aviso de carga fallida (D-298) solo se muestra con la llave: la vista de usuario no lo ve. El nombre «Dashboard general» sigue abriendo Dónde comprar.
- **Pruebas:** `tests/test_overview.py` (el Dashboard ya no existe y cada pieza tiene su lugar), `tests/test_dashboard.py` (menú de Negocio y aviso solo con la llave), `tests/test_i18n.py`.

## D-309 · El Panorama de precios cabe en una pantalla y dice qué región se está viendo

- **Pedido del autor:** al abrir el Panorama no se sabía qué región se estaba viendo sin hacer clic, y la página pedía desplazarse.
- **Decisión:** sobre el mapa, una línea «Viendo: todo Chile · clic en una región para ver solo esa» (o el nombre de la región elegida). Los paneles toman el alto de la ventana bajo la barra, el mapa se ajusta a él y la tabla de productos se desplaza por dentro, con la nota de cobertura a la vista. Medido sin desplazamiento a 1440 × 790, 1470 × 800 y 1920 × 1000.
- **Pruebas:** la suite completa; medición con Playwright.

## D-310 · Dónde comprar: todas las regiones a la vez, con casas 3D flotantes del color de cada región

- **Pedido del autor:** la página tiene espacio para todo; no hace falta navegar con flechas ni encerrar las regiones en cuadros. Casas 3D flotantes, como las ilustraciones de una tienda de audiolibros, de un color distinto por región, y la casa de los detallistas con la puerta abierta, mostrando adentro los puntos de venta en común.
- **Decisión:** las nueve regiones se ven juntas, de norte a sur, en tres filas sin tarjetas. Cada región lleva su nombre subrayado con su color y sus casas: una por mercado mayorista con su nombre, y la casa «Comercio al detalle», con el frente abierto y adentro los íconos de los tipos de punto de venta (nombrados al pasar el cursor). Las casas se dibujan en perspectiva (frente, costado y techo), flotan con un movimiento lento, y el ancho de cada región depende de cuántas casas tiene, para que todas midan lo mismo. Sin precios. Cada región se asienta en su propio terreno, un resplandor del color de la región con una línea de suelo, para que se vea cada agrupación. Se quitan las flechas y la vista de a tres regiones. Cabe en una pantalla a 1440 × 790 y 1920 × 1000.
- **Pruebas:** `tests/test_points_of_sale.py` (una columna de casas por región, un ícono por tipo de punto, sin precios).

## D-311 · Filtros finos en el Panorama y una lectura del período en la tabla de semanas

- **Pedido del autor:** los selectores de la tabla de productos ocupaban espacio de más; el botón de semanas, con un ícono de dinero; y la ventana de semanas tenía un control gigante en vez de una lectura de conjunto.
- **Decisión:** los selectores de Canal y Orden, y la búsqueda, miden 28 px de alto. El botón «Semanas» lleva el ícono $. En la ventana de semanas, la explicación y un control pequeño comparten una línea, y sobre la tabla aparece una «Lectura del período»: la familia que más se encareció en esas semanas (sus cambios semanales encadenados) y en cuántas subió, la que más bajó y en cuántas bajó, y en cuántas semanas subieron más familias de las que bajaron. Cada cifra sale de las celdas de la tabla.
- **Pruebas:** `tests/test_overview.py::test_d311_the_reading_of_the_period_chains_the_cells_of_the_weeks_table`.

## D-312 · La región que se lee, siempre visible sobre las familias

- **Pedido del autor:** al abrir el Panorama no se sabía en qué región estaba por defecto; la región elegida debe verse sobre el movimiento por familia.
- **Decisión:** en la cabecera de «Movimiento por familia» hay una etiqueta «Región: Todo Chile» (o el nombre de la región elegida en el mapa), siempre visible; se suma a la línea «Viendo» sobre el mapa. El Panorama sigue cabiendo en una pantalla.
- **Pruebas:** la suite completa, con la auditoría del inglés.

## D-313 · Un mismo encabezado en los tres paneles del Panorama

- **Pedido del autor:** títulos consistentes, claros y pensados para quien lee, sin cambiar el diseño ni los datos.
- **Decisión:** cada panel lleva una etiqueta corta en mayúsculas y una pregunta como título. Mapa: «Precios por región» y «¿Hacia dónde se movieron los precios?». Familias: «Variación por familia» y «¿Qué familias subieron y cuáles bajaron?», con el subtítulo de una línea «Mediana de variaciones de precios comparables, todo Chile.». Tabla: «Detalle de productos», con la familia elegida en una etiqueta aparte, y «¿Qué productos explican el cambio?». La tipografía y los colores no cambian; la tabla cede la altura de las nuevas líneas y el Panorama sigue cabiendo en una pantalla.
- **Pruebas:** `tests/test_dashboard.py`, `tests/test_home_mockup.py` y la auditoría del inglés.

## D-314 · La tabla de semanas con total, orden y puntos; vuelta a todo Chile

- **Pedido del autor:** la vista «Semanas» con una columna de total, filas ordenadas, celdas pequeñas como punto, etiquetas claras y un título; y una forma de volver a «todo Chile» tras elegir una región. El gráfico del índice mensual se devuelve a su versión anterior, sin los cambios que se habían probado.
- **Decisión:** la tabla lleva una columna final «Total 8 sem» (la variación de la familia en las semanas mostradas, sus medianas semanales encadenadas, en negrita y con signo), con las filas de mayor a menor total. Una celda con cambio menor a 0,3 en valor absoluto muestra un punto tenue y sin fondo; nunca «-0,0». La «Lectura del período» cuenta las alzas y bajas con ese mismo umbral, así que coincide con lo que se ve. El control se llama «Últimas N semanas», el subtítulo es «Variación semanal, %. Rojo: subió · Azul: bajó.» y la ventana lleva el título «¿Qué familias vienen subiendo, semana a semana?». En el mapa, tras elegir una región, la línea «Viendo» ofrece «Ver todo Chile».
- **Pruebas:** `tests/test_overview.py::test_d311_…` (total, orden, sin «-0,0»).

## D-315 · El mapa de precios por región, con menos peso para las regiones sin dato

- **Pedido del autor:** ajuste mínimo, sin cambiar el diseño: las regiones sin dato pesan menos, la leyenda distingue «sin cambio claro» de «sin dato», y una fila resalta su región.
- **Decisión:** las regiones sin dato se dibujan con una trama gris muy clara, su fila con nombre apagado, línea más fina y tenue y «sin dato» pequeño, sin recuadro. La leyenda separa «Sin cambio claro» (gris medio sólido) de «Sin dato» (trama). Al pasar el cursor por una fila, su región se resalta en el mapa con un contorno blanco (y al revés).
- **Pruebas:** la suite completa; revisión en pantalla.

## D-316 · Encabezado esencial del Panorama, la × que cierra y los años del índice ampliado

- **Pedido del autor:** el encabezado del Panorama se veía mal, con cosas inútiles y mezcladas (la pregunta cortada, los contadores de familias y regiones y el aviso de alertas se pisaban); la × de la ventana de semanas no cerraba; y el gráfico del índice mensual ampliado debía mostrar los años bajo el eje sin cambiar nada más.
- **Decisión:** el encabezado guarda solo lo esencial: el camino de la página, la semana y la región leídas, las alertas, los dos botones («Semanas» e «Inflación») y la hora de la carga. Se quitan la pregunta cortada y los contadores, que ya dicen los paneles. La × de todas las ventanas queda por encima del contenido (con el título oculto, el contenido la tapaba). En el índice mensual ampliado, las etiquetas de año (2022 a 2026) van pequeñas y grises bajo el eje, alineadas con la cuadrícula; Streamlit limitaba la caja del gráfico al alto de la ventana y las cortaba en ventanas bajas, así que se levanta ese tope para el gráfico ampliado. La curva, el ancho, las líneas y los colores no cambian.
- **Pruebas:** `tests/test_dashboard.py` (un solo chip en el encabezado) y la suite completa; revisión en pantalla a 1440 × 700 y 1440 × 790.

## D-317 · Un botón para ampliar la tabla de productos del Panorama

- **Pedido del autor:** la tabla de productos del Panorama se ve chica.
- **Decisión:** junto a los filtros hay un botón con el ícono de ampliar. Abre una ventana con la misma tabla (los mismos productos, filtros y orden) al alto de la ventana y con letra algo mayor; se cierra con la ×. El Panorama sigue cabiendo en una pantalla.
- **Pruebas:** la suite completa; revisión en pantalla (abrir, leer, cerrar).

## D-318 · Limpieza del código: fuera las vistas heredadas y el código sin uso

- **Pedido del autor:** preparar el repositorio para publicarlo como proyecto de portafolio: eliminar el código muerto y las vistas heredadas, en una rama aparte, verificando cada función y con las pruebas en verde.
- **Decisión:** salen nueve vistas que solo se abrían por direcciones antiguas (Datos, Portada, Definición del proyecto, Esta semana, Brecha de precio, Canales y regiones, Alertas, Reglas de calidad y el viejo DevOps y seguridad). Sus direcciones y sus secciones antiguas siguen abriendo algo: el Panorama, Consultas SQL, el PRD, el Plan de pruebas o el Centro de operación (`RETIRED_VIEWS`). Se eliminan también las funciones y constantes que solo esas vistas usaban, y las que ya no usaba nadie (verificadas una por una con vulture y buscando cada nombre en todo el repositorio). Se quitan las pruebas de lo eliminado; las que cuidan los documentos y el menú se conservan. Quedan como puntos de entrada deliberados, aunque nadie los llame: `render_page` (lo usan las pruebas), `read_glossary` y `orthogonal`.
- **Pruebas:** la suite completa, sin las pruebas de las vistas retiradas.

## D-319 · El repositorio listo para publicarse: carpetas, historial sin bases pesadas y nombre «greenocean»

- **Pedido del autor:** dejar el repositorio listo como proyecto de portafolio.
- **Decisión:** `run_download.command` pasa a `scripts/`, el CSV de pruebas a `tests/fixtures/` y `docs/historia/` a `docs/archivo/`, con todas las rutas actualizadas. Se reescribe el historial de git para quitar solo `etl/datos.db` y `etl/datos.duckdb` (ya no se versionan desde D-270), con una copia espejo previa (`git clone --mirror`) fuera del repositorio; el historial queda sin esos archivos en las ramas y etiquetas que se publican. El repositorio se renombra a «greenocean»: cambian el remoto, las insignias del README y las dos constantes del panel que apuntan a él (`bi/control.py`, `bi/project.py`). El README gana capturas del panel, un diagrama del flujo y la lista de páginas.
- **Cuidado:** quien tenga una copia del repositorio anterior debe clonar de nuevo; el primer push exige `--force` por la reescritura. Las pruebas que consultan los enlaces públicos del repositorio (`test_t54_every_public_link_answers`) fallan hasta que el repositorio se llame «greenocean» en GitHub.
- **Pruebas:** la suite completa, salvo esas cinco pruebas de enlaces en línea hasta el cambio de nombre.

## D-320 · Método y calidad: la autoevaluación del proyecto, con mediciones reales

- **Pedido del autor:** aplicar un marco de calidad de software y de datos al proyecto (ISO/IEC 25010, 25012 e ISO 8000, 5055, 29119, 42010 y C4, ADR, OWASP Top 10, Twelve-Factor y DORA), medirlo con herramientas reales y publicarlo en una pestaña nueva, en una rama aparte, sin aplicar mejoras al código.
- **Decisión:** `scripts/medir_calidad.py` ejecuta Ruff, SQLFluff, mypy, radon, vulture, pytest con cobertura, Bandit, pip-audit y detect-secrets (instalados en un entorno aparte, no son dependencias del proyecto) y deja cada número con su comando en `docs/calidad/medicion.json`; lo que no se pudo medir queda «no verificado». La página «Método y calidad», dentro de «Stack y evidencia», en español y en inglés, tiene siete pestañas: introducción, estándares, ISO 25010 (ocho características con nota de 0 a 4 y su evidencia), calidad de los datos (indicadores en vivo y límites declarados), buenas prácticas de código (diez, con herramienta, umbral y resultado), cómo verificarlo y limitaciones con las mejoras por prioridad. `docs/calidad/INFORME.md` trae el detalle. Es una autoevaluación: ninguna palabra afirma certificación ni conformidad con una norma. Bajo el logo, una línea pequeña («Evaluado según ISO/IEC 25010 · 25012») abre la página sin mover el menú.
- **Resultado, sin adornos:** 1.819 avisos de Ruff y 109 de 115 archivos sin formatear; 40 funciones sobre 50 líneas y 9 sobre complejidad 10; el código no tiene anotaciones de tipos; 91,5 % de cobertura, pero la ingesta (bronce, INE y pipeline) está bajo el 70 %; Bandit sin hallazgos altos; sin secretos; los commits no siguen Conventional Commits y el CI no corre lint. Promedio ISO/IEC 25010 de las siete características verificadas: 2,6 de 4.
- **Pruebas:** `tests/test_quality_method.py` (los números de la página y del informe vienen de la medición, ninguna frase afirma certificación, la línea del menú abre la página en ambos idiomas).

## D-321 · Dónde comprar, según la maqueta del autor: tarjetas numeradas con su mapa

- **Pedido del autor:** una maqueta para la página de los lugares: título, leyenda de los tipos de lugar, tarjetas numeradas de norte a sur y un mapa en cada una.
- **Decisión:** la página abre con «Lugares de compra por región», su subtítulo y una leyenda de tres tipos: mercado o terminal mayorista (casa con cajas), feria o vega (casa con toldo y frutas) y comercio al detalle (casa con letrero y carrito). Cada región es una tarjeta con su número de norte a sur, su nombre, un borde superior de su color, una casa por lugar (el tipo se deduce del nombre: «vega», «feria» o «venta directa» son ferias) y, a la derecha, el mapa de Chile con la región marcada. El comercio al detalle nombra sus tipos al pasar el cursor; Santiago lleva sus sectores. Cabe en una pantalla a 1440 × 790 y 1920 × 1000.
- **Pruebas:** `tests/test_points_of_sale.py`.

## D-322 · Cuán cara es cada región, tablas con más lugar y la tabla ampliada con sus filtros

- **Pedido del autor:** la cabecera de la tabla de productos más mínima para dar lugar a las filas; la tabla ampliada con los mismos filtros que la chica; la tabla de semanas con aire abajo; en «Dónde comprar», casas que llenen la tarjeta y saber qué región es más cara, sabiendo que no se puede decir de un negocio.
- **Decisión:** la cabecera de productos va en una sola línea (etiqueta, familia, pregunta, mediana, alcance y cantidad) y la tabla gana su alto. La ventana ampliada abre con la búsqueda, el canal y el orden del panel y los cambia por su cuenta sin cerrarse; su × queda en la esquina. La tabla de semanas cierra con bordes redondeados y espacio bajo ella. Cada tarjeta de «Dónde comprar» dice cuán cara es la región frente al promedio nacional y su lugar de 9, con una etiqueta para la más cara y la más barata: es la mediana del índice K3 de la última semana (precio regional sobre el promedio de las regiones, mismo producto, variedad, calidad, canal y unidad), contando solo lo que dos regiones o más tienen precio. Es por región: ODEPA no publica precios por mercado. Las casas crecen con la tarjeta. Todo cabe en una pantalla a 1440 × 790 y 1920 × 1000.
- **Pruebas:** `tests/test_points_of_sale.py::test_d322_…` recalcula el nivel de cada región desde la consulta K3.

## D-323 · Mejora de la calidad medida con números, y autoevaluación continua con aprobación del autor

- **Pedido del autor:** mejorar la calidad del proyecto en una rama aparte, un commit por mejora y sin cambiar el comportamiento del producto ni la lógica de carga; medir antes y después sin inventar números; dejar una autoevaluación automática en cada push que el autor apruebe antes de publicarse.
- **Decisión:** se midió la línea base antes de cambiar nada (`docs/calidad/linea_base.json`, commit 6c6286c) y después se aplicaron, cada una con la suite completa: Ruff configurado en `pyproject.toml` con autofix y formato; tipos en los diez módulos principales y mypy sin errores; pruebas de la ingesta (bronce, INE y pasos de la carga); tres funciones complejas divididas, con salida idéntica comprobada; 0 violaciones WCAG 2.1 AA en las 13 páginas y los cuatro temas; presupuesto de 2 s por página y 1 s por consulta; pre-commit, CI con lint, mypy y cobertura mínima (90 %) en Python 3.11 y 3.12, y Conventional Commits (`CONTRIBUTING.md`). Las metas viven en `docs/calidad/metas.json` y `scripts/verificar_calidad.py` falla diciendo cuál no se cumple. El workflow `calidad.yml` mide en cada push y, en `main`, abre el pull request «Actualizar medición de calidad» con la comparación contra la medición anterior; `scripts/informe_calidad.py` escribe `docs/calidad/INFORME.md` y agrega la medición a `docs/calidad/historial.json`. La página «Método y calidad» lee esos archivos: dice «Autoevaluación automática, revisada y aprobada por el autor · última medición: fecha · commit», muestra antes → ahora → meta, la rúbrica ISO con la nota de D-320 al lado, el historial de mediciones y qué se mide solo y qué se revisa a mano, con su frecuencia. La rúbrica ISO (`docs/calidad/rubrica.json`) queda como borrador hasta que el autor la confirme. El README suma las insignias de los workflows y una de cobertura que lee la medición aprobada en `main` (shields.io, sin cuenta ni servicio de pago).
- **Cómo se cuenta:** Ruff cuenta las reglas E, F y W sin el largo de línea, antes y después: `pyproject.toml` deja E501 fuera porque las líneas largas son textos del panel en español e inglés que el formateador no parte, y su número se mide aparte para que no se oculte. Los candidatos de detect-secrets que el autor revisó se anotan en `.secrets.baseline` con `"is_secret": false`; ese archivo no se escanea a sí mismo. La cobertura de cada módulo de la línea base se midió de nuevo en el mismo commit 6c6286c, porque la primera medición solo guardó los módulos críticos.
- **Lo que no se pudo mejorar:** seis funciones de páginas siguen sobre la complejidad 10 (dividirlas exige pruebas de interfaz), 80 funciones pasan de 50 líneas, SQLFluff no se aplicó al SQL de dbt (es lógica del pipeline), las dependencias del pipeline no se auditan con Python 3.14 y falta el recorrido con teclado y lector de pantalla. Cinco pruebas de enlaces públicos fallan hasta que el repositorio se llame «greenocean» en GitHub (D-319).
- **Cuidado:** el horario semanal del workflow de calidad está comentado hasta que el autor lo active; la carga semanal (`semanal.yml`) no cambia. Para que el workflow abra el pull request, el autor debe activar «Allow GitHub Actions to create and approve pull requests» en la configuración del repositorio.
- **Pruebas:** `tests/test_quality_method.py` (indicadores, metas, verificador, rúbrica, historial, informe y página en ambos idiomas), `tests/test_rendimiento.py`, `tests/test_ingesta.py` y la suite completa.

## D-324 · Nada se sale de su caja: los campos de filtro muestran su borde y los desbordes de texto se corrigen en todas las páginas

- **Pedido del autor:** los campos de filtro de la tabla de productos no mostraban su borde en reposo, y «68 precios» sobresalía de la tarjeta; revisar todo el proyecto, porque un texto que se sale o flota es inaceptable.
- **Decisión:** `tests/medicion/desbordes.cjs` recorre cada página del menú, cada pestaña y la tabla ampliada, en cinco tamaños (1440 × 790, 1920 × 1000, 1280 × 720, 1024 × 768 y teléfono en horizontal), dos temas y los dos idiomas, y lista el texto que es más ancho que su caja, que queda recortado sin puntos suspensivos o que sale de su tarjeta o de la ventana. Con él se corrigió: los campos de filtro de la tabla chica y de la ampliada llevan un borde de 1 px (antes era blanco sobre blanco); la cabecera de la tabla de productos salta de línea y acorta la pregunta con «…»; a 1100 px o menos las dos columnas del Panorama se apilan a todo el ancho y el mapa conserva su alto; en «Dónde comprar» la etiqueta «La más barata» baja de línea en vez de quedar cortada y los nombres ya no se parten a media palabra; en «Documentos» la columna de propósito se oculta cuando no hay lugar para leerla; en el «Mapa de la app» los nombres de capa se achican y por debajo de 760 px de ancho del contenedor pasa a lista; en el diagrama CI/CD la fila de entrega continua se apila de verdad a ancho angosto (una regla más específica la dejaba aplastada) y las etiquetas «puerta» y «opcional» bajan de línea; en «Consultas SQL» el conteo de filas del explorador puede saltar de línea; en el diagrama de calidad las cajas de los extremos tienen un ancho mínimo; en el diagrama de despliegue cuatro textos en inglés son más cortos para caber en sus cajas.
- **Cuidado:** el detector mide el ancho real del texto, no el de sus hijos ocultos, y tiene en cuenta la escala del teléfono en horizontal. No ve un texto que cabe en su caja pero choca con el de al lado: eso se revisa a ojo.
- **Pruebas:** la suite completa y la auditoría de desbordes sin hallazgos.

## D-325 · Se elimina la página «Dónde comprar»

- **Pedido del autor:** quitar la página «Dónde comprar» del proyecto, sin romper nada, dejando el menú de «Negocio · BI» con «Panorama de precios» e «Insights».
- **Decisión:** se quitan la página y todo lo que solo ella usaba: su función y sus precios regionales en `bi/dashboard.py`, sus entradas del menú, de los íconos y de las direcciones, y en `bi/overview.py` las casas, los mapas pequeños, el nivel de precio de cada región, las tarjetas y su CSS; en los diccionarios de inglés, sus 23 textos propios; en las pruebas, las que dibujaban la página; en el README, su captura y su fila (las capturas del README se tomaron de nuevo, porque mostraban la página en el menú, y la tabla pasa a mostrar «Calidad y auditoría»); y en el SAD y en el texto del mapa de la app, su mención. La dirección antigua (`?vista=Dónde comprar`) abre el Panorama, como ya hacía la del Dashboard retirado (`RETIRED_VIEWS`).
- **Lo que se queda, porque otro lo usa:** `bi/assets/points_of_sale.json`, `etl/points_of_sale.py` y `overview.read_points`, `point_icon` y `POINT_ICONS`, que las tarjetas de Insights usan para sus íconos y para contar los mercados mayoristas. La fila «¿Dónde se compra por mayor?» de Insights sigue respondiendo con esos datos y ahora dice «Insights» en su columna «Dónde verlo», porque ya no hay otra página que la muestre. Las entradas anteriores de este registro (D-306, D-308, D-310, D-321 y D-322) cuentan la historia de la página y no se reescriben.
- **Cuidado:** las mediciones de calidad guardadas (`docs/calidad/medicion.json` y `linea_base.json`) listan 13 páginas con «Dónde comprar»; son registros de lo medido y no se editan: la próxima medición ya traerá 12.
- **Pruebas:** la suite completa; `tests/test_overview.py::test_d325_…` fija que la página no existe, que el menú tiene dos páginas, que la dirección antigua abre el Panorama en los dos idiomas y que lo que Insights lee sigue en pie.
