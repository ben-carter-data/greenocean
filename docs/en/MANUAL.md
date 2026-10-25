# Operations Runbook

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Operations Runbook |
| Version | 2.0 |
| Date | 2026-10-25 |
| Status | Current |
| Owner | The author |
| Purpose | State what happens automatically, what is checked and when, and what to do about each failure. |
| Audience | Operation of the project, also without technical training. |
| Related documents | [Software Architecture Document (SAD)](SAD.md) · [Security Test Plan](SEGURIDAD.md) · [Glossary](GLOSARIO.md) |

## Contents

1. [What happens automatically](#1-what-happens-automatically)
2. [What is checked and when](#2-what-is-checked-and-when)
3. [Failures of the weekly load](#3-failures-of-the-weekly-load)
4. [Failures of the published panel](#4-failures-of-the-published-panel)
5. [Recovery](#5-recovery)
6. [Periodic tasks](#6-periodic-tasks)
7. [Author access and administration](#7-author-access-and-administration)
8. [Known limits](#8-known-limits)
9. [Glossary](#9-glossary)
10. [Version history](#10-version-history)

## 1. What happens automatically

The weekly job (`.github/workflows/semanal.yml`) runs every Tuesday at 12:00 UTC: 09:00 in Chilean summer time and 08:00 in winter time. It downloads the sources, builds and tests the database, publishes it in the «base-actual» release and creates the weekly report. The full sequence, step by step, is in the [runtime view of the SAD](SAD.md#6-runtime-view).

It can also be launched by hand: from «Operations center», with the «Run pipeline now» button (it requires the control code), or from the workflow page on GitHub.

If a step fails, the following ones do not run and the served database does not change ([ADR-11 · Publish only if the tests pass](ADR.md#adr-11--publish-only-if-the-tests-pass)).

## 2. What is checked and when

| When | What is checked | Where |
|---|---|---|
| Every Tuesday, after 12:00 UTC | That the run ended green | «Operations» tab of «Operations center», or the GitHub email if it failed |
| Every Tuesday | That the issue «Informe semanal YYYY-MM-DD» (weekly report) exists | Issues of the repository |
| When in doubt about the figures | The quality verdict and the audit controls | «Quality and audit» |

## 3. Failures of the weekly load

Each row is a step of the workflow, with its name in `semanal.yml`. The warning reaches the author through GitHub's «Run failed: semanal» email, and the failed step shows in red in «Operations center». The `etl_run` table records only the published loads: the message of a failure is read in the log of the step.

| Step | Symptom | Probable cause | Action |
|---|---|---|---|
| Restore the closed-year files | The step ends with an error | A problem with the GitHub cache | Launch the job again; without the cache, the download fetches every year |
| Get the published database | The step cannot download the database or its fingerprint does not match | The «base-actual» release is not available or its file changed | Check the release on GitHub; if it is missing, publish the database again from a verified local copy |
| Download the ODEPA files | `DOWNLOAD_ERROR` or `UNEXPECTED_HEADER` in the log | ODEPA did not respond, or changed the columns of a file | With `DOWNLOAD_ERROR`, wait a few hours and launch again; with `UNEXPECTED_HEADER`, check the file and adapt the agent |
| Run the ETL (SQLite backup) | `MISSING_WEEKS`, `UNKNOWN_REGION`, `UNKNOWN_CHANNEL` or `DUPLICATE_KEYS` in the log | A week is missing outside the known gaps, ODEPA added a region or a channel, or there are repeated prices | Check the file at ODEPA; a new region or channel is added to the lists of the ETL; a week missing at the source is recorded as a known gap with its decision |
| Build the data warehouse with dbt | A dbt model or test fails, or `TOO_FEW_ROWS` | A business rule is not met, or the load read less than 90 % of the previous one | Read in the log which model or test failed; it usually names the table and the rule |
| Run the tests against the new database | A pytest test fails | The new data breaks something the code assumes, or the backup and the served database do not match | Read which test failed; it usually names the product or the week |
| Publish the database | GitHub rejects the upload of the file or of the pointer | Workflow permissions, or a change on `main` during the load | Check Settings → Actions → Workflow permissions («Read and write») and launch again |
| Publish the weekly report | The issue is not created | Workflow permissions | Check the permissions; the database is already published |

## 4. Failures of the published panel

| Symptom | Probable cause | Action |
|---|---|---|
| After a push, a page shows `AttributeError` | Streamlit Cloud combined new files with others it had in memory (it happened on 2026-10-12) | In the panel, «Manage app» → ⋮ → **Reboot**, and wait one or two minutes |
| «Operations center» says GitHub did not respond | Without a token, GitHub allows 60 requests per hour, shared by the apps of the same server | None: the panel shows the last saved response and asks again every 5 minutes; with the token configured, the limit rises |
| The panel reports that it does not have the served database | It could not download it from the release when it started | Check that the «base-actual» release exists; the panel downloads it on the next visit |
| The «Run pipeline now» button says the token is missing | The panel's token expired or is not configured | Create a token allowed to launch workflows of this repository and store it as `GITHUB_TOKEN` in the app secrets on Streamlit |

## 5. Recovery

| Situation | Procedure |
|---|---|
| A load failed | Fix the cause as in section 3 and launch the job again; meanwhile, the panel shows the last valid load |
| The release lost its file | Rebuild the database on a computer with the data (`python etl/pipeline.py --local`), check that the suite passes and upload the file to the «base-actual» release together with its pointer (`python bi/served_database.py --pointer`) |
| A new copy of the repository has no database | `python bi/served_database.py` downloads the database of the last load and verifies its fingerprint |

## 6. Periodic tasks

| Frequency | Task |
|---|---|
| Every Tuesday | Check «Operations center» or the email; if it is green, there is nothing to do |
| Every January | Add to `agent/input.csv` the two lines of the new year (wholesale and consumer), with the URL ODEPA publishes on the page of each dataset |
| Periodically | Copy `agent/downloads` to another disk: the CSV files are not versioned ([ADR-04 · Do not commit the raw data to the repository](ADR.md#adr-04--do-not-commit-the-raw-data-to-the-repository)) and the GitHub cache is deleted if it is not used for 7 days |
| Before it expires | Renew the panel's GitHub token; the panel warns when fewer than 14 days are left |

## 7. Author access and administration

In «Operations center», «Author access» asks for the control code (the panel's `CONTROL_CODE` secret) and opens with Enter. With the right code, the «Run pipeline now» button, the token-expiry warning and the administration links appear (GitHub tokens, runs and the administration of the app on Streamlit). Without the secret configured, for example in a local copy, the access stays closed.

The code prevents accidental runs; it is not the main barrier. What protects the project is the author's sign-in on GitHub and Streamlit (with two-step verification) and a token with the minimum permissions. There is no limit of attempts for the code: it is an accepted risk, described in the [Security Test Plan](SEGURIDAD.md). The panel never shows the token or any part of it.

## 8. Known limits

| Limit | Value | Source |
|---|---|---|
| Maximum size of a release file | 2 GB; the served database weighs about 14 MB | GitHub documentation on releases, read on 2026-10-24 |
| GitHub Actions cache | Deleted if it is not used for 7 days; that week the job downloads every year | GitHub Actions documentation, read on 2026-10-24 |
| GitHub API requests without a token | 60 per hour | GitHub API documentation |
| Cloud architecture | Not adopted while the data is public, weekly and small | [ADR-31 · Do not use a cloud data warehouse](ADR.md#adr-31--do-not-use-a-cloud-data-warehouse) and [Capacity and Scalability Plan](ESCALABILIDAD.md) |

## 9. Glossary

The acronyms and terms of this document are defined in the [Glossary](GLOSARIO.md).

## 10. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-12 | First version, as a page of the project (D-043) |
| 1.1 | 2026-10-16 | Side-menu navigation and new pages (D-090 to D-099) |
| 1.2 | 2026-10-17 | Documentation and sources reorganized (D-105, D-106, D-110, D-118) |
| 1.3 | 2026-10-19 | Operations center and operation of the load |
| 1.4 | 2026-10-20 | SQL queries (D-184, D-185) |
| 1.5 | 2026-10-21 | Quality and audit in one view (D-220) |
| 1.6 | 2026-10-23 | Security as a process and monitoring (D-249); download as the printed page (D-248) |
| 1.7 | 2026-10-24 | Deployment and pipeline (D-251, D-255); Stack and evidence (D-266); served database in a release (D-270) |
| 2.0 | 2026-10-25 | Runbook format: symptom, cause, action, recovery, periodic tasks and limits with their source (D-279, professional documentation) |
