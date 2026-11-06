import html
import re

from .models import Document, VerifiedAnalysis


def plain(text: str) -> str:
    """Render model text as literal Markdown text, not active markup."""
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text).replace("\n", "  \n")


def code_block(text: str) -> str:
    runs = [len(m.group()) for m in re.finditer(r"`+", text)]
    fence = "`" * max(3, max(runs, default=0) + 1)
    return f"{fence}text\n{text}\n{fence}"


def build_report(document: Document, analysis: VerifiedAnalysis, provider: str, model: str) -> str:
    sections = [
        "# ServerMedic analysis",
        f"File: {plain(document.filename)}  \n"
        f"Lines: {document.line_count} · Original bytes: {document.size_bytes} · "
        f"Secret replacements: {document.redaction_count}  \n"
        f"Provider: {plain(provider)} · Model: {plain(model)}",
        "## Summary\n\n" + plain(analysis.summary),
        "## Findings",
    ]
    if not analysis.findings:
        sections.append("No problems identified in the supplied log. This does not prove system health.")
    for i, finding in enumerate(analysis.findings, 1):
        sections.extend(
            [
                f"### {i}. {plain(finding.title)} ({finding.severity})",
                "**Observation:** " + plain(finding.observation),
                "**Hypothesis (unconfirmed):** " + plain(finding.hypothesis),
                "**Evidence (extracted from processed log):**",
            ]
        )
        for evidence in finding.evidence:
            sections.append(f"Line {evidence.line}:\n\n{code_block(evidence.text)}")
        sections.append(
            "**Recommended checks — review before running:**\n\n"
            + "\n".join(f"- {plain(check)}" for check in finding.recommended_checks)
        )
    for title, items in (
        ("Limitations", analysis.limitations),
        ("Missing context", analysis.missing_context),
    ):
        sections.append(
            f"## {title}\n\n"
            + ("\n".join(f"- {plain(item)}" for item in items) if items else "None specified.")
        )
    sections.append(
        "## Processed log\n\n"
        + code_block("\n".join(f"{line.number:>3} | {line.text}" for line in document.lines))
    )
    return "\n\n".join(sections) + "\n"
