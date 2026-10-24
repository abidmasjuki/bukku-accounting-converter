"""
Bukku Accounting Converter - Configuration & Constants
Version: 1.2.0
"""

VERSION = "1.2.0"
APP_NAME = "Bukku Accounting Statement Converter"

# Bukku CSV Standard Headers
BUKKU_METADATA_KEYS = [
    "From Date",
    "To Date",
    "Account No",
    "Closing Balance"
]

BUKKU_COLUMNS = [
    "Date",
    "Description",
    "Spent",
    "Received",
    "Ref 1",
    "Ref 2",
    "Ref 3",
    "Ref 4"
]

# Malay month name mapping for filenames and date parsing
MALAY_MONTHS = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "mac": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5, "may": 5,
    "jun": 6, "june": 6,
    "julai": 7, "july": 7,
    "ogos": 8, "aug": 8, "august": 8,
    "september": 9, "sept": 9, "sep": 9,
    "oktober": 10, "okt": 10, "oct": 10, "october": 10,
    "november": 11, "nov": 11,
    "disember": 12, "dis": 12, "dec": 12, "december": 12
}

DEFAULT_TARGET_FOLDER = r"G:\My Drive\RPWP HEALTHCARE MASTER FOLDER\HEARING CENTRE\ACCOUNTING\BUKKU"
