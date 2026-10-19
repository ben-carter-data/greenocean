# GreenOcean · Documento de arquitectura de software (SAD)

Estructura inspirada en arc42 y en los niveles de contexto y contenedores de C4. Describe el sistema tal como está en el repositorio; las razones de cada elección están en `docs/ADR.md` y, completas, en `docs/DECISIONES.md`.

---

## 1. Introducción y objetivos de calidad

GreenOcean es un pipeline de datos semanal con un panel de BI. Toma dos fuentes abiertas de ODEPA, las hace comparables y publica tres respuestas: qué se movió esta semana, si el precio de hoy es normal para la temporada y cuánto paga el consumidor sobre el mayorista.

Los cinco objetivos de calidad que guían la arquitectura, en orden:

| Prioridad | Objetivo | Qué significa aquí |
|---|---|---|
| 1 | Corrección y trazabilidad | Ninguna fila desaparece sin motivo; cada cifra se reconstruye desde la fuente |
| 2 | Integridad ante fallas | Una carga que falla no reemplaza la última base válida |
| 3 | Operación sin supervisión | El pipeline corre solo cada semana y avisa cuando algo sale mal |
| 4 | Coste cero y simplicidad | Solo servicios gratuitos y piezas que el proyecto usa de verdad |
| 5 | Lectura inmediata | Cada vista del panel responde su pregunta en una pantalla |

## 2. Restricciones

| Restricción | Origen |
|---|---|
| Solo fuentes oficiales descargables; sin scraping | D-001 |
| Sin costo de infraestructura | D-012 |
| Repositorio público, licencia MIT | D-013, D-036 |
| GitHub rechaza archivos de más de 100 MB y avisa sobre 50 MB | D-020, D-046 |
| SQLite no trae desviación estándar ni mediana | D-033, D-041, D-049 |
| Python 3.11, pandas, requests, Streamlit 1.36 o superior, Plotly, pytest | `requirements.txt`, D-032 |
| Código en inglés; documentos y panel en español; valores de ODEPA sin traducir | D-021, D-023 |
| Sin nube, contenedores ni modelos predictivos agregados para aparentar | D-019 |

## 3. Contexto del sistema

El sistema tiene un solo proveedor de datos y un solo tipo de consumidor.

| Actor o sistema externo | Relación |
|---|---|
| ODEPA, portal de datos abiertos | Publica un CSV por año y fuente; el pipeline lo descarga por HTTPS |
| GitHub | Guarda el código y el data warehouse, ejecuta los workflows, publica el informe semanal y avisa por correo si falla |
| Streamlit Community Cloud | Publica el panel desde la rama principal |
| Visitantes del panel | Leen el Dashboard, la Arquitectura y las Fuentes; no escriben nada |
| El autor | Mantiene el código, administra los secretos y puede lanzar una ejecución manual |

[[diagrama:plataforma]]

El diagrama muestra cada plataforma como un recuadro con sus componentes dentro: ODEPA, GitHub, el computador del autor, Streamlit Community Cloud y los usuarios, y cómo se comunican (HTTPS con CSV, git push, secretos del panel).

## 4. Vista de bloques y contenedores

| Contenedor | Ubicación | Responsabilidad | Tecnología |
|---|---|---|---|
| Agente de ingesta | `agent/agent.py` | Lee la lista de recursos, descarga, valida tamaño, encabezado y filas, calcula la huella del archivo y registra cada resultado | Python, requests |
| Capa bronce | `raw.db` (tablas `raw_wholesale` y `raw_consumer`) | Guarda las filas tal como llegan, con año y huella del archivo; se reconstruye en cada ejecución y no se sube al repositorio | SQLite |
| ETL | `etl/etl.py` | Limpia, valida, aplica las reglas RN-01 a RN-14, revisa la calidad y carga | Python, pandas |
| Data warehouse (oro) | `etl/datos.db` | Modelo estrella con los precios semanales, más el registro de cargas y rechazos; se sube al repositorio | SQLite |
| Capa de consultas | `bi/queries.sql`, `bi/queries.py` | Una consulta con nombre por indicador; la base se abre en solo lectura | SQL, Python |
| Cálculos del panel | `bi/alerts.py`, `bi/price_context.py` | Alertas K6 y rango habitual, brechas y patrón de temporada, como funciones puras con pruebas | Python, pandas |
| Panel | `bi/dashboard.py` y módulos de `bi/` | Páginas del Dashboard, Arquitectura, Fuentes, Documentación, Alerta de precio y GitHub | Streamlit, Plotly |
| Informe semanal | `bi/report.py` | Resume estado de carga, K7 y alertas de la semana | Python |
| Workflow semanal | `.github/workflows/semanal.yml` | Orquesta ingesta, ETL, pruebas, guardado e informe | GitHub Actions |
| Workflow de pruebas | `.github/workflows/pruebas.yml` | Corre la suite en cada push y pull request | GitHub Actions, pytest |

