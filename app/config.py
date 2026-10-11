from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
DB_PATH = DATA_DIR / "smartgen.sqlite3"
for path in (DATA_DIR, IMAGE_DIR):
    path.mkdir(parents=True, exist_ok=True)
