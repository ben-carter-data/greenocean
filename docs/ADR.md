# Registros de decisiones de arquitectura (ADR)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Registros de decisiones de arquitectura (ADR), formato MADR |
| Versión | 3.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Explicar las once decisiones que más pesan en la arquitectura de GreenOcean: por qué se tomaron, qué alternativas había y qué consecuencias tienen. |
| Audiencia | Arquitectura, ingeniería, gerencia y revisión técnica. |
| Documentos relacionados | [Documento de arquitectura de software (SAD)](SAD.md) · [Índice de decisiones](INDICE_DECISIONES.md) · [Glosario](GLOSARIO.md) |

Cada registro conserva su número original, por eso la numeración no es correlativa. Las decisiones menores están en el [Índice de decisiones](INDICE_DECISIONES.md) y en el registro completo, `docs/DECISIONES.md`. Las opciones consideradas son solo las que constan en ese registro o en el historial del repositorio.

## Índice

| Decisión | Registro | Estado | Fecha |
|---|---|---|---|
| [Usar solo los archivos oficiales de ODEPA y del INE](#adr-01--usar-solo-los-archivos-oficiales-de-odepa-y-del-ine) | ADR-01 | Aceptada | 11-10-2026 |
| [Orquestar con GitHub Actions y publicar en Streamlit Community Cloud](#adr-02--orquestar-con-github-actions-y-publicar-en-streamlit-community-cloud) | ADR-02 | Aceptada | 11-10-2026 |
| [No subir los datos crudos al repositorio](#adr-04--no-subir-los-datos-crudos-al-repositorio) | ADR-04 | Aceptada, modificada por ADR-35 | 11-10-2026 |
| [Reconstruir todo en cada carga](#adr-10--reconstruir-todo-en-cada-carga) | ADR-10 | Aceptada | 11-10-2026 |
| [Publicar solo si pasan las pruebas](#adr-11--publicar-solo-si-pasan-las-pruebas) | ADR-11 | Aceptada | 11-10-2026 |
| [Modelo estrella con una dimensión de fechas sin huecos](#adr-19--modelo-estrella-con-una-dimensión-de-fechas-sin-huecos) | ADR-19 | Aceptada | 11-10-2026 |
| [Parquet, dbt Core y DuckDB](#adr-30--parquet-dbt-core-y-duckdb) | ADR-30 | Aceptada | 19-10-2026 |
| [No usar un data warehouse en la nube](#adr-31--no-usar-un-data-warehouse-en-la-nube) | ADR-31 | Aceptada | 19-10-2026 |
| [Calcular precios reales con el IPC de alimentos del INE](#adr-33--calcular-precios-reales-con-el-ipc-de-alimentos-del-ine) | ADR-33 | Aceptada | 19-10-2026 |
| [Separar la base de trabajo de dbt, la base que lee el panel y el respaldo](#adr-34--separar-la-base-de-trabajo-de-dbt-la-base-que-lee-el-panel-y-el-respaldo) | ADR-34 | Aceptada | 19-10-2026 |
| [Publicar la base servida en un release que cada carga reemplaza](#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza) | ADR-35 | Aceptada | 24-10-2026 |

## En resumen

Cada decisión de este documento responde a una pregunta concreta: de dónde salen los datos, cómo se cargan, cómo se guardan, cuándo se publican y cuánto cuesta. Tres ideas las unen:

- **Solo datos oficiales, recalculados desde cero.** Nada se interpola y repetir una carga nunca duplica datos.
- **Nada se publica sin pruebas.** Una carga con errores se detiene antes de llegar al panel.
- **Costo cero y sin vencimientos.** Servicios gratuitos permanentes y una sola copia publicada de la base.

[[diagrama:mapa_adr]]

[[diagrama:tiempo_adr]]

## ADR-01 · Usar solo los archivos oficiales de ODEPA y del INE

- **Estado:** aceptada (D-001, fuentes oficiales).
- **Fecha:** 11-10-2026.
- **Contexto:** los precios que el proyecto necesita ya se publican como archivos CSV en portales de datos abiertos, con licencias que permiten reutilizarlos.
- **Decisión:** descargar los CSV oficiales de ODEPA (precios) y del INE (IPC de alimentos), sin modificar ningún valor.
- **Opciones consideradas:** extraer precios de sitios de supermercados (*scraping*); registros públicos de salud.
- **Consecuencias:** la fuente es estable, verificable e independiente del diseño de una página web. No se pueden comparar cadenas de supermercados, porque no existe una fuente oficial para ello.

## ADR-02 · Orquestar con GitHub Actions y publicar en Streamlit Community Cloud

- **Estado:** aceptada (D-012, orquestación y publicación).
- **Fecha:** 11-10-2026.
- **Contexto:** un proyecto público, con una carga semanal y un panel de solo lectura, sin costo ni servidores que mantener.
- **Decisión:** GitHub Actions ejecuta la carga semanal y las pruebas de cada cambio; Streamlit Community Cloud publica el panel desde la rama `main`.
- **Opciones consideradas:** un servidor propio; Power BI, que exige licencia para compartir un panel.
- **Consecuencias:** el panel se abre desde un enlace público y el proyecto se puede clonar. La concurrencia y el volumen quedan limitados por los planes gratuitos, suficientes para datos semanales de este tamaño.

## ADR-04 · No subir los datos crudos al repositorio

- **Estado:** aceptada (D-020, datos crudos fuera del repositorio); la base servida y el respaldo salieron del repositorio en D-270 ([ADR-35](#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza)).
- **Fecha:** 11-10-2026.
- **Contexto:** cada CSV anual de ODEPA pesa hasta unos 65 MB y la base cruda de todos los años, cientos de MB. GitHub rechaza archivos de más de 100 MB y el repositorio crecería con cada carga.
- **Decisión:** los CSV y la base de aterrizaje (`etl/raw.db`) se reconstruyen en cada carga y quedan fuera del repositorio. Se versiona el registro de descargas (`manifest.json`), con la huella SHA-256 de cada archivo.
- **Opciones consideradas:** versionar todos los datos; usar almacenamiento de archivos grandes.
- **Consecuencias:** el repositorio no carga con los datos crudos y cada archivo descargado se puede verificar contra su huella. Una copia nueva del proyecto debe ejecutar el agente para obtener los datos crudos; la base de los indicadores se descarga con un comando ([ADR-35](#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza)).

## ADR-10 · Reconstruir todo en cada carga

- **Estado:** aceptada (D-024, reconstrucción completa).
- **Fecha:** 11-10-2026.
- **Contexto:** la base cruda ya se rehace en cada carga, y una semana que cruza dos años reúne filas de dos archivos.
- **Decisión:** cada carga recalcula todos los precios semanales desde las filas crudas, en lugar de agregar solo la semana nueva.
- **Opciones consideradas:** cargas incrementales, semana a semana, con claves.
- **Consecuencias:** repetir una carga nunca duplica filas y el cambio de año no requiere lógica especial. La tabla de rechazos guarda solo los de la última carga; de las anteriores queda su número en `etl_run`. La duración de la carga crece con cada año de datos.

## ADR-11 · Publicar solo si pasan las pruebas

- **Estado:** aceptada (D-029, umbral de filas; D-154, construcción con dbt).
- **Fecha:** 11-10-2026.
- **Contexto:** un archivo truncado o una regla rota no deben llegar nunca al panel.
- **Decisión:** la base servida se reemplaza solo si pasan todas las pruebas de dbt, si la carga lee al menos el 90 % de las filas de la última carga correcta y si pytest pasa sobre la base nueva. Si algo falla, el workflow se detiene antes de publicar, GitHub Actions marca la ejecución como fallida y avisa al autor por correo.
- **Opciones consideradas:** límites fijos de filas por semana.
- **Consecuencias:** el panel siempre muestra la última carga válida. `etl_run` guarda solo las cargas publicadas; las fallidas quedan en el historial de GitHub Actions, visible en «Centro de operación». La primera carga no tiene con qué compararse, y un archivo duplicado no se detecta por conteo: lo detectan las pruebas de unicidad.

## ADR-19 · Modelo estrella con una dimensión de fechas sin huecos

- **Estado:** aceptada (D-023, modelo estrella; D-095, dimensión de fechas).
- **Fecha:** 11-10-2026.
- **Contexto:** comparar un precio con la misma época de otros años exige conocer, para cada semana, su semana ISO, su mes y su estación, aunque esa semana no tenga precios.
- **Decisión:** un modelo estrella con `weekly_price` al centro y las dimensiones de producto, región, canal y fecha; `dim_date` tiene una fila por semana, sin huecos, desde la primera hasta la última.
- **Opciones consideradas:** no se registraron opciones alternativas cuando se tomó la decisión.
- **Consecuencias:** los cálculos por época y el IPC semanal se unen por `week_start` con una clave foránea real. Las tablas y columnas están en inglés, de modo que el modelo no coincide literalmente con los nombres del diseño original.

## ADR-30 · Parquet, dbt Core y DuckDB

- **Estado:** aceptada (D-154, data warehouse con dbt Core y DuckDB).
- **Fecha:** 19-10-2026.
- **Contexto:** las reglas de negocio estaban en un ETL en Python sin capas ni pruebas declarativas, y el proyecto debía seguir siendo gratuito y portable.
- **Decisión:** el bronce en Parquet, las transformaciones y sus pruebas en dbt Core (staging, intermedio y marts) y DuckDB como motor.
- **Opciones consideradas:** BigQuery en modo *sandbox*, cuyas tablas vencen a los 60 días; Snowflake y Redshift, disponibles solo en periodos de prueba; Databricks, sobredimensionado para este volumen; PostgreSQL gratuito, con planes que pausan los proyectos inactivos (registradas el 19-10-2026, en la evolución prevista del stack, D-152).
- **Consecuencias:** cada capa tiene sus pruebas y el motor se puede cambiar desde la configuración de dbt. El ETL en Python se conserva como respaldo independiente para comprobar la paridad.

## ADR-31 · No usar un data warehouse en la nube

- **Estado:** aceptada (D-152, evolución prevista del stack).
- **Fecha:** 19-10-2026.
- **Contexto:** datos públicos, semanales y de pocos megabytes, leídos por un solo panel.
- **Decisión:** la base servida es un archivo DuckDB; no hay un data warehouse en la nube.
- **Opciones consideradas:** BigQuery como segundo destino de dbt, declarado como opción y nunca como dependencia del panel.
- **Consecuencias:** no hay costo, secretos de nube ni vencimientos. Se reconsideraría solo si una empresa sumara sus propios datos; los umbrales están en el [SAD, capacidad y crecimiento](SAD.md#9-capacidad-y-crecimiento).

## ADR-33 · Calcular precios reales con el IPC de alimentos del INE

- **Estado:** aceptada (D-155, precios reales con el IPC).
- **Fecha:** 19-10-2026.
- **Contexto:** sin descontar la inflación, un precio actual parece alto solo porque todo subió.
- **Decisión:** usar la división «Alimentos y bebidas no alcohólicas» del IPC del INE, enlazando sus dos series con la variación oficial de enero de 2024; cada semana toma el IPC del mes de su lunes.
- **Opciones consideradas:** unir las dos series del INE sin enlazarlas, lo que produce un salto falso de −33,7 %.
- **Consecuencias:** los precios reales quedan en pesos del último mes publicado. Una semana de un mes aún no publicado usa ese último mes y queda marcada como provisional; nunca se estima un índice.

## ADR-34 · Separar la base de trabajo de dbt, la base que lee el panel y el respaldo

- **Estado:** aceptada (D-154, data warehouse con dbt Core y DuckDB).
- **Fecha:** 19-10-2026.
- **Contexto:** el panel no debe leer nunca una base a medio construir.
- **Decisión:** dbt construye en una base de trabajo que no se versiona (`etl/warehouse_build.duckdb`); al final de una carga válida, las tablas del panel se copian a un archivo nuevo y compacto que reemplaza de una vez a `etl/datos.duckdb`. El ETL en Python escribe aparte el respaldo `etl/datos.db`.
- **Opciones consideradas:** que el panel lea directamente la base de trabajo de dbt.
- **Consecuencias:** el panel lee un archivo liviano y siempre completo, y el respaldo permite comprobar que dos caminos independientes producen las mismas cifras.

## ADR-35 · Publicar la base servida en un release que cada carga reemplaza

- **Estado:** aceptada (D-270, base servida en un release).
- **Fecha:** 24-10-2026.
- **Contexto:** cada carga subía con un commit la base servida y el respaldo, unos 48 MB. Git conserva cada versión de un archivo: el historial crecía cerca de 1 GB por año con copias que nadie consulta, porque cada base nueva ya contiene la historia completa ([ADR-10](#adr-10--reconstruir-todo-en-cada-carga)). Medidas del 24-10-2026.

[[diagrama:antes_despues]]

- **Decisión:** la base servida se publica como archivo del release «base-actual» de GitHub, reemplazado por cada carga. En Git queda solo su puntero, `etl/datos.version`, con la huella SHA-256, el tamaño y la fecha de la base publicada. El panel, las pruebas de cada push y una copia nueva del proyecto descargan el archivo cuando falta o es más antiguo, y lo usan solo si su huella coincide. El respaldo SQLite se rehace en la máquina de cada carga, donde corre la prueba de paridad, y no se publica.
- **Opciones consideradas:** dejar de versionar solo el respaldo, lo que reducía el crecimiento a unos 300 MB por año sin detenerlo; almacenamiento de archivos grandes (Git LFS), que también conserva cada versión y tiene una cuota gratuita limitada; reescribir el historial periódicamente, lo que invalida las copias ya clonadas.
- **Consecuencias:** el historial deja de crecer con los datos y existe una sola copia publicada. El panel depende de poder descargar la base al arrancar; si no puede, conserva la que tiene. Las versiones anteriores siguen en el historial. Una reconstrucción local más nueva que el puntero se conserva.

## Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 18-10-2026 | Primera versión (D-151, documentación en tres documentos) |
| 1.1 | 19-10-2026 | Decisiones de dbt, DuckDB, Parquet e IPC (D-152, D-154) |
| 1.2 | 20-10-2026 | Cifras alineadas con la base de la semana del 12-10-2026 |
| 1.3 | 21-10-2026 | Redacción de documento de ingeniería (D-210, D-214, D-218) |
| 1.4 | 23-10-2026 | Las diez decisiones con sus partes estándar (D-248) |
| 1.5 | 24-10-2026 | ADR-11 corregido y alternativas de ADR-19 (D-269); ADR-35 (D-270) |
| 2.0 | 25-10-2026 | Formato MADR con fecha y opciones consideradas, índice al inicio, opciones de ADR-30 completadas desde el historial, ADR-19 sin alternativas no registradas (D-279, documentación profesional) |
| 3.0 | 25-10-2026 | Resumen en lenguaje simple, mapa de dónde actúa cada decisión, línea de tiempo y el antes y después del ADR-35; índice por el nombre de cada decisión (D-290, documentos para todo lector) |
