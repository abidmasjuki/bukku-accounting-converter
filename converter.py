"""
Bukku Accounting Converter - Core Engine
Converts Bank Islam (and generic Malaysian / international bank statements)
into the official Bukku Accounting Bank Statement CSV & Excel template format.
Version: 1.0.0
"""

import csv
import os
import re
import calendar
from datetime import datetime
from pathlib import Path
from config import BUKKU_COLUMNS, MALAY_MONTHS, VERSION

def clean_cell(val):
    """
    Cleans cell data by stripping excel formula wrappers like ="value"
    surrounding quotes, whitespace, and trailing balance flags (+/-).
    """
    if val is None:
        return ""
    val = str(val).strip()
    if (val.startswith('="') and val.endswith('"')) or (val.startswith("='") and val.endswith("'")):
        val = val[2:-1]
    elif val.startswith('='):
        val = val[1:].strip('"\'')
    
    # Strip any extra outer quotes
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]
        
    return val.strip()

def format_amount(val):
    """
    Cleans and standardizes amount into a 2-decimal string or empty string.
    """
    if val is None:
        return ""
    s = clean_cell(val).replace(",", "").strip()
    if not s:
        return ""
    try:
        amt = float(s)
        return f"{amt:.2f}"
    except ValueError:
        return ""

