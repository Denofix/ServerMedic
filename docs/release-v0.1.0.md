# ServerMedic v0.1.0 — first public MVP

ServerMedic analyzes small application logs and produces observations, unconfirmed hypotheses, extracted evidence, and recommended diagnostic checks.

## Features

- One UTF-8 .log/.txt file, up to 64 KiB and 500 lines.
- Processed preview with best-effort secret masking and original line numbers.
- OpenAI Responses API with Pydantic Structured Outputs.
- Backend validation of evidence references and source-extracted quotations.
- Clickable evidence navigation and Markdown report export.
- Four synthetic examples, including healthy startup with zero findings.
- FastAPI, React/TypeScript/Vite, Docker Compose, and MIT-licensed original code.

## Verification

- Initial assistant-environment checks: 66 backend tests and 8 browser scenarios passed with test providers; frontend types and production build passed.
- User-run acceptance: Docker images built, both services became healthy, and all four synthetic examples were reviewed with the production OpenAI provider using gpt-6-luna.
- Evidence navigation, Markdown export, a synthetic password mask, and invalid-input UI states were demonstrated by user-supplied reports and screenshots.
- The Checks workflow covers backend tests, frontend/browser checks, and container startup. Inspect the tagged commit's Actions results for the actual CI outcome.

## Scope

This is a local MVP. Hypotheses require verification, masking is approximate, and diagnostic recommendations are never executed. Four accepted examples do not establish general diagnostic accuracy.
