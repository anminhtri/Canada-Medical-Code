"""
Centralized configuration for the CCI Code Pipeline.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
PDF_PATH = PROJECT_ROOT / "2022 CCI Alphabetic and Tabular List.pdf"
CACHE_DIR = PROJECT_ROOT / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── PDF Extraction Settings ────────────────────────────────────────────
DEFAULT_BATCH_SIZE = 50  # pages per batch
DEFAULT_START_PAGE = 1
DEFAULT_END_PAGE = None  # None = all pages

# ── Logging ────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "pipeline.log"

# ── CCI Code Regex ────────────────────────────────────────────────────
CCI_CODE_PATTERN = r"\d+\.[A-Z]{2}\.\d{2}"  # e.g. 1.AA.13
CCI_QUALIFIER_PATTERN = r"\d+\.[A-Z]{2}\.\d{2}\.[A-Za-z0-9\-]+"  # e.g. 1.AA.13.HA-C2
