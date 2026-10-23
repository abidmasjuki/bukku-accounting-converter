"""
Bukku Accounting Converter - Command Line Interface
Version: 1.0.0
"""

import argparse
import sys
import os
import glob
from pathlib import Path
from config import VERSION, APP_NAME, DEFAULT_TARGET_FOLDER
from converter import BukkuStatementConverter

def get_output_filename(parsed_res, input_path, extension="csv"):
    """
    Generates a standardized Bukku template filename such as:
    Bukku-statement-template (Ogos 2026).csv
    """
    stem = input_path.stem
    
    # Check if month & year can be derived from From Date e.g. 01/08/2026
    month_names_en = {
        1: "Jan", 2: "Feb", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "Ogos", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    
    label = ""
    if parsed_res.from_date:
        if "/" in parsed_res.from_date:
            parts = parsed_res.from_date.split("/")
            if len(parts) == 3:
                m = int(parts[1])
                y = parts[2]
                label = f"{month_names_en.get(m, str(m))} {y}"
        elif "-" in parsed_res.from_date:
            parts = parsed_res.from_date.split("-")
            if len(parts) == 3:
                m = int(parts[1])
                y = parts[0]
                label = f"{month_names_en.get(m, str(m))} {y}"

    if not label:
        label = stem

    return f"Bukku-statement-template ({label}).{extension}"

def print_banner():
    print("=" * 70)
    print(f"  {APP_NAME} (v{VERSION})")
    print("  Converts Bank Statements to Bukku-compliant CSV/Excel Templates")
    print("=" * 70)

def convert_single_file(converter, input_path, output_dir=None, export_xlsx=True, custom_out_name=None):
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}")
        return False

    out_folder = Path(output_dir) if output_dir else input_path.parent

    try:
        parsed = converter.parse_file(input_path)
        summary = parsed.to_summary_dict()

        # CSV output
        csv_name = custom_out_name or get_output_filename(parsed, input_path, "csv")
        csv_path = out_folder / csv_name
        converter.export_bukku_csv(parsed, csv_path)

        # XLSX output
        xlsx_path = None
        if export_xlsx:
            xlsx_name = (custom_out_name.rsplit(".", 1)[0] + ".xlsx") if custom_out_name else get_output_filename(parsed, input_path, "xlsx")
            xlsx_path = out_folder / xlsx_name
            try:
                converter.export_bukku_xlsx(parsed, xlsx_path)
            except Exception as e:
                print(f"[WARNING] Could not export Excel: {e}")

        # Verification output
        status = summary["verification_status"]
        status_icon = "OK" if status == "PASS" else "WARN"
        print(f"\n[{status_icon}] Converted: {input_path.name}")
        print(f"    - Bank Detected     : {summary['bank_name']}")
        print(f"    - Account No        : {summary['account_no']}")
        print(f"    - Statement Period  : {summary['from_date']} to {summary['to_date']}")
        print(f"    - Transactions      : {summary['transaction_count']}")
        print(f"    - Total Spent (Dr)  : RM {summary['total_spent']:,.2f}")
        print(f"    - Total Received(Cr): RM {summary['total_received']:,.2f}")
        print(f"    - Closing Balance   : RM {float(summary['closing_balance'] or 0):,.2f}")
        print(f"    - Verification      : {status}")
        print(f"    -> Output CSV       : {csv_path}")
        if xlsx_path and xlsx_path.exists():
            print(f"    -> Output Excel     : {xlsx_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to convert {input_path.name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{VERSION}")
    parser.add_argument("-i", "--input", help="Path to input statement CSV file")
    parser.add_argument("-d", "--dir", help="Directory containing statement CSV files to convert in batch")
    parser.add_argument("-o", "--output-dir", help="Destination folder for Bukku templates (defaults to input folder)")
    parser.add_argument("--out-name", help="Custom output filename (e.g. Bukku-statement-template (Ogos 2026).csv)")
    parser.add_argument("--no-xlsx", action="store_true", help="Skip creating .xlsx Excel version")
    parser.add_argument("--no-fill-empty-desc", action="store_true", help="Leave Description blank if Customer/EFT No is empty")
    parser.add_argument("--ref-style", choices=["standard", "party_first"], default="standard",
                        help="Reference column ordering style (default: standard)")
    parser.add_argument("--date-format", choices=["ymd", "dmy"], default="ymd",
                        help="Transaction date format: 'ymd' (YYYY-MM-DD, Bukku validator compliant) or 'dmy' (DD/MM/YYYY). Without timestamp. Default: ymd")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    print_banner()

    converter = BukkuStatementConverter(
        fill_empty_description=not args.no_fill_empty_desc,
        ref_style=args.ref_style,
        date_format=args.date_format
    )

    if args.input:
        convert_single_file(
            converter,
            args.input,
            output_dir=args.output_dir,
            export_xlsx=not args.no_xlsx,
            custom_out_name=args.out_name
        )
    elif args.dir:
        folder = Path(args.dir)
        if not folder.exists():
            print(f"[ERROR] Directory does not exist: {folder}")
            sys.exit(1)
        
        csv_files = sorted(list(folder.glob("*.csv")))
        # Filter out already converted Bukku templates
        input_files = [f for f in csv_files if "bukku" not in f.name.lower()]
        
        print(f"Found {len(input_files)} bank statement CSVs in {folder}")
        success_count = 0
        for f in input_files:
            if convert_single_file(converter, f, output_dir=args.output_dir, export_xlsx=not args.no_xlsx):
                success_count += 1
        print(f"\n[DONE] Successfully converted {success_count} / {len(input_files)} statements.")
    else:
        # Prompt user for input file or guide them to specify --input or use GUI
        print("[INFO] No input file specified.")
        print("Usage:")
        print('  python cli.py -i "path\\to\\bank_statement.csv"')
        print('  python cli.py -d "path\\to\\folder_with_csvs"')
        print('  python gui.py   (to open the interactive visual tool)')
        print("\nOr drag and drop any bank statement CSV onto convert_statement.bat")

if __name__ == "__main__":
    main()
