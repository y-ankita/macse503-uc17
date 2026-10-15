
from getpass import getpass

import pandas as pd
from sqlalchemy import URL, create_engine, text

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
    "access",
    "attendance",
    "hrms",
    "leave",
    "performance",
]

summary = []
audit = []

try:
    with engine.begin() as connection:
        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS standardized")
        )

    for table in tables:
        print(f"\nStandardizing: {table}")

        df = pd.read_sql(
            f'SELECT * FROM cleaned."{table}_clean"',
            engine,
        )

        original_rows = len(df)
        original_columns = len(df.columns)
        changed_cells = 0
        blank_cells = 0

        # Normalize whitespace only in text columns.
        # Do not modify names, IDs, categories' capitalization,
        # dates, salaries, or numeric values automatically.
        for column in df.select_dtypes(
            include=["object", "string"]
        ).columns:
            before = df[column].copy()

            cleaned_text = (
                df[column]
                .astype("string")
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

            # Treat empty strings as missing values.
            cleaned_text = cleaned_text.mask(
                cleaned_text.eq(""), pd.NA
            )

            changed = (
                before.fillna("<NULL>").astype(str)
                != cleaned_text.fillna("<NULL>").astype(str)
            )
            changed_cells += int(changed.sum())

            before_blank = (
                before.notna() & before.astype(str).str.strip().eq("")
            )
            blank_cells += int(before_blank.sum())

            df[column] = cleaned_text

        # Preserve row count: this step does not delete records.
        assert len(df) == original_rows

        df.to_sql(
            name=f"{table}_standardized",
            schema="standardized",
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=5000,
        )

        summary.append({
            "table_name": table,
            "rows_before": original_rows,
            "rows_after": len(df),
            "columns": original_columns,
            "cells_changed_by_text_normalization": changed_cells,
            "blank_text_cells_converted_to_null": blank_cells,
            "row_count_preserved": len(df) == original_rows,
        })

        # Store aggregate audit information, not employee values.
        audit.append({
            "table_name": table,
            "operation": "Trim and collapse whitespace in text fields",
            "changed_cells": changed_cells,
            "blank_text_cells_converted_to_null": blank_cells,
            "rows_removed": 0,
        })

        print(f"Rows preserved: {len(df)}")
        print(f"Text cells changed: {changed_cells}")
        print(f"Blank text cells converted to NULL: {blank_cells}")

    output_dir = "data_quality_output"
    import os
    os.makedirs(output_dir, exist_ok=True)

    summary_df = pd.DataFrame(summary)
    audit_df = pd.DataFrame(audit)

    with pd.ExcelWriter(
        f"{output_dir}/Standardization_Evidence.xlsx",
        engine="openpyxl",
    ) as writer:
        summary_df.to_excel(
            writer, sheet_name="Standardization Summary", index=False
        )
        audit_df.to_excel(
            writer, sheet_name="Audit Evidence", index=False
        )

    print("\nSTANDARDIZATION COMPLETE")
    print("Output schema: standardized")
    print("Evidence: data_quality_output/Standardization_Evidence.xlsx")
    print(summary_df.to_string(index=False))

finally:
    engine.dispose()