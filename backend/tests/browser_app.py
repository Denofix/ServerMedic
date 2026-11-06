"""Test-only dependency injection. Never used by the production entry point."""

import asyncio

from app.config import Settings
from app.errors import AppError
from app.main import create_app
from app.models import Analysis, Finding


class BrowserFixtureAnalyzer:
    provider = "test"
    model = "fixture-v1"

    async def analyze(self, document):
        await asyncio.sleep(0.15)  # Exercise the loading state, without contacting a model.
        text = "\n".join(line.text for line in document.lines)
        if "SERVERMEDIC_TEST_TIMEOUT" in text:
            raise AppError("llm_timeout", "Analysis timed out. Please try again.", 504)
        rules = [
            (
                "ECONNREFUSED",
                "PostgreSQL connection refused",
                "The database connection was refused.",
                "PostgreSQL might not be listening on the configured address.",
                "Check the database service health and listening port.",
                [4, 5, 8],
            ),
            (
                "APP_SECRET is not set",
                "Required configuration is missing",
                "APP_SECRET is not set.",
                "The application's environment may not include the required variable.",
                "Check the required variable is passed to the application without printing its value.",
                [4, 5],
            ),
            (
                "Address already in use",
                "HTTP port is already in use",
                "The HTTP listener could not bind.",
                "Another process may already be listening on port 8000.",
                "Review listeners with ss -ltnp and verify the configured port.",
                [4, 5, 6],
            ),
        ]
        findings = []
        for marker, title, observation, hypothesis, check, lines in rules:
            if marker in text:
                findings.append(
                    Finding(
                        title=title,
                        severity="high",
                        observation=observation,
                        hypothesis=hypothesis,
                        recommended_checks=[check],
                        evidence_lines=lines,
                    )
                )
                break
        return Analysis(
            summary="A startup failure was observed." if findings else "No errors were observed in this log.",
            findings=findings,
            limitations=["Deterministic test fixture. This is not an AI analysis."],
            missing_context=["Runtime configuration and service status."] if findings else [],
        )


app = create_app(Settings(_env_file=None), analyzer=BrowserFixtureAnalyzer())
