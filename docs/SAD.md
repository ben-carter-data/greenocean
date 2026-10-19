# GreenOcean · Documento de arquitectura de software (SAD)

Cómo está construido GreenOcean hoy: del archivo oficial al panel, capa por capa, con el modelo C4 como mapa.

| Ficha del documento | |
|---|---|
| Sistema | GreenOcean, pipeline semanal de precios de alimentos y panel de BI |
| Versión | Arquitectura entregada al 19-10-2026 (decisiones hasta D-158) |
| Autoría | El autor |
| Método | Vistas C4 (contexto, contenedores, componentes) y secciones de arc42, con sus vistas de ejecución y de despliegue |
| Documentos hermanos | PRD (qué y para quién) y ADR (por qué así) |

---

## 1. Introducción y objetivos de calidad

GreenOcean es un pipeline de datos semanal con un panel de BI. Toma dos fuentes abiertas de ODEPA y el IPC del INE, las hace comparables y publica tres respuestas: qué se movió esta semana, si el precio de hoy es normal para la temporada —en pesos nominales o reales— y cuánto paga el consumidor sobre el mayorista.

La arquitectura sigue el patrón de un data warehouse moderno a escala de portafolio: zona de aterrizaje, capa bronce en Parquet, transformaciones declarativas en dbt Core con pruebas de datos, motor analítico en columnas (DuckDB) y una base de servicio compacta, de solo lectura, que alimenta el panel.

| Prioridad | Objetivo de calidad | Qué significa aquí |
|---|---|---|
| 1 | Corrección y trazabilidad | Ninguna fila desaparece sin motivo; cada cifra se reconstruye desde la fuente |
| 2 | Integridad ante fallas | Una carga que falla nunca reemplaza la última base válida |
| 3 | Operación sin supervisión | El pipeline corre solo cada semana y avisa cuando algo sale mal |
| 4 | Costo cero, sin vencimientos | Solo herramientas abiertas o gratuitas que no expiran ni se pausan |
| 5 | Portabilidad | Cambiar de motor es un cambio de configuración, no de código |
| 6 | Lectura inmediata | Cada vista del panel responde su pregunta en una pantalla |

## 2. Restricciones

| Restricción | Origen |
|---|---|
| Solo fuentes oficiales descargables; sin scraping | ADR-01 |
| Sin costo de infraestructura ni servicios con período de prueba | ADR-02, ADR-30 |
| Repositorio público con licencia MIT | ADR-03 |
| GitHub rechaza archivos de más de 100 MB; los datos crudos no se suben | ADR-04 |
| Python 3.11 en GitHub Actions; dbt Core y dbt-duckdb solo en el workflow, no en el panel publicado | D-154 |
| Código en inglés; documentos y panel en español; valores de ODEPA sin traducir | D-021, D-023 |
| Nada de nube, contenedores ni modelos predictivos agregados para aparentar | D-019, ADR-31 |

## 3. Nivel 1 · Contexto del sistema

El sistema tiene dos proveedores de datos oficiales, una plataforma de código y orquestación, una de publicación y un solo tipo de consumidor: quien lee.

| Actor o sistema externo | Rol | Relación con GreenOcean |
|---|---|---|
| ODEPA, portal de datos abiertos | Proveedor | Publica un archivo por año y fuente (mayorista diario y consumidor semanal); se descarga por HTTPS |
| INE, IPC | Proveedor | Publica la serie del IPC base 2023 y la serie empalmada de divisiones; se descargan por HTTPS |
| GitHub | Plataforma | Guarda el código y la base publicada, ejecuta los workflows, publica el informe semanal y avisa por correo |
| Streamlit Community Cloud | Plataforma | Publica el panel desde la rama principal |
| Visitantes del panel | Usuario | Leen el Dashboard, la arquitectura y la documentación; no escriben nada |
| El autor | Operador | Mantiene el código, administra los secretos y puede lanzar una ejecución manual |

[[diagrama:contexto]]

GreenOcean es una sola caja: su interior es la vista de contenedores de la sección 4. Cada flecha dice qué pasa entre el sistema y su vecino.

## 4. Nivel 2 · Contenedores

Cada contenedor es una unidad que se ejecuta o se guarda por separado.

