# Changelog

All notable changes to the **Bukku Accounting Statement Converter** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.1.0] - 2026-10-24

### Added
- **Online Cloud Web Application**:
  - Flask-based web server (`app.py`) for online cloud deployment.
  - Mobile-responsive, modern frontend (`templates/index.html`) using Tailwind CSS.
  - Live drag-and-drop CSV statement upload zone.
  - Interactive reconciliation audit cards (Bank name, Account No, Statement period, Spent, Received, Closing Balance, Verification badge).
  - Live table preview of converted Bukku statement rows.
  - 1-click downloads for Bukku CSV (`.csv`) and Excel (`.xlsx`).
  - Cloud deployment configuration: `render.yaml` and `Procfile` for Render deployment.
  - Health check endpoint `/health`.
- **Date Format Sanitization & Timestamp Stripping**:
  - Enforced strict removal of all timestamps from the `Date` column across all parsers.
  - Added support for `Y-m-d` (`YYYY-MM-DD`, e.g. `2026-08-03`), directly resolving Bukku's backend validation error: `The statement_lines.0.date does not match the format Y-m-d`.
  - Added support for `dmy` (`DD/MM/YYYY`, e.g. `03/08/2026`) without timestamp to match original Bukku template sample text.
  - Added `--date-format` flag to CLI (`cli.py`) and UI radio selector to desktop GUI (`gui.py`) and web app (`app.py`).
  - Added in-memory parsing (`parse_content`) and streaming export methods (`get_bukku_csv_bytes`, `get_bukku_xlsx_bytes`) to `converter.py`.

---

## [v1.0.0] - 2026-10-05

### Added
- **Core Conversion Engine (`converter.py`)**:
  - Full support for Bank Islam statement formats:
    - Format A: Web portal export with metadata header rows (Date, Account Number, No., Transaction Date, etc.) and footer reconciliation rows (`Total Amount: Dr / Cr`).
    - Format B: Raw 13-column transaction records without header blocks.
  - Multi-bank fuzzy auto-detection parser for other Malaysian and international bank CSVs (Maybank, CIMB, RHB, Public Bank, etc.).
  - Excel formula sanitizer stripping `="value"`, extra quotes, balance signs (`+`/`-`), and thousand separators.
  - Automatic statement period detection: computes full calendar month (`01/MM/YYYY` to `LastDay/MM/YYYY`) when all transactions belong to a single calendar month, or exact span.
  - Automated Closing Balance and Account Number extraction.
  - Dual export formats:
    - RFC-4180 compliant Bukku Bank Statement CSV (`.csv`).
    - Styled Excel Workbook (`.xlsx`) via openpyxl.
  - Mathematical integrity verification: cross-checks parsed transaction sums against the bank's reported footer totals.

- **Command-Line Interface (`cli.py`)**:
  - Single-file conversion (`-i <file>`).
  - Batch folder conversion (`-d <folder>`).
  - Configurable reference column layout (`--ref-style standard` vs `--ref-style party_first`).
  - Automated descriptive fallback toggle (`--no-fill-empty-desc`).
  - Output summary report with bank identity, period, transaction count, debits, credits, and verification status.

- **Desktop Graphical Interface (`gui.py`)**:
  - Clean Tkinter interface running natively on Windows with no third-party GUI dependencies.
  - Quick load buttons for recent monthly statements (Ogos 2026, Sept 2026).
  - Live preview table showing converted Bukku columns: `Date`, `Description`, `Spent`, `Received`, `Ref 1`, `Ref 2`, `Ref 3`, `Ref 4`.
  - Real-time reconciliation badge displaying calculated totals and verification status.
  - One-click export and direct folder opening in Windows File Explorer.

- **Windows Automation Scripts**:
  - `convert_statement.bat`: Double-click or drag-and-drop CSV converter.
  - `run_gui.bat`: Desktop GUI launcher.

- **Automated Verification Suite (`test_converter.py`)**:
  - Unit and integration tests verifying parsing, exact debit/credit mathematical parity, closing balances, and template file creation using authentic accounting statements.
