# Security Test Plan

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Security Test Plan |
| Version | 2.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | Define how it is verified, with repeatable tests, that the security controls of the system are still in force. |
| Audience | Security, architecture, operations and technical review. |
| Related documents | [Software Architecture Document (SAD)](SAD.md) · [Test Plan](PLAN_PRUEBAS.md) · [Operations Runbook](MANUAL.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [Objective and scope](#1-objective-and-scope)
2. [Reference](#2-reference)
3. [Threat model](#3-threat-model)
4. [Test environment](#4-test-environment)
5. [Procedure](#5-procedure)
6. [Test cases](#6-test-cases)
7. [Acceptance criteria](#7-acceptance-criteria)
8. [Accepted risks and limits](#8-accepted-risks-and-limits)
9. [Glossary](#9-glossary)
10. [Version history](#10-version-history)

## 1. Objective and scope

**Objective:** check that a visitor cannot read the secrets, change the data or launch the pipeline without the control code.

**Scope:** everything reachable from the internet: the panel, the SQL queries studio (open to any visitor, because the data is public), the control code and the public code of the repository.

**Out of scope:** the GitHub and Streamlit Community Cloud accounts. Their own sign-in protects them, a configuration of each platform that cannot be verified from the repository.

## 2. Reference

The threats and the cases are classified according to the OWASP Top 10 (2021), the list of web application security risks of the Open Worldwide Application Security Project (OWASP).

## 3. Threat model

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

## 4. Test environment

| Element | Value |
|---|---|
| System | Any computer with Python 3.11 or 3.12, or a GitHub Actions machine (Ubuntu) |
| Dependencies | `requirements.txt` |
| Data | The served database (`python bi/served_database.py`); the tests create their own fake secret and never use the real one |
| Tool | pytest |
| Continuous execution | The `pruebas.yml` workflow runs the same tests on every push and pull request |

## 5. Procedure

[[diagrama:sop]]

| Step | Action | Detail |
|---|---|---|
| 1 | Prepare | Clone the repository and install `requirements.txt`; the tests create a fake secret |
| 2 | Run | `python -m pytest -q tests/test_security.py tests/test_control.py tests/test_sql_explorer.py tests/test_dashboard.py` |
| 3 | Check | Each case compares its result with the expected one and fails if it is not met |
| 4 | Record | The pytest output locally and, on GitHub, the result of `pruebas.yml` next to the commit; every fix is recorded in `docs/DECISIONES.md` |
| 5 | Decide | If it passes, the change is verified; if it fails, it is fixed and the procedure returns to step 2 |

## 6. Test cases

Common precondition: the environment of section 4, without the real secret.

| Case | Name | Steps | Expected result | OWASP | Test |
|---|---|---|---|---|---|
| S-01 | SQL that reads secrets | 19 SQL queries to read secrets or write files | Rejected; the secret never appears | A03 | `tests/test_security.py::test_the_filter_and_the_engine_stop_every_attack_on_the_server_files` |
| S-02 | Direct orders to the engine | 9 direct orders to the engine | Permission error | A05 | `tests/test_security.py::test_the_engine_refuses_even_if_the_filter_is_bypassed` |
| S-03 | Endless queries | Endless queries or queries of millions of rows | Cut after 10 seconds; at most 5,000 rows | A04 | `tests/test_sql_explorer.py::test_slow_query_is_interrupted`, `tests/test_sql_explorer.py::test_result_is_limited_and_flagged` |
| S-04 | Code with ñ or emojis | Code with ñ, accents or emojis | «Clave incorrecta.» (wrong code), without an error | A07 | `tests/test_control.py::test_d199_the_right_code_opens_and_any_character_is_safe` |
| S-05 | Trying codes without stopping | Trying codes without stopping | «Clave incorrecta.» each time, without a lockout (accepted risk, section 8) | A07 | `tests/test_control.py::test_d249_there_is_no_limit_of_attempts_and_the_comparison_is_constant_time` |
| S-06 | Tokens in the repository | Search for tokens in the repository | None | A02 | `tests/test_security.py::test_no_secret_is_tracked_by_git` |
| S-07 | GitHub error | Provoke a GitHub error | The message never shows the token | A09 | `tests/test_control.py::test_github_error_never_shows_the_token` |
| S-08 | Workflow permissions | Abuse the permissions of the workflow | Only content and issues | A01 | `tests/test_security.py::test_the_weekly_job_has_least_privilege` |
| S-09 | Control without a test | Claim a control without a test | Each control of the security architecture points to a test that exists | — | `tests/test_security.py::test_every_control_of_the_map_points_to_a_test_that_exists` |
| S-10 | Pipeline without the code | Launch the pipeline without the code | The button does not exist before the code | A01 | `tests/test_dashboard.py::test_d202_the_manual_run_and_the_links_appear_only_behind_the_code` |

**Result obtained:** each case runs on every push; a case that does not meet its expected result makes `pruebas.yml` fail. The review of 2026-10-20 found an error of the control code with non-ASCII characters, fixed in D-199 (code with any character), and an inaccurate sentence of the SAD, fixed in D-200.

The interactive diagram of the cases, with each case on the technology it attacks, goes with this table:

[[diagrama:pruebas]]

## 7. Acceptance criteria

| Criterion | Verification |
|---|---|
| The ten cases meet their expected result | pytest green locally and in `pruebas.yml` |
| Each control points to a test that exists | Case S-09 |
| No secret in the repository | Case S-06 |

## 8. Accepted risks and limits

| Risk or limit | Decision | Condition |
|---|---|---|
| No limit of attempts for the control code | Risk accepted by the author (D-249, security as a process): the code only prevents pressing «Run pipeline now» by accident, and the most it allows is launching the workflow | The code must be long |
| The panel's GitHub token | Minimum permissions and renewal before expiry | The panel warns when fewer than 14 days are left |
| Two-step verification of the accounts | Declared by the author; not verifiable from the repository | Out of scope (section 1) |

Secret values and problems not yet fixed are not published.

## 9. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 10. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-20 | First version: security section with its view and its plan (D-201, D-202, D-204, D-205) |
| 1.1 | 2026-10-21 | Engineering-document wording (D-210, D-214, D-217, D-218) |
| 1.2 | 2026-10-23 | Security as a process, procedure and accepted risks (D-249) |
| 1.3 | 2026-10-24 | The ten cases in a diagram and the procedure as a cycle (D-258) |
| 2.0 | 2026-10-25 | Self-contained document: reference, threat model, controls, environment, cases with their test and acceptance criteria (D-279, professional documentation) |
