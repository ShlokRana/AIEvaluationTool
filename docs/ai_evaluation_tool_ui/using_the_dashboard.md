# Using The Dashboard

The Test Case Execution Dashboard provides an end-to-end interface for transparent and structured AI evaluation. It helps teams move from configuration to monitoring to detailed result review in one place.

## Dashboard Overview

The dashboard is designed for:

- configuring and starting evaluation runs
- monitoring execution progress in real time
- reviewing completed results with more context than raw logs
- inspecting testcase-level outcomes and evaluation reasoning

## Monitor Test Runs

The main run listing provides the high-level operational view of the system. It allows you to track:

- run ID
- run name
- target
- status
- duration
- domain

You can also filter runs by domain, target, or status to focus on the executions that matter most.

![Test runs overview](../../screenshots/TRDB_first_page.png)

## Create A New Test Run

The new run flow allows you to launch evaluations directly from the interface. Typical configuration choices include:

- target model or application
- test plan
- domain
- language
- metrics
- optional testcase limits or a specific testcase ID

Once the configuration is ready, starting the run sends the execution request through the dashboard workflow instead of requiring a CLI-first flow.

![Create a new test run](../../screenshots/TRDB_add_test_run.png)

## View Test Run Details

Detailed run pages make it easier to understand what happened during execution. These views typically include:

- execution timeline visualization
- results table with testcase, metric, score, and status information
- filtering by metric or status
- run-level context for reviewing progress and outcomes

This is where the dashboard becomes especially useful for reviewing larger or longer-running evaluations.

![Test run details](../../screenshots/TRDB_test_run_details.png)

## Inspect Individual Test Cases

The testcase detail view provides the most granular level of inspection. It helps you examine:

- numerical score
- evaluation reasoning
- conversation ID
- metadata
- full conversation details including user prompt, system prompt, and agent response

This view is useful for diagnosing failures, understanding borderline scores, and validating how the evaluation strategy interpreted a specific interaction.

![Single testcase details](../../screenshots/TRDB_single_testcase_eval_details.png)

## When The Dashboard Is Most Useful

The dashboard is especially helpful when:

- multiple runs need to be monitored together
- stakeholders prefer a visual interface over CLI output
- teams need to review timelines, filters, and testcase details quickly
- evaluation results must be explored interactively rather than only exported
