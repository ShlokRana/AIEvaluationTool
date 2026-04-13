# Docker Run

This page documents the day-to-day commands used to build, start, run, monitor, and stop the Docker-based evaluation workflow.

Think of this page as the operational companion to the setup pages. Once configuration and GPU connectivity are ready, these are the commands you will use most often while running evaluations.

## Build The Images

Build the full stack:

```bash
docker compose build
```

This prepares the reusable images for the CLI, Interface Manager, and optional TDMS services.

## Start Core Services

Start the database, Selenium browser, and Interface Manager:

```bash
docker compose up -d db selenium-browser interface-manager
```

These are the baseline services that should be running before you try importer, executor, or analyzer commands.

## Check Service Status

```bash
docker compose ps
```

For browser-backed targets, you can open the Selenium noVNC view at `http://localhost:7900`.

This is a good early sanity check before starting a longer evaluation run.

## Import Test Data

The importer loads the configured datapoints and evaluation assets into the database used by the rest of the workflow.

```bash
docker compose run --rm app-cli \
python src/app/importer/main.py --config config.json
```

## Run Testcase Execution

This step sends prompts to the configured target application through Interface Manager and records the responses for later analysis.

```bash
docker compose run --rm -w /app/src/app/testcase_executor app-cli \
python main.py --config config.json --testplan-id <id> --execute
```

If you need more control, use the same executor arguments documented in the CLI section, such as `--metric-id`, `--testcase-id`, or `--max-testcases`.

## Analyze Responses

After execution completes, run the analyzer to evaluate the collected responses with the configured strategies.

```bash
docker compose run --rm -w /app/src/app/response_analyzer app-cli \
python analyze.py --config config.json --run-name <run_name>
```

## Generate The Report

The report step turns analyzed run data into a more readable final output for review and sharing.

```bash
docker compose run --rm -w /app/src/app/response_analyzer app-cli \
python report.py --config config.json --run-name <run_name>
```

## Optional: Run TDMS

If you also want the Test Data Management System in the same Docker environment, you can bring up the TDMS services separately.

Build TDMS images:

```bash
docker compose build tdms-backend tdms-frontend
```

Start TDMS services:

```bash
docker compose up -d tdms-backend tdms-frontend
```

Access:

- TDMS frontend at `http://localhost:8080`
- TDMS backend docs at `http://localhost:8100/docs`

## Stop The Stack

Use this when you want to shut the environment down but preserve existing database state.

Stop containers but keep persistent volumes:

```bash
docker compose down
```

## Full Reset

Stop the stack and remove named volumes:

```bash
docker compose down -v
```

Use this when you want to fully reset MariaDB-backed state.

## Clean Up Docker Resources

```bash
docker system prune -a --volumes
```

Use this only when you intentionally want broader Docker cleanup.

## Troubleshooting

Most issues in this flow come from one of four places: database readiness, Selenium reachability, stale config, or model endpoint connectivity.

- Keep `selenium_mode: "remote"` and `selenium_remote_url: "http://selenium-browser:4444/wd/hub"`.
- If CLI commands fail on database connection, verify `db` is healthy with `docker compose ps`.
- If browser automation is not visible, verify `http://localhost:7900` is reachable.
- If config changes are not reflected, recreate the services.

Recreate the stack:

```bash
docker compose up -d --force-recreate db selenium-browser interface-manager app-cli tdms-frontend tdms-backend
```

## Recommended Run Order

- build images
- start core services
- verify GPU endpoints are reachable
- import test data
- execute testcases
- run analysis
- generate reports