def parse_date_flexible(date_str):
    """
    Tries multiple date formats commonly seen in Malaysian bank statements.
    Returns datetime object or None.
    """
    clean_d = clean_cell(date_str)
    if not clean_d:
        return None
    
    formats = [
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y %H:%M:%S",
        "%d %b %Y",
        "%d %B %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(clean_d, fmt)
        except ValueError:
            continue
    return None

def detect_statement_period(transactions, fallback_month=None, fallback_year=None):
    """
    Determines From Date and To Date for Bukku template.
    If all transactions are within one month, returns full calendar month: 01/MM/YYYY to LastDay/MM/YYYY.
    Otherwise returns min_date to max_date.
    """
    dates = []
    for tx in transactions:
        dt = parse_date_flexible(tx.get("date", ""))
        if dt:
            dates.append(dt)
            
    if not dates:
        now = datetime.now()
        y = fallback_year or now.year
        m = fallback_month or now.month
        last_day = calendar.monthrange(y, m)[1]
        return f"01/{m:02d}/{y}", f"{last_day:02d}/{m:02d}/{y}"
        
    dates.sort()
    first_dt = dates[0]
    last_dt = dates[-1]
    
    # Check if single calendar month
    if first_dt.year == last_dt.year and first_dt.month == last_dt.month:
        y = first_dt.year
        m = first_dt.month
        last_day = calendar.monthrange(y, m)[1]
        return f"01/{m:02d}/{y}", f"{last_day:02d}/{m:02d}/{y}"
    else:
        return first_dt.strftime("%d/%m/%Y"), last_dt.strftime("%d/%m/%Y")

class StatementParseResult:
    def __init__(self):
        self.bank_name = "Unknown"
        self.account_no = ""
        self.from_date = ""
        self.to_date = ""
        self.closing_balance = ""
        self.transactions = []
        self.total_spent = 0.0
        self.total_received = 0.0
        self.bank_reported_debit = None
        self.bank_reported_credit = None
        self.metadata = {}

    def to_summary_dict(self):
        return {
            "bank_name": self.bank_name,
            "account_no": self.account_no,
            "from_date": self.from_date,
            "to_date": self.to_date,
            "closing_balance": self.closing_balance,
            "transaction_count": len(self.transactions),
            "total_spent": round(self.total_spent, 2),
            "total_received": round(self.total_received, 2),
            "bank_reported_debit": self.bank_reported_debit,
            "bank_reported_credit": self.bank_reported_credit,
            "verification_status": self.get_verification_status()
        }

    def get_verification_status(self):
        issues = []
        if not self.transactions:
            issues.append("No transactions parsed")
        if self.bank_reported_debit is not None:
            if abs(self.total_spent - self.bank_reported_debit) > 0.01:
                issues.append(f"Spent mismatch: Calc {self.total_spent:.2f} != Bank {self.bank_reported_debit:.2f}")
        if self.bank_reported_credit is not None:
            if abs(self.total_received - self.bank_reported_credit) > 0.01:
                issues.append(f"Received mismatch: Calc {self.total_received:.2f} != Bank {self.bank_reported_credit:.2f}")
        return "PASS" if not issues else "; ".join(issues)

class BukkuStatementConverter:
    def __init__(self, fill_empty_description=True, ref_style="standard"):
        """
        fill_empty_description: If true, when Customer/EFT No is blank (e.g. bank fee/profit),
                               fills Description with Transaction Description (e.g. 'CMS SERVICE CHARGE').
        ref_style:
            'standard':
                Ref 1 = Transaction Description (e.g. INW DuitNow Transfer, CDB CS TO IBFTS3)
                Ref 2 = Sender Name / Recipient Name
                Ref 3 = Payment Details
                Ref 4 = Ref/Cheque No
            'party_first':
                Ref 1 = Sender Name / Recipient Name
                Ref 2 = Payment Details
                Ref 3 = Transaction Description
                Ref 4 = Ref/Cheque No
        """
        self.fill_empty_description = fill_empty_description
        self.ref_style = ref_style

    def parse_file(self, filepath):
        """
        Reads CSV file and identifies the appropriate bank parser.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Try reading lines with utf-8, fallback to latin-1 / cp1252
        rows = []
        for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                with open(filepath, "r", encoding=encoding, errors="replace") as f:
                    # Detect delimiter
                    sample = f.read(4096)
                    f.seek(0)
                    delimiter = "\t" if "\t" in sample and sample.count("\t") > sample.count(",") else ","
                    reader = csv.reader(f, delimiter=delimiter)
                    rows = [r for r in reader]
                if rows:
                    break
            except Exception:
                continue

        if not rows:
            raise ValueError(f"Could not read content or empty file: {filepath}")

        # Check if already a Bukku template CSV
        if len(rows) > 5 and clean_cell(rows[0][0]) == "From Date":
            return self._parse_bukku_native(rows)

        # Detect Bank Islam Type A (Web export with header)
        if self._is_bank_islam_type_a(rows):
            return self._parse_bank_islam_type_a(rows)

        # Detect Bank Islam Type B (Raw 13-col transaction lines)
        if self._is_bank_islam_type_b(rows):
            return self._parse_bank_islam_type_b(rows)

        # Fallback to smart generic parser
        return self._parse_generic_csv(rows)

    def _is_bank_islam_type_a(self, rows):
        has_title = False
        has_account = False
        has_header = False
        for idx, row in enumerate(rows[:15]):
            cleaned = [clean_cell(c) for c in row if c]
            row_text = " ".join(cleaned).lower()
            if "transaction history" in row_text:
                has_title = True
            if "account number" in row_text:
                has_account = True
            if "transaction date" in row_text and "customer/ eft no" in row_text:
                has_header = True
        return (has_title and has_account) or has_header

    def _is_bank_islam_type_b(self, rows):
        # Look for raw rows where row[2] looks like Bank Islam account (14 digits)
        # e.g. 12029010086201
        for row in rows[:5]:
            cleaned = [clean_cell(c) for c in row]
            if len(cleaned) >= 11:
                # col 1 date, col 2 account no
                d = parse_date_flexible(cleaned[1])
                acct = cleaned[2].replace("-", "")
                if d and (acct.isdigit() and len(acct) >= 10):
                    return True
        return False

    def _parse_bank_islam_type_a(self, rows):
        res = StatementParseResult()
        res.bank_name = "Bank Islam (Malaysia)"
        
        header_idx = -1
        for idx, row in enumerate(rows[:15]):
            cleaned = [clean_cell(c) for c in row]
            first_val = next((c for c in cleaned if c), "")
            if "account number" in first_val.lower():
                for c in cleaned[1:]:
                    if c:
                        res.account_no = c
                        break
            elif "date" == first_val.lower() and idx < 7:
                for c in cleaned[1:]:
                    if c:
                        res.metadata["statement_exported_date"] = c
                        break
            elif len(cleaned) >= 2 and cleaned[0].lower().startswith("no") and "transaction date" in cleaned[1].lower():
                header_idx = idx

        if header_idx == -1:
            # Fallback search for table header anywhere
            for idx, row in enumerate(rows):
                cleaned = [clean_cell(c).lower() for c in row]
                if any("transaction date" in c for c in cleaned):
                    header_idx = idx
                    break

        if header_idx == -1:
            raise ValueError("Could not find table header in Bank Islam statement")

        data_rows = rows[header_idx + 1:]
        raw_txns = []
        last_balance = ""

        for row in data_rows:
            cleaned = [clean_cell(c) for c in row]
            if not any(cleaned):
                continue

            row_str = " ".join(cleaned)
            # Detect footer totals e.g. Total Amount: 20967.04 Total Amount: 58108.93
            if "total amount:" in row_str.lower():
                totals = re.findall(r"Total Amount:\s*([\d,\.]+)", row_str, re.IGNORECASE)
                if len(totals) >= 2:
                    try:
                        res.bank_reported_debit = float(totals[0].replace(",", ""))
                        res.bank_reported_credit = float(totals[1].replace(",", ""))
                    except ValueError:
                        pass
                continue

            if len(cleaned) < 10:
                continue

            date_val = cleaned[1]
            if not date_val:
                continue

            # Bank Islam Type A columns:
            # 0: No.
            # 1: Transaction Date
            # 2: Customer/ EFT No
            # 3: Transaction Code
            # 4: Transaction Description
            # 5: Ref/ Cheque No
            # 6: Servicing Branch
            # 7: Debit Amount
            # 8: Credit Amount
            # 9: Balance
            # 10: Sender Name/ Recipient Name (if available)
            # 11: Payment Details (if available)

            customer_eft = cleaned[2]
            txn_desc = cleaned[4]
            ref_cheque = cleaned[5] if len(cleaned) > 5 else ""
            debit_fmt = format_amount(cleaned[7])
            credit_fmt = format_amount(cleaned[8])
            balance_str = cleaned[9].replace(",", "").rstrip("+").rstrip("-")
            sender_recipient = cleaned[10] if len(cleaned) > 10 else ""
            payment_details = cleaned[11] if len(cleaned) > 11 else ""

            if balance_str:
                last_balance = balance_str

            debit_float = float(debit_fmt) if debit_fmt else 0.0
            credit_float = float(credit_fmt) if credit_fmt else 0.0
            res.total_spent += debit_float
            res.total_received += credit_float

            # Determine Description
            desc = customer_eft
            if not desc and self.fill_empty_description:
                desc = txn_desc

            # Assign Refs based on ref_style
            if self.ref_style == "party_first":
                ref1 = sender_recipient
                ref2 = payment_details
                ref3 = txn_desc
                ref4 = ref_cheque
            else: # standard
                ref1 = txn_desc
                ref2 = sender_recipient
                ref3 = payment_details
                ref4 = ref_cheque

            raw_txns.append({
                "date": date_val,
                "description": desc,
                "spent": debit_fmt,
                "received": credit_fmt,
                "ref1": ref1,
                "ref2": ref2,
                "ref3": ref3,
                "ref4": ref4,
                "balance": balance_str
            })

        res.transactions = raw_txns
        res.closing_balance = last_balance
        res.from_date, res.to_date = detect_statement_period(raw_txns)
        return res

    def _parse_bank_islam_type_b(self, rows):
        res = StatementParseResult()
        res.bank_name = "Bank Islam (Malaysia - Raw Format)"

        raw_txns = []
        last_balance = ""

        for row in rows:
            cleaned = [clean_cell(c) for c in row]
            if len(cleaned) < 10:
                continue

            # Col 0: No
            # Col 1: Date
            # Col 2: Account Number
            # Col 3: Transaction Code
            # Col 4: Transaction Description
            # Col 5: Ref / Cheque No
            # Col 6: Servicing Branch
            # Col 7: Debit Amount
            # Col 8: Credit Amount
            # Col 9: Balance
            # Col 10: Customer / EFT No
            # Col 11: Payment Details
            # Col 12: Sender Name / Recipient Name

            if not res.account_no and len(cleaned) > 2:
                res.account_no = cleaned[2]

            date_val = cleaned[1]
            if not parse_date_flexible(date_val):
                continue

            txn_desc = cleaned[4] if len(cleaned) > 4 else ""
            ref_cheque = cleaned[5] if len(cleaned) > 5 else ""
            debit_fmt = format_amount(cleaned[7]) if len(cleaned) > 7 else ""
            credit_fmt = format_amount(cleaned[8]) if len(cleaned) > 8 else ""
            balance_str = cleaned[9].replace(",", "").rstrip("+").rstrip("-") if len(cleaned) > 9 else ""
            customer_eft = cleaned[10] if len(cleaned) > 10 else ""
            payment_details = cleaned[11] if len(cleaned) > 11 else ""
            sender_recipient = cleaned[12] if len(cleaned) > 12 else ""

            if balance_str:
                last_balance = balance_str

            debit_float = float(debit_fmt) if debit_fmt else 0.0
            credit_float = float(credit_fmt) if credit_fmt else 0.0
            res.total_spent += debit_float
            res.total_received += credit_float

            desc = customer_eft
            if not desc and self.fill_empty_description:
                desc = txn_desc

            if self.ref_style == "party_first":
                ref1 = sender_recipient
                ref2 = payment_details
                ref3 = txn_desc
                ref4 = ref_cheque
            else:
                ref1 = txn_desc
                ref2 = sender_recipient
                ref3 = payment_details
                ref4 = ref_cheque

            raw_txns.append({
                "date": date_val,
                "description": desc,
                "spent": debit_fmt,
                "received": credit_fmt,
                "ref1": ref1,
                "ref2": ref2,
                "ref3": ref3,
                "ref4": ref4,
                "balance": balance_str
            })

        res.transactions = raw_txns
        res.closing_balance = last_balance
        res.from_date, res.to_date = detect_statement_period(raw_txns)
        return res

    def _parse_generic_csv(self, rows):
        """
        Smart generic parser for arbitrary bank statement CSVs.
        Finds header by fuzzy matching column names.
        """
        res = StatementParseResult()
        res.bank_name = "Generic Bank Statement"

        header_idx = -1
        col_map = {}

        # Look for header line
        for idx, row in enumerate(rows[:25]):
            cleaned = [clean_cell(c).lower() for c in row]
            date_col = None
            desc_col = None
            spent_col = None
            received_col = None
            amount_col = None
            balance_col = None
            ref_cols = []

            for col_i, col_name in enumerate(cleaned):
                if not col_name:
                    continue
                if any(k in col_name for k in ["date", "tarikh", "txn date", "posting date"]):
                    date_col = col_i
                elif any(k in col_name for k in ["description", "keterangan", "details", "particulars", "narration", "payee"]):
                    if desc_col is None:
                        desc_col = col_i
                    else:
                        ref_cols.append(col_i)
                elif any(k in col_name for k in ["spent", "debit", "withdrawal", "keluar", "dr", "outflow"]):
                    spent_col = col_i
                elif any(k in col_name for k in ["received", "credit", "deposit", "masuk", "cr", "inflow"]):
                    received_col = col_i
                elif "amount" in col_name or "jumlah" in col_name:
                    amount_col = col_i
                elif "balance" in col_name or "baki" in col_name:
                    balance_col = col_i
                elif any(k in col_name for k in ["ref", "cheque", "check", "reference", "party"]):
                    ref_cols.append(col_i)

            if date_col is not None and (desc_col is not None or len(cleaned) >= 3) and (spent_col is not None or amount_col is not None or received_col is not None):
                header_idx = idx
                col_map = {
                    "date": date_col,
                    "desc": desc_col,
                    "spent": spent_col,
                    "received": received_col,
                    "amount": amount_col,
                    "balance": balance_col,
                    "refs": ref_cols
                }
                break

        if header_idx == -1:
            raise ValueError("Could not recognize bank statement column headers in CSV file.")

        raw_txns = []
        last_balance = ""

        for row in rows[header_idx + 1:]:
            cleaned = [clean_cell(c) for c in row]
            if not any(cleaned):
                continue

            date_idx = col_map.get("date")
            if date_idx is None or date_idx >= len(cleaned):
                continue
            date_str = cleaned[date_idx]
            if not parse_date_flexible(date_str):
                continue

            desc_idx = col_map.get("desc")
            desc = cleaned[desc_idx] if desc_idx is not None and desc_idx < len(cleaned) else ""

            # Amounts
            debit_fmt = ""
            credit_fmt = ""
            spent_idx = col_map.get("spent")
            received_idx = col_map.get("received")
            amount_idx = col_map.get("amount")

            if spent_idx is not None and spent_idx < len(cleaned):
                debit_fmt = format_amount(cleaned[spent_idx])
            if received_idx is not None and received_idx < len(cleaned):
                credit_fmt = format_amount(cleaned[received_idx])

            # If single amount column
            if not debit_fmt and not credit_fmt and amount_idx is not None and amount_idx < len(cleaned):
                raw_amt = clean_cell(cleaned[amount_idx]).replace(",", "")
                try:
                    val = float(raw_amt)
                    if val < 0:
                        debit_fmt = f"{abs(val):.2f}"
                    else:
                        credit_fmt = f"{val:.2f}"
                except ValueError:
                    pass

            bal_idx = col_map.get("balance")
            if bal_idx is not None and bal_idx < len(cleaned):
                b_str = cleaned[bal_idx].replace(",", "").rstrip("+").rstrip("-")
                if b_str:
                    last_balance = b_str

            refs = []
            for r_idx in col_map.get("refs", []):
                if r_idx < len(cleaned) and cleaned[r_idx]:
                    refs.append(cleaned[r_idx])

            ref1 = refs[0] if len(refs) > 0 else ""
            ref2 = refs[1] if len(refs) > 1 else ""
            ref3 = refs[2] if len(refs) > 2 else ""
            ref4 = refs[3] if len(refs) > 3 else ""

            debit_float = float(debit_fmt) if debit_fmt else 0.0
            credit_float = float(credit_fmt) if credit_fmt else 0.0
            res.total_spent += debit_float
            res.total_received += credit_float

            raw_txns.append({
                "date": date_str,
                "description": desc,
                "spent": debit_fmt,
                "received": credit_fmt,
                "ref1": ref1,
                "ref2": ref2,
                "ref3": ref3,
                "ref4": ref4,
                "balance": last_balance
            })

        res.transactions = raw_txns
        res.closing_balance = last_balance
        res.from_date, res.to_date = detect_statement_period(raw_txns)
        return res

    def _parse_bukku_native(self, rows):
        """
        Parses an existing Bukku CSV template file.
        """
        res = StatementParseResult()
        res.bank_name = "Bukku Native Template"
        
        for idx in range(min(5, len(rows))):
            r = [clean_cell(c) for c in rows[idx]]
            if len(r) >= 2:
                key = r[0].lower()
                val = r[1]
                if "from date" in key:
                    res.from_date = val
                elif "to date" in key:
                    res.to_date = val
                elif "account no" in key:
                    res.account_no = val
                elif "closing balance" in key:
                    res.closing_balance = val

        header_idx = -1
        for idx, row in enumerate(rows[:10]):
            cleaned = [clean_cell(c).lower() for c in row]
            if "date" in cleaned and "spent" in cleaned and "received" in cleaned:
                header_idx = idx
                break

        if header_idx != -1:
            for row in rows[header_idx + 1:]:
                c = [clean_cell(cell) for cell in row]
                if not any(c):
                    continue
                d = c[0]
                desc = c[1] if len(c) > 1 else ""
                spent = format_amount(c[2]) if len(c) > 2 else ""
                rcvd = format_amount(c[3]) if len(c) > 3 else ""
                r1 = c[4] if len(c) > 4 else ""
                r2 = c[5] if len(c) > 5 else ""
                r3 = c[6] if len(c) > 6 else ""
                r4 = c[7] if len(c) > 7 else ""

                s_fl = float(spent) if spent else 0.0
                r_fl = float(rcvd) if rcvd else 0.0
                res.total_spent += s_fl
                res.total_received += r_fl

                res.transactions.append({
                    "date": d,
                    "description": desc,
                    "spent": spent,
                    "received": rcvd,
                    "ref1": r1,
                    "ref2": r2,
                    "ref3": r3,
                    "ref4": r4
                })

        return res

    def export_bukku_csv(self, parsed_result, output_filepath):
        """
        Exports the parsed statement result into Bukku-compliant CSV format.
        """
        output_filepath = Path(output_filepath)
        output_filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(output_filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Row 1 to 4: Metadata
            writer.writerow(["From Date", parsed_result.from_date, "", "", "", "", "", ""])
            writer.writerow(["To Date", parsed_result.to_date, "", "", "", "", "", ""])
            writer.writerow(["Account No", parsed_result.account_no, "", "", "", "", "", ""])
            writer.writerow(["Closing Balance", parsed_result.closing_balance, "", "", "", "", "", ""])
            # Row 5: Empty line
            writer.writerow(["", "", "", "", "", "", "", ""])
            # Row 6: Bukku Columns
            writer.writerow(BUKKU_COLUMNS)
            # Row 7+: Transactions
            for tx in parsed_result.transactions:
                writer.writerow([
                    tx.get("date", ""),
                    tx.get("description", ""),
                    tx.get("spent", ""),
                    tx.get("received", ""),
                    tx.get("ref1", ""),
                    tx.get("ref2", ""),
                    tx.get("ref3", ""),
                    tx.get("ref4", "")
                ])

        return str(output_filepath)

    def export_bukku_xlsx(self, parsed_result, output_filepath):
        """
        Exports the parsed statement result into Bukku-compliant Excel (.xlsx) format.
        Requires openpyxl.
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            raise ImportError("openpyxl is required for Excel export. Please install openpyxl or export as CSV.")

        output_filepath = Path(output_filepath)
        output_filepath.parent.mkdir(parents=True, exist_ok=True)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Bank Statement"

        # Metadata rows
        meta_data = [
            ("From Date", parsed_result.from_date),
            ("To Date", parsed_result.to_date),
            ("Account No", parsed_result.account_no),
            ("Closing Balance", parsed_result.closing_balance)
        ]

        bold_font = Font(name="Arial", size=10, bold=True)
        regular_font = Font(name="Arial", size=10)
        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")

        for r_i, (k, v) in enumerate(meta_data, start=1):
            ws.cell(row=r_i, column=1, value=k).font = bold_font
            ws.cell(row=r_i, column=2, value=v).font = regular_font

        # Row 5 is blank

        # Row 6: Column Headers
        for c_i, col_name in enumerate(BUKKU_COLUMNS, start=1):
            cell = ws.cell(row=6, column=c_i, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center" if c_i in [1, 3, 4] else "left")

        # Row 7+: Transactions
        for row_idx, tx in enumerate(parsed_result.transactions, start=7):
            ws.cell(row=row_idx, column=1, value=tx.get("date", "")).font = regular_font
            ws.cell(row=row_idx, column=2, value=tx.get("description", "")).font = regular_font
            
            # Spent
            spent_str = tx.get("spent", "")
            cell_spent = ws.cell(row=row_idx, column=3, value=float(spent_str) if spent_str else "")
            cell_spent.font = regular_font
            if spent_str:
                cell_spent.number_format = '#,##0.00'

            # Received
            rcvd_str = tx.get("received", "")
            cell_rcvd = ws.cell(row=row_idx, column=4, value=float(rcvd_str) if rcvd_str else "")
            cell_rcvd.font = regular_font
            if rcvd_str:
                cell_rcvd.number_format = '#,##0.00'

            ws.cell(row=row_idx, column=5, value=tx.get("ref1", "")).font = regular_font
            ws.cell(row=row_idx, column=6, value=tx.get("ref2", "")).font = regular_font
            ws.cell(row=row_idx, column=7, value=tx.get("ref3", "")).font = regular_font
            ws.cell(row=row_idx, column=8, value=tx.get("ref4", "")).font = regular_font

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(output_filepath)
        return str(output_filepath)
