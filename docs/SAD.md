# Documento de arquitectura de software (SAD)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Documento de arquitectura de software (SAD), estructura arc42 con vistas C4 |
| Versión | 3.2 |
| Fecha | 30-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Explicar cómo está construido GreenOcean, cómo corre cada semana, dónde viven sus datos y por qué tiene esa forma. |
| Audiencia | Arquitectura, ingeniería de datos, operación, gerencia y revisión técnica. |
| Documentos relacionados | [Documento de requisitos del producto (PRD)](PRD.md) · [Registros de decisiones de arquitectura (ADR)](ADR.md) · [Plan de pruebas y seguridad](PLAN_PRUEBAS.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [En resumen](#1-en-resumen)
2. [Contexto](#2-contexto)
3. [Contenedores](#3-contenedores)
4. [La carga de cada semana](#4-la-carga-de-cada-semana)
5. [El panel al abrirse](#5-el-panel-al-abrirse)
6. [Los datos](#6-los-datos)
7. [Despliegue](#7-despliegue)
8. [Calidad, seguridad y observabilidad](#8-calidad-seguridad-y-observabilidad)
9. [Capacidad y crecimiento](#9-capacidad-y-crecimiento)
10. [Restricciones y decisiones](#10-restricciones-y-decisiones)
11. [Riesgos y deuda técnica](#11-riesgos-y-deuda-técnica)
12. [Glosario](#12-glosario)
13. [Historial de versiones](#13-historial-de-versiones)

## 1. En resumen

GreenOcean es un pipeline semanal y un panel de solo lectura sobre los precios de los alimentos en Chile. Su arquitectura persigue tres objetivos, en este orden:

| Prioridad | Objetivo de calidad | Qué significa aquí |
|---|---|---|
| 1 | Exactitud y trazabilidad | Cada cifra del panel se puede recalcular desde el archivo original |
| 2 | Confiabilidad de la publicación | Una carga con errores nunca reemplaza a la base servida |
| 3 | Costo cero y mantenimiento mínimo | Solo servicios gratuitos permanentes y sin servidores propios |

Para lograrlos, la carga rehace toda la historia cada martes desde los archivos oficiales, la comprueba por dos caminos independientes y solo entonces reemplaza la base que lee el panel. Todo corre en servicios gratuitos, sin servidores propios.

## 2. Contexto

[[diagrama:contexto]]

El sistema lee dos fuentes públicas, ODEPA y el INE, y se apoya en dos servicios gratuitos: GitHub guarda el código y la base servida y ejecuta la carga; Streamlit Community Cloud publica el panel. El visitante solo lee el panel. El administrador, el autor del proyecto, mantiene el código y los secretos.

### 2.1 Escenarios clave

[[diagrama:escenarios]]

Cada escenario recorre la arquitectura de punta a punta; las secciones 4 y 5 los muestran paso a paso.

## 3. Contenedores

[[diagrama:contenedores]]

El sistema tiene dos aplicaciones y tres almacenes de datos:

| Contenedor | Tecnología | Responsabilidad |
|---|---|---|
| Carga semanal | Python, dbt Core, DuckDB | Descarga los CSV, los guarda sin cambios, los transforma y prueba, y reemplaza la base servida solo si todo pasa. El agente, el ETL y dbt corren en el mismo job |
| Archivos de trabajo | SQLite, Parquet, DuckDB | Aterrizaje, bronce y base de trabajo de dbt; se rehacen en cada carga y no se versionan |
| Base servida | DuckDB (`etl/datos.duckdb`) | Las tablas que lee el panel; se publica en el release «base-actual» |
| Respaldo | SQLite (`etl/datos.db`) | Los mismos precios calculados sin dbt, para la prueba de paridad; se rehace en la máquina de cada carga y no se publica |
| Panel web | Streamlit, Python | Muestra los indicadores y los documentos, y ofrece el estudio SQL; lee la base servida en solo lectura y, con la clave de control, lanza la carga por la API de GitHub |

### 3.1 Componentes de la carga semanal

[[diagrama:componentes_carga]]

Cada componente es un archivo del repositorio y corre como un paso de `semanal.yml`; si uno falla, los siguientes no corren.

### 3.2 Componentes del panel

[[diagrama:componentes_panel]]

`bi/dashboard.py` arma la navegación y cada página con sus vistas; las consultas pasan por `bi/queries.py` y la base se abre en solo lectura. `bi/control.py` es la única pieza que habla con la API de GitHub.

## 4. La carga de cada semana

[[diagrama:secuencia_carga]]

Cada paso empieza solo si el anterior terminó bien:

| Paso | Qué ocurre |
|---|---|
| 1 | A las 12:00 UTC, GitHub Actions crea una máquina nueva y recupera de su caché los CSV de los años cerrados |
| 2 | Descarga del release «base-actual» la base servida de la semana anterior y verifica su huella; de ella salen el historial de cargas y la comparación del paso 6 |
| 3 | El agente descarga de ODEPA el archivo del año en curso y los faltantes, y registra la huella SHA-256 de cada uno en `manifest.json` |
| 4 | El ETL en Python calcula los precios por su cuenta y escribe el respaldo `etl/datos.db` |
| 5 | `etl/pipeline.py` guarda las filas en el aterrizaje, las copia al bronce junto con el IPC del INE y ejecuta `dbt build`, que construye y prueba cada modelo en la base de trabajo |
| 6 | Puerta de publicación: si falla una prueba de dbt o la carga lee menos del 90 % de las filas de la última carga correcta, el proceso se detiene; si todo pasa, las tablas del panel se copian a un archivo nuevo que reemplaza a `etl/datos.duckdb`. Desde D-356 también se detiene si a una fuente le falta una semana en medio de los datos o lleva más de 2 semanas sin publicar; se publica solo hasta la última semana completa en ambas fuentes, sin rellenar, y `etl_run` guarda la semana que espera |
| 7 | pytest corre sobre la base nueva, sin las pruebas de velocidad, que solo informan (D-341), incluida la paridad entre el respaldo y DuckDB |
| 8 | La máquina reemplaza la base en el release y sube su puntero, `etl/datos.version`, a la rama `main`; el panel detecta el puntero nuevo, descarga la base y verifica su huella antes de usarla |
| 9 | Se publica el informe semanal como un issue del repositorio |

El trabajo tiene un límite de 20 minutos: si se cuelga, GitHub lo corta. La carga manual se lanza desde «Ejecutar pipeline ahora» y se sigue en una ventana que no se cierra sola: muestra cada paso con su hora y su duración, el log real de cada job al terminar, sin tokens, y deja minimizarla o cancelar la ejecución en GitHub con la misma clave que la lanza; cancelar es la única escritura del panel en GitHub (D-351).

Si un paso falla, los siguientes no corren y la base servida no cambia ([ADR-11 · Publicar solo si pasan las pruebas](ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas)). La ejecución y sus pasos se siguen en la pestaña «Operación» de [[vista:Centro de operación]].

## 5. El panel al abrirse

[[diagrama:secuencia_panel]]

Al abrirse, el panel compara su base con el puntero de la rama `main`. Si su copia es más antigua, descarga la base del release «base-actual» y la usa solo si su huella SHA-256 coincide. Después abre la base en solo lectura: ninguna página puede cambiar un dato. Si GitHub no responde, el panel sigue con la base que ya tiene.

La entrada pide la vista en cada visita y en cada recarga que hace el lector: Usuario muestra el negocio (el Panorama de precios, guiado en tres pasos, Insights y Precios e inflación); Profesional, todo el proyecto, ordenado según el perfil que elige (Data Eng, BA, BI, DevOps o Seguridad); y Autor, lo mismo más su parte, con la clave de control. La dirección nunca elige la vista; las recargas que hace la propia app (imprimir, abrir un documento, cambiar entre tema claro y oscuro) la conservan una sola vez y nunca la de Autor (D-340, D-357). El botón «Vista», debajo del logo y arriba del menú, la cambia, igual que un clic en el logo (D-373). El tema oscuro es el de entrada. Las páginas con pestañas dibujan solo la que está a la vista (D-360). Si la última carga falló, un aviso rojo arriba del menú lo dice en todas las páginas, con un enlace al paso que falló. El panel se lee en español y en inglés.

## 6. Los datos

[[diagrama:capas]]

El aterrizaje guarda las filas tal como llegan; el bronce es su copia literal en Parquet, por fuente y año; staging normaliza tipos y textos; intermedio aplica las reglas de negocio (unidades, semanas, rechazos); los marts forman el modelo estrella que lee el panel. El recorrido y el linaje están en [[vista:Pipeline y linaje]] y el modelo, en [[vista:Modelo de datos]]. Las fechas se guardan como texto ISO (`AAAA-MM-DD`).

### 6.1 Tablas de la base servida

| Tabla | Función | Contenido |
|---|---|---|
| `weekly_price` | Hechos | Un precio por semana, producto, región, canal y unidad |
| `dim_product` | Dimensión | Producto, variedad, calidad y familia |
| `dim_region` | Dimensión | Regiones con precios |
| `dim_channel` | Dimensión | Canales de venta y su fuente |
| `dim_date` | Dimensión | Una fila por semana, sin huecos |
| `latest_by_source` | Último dato | Las dos últimas semanas de cada fuente, sin el corte de la semana común (D-365) |
| `ipc_monthly` | IPC | IPC de alimentos mensual como una sola serie |
| `ipc_weekly` | IPC | Deflactor de cada semana |
| `ine_ipc_source` | IPC | Filas del IPC tal como se leyeron del INE |
| `etl_run` | Auditoría | Una fila por carga publicada |
| `rejection` | Auditoría | Filas rechazadas por la última carga, con su motivo |
| `dbt_node` | Linaje | Modelos, fuentes y pruebas del último `dbt build` |
| `dbt_result` | Linaje | Resultado de cada modelo y prueba del último `dbt build` |

### 6.2 Hechos y dimensiones

### weekly_price

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `week_start` | VARCHAR | FK → `dim_date` | Lunes de la semana |
| `product_id` | BIGINT | FK → `dim_product` | Producto, variedad y calidad |
| `region_id` | INTEGER | FK → `dim_region` | Región |
| `channel_id` | BIGINT | FK → `dim_channel` | Canal de venta |
| `normalized_unit` | VARCHAR | | Unidad normalizada: `kilo`, `litro` o `unidad`; vacía si no se puede convertir |
| `price` | DOUBLE | | Precio semanal en pesos nominales, por unidad normalizada; vacío cuando la unidad no se puede convertir (marca `UNIDAD_NO_CONVERTIBLE`) |
| `volume` | DOUBLE | | Volumen informado por la fuente, cuando existe |
| `observation_count` | BIGINT | | Número de cotizaciones que forman el precio de la semana |
| `flag` | VARCHAR | | Vacía si el precio entra en los indicadores; `ATIPICO` o `UNIDAD_NO_CONVERTIBLE` si queda fuera de ellos |

### dim_product

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `product_id` | BIGINT | PK | Identificador del producto |
| `product_group` | VARCHAR | | Familia de alimentos |
| `product` | VARCHAR | | Producto |
| `variety` | VARCHAR | | Variedad |
| `quality` | VARCHAR | | Calidad |

### dim_region

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `region_id` | INTEGER | PK | Identificador de la región |
| `region` | VARCHAR | | Nombre de la región |

### dim_channel

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `channel_id` | BIGINT | PK | Identificador del canal |
| `channel` | VARCHAR | | Canal de venta, por ejemplo «Supermercado» o «Feria libre» |
| `source` | VARCHAR | | Fuente de ODEPA: `wholesale` (mayorista) o `consumer` (consumidor) |

### dim_date

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `week_start` | VARCHAR | PK | Lunes de la semana |
| `iso_year` | BIGINT | | Año ISO de la semana |
| `iso_week` | BIGINT | | Número de semana ISO |
| `month` | BIGINT | | Mes del lunes |
| `month_name` | VARCHAR | | Nombre del mes |
| `year` | BIGINT | | Año del lunes |
| `season` | VARCHAR | | Estación en Chile: `verano`, `otoño`, `invierno` o `primavera` |

### latest_by_source

Las dos últimas semanas de cada fuente, sin el corte de D-356: la lee solo la página «Último dato por canal». El Panorama y los indicadores leen `weekly_price`.

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `week_start` | VARCHAR |  | Lunes de la semana; dos semanas por fuente |
| `source` | VARCHAR |  | Fuente: `wholesale` (mayorista) o `consumer` (consumidor) |
| `channel` | VARCHAR |  | Canal de venta |
| `region_id` | INTEGER | FK → `dim_region` | Región |
| `region` | VARCHAR |  | Nombre de la región |
| `product_group` | VARCHAR |  | Familia |
| `product` | VARCHAR |  | Producto |
| `variety` | VARCHAR |  | Variedad |
| `quality` | VARCHAR |  | Calidad |
| `normalized_unit` | VARCHAR |  | Unidad normalizada; vacía si no se puede convertir |
| `price` | DOUBLE |  | Precio semanal en pesos nominales, por unidad normalizada |
| `observation_count` | BIGINT |  | Número de cotizaciones de la semana |
| `flag` | VARCHAR |  | Vacía si el precio entra al cálculo; `ATIPICO` o `UNIDAD_NO_CONVERTIBLE` si queda fuera |

### 6.3 IPC

**Precios reales.** Cada semana toma el IPC de alimentos del mes de su lunes; los precios reales quedan en pesos del último mes publicado ([ADR-33 · Calcular precios reales con el IPC de alimentos del INE](ADR.md#adr-33--calcular-precios-reales-con-el-ipc-de-alimentos-del-ine)).

### ipc_monthly

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `year` | INTEGER | PK (con `month`) | Año |
| `month` | INTEGER | PK (con `year`) | Mes |
| `food_index` | DOUBLE | | IPC de alimentos, base 2023 = 100 |
| `origin` | VARCHAR | | Serie de origen: la base 2023 o la serie empalmada, enlazada en enero de 2024 |

### ipc_weekly

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `week_start` | VARCHAR | PK, FK → `dim_date` | Lunes de la semana |
| `ipc_year` | INTEGER | | Año del IPC usado para esa semana |
| `ipc_month` | INTEGER | | Mes del IPC usado para esa semana |
| `food_index` | DOUBLE | | IPC de alimentos de ese mes |
| `reference_year` | INTEGER | | Año del último mes publicado, al que se llevan los precios |
| `reference_month` | INTEGER | | Último mes publicado |
| `real_factor` | DOUBLE | | Factor que convierte un precio nominal de la semana en pesos del mes de referencia |
| `provisional` | BOOLEAN | | Verdadero si la semana es posterior al último mes publicado |

### ine_ipc_source

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `file` | VARCHAR | | Archivo del INE de origen |
| `year` | VARCHAR | | Año, como lo publica el INE |
| `month` | VARCHAR | | Mes, como lo publica el INE |
| `index_value` | VARCHAR | | Valor del índice, como lo publica el INE |
| `monthly_change` | VARCHAR | | Variación mensual, como la publica el INE |

### 6.4 Auditoría y linaje

### etl_run

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `run_id` | INTEGER | PK | Número de la carga |
| `started_at` | VARCHAR | | Inicio de la carga, en UTC |
| `status` | VARCHAR | | Estado: `LOADED` para una carga publicada |
| `rows_read` | INTEGER | | Filas leídas de ODEPA |
| `rows_loaded` | INTEGER | | Filas cargadas |
| `rows_rejected` | INTEGER | | Filas rechazadas; leídas = cargadas + rechazadas |
| `message` | VARCHAR | | Mensaje de la carga, si lo hay |

### rejection

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `run_id` | INTEGER | FK → `etl_run` | Carga que rechazó la fila |
| `source` | VARCHAR | | Fuente: `wholesale` o `consumer` |
| `reason` | VARCHAR | | Motivo del rechazo, por ejemplo `NON_POSITIVE_PRICE` (precio cero o negativo) |
| `original_row` | JSON | | La fila tal como llegó |

### dbt_node

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `unique_id` | VARCHAR | PK | Identificador del nodo en dbt |
| `name` | VARCHAR | | Nombre del modelo, la fuente o la prueba |
| `resource_type` | VARCHAR | | `model`, `source` o `test` |
| `layer` | VARCHAR | | Capa: `bronze`, `staging`, `intermediate` o `marts`; vacía para las pruebas |
| `materialized` | VARCHAR | | Cómo se materializa el modelo |
| `depends_on` | VARCHAR | | Nodos de los que depende |
| `test_type` | VARCHAR | | Tipo de prueba, para las pruebas |
| `column_name` | VARCHAR | | Columna que prueba, si aplica |
| `description` | VARCHAR | | Descripción del nodo en el proyecto dbt |

### dbt_result

| Columna | Tipo | Clave | Descripción |
|---|---|---|---|
| `unique_id` | VARCHAR | FK → `dbt_node` | Nodo ejecutado |
| `status` | VARCHAR | | Resultado: `success` para un modelo construido, `pass` para una prueba superada |
| `execution_time` | DOUBLE | | Duración en segundos |
| `failures` | INTEGER | | Filas que no cumplen la prueba |
| `generated_at` | VARCHAR | | Fecha del `dbt build` |

**Semanas que esperan.** Cuando una fuente ya publicó una semana y la otra no, esa semana no entra a la base: espera a la otra fuente, sin rellenar nada. La línea de `etl_run` de esa carga lo dice (`SOURCE_LATE: wholesale 2026-10-19`) y el Panorama muestra «ODEPA aún no publica la semana del 19-10 (mayorista)» (D-356).

## 7. Despliegue

[[diagrama:despliegue]]

| Pieza | Dónde corre | Detalle |
|---|---|---|
| Carga semanal y pruebas de cada cambio | Máquinas de GitHub Actions (Ubuntu, Python 3.11) | Se crean y se descartan en cada ejecución; los CSV de años cerrados quedan en la caché de Actions |
| Código y puntero de la base | Repositorio de GitHub, rama `main` | |
| Base servida | Release «base-actual» del repositorio | Una sola copia, reemplazada por cada carga |
| Panel | Streamlit Community Cloud, desde `main` | Guarda los secretos: el token de GitHub y la clave de control |
| Aterrizaje (`etl/raw.db`) | Computador del autor y máquina de cada carga | No se versiona |

El diagrama con el estado en vivo de cada pieza está en la pestaña «Despliegue» de [[vista:Centro de operación]]; el camino de un cambio hasta producción, en su pestaña «CI/CD».

## 8. Calidad, seguridad y observabilidad

**Calidad.** Tres puertas: el archivo (¿llegó completo y al día?), cada fila (¿es válida?) y la base (¿es coherente y pasó sus pruebas?). Once indicadores, en cinco dimensiones, se miden en cada carga contra su umbral; la exactitud, la sexta dimensión, se mide con cuatro controles que comparan las cifras con la fuente. El detalle está en [[vista:Calidad y auditoría]].

**Observabilidad.** Cada carga deja rastro en cuatro lugares: `etl_run` (filas leídas, cargadas y rechazadas de cada carga publicada), `dbt_result` (el resultado de cada modelo y prueba), el registro de GitHub Actions (cada paso, incluidos los que fallan) y el correo que GitHub envía al autor si la carga falla. La pestaña «Monitoreo» de [[vista:Centro de operación]] los reúne.

**Calidad del proyecto.** Cómo se mide la calidad de los datos y del código, quién decide y qué pasa cuando algo falla está en el [Plan de calidad del software (SQAP)](PLAN_DE_CALIDAD.md). En cada push el workflow de calidad mide y falla si un indicador de código pasa su aceptable; el informe numerado se propone solo después de la carga semanal o a mano (D-363). Si el último informe tiene más de 8 días, la alerta del autor lo dice y no lo muestra como el estado de hoy (D-361). Cada falla vivida queda en el registro de fallas, una línea por campo (D-342, D-354).

**Secretos y acceso.** El panel usa tres secretos, guardados en Streamlit y nunca en el repositorio: `CONTROL_CODE` (la clave del autor, comparada en tiempo constante), `GITHUB_TOKEN` (lanza y cancela la carga manual) y `GITHUB_READ_TOKEN` (solo lectura, para la página «GitHub Actions»; si falta, se usa `GITHUB_TOKEN`). Esa página, que solo ve el autor, muestra las últimas ejecuciones y, del último fallo, el job, el paso, las pruebas que fallan y las últimas 60 líneas del log, con un botón «Copiar» y enlaces a la ejecución y al job; el token nunca aparece en pantalla (D-339, D-359).

**Seguridad.** Las amenazas, sus controles y las pruebas que los verifican están en [[vista:Arquitectura de seguridad]]; el procedimiento de verificación, en el [Plan de pruebas y seguridad](PLAN_PRUEBAS.md).

**Requisitos de calidad**

| Atributo | Escenario | Respuesta esperada |
|---|---|---|
| Exactitud | Una regla de negocio cambia por error | La paridad con el respaldo o la reconstrucción desde filas crudas falla en pytest y la carga no se publica |
| Confiabilidad | ODEPA publica un archivo truncado | La carga lee menos del 90 % de la anterior y se detiene; el panel conserva la última base válida |
| Disponibilidad | GitHub no responde al abrir el panel | El panel conserva la base que ya tiene y lo informa si no tiene ninguna |
| Seguridad | Un visitante intenta leer archivos del servidor con SQL | La consulta se rechaza y el motor no tiene acceso a archivos ni a la red |
| Usabilidad | Una pantalla de 1440 × 900 | Cada página principal se ve entera en la ventana del navegador (1440 × 790) |

## 9. Capacidad y crecimiento

### 9.1 Capacidad actual

| Medida | Valor | Origen |
|---|---|---|
| Base servida | Unos 14 MB en la base servida | Tamaño de `etl/datos.duckdb` |
| Datos | Volumen y cobertura de la última carga | [PRD, sección 6](PRD.md#6-alcance) |
| Frecuencia | Una carga por semana | [RF-01](PRD.md#5-requisitos) |
| Usuarios | Un panel público de solo lectura | [PRD, sección 3](PRD.md#3-para-quién-es) |

### 9.2 Qué cede primero

| Límite | Situación actual | Respuesta prevista |
|---|---|---|
| Tamaño de la base servida | Una sola copia en un release, reemplazada por cada carga ([ADR-35](ADR.md#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza)); el historial de Git ya no crece con los datos | Un archivo de release admite hasta 2 GB; mucho antes convendría la opción de la sección 9.4 |
| Duración de la carga | Cada carga rehace la historia completa desde 2022 ([ADR-10](ADR.md#adr-10--reconstruir-todo-en-cada-carga)) y tarda un poco más cada año | Cargas incrementales cuando la duración lo justifique |
| Visitantes simultáneos | Una aplicación gratuita de Streamlit que lee un archivo pequeño en solo lectura | Si varios equipos lo usaran a diario, el plan gratuito sería insuficiente: es uno de los umbrales de la sección 9.4 |

### 9.3 Opciones de crecimiento

Una fuente nueva se incorpora como las actuales: una carpeta en el bronce y sus modelos de dbt, sin modificar los existentes.

| Extensión | Estado | Cómo se incorporaría |
|---|---|---|
| Clima por región y semana | Prevista; fuente oficial por definir | Un staging y un mart por semana y región, junto a las alertas de precio, sin afirmar que el clima cause un precio |
| Data warehouse en la nube | No adoptado ([ADR-31](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube)) | Un destino nuevo en la configuración de dbt, con los mismos modelos y la misma auditoría |

### 9.4 Cuándo se justificaría una nube

Con datos públicos, semanales y pequeños, leídos por un solo panel, un data warehouse en la nube agregaría costo, secretos y riesgos de vencimiento sin beneficio ([ADR-31](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube)). Se justificaría si una empresa sumara sus propios datos:

| Criterio | Hoy | Umbral |
|---|---|---|
| Volumen | Unos 14 MB | Varios GB: ventas por tienda y día, costos, inventario |
| Usuarios | Un panel de solo lectura | Varios equipos o herramientas de BI sobre los mismos datos |
| Acceso | Público | Permisos por persona o datos sensibles |
| Frescura | Semanal | Varias cargas al día o tiempo real |

## 10. Restricciones y decisiones

| Restricción | Origen |
|---|---|
| Solo servicios gratuitos sin vencimiento | [ADR-02 · Orquestar con GitHub Actions y publicar en Streamlit Community Cloud](ADR.md#adr-02--orquestar-con-github-actions-y-publicar-en-streamlit-community-cloud) y [ADR-31 · No usar un data warehouse en la nube](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube) |
| Solo fuentes oficiales y abiertas | [ADR-01 · Usar solo los archivos oficiales de ODEPA y del INE](ADR.md#adr-01--usar-solo-los-archivos-oficiales-de-odepa-y-del-ine) |
| Ninguna cifra se inventa ni se interpola, y el histórico no se borra | Regla del proyecto |
| Python 3.11 o 3.12 para el pipeline con dbt | Compatibilidad de dbt Core |
| Repositorio público | Portafolio abierto; la seguridad depende de los secretos, no del código oculto |

**Estrategia de solución**

| Principio | Cómo se aplica | Decisión |
|---|---|---|
| Rehacer todo en cada carga | Cada martes se recalcula la historia completa desde los archivos oficiales; repetir una carga nunca duplica datos | [ADR-10](ADR.md#adr-10--reconstruir-todo-en-cada-carga) |
| Publicar solo lo validado | La base servida cambia solo si pasan todas las pruebas | [ADR-11](ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas) |
| Comprobar por un segundo camino | Un ETL en Python, independiente de dbt, calcula los mismos precios | [ADR-34](ADR.md#adr-34--separar-la-base-de-trabajo-de-dbt-la-base-que-lee-el-panel-y-el-respaldo) |
| Capas declarativas y probadas | Bronce en Parquet; staging, intermedio y marts en dbt Core sobre DuckDB | [ADR-30](ADR.md#adr-30--parquet-dbt-core-y-duckdb) |
| Bloquear solo lo que importa | Las pruebas que protegen los datos detienen la carga; las de velocidad solo informan y corren en local | D-341 |
| Una sola copia publicada | La base servida vive en un release que cada carga reemplaza | [ADR-35](ADR.md#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza) |

Las decisiones que dan forma a esta arquitectura, con su contexto, sus alternativas y sus consecuencias, están en los [Registros de decisiones de arquitectura (ADR)](ADR.md).

## 11. Riesgos y deuda técnica

| Riesgo o deuda | Efecto | Mitigación actual |
|---|---|---|
| ODEPA cambia el formato de sus archivos | Una carga mal leída | La puerta de publicación la rechaza y el panel conserva la última carga válida |
| Una dependencia cambia sin aviso | Una carga lenta o rota sin cambios en el código; ocurrió con DuckDB 2 (D-227, DuckDB con versión máxima) y con certifi, que retiró la raíz del certificado de ODEPA (D-164, raíz emSign en el agente) | DuckDB tiene versión máxima en `requirements.txt`; la raíz de ODEPA viaja con el agente, sin desactivar la verificación |
| No se puede descargar la base del release | El panel no obtiene la base de la última carga | El panel conserva la base que ya tiene; la carga semanal se detiene antes de construir |
| Cambian las condiciones de los planes gratuitos | Habría que mover la carga o el panel | El pipeline corre en cualquier máquina con Python 3.11 o 3.12 |
| Vistas antiguas en `bi/dashboard.py` | Código que solo se alcanza por direcciones antiguas y que lee `docs/DISENO.md` | Pendiente de retiro |
| Versiones anteriores de la base en el historial de Git | El repositorio pesaba 309 MB el 24-10-2026; desde ADR-35 la base ya no se agrega al historial | Se conservan; borrarlas exigiría reescribir el historial |

## 12. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 13. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 18-10-2026 | Primera versión (D-151, documentación en tres documentos) |
| 1.1 | 19-10-2026 | Arquitectura con dbt, DuckDB y Parquet (D-152, D-154); justificación de cada herramienta |
| 1.2 | 20-10-2026 | Seguridad corregida (D-200); diagramas propios (D-205); cifras de la semana del 12-10-2026 |
| 1.3 | 21-10-2026 | Redacción de documento de ingeniería (D-210, D-214, D-217); IPC directo a Parquet (D-218) |
| 1.4 | 23-10-2026 | Diagrama de contexto (D-242); vistas C4 sin copiar diagramas (D-247); descarga como página impresa (D-248); seguridad como proceso (D-249) |
| 1.5 | 24-10-2026 | Principios, vista de ejecución, calidad y observabilidad, riesgos (D-269); base servida en un release (D-270) |
| 2.0 | 25-10-2026 | Estructura arc42 completa: restricciones, estrategia de solución, conceptos transversales, requisitos de calidad, deuda técnica, glosario e historial (D-279, documentación profesional) |
| 3.0 | 25-10-2026 | De lo más importante a lo menos: resumen, contexto, contenedores, la carga y el panel en secuencia, los datos con su diccionario, despliegue, calidad y seguridad, capacidad y crecimiento (antes en documentos propios); seis diagramas (D-290, documentos para todo lector) |
| 3.1 | 26-10-2026 | Escenarios clave y componentes de la carga y del panel (C4, nivel 3); las vistas, el Dashboard y el aviso de carga fallida en el panel (D-300) |
| 3.2 | 30-10-2026 | Fuentes retrasadas y límite de tiempo de la carga; las tres vistas, las recargas propias y las pestañas que dibujan solo la visible; calidad del proyecto, secretos y la página «GitHub Actions» (D-339 a D-363) |
