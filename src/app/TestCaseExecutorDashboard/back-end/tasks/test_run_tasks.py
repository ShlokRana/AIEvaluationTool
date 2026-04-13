import asyncio
import json
import threading
from datetime import datetime

from configuration.database import db
from configuration.paths import (
    ROOT_CONFIG_PATH as config_path,
    profile_path,
)
from lib.data import Conversation, RunDetail
from lib.interface_manager import InterfaceManagerClient
from services.ws_manager import ws_manager
from utils.port import watch_im_process


def is_error_response(response):
    error_indicators = [
        "chat not found",
        "[error: max retries exceeded]",
        "[error: connection refused]",
        "no response received",
    ]
    return len(response) == 0 or any(
        indicator in response[0]["response"].lower() for indicator in error_indicators
    )

with open(config_path, "r") as f:
    config_read = json.load(f)

interface_manager_config=config_read.get("interface_manager", {})

async def step(ws_payload, delay=0.1):
    await ws_manager.send_all(ws_payload)
    await asyncio.sleep(delay)


async def execute_testcases(
    run_name,
    run_id,
    plan_name,
    target,
    testcases,
    run,
):
    print(f"🚀 Background execution started for run {run_id}")

    client = None
    try:
        print("started")
        stop_watcher = threading.Event()
        watcher_thread = threading.Thread(
            target=watch_im_process,
            args=(interface_manager_config, profile_path, stop_watcher),
            daemon=True,
        )
        watcher_thread.start()

        agent_name = target
        application_name = target
        target_obj = db.get_target_by_name(target)
        application_url = target_obj.target_url
        APPLICATION_TYPE_MAP = {
            "WhatsApp": "WHATSAPP_WEB",
            "WebApp": "WEBAPP",
            "API": "API",
        }
        print("target object", target_obj)
        if target_obj.target_type not in APPLICATION_TYPE_MAP:
            raise ValueError(f"Unsupported target_type: {target_obj.target_type}")

        application_type = APPLICATION_TYPE_MAP[target_obj.target_type]

        if interface_manager_config.get("docker", False):
            base_url = interface_manager_config["base_url"]
        else:
            base_url = interface_manager_config["base_url_local"]

        client = InterfaceManagerClient(
            base_url=base_url,
            application_type=application_type,
            agent_name=agent_name,
        )
        await ws_manager.send_all(
            {"type": "RUN_STARTED", "runId": run_id, "total": len(testcases)}
        )

        try:
            client.sync_config(
                {
                    "application_name": application_name,
                    "application_type": application_type,
                    "agent_name": agent_name,
                    "application_url": application_url,
                }
            )
            client.apply_server_config()
        except Exception as e:
            print(f"Interface manager setup failed for run {run_id}: {e}")
            run.status = "FAILED"
            run.end_ts = datetime.now().isoformat()
            db.add_or_update_testrun(run=run)
            await ws_manager.send_all(
                {
                    "type": "RUN_FINISHED",
                    "runId": run_id,
                    "status": "FAILED",
                    "error": str(e),
                }
            )
            return

        print("⏳ Waiting for WhatsApp to be ready...")

        print("✅ Starting testcase loop!")
        for index, testcase in enumerate(testcases, start=1):
            rundetail = None
            try:
                rundetail = RunDetail(
                    run_name=run_name,
                    plan_name=plan_name,
                    metric_name=testcase.metric,
                    testcase_name=testcase.name,
                )
                rundetail_id = db.add_or_update_testrun_detail(rundetail)
                # For continue runs, always rerun test cases regardless of previous status
                # Commented out the status check to force rerun
                # run_status = db.get_status_by_run_detail_id(run_detail_id=rundetail_id)
                # if run_status is not None and run_status == "COMPLETED":
                #     print(
                #         f"Run detail for testcase {testcase.name} (ID: {testcase.testcase_id}) is already completed. Skipping execution."
                #     )
                #     continue

                message_to_agent = testcase.prompt.user_prompt or ""
                if testcase.prompt.system_prompt:
                    message_to_agent = testcase.prompt.system_prompt + " " + message_to_agent

                conv = Conversation(
                    target=target,
                    run_detail_id=rundetail_id,
                    testcase=testcase.name,
                )
                conv_id = db.add_or_update_conversation(conversation=conv)
                print(f"A new conversation is created with ID: {conv_id}")

                rundetail.status = "RUNNING"
                db.add_or_update_testrun_detail(rundetail)
                conv.prompt_ts = datetime.now().isoformat()
                db.add_or_update_conversation(conversation=conv)

                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 1,
                        "status": "DONE",
                    }
                )
                await ws_manager.send_all(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 2,
                        "status": "RUNNING",
                    }
                )
                step2_start = datetime.now()
                response_from_agent = client.chat(
                    chat_id=testcase.testcase_id,
                    prompt_list=[message_to_agent],
                )
                step2_duration = (datetime.now() - step2_start).total_seconds()
                if step2_duration < 2:
                    print(
                        f"Step 2 completed too fast ({step2_duration:.2f}s) — marking as FAILED"
                    )
                    await step(
                        {
                            "type": "STEP_UPDATE",
                            "runId": run_id,
                            "testcaseIndex": index,
                            "step": 2,
                            "status": "FAILED",
                        }
                    )
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                    continue
                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 2,
                        "status": "DONE",
                    }
                )
                agent_response = response_from_agent.json().get("response", "")

                if is_error_response(agent_response):
                    print("No response received from the agent for test case 1.")
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                    continue

                conv.response_ts = datetime.now().isoformat()
                conv.agent_response = agent_response[0]["response"]
                db.add_or_update_conversation(conversation=conv)

                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 3,
                        "status": "DONE",
                    }
                )
                await step(
                    {
                        "type": "STEP_UPDATE",
                        "runId": run_id,
                        "testcaseIndex": index,
                        "step": 4,
                        "status": "DONE",
                    }
                )
                await step(
                    {"type": "TESTCASE_FINISHED", "runId": run_id, "current": index}
                )
                rundetail.status = "COMPLETED"
                db.add_or_update_testrun_detail(rundetail)
            except Exception as e:
                print(
                    f"Testcase execution failed for run {run_id}, testcase index {index}: {e}"
                )
                if rundetail is not None:
                    rundetail.status = "FAILED"
                    db.add_or_update_testrun_detail(rundetail)
                continue

        stop_watcher.set()
        run.end_ts = datetime.now().isoformat()
        run.status = "COMPLETED"

        db.add_or_update_testrun(run=run)
        await ws_manager.send_all(
            {"type": "RUN_FINISHED", "runId": run_id, "status": "COMPLETED"}
        )
        print(f"🏁 Background execution finished for run {run_id}")

    except Exception as e:
        print(f"Background execution failed for run {run_id}: {e}")
        run.status = "FAILED"
        run.end_ts = datetime.now().isoformat()
        db.add_or_update_testrun(run=run)
        try:
            await ws_manager.send_all(
                {
                    "type": "RUN_FINISHED",
                    "runId": run_id,
                    "status": "FAILED",
                    "error": str(e),
                }
            )
        except Exception as ws_error:
            print(f"Failed to push RUN_FINISHED for failed run {run_id}: {ws_error}")
    finally:
        if client is not None:
            try:
                client.close()
            except Exception as close_error:
                print(f"Client close failed (IM already dead): {close_error}")
