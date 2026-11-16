# Hosted demo verification

## Current policy — 2026-11-17

Public address: **[servermedic.flareledger.fun](https://servermedic.flareledger.fun/)**.
The [servermedic.vercel.app](https://servermedic.vercel.app/) alias remains available.

The published demo intentionally runs without `OPENAI_API_KEY`: it provides
masked previews and four labelled saved reports. `analysis_configured: false`
is the expected state, not a pending activation task. The owner does not need
to fund public model calls or collect visitors' API keys.

Live AI analysis belongs to each user's local installation, configured with that
user's API key in the local backend's `.env` and `PUBLIC_DEMO=false`. See the
[Windows guide](install-windows.md) and [Linux guide](install-linux.md). The hosted
UI links to those guides when live inference is not configured. Optional private
hosted inference remains a separate operator choice described in
[public-demo.md](public-demo.md). No hosted live-inference success is claimed.

## Executed custom-domain HTTP check — 2026-11-16

| Check | Result |
| --- | --- |
| Domain ownership and Vercel DNS configuration | Verified; no DNS conflict reported |
| HTTPS with normal certificate validation | Passed through the public smoke checker |
| Frontend and `/demo` SPA fallback | Passed |
| Same-origin health and unknown API route | Passed; unknown API path stays JSON 404 |
| Uploaded synthetic preview | Passed; secret masked, blank line preserved, `no-store` returned |
| Four saved reports | Passed; curated provider, Markdown and exact evidence checked |
| Anonymous live analysis | Controlled denial before model inference |
| Hosted OpenAI request | Not performed; no provider key configured |

The checker used `scripts/check_public_demo.py` at
`a6f4385fd77bd8cdf9ee4521ccce87ef09748dbf` and exited 0, without a model call.
The custom hostname is assigned to ServerMedic. The apex `flareledger.fun` remains
on FlareLedger and its existing API DNS record was preserved.

An initial attempt at browser automation on the custom hostname did not start:
the verification image's Ubuntu 26.04 was unsupported by Playwright 1.58.2's
installer. That attempt is not reported as a passing browser test.

## Initial hosted application checks — 2026-11-16

Initial production deployment: `dpl_FwRp6HvUkmTP8asBAChb5Q3AmpKh`.
Source base: `33112910f5f06189cace01595f9bb82836ce6f84` plus the public-demo patch,
uploaded directly to Vercel Services. The patch was later merged in
[PR #1](https://github.com/Denofix/ServerMedic/pull/1). The initial deployment
was not Git-connected; automatic Git deployment is a separate project setting.

| Check | Result |
| --- | --- |
| Backend Ruff and pytest | Passed; 79 tests with injected providers/mocked transport |
| Frontend typecheck and production build | Passed locally and in Vercel's builder |
| Vercel frontend and Python backend | Built and deployed |
| Public HTTP smoke | Passed preview, masking, saved reports, evidence and denial checks |
| Manual browser: four saved examples | Reviewed through the published UI |
| Manual browser: evidence | Original line focused/highlighted after selection |
| Manual browser: Markdown export | Downloaded bytes checked for saved-report label, evidence and masking |
| Manual browser: custom synthetic upload | Secret masked, blank line kept, saved-report action removed |
| Hosted OpenAI request | Not performed |

The [main-branch CI run](https://github.com/Denofix/ServerMedic/actions/runs/43961959692)
passed backend, frontend/browser and container jobs for `a6f4385`. Its ten browser
scenarios use an explicit test provider and do not prove real model inference.
The current pull request's Checks tab records validation of the revised UI,
including the key-free public workflow. Earlier local Unix-socket/browser download
failures do not describe the hosted GitHub runner.

## Local live-analysis evidence

The [local MVP acceptance record](ServerMedic_MVP_Acceptance_2026-11-06.md)
documents the separate real-model acceptance. Local inference requires the user's
own API credentials; it is not covered by saved-example or fixture-provider tests.

## Credential handling

The Vercel project has `PUBLIC_DEMO=true` and no OpenAI provider key. Existing
private-access configuration does not enable model calls without that key.
Visitors are not asked to paste an API key into the hosted page or browser
storage. Local credentials are read by the local backend and kept out of the
frontend build. No provider key was added or real model request made for this
published-mode change.
