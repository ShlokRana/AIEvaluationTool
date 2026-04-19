# Docker Run

This page documents the CLI workflow using a shell inside the running backend container.

It is the operational companion to [Setup And Configuration](./setup_and_configuration.md).

## Purpose

- Open a bash shell inside `app-backend`
- Run importer, testcase execution, analysis, and reporting commands from that shell

## Start Required Services

From the host machine:

```bash
docker compose build
docker compose up -d db selenium-browser interface-manager auth-service tdms-backend app-backend
```

Check status:

```bash
docker compose ps
```

## Open Bash In `app-backend`

From the host machine:

```bash
docker exec -it app-backend bash
```

If your local container is named differently, use:

```bash
docker exec -it aiet-app-backend bash
```

## Run CLI Commands Inside Container

All commands below are run inside the container shell.

## Import Test Data

```bash
python src/app/importer/main.py --config config.json
```

## Inspect Plans / Metrics (Optional)

```bash
python src/app/testcase_executor/main.py --config config.json --get-plans
```

```bash
python src/app/testcase_executor/main.py --config config.json --get-metrics
```

## Execute Testcases

```bash
python src/app/testcase_executor/main.py --config config.json --testplan-id <id> --execute
```

## Analyze Responses

```bash
python src/app/response_analyzer/analyze.py --config config.json --run-name <run_name>
```

## Generate The Report

```bash
python src/app/response_analyzer/report.py --config config.json --run-name <run_name> --get-report
```

For UI-side run monitoring and result interpretation, refer to:

- [Test Runs Manual](../TDMS_and_Dashboard_ui/test_runs_manual.md)
- [Run Configuration Manual](../TDMS_and_Dashboard_ui/run_configuration_manual.md)
- [Analysis And Run Details Manual](../TDMS_and_Dashboard_ui/analysis_and_run_details_manual.md)

## Optional: Start Sarvam Service

From the host machine:

```bash
docker compose --profile sarvam up -d sarvam-ai
```

## Exit Container Shell

```bash
exit
```

## Stop The Stack

From the host machine:

```bash
docker compose down
```

## Full Reset

From the host machine:

```bash
docker compose down -v
```

## Clean Up Docker Resources

From the host machine:

```bash
docker system prune -a --volumes
```

## Troubleshooting

- If `docker exec -it app-backend bash` fails, run `docker ps` and confirm the container name.
- If DB connection fails, verify `db.host` is `db` in `config.json`.
- If browser-backed execution fails, verify `selenium_mode: "remote"` and `selenium_remote_url: "http://selenium-browser:4444/wd/hub"` in `src/app/interface_manager/config.json`.

Recreate core services:

```bash
docker compose up -d --force-recreate db selenium-browser interface-manager auth-service tdms-backend app-backend app-front-end tdms-frontend nginx
```
