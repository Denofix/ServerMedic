# 60–90 second demo

Use a configured real model for an AI demo. If using the test-only fixture server, explicitly say that it demonstrates the UI and validation pipeline with no model inference; the UI displays a test-provider banner.

| Time | Action / narration |
| --- | --- |
| 0–10 s | “ServerMedic turns small application logs into observations, possible causes, and concrete next checks.” Show the single-file limits. |
| 10–25 s | Load **PostgreSQL connection**. Show line 2's masked password and preserved blank line 3. “Common secrets are masked before the model sees the file.” |
| 25–45 s | Click **Analyze log**. “The backend analyzes the full accepted file, validates the response, and checks that every referenced line exists.” Allow for actual model latency; prepare a completed result before recording if needed. |
| 45–60 s | Read the observation and unconfirmed hypothesis. Click **L4** to focus the refused-connection line. “Quotations are extracted from this file, not written by the model.” |
| 60–75 s | Download Markdown. Open it and show evidence plus recommended checks. “Recommendations are reviewed by a human; nothing is executed.” |
| 75–90 s | Show a completed **Healthy startup** sample with zero findings. “No forced diagnoses, no accounts or database. FastAPI, React, OpenAI Responses API, Docker Compose, automated checks.” |

Do not claim production reliability, diagnostic accuracy, time savings, real AI acceptance or container validation without corresponding measurements. Model latency is variable; a prepared verified result can keep a recording within 90 seconds.
