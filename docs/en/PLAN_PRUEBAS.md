# Test and Security Plan

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Test and security plan |
| Version | 3.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Explain how we check that each figure is correct, that a load with errors is never published and that nobody can read the secrets, change the data or launch the load without permission. |
| Audience | Management, quality, security, operations and technical review. |
| Related documents | [Product Requirements Document (PRD)](PRD.md) · [Software Architecture Document (SAD)](SAD.md) · [Operations Runbook](MANUAL.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [In summary](#1-in-summary)
2. [What is tested](#2-what-is-tested)
3. [Who takes part in security](#3-who-takes-part-in-security)
4. [Threats and controls](#4-threats-and-controls)
5. [Security cases](#5-security-cases)
6. [Procedure](#6-procedure)
7. [A manual load, step by step](#7-a-manual-load-step-by-step)
8. [A code change, step by step](#8-a-code-change-step-by-step)
9. [Environment and execution](#9-environment-and-execution)
10. [Acceptance criteria](#10-acceptance-criteria)
11. [Accepted risks and limits](#11-accepted-risks-and-limits)
12. [Traceability](#12-traceability)
13. [Glossary](#13-glossary)
14. [Version history](#14-version-history)

## 1. In summary

The tests of GreenOcean answer three questions, always automatically:

- **Are the figures correct?** Each price is recomputed from the ODEPA files and along a second, independent path; the result must match.
- **Can a load with errors reach the panel?** No: if a test fails, the load stops and the panel keeps the last valid database.
- **Can anyone abuse the system?** Ten attacks (S-01 to S-10) are repeated on every code change: reading secrets, hanging the panel, launching the load without the code or stealing the token.

[[diagrama:niveles]]

## 2. What is tested

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

## 3. Who takes part in security

[[diagrama:actores]]

Security does not depend on hiding the code, which is public, but on four actors and on what each one can do:

- **The visitor** reads the panel and uses the SQL studio without an account: the data is public, and the database is read-only.
- **The author** maintains the code and the secrets; with the control code, the author opens the «Run pipeline now» button. The author signs in to GitHub and Streamlit with their own account, with two-step verification.
- **Streamlit Community Cloud** keeps the panel's secrets (the GitHub token and the control code), outside the repository, and publishes the panel from `main`.
- **GitHub** keeps the code, with no secret in it, and runs the weekly workflow with the least privileges: write content and create issues.

## 4. Threats and controls

The threats and the cases are classified according to the OWASP Top 10 (2021), the list of web application security risks of the Open Worldwide Application Security Project (OWASP).

| Threat | Description | OWASP | Controls that mitigate it |
|---|---|---|---|
| T1 | Read secrets or server files with SQL | A03 · A05 | Public SQL with limits, Read-only database |
| T2 | Hang the panel with heavy queries | A04 | Public SQL with limits |
| T3 | Launch the pipeline without permission | A01 · A07 | Control code |
| T4 | Steal the token or the code | A02 · A09 | Protected token, No secret in Git |
| T5 | Abuse the permissions of the workflow | A01 | Least privilege of the job |
| T6 | Take over the administration of GitHub or Streamlit | A07 | External sign-in |

| Control | What it consists of | Where it is |
|---|---|---|
| Public SQL with limits | A single read statement, with no files or web addresses; it is cut at 10 s, returns at most 5,000 rows and uses at most 1 GB of memory | `bi/sql_explorer.py` |
| Read-only database | Engine without external access and with its configuration locked | `bi/queries.py`, `bi/sql_explorer.py` |
| Control code | Prevents accidental runs; compared in constant time | `bi/control.py`, `bi/dashboard.py` |
| Protected token | Never appears on screen or in error messages; the panel warns before it expires | `bi/control.py` |
| No secret in Git | The repository is public; the secrets live on the panel's platform | `.gitignore` |
| Least privilege of the job | The weekly workflow can only write content and create issues | `.github/workflows/semanal.yml` |
| External sign-in | Declared by the author; not verifiable from the repository | GitHub and Streamlit configuration |

The graphic representation of the trust zones, the controls and the threats is in [[vista:Security architecture]].

## 5. Security cases

Common precondition: the environment of section 9, without the real secret.

| Case | Name | Steps | Expected result | OWASP | Test |
|---|---|---|---|---|---|
| S-01 | SQL that reads secrets | 19 SQL queries to read secrets or write files | Rejected; the secret never appears | A03 | `tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files` |
| S-02 | Direct orders to the engine | 9 direct orders to the engine | Permission error | A05 | `tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed` |
| S-03 | Endless queries | Endless queries or queries of millions of rows | Cut after 10 seconds; at most 5,000 rows | A04 | `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged` |
| S-04 | Code with ñ or emojis | Code with ñ, accents or emojis | «Clave incorrecta.» (wrong code), without an error | A07 | `tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe` |
| S-05 | Trying codes without stopping | Trying codes without stopping | «Clave incorrecta.» each time, without a lockout (accepted risk, section 11) | A07 | `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| S-06 | Tokens in the repository | Search for tokens in the repository | None | A02 | `tests/test_security.py::test_no_secret_is_tracked_by_git` |
| S-07 | GitHub error | Provoke a GitHub error | The message never shows the token | A09 | `tests/test_control.py::test_github_error_never_shows_the_token` |
| S-08 | Workflow permissions | Abuse the permissions of the workflow | Only content and issues | A01 | `tests/test_security.py::test_the_weekly_job_has_least_privilege` |
| S-09 | Control without a test | Claim a control without a test | Each control of the security architecture points to a test that exists | — | `tests/test_security.py::test_every_control_of_the_map_points_to_a_test_that_exists` |
| S-10 | Pipeline without the code | Launch the pipeline without the code | The button does not exist before the code | A01 | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code` |

**Result obtained:** each case runs on every push; a case that does not meet its expected result makes `pruebas.yml` fail. The review of 2026-10-20 found an error of the control code with non-ASCII characters, fixed in D-199 (code with any character), and an inaccurate sentence of the SAD, fixed in D-200.

The interactive diagram of the cases, with each case on the technology it attacks, goes with this table:

[[diagrama:pruebas]]

## 6. Procedure

[[diagrama:sop]]

| Step | Action | Detail |
|---|---|---|
| 1 | Prepare | Clone the repository and install `requirements.txt`; the tests create a fake secret |
| 2 | Run | `python -m pytest -q tests/test_security.py tests/test_control.py tests/test_sql_explorer.py tests/test_dashboard.py` |
| 3 | Check | Each case compares its result with the expected one and fails if it is not met |
| 4 | Record | The pytest output locally and, on GitHub, the result of `pruebas.yml` next to the commit; every fix is recorded in `docs/DECISIONES.md` |
| 5 | Decide | If it passes, the change is verified; if it fails, it is fixed and the procedure returns to step 2 |

## 7. A manual load, step by step

[[diagrama:secuencia_manual]]

The «Run pipeline now» button does not exist until the author types the control code. The code is compared in constant time, and the token, which never appears on screen or in error messages, only serves to launch the workflow.

## 8. A code change, step by step

[[diagrama:secuencia_ci]]

Each change runs the same tests on a clean GitHub machine. Its result stays next to the commit; Streamlit publishes `main` without waiting for it, an accepted risk described in section 11.

## 9. Environment and execution

| Element | Value |
|---|---|
| System | Any computer with Python 3.11 or 3.12, or a GitHub Actions machine (Ubuntu); the panel and the tests also run on newer versions |
| Dependencies | `requirements.txt` (panel and tests) and `requirements-pipeline.txt` (dbt) |
| Database | The served database, downloaded with `python bi/served_database.py` |
| Raw data | `etl/raw.db`, only on the author's computer and on the machine of each load; without it, the tests that rebuild from the raw rows are skipped |
| Secrets | The tests create their own fake secret and never use the real one |
| Local execution | `python -m pytest -q` |
| Continuous execution | `pruebas.yml` on every push and pull request: it compiles dbt (`dbt parse`) and runs pytest |
| Before publishing | `semanal.yml` runs pytest on the new database, parity included |

## 10. Acceptance criteria

| Moment | Criterion | Verification |
|---|---|---|
| Entry | The change compiles and the served database is available | `dbt parse` |
| Exit of a change | The full suite passes, the ten security cases included | `pruebas.yml` green |
| Exit of a load | The dbt tests pass, the load reads at least 90 % of the rows of the previous one and pytest passes on the new database | `semanal.yml` |
| Security | Each control points to a test that exists and no secret is in the repository | Cases S-09 and S-06 |
| Change of behavior | It has its entry in `docs/DECISIONES.md` and its tests | The author's review |

## 11. Accepted risks and limits

| Risk or limit | Decision or mitigation |
|---|---|
| Without `etl/raw.db`, the rebuild from raw rows does not run in `pruebas.yml` | It runs on the author's computer and on each weekly load, where the raw data exists |
| The tests that query public links depend on the network | A failed result is repeated before treating it as a defect of the code |
| The screen measurement is not part of the suite | It runs before each visual change |
| No limit of attempts for the control code | Risk accepted by the author (D-249): the code only prevents pressing «Run pipeline now» by accident, the most it allows is launching the workflow, and it must be long |
| The panel's GitHub token | Minimum permissions and renewal before expiry; the panel warns when fewer than 14 days are left |
| Streamlit publishes `main` without waiting for `pruebas.yml` | The author reviews locally before each push |
| Two-step verification of the accounts | Declared by the author; not verifiable from the repository |

Secret values and problems not yet fixed are not published.

## 12. Traceability

Each business question and each requirement of the [PRD](PRD.md#5-requirements) names the test that verifies it, and `tests/test_prd_traceability.py` requires each one to exist.

## 13. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 14. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-20 | First version: security section with its view and its plan (D-201, D-202, D-204, D-205) |
| 1.1 | 2026-10-21 | Engineering-document wording (D-210, D-214, D-217, D-218) |
| 1.2 | 2026-10-23 | Security as a process, procedure and accepted risks (D-249) |
| 1.3 | 2026-10-24 | The ten cases in a diagram and the procedure as a cycle (D-258) |
| 2.0 | 2026-10-25 | Self-contained document: reference, threat model, controls, environment, cases with their test and acceptance criteria (D-279, professional documentation) |
| 2.1 | 2026-10-25 | The Test Plan, version 1.0, starts as a separate document (D-279) |
| 3.0 | 2026-10-25 | A single document for the tests and security: what is tested, who takes part, threats, cases, procedure and the sequences of a manual load and of a code change (D-290, documents for every reader) |
