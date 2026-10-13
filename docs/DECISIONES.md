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
- **Por qué:** la autora pidió un panel de aspecto profesional, de tipo SaaS, fondo oscuro con un modo claro beige y gráficos simples de leer. Una primera versión en forma de informe de arriba abajo se descartó por parecer un reporte. Altair viene instalado con Streamlit: no se agrega ninguna dependencia. Las cifras de la página principal son resultados de las consultas existentes, no hallazgos publicados (D-018, hito 6).
- **Descartado:** la charte de una empresa (riesgo con D-015); Matplotlib, que dibuja imágenes fijas sin información al pasar el cursor; una librería de componentes externa.
- **Se pierde:** el código del panel es más largo (estilos y tarjetas). El cambio de modo está en el menú del panel, no en un botón propio.

## D-038 · Centro de control del pipeline dentro del panel (T-39)

- **Decisión:** una página «Centro de control» muestra el estado del job semanal (última ejecución, próxima ejecución automática, historial con éxito o falla) leyendo la API pública de GitHub, y un botón «Ejecutar ahora» que lanza el mismo workflow `semanal.yml` y muestra sus pasos en directo. El botón exige una clave de GitHub limitada a este repositorio y un código de acceso, ambos guardados por la autora en los secretos de Streamlit, nunca en el código. Sin esos secretos, el botón se reemplaza por un enlace a GitHub.
- **Por qué:** la autora necesita ver y controlar la automatización desde un solo lugar, como en una consola de orquestación, sin entrar a GitHub. Lanzar el mismo workflow mantiene un solo workflow y una sola fuente de verdad. El código de acceso evita que cualquier visitante del panel público lance el pipeline.
- **Descartado:** ejecutar el agente y el ETL dentro del servidor de Streamlit (los datos no quedarían guardados en el repositorio y habría dos versiones de la base); un botón sin protección.
- **Se pierde:** el botón depende de que GitHub responda y de una clave que vence y hay que renovar. Los datos nuevos aparecen en el panel cuando Streamlit recibe la base guardada, normalmente uno o dos minutos después.

## D-039 · Página «Pipeline»: el recorrido de los datos en vivo (T-40)

- **Decisión:** el panel muestra el pipeline como un recorrido por capas (fuentes, ingesta, bronce, limpieza, reglas, calidad, oro y consumo), con la orquestación arriba, la cuarentena de filas rechazadas y la observabilidad abajo. Cada paso tiene un punto con su estado real (última ejecución del job semanal y base actual) y sus cifras del momento; por las flechas viajan puntos animados. Se dibuja como imagen SVG (`bi/architecture.py`).
- **Por qué:** la autora necesita entender y mostrar la arquitectura sin abrir GitHub, en el mismo estilo del panel. Solo aparecen las piezas que el proyecto usa de verdad, para poder defenderlas en una entrevista.
- **Descartado:** dibujar tecnologías que el proyecto no usa (Kafka, S3, Spark); un diagrama fijo sin estados; `st.html`, que elimina los dibujos SVG.
- **Se pierde:** la capa «plata» no se guarda como tabla; aparece como etiqueta en una flecha. Los textos del diagrama no cambian de tamaño con la pantalla.

## D-040 · Explicaciones al pasar el mouse y página «El proyecto» (T-41)

- **Decisión:** cada tarjeta tiene un ⓘ que, al pasar el mouse, explica en palabras simples cómo leer el gráfico; cada barra y cada flecha ▲▼ dice qué significa su número («46 % más caro que el promedio nacional», «Bajó 0,4 % frente a la semana anterior»). Una página «El proyecto» presenta el problema, para quién es, las seis preguntas de negocio con dónde se responde cada una y su estado, por qué se eligió el tema, los datos y los límites.
- **Por qué:** la autora y cualquier visitante deben poder interpretar cada número sin preguntar. Un reclutador busca primero qué problema resuelve el proyecto. Los textos salen de `DISENO.md` y de este registro, sin agregar afirmaciones nuevas.
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
- **Por qué:** quien llega al panel debe poder ir al código, a los informes y a las fuentes sin buscar el repositorio; la autora necesita sus accesos de administración en un solo lugar y saber a tiempo cuándo vence el token (si vence, «Ejecutar ahora» deja de funcionar sin aviso). Una dirección larga escrita como texto no se lee ni se toca bien en un celular.
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