| Contenedor | Ubicación | Responsabilidad | Tecnología |
|---|---|---|---|
| Agente de ingesta | `agent/agent.py` | Descarga los archivos de ODEPA, valida tamaño y encabezado, calcula su huella y registra cada resultado | Python, requests |
| Zona de aterrizaje | `etl/raw.db` | Recibe las filas de los archivos tal como llegan; se reconstruye en cada ejecución y no se sube | SQLite |
| Capa bronce | `etl/bronze/` | Copia literal en Parquet, una partición por fuente y año, más las dos series del INE; no se sube | Parquet (pyarrow) |
| Ingesta del IPC | `etl/ine.py` | Descarga las dos series del INE y guarda la división de alimentos en bronce, como texto | Python, requests |
| Proyecto de transformación | `dbt/` | Staging, intermedio y marts, con 31 pruebas de datos | dbt Core, dbt-duckdb |
| Almacén de trabajo | `etl/warehouse_build.duckdb` | Donde dbt construye y prueba cada modelo; no se sube | DuckDB |
| Orquestador de la carga | `etl/pipeline.py` | Encadena bronce, IPC, dbt build y el control de volumen; escribe la base de servicio y registra la carga | Python |
| Base de servicio | `etl/datos.duckdb` | Las tablas que lee el panel más el registro `etl_run`; unos 13 MB, se sube cada semana | DuckDB |
| Respaldo | `etl/datos.db` | El data warehouse anterior, construido en paralelo y comparado con DuckDB por una prueba de paridad | SQLite |
| Panel | `bi/` | Dashboard, arquitectura, operación y documentación, en solo lectura | Streamlit, Altair |
| Workflow semanal | `.github/workflows/semanal.yml` | Orquesta la carga completa cada martes y publica el informe | GitHub Actions |
| Workflow de pruebas | `.github/workflows/pruebas.yml` | En cada cambio compila el proyecto dbt y corre la suite de pruebas | GitHub Actions, pytest |

[[diagrama:contenedores]]

Las flechas siguen el camino de los datos: de las fuentes a bronce, de bronce a dbt, y del orquestador a la base de servicio que lee el panel. Los dos workflows solo ejecutan; no tocan los datos.

## 5. Elección de tecnologías

Por qué cada herramienta de los contenedores es la que es. Cada razón sale de una decisión registrada o de un hecho comprobable en el repositorio; cuando el registro no guarda las alternativas, la tabla lo dice.

