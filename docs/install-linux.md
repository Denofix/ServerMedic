# Linux: installation, configuration and usage

[Back to README](../README.md) · [Windows guide](install-windows.md)

This guide uses a **Bash-compatible terminal**. Run commands one line at a time, without copying a terminal prompt. Use one local installation method: Docker Compose or native Python/Node.js.

## Choose how to run ServerMedic

| Method | Install on your computer | Open in your browser |
| --- | --- | --- |
| Hosted demo | Nothing | [servermedic.vercel.app](https://servermedic.flareledger.fun/) |
| Docker Compose (recommended for local use) | Git, Docker Engine and Compose v2 or later | [localhost:8080](http://localhost:8080) |
| Native development | Git, Python 3.12 with venv, Node.js 24 with npm | [localhost:5173](http://localhost:5173) |

The hosted demo and local app both offer four **saved example reports** without an OpenAI key. Previewing your own file also needs no key. **Analyze log** makes a live OpenAI request and requires server-side credentials; the hosted demo additionally requires an access code from its owner. Each live request can incur API charges.

## 1. Install prerequisites

On Ubuntu/Debian, install Git and the tools used in this guide:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates
git --version
```

On other distributions, install equivalent packages using your distribution's package manager.

For the Docker method, follow [Docker's installation instructions for your distribution](https://docs.docker.com/engine/install/). The [Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/) include Docker Engine, Buildx and the **Compose plugin** (`docker-compose-plugin`). Use the `docker compose` command.

On a systemd-based installation, start the engine if necessary, then check it:

```bash
sudo systemctl start docker
sudo docker version
sudo docker compose version
```

`docker version` must show both Client and Server. The examples below use `sudo docker` for a system Docker Engine. If you already use a rootless engine or Docker Desktop for Linux, use `docker` without `sudo` consistently so you reach that engine. Python and Node.js run inside the images for this method; installing them on the host is unnecessary.

## 2. Download the current application

Clone as your normal user, from a directory you own:

```bash
mkdir -p "$HOME/projects"
cd "$HOME/projects"
git clone https://github.com/Denofix/ServerMedic.git servermedic
cd servermedic
```

These commands use the current default branch. The earlier `v0.1.0` tag predates the hosted-demo additions. If you already have a checkout, use the update instructions in section 7 instead of cloning into it.

## 3. Configure the backend

From the repository root, create a local configuration file only if one does not already exist:

```bash
if [ ! -f .env ]; then
  cp .env.example .env
fi
chmod 600 .env
```

Open `.env` in a text editor, such as `nano .env` or `vi .env`, and save your settings in that file at the repository root.

| Variable | What to set |
| --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key for live analysis; leave empty for previews and saved reports |
| `LLM_MODEL` | The exact API model ID available to your API project, with Responses API and Structured Outputs support; leave empty when not using live analysis |
| `LLM_TIMEOUT_SECONDS` | `60` by default; allowed range 1–180 seconds |
| `LLM_MAX_OUTPUT_TOKENS` | `6000` by default; allowed range 256–16000 |
| `WEB_PORT` | `8080` by default; affects Docker Compose only |
| `PUBLIC_DEMO` | Keep `false` for the local installation described here |

Use the [OpenAI model catalog](https://developers.openai.com/api/docs/models) to select a compatible model. The project's recorded local acceptance used `gpt-6-luna`; access depends on your API project. A ChatGPT subscription does not configure the backend: the app needs its own API credential and model ID.

Keep the key in the backend's `.env`, which Git ignores. Do not add it to React code or a `VITE_` variable. Shell environment variables take precedence over `.env`; the native backend reads the file directly, so you do not need to `source` it.

For a shared deployment, [the hosted-demo guide](public-demo.md) explains `PUBLIC_DEMO=true`, the private `DEMO_ACCESS_CODE` (16–128 characters), and the per-process admission settings. Local Compose binds its published port to `127.0.0.1`.

## 4. Start with Docker Compose

From the repository root:

```bash
sudo docker compose config --quiet
sudo docker compose up --build --wait --wait-timeout 180
sudo docker compose ps
```

The first build downloads images and dependencies. `--wait` runs the services in the background and waits for their health checks. Open [http://localhost:8080](http://localhost:8080).

Check the API through the same frontend address:

```bash
curl --fail --silent --show-error http://localhost:8080/api/health
```

`status: "ok"` means the backend is running. `analysis_configured: false` is expected when the key or model is empty; previews and saved reports still work. `true` checks configuration presence, not whether a model request will succeed.

After editing `.env`, run `sudo docker compose up --build --wait --wait-timeout 180` again and reload the browser. `docker compose restart` alone does not apply changed Compose environment variables.

If port 8080 is occupied, change `WEB_PORT=8081` in `.env`, run the same `up` command, and open [http://localhost:8081](http://localhost:8081). Use that port for health checks too.

### Running inside a virtual machine or on a remote Linux host

`localhost` refers to the machine running the browser. In a Linux VM, open the browser inside that VM. For a remote host with SSH access, you can instead forward its local frontend port from your workstation:

```bash
ssh -L 8080:127.0.0.1:8080 user@linux-host
```

Replace `user@linux-host` with your SSH login, leave the session open, and visit `http://localhost:8080` on your workstation. Use an available local port if needed. This keeps the supplied Compose binding local to the Linux host.

## 5. Alternative: run without Docker

Skip this section if you use Docker. This method starts the production FastAPI application and the Vite development server locally.

The native environment must provide **Python 3.12**, its `venv` module, and **Node.js 24** with npm. On **Ubuntu 24.04**, Python can be installed with:

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

For other distributions/releases, use a supported method that provides Python 3.12, or use the Docker method. The default `python3` package may provide a different version; do not replace the operating system's Python.

Install Node.js 24 using the [official download selector](https://nodejs.org/en/download) or [Node.js 24 archive](https://nodejs.org/en/download/archive/v24), choosing your Linux architecture and following the selected installation method. Your distribution's default `nodejs` package may be another major version. Verify:

```bash
python3.12 --version
node --version
npm --version
```

Expect Python `3.12.x` and Node `v24.x`. From the repository root, install the pinned runtime dependencies into a virtual environment:

```bash
cd "$HOME/projects/servermedic"
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

Create and edit `.env` as in section 3. The commands below use the virtual environment's executable directly; no activation or system-wide pip install is needed.

In **terminal 1**, from the repository root, start the backend:

```bash
cd "$HOME/projects/servermedic"
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

Leave it running. In **terminal 2**, install the frontend dependencies and start the repository's Vite executable:

```bash
cd "$HOME/projects/servermedic/frontend"
npm ci
npm exec -- vite --host 127.0.0.1 --port 5173 --strictPort
```

Open [http://localhost:5173](http://localhost:5173). Vite forwards `/api` to the backend on port 8000. `--strictPort` keeps the frontend from silently switching ports.

Check health with `curl --fail --silent --show-error http://localhost:8000/api/health`. Interactive API docs are at [http://localhost:8000/docs](http://localhost:8000/docs). `WEB_PORT` does not change either native server's port.

After changing `.env`, stop terminal 1 with **Ctrl+C**, repeat its backend command, and reload the browser. Use `app.main:app`; the `tests.browser_app:app` entrypoint is a separate test fixture and does not provide live AI analysis.

## 6. Use the service

### Explore a saved report without an API key

1. Open the hosted demo or your local frontend address.
2. In **Try a sample**, choose **PostgreSQL connection**. The processed preview appears with original line numbers; the password on line 2 is masked.
3. Click **Open saved example report**. The notice identifies this as a curated saved example; opening it does not call an AI model.
4. Read **Observed in the log** and **Possible cause · unconfirmed** separately. Click an evidence button such as **L4** to focus the corresponding line.
5. Review **Recommended checks**, limitations and missing context.
6. Click **Download Markdown**. Your browser downloads a file such as `postgres-servermedic.md`.
7. Try **Missing configuration**, **Port already in use**, and **Healthy startup**. The saved healthy report has zero findings.

### Analyze your own log

1. Use **browse files** or drag one file into the upload area.
2. Supply one UTF-8 `.log` or `.txt` file, at most **65,536 bytes** and **500 lines**, including blank lines. A final newline counts as an additional empty line. Export a relevant text extract from large or binary logs first.
3. Review **Processed log** before analysis. Selection already uploads the raw file to the backend for masking. Common secrets become `[REDACTED]`, but masking can miss sensitive values.
4. For your local installation, configure the API key and model on the backend. On the hosted demo, enter the owner's code into **Live analysis access code** when live analysis is available. The code is separate from the OpenAI API key; visitors do not enter an API key in the page.
5. Click **Analyze log**, wait for the result, inspect its evidence and export Markdown. Each explicit retry can make another paid API request.

The saved-report button is available only for bundled examples, not for arbitrary uploaded files. There is no saved-report fallback when live analysis fails. A result saying **No problems identified** applies to the supplied sample and does not establish that the whole system is healthy.

ServerMedic recommends checks for human review; it does not connect to your server or run commands. Reports and files are not saved as application history. Download the Markdown before refreshing or removing the selected file. Reloading the page also clears an entered demo code.

## 7. Stop, inspect and update

For Docker, run these commands from the repository root:

```bash
sudo docker compose logs --tail 100 backend frontend
sudo docker compose down
```

`down` stops and removes the project's containers and network. It leaves the source code and `.env` in place. To start again, repeat section 4. For native servers, press **Ctrl+C** in both terminals.

To update an existing checkout, first stop native servers, or stop Docker with `sudo docker compose down`. Check for local changes before pulling:

```bash
cd "$HOME/projects/servermedic"
git status --short
```

If there is output, preserve your local edits before continuing. For a clean checkout:

```bash
git switch main
git pull --ff-only
```

Then rebuild/start Docker as in section 4. For the native method, repeat the `pip install` and `npm ci` commands from section 5, then start both servers. The conditional `.env` copy preserves your existing settings.

## 8. Troubleshooting

| Symptom | What to check |
| --- | --- |
| Permission denied on `/var/run/docker.sock` | With the system engine, use the guide's `sudo docker` commands. For an already configured rootless/Desktop engine, use its own context without `sudo`. |
| Docker cannot connect to its daemon | Check `sudo systemctl status docker` for a systemd system engine. Start the service, or start the rootless/Desktop engine you use. |
| Compose says no configuration file was found | Run it in the repository root containing `compose.yaml`. Install a Compose plugin supporting the shown flags if they are unknown. |
| Port 8080 is already in use | Set `WEB_PORT=8081` and repeat Compose `up`; open port 8081. |
| Native backend port 8000 is busy | Stop the other process using it. Vite's committed proxy targets port 8000; changing only Uvicorn's port breaks API calls. |
| Python venv fails / externally managed Python error | On Ubuntu 24.04 install `python3.12-venv`, create `.venv`, and use `.venv/bin/python -m pip`. Install app packages inside that environment. |
| Frontend install/build rejects the Node version | Check `node --version` in that terminal and select Node.js 24. |
| Browser cannot reach the app from outside a VM | Open it inside the VM, or use the SSH forwarding example. The supplied Compose port binds to the Linux host's loopback address. |
| Backend unavailable / samples do not load | Check Compose health/logs, or keep both native terminals running. Open the frontend port, then reload the page. |
| Live analysis is unavailable / `not_configured` | Set both key and model in the root `.env`, restart/recreate the backend and reload. Shell variables override `.env`. |
| 401 / `demo_access_required` | Enter the current owner-provided code. Reloading clears it. A local install with `PUBLIC_DEMO=false` does not require a code. |
| 429 / `demo_busy` or `demo_rate_limited` | Wait for the active call to finish or the rate window to expire; avoid repeated clicks. |
| 503 / `llm_auth`, `llm_configuration` or `llm_rate_limit` | Check the backend API key, exact model ID, model access, API quota and billing. A successful health check does not validate these. |
| 504 / `llm_timeout`, or 502 / `invalid_result` | Review the log, model support and timeout/output budgets before retrying. No substitute result is fabricated. |
| UTF-8, control-character or size/line error | Export a smaller relevant UTF-8 text file. Binary logs and ANSI terminal escapes are rejected; blank and trailing lines count toward the limit. |

For complete configuration and API details, see [README](../README.md), [the API contract](api.md) and [hosted deployment setup](public-demo.md). Only masked text and filename are sent to OpenAI during live analysis; raw uploads reach the backend even for preview. Use non-confidential data in the public demo.
