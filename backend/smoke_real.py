"""Opt-in paid inference against synthetic samples. Never runs in pytest or CI."""

import argparse
import asyncio
import json
from pathlib import Path

from app.config import Settings
from app.documents import prepare_document
from app.errors import AppError
from app.llm import OpenAIAnalyzer
from app.report import build_report
from app.service import verify_analysis


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all", action="store_true", help="Run all four examples (up to four paid requests)."
    )
    args = parser.parse_args()
    settings = Settings()
    if not settings.configured:
        print("SKIPPED: set OPENAI_API_KEY and LLM_MODEL on the backend. No request sent.")
        return 2
    root = Path(__file__).resolve().parents[1]
    expected = json.loads((root / "examples/expected.json").read_text())
    ids = ["postgres", "missing-env", "port-in-use", "healthy"] if args.all else ["postgres"]
    engine = OpenAIAnalyzer(settings)
    for sample_id in ids:
        document = prepare_document(f"{sample_id}.log", (root / f"examples/{sample_id}.log").read_bytes())
        try:
            analysis = verify_analysis(await engine.analyze(document), document)
            report = build_report(document, analysis, engine.provider, engine.model)
        except AppError as exc:
            print(f"FAILED {sample_id}: {exc.code}: {exc.message}")
            return 1
        supported = set(expected[sample_id]["evidence_lines"])
        if sample_id == "healthy":
            accepted = len(analysis.findings) == 0
        else:
            accepted = bool(analysis.findings) and all(
                supported.intersection(f.evidence_lines) for f in analysis.findings
            )
        if sample_id == "postgres" and "synthetic-password" in report:
            accepted = False
        print(f"{'PASS' if accepted else 'REVIEW'} {sample_id}: {len(analysis.findings)} finding(s).")
        print(json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False))
        if not accepted:
            print("Semantic sample expectations did not pass. Review before claiming acceptance.")
            return 1
    print("Real API response, schema, evidence bounds, report and coarse sample expectations passed.")
    print("Manually review diagnostic quality; these checks do not establish general model accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
