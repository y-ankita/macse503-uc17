import os
from getpass import getpass

import pandas as pd
from sqlalchemy import URL, create_engine

password = getpass("Enter your PostgreSQL password: ")

url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="EHCMDP_PostgreSQL",
)

engine = create_engine(url)

tables = [
    "stg_identity_events_clean",
    "stg_hr_saas_snapshots",
    "stg_hr_saas_leave_requests",
]

results = []

try:
    for table in tables:
        print(f"Diagnosing: {table}")

        try:
            df = pd.read_sql(
                f'SELECT * FROM staging."{table}"',
                engine,
            )

            row_count = len(df)
            duplicate_rows = int(df.duplicated().sum())
            fully_empty_rows = int(df.isna().all(axis=1).sum())

            results.append({
                "table_name": table,
                "total_rows": row_count,
                "total_columns": len(df.columns),
                "exact_duplicate_rows": duplicate_rows,
                "distinct_row_patterns": len(df.drop_duplicates()),
                "fully_empty_rows": fully_empty_rows,
                "rows_with_any_missing": int(
                    df.isna().any(axis=1).sum()
                ),
            })

        except Exception as error:
            print(f"Could not diagnose {table}: {error}")

    if results:
        report = pd.DataFrame(results)

        output_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data_quality_output",
        )
        os.makedirs(output_folder, exist_ok=True)

        output_file = os.path.join(
            output_folder,
            "Staging_Diagnostic_Report.xlsx",
        )

        report.to_excel(output_file, index=False)

        print("\nDiagnostic completed.")
        print(report.to_string(index=False))
        print(f"\nReport saved to: {output_file}")
    else:
        print("\nNo tables were successfully diagnosed.")

finally:
    engine.dispose()
