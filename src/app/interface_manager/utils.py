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
import shutil

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
download_dir = Path(__file__).resolve().parent.parent.parent.parent / "agent_response_cache" 
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
        opts.add_argument("--mute-audio")
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
                # opts.add_argument("--user-data-dir=/home/seluser/chrome-data")
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

        qr_cfg = app_cfg.get("ChatPage", {}).get("scan_qr_code_element")
        print(qr_cfg)
        print(app_name.lower())

        if app_name.lower() == "whatsapp" or app_name.lower() == "whatsapp web" or app_name.lower() == "whatsapp_web":
            wait_for_login = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, qr_cfg))
            )
            print(wait_for_login)
            if wait_for_login:
                time.sleep(60)  # wait for QR code to load
                logger.info("Waiting for WhatsApp Web login via QR code.")
                return True
            else:
                logger.info(f"{app_name} has no LoginPage config → skipping login")
                return True

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
    contact_selection = "//span[@title='" + entity_name + "']"

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
        
        time.sleep(5)

        contact_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, contact_selection))
        )
        contact_select.click()

        logger.info(f"{app_name}: '{entity_name}' search successful")
        return True
    except Exception as e:
        logger.error(f"{app_name}: search failed for '{entity_name}': {e}")
        return False

def split_message(message, max_length=1000):
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]


def normalize_whatsapp_text(text: str) -> str:
    return " ".join((text or "").split())


def get_whatsapp_incoming_messages(driver, chat_cfg):
    """
    Return incoming WhatsApp message bubbles using a few DOM fallbacks.
    WhatsApp Web changes markup frequently, so relying on one XPath is brittle.
    """
    candidate_xpaths = [
        chat_cfg.get("message_in_element"),
        "//div[contains(@class,'message-in')]",
        "//div[contains(@data-testid,'msg-container') and contains(@class,'message-in')]",
    ]

    seen_ids = set()
    messages = []

    for xpath in candidate_xpaths:
        if not xpath:
            continue
        try:
            for msg in driver.find_elements(By.XPATH, xpath):
                element_id = getattr(msg, "id", None)
                if element_id and element_id in seen_ids:
                    continue
                if element_id:
                    seen_ids.add(element_id)
                messages.append(msg)
        except Exception:
            continue

        if messages:
            return messages

    return []


def extract_whatsapp_message_text(msg, chat_cfg) -> str:
    """
    Extract readable text from a WhatsApp incoming bubble.
    Falls back to the bubble's visible text when selectable spans are absent.
    """
    fragments = []

    for node in msg.find_elements(By.XPATH, chat_cfg["agent_response_element"]):
        try:
            txt = normalize_whatsapp_text(node.text)
            if txt:
                fragments.append(txt)
        except StaleElementReferenceException:
            continue

    if fragments:
        unique_fragments = []
        for fragment in fragments:
            if fragment not in unique_fragments:
                unique_fragments.append(fragment)
        return " ".join(unique_fragments)

    try:
        js_text = msg.parent.execute_script(
            "return (arguments[0].innerText || arguments[0].textContent || '').trim();",
            msg
        )
        js_text = normalize_whatsapp_text(js_text)
        if js_text:
            return js_text
    except Exception:
        pass

    try:
        return normalize_whatsapp_text(msg.text)
    except StaleElementReferenceException:
        return ""

def send_text_whatsapp(driver, prompt, chat_cfg):
    wait = WebDriverWait(driver, 30)

    message_box = wait.until(
        EC.element_to_be_clickable((By.XPATH, chat_cfg["prompt_input_box_element"]))
    )

    message_box.send_keys(Keys.CONTROL + "a")
    message_box.send_keys(Keys.DELETE)

    chunks = split_message(prompt)

    for i, chunk in enumerate(chunks):
        message_box.send_keys(chunk)
        if i < len(chunks) - 1:
            message_box.send_keys(Keys.SHIFT + Keys.ENTER)
        time.sleep(0.2)

    send_button = driver.find_element(By.XPATH, chat_cfg["send_button_element"])
    send_button.click()


