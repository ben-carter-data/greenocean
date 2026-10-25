# Índice de decisiones

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Índice de decisiones |
| Versión | 2.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Reunir, por tema, las decisiones que cambian la arquitectura, los datos, la seguridad o la operación. |
| Audiencia | Arquitectura, gerencia y revisión técnica. |
| Documentos relacionados | [Registros de decisiones de arquitectura (ADR)](ADR.md) · [Documento de arquitectura de software (SAD)](SAD.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [En resumen](#1-en-resumen)
2. [Fuentes e ingesta](#2-fuentes-e-ingesta)
3. [Modelo y reglas de datos](#3-modelo-y-reglas-de-datos)
4. [Pipeline y publicación](#4-pipeline-y-publicación)
5. [Calidad y auditoría](#5-calidad-y-auditoría)
6. [Seguridad](#6-seguridad)
7. [Operación y observabilidad](#7-operación-y-observabilidad)
8. [Panel](#8-panel)
9. [Documentación](#9-documentación)
10. [Historial de versiones](#10-historial-de-versiones)

## 1. En resumen

GreenOcean registra cada cambio de comportamiento como una decisión con su fecha, su motivo y sus pruebas. Este índice reúne las 69 que más pesan, agrupadas en ocho temas, para leerlas sin recorrer el registro completo. Cada fila dice primero qué se decidió; cuando la decisión dio origen a un registro de arquitectura, la segunda columna lo enlaza, y el código D-xxx sirve para buscarla en `docs/DECISIONES.md`, que guarda todas en orden cronológico.

[[diagrama:temas]]

[[diagrama:mapa_temas]]

[[diagrama:adr_decisiones]]

## 2. Fuentes e ingesta

Qué se descarga, de dónde y cómo se protege la descarga.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| Los datos vienen de los archivos oficiales de ODEPA, no de copiar páginas web | [Usar solo los archivos oficiales de ODEPA y del INE](ADR.md#adr-01--usar-solo-los-archivos-oficiales-de-odepa-y-del-ine) | D-001 |
| Se empieza con dos fuentes: precios mayoristas y al consumidor | — | D-002 |
| Un producto se identifica por su nombre, su variedad y su calidad, sin mezclarlos | — | D-007 |
| Los archivos crudos no se suben al repositorio | [No subir los datos crudos al repositorio](ADR.md#adr-04--no-subir-los-datos-crudos-al-repositorio) | D-020 |
| La semana del 02-05-2022, que falta en ODEPA, queda registrada como un hueco conocido | — | D-042 |
| Los años cerrados no se vuelven a descargar: se guardan en la caché de GitHub | — | D-047 |
| La descarga sigue funcionando aunque certifi retiró el certificado de ODEPA | — | D-164 |

## 3. Modelo y reglas de datos

Cómo se calcula cada precio y qué se considera una cifra válida.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| Mayorista y consumidor se comparan semana a semana | — | D-006 |
| Un precio con una unidad que no se puede convertir se conserva, pero sin calcular margen | — | D-008 |
| Tablas y columnas con nombres en inglés, y un solo esquema por base | [Modelo estrella con una dimensión de fechas sin huecos](ADR.md#adr-19--modelo-estrella-con-una-dimensión-de-fechas-sin-huecos) | D-023 |
| Cada carga recalcula todos los precios semanales desde cero | [Reconstruir todo en cada carga](ADR.md#adr-10--reconstruir-todo-en-cada-carga) | D-024 |
| Las unidades se convierten leyendo el texto tal como lo escribe ODEPA | — | D-026 |
| Un precio más de cinco veces por encima o por debajo de la mediana de su semana se marca como atípico y no entra a los indicadores | — | D-028 |
| Un calendario de semanas sin huecos para cruzar todas las fechas | [Modelo estrella con una dimensión de fechas sin huecos](ADR.md#adr-19--modelo-estrella-con-una-dimensión-de-fechas-sin-huecos) | D-095 |
| La variación nacional se mide siempre sobre las mismas regiones | — | D-144 |
| Las alertas de precio también comparan las mismas regiones | — | D-145 |
| El panel muestra solo conclusiones que los datos sostienen | — | D-146 |
| Todas las páginas muestran el mismo precio para un producto y una semana | — | D-153 |
| Los precios reales descuentan la inflación con el IPC de alimentos del INE | [Calcular precios reales con el IPC de alimentos del INE](ADR.md#adr-33--calcular-precios-reales-con-el-ipc-de-alimentos-del-ine) | D-155 |
| Una alerta exige al menos dos cotizaciones en cada semana comparada | — | D-158 |

## 4. Pipeline y publicación

Con qué herramientas se construye la base y cuándo se publica.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| El proyecto corre en herramientas gratuitas: SQLite, GitHub Actions y Streamlit | [Orquestar con GitHub Actions y publicar en Streamlit Community Cloud](ADR.md#adr-02--orquestar-con-github-actions-y-publicar-en-streamlit-community-cloud) | D-012 |
| Los datos se revisan antes de cargarlos | [Publicar solo si pasan las pruebas](ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas) | D-029 |
| Si un paso de la carga semanal falla, no se guarda nada | — | D-034 |
| El plan de crecimiento: dbt, DuckDB y Parquet primero; una nube solo con datos de empresa | [No usar un data warehouse en la nube](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube) | D-152 |
| El data warehouse pasa a dbt, DuckDB y Parquet con exactamente los mismos resultados | [Parquet, dbt Core y DuckDB](ADR.md#adr-30--parquet-dbt-core-y-duckdb) | D-154 |
| Las dos construcciones de la base se comparan sin ambigüedad, también el IPC | — | D-194 |
| DuckDB 2.0 espera hasta que una consulta lenta quede revisada | — | D-227 |
| La base publicada vive en un release de GitHub; el repositorio guarda solo su puntero | [Publicar la base servida en un release que cada carga reemplaza](ADR.md#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza) | D-270 |

## 5. Calidad y auditoría

Qué detiene una carga y cómo se demuestra cada cifra.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| Las pruebas y los controles de calidad se ven en el panel desde la primera versión | — | D-016 |
| Un hallazgo se publica solo si se puede reproducir | — | D-018 |
| Los indicadores calculados en SQL se verifican contra un cálculo en Python | — | D-049 |
| La calidad se explica con las seis dimensiones del estándar DAMA-DMBOK | — | D-176 |
| Cada cifra de calidad es una medición real y muestra su origen | — | D-196 |
| Las puertas de calidad se dibujan sobre el recorrido de la carga | — | D-245 |
| Calidad en una vista: seis dimensiones y tres puertas | — | D-256 |
| En Calidad, cada pieza del diagrama abre su detalle | — | D-257 |
| Calidad se dibuja como un pipeline de calidad de datos | — | D-273 |

## 6. Seguridad

Quién puede hacer qué y cómo se comprueba.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| El repositorio es público, sin ningún secreto | — | D-013 |
| La clave de control resiste que la adivinen y acepta cualquier carácter | — | D-199 |
| Cada ataque se muestra con su barrera y su prueba | — | D-200 |
| El botón para lanzar la carga aparece solo después de la clave del autor | — | D-202 |
| La clave de control deja de ser un campo de contraseña del navegador | — | D-207 |
| La seguridad se trata como un proceso, con su procedimiento y su monitoreo | — | D-249 |
| La arquitectura de seguridad se dibuja por zonas de confianza | — | D-254 |

## 7. Operación y observabilidad

Cómo se sabe qué pasó en cada carga y qué hacer.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| El informe semanal y los avisos usan las herramientas de GitHub | — | D-017 |
| La carga se vigila desde un centro de control dentro del panel | — | D-038 |
| La ejecución manual es un botón visible, que muestra su resultado | — | D-149 |
| El Centro de operación sigue el recorrido de cada martes | — | D-165 |
| El diagrama de CI/CD se dibuja desde los workflows reales | — | D-243 |
| La orquestación del martes vive dentro del diagrama de CI/CD | — | D-246 |
| El despliegue se dibuja como un diagrama de despliegue estándar | — | D-255 |
| Las señales de monitoreo cuelgan de la carga semanal | — | D-275 |

## 8. Panel

Cómo se lee el panel en una sola pantalla y en dos idiomas.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| Se navega con un solo menú lateral, sin pestañas | — | D-096 |
| En el teléfono, el panel se lee en horizontal | — | D-166 |
| El Resumen semanal tiene una sola barra de encabezado | — | D-264 |
| Cada página principal tiene una sola barra de encabezado | — | D-267 |
| Cada página cabe en una ventana real de 1440 × 790 | — | D-274 |
| Botones y enlaces comparten un solo componente | — | D-281 |
| El panel y los documentos existen en español y en inglés | — | D-283 |
| Cada página se traduce al inglés mientras se dibuja | — | D-284 |
| Un mapa de la app muestra todo el sistema en una vista | — | D-285 |

## 9. Documentación

Cómo se explica el proyecto.

| Qué se decidió | Registro de arquitectura | Código |
|---|---|---|
| La documentación sigue el estándar PRD, SAD y ADR | — | D-151 |
| Documentos breves y directos | — | D-210 |
| El PDF de un documento es la misma página impresa | — | D-248 |
| Los documentos se revisan contra el producto real | — | D-269 |
| La documentación se separa de la historia del proyecto | — | D-278 |
| Cada documento lleva portada, índice, glosario e historial | — | D-279 |
| Diagramas sin fondo, y el PDF siempre en hoja blanca | — | D-280 |
| Todos los documentos en una sola carpeta del menú | — | D-282 |

## 10. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 25-10-2026 | Primera versión (D-279, documentación profesional) |
| 2.0 | 25-10-2026 | Un resumen con tres diagramas; cada fila dice primero qué se decidió y enlaza su registro de arquitectura por su nombre (D-290, documentos para todo lector) |
