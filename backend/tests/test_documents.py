import pytest

from app.documents import MAX_BYTES, prepare_document
from app.errors import AppError
from app.redaction import redact


def test_original_numbering_and_trailing_blank():
    doc = prepare_document("windows.log", b"one\r\n\r\nthree\r\n")
    assert [(line.number, line.text) for line in doc.lines] == [(1, "one"), (2, ""), (3, "three"), (4, "")]
    assert doc.line_count == 4


def test_unicode_bom_and_cr():
    doc = prepare_document("input.TXT", "\ufeffПривіт\r世界".encode())
    assert [line.text for line in doc.lines] == ["Привіт", "世界"]


@pytest.mark.parametrize(
    ("name", "data", "code"),
    [
        ("x.csv", b"ok", "invalid_extension"),
        ("x.log", b"", "empty_file"),
        ("x.txt", b" \n\t", "empty_file"),
        ("x.log", b"\xff", "invalid_encoding"),
        ("x.log", b"a\0b", "invalid_text"),
        ("x.log", b"\x1b[31mERROR", "invalid_text"),
        ("x.log", b"x" * (MAX_BYTES + 1), "file_too_large"),
        ("x.log", b"x\n" * 500, "too_many_lines"),
    ],
)
def test_rejected_input(name, data, code):
    with pytest.raises(AppError) as error:
        prepare_document(name, data)
    assert error.value.code == code


def test_inclusive_size_and_line_limits():
    assert prepare_document("x.log", b"a" * MAX_BYTES).size_bytes == MAX_BYTES
    assert prepare_document("x.log", b"\n".join([b"a"] * 500)).line_count == 500
    with pytest.raises(AppError):
        prepare_document("x.log", "я".encode() * (MAX_BYTES // 2 + 1))


@pytest.mark.parametrize(
    ("text", "secret"),
    [
        ("url=postgresql://alice:pa%40ss@db:5432/app", "pa%40ss"),
        ('{"Authorization": "Bearer synthetic-token"}', "synthetic-token"),
        ("Authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
        ("Authorization: custom opaque-token", "opaque-token"),
        ("APP_SECRET='some secret with spaces'", "some secret with spaces"),
        ('{"password": "not-real"}', "not-real"),
        ("api_key = synthetic-key", "synthetic-key"),
        ("https://example.test?access_token=abc&ok=1", "abc"),
        ("Bearer abc.def.ghi", "abc.def.ghi"),
        ("sk-proj-synthetic1234567890abcdef", "sk-proj-synthetic1234567890abcdef"),
    ],
)
def test_redaction(text, secret):
    masked, count = redact(text)
    assert secret not in masked
    assert "[REDACTED]" in masked
    assert count >= 1
    assert redact(masked) == (masked, 0)


def test_redaction_preserves_lines_and_empty_lines():
    source = 'password="first"\n\nAuthorization: Bearer second\nlast'
    masked, count = redact(source)
    assert masked.split("\n")[1] == ""
    assert len(masked.split("\n")) == len(source.split("\n"))
    assert count == 2


def test_safe_filename():
    assert prepare_document("C:\\fakepath\\sample.log", b"ok").filename == "sample.log"