| Herramienta | Para qué se usa aquí | Por qué esta | Alternativas descartadas | Decisión |
|---|---|---|---|---|
| Python 3.11 | Ingesta, ETL de respaldo, orquestador, panel, informe y pruebas | Un solo lenguaje de punta a punta: dbt Core, Streamlit, pandas y pytest son paquetes de Python. Código propio con librerías públicas | No registradas; la elección del lenguaje no tiene entrada propia | D-014, D-015, D-022 |
| requests | Descarga por HTTPS de los archivos de ODEPA y de las series del INE | Los datos ya existen como archivos oficiales: basta una descarga, estable y sin depender de la estructura de una página | Scraping de supermercados | ADR-01 · D-001 |
| SQLite (`raw.db`, `datos.db`) | Zona de aterrizaje de las filas de ODEPA y respaldo del data warehouse anterior | Base en un archivo, sin servidor, que cualquiera puede clonar y ejecutar. En la migración se conservó como aterrizaje y como respaldo para comparar fila a fila | Servidor propio; base en la nube; retirar SQLite el mismo día de la migración | ADR-02, ADR-34 · D-012, D-154 |
| Parquet con pyarrow | Capa bronce, una partición por fuente y año, más las series del INE | Copia literal en columnas que dbt lee directo desde DuckDB: 16 MB frente a 644 MB del aterrizaje, reconstruida en cada ejecución | Subir los datos crudos al repositorio; almacenamiento de archivos grandes | ADR-04, ADR-30 · D-154 |
| dbt Core con dbt-duckdb | Staging, intermedio y marts, con 31 pruebas de datos | Transformaciones declarativas por capas, con las reglas de negocio como pruebas que corren en cada construcción. El motor se elige en la configuración | Transformaciones en Python y consultas sueltas, como antes de la migración | ADR-30, ADR-11 · D-152, D-154 |
| DuckDB | Almacén de trabajo de dbt y base de servicio del panel | Motor analítico en columnas, en un archivo, abierto y sin vencimientos. Pipeline en 16 s en vez de unos 4 minutos, pruebas en 40 s en vez de 140 s, base de unos 13 MB frente a 34 MB | Seguir en SQLite; BigQuery sandbox (las tablas vencen a los 60 días); Snowflake y Redshift (solo períodos de prueba); Databricks (sobredimensionado); PostgreSQL gratuito (algunos planes pausan proyectos inactivos) | ADR-30, ADR-31, ADR-34 · D-152, D-154 |
| pandas | Tipos, fechas y validación en el ETL de respaldo; cálculo de las alertas K6 y filtros del panel | La alerta necesita una desviación estándar móvil, que el motor original no traía. Una versión SQL gemela la vigila fila a fila | Escribir la desviación estándar a mano en SQL; reemplazar Python por SQL en el panel | ADR-18 · D-031, D-033, D-049 |
| SQL (`bi/queries.sql`) | Una consulta con nombre por indicador, leída por el panel y el informe | Cada cifra se comprueba ejecutando su consulta en la base; una sola definición por indicador. El panel pide solo el producto elegido | Consultas con parámetros por producto; vistas dentro de la base; tablas precalculadas | ADR-16, ADR-17 · D-031, D-050 |
| Streamlit | Panel web de solo lectura: Dashboard, ingeniería de datos y documentación | Se publica gratis desde un enlace público, sin servidor que mantener, y comparte con el informe el mismo acceso a datos en Python | Power BI (no se abre desde un enlace público sin licencia) | ADR-02, ADR-35 · D-012, D-032, D-035 |
| Altair | Gráficos del panel | Viene instalado con Streamlit, sin dependencia extra; muestra el detalle al pasar el cursor y devuelve el clic al panel para el filtro cruzado | Matplotlib (imágenes fijas); Plotly para el mapa (la vista 3D que lo usaba salió en D-070) | ADR-35 · D-037, D-069 |
| GitHub Actions | Orquestación: workflow semanal cada martes a las 12:00 UTC y workflow de pruebas en cada cambio | Gratuito en un repositorio público y sin servidor. Se detiene en el primer paso que falla, así la base solo cambia con una carga completa; su caché evita bajar los años cerrados | Servidor propio; guardar la base en otra rama o como artefacto; descargar todo cada semana | ADR-02, ADR-14, ADR-15 · D-012, D-034, D-047 |
| GitHub (repositorio e Issues) | Código, base publicada, informe semanal como issue y aviso de falla por correo | Una sola fuente de verdad del código, abierta y con la autoría en el historial. El informe y los avisos no necesitan servidor de correo, claves ni servicios externos | Repositorio privado o mixto; correo propio; mensajería externa | ADR-03, ADR-27, ADR-36 · D-013, D-017 |
| Streamlit Community Cloud | Publicación del panel desde la rama principal | Gratuito, sin servidor que mantener; el panel publicado solo agrega `duckdb` a sus dependencias, sin dbt | Servidor propio; ejecutar la carga dentro del servidor del panel | ADR-02, ADR-28, ADR-29 · D-012, D-038, D-154 |
| pytest | Suite de pruebas: auditoría independiente, paridad DuckDB ↔ SQLite y gemela SQL de K6 | Las pruebas corren solas en cada cambio y antes de cada commit semanal; una prueba en rojo impide subir la base. La herramienta concreta no tiene entrada propia | Agregar las pruebas al final | ADR-15, ADR-18, ADR-34 · D-016, D-154 |
| reportlab | PDF de PRD, SAD y ADR, con portada, índice y paginación | Genera el PDF desde el mismo Markdown que muestran el panel y GitHub | No registradas | D-157 |

Lo descartado para todo el sistema: nube, contenedores y modelos predictivos que no respondan mejor una pregunta (D-019); un warehouse en la nube mientras los datos sean públicos (ADR-31); la comparación por cadena de supermercados (ADR-32), y el scraping (ADR-01). Las dependencias se instalan con pip desde `requirements.txt` (panel) y `requirements-pipeline.txt` (workflows).

## 6. Nivel 3 · Componentes

### 6.1 El proyecto dbt

