Versión en español: README.md

# GreenOcean · Chilean food price monitor

A weekly pipeline and a BI dashboard on wholesale and consumer food prices from ODEPA (the Chilean Office of Agricultural Studies and Policies), with real prices computed from the food CPI of INE (the national statistics institute).

Every Tuesday the pipeline downloads the official sources, puts them in a single unit and a single week, checks their quality with 31 data tests and publishes the database only if everything passes. The dashboard lets you follow every figure back to its source file.

[**Open the public dashboard**](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app/) (it reads in Spanish and in English: add `?lang=en` to the address)

[![tests](https://github.com/ben-carter-data/greenocean/actions/workflows/pruebas.yml/badge.svg)](https://github.com/ben-carter-data/greenocean/actions/workflows/pruebas.yml)
[![weekly load](https://github.com/ben-carter-data/greenocean/actions/workflows/semanal.yml/badge.svg)](https://github.com/ben-carter-data/greenocean/actions/workflows/semanal.yml)
[![quality](https://github.com/ben-carter-data/greenocean/actions/workflows/calidad.yml/badge.svg)](https://github.com/ben-carter-data/greenocean/actions/workflows/calidad.yml)
[![coverage](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fben-carter-data%2Fgreenocean%2Fmain%2Fdocs%2Fcalidad%2Fmedicion.json&query=%24.cobertura.total&suffix=%25&label=coverage&color=brightgreen)](docs/calidad/INFORME.md)

## How the pipeline works

1. **Ingestion** in Python: downloads the ODEPA CSV files and the INE food CPI.
2. **Landing** in SQLite: ODEPA's rows exactly as they arrive.
3. **Bronze** in Parquet: a literal copy of each source, by year.
4. **Transformation** with dbt Core on DuckDB: staging, intermediate and marts, with 31 tests.
5. **Publication** of the served database in a GitHub release, replaced by every load; the Streamlit dashboard downloads it and reads it read-only.

GitHub Actions runs everything every Tuesday and runs the tests on every change. If a test fails, nothing is published and the dashboard keeps showing the last valid load.

## How to run it

| What for | Command |
|---|---|
| Install the dashboard and the tests | `pip install -r requirements.txt` |
| Install the pipeline with dbt (Python 3.11 or 3.12) | `pip install -r requirements-pipeline.txt` |
| Open the dashboard | `streamlit run bi/dashboard.py` |
| Run the tests | `python -m pytest -q` |
| Download ODEPA | `python agent/agent.py` |
| Build the data warehouse | `python etl/pipeline.py` |

## Documentation

The documentation is written in Spanish and lives in [`docs/`](docs/): the product requirements ([PRD](docs/PRD.md)), the architecture ([SAD](docs/SAD.md)), the architecture decisions ([ADR](docs/ADR.md)), the test and security plan ([PLAN_PRUEBAS](docs/PLAN_PRUEBAS.md)), the runbook ([MANUAL](docs/MANUAL.md)) and the full decision log ([DECISIONES](docs/DECISIONES.md)). English translations of the main documents are in [`docs/en/`](docs/en/). The quality method, its numbered reports and its acceptable limits are described in [`docs/calidad/README.md`](docs/calidad/README.md), also in Spanish.

## Scope and limits

- Fruit and vegetables: margin between wholesale and consumer prices. Meat, dairy, eggs, groceries and bread: consumer price only.
- ODEPA publishes 9 of the 16 regions; the national averages cover those 9.
- The real price discounts general food inflation, not each product's own.
- The indicators describe what happened; they do not predict prices or assign causes.

## Data sources

- ODEPA, Ministry of Agriculture of Chile, [open data portal](https://datos.odepa.gob.cl/), Creative Commons Attribution license.
- INE, food and non-alcoholic beverages CPI.

This project is not an official product of ODEPA or INE.

## License

The code is under the MIT license (`LICENSE`). The data keep the license of their sources.