def wait_for_whatsapp_response(
    driver,
    chat_cfg,
    timeout=60,
    quiet_time=3,
    pre_send_count=None
):

    start = time.time()
    last_change = time.time()

    responses = []
    seen_keys = set()

    # ---------- STEP 1: Establish baseline ----------
    incoming_msgs = get_whatsapp_incoming_messages(driver, chat_cfg)

    if pre_send_count is None:
        pre_send_count = len(incoming_msgs)

    logger.info(f"Baseline incoming count: {pre_send_count}")

    # Capture baseline texts safely
    baseline_texts = []
    for msg in incoming_msgs[:pre_send_count]:
        try:
            text = extract_whatsapp_message_text(msg, chat_cfg)
            if text:
                baseline_texts.append(text)
        except StaleElementReferenceException:
            continue

    baseline_len = len(baseline_texts)
    last_marker = baseline_texts[-1] if baseline_texts else None

    # ---------- STEP 2: Wait for new messages ----------
    while time.time() - start < timeout:

        incoming_msgs = get_whatsapp_incoming_messages(driver, chat_cfg)

        current_texts = []
        for msg in incoming_msgs:
            try:
                text = extract_whatsapp_message_text(msg, chat_cfg)
                if text:
                    current_texts.append(text)
            except StaleElementReferenceException:
                continue

        # ---------- STEP 3: Extract only NEW messages ----------
        new_msgs = []

        if len(current_texts) > baseline_len:
            # Primary strategy: index-based
            new_msgs = current_texts[baseline_len:]
        else:
            # Fallback: marker-based
            collecting = False
            for text in current_texts:
                if not collecting:
                    if text == last_marker:
                        collecting = True
                    continue
                new_msgs.append(text)

        # ---------- STEP 4: Deduplicate safely ----------
        new_detected = False

        for idx, text in enumerate(new_msgs):
            key = f"{idx}:{text}"

            if key not in seen_keys:
                seen_keys.add(key)
                responses.append(text)
                new_detected = True

        # ---------- STEP 5: Idle detection ----------
        if new_detected:
            last_change = time.time()
            logger.info(
                f"(Waited:{int(time.time() - start)}) "
                f"Captured {len(responses)} response(s)"
            )

        if responses and (time.time() - last_change > quiet_time):
            logger.info(
                f"No new message for {quiet_time}s — returning responses"
            )
            break

        time.sleep(0.5)

    return responses

