# Canadian Medical Code Automation

**Automated extraction and AI-powered lookup for the Canadian Classification of Health Interventions (CCI).**

This project is a powerful Python-based automation pipeline designed to parse the complex 2022 CCI PDF manual into a highly structured, machine-readable JSON database. It is paired with a local RAG (Retrieval-Augmented Generation) engine to instantly and accurately retrieve matching medical codes and their attributes using natural language.

---

## 📖 Documentation

The project documentation and progression history is split into two main guides:

*   **[Implementation Plan](./implementation_plan.md)**: Understand the "Why" and "What" - the phased approach to ingesting PDFs, building deterministic parsers, and integrating the LLMs.
*   **[Task Checklist](./task.md)**: The active developer checklist and tracking file.

---

## 🚀 Quick Start

If you just want to get the AI code lookup tool running locally:

### Prerequisites
- Python 3.13
- Virtual Environment set up
- OpenRouter API Key

### Setup
1. Install dependencies from the `pyproject.toml`:

   `pip install .`

2. Create a `.env` file in the root directory and add your key:

   `API_KEY=your_openrouter_api_key_here`

3. Boot up the RAG interactive terminal:

   `python -m src.code_lookup`


To extract texts and tables from PDF file into raw text cache: `python -m src.read_pdf`
To re-parse the raw PDF text into the structured JSON database: `python -m src.parser`

---

## 🛠️ Tech Stack

*   **Language**: Python 3.13
*   **PDF Ingestion**: `pdfplumber`
*   **LLM Engine**: OpenRouter API (`nvidia/nemotron-3-super-120b-a12b:free`)
*   **Static Analysis**: Pyright
*   **Linting/Formatting**: Ruff