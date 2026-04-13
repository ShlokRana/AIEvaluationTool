# Setup And Configuration

This page documents the required setup before running the Docker workflow.

The goal of this setup page is to make sure the containers can talk to each other correctly before you start any evaluation run. Most Docker-related issues in this project come from environment values, service naming, or browser automation configuration, so it is worth getting these pieces right first.

## Prerequisites

- Docker Engine `24+`
- Docker Compose `v2+`
- local clone of this repository

You do not need to install every application component manually when using Docker, but you do need a working Docker environment and a cloned repository because the images are built from the local source tree.

## Build Context And Services

The repository includes a Compose file and Dockerfiles for the main services:

- [docker-compose.yml][docker-compose]
- [Dockerfile.app-cli][dockerfile-app-cli]
- [Dockerfile.interface-manager][dockerfile-interface-manager]
- [Dockerfile.tdms-backend][dockerfile-tdms-backend]
- [Dockerfile.tdms-frontend][dockerfile-tdms-frontend]

The Compose stack starts:

- `db`
- `selenium-browser`
- `interface-manager`
- `app-cli`
- `tdms-backend`
- `tdms-frontend`

In practice, the core evaluation workflow usually depends on `db`, `selenium-browser`, `interface-manager`, and `app-cli`. The TDMS services are only needed if you also want the data-management UI.

## Create The Root `.env`

This Docker workflow reads environment variables from the root `.env` file.

Create it from the example if needed:

```bash
cp .env.example .env
```

At minimum, you should set the model-related variables described in the Docker and README guides:

```env
OLLAMA_URL="http://host.docker.internal:11434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

These values are especially important because the `app-cli` container relies on them when calling model endpoints during evaluation and analysis.

## Configure Root `config.json`

Use Docker service names so the containers can resolve each other correctly on the Compose network.

This is one of the biggest differences between local non-Docker execution and Docker execution. Inside the Compose network, services should refer to each other by service name rather than `localhost`.

Example:

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

## Configure Interface Manager For Docker Selenium

Update `src/app/interface_manager/config.json` to use the remote Selenium service:

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

This configuration tells Interface Manager not to try launching a browser locally inside the container. Instead, it connects to the dedicated Selenium container that already exposes WebDriver and a visible browser session.

## Why `host.docker.internal` Matters

The `app-cli` service is configured with `host.docker.internal:host-gateway` in Compose so containerized CLI commands can reach services running on the host machine.

This is especially important for:

- Ollama running on the host
- Sarvam AI served outside the Compose network
- local SSH-forwarded ports to a remote GPU host

That small detail is what makes the GPU workflows in the next page possible without having to add every model-serving process directly into Compose.

## Build The Images

Build the full stack:

```bash
docker compose build
```

If you only want the core evaluation services first:

```bash
docker compose build db selenium-browser interface-manager app-cli
```

Building once up front helps avoid runtime surprises later, especially when the workflow needs Selenium, MariaDB, and the Python CLI container to be ready together.

## Ports Used

- `3306` for MariaDB
- `4444` for Selenium WebDriver
- `7900` for Selenium noVNC
- `8000` for Interface Manager
- `8080` for TDMS frontend
- `8100` for TDMS backend

## Recommended Pre-Run Checklist

- `.env` created
- `config.json` updated for Docker service names
- `src/app/interface_manager/config.json` set to remote Selenium
- target details updated
- data files present
- model endpoints decided before starting execution

If these items are in place, the Docker run phase is usually much smoother.

[docker-compose]: ../../docker-compose.yml
[dockerfile-app-cli]: ../../Dockerfile.app-cli
[dockerfile-interface-manager]: ../../Dockerfile.interface-manager
[dockerfile-tdms-backend]: ../../Dockerfile.tdms-backend
[dockerfile-tdms-frontend]: ../../Dockerfile.tdms-frontend
[getting-started-docker]: ../03-getting-started-docker.md
[configuration]: ../05-configuration.md
[readme]: ../../README.md
[docker-guide]: ../../DOCKER.md