def send_audio_whatsapp(driver, audio_path, chat_cfg):

    wait = WebDriverWait(driver, 30)

    audio_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, chat_cfg["audio_record_button_element"])
        )
    )

    audio_button.click()

    # WARNING: This requires a virtual loopback audio device
    # (e.g. PulseAudio monitor source on Linux, VB-Cable on Windows)
    # so that sd.play() output feeds into the microphone input.
    # Without it, WhatsApp will record silence.
    devices = sd.query_devices()
    default_input = sd.query_devices(kind='input')
    logger.info(f"Recording from input device: {default_input['name']}")
    logger.warning(
        "Audio will play through speakers. Ensure a virtual loopback "
        "device is active so WhatsApp mic captures the playback."
    )

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
    audio_grace=15,
    pre_send_count=None
):
    import os, time, subprocess
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains

    if download_dir is None:
        download_dir = DEFAULT_DOWNLOAD_DIR

    os.makedirs(download_dir, exist_ok=True)

    start_time = time.time()

    text_parts = []
    audio_file = None

    last_update_time = None
    first_response_time = None

    # --------------------------------------------------
    # ✅ BASELINE (ignore old messages)
    # --------------------------------------------------
    baseline_msgs = get_whatsapp_incoming_messages(driver, chat_cfg)

    processed_msgs = set()
    for msg in baseline_msgs:
        try:
            processed_msgs.add(msg.id)
        except:
            processed_msgs.add(str(msg))

    logger.info(f"Baseline messages captured: {len(processed_msgs)}")

    # --------------------------------------------------
    # ✅ SAFE TEXT EXTRACTION
    # --------------------------------------------------
    def safe_extract_text(msg):
        try:
            spans = msg.find_elements(By.XPATH, ".//span[@dir='ltr']")
            texts = [s.text for s in spans if s.text.strip()]
            if texts:
                return " ".join(texts).strip()
            return msg.text.strip()
        except:
            return msg.text.strip()

    logger.info("Waiting for WhatsApp response...")

    while time.time() - start_time < timeout:

        incoming_msgs = get_whatsapp_incoming_messages(driver, chat_cfg)

        new_msgs = []

        # --------------------------------------------------
        # ✅ detect ONLY new messages
        # --------------------------------------------------
        for msg in incoming_msgs:
            try:
                msg_id = msg.id
            except:
                msg_id = str(msg)

            if msg_id not in processed_msgs:
                processed_msgs.add(msg_id)
                new_msgs.append(msg)

        # --------------------------------------------------
        # process messages
        # --------------------------------------------------
        for msg in new_msgs:

            # -------------------------
            # ✅ TEXT CAPTURE
            # -------------------------
            new_text = safe_extract_text(msg)

            if new_text:
                if new_text not in text_parts:
                    text_parts.append(new_text)

                    last_update_time = time.time()

                    if first_response_time is None:
                        first_response_time = time.time()

                    logger.info(f"Captured text → {new_text}")

            # -------------------------
            # ✅ AUDIO CAPTURE
            # -------------------------
            if not audio_file:
                try:
                    voice_nodes = msg.find_elements(
                        By.XPATH,
                        chat_cfg["audio_message_element"]
                    )
                except:
                    voice_nodes = []

                if voice_nodes:
                    logger.info("Audio detected")

                    try:
                        before = set(os.listdir(download_dir))

                        ActionChains(driver).move_to_element(msg).perform()

                        chevron = msg.find_element(
                            By.XPATH,
                            chat_cfg["download_menu_element"]
                        )
                        driver.execute_script("arguments[0].click();", chevron)

                        menu = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located(
                                (By.XPATH, chat_cfg["menu_container_element"])
                            )
                        )

                        buttons = menu.find_elements(
                            By.XPATH,
                            chat_cfg["download_button_element"]
                        )

                        clicked = False
                        for btn in buttons:
                            if btn.is_displayed():
                                for _ in range(3):
                                    try:
                                        driver.execute_script(
                                            "arguments[0].click();", btn
                                        )
                                        clicked = True
                                        break
                                    except:
                                        time.sleep(0.5)
                                if clicked:
                                    break

                        if not clicked:
                            raise Exception("Download button not clickable")

                        # -------------------------
                        # ✅ WAIT FOR DOWNLOAD
                        # -------------------------
                        start_download = time.time()
                        audio_done = False

                        while time.time() - start_download < 60:
                            after = set(os.listdir(download_dir))
                            new_files = after - before

                            valid_files = [
                                f for f in new_files
                                if (
                                    not f.startswith(".")
                                    and not f.endswith(".crdownload")
                                    and f.split(".")[-1] in ["opus", "ogg", "mp3", "m4a"]
                                )
                            ]

                            if valid_files:
                                # ✅ pick latest file
                                file = max(
                                    valid_files,
                                    key=lambda f: os.path.getctime(os.path.join(download_dir, f))
                                )

                                path = os.path.join(download_dir, file)
                                wav_path = os.path.splitext(path)[0] + ".wav"

                                subprocess.run(
                                    ["ffmpeg", "-y", "-i", path, wav_path],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                )

                                # ✅ handle conversion safely
                                if os.path.exists(wav_path):
                                    # remove source file
                                    if os.path.exists(path):
                                        os.remove(path)

                                    # cleanup other junk files in download dir
                                    for f in os.listdir(download_dir):
                                        full_path = os.path.join(download_dir, f)

                                        if full_path == wav_path:
                                            continue  # keep final wav

                                        if (
                                            f.startswith(".")
                                            or f.endswith(".crdownload")
                                            or f.split(".")[-1] in ["ogg", "opus", "mp3", "m4a"]
                                        ):
                                            try:
                                                os.remove(full_path)
                                            except:
                                                pass
                                    audio_file = wav_path
                                else:
                                    audio_file = path  # fallback

                                last_update_time = time.time()

                                if first_response_time is None:
                                    first_response_time = time.time()

                                logger.info(f"Captured audio → {audio_file}")

                                audio_done = True
                                break

                            time.sleep(1)

                        if audio_done:
                            break

                    except Exception as e:
                        logger.warning(f"Audio failed: {e}")

        # --------------------------------------------------
        # ✅ EXIT CONDITION (SMART WAIT)
        # --------------------------------------------------
        if first_response_time:
            if audio_file:
                if last_update_time and (time.time() - last_update_time > audio_grace):
                    logger.info("Response stabilized (text + audio)")
                    break
            else:
                if time.time() - first_response_time > audio_grace:
                    logger.info("Response stabilized (text only)")
                    break

        time.sleep(0.3)

    # --------------------------------------------------
    # ✅ COMBINE TEXT
    # --------------------------------------------------
    final_text = "\n".join(text_parts[:-1]).strip() # remove the last element as it captures the time also.

    # --------------------------------------------------
    # ✅ RETURN (DB COMPATIBLE)
    # --------------------------------------------------
    return {
        "type": "text",
        "content": final_text,
        "file": audio_file
    }


