# AIEvaluationTool Docker Guide

Run the AIEvaluationTool stack using Docker Compose, including MariaDB, Selenium, Interface Manager, and CLI executor.

## What This Starts

- `db` (MariaDB)
- `selenium-browser` (headed Chrome + WebDriver)
- `interface-manager` (FastAPI service for target interaction)
- `app-cli` (import, execution, analysis, report commands)
- Optional: `tdms-backend`, `tdms-frontend`

## Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- Repository cloned locally

## GPU / Model Endpoint Setup (`.env`)

This stack reads environment variables from the root `.env` file:

- Path: `./.env`
- Template: `./.env.example`

Create it if needed:

```bash
cp .env.example .env
```

Set values based on your setup:

### Case 1: Docker machine has GPU

Run/host inference services on the same machine where Docker is running, then point `.env` to host endpoints:

```env
OLLAMA_URL="http://host.docker.internal:11434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

### Case 2: Port forwarding (Docker -> local -> remote GPU)

Use SSH port forwarding from your local machine to the remote GPU machine, then point Docker containers to local forwarded ports via `host.docker.internal`.

Example tunnel:

```bash
ssh <user>@<remote-gpu-host> \
  -L <free-local-1>:localhost:11434 \
  -L <free-local-2>:localhost:16000
```

Then set `.env`:

```env
OLLAMA_URL="http://host.docker.internal:<free-local-1>/"
GPU_URL="http://host.docker.internal:<free-local-2>/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

Notes:

- `OLLAMA_URL` is used by LLM-as-judge and other local-LLM strategies.
- `GPU_URL` is used by strategy modules that call the GPU inference API.
- Keep these URLs reachable from inside Docker containers.

## Required Configuration

### 1. Root `config.json`

Use Docker service names for DB and Interface Manager:

```json
{
  "db": {
    "engine": "mariadb",
    "host": "db",
    "port": 3306,
    "user": "aiet_user",
    "password": "aiet_password",
    "database": "aievaluationtool"
  },
  "files": {
    "plans": "data/plans.json",
    "testcases": "data/updated_datapoints.json",
    "strategies": "data/strategy_id.json"
  },
  "target": {
    "application_type": "WHATSAPP_WEB",
    "application_name": "Vaidya AI",
    "application_url": "https://web.whatsapp.com/",
    "agent_name": "Vaidya AI"
  },
  "interface_manager": {
    "docker": true,
    "base_url": "http://interface-manager:8000"
  }
}
```

### 2. `src/app/interface_manager/config.json`

Use remote Selenium inside Docker:

```json
{
  "application_type": "WHATSAPP_WEB",
  "server_url": "http://localhost:3000",
  "whatsapp_url": "https://web.whatsapp.com",
  "agent_name": "Vaidya AI",
  "application_name": "Vaidya AI",
  "application_url": "https://web.whatsapp.com/",
  "headless": "False",
  "selenium_mode": "remote",
  "selenium_remote_url": "http://selenium-browser:4444/wd/hub"
}
```

## Quick Start

### 1. Build images

```bash
docker compose build
```

### 2. Start core services

```bash
docker compose up -d db selenium-browser interface-manager
```

### 3. Check health/status

```bash
docker compose ps
```

### 4. Open live browser view (for WhatsApp/web flows)

- Selenium noVNC: http://localhost:7900

## Execute Evaluation Pipeline

### 1. Import test data

```bash
docker compose run --rm app-cli \
python src/app/importer/main.py --config config.json
```

### 2. Run test execution

```bash
docker compose run --rm -w /app/src/app/testcase_executor app-cli \
python main.py --config config.json --testplan-id <id> --execute
```

### 3. Analyze responses

```bash
docker compose run --rm -w /app/src/app/response_analyzer app-cli \
python analyze.py --config config.json --run-name <run_name>
```

### 4. Generate report

```bash
docker compose run --rm -w /app/src/app/response_analyzer app-cli \
python report.py --config config.json --run-name <run_name>
```

## Stop / Reset

Stop containers:

```bash
docker compose down
```

Stop and remove DB volume (full reset):

```bash
docker compose down -v
```

## Optional: Run TDMS

Build TDMS images:

```bash
docker compose build tdms-backend tdms-frontend
```

Start TDMS services:

```bash
docker compose up -d tdms-backend tdms-frontend
```

Access:

- TDMS Frontend: http://localhost:8080
- TDMS Backend docs: http://localhost:8100/docs

## Ports Used

- `3306`: MariaDB
- `4444`: Selenium WebDriver
- `7900`: Selenium noVNC
- `8000`: Interface Manager
- `8080`: TDMS Frontend
- `8100`: TDMS Backend

## Troubleshooting

- Keep `selenium_mode: "remote"` and `selenium_remote_url: "http://selenium-browser:4444/wd/hub"`.
- If CLI commands fail on DB connection, ensure `db` is healthy: `docker compose ps`.
- If browser automation is not visible, verify `http://localhost:7900` is reachable.
- If config changes are not reflected, restart services:

```bash
docker compose up -d --force-recreate db selenium-browser interface-manager app-cli tdms-frontend tdms-backend
```
