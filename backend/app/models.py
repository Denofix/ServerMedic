from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


Text = Annotated[str, Field(min_length=1, max_length=2000)]
LineNumber = Annotated[int, Field(strict=True, ge=1, le=500)]


class Finding(StrictModel):
    title: Annotated[str, Field(min_length=1, max_length=160)]
    severity: Literal["low", "medium", "high", "critical"]
    observation: Text
    hypothesis: Text
    evidence_lines: Annotated[list[LineNumber], Field(min_length=1, max_length=12)]
    recommended_checks: Annotated[list[Text], Field(min_length=1, max_length=6)]


class Analysis(StrictModel):
    summary: Text
    findings: Annotated[list[Finding], Field(max_length=12)]
    limitations: Annotated[list[Text], Field(max_length=8)]
    missing_context: Annotated[list[Text], Field(max_length=8)]


class LogLine(StrictModel):
    number: int
    text: str


class Document(StrictModel):
    filename: str
    size_bytes: int
    line_count: int
    redaction_count: int
    lines: list[LogLine]


class Evidence(StrictModel):
    line: int
    text: str


class VerifiedFinding(Finding):
    evidence: list[Evidence]


class VerifiedAnalysis(Analysis):
    findings: list[VerifiedFinding]
    limitations: list[Text]


class AnalysisResponse(StrictModel):
    document: Document
    analysis: VerifiedAnalysis
    markdown: str
    provider: str
    model: str
