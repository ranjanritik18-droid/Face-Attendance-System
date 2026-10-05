# config.py
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATASET = BASE / "dataset"
SNAP = BASE / "snapshots"
DB_PATH = BASE / "attendance.db"
CACHE = BASE / "encodings_cache.pkl"

# Camera / detection settings
CAM_IDX = 0
FRAME_SCALE = 0.25
MATCH_TOL = 0.45
REQUIRED = 3
COOLDOWN = 40
CAPTURE_COUNT = 5
CAPTURE_DELAY = 0.9

DATASET.mkdir(exist_ok=True)
SNAP.mkdir(exist_ok=True)

# Optional Excel support flag (import detection)
PANDAS_OK = False
try:
    import pandas as _pd  # noqa
    import openpyxl  # noqa
    PANDAS_OK = True
except Exception:
    PANDAS_OK = False