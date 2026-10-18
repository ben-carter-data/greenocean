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
