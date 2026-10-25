# Documento de arquitectura de software (SAD)

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Documento de arquitectura de software (SAD), estructura arc42 con vistas C4 |
| Versión | 2.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Describir cómo está construido el sistema, por vistas, y por qué tiene esa forma. |
| Audiencia | Arquitectura, ingeniería de datos, operación y revisión técnica. |
| Documentos relacionados | [Documento de requisitos del producto (PRD)](PRD.md) · [Registros de decisiones de arquitectura (ADR)](ADR.md) · [Diccionario de datos](DICCIONARIO_DATOS.md) · [Plan de pruebas de seguridad](SEGURIDAD.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [Introducción y objetivos](#1-introducción-y-objetivos)
2. [Restricciones](#2-restricciones)
3. [Contexto y alcance](#3-contexto-y-alcance)
4. [Estrategia de solución](#4-estrategia-de-solución)
5. [Vista de bloques de construcción](#5-vista-de-bloques-de-construcción)
6. [Vista de ejecución](#6-vista-de-ejecución)
7. [Vista de despliegue](#7-vista-de-despliegue)
8. [Conceptos transversales](#8-conceptos-transversales)
9. [Decisiones de arquitectura](#9-decisiones-de-arquitectura)
10. [Requisitos de calidad](#10-requisitos-de-calidad)
11. [Riesgos y deuda técnica](#11-riesgos-y-deuda-técnica)
12. [Glosario](#12-glosario)
13. [Historial de versiones](#13-historial-de-versiones)

## 1. Introducción y objetivos

GreenOcean es un pipeline semanal y un panel de solo lectura sobre los precios de los alimentos en Chile. Los requisitos están en el [PRD](PRD.md). Este documento se centra en cómo se cumplen. Los objetivos de calidad que más pesan en la arquitectura son tres:

| Prioridad | Objetivo de calidad | Qué significa aquí |
|---|---|---|
| 1 | Exactitud y trazabilidad | Cada cifra del panel se puede recalcular desde el archivo original |
| 2 | Confiabilidad de la publicación | Una carga con errores nunca reemplaza a la base servida |
| 3 | Costo cero y mantenimiento mínimo | Solo servicios gratuitos permanentes y sin servidores propios |

## 2. Restricciones

| Restricción | Origen |
|---|---|
| Solo servicios gratuitos sin vencimiento | [ADR-02 · Orquestar con GitHub Actions y publicar en Streamlit Community Cloud](ADR.md#adr-02--orquestar-con-github-actions-y-publicar-en-streamlit-community-cloud) y [ADR-31 · No usar un data warehouse en la nube](ADR.md#adr-31--no-usar-un-data-warehouse-en-la-nube) |
| Solo fuentes oficiales y abiertas | [ADR-01 · Usar solo los archivos oficiales de ODEPA y del INE](ADR.md#adr-01--usar-solo-los-archivos-oficiales-de-odepa-y-del-ine) |
| Ninguna cifra se inventa ni se interpola, y el histórico no se borra | Regla del proyecto |
| Python 3.11 o 3.12 para el pipeline con dbt | Compatibilidad de dbt Core |
| Repositorio público | Portafolio abierto; la seguridad depende de los secretos, no del código oculto |

## 3. Contexto y alcance

[[diagrama:contexto]]

El sistema lee dos fuentes públicas, ODEPA y el INE, y se apoya en dos servicios gratuitos: GitHub guarda el código y la base servida y ejecuta la carga; Streamlit Community Cloud publica el panel. El visitante solo lee el panel. El administrador mantiene el código y los secretos.

## 4. Estrategia de solución

| Principio | Cómo se aplica | Decisión |
|---|---|---|
| Rehacer todo en cada carga | Cada martes se recalcula la historia completa desde los archivos oficiales; repetir una carga nunca duplica datos | [ADR-10](ADR.md#adr-10--reconstruir-todo-en-cada-carga) |
| Publicar solo lo validado | La base servida cambia solo si pasan todas las pruebas | [ADR-11](ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas) |
| Comprobar por un segundo camino | Un ETL en Python, independiente de dbt, calcula los mismos precios | [ADR-34](ADR.md#adr-34--separar-la-base-de-trabajo-de-dbt-la-base-que-lee-el-panel-y-el-respaldo) |
| Capas declarativas y probadas | Bronce en Parquet; staging, intermedio y marts en dbt Core sobre DuckDB | [ADR-30](ADR.md#adr-30--parquet-dbt-core-y-duckdb) |
| Una sola copia publicada | La base servida vive en un release que cada carga reemplaza | [ADR-35](ADR.md#adr-35--publicar-la-base-servida-en-un-release-que-cada-carga-reemplaza) |

## 5. Vista de bloques de construcción

[[diagrama:contenedores]]

El sistema tiene dos aplicaciones y tres almacenes de datos:

| Contenedor | Tecnología | Responsabilidad |
|---|---|---|
| Carga semanal | Python, dbt Core, DuckDB | Descarga los CSV, los guarda sin cambios, los transforma y prueba, y reemplaza la base servida solo si todo pasa. El agente, el ETL y dbt corren en el mismo job |
| Archivos de trabajo | SQLite, Parquet, DuckDB | Aterrizaje, bronce y base de trabajo de dbt; se rehacen en cada carga y no se versionan |
| Base servida | DuckDB (`etl/datos.duckdb`) | Las tablas que lee el panel; se publica en el release «base-actual» |
| Respaldo | SQLite (`etl/datos.db`) | Los mismos precios calculados sin dbt, para la prueba de paridad; se rehace en la máquina de cada carga y no se publica |
| Panel web | Streamlit, Python | Muestra los indicadores y los documentos, y ofrece el estudio SQL; lee la base servida en solo lectura y, con la clave de control, lanza la carga por la API de GitHub |

Se omite la vista de componentes (nivel 3 del modelo C4): los módulos de `bi/` no se despliegan por separado, y la carga ya se describe paso a paso en la sección 6 y en el linaje de dbt.

## 6. Vista de ejecución

Cada paso de la carga semanal empieza solo si el anterior terminó bien:

| Paso | Qué ocurre |
|---|---|
| 1 | A las 12:00 UTC, GitHub Actions crea una máquina nueva y recupera de su caché los CSV de los años cerrados |
| 2 | Descarga del release «base-actual» la base servida de la semana anterior y verifica su huella; de ella salen el historial de cargas y la comparación del paso 6 |
| 3 | El agente descarga de ODEPA el archivo del año en curso y los faltantes, y registra la huella SHA-256 de cada uno en `manifest.json` |
| 4 | El ETL en Python calcula los precios por su cuenta y escribe el respaldo `etl/datos.db` |
| 5 | `etl/pipeline.py` guarda las filas en el aterrizaje, las copia al bronce junto con el IPC del INE y ejecuta `dbt build`, que construye y prueba cada modelo en la base de trabajo |
| 6 | Puerta de publicación: si falla una prueba de dbt o la carga lee menos del 90 % de las filas de la última carga correcta, el proceso se detiene; si todo pasa, las tablas del panel se copian a un archivo nuevo que reemplaza a `etl/datos.duckdb` |
| 7 | pytest corre sobre la base nueva, incluida la paridad entre el respaldo y DuckDB |
| 8 | La máquina reemplaza la base en el release y sube su puntero, `etl/datos.version`, a la rama `main`; el panel detecta el puntero nuevo, descarga la base y verifica su huella antes de usarla |
| 9 | Se publica el informe semanal como un issue del repositorio |

Si un paso falla, los siguientes no corren y la base servida no cambia ([ADR-11 · Publicar solo si pasan las pruebas](ADR.md#adr-11--publicar-solo-si-pasan-las-pruebas)). La ejecución y sus pasos se pueden seguir en la pestaña «Operación» de [[vista:Centro de operación]]; el administrador también puede lanzar la carga desde el panel, con la clave de control.

## 7. Vista de despliegue

| Pieza | Dónde corre | Detalle |
|---|---|---|
| Carga semanal y pruebas de cada cambio | Máquinas de GitHub Actions (Ubuntu, Python 3.11) | Se crean y se descartan en cada ejecución; los CSV de años cerrados quedan en la caché de Actions |
| Código y puntero de la base | Repositorio de GitHub, rama `main` | |
| Base servida | Release «base-actual» del repositorio | Una sola copia, reemplazada por cada carga |
| Panel | Streamlit Community Cloud, desde `main` | Guarda los secretos: el token de GitHub y la clave de control |
| Aterrizaje (`etl/raw.db`) | Computador del autor y máquina de cada carga | No se versiona |

El diagrama de despliegue, con el estado en vivo de cada pieza, está en la pestaña «Despliegue» de [[vista:Centro de operación]]; el camino de un cambio hasta producción, en su pestaña «CI/CD».

## 8. Conceptos transversales

**Capas de datos.** El aterrizaje guarda las filas tal como llegan; el bronce es su copia literal en Parquet, por fuente y año; staging normaliza tipos y textos; intermedio aplica las reglas de negocio (unidades, semanas, rechazos); los marts forman el modelo estrella que lee el panel. El recorrido y el linaje están en [[vista:Pipeline y linaje]]; las tablas y sus claves, en [[vista:Modelo de datos]] y en el [Diccionario de datos](DICCIONARIO_DATOS.md).

**Precios reales.** Cada semana toma el IPC de alimentos del mes de su lunes; los precios reales quedan en pesos del último mes publicado ([ADR-33 · Calcular precios reales con el IPC de alimentos del INE](ADR.md#adr-33--calcular-precios-reales-con-el-ipc-de-alimentos-del-ine)).

**Calidad.** Tres puertas: el archivo (¿llegó completo y al día?), cada fila (¿es válida?) y la base (¿es coherente y pasó sus pruebas?). Once indicadores, en cinco dimensiones, se miden en cada carga contra su umbral; la exactitud, la sexta dimensión, se mide con cuatro controles que comparan las cifras con la fuente. El detalle está en [[vista:Calidad y auditoría]].

**Observabilidad.** Cada carga deja rastro en cuatro lugares: `etl_run` (filas leídas, cargadas y rechazadas de cada carga publicada), `dbt_result` (el resultado de cada modelo y prueba), el registro de GitHub Actions (cada paso, incluidos los que fallan) y el correo que GitHub envía al autor si la carga falla. La pestaña «Monitoreo» de [[vista:Centro de operación]] los reúne.

**Seguridad.** Las amenazas, sus controles y las pruebas que los verifican están en [[vista:Arquitectura de seguridad]]; el procedimiento de verificación, en el [Plan de pruebas de seguridad](SEGURIDAD.md).

## 9. Decisiones de arquitectura

Las decisiones que dan forma a esta arquitectura, con su contexto, sus alternativas y sus consecuencias, están en los [Registros de decisiones de arquitectura (ADR)](ADR.md).

## 10. Requisitos de calidad

| Atributo | Escenario | Respuesta esperada |
|---|---|---|
| Exactitud | Una regla de negocio cambia por error | La paridad con el respaldo o la reconstrucción desde filas crudas falla en pytest y la carga no se publica |
| Confiabilidad | ODEPA publica un archivo truncado | La carga lee menos del 90 % de la anterior y se detiene; el panel conserva la última base válida |
| Disponibilidad | GitHub no responde al abrir el panel | El panel conserva la base que ya tiene y lo informa si no tiene ninguna |
| Seguridad | Un visitante intenta leer archivos del servidor con SQL | La consulta se rechaza y el motor no tiene acceso a archivos ni a la red |
| Usabilidad | Una pantalla de 1440 × 900 | Cada página principal se ve entera en la ventana del navegador (1440 × 790) |

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