| Capa | Modelo | Lee de | Qué hace | Regla |
|---|---|---|---|---|
| Staging | `stg_odepa__wholesale` | Bronce mayorista | Tipos, coma decimal, espacios | RN-01, RN-13 |
| Staging | `stg_odepa__consumer` | Bronce consumidor | Igual, y separa producto, variedad y calidad | RN-01, RN-02, RN-13 |
| Staging | `stg_ine__ipc_monthly` | Bronce del INE | Año, mes, índice y variación mensual con tipos | D-155 |
| Intermedio | `int_prices__validated` | Ambos staging de ODEPA | Asigna a cada fila su motivo de rechazo o ninguno | RN-11 |
| Intermedio | `int_prices__units_normalized` | Filas válidas | Lleva cada precio a kilo, unidad o litro, o lo marca | RN-03 a RN-05 |
| Intermedio | `int_prices__weekly` | Precios normalizados | Agrega por lunes, ponderando por volumen en el mayorista | RN-07 a RN-10 |
| Intermedio | `int_prices__outlier_flagged` | Precios semanales | Marca atípicos con la mediana de su propia fuente | RN-12 |
| Marts | `dim_product`, `dim_region`, `dim_channel`, `dim_date` | Intermedio | Dimensiones del modelo estrella | D-095 |
| Marts | `weekly_price` | Intermedio y dimensiones | Tabla de hechos | RN-14 |
| Marts | `rejection` | Validación | Filas rechazadas de la carga, tal como venían | RN-11 |
| Marts | `ipc_monthly` | Staging del INE | Una sola serie mensual enlazada, base 2023 = 100 | D-155 |
| Marts | `ipc_weekly` | `ipc_monthly` y `dim_date` | Factor real de cada semana y marca provisional | D-155 |
| Marts | `ine_ipc_source` | Staging del INE | Las filas originales del INE, para auditoría y respaldo | D-155 |

### 6.2 El panel

| Componente | Ubicación | Responsabilidad |
|---|---|---|
| Acceso a datos | `bi/queries.py`, `bi/queries.sql` | Único punto de conexión a DuckDB, en solo lectura; una consulta con nombre por indicador |
| Alertas | `bi/alerts.py` | Alertas K6 como funciones puras, con una versión SQL gemela que se reconcilia fila a fila |
| Contexto de precios | `bi/price_context.py` | Rango habitual, brechas, margen, patrón de temporada y precios reales |
| Diagramas | `bi/architecture.py`, `bi/star_model.py`, `bi/lineage.py`, `bi/doc_diagrams.py` | Los diagramas vivos de plataforma, recorrido, linaje dbt y modelo estrella, y las vistas propias de estos documentos |
| Calidad y operación | `bi/quality.py`, `bi/control.py` | Calidad de datos, historial de ejecuciones y ejecución manual protegida |
| Informe semanal | `bi/report.py` | Estado de la carga, K7 y alertas, publicado como issue |
| Documentos en PDF | `bi/document_pdf.py` | PRD, SAD y ADR con portada, índice y paginación, generados desde los mismos archivos |
| Aplicación | `bi/dashboard.py` | Navegación, páginas y composición |

## 7. Linaje de los datos

Los datos atraviesan seis capas. Cada una tiene un solo propósito y un solo lugar. El recorrido completo, con el estado real de cada paso, y el linaje dbt modelo a modelo, con sus pruebas, viven en la página Pipeline y linaje del panel; este documento no los repite, porque la vista de contenedores de la sección 4 ya muestra por dónde pasan los datos.

| Capa | Dónde | Qué contiene | Se sube al repositorio |
|---|---|---|---|
| Aterrizaje | `etl/raw.db` | Las filas de los archivos de ODEPA tal como llegan, con año y huella | No |
| Bronce | `etl/bronze/` (Parquet) | La misma copia literal, por fuente y año, y las series del INE como texto | No |
| Staging | Vistas de dbt | Tipos, números legibles, textos normalizados, claves de producto | No |
| Intermedio | Tablas de dbt | Validación, unidades, agregación semanal y atípicos | No |
| Marts | Tablas de dbt | Modelo estrella, rechazos, IPC mensual y semanal | No (almacén de trabajo) |
| Servicio | `etl/datos.duckdb` | Copia compacta de los marts más el registro de cargas | Sí, cada semana |

El paso de marts a servicio es deliberado: el almacén de trabajo de dbt guarda vistas y tablas intermedias que el panel no usa; la base de servicio copia solo las tablas necesarias en un archivo nuevo y lo reemplaza de una vez, cuando todo pasó (ADR-34).

## 8. Flujo del IPC

