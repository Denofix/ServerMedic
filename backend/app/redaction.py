"""Best-effort, line-local redaction. This is not a general DLP filter."""

import re

REDACTED = "[REDACTED]"
URL_PASSWORD = re.compile(r"(\b[a-z][a-z0-9+.-]*://[^\s/:@]+:)[^\s@]+(?=@)", re.I)
AUTHORIZATION = re.compile(
    r"([\"']?\b(?:proxy-)?authorization[\"']?\s*[:=]\s*)"
    r"(?:\[REDACTED\]|\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\r\n,;}\]]+)",
    re.I,
)
KEY_VALUE = re.compile(
    r"([\"']?\b(?:[a-z0-9_]*(?:password|passwd|token|secret|api_key|apikey|access_key)"
    r"[a-z0-9_]*|pwd)[\"']?\s*[:=]\s*)"
    r"(?:\[REDACTED\]|\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;&}\]\"']+)",
    re.I,
)
BEARER = re.compile(r"\b(Bearer|Basic)\s+[a-z0-9._~+/=-]+", re.I)
OPENAI_KEY = re.compile(r"\bsk-(?:proj-)?[a-z0-9_-]{16,}", re.I)


def redact(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in (
        (URL_PASSWORD, r"\g<1>[REDACTED]"),
        (AUTHORIZATION, r"\g<1>[REDACTED]"),
        (KEY_VALUE, r"\g<1>[REDACTED]"),
        (BEARER, r"\g<1> [REDACTED]"),
        (OPENAI_KEY, REDACTED),
    ):
        # Existing markers are left intact; count only new substitutions.
        def replace(match: re.Match[str], repl: str = replacement) -> str:
            nonlocal count
            if REDACTED in match.group(0):
                return match.group(0)
            count += 1
            return match.expand(repl)

        text = pattern.sub(replace, text)
    return text, count
