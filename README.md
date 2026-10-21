# GreenOcean · Monitor de precios de alimentos en Chile

Pipeline semanal y panel de BI sobre los precios mayoristas y al consumidor de ODEPA, con precios reales calculados con el IPC de alimentos del INE.

Cada martes el pipeline descarga las fuentes oficiales, las deja en una misma unidad y una misma semana, valida su calidad con 31 pruebas de datos y publica la base solo si todo pasa. El panel permite seguir cada cifra hasta el archivo de origen.

[**Abrir el panel público**](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app/)

[![pruebas](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/pruebas.yml/badge.svg)](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/pruebas.yml)
[![semanal](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/semanal.yml/badge.svg)](https://github.com/cben6514-boop/monitor-precios-hito1/actions/workflows/semanal.yml)

## Qué responde

- ¿Qué precios cambiaron esta semana y cuáles son inusuales?
- ¿El precio de hoy es normal para la temporada, en pesos nominales o reales?
- ¿Cuánto paga el consumidor sobre el precio mayorista, por canal?

Además muestra la calidad de cada carga (filas leídas, cargadas y rechazadas con su motivo) y permite auditar cualquier precio paso a paso.

## Cómo funciona

1. **Ingesta** en Python: descarga los CSV de ODEPA y el IPC del INE.
2. **Aterrizaje** en SQLite (`etl/raw.db`): las filas de ODEPA tal como llegan.
3. **Bronce** en Parquet: copia literal de cada fuente, por año; el IPC llega aquí directo.
4. **Transformación** con dbt Core sobre DuckDB: staging, intermedio y marts, con 31 pruebas.
5. **Publicación** en `etl/datos.duckdb`, que el panel de Streamlit lee en solo lectura.

GitHub Actions ejecuta todo cada martes y corre las pruebas en cada cambio. Los diagramas completos (pipeline, plataforma y modelo estrella) están en el panel y en el [SAD](docs/SAD.md).

## Estructura

```
├── agent/
│   ├── agent.py         descarga y validación de los archivos de ODEPA
│   └── input.csv        recursos a descargar
├── etl/
│   ├── etl.py           aterrizaje en SQLite y respaldo datos.db
│   ├── raw.db           aterrizaje de ODEPA (no se sube; lo genera la ingesta)
│   ├── bronze.py        capa bronce en Parquet
│   ├── ine.py           IPC de alimentos del INE
│   ├── pipeline.py      dbt build y publicación de la base
│   ├── datos.duckdb     base servida que lee el panel
│   └── datos.db         respaldo en SQLite
├── dbt/                 proyecto dbt: staging, intermedio, marts y pruebas
├── bi/
│   ├── dashboard.py     panel Streamlit
│   ├── queries.sql      consultas del panel
│   └── architecture.py  diagramas en vivo del pipeline y la plataforma
├── docs/                PRD, SAD, ADR, plan de seguridad, decisiones y manual
├── tests/               pruebas automáticas (pytest)
└── .github/workflows/   semanal.yml y pruebas.yml
```

## Stack

Python · SQL · dbt Core · DuckDB · Parquet · SQLite · GitHub Actions · pytest · Streamlit

## Documentación

| Documento | Contenido |
|---|---|
| [PRD](docs/PRD.md) | Contexto, visión, alcance, usuarios y requisitos |
| [SAD](docs/SAD.md) | Arquitectura: pipeline, plataforma y modelo de datos |
| [ADR](docs/ADR.md) | Las diez decisiones de arquitectura más importantes |
| [Plan de seguridad](docs/SEGURIDAD.md) | Cómo se prueba que el panel resiste ataques |
| [Decisiones](docs/DECISIONES.md) | Registro completo de decisiones |
| [Manual](docs/MANUAL.md) | Qué pasa cada martes y qué hacer si falla |

## Cómo ejecutarlo

| Para qué | Comando |
|---|---|
| Instalar el panel y las pruebas | `pip install -r requirements.txt` |
| Instalar el pipeline con dbt (Python 3.11 o 3.12) | `pip install -r requirements-pipeline.txt` |
| Abrir el panel | `streamlit run bi/dashboard.py` |
| Correr las pruebas | `python -m pytest -q` |
| Descargar ODEPA | `python agent/agent.py` |
| Construir el data warehouse | `python etl/pipeline.py` |

## Alcance y límites

- Frutas y verduras: margen entre mayorista y consumidor. Carnes, lácteos, huevos, abarrotes y pan: solo precio al consumidor.
- ODEPA publica 9 de las 16 regiones; los promedios nacionales cubren esas 9.
- El precio real descuenta la inflación general de alimentos, no la de cada producto.
- Los indicadores describen lo ocurrido; no predicen precios ni atribuyen causas.

## Fuentes de los datos

- Oficina de Estudios y Políticas Agrarias (ODEPA), Ministerio de Agricultura de Chile, [portal de datos abiertos](https://datos.odepa.gob.cl/), licencia Creative Commons Atribución.
- Instituto Nacional de Estadísticas (INE), IPC de alimentos y bebidas no alcohólicas.

Este proyecto no es un producto oficial de ODEPA ni del INE.

## Licencia

El código está bajo licencia MIT (`LICENSE`). Los datos mantienen la licencia de sus fuentes.

## Autor

Jocelyn Ben Yahmed
