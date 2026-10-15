from getpass import getpass
import os

import pandas as pd
from sqlalchemy import URL, create_engine, text

# --------------------------------------------------
# 1. PostgreSQL connection
# --------------------------------------------------

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

# --------------------------------------------------
# 2. Source tables
# --------------------------------------------------

tables = [
    "access",
    "attendance",
    "hrms",
    "leave",
    "performance",
]

summary = []
audit = []

# --------------------------------------------------
# 3. Standardization process
# --------------------------------------------------

try:
    with engine.begin() as connection:
        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS standardized")
        )

    for table in tables:
        source_table = f"{table}_clean"
        target_table = f"{table}_standardized"

        print(f"\nStandardizing: {source_table}")

        # Read cleaned source data
        df = pd.read_sql(
            f'SELECT * FROM cleaned."{source_table}"',
            engine,
        )

        original_rows = len(df)
        original_columns = len(df.columns)

        changed_cells = 0
        blank_cells = 0

        # ------------------------------------------
        # 4. Normalize text columns only
        # ------------------------------------------

        text_columns = df.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in text_columns:
            before = df[column].astype("string")

            # Collapse repeated whitespace and trim edges
            cleaned_text = (
                before
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

            # Convert empty or whitespace-only strings to NULL
            cleaned_text = cleaned_text.mask(
                cleaned_text.eq(""),
                pd.NA,
            )

            # Count changes safely, distinguishing NULL from text
            changed = (
                before.fillna("").ne(cleaned_text.fillna(""))
                | before.isna().ne(cleaned_text.isna())
            )

            changed_cells += int(changed.sum())

            # Count originally blank or whitespace-only values
            before_blank = (
                before.notna()
                & before.str.strip().eq("").fillna(False)
            )

            blank_cells += int(before_blank.sum())

            df[column] = cleaned_text

        # ------------------------------------------
        # 5. Validate row-count preservation
        # ------------------------------------------

        rows_after = len(df)

        if rows_after != original_rows:
            raise ValueError(
                f"Row count mismatch in {source_table}: "
                f"{original_rows} before, {rows_after} after."
            )

        # ------------------------------------------
        # 6. Write standardized output table
        # ------------------------------------------

        df.to_sql(
            name=target_table,
            schema="standardized",
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=5000,
            method="multi",
        )

        # ------------------------------------------
        # 7. Record summary and audit evidence
        # ------------------------------------------

        summary.append({
            "source_table": f"cleaned.{source_table}",
            "target_table": f"standardized.{target_table}",
            "rows_before": original_rows,
            "rows_after": rows_after,
            "columns": original_columns,
            "cells_changed": changed_cells,
            "blank_cells_converted_to_null": blank_cells,
            "rows_removed": 0,
            "row_count_preserved": True,
            "status": "SUCCESS",
        })

        audit.append({
            "table_name": source_table,
            "operation": (
                "Trim leading/trailing whitespace, "
                "collapse repeated whitespace, "
                "convert blank text to NULL"
            ),
            "changed_cells": changed_cells,
            "blank_cells_converted_to_null": blank_cells,
            "rows_before": original_rows,
            "rows_after": rows_after,
            "rows_removed": 0,
        })

        print(f"Rows before: {original_rows}")
        print(f"Rows after: {rows_after}")
        print(f"Text cells changed: {changed_cells}")
        print(f"Blank cells converted to NULL: {blank_cells}")
        print(f"Output: standardized.{target_table}")

    # ----------------------------------------------
    # 8. Export Excel evidence
    # ----------------------------------------------

    output_dir = "data_quality_output"
    os.makedirs(output_dir, exist_ok=True)

    evidence_path = os.path.join(
        output_dir,
        "Standardization_Evidence.xlsx",
    )

    summary_df = pd.DataFrame(summary)
    audit_df = pd.DataFrame(audit)

    with pd.ExcelWriter(
        evidence_path,
        engine="openpyxl",
    ) as writer:
        summary_df.to_excel(
            writer,
            sheet_name="Standardization Summary",
            index=False,
        )

        audit_df.to_excel(
            writer,
            sheet_name="Audit Evidence",
            index=False,
        )

    print("\n" + "=" * 55)
    print("STANDARDIZATION COMPLETED SUCCESSFULLY")
    print("=" * 55)
    print("Database: EHCMDP_PostgreSQL")
    print("Output schema: standardized")
    print(f"Evidence workbook: {evidence_path}")
    print("\nStandardization Summary:")
    print(summary_df.to_string(index=False))

finally:
    engine.dispose()