| Paso | Qué ocurre | Dónde |
|---|---|---|
| 1. Descarga | Se leen los dos archivos oficiales del INE y se conserva solo la división 1, «Alimentos y bebidas no alcohólicas» | Ingesta del IPC |
| 2. Bronce | Año, mes, índice y variación mensual se guardan como texto, tal como se publican | `etl/bronze/ine_ipc` |
| 3. Enlace | La serie empalmada (diciembre 2009 a diciembre 2023) está en otra base; se escala para que enero 2024 suba exactamente el +1,0 % oficial | `ipc_monthly` |
| 4. Mes a semana | Cada semana toma el IPC del mes de su lunes | `ipc_weekly` |
| 5. Factor real | IPC del último mes publicado dividido por el IPC del mes de la semana; el precio real queda en pesos de ese último mes | `ipc_weekly` |
| 6. Provisional | Una semana cuyo mes aún no se publica usa el último mes y se marca provisional | `ipc_weekly` |
| 7. Panel | Contexto de precios ofrece Nominal / Real; la serie, su rango habitual y su estado se recalculan en Real | Panel |

Si el INE no responde, la carga no se detiene: se usa el bronce previo o se reconstruye desde las filas del INE guardadas en la base publicada. Hoy la serie enlazada tiene 202 meses, de diciembre 2009 a septiembre 2026, y una sola semana provisional, la del 05-10-2026.

## 9. Modelo de datos

[[diagrama:modelo]]

Es el mismo diagrama de la página Modelo de datos del panel: el modelo estrella es la vista canónica de los datos y se dibuja desde el esquema real. Un hecho al centro, cuatro dimensiones alrededor, el IPC como tabla puente por semana y un grupo de auditoría aparte. El mayorista es un canal más: el margen es una comparación entre dos canales de la misma tabla.

| Tabla | Rol | Grano | Filas |
|---|---|---|---|
| `weekly_price` | Hechos | Semana, producto, región, canal y unidad normalizada | 811.578 |
| `dim_product` | Dimensión | Familia, producto, variedad y calidad | 1.609 |
| `dim_region` | Dimensión | Región con datos y su número oficial | 9 |
| `dim_channel` | Dimensión | Canal y fuente | 8 |
| `dim_date` | Dimensión | Semana (lunes), sin huecos, con semana ISO, mes y estación | 249 |
| `ipc_monthly` | IPC | Mes, base 2023 = 100 | 202 |
| `ipc_weekly` | IPC | Semana, con factor real y marca provisional | 249 |
| `ine_ipc_source` | Auditoría | Fila original del INE | 202 |
| `etl_run` | Auditoría | Carga: inicio, estado, filas leídas, cargadas y rechazadas | 4 |
| `rejection` | Auditoría | Fila rechazada de la última carga, con su motivo | 201 |
| `dbt_node` | Linaje | Modelo, fuente o prueba del proyecto dbt (16 modelos, 3 fuentes, 31 pruebas) | 50 |
| `dbt_result` | Linaje | Resultado de cada modelo y prueba en la última construcción | 47 |

Cada precio guarda su unidad normalizada, el volumen en el mayorista, el número de observaciones de origen y una marca: 826 precios están marcados como atípicos y 12.472 sin unidad convertible. Ninguno se borra.

## 10. Vista de ejecución

### 10.1 El martes automático

[[diagrama:secuencia]]

El diagrama sigue los mensajes entre los participantes; la tabla dice qué pasa si cada paso falla.

| Paso | Qué ocurre | Si falla |
|---|---|---|
| 1 | GitHub Actions inicia el workflow a las 12:00 UTC | — |
| 2 | Restaura de la caché los archivos de años cerrados | Si venció, se descarga todo, sin falla |
| 3 | El agente descarga el año en curso y lo que falte | Un encabezado distinto detiene el workflow |
| 4 | El ETL de respaldo reconstruye el SQLite | El workflow se detiene |
| 5 | El orquestador copia a bronce, actualiza el IPC y corre dbt build | La falla queda en `etl_run`; la base publicada no cambia |
| 6 | Control de volumen: menos del 90 % de las filas de la última carga correcta detiene la carga | Igual que el paso 5 |
| 7 | Se escribe la base de servicio y se reemplaza la publicada | — |
| 8 | La suite de pruebas corre contra la base nueva, incluida la paridad con SQLite | Nada se sube |
| 9 | Un commit guarda las bases y el registro de descargas | — |
| 10 | Se publica el issue «Informe semanal» | — |

GitHub Actions se detiene en el primer paso que falla, avisa al autor por correo y la base del repositorio queda como estaba.

### 10.2 Otros escenarios

