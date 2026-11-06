from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import Analysis, Finding

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def result(lines=None):
    return Analysis(
        summary="The application could not start.",
        findings=[
            Finding(
                title="Startup failure",
                severity="high",
                observation="The log reports a startup error.",
                hypothesis="A required dependency may be unavailable.",
                evidence_lines=lines or [1],
                recommended_checks=["Check dependency health."],
            )
        ],
        limitations=["Only the uploaded log was examined."],
        missing_context=["Deployment configuration."],
    )


class StubAnalyzer:
    provider = "test"
    model = "fixture-v1"

    def __init__(self, response=None, error=None):
        self.response = response if response is not None else result()
        self.error = error
        self.documents = []

    async def analyze(self, document):
        self.documents.append(document)
        if self.error:
            raise self.error
        return self.response


@pytest.fixture
def analyzer():
    return StubAnalyzer()


@pytest.fixture
def client(analyzer):
    with TestClient(create_app(Settings(_env_file=None), analyzer)) as client:
        yield client
