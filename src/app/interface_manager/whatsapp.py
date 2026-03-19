# from selenium import webdriver
# from logger import get_logger
# from utils import (
#     DriverManager,
#     load_config,
#     login_app,
#     logout_app,
#     search_entity,
#     send_message_whatsapp,
# )

# logger = get_logger("whatsapp_driver")

# # Single DriverManager instance for WhatsApp
# driver_manager = DriverManager()


# def get_ui_response_whatsapp():
#     return {"ui": "Whatsapp Web Chat Interface", "features": ["smart-compose", "modular-layout"]}


# def login_whatsapp() -> webdriver.Chrome | None:
#     """Login to WhatsApp Web using DriverManager and generic login_app."""
#     cfg = load_config()
#     url = cfg.get("whatsapp_url")
#     try:
#         driver = driver_manager.get_driver("WhatsApp Web", url)
#         login_app(driver, "whatsapp_web")
#         return driver
#     except Exception as e:
#         logger.error(f"WhatsApp Web login failed: {e}")
#         return None


# def logout_whatsapp(driver: webdriver.Chrome) -> bool:
#     """Logout from WhatsApp Web using generic logout_app."""
#     return logout_app(driver, "whatsapp_web")


# def search_llm(driver: webdriver.Chrome) -> bool:
#     """Search for the configured contact (LLM) in WhatsApp Web using generic search_entity."""
#     return search_entity(driver, "whatsapp_web")


# def send_whatsapp_message(
#     driver: webdriver.Chrome,
#     prompt: str | None = None,
#     audio_path: str | None = None,
#     is_audio: bool = False
# ):
#     """Send text or audio message to WhatsApp Web."""

#     if is_audio:
#         return send_message_whatsapp(driver, audio_path=audio_path, is_audio=True)
#     else:
#         return send_message_whatsapp(driver, prompt)


# def send_prompt_whatsapp(
#     chat_id: int,
#     prompt_list: list[str] | None = None,
#     audio_path: str | None = None,
#     return_voice: bool = False
# ) -> list[dict]:

#     results = []
#     driver = login_whatsapp()

#     if not driver:
#         return [{"chat_id": chat_id, "response": "No response received"}]

#     try:
#         if not search_llm(driver):
#             return [{"chat_id": chat_id, "response": "No response received"}]

#         if audio_path:
#             response = send_message_whatsapp(
#                 driver,
#                 audio_path=audio_path,
#                 is_audio=True
#             )

#             results.append({
#                 "chat_id": chat_id,
#                 "response": response
#             })

#             return results

#         for prompt in prompt_list or []:
#             response = send_message_whatsapp(driver, prompt=prompt)

#             results.append({
#                 "chat_id": chat_id,
#                 "prompt": prompt,
#                 "response": response
#             })

#     finally:
#         pass

#     return results


# def close_whatsapp(driver: webdriver.Chrome | None = None):
#     """Close WhatsApp Web session gracefully."""
#     try:
#         if driver:
#             driver.quit()
#             logger.info("Driver quit successfully.")
#         driver_manager.quit()
#         logger.info("WhatsApp Web session closed successfully.")
#     except Exception as e:
#         logger.error(f"Error closing WhatsApp Web session: {e}")


from selenium import webdriver
from logger import get_logger
from utils import (
    DriverManager,
    load_config,
    login_app,
    logout_app,
    search_entity,
    send_message_whatsapp,
)

logger = get_logger("whatsapp_driver")

# Single driver manager instance
driver_manager = DriverManager()


def get_ui_response_whatsapp():
    return {
        "ui": "Whatsapp Web Chat Interface",
        "features": ["smart-compose", "modular-layout"]
    }


def login_whatsapp() -> webdriver.Chrome | None:
    """
    Login to WhatsApp Web.
    """

    cfg = load_config()
    url = cfg.get("whatsapp_url")

    try:
        driver = driver_manager.get_driver("WhatsApp Web", url)

        login_app(driver, "whatsapp_web")

        return driver

    except Exception as e:
        logger.error(f"WhatsApp Web login failed: {e}")
        return None


def logout_whatsapp(driver: webdriver.Chrome) -> bool:
    """
    Logout from WhatsApp Web.
    """

    try:
        return logout_app(driver, "whatsapp_web")

    except Exception as e:
        logger.error(f"WhatsApp logout failed: {e}")
        return False


def search_llm(driver: webdriver.Chrome) -> bool:
    """
    Search the configured contact (LLM) in WhatsApp Web.
    """

    try:
        return search_entity(driver, "whatsapp_web")

    except Exception as e:
        logger.error(f"Search contact failed: {e}")
        return False


def send_whatsapp_message(
    driver: webdriver.Chrome,
    prompt: str | None = None,
    audio_path: str | None = None,
    file_path: str | None = None
):
    """
    Send a WhatsApp message (text, recorded audio, or file attachment).
    """

    try:

        # -------- VOICE NOTE --------
        if audio_path:

            logger.info(f"Sending voice message → {audio_path}")

            return send_message_whatsapp(
                driver,
                audio_path=audio_path,
                is_audio=True
            )

        # -------- FILE ATTACHMENT --------
        if file_path:

            logger.info(f"Sending file attachment → {file_path}")

            return send_message_whatsapp(
                driver,
                file_path=file_path,
                is_file=True
            )

        # -------- TEXT MESSAGE --------
        if prompt:

            logger.info(f"Sending text message → {prompt}")

            return send_message_whatsapp(
                driver,
                prompt=prompt
            )

        # -------- INVALID INPUT --------
        return {
            "type": "error",
            "content": "No message content provided"
        }

    except Exception as e:

        logger.error(f"Message send failed: {e}")

        return {
            "type": "error",
            "content": "Message sending failed"
        }


def send_prompt_whatsapp(
    chat_id: int,
    prompt_list: list[str] | None = None,
    audio_path: str | None = None,
    return_voice: bool = False
) -> list[dict]:

    results = []

    if audio_path and prompt_list:
        raise ValueError("Provide either audio_path or prompt_list, not both.")

    driver = login_whatsapp()

    if not driver:
        return [{"chat_id": chat_id, "response": "No response received"}]

    try:

        if not search_llm(driver):
            return [{"chat_id": chat_id, "response": "No response received"}]

        # AUDIO MESSAGE
        if audio_path:

            response = send_whatsapp_message(
                driver,
                audio_path=audio_path
            )

            results.append({
                "chat_id": chat_id,
                "prompt": None,
                "response": response
            })

            return results

        # TEXT PROMPTS
        for prompt in prompt_list or []:

            response = send_whatsapp_message(
                driver,
                prompt=prompt
            )

            results.append({
                "chat_id": chat_id,
                "prompt": prompt,
                "response": response
            })

    finally:
        pass

    return results


def close_whatsapp(driver: webdriver.Chrome | None = None):
    """
    Close WhatsApp Web session gracefully.
    """

    try:

        if driver:
            driver.quit()

        driver_manager.quit()

        logger.info("WhatsApp Web session closed successfully.")

    except Exception as e:
        logger.error(f"Error closing WhatsApp Web session: {e}")