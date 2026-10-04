# Changelog

All notable changes to the **Bukku Accounting Statement Converter** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
