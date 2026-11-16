"""Curated reference reports for the four bundled synthetic logs, never inference.

These are deliberately separate from tests and from the live Analyzer protocol.
Only exact allowlisted example bytes are paired with these reports.
"""

from .models import Analysis, Finding

REFERENCE_LIMITATION = (
    "Saved, curated example report. Opening this report does not call an AI model. "
    "It only describes the bundled synthetic log, not an uploaded file."
)


def saved_analysis(example_id: str) -> Analysis:
    findings = {
        "postgres": Finding(
            title="PostgreSQL connection refused; startup aborted",
            severity="high",
            observation=(
                "Connections to 172.18.0.2:5432 were refused. The application could not connect "
                "to db:5432 and reported that startup was aborted because the database was unavailable."
            ),
            hypothesis=(
                "PostgreSQL may not have been accepting connections at the configured endpoint. "
                "The sample does not establish the underlying cause."
            ),
            evidence_lines=[4, 5, 7, 8],
            recommended_checks=[
                "Review PostgreSQL logs and health around 09:00:01–09:00:03 UTC.",
                "Verify that db:5432 resolves to the intended database service and port.",
                "Review database readiness, application startup ordering, and retry settings.",
            ],
        ),
        "missing-env": Finding(
            title="Startup blocked by missing APP_SECRET",
            severity="high",
            observation="Configuration validation reported that APP_SECRET was not set; startup aborted.",
            hypothesis=(
                "The process may not have received the required environment variable. "
                "The log does not show why it is missing."
            ),
            evidence_lines=[3, 4, 5],
            recommended_checks=[
                "Verify the deployment supplies APP_SECRET through its intended secret mechanism.",
                "Confirm availability to the process without printing or sharing the secret value.",
            ],
        ),
        "port-in-use": Finding(
            title="HTTP listener could not bind to port 8000",
            severity="high",
            observation=(
                "The log reports an address-in-use error, a failed bind to 0.0.0.0:8000, "
                "and fatal HTTP server startup failure."
            ),
            hypothesis=(
                "Another process may already be using port 8000. "
                "The sample does not identify the process."
            ),
            evidence_lines=[4, 5, 6],
            recommended_checks=[
                "Inspect listeners on port 8000 and verify whether the owning process is expected.",
                "Review deployment timing for overlapping instances using the same port.",
            ],
        ),
    }
    finding = findings.get(example_id)
    return Analysis(
        summary=(
            finding.observation
            if finding
            else "The log shows a successful startup and a 200 OK health check. No issues are visible."
        ),
        findings=[finding] if finding else [],
        limitations=[REFERENCE_LIMITATION, "This brief sample does not establish longer-term system health."],
        missing_context=["Later logs and runtime configuration."] if finding else [],
    )
