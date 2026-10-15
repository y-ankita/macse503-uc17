
from getpass import getpass
import os

import pandas as pd
from sqlalchemy import URL, create_engine

password = getpass("Enter your PostgreSQL password: ")

url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="EHCMDP_DB",
)

engine = create_engine(url)

tables = [
    "access_clean",
    "attendance_clean",
    "hrms_clean",
    "leave_clean",
    "performance_clean",
]

table_summary = []
missing_report = []

try:
    for table in tables:
        print(f"Validating: {table}")

        df = pd.read_sql(
            f'SELECT * FROM cleaned."{table}"',
            engine,
        )

        rows = len(df)
        duplicates = int(df.duplicated().sum())
        empty_rows = int(df.isna().all(axis=1).sum())

        table_summary.append({
            "table_name": table,
            "rows": rows,
            "columns": len(df.columns),
            "exact_duplicate_rows": duplicates,
            "fully_empty_rows": empty_rows,
            "rows_with_missing_values": int(
                df.isna().any(axis=1).sum()
            ),
        })

        for column in df.columns:
            missing = int(df[column].isna().sum())

            missing_report.append({
                "table_name": table,
                "column_name": column,
                "missing_count": missing,
                "missing_percentage": round(
                    missing / rows * 100, 2
                ) if rows else 0,
            })

    output_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data_quality_output",
    )
    os.makedirs(output_folder, exist_ok=True)

    output_file = os.path.join(
        output_folder,
        "Cleaned_Data_Validation.xlsx",
    )

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        pd.DataFrame(table_summary).to_excel(
            writer,
            sheet_name="Table Validation",
            index=False,
        )

        pd.DataFrame(missing_report).to_excel(
            writer,
            sheet_name="Missing Values",
            index=False,
        )

    print("\nVALIDATION SUMMARY")
    print(pd.DataFrame(table_summary).to_string(index=False))
    print(f"\nReport saved to: {output_file}")

finally:
    engine.dispose()