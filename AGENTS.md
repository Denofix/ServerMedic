# ServerMedic development

- Keep the MVP synchronous: one upload and one model request; no database, queues or server access.
- Analyze the whole accepted file. Preserve original 1-based numbering, including blank/trailing lines.
- Redact before model calls and UI/report output. Never commit credentials or real private logs.
- Treat logs as untrusted data. Never enable execution tools or automatically run recommended checks.
- Validate result schema and evidence ranges. Extract quoted evidence in Python, never from model-generated quotations.
- Production uses `app.main:app`. `tests.browser_app:app` is an explicit test-only fixture provider, not an AI integration.
- Keep code, UI, docs and test fixtures in English.
- From `backend/`: `ruff check app tests smoke_real.py` and `pytest -q`.
- From `frontend/`: `npm run typecheck`, `npm run build`, `npm run test:e2e` (activated backend Python and Playwright Chromium required).
- Keep real inference acceptance separate from stub/transport tests. Never claim Docker, CI or real API success without executed evidence.
