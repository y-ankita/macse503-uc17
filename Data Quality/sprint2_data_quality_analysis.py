
import os
from getpass import getpass

import pandas as pd
from sqlalchemy import URL, create_engine


# 1. Connect to PostgreSQL securely
password = getpass("Enter your PostgreSQL password: ")

connection_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="EHCMDP_DB",
)

engine = create_engine(connection_url)


# 2. Use the five staging tables verified in your database
tables = [
    "access",
    "attendance",
    "hrms",
    "leave",
    "performance",
]


# 3. Save output in the project folder
output_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data_quality_output",
)
os.makedirs(output_folder, exist_ok=True)


# 4. Store results for the four Excel sheets
missing_report = []
duplicate_report = []
conversion_report = []
category_report = []


# 5. Numeric columns that exist in your actual tables
numeric_columns = {
    "access": [
        "id", "mgr_id", "role_rollup_1", "role_rollup_2",
        "role_code", "target",
    ],
    "attendance": [
        "xml_element_id", "xml_parent_element_id",
        "xml_element_level",
    ],
    "hrms": [
        "age", "job_level", "base_salary", "bonus_pct",
        "equity_pct", "fte", "training_count",
        "promotion_count", "employee_id",
    ],
    "leave": [
        "Days Taken", "Total Leave Entitlement",
        "Leave Taken So Far", "Remaining Leaves",
    ],
    "performance": [
        "environmentsatisfaction", "jobsatisfaction",
        "relationshipsatisfaction",
        "trainingopportunitieswithinyear",
        "trainingopportunitiestaken", "worklifebalance",
        "selfrating", "managerrating",
    ],
}


# 6. Analyze each staging table
try:
    for table in tables:
        print(f"Analyzing: {table}")

        df = pd.read_sql(
            f'SELECT * FROM staging."{table}"',
            engine,
        )

        # Missing values
        for column in df.columns:
            missing = int(df[column].isna().sum())

            if missing > 0:
                missing_report.append({
                    "table_name": table,
                    "column_name": column,
                    "missing_count": missing,
                    "missing_percentage": round(
                        missing / len(df) * 100, 2
                    ) if len(df) else 0,
                })

        # Exact duplicate rows
        duplicates = int(df.duplicated().sum())

        duplicate_report.append({
            "table_name": table,
            "total_rows": len(df),
            "duplicate_rows": duplicates,
            "duplicate_percentage": round(
                duplicates / len(df) * 100, 2
            ) if len(df) else 0,
        })

        # Numeric conversion checks
        for column in numeric_columns.get(table, []):
            if column not in df.columns:
                continue

            converted = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            invalid = int((
                converted.isna() & df[column].notna()
            ).sum())

            if invalid > 0:
                conversion_report.append({
                    "table_name": table,
                    "column_name": column,
                    "check_type": "Numeric Conversion",
                    "invalid_values": invalid,
                })

        # Categorical values and their frequencies
        text_columns = df.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in text_columns:
            value_counts = (
                df[column]
                .fillna("<NULL>")
                .astype(str)
                .value_counts()
            )

            for value, count in value_counts.items():
                category_report.append({
                    "table_name": table,
                    "column_name": column,
                    "value": value,
                    "count": int(count),
                })

    # 7. Prepare report sheets with headers even when no issues exist
    reports = {
        "Missing Values": pd.DataFrame(
            missing_report,
            columns=[
                "table_name", "column_name",
                "missing_count", "missing_percentage",
            ],
        ),
        "Duplicates": pd.DataFrame(
            duplicate_report,
            columns=[
                "table_name", "total_rows",
                "duplicate_rows", "duplicate_percentage",
            ],
        ),
        "Conversion Issues": pd.DataFrame(
            conversion_report,
            columns=[
                "table_name", "column_name",
                "check_type", "invalid_values",
            ],
        ),
        "Categorical Values": pd.DataFrame(
            category_report,
            columns=[
                "table_name", "column_name", "value", "count",
            ],
        ),
    }

    # 8. Write all reports to Excel
    output_file = os.path.join(
        output_folder,
        "EHCMDP_Data_Quality_Analysis.xlsx",
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl",
    ) as writer:
        for sheet_name, report in reports.items():
            report.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

            for column_cells in worksheet.columns:
                max_length = max(
                    len(str(cell.value))
                    if cell.value is not None else 0
                    for cell in column_cells
                )

                worksheet.column_dimensions[
                    column_cells[0].column_letter
                ].width = min(max_length + 2, 40)

    print("\nData Quality Analysis completed successfully.")
    print(f"Tables analyzed: {len(tables)}")
    print(f"Output file: {output_file}")
    print("\nGenerated sheets:")

    for sheet_name in reports:
        print(f"- {sheet_name}")

finally:
    engine.dispose()