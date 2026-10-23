# Bukku Accounting Statement Converter

**Version**: `v1.1.0`  
**GitHub Repository**: [https://github.com/abidmasjuki/bukku-accounting-converter](https://github.com/abidmasjuki/bukku-accounting-converter)  
**Purpose**: Automatically convert Bank Islam transaction history CSVs (or any bank statement CSV) into the official Bukku Accounting Bank Statement import template (`.csv` and `.xlsx`).

---

## 🌟 Key Features

1. **Online Web Application (Cloud Ready)**:
   - Deployable directly to Render / Cloud Run / PaaS with pre-configured `render.yaml` and `Procfile`.
   - Responsive web interface with drag-and-drop CSV upload, date format switcher, live reconciliation cards, and 1-click downloads.
2. **Native Bank Islam & Multi-Bank Support**:
   - Handles Bank Islam web exports with metadata headers and footer totals.
   - Handles raw 13-column Bank Islam transaction lines.
   - Smart fallback engine for generic bank CSVs (Maybank, CIMB, RHB, Public Bank, etc.).
3. **Bukku-Strict Date Formatting (No Timestamp)**:
   - Automatically strips all timestamps from the `Date` column.
   - Generates dates in `YYYY-MM-DD` (`Y-m-d`), strictly compliant with Bukku's backend validation rule (`The statement_lines.0.date does not match the format Y-m-d`).
   - Supports `DD/MM/YYYY` without timestamp as an alternate display format.
4. **Formula & Formatting Sanitization**:
   - Automatically removes Excel quotation wrappers like `="12029010086201"` -> `12029010086201`.
   - Cleanses debit/credit amount columns and balance flags (`+`/`-`).
5. **Automated Header & Metadata Generation**:
   - `From Date` & `To Date`: Computes calendar statement period (e.g. `01/08/2026` to `31/08/2026`).
   - `Account No`: Automatically detected and formatted.
   - `Closing Balance`: Extracted from the last transaction's balance column.
6. **Reconciliation Audit Verification**:
   - Automatically cross-checks transaction debits and credits against the bank statement's reported summary totals, ensuring 100% mathematical parity.
7. **Dual Output Formats**:
   - Generates both RFC-4180 standard **CSV** with UTF-8 BOM (for direct Bukku upload) and styled **Excel (.xlsx)**.

---

## 📁 Bukku Statement Format Mapping

| Bukku Column | Source Field (Bank Islam) | Example Value (Y-m-d Format) |
|---|---|---|
| **Date** | Transaction Date | `2026-08-03` *(No timestamp, satisfies Bukku validator)* |
| **Description** | Customer/EFT No (fallback to Txn Desc if blank) | `7-msb-locum-july26` / `RENTAL AUG` |
| **Spent** | Debit Amount | `2000.00` |
| **Received** | Credit Amount | `400.00` |
| **Ref 1** | Transaction Description | `INW DuitNow Transfer` / `CDB CS TO IBFTS3` |
| **Ref 2** | Sender Name / Recipient Name | `MARHAKIM SDN BHD` / `CHUNG KOK MENG` |
| **Ref 3** | Payment Details | `D83RMCD6` / `GAJI JULAI` |
| **Ref 4** | Ref / Cheque No | `810 XRPP329` |

---

## 🚀 How to Run

### Option 1: Online Web App (Cloud / Render)
Run locally:
```bash
python app.py
```
Or deploy to Render using the included `render.yaml`:
1. Connect your GitHub repository `https://github.com/abidmasjuki/bukku-accounting-converter` to Render.
2. Select **Blueprint** or create a **Web Service** with:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
3. Access your web service online from anywhere via your Render URL!
Double-click `run_gui.bat` or run:
```bash
python gui.py
```
- Click **"Browse CSV File..."** or click quick buttons (**Ogos 2026**, **Sept 2026**).
- Review the live data in the preview table and verify the **Reconciliation: PASS** badge.
- Click **"Convert & Save Bukku Template"**.

### Option 2: Drag and Drop
Simply drag any `.csv` file onto [convert_statement.bat](file:///G:/My%20Drive/AI_Business_Empire/Antigravity/Bukku%20Accounting%20Converter/convert_statement.bat) in Windows Explorer.

### Option 3: Command Line (CLI)
Convert a single statement:
```bash
python cli.py -i "path/to/statement.csv"
```

Batch convert an entire directory:
```bash
python cli.py -d "G:\My Drive\RPWP HEALTHCARE MASTER FOLDER\HEARING CENTRE\ACCOUNTING\BUKKU"
```

---

## 🧪 Self-Audit & Test Verification

Run the test suite to verify parsing and mathematical integrity:
```bash
python test_converter.py
```
