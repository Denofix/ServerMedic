import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.demo_access import DemoAccess
from app.errors import AppError
from app.main import create_app
from tests.conftest import StubAnalyzer

ACCESS_CODE = "synthetic-demo-code-for-tests"


def demo_settings(**overrides):
    return Settings(
        public_demo=True,
        demo_access_code=ACCESS_CODE,
        _env_file=None,
        **overrides,
    )


def request_analysis(client, code=None):
    return client.post(
        "/api/analyze",
        files={"file": ("custom.log", b"ERROR sample\n", "text/plain")},
        headers={"Authorization": f"Bearer {code}"} if code else {},
    )


@pytest.mark.parametrize("code", [None, "wrong-code"])
def test_public_demo_denies_unauthorized_model_calls(code):
    analyzer = StubAnalyzer()
    with TestClient(create_app(demo_settings(), analyzer)) as client:
        response = request_analysis(client, code)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert analyzer.documents == []
        assert ACCESS_CODE not in response.text
        assert ACCESS_CODE not in client.get("/api/health").text


@pytest.mark.parametrize("code", ["", "too-short"])
def test_public_demo_fails_closed_without_strong_owner_code(code):
    analyzer = StubAnalyzer()
    settings = Settings(public_demo=True, demo_access_code=code, _env_file=None)
    with TestClient(create_app(settings, analyzer)) as client:
        assert client.get("/api/health").json()["analysis_configured"] is False
        assert request_analysis(client, code).status_code == 503
        assert analyzer.documents == []


def test_access_code_permits_inference_and_enforces_rate_limit():
    analyzer = StubAnalyzer()
    with TestClient(create_app(demo_settings(demo_requests_per_minute=1), analyzer)) as client:
        assert request_analysis(client, ACCESS_CODE).status_code == 200
        blocked = request_analysis(client, ACCESS_CODE)
        assert blocked.status_code == 429
        assert 1 <= int(blocked.headers["retry-after"]) <= 60
        assert len(analyzer.documents) == 1


def test_concurrency_slot_is_released_after_failure():
    async def scenario():
        access = DemoAccess(demo_settings())
        with pytest.raises(RuntimeError):
            async with access.admit():
                with pytest.raises(AppError, match="Another analysis"):
                    async with access.admit():
                        pass
                raise RuntimeError("provider failed")
        async with access.admit():
            pass

    asyncio.run(scenario())


def test_rate_limit_window_expires(monkeypatch):
    async def scenario():
        clock = [100.0]
        monkeypatch.setattr("app.demo_access.time.monotonic", lambda: clock[0])
        access = DemoAccess(demo_settings(demo_requests_per_minute=1))
        async with access.admit():
            pass
        with pytest.raises(AppError, match="too many analyses"):
            async with access.admit():
                pass
        clock[0] += 60
        async with access.admit():
            pass

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("example_id", "evidence"),
    [("postgres", [4, 5, 7, 8]), ("missing-env", [3, 4, 5]), ("port-in-use", [4, 5, 6]), ("healthy", [])],
)
def test_saved_reports_are_public_labelled_and_never_call_model(example_id, evidence):
    analyzer = StubAnalyzer()
    with TestClient(create_app(demo_settings(), analyzer)) as client:
        response = client.get(f"/api/examples/{example_id}/report")
        assert response.status_code == 200
        result = response.json()
        assert result["provider"] == "saved-example"
        assert "does not call an AI model" in result["markdown"]
        assert "synthetic-password" not in response.text
        assert response.headers["cache-control"] == "no-store"
        findings = result["analysis"]["findings"]
        assert (findings[0]["evidence_lines"] if findings else []) == evidence
        for finding in findings:
            for quote in finding["evidence"]:
                assert quote["text"] == result["document"]["lines"][quote["line"] - 1]["text"]
        assert analyzer.documents == []


def test_saved_report_does_not_accept_arbitrary_file_or_identifier():
    analyzer = StubAnalyzer()
    with TestClient(create_app(demo_settings(), analyzer)) as client:
        assert client.get("/api/examples/custom/report").status_code == 404
        assert client.post("/api/examples/postgres/report", content=b"ERROR custom").status_code == 405
        assert analyzer.documents == []
