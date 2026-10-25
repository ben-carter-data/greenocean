# Test Plan

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Test Plan |
| Version | 1.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Define what is tested, how, with which tools and with which criteria a change is accepted. |
| Audience | Engineering, quality and technical review. |
| Related documents | [Product Requirements Document (PRD)](PRD.md) · [Security Test Plan](SEGURIDAD.md) · [Software Architecture Document (SAD)](SAD.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [Objective and scope](#1-objective-and-scope)
2. [Test levels](#2-test-levels)
3. [Environment and execution](#3-environment-and-execution)
4. [Entry and exit criteria](#4-entry-and-exit-criteria)
5. [Traceability](#5-traceability)
6. [Risks and limits](#6-risks-and-limits)
7. [Glossary](#7-glossary)
8. [Version history](#8-version-history)

## 1. Objective and scope

**Objective:** that every figure of the panel is correct and verifiable, that a load with errors is never published and that each change of the code is verified before it reaches production.

**Scope:** the pipeline (ingestion, ETL, dbt and publication), the served database, the panel and the documents. Security has its own plan: the [Security Test Plan](SEGURIDAD.md).

## 2. Test levels

| Level | What it verifies | Tool | Where |
|---|---|---|---|
| dbt data tests | Uniqueness, accepted values, relationships between tables and row reconciliation in each model | dbt Core | `dbt/tests/`, models of `dbt/models/` |
| Figure audit | Weekly prices are rebuilt from the raw rows; the reference figures of the panel are reproduced | pytest | `tests/test_data_audit.py`, `tests/test_reconciliation.py` |
| Parity | The Python ETL and dbt produce the same prices, dimensions and rejections | pytest | `tests/test_migration_parity.py` |
| Publication gate | A load with failed tests or with far fewer rows does not replace the served database | pytest | `tests/test_pipeline_gate.py` |
| CPI and real prices | The weekly factor, the reference month and the provisional weeks | pytest | `tests/test_ipc_audit.py` |
| Panel | Each page draws without errors and shows what its decision requires | pytest with Streamlit's AppTest | `tests/test_dashboard.py` and the tests of each view |
| Diagrams | Each piece drawn exists in the code, the workflow or the database | pytest | `tests/test_devops.py`, `tests/test_monitoring.py`, `tests/test_stack_page.py` and similar |
| Documents | Requirements traceability, figures against the database, structure and wording | pytest | `tests/test_documents.py`, `tests/test_prd_traceability.py` |
| Screen measurement | Horizontal overflow and height of each page at several window sizes | Playwright, outside the project | `tests/medicion/medir.cjs` |

## 3. Environment and execution

| Element | Value |
|---|---|
| Python | 3.11 or 3.12 for the pipeline with dbt; the panel and the tests also run on newer versions |
| Dependencies | `requirements.txt` (panel and tests) and `requirements-pipeline.txt` (dbt) |
| Database | The served database, downloaded with `python bi/served_database.py` |
| Raw data | `etl/raw.db`, only on the author's computer and on the machine of each load; without it, the tests that rebuild from the raw rows are skipped |
| Local execution | `python -m pytest -q` |
| Continuous execution | `pruebas.yml` on every push and pull request: compiles dbt (`dbt parse`) and runs pytest |
| Before publishing | `semanal.yml` runs pytest on the new database, including parity |

## 4. Entry and exit criteria

| Moment | Criterion |
|---|---|
| Entry | The change compiles (`dbt parse`) and the served database is available |
| Exit of a change | The full suite passes in `pruebas.yml` |
| Exit of a load | The dbt tests pass, the load reads at least 90 % of the rows of the previous one and pytest passes on the new database |
| Change of behavior | It has its entry in `docs/DECISIONES.md` and its tests |

## 5. Traceability

Each business question and each requirement of the [PRD](PRD.md#6-requirements) names the test that verifies it, and `tests/test_prd_traceability.py` requires each one to exist.

## 6. Risks and limits

| Risk or limit | Mitigation |
|---|---|
| Without `etl/raw.db`, the rebuild from raw rows does not run in `pruebas.yml` | It runs on the author's computer and in each weekly load, where the raw data exists |
| The tests that query public links depend on the network | A failed result is repeated before treating it as a defect of the code |
| The screen measurement is not part of the suite | It runs before each visual change |

## 7. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 8. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-25 | First version (D-279, professional documentation) |
