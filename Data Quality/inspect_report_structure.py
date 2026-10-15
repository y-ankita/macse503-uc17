
from pathlib import Path
import pandas as pd

base = Path(__file__).resolve().parent

reports = [
    base / "SPRINT 2" / "EHCMDP_Data_Profiling_Report.xlsx",
    base / "SPRINT 2" / "EHCMDP_Data_Quality_Analysis.xlsx",
    base / "SPRINT 2" / "Cleaned_Data_Validation.xlsx",
]

for file in reports:
    print(f"\n{'=' * 65}")
    print("REPORT:", file.name)

    if not file.exists():
        print("FILE NOT FOUND:", file)
        continue

    workbook = pd.ExcelFile(file)
    for sheet in workbook.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet)
        print(f"\nSheet: {sheet}")
        print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
        print("Column names:", df.columns.tolist())

print("\nInspection complete. No files or database tables modified.")