# Índice de decisiones

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Índice de decisiones |
| Versión | 1.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Reunir, por tema, las decisiones que cambian la arquitectura, los datos, la seguridad o la operación. |
| Audiencia | Arquitectura, gerencia y revisión técnica. |
| Documentos relacionados | [Registros de decisiones de arquitectura (ADR)](ADR.md) · [Documento de arquitectura de software (SAD)](SAD.md) · [Glosario](GLOSARIO.md) |

El registro completo, con todas las decisiones en orden cronológico, es `docs/DECISIONES.md`. Este índice reúne solo las que cambian la arquitectura, los datos, la seguridad o la operación; las decisiones de arquitectura de mayor peso tienen además su registro en el [ADR](ADR.md).

## Índice

1. [Fuentes e ingesta](#1-fuentes-e-ingesta)
2. [Modelo y reglas de datos](#2-modelo-y-reglas-de-datos)
3. [Pipeline y publicación](#3-pipeline-y-publicación)
4. [Calidad y auditoría](#4-calidad-y-auditoría)
5. [Seguridad](#5-seguridad)
6. [Operación y observabilidad](#6-operación-y-observabilidad)
7. [Panel](#7-panel)
8. [Documentación](#8-documentación)
9. [Historial de versiones](#9-historial-de-versiones)

## 1. Fuentes e ingesta

| Decisión | Título | ADR |
|---|---|---|
| D-001 | Descargar archivos oficiales en vez de hacer scraping | [ADR-01](ADR.md#adr-01--usar-solo-los-archivos-oficiales-de-odepa-y-del-ine) |
| D-002 | Dos fuentes en la etapa 1 | — |
| D-007 | Clave exacta producto + variedad + calidad | — |
| D-020 | Los datos crudos no se suben al repositorio | [ADR-04](ADR.md#adr-04--no-subir-los-datos-crudos-al-repositorio) |
| D-042 | La semana del 02-05-2022 falta en la fuente y se registra como hueco conocido | — |
| D-047 | Los archivos de años cerrados se guardan en la caché de GitHub Actions | — |
| D-164 | La descarga de ODEPA confía en la raíz emSign que certifi retiró | — |

## 2. Modelo y reglas de datos

| Decisión | Título | ADR |
|---|---|---|
| D-006 | Cruce por semana | — |
| D-008 | Unidades no convertibles se conservan sin margen | — |
| D-023 | Tablas y columnas en inglés; un esquema por base | [ADR-19](ADR.md#adr-19--modelo-estrella-con-una-dimensión-de-fechas-sin-huecos) |
| D-024 | Los precios semanales se reconstruyen completos en cada ejecución | [ADR-10](ADR.md#adr-10--reconstruir-todo-en-cada-carga) |
| D-026 | Conversión de unidades por lectura literal del texto | — |
| D-028 | RN-12: mediana por producto, unidad, semana y fuente, con factor 5 | — |
| D-095 | Dimensión de fechas dim_date | [ADR-19](ADR.md#adr-19--modelo-estrella-con-una-dimensión-de-fechas-sin-huecos) |
| D-144 | Auditoría de datos y variación nacional sobre las mismas regiones | — |
| D-145 | Las alertas K6 miden el cambio sobre las mismas regiones | — |
| D-146 | Revisión de pertinencia: solo conclusiones que se sostienen | — |
| D-153 | Auditoría entre páginas: un solo precio por producto y semana | — |
| D-155 | Precios reales con el IPC de alimentos del INE | [ADR-33](ADR.md#adr-33--calcular-precios-reales-con-el-ipc-de-alimentos-del-ine) |
| D-158 | Una alerta necesita al menos dos cotizaciones en cada semana | — |

## 3. Pipeline y publicación

| Decisión | Título | ADR |
|---|---|---|
| D-012 | SQLite, GitHub Actions y Streamlit Community Cloud | [ADR-02](ADR.md#adr-02--orquestar-con-github-actions-y-publicar-en-streamlit-community-cloud) |
| D-029 | Controles de calidad antes de cargar | [ADR-11](ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas) |
| D-034 | Job semanal: nada se guarda si un paso falla | — |
| D-152 | Evolución prevista: dbt, DuckDB, Parquet, IPC y clima; la nube solo con datos de empresa | [ADR-31](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube) |
| D-154 | El data warehouse pasa a dbt Core, DuckDB y Parquet, con paridad exacta | [ADR-30](ADR.md#adr-30--parquet-dbt-core-y-duckdb) |
| D-194 | Paridad sin ambigüedad y el IPC que no pasa por SQLite | — |
| D-227 | DuckDB 2.0 queda fuera hasta revisar la consulta de brecha entre canales | — |
| D-270 | La base servida vive en un release que cada carga reemplaza; git guarda solo su puntero | [ADR-35](ADR.md#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza) |

## 4. Calidad y auditoría

| Decisión | Título | ADR |
|---|---|---|
| D-016 | Pruebas y controles de calidad visibles desde la primera versión | — |
| D-018 | Los hallazgos se publican solo si se pueden reproducir | — |
| D-049 | Versiones SQL de K6 y K5 verificadas contra Python; K4 sin versión doble | — |
| D-176 | Calidad y auditoría cuenta la historia con un método: las seis dimensiones del DAMA-DMBOK | — |
| D-196 | Calidad y auditoría rehechas: medición real y origen de cada cifra | — |
| D-245 | Etapa 6: las puertas de calidad sobre el recorrido, y RF-03 con su prueba | — |
| D-256 | Calidad y auditoría rehecha: seis dimensiones, tres puertas, y texto de tamaño normal | — |
| D-257 | Calidad y auditoría: el diagrama es la página, y cada pieza abre su detalle | — |
| D-273 | Calidad: el esquema pasa a ser un pipeline de calidad, con el mismo funcionamiento | — |

## 5. Seguridad

| Decisión | Título | ADR |
|---|---|---|
| D-013 | Repositorio público | — |
| D-199 | La clave de control resiste que la adivinen | — |
| D-200 | Pestaña Seguridad: cada ataque, su barrera y su prueba | — |
| D-202 | Una sola puerta del autor: el botón del pipeline aparece solo tras la clave | — |
| D-207 | La clave de control ya no es un campo de contraseña | — |
| D-249 | Etapa 8: la seguridad como proceso, su procedimiento y el monitoreo | — |
| D-254 | Arquitectura de seguridad como diagrama de zonas de confianza | — |

## 6. Operación y observabilidad

| Decisión | Título | ADR |
|---|---|---|
| D-017 | Informe semanal y avisos con las herramientas de GitHub | — |
| D-038 | Centro de control del pipeline dentro del panel | — |
| D-149 | La ejecución manual es un botón visible, con su resultado | — |
| D-165 | Centro de operación: el recorrido del martes es su propia guía | — |
| D-243 | Etapa 5: diagrama de CI/CD con su definición, desde los workflows reales | — |
| D-246 | Etapa 7: la orquestación del workflow semanal, dentro del diagrama de CI/CD | — |
| D-255 | Despliegue como diagrama de despliegue real, y primero en el Centro de operación | — |
| D-275 | Monitoreo: las señales cuelgan de la carga semanal, no de ocho cadenas iguales | — |

## 7. Panel

| Decisión | Título | ADR |
|---|---|---|
| D-096 | Navegación única por menú lateral, sin pestañas | — |
| D-166 | El panel se lee en horizontal en los teléfonos | — |
| D-264 | Resumen semanal: el encabezado es una sola barra | — |
| D-267 | Las páginas principales con una sola barra de encabezado; Precios e inflación con su lectura | — |
| D-274 | La medida es la ventana real del navegador (1440 × 790); Calidad y auditoría cabe en ella | — |

## 8. Documentación

| Decisión | Título | ADR |
|---|---|---|
| D-151 | La documentación es el PRD, el SAD y el ADR | — |
| D-210 | Documentos de dos páginas como máximo | — |
| D-248 | Etapa 10: documentos al estándar y el PDF es la página impresa | — |
| D-269 | Los documentos, revisados contra el producto: PRD, SAD, ADR y Escalabilidad | — |
| D-278 | La documentación se separa de la historia del proyecto | — |

## 9. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 25-10-2026 | Primera versión (D-279, documentación profesional) |
