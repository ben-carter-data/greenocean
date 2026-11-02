# Operations Runbook

| Field | Value |
|---|---|
| Project | GreenOcean |
| Document type | Operations Runbook |
| Version | 3.13 |
| Date | 2026-11-02 |
| Status | Current |
| Owner | The author |
| Purpose | State what happens automatically, what is checked and when, and what to do about each failure. |
| Audience | Whoever operates the project, also without technical training. |
| Related documents | [Software Architecture Document (SAD)](../arquitectura/SAD.md) · [Test and Security Plan](../calidad/PLAN_PRUEBAS.md) · [Glossary](../negocio/GLOSARIO.md) |

## Contents

1. [In summary](#1-in-summary)
2. [What happens automatically](#2-what-happens-automatically)
3. [What is checked and when](#3-what-is-checked-and-when)
4. [Failures of the weekly load](#4-failures-of-the-weekly-load)
5. [Failures of the published panel](#5-failures-of-the-published-panel)
6. [Recovery](#6-recovery)
7. [Author access and administration](#7-author-access-and-administration)
8. [GitHub guide](#8-github-guide)
9. [Failure register](#9-failure-register)
10. [Known limits](#10-known-limits)
11. [Glossary](#11-glossary)
12. [Version history](#12-version-history)

## 1. In summary

GreenOcean almost runs itself. Every Tuesday the load runs without intervention. If something fails, the panel keeps showing the last valid load: a half-finished figure is never published.

The operations work comes down to looking at one result a week, four tasks on the calendar and, if a failure warning arrives, following the table of section 4. The warning arrives in three ways:

- GitHub's email.
- The red run on GitHub.
- Inside the panel, a red notice above the menu on every page, with a link to the step that failed.

[[diagrama:calendario]]

## 2. What happens automatically

The weekly job (`.github/workflows/semanal.yml`) runs every Tuesday at 12:00 UTC: 09:00 in Chilean summer time and 08:00 in winter time. It downloads the sources, builds and tests the database, publishes it in the «base-actual» release and creates the weekly report. The full sequence, step by step, is in the [load sequence of the SAD](../arquitectura/SAD.md#4-the-load-of-each-week).

It can also be launched by hand: from «Operations center», with the «Run pipeline now» button (it requires the control code), or from the workflow page on GitHub. The run's window shows the live flow on top, focused on the load: which piece works and which message travels at each step (D-413).

If a step fails, the following ones do not run and the served database does not change ([ADR-11 · Publish only if the tests pass](../arquitectura/ADR.md#adr-11--publish-only-if-the-tests-pass)).

After every load that ends in green, the quality workflow proposes the weekly quality report, with the 3 data indicators, as the pull request «Actualizar medición de calidad» (D-431). On every push it only measures, and fails if a code indicator is past its acceptable.

## 3. What is checked and when

| When | What is checked or done | Where |
|---|---|---|
| Every Tuesday, after 12:00 UTC | That the run ended green | «Operations» tab of «Operations center», or the GitHub email if it failed |
| Every Tuesday | That the issue «Informe semanal YYYY-MM-DD» (weekly report) exists, the only open one: the previous one is closed with a link to the new one (D-438) | Issues of the repository |
| When in doubt about the figures | The quality verdict and the audit controls | «Quality and audit» |
| Every January | Add to `agent/input.csv` the two lines of the new year (wholesale and consumer), with the URL ODEPA publishes on the page of each dataset | `agent/input.csv` |
| Periodically | Copy `agent/downloads` to another disk: the CSV files are not versioned ([ADR-04 · Do not commit the raw data to the repository](../arquitectura/ADR.md#adr-04--do-not-commit-the-raw-data-to-the-repository)) and the GitHub cache is deleted if it is not used for 7 days | Another disk of the author |
| Before it expires | Renew the panel's two GitHub tokens; «Settings» marks them amber when 15 days or fewer are left, and the alert «Action required» warns on entering as Author (section 8.1) | App secrets on Streamlit |
| After every weekly load | The pull request «Actualizar medición de calidad»: merge it or close it, delete its branch and run `git pull` | Pull requests of the repository (section 8) |
| On entering as Author | The alert «Action required»: first, each token at 15 days or fewer from its expiry; then, the indicators past their acceptable. If it says «Last measurement on …», the report is more than 8 days old and is not today's state | The window the panel opens |

## 4. Failures of the weekly load

[[diagrama:arbol_fallas]]

Each row is a step of the workflow, with its name in `semanal.yml`. The warning reaches the author through GitHub's «Run failed: semanal» email and, in the panel, as a red notice above the menu of every page. The failed step shows in red in «Operations center». The `etl_run` table records only the published loads, so the message of a failure is read in the log of the step.

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

A week a source has not published yet is not a failure. The load publishes up to the last week complete in both sources, and the Dashboard says so. What does stop the load is `MISSING_WEEKS` (a week missing in the middle of the data) and `LATE_SOURCE` (a source has gone more than 2 weeks without publishing). In those cases, check ODEPA and fill nothing in: the load comes back by itself when the source publishes.

Each dependency of `requirements.txt` and `requirements-pipeline.txt` has a maximum version, so that a new version does not break Tuesday's load (D-435). To use a new version, its cap is raised with a push: the CI tests it before the next load.

To read any failure without copying by hand, the panel's page «GitHub Actions», in the Author view, shows the job, the step, the failing tests and the end of the log, with «Copy». To see which step a load is at, without logs and in any view, there is the live flow of «Stack and evidence» (D-412).

## 5. Failures of the published panel

| Symptom | Probable cause | Action |
|---|---|---|
| After a push, a page shows `AttributeError` | Streamlit Cloud combined new files with others it had in memory (it happened on 2026-10-12) | In the panel, «Manage app» → ⋮ → **Reboot**, and wait one or two minutes |
| «Operations center» says GitHub did not respond | Without a token, GitHub allows 60 requests per hour, shared by the apps of the same server | None: the panel shows the last saved response and asks again every 5 minutes; with the token configured, the limit rises |
| The panel reports that it does not have the served database | It could not download it from the release when it started | Check that the «base-actual» release exists; the panel downloads it on the next visit |
| The «Run pipeline now» button says the token is missing | The panel's token expired or is not configured | Create a token allowed to launch workflows of this repository and store it as `GITHUB_TOKEN` in the app secrets on Streamlit |

## 6. Recovery

[[diagrama:secuencia_recuperacion]]

| Situation | Procedure |
|---|---|
| A load failed | Fix the cause as in section 4 and launch the job again; meanwhile, the panel shows the last valid load |
| A manual load hangs | In the run's window, «Cancelar» and confirm; if it does not answer, GitHub cuts it after 20 minutes |
| The release lost its file | Rebuild the database on a computer with the data (`python etl/pipeline.py --local`), check that the suite passes and upload the file to the «base-actual» release together with its pointer (`python bi/served_database.py --pointer`) |
| A new copy of the repository has no database | `python bi/served_database.py` downloads the database of the last load and verifies its fingerprint |

## 7. Author access and administration

The panel has one key only: the one to enter as Author (the panel's `CONTROL_CODE` secret), in the window to choose the view (D-369, D-421). With it the section «DevOps and security» appears, which only the Author sees (D-420): in «Operations center», the «Run pipeline now» button, which starts the load at once, and the token-expiry warning; cancelling a load asks for a confirmation in the same window. The page «Settings» is in that section. That page gathers on one screen the state of the tokens, the latest load, the latest report, the tests and the sources; what to do in each case (section 8.1), and the maintenance tasks. Without the secret configured, for example in a local copy, the access stays closed.

The code prevents accidental runs; it is not the main barrier. What protects the project is the author's sign-in on GitHub and Streamlit (with two-step verification) and a token with the minimum permissions. After 3 failures, each try waits 2 s, and twice as long after each new failure, up to 15 min; the right code resets it (D-393, [Test and Security Plan](../calidad/PLAN_PRUEBAS.md#11-accepted-risks-and-limits)). Each action of the Author (starting, cancelling, reloading the data) checks again on the server that the session is the Author's (D-421). If the wait jams the access, the load can be started from GitHub. The panel never shows the token or any part of it.

To enter: in the window to choose the view, the link «Author access», in its corner, the key and Enter (D-369). The «View» button, under the logo, changes the view; a click on the logo does the same (D-373). Leaving Author closes its session. Every reload of the tab (opening or printing a document, changing the theme, a link such as the one in the «Action required» alert, F5) keeps the view, the Author's too, with a ticket the server issues and checks, valid while the Author's session lasts (D-427, D-428, D-430); only a new tab asks for it again.

The panel uses three secrets, kept in Streamlit (section 8):

- `CONTROL_CODE`: the author's key.
- `GITHUB_TOKEN`: starts the load, reads its state and logs, and cancels it.
- `GITHUB_READ_TOKEN`: read only, for the page «GitHub Actions». If it is missing, the page shows the states without logs and the notice «The read-only token is missing».

## 8. GitHub guide

The links used to run the project, grouped by task.

| Task | Link | What it is for | When to use it | What to click |
|---|---|---|---|---|
| Check failures | [Actions](https://github.com/ben-carter-data/greenocean/actions) | See every run of the three workflows and its state | When the «Run failed» email or the panel's red notice arrives | The red run → the job → the red step |
| Check failures | [Weekly load](https://github.com/ben-carter-data/greenocean/actions/workflows/semanal.yml) | Only the Tuesday loads and the manual ones | Every Tuesday, after 12:00 UTC | The latest run → «weekly-load» |
| Check failures | [Tests](https://github.com/ben-carter-data/greenocean/actions/workflows/pruebas.yml) | Lint, mypy and pytest of every push | After every push | The run of the commit → «pytest» or «lint» |
| Check failures | [Quality](https://github.com/ben-carter-data/greenocean/actions/workflows/calidad.yml) | The quality measure of every push and the weekly report | If the panel or the email warns of an indicator past its acceptable | The run → «medir» → the red step |
| Approve a report | [Pull requests](https://github.com/ben-carter-data/greenocean/pulls) | Review the quality report the workflow did not merge by itself | If it stayed open, with the code past its acceptable (D-436) | «Actualizar medición de calidad» → «Files changed» → «Merge pull request», or «Close pull request» |
| Approve a report | [Branches](https://github.com/ben-carter-data/greenocean/branches) | Delete the branch of a report already merged or closed | After merging or closing the pull request | The bin icon next to the branch «informe-calidad/…» |
| Settings | [Actions · General](https://github.com/ben-carter-data/greenocean/settings/actions) | Workflow permissions to write and open pull requests | If a publication or a pull request is rejected | «Workflow permissions» → «Read and write» and «Allow GitHub Actions to create and approve pull requests» |
| Settings | [Release «base-actual»](https://github.com/ben-carter-data/greenocean/releases/tag/base-actual) | The served database the panel reads | If the panel cannot find its database | Check that the file `datos.duckdb` is in «Assets» |
| Settings | [Issues](https://github.com/ben-carter-data/greenocean/issues) | The weekly report of every published load | Every Tuesday | «Informe semanal» with its date |
| The app | [Published panel](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app) | The app the User, the Professional and the Author see | After every push, to confirm the change | Choose the view; as Author, type the key and Enter |
| The app | [Streamlit Community Cloud](https://share.streamlit.io) | The panel's secrets and its restart | When renewing a token or if the panel shows a module error | The app → ⋮ → «Settings» → «Secrets», or «Reboot» |
| Tokens | [GitHub tokens](https://github.com/settings/personal-access-tokens) | The expiry and the permissions of each token | When «Settings» marks a token amber or red | The token → «Regenerate token»; the new value is shown only once |
| Tokens | [Create a token](https://github.com/settings/personal-access-tokens/new) | A new token, only for this repository | If a token is missing | «Repository access» → this repository; «Permissions» → «Actions» |

**Two rules.** Do not edit files on GitHub's website: every change is made on the author's computer and sent with a push, so local and remote main do not drift apart. After merging a pull request on the website, bring the change with `git pull` before working.

### 8.1 What to do in each case

Five cases, each with its steps in order. An automatic step is done by the system itself; a manual one is done by the author, with the link that leads to that place. The page «Settings» shows this same table.

| Case | Step | Type | What to do | Link |
|---|---|---|---|---|
| The load failed | 1 | Automatic | GitHub stops the next steps and the panel keeps showing the last valid load | — |
| The load failed | 2 | Automatic | The «Run failed: semanal» email arrives and the panel shows a red notice above the menu | — |
| The load failed | 3 | Manual | Read which step failed and the end of its log | [[vista:GitHub Actions]] |
| The load failed | 4 | Manual | Fix the cause following the table of section 4 | — |
| The load failed | 5 | Manual | Start the load again with «Run pipeline now», or with «Run workflow» on GitHub | [[vista:Operations center]] |
| A report arrived | 1 | Automatic | After every load in green, the quality workflow opens the pull request «Actualizar medición de calidad» with the weekly report; if an earlier report is still open, it closes and replaces it | — |
| A report arrived | 2 | Automatic | If the code indicators are within their acceptable, the workflow merges the pull request and deletes its branch, and the dashboard shows the report | — |
| A report arrived | 3 | Manual | If it stayed open, the code is past its acceptable: fix it and review the report in «Files changed» | [Pull requests](https://github.com/ben-carter-data/greenocean/pulls) |
| A report arrived | 4 | Manual | «Merge pull request» and delete the branch «informe-calidad/…» | [Pull requests](https://github.com/ben-carter-data/greenocean/pulls) |
| A report arrived | 5 | Manual | On the computer, bring the change with `git pull` | — |
| A token expires or is missing | 1 | Automatic | «Settings» marks the token amber when 15 days or fewer are left, and red if it expired or is missing; the alert «Action required» warns on entering as Author | [[vista:Settings]] |
| A token expires or is missing | 2 | Manual | On GitHub, regenerate the token or create a new one, only for this repository: «Actions: Read and write» for `GITHUB_TOKEN` and «Actions: Read» for `GITHUB_READ_TOKEN`. The value is shown only once: copy it | [GitHub tokens](https://github.com/settings/personal-access-tokens) |
| A token expires or is missing | 3 | Manual | On Streamlit Community Cloud: the app → ⋮ → «Settings» → «Secrets» | [Streamlit Community Cloud](https://share.streamlit.io) |
| A token expires or is missing | 4 | Manual | Paste the value into `GITHUB_TOKEN` or `GITHUB_READ_TOKEN` and press «Save» | — |
| A token expires or is missing | 5 | Manual | Press «Reboot» and confirm the new date in «Settings» | [[vista:Settings]] |
| A source is late | 1 | Automatic | The load publishes up to the last week complete in both sources and the Dashboard warns «ODEPA has not published the week of … yet» | [[vista:Dashboard]] |
| A source is late | 2 | Automatic | If the source has not published for more than 2 weeks, the load stops with `LATE_SOURCE` and the failure notice arrives | — |
| A source is late | 3 | Manual | Check on ODEPA whether the week is already published | [ODEPA open data](https://datos.odepa.gob.cl) |
| A source is late | 4 | Manual | Fill in nothing: the load resumes by itself when the source publishes | — |
| The app does not update | 1 | Automatic | After every push to main, Streamlit Community Cloud deploys the app again | — |
| The app does not update | 2 | Manual | Open the published panel and confirm the change arrived | [Published panel](https://monitor-precios-hito1-d4hfucgaifcebbwahgrzwf.streamlit.app) |
| The app does not update | 3 | Manual | If a page shows `AttributeError` or does not change: the app → ⋮ → «Reboot», and wait one or two minutes | [Streamlit Community Cloud](https://share.streamlit.io) |
| The app does not update | 4 | Manual | If the panel says it has no served database, check that `datos.duckdb` is in the release | [Release «base-actual»](https://github.com/ben-carter-data/greenocean/releases/tag/base-actual) |

## 9. Failure register

Every diagnosed and solved failure is recorded in `docs/calidad/plan_mitigacion.json` before the push that fixes it. Each occurrence has the date, what happened, the cause, what was done and a comment, in one line per field and in plain language; the long analysis goes in its decision D-xxx. The register reads in «Git workflow» → «Incident log». The Professional view shows what happened and how it was solved; only the Author sees the diagnosis.

## 10. Known limits

| Limit | Value | Source |
|---|---|---|
| Maximum size of a release file | 2 GB; the served database weighs about 14 MB | GitHub documentation on releases, read on 2026-10-24 |
| GitHub Actions cache | Deleted if it is not used for 7 days; that week the job downloads every year | GitHub Actions documentation, read on 2026-10-24 |
| GitHub API requests without a token | 60 per hour | GitHub API documentation |
| Cloud architecture | Not adopted while the data is public, weekly and small | [ADR-31 · Do not use a cloud data warehouse](../arquitectura/ADR.md#adr-31--do-not-use-a-cloud-data-warehouse) and [Capacity and growth in the SAD](../arquitectura/SAD.md#9-capacity-and-growth) |

## 11. Glossary

The acronyms and terms of this document are defined in the [Glossary](../negocio/GLOSARIO.md).

## 12. Version history

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
| 3.0 | 2026-10-25 | A summary at the start, the calendar, the fault tree and the recovery sequence as diagrams (D-290, documents for every reader) |
| 3.1 | 2026-10-30 | GitHub guide and failure register; late sources, the weekly quality report, the manual load window, entering as Author and the three secrets (D-339 to D-363) |
| 3.2 | 2026-10-31 | Wording reviewed; the 12 indicators of the quality plan (2); the token starts, follows and cancels the load (7); the three views (8, 9); the document moves to `docs/operacion/` (D-381, D-384, D-388) |
| 3.3 | 2026-11-01 | What to do in each case (8.1), which the page «Settings» reads; the two tokens in the GitHub guide (8) and their warning at 15 days (3, D-409) |
| 3.4 | 2026-11-01 | The alert «Action required» warns of each token at 15 days or fewer from its expiry (3, 8.1, D-410) |
| 3.5 | 2026-11-01 | The live flow in the manual load's window (2) and in «Stack and evidence» (4, D-412, D-413) |
| 3.6 | 2026-11-01 | One key only, the Author's, and each action checked on the server; the app's reloads keep the Author's view (7, D-421, D-427) |
| 3.7 | 2026-11-01 | Opening or printing a document keeps the view on Streamlit Community Cloud too, which loads the page twice (7, D-428) |
| 3.8 | 2026-11-01 | Every reload of the tab keeps the view, F5 and the link of the «Action required» alert too; only a new tab asks for it (7, D-430) |
| 3.9 | 2026-11-01 | The weekly quality report comes only after a load in green and measures the 3 data indicators (2, D-431) |
| 3.10 | 2026-11-01 | Each dependency has a maximum version; a new one comes in by raising its cap (4, D-435) |
| 3.11 | 2026-11-01 | The report's pull request is merged by itself if the code is within its acceptable (8, 8.1, D-436) |
| 3.12 | 2026-11-01 | The new weekly report closes the previous one (3, D-438) |
| 3.13 | 2026-11-02 | «Price overview» is renamed «Dashboard» and leads the menu (D-442) |
