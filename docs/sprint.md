# MVP sprint

Target: a checked first MVP in 5–6 hours of joint product/engineering work. The estimates below are planning budgets, not a claim of time spent or a guarantee.

| Stage | Budget | Completion gate |
| --- | --- | --- |
| Contract, fixtures, preprocessing | 45 min | Size/encoding/line rules fixed; preview never returns raw secrets |
| Analyzer adapter, validation, report | 90 min | Stub tests and SDK transport tests pass; invalid references produce no report |
| React workspace | 90 min | Upload, samples, states, line navigation and export work |
| Browser checks and packaging | 60 min | Full scenario checked in a browser; reproducible commands included |
| Model/Compose acceptance, fixes | 45–75 min | Real call and container launch checked in an environment that provides them |

## Definition of done

- A single UTF-8 .log/.txt file up to 65,536 original bytes and 500 original lines is accepted.
- All accepted lines, including empty lines, are analyzed without truncation.
- Preview, LLM input, evidence and report use the same redacted document.
- Findings separate observations from hypotheses; every finding has valid line references.
- Citations come from server extraction, never generated quotations.
- Healthy logs may have no findings; insufficient evidence is acknowledged.
- All expected input/provider failures produce useful errors with no report.
- Browser flow and Markdown download pass with a clearly labeled test provider.
- Backend tests, frontend typecheck/build, Compose configuration and CI files are present.
- Real API inference and container runtime acceptance are recorded separately from mock checks.

## Scope

No accounts, database, history, background queue, Kubernetes, RAG, server access, tools, command execution or automated repairs. The analyzer is a replaceable Python protocol. Each analysis completes in one request.

## Actual acceptance

See [verification.md](verification.md) for executed checks and remaining external gates. Project time has not been instrumented; do not present the planning budget as measured development time.