| Escenario | Lo inicia | Qué ocurre | Resultado |
|---|---|---|---|
| Un cambio de código | Un push a la rama principal | El workflow de pruebas compila el proyecto dbt y corre la suite; Streamlit Community Cloud publica la rama principal en paralelo | Una prueba en rojo avisa, no detiene la publicación |
| Una ejecución manual | El autor, con la clave de control, en Ejecuciones | El botón «Ejecutar pipeline ahora» lanza el mismo workflow semanal mediante la API de GitHub, con un token limitado al repositorio, y muestra los pasos en vivo | Un mensaje claro de éxito o de falla (D-149) |
| Una visita al panel | Un visitante | El panel abre la base de servicio en solo lectura, pide solo las filas del producto elegido y guarda los resultados en caché hasta que cambia la base | El estado del pipeline se lee de la API pública de GitHub y, si no responde, de `etl_run` |

## 11. Vista de despliegue

[[diagrama:plataforma]]

Es el mismo diagrama de la pestaña Plataforma y seguridad de Ejecuciones y DevOps: cada plataforma es un nodo de despliegue con sus componentes dentro, y cada conexión dice cómo se comunican (descargas por HTTPS, git push, despliegue de main y secretos del panel).

| Nodo | Qué corre | Qué guarda |
|---|---|---|
| Portal de ODEPA y sitio del INE | Publicación de los archivos oficiales | Fuente de verdad |
| Runner de GitHub Actions (Ubuntu, Python 3.11) | Agente, ETL de respaldo, orquestador, dbt, pruebas, informe | Archivos de años cerrados en caché; aterrizaje, bronce y almacén de trabajo solo durante la ejecución |
| Repositorio en GitHub | Código, workflows, issues | Base de servicio, respaldo SQLite y registro de descargas |
| Streamlit Community Cloud | Panel | Secretos: token de GitHub y clave de control |
| Equipo del autor | Desarrollo y pruebas locales | Aterrizaje, bronce y almacén de trabajo, fuera del repositorio |

## 12. Conceptos transversales

**Calidad de datos como pruebas.** Las reglas son pruebas de dbt que corren en cada construcción. Ninguna base se publica con una prueba en rojo.

| Familia de pruebas | Qué garantiza | Cantidad |
|---|---|---|
| Claves únicas | Dimensiones e IPC semanal sin duplicados | 5 |
| Valores obligatorios | Claves, observaciones, índice y factor real nunca vacíos | 11 |
| Relaciones | Todo hecho apunta a un producto, región, canal y semana existentes; todo factor real, a una semana | 5 |
| Valores aceptados | Unidades, marcas, canales, regiones del 1 al 16 y motivos de rechazo conocidos | 5 |
| Reglas de negocio | Precios positivos, una fila por clave, semanas completas salvo el hueco conocido, conciliación de filas y un IPC por mes | 5 |

**Auditoría independiente.** Fuera de dbt, la suite de Python reconstruye precios desde las filas crudas, repite las invariantes del modelo, vuelve a enlazar el IPC y a calcular el factor de cada semana desde el texto del INE, y compara fila a fila DuckDB con el respaldo SQLite. Una fotografía de las cifras de la semana del 05-10-2026 debe reproducirse exacta.

| Concepto | Cómo se aplica |
|---|---|
| Integridad | dbt construye en un almacén de trabajo; la base de servicio se escribe en un archivo temporal y solo entonces reemplaza la publicada. Una falla deja la base intacta y queda registrada |
| Idempotencia | Cada carga reconstruye todas las tablas desde bronce; ejecutar dos veces la misma semana deja las mismas filas, y una prueba lo vigila |
| Comparación justa | Toda variación semanal compara solo regiones con precio en ambas semanas; todo rango habitual usa la historia de las regiones presentes esta semana |
| Seguridad | El panel abre la base en solo lectura y no ejecuta texto de un visitante. El token de GitHub y la clave de control viven en los secretos del panel; la clave se compara en tiempo constante. El workflow semanal solo puede escribir contenido e issues |
| Observabilidad | `etl_run`, `rejection`, `dbt_node` y `dbt_result` en la base, el historial de GitHub Actions visible en Ejecuciones, el issue semanal y el correo de GitHub ante una falla |
| Portabilidad | El motor se elige en la configuración de dbt, que ya documenta los equivalentes para BigQuery, Snowflake y PostgreSQL sin activarlos. Los modelos usan SQL lo más estándar posible y macros donde los motores difieren; las pocas funciones propias de DuckDB (fechas, expresiones regulares) son lo que habría que adaptar; el panel se conecta en un solo punto |