El menú del panel tiene hoy estas entradas: Dashboard (Resumen semanal, Contexto de precios), Arquitectura (Pipeline, Modelo de datos, DevOps y seguridad, Calidad de datos, Ejecuciones), Fuentes (los dos enlaces de ODEPA), Documentación, Alerta de precio y la página GitHub.

## 5. Flujo de datos por capas

[[diagrama:pipeline]]

| Capa | Qué ocurre | Dónde | Salida |
|---|---|---|---|
| Fuentes | ODEPA publica un CSV por año: mayorista diario y consumidor semanal | Portal de ODEPA | Archivos CSV |
| Ingesta | Descarga del año en curso y de los años cerrados que falten; validación de encabezado | Agente | CSV locales y `manifest.json` |
| Bronce (staging) | Copia literal de las filas, con año y huella | `raw.db` | Tablas crudas |
| Limpieza | Números con coma decimal, espacios, separación de producto, variedad y calidad | ETL | Filas limpias |
| Validación | Precio no positivo, mínimo sobre máximo, volumen no positivo, fecha fuera del año, valor ilegible | ETL | Filas válidas y rechazos con motivo |
| Reglas | Conversión de unidades, asignación al lunes, agregación semanal, marca de atípicos | ETL | Precios semanales |
| Calidad | Controles de filas, semanas faltantes, regiones, canales y claves duplicadas | ETL | Carga aprobada o detenida |
| Oro | Dimensiones, calendario, hechos, registro de la carga y rechazos, en una transacción | `datos.db` | Data warehouse |
| Consumo | Consultas con nombre, cálculos de alertas y contexto, panel e informe | `bi/` | Panel e issue semanal |

La capa plata no se guarda como tabla: son las filas limpias y validadas en memoria entre la limpieza y la carga (D-039).

## 6. Modelo de datos

[[diagrama:modelo]]

Un hecho al centro, cuatro dimensiones alrededor y un grupo de auditoría aparte. El mayorista es un canal más de `dim_channel`: el margen es una comparación entre dos canales de la misma tabla.

| Tabla | Rol | Grano | Filas actuales |
|---|---|---|---|
| `weekly_price` | Hechos | Una fila por semana, producto, región, canal y unidad normalizada | 811.578 |
| `dim_product` | Dimensión | Una clave: familia, producto, variedad y calidad | 1.609 |
| `dim_region` | Dimensión | Una región con datos, con su número oficial | 9 |
| `dim_channel` | Dimensión | Un canal con su fuente (Mayorista y 7 puntos de venta) | 8 |
| `dim_date` | Dimensión | Una semana (lunes), sin huecos, con año y semana ISO, mes y estación del hemisferio sur | 249 |
| `etl_run` | Auditoría | Una carga: inicio, estado, filas leídas, cargadas y rechazadas | 4 |
| `rejection` | Auditoría | Una fila rechazada de la última carga, tal como venía, con su motivo | 201 |

Cada precio semanal guarda además su unidad normalizada (kilo, unidad, litro o vacía), el volumen en el mayorista, el número de observaciones de origen y una marca (`ATIPICO` o `UNIDAD_NO_CONVERTIBLE`). La relación con `dim_date` es una clave foránea real (D-095). La unicidad de la clave del hecho la garantiza el ETL, no un índice (D-046). El archivo pesa unos 34 MB.

## 7. Vista de ejecución

### 7.1 El martes automático

1. A las 12:00 UTC GitHub Actions inicia el workflow semanal.
2. Restaura de la caché los CSV de años cerrados; la clave cambia con el año en curso y con la lista de recursos.
3. El agente descarga el año en curso y lo que falte; si un encabezado cambió, registra `UNEXPECTED_HEADER` y el job falla.
4. El ETL reconstruye `raw.db`, limpia, aplica reglas y pasa los controles. Si uno falla, registra la carga como `FAILED` y no escribe precios.
5. La suite de pruebas corre contra la base nueva, incluida la auditoría de datos.
6. Un commit guarda `datos.db` y `manifest.json`.
7. Se publica el issue «Informe semanal AAAA-MM-DD».

Si cualquier paso falla, los siguientes no corren, la base del repositorio queda como estaba y GitHub avisa al autor por correo.

