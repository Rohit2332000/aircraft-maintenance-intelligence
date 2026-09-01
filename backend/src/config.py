from pathlib import Path
import os
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR = BASE_DIR / "outputs"


# ============================================================
# DATA FILES
# ============================================================

# Optional local development dataset.
# The production API receives the Excel file through UploadFile.
EXCEL_FILE = DATA_DIR / "aircraft_maintenance_intelligence_dataset.xlsx"


# ============================================================
# LLM CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

GROQ_TEMPERATURE = float(
    os.getenv(
        "GROQ_TEMPERATURE",
        "0.0"
    )
)


# ============================================================
# ANALYTICS CONFIGURATION
# ============================================================

TREND_WINDOW = int(
    os.getenv(
        "TREND_WINDOW",
        "5"
    )
)

Z_SCORE_THRESHOLD = float(
    os.getenv(
        "Z_SCORE_THRESHOLD",
        "3.0"
    )
)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)
