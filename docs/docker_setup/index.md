# Docker Setup

This section documents the Docker-based workflow for the AI Evaluation Tool. It covers environment preparation, service configuration, GPU-backed model setup, and the commands used to run the evaluation pipeline through Docker.

If you want a containerized setup that avoids manual service-by-service installation, this is the best place to start. The pages in this section are organized to match the way the stack is normally brought up in practice: first the base configuration, then the model-serving setup, and finally the commands used during everyday execution.

## What This Section Covers

- Docker prerequisites and stack layout
- setup and configuration of Docker-based services
- local GPU and remote GPU model-serving patterns
- running importer, executor, analyzer, and report commands in containers
- optional TDMS services, cleanup, and troubleshooting

## Chapters

- [Setup and Configuration][setup-and-configuration]
- [GPU Setup][gpu-setup]
- [Docker Run][docker-run]

## Stack Overview

The Docker stack in this repository is built around the services defined in [docker-compose.yml][docker-compose]:

- `db` for MariaDB
- `selenium-browser` for headed Chrome and Selenium WebDriver
- `interface-manager` for target communication
- `app-cli` for importer, testcase execution, analysis, reporting, and utility commands
- `tdms-backend` and `tdms-frontend` as optional TDMS services

Together, these services provide the database layer, browser automation layer, target communication layer, and the CLI execution environment needed for a full end-to-end evaluation run.

## How The Docker Workflow Fits Together

- Prepare `.env` and repository config files.
- Build the required Docker images.
- Start the database, Selenium browser, and Interface Manager.
- Make model endpoints reachable from Docker containers.
- Run CLI commands with `docker compose run`.
- Stop, reset, or extend the stack with optional services as needed.

## Related Sections

- [setup-and-configuration](./setup_and_configuration.md)
- [gpu-setup](./gpu_setup.md)
- [docker-run](./docker_run.md)
