import json
import socket
import threading
from urllib.parse import urlparse
import psutil
import requests
from fastapi import HTTPException


def check_service(url: str, name: str):
    try:
        response = requests.get(url, timeout=3)
        print(f"Health check for {name} service at {url} returned status code {response.status_code}")
        if response.status_code < 400:
            return f"{name} service is reachable at {url}"
        if response.status_code >= 400:
            raise HTTPException(
                status_code=503,
                detail=f"{name} service is not healthy at {url}"
            )
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503,
            detail=f"{name} service is not reachable at {url}"
        )
    

def ensure_interface_manager_port_running(
    config_path: str,
    timeout: float = 1.5
):
    # 1️⃣ Read config.json
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Interface Manager config: {str(e)}"
        )

    # 2️⃣ Extract base_url
    config_interface_manager = config.get("interface_manager", {})
    if config_interface_manager.get("docker"):
        base_url = config_interface_manager.get("base_url")
    else:
        base_url = config_interface_manager.get("base_url_local")
        
    if not base_url:
        raise HTTPException(
            status_code=500,
            detail="base_url missing in Interface Manager config"
        )

    # 3️⃣ Parse host & port
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port

    if not host or not port:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid base_url in Interface Manager config: {base_url}"
        )

    # 4️⃣ TCP port check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        result = sock.connect_ex((host, port))
        if result != 0:
            raise HTTPException(
                status_code=503,
                detail=f"Interface Manager is not running at {host}:{port}"
            )
    finally:
        sock.close()    


def stop_interface_manager(config_path: str, profile_path: str = "/home/varun/test_profile"):
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        base_url = config.get("base_url")
        parsed = urlparse(base_url)
        port = parsed.port

        if not port:
            return

        # 1️⃣ Try /close first
        try:
            requests.get(f"{base_url}/close", timeout=3)
            print("IM /close called successfully")
        except Exception as e:
            print(f"/close failed (IM may already be dead): {e}")

        # 2️⃣ Kill ALL python processes on that port
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.net_connections(kind='inet'):
                    if conn.laddr.port == port:
                        print(f"Killing PID {proc.pid} ({proc.name()}) on port {port}")
                        proc.kill()
                        proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 3️⃣ Kill ONLY Chrome with the IM profile — not all Chrome!
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'chrome' in (proc.info['name'] or '').lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if f'user-data-dir={profile_path}' in cmdline:  # 👈 only IM's Chrome
                        print(f"Killing IM Chrome PID {proc.pid} with profile {profile_path}")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        print("✅ IM and IM Chrome killed — other Chrome windows untouched!")

    except Exception as e:
        print(f"Failed to stop interface manager: {e}")

def get_chrome_pids_on_port(port: int) -> set:
    """Get Chrome PIDs that are children of the IM process on this port"""
    chrome_pids = set()
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.net_connections(kind='inet'):
                    if conn.laddr.port == port:
                        # Found the IM process — now get its children
                        im_proc = psutil.Process(proc.pid)
                        for child in im_proc.children(recursive=True):
                            if 'chrome' in child.name().lower():
                                chrome_pids.add(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error getting chrome pids: {e}")
    return chrome_pids   

def watch_chrome_and_kill_im(config_path: str):
    import time

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        base_url = config.get("base_url")
        parsed = urlparse(base_url)
        port = parsed.port

        # 1️⃣ Wait for Chrome to actually launch first
        print("👀 Watcher waiting for Chrome to launch...")
        chrome_pids = set()
        for _ in range(15):  # wait up to 15 seconds for Chrome to appear
            chrome_pids = get_chrome_pids_on_port(port)
            if chrome_pids:
                print(f"👀 Watching specific Chrome PIDs: {chrome_pids}")
                break
            time.sleep(1)

        if not chrome_pids:
            print("👀 No Chrome found — watcher exiting")
            return

        # 2️⃣ Now watch ONLY those specific Chrome PIDs
        while True:
            time.sleep(2)
            any_alive = False
            for pid in chrome_pids:
                try:
                    proc = psutil.Process(pid)
                    if proc.is_running():
                        any_alive = True
                        break
                except psutil.NoSuchProcess:
                    continue

            if not any_alive:
                print("💀 IM Chrome is dead — killing IM!")
                stop_interface_manager(config_path)
                break

        print("👀 Chrome watcher stopped")

    except Exception as e:
        print(f"Watcher error: {e}")

def watch_im_process(config_path: str, profile_path: str, stop_event: threading.Event):
    import time

    def is_im_chrome_open() -> bool:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'chrome' in (proc.info['name'] or '').lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if f'user-data-dir={profile_path}' in cmdline:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    print("👀 Waiting for IM Chrome to open...")

    # 1️⃣ Wait for Chrome with this profile to open
    for _ in range(30):
        if stop_event.is_set():
            print("👀 Run finished — watcher exiting")
            return
        if is_im_chrome_open():
            print(f"👀 IM Chrome is open — watching profile {profile_path}")
            break
        time.sleep(1)
    else:
        print("👀 IM Chrome never opened — watcher exiting")
        return

    # 2️⃣ Now watch if it closes
    while True:
        time.sleep(2)
        if stop_event.is_set():
            print("👀 Run completed normally — NOT killing IM ✅")
            return
        if not is_im_chrome_open():
            print("💀 IM Chrome closed — killing IM!")
            stop_interface_manager(config_path)
            break

    print("👀 Watcher stopped")        

             