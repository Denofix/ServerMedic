import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import AppError
from app.main import create_app
from app.models import Analysis
from tests.conftest import EXAMPLES, StubAnalyzer, result


def upload(client, data=b"ERROR startup\n\nlast", path="/api/analyze", name="sample.log"):
    return client.post(path, files={"file": (name, data, "text/plain")})


def test_preview_does_not_call_model(client, analyzer):
    response = upload(client, b"password=synthetic\n\nline 3", path="/api/preview")
    assert response.status_code == 200
    assert response.json()["lines"][1] == {"number": 2, "text": ""}
    assert "synthetic" not in response.text
    assert analyzer.documents == []
    assert response.headers["cache-control"] == "no-store"


def test_analysis_uses_only_sanitized_data_and_extracts_evidence(client, analyzer):
    analyzer.response = result([3, 1, 3])
    response = upload(client, b"password=synthetic\n\nERROR failure")
    assert response.status_code == 200
    body = response.json()
    finding = body["analysis"]["findings"][0]
    assert finding["evidence_lines"] == [1, 3]
    assert finding["evidence"] == [
        {"line": 1, "text": "password=[REDACTED]"},
        {"line": 3, "text": "ERROR failure"},
    ]
    assert "synthetic" not in response.text
    assert analyzer.documents[0].lines[0].text == "password=[REDACTED]"
    assert "## Processed log" in body["markdown"]


@pytest.mark.parametrize("lines", [[4], [2]])
def test_out_of_range_or_only_blank_evidence_rejected(client, analyzer, lines):
    analyzer.response = result(lines)
    response = upload(client)
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_result"
    assert "markdown" not in response.json()


@pytest.mark.parametrize("bad_lines", [[0], [-1], [501], [True], ["1"], []])
def test_invalid_evidence_type_or_bounds(client, analyzer, bad_lines):
    malformed = result().model_dump()
    malformed["findings"][0]["evidence_lines"] = bad_lines
    analyzer.response = malformed
    assert upload(client).status_code == 502


def test_healthy_result(client, analyzer):
    analyzer.response = Analysis(
        summary="No errors observed.", findings=[], limitations=[], missing_context=[]
    )
    response = upload(client, b"INFO ready")
    assert response.status_code == 200
    assert response.json()["analysis"]["findings"] == []
    assert "No problems identified" in response.json()["markdown"]


def test_maximum_model_limitations_can_be_enriched(client, analyzer):
    analyzer.response = result().model_copy(update={"limitations": [f"Limitation {i}" for i in range(8)]})
    response = upload(client)
    assert response.status_code == 200
    assert len(response.json()["analysis"]["limitations"]) == 11


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("llm_timeout", 504),
        ("llm_unavailable", 503),
        ("model_refusal", 422),
        ("invalid_result", 502),
    ],
)
def test_provider_errors(client, analyzer, code, status):
    analyzer.error = AppError(code, "A safe error message.", status)
    response = upload(client)
    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": "A safe error message."}}


def test_missing_configuration():
    with TestClient(create_app(Settings(openai_api_key="", llm_model="", _env_file=None))) as client:
        assert client.get("/api/health").json()["analysis_configured"] is False
        assert upload(client, path="/api/preview").status_code == 200
        response = upload(client)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "not_configured"


def test_unexpected_exception_is_private():
    with TestClient(
        create_app(Settings(_env_file=None), StubAnalyzer(error=RuntimeError("SECRET"))),
        raise_server_exceptions=False,
    ) as client:
        response = upload(client)
        assert response.status_code == 500
        assert "SECRET" not in response.text


def test_exactly_one_file(client, analyzer):
    assert client.post("/api/analyze").status_code == 400
    assert (
        client.post("/api/analyze", files=[("file", ("a.log", b"a")), ("file", ("b.log", b"b"))]).status_code
        == 400
    )
    assert client.post("/api/analyze", files={"wrong": ("a.log", b"a")}).status_code == 400
    assert (
        client.post("/api/analyze", files={"file": ("a.log", b"a")}, data={"extra": "x"}).status_code == 400
    )
    assert analyzer.documents == []


def test_http_limits(client, analyzer):
    assert upload(client, b"x" * 65536, path="/api/preview").status_code == 200
    response = upload(client, b"x" * 65537)
    assert response.status_code == 413
    assert upload(client, b"x" * 100000).status_code == 413
    assert upload(client, b"\n".join([b"a"] * 500), path="/api/preview").status_code == 200
    assert upload(client, b"\n".join([b"a"] * 501)).status_code == 400
    assert analyzer.documents == []


def test_body_limit_without_content_length(client):
    response = client.post(
        "/api/analyze",
        content=iter([b"x" * 40000, b"y" * 40000]),
        headers={"Content-Type": "multipart/form-data; boundary=a"},
    )
    assert response.status_code == 413


@pytest.mark.parametrize("example_id", ["postgres", "missing-env", "port-in-use", "healthy"])
def test_examples_follow_same_upload_path(client, analyzer, example_id):
    example = client.get(f"/api/examples/{example_id}")
    assert example.content == (EXAMPLES / f"{example_id}.log").read_bytes()
    response = upload(client, example.content, name=f"{example_id}.log")
    assert response.status_code == 200
    assert len(analyzer.documents) == 1


def test_examples_allowlist(client):
    assert len(client.get("/api/examples").json()) == 4
    assert client.get("/api/examples/not-a-sample").status_code == 404


def test_markdown_cannot_break_out_of_code_fence(client, analyzer):
    analyzer.response = result([1])
    response = upload(client, b"ERROR ```<script>alert(1)</script>```")
    markdown = response.json()["markdown"]
    assert "````text" in markdown
    assert "Hypothesis (unconfirmed)" in markdown


def test_model_cannot_supply_quotations(client, analyzer):
    bad = result().model_dump()
    bad["findings"][0]["evidence"] = [{"line": 1, "text": "invented"}]
    analyzer.response = bad
    assert upload(client).status_code == 502