### 7.2 Un push

`pruebas.yml` corre la suite. En paralelo, Streamlit Community Cloud publica la rama principal sin esperar el resultado: una prueba en rojo avisa, no detiene la publicación.

### 7.3 Una ejecución manual

En Ejecuciones, el botón «Ejecutar pipeline ahora» pide la clave de control, lanza el mismo `semanal.yml` mediante la API de GitHub con un token limitado al repositorio, muestra los pasos en vivo y termina con «Se ejecutó correctamente» o «No se ejecutó completamente: un paso falló». Sin la clave y el token en los secretos, el botón aparece desactivado con su motivo (D-149). También se puede lanzar desde GitHub, con la opción de simular una falla después del ETL.

### 7.4 Una visita al panel

El panel abre `datos.db` en solo lectura, pide a SQLite solo las filas del producto elegido y guarda los resultados en caché hasta que cambia la base. El estado del pipeline se lee de la API pública de GitHub; si no responde, del registro `etl_run`.

## 8. Vista de despliegue

| Nodo | Qué corre | Qué guarda |
|---|---|---|
| Portal de ODEPA | Publicación de los CSV | Fuente oficial |
| Runner de GitHub Actions (Ubuntu, Python 3.11) | Agente, ETL, pruebas, informe | CSV de años cerrados en la caché de Actions; `raw.db` solo durante la ejecución |
| Repositorio en GitHub | Código, workflows, issues | `datos.db`, `manifest.json`, historial |
| Streamlit Community Cloud | Panel | Secretos: token de GitHub y clave de control |
| Computador del autor | Desarrollo, pruebas locales, dev container | `raw.db` y CSV locales, fuera del repositorio |

En el servidor publicado el vigilante de archivos de Streamlit está desactivado: nadie edita archivos allí y agotaba los recursos del contenedor (D-109).

## 9. Conceptos transversales

**Calidad de datos y auditoría.** Antes de cargar, el ETL detiene la carga si las filas leídas bajan del 90 % de la última carga correcta, si falta una semana fuera de la lista de huecos conocidos (hoy solo la semana del 02-05-2022 del consumidor), si aparece una región fuera de 1 a 16, un canal desconocido o una clave duplicada. Después, `tests/test_data_audit.py` repite seis invariantes (cada semana es lunes, calendario sin huecos, una fila por clave, ningún precio no positivo, toda clave con familia, leídas = cargadas + rechazadas), reconstruye 120 precios desde las filas crudas y verifica las reglas de lectura de la revisión de pertinencia. La parte que necesita `raw.db` se omite donde ese archivo no existe.

**Seguridad.** El panel abre la base en solo lectura. El token de GitHub y la clave de control viven en los secretos del panel, nunca en el código; la clave se compara en tiempo constante. El workflow semanal solo tiene permiso para escribir contenido e issues. Sin consolas de SQL ni de Python, el panel no ejecuta texto escrito por un visitante (D-143, D-148). La seguridad real está en las cuentas de GitHub y Streamlit; la clave solo ordena quién usa el botón (MANUAL.md).

**Observabilidad.** `etl_run` y `rejection` en la base; un log del agente por ejecución; el historial de GitHub Actions, visible en Ejecuciones; el issue semanal; el correo de GitHub ante una falla.

**Idempotencia (RN-14).** Cada carga borra y reescribe `weekly_price` y `dim_date` dentro de una transacción; las dimensiones solo reciben filas nuevas, así sus identificadores no cambian. Al final se compacta el archivo.

**Comparación justa.** Toda variación semanal compara solo las regiones con precio en ambas semanas; todo rango habitual usa la historia de las regiones presentes esta semana (D-144, D-145, D-146).

**Caché.** En Actions, los CSV de años cerrados (D-047). En el panel, las consultas y los cálculos quedan en caché hasta que cambia la base, así cada carga semanal los renueva (D-050, D-094).

## 10. Atributos de calidad

