# Hosted demo verification — 2026-11-16

URL: https://servermedic.vercel.app/

Deployment: `dpl_FwRp6HvUkmTP8asBAChb5Q3AmpKh` (Vercel Services, production).
Source base: `33112910f5f06189cace01595f9bb82836ce6f84` plus the public-demo patch.
This was a direct source deployment, not a Git-connected deployment. At the initial deployment, the GitHub integration rejected repository writes.
Repository access was subsequently granted, and the public-demo patch is now
published for review in a separate GitHub branch. The hosted deployment still
uses the directly uploaded source; Git integration is a separate setup step.

## Executed checks

| Check | Result |
| --- | --- |
| Backend Ruff | Passed |
| Backend pytest | 79 passed; injected providers and mocked transport, no real inference |
| Frontend TypeScript and production build | Passed locally and in Vercel's builder |
| Vercel frontend and Python backend | Built and deployed |
| Deployed HTTP smoke | Frontend, SPA fallback, JSON API, preview, masking, all saved reports, evidence and anonymous denial passed |
| Browser: four saved examples | Reviewed through the published production UI |
| Browser: evidence jump | L4 selected and the original log line received focus/highlight |
| Browser: Markdown export | Download completed; saved-report label, L4 and masked data verified in the downloaded bytes |
| Browser: custom synthetic file | Uploaded; password masked and blank line preserved; saved report action removed |
| Live OpenAI on hosted deployment | Pending the owner's `OPENAI_API_KEY`; no hosted real-inference success is claimed |

The Playwright suite now contains 10 scenarios. Its local browser launch was
blocked by the execution environment's Unix socket restriction; the alternative
browser download also failed. These are not reported as passing automated
browser tests. The hosted browser checks above were performed separately.
The pull request Checks tab is the authoritative source for subsequent GitHub
Actions results, including the 10 automated browser scenarios. The local browser
restriction above does not describe the hosted GitHub runner.

## Access and remaining activation

`PUBLIC_DEMO=true`, `LLM_MODEL=gpt-6-luna` and a random, encrypted
`DEMO_ACCESS_CODE` are configured in the Vercel project. The access code is not
included in the patch, repository, frontend or this report. The owner must add
`OPENAI_API_KEY` directly to Vercel and redeploy, then run one real analysis.
View or replace the demo code in Vercel's environment-variable settings when
sharing live access with intended testers.

The public saved reports remain curated references, with no claim that opening
them calls a model. Live-analysis errors never return a saved report. Per-process
rate/concurrency limits do not constitute a global financial cap.

Automatic deploys from GitHub remain a separate account setup step: install the
Vercel GitHub integration and connect `Denofix/ServerMedic` to this project.
