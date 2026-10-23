"""
Bukku Accounting Converter - Desktop GUI
A modern Tkinter interface for converting bank statement CSVs into Bukku-compliant templates.
Version: 1.0.0
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from config import VERSION, APP_NAME, DEFAULT_TARGET_FOLDER, BUKKU_COLUMNS
from converter import BukkuStatementConverter
from cli import get_output_filename

class BukkuConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - v{VERSION}")
        self.root.geometry("1020x680")
        self.root.minsize(850, 550)

        # Apply system styling
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # State variables
        self.current_file = None
        self.parsed_res = None
        self.date_format_var = tk.StringVar(value="ymd")
        self.converter = BukkuStatementConverter(fill_empty_description=True, ref_style="standard", date_format="ymd")

        self.setup_ui()

    def setup_ui(self):
        # Header banner
        header_frame = tk.Frame(self.root, bg="#1E3A8A", height=65)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="Bukku Accounting Statement Converter",
            font=("Arial", 16, "bold"),
            fg="#FFFFFF",
            bg="#1E3A8A"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=12)

        ver_label = tk.Label(
            header_frame,
            text=f"v{VERSION}  |  Bank Islam & Multi-Bank Support",
            font=("Arial", 10),
            fg="#93C5FD",
            bg="#1E3A8A"
        )
        ver_label.pack(side=tk.RIGHT, padx=20, pady=18)

        # Top Control Frame (File Selection & Settings)
        controls_frame = ttk.LabelFrame(self.root, text=" 1. Select Bank Statement CSV ", padding=10)
        controls_frame.pack(fill=tk.X, padx=15, pady=10)

        file_btn_frame = ttk.Frame(controls_frame)
        file_btn_frame.pack(fill=tk.X)

        self.btn_browse = ttk.Button(file_btn_frame, text="Browse CSV File...", command=self.browse_file)
        self.btn_browse.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_quick_ogos = ttk.Button(
            file_btn_frame,
            text="Quick Load: Ogos 2026",
            command=lambda: self.load_preset_file("Ogos 2026 transaction_history.csv")
        )
        self.btn_quick_ogos.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_quick_sept = ttk.Button(
            file_btn_frame,
            text="Quick Load: Sept 2026",
            command=lambda: self.load_preset_file("September 2026 transaction_history.csv")
        )
        self.btn_quick_sept.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_batch = ttk.Button(file_btn_frame, text="Batch Convert Folder...", command=self.batch_convert)
        self.btn_batch.pack(side=tk.RIGHT)

        self.lbl_selected_file = ttk.Label(controls_frame, text="No file selected.", foreground="#4B5563")
        self.lbl_selected_file.pack(fill=tk.X, pady=(8, 4))

        opts_frame = ttk.Frame(controls_frame)
        opts_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(opts_frame, text="Transaction Date Format:").pack(side=tk.LEFT, padx=(0, 10))
        rb_ymd = ttk.Radiobutton(
            opts_frame,
            text="YYYY-MM-DD (Bukku Y-m-d Required, No Timestamp)",
            variable=self.date_format_var,
            value="ymd",
            command=self.on_date_format_change
        )
        rb_ymd.pack(side=tk.LEFT, padx=(0, 15))
        rb_dmy = ttk.Radiobutton(
            opts_frame,
            text="DD/MM/YYYY (Template Format, No Timestamp)",
            variable=self.date_format_var,
            value="dmy",
            command=self.on_date_format_change
        )
        rb_dmy.pack(side=tk.LEFT)

        # Statistics Summary Frame
        self.stats_frame = ttk.LabelFrame(self.root, text=" 2. Statement & Reconciliation Summary ", padding=10)
        self.stats_frame.pack(fill=tk.X, padx=15, pady=5)

        self.stats_labels = {}
        fields = [
            ("Bank", "bank_name"),
            ("Account No", "account_no"),
            ("Period", "period"),
            ("Total Transactions", "txn_count"),
            ("Total Spent (Dr)", "spent"),
            ("Total Received (Cr)", "received"),
            ("Closing Balance", "closing_bal"),
            ("Reconciliation", "audit_status")
        ]

        # 2 rows of 4 columns
        for idx, (label, key) in enumerate(fields):
            row = idx // 4
            col = (idx % 4) * 2
            lbl = ttk.Label(self.stats_frame, text=f"{label}:", font=("Arial", 9, "bold"))
            lbl.grid(row=row, column=col, sticky="w", padx=(10, 4), pady=4)
            val = ttk.Label(self.stats_frame, text="-", font=("Arial", 9))
            val.grid(row=row, column=col + 1, sticky="w", padx=(0, 15), pady=4)
            self.stats_labels[key] = val

        # Preview Table Frame
        preview_frame = ttk.LabelFrame(self.root, text=" 3. Bukku Template Preview (Live Data) ", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("date", "desc", "spent", "received", "ref1", "ref2", "ref3", "ref4")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=10)

        col_widths = {
            "date": 140,
            "desc": 200,
            "spent": 90,
            "received": 90,
            "ref1": 150,
            "ref2": 170,
            "ref3": 130,
            "ref4": 90
        }
        for col, title in zip(columns, BUKKU_COLUMNS):
            self.tree.heading(col, text=title)
            align = "e" if col in ["spent", "received"] else ("center" if col == "date" else "w")
            self.tree.column(col, width=col_widths.get(col, 100), anchor=align)

        # Scrollbars
        y_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Bottom Action Bar
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill=tk.X, padx=15, pady=5)

        self.btn_export = ttk.Button(
            action_frame,
            text="Convert & Save Bukku Template (CSV + Excel)",
            command=self.export_current,
            state=tk.DISABLED
        )
        self.btn_export.pack(side=tk.LEFT, padx=(0, 10), ipady=5)

        self.btn_open_folder = ttk.Button(
            action_frame,
            text="Open Folder in Explorer",
            command=self.open_output_folder
        )
        self.btn_open_folder.pack(side=tk.LEFT, ipady=5)

        self.lbl_status = ttk.Label(action_frame, text="Ready.", font=("Arial", 9, "italic"), foreground="#4B5563")
        self.lbl_status.pack(side=tk.RIGHT, pady=5)

    def load_preset_file(self, filename):
        target = Path(DEFAULT_TARGET_FOLDER) / filename
        if target.exists():
            self.process_file(target)
        else:
            messagebox.showwarning("File Not Found", f"Could not find:\n{target}")

    def browse_file(self):
        initial_dir = DEFAULT_TARGET_FOLDER if os.path.exists(DEFAULT_TARGET_FOLDER) else os.getcwd()
        file_path = filedialog.askopenfilename(
            title="Select Bank Statement CSV",
            initialdir=initial_dir,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.process_file(Path(file_path))

    def on_date_format_change(self):
        self.converter.date_format = self.date_format_var.get()
        if self.current_file:
            self.process_file(self.current_file)

    def process_file(self, path):
        self.converter.date_format = self.date_format_var.get()
        self.current_file = path
        self.lbl_selected_file.config(text=f"Selected: {path}", foreground="#1F2937")
        self.lbl_status.config(text="Parsing statement...", foreground="#2563EB")
        self.root.update_idletasks()

        try:
            self.parsed_res = self.converter.parse_file(path)
            self.update_summary()
            self.populate_table()
            self.btn_export.config(state=tk.NORMAL)
            self.lbl_status.config(text="Ready to export.", foreground="#059669")
        except Exception as e:
            self.btn_export.config(state=tk.DISABLED)
            self.lbl_status.config(text=f"Error: {e}", foreground="#DC2626")
            messagebox.showerror("Parsing Error", f"Failed to parse statement:\n{e}")

    def update_summary(self):
        if not self.parsed_res:
            return
        summary = self.parsed_res.to_summary_dict()
        self.stats_labels["bank_name"].config(text=summary["bank_name"])
        self.stats_labels["account_no"].config(text=summary["account_no"] or "(None)")
        self.stats_labels["period"].config(text=f"{summary['from_date']} - {summary['to_date']}")
        self.stats_labels["txn_count"].config(text=str(summary["transaction_count"]))
        self.stats_labels["spent"].config(text=f"RM {summary['total_spent']:,.2f}")
        self.stats_labels["received"].config(text=f"RM {summary['total_received']:,.2f}")
        bal = float(summary['closing_balance']) if summary['closing_balance'] else 0.0
        self.stats_labels["closing_bal"].config(text=f"RM {bal:,.2f}")
        
        status = summary["verification_status"]
        status_color = "#059669" if status == "PASS" else "#DC2626"
        self.stats_labels["audit_status"].config(text=status, foreground=status_color)

    def populate_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.parsed_res:
            return

        for tx in self.parsed_res.transactions:
            self.tree.insert("", tk.END, values=(
                tx.get("date", ""),
                tx.get("description", ""),
                tx.get("spent", ""),
                tx.get("received", ""),
                tx.get("ref1", ""),
                tx.get("ref2", ""),
                tx.get("ref3", ""),
                tx.get("ref4", "")
            ))

    def export_current(self):
        if not self.parsed_res or not self.current_file:
            return

        out_dir = self.current_file.parent
        csv_name = get_output_filename(self.parsed_res, self.current_file, "csv")
        xlsx_name = get_output_filename(self.parsed_res, self.current_file, "xlsx")
        csv_path = out_dir / csv_name
        xlsx_path = out_dir / xlsx_name

        try:
            self.converter.export_bukku_csv(self.parsed_res, csv_path)
            try:
                self.converter.export_bukku_xlsx(self.parsed_res, xlsx_path)
            except Exception:
                pass

            self.lbl_status.config(text=f"Successfully exported: {csv_name}", foreground="#059669")
            messagebox.showinfo(
                "Export Successful",
                f"Bukku template files generated successfully!\n\nCSV:\n{csv_path}\n\nExcel:\n{xlsx_path}"
            )
        except Exception as e:
            self.lbl_status.config(text=f"Export failed: {e}", foreground="#DC2626")
            messagebox.showerror("Export Failed", f"Could not save files:\n{e}")

    def batch_convert(self):
        initial_dir = DEFAULT_TARGET_FOLDER if os.path.exists(DEFAULT_TARGET_FOLDER) else os.getcwd()
        folder = filedialog.askdirectory(title="Select Folder with Statement CSVs", initialdir=initial_dir)
        if not folder:
            return

        folder_path = Path(folder)
        csv_files = [f for f in folder_path.glob("*.csv") if "bukku" not in f.name.lower()]
        if not csv_files:
            messagebox.showinfo("No Files", "No bank statement CSV files found in this folder.")
            return

        count = 0
        for f in csv_files:
            try:
                res = self.converter.parse_file(f)
                c_name = get_output_filename(res, f, "csv")
                x_name = get_output_filename(res, f, "xlsx")
                self.converter.export_bukku_csv(res, folder_path / c_name)
                try:
                    self.converter.export_bukku_xlsx(res, folder_path / x_name)
                except Exception:
                    pass
                count += 1
            except Exception:
                continue

        messagebox.showinfo("Batch Complete", f"Successfully converted {count} statement(s) in:\n{folder}")

    def open_output_folder(self):
        folder = self.current_file.parent if self.current_file else Path(DEFAULT_TARGET_FOLDER)
        if folder.exists():
            os.startfile(folder)
        else:
            messagebox.showwarning("Folder Not Found", f"Folder does not exist:\n{folder}")

def launch_gui():
    root = tk.Tk()
    app = BukkuConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
