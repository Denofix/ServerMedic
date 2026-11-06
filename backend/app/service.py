from .errors import AppError
from .models import Analysis, Document, Evidence, VerifiedAnalysis, VerifiedFinding
from .redaction import redact

BASE_LIMITATIONS = [
    "Hypotheses are not confirmed root causes. Verify them in your environment.",
    "Line references are range-checked; relevance and model reasoning are not mechanically proven.",
    "Secret masking is best-effort. Review processed logs before sharing them.",
]


def verify_analysis(analysis: Analysis, document: Document) -> VerifiedAnalysis:
    findings = []
    for finding in analysis.findings:
        numbers = sorted(set(finding.evidence_lines))
        if any(n < 1 or n > document.line_count for n in numbers):
            raise AppError(
                "invalid_result",
                "The model cited a line outside this file. No report was generated. Try again.",
                502,
            )
        if not any(document.lines[n - 1].text.strip() for n in numbers):
            raise AppError("invalid_result", "The model cited only empty lines. Try the analysis again.", 502)
        data = finding.model_dump()
        # Mask common patterns again in generated text, including suggested commands.
        for field in ("title", "observation", "hypothesis"):
            data[field] = redact(data[field])[0]
        data["recommended_checks"] = [redact(c)[0] for c in finding.recommended_checks]
        data["evidence_lines"] = numbers
        findings.append(
            VerifiedFinding(
                **data,
                evidence=[Evidence(line=n, text=document.lines[n - 1].text) for n in numbers],
            )
        )
    return VerifiedAnalysis(
        summary=redact(analysis.summary)[0],
        findings=findings,
        limitations=list(dict.fromkeys(BASE_LIMITATIONS + [redact(s)[0] for s in analysis.limitations])),
        missing_context=[redact(s)[0] for s in analysis.missing_context],
    )
