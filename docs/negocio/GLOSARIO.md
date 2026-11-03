# Glosario

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Glosario |
| Versión | 2.11 |
| Fecha | 03-11-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Definir una sola vez las siglas y los términos que usan el panel y los documentos. |
| Audiencia | Todo lector del panel y de la documentación. |
| Documentos relacionados | [PRD](PRD.md) · [SAD](../arquitectura/SAD.md) · [ADR](../arquitectura/ADR.md) · [Plan de pruebas y seguridad](../calidad/PLAN_PRUEBAS.md) |

## Índice

1. [En resumen](#1-en-resumen)
2. [Términos](#2-términos)
3. [Historial de versiones](#3-historial-de-versiones)

## 1. En resumen

Este glosario define una sola vez cada palabra técnica del panel y de los documentos. Tres esquemas muestran cómo se relacionan: el camino de una cifra, desde la fila que publica ODEPA hasta la alerta del panel; las capas por las que pasan los datos; y los actores que intervienen.

[[diagrama:terminos_cifra]]

[[diagrama:terminos_capas]]

[[diagrama:terminos_actores]]

## 2. Términos

Los términos van ordenados por tema, desde lo que se lee en el panel hasta los documentos. La columna «Dónde aparece» dice en qué páginas del panel se usa cada término. Un «—» quiere decir que solo aparece en los documentos.

| Sigla o término | Significado | Dónde aparece | Tema |
|---|---|---|---|
| KPI | Indicador clave de desempeño (*key performance indicator*): cada cifra que mide algo del negocio. Los indicadores técnicos se numeran de K1 a K8. | Semanal, Análisis BA y BI (Mensual), Análisis BA y BI (Histórico), Análisis BA y BI (Método) | Indicadores |
| BI | Inteligencia de negocios (*business intelligence*): el análisis de datos para tomar decisiones; aquí, el panel. | — | Indicadores |
| BA | Análisis de negocio (*business analysis*): el rol que traduce los datos en decisiones; una de las vistas profesionales del panel. | Análisis BA y BI (Interesados) | Indicadores |
| BSA | Análisis de sistemas de negocio (*business systems analysis*): el rol que decide cómo el sistema cumple lo que el negocio pide: qué se mide, qué bloquea la publicación y qué avisa. | Análisis BA y BI (Método) | Indicadores |
| RN | Regla de negocio: cada regla de limpieza y cálculo (RN-01 a RN-14). | Calidad y auditoría | Indicadores |
| Alerta de precio | Cambio semanal fuera del promedio ± 2 desviaciones de sus 12 semanas previas, de al menos 10 % y con dos cotizaciones en cada semana (K6). | Semanal | Indicadores |
| Precio real | Precio expresado en pesos del último mes publicado del IPC. | Análisis BA y BI (Precios e inflación) | Indicadores |
| Semana provisional | Semana de un mes cuyo IPC aún no se publica; usa el último mes disponible. | Análisis BA y BI (Precios e inflación) | Indicadores |
| Indicador de calidad de los datos | Cada uno de los 11 indicadores que se miden en cada carga sobre la base publicada, en cinco dimensiones. | Calidad y auditoría | Indicadores |
| Indicador del plan de calidad | Cada uno de los 14 indicadores del SQAP (8 de código y 6 de datos) que el workflow de calidad mide cada semana. | Método y calidad | Indicadores |
| Dimensión de calidad | Aspecto de la calidad que se mide: completitud, actualidad, validez, unicidad, consistencia y exactitud. | Calidad y auditoría | Indicadores |
| DAMA-DMBOK | Guía de gestión de datos de DAMA International (*Data Management Body of Knowledge*); de ella vienen las dimensiones de calidad. | — | Indicadores |
| ODEPA | Oficina de Estudios y Políticas Agrarias, del Ministerio de Agricultura de Chile. Publica las dos fuentes de precios. | Semanal, Pipeline y linaje | Fuentes |
| INE | Instituto Nacional de Estadísticas de Chile. Publica el IPC de alimentos. | Análisis BA y BI (Precios e inflación), Pipeline y linaje | Fuentes |
| IPC | Índice de precios al consumidor; aquí, la división «Alimentos y bebidas no alcohólicas» que publica el INE. | Análisis BA y BI (Precios e inflación) | Fuentes |
| CSV | Archivo de texto con valores separados por comas: el formato en que ODEPA publica los precios. | Pipeline y linaje | Fuentes |
| SHA-256 | Función que calcula la huella de un archivo; cambia si cambia un solo byte. Se usa para verificar los archivos descargados y la Base DuckDB. | Calidad y auditoría | Fuentes |
| JSON | Formato de texto para datos estructurados (*JavaScript Object Notation*); así se guardan el manifiesto de descargas y la fila original de cada rechazo. | — | Fuentes |
| Pipeline | El flujo completo de cada martes, de ODEPA al panel: descarga, ETL de respaldo, construcción con dbt, pruebas, publicación e informe. | Pipeline y linaje, Centro de operación | Pipeline |
| Ingesta | La descarga de los archivos de ODEPA; la hace el agente de ingesta (`agent/agent.py`), que revisa que cada archivo traiga las columnas esperadas. | Pipeline y linaje | Pipeline |
| ETL | Extraer, transformar y cargar. `etl/etl.py` limpia los datos y aplica las reglas para el respaldo `etl/datos.db`; las mismas reglas corren en dbt para la Base DuckDB. | Pipeline y linaje, Centro de operación | Pipeline |
| Puerta de calidad | Control que detiene la carga si algo no cumple: el archivo, cada fila o la base. | Calidad y auditoría | Pipeline |
| Job, workflow | Tarea automática de GitHub Actions; el job semanal (`semanal.yml`) ejecuta el pipeline cada martes. | Centro de operación | Pipeline |
| Cron | La programación del job semanal: cada martes a las 12:00 UTC. | Centro de operación | Pipeline |
| Ejecución | Una pasada completa del job semanal. | Centro de operación | Pipeline |
| CI, CD | Integración continua (*continuous integration*): las pruebas corren solas en cada cambio del código (`pruebas.yml`). Entrega continua (*continuous delivery*): lo que pasa todas las pruebas llega a producción sin pasos manuales. | Centro de operación (CI/CD) | Pipeline |
| Commit, push | Guardar un cambio en el historial del código, y subirlo a GitHub. | Centro de operación (CI/CD) | Pipeline |
| Release | Publicación de GitHub que guarda archivos fuera del historial; el release «base-actual» guarda la Base DuckDB y cada carga la reemplaza. | Centro de operación (CI/CD) | Pipeline |
| Puntero de la base | El archivo `etl/datos.version`: la huella, el tamaño y la fecha de la Base DuckDB publicada. | Centro de operación (Despliegue) | Pipeline |
| Issue | Publicación en GitHub; aquí, el informe semanal que deja cada carga. | Centro de operación (Monitoreo) | Pipeline |
| Pull request | Propuesta de cambio en GitHub que el autor revisa antes de aceptarla; aquí, el informe de calidad de cada semana. | Método y calidad | Pipeline |
| Aterrizaje | La base `etl/raw.db`, con las filas de ODEPA tal como llegan; no se versiona. | Pipeline y linaje | Base de datos |
| Bronce, plata, oro | Las capas de los datos: bronce (Parquet, copia exacta), plata (staging e intermedio de dbt: tipos, reglas y marcas) y oro (marts: el modelo estrella que lee el panel). | Pipeline y linaje | Base de datos |
| Base DuckDB | `etl/datos.duckdb`: la base que lee el panel, con el modelo estrella; se publica en el release «base-actual». Antes se llamaba «Base DuckDB» (D-426). | Pipeline y linaje, Modelo de datos | Base de datos |
| Respaldo | `etl/datos.db`: los mismos precios calculados sin dbt, para la prueba de paridad. | Modelo de datos | Base de datos |
| Paridad | Comparación entre el respaldo y la Base DuckDB: deben dar las mismas cifras. | Calidad y auditoría | Base de datos |
| Data warehouse | La base lista para analizar, con el modelo estrella. | Pipeline y linaje, Modelo de datos | Base de datos |
| Modelo estrella | Una tabla de hechos (`weekly_price`) rodeada de sus dimensiones (producto, región, canal, fecha). | Modelo de datos | Base de datos |
| PK, FK | Clave primaria: la columna que identifica cada fila de una tabla. Clave foránea: la columna que apunta a la clave primaria de otra tabla. | Modelo de datos | Base de datos |
| JOIN | Unión de dos tablas por su clave. | Modelo de datos, Consultas SQL | Base de datos |
| SQL | Lenguaje de consultas estructurado: con él se leen los datos de la base. | Consultas SQL | Base de datos |
| dbt | dbt Core: herramienta que transforma datos con modelos SQL versionados, con pruebas y linaje. | Pipeline y linaje | Base de datos |
| DuckDB | Base de datos analítica en un solo archivo, sin servidor. | Modelo de datos | Base de datos |
| Parquet | Formato abierto de archivos por columnas, comprimido. | Pipeline y linaje | Base de datos |
| Git LFS | Extensión de Git para archivos grandes (*Large File Storage*), que los guarda fuera del historial. | — | Base de datos |
| ISO | Organización Internacional de Normalización; aquí, la semana ISO (de lunes a domingo, numerada según la norma ISO 8601) y las fechas en formato AAAA-MM-DD. | — | Base de datos |
| Token | Credencial con la que el panel lanza la carga, lee su estado y sus logs, y la cancela; nunca se muestra. | Centro de operación | Seguridad |
| Clave de control | Secreto que abre la vista Autor en el panel. | Centro de operación | Seguridad |
| Vista | Lo que el panel muestra según quien lo lee: Usuario (el negocio), Profesional (todo el proyecto) o Autor (lo mismo, más lo que solo ve el autor, con la clave de control). | Mapa de la app, Arquitectura de seguridad | Seguridad |
| OWASP | Open Worldwide Application Security Project; su lista Top 10 clasifica los riesgos de seguridad de aplicaciones web. | Arquitectura de seguridad | Seguridad |
| ASCII | Juego de caracteres básico del inglés, sin ñ ni tildes. | — | Seguridad |
| API | Interfaz por la que un programa se comunica con otro. El panel usa la de GitHub para lanzar la carga, leer su estado y sus logs, y cancelarla. | Centro de operación | Conexiones |
| HTTPS | Conexión web cifrada. | Pipeline y linaje, Centro de operación (Despliegue) | Conexiones |
| URL | Dirección de una página o de un archivo en la web. | — | Conexiones |
| UTC | Tiempo universal coordinado; el job corre a las 12:00 UTC: las 09:00 en Chile en horario de verano y las 08:00 en invierno. | Centro de operación | Conexiones |
| PRD | Documento de requisitos del producto (*Product Requirements Document*). | — | Documentos |
| SAD | Documento de arquitectura de software (*Software Architecture Document*). | — | Documentos |
| SQAP | Plan de calidad del software (*Software Quality Assurance Plan*): qué calidad se cuida, cómo se mide y quién decide. | Método y calidad | Documentos |
| IEEE | Instituto de Ingenieros Eléctricos y Electrónicos; publica el estándar IEEE 730, que da la estructura del SQAP. | — | Documentos |
| IEC | Comisión Electrotécnica Internacional; firma con la ISO las normas ISO/IEC 25010 (calidad del software) e ISO/IEC 25012 (calidad de los datos). | Método y calidad | Documentos |
| ADR | Registro de decisión de arquitectura (*Architecture Decision Record*). | — | Documentos |
| MADR | Formato estándar para escribir un ADR (*Markdown Architectural Decision Records*). | — | Documentos |
| arc42 | Plantilla estándar de documentación de arquitectura de software. | — | Documentos |
| C4 | Modelo de diagramas de arquitectura por niveles: contexto, contenedores, componentes y código. | — | Documentos |
| RF, RNF | Requisito funcional y requisito no funcional. | — | Documentos |
| ID | Identificador de un requisito, de un caso de prueba o de una fila. | — | Documentos |
| PDF | Formato de documento para imprimir; el PDF de cada documento es su página del panel impresa por el navegador. | — | Documentos |
| Runbook | Manual de operación: qué hacer ante cada falla, paso a paso. | — | Documentos |

## 3. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 25-10-2026 | Primera versión como documento propio, a partir del glosario de la guía del proyecto (D-279, documentación profesional) |
| 2.0 | 25-10-2026 | Un resumen con tres esquemas y los términos ordenados por tema, desde los indicadores (D-290, documentos para todo lector) |
| 2.1 | 26-10-2026 | BA, una de las vistas profesionales del panel (D-300) |
| 2.2 | 30-10-2026 | SQAP, IEEE e IEC, del plan de calidad del software (D-355) |
| 2.3 | 31-10-2026 | BSA, de las páginas «Interesados» y «Análisis de negocio y sistemas» (D-376, D-377) |
| 2.4 | 31-10-2026 | Redacción revisada; las tres vistas; los indicadores de calidad de los datos y los del plan de calidad; el pull request del informe de calidad; la alerta de precio completa; el documento pasa a `docs/negocio/` (D-381 a D-385, D-388) |
| 2.5 | 01-11-2026 | «Base servida» pasa a «Base DuckDB» (D-426) |
| 2.6 | 02-11-2026 | «Panorama de precios» pasa a llamarse «Dashboard» y encabeza el menú (D-442) |
| 2.7 | 02-11-2026 | «Base servida» pasa a «Base DuckDB» también en las definiciones, que lo decían con el nombre anterior (D-455) |
| 2.8 | 02-11-2026 | Las páginas que pasaron a pestañas de «Análisis BA y BI» se nombran «Análisis BA y BI (pestaña)» (D-456) |
| 2.9 | 02-11-2026 | La pestaña «Tendencias» de «Análisis BA y BI» pasa a «Mensual» e «Histórico» (D-457) |
| 2.10 | 02-11-2026 | El dashboard de la semana se llama «Semanal» (D-459) |
| 2.11 | 03-11-2026 | El plan de calidad tiene 14 indicadores (D-475) |
