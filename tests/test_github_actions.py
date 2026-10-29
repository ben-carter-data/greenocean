"""The read-only GitHub Actions reader (D-339): only GET, the token never leaves it, logs only with a token, and every
error says what to do."""

import inspect
import json
from datetime import datetime, timezone

import pytest
import requests

from bi import control, github_actions

# Fake tokens, built in parts so that no file of the repository holds a text shaped like a real one.
TOKEN = "github_pat_" + "FAKE0123456789ABCDEFGHIJKLMNOP"
READ_TOKEN = "github_pat_" + "READ0123456789ABCDEFGHIJKLMNO"
SHAPED = "ghp_" + "abcdefghijklmnopqrstuv"
BASE = f"{control.API_URL}/repos/{control.REPOSITORY}"


class Answer:
    def __init__(self, payload=None, status=200, text="", headers=None):
        self.payload, self.status_code, self.text, self.headers = payload, status, text, headers or {}

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}", response=self)


def run(number, conclusion="failure", status="completed", **extra):
    return {
        "id": number,
        "status": status,
        "conclusion": conclusion,
        "run_started_at": "2026-10-29T13:12:00Z",
        "updated_at": "2026-10-29T13:14:30Z",
        "head_sha": "843decdec105bd94ba10e66e535f75c8da174b61",
        "head_commit": {"message": "test(seguridad): una línea\n\ncuerpo"},
        "head_branch": "main",
        "event": "push",
        "html_url": f"https://github.com/{control.REPOSITORY}/actions/runs/{number}",
        **extra,
    }


LOG = (
    f"2026-10-29T13:13:00.1234567Z collected 996 items\n"
    f"2026-10-29T13:13:50.0000000Z \x1b[31mFAILED tests/test_a.py::test_one - AssertionError\x1b[0m\n"
    f"2026-10-29T13:13:50.0000001Z FAILED tests/test_b.py::test_two[es] - KeyError\n"
    f"2026-10-29T13:13:50.0000002Z FAILED tests/test_a.py::test_one - AssertionError\n"
    f"2026-10-29T13:13:51.0000000Z Authorization: Bearer {TOKEN}\n"
    f"2026-10-29T13:13:52.0000000Z token was {READ_TOKEN} and {SHAPED}\n"
    + "".join(f"2026-10-29T13:14:{n:02d}.0000000Z line {n}\n" for n in range(10, 70))
)


class Network:
    """A pretend GitHub: records every request, and fails the ones a test asks to fail."""

    def __init__(self, fail=None, logs=True, log=LOG):
        self.calls, self.fail, self.logs, self.log = [], fail or {}, logs, log

    def __call__(self, url, headers=None, params=None, timeout=None):
        self.calls.append((url, dict(headers or {})))
        path = url.removeprefix(control.API_URL)
        for needle, answer in self.fail.items():
            if needle in path:
                return answer
        if path.endswith("/rate_limit"):
            return Answer({}, headers={control.TOKEN_EXPIRATION_HEADER: "2026-12-31 12:00:00 UTC"})
        if "/workflows/" in path:
            return Answer({"workflow_runs": [run(3), run(2, "success"), run(1, None, "in_progress")]})
        if path.endswith("/jobs"):
            jobs = [
                {
                    "id": 77,
                    "name": "pytest (3.12)",
                    "conclusion": "failure",
                    "steps": [{"name": "Run pytest", "conclusion": "failure"}, {"name": "x", "conclusion": "success"}],
                }
            ]
            return Answer({"jobs": jobs + [{"id": 78, "name": "lint", "conclusion": "success", "steps": []}]})
        if path.endswith("/annotations"):
            return Answer(
                [
                    {"annotation_level": "failure", "message": "Process completed with exit code 1."},
                    {"annotation_level": "warning", "message": "Node.js 20 is deprecated"},
                ]
            )
        if path.endswith("/logs"):
            return Answer(text=self.log) if self.logs else Answer(status=404)
        raise AssertionError(f"unexpected request: {path}")


@pytest.fixture
def network(monkeypatch):
    fake = Network()
    monkeypatch.setattr(github_actions.requests, "get", fake)
    monkeypatch.setattr(control.requests, "get", fake)
    return fake


def test_d339_the_reader_only_reads_and_no_write_verb_exists_in_it():
    source = inspect.getsource(github_actions)
    for verb in ("requests.post", "requests.put", "requests.patch", "requests.delete", "requests.request"):
        assert verb not in source, verb
    assert source.count("requests.get(") == 1  # the only function that touches the network
    assert github_actions.CACHE_SECONDS == 120 and github_actions.LOG_LINES == 60


def test_d339_the_read_token_wins_over_the_usual_one_and_none_means_none():
    assert github_actions.pick_token(READ_TOKEN, TOKEN) == READ_TOKEN
    assert github_actions.pick_token(None, TOKEN) == TOKEN and github_actions.pick_token("", TOKEN) == TOKEN
    assert github_actions.pick_token(None, None) is None and github_actions.pick_token("", "") is None