## 13. Atributos de calidad

| Atributo | Cómo se logra | Cómo se verifica |
|---|---|---|
| Exactitud | Clave exacta, conversión literal de unidades, agregación ponderada | Precios reconstruidos desde las filas crudas en cada ejecución de pruebas |
| Paridad de la migración | DuckDB y SQLite construidos en paralelo | 811.578 precios iguales, diferencia máxima 4,9 × 10⁻¹⁶ |
| Exactitud del deflactor | Enlace con la variación oficial | Recalculado sin dbt, diferencia relativa menor a 10⁻¹² |
| Completitud trazable | Rechazo con motivo, nunca borrado | Prueba de conciliación de dbt |
| Integridad | Reemplazo atómico de la base | Opción manual de simular una falla en el workflow |
| Rendimiento | Motor en columnas y caché por versión de la base | Pipeline completo en 16 s y pruebas en 40 s, frente a unos 4 minutos y 140 s antes (D-154) |
| Costo | Herramientas abiertas y servicios gratuitos | Ningún servicio de pago |

## 14. Riesgos y deuda técnica

| Tema | Descripción | Referencia |
|---|---|---|
| Doble escritura | El respaldo SQLite se sigue construyendo mientras el autor decide retirarlo | D-154 |
| Entorno local de dbt | dbt aún no se instala en Python 3.14; en local corre en un entorno aparte con Python 3.12 | D-154 |
| Historial de Git | Cada commit semanal reescribe las bases | ADR-15 |
| Caché vencida | Algunas semanas se descarga todo; una corrección de ODEPA en un año cerrado entra tarde | ADR-14 |
| Volumen sin convertir | La ponderación usa el volumen en su unidad de venta | ADR-07 |
| Rezago del INE | La última semana suele ser provisional | ADR-33 |
| Código de K5 residual | El cálculo sigue en el repositorio aunque el indicador salió del producto | ADR-25 |
| Token con vencimiento | Si vence, la ejecución manual deja de funcionar | ADR-28 |
| Cuatro martes seguidos | La operación sin intervención aún no se observó cuatro semanas consecutivas | PRD, criterio 1 |

## 15. Escalabilidad

La arquitectura está pensada para crecer cambiando configuración, no código. Lo que sigue es una proyección, no una entrega.

| Extensión | Fuente | Estado | Cómo entraría |
|---|---|---|---|
| Clima por región y semana | Fuente oficial por definir | Prevista | Nueva carpeta de bronce, un staging y un mart por semana y región, junto a las alertas K6, sin afirmar causalidad |
| Warehouse en la nube | — | No adoptado | Un nuevo destino en la configuración de dbt, con los mismos modelos y la misma auditoría |

**¿Por qué no hay nube?** Con datos públicos, semanales y de pocos megabytes, leídos por un solo panel, un warehouse en la nube agregaría costo, secretos y riesgos de vencimiento sin beneficio (ADR-31). Se justificaría solo si una empresa sumara sus propios datos:

| Criterio | Hoy | Umbral que justificaría la nube |
|---|---|---|
| Volumen | Unos 13 MB en la base de servicio | Varios GB: ventas por tienda y día, costos, inventario |
| Usuarios | Un panel de solo lectura | Varios equipos o herramientas de BI sobre los mismos datos |
| Acceso | Público | Permisos por persona o datos sensibles |
| Frescura | Semanal | Varias cargas al día o tiempo real |

## 16. Glosario

| Término | Significado |
|---|---|
| Aterrizaje | Zona donde llegan las filas de los archivos antes de pasar a bronce |
| Bronce | Copia literal de los datos de la fuente, en Parquet |
| Staging | Primera capa de dbt: tipos y textos limpios, sin cambiar el grano |
| Intermedio | Capa de dbt con las reglas de negocio |
| Marts | Tablas finales del modelo estrella y del IPC |
| Base de servicio | Archivo compacto de DuckDB que lee el panel |
| Clave de producto | Producto + variedad + calidad |
| Factor real | IPC del último mes publicado dividido por el IPC del mes de la semana |
| Provisional | Semana cuyo mes aún no publica el INE |
| Rango habitual | P25 a P75 del precio en la misma semana ISO ±1 de años anteriores |
| Workflow | Tarea automática de GitHub Actions |
