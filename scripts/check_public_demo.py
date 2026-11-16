"""Check a deployed demo without inference; --live explicitly makes one paid request."""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="HTTPS deployment origin, without an API path")
    parser.add_argument("--live", action="store_true", help="One paid PostgreSQL analysis")
    args = parser.parse_args()
    origin = args.url.rstrip("/")
    parsed = urlparse(origin)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
        or (parsed.scheme != "https" and parsed.hostname not in ("localhost", "127.0.0.1"))
    ):
        parser.error("Use an HTTPS origin (HTTP is allowed only for localhost).")

    def request(path, body=None, headers=None):
        req = Request(origin + path, data=body, headers=headers or {})
        try:
            with urlopen(req, timeout=90) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            return error.code, error.headers, error.read()

    def json_request(path, body=None, headers=None):
        status, response_headers, payload = request(path, body, headers)
        assert "application/json" in response_headers.get("Content-Type", ""), path
        return status, response_headers, json.loads(payload)

    raw = (ROOT / "examples/postgres.log").read_bytes()
    boundary = "ServerMedicSyntheticSmokeBoundary"
    multipart = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="postgres.log"\r\n'
        "Content-Type: text/plain\r\n\r\n"
    ).encode() + raw + f"\r\n--{boundary}--\r\n".encode()
    upload_headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}

    status, _, page = request("/")
    assert status == 200 and b"ServerMedic" in page
    status, _, deep_link = request("/demo")
    assert status == 200 and b"ServerMedic" in deep_link
    print("PASS frontend and SPA fallback")
    status, _, health = json_request("/api/health")
    assert status == 200 and health["status"] == "ok" and health["public_demo"]
    print("PASS same-origin API and hosted access policy")
    status, _, missing = json_request("/api/does-not-exist")
    assert status == 404 and isinstance(missing, dict)
    print("PASS unknown API route stays JSON (not SPA HTML)")
    status, headers, document = json_request("/api/preview", multipart, upload_headers)
    assert status == 200 and headers.get("Cache-Control") == "no-store"
    assert "synthetic-password" not in json.dumps(document)
    assert "[REDACTED]" in document["lines"][1]["text"] and document["lines"][2]["text"] == ""
    print("PASS upload, redaction, original blank lines, and no-store")
    for example_id in ("postgres", "missing-env", "port-in-use", "healthy"):
        status, _, report = json_request(f"/api/examples/{example_id}/report")
        assert status == 200 and report["provider"] == "saved-example"
        assert "Saved, curated example report" in report["markdown"]
        assert "synthetic-password" not in json.dumps(report)
        if example_id == "healthy":
            assert report["analysis"]["findings"] == []
        for finding in report["analysis"]["findings"]:
            for evidence in finding["evidence"]:
                assert evidence["text"] == report["document"]["lines"][evidence["line"] - 1]["text"]
        print(f"PASS saved {example_id} report and extracted evidence")
    status, _, blocked = json_request("/api/analyze", multipart, upload_headers)
    assert status in (401, 503) and blocked["error"]["code"] in (
        "demo_access_required", "demo_unavailable", "not_configured"
    )
    print("PASS anonymous requests cannot run live inference")
    if args.live:
        code = os.environ.get("DEMO_ACCESS_CODE", "").strip()
        if not code:
            parser.error("Set DEMO_ACCESS_CODE in your environment for --live; never pass it in a URL.")
        assert health["analysis_configured"], "Live inference is not configured on this deployment."
        status, _, report = json_request(
            "/api/analyze", multipart, {**upload_headers, "Authorization": f"Bearer {code}"}
        )
        assert status == 200, f"Live analysis returned HTTP {status}: {report.get('error', {}).get('code')}"
        assert report["provider"] == "openai" and report["analysis"]["findings"]
        assert "synthetic-password" not in json.dumps(report)
        for finding in report["analysis"]["findings"]:
            for evidence in finding["evidence"]:
                assert evidence["text"] == report["document"]["lines"][evidence["line"] - 1]["text"]
        print("PASS one live OpenAI analysis, extracted evidence, and Markdown")
    else:
        print("LIVE INFERENCE NOT TESTED (no model requests made).")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError, KeyError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