def send_message_whatsapp(
    driver,
    prompt: str = None,
    audio_path: str = None,
    file_path: str = None,
    is_audio: bool = False,
    is_file: bool = False,
    download_dir: str = None
):
    import time
    from selenium.webdriver.common.by import By

    max_retries = 3
    attempt = 0

    config = load_config()
    app_name = config.get("application_type")

    app_cfg = load_xpaths()["applications"][app_name.lower()]
    chat_cfg = app_cfg["ChatPage"]

    # ---------- Helper: Stable incoming count ----------
    def get_stable_incoming_count(driver, xpath, retries=3, delay=0.5):
        prev = -1
        for _ in range(retries):
            elems = driver.find_elements(By.XPATH, xpath)
            curr = len(elems)
            if curr == prev:
                return curr
            prev = curr
            time.sleep(delay)
        return curr

    while attempt < max_retries:

        try:
            # ---------- Connectivity ----------
            if not check_and_recover_connection():
                return {
                    "type": "error",
                    "content": "No internet connection"
                }

            in_xpath = chat_cfg["message_in_element"]

            # ---------- TEXT MESSAGE ----------
            if not is_audio and not is_file:

                logger.info("Sending text message")

                # ✅ Stable baseline BEFORE send
                pre_send_count = get_stable_incoming_count(driver, in_xpath)
                logger.info(f"Pre-send incoming message count: {pre_send_count}")

                send_text_whatsapp(driver, prompt, chat_cfg)

                responses = wait_for_whatsapp_response(
                    driver,
                    chat_cfg,
                    timeout=60,
                    quiet_time=3,
                    pre_send_count=pre_send_count
                )

                if responses:
                    response = " ".join(responses)
                    logger.info(f"Received response: {response}")
                    return {
                        "type": "text",
                        "content": response
                    }

                return {
                    "type": "error",
                    "content": "No response received"
                }

            # ---------- AUDIO MESSAGE ----------
            elif is_audio and not is_file:

                logger.info(f"Sending voice note → {audio_path}")

                pre_send_count = get_stable_incoming_count(driver, in_xpath)
                logger.info(f"Pre-send incoming count (audio): {pre_send_count}")

                send_audio_whatsapp(driver, audio_path, chat_cfg)

                response = wait_for_whatsapp_audio_or_text_response(
                    driver,
                    chat_cfg,
                    download_dir=download_dir,
                    pre_send_count=pre_send_count
                )

                return response

            # ---------- FILE ATTACHMENT ----------
            elif is_file:

                logger.info(f"Sending file attachment → {file_path}")

                pre_send_count = get_stable_incoming_count(driver, in_xpath)
                logger.info(f"Pre-send incoming count (file): {pre_send_count}")

                send_file_whatsapp(driver, file_path, chat_cfg)

                response = wait_for_whatsapp_audio_or_text_response(
                    driver,
                    chat_cfg,
                    download_dir=download_dir,
                    pre_send_count=pre_send_count
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

    if not textarea:
        raise RuntimeError("Prompt input box not found")
    
    # To clear text area
    textarea.send_keys(Keys.CONTROL + "a")
    textarea.send_keys(Keys.DELETE)
    
    initial_count = driver.execute_script("""
        const host = arguments[0];
        return host.shadowRoot.querySelectorAll(arguments[1]).length;
    """, shadow_host, response_selector)

    textarea.send_keys(prompt)
    textarea.send_keys(Keys.RETURN)

    time.sleep(10)
    
    text = wait_for_new_shadow_text(driver, shadow_host, response_selector, initial_count)

    return {
        "type": "text",
        "content": text
    }


APP_HANDLERS = {
    "farmerchat": handle_farmerchat,
}


# Sending Message to Web applications
def send_message_webapp(
    driver,
    app_name,
    download_dir=None,
    prompt=None,
    audio_path=None,
    max_retries=3,
):

    if download_dir is None:
        download_dir = DEFAULT_DOWNLOAD_DIR

    app = app_name.lower()
    handler = APP_HANDLERS.get(app)

    if not handler:
        raise ValueError(f"Unsupported application: {app}")


    for attempt in range(1, max_retries + 1):

        try:
            if not check_and_recover_connection():
                return {
                    "type": "error",
                    "content": "No internet connection"
                }
            
            return handler(driver, prompt, audio_path, download_dir)

        except Exception as e:

            logger.warning(f"[{app}] attempt {attempt} failed: {e}")

            if attempt == max_retries:
                logger.error(f"[{app}] All {max_retries} attempts failed")
                return {
                    "type": "error",
                    "content": f"Max retries reached for {app}: {str(e)}"
                }

            time.sleep(1.5)


def wait_for_shadow_audio_and_text(driver, shadow_host, audio_selector, text_selector, timeout=30):

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
            logger.info(f"Waited {time.time() - start:.2f}s Received text: {txt}")

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

    time.sleep(10)

    audio_element, text = wait_for_shadow_audio_and_text(
        driver,
        shadow_host,
        audio_selector,
        response_selector
    )

    audio_src = audio_element.get_attribute("src") if audio_element else None

    if not audio_src:
        logger.warning("No audio src found — returning text only")
        return {
            "type": "text",
            "content": text or "No response received"
        }

    try:
        audio_result = download_audio(driver, audio_element, audio_src, download_dir)

        if text:
            return {
                "type": "text",
                "content": text,
                "file": audio_result["file"]   # optional metadata
            }

        return audio_result

    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        if text:
            logger.warning("Falling back to text response")
            return {
                "type": "text",
                "content": text
            }
        return {
            "type": "error",
            "content": f"Audio download failed and no text available: {str(e)}"
        }

# ------------------------------------------------------------
# WAIT FOR TEXT RESPONSE (NORMAL DOM)
# ------------------------------------------------------------

def wait_for_text_response(driver, xpath, timeout=60, stable_time=2):

    start = time.time()
    last_text = ""
    last_change = time.time()

    while time.time() - start < timeout:

        nodes = driver.find_elements(By.XPATH, xpath)

        if nodes:
            # Collect all visible text nodes
            full_text = " ".join(
                n.text.strip() for n in nodes if n.text.strip()
            )

            if full_text and full_text != last_text:
                last_text = full_text
                last_change = time.time()
                logger.info(
                    f"(Waited:{int(time.time() - start)}) "
                    f"Received: {full_text}"
                )

            # Return only when text has stopped changing
            if last_text and (time.time() - last_change) > stable_time:
                return last_text

        time.sleep(0.5)

    raise TimeoutException("Response timeout")

# ------------------------------------------------------------
# WAIT FOR TEXT RESPONSE (SHADOW DOM)
# ------------------------------------------------------------

def wait_for_new_shadow_text(driver, shadow_host, selector, initial_count, timeout=60, stable_time=3, poll_interval=0.5):

    start = time.time()
    last_text = ""
    last_change = time.time()
    first_text_time = None 

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
            time.sleep(0.2)
            continue

        text = (result["text"] or "").strip()

        if text != last_text:
            last_text = text
            last_change = time.time()
            # Log streaming progress
            logger.debug(
                f"(Waited:{int(time.time()-start)}) "
                f"Streaming: {text[:50]}..."
            )

        # Record when first text appeared
        if text and first_text_time is None:
            first_text_time = time.time()

        # Wait until minimum time passed AND text stopped changing
        if (
            text and
            first_text_time and
            (time.time() - first_text_time) > 1 and       # min 1s after first text
            (time.time() - last_change) > stable_time      # text stopped changing
        ):
            logger.info(
                f"(Waited:{int(time.time() - start)}) "
                f"Received: {text}"
            )
            return text

        time.sleep(poll_interval)   # configurable poll interval

    raise TimeoutException("New shadow response timeout")


# ------------------------------------------------------------
# AUDIO DOWNLOAD + CONVERT TO WAV
# ------------------------------------------------------------
import uuid

def download_audio(driver, audio_element, src, download_dir):
    file_path = os.path.join(download_dir, f"agent_response.wav")

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

        if not base64_data:
            raise RuntimeError("Failed to extract blob audio")

        audio_bytes = base64.b64decode(base64_data)

    else:
        logger.info("Downloading audio via HTTP")

        response = requests.get(src, timeout=10)
        response.raise_for_status()
        audio_bytes = response.content

    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    logger.info(f"Audio saved → {file_path}")

    return {"type": "audio", "file": file_path}


# ------------------------------------------------------------
# SHADOW HOST DISCOVERY
# ------------------------------------------------------------

def get_shadow_host(driver, iframe_selector, host_selector=None):

    frames = driver.find_elements(By.CSS_SELECTOR, iframe_selector)

    if frames:
        driver.switch_to.frame(frames[0])

    if host_selector:
        # Target a specific shadow host by CSS selector
        host = driver.execute_script("""
            const el = document.querySelector(arguments[0]);
            return el && el.shadowRoot ? el : null;
        """, host_selector)
        logger.info(f"Shadow host found via selector: {host_selector}")
    else:
        # Fallback — first shadow host found
        host = driver.execute_script("""
            return Array.from(document.querySelectorAll('*'))
            .find(el => el.shadowRoot);
        """)
        logger.info("Shadow host found via fallback scan")

    if not host:
        raise RuntimeError("Shadow host not found")

    return host

# Validates Chrome and ChromeDriver versions to ensure they are compatible.
# This check prevents Selenium WebDriver initialization failures during web evaluations.
def test_chrome_driver_compatibility(container_name=None):
    BASE_CMD = (
        "(google-chrome --version 2>/dev/null || "
        "google-chrome-stable --version 2>/dev/null || "
        "chromium --version 2>/dev/null || "
        "chromium-browser --version 2>/dev/null) && "
        "chromedriver --version 2>/dev/null"
    )

    def run(cmd):
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return result.stdout if result.returncode == 0 else None

    def parse(output):
        try:
            lines = output.strip().split("\n")
            chrome = next(l for l in lines if "Chrome" in l).split()[2]
            driver = next(l for l in lines if "ChromeDriver" in l).split()[1]
            return int(chrome.split(".")[0]), int(driver.split(".")[0])
        except Exception:
            return None, None

    # -------------------------
    # MODE SELECTION (HOST ONLY)
    # -------------------------
    if container_name:
        source = f"DOCKER:{container_name}"
        cmd = ["docker", "exec", container_name, "sh", "-c", BASE_CMD]
        key = "docker"
    else:
        source = "LOCAL"
        cmd = ["sh", "-c", BASE_CMD]
        key = "local"

    # -------------------------
    # EXECUTION
    # -------------------------
    output = run(cmd)

    if not output:
        logger.error(f"[Mode: {source}] Chrome/Driver not available")
        return {key: False}

    chrome_major, driver_major = parse(output)

    if chrome_major is None or driver_major is None:
        logger.error(f"[Mode: {source}] Failed to parse versions")
        return {key: False}

    if chrome_major == driver_major:
        logger.info(f"[Mode: {source}] PASS: Chrome {chrome_major} == Driver {driver_major}")
        return {key: True}
    else:
        logger.error(f"[Mode: {source}] FAIL: Chrome {chrome_major} != Driver {driver_major}")
        return {key: False}
