import os
import json
import sys
from pathlib import Path
from lib.utils import get_logger, get_logger_verbosity
logger = get_logger(__name__)
# Allow running this file directly (e.g. `python database.py`) by ensuring the repo's `src/`
# directory is on `sys.path` so imports like `from lib.orm import DB` work.



SRC_DIR = Path(__file__).resolve().parents[4]
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
project_root = Path(__file__).resolve().parents[5]

# Import after config/print so a missing dependency doesn't hide the engine selection output.
from lib.orm import DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = Path(project_root) / "config.json"
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

db_cfg = config.get("db", {})
engine_type = db_cfg.get("engine", "sqlite").lower()

port_config = config.get("port", {})
BACKEND_PORT = int(port_config.get("back-end"))

if engine_type == "sqlite":
    db_file = db_cfg.get("file", "AIEvaluationData.db")

    # data folder under project root
    db_folder = os.path.join(project_root, "data")
    os.makedirs(db_folder, exist_ok=True)
    
    # DB file inside the data folder
    db_path = os.path.join(db_folder, db_file)
    
    # Update the SQLALCHEMY_DATABASE_URL
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}".format(db_path=db_path)
    
    # # Re-create the engine with the new URL
    # engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
elif engine_type == "mariadb":
    SQLALCHEMY_DATABASE_URL = "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}".format(
        user=db_cfg.get("user"),
        password=db_cfg.get("password"),
        host=db_cfg.get("host"),
        port=db_cfg.get("port"),
        database=db_cfg.get("database"),
    )
else: 
    raise ValueError("Unsupported database engine: {engine_type}")

db = DB(db_url=SQLALCHEMY_DATABASE_URL, debug=False)

def get_db():
    return db

