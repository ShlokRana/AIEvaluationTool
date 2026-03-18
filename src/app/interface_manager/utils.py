import os
import time
import json
import socket
import psutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
    InvalidElementStateException
)
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import traceback
from pathlib import Path
import sounddevice as sd
import soundfile as sf
import base64
import subprocess

APP_HANDLERS = {
    "cpgrams": "handle_cpgrams",
    "farmerchat": "handle_farmerchat",
}

from logger import get_logger

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def wait_until_complete(filepath):
    last_size = -1

    while True:
        current_size = os.path.getsize(filepath)

        if current_size == last_size:
            break

        last_size = current_size
        time.sleep(1)

logger = get_logger("interface_manager")

# Setting up a consistent download directory for all apps using this driver instance.
download_dir = Path.cwd().parents[2] / "agent_response_cache" 
os.makedirs(download_dir, exist_ok=True)
DEFAULT_DOWNLOAD_DIR = download_dir

# --------------------------------------------------------------------
# Driver Management
# --------------------------------------------------------------------
class DriverManager:
    """
    Manage a Selenium Chrome WebDriver instance with profile isolation.
    Ensures reuse if alive, otherwise restarts with clean profile.
    """

    def __init__(self, profile_name: str = "test_profile"):
        self.profile_folder_path = os.path.join(os.path.expanduser("~"), profile_name)
        self.driver: webdriver.Chrome | None = None

    def get_driver(self, app_name: str, url: str) -> webdriver.Chrome:
        """
        Returns a cached driver if alive, otherwise creates a new one.
        """
        if self.driver and self._is_alive():
            logger.info(f"Reusing existing Chrome session for {app_name}")
            return self.driver

        self.close_chrome_with_profile()

        logger.info(f"Launching {app_name} at {url}")

        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--start-maximized")
        prefs = {
            "download.default_directory": str(download_dir),
            "profile.default_content_setting_values.media_stream_mic": 1,
            "download.directory_upgrade": True
        }
        opts.add_experimental_option("prefs", prefs)
        mode = load_json('config.json').get('headless', 'False')
        # to turn off headless mode - remove the below line or comment it out.
        if mode == "True":
            opts.add_argument("--headless")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        cfg = load_config()
        selenium_mode = str(cfg.get("selenium_mode", "local")).lower()
        remote_url = cfg.get("selenium_remote_url", "http://selenium-browser:4444/wd/hub")

        try:
            if selenium_mode == "remote":
                logger.info(f"Using Remote WebDriver at {remote_url}")
                self.driver = webdriver.Remote(
                    command_executor=remote_url,
                    options=opts
                )
            else:
                opts.add_argument(f"user-data-dir={self.profile_folder_path}")
                logger.info("Using local Chrome WebDriver")
                self.driver = webdriver.Chrome(options=opts)

            self.driver.get(url)
            logger.info(f"Driver ready for {app_name}")
            return self.driver
        except WebDriverException as e:
            logger.error(f"Failed to start Chrome for {app_name}: {e}")
            self.driver = None
            raise

        # try:
        #     # service = Service(ChromeDriverManager().install())
        #     # self.driver = webdriver.Chrome(service=service, options=opts)
        #     # @bugfix: Use the below line to load driver faster -- Balayogi 12.01.2026
        #     self.driver = webdriver.Chrome(options=opts)
        #     self.driver.get(url)
        #     logger.info(f"Driver ready for {app_name}")
        #     return self.driver
        # except WebDriverException as e:
        #     logger.error(f"Failed to start Chrome for {app_name}: {e}")
        #     self.driver = None
        #     raise

    def _is_alive(self) -> bool:
        """Check if the cached driver is still valid."""
        try:
            _ = self.driver.title
            return True
        except Exception:
            return False
 
    def close_chrome_with_profile(self) -> bool:
        """Kill any Chrome process using this profile."""
        closed_any = False
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                if "chrome" in (proc.info["name"] or "").lower():
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if f"user-data-dir={self.profile_folder_path}" in cmdline:
                        proc.kill()
                        closed_any = True
                        logger.info(f"Killed Chrome with profile {self.profile_folder_path}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return closed_any

    def quit(self):
        """Cleanly quit the driver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver quit successfully")
            except Exception as e:
                logger.warning(f"Error while quitting driver: {e}")
            finally:
                self.driver = None


# --------------------------------------------------------------------
# Config Loaders
# --------------------------------------------------------------------
def load_config() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as file:
        return json.load(file)


def load_xpaths() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "xpaths.json"), "r") as file:
        return json.load(file)


def load_creds() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "credentials.json"), "r") as file:
        return json.load(file)


# --------------------------------------------------------------------
# Connectivity Helpers
# --------------------------------------------------------------------

def is_connected(test_url: str = "https://www.google.com", timeout: int = 5) -> bool:
    """Check internet connectivity using HTTPS GET (more reliable than raw sockets)."""
    try:
        r = requests.get(test_url, timeout=timeout)
        return r.status_code == 200
    except requests.RequestException as ex:
        logger.error(f"HTTP connectivity check failed: {ex}")
        return False


def check_selenium_internet(driver, test_url: str = "https://www.google.com") -> bool:
    """Validate connectivity from inside the Selenium browser itself."""
    try:
        driver.get(test_url)
        title = driver.title or ""
        return "Google" in title or "google" in title.lower()
    except Exception as e:
        logger.error(f"Selenium browser connectivity check failed: {e}")
        return False


def check_and_recover_connection(driver=None) -> bool:
    """
    Unified connectivity check:
    1. Try Python requests.
    2. If Selenium driver provided, try inside the browser.
    3. Retry with exponential backoff.
    """
    if is_connected():
        logger.info("Device is connected to the internet (requests).")
        return True

    if driver and check_selenium_internet(driver):
        logger.info("Device has internet via Selenium browser.")
        return True

    delay, max_attempts, max_delay = 3, 5, 60
    for attempt in range(1, max_attempts + 1):
        logger.warning(f"Connectivity lost. Attempt {attempt}/{max_attempts} - retrying in {delay}s...")
        time.sleep(delay)

        if is_connected():
            logger.info("Recovered connectivity (requests).")
            return True
        if driver and check_selenium_internet(driver):
            logger.info("Recovered connectivity via Selenium browser.")
            return True

        delay = min(delay * 2, max_delay)

    logger.error("Device remains disconnected after all retry attempts.")
    return False


def retry_on_internet(max_attempts: int = 5, initial_delay: int = 3, max_delay: int = 60) -> bool:
    """Retry internet connectivity check with backoff."""
    delay = initial_delay
    logger.info("Checking internet connectivity...")
    for attempt in range(1, max_attempts + 1):
        if is_connected():
            logger.info("Device is connected to the internet.")
            return True
        logger.warning(f"Attempt {attempt}/{max_attempts}. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)
    logger.error("Device remains disconnected after all retry attempts.")
    return False


# --------------------------------------------------------------------
# UI Helpers
# --------------------------------------------------------------------
def is_logged_in(driver: webdriver.Chrome, send_element: str) -> bool:
    """Check if a user is logged in by verifying presence of a profile element."""
    try:
        print("received xpath: ", send_element)
        # print(driver.page_source)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, send_element))
        )
        return True
    except Exception as e:
        return False


def safe_click(driver: webdriver.Chrome, selector: str, retries: int = 3, wait_time: int = 10) -> bool:
    """Safely click an element with retries and wait conditions."""
    by_type = By.XPATH if selector.strip().startswith(("/", "(")) else By.CSS_SELECTOR

    for attempt in range(retries):
        try:
            logger.debug(f"Attempt {attempt + 1}: Locating element ({by_type}) {selector}")
            element = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable((by_type, selector))
            )
            element.click()
            logger.debug(f"Clicked element ({by_type}) {selector}")
            return True
        except (StaleElementReferenceException, TimeoutException) as e:
            logger.warning(f"Retrying due to {type(e).__name__} for selector {selector}")
            time.sleep(1)
        except WebDriverException as e:
            logger.error(f"WebDriver error during click: {e}")
            break
    return False


# --------------------------------------------------------------------
# Server Helpers
# --------------------------------------------------------------------
def is_server_running(url: str | None = None, timeout: int | None = None) -> bool:
    """Check if a server is reachable and responding."""
    config = load_config()
    url = url or config.get("server_url")
    timeout = timeout or config.get("server_timeout")

    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Server unreachable at {url}: {e}")
        return False


def wait_for_server(
    url: str | None = None,
    retries: int | None = None,
    delay: int | None = None,
    max_delay: int | None = None,
    on_retry_callback=None,
) -> bool:
    """Retry until server responds or attempts exhausted."""
    config = load_config()

    url = url or config.get("server_url")
    retries = retries if retries is not None else config.get("retries", 5)
    delay = delay if delay is not None else config.get("retry_delay", 3)
    max_delay = max_delay if max_delay is not None else config.get("max_retry_delay", 60)

    current_delay = delay
    for attempt in range(1, retries + 1):
        if is_server_running(url=url, timeout=config.get("default_timeout", 10)):
            logger.info(f"Server at {url} is up.")
            return True

        logger.warning(f"Attempt {attempt}/{retries}: Server not responding. Retrying in {current_delay}s...")
        if on_retry_callback:
            on_retry_callback(attempt, retries, current_delay)

        time.sleep(current_delay)
        current_delay = min(current_delay * 2, max_delay)

    logger.error(f"Server at {url} is not reachable after {retries} attempts.")
    return False

# --------------------------------------------------------------------
# Generic App Helpers (Login / Logout / Search / Send Message)
# --------------------------------------------------------------------
def login_app(driver: webdriver.Chrome, app_name: str) -> bool:
    """
    Generic login flow for apps that define a LoginPage in xpaths.json.
    Uses credentials.json for username/password.
    """
    try:
        app_cfg = load_xpaths()["applications"][app_name.lower()]
        login_cfg = app_cfg.get("LoginPage")
        logout_cfg = app_cfg.get("LogoutPage")
        cred_cfg = load_creds()["applications"].get(app_name.lower(), {})

        if not login_cfg:
            logger.info(f"{app_name} has no LoginPage config → skipping login")
            return True

        # Already logged in?
        if logout_cfg and is_logged_in(driver, logout_cfg["profile_pic_element"]):
            logger.info(f"Already logged in to {app_name.upper()}")
            return True

        # Perform login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, login_cfg["email_input_element"]))
        ).send_keys(cred_cfg["username"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, login_cfg["password_input_element"]))
        ).send_keys(cred_cfg["password"])

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, login_cfg["login_button_element"]))
        ).click()

        logger.info(f"Login successful for {app_name.upper()}")
        return True

    except Exception as e:
        logger.error(f"{app_name.upper()} login failed: {e}")
        print(e)
        return False


def logout_app(driver: webdriver.Chrome, app_name: str) -> bool:
    """
    Generic logout flow for apps that define a LogoutPage in xpaths.json.
    """
    try:
        app_cfg = load_xpaths()["applications"][app_name.lower()]
        logout_cfg = app_cfg.get("LogoutPage") or app_cfg.get("ChatPage")

        if not logout_cfg:
            logger.info(f"{app_name} has no LogoutPage config → skipping logout")
            return True

        safe_click(driver, logout_cfg["profile_element"])
        safe_click(driver, logout_cfg["logout_button_element"])

        logger.info(f"Logout successful for {app_name.upper()}")
        return True
    except Exception as e:
        logger.error(f"{app_name.upper()} logout failed: {e}")
        return False


def search_entity(driver: webdriver.Chrome, app_name: str) -> bool:
    """
    Generic search (contact, model, etc.) based on ChatPage config.
    Uses agent_name from config.json.
    """
    cfg = load_config()
    app_cfg = load_xpaths()["applications"][app_name.lower()]
    chat_cfg = app_cfg["ChatPage"]
    entity_name = cfg.get("agent_name")

    try:
        search_input_xpath = chat_cfg.get("contact_search_element") or chat_cfg.get("model_name_entry_element")
        if not search_input_xpath:
            logger.info(f"{app_name} has no search element → skipping search")
            return True

        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, search_input_xpath))
        )
        search_box.clear()
        search_box.send_keys(entity_name)
        search_box.send_keys(Keys.RETURN)

        logger.info(f"{app_name}: '{entity_name}' search successful")
        return True
    except Exception as e:
        logger.error(f"{app_name}: search failed for '{entity_name}': {e}")
        return False

def split_message(message, max_length=1000):
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

def send_text_whatsapp(driver, prompt, chat_cfg):
    wait = WebDriverWait(driver, 30)

    message_box = wait.until(
        EC.element_to_be_clickable((By.XPATH, chat_cfg["prompt_input_box_element"]))
    )

    driver.execute_script("arguments[0].focus();", message_box)

    driver.execute_script("""
    arguments[0].innerHTML = "";
    """, message_box)

    chunks = split_message(prompt)

    for chunk in chunks:
        message_box.send_keys(chunk)
        message_box.send_keys(Keys.SHIFT + Keys.ENTER)
        time.sleep(0.2)

    send_button = driver.find_element(By.XPATH, chat_cfg["send_button_element"])
    send_button.click()


def wait_for_whatsapp_response(driver, chat_cfg, timeout=30, quiet_time=2):
    import time
    from selenium.webdriver.common.by import By

    msg_xpath = f"{chat_cfg['message_in_element']} | {chat_cfg['message_out_element']}"
    start = time.time()
    last_change = time.time()
    responses = []

    # Snapshot the last message's HTML before the reply
    msgs = driver.find_elements(By.XPATH, msg_xpath)
    last_html = msgs[-1].get_attribute("outerHTML") if msgs else None

    while time.time() - start < timeout:
        msgs = driver.find_elements(By.XPATH, msg_xpath)
        if not msgs:
            time.sleep(0.3)
            continue

        last_msg = msgs[-1]
        html = last_msg.get_attribute("outerHTML")

        # Only proceed if the last message changed
        if html != last_html:
            last_html = html

            cls = last_msg.get_attribute("class") or ""
            if "message-in" in cls:  # only process incoming messages
                nodes = last_msg.find_elements(By.XPATH, chat_cfg["agent_response_element"])
                for n in nodes:
                    txt = n.text.strip()
                    logger.info(
                    f"(Waited:{int(time.time() - start)}) "
                    f"Received: {txt}"
                    )
                    if txt:
                        responses.append(txt)
                        last_change = time.time()

        if responses and time.time() - last_change > quiet_time:
            break

        time.sleep(0.3)

    return responses

def send_audio_whatsapp(driver, audio_path, chat_cfg):

    wait = WebDriverWait(driver, 30)

    audio_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, chat_cfg["audio_record_button_element"])
        )
    )

    audio_button.click()

    data, sr = sf.read(audio_path, dtype="float32")

    sd.play(data, sr)
    sd.wait()

    time.sleep(1)

    send_button = driver.find_element(
        By.XPATH,
        chat_cfg["send_button_element"]
    )

    send_button.click()

def send_file_whatsapp(driver, file_path, chat_cfg):

    wait = WebDriverWait(driver, 30)

    attach_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, chat_cfg["attachment_button_element"])
        )
    )

    attach_btn.click()

    file_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, chat_cfg["attachment_input_element"])
        )
    )

    file_input.send_keys(os.path.abspath(file_path))

    send_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, chat_cfg["send_button_element"])
        )
    )

    send_button.click()

    logger.info(f"File attachment sent → {file_path}")


def wait_for_whatsapp_audio_or_text_response(
    driver,
    chat_cfg,
    download_dir,
    timeout=60,
    audio_grace=20
):

    os.makedirs(download_dir, exist_ok=True)

    message_in = chat_cfg["message_in_element"]
    message_out = chat_cfg["message_out_element"]

    msg_xpath = f"{message_in} | {message_out}"

    start_time = time.time()

    text_candidate = None
    text_detect_time = None

    messages = driver.find_elements(By.XPATH, msg_xpath)
    last_html = messages[-1].get_attribute("outerHTML") if messages else None

    while time.time() - start_time < timeout:

        messages = driver.find_elements(By.XPATH, msg_xpath)

        if messages:

            last_msg = messages[-1]
            html = last_msg.get_attribute("outerHTML")

            if html != last_html:

                last_html = html
                cls = last_msg.get_attribute("class") or ""

                if "message-in" not in cls:
                    continue

                waited = int(time.time() - start_time)

                # -------------------------
                # AUDIO DETECTION
                # -------------------------
                voice_nodes = last_msg.find_elements(
                    By.XPATH,
                    chat_cfg["audio_message_element"]
                )

                if voice_nodes:

                    logger.info(f"(Waited:{waited}s) Voice message detected")

                    ActionChains(driver).move_to_element(last_msg).perform()

                    chevron = last_msg.find_element(
                        By.XPATH,
                        chat_cfg["download_menu_element"]
                    )

                    chevron.click()

                    before = set(os.listdir(download_dir))

                    download_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, chat_cfg["download_button_element"])
                        )
                    )

                    download_btn.click()

                    start_download = time.time()

                    while time.time() - start_download < 60:

                        after = set(os.listdir(download_dir))
                        new_files = after - before

                        if new_files:

                            file = new_files.pop()

                            if not file.endswith(".crdownload"):

                                path = os.path.join(download_dir, file)

                                logger.info( f"(Waited:{waited}s) Audio downloaded → {path}")

                                wav_path = os.path.splitext(path)[0] + ".wav"

                                subprocess.run(
                                    ["ffmpeg", "-y", "-i", path, wav_path],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                )

                                logger.info(f"Converted to WAV → {wav_path}")

                                 # Delete original file
                                if os.path.exists(wav_path):
                                    os.remove(path)
                                    logger.info(f"Deleted original file → {path}")

                                return {
                                    "type": "audio",
                                    "file": wav_path
                                }

                        time.sleep(1)

                # -------------------------
                # TEXT DETECTION
                # -------------------------
                text_nodes = last_msg.find_elements(
                    By.XPATH,
                    chat_cfg["agent_response_element"]
                )

                text_values = []

                for node in text_nodes:
                    txt = node.text.strip()
                    if txt:
                        text_values.append(txt)

                if text_values and text_candidate is None:

                    text_candidate = " ".join(text_values)
                    text_detect_time = time.time()

                    logger.info(
                        f"(Waited:{waited}s) Text detected "
                        f"(waiting for possible audio) → {text_candidate}"
                    )

        # -------------------------
        # GRACE PERIOD CHECK
        # -------------------------
        if text_candidate and text_detect_time:

            if time.time() - text_detect_time > audio_grace:

                waited = int(time.time() - start_time)

                logger.info(
                    f"(Waited:{waited}s) Returning text response → {text_candidate}"
                )

                return {
                    "type": "text",
                    "content": text_candidate
                }

        time.sleep(0.3)

    if text_candidate:
        logger.info("Timeout reached — returning detected text")
        return {
            "type": "text",
            "content": text_candidate
        }

    return {
        "type": "error",
        "content": "No audio or text response detected"
    }


def send_message_whatsapp(
    driver: webdriver.Chrome,
    prompt: str = None,
    audio_path: str = None,
    file_path: str = None,
    is_audio: bool = False,
    is_file: bool = False,
    download_dir: str = None
):

    max_retries = 3
    attempt = 0

    config = load_config()
    app_name = config.get("application_type")

    app_cfg = load_xpaths()["applications"][app_name.lower()]
    chat_cfg = app_cfg["ChatPage"]

    while attempt < max_retries:

        try:

            # ---------- Connectivity check ----------
            if not check_and_recover_connection():
                return {
                    "type": "error",
                    "content": "No internet connection"
                }

            # ---------- TEXT MESSAGE ----------
            if not is_audio and not is_file:

                logger.info("Sending text message")

                send_text_whatsapp(driver, prompt, chat_cfg)

                responses = wait_for_whatsapp_response(
                    driver,
                    chat_cfg
                )

                if responses:
                    return {
                        "type": "text",
                        "content": " ".join(responses)
                    }

                return {
                    "type": "error",
                    "content": "No response received"
                }

            # ---------- RECORDED VOICE NOTE ----------
            elif is_audio and not is_file:

                logger.info(f"Sending voice note → {audio_path}")

                send_audio_whatsapp(
                    driver,
                    audio_path,
                    chat_cfg
                )

                response = wait_for_whatsapp_audio_or_text_response(
                    driver,
                    chat_cfg,
                    download_dir=download_dir
                )

                return response

            # ---------- FILE ATTACHMENT ----------
            elif is_file:

                logger.info(f"Sending file attachment → {file_path}")

                send_file_whatsapp(
                    driver,
                    file_path,
                    chat_cfg
                )

                response = wait_for_whatsapp_audio_or_text_response(
                    driver,
                    chat_cfg,
                    download_dir=download_dir
                )

                return response

            else:

                return {
                    "type": "error",
                    "content": "Invalid message configuration"
                }

        except Exception as e:

            attempt += 1

            import traceback
            logger.error(f"Attempt {attempt} failed: {repr(e)}")
            logger.error(traceback.format_exc())

            if attempt < max_retries:
                time.sleep(1)
            else:
                return {
                    "type": "error",
                    "content": "Max retries reached"
                }

# Sending Message to Web applications
def send_message_webapp(
    driver,
    app_name,
    prompt=None,
    audio_path=None,
    download_dir=None,
    max_retries=3,
):

    app = app_name.lower()
    handler_name = APP_HANDLERS.get(app)

    if not handler_name:
        raise ValueError(f"Unsupported application: {app}")
    
    if download_dir is None:
        download_dir = DEFAULT_DOWNLOAD_DIR

    handler = globals()[handler_name]

    for attempt in range(1, max_retries + 1):

        try:
            return handler(driver, prompt, audio_path, download_dir)

        except Exception as e:

            logger.warning(f"[{app}] attempt {attempt} failed: {e}")

            if attempt == max_retries:
                raise

            time.sleep(1.5)


# ------------------------------------------------------------
# CPGRAMS HANDLER
# ------------------------------------------------------------

def handle_cpgrams(driver, prompt, audio_path, download_dir):

    if audio_path:
        raise NotImplementedError("Audio mode not supported for CPGRAMS")

    cfg = load_xpaths()["applications"]["cpgrams"]["ChatPage"]

    input_xpath = cfg["prompt_input_box_element"]
    response_xpath = cfg["agent_response_element"]

    input_box = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, input_xpath))
    )

    input_box.clear()
    input_box.send_keys(prompt)
    input_box.send_keys(Keys.RETURN)

    text = wait_for_text_response(driver, response_xpath)

    return {
        "type": "text",
        "content": text
    }


# ------------------------------------------------------------
# FARMERCHAT HANDLER
# ------------------------------------------------------------

def handle_farmerchat(driver, prompt, audio_path, download_dir):

    cfg = load_xpaths()["applications"]["farmerchat"]["ChatPage"]

    iframe_selector = cfg["shadow_root_element"]
    textarea_selector = cfg["prompt_input_box_element"]
    response_selector = cfg["agent_response_element"]
    audio_selector = cfg["audio_message_element"]
    mic_selector = cfg["mic_button_element"]
    send_selector = cfg["send_button_element"]

    shadow_host = get_shadow_host(driver, iframe_selector)

    if audio_path:
        return farmerchat_audio_flow(
            driver,
            shadow_host,
            audio_path,
            mic_selector,
            send_selector,
            audio_selector,
            response_selector,
            download_dir
        )

    textarea = driver.execute_script("""
        const host = arguments[0];
        return host.shadowRoot.querySelector(arguments[1]);
    """, shadow_host, textarea_selector)
    
    # To clear text area
    textarea.clear()

    if not textarea:
        raise RuntimeError("Prompt input box not found")
    
    initial_count = driver.execute_script("""
        const host = arguments[0];
        return host.shadowRoot.querySelectorAll(arguments[1]).length;
    """, shadow_host, response_selector)

    textarea.send_keys(prompt)
    textarea.send_keys(Keys.RETURN)

    text = wait_for_new_shadow_text(driver, shadow_host, response_selector, initial_count)

    return {
        "type": "text",
        "content": text
    }


def wait_for_shadow_audio_and_text(driver, shadow_host, audio_selector, text_selector, timeout=60):

    start = time.time()

    last_text = None
    audio_element = None

    while time.time() - start < timeout:

        result = driver.execute_script("""
            const host = arguments[0];
            const audioSel = arguments[1];
            const textSel = arguments[2];

            const audioNodes = host.shadowRoot.querySelectorAll(audioSel);
            const textNodes = host.shadowRoot.querySelectorAll(textSel);

            const lastAudio = audioNodes.length ? audioNodes[audioNodes.length-1] : null;
            const lastText = textNodes.length ? textNodes[textNodes.length-1].textContent : "";

            return {
                hasAudio: lastAudio && lastAudio.src ? true : false,
                text: lastText
            };
        """, shadow_host, audio_selector, text_selector)

        if result["text"]:
            txt = result["text"].strip()

            if txt != last_text:
                last_text = txt
                last_change = time.time()

        if result["hasAudio"] and last_text and (time.time() - last_change) > 2:
            audio_element = driver.execute_script("""
                const host = arguments[0];
                const nodes = host.shadowRoot.querySelectorAll(arguments[1]);
                return nodes[nodes.length - 1];
            """, shadow_host, audio_selector)

            return audio_element, last_text

        time.sleep(0.5)

    raise TimeoutException("Audio/text response timeout")


# ------------------------------------------------------------
# FARMERCHAT AUDIO FLOW
# ------------------------------------------------------------

def farmerchat_audio_flow(
    driver,
    shadow_host,
    audio_path,
    mic_selector,
    send_selector,
    audio_selector,
    response_selector,
    download_dir
):

    mic_button = driver.execute_script("""
        const host = arguments[0];
        return host.shadowRoot.querySelector(arguments[1]);
    """, shadow_host, mic_selector)

    if not mic_button:
        raise RuntimeError("Mic button not found")

    mic_button.click()

    data, sr = sf.read(audio_path, dtype="float32")

    logger.info(f"Playing audio at {sr} Hz")

    sd.play(data, sr)
    sd.wait()

    send_button = driver.execute_script("""
        const host = arguments[0];
        return host.shadowRoot.querySelector(arguments[1]);
    """, shadow_host, send_selector)

    if not send_button:
        raise RuntimeError("Send button not found")

    send_button.click()

    time.sleep(0.5)

    audio_element, text = wait_for_shadow_audio_and_text(
        driver,
        shadow_host,
        audio_selector,
        response_selector
    )

    audio_src = audio_element.get_attribute("src")

    audio_result = download_audio(driver, audio_element, audio_src, download_dir)

    if text:
        audio_result["content"] = text

    return audio_result

# ------------------------------------------------------------
# WAIT FOR TEXT RESPONSE (NORMAL DOM)
# ------------------------------------------------------------

def wait_for_text_response(driver, xpath, timeout=60):

    start = time.time()

    while time.time() - start < timeout:

        nodes = driver.find_elements(By.XPATH, xpath)

        if nodes:

            text = nodes[-1].text.strip()

            if text:
                return text

        time.sleep(0.5)

    raise TimeoutException("Response timeout")


# ------------------------------------------------------------
# WAIT FOR TEXT RESPONSE (SHADOW DOM)
# ------------------------------------------------------------

def wait_for_new_shadow_text(driver, shadow_host, selector, initial_count, timeout=60, stable_time=3):

    start = time.time()
    last_text = ""
    last_change = time.time()

    while time.time() - start < timeout:

        result = driver.execute_script("""
            const host = arguments[0];
            const sel = arguments[1];
            const nodes = host.shadowRoot.querySelectorAll(sel);

            return {
                count: nodes.length,
                text: nodes.length ? nodes[nodes.length-1].textContent : ""
            };
        """, shadow_host, selector)

        # Wait until a NEW message appears
        if result["count"] <= initial_count:
            time.sleep(0.5)
            continue

        text = (result["text"] or "").strip()

        if text != last_text:
            last_text = text
            last_change = time.time()

        # Wait until text stops changing
        if text and (time.time() - last_change) > stable_time:
            return text

        time.sleep(0.5)

    raise TimeoutException("New shadow response timeout")


# ------------------------------------------------------------
# WAIT FOR AUDIO RESPONSE
# ------------------------------------------------------------

def wait_for_shadow_audio(driver, shadow_host, selector, timeout=60):

    start = time.time()

    while time.time() - start < timeout:

        audio = driver.execute_script("""
            const host = arguments[0];
            const nodes = host.shadowRoot.querySelectorAll(arguments[1]);

            if (!nodes.length) return null;

            const last = nodes[nodes.length-1];

            if (last.src) return last;

            return null;
        """, shadow_host, selector)

        if audio:
            return audio

        time.sleep(0.5)

    raise TimeoutException("Audio response timeout")


# ------------------------------------------------------------
# AUDIO DOWNLOAD + CONVERT TO WAV
# ------------------------------------------------------------

def download_audio(driver, audio_element, src, download_dir):
    os.makedirs(download_dir, exist_ok=True)

    raw_path = os.path.join(download_dir, "agent_response.raw")
    wav_path = os.path.join(download_dir, "agent_response.wav")

    if src.startswith("blob:"):

        logger.info("Extracting blob audio")

        base64_data = driver.execute_async_script("""
            const audio = arguments[0];
            const callback = arguments[arguments.length - 1];

            fetch(audio.src)
            .then(r => r.blob())
            .then(blob => {
                const reader = new FileReader();
                reader.onloadend = () => {
                    callback(reader.result.split(',')[1]);
                };
                reader.readAsDataURL(blob);
            })
            .catch(() => callback(null));
        """, audio_element)

        audio_bytes = base64.b64decode(base64_data)

    else:

        logger.info("Downloading audio via HTTP")

        audio_bytes = requests.get(src).content

    with open(raw_path, "wb") as f:
        f.write(audio_bytes)

    subprocess.run(
        ["ffmpeg", "-y", "-i", raw_path, wav_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    os.remove(raw_path)

    logger.info(f"Audio saved → {wav_path}")

    return {
        "type": "audio",
        "file": wav_path
    }


# ------------------------------------------------------------
# SHADOW HOST DISCOVERY
# ------------------------------------------------------------

def get_shadow_host(driver, iframe_selector):

    frames = driver.find_elements(By.CSS_SELECTOR, iframe_selector)

    if frames:
        driver.switch_to.frame(frames[0])

    host = driver.execute_script("""
        return Array.from(document.querySelectorAll('*'))
        .find(el => el.shadowRoot);
    """)

    if not host:
        raise RuntimeError("Shadow host not found")

    return host

# Validates Chrome and ChromeDriver versions to ensure they are compatible.
# This check prevents Selenium WebDriver initialization failures during web evaluations.
def test_chrome_driver_compatibility():
    try:
        logger.info("Starting Chrome–ChromeDriver compatibility check")

        chrome_commands = [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser"
        ]

        chrome_version = None
        chrome_binary = None

        for cmd in chrome_commands:
            if shutil.which(cmd):
                chrome_binary = cmd
                output = subprocess.check_output([cmd, "--version"]).decode().strip()
                chrome_version = output.split()[2]
                break

        if not chrome_version:
            logger.error("No Chrome or Chromium browser found")
            return False

        logger.info("Using browser executable: %s", chrome_binary)
        logger.info("Detected Chrome version: %s", chrome_version)

        driver_output = subprocess.check_output(["chromedriver", "--version"]).decode().strip()
        driver_version = driver_output.split()[1]

        logger.info("Detected ChromeDriver version: %s", driver_version)

        chrome_major = int(chrome_version.split(".")[0])
        driver_major = int(driver_version.split(".")[0])

        version_gap = abs(chrome_major - driver_major)

        if version_gap <= 1:
            logger.info(
                "Compatibility test PASSED: version gap (%d) within allowed tolerance",
                version_gap
            )
            return True
        else:
            logger.error(
                "Compatibility test FAILED: Chrome %d vs ChromeDriver %d (gap too large)",
                chrome_major,
                driver_major
            )
            return False

    except Exception as e:
        logger.exception("Unexpected error during compatibility check: %s", e)
        return False
        
