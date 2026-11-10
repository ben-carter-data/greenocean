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

- **Actualización (31-10-2026):** el riesgo aceptado de los intentos ilimitados se reemplazó por un límite común a todas las puertas de la clave (D-393).

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

## D-326 · El usuario de GitHub pasa a «ben-carter-data»

- **Pedido del autor:** el usuario de GitHub cambió de «cben6514-boop» a «ben-carter-data»; el proyecto debe reflejarlo.
- **Decisión:** el remoto de git y todo enlace al repositorio apuntan a `ben-carter-data/greenocean`: las constantes `REPOSITORY` (`bi/control.py`, de donde salen las consultas a GitHub y el disparo de la carga) y `GITHUB_URL` (`bi/project.py`, de donde salen los enlaces del panel y la descarga de la base del release «base-actual»), el repositorio que consulta `scripts/medir_calidad.py` para las métricas DORA, las cuatro insignias del README (pruebas, semanal, calidad y cobertura) y los enlaces de `docs/archivo/hito-4.md`. Los workflows no nombran el repositorio (usan el contexto de GitHub) y no cambian. La dirección pública de la app de Streamlit lleva el nombre antiguo del repositorio (`monitor-precios-hito1`) y no se toca: es la que el autor publicó.
- **Cuidado:** el repositorio, sus ramas, el release y el tag no cambian; solo el usuario que los aloja. La conexión de Streamlit Cloud con el repositorio y los secretos de la app se actualizan en sus propios paneles, fuera del código. La insignia de cobertura lee `docs/calidad/medicion.json` de `main`, que existirá cuando la rama de trabajo llegue a `main`.
- **Pruebas:** la suite completa, incluidas las de enlaces públicos.

## D-327 · La tabla de productos se explica sola: promedio de regiones, cálculo por fila y regiones sin precio

- **Pedido del autor:** la tabla «Detalle de productos» del Panorama no se explicaba. Mostraba $1.199 → $1.812 junto a +45,3 % (Zapallo Camote, Mayorista, 05-10 a 12-10), y dividir los precios daba +51 %: nadie podía saber que los precios eran un promedio de regiones ni que una región se había dejado fuera. Un cálculo correcto pero silencioso no sirve ante quien mira el panel por primera vez. Quien compra en Arica debe poder ver que Arica no publicó ese producto.
- **Decisión:** la tabla dice lo que mide. Los encabezados son «Precio medio 05-10» y «Precio medio 12-10», con su explicación al pasar el cursor. Una línea fija sobre la tabla dice que los precios son el promedio de las regiones con precio publicado en las dos semanas (la fuente publica 9 regiones), que una región sin precio de un producto en alguna de las dos semanas se deja fuera de ese producto sin rellenar nada, y cuántos precios de la semana no aparecen porque ninguna región los tiene en ambas. Los dos precios de cada fila son el promedio de las mismas regiones que usa la variación, así que dividirlos da la variación mostrada; para esta tabla, esto reemplaza a D-153 (el precio nacional de todas las regiones sigue en Precios e inflación y en el precio de una sola semana). Cada fila lleva el enlace «Ver cálculo · 7 de 9 regiones», que abre en su lugar, sin recargar, las regiones tomadas en cuenta con su precio de cada semana, el promedio y la variación, y luego las regiones fuera del promedio con su motivo: «sin precio publicado el 12-10», «el 05-10» o «en las dos semanas». Los motivos dicen solo lo que muestran los datos; la fuente no explica por qué falta un precio. Un producto sin ninguna región con precio en las dos semanas no se muestra. Los cambios apoyados en una sola región van al final del orden, como ya iban los de una sola cotización (D-146).
- **Comprobado en los datos:** entre el 05-10 y el 12-10 las 9 regiones publicaron precios; ninguna faltó para todos los productos. El hueco es por producto: cada región tiene entre un 9 % (Coquimbo) y un 25 % (Arica) de series con precio en una sola de las dos semanas. Por eso el aviso va en la fila y no en un cartel general.
- **Pruebas:** `tests/test_home_mockup.py::test_d327_…` (la fila cuadra, el enlace lista las regiones usadas y las excluidas con su motivo, la nota fija, el orden) y `tests/test_data_audit.py::test_d327_…` (el cálculo de cada fila se recompone desde la base: las regiones usadas son las que tienen precio en ambas semanas, su promedio es el precio mostrado y usadas más excluidas son las regiones publicadas).

## D-328 · Las acciones de Streamlit Cloud no se dibujan sobre la barra de la página

- **Pedido del autor:** en la app pública, «Share», la estrella y el lápiz de Streamlit Cloud se superponían a la fecha de la barra de encabezado, en la esquina superior derecha.
- **Decisión:** esas acciones (`stToolbarActions`) se ocultan con CSS, como ya se ocultaba el menú de Streamlit (la app es dueña de su interfaz). Solo las ve el dueño de la app con sesión iniciada; el visitante no las tenía. El dueño comparte la dirección de la app y administra desde el panel de Streamlit Cloud.
- **Cuidado:** no se puede comprobar en local, porque Streamlit Cloud es quien dibuja esas acciones. Se verifica en la app publicada.
- **Pruebas:** la suite completa.

## D-329 · El resumen también declara sus huecos: familias y mapa

- **Pedido del autor:** el gráfico de familias y el mapa calculan con los mismos precios comparables que la tabla de productos (D-327), pero no lo decían. Los huecos de la fuente deben declararse también en el resumen.
- **Decisión:** bajo el gráfico de familias, una línea leída del mismo modelo que la tabla: «Con 719 de 772 precios de la semana. En 247 quedó fuera una región sin precio». En el mapa, el cuadro de cada región suma «N productos sin precio publicado en una de las dos semanas: fuera del cálculo», que cuenta los productos que la región publicó solo la semana anterior y los que publicó solo esta. Sin enlace por familia: una familia agrupa cientos de productos y el detalle de cada uno ya está en la tabla. Las líneas fijas de la tabla y de las familias se acortaron para que la tabla conserve su alto, y los encabezados «Precio medio» van en dos líneas.
- **Pruebas:** `tests/test_home_mockup.py::test_d329_…`; la auditoría de desbordes del Panorama da 0 en cinco tamaños, dos temas y dos idiomas. El detector ignora lo que guarda un «Ver cálculo» cerrado, que el lector no ve.

## D-330 · Calidad en dos partes: los datos que publicamos y el código que los trata

- **Pedido del autor:** la sección de calidad debe demostrar, con lo mínimo, que la calidad se gestiona: la de los datos publicados y la del código. Lo demás sale. Cada indicador se lee como su falla frente a un aceptable (el piso), con una meta, un margen crítico y una explicación sencilla.
- **Decisión (aprobada el 2026-10-29):** `docs/calidad/metas.json` es la única fuente de los 12 indicadores: 8 de código (pruebas que fallan, cobertura total y del módulo más bajo, Ruff, mypy, hallazgos altos de Bandit, vulnerabilidades de pip-audit y posibles secretos) y 4 de datos (pruebas dbt superadas, precios con comparación válida, filas rechazadas y días desde la última carga). Cada uno guarda su aceptable, su meta (igual al aceptable donde el autor no fijó otra), su margen crítico, qué mide, por qué importa, cómo se mide, la acción sugerida y la frecuencia, en español e inglés. Aceptables: cobertura 90 % y 70 % por módulo, comparables 90 %, rechazadas 1 %, vigencia 8 días, pruebas dbt 100 % y 0 en pruebas fallidas, Ruff, mypy, hallazgos altos, vulnerabilidades y secretos. Márgenes críticos: cualquier caso para pruebas fallidas, dbt, Bandit, pip-audit (no informa severidad, así que toda vulnerabilidad es crítica) y secretos; 5 para Ruff, mypy y la cobertura total; 10 para la cobertura por módulo y los comparables; 4 puntos para las rechazadas; 7 días para la vigencia. Los estados son cumple, aviso (peor que la meta, dentro del aceptable), urgente y crítico. El insight de cada indicador se arma con las plantillas de `docs/calidad/politica.json` y las cifras de la medición, nunca con cifras escritas a mano. `scripts/verificar_calidad.py` falla el CI solo cuando un indicador de código pasa su aceptable; los de datos van en modo aviso hasta que el autor apruebe que bloqueen la publicación (después de la etapa 3, con plan previo).
- **Lo que salió de la medición:** tiempos por página y por consulta, accesibilidad, navegadores, complejidad, funciones con tipos y archivos sin formatear. No se borró ningún script ni prueba: el detector de desbordes y la prueba de rendimiento siguen, esta última con su tope de 1 s de D-323 escrito en la propia prueba. El workflow «calidad» ya no instala navegadores. mypy se mide ahora con las dependencias del proyecto, como en el CI, porque sin ellas no vio un error real (D-323).
- **Pruebas:** `tests/test_quality_method.py::test_d330_…` (los 12 indicadores con sus campos y los números aprobados, los estados, la falla frente al aceptable, el insight y la variación) y la suite completa.

## D-331 · Informes de calidad numerados e inmutables

- **Pedido del autor:** cada medición debe quedar como un registro que no se edita, numerado («Informe de calidad N° X»), con su fecha, su semana de datos y el código evaluado; generado después de cada carga semanal, incluso si falla, y propuesto al autor en un pull request.
- **Decisión:** `scripts/informe_calidad.py` convierte una medición en el informe siguiente, `docs/calidad/informes/informe-NNN.json`. Cada informe congela la medición completa y los aceptables con que se evaluó, y guarda por indicador el valor, la falla frente al aceptable, el estado, el insight y la variación frente al informe anterior. El archivo se abre en modo «x», que falla si ya existe: un informe nunca se sobrescribe, y repetir la misma medición no agrega nada; un error se corrige en el informe siguiente. `docs/calidad/INFORME.md` muestra el último. Los cuatro primeros informes son las cuatro mediciones reales del historial (cf561e7, 6c6286c, d66804c y b015e3a), recuperadas completas del historial de git; lo que entonces no se medía dice «sin medición», sin inventar valores. Se evaluaron con los aceptables aprobados el 2026-10-29 (D-330), y así lo dicen.
- **Workflow:** en `main`, el workflow «calidad» genera el informe y abre el pull request con la comparación contra el informe anterior; fusionarlo es la aprobación del autor. Compara primero con los aceptables y falla al final si un indicador de código los pasa, aunque igual propone el informe. Dos propuestas quedan escritas y comentadas, sin activar: correr después de cada carga semanal (`workflow_run` de «semanal», terminada con éxito o con falla), que reemplaza el cron del lunes, que caía antes de la carga del martes; y fusionar solo el pull request cuando todos los indicadores de código están dentro de lo aceptable (`gh pr merge --auto`, que necesita activar «Allow auto-merge»).
- **Pruebas:** `tests/test_quality_method.py::test_d331_…` (numeración continua, cada informe reconstruido desde su propia medición y sus aceptables da los mismos estados, los cuatro primeros son las mediciones del historial, INFORME.md es el último, un informe no se reescribe, la variación y el cuerpo del pull request).

## D-332 · «Método y calidad» en dos pestañas: Resumen e Informes

- **Pedido del autor:** quien no conoce el panel debe entender en un minuto que la calidad se gestiona. La página tenía siete pestañas y abría con una tabla técnica.
- **Decisión (aprobada el 2026-10-29):** dos pestañas. «Resumen» dice en dos frases qué se mide y cómo va («Medimos 12 indicadores… Hoy: 10 de 11 medidos dentro de lo aceptable · 1 no conformidad») y muestra los datos que publicamos y el código que los trata en dos cuadros: cada indicador con su falla en una barra, la marca de su aceptable, la cifra y el estado en color. Los cinco conteos que casi siempre están en cero (Ruff, mypy, Bandit, pip-audit, secretos) comparten una línea cuando todos cumplen. Solo los indicadores fuera de lo aceptable muestran su insight a la vista; los demás lo dicen al pasar el cursor, con qué mide y por qué importa. El botón «Abrir el último informe» abre el informe completo. «Informes» lista los informes numerados, del más reciente al más antiguo, sobre fondo negro profundo con acento azul cielo, y reemplaza a «Historial». Salen las pestañas ISO 25010, Datos, Navegadores, Estándares, Historial y Límites. La línea bajo el logo dejó de decir «Evaluado según ISO/IEC 25010 · 25012», que la página ya no muestra, y dice «Autoevaluación de calidad · Informe N° 4», que cambia sola con cada informe. Todo se lee de los informes, de `metas.json` y de `politica.json`.
- **Pruebas:** `tests/test_quality_method.py::test_d332_…` (el encabezado y la línea del logo nombran el último informe, el resumen lee el informe y no usa la palabra de una certificación externa, solo los indicadores fuera de lo aceptable muestran su insight, la tabla de informes va del más reciente al más antiguo, la página tiene dos pestañas en ambos idiomas). La auditoría de desbordes de la página da 0 en cinco tamaños, dos temas y dos idiomas.

## D-333 · Los informes se abren como diapositivas y se descargan en PDF

- **Pedido del autor:** una tabla de informes con filtros por año, mes y semana y un buscador, el número como enlace y un ícono de PDF; y un visor en diapositivas (flechas, teclado, pantalla completa) con «Descargar PDF» y «Comparar con…».
- **Decisión:** la pestaña «Informes» filtra por año, mes, semana de datos y una búsqueda por número («N° 2» busca el informe 2, no cualquier «2»), fecha o código; la variación de cada fila se calcula siempre contra su informe anterior real, aunque el filtro lo oculte. El número y el ícono «PDF ↓» abren el informe por la dirección (`?informe=N`), que se limpia al abrirlo. El visor (`bi/quality_viewer.py`) es un documento propio en un iframe, así que el teclado, la pantalla completa y la impresión funcionan sin tocar el DOM del panel, y «Descargar PDF» imprime solo el informe, con sus colores. Ocho diapositivas: portada; qué medimos y por qué (las dos calidades, su objetivo y sus aceptables); cómo se mide (qué mide, cómo, aceptable, meta y frecuencia de cada indicador); resultados (falla frente al aceptable e insight); comparación (por defecto con el informe anterior, con dos selectores para cualquier par y barras violeta y azul cielo, legibles sobre negro); qué falló y qué hacemos (la causa, la acción y el estado que el autor anota en `no_conformidades.json`, o la acción sugerida y «Causa pendiente de registrar por el autor»); incidentes externos (solo su conteo en el período; el detalle es del autor); y anexo técnico (Ruff por regla, los módulos menos cubiertos, las validaciones de datos y cómo reproducir las mediciones). Los textos fijos están en `politica.json`.
- **Pruebas:** `tests/test_quality_method.py::test_d333_…` (ocho diapositivas leídas del informe, la causa del autor, la comparación por defecto con el anterior, el conteo sin detalle de incidentes, el inglés; los filtros, la búsqueda por número y los enlaces). Probado en un navegador real: los enlaces abren el visor, las flechas recorren las ocho diapositivas y la comparación cambia de par sin errores. Desbordes de la página: 0.

## D-334 · No conformidades, plan de mitigación e incidentes externos en archivos simples

- **Pedido del autor:** un catálogo de fallas con cómo se detectan, su causa interna o externa, su severidad, la contención y la acción correctiva; un registro de no conformidades donde el autor escribe la acción y el estado; y un registro de incidentes externos con respuestas por defecto pendientes de su aprobación.
- **Decisión:** `docs/calidad/plan_mitigacion.json` lista nueve fallas (F-01 a F-09), cuatro de ellas con su caso real (D-299, D-164, D-227, D-327). `docs/calidad/no_conformidades.json` registra cada indicador fuera de su aceptable en los informes N° 1 a 4, con la causa solo donde está demostrada; la causa de las 18 pruebas que fallaban en el informe N° 1 no se conoce y queda vacía. La acción y el estado quedan vacíos para el autor; el visor muestra entonces la acción sugerida y «pendiente del autor». `docs/calidad/incidentes_externos.json` no tiene incidentes registrados: las cargas que fallaron el 25 y el 27 de octubre tuvieron una causa interna (D-299). Sus respuestas por defecto (fuente retrasada, formato ilegible, valores atípicos, región o producto sin datos) esperan la aprobación del autor; mostrarlas en la interfaz pública no se hizo y se propone aparte.
- **Pruebas:** `tests/test_quality_method.py::test_d334_…`.

## D-335 · Perfil de autor con alerta «Acción requerida» y diagnóstico automático

- **Pedido del autor:** un tercer perfil, «Autor», protegido por la clave de ejecución ya existente; solo el autor ve la alerta de lo que está bajo su aceptable. Visitante y profesional no cambian.
- **Decisión:** la pantalla «Elige tu vista» suma «Autor», que pide la misma clave (`CONTROL_CODE`, guardada en los secretos de Streamlit, nunca en el repositorio), la compara en tiempo constante como «Acceso del autor» y abre la marca de sesión que ya existía (`ADMIN_UNLOCKED`): no hay una segunda clave ni un segundo mecanismo. Con ella abierta, al entrar se muestra una sola vez por visita la ventana «Acción requerida» si el último informe tiene algún indicador urgente o crítico: los críticos primero, y por cada uno su nivel, la falla frente al aceptable, por qué importa, el diagnóstico automático (qué falló y dónde, desde qué informe, y si la causa es interna o puede ser de la fuente), la causa registrada, la acción sugerida, la fecha de la última medición y el enlace al informe; si la última carga falló, una línea lo dice. «Entendido» la cierra y reaparece en la visita siguiente mientras la condición dure. Si todo está dentro de lo aceptable, no aparece nada. El diagnóstico se arma con las plantillas de `politica.json` y las cifras de la medición, se guarda en cada informe nuevo y no contiene claves, rutas internas ni datos personales; los cuatro informes anteriores no se reescriben, su diagnóstico se calcula al mostrarlos. Los informes siguen siendo públicos y muestran las fallas de calidad de datos y de código; de los incidentes externos solo muestran su conteo.
- **Límite que el autor debe saber:** el panel publicado no puede escribir en el repositorio, así que no hay un campo en la ventana para anotar la acción y el estado; se anotan en `docs/calidad/no_conformidades.json` y la ventana lo indica. La alerta no calcula nada: lee el informe.
- **Pruebas:** `tests/test_quality_method.py::test_d335_…` (el diagnóstico y su origen sin secretos, el orden de crítico primero y el contenido de la alerta, que un informe nuevo guarda su diagnóstico y los antiguos no cambian, y que solo la sesión del autor registra la alerta). Probado en un navegador real con una clave local de prueba, que ya no existe: la clave incorrecta no abre nada, la correcta muestra la alerta una vez, «Entendido» la cierra y el profesional no la ve.

## D-336 · Las ventanas emergentes se ven bien en todos los tamaños

- **Pedido del autor:** en la ventana «Elige tu vista» las letras no quedaban bien, y debían revisarse las ventanas en general.
- **Decisión:** en «Elige tu vista» la línea «Data Eng · BA · BI · DevOps · Seguridad» se centraba sobre la columna de «Profesional» y, con tres píldoras desde D-335, se salía 17 px por la izquierda (25 px fuera de la pantalla en un teléfono); ahora empieza bajo su píldora. La píldora «Autor», un menú emergente, salía más baja (40 px) y de otro tono que las otras dos; las tres comparten ahora estilo y alto (52 px), con el nombre en una sola línea en español e inglés (antes «Professional» bajaba a dos) y, en pantallas de 480 px o menos, sin ícono para que el nombre quepa. En las ventanas del informe y de «Acción requerida», la × de cerrar flotaba arriba al centro, casi invisible sobre el negro del visor y 23 px fuera de su tarjeta; va en la esquina superior derecha, con fondo propio, y la barra del visor le deja sitio. El detector de desbordes no abría ninguna ventana emergente porque entraba con el perfil ya elegido: ahora abre y audita la de elegir vista, las semanas, las alertas y el informe (`DIALOGS=1`, o `DIALOGS=only`).
- **Pruebas:** la auditoría de las cuatro ventanas da 0 hallazgos en cinco tamaños, dos temas y dos idiomas; la suite completa.

## D-337 · Una línea de ayuda para leer las barras del Resumen

- **Pedido del autor:** una sola línea discreta bajo la frase de resumen que explique cómo leer las barras y la raya, con su versión en inglés, en `politica.json`; antes de escribirla, confirmar que describe de verdad el dibujo.
- **Verificación y ajuste:** la raya sí marca el máximo aceptable (se dibuja en la posición del aceptable de cada indicador, en el borde izquierdo cuando el aceptable es 0), y «mientras la barra no pase la raya, cumple» es verdad en los 12 indicadores porque en todos la meta es igual al aceptable. Lo que no era cierto era «el % de falla»: Ruff, mypy, Bandit, pip-audit y secretos se miden en casos, y la vigencia en días. La frase dice entonces «la falla actual (en %, en casos o en días)». El resto va como el autor lo escribió: «Cómo leerlo: cada barra es la falla actual (en %, en casos o en días) y la raya marca el máximo aceptable. Mientras la barra no pase la raya, cumple. «Aceptable 0» significa cero tolerancia.» y «How to read this: each bar is the current failure (in %, in cases or in days) and the tick marks the maximum we accept. While the bar stays short of the tick, it passes. “Acceptable 0” means zero tolerance.»
- **Cuidado:** si el autor fija alguna vez una meta más estricta que el aceptable, una barra entre la meta y la raya dirá «Aviso» y no «Cumple», y la frase habrá que revisarla; la prueba lo detecta.
- **Pruebas:** `tests/test_quality_method.py::test_d337_…` (la línea está bajo la frase de resumen y una sola vez, en ambos idiomas; y contrasta la frase con el dibujo: en cada estado, «cumple» equivale a que la barra no pase la raya, el aceptable 0 pone la raya en el borde, y las unidades son solo %, casos o días).

## D-338 · Regla de idiomas del repositorio y README en inglés como archivo aparte

- **Pedido del autor:** una regla de idiomas que se aplique siempre, y un README en inglés sin traducir todo lo demás.
- **Decisión:** en inglés, solo dos cosas: el «About» de GitHub (su descripción y sus temas) y `README.en.md`. En español: `README.md`, la documentación, los mensajes de commit y las decisiones. El código y sus comentarios quedan en inglés, como dice `CLAUDE.md` y como ya está todo el código. El panel ya es bilingüe (D-283) y no se toca. No se traduce lo que está en español y no se mezclan dos idiomas dentro de un mismo archivo. La única excepción es la línea de enlace entre las dos versiones: `README.md` abre con «English version: README.en.md» y `README.en.md` abre con «Versión en español: README.md». `README.en.md` es una versión corta (qué es, el panel público, las insignias, cómo funciona el pipeline, cómo ejecutarlo y un enlace a la documentación, aclarando que está en español); no repite las páginas del panel ni el método de calidad. Los documentos de `docs/en/` ya existían (D-283) y siguen como están.
- **Pruebas:** `tests/test_project.py::test_d338_…` (cada README abre con su enlace al otro, `README.en.md` no contiene letras propias del español salvo en esa primera línea, y los comentarios del código siguen en inglés: se ignora lo que citan entre « » de los textos del panel).

## D-339 · Página «GitHub Actions», solo lectura y solo para el Autor

- **Pedido del autor:** una página en el menú, visible solo para el Autor, con las últimas ejecuciones de las tres cargas (pruebas, carga semanal y calidad) y, cuando una falló, qué falló, sin tocar nada en GitHub.
- **Decisión:** la página «GitHub Actions» está en «DevOps y seguridad». Por cada flujo muestra sus últimas ocho ejecuciones (estado, fecha en hora de Chile, commit, cómo empezó, duración y «Abrir en GitHub»). De la última que falló muestra el job, el paso, las anotaciones de GitHub, los nombres de las pruebas que fallan (tomados de las líneas `FAILED` del log, sin tocar `pruebas.yml`) y las últimas 60 líneas del log.
- **Acceso:** el menú oculta la página si el Autor no entró, y la dirección directa muestra solo «Esta página es solo para el autor», antes de cualquier consulta a GitHub.
- **Token:** `GITHUB_READ_TOKEN` si existe; si no, `GITHUB_TOKEN`. Vive en los secretos de Streamlit, nunca en el repositorio ni en pantalla: se cubren el token y todo texto con forma de token, aunque un log lo imprima. Solo hay peticiones GET (`bi/github_actions.py` tiene una única llamada y ninguna de escritura); no hay botón para relanzar ni cancelar. Sin token se ven solo los estados, con un aviso de que los logs lo necesitan. Un token vencido o sin permiso «Actions: Read» se explica con la acción a seguir.
- **Caché:** dos minutos, con el token fuera de la clave, para no gastar el límite de consultas.
- **Límite:** los logs de GitHub se borran a los 90 días; entonces la página lo dice y sigue mostrando el resto.
- **Pruebas:** `tests/test_github_actions.py` (solo GET, orden de los tokens, redacción, errores 401, 403 y 404) y `tests/test_actions_page.py` (solo el Autor la ve, página cerrada sin consultas, tablas y detalle del fallo, token nunca en pantalla, caché, inglés).

## D-340 · La ventana «Elige tu vista» se abre siempre: la dirección ya no elige el perfil

- **Pedido del autor:** la ventana de entrada es obligatoria en toda situación, también si la visita ya usaba la aplicación o recarga la página; ninguna dirección puede saltársela.
- **Decisión:** `settle_profile` ya no toma el perfil de `?perfil=…&rol=…` en la primera entrada (D-295). El perfil solo se elige en la ventana, y el estado de autor solo con la clave. Una visita nueva o una recarga empieza sin perfil, muestra la ventana y borra de la dirección lo que traía. Ya elegido, la dirección muestra el perfil pero no lo cambia.
- **Consecuencia que el autor debe saber:** un enlace compartido con `?perfil=` ya no abre directo en un perfil. Un enlace dentro del contenido que recarga la página (no el menú de la izquierda, que no recarga) vuelve a pedir el perfil.
- **Pruebas:** `tests/test_actions_page.py::test_d339_a_fresh_visit_or_a_reload_…` (ocho direcciones abren la ventana y no guardan nada del perfil); las pruebas que entraban por la dirección ahora fijan el perfil en la sesión.

## D-341 · Las pruebas de rendimiento salen del CI y siguen en local

- **Causa:** `test_d323_each_named_query_answers_within_its_budget[k3_regional_index]` falló en el CI: 1,42 s contra el presupuesto de 1,0 s. En el equipo del autor la misma consulta tarda 0,44 s: DuckDB resuelve en 0,03 s y el resto es entregar a pandas las 801.263 filas que devuelve (el 98 % de la tabla). No hay un índice ni una reescritura simple y segura: acortarla significaría devolver menos filas o columnas, y eso cambia lo que reciben el panel y sus consumidores.
- **Decisión:** las pruebas de `tests/test_rendimiento.py` llevan el marcador `rendimiento`, registrado en `pyproject.toml`. `pruebas.yml` corre `pytest -m "not rendimiento"`. Los presupuestos (1,0 s, D-323) y las pruebas no cambian, y en local corren con `python -m pytest -m rendimiento`. Un `pytest` sin filtro en local sigue corriéndolas.
- **Por qué:** desde D-330 el tiempo por consulta salió de los indicadores de calidad (etapa 1), y los runners compartidos de GitHub no son un entorno estable para medir velocidad.
- **Pruebas:** el CI deja de medir velocidad; la cobertura mínima (90 %) se sigue revisando.
- **Ampliación (30-10):** la carga semanal también corría esas pruebas (`pytest -q` en `semanal.yml`) y fallaba en el paso «Run the tests against the new database»; ahora usa `-m "not rendimiento"`, igual que `pruebas.yml`. Es una causa probable de las cargas fallidas desde el 29-10; las del 25 y 27-10 corrieron antes de que existieran esas pruebas y fallaron por otra causa.

## D-342 · Registro de fallas con categoría «operación», estación del flujo git y ocurrencias

- **Pedido del autor:** un registro de las fallas que vive el proyecto (CI, git, despliegue), con cómo se detectan, su causa, la solución estándar y cada vez que ocurrieron, en el archivo que ya existe.
- **Decisión:** `docs/calidad/plan_mitigacion.json` suma la categoría «operación» (las otras son «datos» y «código»). Cada falla lleva su estación del flujo git (1 a 15) y la lista `ocurrencias`; cada ocurrencia, fecha, ocurrencia, diagnóstico, solución y comentario, más estación, estado (abierta o resuelta) y commit o decisión, que sirven para filtrar y enlazar. `causa` sigue siendo interna o externa; el texto de la causa va en `causa_raiz` y la solución estándar en `correctiva`. Se cargan las ocho fallas de operación vividas el 27, 28 y 29 de octubre (F-10 a F-17): la prueba de rendimiento lenta (D-341), calidad que no abre el pull request (abierta, sin diagnóstico), la carga del 27-10, la edición web cancelada, los logs sin acceso (D-339), el formato de ruff, el aviso de Node.js 20 (abierta) y el cambio de usuario (D-326, con Streamlit Cloud ya actualizándose desde main). Lo que no consta en el historial se anota como «desconocido».
- **Regla:** cada falla diagnosticada y resuelta se anota en el registro antes del push (CLAUDE.md).
- **Límite que el autor debe saber:** el repositorio es público. El diagnóstico se muestra solo al Autor en el panel (D-345), pero el archivo lo puede leer cualquiera; por eso los diagnósticos no llevan datos sensibles.
- **Pruebas:** `tests/test_quality_method.py::test_d334_…` (categorías, estaciones de 1 a 15, esquema de cada ocurrencia en español e inglés y las ocho de operación).

## D-343 · Sección «Calidad» en el menú; se quita la línea de autoevaluación bajo el logo

- **Pedido del autor:** sacar del encabezado del menú el texto «Autoevaluación de calidad · Informe N° X» (su contenido ya está en la sección) y reunir lo de calidad en una sección propia.
- **Decisión:** el menú suma la sección «Calidad» («Quality») con «Calidad y auditoría» (antes en Ingeniería de datos) y «Método y calidad» (antes en Stack y evidencia); la página «Git workflow» se suma en D-344. «GitHub Actions» se queda en DevOps y seguridad, solo para el Autor. Los nombres de las páginas y sus direcciones no cambian, así que los enlaces internos siguen sirviendo. La sección sigue la regla de los demás bloques: el perfil de usuario no la ve, el profesional y el autor sí, al final de cada orden. Se retiran `show_assessment_line` y `quality_method.sidebar_line`.
- **Pruebas:** `tests/test_dashboard.py` (el menú y el orden de cada perfil con la sección nueva), `tests/test_app_map.py` (el bloque Stack) y `tests/test_quality_method.py::test_d332_…` (la línea ya no existe y las dos páginas quedan juntas).

## D-344 · Página «Git workflow»: el mapa de 15 estaciones y el registro de incidentes

- **Pedido del autor:** una página «Git workflow» (mismo nombre en español e inglés) en la sección Calidad, para el profesional y el autor, con dos pestañas: el mapa del ciclo y el registro de incidentes.
- **Decisión:** `bi/git_workflow.py` dibuja el mapa que fija `docs/referencia/ciclo_git.html`: 15 estaciones en tres carriles en zigzag (Preparar, Guardar y verificar, Publicar), íconos genéricos sin marcas, número, título, quién actúa y comando; las opcionales (4, 7, 10) con borde punteado, los puntos de control (8, 12, 14) como rombos amarillos y «Desplegado» en verde. Un clic abre un panel lateral con qué hace y por qué, los comandos con botón de copiar, qué hacer si falla, el ejemplo real de GreenOcean y las ocurrencias del registro de fallas (D-342) en esa estación; Anterior y Siguiente, las flechas del teclado y Escape recorren y cierran el panel. Se dibuja en un `st.iframe` con su propio HTML, como la página GitHub. La pestaña «Registro de incidentes» es la tabla del registro, de la más reciente a la más antigua.
- **Diferencias con la referencia:** el panel y el fondo se limitan al marco, que tiene altura fija; las flechas y Escape funcionan con el foco dentro del marco (tras el primer clic); la tipografía es la del sistema (no se pide nada a Google Fonts); el color sale del tema del panel; el comando de tipos es `mypy` (sin punto), que es el que corre el CI. Los ejemplos se contrastaron con el historial: se corrigió el avance de la estación 12 (`91f9bb5..0020096`; `0da1236` salió solo de la simulación) y el de la 14 (calidad sigue sin abrir el pull request); el `eb6bce6` → `843decd`, los 16 commits y 37 archivos, y las ramas `usuario-nuevo` y `calidad-simple` coinciden con el reflog; «etapa 0», la clave de prueba en 0 commits y la espera de «continúa» no se pueden comprobar en el historial.
- **Pruebas:** `tests/test_git_workflow.py` (las 15 estaciones contra el archivo de referencia, opcionales, puntos de control y final; el comportamiento del panel; ambas lenguas; la sección y el perfil).

## D-345 · Quién ve qué en el registro de fallas

- **Decisión (opción A del autor):** el profesional ve fecha, ocurrencia, solución y comentario; el diagnóstico y los logs solo el autor. Es ocultamiento de pantalla, no secreto: `docs/calidad/plan_mitigacion.json` está en un repositorio público, por eso los diagnósticos no llevan datos sensibles.
- **Pruebas:** `tests/test_git_workflow.py::test_d345_…` (el diagnóstico no aparece en el HTML ni en la tabla del profesional y sí en los del autor, en español e inglés).

## D-346 · «Últimas fallas» en el Resumen de «Método y calidad»

- **Pedido del autor:** un bloque compacto con las tres fallas más recientes y un enlace «Ver registro completo» al registro de incidentes, sin pestañas nuevas.
- **Decisión:** el Resumen cierra con «Últimas fallas»: fecha, identificador, qué ocurrió y su solución, de la más reciente a la más antigua. El diagnóstico no va aquí (D-345). El enlace es un enlace de la propia app (no recarga la página, así que no vuelve a pedir el perfil) a «Git workflow», que se abre en la pestaña «Registro de incidentes» con `?pestana=registro`. La página sigue con sus dos pestañas.
- **Pruebas:** `tests/test_quality_method.py::test_d346_…` (tres filas, la más reciente primero, solución y no diagnóstico, dos pestañas, el enlace en ambos idiomas).

## D-347 · El visor de informes es una presentación

- **Pedido del autor:** que el visor de informes se vea como una presentación: diapositiva grande 16:9 al centro, miniaturas a la izquierda con la actual resaltada, flechas del teclado, contador «3 / 8», pantalla completa y fundido; en el teléfono, las miniaturas abajo en una tira; se mantienen «Descargar PDF» y «Comparar con…».
- **Decisión:** las ocho diapositivas viven en un lienzo fijo de 960 × 540 que se escala para caber en el escenario, centrado; las miniaturas son copias reducidas de cada diapositiva (sin identificadores ni interacción). El cambio de diapositiva es un fundido de opacidad de 0,35 s (sin movimiento si el lector pidió menos movimiento). Hasta 760 px de ancho las miniaturas pasan a una tira bajo la diapositiva. «Descargar PDF» sigue imprimiendo las ocho diapositivas, una por página; la ventana del visor mide 700 px de alto.
- **Límite:** una diapositiva con más contenido que el lienzo (el anexo) se desplaza dentro de él. No se ha podido abrir en un navegador real desde esta sesión (Playwright no está instalado aquí): la estructura y la sintaxis del script están probadas, y la apariencia queda por revisar en local.
- **Pruebas:** `tests/test_quality_method.py::test_d347_…`.

## D-348 · Vistas compactas: pocas filas a la vez, cerradas, de una en una

- **Pedido del autor:** que las tablas que crecen (informes, registro de incidentes y GitHub Actions) no se alarguen: como máximo 20 filas por página, filas colapsadas con una sola abierta, logs en una caja de altura fija y cerrada, y en GitHub Actions una línea por workflow con el historial y el log solo al abrir.
- **Decisión:** `bi/compact_table.py` dibuja una lista: cada fila es un botón con su línea de resumen y, si es la abierta, su detalle debajo; abrir otra cierra la anterior. Páginas de 20 con «Anterior» y «Siguiente» y «Página 1 de 3 · 45 filas»; cambiar un filtro vuelve a la primera página con todo cerrado. «Informes» pierde su tabla de ocho columnas: la línea dice número, fecha y cuántos indicadores están dentro de lo aceptable, y el detalle trae semana de datos, código, no conformidades, variación y el botón que abre el informe o su PDF (ya no es un enlace que recargue la página). El registro de incidentes (con filtro de estado) usa la misma lista: el profesional abre una fila y ve solución y comentario; el autor, además, el diagnóstico. «GitHub Actions» muestra una línea por workflow con su última ejecución; al abrirla, las ocho ejecuciones y, si falló, el job, el paso, las pruebas y el log en un cuadro de 300 px con su propio scroll, dentro de un desplegable cerrado.
- **Tablas con `st.dataframe`:** quedan como estaban; no se tocaron en esta decisión.
- **Pruebas:** `tests/test_compact_tables.py` (nunca más de 20 filas, páginas, una abierta a la vez, diagnóstico solo del autor, log cerrado y de altura fija) y las de `test_actions_page.py` y `test_quality_method.py`, adaptadas.
- **Hallazgo aparte:** el panel mostraba en español, con la vista en inglés, la frase de Monitoreo cuando dos indicadores están por revisar («Días desde la última semana» y «Última carga», como pasa con la carga del martes 27-10 fallida). Se agregó su inglés a `bi/i18n_en.py`.

## D-349 · El tema oscuro es el predeterminado

- **Pedido del autor:** que el tema oscuro sea el de entrada en toda la app, también en la ventana «Elige tu vista», hasta que la persona elija otro en «Apariencia»; los enlaces con `?tema=` siguen mandando.
- **Decisión:** `DEFAULT_THEME` pasa de «Corporativo» a «Vantablack» y `.streamlit/config.toml` arranca en la base oscura de Streamlit, para que la primera pintura no sea clara. Una elección en «Apariencia» o un `?tema=` en la dirección sigue ganando.
- **Límite:** no se vio en un navegador real (Playwright no está en esta sesión); la prueba cubre el tema de la sesión, la dirección y la base de la configuración.
- **Pruebas:** `tests/test_dashboard.py::test_d349_…` y los dos `test_d071_…` ajustados.

## D-350 · La clave del Autor se envía con Enter

- **Pedido del autor:** al escribir la clave en «Autor», Enter no la enviaba; debía enviarla, sin botón «Entrar», y en el teléfono la tecla «Ir» del teclado también.
- **Decisión:** el campo comprueba la clave en su `on_change`, que se dispara con Enter (y con «Ir»). Clave correcta: entra como profesional con el rol por defecto. Clave incorrecta: el campo se vacía y el error «Clave incorrecta.» aparece en el mismo menú, sin recargar la página y con la ventana de entrada abierta. Se retira el botón «Entrar». No se usó `st.form`, que obliga a un botón de envío visible. El mensaje de error no tenía su inglés: ahora dice «Incorrect key.».
- **Pruebas:** `tests/test_control.py::test_d350_…` (Enter con clave correcta entra; con clave incorrecta muestra el error y no entra; no hay botón «Entrar»; el inglés del mensaje).

## D-351 · «Ejecutar pipeline ahora»: ventana que no se cierra sola, con seguimiento, minimizar y cancelar

- **Pedido del autor:** que un clic afuera no pierda el progreso, poder detener una ejecución pegada y ver un log chico; con un indicador en el encabezado al minimizar.
- **Decisión:** la ventana es `dismissible=False` (ni X ni clic afuera) y tiene dos acciones: «Minimizar» y «Cancelar». «Minimizar» la cierra y deja arriba del menú, solo para el Autor, «Ejecución en curso · <paso>»; un clic lo reabre. La ejecución sigue en GitHub. «Cancelar» pide dentro de la ventana «¿Seguro que quieres cancelar? Esto detiene la ejecución en GitHub.»; al confirmar llama a `POST /actions/runs/{id}/cancel` con el mismo token que lanza el pipeline y muestra «Cancelada». Si GitHub rechaza (permiso, ejecución ya terminada), muestra el motivo y deja la ejecución como estaba. Al terminar (bien, con falla o cancelada), «Cancelar» pasa a «Cerrar» y el indicador muestra el resultado hasta cerrar. Abrir la ventana con una ejecución en seguimiento muestra esa, no lanza otra.
- **Log:** una caja de 260 px con scroll. Durante la ejecución, una línea por paso con hora, estado y duración, actualizada cada 4 s (GitHub no entrega el log de un job que corre); al terminar cada job, sus últimas 60 líneas reales, sin tokens. «Copiar» copia ese texto (ya sin tokens) con el portapapeles del navegador o, si el marco lo prohíbe, lo deja seleccionado.
- **Límite de tiempo:** `timeout-minutes: 20` en `semanal.yml` (no se midió una carga buena: la API sin clave estaba agotada; ajustar con la página «GitHub Actions» si una carga normal se acerca). Pasados 20 minutos la ventana deja de consultar y dice «Sigue en GitHub» con el enlace.
- **Escritura nueva:** cancelar es la primera petición de escritura desde D-339. Vive en `bi/control.py`; `bi/github_actions.py` sigue sin ninguna (lo prueba un test).
- **Límite:** no se vio en un navegador real (Playwright no está en esta sesión). En AppTest el fragmento se redibuja en un segundo turno; en el navegador, solo.
- **Pruebas:** `tests/test_run_monitor.py` y `tests/test_dashboard.py::test_d351_…` y `test_d149_…`.

## D-352 · Panorama de precios: orden de lectura en tres pasos

- **Pedido del autor:** que quien llega no sepa por dónde empezar; sin cambiar la disposición ni el mapa de Chile.
- **Decisión:** los paneles se numeran: «1 · Elige una región» (mapa), «2 · Elige una familia» y «3 · Mira los productos». El mapa suma el botón grande «Todo Chile»; un clic en una región o en él completa el paso 1, y un clic en una familia el paso 2. En la vista Usuario los paneles 2 y 3 empiezan atenuados, con un candado y su frase («Elige primero una región» / «Elige primero una familia»), sin interacción (los campos de la tabla, desactivados), y no se preselecciona región ni familia. Un paso desbloqueado no se vuelve a bloquear: al cambiar de región o de familia, la familia y la tabla se actualizan y siguen abiertas. Un enlace que nombra una región o una familia cuenta como haberla elegido. En Profesional y Autor los pasos se numeran y todo está abierto. El panel que se acaba de abrir se resalta 1,6 s. La búsqueda de la tabla (lupa y borde) usa el color de acento de cada tema.
- **Tendencias y «Toda la canasta»:** cada familia suma una mini línea con la mediana del cambio semanal de las últimas 8 semanas, y arriba del panel 2 hay una fila destacada «Toda la canasta» con la mediana de todos los precios comparables, sin distinguir familia, para la región elegida (o todo Chile), con su línea. La fila no se elige ni desbloquea el paso 3. Las cifras salen de los datos: la mediana de la fila es la de las filas de la semana y región elegidas; las líneas, de las variaciones semanales nacionales (`read_home_trends`).
- **Límite:** las mini líneas son nacionales aunque se elija una región (la mediana de la fila sí es de la región). Sin archivo de referencia: se hizo con la descripción del autor. No se vio en un navegador real; la revisión visual es la parte 4.
- **Pruebas:** `tests/test_panorama_steps.py` (paneles 2 y 3 bloqueados en Usuario, «Todo Chile» desbloquea el 2, una familia el 3, sin bloqueo en Profesional y Autor, la búsqueda en acento en los cuatro temas, la fila de la canasta y las tendencias recalculadas desde las variaciones).

## D-353 · Cambiar de vista desde el menú

- **Pedido del autor:** después de elegir un perfil no había forma de volver a «Elige tu vista» sin editar el enlace.
- **Decisión:** abajo en el menú, encima de «Apariencia» y los idiomas, un indicador «Vista: Usuario ▾» (o «Profesional», o «Autor» si la clave está abierta). Un clic reabre «Elige tu vista», que esta vez ofrece «Mantener esta vista»; al elegir otro perfil el enlace se actualiza solo (`?perfil=` y `?rol=`). Elegir Usuario o Profesional con la clave del Autor abierta cierra esa sesión: desaparecen «GitHub Actions», la alerta de calidad y el indicador de la ejecución, y volver a Autor pide la clave otra vez (la comprobación sigue siendo la de D-350). La dirección sigue sin poder elegir el perfil (D-340).
- **Pruebas:** `tests/test_view_switch.py` (el indicador muestra el perfil en español e inglés, reabre la ventana, actualiza el enlace y salir de Autor exige la clave de nuevo).

## D-354 · El registro de fallas se escribe corto y en lenguaje simple

- **Pedido del autor:** que cada ocurrencia del registro se lea de un vistazo; el análisis largo, en su decisión.
- **Decisión:** cada campo de una ocurrencia es una línea en lenguaje simple: la ocurrencia dice qué pasó; el diagnóstico, la causa en una frase; la solución, qué se hizo en una frase; el comentario, lo que hay que recordar. La regla queda en CLAUDE.md (cómo escribirlo), en `docs/calidad/politica.json` (español e inglés) y en `docs/calidad/README.md` (cómo está hecho). F-10 pasa a una sola ocurrencia con el texto del autor (la carga semanal y el CI fallaban por la prueba de velocidad); F-11 a F-17 se acortaron con la misma regla. F-10 sigue abierta hasta que una carga real publique.
- **Pruebas:** `tests/test_quality_method.py::test_d334_…` (esquema del registro) y `test_d354_…` (cada campo en una sola línea y la regla en la política, en los dos idiomas).

## D-355 · Plan de calidad del software (SQAP)

- **Pedido del autor:** un plan de calidad al nivel del PRD y el SAD, con la estructura de IEEE 730 adaptada al proyecto, en lenguaje simple y sin cifras escritas a mano.
- **Decisión:** `docs/PLAN_DE_CALIDAD.md` (y `docs/en/PLAN_DE_CALIDAD.md`), «Plan de calidad del software (SQAP)», con doce secciones: por qué existe, visión y misión, qué medimos (ISO/IEC 25012 y 25010), cómo, qué no medimos (tiempo de respuesta, navegadores y accesibilidad, con D-330 y D-341), cómo se lee un indicador, pruebas que bloquean e informan (F-10 como ejemplo), informes, registro de fallas, incidentes de las fuentes (solo ODEPA e INE; lo de GitHub, el CI o el despliegue es categoría operación del registro), quién decide y que es una autoevaluación. Tres diagramas nuevos leen `metas.json` y `politica.json`: las dos calidades con su número de indicadores, la escala de estados y el ciclo semanal. El plan entra a la carpeta «Documentos» en la familia «calidad»; `docs/calidad/README.md` enlaza al plan; el glosario suma SQAP, IEEE e IEC.
- **Pruebas:** las de los documentos (`tests/test_documents.py`, `tests/test_doc_diagrams.py`, `tests/test_i18n.py`) cubren al plan como a los demás: portada, índice, diagramas, glosario, historial y su versión en inglés con la misma estructura.

## D-356 · Regla de las fuentes retrasadas

- **Causa:** la carga #17 (30-10) falló en la prueba dbt `d042_no_unexpected_missing_week`: el consumidor ya había publicado la semana del 19-10 y el mayorista no, así que el calendario llegaba a esa semana y al mayorista le faltaba (registro F-06).
- **Regla:** se publica hasta la última semana completa en ambas fuentes, sin rellenar nada. Una semana reciente que una fuente aún no publica no bloquea la carga: se registra como incidente externo y la app muestra un aviso discreto («ODEPA aún no publica la semana X»). Bloquea solo si falta una semana en medio de los datos, o si la fuente lleva más de 2 semanas sin publicar, y entonces hay aviso urgente al Autor. Queda en CLAUDE.md, en el SQAP (§10) y en `docs/calidad/politica.json`, en español e inglés.
- **Aplicación (aprobada el 30-10):** dbt corta `int_prices__outlier_flagged` en la última semana completa en ambas fuentes, así que el calendario, las dimensiones y `weekly_price` llegan solo hasta ahí; d042 no cambia su regla y sigue deteniendo un hueco en medio. El ETL de respaldo en SQLite hace el mismo corte, para que la paridad no cambie. Después de dbt, `etl/pipeline.py` lee la última semana de cada fuente: si alguna va más de 2 semanas detrás de la última semana completa de la fecha de la carga, la carga se rechaza con `LATE_SOURCE` y el panel muestra el aviso de carga fallida al Autor (D-298); si una fuente solo va detrás de la otra, la carga se publica y deja en su línea de `etl_run` la semana que espera (`SOURCE_LATE`), que el Panorama muestra como «ODEPA aún no publica la semana del X (mayorista)».
- **Límite:** el incidente externo no se escribe solo en `incidentes_externos.json`: la carga corre en GitHub y no escribe ese archivo. Lo anota la herramienta del autor al revisar, o el pull request del CI cuando F-11 esté resuelta. El aviso de carga fallida no distingue todavía el motivo: el detalle está en el log, en la página «GitHub Actions».
- **Pruebas:** `tests/test_late_sources.py` (retraso reciente que espera, hueco en medio que detiene, fuente con más de 2 semanas que detiene con motivo, el pipeline que rechaza o publica con su aviso, el corte en dbt y el texto del Panorama).

## D-357 · Las recargas que hace la app no vuelven a pedir el perfil

- **Causa:** desde D-340 toda sesión nueva pide el perfil, y la app recarga la página por su cuenta al abrir o imprimir un documento desde «Documentos» y al cambiar entre un tema claro y uno oscuro (D-070, D-280). El PDF salía con «Elige tu vista» encima, y al elegir un perfil se perdía el documento.
- **Decisión (opción 1, aprobada el 30-10):** justo antes de cada una de esas recargas, la pestaña del navegador guarda la vista (Usuario o Profesional y su rol), nunca el Autor. Al volver, la app la usa una sola vez, la borra y deja al lector en la página que pedía. Una recarga que hace el lector no encuentra nada guardado, así que la ventana vuelve a salir (D-340 sigue igual para él). El Autor que imprime vuelve como Profesional y, para volver a Autor, escribe su clave.
- **Verificación:** en un navegador, «PDF» y el cambio de tema ya no muestran la ventana y una recarga manual sí la muestra.
- **Pruebas:** `tests/test_app_reloads.py` (la vista guardada se usa y no se pierde el documento; sin vista guardada, o con una que no es pública, vuelve la ventana; cada recarga de la app guarda la vista antes).

## D-358 · El PDF de un documento numera sus hojas y su portada va sola

- **Pedido del autor:** el PDF de los documentos debe verse formal, con el ajuste mínimo y sin un script nuevo; sigue siendo la página impresa por el navegador (D-248).
- **Decisión:** la hoja de impresión agrega «Página X de Y» al pie de cada hoja (en el idioma del lector) y un salto de página después de la portada, que queda sola en la primera hoja con título, versión, fecha, estado, responsable, audiencia y documentos relacionados.
- **Verificación:** el SQAP impreso desde «Documentos → PDF» sale en 5 hojas, sin la ventana de entrada (D-357), con la portada sola y «Página 1 de 5» al pie.
- **Pruebas:** `tests/test_documents.py::test_d358_…`.

## D-359 · El log de un fallo se copia y lleva a GitHub

- **Pedido del autor:** en «GitHub Actions», el log de una ejecución fallida con un botón «Copiar» y un enlace directo a esa ejecución en GitHub; sin diagnóstico automático.
- **Decisión:** el último fallo de cada workflow muestra «Abrir la ejecución en GitHub»; bajo las últimas 60 líneas del log de cada job hay un botón «Copiar» (el mismo de la ventana de ejecución, D-351, con el texto ya sin tokens) y «Abrir el job en GitHub», que abre el job fallido con sus pasos.
- **Pruebas:** `tests/test_actions_page.py::test_d359_…`.

## D-360 · Las páginas con pestañas dibujan solo la pestaña a la vista

- **Pedido del autor:** el panel se siente lento al cambiar de página; aprobado dibujar solo la pestaña visible en las páginas lentas, con el mismo aspecto de pestañas.
- **Medición (30-10, en local):** cambiar de pestaña tarda 0,2 s y cambiar de página entre 0,2 y 1,5 s; las más lentas son Centro de operación (1,5 s), Insights, Calidad y auditoría y Pipeline y linaje (alrededor de 1 s). `st.tabs` dibuja todas las pestañas en cada vuelta: en Centro de operación, cuatro diagramas a la vez.
- **Decisión:** Centro de operación y Calidad y auditoría cambian `st.tabs` por un selector con aspecto de pestañas (`show_view_tabs`) que dibuja solo la elegida. Insights y Pipeline y linaje no tienen pestañas: su tiempo viene de otra parte y queda por medir. Las lecturas a GitHub de Centro de operación ya se guardan 5 minutos (las ejecuciones y sus pasos) y una hora (el vencimiento del token): no cambian. Ninguna prueba bloquea por tiempo.
- **Pruebas:** las de cada página eligen la pestaña que leen; la auditoría del inglés revisa cada pestaña como una pantalla.

## D-361 · Una alerta de un informe antiguo dice que es antigua

- **Causa:** la alerta «Acción requerida» leyó el informe N° 4 (27-10), con 5 pruebas fallando, como si fuera el estado de hoy; no había informe nuevo porque el workflow de calidad falla (F-11).
- **Decisión:** si el último informe tiene más de 8 días, la alerta empieza con «Última medición del 27-10: puede no reflejar el estado actual.» y sus indicadores no llevan el color de crítico o urgente, sino uno gris de medición antigua. El texto vive en `docs/calidad/politica.json` (`alerta.antigua`), en español e inglés.
- **Pruebas:** `tests/test_quality_method.py::test_d361_…` (a los 3 días es el estado de hoy; a los 9, una medición antigua sin color de crítico).

## D-362 · La rama del informe de calidad tiene su propio prefijo

- **Causa de F-11:** el paso «Proponer el informe al autor» fallaba con «[remote rejected] calidad/informe-acf6839 (directory file conflict)». En el repositorio existe la rama remota «calidad» (último commit `6c6286c`, del 26-10, ya fusionada en main), y git no permite una rama «calidad/...» mientras exista una llamada «calidad».
- **Decisión:** `calidad.yml` crea la rama del informe como «informe-calidad/<commit>». No se borra nada; borrar la rama «calidad», ya fusionada y sin uso, queda propuesto y espera la aprobación del autor.
- **Verificación pendiente:** F-11 queda abierta hasta que el workflow abra su primer pull request después del push.

## D-363 · El informe de calidad es semanal: un push solo mide

- **Causa:** `calidad.yml` proponía un informe en cada push a main; el 30-10 se abrieron propuestas de los informes N° 5, 6 y 7. D-331 dice que el informe es semanal.
- **Decisión:** en un push, el workflow mide los 12 indicadores y falla si un indicador de código pasa su aceptable, sin proponer informe. Propone el informe numerado solo cuando termina la carga semanal (`workflow_run` de «semanal», también si la carga falló) o cuando se lanza a mano (`workflow_dispatch`). Se activa así el disparador que D-331 dejó propuesto.
- **Limpieza:** las dos propuestas del informe N° 7 (ramas `informe-calidad/400bee8` y `informe-calidad/6cbe4ee`) se cerraron sin fusionar al borrar sus ramas.
- **Pruebas:** `tests/test_quality_method.py::test_d363_…` (los disparadores y la condición del paso que propone el informe).

## D-364 · Cuatro casos de seguridad nuevos: S-11 a S-14

- **Pedido del autor:** que el plan de pruebas y seguridad cuente los ataques que trajeron las vistas del Autor, la página «GitHub Actions» y la ventana de la carga.
- **Decisión:** `bi/security_plan.py` suma S-11 (la clave del Autor con Enter), S-12 (abrir la parte del autor con una dirección o una recarga), S-13 (un log que imprime el token) y S-14 (una escritura en GitHub fuera de lanzar y cancelar), cada uno con su prueba existente. El esquema pasa a dos arcos de siete casos, encima y debajo del candado, para que cada nombre tenga su lugar. El plan de pruebas (español e inglés) los lleva en su tabla y explica qué pruebas bloquean y cuáles solo informan.
- **Pruebas:** las del plan (`tests/test_documents.py`, `tests/test_doc_diagrams.py`) leen los catorce casos del código.

## D-365 · Página «Último dato por canal»

- **Pedido del autor:** una página en Negocio · BI, junto al Panorama, para todos los perfiles, con dos bloques, Mayorista y Consumidor, cada uno con su última semana publicada: la variación por familia frente a su semana anterior y la tabla de productos con su búsqueda; si un canal no publicó la semana más reciente, su bloque lo dice y muestra su último dato. El Panorama no cambia; su encabezado enlaza a la página.
- **Precisión de D-356 (opción A):** el Panorama y los indicadores publican hasta la semana completa en ambas fuentes; esta página muestra la última semana de cada fuente, rotulada. La regla queda así en CLAUDE.md, en el SQAP (§10) y en `politica.json`.
- **Decisión:** dbt construye `latest_by_source`, con las dos últimas semanas de cada fuente tomadas de `int_prices__weekly`, sin el corte, y con la misma marca de atípicos (RN-12); el pipeline la sirve y el diccionario de datos del SAD la describe. `bi/channel_latest.py` arma cada bloque como la tabla del Panorama: el precio de cada producto y canal es el promedio de las regiones con precio en las dos semanas, y la variación compara esas regiones. Las barras por familia y la tabla son las del Panorama (`home_mockup`). Mientras la base servida no traiga la tabla, la página dice que se llena con la próxima carga.
- **Pruebas:** `tests/test_channel_latest.py` (la semana propia de cada fuente y el aviso, la variación recalculada en SQL, la página para cada perfil con sus dos bloques y el enlace del Panorama, la tabla servida y documentada).

## D-366 · La carga semanal solo corre las pruebas de datos y del pipeline

- **Causa:** la carga del 30-10 no publicó porque fallaron dos pruebas de pantalla en el paso «Pruebas automáticas»: una de ellas, la del inglés de «Ejecuciones · Operación», porque la carga se mostraba a sí misma «En curso…» y «Esperando la base», dos textos sin inglés.
- **Regla:** la carga semanal corre solo las pruebas de datos y del pipeline (`pytest -m "datos and not rendimiento"`); la lista de esos archivos vive en `tests/conftest.py`, que les pone el marcador `datos`. Las de pantalla (traducciones, páginas, AppTest, documentos) corren en el CI de cada push. Una falla de pantalla nunca bloquea la publicación de datos. Queda en CLAUDE.md, en el SQAP (§7) y en `politica.json`.
- **Pruebas:** la que protege D-341 (`tests/test_rendimiento.py`) verifica también el filtro de la carga y que ningún archivo de datos use AppTest ni la auditoría del inglés.

## D-367 · La ventana de la carga muestra el log del paso que falló

- **Causa:** cuando falló la carga del 30-10, la ventana mostró las últimas 60 líneas del job: el final de una comparación y la limpieza de GitHub. La línea `FAILED` de la segunda prueba quedó fuera.
- **Decisión:** si un job falla, la ventana muestra la parte del log del paso que falló, desde su comando hasta la marca `##[error]` de GitHub, con sus últimas 60 líneas y, primero, las líneas `FAILED` de pytest que queden antes. El título nombra el paso por su comando. Un job que terminó bien sigue mostrando sus últimas líneas.
- **Pruebas:** `tests/test_run_monitor.py::test_d367_…`.

## D-368 · La franja de observabilidad suma la API REST de GitHub

- **Pedido del autor:** que el «Recorrido completo por capas» de «Pipeline y linaje» muestre cómo el panel sabe y actúa sobre las cargas a través de GitHub.
- **Decisión:** la franja OBSERVABILIDAD suma un sexto elemento, «API REST de GitHub · token · cargas, logs, lanzar, cancelar», en el recorrido horizontal y en el vertical del teléfono. Su explicación al pasar el cursor nombra la página «GitHub Actions» y la ventana de ejecución. Con seis elementos, la franja ocupa todo el ancho del diagrama. Nada más cambia. El SAD no tiene un diagrama con franja de observabilidad, así que no cambia.
- **Pruebas:** `tests/test_architecture.py::test_d368_…` (el elemento en las dos franjas, su explicación y su inglés).

## D-369 · La ventana «Elige tu vista»: dos opciones y el acceso del autor en una esquina

- **Pedido del autor:** que Profesional y Usuario sean las dos opciones grandes, una al lado de la otra; que Autor salga de entre ellas; y que, mientras la ventana está abierta, el panel de atrás no se pueda leer.
- **Decisión:** la ventana muestra solo dos píldoras, Profesional (con sus perfiles debajo) y Usuario. El acceso del Autor pasa a un enlace pequeño y discreto, «Acceso del autor» (inglés «Author access»), en la esquina superior derecha; al hacer clic abre su campo de clave, que se envía con Enter como antes (D-350) y usa la misma clave (D-335). Mientras la ventana está abierta, una capa oscura casi opaca y con desenfoque fuerte tapa la app. Nada más cambia: la ventana se sigue pidiendo en cada visita y recarga (D-340, D-357).
- **Pruebas:** `tests/test_control.py::test_d369_…` (en español e inglés, las dos opciones principales sin Autor, el enlace de la esquina con su campo de clave, y la capa que tapa el fondo).

## D-370 · El diagrama de despliegue nombra la API REST de GitHub y los pull requests del informe

- **Pedido del autor:** que la flecha del panel a GitHub diga lo que el panel hace con la API, y que la caja del informe semanal sea la de los pull requests.
- **Decisión:** la ruta de Streamlit Cloud a GitHub pasa de «API REST · workflow_dispatch» a «API REST de GitHub · lanzar, leer estado y logs, cancelar», en dos líneas para que quepa. La caja «Issues · Informe semanal» pasa a «Pull requests · informe semanal»: tras cada carga, el workflow de calidad propone el informe numerado como un pull request (D-331, D-363). Nada más cambia.
- **Pruebas:** `tests/test_deployment.py::test_d370_…` (los textos nuevos, sin los viejos, su inglés y el disparador del informe en `calidad.yml`).

## D-371 · Al elegir la vista, la app abre el Panorama

- **Pedido del autor:** que al elegir cualquier perfil en «Elige tu vista» la app lleve al Panorama de precios, sea cual sea la página desde donde se abrió; que un documento abierto por su dirección («Abrir» o «PDF») se quede; y confirmar que el indicador «Vista: <perfil> ▾» se ve en todas las vistas y reabre la ventana. El fondo tapado y el acceso del autor en una esquina ya los trajo D-369.
- **Decisión:** antes, cada perfil profesional abría la primera página de su menú (por ejemplo, Seguridad abría «Arquitectura de seguridad»). Ahora Usuario, Profesional, cualquiera de sus perfiles y el Autor abren el Panorama. Si la dirección pide uno de los documentos del proyecto (PRD, SAD, ADR, manual, glosario, índice de decisiones, plan de pruebas o SQAP), la app se queda en él. El orden del menú de cada perfil no cambia. El indicador ya estaba en Usuario, Profesional y Autor; ahora una prueba lo fija.
- **Pruebas:** `tests/test_control.py::test_d371_…` (el Panorama desde tres páginas distintas, el documento que se queda en español e inglés, y el indicador que reabre la ventana en las tres vistas); D-369 prueba las dos opciones principales sin Autor.

## D-372 · Panorama: pasos bloqueados en todas las vistas, números grandes y búsqueda llamativa

- **Pedido del autor:** tres ajustes en el Panorama: el bloqueo de pasos para todas las vistas, los números de los pasos grandes y destacados, y una búsqueda que se note.
- **Bloqueo (precisa D-352):** en Usuario, Profesional y Autor, los paneles 2 y 3 quedan bloqueados, con su candado y su frase, hasta completar el paso anterior. Ya no hay una familia elegida de antemano. Un paso hecho no se vuelve a bloquear en la visita, y un enlace que nombra una región o una familia cuenta como elegido.
- **Pasos:** cada panel empieza con su número (1, 2 o 3) en un círculo de color de 30 px, seguido de su texto («Elige una región», «Elige una familia», «Mira los productos») a 14,5 px, en negrita.
- **Búsqueda:** el campo es un poco más grande (44 px de alto, texto de 15 px). Su lupa y su borde de 2 px van en celeste luminoso: el acento de la app en los temas oscuros y, en los claros, cuyo acento es un azul parecido al de «bajó», el celeste #0891b2. Un brillo suave pulsa mientras nadie ha escrito. Se detiene al hacer clic en el campo o al escribir, y queda detenido el resto de la visita una vez que alguien escribió. No se anima si el sistema pide movimiento reducido, ni mientras el panel está bloqueado.
- **Inglés:** la nota de cobertura que aparece sin familia elegida (antes solo en la vista Usuario) no tenía inglés; ahora lo tiene, y sobra un espacio doble.
- **Pruebas:** `tests/test_panorama_steps.py::test_d372_…` (el bloqueo en las vistas Profesional y Autor, el número en su círculo con el texto y su inglés, y el color, el tamaño, el brillo y sus tres paradas de la búsqueda).

## D-373 · El botón «Vista» sube debajo del logo, y el logo también cambia de vista

- **Pedido del autor:** que el indicador «Vista: <perfil> ▾» pase arriba del menú, justo debajo del logo, como un botón visible con ícono de perfil y el texto «Vista: Usuario · Cambiar»; que salga de abajo, junto a «Apariencia»; y que el logo también reabra «Elige tu vista». Sin botón extra en el encabezado.
- **Decisión:** el botón va primero en el menú, antes del aviso de la carga y de las secciones. Lleva el ícono de perfil, borde y fondo en celeste, y dice «Vista: Usuario · Cambiar» («View: User · Change»), con Profesional o Autor según la vista. Un clic en el logo GreenOcean (el del menú o el del encabezado con el menú plegado) abre la ventana en vez de ir a la primera página: lo captura el script que ya guarda la vista en las recargas de la app (D-357). Al elegir otra vista por cualquiera de los dos caminos, la sesión de Autor se cierra (D-353). El PRD, el SAD y el manual (español e inglés) dicen dónde está el botón, y el manual nombra el enlace «Acceso del autor» de D-369.
- **Pruebas:** `tests/test_view_switch.py::test_d373_…` (el botón antes del menú y fuera del pie, su texto e ícono en las tres vistas y en inglés, y que reabre la ventana; el clic en el logo abre la ventana).

## D-374 · Las semanas se leen como rango de lunes a domingo

- **Pedido del autor:** que la app muestre siempre una semana como su rango de lunes a domingo, con la abreviatura del mes («19–25 oct», «26 oct – 1 nov»), nunca solo por su lunes («semana del 19-10»); y que el encabezado del Panorama diga cuál es la próxima semana.
- **Decisión:** un módulo nuevo, `bi/weeks.py`, escribe el rango en español y en inglés («Oct 19–25», «Oct 26 – Nov 1»), con el año al final cuando hace falta («19–25 oct 2026»). Solo usa la biblioteca estándar, porque también lo usa el informe semanal de la carga. Por dentro, la semana sigue siendo su lunes (`week_start`). La traducción de las páginas reconoce los dos tipos de rango, dentro de un mes y entre dos meses, y da el mismo inglés que el código.
- **Dónde:** en el Panorama (la semana del encabezado, las columnas de precio de la tabla, el detalle «Ver cálculo» y el mapa); en «Último dato por canal» (la semana de cada fuente, la anterior y la que falta); en los avisos («ODEPA aún no publica la semana 19–25 oct (mayorista)»); en los informes (el informe semanal de la carga y la semana de datos de los informes de calidad, en el panel y en su presentación, sin tocar los archivos de los informes, que no se editan); y en las tablas y textos: la tabla de semanas, los atípicos, la cobertura de Calidad, los KPI, el Centro de operación y las cifras del pipeline y del despliegue.
- **Próxima semana:** bajo el rango de la semana mostrada, una línea discreta «Próxima semana: 19–25 oct» («Next week: Oct 19–25»), calculada sola como la semana mostrada más siete días.
- **Pruebas:** `tests/test_weeks.py` (un rango dentro del mes y otro que cruza de mes, en los dos idiomas; la próxima semana en el encabezado, en español e inglés; los avisos y las tablas, y que ningún archivo del panel escribe «semana del» con una fecha).

## D-375 · La sección «Negocio · BI» pasa a «Negocio · BA y BI»

- **Pedido del autor:** renombrar la sección del menú, porque reunirá el análisis de negocio y de sistemas (BA y BSA) junto a la inteligencia de negocios (BI).
- **Decisión:** el menú, la ruta de cada página («Negocio · BA y BI › Panorama de precios») y el PRD §7 dicen «Negocio · BA y BI»; en inglés, «Business · BA and BI». Las páginas de la sección no cambian todavía.
- **El encabezado del Panorama (precisa D-374):** con el nombre más largo y la línea «Próxima semana», el encabezado se montaba sobre sus botones bajo 1440 px. La línea de la próxima semana pasa bajo el nombre de la página y termina junto al rango de la semana, así ya no ensancha el encabezado. Cuando falta espacio, ceden primero el nombre de la sección («Negocio · B…», o nada) y la región del rango («12–18 oct · Arica y Pa…»). El nombre de la página, la próxima semana y el rango de la semana siempre se leen enteros. Bajo 1300 px, el encabezado usa dos filas. Se midió sin superposición entre 1120 y 1536 px, con y sin región elegida.
- **Pruebas:** `tests/test_weeks.py::test_d375_…` (la línea bajo el nombre de la página, la región aparte y las reglas que ceden espacio) y las pruebas del menú y de la traducción con el nombre nuevo.

## D-376 · Página «Interesados»

- **Pedido del autor:** una página para todos, con una tarjeta por interesado: quién es, qué pregunta se hace, qué decisión le ayuda a tomar y un enlace a la página donde está la respuesta. El mismo contenido va en el PRD §3, y la página lo lee de ahí.
- **Decisión:** el PRD §3 se divide en «3.1 Interesados» (cinco: personas y familias; restaurantes y almacenes; mayoristas, agricultores y feriantes; periodistas y economistas; equipos técnicos y reclutadores) y «3.2 Perfiles de uso», la tabla de antes, que sigue junto a ellos. La página dibuja una tarjeta con ícono por cada fila de 3.1, en el idioma de la visita (`docs/` o `docs/en/`), y cada enlace es un `[[vista:…]]` de la tabla. Por eso «Precios e inflación», que se abre desde el Panorama, también se enlaza desde un documento. En la vista Usuario, la tarjeta técnica muestra «Cambiar a Profesional» en vez de páginas que su menú no tiene; el botón deja la vista Profesional con el perfil Data Eng y se queda en la página.
- **Precisión:** la pregunta de periodistas y economistas no dice «por región»: el IPC de alimentos del INE es nacional y «Precios e inflación» compara las familias con él en todo Chile.
- **Por ahora:** la página va al final de la sección; D-378 ordena la sección.
- **Pruebas:** `tests/test_stakeholders.py` (las cinco filas del PRD en los dos idiomas, cada página enlazada existe, los enlaces en la vista Profesional, «Cambiar a Profesional» solo en la tarjeta técnica de la vista Usuario, y el inglés); `tests/test_prd_traceability.py` lee los casos de uso de 3.2.

## D-377 · Página «Análisis de negocio y sistemas»

- **Pedido del autor:** una página para todos que muestre el trabajo de Business Analyst y de Business Systems Analyst, contado como un caso, leyendo del PRD, del SQAP y de las decisiones, sin duplicar texto.
- **Decisión:** diez bloques, con la lista a la izquierda y un bloque a la vez a la derecha, para que la página quepa en una pantalla. Un enlace puede abrirla en un bloque (`?bloque=KPIs`). Cada texto se lee del documento al dibujarse, en el idioma de la visita (`bi/business_analysis.py`):
  1. **El problema:** PRD §2.
  2. **Interesados:** un resumen de PRD §3.1 y el enlace a «Interesados» (D-376).
  3. **Qué escuchamos:** PRD §3.3. Dice solo lo que el autor escribió: una revisión de uso (no sabían por dónde empezar a leer el Panorama) y una revisión de arquitectura por un usuario real, sin cambios solicitados; esta no se liga a ninguna decisión. No hay otras revisiones ni cifras.
  4. **Requisitos:** RF-01 a RF-09 de PRD §5, cada uno con su criterio medible.
  5. **Alcance:** PRD §6, que gana la columna «Por qué» en lo que incluye y en lo que excluye. Cada razón sale de lo ya escrito (ADR-01, ADR-02, ADR-33, D-009, D-019, D-356, RN-03, RN-07, RN-11, RF-06, RNF-02 y RNF-03); la única que no estaba escrita, la de «Recomendaciones de compra para el consumidor», la dio el autor: el panel describe lo que pasó con los precios, y recomendar qué comprar exige un juicio sobre cada persona que los datos públicos no dan.
  6. **Proceso:** una figura nueva, `ciclo_semanal` (carga, pruebas, publicación, informe semanal, informe de calidad y las correcciones de la semana siguiente), con íconos y flechas rectas. La usan la página y el PRD §2, así que se dibuja una sola vez.
  7. **KPIs:** la definición de cada uno (qué mide, cómo se calcula y por qué), que sale de Insights; sus valores se quedan en las páginas de BI. Insights pierde el selector «Preguntas / KPIs», conserva su tabla de preguntas y enlaza a este bloque.
  8. **Decisiones de sistema:** seis, cada una con una o dos frases del SQAP y un enlace: qué medimos y qué no (§3 y §5, con «No medimos» antes de la segunda), umbrales aceptables (§6), pruebas que bloquean y pruebas que informan (§7), fuentes retrasadas (§10), registro de fallas con su historial (§9, enlace a la pestaña «Registro» de Git workflow) y alertas al Autor (§10).
  9. **Evaluación:** SQAP §4, los criterios de aceptación de PRD §10 y el último informe de calidad.
  10. **Del feedback al cambio:** la tabla de PRD §3.3, con la decisión de cada cambio (D-352 y D-372 para la revisión de uso).
- **Documentos:** el PRD sube a 3.4 (qué escuchamos, el porqué del alcance y el ciclo semanal en §2); el glosario suma BSA (2.3). La figura entra en la lista de figuras del PRD (`tests/test_documents.py`).
- **Pruebas:** `tests/test_business_analysis.py` (los diez bloques y su inglés, cada texto leído del documento en los dos idiomas, lo que se escuchó sin nada más, las seis decisiones leídas del SQAP con su página, la figura del ciclo, las definiciones fuera de Insights, el bloque abierto por enlace y la página en inglés).

## D-378 · La sección «Negocio · BA y BI» se lee en el orden de un visitante

- **Pedido del autor:** con el plan aprobado, ordenar la sección en el orden de lectura de un visitante: primero BA y BSA (Interesados y Análisis de negocio y sistemas) y después BI (Panorama de precios, Último dato por canal e Insights); actualizar enlaces, mapa de la app y pruebas.
- **Inventario (el plan aprobado):** ninguna otra página cambia de sección. «Precios e inflación» sigue abriéndose desde el botón «Inflación» del Panorama (D-308); Consultas SQL sigue en Ingeniería de datos, porque es una herramienta técnica (el análisis la enlaza como evidencia de P-2 y P-3); y Calidad, DevOps y Stack siguen como estaban. Las definiciones de los KPI salieron de Insights en D-377.
- **Decisión:** el menú de la sección va así: Interesados, Análisis de negocio y sistemas, Panorama de precios, Último dato por canal e Insights, en las vistas Usuario, Profesional y Autor. Al elegir una vista, la app sigue abriendo el Panorama (D-371), aunque ahora no sea la primera línea del menú. Las dos páginas nuevas se dibujan como las demás páginas principales (una barra fina y todo en una pantalla): sin el pie «Anterior / Siguiente», que se midió sin desbordar a 1440 × 790 y a 1920 × 1000 en los diez bloques del análisis.
- **Mapa de la app:** la lista de páginas del nodo del panel estaba desactualizada (le faltaban «Último dato por canal», «Método y calidad» y «Git workflow»); ahora nombra todas las páginas, en el orden del menú, con su inglés.
- **Documentos:** el PRD (§7) lista las páginas de la sección en su orden y sube a 3.5.
- **Pruebas:** `tests/test_menu_order.py` (el orden de la sección para cada vista y en inglés, sin pie en sus páginas principales, el Panorama como destino de la elección y el mapa de la app con el mismo orden del menú); las pruebas que fijaban el orden anterior pasan al nuevo.

## D-379 · Los botones «Minimizar» y «Cerrar» de la ventana de la carga dejan de perderse

- **Aviso del autor:** con la carga terminada, «Minimizar» y «Cerrar» no respondían.
- **Causa:** la ventana de la carga se refresca sola cada 4 s (D-351), y los dos botones la cerraban recargando toda la página desde dentro de ese refresco. Si uno de los refrescos caía mientras la página se recargaba, la ventana quedaba abierta y sin quien la atendiera en el servidor, y sus botones no hacían nada. Streamlit lo reconoce en su propio código como un caso conocido con este patrón (una ventana con una parte que se refresca sola). Ocurre más cuanto más lenta es la página, y las pruebas con AppTest no lo ven, porque no reproducen el refresco.
- **Medición:** la ventana real, con GitHub reemplazado por respuestas fijas y una recarga de página de 3 s, 12 clics en «Cerrar» repartidos por el ciclo de refresco, en ventanas posteriores a la primera de la sesión: la versión anterior dejó la ventana abierta 3 veces; la nueva, ninguna.
- **Límite:** en esa prueba larga hubo cierres de unos 10 s, iguales en las dos versiones. Con un solo clic no se repitieron, y no los he explicado. La falla se comprueba en el uso real con la próxima carga manual.
- **Decisión:** «Minimizar» y «Cerrar» pasan a ser acciones que corren antes que el refresco (devoluciones de llamada) y cierran en dos pasos. Primero recargan solo el marco de la ventana, un fragmento con nombre y sin refresco propio, que no dibuja la parte que se refresca: Streamlit cancela su temporizador en ese momento. Después el marco recarga la página, sin nada que pueda caer durante la recarga. Si una copia vieja de la ventana sigue en pantalla cuando su ejecución ya no existe, se cierra sola. «Cancelar» y su confirmación no cambian.
- **Registro de fallas:** F-20 (código, estación 15), abierta hasta que se compruebe con una carga real.
- **Pruebas:** `tests/test_run_window_close.py` (la estructura, lo que hace cada botón con la ejecución y que el cierre pasa siempre primero por el marco); las de D-351 siguen igual.

## D-380 · Las pruebas y las páginas se ponen al día con la base de la carga del 31-10

- **Qué pasó:** la carga semanal del 31-10 construyó la base con la tabla `latest_by_source` de D-365, así que tiene 17 modelos dbt (antes 16). Al traer esa base, 24 pruebas fallaron en esta máquina; con la última versión ya publicada (sin mis cambios) fallaban las mismas, y el CI las habría puesto en rojo en el próximo push. No habían bloqueado la carga porque son pruebas de pantalla (D-366).
- **Lo que era del proyecto y se corrige:**
  - El linaje dbt no cabía con diez marts: las filas se estiran un poco (de 144 a 706) y el área sensible de cada mart pasa de 68 a 62 px de alto (el cuadro mide 54).
  - `latest_by_source` no tenía descripción en el esquema de dbt; ahora la tiene (sin pruebas nuevas, siguen siendo 31). La prueba del linaje exige que todo modelo del proyecto esté descrito en su archivo, y tolera que la base publicada sea anterior a una descripción.
  - Las pruebas que fijaban «16 modelos», «12 tablas» o «9 marts» ahora leen la cifra de la base.
  - La página «Último dato por canal», que hasta hoy solo mostraba su aviso, tenía frases a medio traducir («… · all of Chile»): ahora recibe «todo Chile» en español y se traduce la frase entera, como el Panorama.
  - La prueba del orden de los productos reconocía una cifra «delgada» solo por la marca «1 cotización»; desde D-327 también lo es la que se apoya en una sola región (D-327 no actualizó la prueba, y esta semana hay filas así).
  - La tabla de paridad SQLite ↔ DuckDB mezclaba números y palabras («misma suma» / «distinta») en la misma columna y fallaba al dibujarse cuando las dos bases difieren; ahora todo es texto. Y la lista de archivos que no coinciden con su huella usa «y» o «and» según el idioma.
- **Lo que no es del proyecto:** mi respaldo SQLite local (`etl/datos.db`, del 21-10) es anterior a la base publicada, así que las pruebas de paridad (y el veredicto «Datos sanos» de Calidad) fallan en esta máquina hasta que se reconstruya con `python etl/etl.py`. En el CI ese archivo no existe y esas pruebas se saltan. Se verificó el resto con el respaldo apartado, como lo ve el CI: 1172 pasan.
- **Pruebas:** `tests/test_lineage.py` (diez marts, esquema descrito), `tests/test_quality_audit.py` (la paridad se dibuja con las bases distintas, la lista de archivos), `tests/test_channel_latest.py` (el alcance en español), y las que fijaban cifras ahora las leen de la base.

## D-381 · Los documentos se ordenan en cuatro carpetas

- **Pedido del autor:** ordenar `docs/` (y `docs/en/` igual) por el contenido real de cada documento, con una carpeta por tema, y mostrarlas en «Documentos» con su ícono.
- **Decisión:** cuatro carpetas. `negocio/`: PRD y Glosario. `arquitectura/`: SAD, ADR e Índice de decisiones. `calidad/`: Plan de calidad (SQAP) y Plan de pruebas y seguridad. `operacion/`: Manual. En `docs/` quedan `DECISIONES.md` (el registro, que se cita en cada commit) y `DISENO.md` y `PROYECTO.md` (fuentes que lee la app); `archivo/`, `img/`, `referencia/` y `privado/` no cambian. `calidad/` ya guardaba los datos del plan de calidad (metas, informes, plan de mitigación): los dos documentos se suman al lado, sin mover esos datos, para no tocar el CI.
- **Cómo se resuelve:** `i18n.DOCUMENT_FOLDERS` dice la carpeta de cada documento e `i18n.document_path` da su ruta en el idioma de la visita; nada arma una ruta a mano. Los enlaces entre documentos son relativos a su carpeta (`../negocio/GLOSARIO.md`), así que funcionan también en GitHub, y la app los sigue reconociendo. El PDF no cambia: es la página impresa.
- **La app:** «Documentos» agrupa los ocho documentos por carpeta, cada una con su ícono (maletín, planos, escudo con visto y llave) y su nombre en español e inglés; el orden de lectura pasa a ser el de las carpetas.
- **Pruebas:** `tests/test_dashboard.py::test_d282_…` (cuatro carpetas, cada documento en su carpeta en español e inglés y nada más en `docs/`), `tests/test_documents.py` (cada enlace entre documentos llega a su archivo) y las que leían los documentos por su ruta antigua, que ahora usan `document_path`. La prueba de enlaces públicos (`test_t54`) consulta GitHub y no pasa hasta que estos archivos estén en `main`.

## D-382 · Los diagramas muestran a los tres perfiles y lo que el panel hace con la API de GitHub

- **Pedido del autor:** que ningún diagrama muestre un solo «Visitante» o un «Administrador»: el panel tiene tres vistas (Usuario, Profesional y Autor) y cada diagrama debe decir qué ve cada una. Y que toda flecha del panel a GitHub diga lo que hace: lanzar, leer estado y logs, cancelar.
- **Decisión:** el contexto y los contenedores (las vistas de la app y las figuras del SAD), el mapa de la app, los componentes del panel, los escenarios, la secuencia al abrir el panel, los actores del glosario y el despliegue muestran a las tres personas, cada una con su color: Usuario (verde, ve el negocio), Profesional (azul, ve todo y usa el SQL de solo lectura) y Autor (ámbar, con la clave de control). «Administrador» pasa a «Autor» en todas partes. En los dos mapas de seguridad, Usuario y Profesional comparten un nodo porque comparten el nivel de confianza (sin cuenta); el Autor tiene la clave. La secuencia al abrir el panel suma el paso «Elige tu vista». En el mapa de la app, el Profesional ocupa la columna «Lectores» junto al Usuario y el Autor pasa junto al panel y sus secretos. Las flechas a la API de GitHub dicen «lanzar, leer estado y logs, cancelar» (o, partidas en dos, «lanza y cancela la carga» y «lee estado y logs»), como hace `bi/control.py`.
- **Pruebas:** `tests/test_doc_diagrams.py` (contexto y contenedores con las tres personas y sus líneas), `tests/test_app_map.py` (el Profesional en el tema seguridad, por el SQL), `tests/test_security.py` y `tests/test_i18n.py` (el inglés de cada texto nuevo).

## D-383 · El despliegue muestra los dos informes: el semanal como issue y el de calidad como pull request

- **Pedido del autor:** que el diagrama de despliegue tenga dos cajas, una por informe, porque GitHub guarda cada uno en un lugar distinto.
- **Decisión:** dentro de GitHub hay dos entornos. «Issues · informe semanal»: al final de cada carga, `semanal.yml` abre un issue «Informe semanal» (`gh issue create`). «Pull requests · informe de calidad»: tras cada carga, `calidad.yml` mide los indicadores y propone el informe numerado como un pull request, que el autor aprueba (D-331, D-363). Esto corrige D-370, que había dejado una sola caja. Para dar espacio, la ruta «despliegue de main» baja unos píxeles; ninguna otra pieza se mueve.
- **Pruebas:** `tests/test_deployment.py::test_d383_…` (las dos cajas, el comando de cada workflow y su inglés).

## D-384 · Los 11 indicadores de la carga y los 12 del plan de calidad tienen nombres distintos

- **Pedido del autor:** que «indicadores de calidad» no signifique 11 en un sitio y 12 en otro.
- **Decisión:** dos nombres. «Indicadores de calidad de los datos» son los 11 que `bi/quality_live.py` mide en cada carga sobre la base publicada, en cinco dimensiones (completitud, actualidad, validez, unicidad y consistencia); se ven en «Calidad y auditoría». «Indicadores del plan de calidad» son los 12 de `docs/calidad/metas.json` (8 de código y 4 de datos) que el workflow de calidad mide cada semana; se ven en «Método y calidad». El panel (Insights, el resumen de la carga, el mapa de la app, «Método y calidad»), el README de `docs/calidad/` y los documentos usan cada nombre para su conjunto; el PRD y el SQAP lo adoptan en su propio commit.
- **Pruebas:** `tests/test_quality_method.py` (la frase del plan con su nombre) y `tests/test_i18n.py` (el inglés de cada frase).

## D-385 · La alerta de precio tiene una sola definición y cada KPI dice su indicador técnico

- **Pedido del autor:** que la alerta de precio (K6) se defina igual en todas partes, y que los dos vocabularios de indicadores se encuentren.
- **Decisión:** la regla vive en `bi/alerts.py`: un cambio fuera del promedio ± 2 desviaciones de sus 12 semanas previas, de al menos 10 % y con dos cotizaciones en cada semana. `alerts.describe_rule()` la escribe desde esas constantes y la tabla de KPIs la usa; el PRD (RF-05, en los dos idiomas), `docs/PROYECTO.md` y `docs/DISENO.md` dicen lo mismo con las mismas cifras. En «Análisis de negocio y sistemas», la tabla de KPIs suma la columna «Indicador técnico»: «K1 · Brecha de precio», «K6 · Alertas de precio» y «K8 · Filas rechazadas» abren su cálculo paso a paso; los otros cinco KPIs se calculan solo para el panel y llevan un guion.
- **Pruebas:** `tests/test_kpi_vocabulary.py` (la regla sale de las constantes y los cuatro textos la repiten; cada KPI con su indicador o su guion).

## D-386 · Las medidas de ADR-35 se rotulan como históricas y `DISENO.md` no lleva nombre personal

- **Pedido del autor:** que la figura «ADR-35: la base servida, antes y después» no muestre una fecha fija como si fuera actual, y que ningún documento lleve un nombre personal.
- **Decisión:** la nota de la figura dice que las cifras de «antes» se midieron el 24-10-2026, al decidir ADR-35, y suma el tamaño de hoy de la base servida, medido al dibujarla (sin la base, solo la parte histórica). El texto del ADR ya es un registro histórico y no cambia. La cabecera de `docs/DISENO.md` pasa de un nombre personal a «Autor: el autor». `LICENSE` conserva el nombre, porque la licencia exige un titular; la firma del README queda como está hasta que el autor decida.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d386_…` (la nota histórica y el tamaño medido) y `tests/test_documents.py::test_d386_…` (ningún documento de `docs/` firmado con un nombre).

## D-387 · El README nombra todas las páginas del menú, en su orden

- **Pedido del autor:** que el README y `CLAUDE.md` no queden atrasados respecto de la app.
- **Decisión:** la lista «Páginas del panel» del README sigue el menú, sección por sección (de Interesados a Git workflow, con GitHub Actions marcada como página del autor), y dice qué muestra cada vista. `CLAUDE.md` deja de fijar el rango de decisiones («desde D-001, una por cambio»), que se atrasaba en cada entrega; el número de pruebas y las carpetas de `docs/` ya se pusieron al día en D-381.
- **Pruebas:** `tests/test_menu_order.py::test_d387_…` (cada página del menú está en la lista del README, en el mismo orden).

## D-388 · Revisión de los ocho documentos: redacción simple y al día con la app

- **Pedido del autor:** que los documentos oficiales (PRD, SAD, SQAP, Manual, Plan de pruebas y seguridad, ADR, Índice de decisiones y Glosario) digan lo mismo que la app, en texto, tablas y diagramas, y que se lean como los escribiría un redactor profesional: frases cortas y directas, sin relleno ni repeticiones. El orden visual (portada, índice, tablas y diagramas) no cambia, y la versión en inglés sigue a la española.
- **Decisión:** un commit por documento, con su versión inglesa. Cada uno sube su versión menor y anota en su historial qué cambió. Las reglas comunes: una idea por frase; las listas largas dentro de un párrafo pasan a viñetas; cada nombre de pantalla es el que la app muestra en ese idioma; las tres vistas (Usuario, Profesional y Autor) reemplazan a «visitante» y «administrador»; los 11 indicadores de calidad de los datos y los 12 del plan de calidad se nombran como en D-384; la alerta de precio se define como en D-385; el informe semanal es un issue y el de calidad un pull request (D-383); y las cifras son las de la carga del 31-10-2026.
- **Pruebas:** las de cada documento (`tests/test_documents.py`, `tests/test_i18n.py`, `tests/test_prd_traceability.py`, `tests/test_business_analysis.py`), que ahora siguen a cada documento a través de su carpeta (D-381) y leen los nombres nuevos.

## D-389 · La base servida tiene 13 tablas, y el mapa de la base las muestra todas

- **Qué no cuadraba:** D-365 sumó `latest_by_source` a la base servida, pero el mapa de la base, el mapa de almacenamiento, los cruces entre bases y la vista de contenedores seguían diciendo «12 tablas» y «nueve tablas del modelo». El SAD ya listaba las 13.
- **Decisión:** el grupo «Modelos dbt» del mapa de la base suma `latest_by_source` y pasa a «diez tablas del modelo»; los cuatro textos dicen 13 tablas, en los dos idiomas.
- **Pruebas:** `tests/test_storage_map.py::test_the_thirteen_served_tables_…` (las tablas del mapa son las que copia la carga, más el registro de cargas y las dos trazas de dbt).

## D-390 · La auditoría desde `raw.db` toma una muestra fija y dentro de las semanas que guarda

- **Qué pasó:** en local, `test_weekly_prices_rebuild_exactly_from_the_raw_rows` falló en las dos fuentes con una división por cero, sin que nada hubiera cambiado. La consulta de la muestra no tenía `ORDER BY`, así que DuckDB podía devolver las filas en otro orden y la misma semilla elegía otras filas. Algunas eran de semanas posteriores al `raw.db` local (del 23-10), que no se pueden reconstruir. En el CI no corre, porque no hay `raw.db`.
- **Decisión:** la muestra se ordena (`ORDER BY ALL`) y solo toma semanas hasta la última que guarda `raw.db`. La misma semilla elige siempre las mismas filas. Queda anotada como F-21 en el registro de fallas.
- **Pruebas:** la misma prueba, que pasa en corridas repetidas.

## D-391 · «Calidad y auditoría» se lee entera en inglés y «Precios e inflación» se ubica en su sección

- **Qué no cuadraba:** al regenerar las capturas (D-392) aparecieron dos cosas. En inglés, el diagrama de calidad dejaba en español sus palabras cortas («Puerta 1», «Mide», «Rechazo», «Origen», la leyenda y «Tres puertas · seis dimensiones · un veredicto») y el botón «Volver a medir»; la prueba de idioma no las veía por ser palabras sueltas. Y la ruta de «Precios e inflación» decía «Dashboard › Precios e inflación», con el nombre de una ventana que el menú ya no usa.
- **Decisión:** esas once frases tienen su inglés. Una página que se abre desde un botón (D-308) se ubica en la sección del menú de la página desde donde se abre: «Negocio · BA y BI › Precios e inflación», con el mismo formato «Sección › Página» de las demás. Para que la ruta completa quepa junto a los chips, la pregunta de la barra cede primero (su mínimo baja de 9em a 6,5em) y conserva su texto completo al pasar el cursor.
- **Pruebas:** `tests/test_quality_audit.py::test_d391_…` (cada palabra del diagrama y el botón tienen su inglés) y `tests/test_page_bar.py::test_d391_…` (la ruta de cada página con puerta).

## D-392 · Capturas nuevas del panel en los documentos y en el README

- **Pedido del autor:** regenerar las capturas, que eran del 20-10-2026 y mostraban el menú y las páginas de entonces.
- **Decisión:** seis capturas del 31-10-2026 en `docs/img/` y `docs/img/en/`, a 1440 × 900, una por tema al menos: el Panorama en la vista Usuario (Corporativo, paso 1) y en la Profesional (Vantablack, con una región y una familia elegidas), Precios e inflación (Dark Grey), Pipeline y linaje (Blue Light), Consultas SQL (Corporativo) y Calidad y auditoría (Vantablack). Cada pie dice su tema y su vista, en el idioma del documento; antes, el PRD en inglés los mostraba en español. Las cuatro del README (Panorama, Insights, Pipeline y Calidad) son del tema oscuro, el de entrada. Se tomaron sin el respaldo local `etl/datos.db`, que está desactualizado: con él, la calidad marcaba una paridad fallida que en producción no existe.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d205_…` (seis capturas reales, los cuatro temas, las dos vistas y su tamaño) y `tests/test_doc_diagrams.py::test_d392_…` (los pies en inglés).

## D-393 · La clave del Autor tiene un límite de intentos con espera creciente

- **Pedido del autor:** cerrar el riesgo aceptado en D-249. Un script podía probar claves sin parar, y recargar la página reiniciaba cualquier conteo.
- **Decisión:** todas las puertas de la clave (la esquina de «Elige tu vista», «Acceso del autor» en Centro de operación y la ventana de ejecución) comparten una sola espera, guardada en el servidor y no en la sesión. Tras 3 fallos, cada intento espera 2 s, y el doble tras cada nuevo fallo, hasta 15 min. Mientras espera, ni la clave correcta se compara: el panel dice «Demasiados intentos. Vuelve a intentar en N s». La clave correcta vuelve el conteo a cero. Como la espera es común, alguien podría trabar el acceso un rato; el autor siempre puede lanzar la carga desde GitHub.
- **Pruebas:** `tests/test_control.py::test_d393_…` (2, 4, 8, 16 s… hasta 900 s, la clave correcta rechazada mientras espera y la vuelta a cero) y `tests/test_dashboard.py::test_d393_…` (la ventana de ejecución dice «Demasiados intentos» al cuarto intento). El caso S-05 del plan de pruebas apunta a la prueba nueva.

## D-394 · «Ver todo el proyecto» abre la vista Profesional sin clave

- **Pedido del autor:** que en la vista Usuario «Ver todo el proyecto» no pida la clave del Autor.
- **Qué no cuadraba:** la vista Profesional es libre en «Elige tu vista», pero este botón pedía la clave de control y daba la vista Autor. Quien recibía «la clave para ver todo» recibía en realidad el poder de lanzar cargas, y el panel tenía una tercera puerta a la clave.
- **Decisión:** el botón pasa a la vista Profesional, sin clave y sin la parte del Autor. Quedan dos puertas a la clave: la esquina de «Elige tu vista» y «Acceso del autor» en Centro de operación. Ambas comparten la espera de D-393.
- **Pruebas:** `tests/test_dashboard.py::test_d394_…` (sin campo de clave, abre Profesional y nunca Autor).

## D-395 · La vista Autor se cierra tras 30 minutos sin actividad

- **Pedido del autor:** que una pestaña olvidada en un computador compartido no quede como Autor para siempre.
- **Decisión:** cada ejecución completa de la página (un clic, una elección, un cambio de página) cuenta como actividad. Si pasan más de 30 minutos sin ninguna, la vista Autor se cierra igual que al salir de ella (D-353): se pierde la clave y la carga seguida queda en GitHub. El panel lo avisa con «La vista Autor se cerró tras 30 min sin actividad», y volver a entrar pide la clave. El refresco automático de la ventana de ejecución no cuenta como actividad.
- **Pruebas:** `tests/test_view_switch.py::test_d395_…` (29 min la mantiene, más de 30 la cierra, sin clave no hay nada que cerrar).

## D-396 · «Recargar datos» solo para el Autor

- **Pedido del autor:** que nadie sin la clave pueda vaciar la memoria del panel de todos.
- **Qué no cuadraba:** el botón de Centro de operación vaciaba la caché compartida por todos los lectores. Cualquiera podía pulsarlo una y otra vez y obligar al panel a recalcularlo todo, más lento para todos.
- **Decisión:** el botón aparece solo en la vista Autor. La base nueva igual llega sola: el panel la descarga cuando cambia su puntero.
- **Pruebas:** `tests/test_dashboard.py::test_d396_…` y `test_d149_…` (sin la clave no hay botón; con ella, recarga y confirma).

## D-397 · «GitHub Actions» usa solo el token de solo lectura

- **Pedido del autor:** mínimo privilegio en la página que lee GitHub.
- **Qué no cuadraba:** si faltaba `GITHUB_READ_TOKEN`, la página leía con `GITHUB_TOKEN`, que también puede lanzar y cancelar cargas.
- **Decisión:** la página envía solo `GITHUB_READ_TOKEN`. Si falta, muestra los estados de las ejecuciones (que son públicos) sin logs, con el aviso «Falta el token de solo lectura», y nunca usa el otro. El otro token se sigue tachando en cualquier texto, por si un log lo imprimiera.
- **Pruebas:** `tests/test_github_actions.py::test_d397_…` y `tests/test_actions_page.py` (sin el token de solo lectura no se envía ninguna credencial y aparece el aviso).

## D-398 · El encabezado solo sirve para ubicarse; la información va en el contenido y los enlaces, en el menú

- **Pedido del autor:** ordenar el encabezado de todas las páginas y que nada se monte sobre otra cosa.
- **Decisión:** el encabezado lleva solo «Volver», la ruta de la página (su descripción al pasar el cursor), la semana mostrada como rango con «Próxima semana» en letra pequeña donde aplica (el Panorama) y la fecha de los datos. Lo demás pasa a una fila del contenido, justo debajo, que se acomoda en dos líneas si no cabe: la pregunta de la página cuando no es su nombre, sus cifras, sus términos y sus controles (el selector de Documentos, «Volver a medir», el acceso del autor). Salen los enlaces a otras páginas: «Inflación» y «Ver último dato por canal» del Panorama, el plan de pruebas de Arquitectura de seguridad y el mapa de la app de Stack y evidencia. En el Panorama, «Semanas» pasa a un selector del contenido («La semana» o «Últimas semanas», con la tabla en la página) y el contador de alertas pasa a un aviso propio («▲ 13 alertas de precio esta semana»), que abre el detalle por familia. «Precios e inflación», que solo se abría desde el Panorama (D-308), entra al menú de Negocio en el orden pedido: Panorama de precios, Último dato por canal, Precios e inflación e Insights. La ruta ya no se esconde en pantallas angostas: se corta con «…» antes de tocar la fecha.
- **Medición:** en 1920 × 1000, 1440 × 900, 1280 × 800 y 1024 × 768, en español e inglés, ningún elemento del encabezado ni de la fila de contenido se monta sobre otro. En 1280 × 800 y 1024 × 768 algunas páginas se desplazan; eso queda para el plan de 4B.
- **Regla en CLAUDE.md:** el encabezado es solo para ubicarse y navegar; la información va en el contenido y los enlaces a páginas en el menú.
- **Pruebas:** `tests/test_page_bar.py::test_d398_…` (en cada página y en los dos idiomas, el encabezado no tiene enlaces ni otro botón que «Volver»; la ruta se corta en vez de esconderse; la fila de contenido se acomoda), y las pruebas del menú, del Panorama y del mapa de la app con el orden nuevo.

## D-399 · La prueba de los filtros de informes no supone una sola semana

- **Qué pasó:** al fusionar el informe N° 7 (semana del 26-10), `pytest` falló en main en `test_d333_…`: la prueba suponía que todos los informes, salvo el N° 1, eran de la semana del 12-10. El error era de la prueba, no de la app.
- **Decisión:** la prueba recorre las semanas que traen los informes y comprueba que el filtro de cada una devuelve exactamente los informes de esa semana.
- **Pruebas:** `tests/test_quality_method.py::test_d333_…`.

## D-400 · Las dos no conformidades del informe N° 7 quedan registradas

- **Qué pasó:** el informe N° 7 (carga del 31-10) trae dos indicadores fuera de lo aceptable que nadie había anotado, y la regla de D-334 hizo fallar `pytest` en main.
- **Decisión:** se anotan en `docs/calidad/no_conformidades.json`. «Pruebas que fallan» (crítico, 6 pruebas) lleva su causa demostrada: la base del 31-10 llegó a main antes que los arreglos de D-380. «Precios con comparación válida» (urgente, 83,3 %) queda con la causa pendiente, porque no está demostrada. La acción y el estado de las dos quedan en blanco: los escribe el autor.
- **Pruebas:** `tests/test_quality_method.py::test_d334_…`.

## D-401 · El workflow de calidad anota las no conformidades al crear cada informe

- **Qué pasó:** las no conformidades del informe N° 7 no estaban anotadas, y fusionar el informe hizo fallar `pytest` en main (D-400).
- **Decisión:** `scripts/informe_calidad.py`, al crear un informe, agrega a `docs/calidad/no_conformidades.json` una línea por cada indicador urgente o crítico que falte, con la causa, la acción y el estado en blanco para el autor. Una segunda corrida no agrega nada. `calidad.yml` sube ese archivo en el mismo pull request del informe, así que fusionarlo deja main en verde.
- **Pruebas:** `tests/test_quality_method.py::test_d401_…` (agrega solo lo que falta, una vez, y el workflow sube el archivo).

## D-402 · El respaldo SQLite se ignora con cualquier nombre y ya no se renombra

- **Qué pasó:** para correr la suite como el CI, sin el respaldo local desactualizado, se renombraba `etl/datos.db` a `etl/datos.db.hold`. `.gitignore` solo ignoraba el nombre original, y el commit `8cc2da3` (D-391) subió el respaldo (34 MB) a GitHub. Lo borró de la versión actual el commit de D-393.
- **Decisión:** queda en el historial, por decisión del autor. Son precios públicos sin secretos, y sacarlo exigiría un push forzado. `.gitignore` ignora `etl/datos.db*`. El respaldo ya no se renombra: la suite «como el CI» corre en una copia aparte del repositorio (`git worktree`), que no lo tiene. Queda registrado como F-22, de categoría operación.
- **Pruebas:** `tests/test_quality_method.py` (el registro de fallas sigue numerado y completo).

## D-403 · Las palabras de los datos se leen en el idioma de la visita

- **Pedido del autor (4B):** que familias, canales, calidades y unidades, que vienen en español desde ODEPA, se lean en el idioma elegido, con una tabla de traducción.
- **Decisión:** `bi/data_terms.py` guarda la tabla: 7 familias (y los nombres cortos del Panorama), 8 canales, 61 calidades (las «Calibre N» por regla) y 3 unidades. El panel la usa al dibujar el Panorama y las páginas de canal; la base no cambia, y el estudio SQL y las descargas siguen mostrando lo guardado. Los nombres de productos no se traducen.
- **Pruebas:** `tests/test_data_terms.py` (cada familia, canal, calidad y unidad de la base tiene su inglés; solo cambia en una visita en inglés; un producto conserva su nombre).

## D-404 · «Último dato por canal» muestra una tarjeta por canal

- **Pedido del autor (4B):** que la página principal muestre todos los canales de los datos, cada uno en una tarjeta clicable entera.
- **Decisión:** una cuadrícula con una tarjeta por canal: primero el mayorista y después los canales al consumidor, de más a menos precios. Cada tarjeta muestra el nombre del canal y su fuente, su última semana como rango, la cantidad de precios de esa semana, la variación mediana de sus precios comparables frente a la semana anterior (el mismo cálculo del «Cambio típico» del Panorama) y su estado: «Al día», o «Atrasado» con el aviso «ODEPA aún no publica la semana X». Toda la tarjeta es el enlace a la página de su canal.
- **Pruebas:** `tests/test_channel_latest.py::test_d404_…` (una tarjeta entera por canal, cada una con su semana, sus precios, su variación y su estado; un clic abre el canal).

## D-405 · Cada canal se abre con el diseño y los pasos del Panorama

- **Pedido del autor (4B):** que un clic en una tarjeta abra la página de ese canal con el mismo diseño y los mismos pasos que el Panorama (región, familia y productos), en su propia última semana, sin duplicar lógica.
- **Decisión:** la página de un canal la dibuja el Panorama mismo. Mientras se dibuja, un «alcance» indica el canal, y las lecturas de datos del Panorama (precios nacionales, la foto de cada semana, las variaciones, las alertas, las regiones y las tendencias) lo usan. Con un canal, leen `latest_by_source` filtrada a ese canal y a sus dos últimas semanas, con las mismas reglas de las consultas K6 y K3: el precio nacional es el promedio de sus regiones, y el cambio usa solo las regiones con precio en ambas semanas. La memoria de cada lectura y el estado de los pasos son propios de cada canal, así que el Panorama nunca muestra cifras de un canal. La ruta dice «Negocio · BA y BI › Último dato por canal › Feria libre», y los enlaces del mapa y de las familias vuelven a la misma página de canal. Un canal no tiene la tabla de «Últimas semanas» (solo hay dos), y su aviso de atraso es el suyo.
- **Pruebas:** `tests/test_channel_latest.py::test_d405_…` (la página de un canal es el Panorama con ese canal y sus productos; el Panorama abierto después sigue con todos los canales; en la semana común, el precio nacional de un canal coincide con el de la consulta del Panorama).

## D-406 · Cobertura de familias, una sola escala y navegación de los canales

- **Pedido del autor (4B):** si un canal cubre solo algunas familias, una nota breve leída de los datos; la misma escala en las barras; tablas sin cortes.
- **Decisión:** cada tarjeta dice cuántas familias cubre («2 de 7 familias») cuando no son todas, y su variación es una barra que sale del centro, en la escala de la mayor variación entre las tarjetas. La página de un canal lo explica en su fila de contenido, leído de los datos: «Este canal publica 1 de las 7 familias: Pan.». Una tarjeta recarga la página como un documento de la carpeta, así que la vista se conserva una vez (D-357), nunca la de Autor. Los enlaces del mapa y de las familias de un canal apuntan a la misma página y se capturan sin recargar, como en el Panorama. Las tablas son las del Panorama: el texto pasa a otra línea en vez de cortarse.
- **Pruebas:** `tests/test_channel_latest.py::test_d406_…` (la escala común y la cobertura de las tarjetas, la nota de Panadería leída de la base y la navegación sin recarga).

## D-407 · Una pantalla también a 1280 × 800; a 1024 × 768 se desplaza sin cortes

- **Pedido del autor (4B, parte 5):** RNF-06 se extiende a 1.280 × 800, y en 1.024 × 768 se acepta el desplazamiento vertical sin cortes.
- **Decisión:** las páginas principales se ven enteras, sin desplazar, a 1440 × 790, a 1280 × 800 y a 1920 × 1000. La fila de contenido de D-398 sumó unos 40 px a las páginas con cifras o controles; las alturas que dependen de la ventana dejan ese espacio: el modelo estrella y sus otras vistas, el explorador de consultas SQL, el diagrama de despliegue del centro de operación, la seguridad y el stack. El diagrama de calidad acorta sus flechas verticales y su leyenda; bajo 1366 px de ancho, las tarjetas de «Precios e inflación» dejan la altura que toman los controles de arriba. Los diseños no cambian, solo su tamaño. La barra del Panorama ya no pasa a dos líneas bajo 1300 px, y bajo 860 px de alto las filas de las familias son más delgadas y la nota de la tabla de productos se oculta. A 1024 × 768 la página puede bajar, pero nada se corta ni se desplaza a lo ancho. Las páginas de lectura (método, ciclo git y documentos) siguen bajando, como antes. El PRD lo dice en RNF-05 y RNF-06, en español e inglés, y los scripts de medición miden 1280 × 800 por defecto.
- **Pruebas:** `tests/test_page_bar.py::test_d407_…` (el PRD, los tamaños de medición y las reglas de altura); la medición con Playwright da 0 px de desplazamiento en las páginas principales a los dos tamaños.

## D-408 · Elegida la familia, los pasos 1 y 2 se pliegan y la tabla de productos toma la pantalla

- **Pedido del autor (4B):** la tabla del paso 3 debe mostrar al menos 8 filas a 1440 × 790 y 6 a 1280 × 800; si hace falta, los pasos 1 y 2 se compactan después de elegir, como una línea con lo elegido y un botón «Cambiar». Igual en el Panorama y en cada canal.
- **Decisión:** cuando ya hay una región y una familia elegidas, el mapa y las familias dejan su lugar a dos líneas: «1 Región · Todo Chile · Cambiar» y «2 Familia · Frutas · +0,3 % · Cambiar». El paso 3 toma todo el ancho y la altura que dejan, y cada fila ocupa dos líneas: el producto, y debajo su calidad y unidad junto a «Ver cálculo». Bajo 860 px de alto, la línea fija sobre la tabla se oculta, como en D-407. «Cambiar» vuelve a abrir los pasos 1 y 2 sin bloquear nada (D-352); elegir una familia los pliega de nuevo, y elegir solo una región los deja abiertos para ver cómo se movieron sus familias. Cada canal guarda su propio estado (D-405). Con la base del 31-10-2026 se ven 9 filas a 1440 × 790 y 9 o 10 a 1280 × 800, sin desplazar, en español y en inglés.
- **Pruebas:** `tests/test_panorama_steps.py::test_d408_…` (las líneas plegadas, «Cambiar» y cuándo se vuelve a plegar, y la altura de la tabla), `tests/test_channel_latest.py::test_d408_…` (un canal se pliega con su propio estado) y la medición con Playwright de las filas visibles.

## D-409 · «Configuración», la consola del autor, reemplaza a «Enlaces del autor»

- **Pedido del autor (parte 3):** una consola simple, solo para el Autor, en «DevOps y seguridad», con tarjetas e íconos en una sola pantalla: el estado con color, «¿Qué pasó?» con los pasos de cada caso y el mantenimiento con fecha, leído del MANUAL sin duplicar y sin mostrar nunca el valor de un token.
- **Decisión:** la página «Configuración» tiene tres bandas.
  - **Estado:** seis tarjetas. El token de lanzamiento y el de solo lectura muestran los días que les quedan y su fecha, leída de GitHub. Se ven en ámbar con 15 días o menos, y en rojo si vencieron o faltan. Las otras cuatro son la última carga (roja si una ejecución posterior falló, ámbar con más de 8 días), el último informe de calidad (D-361), las pruebas del CI en main y las fuentes atrasadas (D-356).
  - **¿Qué pasó?:** cinco botones, uno por caso. Cada uno abre sus pasos en orden, marcados «Automático» o «Manual», con su enlace. Una página del panel se abre en la misma visita, porque una recarga cerraría la sesión de Autor; una dirección externa se abre en otra pestaña.
  - **Mantenimiento y guía:** renovar cada token antes de su fecha, las ramas viejas de informes contadas en GitHub, las líneas de enero de `agent/input.csv` (comprobadas en el archivo) y la copia de `agent/downloads`. Al lado, los enlaces de la guía de GitHub.
- **Fuente única:** los casos y sus pasos son la nueva sección 8.1 del MANUAL («Qué hacer en cada caso»), en español e inglés. Los enlaces salen de la guía de GitHub (8), que suma los dos enlaces de tokens, y las tareas, de «Qué se revisa y cuándo» (3).
- **Qué cambia en el resto del panel:** el aviso del token pasa de 14 a 15 días o menos en todo el panel y en los documentos. En «Centro de operación», el desplegable «Enlaces del autor» deja su lugar a «Cerrar acceso»: los enlaces viven en «Configuración», en el menú (D-398).
- **Cómo lee GitHub:** pide la fecha de cada token con ese mismo token, como ya hacía el aviso. Las ejecuciones de pruebas y las ramas las lee solo con el token de solo lectura (D-397). Guarda solo fechas, estados y frases de error, durante 5 minutos.
- **Pantalla:** cabe en una pantalla a 1440 × 790 y a 1280 × 800, en los dos idiomas (RNF-06).
- **Pruebas:** `tests/test_configuration.py`, que comprueba:
  - Solo el Autor la ve, y sin la clave no se consulta a GitHub.
  - Ningún token aparece, ni en la página ni en las cinco ventanas.
  - Los colores siguen fechas simuladas.
  - Los casos, pasos y enlaces son los del MANUAL en los dos idiomas, y en inglés no queda texto en español.
  - Las tareas de mantenimiento salen de los datos.

## D-410 · La alerta «Acción requerida» avisa cada token a 15 días o menos de vencer

- **Pedido del autor (parte 3):** aviso en la alerta del Autor 15 días antes de cada vencimiento.
- **Decisión:** al entrar como Autor, la alerta «Acción requerida» se abre también cuando un token está a 15 días o menos de vencer, o ya venció, aunque el informe de calidad esté en orden.
  - **Qué muestra:** primero los tokens, cada uno con su nombre («Token de lanzamiento», «Token de solo lectura»), los días que le quedan o el día en que venció, y dónde están sus pasos: «Configuración», caso «Un token vence o falta». Después vienen los indicadores del informe, como en D-335.
  - **Mismas reglas:** el aviso usa la regla y la fecha de las tarjetas de «Configuración» (D-409). Nunca muestra el valor del token.
  - **Qué no avisa:** un token que falta o que GitHub no deja leer no entra en la alerta, porque no se adivina su fecha; «Configuración» lo marca en rojo o «Sin leer».
- **Cuántas consultas:** la fecha se pide a GitHub como mucho una vez por hora, la misma consulta del aviso del token.
- **Documentos:** el MANUAL, en español e inglés, lo dice en «Qué se revisa y cuándo» (3) y en el paso automático del caso de los tokens (8.1).
- **Pruebas:** `tests/test_configuration.py::test_d410_…`, que comprueba:
  - La regla de los 15 días.
  - El texto y el color de cada token.
  - Con un token a 10 días, la alerta lo muestra antes del informe; a 40 días, no.
  - Nunca aparece el valor de un token.

## D-411 · Un dato de prueba con forma de clave dejaba en rojo la medición de calidad

- **Qué pasó:** después del push de D-409 y D-410, el job «medir» del workflow de calidad falló en main. El indicador `secretos_sin_clasificar` dio 1, y su aceptable es 0. Las pruebas de pytest, Ruff y mypy seguían en verde.
- **Causa:** una prueba de `tests/test_configuration.py` usaba un trozo de un identificador de commit como dato. La herramienta detect-secrets lo tomó por una posible clave. No había ningún secreto.
- **Decisión:** el dato de prueba pasa a `1234567`, que no tiene forma de clave. Antes de cada push se corre también la medición de calidad (`scripts/medir_calidad.py` y `scripts/verificar_calidad.py`), no solo las pruebas. Queda anotado como F-23 en `docs/calidad/plan_mitigacion.json`.
- **Pruebas:** la medición de calidad, corrida en una copia limpia del commit, deja `secretos_sin_clasificar` en 0; la suite completa sigue en verde.

## D-412 · «Flujo del sistema en vivo»: la arquitectura real, con sus mensajes y la carga en curso

- **Pedido del autor (parte 4, fase 1):** la arquitectura real del proyecto en una sola vista, con datos reales, visible para todos en «Stack y evidencia». Cada flecha dice quién pide, qué pide, qué responde y cuándo. Hay un modo en vivo, mensajes clicables y un botón para pausar, y se aplica la regla de animación del autor.
- **Decisión:** «Stack y evidencia» tiene dos vistas, «Herramientas» (la de siempre) y «Flujo del sistema en vivo».
  - **Piezas:** ODEPA, INE y PyPI; GitHub (Actions, la caché, el repositorio, issues y pull requests, el release «base-actual» y la API); el runner de la carga, con Python, SQLite, Parquet, dbt, DuckDB y pytest; Streamlit Community Cloud con la app, y el navegador. Una franja DevSecOps reúne el CI de cada push, la calidad, los secretos y tokens, el `github.token` del job y la puerta de Autor (D-393).
  - **Flechas:** solo rectas y en ángulo recto. Cada una lleva una etiqueta corta, para entender el diagrama sin hacer clic.
  - **Al hacer clic en una flecha:** qué pide, qué responde, cuándo, para qué y qué viajó en la última carga real, leído de `manifest.json`, `etl/datos.version` y la base.
  - **Lo deducido:** el único dato que no se puede leer es el redespliegue de Streamlit después de un push a main, y va rotulado «deducido».
- **Fidelidad:** el diagrama muestra lo que la carga hace de verdad. La base se sube al release y git recibe solo su puntero (D-270). Los secretos del panel viven en Streamlit; GitHub solo pone el token propio del job.
- **Animación:** sigue la regla del autor. Una pieza que trabaja sola, como dbt o pytest, se ilumina y pulsa. Una comunicación es un punto que viaja por la flecha, de quien pide a quien responde, y vuelve por el mismo camino con otro color. Cada paso de `semanal.yml` está asignado a sus piezas y flechas.
- **Modo en vivo:**
  - **Con una carga en curso:** el diagrama muestra su paso real y pregunta de nuevo cada 30 s.
  - **Sin carga en curso:** queda quieto, con la fecha y la hora de la última ejecución real, y con «Repetir la última ejecución». «Pausar» detiene la animación.
  - **Lecturas a GitHub:** solo con el token de solo lectura (D-397), o sin token. La respuesta se guarda 2 minutos con token y 10 sin él, para no gastar el límite de 60 consultas por hora.
- **Logs:** los ve solo el Autor, en «GitHub Actions». El diagrama no los lleva.
- **Pantalla:** el selector de vistas va en la fila de contenido (D-398). El mapa de «Herramientas» descuenta esa fila, así que las dos vistas caben en una pantalla a 1440 × 790 y a 1280 × 800 (RNF-06).
- **Pruebas:** `tests/test_live_flow.py`, que comprueba:
  - Cada flecha tiene sus cuatro datos en los dos idiomas.
  - Cada pieza existe en el repositorio.
  - Cada paso de `semanal.yml` mueve una pieza o una flecha.
  - El modo en vivo y el quieto, con respuestas simuladas.
  - No viajan logs ni tokens.
  - La animación cumple la regla del autor.
  - En inglés no queda texto en español.

## D-413 · La ventana «Ejecutar pipeline ahora» muestra el flujo en vivo enfocado en la ejecución

- **Pedido del autor (parte 4, fase 1):** al lanzar la carga, la ventana muestra arriba el diagrama en vivo, enfocado en la ejecución, y abajo el resumen por pasos con sus botones, como hoy. Debe ser responsiva, sin cortes ni desbordes, y usar el mismo componente y los mismos datos, sin duplicar lógica.
- **Decisión:** arriba de la ventana va el mismo dibujo de D-412, recortado a las fuentes, GitHub y el runner, sin el navegador ni la franja DevSecOps; la ventana pasa a ancho «large» para que se lea. Lo alimenta el seguimiento que la ventana ya hace cada 4 s (D-351), así que no hace consultas nuevas a GitHub. El marco cambia solo cuando cambia un paso, de modo que no se vuelve a dibujar en cada consulta. Debajo siguen el estado, el log y los botones «Minimizar», «Cancelar» y «Cerrar», sin cambios. Con menos de 900 px de ancho, el diagrama queda detrás del botón «Ver el diagrama» y los pasos van primero.
- **Pruebas:** `tests/test_live_flow.py::test_d413_…`, que comprueba:
  - Con una ejecución simulada en curso, la ventana muestra el diagrama en vivo, enfocado y con el paso real, sin el token.
  - El mismo marco sirve para el ancho y para la pantalla angosta.
  - Los botones de la ventana siguen ahí.

## D-414 · El SAD lleva la imagen fija del flujo del sistema

- **Pedido del autor (parte 4, fase 1):** una versión fija del flujo, en imagen, para el SAD.
- **Decisión:** el SAD suma la sección 3.3, «Flujo del sistema», en español e inglés. Trae el marcador `[[diagrama:flujo]]`, que dibuja la misma vista de D-412 sin script ni estado. Debajo de la imagen va el momento de la última carga real publicada, leído de `etl/datos.version`, y un enlace a la vista en vivo de «Stack y evidencia». Como todo diagrama de documento, no tiene fondo ni sombras y se imprime en hoja blanca (D-280).
- **Pruebas:** `tests/test_live_flow.py::test_d414_…` (el marcador en los dos idiomas, sin script y con la fecha de la última carga), más las pruebas de los diagramas de documentos (`tests/test_doc_diagrams.py` y `tests/test_documents.py`), que ahora cuentan la imagen nueva.

## D-415 · Las mini arquitecturas del flujo en vivo quedan como mejora futura

- **Pedido del autor:** la fase 2 de «Flujo del sistema en vivo» queda fuera; se registra como decisión y como mejora futura.
- **Decisión:** no se construye la fase 2: cada pieza abriría su nivel de zoom C4, con su definición, lo que hace aquí, por qué esa herramienta, lo que entra y lo que sale, y la mini arquitectura interna de GitHub, la carga semanal, dbt, la app y la seguridad. El flujo se queda como está en D-412 a D-414. El PRD lo anota en «Próximos pasos» (11), en español e inglés.
- **Pruebas:** no cambia el comportamiento; las pruebas de los documentos verifican que la vista enlazada existe en el menú.

## D-416 · Revisión de coherencia después de «Configuración» y del flujo en vivo

- **Pedido del autor (parte 5):** revisar que las páginas nuevas usen las mismas cifras, nombres y definiciones que el resto de la app y los documentos.
- **Decisión:** se corrigen cinco frases que ya no eran ciertas.
  - **Ayuda de «Acceso del autor»:** decía que abría «los enlaces de administración». Ahora dice que abre las páginas del autor, que viven en «Configuración» (D-409); tiene su inglés.
  - **SAD 3.2:** decía que `bi/control.py` era la única pieza que habla con la API de GitHub. Ahora dice que es la única que escribe (lanzar y cancelar), y que `bi/github_actions.py` y `bi/run_monitor.py` solo leen.
  - **SAD 8:** `GITHUB_TOKEN` lanza la carga, lee su estado y sus logs, y la cancela, como dice el MANUAL.
  - **PRD 7:** el orden del menú incluye «Precios e inflación» (D-398).
  - **Caso S-12 del plan de pruebas y de `bi/security_plan.py`:** suma la prueba de que «Configuración» no se abre sin la clave.
- **Pruebas:** las de los documentos y del plan de seguridad (`tests/test_documents.py`, `tests/test_doc_diagrams.py`) verifican que cada caso apunta a una prueba que existe y que el plan coincide con el código; `tests/test_i18n.py`, el inglés.

## D-417 · El SAD, el MANUAL, el PRD y el índice cuentan las páginas y reglas nuevas

- **Pedido del autor (parte 5):** agregar la página «Configuración», el diagrama nuevo y los cambios de seguridad al SAD, el MANUAL y el PRD, en español e inglés, con la misma redacción simple.
- **Decisión:**
  - **SAD:** la observabilidad (8) nombra el flujo en vivo; los secretos (8) describen «Configuración» y el aviso de los tokens a 15 días; la usabilidad (8) pide una pantalla también a 1280 × 800. La versión pasa a 3.5.
  - **MANUAL:** la ventana de la carga manual muestra el flujo enfocado (2), y «Stack y evidencia» dice en qué paso va una carga sin logs (4). La versión pasa a 3.5.
  - **PRD:** la vista Autor incluye «Configuración» (3.2). En Pantallas (7) se suman el Panorama que pliega sus pasos, las tarjetas por canal y las dos vistas de «Stack y evidencia». La versión pasa a 3.9.
  - **Índice de decisiones:** suma las diez grandes de esta etapa (D-393 a D-414) y pasa de 88 a 98 filas.
  - **CLAUDE.md:** nombra los módulos nuevos y el número de pruebas.
- **Pruebas:** las de los documentos verifican la misma estructura, los mismos identificadores y las mismas cifras en los dos idiomas (`tests/test_i18n.py`, `tests/test_documents.py`), y que cada vista enlazada existe.

## D-418 · La semana con 83,3 % de precios comparables se registra como incidente externo de la fuente

- **Qué pasó:** en la semana del 26 oct al 1 nov, el indicador `comparables_pct` dio 83,3 %, bajo su aceptable de 90 %. 145 de 868 precios no tienen comparación con la semana anterior.
- **Causa:** la fuente. De esos 145 precios, 73 llevaban más de 12 semanas sin precio, 58 entre 2 y 12 semanas, y 14 tenían precio la semana anterior, pero en otras regiones, así que no hay una comparación entre las mismas regiones. Son 141 frutas y hortalizas y 4 carnes. Lo calcula `python scripts/semanas_sin_precio.py --semana 2026-10-26`. El código hace lo correcto: sin precio anterior en las mismas regiones no hay variación, y no se inventa una.
- **Corrección (D-434):** la causa original decía que los 145 llevaban «más de 12 semanas sin dato». Era incorrecta: se escribió a partir de unos casos revisados a mano, sin medir cada serie, y solo 73 de 145 lo cumplen.
- **Decisión del autor:** el aceptable se queda en 90 %. Esta semana se registra como incidente externo de ODEPA en `docs/calidad/incidentes_externos.json`, con la respuesta prevista para un producto sin datos: se muestra «sin comparación», sin rellenar. En la próxima carga esos precios ya tendrán semana anterior; si el indicador no vuelve a 90 % o más, se revisa el código.
- **Pruebas:** `tests/test_quality_method.py` verifica que cada incidente diga qué pasó, la causa y la respuesta en los dos idiomas, con un tipo y una fuente conocidos.

## D-419 · La alerta «Acción requerida» oculta lo resuelto, lee la causa de un incidente externo y escribe cada idioma con sus palabras

- **Pedido del autor:** tres arreglos de la alerta del Autor.
  - «Pruebas que fallan» salía crítico, aunque ya se resolvió con D-380 y main está en verde.
  - «Precios con comparación válida» decía «Causa por determinar», aunque D-418 la registró como incidente externo.
  - En inglés decía «723 de 868».
- **Decisión:**
  - **Lo resuelto no sale:** una no conformidad cuyo estado el autor escribió como «resuelta» no aparece en la alerta, y no la abre. A pedido del autor, la de «Pruebas que fallan» del informe N° 7 queda en `docs/calidad/no_conformidades.json` con su acción (D-380) y el estado «resuelta», en español e inglés.
  - **De dónde sale la causa,** en este orden: la que escribe el registro de no conformidades; si no hay, el incidente externo del mismo indicador en el período del informe (desde el informe anterior hasta este); y si tampoco hay, el diagnóstico automático. La de los precios comparables dice ahora «Incidente externo de ODEPA (D-418)» y su causa.
  - **Cada idioma con sus palabras:** el diagnóstico une sus cifras con «de» en español y con «of» en inglés. Un informe no se edita: el informe N° 7 guarda su copia tal como se escribió, y la alerta vuelve a calcular el diagnóstico a partir de la medición del propio informe. Los informes siguientes ya se escriben bien.
- **Pruebas:** `tests/test_quality_method.py::test_d419_…`, que comprueba:
  - Con los registros reales, la alerta no muestra lo resuelto.
  - Muestra la causa del incidente.
  - No usa la palabra del otro idioma entre dos cifras (`\d de \d` en inglés, `\d of \d` en español).
  - La prueba del registro de no conformidades acepta la acción y el estado escritos en los dos idiomas.

## D-420 · «DevOps y seguridad» es solo del Autor; «Arquitectura de seguridad» pasa a «Stack y evidencia»

- **Decisión del autor:** la sección «DevOps y seguridad» solo existe para el perfil Autor. Usuario y Profesional no la ven en el menú, y si entran por la dirección, la página dice que no hay acceso. «Arquitectura de seguridad» pasa a «Stack y evidencia», visible para Profesional, sin mostrar valores secretos.
- **Decisión:**
  - **Páginas del Autor:** «Centro de operación», «GitHub Actions» y «Configuración».
  - **Menú:** para Usuario y Profesional, la sección desaparece entera; una sección sin páginas no se dibuja.
  - **Control en el servidor:** una sola función, `show_page`, dibuja cada página en la ventana y en las pruebas. Antes de dibujar una página del Autor comprueba en el servidor (la sesión) que la visita es del Autor, sin importar la dirección. Si no lo es, solo muestra «No tienes acceso a esta página: es solo para el perfil Autor.», con su inglés.
  - **«Arquitectura de seguridad»:** pasa al final de «Stack y evidencia», y su ruta dice «Stack y evidencia › Arquitectura de seguridad». El perfil de seguridad empieza el menú por esa sección.
  - **Lista de páginas:** el mapa de la app y el README nombran las páginas en el nuevo orden y dicen cuáles ve solo el Autor.
  - **Auditoría de inglés:** lee las páginas del Autor como las ve el Autor. Así aparecieron dos enlaces del Autor sin traducir en la pestaña «Operación» («Tokens de GitHub» y «Administrar la app»), que ya tienen su inglés.
- **Pruebas:**
  - `tests/test_menu_order.py::test_d420_…`: para Usuario y Profesional, cada página de DevOps por la dirección dice que no hay acceso y no dibuja nada propio, y el menú no tiene la sección. Profesional lee la seguridad en «Stack y evidencia». El Autor ve la sección entera.
  - Las pruebas del menú, la ruta, los vecinos, los perfiles y el encabezado siguen el orden nuevo.

## D-421 · Una sola clave en el panel, y cada acción del Autor se comprueba en el servidor

- **Decisión del autor:** hay una sola clave, la de entrar como Autor. Se quita el campo «Clave de control» y cualquier otra clave dentro del panel. Iniciar una ejecución queda directo; cancelar pide confirmar «¿Seguro?» en la página. Cada acción del Autor comprueba en el servidor que la sesión es del Autor.
- **Decisión:**
  - **Una clave:** la clave se escribe solo en «Elige tu vista» (D-369). El «Centro de operación» ya no tiene «Acceso del autor» ni campo de clave: es una página del Autor (D-420), así que muestra directo «Ejecutar pipeline ahora», «Recargar datos» y «Cerrar acceso». «Cerrar acceso» cierra la sesión del Autor, igual que cambiar de perfil (D-353).
  - **Lanzar:** la ventana de la ejecución ya no pide clave; lanza la carga de inmediato.
  - **Control en el servidor:** la ventana de la ejecución, la cancelación y «Recargar datos» vuelven a comprobar la sesión antes de actuar. Sin sesión del Autor, la ventana solo dice que no hay acceso, la cancelación no se envía y la recarga no ocurre.
  - **Se mantienen:** el límite de intentos (D-393), la caducidad a los 30 min, el cierre al cambiar de perfil, los tokens con permisos mínimos (D-397) y el registro de cada ejecución (GitHub la guarda como `workflow_dispatch`; el registro del servidor anota cuándo se lanzó o canceló).
  - **Regla:** `CLAUDE.md` agrega que las secciones de operación y seguridad interna se muestran solo al perfil administrador, con control de acceso en el servidor (el repositorio no tiene `AI_MASTER_METHODOLOGY.md`).
  - **Documentos:** el MANUAL (sección 7) y el mapa de la app cuentan la clave única, en los dos idiomas.
- **Pruebas:**
  - `tests/test_dashboard.py::test_d421_…`: como Autor no hay campo de clave y la ventana lanza la carga; el panel tiene un solo campo de clave; «Recargar datos» no actúa sin la sesión del Autor y la cancelación está detrás de `is_author()`.
  - `tests/test_dashboard.py::test_d202_…`: sin la sesión, la ventana de la ejecución no lanza nada ni pide clave.
  - `tests/test_operation_center.py::test_d165_…`: el Centro de operación del Autor muestra la ejecución manual sin campo de clave.

## D-422 · El diagrama de despliegue muestra el release aparte y los tres workflows

- **Pedido del autor:** en «Centro de operación › Despliegue», separar el release en su propia caja con `datos.duckdb` y dejar en el repositorio solo `datos.version`; agregar `calidad.yml` y mostrar que `pruebas.yml` corre aparte, en cada push; quitar la franja blanca a la derecha de Streamlit.
- **Decisión:**
  - **Release:** un entorno propio, «Release «base-actual»», con `datos.duckdb` y su tamaño. El repositorio (rama `main`) guarda el código, el puntero `datos.version` y `manifest.json` (D-270). La carga sube la base al release («gh release upload») y el panel la descarga de ahí: las dos flechas están dibujadas.
  - **Workflows:** el runner de la carga tiene `semanal.yml` y, después de cada carga, `calidad.yml`, que propone el informe como pull request. Las pruebas de cada push corren en otro runner, aparte: `pruebas.yml` (lint y pytest en Python 3.11 y 3.12) y `calidad.yml`, que solo mide. Una flecha va del repositorio a ese runner.
  - **Tamaño:** el dibujo es más ancho (1210 de ancho), no más alto, así que sigue cabiendo en una pantalla.
  - **Franja:** la cara lateral de cada caja 3D se dibujaba con el borde blanco del texto, y en la caja de Streamlit Cloud, la última a la derecha, se leía como una franja blanca. Las caras lateral y superior llevan ahora el borde gris suave del resto del dibujo.
  - **Textos:** el panel guarda «tokens y clave» (D-397, D-421); la nota del panel dice que lanza la carga en la sesión del Autor. Todo con su inglés.
  - **Documentos:** el SAD (7) cuenta las dos máquinas, los tres workflows y la descarga desde el release, en los dos idiomas (versión 3.6).
- **Pruebas:** `tests/test_deployment.py::test_d422_…`: el release tiene `datos.duckdb` y el repositorio no; el runner de la carga tiene `semanal.yml` y `calidad.yml`, y el de cada push `pruebas.yml` y `calidad.yml`; las flechas al release, desde el release y hacia las pruebas existen; ninguna caja se sale del dibujo.

## D-423 · «Volver» lleva a la página anterior de la visita, con su estado

- **Pedido del autor:** la flecha ← del encabezado debe volver a la página anterior de esta sesión, con su estado (un canal abierto, los pasos del Panorama). Solo sin página anterior vuelve a «Elige tu vista». Con un historial simple en la sesión, sin recargar la página.
- **Causa:** «Volver» guardaba el recorrido en el navegador y cambiaba la dirección con una recarga completa. La recarga abría una sesión nueva sin la vista elegida, así que la visita caía siempre en «Elige tu vista».
- **Decisión:**
  - **Historial en la sesión:** cada página que se dibuja agrega un paso con su ventana, sus parámetros propios (página, canal, familia) y su estado: los filtros del informe y los pasos del Panorama, cada canal con los suyos. Volver a dibujar la misma página solo actualiza su estado. Guarda hasta 30 pasos.
  - **Volver:** al hacer clic, la página actual sale del historial, la anterior recupera su estado y se abre con `st.switch_page`, en la misma sesión y sin recargar. Sin página anterior, se abre «Elige tu vista».
  - **Recargas de la app:** una tarjeta de canal y un documento de la carpeta recargan la página (D-406). El mismo mecanismo que conserva la vista en esas recargas (D-357) lleva también el historial, aunque la dirección ya nombre la vista; al volver, solo se aceptan pasos bien formados y claves de estado conocidas.
  - Se retira el script que cambiaba la dirección para volver.
- **Pruebas:** `tests/test_page_bar.py::test_d423_…`: desde «Modelo de datos», «Volver» abre el Panorama con sus pasos como estaban y la vista intacta; sin página anterior abre «Elige tu vista»; el historial que llega por una recarga solo toma pasos bien formados y queda antes de la página que la recarga abrió.

## D-424 · Los escenarios clave del SAD muestran todo lo que puede hacer cada actor

- **Pedido del autor:** el diagrama de escenarios del SAD se veía pobre: cinco filas sueltas, con el Autor repetido y sin decir qué ve cada perfil. Debe mostrar todos los privilegios reales de cada actor, sin resumir, tomando como ejemplo un árbol con el sistema arriba y una columna por actor.
- **Decisión:**
  - **Forma:** un árbol. GreenOcean arriba, y de él cuatro columnas: Usuario, Profesional, Autor y GitHub Actions. Bajo cada actor, una línea por acción con su ícono, lo que hace (en negrita), la parte del sistema que la atiende (en color) y su referencia (en gris). Sin cajas ni discos: íconos de línea, texto y líneas rectas (D-297).
  - **Contenido, leído de la app:** el Usuario, sus seis páginas de negocio, las fuentes y el paso a Profesional sin clave. El Profesional suma ingeniería, stack, calidad, git y la carpeta de documentos. El Autor suma la entrada con la única clave, lanzar, cancelar, recargar, los logs, el aviso de carga fallida, «Acción requerida», «Configuración», la aprobación del informe de calidad y el cambio de código y secretos. GitHub Actions: la carga de cada martes, la publicación solo de una carga válida, el informe semanal, la medición de calidad y las pruebas de cada push.
  - **Límites:** bajo cada columna, en cursiva, lo que ese perfil no alcanza; bajo el Autor, que cada acción se comprueba en el servidor (D-421).
  - **Documentos:** el SAD (2.1) lo explica en una frase, en los dos idiomas (versión 3.7).
- **Pruebas:** `tests/test_doc_diagrams.py::test_d424_…`: cada página del menú aparece en la columna del perfil que la ve y en ninguna otra; las páginas del Autor y sus acciones están en su columna; los tres workflows nombrados existen.

## D-425 · Los escenarios clave son un mapa del panel web por perfil, con herencia

- **Decisión del autor:** reemplazar el árbol de D-424 por un mapa que el autor diseñó: los perfiles a la izquierda, el panel web al centro con una franja por perfil y, a la derecha, la Base DuckDB y GitHub Actions. Lo prefiere al árbol lineal, aunque use recuadros.
- **Errores corregidos del diseño original:**
  - La flecha «lanza» iba a `pruebas.yml`; el panel lanza `semanal.yml` (`bi/control.py`, `WORKFLOW_FILE`).
  - `calidad.yml` también mide en cada push, no solo después de cada carga.
  - «Stack y evidencia» (Flujo del sistema en vivo) también lee el estado de GitHub con `GITHUB_READ_TOKEN`, para el Profesional; faltaba esa flecha.
  - Nombres del menú: «Insights» (no «Insights de la semana») y «GitHub Actions» (no «GitHub Actions en el panel»).
  - Faltaban la entrada del Autor (secreto `CONTROL_CODE`, espera tras 3 fallos, sesión de 30 min, RF-09), RF-07 junto a «Ejecutar pipeline ahora», el «Índice de decisiones» en los documentos y «Ver todo el proyecto» en el Usuario.
  - Varios textos se salían de su recuadro o se montaban; ahora el dibujo es una grilla que ajusta el texto.
- **Forma:** cada perfil queda en la fila de su franja del panel, con su flecha («ve», «además ve», «además opera») y su herencia («hereda todo · sin clave», «hereda todo · con clave»). Las flechas a GitHub Actions nombran el token que usan.
- **Documentos:** el SAD (2.1) explica el mapa y la herencia, en los dos idiomas (versión 3.8).
- **Pruebas:** `tests/test_doc_diagrams.py::test_d425_…`: cada página del menú está en la franja del primer perfil que la ve y en ninguna anterior; el panel lanza `semanal.yml`; los tres workflows existen; cada referencia P-x o RF-x del dibujo existe en el PRD.

## D-426 · «Base servida» pasa a «Base DuckDB · etl/datos.duckdb», y los contenedores muestran el release y los tokens

- **Pedido del autor:** en el diagrama «Contenedores (C4, nivel 2)» del SAD, usar el mismo nombre que en los escenarios (D-425) y mostrar cómo el panel web y la carga semanal usan GitHub.
- **Decisión:**
  - **Nombre:** «Base servida» pasa a «Base DuckDB · `etl/datos.duckdb`» en el diagrama y en todo el SAD, también en sus figuras de componentes, capas y despliegue; en inglés, «DuckDB database». El historial de versiones conserva el nombre de su época. Los enlaces al ADR-35 no cambian, porque apuntan a su título.
  - **Flechas nuevas:** Carga semanal → GitHub, «sube la Base DuckDB al release «base-actual»»; Panel web → GitHub, «lanza y cancela cargas (`GITHUB_TOKEN`)» y «lee estado de workflows (`GITHUB_READ_TOKEN`)». La flecha del panel web a la Base DuckDB dice ahora que la lee desde el release «base-actual», en solo lectura.
  - **Respaldo:** «Respaldo · `etl/datos.db`», con una línea que dice para qué sirve: los mismos precios calculados sin dbt, para comprobar que dbt no cambió ninguna cifra (la prueba de paridad).
  - **Etiquetas de dos o más líneas:** el dibujo de figuras acepta etiquetas partidas en líneas y, en una línea vertical, ponerlas a su izquierda, para que no se monten sobre otras.
  - **Documentos:** el SAD (versión 3.9) y el Glosario (versión 2.5), en los dos idiomas.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d297_…` busca los nombres nuevos, las 12 flechas y sus etiquetas con los dos tokens; `tests/test_documents.py::test_d248_the_file_sizes_…` lee el tamaño «en la Base DuckDB».

## D-427 · Abrir o imprimir un documento ya no vuelve a «Elige tu vista», tampoco para el Autor

- **Reporte del autor:** al abrir un documento de la carpeta como Autor, la app volvía a «Elige tu vista» y pedía la clave; al imprimirlo, volvía a pasar y la impresión salía con esa ventana. La vista se elige una sola vez por visita y solo se vuelve a ella con «Vista: … · Cambiar».
- **Causa:** abrir un documento, imprimirlo (que cambia al tema claro, D-280) y cambiar la base del tema recargan la página, y cada recarga abre una sesión nueva. D-357 conserva la vista en esas recargas, pero nunca la del Autor, para que el navegador no guardara nada que abriera esa vista sin la clave. Además, la impresión salía a los 3 segundos aunque «Elige tu vista» siguiera abierta.
- **Decisión:**
  - **Ticket del Autor:** mientras la sesión es del Autor, el servidor emite un ticket aleatorio (`secrets.token_urlsafe`), lo guarda en su memoria con el mismo vencimiento de la sesión (30 min sin actividad, D-395) y lo renueva en cada ejecución. Antes de una recarga de la app, la pestaña lo guarda junto con la vista; después, el servidor lo canjea una sola vez y, si es suyo y no venció, la sesión nueva vuelve a ser del Autor sin pedir la clave.
  - **Seguridad:** el navegador solo guarda un número que el servidor emitió; uno inventado, uno ya usado o uno vencido no abre nada. Salir de Autor o cambiar de perfil (D-353) anula el ticket. La recarga que hace el lector (F5) sigue pidiendo la vista (D-340).
  - **Impresión:** el documento se imprime solo cuando «Elige tu vista» ya no está en la página; si sigue abierta a los 20 segundos, no se imprime nada.
  - **Documentos:** RF-09 del PRD y el MANUAL (7), en los dos idiomas.
- **Pruebas:** `tests/test_app_reloads.py::test_d427_…`: el Autor vuelve con un ticket emitido por el servidor, y no con uno usado, inventado o vencido (D-428 lo deja valer hasta que vence la sesión); solo una sesión de Autor tiene ticket y salir lo anula; la impresión espera a que «Elige tu vista» desaparezca. En el navegador, como Autor: abrir el PRD desde la carpeta e imprimirlo no muestra «Elige tu vista» y la vista sigue siendo «Autor».

## D-428 · Imprimir un documento conserva la vista también en la app publicada

- **Reporte del autor:** en la app publicada, imprimir un documento seguía volviendo a «Elige tu vista», aunque en local D-427 funcionaba.
- **Causa:** Streamlit Community Cloud dibuja la app dentro de un marco (iframe) y, tras una recarga de la app, carga la página dos veces: primero el marco y después la página entera. La primera carga leía y borraba la vista guardada (D-357) y canjeaba el ticket del Autor (D-427); la segunda ya no encontraba nada y mostraba «Elige tu vista». Además, el guion de impresión de D-427 tenía un signo «menor que», que `st.html` puede descartar (D-280); la prueba `test_d280_the_pdf_is_a_white_sheet_in_every_theme` lo detectó en el CI.
- **Decisión:**
  - **Vista guardada:** cada página la lee una sola vez (una marca en la página) y la deja 30 segundos, para que la segunda carga también la encuentre; pasado ese tiempo se borra, y una recarga del lector vuelve a pedir la vista (D-340).
  - **Ticket del Autor:** la sesión nueva lo toma como suyo y vale hasta que vence la sesión del Autor (30 min sin actividad, D-395); salir de Autor o cambiar de perfil lo anula. Sigue siendo un número aleatorio que solo el servidor emite.
  - **Impresión:** el guion espera sin el signo «menor que».
  - **Documentos:** RF-09 del PRD (3.11) y el MANUAL (7, 3.7), en los dos idiomas; ocurrencia en F-18.
- **Pruebas:** `tests/test_app_reloads.py::test_d427_…` (la segunda carga vuelve como Autor; uno anulado, inventado o vencido no) y `test_d428_each_page_reads_the_kept_view_once_and_leaves_it_for_the_second_load_of_the_cloud`. En la app publicada, con Playwright: abrir el PRD e imprimirlo.

## D-429 · Los escenarios clave del SAD tienen el tamaño de los demás diagramas

- **Reporte del autor:** el mapa de escenarios (D-425) era demasiado alto (unos 1.240 px a 960 px de ancho, el doble que los contenedores) y ocupaba mucho espacio.
- **Decisión:**
  - La Base DuckDB y GitHub Actions pasan a una fila bajo el panel web, que así usa todo el ancho; sus flechas son verticales: «lee» de la Base DuckDB, «lanza y cancela» con `GITHUB_TOKEN` (Autor) y «estado y logs» con `GITHUB_READ_TOKEN` (logs, solo el Autor); «publica» va de GitHub Actions a la Base DuckDB.
  - Las páginas del Usuario se acomodan en filas según su largo; el nombre y el detalle de cada página van en la misma línea.
  - La protección pasa al encabezado del panel y a «Entrada»; el rol, al título del Profesional; «Fuera del panel», a la sección del Autor; la leyenda, bajo los perfiles.
  - Nada se quitó: las mismas páginas, acciones, secretos, workflows y referencias del PRD. Mide unos 760 px a 960 px de ancho, en los dos idiomas, sin desborde a 820 px.
  - **Documentos:** SAD 3.10 (2.1), en los dos idiomas.
- **Pruebas:** `tests/test_doc_diagrams.py::test_d429_…` y las de D-425, que siguen exigiendo cada página del menú en la sección de su perfil.

## D-430 · La vista se elige una vez por pestaña: ninguna recarga la vuelve a pedir

- **Reporte del autor:** como Autor, el enlace «Abrir el informe» del aviso «Acción requerida» llevaba a «Elige tu vista». Una vez dentro, la ventana no debe volver a aparecer, salvo que el lector toque el botón de la vista.
- **Causa:** D-357 guardaba la vista solo antes de las recargas que la app conocía (un documento, imprimir, una tarjeta de canal, el tema). Un enlace común, como el del aviso, o F5 recargaban sin guardarla, y la sesión nueva pedía la vista.
- **Decisión:**
  - Cada ejecución guarda la vista, el rol, el historial de «Volver» y el ticket del Autor en la pestaña (`sessionStorage`); toda recarga de la pestaña la encuentra, sea un enlace, el aviso, F5 o una recarga de la app. Esto reemplaza la regla de D-340 de que la recarga del lector pide la vista.
  - «Elige tu vista» aparece una vez por pestaña; después, solo «Vista: … · Cambiar» o el logo (D-373) la abren. Una pestaña nueva o una visita nueva la piden.
  - **Seguridad:** sin cambios en el Autor: la pestaña guarda solo el ticket que emite el servidor, que vence con su sesión (30 min sin actividad, D-395) y que «Cerrar acceso» o cambiar de perfil anulan. Ninguna dirección abre la parte del autor.
  - **Documentos:** RF-09 del PRD (3.12) y el MANUAL (7, 3.8), en los dos idiomas; ocurrencia en F-18.
- **Pruebas:** `tests/test_app_reloads.py::test_d430_every_run_keeps_the_view_so_no_reload_of_the_tab_asks_for_it_again`, y las de D-357, D-427 y D-428 al día. En el navegador, como Autor: el enlace del aviso, F5 dos veces y «Centro de operación» siguen en «Autor»; una pestaña nueva pide la vista.

## D-431 · Un solo informe de calidad numerado: el semanal de los datos, en cuatro páginas

- **Diagnóstico del autor, verificado:**
  - El informe mezclaba tres frecuencias: según `metas.json`, 8 indicadores de código se miden «en cada push», 3 de datos «en cada carga semanal» y 1 «cada día». Por eso hubo 7 informes entre el 26 y el 31 de octubre.
  - «Qué medimos y por qué» y «Cómo se mide» repetían en cada informe la metodología, que no cambia entre informes y que el SQAP define (con el detalle por indicador en `metas.json`).
  - El N° 7 grabó como crítico un estado de unos minutos: la base de la carga llegó a main antes que los arreglos de D-380.
  - El denominador cambiaba: N° 1 = 6/8, N° 2 = 8/11, N° 3 = 10/11, N° 7 = 10/12. Los 12 indicadores eran siempre los mismos; lo que cambiaba era cuántos se habían medido.
- **Decisión:**
  - **Por frecuencia:** el código se verifica en el CI de cada push (pasa o falla en GitHub Actions) y no genera informe. El único informe numerado es el semanal de los datos, con los 3 indicadores de cada carga: pruebas de datos dbt superadas, precios con comparación válida y filas rechazadas (`quality_metrics.WEEKLY_INDICATORS`). Los días desde la última carga quedan en el panel.
  - **Solo tras una carga en verde:** `calidad.yml` propone el informe solo en `workflow_run` de `semanal.yml` con conclusión `success`, es decir, con sus pruebas pasadas y la base publicada; nunca a mano ni a mitad de un despliegue.
  - **El SQAP es la metodología:** el informe deja «Qué medimos y por qué», «Cómo se mide» y el anexo técnico. Su portada dice «Medido según SQAP vX.Y», con enlace, y cada informe guarda esa versión (`sqap`).
  - **Una tabla de no conformidades e incidencias:** indicador, estado, causa, disposición y fecha; las de ese informe, las abiertas de informes anteriores de la misma serie y los incidentes externos de su período. Esto reemplaza el conteo de incidentes de D-334: la causa y la respuesta de un incidente se leen en el informe.
  - **La comparación avisa** si los dos informes no miden los mismos indicadores, y compara solo los que están en ambos.
  - **Dos series:** los 7 informes de `docs/calidad/informes/` no se editan; son la serie de construcción y se nombran C-1 a C-7. La serie semanal empieza en el N° 1, en `docs/calidad/informes/semanales/`. El panel muestra una serie a la vez («Semanal» o «Construcción (C-1 a C-7)»), la dirección nombra el informe como `informe=1` o `informe=C7`, y cada no conformidad nueva guarda su serie. Hasta el primer informe semanal, el panel y la alerta siguen leyendo C-7.
  - **Cierre de la serie de construcción:** a pedido del autor, las 10 no conformidades abiertas de C-1 a C-7 se cierran en bloque, con la disposición «cerrada al término de la serie de construcción; los indicadores se remiden en la serie semanal desde el N° 1» y el estado «cerrada»; sus causas y el resto del histórico no se tocan. «Cerrada» cuenta como «resuelta» (`is_resolved`): no sale en la alerta ni en la tabla de informes posteriores. Por eso, hasta el primer informe semanal, la alerta «Acción requerida» ya no muestra los precios comparables de C-7.
  - **Impresión compacta:** al imprimir, las tablas usan letra de 11,5 px y menos relleno, para que los 12 indicadores de la serie de construcción quepan en una página.
  - **Resultado:** el PDF semanal tiene 4 páginas (portada, resultados, comparación e incidencias), y también cada informe C-1 a C-7, en los dos idiomas; el N° 7 con el diseño anterior tenía 11 en A4 horizontal.
  - **Documentos:** SQAP 1.5 (8) y MANUAL 3.9 (2), en los dos idiomas; la figura del ciclo de calidad dice «Informe semanal».
- **Pruebas:** `tests/test_quality_method.py::test_d431_…` (cuatro páginas, el enlace al SQAP con su versión, la tabla única, solo los indicadores de datos, el aviso de la comparación, los nombres C-1 a C-7 y la serie de cada no conformidad) y las de D-331, D-333, D-335, D-347 y D-363 al día.

## D-432 · La dirección de un informe lo abre también después de una recarga

- **Defecto preexistente:** una dirección con `informe=…` (la del enlace «Abrir el informe» del aviso «Acción requerida», o una compartida) no abría el informe cuando la página se recargaba. La primera ejecución de la recarga todavía no tiene la vista: llega un momento después, desde el JavaScript que la guarda en la pestaña (D-357, D-430). Esa primera ejecución leía y borraba `informe=…`, y el rerun que trae la vista cerraba la ventana del informe. Se encontró al revisar D-431.
- **Decisión:** «Método y calidad» lee `informe=…` solo cuando la sesión ya tiene su vista; hasta entonces, la dirección espera. Se lee una sola vez, como antes.
- **Pruebas:** `tests/test_app_reloads.py::test_d432_a_report_address_opens_its_report_after_the_reload_brings_the_view_back` imita la vista que llega en la segunda ejecución: falla sin el arreglo y pasa con él. En el navegador, `informe=C3` abre el informe C-3 con sus 4 páginas.

## D-433 · El aceptable de los precios comparables se calibra con la historia: 81 %, el percentil 5

- **Pedido del autor:** el aceptable de 90 % de `comparables_pct` está sobre la mediana histórica, y el Informe semanal de calidad N° 1 nacería con la misma alerta falsa que C-7. Hay que corregirlo antes de la carga del martes 3-11.
- **Evidencia:** medido semana a semana sobre la Base DuckDB, con el cálculo de `scripts/medir_calidad.py`, en 251 semanas (10-01-2022 a 26-10-2026): mediana 89,3 %, percentil 5 81,2 %, percentil 10 84,6 %; 145 semanas bajo 90 % y 12 bajo 81 %. La tabla completa está en ADR-36.
- **Decisión:** el aceptable pasa de 90 % a 81 % en `docs/calidad/metas.json`, y la meta también; el margen crítico sigue en 10 puntos. Es una calibración, no una relajación del estándar: el 90 % se había fijado sin referencia a la distribución histórica. La meta acompaña al aceptable como en los otros 11 indicadores: con la meta en 90 %, el indicador habría quedado en «aviso» más de la mitad de las semanas, y la regla de lectura del panel («mientras la barra no pase la raya, cumple», D-337) dejaría de ser cierta.
  - Los informes C-1 a C-7 no se vuelven a evaluar: son registros cerrados y guardan el aceptable de 90 % con que se midieron, bajo el SQAP vigente entonces.
  - **Documentos:** ADR-36 (ADR 3.3) y SQAP 1.6 (6), en los dos idiomas; la línea de tiempo de las decisiones suma ADR-36.
- **Pruebas:** `tests/test_quality_method.py::test_d433_the_comparable_prices_acceptable_is_the_fifth_percentile_and_the_closed_reports_keep_theirs`, y las de D-330 y D-248 al día (81 % y 12 ADR).

## D-434 · La causa del incidente de D-418 se corrige con las cifras medidas

- **Qué pasó:** la causa registrada en D-418 y en `docs/calidad/incidentes_externos.json` decía que los 145 precios sin comparación de la semana del 26 oct «llevaban más de 12 semanas sin precio». La alerta «Acción requerida» y el informe C-7 la mostraban como cierta.
- **Por qué era incorrecta:** se escribió a partir de unos casos revisados a mano, sin medir cada serie. Medida serie por serie sobre la Base DuckDB, 73 llevaban más de 12 semanas sin precio, 58 entre 2 y 12, y 14 tenían precio la semana anterior, pero en otras regiones. El reparto por grupo sí era correcto: 141 frutas y hortalizas y 4 carnes.
- **Decisión:**
  - **Texto corregido:** D-418 y el incidente dicen las cifras medidas; D-418 anota que la causa original era incorrecta y por qué. Nada más del histórico cambia: el informe C-7 no guarda la causa, la lee del registro.
  - **Reproducible:** `scripts/semanas_sin_precio.py` calcula, para una semana, cuánto llevaba sin precio cada precio sin comparación, con el mismo código del indicador (`k6_national_weekly_price` y `alerts.add_weekly_variation`). `python scripts/semanas_sin_precio.py --semana 2026-10-26` da 145 de 868: 14, 58 y 73.
  - **Regla:** una causa con cifras se escribe con la medición que la produce, nunca a ojo.
- **Pruebas:** `tests/test_quality_method.py::test_d434_the_cause_of_the_incident_is_the_measured_one` vuelve a medir la semana del 26 oct con el script y compara con el texto del incidente.

## D-435 · Cada dependencia tiene una versión máxima

- **Pedido del autor:** en `requirements.txt` y `requirements-pipeline.txt`, streamlit, pandas, dbt-core, dbt-duckdb y pyarrow no tenían tope. Una versión nueva ya rompió dos cargas: certifi (D-164) y DuckDB 2.0.0 (D-227).
- **Decisión:** cada dependencia tiene un tope justo encima de la versión que funciona hoy. Para Python 3.11 en Linux, como en el CI, pip resuelve hoy streamlit 1.66.1, pandas 3.1.0, dbt-core 1.12.0, dbt-duckdb 1.11.1, pyarrow 26.0.0, duckdb 1.5.6, requests 2.34.2 y pytest 9.2.0; todas salieron antes del CI en verde del 01-11-2026. Los topes son `streamlit<1.67`, `pandas<3.2`, `dbt-core<1.13`, `dbt-duckdb<1.12`, `pyarrow<27`, `requests<3` y `pytest<10`; `duckdb<2` ya estaba (D-227).
  - Streamlit y dbt quedan topados en su versión menor siguiente, porque el panel usa partes internas de Streamlit (los componentes v2, los `data-testid`) y dbt cambia de comportamiento entre versiones menores; pandas, pyarrow, requests y pytest, en su versión mayor o menor siguiente.
  - Hoy los topes no cambian lo que se instala: pip resuelve las mismas versiones con y sin topes (`pip install --dry-run --python-version 3.11`, para la plataforma de los runners de GitHub). Solo frenan una versión futura.
  - Una versión nueva entra solo cuando el autor sube su tope con un push y el CI la prueba antes de la carga siguiente.
  - **Documentos:** MANUAL 3.10 (4), en los dos idiomas.
- **Pruebas:** `tests/test_documents.py::test_d435_every_dependency_has_a_maximum_version`.

## D-436 · El pull request del informe de calidad se fusiona solo si el código está en su aceptable

- **Pedido del autor:** que el informe no se congele. Si nadie acepta el pull request «Actualizar medición de calidad», «Método y calidad» y la alerta se quedan en el último informe aceptado.
- **Decisión:**
  - **Fusión automática:** después de abrir el pull request, `calidad.yml` lo fusiona (squash) y borra su rama si el paso «Comparar con los aceptables» terminó bien, es decir, si los indicadores de código están en su aceptable. Si no, queda abierto para el autor. Hasta ahora, esta fusión estaba escrita en comentarios, con `--auto`.
  - **Sin «Allow auto-merge»:** la fusión es directa, no la automática de GitHub. `--auto` solo espera a las verificaciones obligatorias de una regla de rama; sin esa regla no tiene a quién esperar, y un pull request abierto por `GITHUB_TOKEN` no hace correr `pruebas.yml`. Basta el permiso que ya existe: Settings → Actions → General → «Read and write permissions» y «Allow GitHub Actions to create and approve pull requests». Si una regla de rama de main rechaza la fusión, el pull request queda abierto y la ejecución lo avisa; la fusión se reintenta tres veces, porque un pull request recién abierto puede tardar unos segundos en estar listo.
  - **Un número, un pull request:** el número del informe es el siguiente al último fusionado en main. Si un informe sigue abierto cuando llega el siguiente (porque el código estaba fuera de su aceptable), el workflow lo cierra con la nota «Reemplazado por el informe de …», borra su rama, y el nuevo toma el mismo número. Nunca hay dos pull requests con un número, y el cerrado queda en GitHub como registro.
  - **Documentos:** SQAP 1.7 (8 y 11) y MANUAL 3.11 (8 y 8.1), en los dos idiomas; la figura del ciclo de calidad y el calendario de «Método y calidad».
- **Pruebas:** `tests/test_quality_method.py::test_d436_the_report_is_merged_by_itself_only_with_the_code_in_range_and_an_open_one_is_replaced`.

## D-437 · Una no conformidad de la serie semanal se cierra sola cuando su indicador vuelve al aceptable

- **Pedido del autor:** que las no conformidades no queden abiertas para siempre cuando el problema ya pasó.
- **Decisión:**
  - Al escribir un informe semanal, `scripts/informe_calidad.py` revisa las no conformidades abiertas de la serie semanal de informes anteriores. Si su indicador está «Cumple» o «Aviso» en el informe nuevo, les pone el estado «resuelta automáticamente, informe N° x» (y su inglés). La causa y la acción que escribió el autor se conservan.
  - Solo la serie semanal, desde el N° 1. Las 10 de la serie de construcción ya se cerraron en bloque (D-431) y no se tocan.
  - Un indicador sin medición no cierra nada: tiene que volver a medirse dentro de su aceptable. Una no conformidad abierta por el mismo informe solo la cierra un informe posterior. Una segunda ejecución no cierra nada más.
  - El cierre viaja en el mismo pull request del informe (D-436), así que queda en git como cualquier otro cambio.
  - **Documentos:** SQAP 1.8 (8), en los dos idiomas, y la nota de `no_conformidades.json`.
- **Pruebas:** `tests/test_quality_method.py::test_d437_a_weekly_non_conformity_closes_by_itself_when_its_indicator_is_back_and_the_construction_series_is_untouched`.

## D-438 · Al abrir el «Informe semanal», se cierra el anterior

- **Pedido del autor:** que los issues «Informe semanal» no se acumulen. Cada martes se abría uno nuevo y nadie cerraba los anteriores.
- **Decisión:**
  - El paso «Publish the weekly report» de `semanal.yml` abre el issue nuevo y, después, cierra cada issue abierto cuyo título empieza por «Informe semanal », salvo el nuevo, con el comentario «Reemplazado por el informe de esta semana: …», que enlaza al nuevo.
  - Se cierra después de abrir el nuevo, así nunca queda la semana sin informe abierto. El primer martes cierra también los que hoy sigan abiertos.
  - Se eligió cerrar en vez de editar un único issue: cada semana queda como su propio registro, con su fecha y su enlace, y solo el último queda abierto.
  - El workflow ya tenía el permiso `issues: write`; no se agrega ninguno.
  - **Documentos:** PRD 3.13 (RF-08) y MANUAL 3.12 (3), en los dos idiomas.
- **Pruebas:** `tests/test_prd_traceability.py::test_rf08_the_new_weekly_report_closes_the_previous_ones`.

## D-439 · Dos riesgos de abandono quedan en el registro de riesgos, con su mitigación propuesta

- **Pedido del autor:** documentar, sin implementar, dos riesgos de que el sistema deje de funcionar si nadie lo opera.
- **Riesgos:**
  - **Workflows desactivados por inactividad:** GitHub desactiva los workflows programados de un repositorio público tras 60 días sin actividad. Su documentación no define qué cuenta como actividad ni si sirve el commit semanal del bot. Si pasa, `semanal.yml` deja de correr los martes y el panel no lo avisa.
  - **App dormida:** Streamlit Community Cloud duerme la app por falta de visitas, no por falta de commits. El visitante ve la pantalla de la app dormida y debe despertarla.
- **Mitigación propuesta, sin implementar:**
  - No depender de la regla de GitHub: «Configuración» leería el estado de `semanal.yml` en la API (`active` o `disabled_inactivity`), la alerta «Acción requerida» lo avisaría y un botón lo reactivaría con `GITHUB_TOKEN`, el mismo que ya lanza la carga. GitHub, además, avisa por correo antes de desactivarlo.
  - Para la app dormida: el `README.md` y el enlace del portafolio avisan que puede tardar en despertar y muestran las capturas reales de `docs/img/`. No verificado: el plazo exacto de hibernación y si una visita automática la mantiene despierta.
- **Documentos:** PRD 3.14 (9) y SAD 3.11 (11), en los dos idiomas. De paso, la fila del SAD sobre dependencias dice que todas tienen versión máxima (D-435).
- **Pruebas:** `tests/test_documents.py::test_d439_the_risk_registers_name_both_abandonment_risks`.

## D-440 · Un diagrama se achica sin que sus textos se pisen: «Stack y evidencia» es el primero

- **Reporte del autor:** al achicar la ventana, el diagrama de herramientas de «Stack y evidencia» mezclaba sus letras. Medido sin ninguna pestaña abierta: 0 textos encimados a 1920 × 1000, 3 a 1440 × 790, 22 a 1100 × 650 y 127 a 700 × 500, en los dos idiomas.
- **Causa:** las posiciones de cada herramienta se achican con el diagrama, pero las letras tenían un tamaño mínimo fijo (de 10,5 a 12 px) y no podían partirse en dos líneas; al achicarse, los nombres, las descripciones y las etiquetas de las flechas quedaban más anchos que el espacio entre herramientas. Además, el ancho del diagrama dependía del alto de la ventana (D-277): una ventana baja lo dejaba en 238 px aunque sobrara ancho.
- **Decisión, la regla para todos los diagramas** (se aplica a los demás en la revisión de diagramas):
  1. Todo texto que esté entre dos elementos se escala con el diagrama, sin tamaño mínimo fijo: así no puede pisar a su vecino, igual que en una imagen.
  2. Una descripción larga se parte en líneas dentro del ancho de su elemento.
  3. Cuando el diagrama queda tan chico que un texto secundario no se podría leer, ese texto se oculta; la explicación al pasar el cursor y la leyenda lo conservan. Los nombres se ven siempre.
  4. Una ventana baja no achica el diagrama bajo un ancho legible; si falta alto, la página se desplaza un poco.
- **En «Stack y evidencia»:** ancho mínimo de 760 px por alto de ventana; la etapa de cada herramienta y las etiquetas de las flechas, a 12,5 unidades del diagrama, sin mínimo; las descripciones se parten dentro de su herramienta (mínimo 9 px); bajo 700 px de ancho se ocultan las etapas y las etiquetas de las flechas, y bajo 480 px, las descripciones; la etiqueta «cada martes» se corre a la derecha para no rozar el logo de GitHub en inglés («every Tuesday»). «Capa bronce» tiene ahora su inglés, «Bronze layer».
- **Resultado medido:** 0 textos encimados a 1920 × 1000, 1440 × 790, 1280 × 800, 1100 × 650, 700 × 500 y 520 × 700, en español e inglés; la letra visible más chica, 8,7 px a 1440 × 790. A 1440 × 790 y 1280 × 800 la página sigue cabiendo en una pantalla.
- **Pruebas:** `tests/test_stack_page.py::test_d440_no_text_can_cover_its_neighbour_when_the_window_shrinks`.

## D-441 · El «Mapa de la app» se abre por dentro: dueños, fichas, lupa, mensajes, ritmos y el recorrido del martes

- **Pedido del autor:** que el mapa explique cada pieza hasta su interior, sin reemplazarlo. Se mantienen el tema Vantablack, los logos oficiales, las nueve columnas de etapas, los filtros por tema, la leyenda de líneas y el resaltado al pasar el cursor.
- **Lo que se agrega:**
  1. **Dueños:** cuatro cajas, Fuentes externas (ODEPA mayorista, ODEPA consumidor, INE · IPC), Proyecto GreenOcean (con sus tres workflows), Plataformas externas (GitHub, PyPI, Streamlit Community Cloud) y Personas (Usuario, Profesional y Autor, cada uno con su línea de acceso). Borde continuo lo propio y punteado lo externo. ODEPA se separa en sus dos fuentes; «Repositorio GitHub» y «GitHub Actions» pasan a ser GitHub (plataforma) y `semanal.yml`, `pruebas.yml` y `calidad.yml` (propios); se suma «DevOps y seguridad».
  2. **Ficha de cada pieza** (un clic): qué hace, qué tiene adentro, los números con el comando que da cada uno, qué pasa si falla y por qué es así, con su decisión leída de `docs/DECISIONES.md` o del ADR. Tres piezas no tienen decisión propia y la ficha lo dice: HTML · CSS · JavaScript, Altair · Vega-Lite y Apoyo con IA. Un enlace abre su página del menú.
  3. **Lupa:** cada pieza lleva junto a su logo dos íconos pequeños, visibles desde el mapa completo: «i» abre la ficha (el texto) y la lupa entra, sin pasar por la ficha (la ficha conserva su botón «⌕ Ver por dentro»). Muestra cómo funciona la herramienta misma, con las cifras de GreenOcean, y aparte lo que hace en el proyecto. Nueve herramientas abren en «Cómo funciona»: DuckDB (proceso anfitrión, plan, ejecución vectorizada, almacenamiento columnar, un solo archivo en solo lectura), dbt (modelos, grafo, compilación, ejecución, pruebas como consultas y su rastro en `dbt_node` y `dbt_result`), SQLite, Parquet, Streamlit, GitHub Actions, PyPI, pytest y Altair · Vega-Lite; un segundo botón, «En GreenOcean», muestra lo que hace aquí. La vista «En GreenOcean» existe en 24 piezas, con el mismo lenguaje (columnas, logos y líneas): los pasos de cada workflow en el orden de su archivo, los modelos de dbt por capa, la puerta de publicación, el respaldo y su paridad, las secciones del panel, las páginas de operación, las tablas de la Base DuckDB, GitHub y la ingesta de cada fuente. Las personas no tienen interior. Los pasos de `semanal.yml` usan los nombres en español del diagrama de CI/CD (`bi/devops.py`); los de un workflow con varios jobs (`pruebas.yml`) se dibujan en paralelo, porque así corren.
  4. **Mensajes que viajan:** en reposo se mueve solo lo que siempre corre (el flujo de datos y los accesos). Cada línea se abre con un clic y dice qué viaja (archivo, consulta o token), qué vuelve, cada cuánto y en qué archivo pasa.
  5. **Ritmos:** un segundo filtro (cada martes, cada mes, cada push, manual, siempre), también como botón junto a la pieza que lo dispara. Al activarlo se mueve solo esa cadena y lo demás se atenúa. «Cada martes» tiene 26 líneas: moverlas todas a la vez se leía como si todo pasara al mismo tiempo. Por eso se mueve paso a paso, en el orden del recorrido del martes, y solo se ven las líneas del paso en curso; las demás se esconden hasta su turno. Mientras un ritmo o el recorrido avanzan, el cursor ya no enciende las líneas de una pieza: el botón «Cada martes» está dentro de `semanal.yml`, y al pulsarlo el cursor quedaba encima y tapaba la secuencia con las 13 líneas de esa pieza.
  6. **Recorrido del martes:** doce pasos en el orden real de la carga semanal, con las cifras de dbt leídas de `dbt_node`.
- **Un logo, una pieza:** el logo de GitHub queda solo en GitHub, la plataforma. Los tres workflows llevan un ícono de workflow y el release, uno de paquete con etiqueta; «Puerta de publicación» deja el escudo, que es de «Seguridad», y lleva una barrera. Las piezas siguen separadas, porque hacen cosas distintas: juntarlas en una sola llevaría unas 20 líneas al mismo punto. Solo comparten ícono las piezas de un mismo tipo: los dos ODEPA, que son la misma fuente, y los tres workflows.
- **Líneas ortogonales, cada una con su color:** como en un diagrama entidad-relación, las líneas ya no son curvas: corren en tramos rectos con giros de 90°. El panel divide el dibujo en una cuadrícula de 6 px; cada pieza (logo, nombre y botones) y cada rótulo es un muro, y cada línea toma el camino con menos giros que rodea los muros y evita los carriles de las líneas ya trazadas. Así dos líneas nunca van una encima de otra y se cruzan solo en ángulo recto. Primero se trazan las que siempre se ven, después las más cortas. Cada línea tiene su propio color, en el mapa y en cada lupa. Los tonos se separan por el ángulo áureo y por tres niveles de luz, y cada color queda al menos a 3:1 sobre el fondo del tema (WCAG 2.1 para gráficos), en los temas oscuros y en los claros. El tipo de línea lo dice el trazo: continuo (datos), guiones (órdenes), puntos (controles), fino (apoyo) y grueso (accesos). La ficha de cada línea muestra su color.
- **Aire para las líneas:** solo se trazan las líneas a la vista: en reposo, con un tema, en un paso de un ritmo o del recorrido, o las de la pieza bajo el cursor. Así no dan vueltas alrededor de líneas escondidas. Una ida y vuelta (por ejemplo, GitHub y `semanal.yml`) sale y llega por lados distintos, para que las dos líneas no compartan carril. Las columnas de afuera son un poco más angostas y quedan más lejos del proyecto, y las filas se separan más. Cada línea a la vista muestra su mensaje, pero en reposo una etiqueta aparece solo si no toca ningún nombre, logo, botón ni otra etiqueta; si no cabe limpia, se esconde y aparece al pasar el cursor por su línea. En una secuencia, la única línea a la vista muestra siempre su etiqueta. Nunca se ven varias líneas a la vez: la pieza bajo el cursor, un tema o un ritmo muestran sus líneas de a una, cada 1,8 s, cada una con su recorrido y su mensaje, y bajo el mapa se lee cuál es («3 / 13 · `semanal.yml` → pytest: «pytest -m datos»»). Las dos piezas de esa línea se destacan y el resto se atenúa. «Cada martes» las muestra en el orden del recorrido del martes. La descripción de la pieza las lista todas. Solo el «Recorrido del martes» muestra varias juntas, porque cada paso explica lo que pasa a la vez; en reposo se ve el flujo de datos, como vista general. El botón «Pantalla completa» da al mapa toda la ventana; sus filas se reparten el alto y Esc lo devuelve. La descripción de una pieza nunca tapa el dibujo: con el menú abierto se muestra sobre el menú; con el menú cerrado, en una columna angosta al lado del mapa o en la esquina que no cubre la pieza ni las piezas con que se conecta; en pantalla completa tiene su propia columna a la derecha.
- **Zigzag y nombres cortos:** el flujo de datos alterna una fila arriba y otra abajo (Agente, Parquet, DuckDB y Panel web arriba; SQLite, dbt Core y Release abajo), así cada línea llega a su pieza por un lado libre y no se apretan en una sola fila. «Secretos del panel» pasa bajo «Panel web», que es la pieza que lo lee, sobre «DevOps y seguridad», que también lo usa. Las cajas de fuentes y personas se alejan 26 px de la caja del proyecto, para que sus líneas y etiquetas tengan pasillo. El mapa escribe un nombre corto cuando el completo satura el dibujo («Agente», «Release», «Secretos», «Streamlit Cloud», «DevOps», «HTML · CSS · JS», «Altair», «Puerta», «Paridad», «Medición», «IA»); el nombre completo sigue en la descripción, la ficha y la línea bajo el mapa.
- **Pantallas chicas:** el mapa ya no se reordena en dos columnas bajo 760 px. Bajo 820 px de ancho (una tablet, un celular o una ventana chica) conserva el mismo dibujo que a 1280 × 800, reducido como una imagen; un toque abre la ficha y «Pantalla completa» lo muestra en grande. Las líneas se trazan en las unidades del dibujo y se reducen con él. Las descripciones al pasar el cursor no aparecen en la miniatura, porque ahí no hay cursor.
- **Compartimentos y precisión:** las cajas quedan a unos 4 mm entre sí, y dentro del proyecto cada franja es un tono más oscura: la aplicación arriba, «Navegador y operación» un 5 % más gris y «Lo que vigila» un 10 %. Lo que no es del proyecto (fuentes, plataformas y personas) conserva el fondo de la página. Las líneas paralelas guardan dos celdas de distancia cuando pueden. Una línea entra a la pieza por un costado o por arriba de su logo, nunca bajo el nombre, para que su punta toque la pieza y no quede en el aire. Puede pasar detrás de un nombre, pero eso le cuesta tanto como una vuelta.
- **Sentido y orden de las líneas:** cada línea termina en una punta de flecha junto al logo al que llega, así su sentido se lee aunque nada se mueva. Al pasar el cursor por una pieza se encienden sus líneas sin etiquetas; la etiqueta de una línea aparece al pasar el cursor por esa línea, o en su ficha. Todas juntas se tapaban unas a otras.
- **Espacio:** los logos del mapa pasan de 30 a 40 px y las filas se juntan; la leyenda baja al pie, en lugar de la nota, que sobraba con los íconos «i» y lupa.
- **Personas sin cruces:** Usuario, Profesional y Autor se ordenan de arriba abajo según la pieza a la que llegan (el panel web, el panel web, «DevOps y seguridad»), así sus líneas ya no se cruzan.
- **Lo que se lee y lo que se escribe a mano:** las cifras salen de `dbt_node`, `dbt_result`, `etl_run`, las tablas de la Base DuckDB, `agent/downloads/manifest.json`, `agent/input.csv`, `etl/datos.version`, los workflows, los requirements, `docs/calidad/metas.json`, `plan_mitigacion.json`, el Plan de pruebas y seguridad y el menú del panel. Solo el «por qué» se escribe a mano. Lo que el repositorio no puede mostrar dice «no verificado aquí»: el tamaño de `etl/datos.db` (solo existe donde corre la carga) y el plazo en que Streamlit Community Cloud duerme la app.
- **Una pantalla:** la segunda barra (ritmos y recorrido) costaba una fila; las filas del mapa se juntan. Medido: el fondo de la página queda en 768 de 790 px a 1440 × 790 y en 771 de 800 a 1280 × 800, en los dos idiomas; 0 textos encimados a 1920 × 1000, 1440 × 790, 1280 × 800, 1100 × 650, 700 × 500 y 520 × 700. Durante el recorrido, su frase toma el lugar de la leyenda.
- **Falla encontrada (F-24):** en inglés no se dibujaban en reposo las líneas del flujo de datos, desde antes de este cambio. La capa de inglés traduce toda cadena de un script que sea un texto del diccionario, y el script comparaba el tema con «datos», que pasaba a «data». Ahora Python marca cada línea que se ve en reposo y una prueba exige que ninguna cadena del script tenga traducción.
- **Pruebas:** `tests/test_app_map.py` (las de D-285 a D-293 al día con las líneas nuevas, y `test_d441_each_piece_says_who_owns_it_and_the_boxes_hold_exactly_those_pieces`, `test_d441_a_logo_names_one_piece_and_every_line_shows_its_direction`, `test_d441_lines_are_orthogonal_and_each_has_a_colour_of_its_own_in_every_theme`, `test_d441_every_card_has_its_five_parts_and_a_decision_that_exists`, `test_d441_every_piece_but_a_person_has_an_inside_and_its_lines_join_its_pieces`, `test_d441_the_magnifier_of_a_tool_shows_how_the_tool_itself_works`, `test_d441_a_workflow_inside_follows_its_file_and_every_line_runs_straight`, `test_d441_each_rhythm_moves_its_own_chain_and_the_people_lines_never_cross` y `test_d441_the_tuesday_walk_follows_the_real_sequence`).

## D-442 · «Panorama de precios» pasa a llamarse «Dashboard» y encabeza el menú

- **Pedido del autor:** la página principal, el resumen semanal de precios, quedaba como una línea más dentro de «Negocio · BA y BI», y «Panorama de precios» no decía qué era. Debía llamarse «Dashboard» y estar arriba de todo, como un cuadro con ícono de dashboard.
- **Decisión:**
  - **Nombre:** la página ya se llamaba «Dashboard» por dentro (`PAGE_HOME`); ahora ese es también su nombre visible, en los dos idiomas, en el menú, el encabezado, el «Mapa de la app», los documentos y el `README.md`.
  - **Menú:** el Dashboard es un cuadro de su propia sección, el primero del menú, para los tres perfiles: una miniatura de dashboard (tres cifras, barras y una línea) y su nombre. Queda marcado mientras está abierto. «Negocio · BA y BI» sigue debajo, sin él. El orden del menú, del encabezado y del pie anterior/siguiente empieza en el Dashboard.
  - **Ícono:** una miniatura propia, no el logo de Power BI ni el de Looker: el proyecto no usa esas herramientas, y su logo diría algo falso sobre el stack.
  - **Historia:** las decisiones anteriores, `docs/archivo/`, los informes de calidad ya emitidos y las filas del historial de versiones conservan el nombre de su momento.
- **Documentos:** PRD 3.15, Glosario 2.6, SAD 3.12, MANUAL 3.13 y SQAP 1.9, en los dos idiomas.
- **Pruebas:** `tests/test_menu_order.py` (el Dashboard encabeza el menú y el orden; la sección sigue sin él) y las pruebas de páginas, encabezado y traducciones con el nombre nuevo.

## D-443 · Regla de idioma: en inglés no queda texto en español en ninguna parte de la app

- **Pedido del autor:** con el inglés elegido, todo texto visible debe estar en inglés, salvo los nombres oficiales (ODEPA, INE, productos, regiones) y los nombres de archivos y código; una prueba debe recorrer cada página y cada diagrama, y la regla debe quedar en CLAUDE.md.
- **Lo que ya existía:** `tests/test_i18n.py::test_d284_*` recorría con `tests/i18n_audit.py` cada página del menú, sus vistas y pestañas y cada documento, siempre como Profesional, y leía los textos de HTML, gráficos y controles, pero no los que escribe un script.
- **Lo que se agrega:**
  - La auditoría lee también las frases que los scripts escriben en la página (cadenas con palabras, no código) y recorre dos pantallas más: la ventana «Elige tu vista», antes de elegir vista, y la vista Usuario.
  - **Encontró tres textos sin inglés,** todos en `bi/zoom.py`: «Acercar», «Alejar» y «Volver al tamaño original» (los botones del zoom de cada diagrama y documento) y «En este proyecto:» (la explicación de un término al pasar el cursor). La traducción ya existía para algunos, pero la capa de inglés no los encontraba: junto a una cadena de un solo carácter («⟲», «＋») leía mal las comillas. Ahora cada texto es su propia cadena.
  - En inglés, la explicación de un término no separaba su papel («Here:») de su definición, porque el script solo buscaba «Aquí:»; ahora separa los dos.
  - En «Git workflow», la palabra citada «continúa» va entre «» como el resto de los nombres citados.
- **La regla** queda en CLAUDE.md, «Convenciones»: qué queda en su idioma y qué prueba la vigila.
- **Documentos:** Plan de pruebas y seguridad 3.4 (2), en los dos idiomas.
- **Pruebas:** `tests/test_i18n.py::test_d284_no_screen_shows_spanish_when_the_reader_chose_english` (ahora también «Elige tu vista» y la vista Usuario, y los textos de los scripts) y `tests/test_i18n.py::test_d443_the_texts_a_script_writes_are_whole_strings_with_their_english`.

## D-444 · «Interesados» es un mapa de anillos de interés alrededor de GreenOcean

- **Pedido del autor:** reemplazar las cinco tarjetas por un mapa de anillos concéntricos, con GreenOcean al centro y una leve perspectiva 3D; tres anillos con nombre y color (interés alto, medio y bajo); cada interesado solo como un ícono de línea y su nombre completo, sin tarjetas, cajas, círculos, bordes ni fondos; al pasar el cursor o con el teclado el ícono crece y aparece una frase simple que explica su nivel; un clic abre su página.
- **Criterio de los anillos:** cuánto depende su decisión de estos datos y con qué frecuencia los usa. Se lee bajo el mapa.
- **Ubicación y justificación** (PRD 3.4, la tabla que la página lee en el idioma de la visita):
  - **Interés alto:** Restaurantes y almacenes (compran cada semana y el canal y la semana cambian su costo), Mayoristas, agricultores y feriantes (fijan su precio de venta cada semana) y Periodistas y economistas (cada nota sobre precios necesita una cifra oficial comprobable).
  - **Interés medio:** Personas y familias (les ayuda antes de comprar, pero su compra no depende solo de estos datos) y Equipos técnicos y reclutadores (lo revisan de vez en cuando, por cómo se construye).
  - **Interés bajo:** ODEPA y el INE, que entregan los datos y no deciden con ellos.
- **Dibujo:** cada anillo es una elipse (un disco visto desde arriba, con sombra) y cada interesado tiene su ángulo en su anillo, para que dos nombres nunca se encuentren. El dibujo guarda su proporción a cualquier ancho y sus letras crecen con él, como una imagen (D-441: la forma no cambia en una pantalla chica). En la vista Usuario, el interesado cuya página es solo del Profesional (Equipos técnicos y reclutadores) no es un enlace y su frase dice que se abre en la vista Profesional.
- **Lo que cambia en el PRD:** 3.1 sigue siendo la tabla de preguntas y decisiones, que ahora muestra «Análisis de negocio y sistemas»; 3.4 es el mapa nuevo.
- **Documentos:** PRD 3.16 (3.1, 3.4), en los dos idiomas.
- **Pruebas:** `tests/test_stakeholders.py::test_d444_the_page_is_the_interest_map_read_from_the_prd` y `tests/test_d444_the_map_reads_in_english_and_keeps_its_places`.

## D-445 · Revisión de los diagramas contra el sistema actual

- **Pedido del autor:** comparar cada diagrama del panel y de los documentos con el sistema de hoy (D-270 en adelante, los tres workflows, los tokens de D-397 y el acceso del Autor), corregirlo y aplicar la regla de D-440 (sin textos encimados a ningún tamaño, en los dos idiomas).
- **Datos que estaban mal:**
  - «Arquitectura de seguridad»: la clave de control solo «lanzaba el workflow semanal»; ahora dice que abre la vista Autor (sus tres páginas y la carga manual) con la sesión comprobada en el servidor (D-420, D-421). El token protegido nombra `GITHUB_TOKEN` y `GITHUB_READ_TOKEN`; el privilegio mínimo nombra `semanal.yml`, `calidad.yml` y `pruebas.yml`; los secretos del panel nombran los tres.
  - «Pipeline y linaje»: los secretos estaban en «GitHub Actions · Secrets»; viven en los secretos de Streamlit. La API REST de GitHub dice qué token lee y cuál lanza; la etiqueta «consultas» ya no tapa el nombre «Informe semanal».
  - «Stack y evidencia»: GitHub Actions abría «Centro de operación», que es solo del Autor; ahora abre «Git workflow».
  - «Git workflow»: GitHub Actions no despliega (lo hace Streamlit Community Cloud desde main), y F-11 ya está resuelta.
  - Monitoreo: el informe es el paso 10, no el 9; el aviso de vencimiento vale para los dos tokens; el panel no está «siempre en línea»: se duerme sin visitas (D-439).
  - Secuencia de la carga semanal (SAD): la inicia `semanal.yml`, no «GitHub Actions», y el IPC lo descarga `etl/ine.py` dentro de `etl/pipeline.py`, no el agente.
  - El informe de calidad ya no «lo aprueba el autor»: tras una carga en verde se propone y se fusiona solo si el código está en su aceptable (D-431, D-436), en el despliegue, el flujo en vivo, los escenarios y la mejora continua del SAD.
- **Nombres:** «base servida» pasa a «Base DuckDB» en todos los diagramas y textos del panel (D-426), con su inglés; «Workflow semanal», «GitHub Actions» como actor y «el token» pasan a `semanal.yml`, `GITHUB_TOKEN` y `GITHUB_READ_TOKEN`; el informe de la mejora continua es el «Informe semanal de calidad». En «Dónde viven los datos», la zona que guarda la Base DuckDB y el respaldo local se llama «Resultado de la carga», porque el respaldo no se publica.
- **Sin cambios, revisados:** contexto, contenedores, escenarios, capas de despliegue y secuencias del panel, del CI y de la recuperación del SAD; el ciclo de calidad; los pasos de CI/CD; el modelo estrella y el entidad-relación; las cifras del linaje.
- **Queda anotado, sin cambio:** el entidad-relación no dibuja `latest_by_source` (D-365), que no tiene relaciones; el título de ADR-35 conserva «base servida», porque es el nombre de la decisión en su momento.
- **Capturas:** las seis capturas de `docs/img/` y `docs/img/en/` se toman de nuevo, sin el respaldo local (D-392): mostraban «Panorama de precios» y el menú anterior a D-442. M-1 muestra el Dashboard con la región y la familia elegidas; M-2, con la región elegida. PRD 3.17.
- **Medición:** 0 textos encimados en los diagramas a 1440 × 790, 1280 × 800, 1920 × 1000 y 1100 × 650, en español e inglés (Playwright, como D-440).
- **Pruebas:** las de cada diagrama (`tests/test_architecture.py`, `tests/test_doc_diagrams.py` y las demás) con los textos nuevos, y `tests/test_i18n.py` sin español en inglés.

## D-446 · El Dashboard nunca pliega sus pasos: el panorama queda completo

- **Pedido del autor:** al elegir la región y la familia, el Dashboard mostraba solo la tabla y el mapa y las familias desaparecían. El pliegue de D-408 era para las páginas de cada canal, no para el Dashboard, que siempre debe mostrar el panorama completo; la tabla ya tiene su botón para ampliarse (D-317).
- **Decisión:** en el Dashboard, los pasos 1, 2 y 3 quedan siempre juntos: el mapa, las familias con la elegida marcada y la tabla de productos. Para ver más filas, el botón de ampliar abre la tabla al tamaño de la ventana. Las páginas de cada canal («Último dato por canal») siguen plegando los pasos 1 y 2 al elegir la familia, con «Cambiar», como dice D-408.
- **Documentos:** PRD 3.18 (7 y la captura M-1, en `docs/img/` y `docs/img/en/`) e Índice de decisiones, en los dos idiomas.
- **Pruebas:** `tests/test_panorama_steps.py::test_d446_the_dashboard_never_folds_its_steps_when_a_family_is_chosen` y `tests/test_home_mockup.py::test_d092_region_and_family_clicks_fill_the_products_table` (el mapa sigue a la vista); `tests/test_channel_latest.py::test_d408_a_channel_folds_its_steps_like_the_panorama` sigue verde.

## D-447 · La tabla del Dashboard: encabezado de una línea, en una sola pantalla, con su propio desplazamiento

- **Pedido del autor:** con el panorama completo (D-446), el encabezado de la tabla de productos ocupaba cuatro líneas. El Dashboard es una sola pantalla: la tabla se ve en pequeño bajo las familias y se desplaza sola, sin mover la página.
- **Decisión:** en el Dashboard, el encabezado ocupa una línea. Las columnas de precio dicen solo su semana («19–25 oct», «26 oct – 1 nov»), con «Precio medio» al pasar el cursor, y la columna de regiones dice «Regiones ↑ / ↓». La ventana de la tabla y cada canal conservan «Precio 19–25 oct». La tabla termina en el borde inferior de la ventana y se desplaza por dentro; mide al menos 110 px. El botón de ampliar la abre al tamaño de la ventana.
- **Lo que se probó y se descartó:** reservar 10 filas hacía crecer la página bajo el mapa, y el Dashboard dejaba de ser una sola pantalla (D-309).
- **Medición:** el panel termina dentro de la ventana a 1440 × 790, 1280 × 800, 1440 × 900 y 1920 × 1000, sin desplazamiento horizontal. Bajo él queda solo la nota de cobertura, como antes (Playwright).
- **Pruebas:** `tests/test_panorama_steps.py::test_d447_the_dashboard_table_has_a_one_line_header_and_scrolls_inside_one_screen`, y las del encabezado en `tests/test_dashboard.py`, `tests/test_home_mockup.py` y `tests/test_weeks.py`.

## D-448 · El SAD dibuja los diagramas de la app con el mismo código

- **Pedido del autor:** el SAD mostraba las tablas sueltas, una bajo otra, en vez del diagrama entidad-relación de «Modelo de datos»; no tenía el modelo estrella, «Dónde viven los datos» ni las herramientas de «Stack y evidencia», y su diagrama de despliegue no era el de la app.
- **Decisión:** los documentos ya no copian esas vistas: `bi/app_diagrams.py` las dibuja con el mismo código del panel, como una imagen fija sin el estado en vivo, y `bi/doc_diagrams.py` las publica con sus marcadores. El SAD queda así:
  - **3.4 Herramientas** (`[[diagrama:herramientas]]`): las herramientas de «Stack y evidencia» y sus tres cifras.
  - **6.1 Dónde viven los datos** (`almacenamiento`), **6.2 Modelo estrella** (`estrella`), **6.3 Entidad-relación** (`entidad_relacion`) y **6.4 Cruces entre bases** (`cruces`), las cuatro vistas de «Modelo de datos».
  - **6.5 Diccionario de datos:** la lista de tablas y las columnas de cada una, después de los diagramas.
  - **7. Despliegue** (`despliegue`): el diagrama de la pestaña «Despliegue» del «Centro de operación», sin los puntos de estado ni la próxima ejecución. Reemplaza al dibujo propio del SAD, que se retira.
- **Una sola fuente:** las funciones y las definiciones de las tablas, los tamaños de los archivos y las explicaciones al pasar el cursor viven en `bi/app_diagrams.py`; el panel y el SAD leen las mismas.
- **De paso:** la nota de «Cruces entre bases» pasa a dos líneas, porque en el marco más angosto del documento se cortaba. En la tabla de despliegue, el informe de calidad ya no «lo aprueba el autor»: se fusiona solo si el código está en su aceptable (D-431, D-436).
- **Documentos:** SAD 3.13, en los dos idiomas.
- **Pruebas:** `tests/test_documents.py::test_each_document_carries_the_diagrams_its_kind_of_document_needs` (los 15 diagramas del SAD, en orden) y `::test_d279_the_data_dictionary_describes_every_table_and_column_of_the_served_database` (el diccionario en 6.5); `tests/test_doc_diagrams.py` (cada diagrama es un documento sin script, sin fondo y sin sombras al imprimir).

## D-449 · «Git workflow» es un diagrama de flujo de forma fija

- **Pedido del autor:** el mapa no se veía como un diagrama de workflow: en una ventana mediana las 15 estaciones quedaban en una cuadrícula de tres columnas, sin flechas.
- **Decisión:** el mapa es un solo dibujo con forma fija, que una pantalla chica achica sin reordenar (como D-441). Tiene tres carriles con nombre: Preparar, Guardar y verificar, y Publicar. El camino serpentea de izquierda a derecha, de derecha a izquierda y otra vez de izquierda a derecha, con una flecha del color del carril entre cada dos estaciones y en cada vuelta.
- **Cada estación** muestra su número, su ícono, su título, su línea y su primer comando (con «+n» si tiene más). Una opcional va con borde punteado y el final, en un círculo verde.
- **Cada punto de control** es un rombo con sus dos salidas: la verde sigue («verde» o «sí») y la roja dice adónde vuelve el cambio («rojo → volver a 5», «pide forzar → parar»).
- **Lo que no cambia:** un clic o Enter en una estación abre el mismo panel lateral, con sus comandos para copiar, qué hacer si falla, el ejemplo de GreenOcean y sus fallas del registro.
- **Pruebas:** `tests/test_git_workflow.py::test_d449_the_map_is_a_flowchart_of_fixed_shape_with_an_arrow_between_every_two_stations`.

## D-450 · «Toda la canasta» se marca como una casilla, la cabecera de la tabla es fina y la búsqueda va en verde flúor

- **Pedido del autor:**
  - las líneas de tendencia de las familias se salían del panel;
  - el botón de ampliar no respondía;
  - un clic en «Toda la canasta» no desbloqueaba la tabla, que mostraba la primera familia por defecto: debía ser una casilla que la desbloquee;
  - la parte de arriba de la tabla ocupaba mucha altura;
  - el campo de búsqueda debía ir en verde flúor.
- **Causa del botón:** en la vista Usuario, mientras no se elige una familia, el panel 3 está bloqueado (D-352) y el bloqueo no deja tocar sus controles, tampoco «Ampliar». Con una familia elegida, el botón abre la ventana (comprobado con clics reales a 1280 × 684 y 1440 × 790).
- **Decisión:**
  - **«Toda la canasta»** se elige como una familia: es una casilla que se marca, completa el paso 2 y abre el paso 3 con los productos de todas las familias, con su mediana y su cobertura sumada. Reemplaza la regla de D-352 de que la fila no se elige.
  - **Las familias** no pasan el borde de su panel: el nombre y la barra ceden espacio antes que las cifras y la tendencia.
  - **La cabecera del panel 3** es una línea fina (el paso, la familia, la mediana, el lugar y la cuenta) y los filtros otra, de 28 px; la pregunta queda al pasar el cursor. La tabla gana 56 px en una sola pantalla (D-447).
  - **La búsqueda** brilla en verde flúor (`#39ff14`) en los temas oscuros y en un verde más hondo (`#00a83a`) en los claros, para que se lea sobre blanco. Reemplaza el celeste de D-372.
- **Pruebas:** `tests/test_panorama_steps.py::test_d450_the_whole_basket_row_is_the_median_of_every_comparable_price_and_is_ticked_like_a_box`, `::test_d450_ticking_the_whole_basket_opens_every_product_of_the_week`, `::test_d450_the_products_head_is_one_thin_line_and_the_families_stay_inside_their_panel` y `::test_d450_the_search_glows_in_fluorescent_green_apart_from_the_blue_of_falls`.

## D-451 · Las explicaciones de los paneles 1 y 2 van tras una «i»

- **Pedido del autor:** las descripciones de los paneles «Elige una región» y «Elige una familia» ocupaban altura que le faltaba a la tabla de productos; preguntó si convenía plegarlas o dejarlas tras un ícono de ayuda.
- **Decisión:** un ícono «i» junto al paso de cada panel guarda su título («Precios por región», «Variación por familia»), su pregunta y su explicación, con las cifras de cobertura del panel 2. Se abre al pasar el cursor o con el teclado. Se prefirió al bloque plegable: no pide clics, no mueve la página y el espacio queda libre siempre. Quedan a la vista lo que se elige y cómo leerlo: «Viendo: …», «Todo Chile», la leyenda del mapa, «Región: …» y la escala.
- **Resultado:** en el Dashboard, la tabla de productos sube 70 px y el mapa crece. A 1440 × 790 se ven 4 filas (antes 3), a 1920 × 1000 se ven 8 (antes 6), sin desplazar la página (Playwright).
- **Pruebas:** `tests/test_panorama_steps.py::test_d451_the_panels_explain_themselves_behind_a_small_i_next_to_their_step` y la altura de la tabla en `::test_d447_the_dashboard_table_has_a_one_line_header_and_scrolls_inside_one_screen`.

## D-452 · Cada canal se comporta igual que el Dashboard, y «Último dato por canal» es el segundo recuadro del menú

- **Pedido del autor:**
  - la página de un canal debe verse y comportarse exactamente como el Dashboard: dejaba un espacio vacío bajo los paneles y, al desbloquear la tabla, la agrandaba de golpe plegando los pasos 1 y 2;
  - «Último dato por canal» debe tener un ícono de dashboard y estar con el Dashboard, sobre «Negocio · BA y BI».
- **Decisión:**
  - **Sin pliegue:** el pliegue de D-408 se retira también en los canales. Un canal muestra siempre el mapa, las familias y la tabla juntos, como el Dashboard (D-446). Se quitan «Cambiar» y su estado.
  - **Una sola regla de altura:** la tabla de productos llena el panel 3 hasta el borde de la ventana, cualquiera sea el número de familias, y se desplaza sola, sin mover la página. Cada caja, del panel de arriba hasta la tabla, es una columna flexible. Así la altura llega a la tabla sin una cifra fija, que antes suponía las siete familias del Dashboard y dejaba un hueco en un canal con dos. La tabla mide al menos 110 px.
  - **Menú:** arriba hay dos recuadros con ícono de dashboard, el Dashboard y «Último dato por canal» (un dashboard partido en dos fuentes). La sección «Negocio · BA y BI» queda con Interesados, Análisis de negocio y sistemas, Precios e inflación e Insights. La ruta del encabezado dice «Dashboard › Último dato por canal › Mayorista».
- **Medición:** sin hueco ni desplazamiento horizontal a 1440 × 790, 1280 × 800, 1440 × 900 y 1920 × 1000 en el Dashboard, y a 1440 × 790 en el canal Mayorista, en las vistas Usuario y Profesional. En el canal Mayorista se ven 9 filas (Playwright).
- **Documentos:** PRD 3.19 (7, menú, Dashboard y Último dato por canal), Índice de decisiones 2.4 y README, en los dos idiomas donde corresponde. El «Mapa de la app» nombra las páginas en el orden nuevo.
- **Pruebas:** `tests/test_channel_latest.py::test_d452_a_channel_behaves_exactly_like_the_dashboard_and_never_folds`, `tests/test_menu_order.py` (los dos recuadros y la sección), `tests/test_dashboard.py::test_d213_the_menu_is_flat_sections_open_by_default_with_every_page_once`, `::test_d250_the_path_and_the_footer_follow_the_menu` y `::test_d295_each_professional_profile_reads_the_menu_like_its_portfolio`, y la altura en `tests/test_panorama_steps.py::test_d447_the_dashboard_table_has_a_one_line_header_and_scrolls_inside_one_screen`.

## D-453 · Los dos dashboards abren «Negocio · BA y BI», y cada canal tiene su ícono 3D

- **Pedido del autor:** los dos recuadros de dashboard deben estar en la sección «Negocio · BA y BI», justo antes de «Interesados». Cada tarjeta de canal puede tener un ícono 3D único que la identifique, con sus propios colores.
- **Decisión:**
  - **Menú:** la sección «Negocio · BA y BI» abre con sus dos recuadros, el Dashboard (D-442) y «Último dato por canal» (D-452), y sigue con Interesados, Análisis de negocio y sistemas, Precios e inflación e Insights. Los recuadros siguen a la vista aunque la sección se pliegue. Cada rol ordena las secciones como antes (D-295), así que los dashboards van donde cae la sección. La ruta del encabezado vuelve a nombrar la sección: «Negocio · BA y BI › Dashboard».
  - **El recuadro encendido** lleva la clase «_lit», no «_nav_current». La línea actual de una sección dibuja su barra en el mismo lugar donde el recuadro dibuja su ícono, y lo borraba. Solo el recuadro de la página abierta lleva el borde azul y su barra; el otro, un borde tenue. Antes, el borde azul quedaba en el que no estaba abierto.
  - **Tarjetas de canal:** cada canal tiene un ícono 3D propio, con degradados, sombra en el piso y sus colores (`bi/channel_icons.py`):
    - Mayorista: cajas apiladas, naranja.
    - Supermercado: carro, azul.
    - Feria libre: puesto con toldo a rayas y fruta.
    - Carnicería: corte de carne sobre una tabla, carmesí.
    - Supermercado en Línea: teléfono con un carro, violeta.
    - Mercado Minorista: local con toldo, turquesa.
    - Panadería: pan dorado.
    - Mercado Mayorista: camión de reparto, índigo.

    Un canal que llegue después recibe una etiqueta neutra. El ícono es una imagen, así el markdown de Streamlit conserva sus degradados. El nombre del canal y su fuente van en dos líneas junto al ícono, así «Consumidor» ya no sale de la tarjeta.
- **Documentos:** PRD 3.20 (7) y README.
- **Pruebas:** `tests/test_channel_latest.py::test_d453_each_channel_card_has_its_own_3d_icon_in_its_own_colours`, `tests/test_menu_order.py` (la sección con sus dos recuadros), `tests/test_dashboard.py::test_d295_each_professional_profile_reads_the_menu_like_its_portfolio`, `::test_d102_the_current_window_also_starts_open_and_can_be_toggled` (los recuadros no se pliegan) y `::test_d264_the_resumen_has_one_thin_bar_with_the_path_the_figures_and_the_alerts` (la ruta).

## D-454 · Una sesión que el servidor olvidó recupera la vista, sin preguntar ni volver al Dashboard

- **Pedido del autor:** tras unos 30 minutos sin actividad, un clic en un enlace (por ejemplo, «Documentos») llevaba al inicio en vez de a la página. Una vez elegida la vista, se debe navegar sin interrupciones; solo «Vista: … · Cambiar» vuelve a preguntar.
- **Causa:** tras un rato largo sin actividad (o si el computador se duerme, o el servidor se reinicia), el servidor olvida la sesión. El navegador se reconecta en la misma página, sin recargarla, y abre una sesión nueva sin vista. La vista seguía guardada en la pestaña (D-430), pero el guardián solo la leía una vez por página (D-428). Así, la sesión nueva mostraba «Elige tu vista» y, al elegir, abría el Dashboard (D-371).
- **Decisión:** el guardián vuelve a enviar la vista guardada cada vez que el servidor llega sin vista y la pestaña tiene una. La sesión nueva la recupera, con su rol y su historial de «Volver» (D-423), y el clic abre la página pedida. Una pestaña nueva sigue preguntando, y «Vista: … · Cambiar» y el logo siguen abriendo la ventana (D-373).
- **Lo que no cambia:** la vista Autor se sigue cerrando tras 30 minutos sin actividad (D-395), por seguridad. Si el servidor se reinició, su boleto ya no existe (D-427) y la visita sigue como Profesional.
- **Medición:** con Playwright: Profesional en «Modelo de datos», el servidor olvida la sesión y un clic en «Documentos» abre la carpeta como Profesional, sin la ventana «Elige tu vista».
- **Pruebas:** `tests/test_app_reloads.py::test_d454_a_session_the_server_forgot_reads_the_kept_view_again`.

## D-455 · Los documentos usan los diagramas de la app, y el PRD nombra solo los tres perfiles del panel

- **Pedido del autor:** el diagrama de casos de uso del PRD no era correcto. Mostraba cuatro perfiles que el panel no tiene (Gerencia, Analista de pricing, Compras y abastecimiento, Revisor técnico) y a GitHub Actions como actor, cuando el panel tiene tres vistas: Usuario, Profesional y Autor. Los documentos deben usar los diagramas que ya están en la app, en vez de dibujos propios, sin contradicciones entre la app, los documentos y las cifras.
- **Decisión:** donde la app ya dibuja lo mismo, el documento usa ese diagrama, desde el mismo código (`bi/app_diagrams.py`, como D-448):

| Documento | Dibujo propio que se retira | Diagrama de la app que lo reemplaza |
|---|---|---|
| PRD 3.2 | Casos de uso con los cuatro perfiles | — (la tabla 3.2 son los tres perfiles del panel) |
| PRD 3.4 | — | Mapa de anillos de «Interesados» (`[[diagrama:interes]]`) |
| PRD 1 | «Del dato a la decisión», que nombraba a «Gerencia» | — (el PRD conserva «Del dato al informe, cada semana», que es el bloque «Proceso» de «Análisis de negocio y sistemas») |
| SAD 6 | «Capas de los datos» | Recorrido por capas de «Pipeline y linaje» (`recorrido`) |
| Plan de pruebas 1 | «En cada carga» | Pestaña CI/CD del «Centro de operación» (`cicd`) |
| Plan de pruebas 3 y 4 | «Quién participa en la seguridad» | «Arquitectura de seguridad» (`seguridad`), en la sección 4, donde el texto ya la nombraba |
| Plan de pruebas 8 | «Secuencia de un cambio de código» | El diagrama de flujo de «Git workflow» (`git_workflow`) |
| SQAP 3 | «El ciclo de cada semana» | El flujo de calidad de «Calidad y auditoría» (`calidad`), junto a los 11 indicadores de los datos |
| MANUAL 1 | «Tareas periódicas» | Pestaña «Monitoreo» del «Centro de operación» (`monitoreo`) |

- **Cómo se dibujan:**
  - Como una imagen fija, sin el estado en vivo ni los paneles que se abren con un clic.
  - El recorrido muestra el estado que prueba la última carga publicada y las mismas cifras de la página: filas, precios, semana y próxima carga. Su leyenda dice dónde está el estado en vivo.
  - El mapa de interés se dibuja en el documento mismo, no en un marco, porque sus íconos son letras de la fuente de íconos del panel. Ningún interesado es un enlace.
  - `bi/interest_map.py` dibuja el mapa para la página y para el PRD.
  - En un marco angosto, como la columna de un documento, «Monitoreo» deja el espacio del ícono al nombre, así ningún nombre se corta.
- **Lo que se mantiene:** las figuras sin equivalente en la app: los diagramas C4, los escenarios y las secuencias del SAD, las del ADR, el Índice y el Glosario, la secuencia de la carga manual y el procedimiento de seguridad, el árbol de fallas y la recuperación. Se revisó que solo nombren las tres vistas y los nombres oficiales.
- **Coherencia del texto:**
  - El PRD 3.2 ya no dice que «Elige tu vista» pregunta en cada recarga: pregunta una vez por pestaña (D-430, D-454). El Autor tiene también «Centro de operación» (D-420).
  - El Plan de pruebas nombra los dos tokens y la clave de control (`GITHUB_TOKEN`, `GITHUB_READ_TOKEN`, `CONTROL_CODE`) y la carga semanal por su archivo (`semanal.yml`).
  - El MANUAL dice que el pull request de calidad se fusiona solo si el código está en su aceptable (D-436).
  - «Base servida» pasa a «Base DuckDB» en el texto del PRD, el Plan de pruebas, el MANUAL, el Glosario, el ADR y `metas.json` (D-426). El título de ADR-35 y los historiales de versiones conservan el nombre de su momento.
- **Documentos:** PRD 3.21, SAD 3.14, Plan de pruebas y seguridad 3.5, SQAP 1.10, MANUAL 3.14, Glosario 2.7 y ADR 3.4, en los dos idiomas.
- **Pruebas:**
  - `tests/test_doc_diagrams.py::test_d455_the_documents_draw_the_panels_own_diagrams_and_no_invented_profile`.
  - `tests/test_prd_traceability.py::test_d455_the_usage_profiles_are_the_three_views_of_the_panel`.
  - `tests/test_documents.py::test_each_document_carries_the_diagrams_its_kind_of_document_needs`.

## D-456 · «Análisis BA y BI»: una sola página con pestañas, con la historia de los precios como informe

- **Pedido del autor:** simplificar la parte BA. Debe ser un dashboard de análisis histórico, con las tendencias de los precios por mes, año y temporada y sus valores atípicos, en una sola página. Insights, Precios e inflación e Interesados quedan dentro, en pestañas. Todo bajo un recuadro con ícono, como el Dashboard, coherente y explicado al pasar el cursor; simple y eficaz, inspirado en un informe de Power BI. El nombre es «Análisis BA y BI». De «Análisis de negocio y sistemas» queda solo una pestaña «Método» breve (decisiones del autor).
- **Diagnóstico:** «Análisis de negocio y sistemas» eran 10 bloques de texto copiados del PRD y del SQAP, sin análisis de datos. «Interesados» aparecía tres veces. «Insights» repetía en texto lo que mostraban el Dashboard y «Precios e inflación».
- **Decisión:**
  - **Menú:** «Negocio · BA y BI» son tres recuadros con ícono de dashboard: el Dashboard, «Último dato por canal» y «Análisis BA y BI». El tercero tiene su propio ícono: un informe con una lupa.
  - **Pestañas de «Análisis BA y BI»:** Tendencias, Precios e inflación, Insights, Interesados y Método. Las cuatro últimas son las páginas de antes, dibujadas por su mismo código bajo su pestaña. Su pregunta y sus cifras quedan en la fila bajo las pestañas, sin una segunda barra (D-398).
  - **Direcciones antiguas:** la dirección de cada página antigua abre su pestaña, también desde un enlace de un documento (`pestana=…`). En los documentos, una pestaña se nombra «Análisis BA y BI (Pestaña)», como «Centro de operación (CI/CD)».
  - **Tendencias** es un informe de una sola pantalla. Arriba, en la fila de las pestañas, se elige el período (los últimos 12 meses, desde enero 2022 o un año) y la familia (toda la canasta o una de las siete).
    - **Cinco cifras clave:** cambio de precios, frente al IPC, brecha consumidor–mayorista (K1), alertas de precio (K6) y mes más barato (K4).
    - **Tres gráficos:** el precio mes a mes frente al IPC, la temporada por mes del calendario y los valores atípicos por mes.
    - **Una tabla por familia.**
    - Cada cifra, columna y gráfico explica al pasar el cursor cómo se calcula.
  - **Método:** solo lo que el PRD no tiene: cómo se calcula cada KPI y las decisiones de sistema. El resto queda en el PRD. El enlace «Ver las definiciones de los KPI» de Insights abre esta pestaña.
- **Coherencia de las cifras:**
  - Todo sale de las mismas consultas y reglas del panel: el índice mensual de «Precios e inflación» (D-163), ahora con la canasta completa (la mediana de las mismas series), K1, K4 y K6.
  - El período termina en el último mes que publicó el INE, para comparar con la inflación.
  - Con la base del 31-10-2026, en los últimos 12 meses Frutas sube +5,9 % y el IPC +4,3 %, igual que en «Precios e inflación» e «Insights». Desde enero 2022 el IPC sube +44,8 %.
- **Eje del tiempo:** «Precio mes a mes» y «Valores atípicos por mes» empiezan en el mes en que empieza el período, aunque no haya datos. Una alerta necesita las 12 semanas anteriores (K6), así que la primera posible es de abril 2022. Antes, el gráfico de alertas empezaba su eje en el primer mes con alertas, y con «Desde ene 2022» su primera etiqueta era «01-2023», aunque 2022 tuviera alertas (lo notó el autor). Cada barra ocupa su mes, y al pasar el cursor por el título de cada gráfico se lee cómo se calcula.
- **Temporada:** sus barras son los meses del calendario, no los de un año. Cada una junta las semanas de ese mes de todos los años del período: con «Desde ene 2022», febrero reúne los febreros de 2022 a 2026; con los últimos 12 meses, cada mes aparece una vez, en su año. El subtítulo nombra el rango («oct 2025 – sep 2026; cada mes frente a su año») y, al pasar el cursor, cada barra dice sus años y sus semanas (lo preguntó el autor).
- **Lo que deja de ser de la app:** el bloque «Proceso» de la página antigua se retira. «Del dato al informe, cada semana» vuelve a ser solo una figura del PRD, y lo que D-455 decía de ella queda así corregido.
- **Medición:** la pestaña Tendencias cabe sin desplazar la página a 1440 × 900 y 1440 × 790, en español e inglés (Playwright).
- **Documentos:** PRD 3.22 (3.1, 3.2, 3.4, la pantalla de P-4 y 7), SAD 3.15 (los escenarios clave y la vista Usuario), Glosario 2.8, CLAUDE.md (los nombres oficiales y los módulos nuevos `ba_trends.py`, `interest_map.py`, `app_diagrams.py` y `channel_icons.py`), README y la captura M-3, en los dos idiomas donde corresponde.
- **Pruebas:**
  - `tests/test_menu_order.py::test_d456_the_section_is_its_three_dashboards_and_the_analysis_gathers_the_rest_in_tabs`.
  - `tests/test_ba_trends.py`: las cifras se recalculan y coinciden con «Precios e inflación».
  - `tests/test_business_analysis.py::test_d456_the_method_tab_draws_the_kpis_and_the_system_decisions_and_insights_links_to_it` y `::test_d456_the_method_tab_reads_in_english`.
  - `tests/test_page_bar.py::test_d391_the_inflation_page_sits_in_its_menu_section` (la dirección abre su pestaña).
  - Las del menú, el encabezado, el idioma y los documentos, con la sección nueva.

## D-457 · «Análisis BA y BI»: lo mensual y lo histórico en pestañas separadas, y cada gráfico se explica al pasar el cursor

- **Pedido del autor:** en «Tendencias» no se entendía de qué año eran los meses de «Precio mes a mes», y el período (12 meses) y la historia (desde 2022) se mezclaban en la misma vista. Todo lo mensual y periódico va en una pestaña; todo lo histórico, de 2022 a 2026, en otra. Cada gráfico dice claramente su período. Al pasar el cursor, el gráfico se agranda, sin pasar el ancho de la página, y explica qué mide y qué se deduce, para que nadie tenga que adivinar. Sin un solo error en las cifras: es el portafolio del autor y lo verá un gerente.
- **Diagnóstico:**
  - El eje de «Precio mes a mes» mostraba los meses sin año, y su subtítulo decía «inicio del período = 100» sin nombrar ese mes.
  - «Tendencias» tenía el período «Desde ene 2022» junto a los de 12 meses y de un año: la misma vista servía para un período y para toda la historia.
  - Las explicaciones estaban solo en el título de cada gráfico, en un texto fijo que no decía lo que muestran los datos.
- **Decisión:**
  - **Pestañas:** «Tendencias» se divide en «Mensual» e «Histórico». Las pestañas de «Análisis BA y BI» son seis: Mensual, Histórico, Precios e inflación, Insights, Interesados y Método. La dirección antigua de «Tendencias» abre «Mensual».
  - **Mensual:** un período, los últimos 12 meses o un año, mes a mes. Se elige el período y la familia.
    - Cinco cifras clave: cambio de precios, frente al IPC, brecha consumidor–mayorista (K1), alertas de precio (K6) y mayor alza mensual.
    - Tres gráficos: precio mes a mes, cambio de cada mes frente al anterior (con el IPC de ese mes) y alertas de precio por mes.
    - La tabla por familia.
  - **Histórico:** siempre de enero 2022 al último mes que publicó el INE, por año y temporada. Se elige solo la familia, que las dos pestañas comparten.
    - Cinco cifras clave: cambio desde enero 2022, frente al IPC, año de mayor alza, mes más barato (K4) y alertas de precio.
    - Tres gráficos: precio desde enero 2022, cambio de cada año (con el IPC de ese año) y temporada.
    - La tabla por familia.
  - **Cada gráfico dice sus meses:** «sep 2025 – sep 2026 · base sep 2025 = 100», «oct 2025 – sep 2026 · frente al mes anterior», «2022–2026 · de diciembre a diciembre». Cada tarjeta dice los dos meses que compara («sep 2025 → sep 2026»).
  - **Zoom al pasar el cursor:** el gráfico se agranda en una ventana de 750 px como máximo (o 72 % de la pantalla), dentro de la página, y dice «Qué mide» y «Qué se deduce». El texto se calcula con las mismas cifras que dibuja; nada se escribe a mano. Las definiciones de K1, K6 y del índice frente al IPC son las de «Método» (`overview.KPIS` y `alerts.describe_rule`, D-385).
  - **Eje de los meses** (lo preguntó el autor): «Precio mes a mes» tenía un punto por mes, pero Vega, la librería de los gráficos, rotulaba uno de cada tres meses para que las etiquetas no se tocaran. Ahora cada mes tiene su punto y su etiqueta con el año, inclinada, en los tres gráficos de «Mensual»; «Histórico» rotula cada año. Además, el borde del eje se escribía como texto («2026-09-01»), que el navegador lee como medianoche UTC, el día anterior en Chile: el último mes quedaba fuera del eje y sin etiqueta. Ahora el borde va en hora local, como los datos. Los valores al pasar el cursor ya eran los correctos (sep 2025 = 100,0).
- **Cómo se mide un cambio:**
  - Los últimos 12 meses, desde el mismo mes del año anterior; un año, de diciembre a diciembre, como el IPC del INE. 2022 empieza en enero, el mes base, porque no hay índice antes, y el año en curso llega al último mes publicado. El gráfico de cada año lo dice al pasar el cursor («desde ene», «hasta sep»).
  - Un mes sin índice queda vacío; nunca se rellena.
  - «Frente al IPC» se colorea solo a más de 2 puntos, igual que su veredicto y la tabla. Antes se coloreaba por su signo, y un «+1,8 pts» rojo decía «al ritmo de la inflación».
- **Coherencia de las cifras** (base del 31-10-2026):
  - **Mensual:** en los últimos 12 meses la canasta sube +6,1 % y el IPC +4,3 %, igual que en «Precios e inflación». Sus 12 cambios mensuales encadenados dan el mismo +6,1 %. Subió en 8 de 12 meses; la mayor alza fue jul 2026 (+3,9 %).
  - **Histórico:** desde enero 2022 la canasta sube +43,7 % y el IPC +44,8 %. Los cambios de cada año (2022 +16,4 %, 2023 +5,6 %, 2024 +4,6 %, 2025 +2,8 % y 2026 hasta septiembre +8,7 %) encadenados dan el mismo +43,7 %. Solo 2026 superó al IPC por más de 2 puntos.
  - **Alertas:** 916 en los últimos 12 meses y 4.004 desde 2022, la suma de las filas de cada tabla. La base tiene 4.057: las 53 restantes son de octubre 2026, después del último mes del IPC.
  - **Temporada:** febrero es el mes más barato (−3,6 % frente al promedio de su año) y noviembre el más caro (+2,5 %). Son precios del día: cuando los precios suben durante el año, los primeros meses quedan bajo su promedio y los últimos sobre él. El zoom lo dice, para no confundir la inflación con la temporada.
- **Medición (Playwright):** las dos pestañas caben sin desplazar la página a 1440 × 900 y 1440 × 790, en español e inglés. El zoom queda dentro de la página, en tema oscuro y claro. A 1280 × 800, «Mensual» se desplaza 50 px: los filtros bajan a una segunda fila bajo las seis pestañas.
- **Documentos:** PRD 3.23 (3.2 y 7), SAD 3.16 (los escenarios clave), Glosario 2.9, CLAUDE.md, README y la captura M-3, en los dos idiomas.
- **Pruebas:**
  - `tests/test_ba_trends.py`: los cambios de cada mes encadenados dan el del período; los de cada año, el de enero 2022; las cifras coinciden con «Precios e inflación»; cada frase del zoom tiene las cifras que explica; cada tarjeta usa las definiciones de «Método»; un mes sin índice queda vacío; cada pestaña dibuja sus tres gráficos con su versión grande; cada mes de un período tiene su punto y su etiqueta (`test_d457_every_month_of_a_period_has_its_point_and_its_label`); la dirección de «Tendencias» abre «Mensual».
  - `tests/i18n_audit.py`: la auditoría de inglés recorre cada pestaña de «Análisis BA y BI», y «Mensual» con 2022 y una familia.
  - Las del menú y de los documentos, con las seis pestañas.

## D-458 · «Análisis BA y BI»: un recuadro verde sobre las pestañas dice qué se ve, de qué mes a qué mes y por qué

- **Pedido del autor:** quien visita la página no sabe por qué un gráfico empieza en diciembre y termina en septiembre, y no tiene por qué conocer el sistema. Sobre las pestañas debe haber un recuadro en el verde flúor de GreenOcean que lo diga en palabras simples y cambie con cada período elegido: «Estás viendo los últimos 12 meses: de oct 2025 a sep 2026», y por qué. Además, bajo la tabla sobraba espacio: los gráficos deben usarlo.
- **Decisión:**
  - **El recuadro:** va entre el encabezado y las pestañas, en las seis pestañas, con el alto de dos líneas, para que las pestañas no salten al cambiar de una a otra. Dice qué se ve, de qué mes a qué mes y por qué empieza y termina ahí. El texto se arma con los meses de los datos y cambia con la pestaña y el período; nada se escribe a mano. Es contenido bajo el encabezado, no parte de él (D-398).
    - **Mensual, últimos 12 meses:** de oct 2025 a sep 2026. Termina en el último mes con la inflación del INE, que llega una vez al mes y con atraso; el precio parte un año antes (= 100) para medir el cambio de 12 meses.
    - **Mensual, el año en curso:** de enero al último mes del INE. Parte en diciembre del año anterior (= 100), el cierre de ese año, para medir lo que va del año, como el IPC del INE.
    - **Mensual, un año completo:** de enero a diciembre; parte en diciembre del año anterior.
    - **Mensual, 2022:** parte en enero 2022 = 100, el primer mes de los datos, así que el cambio de cada mes empieza en febrero; la primera alerta posible es de abril.
    - **Histórico:** de enero 2022 al último mes del INE; cada año va de diciembre a diciembre (2022 desde enero, el año en curso hasta su último mes).
    - **Precios e inflación:** sus meses y que subir con el IPC no prueba que la inflación cause la subida. Es la nota que estaba bajo sus tarjetas, que deja de repetirse.
    - **Insights:** la semana de los precios (la del Dashboard) y el último mes del INE.
    - **Interesados:** la regla de los anillos, que estaba bajo el mapa; el mapa del PRD la conserva. **Método:** de dónde se leen los KPI y las decisiones de sistema.
  - **Color:** el verde flúor de la búsqueda del Dashboard (D-450), #39ff14 en los temas oscuros y #00a83a en los claros, en el borde, el ícono y un fondo verde suave. El texto va en la tinta del tema, para que se lea en los cuatro temas.
  - **Gráficos más grandes:** en Mensual e Histórico, los tres gráficos toman el alto que deja la ventana, sobre un piso. A 1440 × 900 pasan de 182 a 263 px de alto; a 1512 × 982, a 345 px. A 1440 × 790 bajan a 154 px, el costo del recuadro en la pantalla más baja. Bajo 1400 px de ancho los filtros bajan a otra fila: pierden su etiqueta, porque el recuadro ya nombra el período, y el piso baja a 128 px. La tabla queda más abajo y más compacta.
  - **Espacio de las otras pestañas:** Precios e inflación gana el alto de la nota que pasó al recuadro. La tabla de Insights reserva 305 px en vez de 290 para el recuadro, y sus filas pierden 1 px de margen.
- **Medición (Playwright):** Mensual, Histórico, Precios e inflación, Insights e Interesados caben sin desplazar la página a 1440 × 900 y 1440 × 790, en español e inglés; Mensual e Histórico, también a 1280 × 800 y 1512 × 982. «Precios e inflación», que se desplazaba 28 px desde D-456, ahora cabe. Método es texto y se sigue desplazando, como antes.
- **Documentos:** PRD 3.24 (7) y la captura M-3, en los dos idiomas.
- **Pruebas:** `tests/test_ba_trends.py::test_d458_the_green_panel_says_from_which_month_to_which_and_why_for_each_period` (los textos de cada período, con sus meses) y `::test_d458_the_panel_sits_above_the_tabs_and_follows_the_tab_and_the_period` (el recuadro va sobre las pestañas, cambia con el período y la pestaña, y las notas que se movieron se dicen una sola vez). La auditoría de inglés recorre el recuadro en cada pestaña.

## D-459 · Los tres dashboards van bajo el título «Dashboards», y el de la semana se llama «Semanal»

- **Pedido del autor:** las tres páginas de «Negocio · BA y BI» son dashboards, así que llamar «Dashboard» solo a la primera es raro. El conjunto se llama «Dashboards» y cada uno tiene su nombre; el primero, el de la semana, uno corto y profesional. El autor eligió entre tres opciones: el título «Dashboards» y «Semanal».
- **Decisión:**
  - **Menú:** bajo «Negocio · BA y BI» va el título «Dashboards», más pequeño que una sección y con sangría, y bajo él los tres recuadros: Semanal, Último dato por canal y Análisis BA y BI. El título sigue a la vista con los recuadros aunque la sección se pliegue (D-453).
  - **Nombre:** la página que se llamaba «Dashboard» (antes «Panorama de precios», D-442) se llama «Semanal»; en inglés, «Weekly». Su ruta es «Negocio · BA y BI › Semanal». En un texto se dice «el dashboard Semanal».
  - **Direcciones antiguas:** `?vista=Dashboard`, un marcador o un enlace viejo, abre Semanal. La recarga que vuelve al inicio usa el nombre nuevo.
  - **Lo que no cambia:** la página, sus tres pasos y sus cifras. Las otras dos conservan su nombre. Los historiales de versiones y las decisiones anteriores dicen «Dashboard», como se llamaba entonces.
- **Coherencia:** el nombre cambia en la app, en el mapa de la app, en Stack y evidencia, en Insights («dónde verlo») y en los documentos: PRD 3.25, SAD 3.17, SQAP 1.11, Glosario 2.10 y MANUAL 3.15, en los dos idiomas, más CLAUDE.md, README, `docs/PROYECTO.md` y la política de calidad. Los enlaces de los documentos a la página (`[[vista:Semanal]]`, `[[vista:Weekly]]`) llevan a ella. Las seis capturas de los documentos se tomaron de nuevo, con el menú nuevo, en los dos idiomas.
- **Pruebas:** `tests/test_menu_order.py::test_d459_the_three_dashboards_sit_under_their_title_and_the_old_address_opens_semanal` (el título, los tres nombres en los dos idiomas y la dirección antigua), y las del menú, el encabezado, el idioma y los documentos, con el nombre nuevo.

## D-460 · «Análisis BA y BI»: tarjetas finas, meses en dos líneas cortas y una lupa verde que abre cada gráfico en grande

- **Pedido del autor:** las tarjetas ocupaban mucho alto y los gráficos del medio se veían comprimidos; en su pantalla, más angosta, las notas de las tarjetas ocupaban hasta tres líneas. Además, en vez de agrandar el gráfico al pasar el cursor, prefiere un ícono verde luminoso que lo abra.
- **Diagnóstico:** en una pantalla angosta, las etiquetas inclinadas de los meses («sep 2025» a 45°) se comían la mitad del alto de cada gráfico, y los filtros bajaban a otra fila bajo las seis pestañas.
- **Decisión:**
  - **Tarjetas finas:** una línea para el nombre, otra para la cifra y otra para su nota. Si una no cabe, termina en «…», y la tarjeta la dice completa al pasar el cursor. Bajan a 68 px de alto (antes, 83 px a 1440 × 900, y más en una pantalla angosta).
  - **Meses en dos líneas cortas:** en los gráficos de la página, cada mes lleva su nombre corto y, debajo, el año, solo en el primer mes y en enero («sep / 2025 · oct · … · ene / 2026»). En la ventana grande, cada mes lleva su año, «sep 2025».
  - **Lupa verde:** junto al título de cada gráfico hay una lupa en el verde flúor de GreenOcean (D-450), con un brillo. Al hacer clic se abre una ventana con el gráfico grande, sus meses, «Qué mide» y «Qué se deduce». Ya no se abre al pasar el cursor (reemplaza el zoom de D-457), y la página dibuja tres gráficos en vez de seis.
  - **Pantallas angostas:** bajo 1400 px las pestañas y los filtros se achican un poco y siguen en una sola fila hasta 1250 px de ancho.
- **Medición (Playwright):** todo cabe sin desplazar la página a 1440 × 900, 1440 × 790 (español e inglés), 1366 × 768, 1280 × 800 y 1280 × 720. Los gráficos miden 297 px de alto a 1440 × 900 (antes 263), 187 px a 1440 × 790 (antes 154) y 197 px a 1280 × 800 (antes 128).
- **Documentos:** PRD 3.26 (7) y la captura M-3, en los dos idiomas.
- **Pruebas:** `tests/test_ba_trends.py::test_d460_the_green_magnifier_opens_the_chart_large_in_a_window`, `::test_d460_each_tab_draws_three_charts_and_each_magnifier_opens_its_window` (la lupa abre la ventana con sus textos y su gráfico) y `::test_d457_every_month_of_a_period_has_its_point_and_its_label` (las etiquetas en dos líneas en la página y completas en la ventana).

## D-461 · «Análisis BA y BI»: los gráficos nunca bajan de 230 px; en una ventana baja, la tabla se desplaza por dentro

- **Pedido del autor:** en su pantalla, más baja que la medida de 1440 × 790, los gráficos se veían aún más comprimidos que antes de D-460.
- **Diagnóstico:** los gráficos toman el alto que deja la ventana, sobre un piso de 154 px (128 px en una ventana angosta). En una ventana baja ese piso mandaba y la tabla se quedaba con el resto; antes de D-458 los gráficos medían 182 px fijos.
- **Decisión:** el piso de los gráficos sube a 230 px (210 px bajo 1400 px de ancho). La tabla por familia va en su propia caja, que se desplaza por dentro con el encabezado siempre a la vista, y toma el alto que queda, nunca menos de 140 px. En una ventana alta no cambia nada: la tabla cabe entera y no se desplaza.
- **Medición (Playwright):** a 1440 × 790 los gráficos miden 230 px (antes 187) y la tabla muestra 7 de sus 9 filas; a 1440 × 900, 297 px y la tabla entera; a 1280 × 720, 210 px. Nada desplaza la página a 1440 × 900, 1440 × 790 ni 1280 × 720; a 1440 px de ancho, solo una ventana de menos de unos 720 px de alto desplaza la página.
- **Pruebas:** `tests/test_ba_trends.py::test_d460_the_green_magnifier_opens_the_chart_large_in_a_window` revisa también el piso de los gráficos y la caja de la tabla.

## D-462 · Los tres dashboards abren con el menú plegado y su botón palpita en verde

- **Pedido del autor:** con el menú plegado, los dashboards se ven mejor, pero el botón para abrirlo casi no se veía. En los tres dashboards el menú se pliega solo, y el botón queda palpitando en verde flúor para mostrar que está ahí. Además, el espacio de arriba debe aprovecharse: quedaba una franja vacía sin razón (el autor eligió los tres dashboards, no solo Análisis BA y BI).
- **Decisión:**
  - **Menú plegado:** al abrir Semanal, Último dato por canal o Análisis BA y BI, el menú se pliega una vez. Si quien lee lo abre, queda abierto mientras siga en esa página; al abrir otro dashboard se pliega de nuevo. En las demás páginas no cambia nada. Un teléfono girado conserva su menú abierto (D-166).
  - **Botón que palpita:** en los tres dashboards, el botón que pliega y despliega el menú va en el verde flúor de GreenOcean (D-450) y late con un brillo. Si el sistema pide menos movimiento, solo brilla.
  - **Sin franja arriba:** con el menú plegado, la página empieza arriba, a la derecha del logo y del botón, en vez de dejar 54 px vacíos bajo ellos.
  - **Detalle de Streamlit:** esta versión marca el menú con `data-collapsed`, no con `aria-expanded`; el guion lee los dos.
- **Medición (Playwright):** Semanal abre con el menú plegado y el botón latiendo; abierto a mano, sigue abierto; Pipeline y linaje no late; Análisis BA y BI se pliega otra vez.
- **Pruebas:** `tests/test_menu_order.py::test_d462_a_dashboard_opens_with_the_menu_folded_and_its_button_beating_in_green`.

## D-463 · La app abre con el menú abierto; se pliega al ir a un dashboard o a una página de diagramas

- **Pedido del autor:** al abrir la app el menú debe estar abierto. El plegado automático de D-462 vale solo al ir a un dashboard o a cualquier página de diagramas. Y con el menú plegado no debe quedar un margen grande a la izquierda.
- **Decisión:**
  - **Apertura:** la primera página de la visita deja el menú abierto, también Semanal tras «Elige tu vista».
  - **Plegado:** el menú se pliega una vez al ir a Semanal, Último dato por canal, Análisis BA y BI, Pipeline y linaje, Modelo de datos, Stack y evidencia, Mapa de la app, Arquitectura de seguridad, Git workflow o Centro de operación. Abierto a mano, sigue abierto en esa página. En esas páginas el botón palpita en verde.
  - **Margen:** con el menú plegado, el botón que lo abre va bajo el logo, no a su lado, y la página empieza a 68 px del borde en vez de 112 px.
- **Medición (Playwright):** «Elige tu vista» y Semanal abren con el menú abierto; Calidad y auditoría lo deja abierto; Pipeline y linaje lo pliega; Semanal, abierta desde el menú, lo pliega.
- **Documentos:** PRD 3.28 (7) y las seis capturas, en los dos idiomas.
- **Pruebas:** `tests/test_menu_order.py::test_d462_a_dashboard_opens_with_the_menu_folded_and_its_button_beating_in_green`, con la primera página y las de diagramas.

## D-464 · «Modelo de datos»: sus diagramas toman el alto libre de la pantalla

- **Pedido del autor:** en «Modelo de datos» quedaba un margen grande bajo el diagrama entidad-relación; el diagrama puede verse más grande y nítido.
- **Diagnóstico:** las tres vistas se ajustan al alto de la ventana restando un margen fijo para lo que va arriba y abajo: 427 px la entidad-relación (D-232), 371 px «Dónde viven los datos» (D-236) y 395 px «Cruces entre bases» (D-237). Desde que la página empieza más arriba (D-462, D-463), esos márgenes dejaban entre 166 y 188 px vacíos bajo el diagrama.
- **Decisión:** los márgenes bajan a 287, 235 y 249 px. El dibujo sigue siendo el mismo SVG, que no pierde nitidez al crecer.
- **Medición (Playwright):** a 1440 × 900, la entidad-relación pasa de 473 a 613 px de alto, «Dónde viven los datos» de 529 a 665 px y «Cruces entre bases» de 505 a 651 px; a 1266 × 712, la entidad-relación pasa de 285 a 425 px. Ninguna vista desplaza la página.

## D-465 · El menú se abre solo al entrar a la app; después se pliega al ir a un dashboard o a un diagrama

- **Pedido del autor:** la única vez que el menú está abierto por defecto es al entrar a la app; después, la regla de D-463 está bien. En su prueba, Semanal abría con el menú plegado, porque el navegador recordaba el menú plegado de antes.
- **Decisión:** la pestaña recuerda la página anterior (`sessionStorage`). En la primera página de la pestaña, la entrada a la app, el menú se abre aunque el navegador lo recuerde plegado. Al recargar o volver a dibujar la misma página no cambia. Al ir a otra página, se pliega si es un dashboard o una página de diagramas. En una pantalla angosta o en un teléfono girado manda la regla de antes (D-166).
- **Medición (Playwright):** la entrada (Semanal) abre el menú; Pipeline y linaje lo pliega; al recargarla sigue plegado; una pestaña nueva lo abre otra vez.
- **Pruebas:** `tests/test_menu_order.py::test_d462_a_dashboard_opens_with_the_menu_folded_and_its_button_beating_in_green`, con la regla de la entrada.

## D-466 · Cada carga de la app abre el menú, y cada año tiene su color en «Cambio de cada año»

- **Pedido del autor:** al entrar a la app el menú seguía plegado; y en el gráfico histórico «Cambio de cada año» todas las barras tenían el mismo color.
- **Diagnóstico:** D-465 recordaba la página anterior en la pestaña (`sessionStorage`), así que cargar la app de nuevo en la misma pestaña contaba como ir a Semanal desde otra página, y la plegaba. Las barras se pintaban por subida o bajada, y todos los años subieron.
- **Decisión:**
  - **Menú:** la página anterior se recuerda solo durante una carga de la app. Cada carga, al escribir la dirección o al recargar, es una entrada y abre el menú; dentro de la carga, ir a un dashboard o a un diagrama lo pliega (D-463).
  - **Colores:** cada año tiene su propio color; la altura de la barra dice cuánto subió o bajó, y la raya corta sigue siendo el IPC de ese año.
- **Medición (Playwright):** en la misma pestaña, tras ir a Análisis BA y BI (menú plegado), escribir la dirección de la app abre Semanal con el menú abierto.
- **Pruebas:** `tests/test_ba_trends.py::test_d466_each_year_has_its_own_colour` y la del menú en `tests/test_menu_order.py`.

## D-467 · «Mapa de la app»: los datos recorren su camino real una flecha a la vez, sin marcos, y la ficha corta se abre con la «i»

- **Pedido del autor:** el mapa se veía saturado. Sin cambiar su contenido: la «i», la lupa y el nombre van con el logo y no fuera; se quitan los marcos, cuyos bordes se mezclaban con las flechas; la explicación de una pieza se abre con un clic en su «i», no al pasar el cursor, y mientras está abierta la animación se detiene; la animación sigue el orden real de la app, desde la fuente, por cada etapa, hasta las personas, una flecha a la vez, también donde dos cosas ocurren a la vez. Flechas libres, visibles y precisas.
- **Diagnóstico:** en reposo se movían a la vez todas las flechas marcadas «siempre», sobre todo los accesos de las personas, así que la animación parecía empezar por los usuarios. La explicación aparecía bajo el cursor y tapaba la figura mientras todo seguía moviéndose.
- **Decisión:**
  - **El recorrido:** en reposo, un solo punto recorre las flechas en el orden de los datos: ODEPA mayorista y consumidor → Agente → raw.db → Parquet; INE → Agente → Parquet; Parquet → dbt → Base DuckDB → Release → Panel web → HTML y gráficos → Usuario y Profesional. Hacia las personas va al revés de su línea de acceso, porque los datos salen hacia ellas. Todas las flechas siguen dibujadas; solo se mueve la de su turno. El recorrido espera mientras se mira una pieza, un tema, un ritmo, el «Recorrido del martes» o una explicación. El orden vive en `STORY`, en `bi/app_map.py`.
  - **La «i»:** un clic muestra la explicación corta de la pieza y detiene todo movimiento; un clic fuera o Escape la cierra. Un clic en la pieza sigue abriendo su ficha completa, y la lupa, su interior.
  - **Las piezas:** la «i» y la lupa van sobre las esquinas superiores del logo, como parte de la pieza.
  - **Sin marcos:** se quitan los marcos de dueño (proyecto, plataformas, fuentes y personas) y el fondo de las dos últimas filas. Cada fila conserva su nombre, y cada columna, el suyo.
- **Medición (Playwright):** en reposo se mueve un punto por vez, en el orden del recorrido (raw.db → Parquet, INE → Agente, Agente → Parquet, Parquet → dbt…); con la «i» de dbt abierta, las animaciones quedan en pausa.
- **Pruebas:** `tests/test_app_map.py::test_d467_the_data_travels_its_real_way_one_line_at_a_time_and_a_description_opens_on_its_i` y la de las líneas, sin marcos.

## D-468 · «Mapa de la app»: el recorrido sigue el orden real de la carga semanal, y cada paso parpadea en vez de mover una bolita

- **Pedido del autor:** el recorrido debe partir de donde parte la acción y seguir el orden real del pipeline. Prefiere flechas que parpadean, una por una, a una bolita en movimiento continuo; una bolita sola no se entiende y se quita.
- **El orden real** (leído de `.github/workflows/` y `etl/pipeline.py`): GitHub Actions corre `semanal.yml` el martes a las 12:00 UTC, o lo lanza el Autor a mano. Luego: dependencias de PyPI → la base publicada → `agent/agent.py` baja ODEPA (mayorista y consumidor) y la puerta revisa su encabezado → `etl/etl.py` a raw.db → `etl/pipeline.py` copia raw.db al bronce, agrega el IPC (`etl/ine.py`, parte de la ingesta) y corre dbt, con sus pruebas → Base DuckDB → `pytest -m datos` y la paridad → la puerta publica solo si todo pasó → release → puntero e «Informe semanal» → `calidad.yml` y su pull request → Streamlit Community Cloud toma el commit → el panel baja la base → HTML y gráficos → Usuario y Profesional.
- **Decisión:**
  - **30 pasos en ese orden** (`STORY` en `bi/app_map.py`). El primero ilumina `semanal.yml`, que dispara la carga; cada uno de los demás es una flecha que ya estaba en el mapa.
  - **Parpadeo:** la flecha del paso parpadea, con su punta, y sus dos piezas se iluminan. Bajo el mapa se lee el paso: «8 / 30 · Agente de ingesta → SQLite: CSV → raw.db». Ya no hay bolitas, tampoco al mirar una pieza o el «Recorrido del martes»: la flecha en curso parpadea.
  - **Una por una:** donde una herramienta hace varias cosas, sus flechas parpadean de a una, en el orden en que ocurren.
- **Revisión:** la pieza «Agente de ingesta» reúne `agent/agent.py` y `etl/ine.py`, como dice su ficha; por eso el IPC del INE pasa por ella. No era un error.
- **Medición (Playwright):** los pasos 4 a 11 se suceden uno por vez, cada uno con una sola flecha y su punta parpadeando y sus dos piezas iluminadas.
- **Pruebas:** `tests/test_app_map.py::test_d467_the_data_travels_its_real_way_one_line_at_a_time_and_a_description_opens_on_its_i`, con el orden real y sin bolitas.

## D-469 · «Mapa de la app»: nada responde al cursor, el recorrido parte en GitHub y se ve una flecha por vez

- **Pedido del autor:** el cursor no debe mostrar flechas: el mapa responde solo al clic sobre la «i» o la lupa. El flujo debe verse partir de la acción de GitHub. Y debe ser intermitente: aparece una flecha y desaparece antes de que aparezca la siguiente, en el orden de ejecución.
- **Decisión:**
  - **Solo clics:** una pieza ya no reacciona al pasar el cursor ni a un clic propio, y una flecha tampoco. Solo actúan la «i» (la explicación corta, D-467) y la lupa (el interior). Los filtros, los ritmos y el «Recorrido del martes» siguen con su botón.
  - **Desde GitHub:** una flecha nueva, «GitHub → semanal.yml: martes 12:00 UTC» (el cron de `semanal.yml`; el Autor también puede lanzarla a mano), abre el recorrido y su primer paso. El recorrido tiene 30 pasos y empieza en ella.
  - **Una flecha por vez:** en reposo no se dibuja ninguna otra flecha. La del paso aparece con sus dos piezas iluminadas y el texto bajo el mapa, se mantiene un segundo y medio, desaparece, y tras una pausa aparece la siguiente.
  - **Aire arriba:** el mapa baja 16 px para que la flecha de GitHub, que corre sobre la fila de arriba, no roce los filtros.
- **Medición (Playwright):** el paso 1 muestra solo la flecha de GitHub a `semanal.yml`; luego PyPI, la base anterior y el agente, cada una sola y con una pausa sin flechas entre ellas. Con el cursor sobre dbt no se ilumina nada.
- **Pruebas:** `tests/test_app_map.py` (ningún `mouseenter` en el guion, el recorrido parte en GitHub, una línea por vez con su pausa).

## D-470 · «Mapa de la app»: la puerta de publicación entra en su momento real

- **Revisión del orden** (pedida por el autor: el recorrido debe ser el orden real de la app): «Puerta → Release: publica solo si todo pasa» aparecía después de pytest. La revisión que dibuja esa flecha (fuente atrasada y pocas filas, `etl.MINIMUM_ROWS_RATIO`) corre dentro de `etl/pipeline.py`, justo después de `dbt build` y antes de escribir la Base DuckDB.
- **Decisión:** en `STORY` el paso va después de «Puerta → dbt» y antes de «dbt → Base DuckDB». Los demás pasos ya seguían el orden de `semanal.yml`.
- **Pruebas:** `tests/test_app_map.py::test_d467_the_data_travels_its_real_way_one_line_at_a_time_and_a_description_opens_on_its_i`.

## D-471 · «Mapa de la app»: los 30 pasos de la carga, junto al mapa

- **Pedido del autor:** la lista de los 30 pasos de la carga, en su orden real, merece su propio lugar en el panel. Eligió ponerla junto al mapa.
- **Decisión:**
  - **La lista:** a la derecha del mapa, con el título «La carga semanal, paso a paso» y los pasos en cuatro grupos, según quién los corre: GitHub Actions (el cron del martes), `semanal.yml` (un paso tras otro, del 2 al 21), «Después de la carga» (`calidad.yml` y Streamlit Cloud) y «Cuando alguien abre el panel». Cada paso dice su flecha, lo que lleva y el archivo o comando que lo hace (`agent/agent.py`, `etl/ine.py`, `dbt build`, `gh release upload`, `workflow_run`…). El orden y los grupos viven en `STORY` y `STORY_GROUPS`, en `bi/app_map.py`, los mismos que mueve el mapa.
  - **Sincronía:** el paso que el mapa muestra se ilumina en la lista, que se desplaza sola para tenerlo a la vista. Un clic en un paso muestra su flecha, y el recorrido sigue desde ahí.
  - **La verdad del paralelo:** una nota al pie dice que desde el paso 21 Streamlit Cloud toma el commit mientras GitHub abre el informe y corre `calidad.yml`, el único punto donde dos cosas ocurren a la vez.
  - **Espacio:** el mapa mide solo su parte de la fila, y la lista se oculta en pantalla completa y bajo 900 px de ancho, donde no cabe.
- **Medición (Playwright):** a 1440 × 900, en español e inglés, la lista acompaña al mapa sin achicarlo; un clic en el paso 12 muestra «Parquet → dbt Core» en el mapa y en la lista.
- **Pruebas:** `tests/test_app_map.py::test_d471_the_steps_of_the_load_sit_beside_the_map_grouped_by_who_runs_them`.

## D-472 · «Mapa de la app»: en pantalla completa, la columna derecha es la lista de pasos y no un recuadro vacío

- **Pedido del autor:** el botón «Pantalla completa» mostraba un recuadro vacío, con borde punteado, a la derecha del mapa.
- **Diagnóstico:** desde D-441, la pantalla completa reservaba esa columna (y 370 px de margen) para la explicación de una pieza, que se abría al pasar el cursor. Desde D-467 la explicación se abre solo con la «i», así que la columna quedaba vacía casi siempre, y la lista de pasos (D-471) se ocultaba en ese modo.
- **Decisión:** en pantalla completa se quitan el recuadro y su margen; la lista «La carga semanal, paso a paso» ocupa la columna derecha, a toda la altura. La explicación de la «i» se abre encima mientras se lee, con la animación detenida.
- **Medición (Playwright):** a 1440 × 900, en pantalla completa, el mapa ocupa la izquierda y la lista la derecha; la «i» de dbt abre su explicación sin cubrir la lista entera.
- **Pruebas:** `tests/test_app_map.py` (sin el recuadro vacío y con la fila del mapa y su lista en pantalla completa).

## D-473 · Cierre de la app: el inglés de «Pipeline y linaje», la ficha completa del mapa, «Al abrir el panel», las imágenes del README y el menú en pantallas angostas
- **Pedido del autor:** terminar la app con cinco arreglos cortos.
- **1. Inglés de «Pipeline y linaje»:** el diagrama mostraba en español FUENTES, INGESTA, ATERRIZAJE, INTERMEDIO, CONSUMO, EJECUTA, «Agente ODEPA», «SQLite · tal cual llega» y «Parquet · copia exacta». Ahora cada uno tiene su inglés. La auditoría de idioma no los veía, porque reconoce el español por sus acentos y palabras cortas; queda anotado como F-25.
- **2. Ficha completa en el «Mapa de la app»:** desde D-467 la «i» abre solo la explicación corta, y la ficha con las cifras y sus comandos ya no se podía abrir. La explicación lleva ahora el botón «Ver la ficha completa», que la cierra y abre la ficha. El recorrido espera mientras la ficha está abierta.
- **3. «Al abrir el panel»:** el ritmo «Siempre» hacía pensar que algo corre todo el tiempo. Nada corre así: el Panel web trabaja cuando alguien lo abre. El ritmo se llama ahora «Al abrir el panel» (en inglés, «When the panel opens»).
- **4. Imágenes del README:** las cuatro capturas eran del 31-10, con el menú anterior. Se tomaron de nuevo a 1440 × 900, en la vista Profesional y sin el respaldo `etl/datos.db`, como en producción: Semanal, «Análisis BA y BI (Insights)», «Pipeline y linaje» y «Calidad y auditoría».
- **5. Menú en pantallas angostas (D-166):** el script que pliega el menú en un teléfono horizontal leía `aria-expanded`, que Streamlit ya no escribe. Ahora lee también `data-collapsed`, como el pliegue de los dashboards.
- **Medición (Playwright):** en el «Mapa de la app», la «i» de DuckDB y luego «Ver la ficha completa» abren la ficha, cierran la explicación y detienen el recorrido. En inglés, la auditoría ya no encuentra español en «Pipeline y linaje» ni en el «Mapa de la app».
- **Pruebas:** `tests/test_architecture.py` (el inglés de las etiquetas en mayúsculas) y `tests/test_app_map.py` (el botón de la ficha, la pausa del recorrido y el nombre del ritmo).

## D-474 · Pendientes chicos: latest_by_source en el diagrama entidad-relación, el título de ADR-35, código sin uso y el menú en el teléfono
- **Pedido del autor:** resolver hoy todos los pendientes chicos.
- **Diagrama entidad-relación:** omitía `latest_by_source` sin decirlo. Esa tabla no tiene claves: guarda las 2 últimas semanas de cada fuente, ya con sus nombres (D-365), así que no entra al modelo. La leyenda ahora la nombra fuera del diagrama, en una línea propia para que el texto no pase el ancho. Una prueba exige que cada tabla de la Base DuckDB esté dibujada o nombrada en la leyenda.
- **Título de ADR-35:** decía «base servida», el nombre anterior a D-426. D-455 lo había conservado a propósito; el autor pidió resolverlo, para que haya un solo nombre en todo el proyecto. El título pasa a «Publicar la Base DuckDB en un release que cada carga reemplaza». Su estado recuerda el título original. Los enlaces del SAD y del Índice de decisiones apuntan al ancla nueva, en los dos idiomas.
- **Código sin uso:** `bi/doc_views.py` todavía dibujaba las vistas de contexto y de contenedores del SAD, aunque desde D-289 las dibuja `bi/doc_figures.py`, que las reemplazaba. Se borraron esas vistas y sus ayudas; quedan los logos compartidos y las capturas de los documentos.
- **Menú en el teléfono (D-166, D-473):** se midió con Playwright. A 844 × 390 con pantalla táctil (teléfono en horizontal), el menú se abre. En una ventana de 1000 × 760, se pliega. No hubo que cambiar nada.
- **CLAUDE.md:** la suite tiene unas 1.350 pruebas, y los diagramas de los documentos salen de `bi/doc_figures.py`, `bi/app_diagrams.py` y, para las capturas, `bi/doc_views.py`.
- **Pruebas:** `tests/test_er_diagram.py` (cada tabla, dibujada o nombrada) y `tests/test_doc_views_build.py` (solo las capturas).

## D-475 · Calidad: los precios comparables se miden sobre los que tenían precio la semana anterior, y dos indicadores nuevos de datos
- **Pedido del autor:** hacer hoy las mejoras B y C de las alertas, que habían quedado para después.
- **B. Precios comparables:** hasta ahora la medida dividía por todos los precios de la semana. Un precio que reaparece tras semanas sin dato no puede tener comparación, y eso no es una falla: en la semana del 26-10-2026 fueron 131 de los 145 sin comparación. Ahora la medida cuenta solo los precios que también tenían precio la semana anterior: 723 de 737, 98,1 %. Los que reaparecen se cuentan aparte (`reapariciones`), sin alerta.
- **Nuevo aceptable:** con la regla de ADR-36 (el percentil 5 de la historia), el aceptable y la meta pasan de 81 % a 97 %. Los percentiles de las 251 semanas son mínimo 95,7 %, percentil 5 97,1 % y mediana 98,3 %. Con 97 %, 9 semanas habrían quedado fuera y ninguna bajo el margen crítico (87 %). ADR-36 lleva la revisión y su tabla.
- **C. Regiones o canales ausentes (`ausencias_region_canal`):** cuenta las regiones y los canales con precios en cada una de las 8 semanas anteriores que no tienen ninguno en la última. Antes nada lo detectaba. En la historia pasó en 8 de 244 semanas, casi siempre en feriados: 1 de enero, 18 de septiembre y fin de año. Aceptable 0, margen crítico 2.
- **C. Precios atípicos de la semana (`atipicos_pct`):** el porcentaje de precios de la última semana marcados `ATIPICO` (RN-12). El indicador «Precios apartados» de «Calidad y auditoría» los cuenta sobre toda la historia, donde una semana mala se diluye. Aceptable 0,25 %, el percentil 95 de 252 semanas, con margen crítico de 0,25 puntos. La semana del 26-10-2026 da 0,03 % (1 de 3.300).
- **El plan de calidad pasa a 14 indicadores:** 8 de código y 6 de datos. El informe semanal mide 5 de datos. Los informes C-1 a C-7 son registros cerrados: guardan sus 12 indicadores y sus aceptables, y no se reevalúan. La serie semanal parte en el N° 1 con los 14.
- **«Método y calidad»:** la frase del resumen decía «Medimos los 12 indicadores del plan», contando las filas del informe en pantalla. Ahora nombra el informe: «El informe C-7 mide 12 de los 14 indicadores del plan de calidad». Un informe semanal, que solo trae indicadores de datos, dice que el código se verifica en el CI de cada push.
- **Cifras chicas:** un porcentaje bajo 1 % se muestra con dos decimales (0,25 %), para que el aceptable no se redondee a «0,3» ni la falla a «0,0».
- **Medición:** `docs/calidad/medicion.json` lleva la parte de datos medida de nuevo el 03-11-2026 con `scripts/medir_calidad.py`. Los 6 indicadores de datos cumplen.
- **Pruebas:** `tests/test_quality_method.py` (las metas, la medida nueva, las dos detecciones, los decimales, el SQAP y ADR-36; las series cerradas guardan sus 12).

## D-476 · «Último dato por canal»: la tarjeta dice por qué un canal tiene menos familias
- **Pedido del autor:** la tarjeta Mayorista decía «2 de 7 familias», y el visitante no tenía cómo saber por qué.
- **Causa:** no es un faltante. ODEPA publica cada canal solo con algunas familias. Mayorista tiene solo Frutas y Hortalizas desde enero de 2022; Carnicería, carnes; Panadería, pan. Solo los supermercados tienen las 7 (consulta a la Base DuckDB: familias distintas por canal en `weekly_price`).
- **Decisión:** cuando un canal tiene menos familias que el total, su tarjeta dice por qué, en letra chica bajo los precios: «ODEPA solo publica 2 de las 7 familias en este canal». La cuenta se lee de los datos de esa semana, nunca se escribe a mano.
- **Medición (Playwright):** a 1440 × 900 las ocho tarjetas caben en una pantalla. En inglés, la auditoría de idioma no encuentra español en la página.
- **Pruebas:** `tests/test_channel_latest.py` (la tarjeta dice por qué tiene menos familias).

## D-477 · Alertas de precio: alzas fuertes en rojo y bajas fuertes en verde
- **Pedido del autor:** en la tabla de alertas, una bajada fuerte salía en rojo y con el nivel «Muy alta», como si fuera un peligro. Para quien compra, una bajada es una buena noticia. El autor pidió dos tipos de alerta: roja para las subidas y verde para las bajadas.
- **Nombres (aprobados por el autor):** «alza fuerte» y «baja fuerte». Los niveles de un alza son Muy alta, Alta y Moderada; los de una baja, Baja importante, Baja moderada y Baja leve. Los umbrales no cambian: más de 4, más de 3 y más de 2 desviaciones respecto de las 12 semanas anteriores, y un cambio de al menos 10 % (K6).
- **Panel:** bajo la barra del Semanal hay dos botones, «▲ 7 alzas fuertes» en rojo y «▼ 6 bajas fuertes» en verde. Cada uno abre su ventana: las familias en tarjetas de su color y, al elegir una, su tabla. Los niveles se pintan en tres rojos o tres verdes, de intenso a suave. La columna «Cambio» sigue en rojo cuando sube y en azul cuando baja, como en todo el panel.
- **Inglés:** la ventana de alertas no tenía inglés. Ahora se traducen el título, las tarjetas, la guía de niveles, la unidad y la tabla. La tabla se traduce antes de darle estilo, porque una tabla con estilo no pasa por la capa de inglés.
- **«Informe semanal»:** `bi/report.py` separa las alertas en dos tablas, «Alzas fuertes» y «Bajas fuertes».
- **Documentos:** RF-05 del PRD y el Glosario, con los dos términos nuevos, en los dos idiomas.
- **Medición (Playwright):** a 1440 × 900, en español y en inglés, se abrieron los dos botones y una familia de cada uno.
- **Pruebas:** `tests/test_home_mockup.py`, `tests/test_dashboard.py` y `tests/test_report.py`.

## D-478 · Todo parte por familia y baja a los productos, con el mismo buscador
- **Pedido del autor:** mostrar todas las vistas primero por familia, con la opción de bajar a los productos o de buscar uno, para cuadrar en vivo cualquier cifra con un gerente. Además, la ventana verde decía «6 bajas fuertes» y la tabla por familias no las mostraba: las alertas miran cada producto y la tabla, el promedio de la familia, y las alzas y bajas de una misma familia se compensan.
- **La regla:** cada vista parte por familia, con «Toda la canasta» por defecto. Una familia o una búsqueda baja a sus productos. Donde se listan productos de varias familias, cada uno dice su familia. El buscador es el mismo en todas partes: la lupa del paso 3 de «La semana», con su regla (cada palabra empieza una palabra del producto o su variedad), ahora en un solo lugar (`overview.matches_search`).
- **«La semana»:** con «Toda la canasta», la tabla de productos lleva la columna «Familia».
- **«Últimas semanas»:** un selector de familia y la lupa. Con una familia, la tabla muestra arriba la fila de la familia («Frutas · toda la familia», la misma de la tabla por familias) y bajo ella sus productos, cada uno con la mediana de sus cambios de cada semana, la misma regla de la familia. Con la lupa, los productos encontrados en toda la canasta, cada uno con su familia.
- **Ventanas de alertas:** la lupa sobre las tarjetas busca en todas las familias y la tabla trae la columna «Familia». Dentro de una familia, la lupa filtra sus productos. La ayuda de un botón ya no queda encima de la ventana que abrió.
- **Niveles de las alertas:** toda alerta es de al menos 10 % y fuera de lo habitual, así que «Baja leve» o «Moderada» contradecían el nombre «fuerte». Los niveles pasan a Alza extrema, Alza muy fuerte y Alza fuerte, y Baja extrema, Baja muy fuerte y Baja fuerte. El nivel mínimo se llama como la alerta. Los umbrales no cambian.
- **«Mensual» e «Histórico»:** bajo «Familia», un selector «Producto» en el que se puede escribir para buscar. Un producto se calcula con la regla de la familia: su índice es la mediana de sus propias series de consumidor frente a enero 2022, y K1, K4 y K6 se leen de sus filas. La tabla muestra la familia y, debajo, sus productos (el elegido primero). Lo que se cuenta suma exacto: las alertas y los pares K1 de una familia son la suma de los de sus productos (comprobado en las 7 familias). Un producto sin precio en enero 2022 o en el último mes no tiene índice y muestra «—», sin estimar.
- **«Precios e inflación»:** la familia ampliada tiene un selector «Producto»: la línea del producto frente al IPC, en el color de su familia y con su propia escala, y su lectura de los datos.
- **«Insights»:** las mayores bajas dicen la familia de cada producto.
- **Queda igual:** el mapa de regiones y las tarjetas de canal, porque su orden es por región y por canal; «Consultas SQL», que es una página de ingeniería.
- **Medición (Playwright):** a 1440 × 900, en español y en inglés, sin errores: la búsqueda en la ventana de alertas, la tabla de «Toda la canasta», «Últimas semanas» con Frutas, «Mensual» con Frutas y con Plátano, y un producto ampliado en «Precios e inflación».
- **Pruebas:** `tests/test_overview.py` (la tabla por producto recalculada, la búsqueda y la familia en los Insights), `tests/test_ba_trends.py` (la familia es la suma de sus productos y el índice de un producto recalculado a mano), `tests/test_home_mockup.py` (la columna «Familia», los niveles y «Últimas semanas» con una familia).

## D-479 · Las alertas dicen su regla en las palabras de cada vista
- **Pedido del autor:** en «Semanal» nadie podía saber que una alza o baja fuerte se mide contra las 12 semanas previas: la ayuda decía solo «fuera de lo habitual» y la ventana, «El color indica cuán inusual fue la baja». No debe haber cálculos silenciosos. La baja fuerte se presenta como lo que es para quien compra: una oportunidad.
- **La regla no cambia (K6):** el precio cambia al menos 10 % frente a la semana anterior y ese cambio queda a más de 2 desviaciones estándar del promedio de los cambios semanales de sus 12 semanas previas. Las 12 semanas no son el precio de la página: son la referencia para decir que un cambio es fuera de lo normal.
- **Usuario:** palabras simples con el término de estadística entre paréntesis: «El precio bajó al menos 10 % frente a la semana anterior: más de 2 veces lo que ese producto suele moverse en sus 12 semanas previas (desviación estándar). Una oportunidad de compra.» El alza termina en «Conviene comparar antes de comprar.».
- **Profesional y Autor:** la fórmula: «K6 · variación semanal ≤ −10 % y a más de 2 desviaciones estándar del promedio de las variaciones de sus 12 semanas previas; precio nacional, con dos cotizaciones en cada semana.».
- **Dónde:** la ayuda de los dos botones de alertas, el texto bajo las tarjetas de la ventana y la leyenda de niveles, que ahora da el umbral de cada nivel: «más de 2×», «3× o más», «4× o más» para el Usuario, y «> 2 σ», «≥ 3 σ», «≥ 4 σ» para Profesional y Autor, con lo que significa el número.
- **Una sola fuente:** los textos se arman con las constantes de `bi/alerts.py` (`describe_kind`, `describe_scale`) y los umbrales de los niveles, como la regla de D-385.
- **Pruebas:** `tests/test_kpi_vocabulary.py` comprueba que cada texto lleva los números del código, que el inglés existe y que cada nivel muestra su umbral.

## D-480 · Ningún cálculo silencioso en las páginas de negocio
- **Pedido del autor:** revisar toda la app después de D-479: cada cifra debe decir en pantalla sobre qué se calcula (la ventana, el agregado, el umbral y el alcance), con palabras simples y el término técnico entre paréntesis. Una revisión de las páginas encontró unas 30 cifras sin esa explicación y cuatro errores.
- **Errores corregidos:** (1) con una región elegida, la ayuda del precio del paso 3 decía «promedio de las regiones»; ahora dice «Precio publicado en la región elegida». (2) «¿La inflación de los alimentos está bajando?» respondía «Sí» escrito fijo; ahora se calcula (Sí, No o bajó) y nombra los dos meses que compara. (3) «3 de ellos en Santiago» estaba escrito fijo; ahora se cuenta del archivo de mercados. (4) «En promedio» describía una mediana; ahora dice «Mediana de la brecha (K1), semana …».
- **Una sola regla de «sin cambio»:** «Últimas semanas» marcaba «·» bajo 0,3 % y «La semana» decía «Sin cambio» solo bajo 0,05 %: un +0,2 % se leía «Subió» en una y «·» en la otra. Las dos usan ahora 0,05 %, también para contar las semanas de alza y de baja de la «Lectura del período». Una celda sin dato se marca «—», ya no con el mismo punto.
- **«La semana»:** la «i» del mapa explica la cifra (el % del grupo más grande, frente a la semana anterior), el umbral de 0,05 % y por qué una región queda gris «=» (prueba de signos, p < 0,05); la leyenda «Sin cambio claro» lo dice al pasar el cursor. La «i» de las familias dice mediana, frente a la semana anterior, el umbral y que la línea pequeña son las últimas 8 semanas de todo Chile, también al pasar el cursor por ella. El paso 3 tiene su propia «i»: qué es un precio, la mediana, «Regiones ↑ / ↓» (todo Chile, 0,05 % o más, sin contar las que no cambiaron) y el «m» de «n de m regiones».
- **«Últimas semanas»:** el texto dice «mediana, todo Chile» y su ayuda explica cada celda, la fila de un producto, «·», «—» y «Total», que al pasar el cursor da la fórmula de los cambios encadenados.
- **«Último dato por canal»:** cada tarjeta dice de cuántos precios comparables es la mediana y que «N precios por región» cuenta los precios publicados; la barra dice su escala.
- **«Precios e inflación», «Mensual» e «Histórico»:** la ayuda «Sin inflación» describe lo que se dibuja (el índice dividido por el IPC, por 100); «Métrica» y el texto del gráfico dicen la muestra fija (series con precio en enero 2022 y en el último mes) y que la mediana no pondera; la tarjeta «Cambio de precios» y la ayuda de «Familia» lo repiten.
- **«Insights»:** «típico» pasa a «mediana frente a la semana anterior»; «más que el IPC» dice su umbral de 2 puntos; se quita «son las que más pesan hoy en la canasta», que no se calculaba en ninguna parte; las mayores bajas mayoristas dicen su regla de dos cotizaciones.
- **Pruebas:** `tests/test_overview.py` (el mismo umbral en las dos pestañas, «—» y la fórmula de «Total»), `tests/test_home_mockup.py` (el precio regional, la «i» del paso 3 y la línea pequeña nacional), `tests/test_channel_latest.py`.

## D-481 · Revisión antes del push: documentos, registro de fallas, seguridad y CI
- **Pedido del autor:** antes de subir D-443 a D-480, revisar todo el proyecto: cada botón, el diseño, la seguridad, la fiabilidad de los datos, la explicación de cada cifra, el registro de fallas y las mejoras.
- **Seguridad:** la revisión de los 38 commits no encontró secretos, datos personales, inyección de HTML ni acceso del Autor sin su clave; las 34 pruebas de `tests/test_security.py` pasan. Un comentario decía que un ticket del Autor se usa una vez; desde D-428 sirve hasta que vence, y el comentario lo dice ahora.
- **CI:** ruff, el formato y mypy sin observaciones; cobertura de 95,2 % (el mínimo es 90 %). Los commits no tocan dbt, los workflows ni las dependencias.
- **Documentos:** el Índice de decisiones pasa a 2.5: nombra la página «Semanal» (antes «Panorama» y «Dashboard»), deja de contar 11 y 12 indicadores y suma ADR-36 (D-433, D-475), D-443, D-477, D-478 y D-480; dice 105 decisiones, las que tienen sus tablas. ADR 3.6 cuenta doce decisiones, no once. El Glosario 2.14 da los límites de cada nivel de alerta como los muestra la ventana (4 o más, 3 o más, más de 2). El PRD 3.31 describe la columna «Familia», la «i» de cada paso y el selector «Producto».
- **Registro de fallas:** se anotan las fallas resueltas de D-443 a D-480 que faltaban: una ocurrencia nueva de F-18 (D-454) y de F-02 (D-471), y cuatro fallas nuevas: F-27 (un texto dice algo distinto de lo que se calcula: D-445, D-475, D-480), F-28 (un arreglo rompe otra vista: D-466, D-472, D-473), F-29 (un texto queda en español en la página en inglés: D-443, D-477) y F-30 (Streamlit deja de escribir un atributo que un script lee: D-473).
- **Código:** las tarjetas de canal pintaban el cambio con un umbral propio escrito a mano; ahora usan `overview.STILL`, el mismo «sin cambio» de 0,05 % del resto del panel.

## D-482 · Cada cifra de las alertas y de los índices se explica como se calcula
- **Origen:** la guía para explicar cada cifra en una demo (D-481) recalculó las cifras desde la Base DuckDB y encontró tres explicaciones que no coincidían con el cálculo.
- **«Anterior» de la ventana de alertas:** se calculaba hacia atrás, el precio nacional de la semana dividido por (1 + cambio). Si las regiones cambiaban entre semanas, salía un precio que nunca se publicó: Pimiento mostraba $1.132 → $1.003, y «La semana» $1.076 → $954. Ahora «Anterior» y «Actual» son los dos precios de los que sale el cambio: el promedio de las regiones con precio en las dos semanas (D-144), los mismos de «La semana». Una fila sin esos precios muestra «—»; nunca se estima.
- **Texto del Usuario de las alertas:** decía «más de 2 veces lo que ese producto suele moverse», como si se midiera el cambio desde cero. El cálculo mide la distancia al cambio promedio de las 12 semanas previas, en desviaciones estándar, como dice el texto del Profesional. Ahora el Usuario lee: «…y ese cambio se alejó del cambio promedio de sus 12 semanas previas más de 2 veces lo que suele variar (desviación estándar)», y la leyenda de niveles dice lo mismo.
- **«Muestra fija»:** el índice exige precio en enero 2022 y en el último mes, pero un mes intermedio usa las series con precio ese mes (395 a 409 de las 409 de la canasta). Los textos dejan de decir «muestra fija» y dicen la regla tal cual.
- **Detalles:** «Mensual» e «Histórico» dicen «alzas fuertes» y «bajas fuertes», los nombres oficiales (D-477), en vez de «subidas» y «bajadas»; las mayores bajas de «Insights» dicen la variedad, para que dos variedades del mismo producto no parezcan repetidas; un comentario del código que decía que la tabla muestra precios nacionales dice ahora la regla de D-327.
- **Guía de la demo:** `docs/privado/guia_demo_cifras.md`, fuera de git: cada cifra del panel en lenguaje natural y profesional, cómo se calcula y la pregunta probable de un gerente, con el ejemplo de Pimiento (−11,4 %, a 4,63 desviaciones: Baja extrema) y Zapallo italiano (−33,7 %, a 2,44: Baja fuerte).
- **Pruebas:** `tests/test_kpi_vocabulary.py` comprueba que «Anterior» y «Actual» son los precios del cambio en todas las alertas de la semana y que el texto del Usuario dice la distancia al cambio promedio.

## D-483 · Revisión con el navegador: inglés, diagramas, calidad y celular
- **Origen:** la revisión antes del push recorrió cada página, botón y pestaña en las vistas Usuario y Profesional, en español y en inglés, y en un teléfono horizontal. No hubo errores de página. Encontró estos defectos, todos corregidos aquí.
- **Inglés:** las opciones de «Orden» (Subidas, Bajadas, Nombre, Inusuales), el pie «Cobertura:» y etiquetas de «Pipeline y linaje» y del modelo entidad-relación quedaban en español. La auditoría de idioma no reconoce como español una frase corta sin acentos (F-29). El pie decía en inglés «in 233 regions» por «en 233 cambios»: la frase en español dice ahora «en 233 cambios se dejaron fuera las regiones con precio en una sola semana».
- **Canales con el mismo nombre en todo el panel:** el selector «Canal» del paso 3 y de su ventana ampliada nombra cada canal como la tabla (D-403). Las mayores bajas de «Insights» dicen su familia y su canal en el idioma de la visita. La ayuda de cada familia usa su nombre corto, como la fila.
- **Aviso de GitHub en otro idioma:** el flujo en vivo guardaba en memoria la respuesta de GitHub con su aviso ya escrito, y una visita en español leía «GitHub answered 403…». La memoria guarda ahora cada respuesta por idioma (F-31).
- **«Método y calidad»:** decía «Hoy: 10 de 12…» para el informe C-7, cerrado el 31-10-2026, mientras «Calidad y auditoría» muestra el estado de hoy. Ahora dice la fecha del informe y que C-7 es un registro cerrado de la serie de construcción, medido con las reglas de entonces.
- **Diagramas (D-440):** en «Arquitectura de seguridad», el subtítulo de «Mejora continua» sigue al título, la flecha de la API dice su trabajo en dos líneas («lanzar y cancelar», «leer estado y logs», como permite D-370), los secretos del panel muestran también GITHUB_READ_TOKEN, que se cortaba, y T6 se separa del círculo 7. En el flujo en vivo, el nombre de cada grupo se dibuja sobre las flechas, con un halo del color de la página (F-32).
- **Pantallas:** en «Consultas SQL», los filtros tienen el ancho de «Producto: todas»; en la ventana ampliada de productos, «Canal» no se parte. En un teléfono horizontal, los meses de «Mensual» se encimaban: el eje nombra cada mes mientras caben y, si no, uno de cada dos (antes, siempre todos, D-460). «Mensual» e «Histórico» dicen «alzas fuertes y bajas fuertes» también en el subtítulo del gráfico de alertas.
- **Queda para el autor:** (1) en 1440 × 900, la línea de cobertura bajo el paso 3 de «Semanal» queda 31 px bajo el borde; ya era así, y la página entra completa a partir de unos 960 px de alto. (2) Un enlace compartido a una página (`?vista=…`) pide la vista y abre «Semanal», no la página del enlace; D-340 hace obligatoria la ventana, pero no dice adónde va después. (3) `tests/medicion/desbordes.cjs` abre las páginas con `?perfil=`, que D-340 ignora, así que solo mide la ventana de entrada.
- **Pruebas:** `tests/test_quality_method.py` (la fecha del informe y «registro cerrado»), `tests/test_ba_trends.py` (los meses del eje y el nombre de las alertas).

## D-484 · La ventana de alertas llama «Variación» a la misma cifra que la tabla de productos
- **Pedido del autor:** la última columna de la tabla de alertas se llamaba «Cambio», y la tabla de productos de «La semana» llama «Variación» a la misma cifra: el cambio del precio frente a la semana anterior, en las mismas regiones. Ahora las dos dicen «Variación» (en inglés, las dos ya decían «Change»), para cuadrar una fila con la otra sin traducir de cabeza.
- **Pruebas:** `tests/test_home_mockup.py` (las columnas de la tabla de alertas y su color).

## D-485 · La carga semanal tiene tres intentos el martes y nunca corren dos a la vez
- **Problema:** GitHub atrasa o se salta las tareas programadas cuando tiene mucha demanda, sobre todo a la hora en punto. Las cargas automáticas de este repositorio partieron con horas de atraso: 13-10 a las 18:33 UTC, 20-10 a las 15:53 y 27-10 a las 16:54, todas programadas a las 12:00. El 03-11, a las 13:49 UTC, la de ese día aún no partía. Además, nada impedía que una carga lanzada a mano corriera junto con la automática, y las dos subirían la base a la vez.
- **Decisión (pedida por el autor):** `semanal.yml` se programa con `17 12,14,16 * * 2`: martes a las 12:17, 14:17 y 16:17 UTC (09:17, 11:17 y 13:17 en Chile en horario de verano), fuera de la hora en punto. Su primer paso es un guardia: un intento programado que encuentra una carga de `semanal.yml` en verde ese mismo día (UTC) termina en segundos sin hacer nada, así no se registran cargas repetidas en `etl_run` ni se publica dos veces. Una carga lanzada a mano corre siempre. Un intento fallido no impide el siguiente. La regla `concurrency` hace que un intento que parte mientras otro corre espere su turno. El guardia lee las ejecuciones del workflow, por eso el permiso suma `actions: read`.
- **Sin servicios externos:** lanzar la carga desde un servicio de tareas programadas de terceros exigiría darle un token de GitHub; no se hace (ADR-31, D-397).
- **Panel y documentos:** la próxima carga se calcula a las 12:17 UTC; el paso del guardia tiene su nombre en español e inglés; el PRD (RF-01), el SAD, el MANUAL, el Glosario, el mapa de la app, el flujo en vivo, DevOps y el glosario técnico dicen la hora nueva y los intentos.

## D-486 · Un gráfico de «Análisis BA y BI» funciona también con pandas 3.1
- **Problema:** las pruebas del CI fallaron en los pushes de D-484 y D-485, en Python 3.11 y 3.12; en el equipo del autor pasaban. El CI instala la versión más nueva que permite `requirements.txt` (pandas 3.1), y el equipo tenía pandas 3.0. Con pandas 3.1, cuando el mes de partida no tiene precio, el gráfico de «Análisis BA y BI (Mensual)» e «(Histórico)» buscaba el valor base en una selección vacía, recibía texto en vez de número y no podía dividir.
- **Decisión:** el valor base se convierte a número antes de dividir. Una selección vacía da un gráfico vacío, como antes, en las dos versiones.
- **Cómo se halló:** los logs del CI piden token (F-14), así que la suite se corrió en un entorno igual al del CI: Python 3.12, las versiones que instala y la hora en UTC.
- **Pruebas:** `tests/test_ba_trends.py`, que ya fallaba en el CI, pasa con pandas 3.0 y 3.1.

## D-487 · La carga semanal intenta todo el martes, cada 15 minutos hasta mediodía
- **Problema:** el 03-11-2026 GitHub no lanzó ningún intento programado de la carga: ni el de las 12:00 UTC ni los de D-485 (14:17 y 16:17). Los datos deben estar listos antes de la tarde.
- **Decisión (pedida por el autor):** `semanal.yml` tiene tres líneas de cron: `7,22,37,52 12-14 * * 2` (un intento cada 15 minutos de 12:07 a 14:52 UTC, 09:07 a 11:52 en Chile en verano), `7 15-23 * * 2` y `7 0-2 * * 3` (uno cada hora hasta las 02:07 UTC del miércoles, 23:07 en Chile), siempre fuera de la hora en punto. En invierno todo ocurre una hora antes en Chile. Si el martes termina sin carga, el Autor la lanza a mano con «Ejecutar pipeline ahora»; una vez por semana es parte de su operación.
- **Guardia:** busca una carga en verde desde el martes (UTC), no solo del mismo día, porque GitHub puede lanzar el miércoles un intento atrasado del martes; así nunca se repite una carga. El paso se llama «Revisa si la carga de este martes ya se hizo». Una carga lanzada a mano corre siempre.
- **Descartado:** un servicio externo de tareas programadas (necesita un token de GitHub fuera del repositorio) y el computador del autor (debe funcionar con el computador apagado).
- **Panel y documentos:** la próxima carga se calcula a las 12:07 UTC; el PRD (RF-01), el SAD, el MANUAL, el Glosario, DevOps, el mapa de la app, el flujo en vivo y el glosario técnico dicen la hora y los intentos nuevos.
- **Pruebas:** `tests/test_control.py`, `tests/test_devops.py` (las líneas de cron y el guardia desde el martes) y `tests/test_prd_traceability.py`.

## D-488 · La medición de calidad vuelve a verde y el linaje queda en inglés con la base nueva
- **Problema:** `calidad.yml` falló en los pushes del 03-11 por dos indicadores críticos de código. Bandit marcaba como alto el SHA-1 que da a cada página una llave neutra (D-443), y el detector de secretos tenía un candidato sin clasificar: la palabra «Secreto» del diccionario de inglés. Además, con la base de la carga del 03-11, la ficha de `latest_by_source` en «Pipeline y linaje» quedaba en español en la página en inglés: su descripción dbt llegó a la base con esa carga y nunca tuvo traducción (F-29).
- **Decisión:** el SHA-1 declara `usedforsecurity=False`, porque solo nombra una página y no protege nada. «Secreto» queda en `.secrets.baseline` como candidato revisado y no secreto. La descripción de `latest_by_source` tiene su inglés en `bi/i18n_en.py`.
- **Pruebas:** `tests/test_i18n.py` (la auditoría de idioma con la base nueva) y la medición de `scripts/medir_calidad.py`.

## D-489 · Las alertas de cada familia se ven en el paso 2 y se listan en el paso 3, sin ventanas
- **Pedido del autor:** las dos ventanas de D-477 mostraban las mismas familias, con el mismo ícono, en rojo y en verde, y no se entendía qué estaba pasando. Una familia puede bajar en conjunto y tener productos con alza fuerte, porque la alerta es de cada producto y la barra es la mediana de la familia.
- **Decisión:** en el paso 2 de «Semanal», entre el nombre de cada familia y su barra, aparecen sus alertas de la semana: ▲ n en rojo (alzas fuertes) y ▼ n en verde (bajas fuertes), solo si tiene. Al pasar el cursor, cada marca dice qué hará el clic («Muestra en la tabla solo las 4 alzas fuertes de Frutas…»). Al pulsarla, el paso 3 muestra solo esos productos, con su nivel, el precio anterior y el actual, la variación y la regla K6 en palabras (D-479); «Ver todos los productos», o la fila de la familia, devuelven la tabla normal. Los botones «▲ n alzas fuertes» y «▼ n bajas fuertes» hacen lo mismo con toda la canasta. Las ventanas de D-477 desaparecen.
- **Precio nacional:** las alertas usan el precio nacional (K6) aunque la región elegida sea otra; el paso 3 lo dice («precio nacional de ODEPA») y la «i» del paso 2 explica la diferencia entre la barra y las marcas.
- **Tabla:** la unidad va junto al producto y la familia ya no es columna, porque se elige en el paso 2; así la tabla cabe en el panel.
- **Pruebas:** `tests/test_home_mockup.py` (las marcas son enlaces propios, nunca dentro del enlace de la fila; el paso 3 sin ventana), `tests/test_dashboard.py` y `tests/test_panorama_steps.py` (las columnas de la fila).

## D-490 · «Semanal» deja la tabla de las últimas semanas
- **Pedido del autor:** la pestaña «Últimas semanas» de «Semanal» (D-308, D-478) no aporta: la evolución semana a semana ya está en la línea pequeña de cada familia del paso 2 (las últimas 8 semanas), y la de meses y años en «Análisis BA y BI (Mensual)» e «(Histórico)».
- **Decisión:** «Semanal» muestra solo la semana. La fila bajo el encabezado guarda las alertas de la semana y el aviso de una fuente atrasada (D-398). Se retira el código que solo usaba la tabla (`show_weeks_panel`, `show_weeks_table` y, en `bi/overview.py`, `product_heat`, `weeks_insight`, `period_totals`, `build_heat_table_html`, `heat_table_css` y `QUIET`) con sus pruebas.
- **Pruebas:** `tests/test_overview.py` comprueba que la tabla ya no existe en el panel.

## D-491 · Las alertas de la familia elegida, entre el paso 2 y el paso 3
- **Pedido del autor:** las marcas ▲ ▼ de cada familia (D-489) y los botones de arriba hacían lo mismo, y los botones de arriba rompían el orden de lectura 1 → 2 → 3.
- **Decisión:** salen las marcas de cada familia y los botones de arriba. Entre el paso 2 y el paso 3 queda una línea delgada con «▲ n alzas fuertes» y «▼ n bajas fuertes» de la familia elegida, o de toda la canasta. Están apagadas, y lo dicen al pasar el cursor («Elige primero una familia.»), hasta que se elige una familia (D-352). Al pulsar una, el paso 3 muestra solo esos productos, como en D-489; al pulsarla de nuevo, vuelve la tabla de todos los productos, y elegir otra familia también la devuelve. La que está activa se ve con borde.
- **«Inusuales»:** sale del menú «Orden» del paso 3, porque las alertas tienen sus propios botones y sus nombres oficiales (D-477).
- **Tabla:** la columna del producto tiene un ancho fijo, con el nombre completo al pasar el cursor, para que «Variación» nunca quede fuera del panel.
- **La «i» del paso 2** dice que la barra es la mediana de la familia, y que bajo el panel ▲ y ▼ muestran sus alzas y bajas fuertes.
- **Pruebas:** `tests/test_home_mockup.py` (las alertas esperan una familia, filtran el paso 3 y vuelven; las familias ya no llevan marcas), `tests/test_dashboard.py` (sin «Inusuales»; la ayuda de las alertas apagadas).

## D-492 · La búsqueda junto a las alertas, y el paso 3 sin textos de más
- **Pedido del autor:** al pulsar una alerta, la búsqueda desaparecía; la tabla se montaba sobre la línea de cobertura; y el paso 3 repetía lo ya elegido («Toda la canasta», cuántas alzas) y mostraba una guía de niveles y una línea sobre la desviación estándar que nadie lee.
- **Decisión:** la búsqueda, en verde y con su pulso (D-372, D-450), pasa a la línea de las alertas, entre el paso 2 y el paso 3, y nunca desaparece. Sin alerta elegida busca en todos los productos, como antes; con «▲ alzas fuertes» o «▼ bajas fuertes» elegida busca solo dentro de esas alertas, con la misma regla de búsqueda (D-478). El paso 3 se llama «Productos» («Mira los productos» decía lo obvio). Con una alerta elegida, su encabezado muestra solo «3 Productos» y, en la esquina derecha, «precio nacional de ODEPA»; salen la familia, el conteo, la guía de niveles, la línea de la desviación estándar y la regla bajo la tabla.
- **Sin cálculos silenciosos (D-479):** el umbral de cada nivel se dice al pasar el cursor por «Nivel» («Alza extrema: 4× o más…» en la vista Usuario, en σ en la Profesional), y la regla K6 al pasar el cursor por cada botón de alerta.
- **Tabla:** se dibuja como la tabla de productos, con su desplazamiento dentro del panel, así nunca pasa sobre la línea de cobertura; cada nivel es un tono del color de su alerta.
- **Pruebas:** `tests/test_home_mockup.py` (la búsqueda filtra dentro de la alerta y la tabla cuenta sus filas), `tests/test_kpi_vocabulary.py` (los umbrales al pasar el cursor), `tests/test_panorama_steps.py` (la búsqueda, su color y su pulso).

## D-494 · El canal es el paso 2 de «Semanal», y la sección queda con dos dashboards
- **Pedido del autor:** «Último dato por canal» era un segundo dashboard semanal con los mismos pasos (D-405). Se simplifica: el canal pasa a ser un paso de «Semanal», y «Negocio · BA y BI» queda con dos dashboards, «Semanal» y «Análisis BA y BI».
- **Decisión:** «Semanal» se lee en cuatro pasos: 1 Región, 2 Canal, 3 Familia y 4 Productos. El canal es el único paso opcional: sin elegirlo se ven todos («Todos los canales»), como antes. El paso 2 espera la región, como el 3; el 4 espera una familia (D-352). Al elegir un canal, la página entera se dibuja con sus precios y su propia última semana, aunque la otra fuente todavía no la publique (D-365, D-405), la ruta dice «Semanal › Feria libre» y la línea bajo el encabezado dice qué familias publica ese canal (D-406). Elegir un canal no recarga la página: su enlace se captura como el de una región o una familia, y conserva la región y la familia.
- **Qué tiene cada canal:** bajo el nombre de ODEPA, en letra pequeña, va lo que el canal vende cuando no vende de todo: «Mayorista · frutas y hortalizas», «Mercado Mayorista · legumbres», «Carnicería · carnes» y «Panadería · pan», y su variación. El nombre de ODEPA queda primero, para que cada precio se pueda rastrear hasta la fuente, y una prueba compara cada etiqueta con los datos.
- **Opcional, y lo dice:** bajo el título del paso 2 se lee «Opcional: sin elegir, se ven todos.», y «Todos los canales» lleva un cuadrito que se marca cuando está elegido. Antes de elegir la región, el paso 2 espera atenuado, sin candado propio: el del paso 3 ya dice qué hacer.
- **Pantalla:** el mapa cede un poco de ancho; los pasos 2 y 3 quedan lado a lado con la misma altura; cada canal va en un bloque chico con su logo, de a dos por fila, con letra delgada y del tamaño de la lista de regiones, para que los pasos 2 y 3 no crezcan y la tabla conserve su alto (hasta 1366 px de ancho, lo que vende cada canal queda al pasar el cursor), y debajo de ambos la línea de alertas y la tabla de productos ocupan todo el ancho (D-489 a D-492).
- **Lo que sale:** la página «Último dato por canal», su recuadro en el menú y sus tarjetas. Su dirección antigua abre «Semanal» con el mismo canal (`RETIRED_VIEWS`). La tabla servida `latest_by_source` sigue: alimenta el paso 2.
- **Pruebas:** `tests/test_channel_latest.py` (el paso 2, su dirección antigua, lo que dice cada canal frente a los datos), `tests/test_panorama_steps.py` (los cuatro pasos y sus candados), `tests/test_menu_order.py`, `tests/test_dashboard.py` y `tests/test_overview.py` (el menú con dos dashboards).

## D-495 · La tabla de productos solo ordena, y nunca se sale de su panel
- **Pedido del autor:** con el canal en el paso 2 (D-494) y las alzas y bajas fuertes en sus botones (D-491), los filtros de la tabla repetían lo ya elegido. Y en una ventana baja, la nota de cobertura se montaba sobre la tabla.
- **Decisión:** la tabla del paso 4 conserva solo «Orden», con «Mayor cambio» y «Nombre»; salen el selector «Canal» y los órdenes «Subidas» y «Bajadas», también en la tabla ampliada. En la pantalla, la fila de los pasos 2 y 3 mide lo que su contenido y no crece; el panel de productos toma el resto y nunca menos de 210 px, así en una ventana baja la página se desplaza un poco en vez de montar un texto sobre otro; en una ventana angosta (1100 px o menos) los paneles se apilan y la tabla se limita a 420 px con su propio desplazamiento.
- **Medido:** con Playwright a 1000 × 650, 1280 × 700, 1280 × 800, 1440 × 900 y 1920 × 1080, el borde inferior de la tabla queda dentro de su panel y la nota de cobertura debajo, y ningún nombre de canal se sale de su bloque.
- **Pruebas:** `tests/test_dashboard.py` y `tests/test_home_mockup.py` (el único selector de la tabla y el orden por nombre), `tests/test_control.py` y `tests/test_menu_order.py`.

## D-496 · Una tablet horizontal ve «Semanal» en columnas, como el escritorio
- **Pedido del autor:** a unos 1060 px de ancho, «Semanal» se apilaba como en un teléfono: el mapa ocupaba todo el ancho y crecía, y los pasos quedaban abajo. Una tablet horizontal tiene entre 1024 y 1100 px y, con el menú plegado (D-463), le sobra ancho para las tres columnas.
- **Decisión:** los paneles se apilan solo bajo 900 px de ancho, un teléfono. De 901 px hacia arriba valen las reglas de una pantalla (D-309, D-407): el mapa, el paso 2 y el paso 3 lado a lado, y la tabla debajo con el alto que la ventana deja. Las otras páginas que se reordenan a 1100 px (la galería de familias y el Centro de operación) no cambian.
- **Tablet con el menú abierto:** la app abre con el menú desplegado (D-466), así que el ancho de la tabla no depende solo de la ventana. De 901 a 1150 px, las familias dejan la palabra de su estado («Subió», «Bajó») y un nombre largo pasa a dos líneas; en un paso 2 muy angosto, los bloques reducen su margen. La tabla de productos se ajusta al ancho de su propio panel: bajo 600 px, letra y márgenes más chicos y «Ver cálculo» en su propia línea; bajo 530 px, además, los títulos en dos líneas. Así ninguna columna se corta, con el menú abierto o plegado (RNF-06).
- **«Orden» vuelve a tener «Subidas» y «Bajadas» (corrige D-495):** ordenan todos los productos por su variación normal, la mayor alza o la mayor baja primero. No repiten los botones de alertas, que muestran solo los cambios fuera de lo habitual (K6, D-491). «Orden» queda con «Mayor cambio», «Subidas», «Bajadas» y «Nombre».
- **Medido:** con Playwright a 1024 × 768 con el menú plegado y abierto, a 1060 × 800 y 1150 × 800 con el menú abierto, a 1280 × 800 y 1440 × 900 y a 1920 × 1080, en español y parte de ellos en inglés: ningún nombre de canal o familia queda cortado, ninguna columna de la tabla se pierde, los pasos 2 y 3 miden lo mismo y la nota de cobertura queda debajo.
- **Pruebas:** `tests/test_dashboard.py` (los cuatro órdenes, y «Bajadas» de la menor variación a la mayor).

## D-497 · Un filtro por subidas y bajadas junto a la búsqueda, en vez de «Orden»
- **Pedido del autor:** «Orden» tenía «Nombre», pero un nombre ya se busca escribiéndolo, y las alzas y bajas fuertes ya tienen sus botones. Lo que falta es ver todas las subidas o todas las bajadas, incluidas las fuertes, y que el control esté al lado de la búsqueda.
- **Decisión (corrige D-495 y D-496):** sale «Orden», con «Mayor cambio» y «Nombre». En la línea de alertas, junto a la búsqueda, queda un filtro con «Todo» (por defecto), «Subidas» y «Bajadas», también en la tabla ampliada. «Subidas» y «Bajadas» dejan todos los productos que subieron o bajaron, los fuertes incluidos; un cambio que se redondea a 0,0 % no es ni lo uno ni lo otro. La tabla siempre va con el mayor cambio primero, y el encabezado dice cuántos precios quedan («12 de 40 precios»).
- **Cada control hace una cosa:** el nombre se escribe en la búsqueda, el sentido se elige en el filtro y solo los cambios fuera de lo habitual (K6) están en los botones de alertas (D-491).
- **Con una alerta elegida:** el filtro se apaga y queda en «Todo», para que nunca diga «Bajadas» mientras la tabla muestra alzas fuertes. La búsqueda sigue buscando dentro de la alerta (D-492).
- **Sin filas:** si ningún producto va en ese sentido, la tabla lo dice («Ninguno de estos productos subió esta semana.»), en vez de decir que no hay precios.
- **Pantalla:** «Ampliar» sube a la línea del encabezado del paso 4, así la tabla gana la fila que dejaba el selector. Con menos de 640 px de línea, los botones de alertas se achican y la búsqueda cede ancho; con un panel de productos de menos de 600 px, el encabezado pasa a dos líneas antes que cortar un texto.
- **Pruebas:** `tests/test_dashboard.py` y `tests/test_home_mockup.py` (las tres opciones, qué deja cada una, los fuertes incluidos, el filtro apagado con una alerta y el mensaje sin filas), `tests/test_menu_order.py` y `tests/test_control.py`.

## D-498 · La tabla ampliada tiene las mismas funciones que el panel
- **Pedido del autor:** al ampliar la tabla de productos, se tienen que ver igual los botones de alertas, la búsqueda y el filtro.
- **Decisión:** la ventana de «Ampliar» trae la misma línea del panel: «▲ alzas fuertes», «▼ bajas fuertes», la búsqueda en verde y el filtro «Todo», «Subidas» y «Bajadas» (D-497), con los mismos conteos y las mismas reglas. Abre con lo que el panel tenía elegido, y pulsar un botón dentro de la ventana no la cierra. Lo elegido dentro de la ventana no cambia el panel, como ya pasaba con la búsqueda (D-322).
- **Con una alerta elegida:** «Ampliar» también aparece, y la ventana abre en esa alerta (antes el botón no estaba). El filtro se apaga y queda en «Todo», como en el panel (D-497).
- **Con un canal elegido:** las alertas de la ventana son las de ese canal, como en el panel (D-405), también después de pulsar un botón dentro de ella, que vuelve a dibujar solo la ventana.
- **Lo que no cambia:** dentro de una ventana no se muestran los textos al pasar el cursor por un botón (D-478); la regla K6 se lee en el panel.
- **Pruebas:** `tests/test_home_mockup.py` (los botones de la ventana dicen lo mismo que los del panel, abre con el filtro y la alerta elegidos, conserva el canal, sus estilos).

## D-499 · Con una región elegida, todo lo que sigue trabaja con esa región
- **Pedido del autor:** por defecto, «Semanal» muestra todo Chile, y entonces todo lo que sigue es de todo Chile. Si se elige una región, todo lo que sigue trabaja con esa región: subidas, bajadas, lo que sea.
- **Qué no seguía a la región:** tres partes de «Semanal» eran nacionales aunque hubiera una región elegida. Los canales del paso 2: en Valparaíso se veían «Supermercado en Línea» y «Mercado Mayorista» con su cifra, sin un solo precio en esa región. Las líneas pequeñas del paso 3 (D-480). Y las alertas (D-033, D-489): en la semana del 26-10-2026, los botones de Valparaíso decían 8 alertas en Frutas, todas nacionales, cuando con la misma regla Valparaíso no tuvo ninguna.
- **Decisión:** con una región elegida, los canales son solo los que publican ahí y con sus cifras; las líneas son la mediana de esa región; y los botones de alertas y su tabla aplican la misma regla K6 al precio de esa región, también en la tabla ampliada (D-498). La tabla lo dice: «precio de ODEPA en Valparaíso». Con todo Chile, todo sigue igual que antes.
- **Corrige D-033:** esa decisión descartó las alertas por región porque las series serían más cortas y con más ruido. Medido en la semana del 26-10-2026, no es así: tienen historia suficiente el 65 % de los precios, tanto nacionales (567 de 868) como regionales (2.122 de 3.248), y salen como alerta el 2,3 % y el 3,3 %.
- **Qué no cambia:** K6 nacional sigue siendo el indicador oficial del «Informe semanal», de «Análisis BA y BI» y de las pruebas de calidad. El cálculo por región se hace en el panel, con la consulta `k6_regional_weekly_price`, sin tocar la carga semanal. La columna «Regiones ↑ / ↓» de la tabla sigue contando todas las regiones, porque esa es su pregunta.
- **Canal sin precios en la región:** ya no se ofrece, así que no se puede elegir. Si llega por una dirección guardada, la página vuelve a todo Chile, como ya hacía.
- **Pruebas:** `tests/test_region_scope.py` (cada alerta de una región se recalcula desde `weekly_price`, los botones cuentan lo mismo, los canales y las líneas son de la región, con todo Chile no cambia nada, y el inglés), `tests/test_queries.py`.

## D-500 · Los enlaces al repositorio en GitHub son solo para el Autor
- **Pedido del autor:** ningún perfil que no sea el Autor debe ver GitHub, porque el botón lleva a su repositorio.
- **Qué se encontró:** al recorrer las pantallas como Usuario y como Profesional, además del botón del pie del menú, había enlaces al repositorio en la página «Enlaces», en la carpeta «Documentos» y en cada documento, en «Modelo de datos», en las evidencias de «Calidad y auditoría» y en «Consultas SQL». El «Flujo del sistema en vivo» y el visor de informes también los traían, y «Mapa de la app» mostraba el nombre del repositorio como texto.
- **Decisión:** esos enlaces los dibuja el servidor solo para la sesión del Autor (D-420), con la misma comprobación de la sesión; nunca se leen de la dirección. Para cualquier otro perfil, el botón no existe, la página «Enlaces» dice que no tiene acceso, un enlace dentro de un documento queda como texto y los demás no se dibujan. El documento impreso es esa misma página, así que tampoco los trae.
- **Qué no cambia:** el nombre de la tecnología sin enlace («GitHub Actions», «GitHub CLI») sigue en diagramas y documentos, porque describe cómo funciona el proyecto. El repositorio sigue siendo público: `bi/served_database.py` descarga de ahí la Base DuckDB.
- **Falla registrada:** F-34.
- **Pruebas:** `tests/test_repository_links.py` recorre cada pantalla de `tests/i18n_audit.py` como Usuario y como Profesional, y falla si aparece una dirección del repositorio; también comprueba lo que conserva el Autor y el acceso directo a «Enlaces». `tests/test_dashboard.py` lee como Autor lo que es del Autor.

## D-501 · Letras finas y chicas, y un menú más angosto, como un panel lateral
- **Pedido del autor:** las letras del panel deben ser más finas y chicas, no gruesas, con el tamaño del menú lateral de VS Code y la inspiración de Apple; y el menú debe ocupar menos ancho.
- **Medido antes:** la letra ya era la del sistema (D-175); lo que pesaba era la medida y el grosor. En el menú, «Semanal» iba a 16 px en negrita, las opciones a 15 px, las secciones en mayúsculas con letras separadas, y el menú medía 300 px.
- **Decisión (corrige D-231):** el menú mide 232 px. Las secciones y «Dashboards» van a 11 px, en gris, sin mayúsculas ni separación; las opciones y los recuadros «Semanal» y «Análisis BA y BI», a 13 px en peso normal, con filas de 24 px; «Documentos», «Fuentes», la vista elegida y «Apariencia», a 11,5 px. Las filas y los recuadros se achican con su letra.
- **Más fina:** toda la app usa el suavizado fino de la letra (`antialiased`), porque sin él un Mac engrosa el texto claro sobre fondo oscuro. En «Semanal», todos los pesos bajan un escalón (la negrita pasa a seminegrita, y esta a peso medio); los títulos de los pasos van a 13 px en peso medio y el título de cada página, a 17 px.
- **«Fuentes» a la altura de «Documentos»:** la flecha oculta de su botón seguía ocupando espacio y lo subía unos 11 px.
- **Qué no cambia:** las cifras, los diagramas y el círculo de color de cada paso (D-372).
- **Para verlo:** hay que reiniciar `streamlit run`, porque un cambio en `bi/dashboard.py` no siempre se ve al recargar (trampa ya conocida del panel).
- **Pruebas:** `tests/test_dashboard.py` y `tests/test_panorama_steps.py` (las medidas). Medido con Playwright en español y en inglés, también como Autor con el botón de GitHub: ningún texto del menú ni de los pasos se corta o se sale.

## D-502 · La vista Usuario ve solo sus dos dashboards y las fuentes
- **Pedido del autor:** la vista Usuario no debe dejar ver nada de las otras vistas; lo único que ve son los dos dashboards y las fuentes. El botón «Ver todo el proyecto» no tenía sentido ahí.
- **Decisión (corrige D-295 y D-394):** sale «Ver todo el proyecto», con su estilo y su texto. La única puerta a otra vista es «Vista: Usuario · Cambiar» (D-373), que reabre «Elige tu vista». El menú queda con «Semanal», «Análisis BA y BI» y «Fuentes».
- **Ningún camino se sale:** una dirección que pide otra vista (otra página del menú, un documento, una página del Autor o una vista retirada) dibuja «Semanal», sin nombrar la página ni decir que no hay acceso. Se comprueba en el servidor, en `user_view_page`, que usa la sesión y nunca la dirección: al elegir la ventana, al elegir su vista y antes de dibujar la página.
- **Enlaces que salían:** la nota de cobertura de «Semanal» enlazaba «Calidad» y «Metodología»; en la vista Usuario la nota conserva sus cifras y cierra sin esos dos enlaces. La pestaña «Método» de «Análisis BA y BI» enlazaba «Git workflow» y el SQAP en «Decisiones de sistema»; esos enlaces solo se dibujan si el menú de la visita lleva a esa página (`can_open`, D-376).
- **Documentos:** la figura «seguridad» del Plan de pruebas decía que «Ver todo el proyecto» pasaba a Profesional sin clave; ahora dice que no hay puerta a otra vista.
- **Pruebas:** `tests/test_user_view.py` (nuevo) recorre, en español y en inglés, «Semanal» (con región, con familia y con una alerta elegida) y las seis pestañas de «Análisis BA y BI», y falla si aparece una dirección «vista=» fuera de las dos páginas, «Ver todo el proyecto» o el botón del cambio; comprueba que cuatro direcciones de otras vistas abren «Semanal», que la nota conserva sus cifras sin los dos enlaces y que la vista Profesional no pierde nada. `tests/test_dashboard.py` y `tests/test_menu_order.py` siguen la misma regla.

## D-503 · El modelo estrella usa su panel: apaisado y a la medida de la ventana
- **Pedido del autor:** «a este diagrama modelo estrella le falta ser más grande, más visible; en la ventana tenemos bastante espacio para mostrar un modelo grande. No sé por qué se ve tan miniatura».
- **Medido antes:** `bi/star_model.py` dibujaba una cruz casi cuadrada (viewBox 1000 × 925: dim_date arriba, dim_channel abajo, dim_product y dim_region a los lados, el IPC y la auditoría en las esquinas) y `bi/dashboard.py` la limitaba al alto de la ventana menos 340 px. Por la proporción, mandaba el alto: en 1440 × 900 el dibujo medía 605 × 560 px dentro de un panel de 1048 px de ancho, con los nombres de columna a 10,3 px; en 1280 × 800, 497 × 460 px y 8,5 px; en 1920 × 1080, 800 × 740 px y 13,6 px.
- **Decisión:** la estrella es apaisada, con la proporción de su panel (viewBox 1180 × 591, 2,0 : 1). weekly_price al centro; dim_date sobre dim_product a su izquierda y dim_region sobre dim_channel a su derecha, cada una unida al hecho por una línea punteada en codo (la de arriba llega a un tercio del alto del hecho; la de abajo, a dos tercios, así nunca comparten tramo). El grupo IPC DE ALIMENTOS (INE) ocupa la columna de más a la izquierda, a la altura de dim_date, con su línea de ipc_weekly a dim_date; AUDITORÍA DE CARGAS cierra la columna derecha, bajo dim_channel y fuera de la estrella, con su flecha etl_run → rejection. Las posiciones siguen saliendo de las columnas reales de `etl/schema.sql`, cada columna se centra sobre la más alta y el dibujo crece si una tabla gana columnas.
- **Por qué esta geometría:** se calcularon tres opciones con sus escalas en 1440 × 900. La cruz con el IPC y la auditoría en columnas exteriores y menos aire (1460 × 877) solo subía el texto a 10,9 px; dos dimensiones por lado con el IPC y la auditoría en columnas propias (1440 × 572, proporción 2,5) lo dejaba en 11,9 px; dos dimensiones por lado con la auditoría dentro de la columna derecha (1180 × 591, proporción 2,0) lo lleva a 14,5 px. Se eligió la última: llena el ancho del panel en las cuatro ventanas medidas y el alto en 1920 × 1080.
- **La reserva de alto:** lo que hay arriba y abajo del dibujo mide 319 px (barra de la página, chips, pestañas y la frase en una línea: 219 px; leyenda y relleno del panel: 60 px; dos bloques vacíos del marco y el relleno de la página: 40 px). La reserva pasa de 340 px a 331 px, y a 350 px bajo 1320 px de ventana, donde la frase ocupa dos líneas.
- **Medido después:** 1280 × 800: dibujo de 846 × 424 px y texto de 12,2 px; 1440 × 900: 1006 × 504 px y 14,5 px; 1920 × 1080: 1486 × 744 px y 21,4 px; 1024 × 768: 590 × 296 px y 8,5 px. Sin scroll de página, ningún texto fuera del dibujo ni solapado, en español y en inglés.
- **Qué no cambia:** sin marco de zoom (D-251), un solo SVG estático con `width="100%"`, sin script; los mismos textos, tooltips, fondo radial y leyenda. El SAD dibuja la misma estrella («[[diagrama:estrella]]», `bi/app_diagrams.py`).
- **Pruebas:** `tests/test_star_model.py` (las cinco tarjetas y los dos grupos nunca se solapan, con cualquier conteo de columnas, en cuatro tablas distintas y con un dim_date más corto que la cadena del IPC; la proporción queda entre 1,8 y 2,1; la auditoría va a la derecha del hecho y bajo dim_channel; el IPC, junto a dim_date), `tests/test_view_regression.py`, `tests/test_doc_diagrams.py` y `tests/test_dashboard.py` (la página panorámica y el orden de las vistas). Medido con Playwright en 1280 × 800, 1440 × 900, 1920 × 1080 y 1024 × 768, en los dos idiomas.

## D-504 · El menú entero a la vista: sin desplazamiento hacia un vacío, con desplazamiento solo si el contenido no cabe
- **Pedido del autor:** el menú lateral puede deslizarse por si un día se agrega una sección, pero mientras cabe no debe poder desplazarse hacia un vacío, porque eso tapa el logo GreenOcean y el botón de plegar. Se tiene que ver el menú completo, con el logo y el botón, constantemente.
- **Causa medida:** la columna del menú se estiraba al alto de la ventana (`min-height:calc(100vh - 86px)`) y encima recibía 140 px de relleno abajo, reservados para el pie «Documentos», «Fuentes», «Apariencia» y ES/EN, que era `position:fixed`. El contenido desbordaba siempre 126 px (152 como Profesional a 600 px de alto), medido con Playwright a 1440 × 900, 1440 × 768, 1280 × 700 y 1024 × 600, como Usuario y como Profesional, con el menú terminando a 279 o a 495 px. Desplazado al final, el logo quedaba a −126 px y el botón de plegar a −113 px, fuera de la ventana, con un vacío de 407 a 623 px entre la última opción y el pie.
- **Decisión:** solo CSS, porque Streamlit es dueño del DOM. El pie deja de ser fijo: va al final del flujo del menú, empujado al fondo (`margin-top:auto` en una columna cuyo mínimo es el alto de la ventana menos el encabezado) y pegado abajo con `position:sticky; bottom:0`, a los 232 px de ancho (D-501; hizo falta `max-width:none`, porque Streamlit limita ese contenedor al 100 %). El encabezado con el logo y el botón de plegar queda pegado arriba (`position:sticky; top:0`) con el fondo del menú y mide 72 px: sus 52 px más los 20 px de aire que ya había bajo el logo (16 px de margen de Streamlit y 4 px de relleno), para que su superficie pinte esa franja cuando el menú pasa por debajo. Desaparecen los rellenos de 140 y de 116 px. En el teléfono girado (D-166) la columna crece con su menú (`161.3vh`), así el pie sigue al fondo de la pantalla.
- **Medido después:** desborde 0 en los cuatro tamaños y en 1440 × 520 como Usuario, y como Profesional en todos los que caben; desborda solo cuando el menú no cabe (Profesional a 1024 × 600: 20 px; a 1440 × 520: 100 px) y entonces, desplazado al final, el logo (0–72) y el botón de plegar (13–45) siguen dentro de la ventana, el pie termina en el borde inferior (476–600, 396–520) y la última opción, «Git workflow», termina 1 px sobre el pie: ni vacío ni opción tapada. El botón de plegar no se movió (13–45 antes y después) ni el ancho de 232 px. Plegar y volver a abrir el menú da las mismas cifras. En 390 × 844 sale «Gira tu teléfono»; en 844 × 390 el menú abre a escala .62, sin desborde y con el pie en el borde (313–390). 1440 × 480 cae en ese modo teléfono y no desborda.
- **Qué no cambia:** el plegado automático del menú (D-463, D-466), el ancho de 232 px (D-501), el pie con «Documentos», «Fuentes», «Apariencia», ES/EN y, solo para el Autor, GitHub (D-500), ni el desplazamiento de las fuentes al abrirlas (D-286).
- **Pruebas:** `tests/test_sidebar_scroll.py` (nuevo) comprueba en los cuatro temas que no quedan los rellenos de 140 y 116 px, que la columna mide `100vh − 72px`, que el pie va en el flujo y pegado abajo, que el encabezado va pegado arriba con el fondo del menú, la regla del teléfono girado y que el pie no mueve nodos con scripts. `tests/test_view_switch.py`, `tests/test_home_mockup.py`, `tests/test_dashboard.py`, `tests/test_menu_order.py`, `tests/test_panorama_steps.py` y `tests/test_repository_links.py` siguen en verde.

## D-505 · Los estilos viajan en el primer elemento de cada página
- **Pedido del autor:** al abrir «Análisis BA y BI» desde el menú, por un instante aparecen unas escrituras sueltas, como si algo hubiera quedado a la vista y luego se escondiera.
- **Diagnóstico:** los estilos de «Semanal» (`bi/home_mockup.css`, 85 KB) se dibujaban dentro de la página, no en su cabecera. Al cambiar de página, Streamlit reemplaza los elementos en orden: el elemento que llevaba esos estilos se reemplazaba antes que el contenido de «Semanal», que quedaba un cuadro sin estilos, en texto plano. Se vio grabando el cambio de página con Chromium a 25 cuadros por segundo: en el cuadro del cambio se leen los cuatro pasos como texto corrido.
- **Decisión:** esos estilos pasan a `apply_style`, que es lo primero que dibuja toda página. Así ninguna página los pierde mientras Streamlit cambia de página, y el contenido viejo nunca aparece sin estilo. El panel no cambia de aspecto.
- **Pruebas:** `tests/test_dashboard.py` (la página de diagramas no dibuja «Ampliar»: la comprobación mira lo que la página dibuja, no sus hojas de estilo); `tests/test_panorama_steps.py` y `tests/test_weeks.py` siguen leyendo los estilos desde `home_mockup.style`.

## D-506 · La canasta explica por qué su mediana dice lo que dice
- **Pedido del autor:** la fila «Toda la canasta» del paso 3 a veces marca 0,0 % «Sin cambio» aunque muchos precios se movieron, porque la mayoría no cambió. Confunde: casi todas las familias bajan y la canasta dice que no pasó nada.
- **Decisión:** junto a la cifra de esa fila aparece una «i» propia, distinta de la del título del paso. Al pasar el cursor, dice en una frase hacia dónde se movieron más precios («Más precios bajaron que subieron», «Más precios subieron que bajaron» o «Subieron y bajaron en cantidades parecidas»), con «pero la mayoría no cambió» solo cuando los sin cambio son más de la mitad; debajo, los tres conteos («▲ 307 subieron · ▼ 346 bajaron · = 70 sin cambio») en el rojo y el azul del panel; y, solo cuando la mediana es 0,0 %, «Por eso la mediana queda en 0 %.».
- **De dónde salen las cifras:** de los mismos precios comparables que calculan la mediana (`basket_counts` sobre las filas de `basket_median`), con la misma regla «Subió / Bajó / Sin cambio» de las familias (`change_state`, 0,05 %). Siguen la región del paso 1 y el canal del paso 2 (D-499). Subieron + bajaron + sin cambio es el total.
- **«Parecidas»:** los dos lados se diferencian en menos del 5 % de los precios comparados.
- **Lo que no cambia:** la fila se ve igual, con su cifra y su palabra; la «i» solo agrega 16 px. Quien no tenga la duda no ve nada nuevo.
- **Pruebas:** `tests/test_panorama_steps.py` (los conteos cubren todas las filas comparables, cada frase en su caso, la razón solo con mediana cero, los colores y la canasta vacía). Medido en el navegador, en español y en inglés: la ventana queda dentro del panel y «Sin cambio» no se parte.

## D-507 · Las tres páginas de «Calidad» dicen qué hace cada una
- **Pedido del autor:** los nombres no describían la página. El plan fija qué es aceptable; los controles verifican cada carga; el registro anota qué falló y cómo se resolvió.
- **Decisión:** la sección «Calidad» del menú se lee en ese orden, con estos nombres: «Plan de calidad» (antes «Método y calidad»), «Controles de datos» (antes «Calidad y auditoría») y «Cambios e incidentes» (antes «Git workflow»). El título de la sección no cambia. El nombre nuevo vale en el menú, en la ruta del encabezado, en «← Anterior» y «Siguiente →», en el mapa de la app, en los diagramas de los documentos y en inglés: «Quality plan», «Data controls» y «Changes and incidents».
- **Las direcciones no cambian:** cada página conserva su ruta (`metodo-y-calidad`, `operaciones`, `git-workflow`). Un enlace guardado con el nombre antiguo abre la misma página, porque los tres nombres viejos entran en `RETIRED_VIEWS`.
- **Lo que no se toca:** los incidentes y los informes ya registrados que nombran las páginas antiguas, porque son históricos; y el contenido de las tres páginas.
- **Pruebas:** `tests/test_dashboard.py` (el menú, la ruta y los pasos «Anterior / Siguiente»), `tests/test_menu_order.py` (el mapa de la app y el README en el orden del menú), `tests/test_quality_method.py`, `tests/test_git_workflow.py` y `tests/test_i18n.py` (los tres nombres en inglés).

## D-508 · El dashboard «Análisis BA y BI» se llama «Análisis»
- **Pedido del autor:** un nombre más corto para el segundo dashboard. Se propuso «Histórico», pero la página ya tiene una pestaña con ese nombre (toda la historia por año y temporada) y la ruta habría dicho lo mismo que la pestaña; el autor decidió «Análisis», y la pestaña sigue «Histórico».
- **Decisión:** «Análisis» (en inglés, «Analysis») en el menú, en la ruta, en el mapa de la app, en los diagramas y en los documentos; sus pestañas no cambian. Una pestaña se nombra «Análisis (Pestaña)».
- **Las direcciones no cambian:** la página conserva su ruta (`analisis-ba-y-bi`); un enlace guardado con «Análisis BA y BI» abre la misma página (`RETIRED_VIEWS`). Los incidentes y los informes ya registrados no se tocan.
- **Pruebas:** `tests/test_menu_order.py` (el mapa de la app y el README en el orden del menú), `tests/test_dashboard.py`, `tests/test_page_bar.py` y `tests/test_i18n.py`.

## D-509 · «Descargar» en el paso 4: los precios filtrados, en Excel o en CSV
- **Pedido del autor:** un ícono «Descargar» en el paso 4, junto a «Ampliar» y, en la tabla ampliada, junto al conteo de precios, con un menú de dos opciones: Excel y CSV. Baja todos los precios filtrados, no solo las filas a la vista, en el idioma de la app: encabezados, familias, canales y notas; el nombre de cada producto queda como lo publica ODEPA. Un dataset para BI, sin gráficos.
- **Decisión:** `bi/price_export.py` arma las filas desde los mismos datos de la tabla: los dos precios de las mismas regiones (D-327), la variación como número, las regiones al alza y a la baja, y la marca de una sola cotización. Quince columnas: familia, producto, variedad, calidad, canal, unidad, alcance, semana anterior y su precio, semana y su precio, variación, regiones al alza, regiones a la baja y «una sola cotización».
- **Excel:** hoja «Datos», una tabla de Excel («Precios») con autofiltro, encabezado congelado, formato de pesos en los precios, de porcentaje con signo en la variación y de entero en los conteos; sin celdas combinadas, porque rompen un filtro y una tabla dinámica. Hoja «Notas»: la semana, los filtros elegidos (región, canal, familia, alerta, orden y búsqueda), la fecha de la carga, la fuente ODEPA con su licencia, cómo se calcula la variación, cuántas regiones publica la fuente y cuántos precios quedaron fuera por no tener región comparable.
- **CSV:** la misma tabla, con punto y coma y en UTF-8 con BOM, para que Excel la abra con sus acentos en su lugar.
- **Dependencia nueva, con acuerdo del autor:** `openpyxl` (MIT, sin cuenta ni vencimiento), con tope de versión como las demás (D-435). Los dos archivos se construyen una vez por conjunto de precios e idioma (`st.cache_data`).
- **El archivo se llama por lo que trae:** «greenocean-precios-2026-10-26-todo-chile.xlsx».
- **De paso:** en la tabla ampliada la columna «Familia» se escribe entera; antes cortaba «Hortaliz…».
- **Pruebas:** `tests/test_price_export.py` (las filas con las cifras de la tabla y el producto como ODEPA lo escribe, la tabla con su filtro, sus formatos y sus notas, sin celdas combinadas, el CSV con BOM, el archivo en inglés salvo el producto, cada texto con su inglés, y el menú en el panel y en la ventana con todos los precios filtrados).

## D-510 · «En vivo»: la marca de una cifra que se lee de la base al abrir la página
- **Pedido del autor:** a simple vista, las cifras de los diagramas parecen escritas a mano o una foto de algún momento. Quiere que se sienta que son números que se extraen y cambian, en cada diagrama que los tenga.
- **Decisión:** junto a las cifras que se leen de la base aparece un punto verde que late despacio, una vez por segundo, con las palabras «en vivo · leído de la base al abrir»; al pasar el cursor dice qué se leyó (las tablas y la consulta). No parpadea la cifra: un número que parpadea se lee como «cargando»; late el punto, como el botón del menú (D-466). Con «menos movimiento» activado en el sistema, el punto no late.
- **Dónde va:** en la fila de cifras de «Modelo de datos» y «Pipeline y linaje»; en la fila bajo la barra de «Controles de datos», «Stack y evidencia» y «Centro de operación» y «GitHub Actions» (del Autor); en la barra de «Análisis», cuya fila la dibuja cada pestaña; y dentro de los dos diagramas que llevan sus propias cifras: el pipeline de calidad de «Controles de datos» y las tres cifras de «Stack y evidencia». «Semanal» ya lleva en su barra el punto verde con la fecha de los datos (D-398).
- **Dónde no va:** en los diagramas que no miden nada, «Mapa de la app», «Arquitectura de seguridad», «Plan de calidad» (un informe cerrado, D-483) y «Cambios e incidentes», para que la diferencia se note.
- **Pruebas:** `tests/test_live_mark.py` (el latido de un segundo y su freno con menos movimiento; la fila agrega la marca solo cuando se le dice qué se leyó; cada página con cifras de la base la muestra; una que no mide nada, no; y en inglés). Una marca va en `bi/live_mark.py`, con su estilo para la página y para los diagramas en su propio marco.

## D-511 · «Consultas SQL»: los filtros en la línea de la pestaña, finos, y el editor con más alto
- **Pedido del autor:** los cinco filtros ocupaban dos líneas de píldoras gruesas sobre el editor, con espacio vacío mal repartido; quiere la zona más fina y elegante, al estilo de Apple, y más alto para el código.
- **Decisión:** los filtros pasan a la misma línea que la pestaña del script, a su derecha, como píldoras de 24 px y letra de 11,5 px, cada una del ancho de su filtro (Familia 132, Producto 132, Canal 108, Región 108, Año 84 px). Una píldora dice su filtro («Producto») mientras no se elige nada, y el valor cuando se elige; al pasar el cursor: «Producto: elige uno o déjalo en todos». Sale el rótulo «FILTROS» y la pestaña deja de repetir «datos.duckdb», que ya está en la barra de arriba. Bajo 1300 px de ventana, la última píldora pasa entera a una segunda línea; nada se corta.
- **El editor crece lo que la fila dejó:** de 172 a 264 px a 1440 × 900 (de 6 a 12 líneas a la vista); la fila de resultados empieza a la misma altura que antes, así la página sigue sin desplazamiento a 1440 × 900 y a 1280 × 800. La nota de la consulta «Tabla completa» ya no dice «Todas» no filtra, sino «un filtro sin elegir no filtra».
- **Pruebas:** `tests/test_page_bar.py` (la fila de la pestaña envuelve y la píldora «Año» mide 84 px), `tests/test_sql_explorer.py` (el alto del editor y de los resultados suman el alto del estudio). Medido con Playwright a 1440 × 900 y 1280 × 800: ninguna píldora corta su texto; a 1440 las cinco caben en la línea de la pestaña.

## D-512 · Las filas del menú, con el aire del explorador de VS Code
- **Pedido del autor:** las opciones del menú quedaron demasiado pegadas (D-501): un clic puede caer en la vecina. Quiere un milímetro de aire, como en VS Code.
- **Decisión:** cada fila mide 28 px (antes 24) y entre filas quedan unos 8 px de aire; cada sección deja 8 px arriba y abajo, y 4 px bajo su título. Las letras no cambian. Medido con Playwright a 1440 × 900 y 1024 × 768 como Profesional: once filas, el menú termina a 575 px, el pie queda a la vista y nada se desplaza.
- **Pruebas:** `tests/test_sidebar_scroll.py`, `tests/test_dashboard.py` y `tests/test_menu_order.py` siguen en verde.

## D-513 · La barra de cada página con la medida de la de Apple
- **Pedido del autor:** el encabezado de «Consultas SQL» ocupaba mucho alto y sus componentes eran grandes; toda la app debe tener la letra elegante y fina de la barra de Apple.
- **Decisión:** la barra de toda página (D-267, D-398) mide 36 px (antes 44), con la ruta a 12,5 px en peso normal y el nombre de la página un escalón más pesado (500, antes 600); la hora de los datos a 11,5 px; el botón «Volver» de 28 px. Los chips de cifras miden 22 px (antes 27), con letra de 12 px y la cifra en peso medio, nunca negrita; la fila bajo la barra queda a 4 px de ella y sus botones miden 26 px. La barra de «Semanal» (D-264) sigue la misma medida: 38 px por su segunda línea «Próxima semana». Un párrafo invisible le daba 12 px de más a la hora de esa barra; se quitó.
- **Medido:** a 1440 × 900, «Consultas SQL» y «Modelo de datos» terminan su cabecera a 127 y 114 px desde el borde (antes 140 y 127); la barra de «Semanal» pasa de 48 a 38 px.
- **Pruebas:** `tests/test_page_bar.py` (la fila bajo la barra con su nuevo aire), `tests/test_panorama_steps.py`, `tests/test_home_mockup.py` y `tests/test_sql_explorer.py` en verde.

## D-514 · «Consultas SQL» sin la fila de chips: sus límites junto a «Ejecutar», y el editor más alto
- **Pedido del autor:** la fila «DuckDB solo lectura · máx. 5.000 filas · 10 s» bajo la barra ocupaba un alto que podía ir al editor.
- **Decisión:** esa fila sale. «DuckDB» y «solo lectura» ya estaban en la píldora de conexión de la barra del estudio; los dos límites («máx. 5.000 filas · 10 s») pasan en letra pequeña junto a «Ejecutar», con su explicación al pasar el cursor. El editor crece lo que la fila dejó: de 264 a 278 px, y empieza 58 px más arriba, así se ven hasta 13 líneas sin desplazamiento.
- **Medido:** a 1440 × 900 el estudio empieza a 109 px (antes 167) y los resultados a 520 (antes 564); a 1280 × 800 nada se sale de la ventana.
- **Pruebas:** `tests/test_sql_explorer.py` (el alto del editor y de los resultados suman el alto del estudio), `tests/test_page_bar.py` y `tests/test_i18n.py` (los límites en inglés).

## D-515 · «Relaciones» en «Consultas SQL»: cómo se unen las vistas, con cada JOIN listo para copiar
- **Pedido del autor:** el explorador lista las vistas una bajo otra, pero nadie puede adivinar sus llaves; quiere ver las relaciones, como el diagrama entidad-relación de SQL Server u Oracle, de la forma más simple.
- **Decisión:** un botón «Relaciones» en el explorador, sobre «Descargar tablas», abre una ventana con el diagrama entidad-relación de las ocho vistas, en la notación de «Modelo de datos» (D-195): cada vista con sus columnas y tipos reales (DESCRIBE sobre las vistas), las columnas que identifican una fila marcadas PK, cada unión como una línea con pata de gallo, y el mismo mes del IPC como línea punteada. Debajo, cada JOIN escrito tal como se escribe, listo para copiar en el editor. Las uniones se declaran una sola vez en `bi/sql_relations.py`: precios → semanas (por semana), precios → ipc_semanal (por semana, a lo más un factor real), precios → productos (por familia, producto, variedad y calidad), rechazos → cargas (por el inicio de la carga) y, sin clave, ipc_semanal ~ ipc_mensual (el mismo mes).
- **Pruebas:** `tests/test_sql_relations.py` comprueba que cada clave y cada columna de unión existe en las vistas, que ninguna unión deja huérfanos en los datos, que cada JOIN escrito corre tal cual sobre las vistas, que el dibujo tiene las ocho vistas y las cinco líneas, que cada texto tiene su inglés y que el botón abre la ventana con el dibujo y los JOIN. Medido con Playwright: ningún texto sale del dibujo.

## D-516 · «Consultas SQL»: el diagrama en una sola vista, la tabla con todo el alto, el menú plegado y todo en inglés
- **Pedido del autor:** la ventana «Relaciones» ocupaba toda la pantalla y no se veía de una vez; el menú debe plegarse al entrar, como en los dashboards; la tabla de resultados era chica y dejaba espacio vacío debajo; y con el panel en inglés quedaban textos en español, incluso los comentarios del SQL.
- **Decisión (diagrama):** las ocho vistas pasan a cuatro columnas, más anchas que altas (1386 × 620), con filas de 24 px y la leyenda en la esquina libre. El dibujo nunca pasa del alto de la ventana (`max-height`), así que se reduce entero en una ventana chica. Los JOIN pasan a su propia pestaña, «JOIN listos para copiar», junto a «Diagrama», y sale la nota de arriba, que la leyenda ya explica. `rechazos` y `cargas`, una bajo la otra, se unen con un corchete por su borde izquierdo.
- **Decisión (menú):** `PAGE_SQL` se suma a las páginas que pliegan el menú (D-463).
- **Decisión (tabla):** la tabla toma todo el alto que la ventana deja bajo el editor, en vez del alto fijo de D-183 y D-233, que recortaba la tabla y dejaba inalcanzables sus últimas filas. El alto llega al contenedor de la tabla y Streamlit la dibuja de verdad a esa medida (`height="stretch"`), con filas de 28 px. La línea de resumen y las descargas suben a la línea de las pestañas. Con pocas filas la tabla conserva su propio alto. El explorador de objetos también usa el alto libre.
- **Decisión (inglés):** con `?lang=en` se traducen los comentarios de las seis consultas de ejemplo, la línea de resultado, los mensajes de error, los nombres de los scripts y de los archivos descargados (`query.csv`) y lo que se lee al pasar el cursor (la descripción de cada vista, la pregunta de cada consulta, «Ejecutar»). Si la visita cambia de idioma con un ejemplo abierto, sus comentarios cambian con ella; un texto que el lector escribió no se toca. La lista `EXAMPLES` se arma una sola vez para todas las visitas, así que sigue en español y la página pide cada ejemplo en el idioma de la visita.
- **Lo que queda en español, a propósito (D-443):** los nombres de las vistas y sus columnas (`precios`, `familia`) son código: el lector los escribe tal cual en su consulta, y un encabezado `family` daría un error al usarlo. Los datos de ODEPA tampoco cambian. Por eso la capa de inglés ya no renombra las columnas de una consulta (`i18n.KEEP_NAMES`), ni los nombres del diagrama (`translate="no"`), ni los botones de las vistas (`i18n.Verbatim`). Antes traducía solo algunos: `semana` salía como `week` y `precios` como `prices`. Al renombrar `semana`, la tabla además perdía su formato de fecha y mostraba la medianoche.
- **Auditoría:** `tests/i18n_audit.py` ahora lee también lo que dice cada control al pasar el cursor; así apareció otro texto sin inglés, en «Controles de datos», que quedó traducido. La falla se anota como F-36.
- **Medido con Playwright:** a 1440 × 900, la ventana «Relaciones» mide 634 px de alto y la tabla 276 px (9 filas; antes, 146 px y 3 filas), con la barra de estado a la vista. A 1280 × 680 el diagrama se reduce y sigue entero, sin textos encimados. Ni el inglés ni el español muestran textos cruzados.
- **Pruebas:** `tests/test_sql_explorer.py` y `tests/test_sql_relations.py` (la tabla, cada comentario y mensaje en inglés, los nombres como código, el dibujo apaisado sin cajas encimadas y el menú plegado) y `tests/test_i18n.py`.

## D-517 · «Relaciones»: cada grupo de vistas conectadas, con su color
- **Pedido del autor:** las vistas que no se conectan con las demás podrían distinguirse por color, si pertenecen a otra base o a otro proceso.
- **Hecho comprobado:** las ocho vistas están en la misma Base DuckDB · `etl/datos.duckdb` y las escribe la misma carga semanal (`semanal.yml`). Lo que las separa es qué guardan: `productos`, `precios`, `semanas`, `ipc_semanal` e `ipc_mensual` guardan los datos de ODEPA e INE; `cargas` y `rechazos`, el registro de cargas; `modelos_dbt`, los modelos y las pruebas de dbt Core.
- **Decisión:** cada grupo lleva su color en el encabezado, las claves y las líneas: el color del tema para los datos, ámbar para el registro de cargas y rosado para dbt Core. El rojo no se usa, porque ya significa un precio que sube. La leyenda nombra cada grupo junto a su color y aclara que las ocho vistas están en la misma Base DuckDB, para que el color no se lea como otra base.
- **Pruebas:** `tests/test_sql_relations.py` comprueba que cada grupo es exactamente un conjunto de vistas conectadas entre sí, que cada color contrasta al menos 4,5 a 1 con su tarjeta en los cinco temas, y que la leyenda se lee en los dos idiomas. Medido con Playwright: la ventana no cambia de tamaño y ningún texto queda encimado.

## D-518 · «Análisis (Histórico)»: el mayor salto del IPC de alimentos, en un cuadro verde
- **Pedido del autor:** colocar en la pestaña «Histórico», en un cuadro verde, este insight: «Los alimentos subieron +24,7 % en 2022 según el IPC del INE, el mayor salto desde 2010. Desde 2023 suben entre 3,6 % y 5,2 % al año: el alza se moderó, pero los precios no volvieron atrás.»
- **Decisión:** el cuadro va entre los gráficos y la tabla, con el texto del autor. Sus cifras no están escritas a mano: se recalculan desde `ipc_monthly` en la Base DuckDB, de diciembre a diciembre y solo con años completos. Por eso el 2026 todavía no cuenta, y entrará al rango cuando el INE publique su diciembre. La frase sigue a los datos: dice que los precios no volvieron atrás solo mientras el último índice no baje del diciembre del salto. No menciona el COVID, porque los datos dicen cuándo pasó, no por qué. El texto no cambia al elegir una familia: habla de los alimentos en general, según el INE.
- **Las dos cifras de 2022:** el cuadro dice +24,7 %, desde diciembre de 2021. La raya de 2022 en «Cambio de cada año» marca +22,7 %, porque ahí ese año parte en enero, el primer mes de los precios de ODEPA. El texto al pasar el cursor sobre el cuadro lo explica, y una prueba comprueba que esa cifra es la misma de la raya.
- **Medido con Playwright:** a 1440 × 810 el cuadro mide 32 px, en una línea, y la página cabe sin scroll: la tabla cede ese alto. A 1440 × 900 la página pide 44 px de scroll, porque los gráficos y la tabla crecen a la vez con la ventana; viene de antes de este cambio y queda sin tocar.
- **Pruebas:** `tests/test_ba_trends.py` (la frase, sus cifras recalculadas desde la base, sus casos cuando los datos cambian, el inglés, y que el cuadro sale solo en «Histórico»).

## D-519 · «Relaciones» dice lo mismo que «Modelo de datos»
- **Pedido del autor:** preguntó si es normal que los tres diagramas de la base discrepen en su contenido.
- **Lo que es normal:** muestran capas distintas. El modelo estrella y el diagrama entidad-relación de «Modelo de datos» dibujan las tablas; «Relaciones», las vistas que las leen con nombres en español y sin ids. Por eso `precios` es `weekly_price`, `dim_region` y `dim_channel` no tienen vista (su nombre va dentro de `precios`), `semana` es DATE en la vista y `week_start` es VARCHAR en la tabla, y `rechazos` abre en columnas el JSON de `rejection`. Las filas de cada vista son las de su tabla.
- **Lo que no era normal, tres errores de D-515:** (1) una línea unía `precios` con `ipc_semanal`, pero la relación real es `ipc_weekly` con `dim_date`, como declara `dbt/models/marts/schema.yml`; ahora une `ipc_semanal` con `semanas`. El JOIN de `precios` con `ipc_semanal` sigue siendo válido y sigue en la lista, porque las dos usan la misma semana. (2) La leyenda decía que `precios` no tiene clave, mientras el diagrama entidad-relación marca una en `weekly_price`; ahora marca las mismas columnas con sus nombres, las ocho que identifican una fila. (3) Solo `producto` salía como FK, aunque el catálogo se une por cuatro columnas; ahora salen las cuatro.
- **Una prueba que no probaba:** la de D-515 decía correr cada JOIN escrito, pero se saltaba el primer bloque, el de `precios`. Ahora los corre todos.
- **Pruebas:** `tests/test_sql_relations.py` compara cada línea con las relaciones de `er_diagram.py`, sus extremos incluidos, y comprueba en la Base DuckDB que cada clave identifica una fila, que cada vista tiene las filas de su tabla y que ningún precio queda fuera del catálogo al unir por las cuatro columnas. La falla se anota como F-37.

## D-520 · Cada unidad de venta, leída como se revisó a mano
- **Pedido del autor:** ningún dato malo por culpa del software. Revisar las 12.626 filas sin unidad, corregir lo que sea nuestro, reconstruir y decir cuánto cambian las cifras publicadas.
- **Lo que era nuestro:** (A) `$/docena de paquetes 5 unidades` se dividía por 5, no por 60: Betarraga en La Araucanía, semana del 4 de abril de 2022, publicaba $1.870 por unidad, con $158 la semana anterior. Estaba marcada `ATIPICO`, así que no entraba a los indicadores. (B) `$/cien…` y `12 canastillos 125 gramos` tienen una lectura exacta y quedaban sin precio.
- **Decisión:** `$/cien…` son 100 unidades y `N canastillos G gramos` son N × G gramos, en la ETL y en dbt. La docena de paquetes con unidades queda sin precio: cinco filas de 2022 calzan con 12 × 5 unidades, pero la de diciembre de 2024 calza con un solo paquete, y la fuente no da una lectura segura. El resto de las 12.185 filas sin unidad es de la fuente, sin peso o con un rango, y sigue sin precio: inventarlo daría cifras falsas (RN-05).
- **Lecturas comprobadas contra los precios:** `$/cien` da $280 en choclo, contra $242 de `$/unidad`; `$/cien en rama` da $140 en cebolla, contra $100 a $150 de sus paquetes. Los canastillos cuestan entre 25 % y 77 % más por kilo que la bandeja de 2 kilos de la misma semana: es otro formato, no un error.
- **Prueba nueva:** `tests/fixtures/reviewed_units.csv` guarda las 199 unidades que ODEPA ha usado, con su lectura revisada; la ETL y dbt deben leerlas igual. `tests/test_unit_catalog.py` falla con cualquier unidad nueva y corre en local. La carga semanal se detiene solo si una unidad nueva recibe precio sin ser un envase simple (`tests/test_unit_review.py`), el único caso que puede publicar una cifra falsa: ODEPA agrega unas siete unidades al año, y detener la carga por `$/caja 110 unidades` sería la falla F-01.
- **Control:** los archivos de ODEPA del 4 de noviembre son idénticos a los de la carga publicada (huellas de `agent/downloads/manifest.json`), con datos hasta la semana del 26 de octubre. Una reconstrucción con la regla anterior reprodujo la base publicada: mismas 821.072 filas, y los precios difieren como máximo en 7 billonésimas de peso. Todo lo que sigue se debe a la regla.
- **Antes y después (Base DuckDB local, se publica con la próxima carga):**
  - `weekly_price`: 821.072 → 820.964 filas, porque las filas sin unidad se funden con las de su producto. Sin unidad: 12.626 → 12.185. Con precio válido: 807.611 → 807.945. Atípicas: 835 → 834.
  - Precios nuevos: 334 (Rabanito 248, su primer precio mayorista; Arándano 79; Cebolla 7).
  - Precios que cambian: 107 semanales (Arándano 101, Frambuesa 4, Betarraga 1, Cebolla 1) y 110 de 209.516 nacionales, con mediana +4,5 % y máximo +62,1 %. Última semana publicada: 1 de 868, Arándano Primera mayorista, de $7.041 a $7.315.
  - Alertas K6: 4.057 → 4.071, ninguna se pierde (Rabanito 9, Arándano 4, Frambuesa 1); última semana, 13 → 13. K1: 115 márgenes cambian y 57 son nuevos. K2 no cambia. El índice de «Análisis» no cambia.
- **Lo que no se reescribe:** el incidente de D-418 midió 145 de 868 precios en la semana del 26 de octubre, con la regla de entonces, y así queda. Con esta regla la misma semana tiene 869, por el precio nuevo de Rabanito; los 145 sin comparación se mantienen, y uno de ellos pasa de más de 12 semanas sin precio a menos de 12.
- **Pruebas:** `tests/test_unit_review.py`, `tests/test_unit_catalog.py`, `tests/test_etl.py` y la suite completa sobre la base reconstruida (1.463 en verde, 7 saltadas). La paridad entre el respaldo SQLite y la Base DuckDB se corrió en una copia aparte: la ETL de respaldo da las mismas 820.964 filas. La falla se anota como F-38.

## D-521 · El precio mayorista semanal pesa los kilos o unidades que trae el volumen
- **Pedido del autor:** revisar cómo se promedia una semana que mezcla envases. Buscar primero qué significa el volumen en ODEPA.
- **La definición:** el boletín semanal de ODEPA dice que se obtiene «una estimación del volumen que ingresó a los mercados en cada jornada, con base en cálculos sobre capacidades de carga de los camiones y cuantificación del movimiento diario de productos», y su tabla de volumen lo expresa por envase, como «Malla 18 kilos». Su página de datos abiertos no lo define. Nuestros documentos decían «volumen vendido»: era incorrecto y se corrigió.
- **La prueba en los datos:** si el volumen contara kilos, el 99,997 % de las filas de `$/bins (400 kilos)` habría vendido menos de un bins. Con «(volumen en unidades)» el 99 % de los valores es múltiplo exacto del envase; sin esa etiqueta, los múltiplos aparecen como por azar.
- **La falla:** RN-07 sumaba volúmenes de envases distintos como si fueran iguales: un bins de 400 kilos pesaba lo mismo que una caja de 15. Afecta a las semanas que mezclan envases: 28.328 de 237.641 precios mayoristas (11,9 %).
- **Decisión:** cada precio pesa `volumen × kilos o unidades del envase`, en la ETL y en dbt. Con «(volumen en unidades)» el volumen ya cuenta unidades. La columna `volume` sigue como la informa la fuente.
- **Lo que queda inferido, no declarado:** ODEPA rotula `$/kilo (en caja de 17 kilos)` sin decir si cuenta kilos o cajas. Se lee como cajas porque 150 de mediana en palta dan 2.550 kilos, igual que los 2.400 de `$/bandeja 10 kilos`, y sus valores no son múltiplos de 17. Si contara kilos, 1.357 precios semanales cambiarían más de 5 % y 271 más de 25 %. Se puede confirmar con ODEPA en basededatos@odepa.gob.cl. `$/kilo (volumen en unidades)`, en Zapallo y Sandía, cuenta frutos sin peso declarado y pesa por fruto; solo 1 precio semanal lo mezcla con otro envase.
- **Antes y después (Base DuckDB local, se publica con la próxima carga), sobre la base de D-520 y con los mismos archivos de ODEPA:**
  - Precios mayoristas semanales que cambian: más de 1 %, 12.701 (5,3 %); más de 5 %, 5.954 (2,5 %); más de 25 %, 977 (0,4 %); más de 50 %, 19. Bajan 8.623 y suben 4.077.
  - Precios nacionales que cambian: 15.537 de 209.783, con mediana −0,2 %, entre −65,8 % y +40 %. Última semana publicada: 66 de 869.
  - Margen K1: 9.484 valores se mueven más de 5 puntos y 3.709 más de 25; la mediana pasa de 77,2 % a 78,0 %. K2 no cambia.
  - Alertas K6: 4.071 → 4.043 (salen 117, entran 89). Última semana: 13 → 15, entran Mandarina Murcott Especial y Lechuga Conconina Primera. Atípicas: 834 → 835.
  - Consumidor: ningún precio cambia, y el índice de «Análisis» tampoco.
- **Lo que esta regla no arregla:** un cambio de envase entre semanas sigue pareciendo un movimiento de precio. Kiwi Hayward Especial mayorista, semana del 26 de octubre, publicaba +25,6 % y con esta regla marca +23,6 %, porque la región del Maule pasó de `$/bandeja 18 kilos` a `$/bandeja 10 kilos`; en el mismo envase subió +8,8 %.
- **Por decidir, sin aplicar: comparar solo el mismo envase entre semanas.** Medido sobre esta regla: alertas K6 4.043 → 3.924 (salen 363, entran 244); última semana 15 → 12. De 2.377 alertas mayoristas con envase común, 223 (9,4 %) cambian menos de 10 % en el mismo envase y 44 apuntan en sentido contrario. El 6,0 % de los cambios semanales nacionales mayoristas se mueve más de 5 puntos. Agregaría una tabla de 271.070 filas por envase a la Base DuckDB. El consumidor no usa volumen, pero 7.530 de sus 571.138 precios semanales (1,3 %) también mezclan envases.
- **Riesgo conocido:** pesar por cantidad da más peso a una fila mal rotulada por la fuente. Choclo en La Araucanía, semana del 7 de abril de 2025, pasa de $102 a $8 por una fila de `$/malla 50 unidades` a $200, que parece precio por unidad; RN-12 la marca como atípica, así que no entra a los indicadores.
- **Pruebas:** `tests/test_etl.py` (el peso por cantidad), `tests/test_unit_review.py` (lo que trae cada una de las 199 unidades, igual en la ETL y en dbt), `tests/test_data_audit.py` (el recálculo desde las filas crudas) y la suite completa. La falla se anota como F-39.

## D-522 · Toda variación compara solo el mismo envase
- **Pedido del autor:** aplicar la regla en todo lo que muestra una variación (alertas, tabla del paso 4, medianas por familia, mapa y Excel), mostrar el envase comparado bajo el producto y como columna en el Excel y el CSV. El autor aprobó dejar fuera lo que no compara semanas seguidas.
- **La falla:** D-521 corrige el nivel del precio, pero un cambio de envase entre dos semanas seguía pareciendo un movimiento. Kiwi Hayward Especial mayorista, semana del 26 de octubre, publicaba +25,6 %: la región del Maule pasó de `$/bandeja 18 kilos` a `$/bandeja 10 kilos`. En el mismo envase subió +8,8 %, y no es una alerta.
- **Decisión (RN-15):** `int_prices__same_package` compara cada región con la semana anterior solo en los envases vendidos las dos semanas. Dentro de un envase el volumen pesa como en RN-07; entre envases, un promedio simple, para no depender de cuánto trae cada uno. La tabla nueva `weekly_same_package` guarda ese cambio entre precios válidos de las dos semanas, y `latest_by_source` lo trae para el paso 2. Un precio sin un envase común queda fuera de la comparación, y «Ver cálculo» lo dice en cada región. `weekly_price` no cambia: sigue siendo el nivel del precio.
- **Quién la usa:** alertas K6 nacionales y por región, K5, el paso 2 por canal, la tabla del paso 4, las medianas por familia, el mapa, las regiones que suben y bajan, las líneas de tendencia, el Excel y el CSV, el «Informe semanal» y la medición de calidad.
- **Quién no, con aprobación del autor:** el índice de «Análisis» (cada mes contra enero de 2022, mediana de series de consumidor: la regla sacaría 16 de 1.868 series regionales), «Temporada» (K4, cada semana contra el promedio de su año), K1, K2 y K3 (comparan la misma semana), RN-12 (la mediana de la misma semana), el cuadro del IPC (el INE no tiene envases) y Consultas SQL (muestra el `precio` real; la tabla nueva también se puede consultar).
- **Lo que se ve:** el paso 4 dice «Envase comparado: …» en la línea bajo el producto, y el Excel y el CSV traen esa columna; al pasar el cursor explica por qué el precio puede diferir del de Consultas SQL. Si el envase es el mismo kilo o unidad de la fila, no agrega nada y no se muestra.
- **Antes y después (Base DuckDB local, se publica con la próxima carga), sobre la base de D-521 y con los mismos archivos de ODEPA:**
  - Alertas K6: 4.043 → 3.903 (salen 413, entran 273); mayoristas 2.390 → 2.271; de consumidor 1.653 → 1.632. Última semana: 15 → 13 (sale Kiwi Especial y Pomelo Start Ruby).
  - Cambios semanales nacionales: 185.081 → 184.078 con comparación (1.003 quedan fuera). Se mueven más de 5 puntos: 3.868 mayoristas y 188 de consumidor. Última semana: 724 → 719 con comparación, y 49 se mueven más de 1 punto.
  - Medianas por familia de la última semana: solo cambia Frutas, de +0,38 % a +0,48 %, y Hortalizas, de −0,02 % a −0,01 %. La canasta sigue en 0,0 %.
  - Base DuckDB: de 14,7 a 29,4 MB, por las 708.730 filas de `weekly_same_package`.
- **Mientras llega la próxima carga:** la base publicada no trae la tabla. `queries.resolve_same_package` da entonces las mismas columnas desde `weekly_price`, con la regla anterior, así que la app y el CI funcionan antes de la carga.
- **Pruebas:** `tests/test_same_package.py` reconstruye la tabla desde las filas crudas de ODEPA, sin dbt, y comprueba el kiwi, la lectura por canal y la base anterior. `tests/test_reconciliation.py` (K5 y K6 en SQL y Python), `tests/test_region_scope.py` (cada alerta regional recalculada) y `tests/test_price_export.py` (la columna nueva). La falla se anota como F-40.

## D-523 · «Reglas de transformación»: qué le hacemos a los datos y por qué
- **Pedido del autor:** una página en «Ingeniería de datos», junto a «Pipeline y linaje», para que cualquiera que revise el proyecto entienda qué se le hace a los datos de ODEPA y por qué, sin leer el código. Simple, premium y con un diagrama que muestre dónde se aplica cada regla.
- **Decisión:** cada regla dice qué problema de la fuente resuelve y qué pasaría si no existiera, en lenguaje claro y con un caso real cuando ayuda. Los números RN y D y el código van como respaldo, al final. Arriba, un diagrama con los logos en el orden que recorre el dato y, bajo cada capa, sus reglas numeradas; un clic en una regla la abre y un clic en una capa filtra la lista. Dos pestañas: «Reglas del pipeline» y «Cálculos e indicadores», esta última con cuáles usan la regla del mismo envase (●) y por qué las demás no (○).
- **Inventario:** se hizo leyendo el código: 69 transformaciones. Las reglas 1 a 41 son del pipeline, por capa; las 42 a 69, los indicadores y cálculos del panel. Son dos más que las 67 del primer recuento, por `int_prices__same_package` y `weekly_same_package` (D-522), y por eso se corre la numeración. Viven en `docs/arquitectura/reglas_transformacion.json`, en los dos idiomas.
- **Inferencias marcadas (◆):** tres lecturas que calzan con los precios pero que ODEPA no declara: `$/kilo (en caja de 17 kilos)` cuenta cajas, `$/docena de atados (N kilos)` es el peso de toda la docena y `$/cien en rama` son 100 unidades.
- **Código:** una referencia guarda un texto del archivo, no un número de línea, y la línea se calcula al dibujar la página, así no queda vieja. El archivo y la línea los ve cualquiera; el enlace al repositorio, solo el Autor (D-500).
- **Medido con Playwright:** a 1440 × 790 y 1280 × 800 la página cabe sin scroll en las dos pestañas; a 1920 × 1000, 1100 × 650 y 700 × 500 el diagrama se escala entero, con 0 textos y 0 reglas encimados, en español y en inglés. El menú se pliega al entrar.
- **Pruebas:** `tests/test_transformation_rules.py` (cada regla con problema y consecuencia en los dos idiomas, cada referencia a una línea que existe, cada D y RN citado existe, las tres inferencias, lo que usa la regla y por qué no el resto, el enlace solo para el Autor, flechas rectas, la vista Usuario no llega).

## D-524 · «Catálogo de controles», con las unidades nuevas a la vista
- **Pedido del autor:** una pestaña «Catálogo de controles» en «Controles de datos», donde aparezcan las unidades nuevas sin clasificar, para que no se acumulen en silencio.
- **Decisión:** la pestaña lista los 20 controles del proyecto, leídos de `docs/calidad/catalogo_controles.json`: qué protege cada uno, cuándo corre y qué pasa si falla (detiene la carga, conserva lo anterior, marca el dato y sigue, o avisa), con su respaldo. Arriba, las unidades de venta: cuántas están revisadas a mano y cuáles son nuevas, cómo se leen hoy, desde cuándo y si detendrían la carga.
- **Por qué una tabla nueva:** la app publicada no tiene `etl/raw.db`, así que no podía saber qué unidades trae ODEPA. Cada carga guarda ahora en la Base DuckDB las unidades que vio (`source_unit`). La lista revisada pasa de `tests/fixtures/` a `etl/reviewed_units.csv`, porque ya no la leen solo las pruebas.
- **También en el «Informe semanal»:** una unidad nueva va ahí en su propia sección, porque nadie abre la página cada martes. Sin unidades nuevas, la sección no aparece.
- **Pruebas:** `tests/test_control_catalog.py` (cada control con sus textos y una línea de código que existe, qué puede hacer cada unidad nueva, la página y el informe las nombran, el enlace solo para el Autor, el inglés). El MANUAL dice qué hacer si la carga se detiene por una unidad nueva.

## D-525 · «Descargar» con una alerta elegida baja las alertas, y la ventana escribe sus propios filtros
- **Falla (F-41):** con «▲ n alzas fuertes» o «▼ n bajas fuertes» pulsado, el paso 4 muestra la tabla de alertas, pero «Descargar» bajaba los precios de la familia entera mientras la hoja «Notas» decía «Solo alzas fuertes». Y en la tabla ampliada, la hoja «Notas» escribía los filtros del panel al abrirla, no los que la ventana tenía al bajar el archivo.
- **Decisión:** con una alerta elegida, el archivo lleva las filas de la tabla de alertas: las mismas, en el mismo orden y con los dos precios que muestra (D-482); las regiones al alza y a la baja salen del mismo conteo que la tabla de productos, y el envase comparado, de la fila de la familia del mismo producto (D-522). La búsqueda acota entre las alertas, como en la tabla. La ventana calcula sus notas con sus propias elecciones (búsqueda, orden y alerta) y, con una alerta, ofrece también «Descargar» junto al encabezado, que antes no tenía.
- **Pruebas:** `tests/test_price_export.py` (las filas del archivo son las de la tabla de alertas con sus cifras, la búsqueda acota entre ellas y el envase viaja desde la fila de la familia; en el panel, con una alerta elegida, el conteo y las notas son los de las alertas, y la ventana ofrece la descarga; la ventana escribe su propia búsqueda en las notas).

## D-526 · «Modelo de datos» usa los nombres oficiales: «registro de cargas» y «clave lógica»
- **Pedido del autor:** sí a los dos cambios que la sesión propuso al cerrar D-519.
- **Decisión:** el modelo estrella titula «REGISTRO DE CARGAS» el grupo etl_run → rejection, que decía «AUDITORÍA DE CARGAS», y el chip de la barra dice «Registro de cargas», el nombre oficial de `etl_run`. El rol «auditoría» de las dos tablas en el diccionario del SAD y en los textos al pasar el cursor no cambia: dice qué son, no cómo se llaman. El diagrama entidad-relación dice que la clave de weekly_price es lógica: sus cinco columnas PK identifican cada fila, pero normalized_unit queda vacía en las cotizaciones sin unidad legible (12.185 filas hoy, D-520) y una clave primaria estricta no admite vacíos. La cifra se lee de la base al abrir la página, en el panel y en la figura del SAD; sin ella, la leyenda queda como estaba.
- **Pruebas:** `tests/test_star_model.py` y `tests/test_dashboard.py` (el título nuevo, una vez, y el antiguo en ninguna parte), `tests/test_er_diagram.py` (la cifra es la de la base, la leyenda crece una línea solo con ella, y se lee en inglés).

## D-527 · El CI prueba con la base publicada: la suite corre con las dos bases antes de subir
- **Falla (F-42):** la subida de D-500 a D-526 dejó en rojo los dos workflows del commit 410d6e0. `pruebas.yml`: ninguna prueba falló; el job de pytest tocó su tope de 15 minutos (tardó 14,6–15,1; la última corrida verde iba en 13,5) y GitHub lo canceló. `calidad.yml`: dos indicadores fuera de lo aceptable. `secretos_sin_clasificar` = 1, porque el nombre de una prueba de D-521 («…packages_weighs_the_kilos_each_brings…») contiene «ghs_» y 36 letras, que detect-secrets lee como un token de GitHub. `pruebas_fallidas` = 2, porque el CI descarga la base publicada, que aún no tiene `source_unit` (la prueba del diccionario del SAD no la toleraba) y trae en `dbt_node` la descripción anterior de `int_prices__weekly`, cuyo inglés D-521 había reemplazado; la suite local corría solo con la base reconstruida.
- **Decisión:** el job de pytest tiene tope de 30 minutos; la prueba se llama «…packages_is_weighted_by_the_kilos_each_brings_not_by_the_packages»; `etl/pipeline.py` declara en `PYTHON_TABLES` la tabla que escribe en Python (`source_unit`) y la prueba del diccionario la tolera; la capa de inglés conserva la traducción de la descripción anterior junto a la nueva. Regla nueva en CLAUDE.md: antes de subir, la suite completa corre con la base publicada y con la reconstruida.
- **Pendiente tras la próxima carga:** cuando la base publicada traiga `source_unit` y la descripción nueva, quitar las dos tolerancias, marcadas D-527: la de `tests/test_documents.py` y la entrada antigua de `bi/i18n_en.py`. Queda anotado también en F-42, cuya ocurrencia sigue abierta hasta entonces.
- **Pruebas:** la suite completa en verde con las dos bases, la publicada (en una copia del repositorio, sin respaldo, como el CI) y la reconstruida.

## D-528 · Se quitan las tolerancias de D-527 y el envase se lee entero en la ventana ampliada
- **Pedido del autor:** con la carga del 4 de noviembre publicada (la Base DuckDB trae `source_unit` y la descripción nueva de `int_prices__weekly`), quitar las dos tolerancias de D-527, cerrar F-42 y que el envase comparado se vea completo en la tabla ampliada.
- **Decisión:** la entrada antigua de la descripción sale de `bi/i18n_en.py`. La prueba del diccionario del SAD deja de ser temporal: una tabla que el pipeline escribe en Python (`PYTHON_TABLES`) cuenta como servida, igual que las de dbt, porque la misma ventana entre un push y la carga siguiente se repetiría con cualquier tabla nueva. En la ventana ampliada el envase comparado puede ocupar hasta 720 px; en el panel sigue en 330, con el texto completo al pasar el cursor. F-42 queda resuelta.
- **Pruebas:** lint y las pruebas de los archivos tocados (`tests/test_documents.py`, `tests/test_i18n.py`, `tests/test_quality_method.py`, `tests/test_git_workflow.py`, `tests/test_home_mockup.py`), con la base reconstruida y con la publicada.

## D-529 · «Acta de cierre»: el noveno documento, con cómo empezó el proyecto, qué se encontró y a quién sirve
- **Pedido del autor:** un acta de cierre, elegante y simple, que cuente cómo empezó el proyecto, su visión y misión, qué se creía de las fuentes y qué se encontró, cómo se abordó, el rol del autor como ingeniero y BSA, lo que aprendió de DevOps y del negocio, a quién sirve, las sorpresas en los datos, los puntos fuertes y menos fuertes y lo que queda por profundizar; visible en la carpeta «Documentos» de la app, no solo en el repositorio.
- **Decisión:** `docs/negocio/ACTA_DE_CIERRE.md`, con su versión en inglés, es un documento de lectura más: portada, índice, doce secciones, glosario e historial, y tres figuras propias (`linea_proyecto`, las etapas del proyecto por fecha; `esperado_real`, lo que se esperaba de las fuentes frente a lo que se encontró; `para_quien`, a quién sirve). Va en «Documentos» después del PRD, con la ruta `acta-de-cierre`. Cada cifra del acta sale del repositorio (69 reglas, 20 controles, 1.505 pruebas, 14 indicadores, 42 fallas, 519 decisiones, 12.185 filas sin unidad, el kiwi de 25,6 % a 8,8 %, el IPC de 2022); el asistente de inteligencia artificial se nombra como tal, sin marca.
- **Pruebas:** las de todo documento de lectura (`tests/test_documents.py`, `tests/test_i18n.py`, `tests/test_doc_diagrams.py`) y la carpeta con nueve documentos (`tests/test_dashboard.py`).

## D-530 · Una visita nueva parte con el Semanal bloqueado; la misma visita conserva lo elegido
- **Pedido del autor:** al reiniciar el computador, el dashboard Semanal seguía desbloqueado. Regla: una visita nueva parte bloqueada; dentro de la misma visita, también al cambiar de perfil, se mantiene lo elegido.
- **Causa:** desde D-372 una dirección que nombra una región o una familia (`?_home_region=…&familia=…`) contaba como elegida. El navegador restaura esa dirección al volver a abrir la pestaña, también después de un reinicio, y la sesión nueva desbloqueaba los pasos sin ningún clic. Nada se guardaba en el navegador: era la dirección.
- **Decisión:** la dirección sola ya no desbloquea nada. Cuando la visita elige una región o una familia, la app escribe en la dirección un ticket de visita (`_v`) que el servidor emitió y renueva en cada ejecución; caduca a los 30 minutos sin actividad, como la sesión del Autor (D-395). Una sesión nueva que llega con un ticket vigente continúa la visita (una recarga, la segunda carga de Streamlit Community Cloud, un reinicio breve); sin ticket, o con uno caducado, parte bloqueada aunque la dirección nombre la familia. Dentro de la sesión los pasos siguen en el estado, también al cambiar de perfil y al volver con «Volver».
- **Pruebas:** `tests/test_panorama_steps.py::test_d530_…` (sin ticket y con ticket caducado, bloqueado; con ticket vigente, abierto y la sesión lo adopta; un clic escribe el ticket en la dirección y caduca por inactividad). Las pruebas que fijaban una familia en la dirección marcan el paso hecho o llevan un ticket de pruebas.

## D-531 · Al recargar la página o cambiar de perfil, el Semanal vuelve a su estado inicial
- **Pedido del autor:** el dashboard Semanal debe partir bloqueado en cada recarga y en cada cambio de perfil; lo elegido se conserva solo mientras dura la sesión, sin recargar.
- **Decisión:** reemplaza a D-530. La dirección nunca abre un paso: ni `_home_region` ni `familia` cuentan como elegidos, y el ticket de visita (`_v`) desaparece. Un paso se abre solo con un clic de la sesión (mapa, «Todo Chile», familia); un enlace de canal (paso 2) lleva los pasos ya hechos al canal que abre. Elegir una vista en «Elige tu vista», también con «Vista: … · Cambiar», devuelve el Semanal al inicio: borra los pasos de todos los canales y quita de la dirección la región, la semana, la familia, la alerta y el canal (`reset_home_steps`). Una recarga crea una sesión nueva y parte bloqueada por sí sola.
- **Pruebas:** `tests/test_panorama_steps.py::test_d531_…` (la dirección sola no abre nada; el enlace de canal conserva los pasos; elegir perfil los borra y limpia la dirección); las pruebas que fijan una familia en la dirección marcan los pasos hechos.

## D-532 · Buscar, filtrar, una alerta o «Ampliar» redibujan solo el paso 4, no toda la página
- **Pedido del autor:** la app pública se siente lenta; medir dónde se va el tiempo y acelerar.
- **Medición:** en local, un clic en el Semanal reejecutaba la página entera (0,2 s de servidor; unas tres veces más en Streamlit Community Cloud) y volvía a armar el mapa, los canales, las familias y la tabla. Una búsqueda tardaba 449 ms de punta a punta en el navegador.
- **Decisión:** la línea de alertas y el paso 4 viven en un fragmento (`st.fragment`): una búsqueda, el filtro «Mostrar», un botón de alerta o «Ampliar» reejecutan solo esa parte; el mapa y los pasos 1 a 3 no se tocan. El fragmento lee la alerta de la dirección por sí mismo, y un botón de alerta reejecuta el fragmento, no la página. Un clic en el mapa, en «Todo Chile», en un canal o en una familia sigue reejecutando la página, porque cambia todo lo demás. Las cifras no cambian.
- **Pruebas:** `tests/test_panorama_steps.py::test_d532_…` (la estructura del fragmento) y las de siempre del Semanal, que corren la página completa.

## D-533 · «Análisis de la fuente de datos»: una carpeta aparte con los dos cuadernos que estudian el archivo de ODEPA
- **Pedido del autor:** mostrar en la app el estudio de la fuente, sin mezclarlo con los documentos de arquitectura: una carpeta propia, al lado de la de documentos, con el nombre dentro de la carpeta; la de documentos pasa a llamarse «Documentos del proyecto»; «Fuentes» queda como estaba, debajo; no una pestaña.
- **Decisión:** el pie del menú tiene dos carpetas lado a lado, «Documentos del proyecto» (antes «Documentos»; la dirección antigua abre la misma página) y «Análisis de la fuente de datos», y debajo la ficha «Fuentes». La carpeta nueva lista los dos cuadernos de Jupyter de `notebooks/`, el estudio en español y su versión en inglés, cada uno con su idioma, sus celdas, su tamaño y «Descargar» (.ipynb). Solo se abre en la app el cuaderno del idioma de la visita (D-443); el otro se descarga, y su título se cita entre «». Un cuaderno abierto se lee entero: textos, código y las salidas que guarda el archivo; la app nunca lo ejecuta. Por eso los cuadernos se guardan ejecutados, con sus salidas, también para leerlos en GitHub. Las salidas son los datos crudos de ODEPA tal como el cuaderno los imprimió: la capa de inglés no las traduce y la auditoría de idioma las lee como datos. La vista Usuario no ve ninguna de las dos carpetas (D-502). El cuaderno en español lleva también sus comentarios de código en español: es la excepción a «el código y sus comentarios, en inglés», porque es un documento de lectura en un idioma.
- **Pruebas:** `tests/test_source_study.py` (los dos cuadernos tienen la misma estructura, salidas guardadas y ningún error; la carpeta lista los dos y abre solo el del idioma de la visita; un cuaderno abierto muestra su código y sus salidas; la vista Usuario no tiene carpetas), las del menú y del pie (`tests/test_dashboard.py`, `tests/test_menu_order.py`, `tests/test_sidebar_scroll.py`) y la auditoría de inglés, que recorre también el cuaderno abierto (`tests/test_i18n.py`).

## D-534 · El estudio de la fuente queda cerrado: las piezas pesan como un kilo y tres lecturas quedan como inferencias
- **Pedido del autor:** cerrar el proyecto sin pendientes en el estudio de la fuente: mantener cómo se pesan las piezas de zapallo y sandía, y no consultar a ODEPA.
- **Decisión:** en `$/kilo (volumen en unidades)` cada pieza sigue pesando como un kilo dentro de la semana (`volume_quantity = 1`, D-521): no cambia el precio de cada día, y un peso por pieza sería inventado. La regla 21 de «Reglas de transformación» lo dice. La caja de 17 kilos, el volumen en envases y «cien» siguen siendo inferencias respaldadas por los datos, marcadas como tales, sin consulta pendiente: los dos cuadernos (anomalía 14 tratada, resumen sin «por confirmar») y el Acta de cierre (versión 1.1, sin la consulta en «Qué queda») lo dicen. Las limitaciones del Acta siguen nombrando las tres inferencias. No cambia ninguna cifra.
- **Pruebas:** `tests/test_source_study.py`, `tests/test_transformation_rules.py` y las del Acta en `tests/test_documents.py`.

## D-535 · «Análisis de la fuente de datos» muestra solo el cuaderno del idioma de la visita
- **Pedido del autor:** mostrar un solo cuaderno, el del idioma de la visita, para que en inglés todo se vea en inglés, con una línea que avise que el mismo estudio está en el otro idioma.
- **Decisión:** la carpeta lista solo el cuaderno del idioma de la visita, con «Abrir» y «Descargar». La línea de arriba dice «Cuaderno de Jupyter · el mismo estudio está también en inglés (EN)», y en una visita en inglés, «… also in Spanish (ES)»; el botón ES/EN del pie lleva a la otra versión. Los dos cuadernos siguen en `notebooks/` y se leen en GitHub. Reemplaza el listado de los dos cuadernos de D-533.
- **Pruebas:** `tests/test_source_study.py` (un solo cuaderno, una descarga, sin el título ni la dirección del otro, y la línea que nombra el otro idioma), la auditoría de inglés (`tests/test_i18n.py`) y las del menú y el encabezado (`tests/test_dashboard.py`, `tests/test_menu_order.py`, `tests/test_page_bar.py`).

## D-536 · «Documentos del proyecto» muestra los cinco principales; los otros cuatro quedan como anexos
- **Pedido del autor:** reducir lo que ve quien abre la carpeta, sin borrar nada de lo que la app y las pruebas leen por debajo.
- **Decisión:** la carpeta lista cinco documentos: PRD, Acta de cierre, SAD, Plan de calidad y MANUAL. El Glosario, el ADR, el Índice de decisiones y el Plan de pruebas y seguridad quedan como anexos (`FOLDER_ANNEXES`): siguen en `docs/` y `docs/en/`, con su página, su PDF y su ruta «Documentos del proyecto › …», y se abren desde los enlaces de los demás documentos; el «Mapa de la app», «Arquitectura de seguridad» y las figuras siguen leyéndolos. Los pasos «← Anterior» y «Siguiente →» recorren solo los cinco principales, y un anexo vuelve a la carpeta, para que ningún paso muestre un documento que la carpeta no lista. El «Mapa de la app» lo dice. Ningún archivo se borra; en GitHub se ven los nueve.
- **Pruebas:** `tests/test_dashboard.py` (la carpeta lista cinco y ningún anexo; los pasos de un documento principal y de un anexo), `tests/test_documents.py`, `tests/test_i18n.py`, `tests/test_app_map.py` y `tests/test_page_bar.py`.

## D-537 · La cuadrícula de «Documentos del proyecto» llena la fila, como un estante
- **Pedido del autor:** en la vista de cuadrícula, los documentos dejaban un gran espacio vacío a la derecha; mostrarlos como una biblioteca de audiolibros, que reparte las portadas en todo el ancho.
- **Decisión:** la cuadrícula ya no agrupa por carpeta: los documentos principales van en una sola fila que se reparte todo el ancho (`repeat(auto-fit, minmax(170px, 1fr))`), y una ventana angosta baja los últimos a otra fila. Cada tarjeta dice arriba, en el color de su carpeta, a cuál pertenece (Negocio, Arquitectura, Calidad, Operación). La vista de lista sigue agrupada por carpeta, porque sus filas ya ocupan el ancho. El índice que se abre al pasar el cursor se abre hacia la izquierda en las dos últimas tarjetas.
- **Pruebas:** `tests/test_dashboard.py` (una sola cuadrícula, sin grupos, una tarjeta y un nombre de carpeta por documento principal, y las cuatro carpetas nombradas), `tests/test_i18n.py` y `tests/test_documents.py`.

## D-538 · El pie del menú pone las dos carpetas y «Fuentes» en una sola fila compacta
- **Pedido del autor:** las dos carpetas y «Fuentes» ocupaban tanto alto que el menú se cortaba y «Calidad» no se veía al abrir la app; entre plegar el pie en una línea o compactarlo, eligió compactarlo.
- **Decisión:** «Documentos del proyecto», «Análisis de la fuente de datos» y «Fuentes» van lado a lado en una fila de 62 px, en vez de dos filas de unos 125 px; cada mosaico guarda su nombre oficial completo, en letra chica (0,65 rem), con su ícono un poco menor. Siguen a la vista y a un clic. La vista Usuario, que no tiene carpetas (D-502), ve en esa fila solo «Fuentes».
- **Pruebas:** `tests/test_sidebar_scroll.py` (una fila de 62 px con los tres mosaicos, «Fuentes» dentro de ella), y las del menú, la vista Usuario y el inglés (`tests/test_menu_order.py`, `tests/test_user_view.py`, `tests/test_dashboard.py`, `tests/test_i18n.py`).

## D-539 · El pie del menú pasa a ser una barra de íconos a la izquierda, como la de VS Code
- **Pedido del autor:** la fila compacta de D-538 cortaba las palabras y no liberaba el alto: «Calidad» seguía fuera de la vista. Tomar como modelo la barra de actividad de VS Code: una columna angosta de íconos al costado del menú, con lo que estaba en el pie.
- **Decisión:** el pie deja el final del menú y se vuelve una columna de 40 px (`ACTIVITY_BAR`) pegada al borde izquierdo, de alto completo: arriba «Documentos del proyecto», «Análisis de la fuente de datos» y «Fuentes»; abajo «Apariencia» y ES/EN (y GitHub para el Autor). Cada ícono dice su nombre al pasar el cursor, y su nombre sigue para los lectores de pantalla; la carpeta abierta se marca con una raya, como en VS Code. El menú conserva sus 232 px al lado (D-501), así que el panel lateral mide 272 px; con el menú plegado, la barra se pliega con él. La vista Usuario ve en la barra solo «Fuentes», «Apariencia» y el idioma (D-502). Reemplaza la fila de D-538. Como el contenido quedó 40 px más angosto, la nota «Cobertura» de «Semanal» pasaba a tres líneas: su margen superior y su interlineado se ajustaron para que la página siga cabiendo en una pantalla.
- **Medición** (Chrome sin ventana, por su puerto de depuración): a 1440 × 900 el menú cabe entero y «Semanal» mide 900 px de 900; a 1280 × 720 el menú también cabe (antes le sobraban 18 px y «Calidad» quedaba cortada) y «Semanal» baja de 757 a 744 px; con el teléfono girado (844 × 390) la barra se ve a la escala del resto.
- **Pruebas:** `tests/test_sidebar_scroll.py` (la barra fija a la izquierda, de 40 px, el menú a su lado con sus 232 px, los íconos de 34 px, plegada con el menú, y cada ícono con su nombre al pasar el cursor), `tests/test_dashboard.py`, `tests/test_menu_order.py`, `tests/test_user_view.py`, `tests/test_page_bar.py`, `tests/test_repository_links.py` y `tests/test_i18n.py`.

## D-540 · Íconos de línea con forma en la barra, y el stack de cada área en cinco íconos nuevos
- **Pedido del autor:** que cada ícono de la barra tenga la forma de lo que abre, como en VS Code, no solo un color: hojas para «Documentos del proyecto», un matraz de laboratorio para «Análisis de la fuente de datos» y una base de datos para «Fuentes». Y usar el espacio libre para listar, por área, las herramientas y los conceptos de ingeniería que usa el proyecto, solo sus nombres y por orden de relevancia, para mostrarlos y estudiarlos; visibles para todas las vistas, también la del Autor en DevOps.
- **Decisión:** `bi/activity_bar.py` guarda los íconos (línea de 1,6 px en una cuadrícula de 24) y las cinco áreas: «Stack · Código», «Stack · Ingeniería de datos», «Stack · Calidad», «Stack · DevOps y seguridad» y «Stack · Negocio · BA y BI», nombres aprobados por el autor (las áreas siguen las secciones del menú). Cada ícono es una máscara CSS pintada con la tinta suave del menú, que se aclara al pasar el cursor o con su página abierta. Cada área abre una ventanita con sus nombres numerados, sin explicaciones ni enlaces, y va encima de «Fuentes». Las áreas se ven en todas las vistas, también la de Usuario: no abren ninguna otra página (D-502 sigue: ningún enlace sale de sus páginas). Cada nombre de las listas está en el repositorio: las dependencias de `requirements.txt` y `requirements-pipeline.txt`, las herramientas de `pruebas.yml` y `calidad.yml`, los modelos y pruebas de `dbt/`, `.devcontainer/` y los documentos.
- **Medición** (Chrome sin ventana): a 1440 × 900 los íconos quedan a 40 px uno de otro, el menú cabe entero y «Semanal» mide 900 px de 900; la ventana de «Stack · DevOps y seguridad» muestra sus 15 nombres.
- **Pruebas:** `tests/test_sidebar_scroll.py` (un ícono de línea por botón, y las cinco áreas en la barra para Usuario y Profesional, sin enlaces), `tests/test_user_view.py` y la auditoría de inglés (`tests/test_i18n.py`), con el inglés de cada nombre en `bi/i18n.py`.
- **Falla F-43, encontrada al correr la suite completa:** `test_d335` del aviso de calidad usaba la fecha de hoy; desde el 5 de noviembre el informe N° 2 cuenta como antiguo (D-361) y la prueba falló, también en `pruebas.yml` y `calidad.yml` del commit e192a15. La prueba fija ahora el día del informe. Tres pruebas del menú (`test_d295`, `test_d070`, `test_d117`) leen el menú sin las ventanas de stack, que nombran áreas y herramientas, no secciones; y `test_d339` de «GitHub Actions» lee solo la página.

## D-541 · `bi/dashboard.py` se divide en archivos por responsabilidad
- **Pedido del autor:** el archivo del panel tenía unas 10.000 líneas que no necesitaban estar juntas (baja cohesión): páginas, perfiles, estilos, menú y nombres fijos. Separarlo por familias, en el orden que no rompe nada, y que cada archivo siga la forma de `agent/agent.py` (docstring, imports, región de constantes, región de variables y una región por tema, sin funciones dentro de otras; regla R-001 de `AKGRO.md`).
- **Decisión:** primero la base, que todas las páginas usan, y después las páginas, porque Streamlit corre `bi/dashboard.py` como programa principal y un módulo no puede importarlo. El orden: `bi/constants.py` (nombres fijos), `bi/data_access.py`, `bi/app_style.py`, `bi/app_frame.py`, y las páginas `page_quality`, `page_engineering`, `page_documents`, `page_analysis`, `page_weekly` y `page_devops`; `bi/dashboard.py` se queda con la navegación, el menú, la barra de íconos y el arranque. Cada paso es un commit con sus pruebas. `bi/dashboard.py` importa lo que usa, y los pocos nombres que las pruebas leen a través de él quedan marcados como tales. El código se mueve sin cambiar su lógica.
- **Paso 1:** `bi/constants.py` recibe los 149 nombres fijos de la región «Constants» (la ruta de `manifest.json`, en su región «Variables»). Cinco nombres que nada usaba (`GAP_MEANING`, `ALERT_MEANING`, `DEFAULT_CHANNEL`, `SUPERMARKET`, `WHOLESALE_LABEL`) se borran. El ancla del «Mapa de la app» que señalaba `SECRET_CONTROL_CODE` apunta a su archivo nuevo. `bi/dashboard.py` baja de 10.100 a 9.711 líneas.
- **Pruebas:** las del mapa de la app (sus anclas), la recarga de módulos, el menú, la barra, la vista Usuario, el panel, el inglés, el encabezado, los documentos y «Semanal».
- **Paso 2:** `bi/data_access.py` recibe las lecturas de la Base DuckDB, su versión publicada, las alertas, los indicadores y la hora de Chile (35 definiciones, sin cambiar su lógica), con `read_latest_by_source`, que estaba entre las de «Análisis» pero solo lee la base. El ancla de la regla 54 de «Reglas de transformación» apunta a su archivo nuevo. Se borran las ocho regiones que quedaron vacías, entre ellas «Margins page», «Channels and regions page» y «Seasonality page», restos de páginas retiradas. `bi/dashboard.py` queda en 9.425 líneas.
- **Paso 3:** `bi/app_style.py` recibe las hojas de estilo globales: el tema, el CSS de la app, los colores del código y el menú con su barra de íconos, con sus constantes (tintas del menú, ancho de la barra y los SVG de los mosaicos) y la función que decide si un fondo es oscuro (16 definiciones). Los estilos de cada página siguen con su página. Una prueba de la ventana ampliada que buscaba sus selectores en `bi/dashboard.py` los busca en su archivo nuevo. `bi/dashboard.py` queda en 8.008 líneas.
- **Paso 4, preparación:** el marco de la app (perfiles, acceso del Autor, encabezado) usa piezas que vivían más abajo, y un módulo no puede pedírselas a `bi/dashboard.py`. Antes de mudarlo, cada pieza va a su archivo según su responsabilidad: las claves de sesión de «Semanal», del Autor y de la ventana de la carga, las listas del menú (secciones, puertas, etiquetas, la carpeta de documentos y sus anexos) y el historial de «Volver» van a `bi/constants.py`; la clave secreta, las cargas de GitHub y el vencimiento del token, a `bi/data_access.py` (región «GitHub reads»). El ancla del «Mapa de la app» de los secretos apunta a su archivo nuevo, y una prueba de la ventana «Elige tu vista» lee el código de todo `bi/`.
- **Paso 4:** `bi/app_frame.py` recibe el marco de la app (76 definiciones): el tema y el perfil de la visita, el acceso del Autor y sus avisos, las direcciones y ventanas de las páginas con el historial de «Volver», el encabezado con sus controles, y las tarjetas, enlaces y textos que dibujan todas las páginas. Las anclas del «Mapa de la app» (la ventana «Elige tu vista») y la pieza «Secretos y tokens» del «Flujo del sistema en vivo» apuntan a sus archivos nuevos (`bi/app_frame.py` y `bi/constants.py`); cuatro pruebas que buscaban código en `bi/dashboard.py` leen ahora todo `bi/`. `bi/dashboard.py` queda en 6.855 líneas.
- **Paso 5, preparación:** las páginas comparten piezas entre ellas; antes de separarlas, las compartidas bajan a su capa, sin cambiar su lógica: la barra de cada página, el encabezado compacto, la hora de las cargas, los enlaces externos y al repositorio, las pestañas, la búsqueda de una página por su nombre, el tema oscuro, la dirección de un canal y las fuentes atrasadas, a `bi/app_frame.py`; las fotos de la semana, el linaje, el manifiesto de descargas, las familias y los datos del flujo, a `bi/data_access.py`; el orden y los íconos del menú, los nombres de canal, de pestaña y de dirección, el catálogo de consultas y el registro de ventanas, a `bi/constants.py`. Las pruebas que fingían ser el Autor reemplazando `is_author` en `bi/dashboard.py` fingen ahora la sesión, que es lo único que esa función lee, así no dependen de dónde vive el código. `bi/dashboard.py` queda en 6.597 líneas.
- **Paso 5:** `bi/page_quality.py` recibe «Controles de datos»: las cifras de cada carga, las filas excluidas y sus motivos, y la evidencia de calidad con su botón para volver a medir (21 definiciones). Los imports de los módulos nuevos quedan ordenados en tres grupos (estándar, externos y del proyecto). Una prueba que buscaba en `bi/dashboard.py` cómo se nombran los archivos cambiados lo busca en su módulo.
- **Paso 6:** `bi/page_engineering.py` recibe las páginas de ingeniería de datos (64 definiciones): «Pipeline y linaje» con la carga paso a paso, los diagramas de DevOps que también dibujan los documentos y las páginas de operación, «Modelo de datos», el catálogo de «Consultas SQL», «Stack y evidencia» y los indicadores (KPI). Antes bajan dos piezas compartidas: el estilo de las cargas a `bi/app_style.py` y la línea de atribución a `bi/app_frame.py`. La suite completa: 1.553 pruebas en verde. `bi/dashboard.py` queda en 5.158 líneas.
- **Paso 7:** `bi/page_analysis.py` recibe «Análisis» y sus pestañas, las tarjetas de familia, el contexto del precio, los «Insights» y los textos del análisis (47 definiciones). El ancla del «Mapa de la app» de los gráficos apunta al dibujante común de `bi/app_frame.py`, y la prueba que exige una sola fuente de las definiciones de los KPI revisa los archivos de la división. `bi/dashboard.py` queda en 4.083 líneas.
- **Paso 8:** `bi/page_weekly.py` recibe «Semanal» (49 definiciones): sus pasos, el modelo de la semana por región, las alertas de precio con su línea de alertas y búsqueda, los productos del paso 4 con su ventana ampliada, y «Descargar», que estaba entre las funciones de la página de arquitectura. Las anclas de las reglas 55, 58, 59 y 60 de «Reglas de transformación» apuntan a su archivo nuevo, y tres pruebas de «Semanal» leen ese módulo. Los títulos de región que nombran una página la citan entre «», como pide la regla de comentarios en inglés. `bi/dashboard.py` queda en 2.785 líneas.
- **Paso 9:** `bi/page_devops.py` recibe la sección DevOps y seguridad del Autor (37 definiciones): la ventana de la carga con «Ejecutar pipeline ahora», el acceso y los tokens del Autor, «Centro de operación» y sus pestañas, «GitHub Actions», «Configuración» y la página de seguridad. Tres pruebas que buscaban ese código en `bi/dashboard.py` lo buscan en su módulo. `bi/dashboard.py` queda en 2.106 líneas.
- **Paso 10:** la última sección mezclaba páginas de varias familias; cada una va con la suya: «Stack y evidencia» con el «Flujo del sistema en vivo», «Reglas de transformación» y «Mapa de la app», a `bi/page_engineering.py`; «Plan de calidad» con sus informes y «Cambios e incidentes», a `bi/page_quality.py`; la carpeta de documentos, la página de cada documento con sus diagramas y su impresión, los cuadernos y los enlaces del Autor, a `bi/page_documents.py`. El «Mapa de la app» contaba las pestañas de «Centro de operación» leyendo su tabla; para que Ingeniería no dependa de DevOps, los cuatro nombres viven una sola vez en `bi/constants.py` (`RUNS_TABS`) y la tabla de `bi/page_devops.py` se arma con ellos. El ancla del «Mapa de la app» de los documentos apunta a su archivo nuevo.
- **Lo que queda en `bi/dashboard.py`** (1.372 líneas): sus constantes y variables arriba, y cuatro regiones: las ventanas y páginas, los pies de página, el historial de «Volver», el menú con su barra de íconos y el arranque.
- **La recarga de D-172:** con el panel dividido, una página guarda las funciones que importó del marco, y recargar solo el archivo que cambió la dejaba con las anteriores. Ahora cada ejecución recarga el archivo que cambió y todos los que lo importan, directa o indirectamente, primero las dependencias (`order_reloads`, que lee los imports desde el código de cada módulo).
- **Resultado:** el archivo más grande del panel baja de 10.100 a unas 1.500 líneas (`bi/app_style.py`, solo CSS), y `bi/dashboard.py` a 1.372. Ruff, el formato y mypy en verde; la suite completa con 1.553 pruebas en verde, y una prueba distinta falló de forma intermitente en tres corridas (pasa sola y en su archivo; recorren pantallas con AppTest). En la app real, las 13 páginas probadas abren sin errores en el navegador, también tras cambiar `bi/app_frame.py` con el servidor encendido.
- **Pruebas:** `tests/test_app_reloads.py` (un módulo que cambia se recarga con los que lo importan, primero las dependencias), y las que leían código en `bi/dashboard.py` leen ahora el módulo de su página.
- **Sin funciones dentro de otras (R-001):** los archivos de la división traían 16 funciones definidas dentro de otras, del código anterior; una era de D-540. Las 16 pasan a primer nivel sin cambiar lo que hacen: lo que leían de su función envolvente llega por parámetro, con `functools.partial` donde Streamlit o una función pide un llamable (la página de una dirección antigua, el selector de «Stack y evidencia», los enlaces de los pasos 1 a 3 de «Semanal», el mapa de interesados, los enlaces de los documentos). En «Semanal», el paso 4 y el bloque que lo redibuja solo (D-532) reciben las elecciones de la página en un diccionario, `choices`, que Streamlit guarda de la última ejecución para cada redibujo del bloque. Una lambda de una línea que Streamlit pide como argumento no cuenta como función del módulo.
- **Prueba de la regla:** `tests/test_project.py` revisa los once archivos: docstring, imports antes de la primera región, regiones cerradas, constantes y variables antes que las funciones, y ninguna función dentro de otra. La suite completa: 1.565 pruebas en verde. El redibujo solo del paso 4 al buscar, filtrar, elegir una alerta o «Ampliar» no se puede pulsar con AppTest y queda para revisarlo en el navegador.

## D-542 · Regiones de R-001 en todo el proyecto y código sin uso fuera
- **Pedido del autor:** hacer primero lo más simple y rápido de la limpieza pendiente, y listar después lo que toma más tiempo.
- **Decisión:** se borran 14 funciones que nada llamaba: `alert_count_text` (`bi/page_weekly.py`), `incidents_in` (`bi/quality_viewer.py`), `tab_of` (`bi/transformation_rules.py`) y, en `scripts/medir_calidad.py`, nueve medidas de indicadores que el plan de calidad dejó de medir con sus 14 indicadores actuales (D-330) y los dos ayudantes que solo ellas usaban. Los 53 archivos de `bi/`, `etl/`, `agent/` y `scripts/` sin regiones reciben las de R-001 solo como comentarios, sin mover código: el bloque de constantes y variables que sigue a los imports, una región con el tema del archivo y, si lo tiene, «Run» para su arranque. Cuatro archivos antiguos con código fuera de una región o cierres sueltos (`bi/architecture.py`, `bi/doc_views.py`, `bi/project.py`, `bi/quality_view.py`) abren la región que faltaba o pierden el cierre sobrante. Los `__init__.py`, que solo marcan una carpeta como paquete, quedan como están.
- **Lo que queda como deuda:** 37 funciones dentro de otras en 13 archivos antiguos; separar por temas la región única de esos archivos y subir sus constantes al inicio; seis bloques de JavaScript y HTML guardados como texto de Python; el CSS de `bi/app_style.py` como archivos `.css` con variables por tema; las pruebas que revisan textos exactos; y las regiones de las 92 pruebas de `tests/`.
- **Pruebas:** `tests/test_project.py` exige que cada archivo de `bi/`, `etl/`, `agent/` y `scripts/` tenga regiones cerradas y no anidadas. Ruff, formato y mypy en verde; la suite completa, una sola vez al final: 1.566 pruebas en verde.

## D-543 · Ninguna función dentro de otra en todo el proyecto, y el JavaScript y el HTML en sus propios archivos
- **Pedido del autor:** terminar los dos pendientes considerables de la limpieza, rápido, y dejarlo como regla para que no vuelva a pasar (R-002 de `AKGRO.md`: cada implementación y cada corrección se revisa en su buena práctica al hacerla, no después).
- **Decisión:** las 37 funciones escritas dentro de otras, en 13 archivos antiguos, pasan a primer nivel sin cambiar lo que hacen. Las 17 que no leían nada de su función envolvente se mueven tal cual, con el nombre `_<función>_<nombre>`; las 20 que sí leían valores de afuera los reciben por parámetro, con `functools.partial` donde se entregaban como valor (un `re.sub`, una clave de orden, un camino de aristas, la proyección del mapa) y `functools.partialmethod` en las envolturas de traducción de `bi/i18n.py`, cuyos parámetros propios van solo por posición para no chocar con los de Streamlit (`options=`, por ejemplo). Los tres lectores con caché y la ventana «Relaciones» de `bi/sql_explorer.py` envuelven su función de primer nivel al llamarla, como antes. Los seis textos largos de JavaScript y HTML salen de Python a `bi/static/` (`app_map.js`, `lineage.js`, `transformation_rules.js`, `live_flow.js`, `zoom.js` y `sql_editor.html`), y los lee `bi/static_files.py`; el del zoom lleva sus dos números como marcas que Python reemplaza. Cada texto que llega a la página es idéntico al de antes, carácter por carácter (comprobado al importar cada módulo). Un cambio en un archivo de `bi/static/` se ve al reiniciar el servidor o al cambiar su módulo, porque se lee al cargarlo.
- **Lo que sigue como deuda:** el CSS de `bi/app_style.py` dentro de Python, las pruebas que revisan textos exactos y las regiones de las pruebas de `tests/`.
- **Pruebas:** `tests/test_project.py` falla si una función se escribe dentro de otra en `bi/`, `etl/`, `agent/` o `scripts/`, y si un texto de más de 100 líneas vuelve a quedar dentro de Python. Ruff, formato y mypy en verde; la suite completa: 1.568 pruebas en verde. En el navegador, «Mapa de la app», «Pipeline y linaje», «Consultas SQL» y «Reglas de transformación» abren sin errores, también en inglés.

## D-544 · El CSS sale de Python a `bi/static/`, las pruebas tienen sus regiones y las pruebas frágiles miran la forma del código
- **Pedido del autor:** resolver ahora la deuda menor que dejó la limpieza (el CSS de `bi/app_style.py` dentro de Python, las pruebas que revisan textos exactos y las pruebas sin regiones) y guardarlo como regla para que no vuelva a pasar: R-003 (el CSS, el JavaScript y el HTML viven en `bi/static/`), R-004 (una prueba mira lo que ve el visitante y lo que hacen los datos, no el texto del código) y R-005 (una prueba nueva solo si es estrictamente necesaria) de `AKGRO.md`.
- **Decisión:** toda hoja de estilo escrita en Python, en `bi/app_style.py` y en los demás módulos, pasa a su archivo en `bi/static/`: 68 archivos nuevos, 59 hojas de estilo y 9 textos de HTML y JavaScript. `bi/app_style.py` baja de 1.509 a 302 líneas. Lo que cambia con el tema o con un dato entra como marca, `var(--go-nombre)` en CSS y `__GO_NOMBRE__` en JavaScript y HTML; `bi/static_files.py` la reemplaza (`fill`) y envuelve el texto en su etiqueta (`style`, `script`). Cada texto que llega a la página es idéntico al de antes, carácter por carácter, en los cuatro temas: se comparó lo que devolvía cada función antes y después de moverlo. Los archivos de `tests/` reciben las regiones de R-001: hoy las tienen los 92, todos menos `__init__.py`. Ocho pruebas que comparaban el texto del código se rehacen: cinco miran la forma del código con `tests/code_shape.py` (qué llama una función, con qué argumentos y dentro de qué condición), dos leen la hoja de estilo que de verdad se genera y una deja de depender del formato del archivo.
- **Lo que sigue como deuda:** de esas ocho, cinco todavía leen el texto del código en alguna línea; en total, 30 pruebas lo hacen, aparte de las seis de `tests/test_project.py`, que vigilan a propósito cómo se construye el código. Se revisarán una por una con R-005: se borra la que repite lo que otra prueba ya revisa y se rehace solo la que cuida algo real. Quedan también 12 trozos de JavaScript de 10 a 43 líneas dentro de Python (`bi/app_frame.py`, `bi/dashboard.py`, `bi/github_page.py`, `bi/page_documents.py`, `bi/page_weekly.py`), que la prueba de D-543 no ve porque busca textos de más de 100 líneas. Y 17 archivos de más de 300 líneas guardan todo su código en una sola región: algunos están bien así porque son solo datos (las traducciones, las constantes), otros mezclan temas y deben separarse; esta deuda venía de D-542, y D-543 la dejó fuera de su lista sin resolverla.
- **Pruebas:** `tests/test_project.py` falla si un texto de más de 300 caracteres que se lee como CSS vuelve a quedar dentro de Python (salvo un dibujo SVG, que se arma con coordenadas calculadas), y la prueba de regiones revisa también `tests/`. Ruff, formato y mypy en verde. La suite completa corrió dos veces: en la primera falló una vez una prueba de pantalla (`tests/test_repository_links.py`, vista Profesional), que pasó sola y en la segunda corrida, sin causa encontrada; en la segunda, 1.569 pruebas en verde.

## D-545 · Las pruebas miran lo que hace la app, el JavaScript sale de Python y cada archivo tiene una región por tema
- **Pedido del autor:** terminar lo que quedó de la limpieza: las pruebas que leían el texto del código, los trozos de JavaScript dentro de Python y los archivos con una sola región.
- **Decisión:** ninguna prueba lee ya el texto del código Python, salvo las seis de `tests/test_project.py`, que vigilan a propósito cómo se construye el código. Las 30 pruebas que lo hacían, y una más que la búsqueda no había visto, miran ahora la forma del código con `tests/code_shape.py` (qué llama una función, con qué argumentos, en qué orden y bajo qué decorador) o lo que de verdad hace la app: dos prueban con un GitHub falso que cancelar una carga y lanzarla a mano envían lo correcto. Las partes que repetían lo que otra prueba ya revisa se borran (R-005 de `AKGRO.md`), como el enlace del encabezado de «Stack y evidencia», que `tests/test_page_bar.py` revisa en cada página. Los 12 trozos de JavaScript que quedaban dentro de Python pasan a `bi/static/` (11 archivos `.js` y uno `.html`); la página recibe el mismo texto, carácter por carácter (17 de 17 comparaciones). En las regiones de R-001: 20 archivos grandes que tenían una sola región se separan por tema; 71 tramos de código que estaban fuera de toda región quedan dentro de una; y las 42 regiones «Constants and variables» se separan como en `agent/agent.py`: los valores fijos en «Constants» y los que se calculan al cargar el módulo en «Variables». Una constante no lee ninguna variable, así que ponerlas primero no cambia nada. Dos constantes que estaban debajo de funciones suben con las demás (`DOCUMENT_FOLDERS` en `bi/i18n.py` y `GITHUB_PAGE_SCRIPT` en `bi/github_page.py`).
- **Lo que sigue como deuda:** 26 funciones escritas dentro de otras en 24 pruebas de `tests/`, y 177 constantes de 36 archivos escritas debajo de funciones y no al inicio; algunas se arman con esas funciones y no pueden subir.
- **Pruebas:** la prueba de D-543 falla ahora con cualquier script dentro de Python, corto o largo. Ruff, formato y mypy en verde; la suite completa, 1.568 pruebas en verde y una que falló porque solo buscaba los scripts en los archivos `.html`; corregida para leer también los `.js`, pasa junto con las que vigilan la estructura del código (39 en verde).

## D-546 · El código queda conforme con R-001 a R-005, y una auditoría lo demuestra
- **Pedido del autor:** dejar el código del proyecto conforme con R-001 a R-005 de `AKGRO.md`, todo de una vez y demostrado por una auditoría con cero en cada línea, sin cambiar ningún comportamiento, cifra ni texto que vea el visitante.
- **Funciones dentro de otras (R-001, R-002):** las 30 que quedaban (29 en 17 archivos de `tests/` y una en `tests/medicion/tabla.py`) suben al primer nivel. Lo que leían de su función llega por parámetro, o con `functools.partial` donde se entregan como valor (por ejemplo, a `monkeypatch.setattr`); los falsos que guardaban llamadas reciben su lista o su diccionario, y los dos que eran clases dentro de una prueba son clases de primer nivel. Cada prueba prueba lo mismo que antes.
- **Asignaciones debajo de la primera función (R-001):** las 209 (177 en 36 archivos de la app, 29 en 18 de pruebas y 3 en el bloque de arranque de `tests/i18n_audit.py`, que pasa a una función `main()` como en `agent/agent.py`) suben a su región. La regla, la misma en todos los archivos: va a «Constants» lo que vale lo mismo dondequiera y cuandoquiera que cargue el módulo (textos, números, expresiones regulares y valores armados solo con constantes e imports); va a «Variables» lo que depende del lugar o del momento de la carga (la ruta del propio archivo, un archivo leído del disco, el estado del disco, un objeto que guarda estado). Ninguna constante lee una variable. Las 16 que se armaban con funciones del mismo módulo son ahora funciones que lo devuelven, con `functools.cache` donde se leen seguido, y todos sus usos (también en las pruebas) las llaman: `insides()` y `engines()` en `bi/app_map_detail.py`, `icon_logo_slug()` en `bi/architecture.py`, `icons()` y `fallback()` en `bi/channel_icons.py`, `attempt_gate()` en `bi/control.py`, `build_lines()` y `join_y()` en `bi/database_crossings.py`, `builders()` en `bi/doc_diagrams.py`, `figures()` en `bi/doc_figures.py`, `views()` en `bi/doc_views.py`, `products_hint()` en `bi/home_mockup.py`, `icons()` en `bi/live_flow.py`, `defs()` e `icons()` en `bi/quality_view.py` y `examples()` en `bi/sql_explorer.py`. `RUNS_VIEWS` (`bi/page_devops.py`) sube como constante: sus funciones de una línea solo nombran la función de cada pestaña y la buscan al llamarla, y la tarjeta «DevOps» del «Mapa de la app» lo cita por ese nombre, que así sigue siendo cierto. Las alturas de `bi/doc_diagrams.py` quedan como una constante escrita en una sola expresión, en el mismo orden de antes. Los alias de funciones de otro módulo (`read_store_sizes`, `format_file_size`, `matches_product_search`) pasan a ser imports.
- **El resto de R-001:** los tres imports del medio de `bi/i18n.py` suben al comienzo (ni `bi/weeks.py` ni `bi/i18n_en.py` importan `bi/i18n.py`, así que no hay ciclo); `bi/dashboard.py`, `bi/report.py` y `etl/profile_years.py` dejan su región «Imports of the project», y su arranque (`sys.path.insert` y sus imports) queda arriba, como en las pruebas; lo mismo en cinco archivos de pruebas que lo tenían dentro de una región. `etl/etl.py` pone «Constants» antes de «Variables», `bi/doc_figures.py` lleva sus constantes al comienzo y `bi/sql_explorer.py` saca sus funciones de la región de valores. Otras 28 asignaciones que estaban en regiones de tema, sobre las funciones, pasan a «Constants» o «Variables». Los siete archivos de pruebas de más de 300 líneas con una sola región, y `bi/tech_glossary.py`, se separan por tema sin mover ninguna prueba de lugar.
- **Código sin uso (R-002):** una búsqueda que sigue cada nombre de primer nivel módulo por módulo (de qué módulo se importa, quién lo lee, también desde los scripts que corre AppTest, los workflows, los cuadernos y `bi/static/`), revisada a mano, encontró 45 nombres que nada usa; al borrarlos quedaron sin uso 6 más, que se borran también. Se borran además 4 piezas de la app que la app ya no dibuja ni llama y que solo miraba una prueba: las cajas de dueño del «Mapa de la app» (`OWNER_BOXES`: ningún elemento las dibuja), `late_week` (la tarjeta del canal calcula la semana pendiente por su cuenta), `build_report_view` (el informe se abre en `bi/quality_viewer.py`) y las rampas del mapa de calor (`HEAT_RAMPS`); con ellas, las líneas de prueba que solo las miraban, y la prueba de las cajas pasa a llamarse `test_d441_each_piece_says_who_owns_it`. Los datos que las pruebas usan como referencia se quedan.
- **Que no vuelva a pasar (sin funciones de prueba nuevas, R-005):** `test_d543_no_function_of_the_project_is_written_inside_another` revisa también `tests/` y los métodos de una clase; `test_d542_every_python_file_of_the_project_has_its_regions_closed_and_not_nested` falla además si una sentencia del módulo queda fuera de una región (salvo el docstring, los imports y el `sys.path.insert` de arranque), si una región junta «Constants and variables» o si una asignación de módulo queda debajo de la primera función. `test_d541` ya no exceptúa a `bi/dashboard.py` y pide «Constants» y «Variables» primero, en ese orden, y deja de repetir la revisión de funciones anidadas. La prueba del idioma de los comentarios pasa a la región de las pruebas de estructura, entre las que D-545 ya la contaba.
- **Auditoría** (fuera del repositorio; recorre `bi/`, `etl/`, `agent/`, `scripts/` y `tests/`; antes es el commit 5271293):

| Línea | Antes | Después |
|---|--:|--:|
| 1. Funciones escritas dentro de otras | 30 | 0 |
| 2. Sentencias de módulo fuera de una región | 13 | 0 |
| 3. Archivos con regiones sin cerrar, anidadas o sin regiones | 1 | 0 |
| 4. Regiones «Constants and variables» combinadas | 0 | 0 |
| 5. Asignaciones de módulo debajo de la primera función | 209 | 0 |
| 6. Textos de CSS, JavaScript o HTML dentro de Python (criterio de `tests/test_project.py`) | 0 | 0 |
| 7. Pruebas que leen el texto de un `.py` (fuera de `tests/code_shape.py` y de las seis de estructura) | 0 | 0 |
| 8. Funciones y constantes de primer nivel que nada usa | 45 | 0 |
| 9. Archivos de más de 300 líneas con una sola región de tema (salvo los de solo datos) | 7 | 0 |
| 10. Imports debajo de la primera región | 26 | 0 |
| 11. Asignaciones fuera de «Constants» y «Variables» | 224 | 0 |
| 12. Regiones fuera del orden de R-001 o funciones dentro de «Constants» o «Variables» | 12 | 0 |

  Las líneas 10 a 12 no estaban en el pedido: son el resto del orden de R-001 y aparecieron al revisarlo. En la línea 6, el mismo criterio encuentra en `tests/` cinco frases cortas de JavaScript que las pruebas buscan en la página, y la expresión regular del propio criterio; no son código que corra. En la línea 7, cuatro pruebas abren archivos que la app o los documentos citan como evidencia, algunos `.py` (las líneas del «Mapa de la app», las piezas del «Flujo del sistema en vivo», las señales de monitoreo y la prueba que nombra cada ADR), para comprobar que la cita es cierta: miran lo que ve el lector, como pide R-004.
- **Verificación de que nada cambió:** las 1.456 constantes de los módulos se compararon antes y después, carácter por carácter: idénticas, salvo las 34 borradas por muertas y `INSIDES`, cuyas dos funciones de una línea pasaron a `functools.partial` con los mismos argumentos. Cada constante que pasó a ser función devuelve lo mismo que valía. Las 122 pantallas del panel (61 en español y 61 en inglés: las que recorre `tests/i18n_audit.py` y tres más de la vista Autor) se dibujaron antes y después: 112 idénticas y 10 que solo reordenan filas empatadas, igual que dos corridas sin ningún cambio, una vez apartados el reloj (días desde la última carga y hora de lectura, porque las corridas cruzaron la medianoche UTC) y los números de línea que «Reglas de transformación» muestra: se calculan al dibujar la página, siguen al código que se movió y apuntan a la línea correcta.
- **Pruebas:** Ruff, formato y mypy en verde. La suite completa dio 1.566 pruebas en verde y 3 fallas en `tests/test_raw_load.py`: usaba como fábrica la descarga falsa de `tests/test_agent.py`, que al subirla al primer nivel había cambiado de forma (F-44 en `docs/calidad/plan_mitigacion.json`). `fake_downloader` vuelve a entregar la descarga, ahora con `functools.partial`, y las dos pruebas quedan como estaban. La segunda corrida completa, con la corrección: 1.569 pruebas en verde y 7 que se saltan, las mismas de siempre.

## D-547 · El README se lee como una persona y guía a quien lo revisa
- **Pedido del autor:** que el README suene humano y profesional para un portafolio, sin las listas largas que sonaban a texto generado, y que un data engineer y un analista de sistemas de negocio (BSA) encuentren rápido lo suyo.
- **Decisión:** `README.md` y `README.en.md` se reescriben en primera persona y dicen lo mismo en los dos idiomas (antes el inglés tenía un tercio del español). Suman «Por qué lo hice», con lo que cuenta el Acta de cierre, incluido que el proyecto se construyó con un asistente de inteligencia artificial bajo reglas escritas y que las decisiones fueron del autor; «Por dónde empezar», con una ruta para ingeniería de datos (el agente, `etl/`, los modelos de dbt y la carga de cada martes) y otra para BSA (el PRD, el Acta de cierre, el plan de calidad, el registro de fallas y el índice de decisiones); y «Lo que encontré en los datos». La lista de páginas del panel pasa a un bloque plegable, el párrafo de calidad se acorta, y el árbol muestra `agent/certs/` y `agent/downloads/`, que faltaban. Las cifras y los enlaces son los de siempre; el inglés enlaza a los documentos de `docs/en/`.
- **Pruebas:** las que leen los README (`tests/test_project.py`, `tests/test_menu_order.py`) y las de documentos, idiomas y panel: 336 en verde.

## D-548 · El Acta de cierre dice que el panel ya está dividido
- **Pedido del autor:** corregir lo que un reclutador vería como contradicción antes de publicar.
- **Decisión:** el Acta de cierre, en español y en inglés, decía en sus puntos menos fuertes que el panel vive en un solo archivo de casi 10.000 líneas, y en «Qué queda» que falta dividirlo; desde D-541 está dividido por responsabilidad. Ahora dice que lo estuvo, que se dividió después del cierre y que sigue siendo grande, con funciones largas, y lo que queda es acortar esas funciones. Pasa a la versión 1.2, con su fila en el historial. Las demás cifras del Acta son las del día del cierre y se quedan como estaban.
- **Pruebas:** las de documentos e idiomas.

## D-549 · El panel arranca en Streamlit Cloud: ningún import del proyecto antes de agregar su carpeta a la ruta
- **Pedido del autor:** el panel público mostraba `ModuleNotFoundError` en `bi/dashboard.py` tras el push de D-544 a D-548.
- **Decisión:** `from bi import static_files`, que D-544 dejó antes de `sys.path.insert`, pasa a la lista de imports del proyecto que viene después. Streamlit Cloud pone en la ruta de Python solo la carpeta `bi/`; en local y en el CI la carpeta del proyecto ya estaba en la ruta, por eso las pruebas pasaban con el panel roto (F-45 en `docs/calidad/plan_mitigacion.json`). `test_d549_the_panel_starts_as_streamlit_cloud_starts_it` arranca el panel en un proceso aparte, solo con `bi/` en la ruta: falla con el código anterior y pasa con la corrección.
- **Nueva dirección:** el autor cambió el subdominio del panel en Streamlit Community Cloud a `greenocean.streamlit.app`; los dos README y el MANUAL, en los dos idiomas (versión 3.19), la usan. Las decisiones y el archivo histórico guardan la anterior, porque cuentan el pasado.
- **Pruebas:** las de `tests/test_dashboard.py`, las de estructura de `tests/test_project.py` y las de recarga del panel.

## D-550 · Cada nombre del stack dice qué es y dónde lo usa el proyecto
- **Pedido del autor:** que las listas «Stack · …» de la barra del menú no sean solo nombres: al pasar el mouse por cada uno, una explicación corta.
- **Decisión:** los 59 nombres de las cinco listas tienen su explicación, en español y en inglés, con la misma forma: qué es, en una frase, y «Aquí:», en negrita, dónde lo usa el proyecto. Cada dato se comprobó en el código (por ejemplo, que `requests` también trae el IPC del INE, que el Excel de «Descargar» lo escribe openpyxl y que un precio cinco veces sobre o bajo la mediana de su semana se marca como atípico). La explicación aparece al pie de la ventana al pasar el mouse o al llegar con el teclado, en un espacio que la ventana reserva, así la lista no se mueve; mientras tanto, ese espacio dice «Pasa el mouse sobre un nombre para ver qué es y dónde se usa». Dev Container sale de la lista de DevOps: lo agregó Streamlit al publicar el panel y el proyecto no lo usa. El título y los números de la ventana toman el color de su texto, para leerse también en los temas claros.
- **Pruebas:** un nombre sin explicación, o una explicación sin su inglés, hace fallar las pruebas que abren el panel y la que recorre cada pantalla en inglés. En verde las del menú, del panel, de los idiomas y de la estructura del código (303).

## D-551 · Una sola tabla de KPI, a un clic desde la barra del menú
- **Pedido del autor:** una sección propia para los KPI en la barra de íconos del menú, con cada KPI en una tabla ordenada: qué es, cómo se calcula, por qué y dónde verlo, con nombres formales y un enlace al lugar exacto.
- **Decisión:** la tabla de KPI de «Análisis › Método» es la única del panel, y ahora la abre también un ícono «KPI» de la barra, en todas las vistas, en una ventana ancha. Sus columnas son las de una ficha de KPI: KPI, Qué pregunta responde, Cómo se calcula, Por qué, Ubicación e Indicador técnico. La ubicación es un enlace que abre la página o la pestaña donde se ve cada KPI, comprobada en el código: cuatro en «Semanal», dos en «Análisis › Precios e inflación», la brecha en «Análisis › Insights» y la calidad de los datos en «Controles de datos». En la vista Usuario, lo que saldría de su vista (Controles de datos y los indicadores K1, K6 y K8) se lee como texto (D-502). La tabla de «Insights» usa la misma palabra, «Ubicación», con enlaces; su propia fila dice «Aquí, a la derecha», en vez de nombrarse a sí misma.
- **Pruebas:** las de la vista Usuario, los idiomas, el menú, «Análisis» y los KPI (393 en verde). La prueba que pedía que solo `show_analysis_block` usara las definiciones mira ahora la función que dibuja la tabla, que es la única que las usa.

## D-552 · «Reglas de transformación»: cada etapa se explica, la lista se separa y cada regla es una tabla
- **Pedido del autor:** que al pasar el mouse por cada ícono del diagrama se entienda qué es esa etapa y qué pasa ahí; que la lista de reglas no sea una sola lista larga, sino separada por etapa; que el detalle de cada regla sea una tabla; que los K1 a K8 digan claramente que son KPI; y nombres formales (R-008 de `AKGRO.md`).
- **Decisión:** cada ícono del diagrama (ODEPA, INE, Ingesta, Staging, Intermedio, Marts, Publicación y Panel web, y en «Cálculos e indicadores» la Base DuckDB, los indicadores en SQL y los cálculos del panel) abre al pasar el mouse, o al llegar con el teclado, una tarjeta con qué es y, tras «Aquí:», qué pasa en el proyecto. «Intermedio» conserva su nombre, el estándar de dbt (*intermediate*), y la tarjeta lo explica. En la lista, cada etapa abre una franja con su nombre y lo que hace en una línea. El detalle de cada regla es una tabla de filas con nombre formal: Etapa, KPI (solo en K1 a K8: su código, su nombre y qué mide), Problema que resuelve, Impacto si no existiera, Ejemplo, Inferencia, Regla del mismo envase (Sí o No, con su porqué) y Respaldo. Los nombres y las descripciones de K1 a K8 tienen ahora su inglés, que les faltaba también en «Análisis › Método». El archivo, que pasó de 300 líneas, se separa en tres regiones de tema.
- **Pruebas:** las de la página, los idiomas, la barra de las páginas, la estructura del código y el panel (334 en verde); la página se revisó dibujada en Chrome, en español y en inglés.

## D-553 · Los KPI se explican con palabras que entiende cualquiera
- **Pedido del autor:** que la tabla de KPI (la ventana «KPI» y «Análisis › Método») se lea sin ser profesional: textos como «La mediana no se mueve por un precio extremo» no decían qué es lo que no se mueve.
- **Decisión:** «Cómo se calcula» y «Por qué» de los ocho KPI se reescriben con palabras simples, y el término técnico va entre paréntesis la primera vez (la mediana, precio comparable, prueba de signo, desviación estándar, cotizaciones, índice, IPC de alimentos del INE, en términos reales, completitud, actualidad, validez, unicidad, consistencia y exactitud). La pregunta de «Precio real» dice «si se quita el efecto de la inflación» en vez de «descontada la inflación». Cada texto dice lo que hace el código: la mediana de los cambios en las regiones con dato las dos semanas, la prueba de signo de dos colas con p < 0,05, la alerta con un cambio de al menos 10 %, a más de 2 desviaciones del cambio promedio de sus 12 semanas previas y con dos cotizaciones en cada semana, el índice con enero 2022 = 100 y la mediana de las series de la familia, y «al ritmo» hasta 2 puntos del IPC. La brecha aclara que no es la ganancia del vendedor, y ningún texto atribuye causas. La regla de la alerta sigue escrita una sola vez desde las constantes de `bi/alerts.py`, ahora en palabras simples, y comparte con las fichas de alza y baja la frase de la distancia (`describe_distance`); los documentos la siguen escribiendo como fórmula, con las mismas cifras. Los textos al pasar el mouse de «Mensual» e «Histórico», que toman sus definiciones de la misma tabla, cambian con ella. Cada texto tiene su inglés, y se borran las traducciones de los textos anteriores.
- **Pruebas:** la de la regla de la alerta compara ahora los documentos con las constantes del código, no con el texto del panel; las de los KPI, «Análisis», la vista Usuario, los idiomas, la estructura del código y el panel (308 en verde). La tabla se revisó dibujada en Chrome, en español y en inglés.

## D-554 · «Histórico» deja «Temporada», y cada gráfico dice qué significa cada color
- **Pedido del autor:** la gráfica «Temporada» de «Análisis › Histórico» no se entendía, y ningún gráfico de «Mensual» ni de «Histórico» decía qué es el rojo, el azul o la línea punteada. El autor eligió quitarla, poner una etiqueta de colores a cada gráfico y, como la tendencia de los años ya está en la pestaña, dejar el espacio libre para que los otros gráficos se vean más grandes.
- **Por qué se quita «Temporada»:** comparaba cada mes con el promedio de su año en precios del día. Como los precios suben a lo largo de cada año, los primeros meses salían bajo su promedio y los últimos sobre él aunque no hubiera temporada: la barra mezclaba la temporada con la inflación de cada año, y su propia explicación lo advertía. Con ella se van la tarjeta «Mes más barato» y su columna en la tabla, que salían del mismo cálculo, y la lectura de K4 en «Análisis». K4 sigue en el pipeline y en sus páginas técnicas, y la temporada medida en pesos reales sigue en «Consultas SQL · Calendario de compra» (D-185): la regla 66 de «Reglas de transformación», «Resume la temporada de cada mes», apunta ahora a esa consulta. Once productos que solo tenían K4 en «Análisis» (Breva, Caqui, Fruto del paraíso, Guayaba, Higo, Locoto, Mora, Níspero, Puerro, Ramas de apio y Tumbo) dejan su selector «Producto»: sin la temporada, su fila no tenía ninguna cifra.
- **Por qué no se agrega otro gráfico:** la tendencia de los años ya está en «Precio desde enero 2022» (mes a mes, frente al IPC) y en «Cambio de cada año» (cuánto subió cada año, frente al IPC). Una recta de regresión sobre 2022–2026 promediaría el salto de 2022 (+24,7 % del IPC de alimentos) con los años de alzas moderadas (entre 3,6 % y 5,2 %) y daría una pendiente que no describe ninguno. «Histórico» dibuja ahora dos gráficos, cada uno de la mitad del ancho, y sus cuatro tarjetas llenan su fila.
- **La etiqueta de colores:** bajo el título de cada gráfico, y en la ventana de su lupa, una línea dice qué es cada color y cada línea, dibujados como en el gráfico: «Toda la canasta» (o la familia elegida) e «IPC de alimentos» en el precio; «Subió», «Bajó» e «IPC de alimentos» en el cambio de cada mes; «Alzas fuertes» y «Bajas fuertes» en las alertas; la familia, con los colores de sus años, y el IPC en el cambio de cada año. Etiqueta y gráfico toman sus nombres y colores de las mismas funciones. Las alertas dicen ahora en su subtítulo «cambios fuera de lo normal (K6)», porque la etiqueta ya nombra las alzas y bajas fuertes, y al pasar el cursor «Alzas fuertes» y «Bajas fuertes» en vez de «Subidas» y «Bajadas». El PRD (español e inglés) pasa a la versión 3.64.
- **Pruebas:** una nueva comprueba que la etiqueta de cada gráfico contenga cada color que el gráfico dibuja; las de «Análisis» cuentan dos gráficos y cuatro tarjetas en «Histórico», y se borra la de «Temporada». La suite completa corrió una vez: 1.567 en verde y 3 fallas de este mismo cambio (la fecha de portada del PRD, en los dos idiomas, y la regla 66), corregidas y vueltas a correr en verde con sus archivos. Las cifras no cambian, así que no hace falta correrla con la base publicada. Revisado en Chrome, en español y en inglés.

## D-555 · La suite corre una vez por push, en tres grupos a la vez, y la calidad reutiliza su cobertura
- **Pedido del autor:** `calidad.yml` quedó en rojo en dos subidas y se canceló por tiempo en la tercera, y el CI se había vuelto el doble de lento. El autor pidió resolverlo de una vez para que no vuelva a pasar, y propuso dividir las pruebas.
- **Diagnóstico:** el rojo venía del detector de secretos. Marcaba como posible clave la explicación de `detect-secrets` en el stack del menú (D-550), y ese candidato no estaba en `.secrets.baseline`, así que el indicador de secretos sin clasificar pasaba su aceptable. La lentitud venía de que la suite completa, 1.561 pruebas, corría tres veces por push: en Python 3.11 y 3.12 en `pruebas.yml`, y otra vez en `calidad.yml` para medir la cobertura. Cada ejecución tardaba unos 28 minutos en los servidores de GitHub, contra 3,5 en el computador del autor, y `calidad.yml` llegó a su tope de 40. Ninguna prueba es gigante: la más lenta tarda 27 segundos en local.
- **Decisión:** el candidato se anota como revisado en `.secrets.baseline`. `pruebas.yml` reparte la suite en tres grupos que corren a la vez en cada versión de Python; `scripts/grupo_pruebas.py` los arma equilibrando el tamaño de los archivos, y un archivo de pruebas nuevo entra solo a un grupo. dbt parse corre una vez por versión. En 3.11, cada grupo guarda su cobertura y sus cuentas. `calidad.yml` espera la ejecución de `pruebas.yml` del mismo commit y, si terminó en verde, combina esa cobertura en vez de correr la suite otra vez (`medir_calidad.py --coverage`); tras una carga semanal usa la última ejecución en verde de main, y sin ninguna corre la suite como antes. La cobertura mínima de 90 % sigue revisándose en el CI, como indicador de `calidad.yml` (`docs/calidad/metas.json`), porque cada grupo por separado no la alcanza. Se descartó pytest-xdist porque agrega una dependencia.
- **Comprobado en local:** los tres grupos juntos corren las mismas 1.554 pruebas y 7 omitidas que la suite completa, y su cobertura combinada da 96,0 %. Las pruebas de los workflows, del mapa de la app, de los idiomas, del método de calidad y de la forma del código pasan; la auditoría de buenas prácticas sigue en cero. Falla F-46. El tiempo en GitHub se verifica después del push.

## D-556 · «Mensual» muestra el precio frente al IPC y las alzas y bajas fuertes; «alerta» queda para «Semanal»
- **Pedido del autor:** el gráfico «Alertas de precio por mes» hablaba de semanas en una pestaña de meses, no mostraba una tendencia y usaba la palabra «alerta», que promete una urgencia que en la historia no existe. El autor pidió dos gráficos para «Mensual»: el precio frente al IPC, y cuántas alzas fuertes y cuántas bajas fuertes hubo, para responder simple: ¿hubo más alzas o más bajas extremas?
- **Decisión:** «Mensual» dibuja dos gráficos más anchos. «Precio mes a mes» queda como está: la línea del precio contra la del IPC de alimentos. «Alzas y bajas fuertes» reemplaza a «Cambio de cada mes» y a «Alertas de precio por mes»: cada mes, sus alzas fuertes hacia arriba y sus bajas fuertes hacia abajo, desde una misma línea, y la etiqueta de colores da el total de cada una. Al ampliarlo dice cuál dominó y el tamaño típico de cada una (la mediana): con los últimos 12 meses, 614 alzas fuertes y 268 bajas fuertes, típicas de +18,7 % y −16,7 %, de tamaño parecido. El tamaño se compara como razón de precios, porque una baja de 16,7 % se deshace con un alza de 20 %; dos tamaños son «parecidos» si el mayor no pasa 1,25 veces al menor. La tarjeta y la columna «Alertas» de «Mensual» e «Histórico» pasan a «Alzas y bajas fuertes». La palabra «alerta» queda en «Semanal», donde invita a actuar esa misma semana.
- **Por qué no se dividen las barras por semana:** el color ya distingue alzas de bajas, y un mes tiene 4 o 5 semanas; un segundo código de colores haría el gráfico ambiguo.
- **Pruebas:** las de «Análisis» cuentan dos gráficos en cada pestaña, comprueban que las bajas cuelgan bajo la línea y recalculan desde las filas de K6 las cantidades y el tamaño típico que dice el texto; las de idiomas, vista Usuario, barra de páginas y KPI pasan. Revisado en Chrome, en español y en inglés.

## D-557 · La cobertura se mide en Python 3.12 con sys.monitoring, y cada grupo nombra sus pruebas más lentas
- **Qué pasó en el primer push de D-555:** los grupos 2 y 3 terminaron en 2 a 4 minutos, pero el grupo 3 falló en las dos versiones y el grupo 1 tardó 29 minutos en Python 3.11, contra 5 en 3.12. En una copia que imita al CI (Python 3.12, base publicada) el grupo 3 falló por una prueba de `tests/test_rendimiento.py` que buscaba las líneas `run: pytest` del workflow y no encontraba la orden dentro del paso de varias líneas. El código no tenía error. El grupo 1 no se pudo reproducir lento en local (90 segundos): la lentitud aparece solo en el CI, con el trazador antiguo de cobertura de 3.11, y los registros del CI no se pueden leer sin una clave.
- **Decisión:** la prueba busca `pytest -q` en cualquier línea. La cobertura se mide en Python 3.12 con `COVERAGE_CORE=sysmon`, que usa `sys.monitoring` y cuesta mucho menos que el trazador antiguo; Python 3.11 corre los mismos grupos sin medir. Cada grupo escribe un informe JUnit y `scripts/pruebas_lentas.py` publica sus cinco pruebas más lentas como avisos de GitHub, que se leen en el resumen de la ejecución sin abrir el registro: si un grupo vuelve a demorar, nombra a la culpable.
- **Pruebas:** la de los workflows, el mapa de la app, DevOps, despliegue, idiomas, el método de calidad y la forma del código pasan; en la copia del CI, el grupo 3 pasa y el grupo 1 con `sysmon` tarda 90 segundos. Falla F-47. El tiempo real en GitHub se verifica después del push.

## D-558 · Las dos pruebas que buscan CSS y JavaScript dentro de Python leen cada archivo una sola vez
- **Qué mostraron los avisos de D-557:** con la cobertura ya fuera de Python 3.11, el grupo 1 de 3.11 seguía en 11 minutos, contra 5 en 3.12. Sus avisos nombraron a las culpables: `test_d543_javascript_and_html_live_in_their_own_files` y `test_d544_no_stylesheet_is_written_inside_python`, con 268 y 269 segundos cada una. El método antiguo de cobertura no era la causa principal.
- **Causa:** por cada una de las 33.675 cadenas de texto de `bi/`, `etl/`, `agent/` y `scripts/`, `ast.get_source_segment` volvía a partir el archivo entero en líneas, un costo cuadrático que en archivos grandes como `bi/i18n_en.py` se nota, y mucho más en Python 3.11.
- **Decisión:** `tests/code_shape.py` suma `string_literals`, que parte cada archivo una sola vez y corta cada cadena por su posición; las dos pruebas la usan y revisan lo mismo que antes. Las 33.675 cadenas que devuelve son idénticas, una por una, a las de `ast.get_source_segment`; las dos pruebas pasan de 36 segundos a menos de 1 en el computador del autor. Se borran tres `import ast` repetidos dentro de funciones de `tests/test_project.py`.

## D-559 · Cada barra de «Alzas y bajas fuertes» dice su número
- **Pedido del autor:** ver, sobre cada barra del gráfico, cuántas alzas fuertes y cuántas bajas fuertes hubo ese mes, no solo los totales de la etiqueta de colores.
- **Decisión:** cada barra lleva su número en su extremo, en el color de su barra: el de las alzas, sobre la roja; el de las bajas, bajo la azul. El eje vertical deja un 18 % del alto libre más allá de la barra más larga de cada lado (`LABEL_ROOM`), para que los números no toquen los nombres de los meses ni el borde superior.
- **Pruebas:** la del gráfico comprueba que tiene sus barras y sus dos capas de números; revisado en Chrome a 1500 y a 1100 px de ancho, sin textos montados.

## D-560 · «Histórico» y «Semanal» terminan dentro de la ventana, con un margen abajo
- **Pedido del autor:** en una ventana de laptop, la última línea de algunas páginas quedaba cortada y obligaba a un scroll innecesario; pidió un margen de uno o dos milímetros abajo.
- **Medición** (Chrome sin ventana, la página principal desplazable de Streamlit): «Análisis › Histórico» se pasaba 44 px en todos los tamaños, porque el recuadro verde del IPC (D-518) le quitaba espacio solo a la tabla y no a los gráficos, que no llegaban a su piso. «Semanal» se pasaba 44 px en ventanas de hasta unos 700 px de alto. «Análisis › Mensual» cabía en todos.
- **Decisión:** en «Histórico», los gráficos ceden al recuadro verde su alto y un margen de 8 px (`INSIGHT_TILE_ROOM = 52`), y en ventanas de hasta 760 px de alto aceptan un piso de 160 px (`LOW_FLOOR`). En «Semanal», en ventanas de hasta 760 px de alto, los paneles dejan sitio para la línea de cobertura y el margen, y la tabla de productos cede el alto y se desplaza dentro de su caja. Ahora «Histórico» cabe en 1280 × 700, 1440 × 900 y 1920 × 1080, y «Semanal» en 1366 × 768, 1440 × 760 y más. En 1280 × 700, «Semanal» todavía se pasa 44 px: el contenido de los pasos 2 y 3 es más alto que la ventana, y caber ahí exige achicar sus tarjetas, un cambio de diseño que queda a decisión del autor.
- **Pruebas:** las de «Análisis», la página de inicio, la barra de páginas y la forma del código pasan.

## D-561 · El botón «Vista: … · Cambiar» queda siempre a la vista
- **Pedido del autor:** en la vista Autor, con una ventana baja, el menú se desplaza y el botón «Vista: … · Cambiar» quedaba tapado bajo el logo.
- **Decisión:** la caja del botón queda fija justo bajo el logo (`position: sticky`, a 72 px, la altura del encabezado del menú), sobre el color del menú, y las filas pasan por debajo al desplazarse. La regla va en la caja que Streamlit pone alrededor del botón: en el botón mismo no tiene efecto, porque esa caja lo encierra.
- **Pruebas:** las del menú y la barra lateral pasan; revisado en Chrome a 1280 × 540 con el menú desplazado 62 px: el botón queda a 72 px del borde, bajo el logo.

## D-562 · «Mapa de la app» pasa a ser un diagrama BPMN en una sola vista (parte 1 de 3: el dibujo)
- **Pedido del autor:** el mapa anterior (D-285, D-441) se veía desordenado: líneas que se cruzaban, filtros y un recorrido animado de 30 pasos. Pidió un BPMN, el estándar para dibujar procesos, con los mismos logos, nombres formales, una sola vista sin scroll y más horizontal que vertical. Aprobó una maqueta y el plan en tres partes: el dibujo, los clics y, al final, las pruebas, los documentos y la limpieza del código anterior.
- **Decisión:** `bi/app_bpmn.py` dibuja una sola hoja gris intermedia, igual en todos los temas. Arriba, ODEPA, INE, GitHub, PyPI y Streamlit Community Cloud como pools contraídos (participantes externos, cajas negras). Al centro, el pool «Carga semanal» con cuatro carriles (Ingesta, Transformación, Control de calidad y Publicación): un evento de inicio con temporizador (martes 12:07 UTC), los subprocesos contraídos con su logo, los almacenes `raw.db`, bronce y `datos.duckdb`, la compuerta exclusiva de la puerta de publicación, su fin de error («nada se publica») con una anotación y el fin «panel actualizado». Abajo, el pool «Integración continua», que empieza con un mensaje (un push), los perfiles Usuario, Profesional y Autor, y un grupo BPMN «vigilancia y soporte» con las once piezas que no son parte del flujo de datos. Una leyenda nombra cada símbolo. Se quitan los filtros y el recorrido animado.
- **Una vista:** Streamlit limpia un SVG dibujado en la página, así que la hoja va en su propio marco (iframe), como los diagramas de «Modelo de datos»; una marca le da el alto que deja la ventana (`calc(100vh - 235px)`) y la hoja se escala a ese alto.
- **Pruebas:** las de la página, el menú, la barra de páginas, los enlaces, la vista Usuario, la forma del código y la de idioma por pantalla pasan. Revisado en Chrome a 1280 × 700, 1440 × 900 y 1920 × 1080, en español y en inglés: la página no tiene scroll y ningún texto se monta sobre otro.

## D-563 · El mapa BPMN queda estático y se borra el mapa anterior
- **Decisión del autor:** el BPMN muestra el proceso; la arquitectura y el linaje ya tienen sus propios diagramas («Stack y evidencia», «Pipeline y linaje» y el SAD). Por eso no se hacen las partes 2 y 3 previstas en D-562 (clics, conexiones azules y columna lateral): el mapa queda como está, en una sola vista, y se cierra el proyecto.
- **Limpieza:** nada llamaba ya al mapa anterior, así que se borran `bi/app_map.py`, `bi/app_map_detail.py`, `bi/static/app_map.js`, `bi/static/app_map.css`, sus pruebas y las 118 traducciones al inglés que solo él usaba; también `orthogonal` de `bi/security_plan.py`, que nada usaba y la auditoría no veía porque la palabra aparecía en el mapa anterior. Los logos y los nombres que el BPMN tomaba de él pasan a `bi/app_bpmn.py`; la hoja dibujada es idéntica, carácter por carácter. La descripción de la página dice ahora lo que muestra («Todo el sistema en un diagrama BPMN: la carga semanal, la integración continua y quién participa») , el Índice de decisiones pasa a la versión 2.6 y el Glosario suma BPMN (versión 2.18). Como no habrá clics, la leyenda deja de prometerlos: el «+» de un subproceso dice que agrupa varios pasos y la línea punteada es la asociación con su almacén.
- **Pruebas:** las de la página, el menú, la forma del código y las de idioma pasan; la prueba que exigía que el mapa nombrara las páginas del menú se va con él.

## D-564 · La prueba del aviso de calidad sin pendientes fija el día de su informe
- **Qué pasó:** `pruebas.yml` y `calidad.yml` quedaron en rojo en el commit de D-563, en el grupo 2 de las dos versiones de Python. No fue por la limpieza: la carga corrió pasada la medianoche UTC, el 9 de noviembre, y desde ese día el informe C-7 (31-10) tiene más de 8 días. El aviso de calidad sumó entonces «puede no reflejar el estado actual» (D-361), y `test_d419` esperaba un aviso vacío.
- **Decisión:** la prueba llama al aviso con el día de su propio informe, como ya hacía `test_d335` desde F-43; la regla de D-361 no cambia. Se revisaron las demás llamadas al aviso en las pruebas: solo buscan textos que están, así que no dependen del día.
- **Pruebas:** el grupo 2 pasa en una copia aparte con la base publicada y la hora UTC, como en el CI; la falla queda como segunda ocurrencia de F-43.

## D-565 · «Mensual» e «Histórico» dicen primero la conclusión: cuatro tarjetas de hallazgos y una tabla corta
- **Pedido del autor:** las dos pestañas mostraban muchas cifras con el mismo peso (cinco y cuatro tarjetas, una tabla de cinco y cuatro columnas y, en «Histórico», un recuadro aparte) y dejaban la conclusión al lector. Pidió simplificarlas sin maqueta: menos elementos, más fáciles de leer.
- **Decisión:** cada pestaña tiene cuatro tarjetas y cada una dice un hallazgo calculado, nunca escrito a mano: el cambio de precios junto a su distancia del IPC; lo que más se encareció frente al IPC (la familia, o el producto bajo una familia); dónde está el riesgo (la parte de las alzas fuertes que suman las dos familias o productos con más, contadas sin ponderar); y en «Mensual» los dos meses que más subieron, en «Histórico» el mayor salto anual del IPC de alimentos (D-518, que deja de ser un recuadro aparte y dice su frase al pasar el cursor). La tabla queda con tres columnas (cambio, frente al IPC, alzas y bajas fuertes) y ordenada de lo que más subió frente al IPC a lo que menos, con la canasta o la familia elegida arriba. Salen la brecha consumidor–mayorista (K1 sigue en «Insights»), la mayor alza mensual y el año de mayor alza, que ya se leen en los gráficos. El recuadro verde de arriba pasa a una línea en todas las pestañas: el porqué de sus meses queda al pasar el cursor por su «i», y los gráficos ganan esos 18 px.
- **Limpieza:** «Mensual» e «Histórico» ya no leen K1, así que su consulta, sus columnas y `wholesale_families` salen de este flujo; se comprobó que K1 no aportaba productos que las series y las alertas no tuvieran, así que la lista de productos no cambia.
- **Captura de los documentos:** la de «Análisis» (M-3) era del 31 de octubre, con tres gráficos y «Alertas de precio»; se tomó de nuevo, en Dark Grey, en español y en inglés.
- **Pruebas:** las de «Análisis» recalculan cada tarjeta y el orden de la tabla. En Chrome, las dos pestañas caben sin scroll a 1280 × 700, 1440 × 900 y 1920 × 1080, en español y en inglés, con un margen abajo.

## D-566 · «Plan de calidad» en una sola vista, sin el recuadro vacío del código
- **Pedido del autor:** revisar la página, que los nombres correspondan, simplificar y quitar lo vacío u obsoleto, en una sola vista si hace falta.
- **Lo que se encontró:** los informes semanales miden solo los indicadores de datos (el código se revisa en el CI de cada push, D-431), así que el recuadro «Código que los trata» se dibujaba vacío. Dos indicadores tienen el nombre del cumplimiento y mostraban la falla sin decirlo: «Pruebas de datos dbt superadas · 0 %» se leía como «ninguna pasó». «Resumen» se pasaba de la ventana y la lista de «Informes» tenía cuatro filtros para tres informes.
- **Decisión:** el recuadro del código se dibuja solo cuando el informe tiene indicadores de código (los C-1 a C-7), y los datos toman el ancho completo. Las filas llevan encima los nombres de sus columnas, los mismos del visor de informes: «Indicador · Falla · Aceptable · Estado»; así cada nombre oficial se lee con su falla, sin renombrar nada. A la vista queda la respuesta («El 2026-11-04: 5 de 5 medidos dentro de lo aceptable · 0 no conformidades»); qué mide el informe y cómo leer las barras pasan al «i» del título del recuadro, y la autoevaluación del encabezado, al pasar el cursor. Cada una de las últimas fallas ocupa una línea, con su texto completo al pasar el cursor; en ventanas bajas se ven las dos últimas, o la última. «Ver registro completo» y «Abrir el último informe» van en una fila. En «Informes», los filtros aparecen solo con más de 10 informes en la serie.
- **Pruebas:** las del plan de calidad, idioma, barra de páginas, documentos y vista Usuario pasan. En Chrome, «Resumen» cabe sin scroll a 1280 × 700, 1366 × 768 y 1440 × 900, en español y en inglés. `test_t54_every_public_link_answers` falla en local por la caída de GitHub de hoy (sus enlaces responden 504), igual que en el CI del commit anterior; no depende de este cambio.

## D-567 · Una caída de GitHub o de PyPI ya no pone en rojo el CI
- **Qué pasó:** el 9 de noviembre, `pruebas.yml` quedó en rojo en dos subidas seguidas (fb7c2cb y c2eca2e) sin que fallara el código. La página de estado de GitHub informó que respondía 504 al tráfico sin sesión, incluidas las descargas de releases. El CI descargaba la Base DuckDB del release «base-actual» sin sesión y sin reintentos, pip no reintentaba, y `test_t54_every_public_link_answers` tomaba ese 504 como un enlace roto.
- **Decisión:** `bi/served_database.py` pide la base con el token del propio workflow (`GH_TOKEN`, a través de la API de GitHub) cuando lo tiene, y sin él, como hasta ahora, en su dirección pública (el panel y una copia nueva del repositorio no cambian). Cada descarga se intenta hasta cinco veces ante un tiempo agotado, un corte de conexión o un error del lado del servidor, con esperas de 5, 10, 20 y 40 segundos; un 404 o un archivo que no coincide con `etl/datos.version` fallan de inmediato. Los tres workflows piden a pip diez reintentos (`PIP_RETRIES`) y guardan los paquetes en la caché de Actions; `pruebas.yml` declara que su token solo lee. La prueba de enlaces salta un 5xx, que es una caída del sitio, y sigue fallando con un 4xx, que es un enlace roto.
- **Lo que no se puede evitar:** una caída de más de un minuto y cuarto sigue fallando, después de sus intentos; en ese caso se vuelve a correr el CI cuando el servicio vuelve.
- **Pruebas:** `tests/test_served_database.py` comprueba los reintentos (504 y 502 se esperan, 404 no), que una caída larga falla tras sus intentos y que en el CI la base se pide con el token; la dirección de la API se probó contra GitHub y nombra `datos.duckdb`. Registrado como F-48.

## D-568 · El CI nombra la prueba que falla y repite una instalación caída
- **Qué pasó:** con D-567, la descarga de la base pasó en los seis grupos, pero un grupo no pudo instalar sus paquetes ni con los diez reintentos de pip, y el grupo 2 falló en las dos versiones sin que se pudiera saber en qué prueba: el registro de un job solo se lee con sesión de administrador. La prueba de enlaces tardaba 11 s en el CI, como si GitHub respondiera «429» («demasiadas solicitudes») a sus servidores, un caso que D-567 no saltaba.
- **Decisión:** `scripts/pruebas_lentas.py` escribe, además de las cinco pruebas más lentas, cada prueba que falla con la primera línea de su error, como una nota en rojo que se lee sin abrir el registro. La instalación de paquetes se intenta entera hasta tres veces, con 30 y 60 s de espera, en `pruebas.yml` y `calidad.yml`; la carga semanal no lo necesita, porque se reintenta sola cada 15 minutos (D-485) y pip ya reintenta (D-567). La prueba de enlaces salta también un «429».
- **Las notas en rojo encontraron la causa real del grupo 2:** no era GitHub, sino dos errores de D-567. Su anotación en `plan_mitigacion.json` usaba la categoría «CI», que no existe (pasa a «operación»), y la repetición de la instalación en `semanal.yml` cambió el nombre que GitHub da al paso, que el «Flujo del sistema en vivo» lee (ese paso vuelve a ser como era).
- **Medición de calidad:** con las pruebas en verde, `calidad.yml` marcó un candidato a secreto sin clasificar: detect-secrets leía la nueva línea `GH_TOKEN: ${{ github.token }}` de `calidad.yml` como un valor nuevo. No es un secreto, sino la referencia al token del propio workflow: entra a `.secrets.baseline` como revisado (solo su huella), y los comentarios salen de las líneas del token. Medido con las mismas versiones de detect-secrets y Bandit que el CI: 0 sin clasificar y 0 hallazgos altos.
- **Pruebas:** el script se probó con un informe JUnit de ejemplo (una falla y un error, cada uno con su mensaje); la suite completa pasa en una copia aparte con la base publicada y la hora UTC, como en el CI.

## D-569 · Si pytest se cae entero en el CI, se sabe dónde y el grupo corre otra vez
- **Qué pasó:** en 1e14e3e, el grupo 2 de `pruebas.yml` terminó con código 139 en las dos versiones de Python: el proceso de pytest se cayó (un «segmentation fault», propio de una biblioteca nativa) antes de escribir su informe, así que las notas de D-568 no pudieron decir en qué prueba. El reparto por tamaño de `scripts/grupo_pruebas.py` había movido siete archivos a ese grupo. La misma combinación pasa en local, con la base publicada y la hora UTC: la caída es de los servidores Linux de GitHub.
- **Decisión:** el paso de las pruebas guarda la salida de pytest. Si el proceso termina con 128 o más (una señal, no una prueba que falla), `scripts/pruebas_lentas.py --caida` escribe en una nota roja el error que Python dejó al caer y las pruebas de su rastro, y el grupo corre una vez más. Si la segunda pasa, el push queda en verde con la nota a la vista; si se cae otra vez, falla ya diciendo dónde.
- **Pruebas:** la lógica del paso se probó con un pytest falso que se cae la primera vez (nota con la prueba y la línea, segunda corrida en verde) y la lectura del rastro, con una salida de ejemplo. Registrado como F-49.

## D-570 · Antes de cada push, lo mismo que el CI; y el CI de cada push, más liviano
- **Pedido del autor:** de los últimos siete pushes, seis terminaron en rojo: dos por una caída de GitHub, una por una prueba que leía el reloj, una por una caída de pytest en Linux y dos porque se subieron cambios revisados solo en parte. Pidió que no vuelva a pasar.
- **Decisión:** `scripts/antes_de_subir.py` corre, sobre el commit que se va a subir, lo que corre el CI: Ruff (reglas y formato), mypy, el escáner de secretos y Bandit en las versiones que instala `calidad.yml` (que lee de ahí, para que nunca difieran), y todas las pruebas en una copia aparte del repositorio con la base publicada y la hora UTC (D-527). Las herramientas de escaneo viven fuera del proyecto, en `~/.cache/greenocean-herramientas`, y la base publicada queda guardada ahí para el próximo push. Con `--instalar` queda como hook `pre-push`: cada `git push` lo corre y no sube si algo está en rojo; `git push --no-verify` lo salta. En el CI, las pruebas de cada push corren solo en Python 3.12, la mitad de las máquinas; 3.11 se sigue probando cada martes, en la carga semanal, que corre en esa versión.
- **Lo que no cubre:** la cobertura mínima del 90 % se mide solo en `calidad.yml` (medirla aquí sumaría varios minutos), y una caída de GitHub o de PyPI sigue siendo externa (D-567).
- **Pruebas:** el script se corrió completo sobre su propio commit, en verde; los textos que decían «3.11 y 3.12» (el diagrama de despliegue, el SAD en sus dos idiomas y CONTRIBUTING.md) dicen ahora lo que corre en cada push.

## D-571 · «Plan de calidad» es solo el archivo de informes: cada cosa de la calidad vive en un lugar
- **Pedido del autor:** los cinco indicadores del último informe se veían dos veces: en «Plan de calidad › Resumen» y en cada informe abierto desde «Informes». («Controles de datos» mide en vivo otros 11, los de la carga; solo dos se parecen: filas rechazadas y pruebas de dbt.) Las tres últimas fallas de «Resumen» también estaban en «Cambios e incidentes». Además, el visor de informes redondeaba a un decimal: escribía 0,0 % donde el resto de la app dice 0,01 % y 0,03 %, y 0,2 % donde dice 0,25 %. Pidió que cada cosa viva en un solo lugar.
- **Decisión:** «Controles de datos» es el estado de hoy y no cambia. «Plan de calidad» es solo el archivo de los informes numerados, sin pestañas. Arriba, una línea con el último («Informe semanal de calidad N° 3 · 2026-11-04 · 5 de 5 dentro de lo aceptable · 0 no conformidades»), con la autoevaluación al pasar el cursor. Debajo, el selector de serie y la lista de informes, como hasta ahora; cada informe se abre como presentación, con su PDF. Salen de la página la tabla de indicadores, «Últimas fallas» y sus dos botones («Ver registro completo» y «Abrir el último informe»): las fallas viven en «Cambios e incidentes». El visor escribe cada cifra como el resto de la app y muestra bajo sus resultados la línea «Cómo leerlo», que antes estaba en la «i» de «Resumen».
- **Documentos:** el SQAP, en sus dos idiomas, decía que la página muestra qué mide cada indicador, por qué importa, cómo se mide y qué hacer si falla, que viven en `docs/calidad/metas.json`. Ahora dice que cada informe muestra los indicadores que midió contra su aceptable y que la página es el archivo de los informes, cada uno abierto como presentación, con su PDF (versión 1.14). Ningún otro documento, ni los README, describía las pestañas de la página, su tabla de indicadores ni sus últimas fallas.
- **Revisión independiente:** un revisor que no hizo el cambio lo leyó entero. Además de lo anterior, se corrigieron: la columna «Variación» de la comparación, que también se escribe ahora con la regla de la app; la prueba de la página, que habría fallado sola al pasar de 20 informes, porque la lista muestra 20 por página; y los colores de estados que ya nada dibuja. Queda una diferencia que no es de este cambio: «Controles de datos» escribe las filas rechazadas con tres decimales (0,008 %), y el visor y el aviso del Autor, con la regla de la app (0,01 %).
- **Pruebas:** la de la página comprueba que ya no tiene pestañas, tabla de indicadores ni bloque de fallas. Una nueva, `tests/test_quality_viewer.py`, comprueba que el visor escribe cada cifra como la app, que muestra la línea «Cómo leerlo» una vez en cada idioma y que una barra nunca pasa su raya mientras cumple su aceptable.

## D-572 · Las filas rechazadas se escriben con la misma regla en toda la app
- **Pedido del autor:** la misma cifra se leía 0,008 % en «Controles de datos» y 0,01 % en el informe de calidad: 201 filas rechazadas de 2.541.374 leídas son 0,0079 %, redondeado con tres decimales en un lugar y con dos en el otro.
- **Decisión:** «Controles de datos» (la fila de validez y la tarjeta de lo que no se cargó) escribe la parte rechazada con la regla de la app (`quality_metrics.percent_decimals`: dos decimales bajo 1 %), la misma del informe, del visor y del aviso del Autor. La cifra no cambia; solo su redondeo, que ahora es uno solo.
- **Pruebas:** la de la tarjeta de lo que no se cargó espera 0,01 % y no 0,008 %.

## D-573 · Un teléfono girado dibuja el panel con el ancho de un computador
- **Pedido del autor:** en el teléfono, aun girado, el panel se veía mal: el menú ocupaba un cuarto de la pantalla, los pasos de «Semanal» quedaban apilados y el mapa de Chile, enorme.
- **Causa:** D-166 dibujaba la página más ancha y la achicaba al 62 %, pero las reglas de diseño del panel (sus `@media` por ancho) seguían viendo el ancho real del teléfono, 844 px, y armaban la versión angosta.
- **Decisión:** en un teléfono girado (su lado corto mide 500 px o menos), `bi/static/phone_viewport.js` pide al navegador que dibuje la página con 1.360 px de ancho, como un computador, a través de la etiqueta `viewport`; todas las reglas ven ese ancho y arman la página de escritorio, que el teléfono muestra entera. Derecho, el teléfono conserva su ancho y sigue pidiendo girarlo. Se quita el achicado de D-166, y los scripts del menú reconocen el teléfono girado con la misma función. Las tabletas y los computadores no cambian.
- **En Streamlit Community Cloud:** el panel corre dentro de un marco (un iframe) de una página de Streamlit, y el teléfono obedece la etiqueta `viewport` de esa página de afuera, no la del marco: el primer arreglo funcionaba en local pero no en la app pública. Como el marco y la página son del mismo sitio, el script ajusta también la etiqueta de afuera; cada una guarda su valor original para cuando el teléfono vuelve a estar derecho. Se comprobó en la app pública con un iPhone emulado: con la página de afuera en 1.360 px, el marco mide 1.360 px y «Semanal» se ve entero.
- **Como un videojuego:** el autor pidió que el teléfono girado muestre cada página entera, como el computador, sin deslizar. El ancho ya no es fijo: la página se arma con el alto en que caben todas las páginas (768 px) y el ancho que pide la forma del teléfono, nunca menos de 1.440 px; el teléfono la muestra entera, achicada de forma pareja, y se puede ampliar con dos dedos. En el teléfono girado, los dashboards pliegan el menú como en el computador, y el diagrama del pipeline, que crece con el ancho, no pasa del alto disponible (solo ahí: en el computador conserva su tamaño aprobado). Medido en un iPhone 14, un iPhone 14 Pro Max, un iPhone SE y un Android emulados: «Semanal», «Análisis», «Pipeline y linaje», «Plan de calidad» y «Mapa de la app» caben enteras en los cuatro.
- **La flecha del menú:** en el teléfono girado, la página se achica a la mitad para caber entera, y la flecha verde que abre el menú plegado quedaba tan chica que no se notaba. Ahí se dibuja al doble de su tamaño y la página le deja sitio; en el computador no cambia.
- **El zoom del pipeline:** el tope de alto del diagrama le impedía crecer cuando el lector lo ampliaba con su propio zoom: el recuadro crecía y el dibujo quedaba chico, corrido a un lado y cortado (lo vio el autor en su teléfono). El tope se aplica ahora solo sin ampliar.
- **Pruebas:** en un iPhone emulado en Chrome, abierto girado, abierto derecho y girado después de abrirlo: girado, la página mide 1.360 px, «Semanal» muestra sus tres pasos lado a lado y el menú queda abierto; derecho, aparece «Gira tu teléfono». La prueba del diseño de teléfono revisa el script y que el achicado ya no está.

## D-574 · «Gira tu teléfono» lo dice también en inglés, chico
- **Pedido del autor:** el aviso que pide girar el teléfono salía solo en español con el enlace normal, y desde esa pantalla no se puede cambiar el idioma: alguien que no lee español no entiende qué hacer.
- **Decisión:** en la versión en español, bajo el texto del aviso, una línea chica y más tenue en inglés: «Turn your phone: the panel reads in landscape.». La versión en inglés no la repite (ya está entera en inglés, D-443), así que la línea queda oculta.
- **Pruebas:** la del diseño de teléfono comprueba la línea en español y que en inglés queda oculta; revisado en un iPhone emulado, derecho.

## D-575 · El README principal pasa a inglés
- **Pedido del autor:** va a postular también a empresas de fuera de Chile, y GitHub muestra primero `README.md`, que estaba en español.
- **Decisión:** `README.md` es ahora la versión en inglés y `README.es.md`, la versión en español; la primera línea de cada uno enlaza al otro. El contenido no cambia. El código y sus comentarios ya estaban en inglés; los documentos de `docs/` siguen en español con su copia en `docs/en/`, y los commits y las decisiones, en español (reescribir el historial no se justifica).
- **Pruebas:** la regla de idioma de los README (cada uno enlaza al otro y el inglés no mezcla español) y la lista de páginas del menú, que se lee del README en español.

## D-576 · La vista Profesional ve las páginas del Autor, con candado
- **Pedido del autor:** un profesional no sabía que existe la consola de operación, que es la parte que muestra DevOps (lanzar la carga, seguir las ejecuciones, administrar los tokens). Pidió que se vea que existe, bloqueada.
- **Decisión:** en la vista Profesional, el menú muestra la sección «DevOps y seguridad» con sus tres páginas («Centro de operación», «GitHub Actions» y «Configuración»), cada una con un candado con persona (`lock_person`; el candado solo ya es «Arquitectura de seguridad»). La sección va al final, antes de las carpetas, para que cada rol empiece por lo que puede abrir. Abierta, una página dice que no hay acceso, qué contiene y cómo se entra («Vista: … · Cambiar» › «Acceso del autor»), sin nada propio: ni cifras, ni botones, ni enlaces al repositorio. El control de acceso no cambia: el servidor revisa la sesión antes de dibujar cada página y antes de cada acción (D-420). La vista Usuario sigue sin ver la sección (D-502).
- **Pruebas:** las de acceso comprueban que la vista Profesional ve las tres páginas con su candado y que, abiertas, no muestran nada propio ni piden nada a GitHub; que la vista Usuario no las ve; y que una visita nueva nunca abre la parte del Autor. El MANUAL, en sus dos idiomas, lo dice (versión 3.20).

## D-577 · Un reloj externo lanza la carga cada martes
- **Pedido del autor:** el martes 10 de noviembre, a media mañana, la carga semanal no había partido sola. La carga debe ser automática y no puede depender de algo que falla casi siempre.
- **Diagnóstico:** de las 26 ejecuciones de `semanal.yml`, solo 5 partieron solas, y las tareas programadas de GitHub llegaron cada martes entre 4 y 6 horas tarde (13 de octubre a las 15:33 de Chile, 20 de octubre a las 12:53, 27 de octubre a las 13:54, en vez de las 09:00). GitHub advierte que su tarea programada se atrasa o se salta cuando sus servidores están cargados. ODEPA ya había publicado: sus dos archivos de 2026 cambiaron el viernes 6 de noviembre.
- **Decisión:** cron-job.org, un reloj web gratuito, lanza la carga cada martes a las 10:00 de Chile (zona America/Santiago). Llama a la API de GitHub por la misma puerta que el botón «Run workflow» (`workflow_dispatch`), con el token `greenocean-cron`, que vale solo para este repositorio y solo tiene el permiso «Actions: Read and write»: puede lanzar y cancelar cargas, pero no tocar el código, los datos publicados ni los secretos. El código, la app y los diagramas no cambian: siguen dibujando el lanzamiento a pedido. La tarea programada de GitHub queda de respaldo; si llega tarde, su guardia ve la carga en verde y no hace nada (D-485). Una carga lanzada así aparece como «Manual», porque GitHub no distingue quién la pidió.
- **Mantenimiento:** el token vence cada año. GitHub avisa por correo una semana antes, y cron-job.org avisa por correo si un martes su llamado falla. El MANUAL lo dice en sus dos idiomas (versión 3.21).
- **Descartado:** que la app lance la carga cuando alguien la visita (depende de las visitas, y Streamlit apaga la app sin ellas), una tarea programada en el computador del autor (depende de que esté encendido), Cloudflare Workers (exige escribir y mantener un script) y los relojes de Google Cloud y AWS (piden tarjeta de crédito).
- **Pruebas:** no cambia código. La prueba es la ejecución de prueba de cron-job.org, que debe responder 204 y dejar una carga en verde en Actions.
