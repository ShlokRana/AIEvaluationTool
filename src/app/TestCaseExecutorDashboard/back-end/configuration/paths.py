import json
import os
from openpyxl import load_workbook
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # config/

BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))  # back-end/
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../../../.."))  # repo root

# INTERFACE_MANAGER_CONFIG = os.path.join(Path(__file__).resolve().parents[5], "config.json")
ROOT_CONFIG_PATH = os.path.join(Path(__file__).resolve().parents[5], "config.json")
 
profile_path = os.path.expanduser("~/test_profile")


TEMPLATE_PATH = os.path.join(BACKEND_ROOT, "templates", "Reports.xlsx")


wb = load_workbook(TEMPLATE_PATH)