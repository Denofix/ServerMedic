# API contract

All paths are relative to the same origin. No CORS setup is required; Vite and Nginx proxy `/api` to FastAPI. Interactive backend docs: `/docs` in local backend development.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness and configuration presence; not a real model probe |
| GET | `/api/examples` | Four sample descriptors |
| GET | `/api/examples/{id}` | Synthetic UTF-8 log bytes; allowlisted IDs only |
| POST | `/api/preview` | Validate and redact; no model call |
| POST | `/api/analyze` | Validate, redact, analyze, verify citations, render report |

Both POST endpoints require **exactly one** multipart field named `file`, containing a `.log` or `.txt` file. Additional files/fields are rejected. The original bytes must be at most 65,536. The entire HTTP body is bounded to 72 KiB to allow multipart framing.

UTF-8 BOM is accepted and stripped. CRLF and CR are normalized to LF. Splitting uses `text.split("\n")`: empty interior and trailing lines retain their original numbers. For example, `a\n\nb\n` produces lines 1–4; a final newline introduces a trailing empty line. Limits include that line. Binary/control characters other than tabs and CR/LF are rejected, including ANSI escape sequences. Input with no non-whitespace content is rejected.

Preview response:

```json
{
  "filename": "service.log",
  "size_bytes": 26,
  "line_count": 2,
  "redaction_count": 1,
  "lines": [
    {"number": 1, "text": "password=[REDACTED]"},
    {"number": 2, "text": "ERROR startup failed"}
  ]
}
```

`size_bytes` is the original file size. `redaction_count` counts pattern replacements, not distinct secrets. Metadata values above are illustrative.

Analyzer schema (Pydantic definitions live in `backend/app/models.py`):

```python
class Finding(BaseModel):
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    observation: str
    hypothesis: str
    evidence_lines: list[int]
    recommended_checks: list[str]

class Analysis(BaseModel):
    summary: str
    findings: list[Finding]
    limitations: list[str]
    missing_context: list[str]
```

The implemented schemas forbid extra keys, bound lengths/counts, and require strict integer line numbers. Every finding must have 1–12 evidence lines and 1–6 checks. Up to 12 findings are permitted. Backend validation rejects out-of-range references and evidence composed only of blank lines, sorts/deduplicates references, and adds `evidence: [{line, text}]` extracted from the processed document. Range validation does **not** prove that a cited line supports a generated hypothesis.

Analysis response:

```text
{
  document: Document,
  analysis: Analysis with extracted evidence,
  markdown: string,
  provider: string,
  model: string
}
```

`markdown` is generated server-side from the verified object. Browser export simply downloads it as UTF-8. There is no second report-generation endpoint accepting untrusted client analysis and no server report cache.

Errors have shape `{"error":{"code":"...","message":"..."}}`. Normal processing errors contain no model output, raw log data, or provider exception text.

| Status | Example codes |
| --- | --- |
| 400 | `invalid_upload`, `invalid_extension`, `invalid_encoding`, `invalid_text`, `empty_file`, `too_many_lines` |
| 413 | `file_too_large`, `request_too_large` |
| 422 | `model_refusal` |
| 502 | `invalid_result` |
| 503 | `not_configured`, `llm_auth`, `llm_rate_limit`, `llm_configuration`, `llm_unavailable` |
| 504 | `llm_timeout` |
| 500 | `internal_error` (generic, no exception details) |
