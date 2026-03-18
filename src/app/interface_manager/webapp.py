import time
from typing import List, Optional

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from logger import get_logger
from utils import (
    DriverManager,
    load_config,
    load_xpaths,
    is_logged_in,
    login_app,
    logout_app,
    send_message_webapp,
)

logger = get_logger("webapp_driver")

driver_manager = DriverManager(profile_name="test_profile")


# --------------------------------------------------------
# UI Info
# --------------------------------------------------------

def get_ui_response_webapp():
    return {
        "ui": "Web Application Chat Interface",
        "features": ["smart-compose", "modular-layout"],
    }


# --------------------------------------------------------
# Login
# --------------------------------------------------------

def login_webapp(app_name: str):

    cfg = load_config()
    url = cfg.get("application_url", "UNKNOWN")

    driver = driver_manager.get_driver(app_name, url)

    return login_app(driver, app_name)


# --------------------------------------------------------
# Logout
# --------------------------------------------------------

def logout_webapp(driver, app_name: str):

    return logout_app(driver, app_name)


# --------------------------------------------------------
# Model search (OpenWebUI only)
# --------------------------------------------------------

def search_llm(driver):

    cfg = load_config()

    app_name = cfg.get("application_name", "UNKNOWN")
    agent_name = cfg.get("agent_name", "UNKNOWN")

    xpaths = load_xpaths()["applications"]["openweb-ui"]["ChatPage"]

    try:

        if not login_webapp(app_name):
            return False

        logger.info("Launched OpenWeb-UI")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, xpaths["model_selection_element"])
            )
        ).send_keys(Keys.RETURN)

        time.sleep(2)

        logger.info("Searching model '%s'", agent_name)

        search_box = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.ID, xpaths["model_name_entry_element"])
            )
        )

        search_box.send_keys(agent_name)
        search_box.send_keys(Keys.RETURN)

        logger.info("Model '%s' selected", agent_name)

        return True

    except Exception as e:

        logger.error("Model search failed: %s", e)

        return False


# --------------------------------------------------------
# Prompt sending
# --------------------------------------------------------

def send_prompt(
    app_name: str,
    chat_id: int,
    prompt_list: Optional[List[str]] = None,
    audio_path: Optional[str] = None,
    return_voice: bool = False,
) -> List[dict]:

    results: List[dict] = []

    cfg = load_config()
    xpaths = load_xpaths()

    url = cfg.get("application_url", "UNKNOWN")

    app_name = app_name.lower()

    driver = driver_manager.get_driver(app_name, url)

    prompt_list = prompt_list or []

    # ----------------------------------------------------
    # Login check
    # ----------------------------------------------------

    logout_cfg = (
        xpaths
        .get("applications", {})
        .get(app_name, {})
        .get("LogoutPage", {})
    )

    send_element = logout_cfg.get("send_element")

    login_ok = True

    if send_element:

        login_ok = is_logged_in(driver, send_element=send_element)

        if not login_ok:

            logger.info("User not logged in. Attempting login")

            login_ok = login_webapp(app_name)

    if not login_ok:

        logger.error("Login failed for %s", app_name)

        return results

    # ----------------------------------------------------
    # TEXT MODE
    # ----------------------------------------------------

    if not audio_path:

        for prompt in prompt_list:

            clean_prompt = " ".join(prompt.split())

            logger.info("Sending prompt to %s: %s", app_name, clean_prompt)

            response = send_message_webapp(
                driver=driver,
                app_name=app_name,
                prompt=clean_prompt,
                audio_path=None,
            )

            if not isinstance(response, dict):

                raise RuntimeError(
                    f"Invalid response returned from handler: {response}"
                )

            if response.get("type") == "audio":

                logger.info("Audio saved at %s", response.get("file"))

            results.append(
                {
                    "chat_id": chat_id,
                    "prompt": clean_prompt,
                    "response": response,
                }
            )

        return results

    # ----------------------------------------------------
    # AUDIO MODE
    # ----------------------------------------------------

    logger.info("Sending audio prompt to %s: %s", app_name, audio_path)

    response = send_message_webapp(
        driver=driver,
        app_name=app_name,
        prompt=None,
        audio_path=audio_path,
    )

    if not isinstance(response, dict):

        raise RuntimeError(
            f"Invalid response returned from handler: {response}"
        )

    if response.get("type") == "audio":

        logger.info("Audio saved at %s", response.get("file"))

    results.append(
        {
            "chat_id": chat_id,
            "prompt": "[Audio Prompt]",
            "response": response,
        }
    )

    return results


# --------------------------------------------------------
# Close session
# --------------------------------------------------------

def close_webapp(app_name: str):

    try:

        logger.info("Closing WebApp session for %s", app_name)

        driver_manager.quit()

        logger.info("Session closed for %s", app_name)

    except Exception as e:

        logger.warning("Driver quit issue: %s", e)

    return True