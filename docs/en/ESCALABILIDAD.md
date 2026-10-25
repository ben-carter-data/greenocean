# Capacity and Scalability Plan

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Capacity and Scalability Plan |
| Version | 2.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Measure the current capacity, anticipate what gives way first if the system grows and set the thresholds that would justify changing the architecture. |
| Audience | Architecture, management and operations. |
| Related documents | [Software Architecture Document (SAD)](SAD.md) · [Architecture Decision Records (ADR)](ADR.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [Current capacity](#1-current-capacity)
2. [What gives way first](#2-what-gives-way-first)
3. [Growth options](#3-growth-options)
4. [When a cloud would be justified](#4-when-a-cloud-would-be-justified)
5. [Glossary](#5-glossary)
6. [Version history](#6-version-history)

## 1. Current capacity

| Measure | Value | Origin |
|---|---|---|
| Served database | About 14 MB in the served database | Size of `etl/datos.duckdb` |
| Data | Volume and coverage of the last load | [PRD, section 3](PRD.md#3-scope) |
| Frequency | One load per week | [RF-01](PRD.md#6-requirements) |
| Users | One public, read-only panel | [PRD, section 4](PRD.md#4-users-and-use-cases) |

## 2. What gives way first

| Limit | Current situation | Planned response |
|---|---|---|
| Size of the served database | A single copy in a release, replaced by each load ([ADR-35](ADR.md#adr-35--publish-the-served-database-in-a-release-that-each-load-replaces)); the Git history no longer grows with the data | A release file can hold up to 2 GB; long before that, the option of section 4 would be advisable |
| Duration of the load | Each load rebuilds the whole history since 2022 ([ADR-10](ADR.md#adr-10--rebuild-everything-on-each-load)) and takes a little longer every year | Incremental loads when the duration justifies them |
| Simultaneous visitors | A free Streamlit app that reads a small file read-only | If several teams used it daily, the free plan would not be enough: it is one of the thresholds of section 4 |

## 3. Growth options

A new source is added like the current ones: a folder in bronze and its dbt models, without changing the existing ones.

| Extension | Status | How it would be added |
|---|---|---|
| Weather by region and week | Planned; official source to be defined | A staging model and a mart by week and region, next to the price alerts, without claiming that the weather causes a price |
| Cloud data warehouse | Not adopted ([ADR-31](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse)) | A new target in the dbt configuration, with the same models and the same audit |

## 4. When a cloud would be justified

With public, weekly and small data, read by a single panel, a cloud data warehouse would add cost, secrets and expiry risks with no benefit ([ADR-31](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse)). It would be justified if a company added its own data:

| Criterion | Today | Threshold |
|---|---|---|
| Volume | About 14 MB | Several GB: sales by store and day, costs, inventory |
| Users | One read-only panel | Several teams or BI tools on the same data |
| Access | Public | Permissions per person or sensitive data |
| Freshness | Weekly | Several loads a day or real time |

## 5. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 6. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-21 | First version, as a section of the decision log (D-210) |
| 1.1 | 2026-10-24 | What gives way first and what would be added (D-269); served database in a release (D-270) |
| 2.0 | 2026-10-25 | Own document with current capacity, limits, options and thresholds (D-279, professional documentation) |
