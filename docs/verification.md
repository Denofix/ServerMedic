# Executed verification

> This file records the initial assistant-environment checks. Subsequent user-run Docker Compose and live OpenAI acceptance are recorded in [ServerMedic_MVP_Acceptance_2026-11-06.md](ServerMedic_MVP_Acceptance_2026-11-06.md).

Date: **2026-11-06**. This is an evidence record, not a claim of production readiness or general diagnostic accuracy.

## Initial assistant environment

- Empty starting workspace; no pre-existing repository or remote was supplied.
- Python 3.12.14, Node.js 24.22.1, npm 11.9.0.
- Dependencies installed and pinned in Python requirements and npm lockfile.
- No `OPENAI_API_KEY` or `LLM_MODEL` configured. No OpenAI inference request was made.
- Docker executable/daemon unavailable in this environment.

## Initial results

| Check | Executed result | Method / boundary |
| --- | --- | --- |
| Backend lint | PASS | `ruff check app tests smoke_real.py` |
| Backend tests | **66 passed** | `pytest -q`, latest run 1.57 s; injected providers and real SDK with mocked HTTP transport |
| Frontend types | PASS | `npm run typecheck` |
| Frontend production build | PASS | `npm run build`; Vite generated `dist/` |
| Browser scenarios | **8 passed** | Playwright 1.58.2, Chromium 143.0.7499.0; latest run 6.6 s, including test-server startup |
| Visual review | PASS | Inspected initial and result desktop views at 1440 px and result view at 390 px; no page-width overflow |
| Production backend startup | PASS | Started `uvicorn app.main:app` as a subprocess and sent actual HTTP requests |
| Production HTTP preview | PASS | PostgreSQL sample → 200; password masked, no raw synthetic password in response |
| Production missing-config HTTP error | PASS | Same sample → 503 `not_configured`; no inference attempted |
| Compose/workflow static inspection | PASS (limited) | YAML parsed; service names, Dockerfile paths, local port binding, read-only flags and CI job names checked |
| Docker Compose build/start | **NOT RUN** | No Docker runtime. Static YAML inspection is not `docker compose config` or container validation. |
| GitHub Actions | **NOT RUN** | Workflow prepared locally; no remote repository or Actions run exists. |
| Real OpenAI acceptance | **SKIPPED** | `python smoke_real.py` exited 2 with an explicit missing-configuration message. |

## Backend coverage

- UTF-8, BOM, CRLF/CR normalization and 1-based original numbering.
- Blank interior and trailing lines retained; exact inclusive size/line boundaries.
- Empty/whitespace files, invalid extension, encoding, binary/control characters.
- Exactly one multipart file, no extra fields, bounded HTTP body including chunked input.
- Common URL/header/assignment credentials, masks across lines, idempotent redaction.
- Sanitized-only model input and UI/report response.
- Invalid, zero/negative, non-integer, out-of-range or only-blank evidence rejected.
- Duplicate references deduplicated and sorted; quotations extracted from source lines.
- Extra model-supplied quotation fields rejected by the schema.
- Zero-finding output, model limitation enrichment, Markdown code-fence safety.
- Missing config, refusal, invalid/incomplete output, safe error messages, timeout, upstream status/transport errors.
- Official SDK request serialization and Pydantic parsing tested through an in-memory HTTP mock. No OpenAI endpoint was contacted by tests.

## Browser coverage

1. Initial screen → PostgreSQL sample → masked preview → analysis → evidence focus → downloaded Markdown content.
2. Missing-variable sample → finding with existing evidence lines.
3. Occupied-port sample → finding with existing evidence lines.
4. Healthy sample → zero findings and enabled report export.
5. Local file upload → same redaction/analysis path → remove file clears result.
6. Wrong extension, oversized file, too many lines → helpful errors.
7. Simulated LLM timeout → retained preview, retry option, no export.
8. 390 px viewport → working result, no horizontal page overflow.

The browser ran against `tests.browser_app:app`, an explicitly labeled deterministic fixture provider. These results demonstrate frontend/backend wiring and result handling, not model reasoning quality.

### Browser installation obstacle

Standard Playwright Chromium downloads produced invalid archive data in this environment, including after pinning Playwright 1.58.2. A temporary `@sparticuz/chromium@143.0.4` package supplied the actual Chromium 143 binary for local tests and visual inspection. The binary and package are **not** part of the delivered source or runtime dependencies. The normal project/CI path uses `npx playwright install --with-deps chromium`. The optional existing-browser path is documented in README.

## Gates pending at the time of the initial checks

1. In an environment with Docker, run `docker compose config --quiet` and `docker compose up --build --wait`. Verify frontend, masked preview and health. CI contains the same container checks.
2. Configure your own API key and a supported `LLM_MODEL` locally. Run `python smoke_real.py --all` from `backend/`, then manually review hypotheses and evidence.
3. Repeat the browser scenario using the production OpenAI provider. Record actual model ID, response quality and latency before claiming a real AI demo.
4. Push to a chosen GitHub repository and inspect the actual Actions results. No repository has been published or remote content changed by this work.

The original target of 5–6 hours remains a sprint budget. Wall-clock development time was not instrumented and is not reported as a measured outcome.