| Atributo | Cómo se logra | Cómo se verifica |
|---|---|---|
| Exactitud | Clave exacta, conversión literal de unidades, agregación ponderada | 400 precios reconstruidos desde las filas crudas coincidieron exactamente (D-144); 120 en cada ejecución de pruebas |
| Completitud trazable | Rechazo con motivo, nunca borrado | Leídas = cargadas + rechazadas en cada carga |
| Integridad | Workflow que se detiene en el primer paso fallido | Opción manual de simular una falla (T-23) |
| Idempotencia | Reconstrucción completa en transacción | Pruebas de RN-14; cargas sucesivas con las mismas cifras |
| Consistencia de cálculo | K6 en Python con versión SQL gemela | Prueba de reconciliación fila a fila (D-049, D-145) |
| Pertinencia | Mediana por familia, prueba de signos, alerta material, patrón con acuerdo de años | Pruebas de `tests/test_data_audit.py` (D-146) |
| Rendimiento | Filtro en SQLite por producto y caché | Medido en D-050: el Panel pasó de 6,8 s a 2,5 s en local |
| Disponibilidad del panel | Servicio gestionado, vigilante de archivos desactivado | Arranque comprobado (D-109) |
| Seguridad | Solo lectura, secretos, permisos mínimos | Pruebas `test_d149_*` de la ejecución manual |
| Coste | Servicios gratuitos | Sin servicios de pago en el stack |

## 11. Riesgos y deuda técnica

| Tema | Descripción | Referencia |
|---|---|---|
| Crecimiento del historial | Cada commit semanal reescribe `datos.db`; el historial de Git crece cada semana | D-034, D-046 |
| Unicidad fuera de la base | Sin índice único, otro programa que escriba en la base podría duplicar filas | D-046 |
| Caché vencida | GitHub borra la caché sin uso en 7 días; algunas semanas se descarga todo | D-047 |
| Correcciones tardías de ODEPA | Un cambio en un año cerrado entra recién cuando la caché se renueva | D-047 |
| Volumen sin convertir | RN-07 pondera con el volumen en la unidad de comercialización; envases distintos pesan mal | D-027 |
| Mediana de atípicos | Mezcla variedades y calidades; marca algunos precios probablemente reales | D-028 |
| Código de K5 residual | `bi/lag.py` y la consulta `k5_weekly_variations_sql` siguen en el repositorio aunque el indicador salió del producto | D-146 |
| Token con vencimiento | Si vence, la ejecución manual deja de funcionar | D-038, D-053 |
| Cuatro martes seguidos | La operación sin intervención aún no se observó cuatro semanas consecutivas | T-26 |
| Warehouse en la nube | No hace falta en el alcance actual; los criterios para adoptarlo están en la sección 12 | ADR-31 |

## 12. Evolución prevista

Esta sección describe una arquitectura **planificada, no entregada** (ADR-30). El plan por fases está en `docs/PROMPT_EVOLUCION.md`.

| Capa | Hoy | Prevista |
|---|---|---|
| Bronce | SQLite `raw.db`, fuera del repositorio | Parquet por fuente y año |
| Transformación | Python (`etl/etl.py`) y consultas con nombre | dbt Core: staging → intermedio → marts, con las reglas como pruebas |
| Oro | SQLite `datos.db` | DuckDB, un solo archivo en el repositorio |
| Nuevas fuentes | — | IPC del INE (precios reales) y clima por región |

**Portabilidad.** El motor se elige en la configuración de dbt; los modelos usan SQL estándar y macros donde los motores difieren; el panel accede a los datos por una sola capa (`bi/queries.py`). Así, pasar a BigQuery, Snowflake, PostgreSQL o Databricks sería un cambio de configuración, verificado con la misma auditoría.

**¿Y un warehouse en la nube?** En su alcance público actual el proyecto no lo necesita y probablemente nunca lo necesitará: datos abiertos, semanales y pequeños, leídos por un solo panel. Se justificaría si una empresa lo adoptara y le sumara sus propios datos:

| Criterio | Hoy | Umbral que justificaría la nube |
|---|---|---|
| Volumen | ~34 MB | Varios GB: ventas por tienda y día, costos, inventario |
| Usuarios | Un panel de solo lectura | Varios equipos o herramientas BI sobre los mismos datos |
| Acceso | Público | Permisos distintos por persona o datos sensibles |
| Frescura | Semanal | Tiempo real o varias cargas al día |

## 13. Glosario breve

| Término | Significado |
|---|---|
| Bronce, plata, oro | Datos tal como llegan, limpios con reglas y listos para analizar |
| Clave de producto | Producto + variedad + calidad |
| Cotización | Un precio informado por la fuente para una semana, región y canal |
| Data warehouse | `datos.db`, la base con el modelo estrella |
| Grano | Lo que representa una fila de la tabla de hechos |
| Hueco conocido | Semana que falta en la fuente y está registrada como tal |
| Rango habitual | P25 a P75 del precio en la misma semana ISO ±1 de años anteriores |
| Staging | Capa intermedia donde se guardan los datos crudos (`raw.db`) |
| Workflow | Tarea automática de GitHub Actions |
