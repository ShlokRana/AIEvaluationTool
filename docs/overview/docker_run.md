# Docker Run

The Docker workflow provides a containerized way to run the AI Evaluation Tool stack without setting up every supporting service manually on the host system.

## What Docker Adds

Docker packages the main evaluation services into a reproducible environment. This makes it easier to start the database, browser automation layer, interface layer, and CLI runtime in a consistent way across machines.

## Core Services In The Stack

The Docker setup centers around these services:

- `db` for MariaDB
- `selenium-browser` for browser automation and live browser viewing
- `interface-manager` for target interaction
- `app-cli` for importer, execution, analysis, and reporting commands

Optional services are also available for TDMS:

- `tdms-backend`
- `tdms-frontend`

## Typical Docker Workflow

At a high level, the Docker workflow looks like this:

1. Prepare `.env` and repository configuration files.
2. Build the Docker images.
3. Start the core services.
4. Make Ollama and Sarvam AI reachable from the containerized CLI flow.
5. Run importer, testcase execution, analysis, and report commands with `docker compose`.

This makes Docker a good option when you want a reproducible environment for local development, shared setup across teammates, or cleaner service orchestration.

## GPU And Model Serving

The Docker setup is designed to work with both local and remote model-serving patterns. In practice, Docker is mainly used to containerize the evaluation services, while Ollama and Sarvam AI can be hosted either on the same machine or on a remote GPU machine and exposed through environment variables.

## When To Use This Path

Docker is a strong choice when:

- you want a repeatable environment
- you want to avoid manual service-by-service installation
- you need Selenium, MariaDB, Interface Manager, and the CLI to work together consistently
- you want to keep the execution workflow closer to production-like service boundaries

## Related Sections

- [Docker Setup](../docker_setup/index.md)
- [AI Evaluation Tool CLI](../ai_evaluation_tool_cli/index.md)

