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

# Single DriverManager instance for WhatsApp
driver_manager = DriverManager()


def get_ui_response_whatsapp():
    return {"ui": "Whatsapp Web Chat Interface", "features": ["smart-compose", "modular-layout"]}


def login_whatsapp() -> webdriver.Chrome | None:
    """Login to WhatsApp Web using DriverManager and generic login_app."""
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
    """Logout from WhatsApp Web using generic logout_app."""
    return logout_app(driver, "whatsapp_web")


def search_llm(driver: webdriver.Chrome) -> bool:
    """Search for the configured contact (LLM) in WhatsApp Web using generic search_entity."""
    return search_entity(driver, "whatsapp_web")


def send_whatsapp_message(
    driver: webdriver.Chrome,
    prompt: str | None = None,
    audio_path: str | None = None,
    is_audio: bool = False
):
    """Send text or audio message to WhatsApp Web."""

    if is_audio:
        return send_message_whatsapp(driver, audio_path=audio_path, is_audio=True)
    else:
        return send_message_whatsapp(driver, prompt)


def send_prompt_whatsapp(
    chat_id: int,
    prompt_list: list[str] | None = None,
    audio_path: str | None = None,
    return_voice: bool = False
) -> list[dict]:

    results = []
    driver = login_whatsapp()

    if not driver:
        return [{"chat_id": chat_id, "response": "No response received"}]

    try:
        if not search_llm(driver):
            return [{"chat_id": chat_id, "response": "No response received"}]

        if audio_path:
            response = send_message_whatsapp(
                driver,
                audio_path=audio_path,
                is_audio=True
            )

            results.append({
                "chat_id": chat_id,
                "response": response
            })

            return results

        for prompt in prompt_list or []:
            response = send_message_whatsapp(driver, prompt=prompt)

            results.append({
                "chat_id": chat_id,
                "prompt": prompt,
                "response": response
            })

    finally:
        pass

    return results


def close_whatsapp(driver: webdriver.Chrome | None = None):
    """Close WhatsApp Web session gracefully."""
    try:
        if driver:
            driver.quit()
            logger.info("Driver quit successfully.")
        driver_manager.quit()
        logger.info("WhatsApp Web session closed successfully.")
    except Exception as e:
        logger.error(f"Error closing WhatsApp Web session: {e}")
