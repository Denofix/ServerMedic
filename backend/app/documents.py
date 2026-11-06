import re

from .errors import AppError
from .models import Document, LogLine
from .redaction import redact

MAX_BYTES = 64 * 1024
MAX_LINES = 500


def prepare_document(filename: str, content: bytes) -> Document:
    if not filename.lower().endswith((".log", ".txt")):
        raise AppError("invalid_extension", "Choose one .log or .txt file.")
    if len(content) > MAX_BYTES:
        raise AppError("file_too_large", "The file exceeds 64 KiB (65,536 bytes).", 413)
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise AppError("invalid_encoding", "The file must be valid UTF-8 text.") from None
    if not text.strip():
        raise AppError("empty_file", "The file is empty. Choose a log containing text.")
    if any(ord(c) < 32 and c not in "\n\r\t" for c in text) or "\x7f" in text:
        raise AppError("invalid_text", "Binary files and control characters are not supported.")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")  # Includes internal and trailing empty lines.
    if len(lines) > MAX_LINES:
        raise AppError("too_many_lines", "The file exceeds 500 lines, including empty lines.")
    processed, redactions = redact(normalized)
    safe_name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    safe_name = re.sub(r"[\x00-\x1f\x7f]", "_", safe_name)[:120]
    safe_name, _ = redact(safe_name)
    return Document(
        filename=safe_name,
        size_bytes=len(content),
        line_count=len(lines),
        redaction_count=redactions,
        lines=[LogLine(number=i, text=line) for i, line in enumerate(processed.split("\n"), 1)],
    )
