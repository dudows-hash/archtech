import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HISTORY_PATH = DATA_DIR / "history.json"

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID", "")

PIPELINE_STEP_DELAY = float(os.getenv("PIPELINE_STEP_DELAY", "0.7"))
SECRET_KEY = os.getenv("SECRET_KEY", "arch-tech-commercial")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
