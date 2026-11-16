# Hosted demonstration

Public address: **[servermedic.flareledger.fun](https://servermedic.flareledger.fun/)**.
The [servermedic.vercel.app](https://servermedic.vercel.app/) alias remains available.

## Published mode: no owner-funded model calls

The public website runs without an OpenAI API key. Visitors can:

- Upload one UTF-8 `.log` or `.txt` file to inspect the masked preview.
- Select one of four synthetic logs, then **Open saved example report**.
- Inspect evidence, jump to original line numbers, and export Markdown.

Saved reports are curated references labelled `saved-example / curated-v1`, with
an explicit no-inference notice in the UI and exported report. They never analyze
custom uploads or replace failed live requests. The published website does not
offer live model inference or ask visitors to enter an API key.

For live AI analysis, users run the frontend and backend on their own computer:
[Windows setup](install-windows.md) or [Linux setup](install-linux.md). Each user
sets `OPENAI_API_KEY` and `LLM_MODEL` in that checkout's root `.env`, leaves
`PUBLIC_DEMO=false`, and restarts the local backend. Calls go from that backend
to OpenAI and are charged to the user's own API account. The public website does
not receive the key. Masked log text and filename still go to OpenAI for analysis.

## Vercel deployment

The hosted application keeps React + TypeScript + Vite and the production FastAPI
entrypoint. Vercel Services (currently beta) builds both and exposes one origin.
The backend owns `/api` and `/api/*`; the frontend owns all other paths. It does
not use the test-only browser application.

Create the project from the repository root with the **Services** preset, Python
3.12 and Node.js 24. The committed `vercel.json` owns build and routing settings.
The backend is rooted at the repository so the original `examples/` directory
is included. No Docker daemon or persistent volume is required.

The root `requirements.txt` mirrors the pinned backend requirements because the
Vercel development parser does not resolve nested `-r` includes. CI checks both
files match. The nearest Python metadata, `backend/pyproject.toml`, declares the
same pins; a packaging test prevents dependency drift.

For the published mode, keep `PUBLIC_DEMO=true` and leave `OPENAI_API_KEY` unset
in Production and Preview. No provider credential or owner-funded request is
needed for preview and saved reports. `analysis_configured: false` in health is
expected for this mode. Restart/redeploy after changing environment variables.
Never prefix a credential with `VITE_`.

## Custom domain

`servermedic.flareledger.fun` is attached to the ServerMedic project as a verified
production domain. The apex `flareledger.fun` serves the separate FlareLedger
project. Both use Vercel DNS; the ServerMedic hostname resolves through existing
wildcard routing. HTTPS and same-origin `/api` routes were checked on the custom
hostname. No apex reassignment or nameserver migration was needed.

## Verify the published mode without a model call

From a checked-out repository:

```bash
python scripts/check_public_demo.py https://servermedic.flareledger.fun
```

The checker covers frontend and SPA fallback, same-origin JSON API, preserved
blank lines, masking, four saved reports, Markdown, exact evidence and anonymous
live-inference denial. It does not call OpenAI. `--live` is not part of the public
demo's acceptance criteria.

## Optional: a separately configured private live deployment

The application retains private hosted inference for operators who deliberately
choose to run it on their own deployment. This is not required for the published
demo or a user's local installation.

| Variable | Private hosted inference only |
| --- | --- |
| `PUBLIC_DEMO` | `true` |
| `OPENAI_API_KEY` | Operator's server-side API credential |
| `LLM_MODEL` | Exact accessible Responses + Structured Outputs model ID |
| `DEMO_ACCESS_CODE` | Private random code, 16–128 characters |
| `LLM_TIMEOUT_SECONDS` | `60`, below the supplied 75-second function duration |
| `DEMO_REQUESTS_PER_MINUTE` | `5` live admissions per running backend process |
| `DEMO_MAX_CONCURRENT` | `1` live request per running backend process |

Missing/short codes disable hosted inference even when an API key exists.
Anonymous live requests are rejected before calling the model. The access code
is held only in page memory and sent only as the live request's Authorization
header; it is cleared on reload. An access code is not an OpenAI API key.

The rate/concurrency counters live in process memory: cold starts reset them
and replicas have independent counters. They are not a global quota or monetary
cap. The private code remains the access boundary for this optional mode.

## Privacy

Selecting a file uploads its raw contents to the backend for masking, even in
preview-only use. The public preview and saved-report paths make no model call.
Masking is approximate; do not upload confidential logs to the public demo.
With a configured local backend, live analysis sends only masked text and the
filename to OpenAI. Vercel and OpenAI have their own platform data policies;
application `no-store` headers do not override those policies.

## Deployment updates

Connect this project to `Denofix/ServerMedic` in Vercel's Git settings for automatic
branch deployments. Direct source deployments do not auto-update when Git changes.
Verify the deployed source and run the no-inference smoke check after changes.
