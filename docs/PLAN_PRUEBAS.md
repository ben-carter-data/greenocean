# Plan de pruebas

| Campo | Valor |
|---|---|
| Proyecto | GreenOcean |
| Tipo de documento | Plan de pruebas |
| Versión | 1.0 |
| Fecha | 25-10-2026 |
| Estado | Vigente |
| Responsable | El autor |
| Propósito | Definir qué se prueba, cómo, con qué herramientas y con qué criterios se acepta un cambio. |
| Audiencia | Ingeniería, calidad y revisión técnica. |
| Documentos relacionados | [Documento de requisitos del producto (PRD)](PRD.md) · [Plan de pruebas de seguridad](SEGURIDAD.md) · [Documento de arquitectura de software (SAD)](SAD.md) · [Glosario](GLOSARIO.md) |

## Índice

1. [Objetivo y alcance](#1-objetivo-y-alcance)
2. [Niveles de prueba](#2-niveles-de-prueba)
3. [Entorno y ejecución](#3-entorno-y-ejecución)
4. [Criterios de entrada y de salida](#4-criterios-de-entrada-y-de-salida)
5. [Trazabilidad](#5-trazabilidad)
6. [Riesgos y límites](#6-riesgos-y-límites)
7. [Glosario](#7-glosario)
8. [Historial de versiones](#8-historial-de-versiones)

## 1. Objetivo y alcance

**Objetivo:** que cada cifra del panel sea correcta y comprobable, que una carga con errores nunca se publique y que cada cambio del código se verifique antes de llegar a producción.

**Alcance:** el pipeline (ingesta, ETL, dbt y publicación), la base servida, el panel y los documentos. La seguridad tiene su propio plan: el [Plan de pruebas de seguridad](SEGURIDAD.md).

## 2. Niveles de prueba

| Nivel | Qué verifica | Herramienta | Dónde |
|---|---|---|---|
| Pruebas de datos de dbt | Unicidad, valores aceptados, relaciones entre tablas y conciliación de filas en cada modelo | dbt Core | `dbt/tests/`, modelos de `dbt/models/` |
| Auditoría de cifras | Los precios semanales se reconstruyen desde las filas crudas; las cifras de referencia del panel se reproducen | pytest | `tests/test_data_audit.py`, `tests/test_reconciliation.py` |
| Paridad | El ETL en Python y dbt producen los mismos precios, dimensiones y rechazos | pytest | `tests/test_migration_parity.py` |
| Puerta de publicación | Una carga con pruebas fallidas o con muchas menos filas no reemplaza la base servida | pytest | `tests/test_pipeline_gate.py` |
| IPC y precios reales | El factor semanal, el mes de referencia y las semanas provisionales | pytest | `tests/test_ipc_audit.py` |
| Panel | Cada página se dibuja sin errores y muestra lo que su decisión exige | pytest con AppTest de Streamlit | `tests/test_dashboard.py` y las pruebas de cada vista |
| Diagramas | Cada pieza dibujada existe en el código, el workflow o la base | pytest | `tests/test_devops.py`, `tests/test_monitoring.py`, `tests/test_stack_page.py` y afines |
| Documentos | Trazabilidad de requisitos, cifras contra la base, estructura y redacción | pytest | `tests/test_documents.py`, `tests/test_prd_traceability.py` |
| Medición de pantallas | Desborde horizontal y altura de cada página en varios tamaños de ventana | Playwright, externo al proyecto | `tests/medicion/medir.cjs` |

## 3. Entorno y ejecución

| Elemento | Valor |
|---|---|
| Python | 3.11 o 3.12 para el pipeline con dbt; el panel y las pruebas también corren en versiones más recientes |
| Dependencias | `requirements.txt` (panel y pruebas) y `requirements-pipeline.txt` (dbt) |
| Base | La base servida, descargada con `python bi/served_database.py` |
| Datos crudos | `etl/raw.db`, solo en el computador del autor y en la máquina de cada carga; sin ella, las pruebas que reconstruyen desde las filas crudas se omiten |
| Ejecución local | `python -m pytest -q` |
| Ejecución continua | `pruebas.yml` en cada push y pull request: compila dbt (`dbt parse`) y ejecuta pytest |
| Antes de publicar | `semanal.yml` ejecuta pytest sobre la base nueva, incluida la paridad |

## 4. Criterios de entrada y de salida

| Momento | Criterio |
|---|---|
| Entrada | El cambio compila (`dbt parse`) y la base servida está disponible |
| Salida de un cambio | La suite completa pasa en `pruebas.yml` |
| Salida de una carga | Pasan las pruebas de dbt, la carga lee al menos el 90 % de las filas de la anterior y pytest pasa sobre la base nueva |
| Cambio de comportamiento | Tiene su entrada en `docs/DECISIONES.md` y sus pruebas |

## 5. Trazabilidad

Cada pregunta de negocio y cada requisito del [PRD](PRD.md#6-requisitos) nombra la prueba que lo verifica, y `tests/test_prd_traceability.py` exige que cada una exista.

## 6. Riesgos y límites

| Riesgo o límite | Mitigación |
|---|---|
| Sin `etl/raw.db`, la reconstrucción desde filas crudas no corre en `pruebas.yml` | Corre en el computador del autor y en cada carga semanal, donde los datos crudos existen |
| Las pruebas que consultan enlaces públicos dependen de la red | Un resultado fallido se repite antes de tratarlo como un defecto del código |
| La medición de pantallas no forma parte de la suite | Se ejecuta antes de cada cambio visual |

## 7. Glosario

Las siglas y los términos de este documento se definen en el [Glosario](GLOSARIO.md).

## 8. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 25-10-2026 | Primera versión (D-279, documentación profesional) |