def test_d339_a_run_shows_state_date_commit_duration_and_its_link(network):
    runs = github_actions.list_runs("pruebas.yml", None)
    first = runs[0]
    assert (first["state"], first["seconds"], first["event"], first["branch"]) == ("failed", 150.0, "push", "main")
    assert first["sha"].startswith("843decd") and first["message"] == "test(seguridad): una línea"
    assert first["started_at"] == datetime(2026, 10, 29, 13, 12, tzinfo=timezone.utc)
    assert first["url"].endswith("/actions/runs/3")
    assert [item["state"] for item in runs] == ["failed", "ok", "in_progress"] and runs[2]["seconds"] is None


def test_d339_without_a_token_only_the_states_are_read_and_no_log_is_asked_for(network):
    model = github_actions.build_model(None, None)
    assert model["token"] is False and [item["name"] for item in model["workflows"]] == [
        "pruebas",
        "semanal",
        "calidad",
    ]
    assert all(item["failure"] is None and len(item["runs"]) == 3 for item in model["workflows"])
    paths = [url.removeprefix(control.API_URL) for url, _ in network.calls]
    assert not any(path.endswith(("/jobs", "/logs", "/annotations", "/rate_limit")) for path in paths)
    assert all("Authorization" not in headers for _, headers in network.calls)


def test_d339_with_a_token_the_latest_failure_shows_job_step_tests_and_the_last_sixty_lines(network):
    model = github_actions.build_model(READ_TOKEN, TOKEN)
    assert model["token"] and model["expiration"] == datetime(2026, 12, 31, 12, tzinfo=timezone.utc)
    detail = model["workflows"][0]["failure"]
    job = detail["jobs"][0]
    assert (job["name"], job["steps"]) == ("pytest (3.12)", ["Run pytest"]) and len(detail["jobs"]) == 1  # lint passed
    assert job["tests"] == ["tests/test_a.py::test_one", "tests/test_b.py::test_two[es]"]  # once each, in order
    assert job["annotations"] == ["Process completed with exit code 1."]  # the warning is not a failure
    assert len(job["tail"]) == github_actions.LOG_LINES and job["tail"][-1] == "line 69"
    assert "\x1b" not in "".join(job["tail"]) and not job["tail"][0].startswith("2026-")
    # The token read is the read-only one, sent as a header and only there.
    sent = {headers.get("Authorization") for _, headers in network.calls}
    assert sent == {f"Bearer {READ_TOKEN}"}


def test_d339_the_token_never_leaves_the_reader_not_even_when_a_log_prints_it(network):
    model = github_actions.build_model(READ_TOKEN, TOKEN)
    text = json.dumps(model, default=str) + " ".join(github_actions.clean_log(LOG, (READ_TOKEN, TOKEN)))
    for secret in (TOKEN, READ_TOKEN, SHAPED, "FAKE0123456789", "READ0123456789"):
        assert secret not in text, secret
    assert "***" in text and "Bearer ***" in " ".join(github_actions.clean_log(LOG, (READ_TOKEN, TOKEN)))
    assert github_actions.redact("x " + "ghs_" + "0123456789abcdefghij y") == "x *** y"


@pytest.mark.parametrize(
    ("status", "needle"),
    [(401, "venció o no es válido"), (403, "no tiene permiso para leer los logs"), (404, "ya no existe")],
)
def test_d339_each_error_says_what_to_do_and_never_shows_the_token(monkeypatch, status, needle):
    failing = Network(fail={"/logs": Answer(status=status, headers={"X-Debug": TOKEN})}, logs=True)
    monkeypatch.setattr(github_actions.requests, "get", failing)
    monkeypatch.setattr(control.requests, "get", failing)
    model = github_actions.build_model(READ_TOKEN, None)
    job = model["workflows"][0]["failure"]["jobs"][0]
    assert needle in job["log_error"] and TOKEN not in json.dumps(model, default=str)
    assert job["tail"] == [] and job["tests"] == []  # the page still has the rest: states, job, step


def test_d339_an_expired_token_is_reported_once_and_no_detail_is_attempted(monkeypatch):
    failing = Network(fail={"/rate_limit": Answer(status=401)})
    monkeypatch.setattr(github_actions.requests, "get", failing)
    monkeypatch.setattr(control.requests, "get", failing)
    model = github_actions.build_model(READ_TOKEN, None)
    assert "venció o no es válido" in model["token_error"]
    assert all(item["failure"] is None and item["runs"] for item in model["workflows"])  # the states still show
    assert not any(url.endswith("/jobs") for url, _ in failing.calls)


def test_d339_a_request_limit_or_a_network_failure_is_named_without_the_address(monkeypatch):
    limited = Network(
        fail={
            "/workflows/pruebas.yml": Answer(
                status=403, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Limit": "60"}
            )
        }
    )
    monkeypatch.setattr(github_actions.requests, "get", limited)
    monkeypatch.setattr(control.requests, "get", limited)
    model = github_actions.build_model(None, None)
    assert "límite de consultas" in model["workflows"][0]["error"] and model["workflows"][1]["error"] is None
    assert control.API_URL not in model["workflows"][0]["error"]
    assert "GitHub no respondió" in github_actions.explain(requests.Timeout())
