# Hosted demonstration

Public address: **[servermedic.flareledger.fun](https://servermedic.flareledger.fun/)**.
The [servermedic.vercel.app](https://servermedic.vercel.app/) alias remains available.

The hosted application keeps React + TypeScript + Vite and the production FastAPI
entrypoint. Vercel Services (currently beta) builds both and exposes one origin.
The backend owns `/api` and `/api/*`; the frontend owns all other paths. It does
not use the test-only browser application.

## What visitors can try

- Upload one UTF-8 `.log` or `.txt` file to inspect the masked preview.
- Select one of four synthetic logs, then **Open saved example report**.
- Inspect evidence, jump to original line numbers, and export Markdown.
- Use an owner-provided code to run live AI analysis of their accepted file,
  when the server's model credentials and code are configured.

Saved reports are curated references labelled `saved-example / curated-v1`, with
an explicit no-inference notice in the UI and exported report. They are never
returned as a fallback for a failed live request or for an arbitrary upload.

## Custom domain

`servermedic.flareledger.fun` is attached to the ServerMedic project as a verified
production domain. The apex `flareledger.fun` serves the separate FlareLedger
project. Both use Vercel DNS; the ServerMedic hostname resolves through the
existing wildcard routing. HTTPS and the same-origin `/api` routes were checked
on the custom hostname. No apex reassignment or nameserver migration was needed.

## Owner setup in Vercel

Create a project from the repository root with the **Services** preset, Python
3.12 and Node.js 24. The committed `vercel.json` owns build and routing settings.
The backend service is rooted at the repository so its original `examples/`
directory is included. No Docker daemon or persistent volume is required.
The root `requirements.txt` mirrors the pinned backend requirements because the
Vercel development parser does not resolve nested `-r` includes. CI checks the
two files match; update both when changing backend dependencies.
The nearest Python project metadata, `backend/pyproject.toml`, also declares the
same complete set of pins for the cloud builder. A packaging test prevents drift
between its dependency list and the requirements files.

Set these **server-side** environment variables for the intended environment:

| Variable | Value |
| --- | --- |
| `PUBLIC_DEMO` | `true` |
| `OPENAI_API_KEY` | An API key entered directly in Vercel, never in Git or chat |
| `LLM_MODEL` | An accessible Responses + Structured Outputs model; acceptance used `gpt-6-luna` |
| `DEMO_ACCESS_CODE` | A private random code, 16–128 characters |
| `LLM_TIMEOUT_SECONDS` | `60` (below the deployed function's 75-second limit) |
| `DEMO_REQUESTS_PER_MINUTE` | `5` per running backend process |
| `DEMO_MAX_CONCURRENT` | `1` live request per running backend process |

Redeploy after changing variables. Do not prefix credentials with `VITE_`.
Share the access code privately with intended testers. The browser holds it in
React memory only, clears it on reload, and sends it only as the live analysis
request's Authorization header. It is not placed in a URL or browser storage.

Missing or shorter-than-16-character codes disable live analysis even when an
OpenAI key exists. Anonymous live calls return a controlled 401 or 503 before
the model is called. The local Compose default remains `PUBLIC_DEMO=false`.

## Limits and privacy

The rate and concurrency counters live in process memory. Cold starts reset them,
and serverless replicas have independent counters. They are **not a global daily
quota or a hard monetary cap**. The private code is the primary access boundary.
Use a dedicated API project with appropriate billing controls, rotate the demo
code when needed, and keep access restricted. An unrestricted public AI service
needs a durable shared quota mechanism before anonymous model access is enabled.

Both preview and analysis upload the raw file to the backend. Only live analysis
sends masked content to OpenAI. Masking is approximate. Do not use confidential
logs in the public demo. Vercel and OpenAI may retain platform metadata according
to their policies; application `no-store` headers do not override those policies.

## Verification

From a checked-out repository, run the no-inference smoke check:

```bash
python scripts/check_public_demo.py https://servermedic.flareledger.fun
```

It checks the frontend, deep-link fallback, same-origin JSON API, original blank
lines, masking, four saved reports, Markdown, exact evidence and anonymous denial.

After configuring live credentials, enter the access code without echoing it:

```bash
read -rs -p 'Demo access code: ' DEMO_ACCESS_CODE
export DEMO_ACCESS_CODE
python scripts/check_public_demo.py https://servermedic.flareledger.fun --live
unset DEMO_ACCESS_CODE
```

`--live` makes exactly one paid model request for the synthetic PostgreSQL log.
Also repeat the upload → live analysis → evidence jump → Markdown path in a browser.
A passing saved-example smoke check is not evidence of live OpenAI availability.

## Deployment updates

Connect the project to `Denofix/ServerMedic` in Vercel's Git settings for automatic
branch deployments. If the account has no GitHub integration installed, a direct
source deployment can still host the app; it will not auto-update when Git changes.
Verify the deployed commit and run the smoke check after every change.
