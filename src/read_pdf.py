import json
from pathlib import Path
from typing import List, Dict

import pdfplumber
from loguru import logger

from config import CACHE_DIR

pdf_path = "2022 CCI Alphabetic and Tabular List.pdf"
start_page = 68
end_page = 69


def get_cache_path(start_page: int, end_page: int) -> Path:
    return CACHE_DIR / f"raw_text_{start_page}_{end_page}.json"


def extract_pages(start_page: int, end_page: int, pdf_path: str | Path) -> List[Dict]:
    cache_path = get_cache_path(start_page, end_page)

    if cache_path.exists():
        logger.info(f"Loading cached text from {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info(f"Extracting text from {pdf_path} (pages {start_page}-{end_page})")

    extracted_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page)

        for i in range(start_idx, end_idx):
            page = pdf.pages[i]
            text = page.extract_text(layout=True)
            tables = page.extract_tables()
            if text:
                extracted_pages.append(
                    {"page_num": i + 1, "text": text, "tables": tables}
                )
            else:
                logger.warning(f"No text found on page {i+1}")

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(extracted_pages, f, ensure_ascii=False, indent=2)

    return extracted_pages


if __name__ == "__main__":
    result = extract_pages(start_page, end_page, pdf_path)
