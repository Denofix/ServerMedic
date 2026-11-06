# ServerMedic v0.1 — local MVP acceptance

Date: **2026-11-06** (Europe/Kyiv).

**Outcome: all four agreed synthetic demonstration scenarios passed local acceptance with the production OpenAI provider.** This is acceptance of the defined MVP scenarios, not a measurement of general diagnostic accuracy or production reliability.

## Evidence and execution boundary

The user executed Docker and browser checks on a local VMware Ubuntu Desktop VM and supplied terminal output, screenshots and exported Markdown reports. The assistant reviewed those materials against `examples/expected.json` and the supplied processed logs. The assistant did not connect to the VM or independently send these live API requests.

Environment reported by the user:

- Ubuntu 24.04.4 LTS, x86_64, inside VMware.
- Docker Engine installed; `hello-world` succeeded. Engine version was not reported.
- Docker Compose v5.7.0.
- Production backend entry point: `app.main:app`.
- Provider/model reported in successful UI results and reports: `openai` / `gpt-6-luna`.
- Frontend accessed within Ubuntu at `http://localhost:8080`.

## Live demonstration results

| Scenario | Reported result | Evidence lines | Review |
| --- | --- | --- | --- |
| PostgreSQL connection | One high-severity finding: connection refused and startup aborted; exact cause explicitly unconfirmed | 4, 5, 7, 8 | PASS |
| Missing configuration | One high-severity finding: APP_SECRET was not set and startup was aborted; injection failure remains a hypothesis | 3, 4, 5 | PASS |
| Port already in use | One high-severity finding: bind to 0.0.0.0:8000 failed; no invented process identity | 4, 5, 6 | PASS |
| Healthy startup | Zero findings; summary matches successful configuration, DB connection, migrations, listener and health request | No finding references required | PASS |

Each finding's supplied quotations match the corresponding processed log. Recommendations are diagnostic checks, with no claimed execution or automatic repair. Missing context and limits of diagnosis are stated. The healthy result appropriately avoids inferring long-term system health from a short excerpt.

Two supplied PostgreSQL reports differ in wording but preserve the same core observation and evidence. This demonstrates consistency for those two results, not a statistical repeatability evaluation.

## User-observed end-to-end and validation checks

| Check | Observed evidence | Outcome |
| --- | --- | --- |
| Compose build and startup | `docker compose config --quiet` succeeded; images built; backend and frontend reported healthy | PASS |
| Production frontend | Browser renders the workspace and live results through localhost:8080 | PASS |
| Sample preview | PostgreSQL sample displayed before analysis | PASS |
| Local file selection and analysis | File picker selected the project's postgres.log; another successful report was supplied | PASS based on the supplied sequence |
| Secret masking | PostgreSQL line 2 contains `[REDACTED]` in preview and report; replacement count is 1 | PASS for that synthetic URL password |
| Original numbering | Interior and trailing blank lines retain their numbers in supplied reports | PASS |
| Evidence navigation | Screenshot shows line 4 highlighted after evidence selection | PASS |
| Markdown export | Browser download completed and the report was opened; report text supplied for review | PASS |
| Empty-file handling | UI displays a clear empty-file error and disabled analysis | PASS |
| Oversized-file handling | UI displays the 64 KiB / 65,536 byte limit error | PASS |
| Excess-line handling | UI displays the 500-line limit error | PASS |

The UI rejection screenshots alone do not establish which network requests were sent. Backend boundary enforcement was separately covered by the automated tests recorded in `verification.md`.

Zero secret replacements for the missing-variable sample are expected: `APP_SECRET` is a variable name, not a disclosed value. This acceptance does not establish complete secret detection for arbitrary logs.

## Earlier automated verification

The earlier assistant-environment record in `verification.md` remains the provenance for **66 passing backend tests**, **8 passing browser scenarios using an explicit test fixture provider**, backend lint, frontend type checking and production build. Those checks were not rerun as part of this document-only acceptance update.

SDK tests used a mocked HTTP transport. Provider failures, invalid results and citation bounds were checked automatically with test implementations. The user's live results above supply the separate real-model and Compose evidence that was unavailable in the initial assistant environment. The optional `smoke_real.py --all` CLI was not reported as executed; these were browser-driven live checks.

## Remaining release work

1. Add this acceptance record to the repository alongside the initial verification record.
2. Publish to a chosen GitHub repository and inspect actual Actions results. No GitHub CI execution is evidenced yet.
3. Record a short demo using a supplied synthetic sample and describe exactly what was measured.

Broader diagnostic evaluation on additional logs, latency/cost measurements, load tests and public-service controls remain future work. No measured percentage accuracy, productivity improvement or total development duration is claimed.

## Minor presentation note

The current Markdown exporter escapes punctuation such as dots, hyphens and underscores. The exported reports remain valid Markdown, although raw text editing shows the escape characters. Reducing unnecessary escapes can be treated as a later formatting improvement.
