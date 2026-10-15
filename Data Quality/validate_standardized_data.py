
from getpass import getpass
from pathlib import Path

import pandas as pd
from sqlalchemy import URL, create_engine

password = getpass("Enter your PostgreSQL password: ")

url = URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="EHCMDP_DB",
)

engine = create_engine(url)

tables = ["access", "attendance", "hrms", "leave", "performance"]
table_results = []
missing_results = []
whitespace_results = []

try:
    for table in tables:
        print(f"Validating {table}...")

        cleaned = pd.read_sql(
            f'SELECT * FROM cleaned."{table}_clean"', engine
        )
        standardized = pd.read_sql(
            f'SELECT * FROM standardized."{table}_standardized"',
            engine,
        )

        exact_duplicates = int(
            standardized.duplicated(keep=False).sum()
        )
        duplicate_rows_beyond_first = int(
            standardized.duplicated().sum()
        )
        fully_empty_rows = int(
            standardized.isna().all(axis=1).sum()
        )
        missing_cells = int(standardized.isna().sum().sum())

        table_results.append({
            "table_name": table,
            "cleaned_rows": len(cleaned),
            "standardized_rows": len(standardized),
            "cleaned_columns": len(cleaned.columns),
            "standardized_columns": len(standardized.columns),
            "row_count_matches": len(cleaned) == len(standardized),
            "column_count_matches": (
                len(cleaned.columns) == len(standardized.columns)
            ),
            "duplicate_rows_beyond_first": duplicate_rows_beyond_first,
            "rows_in_duplicate_groups": exact_duplicates,
            "fully_empty_rows": fully_empty_rows,
            "missing_cells": missing_cells,
        })

        for column in standardized.columns:
            null_count = int(standardized[column].isna().sum())
            if null_count:
                missing_results.append({
                    "table_name": table,
                    "column_name": column,
                    "missing_count": null_count,
                    "missing_percentage": round(
                        null_count / len(standardized) * 100, 2
                    ) if len(standardized) else 0,
                })

            if (
                pd.api.types.is_string_dtype(standardized[column])
                or standardized[column].dtype == object
            ):
                values = standardized[column].dropna().astype(str)

                leading_or_trailing = int(
                    values.ne(values.str.strip()).sum()
                )
                repeated_whitespace = int(
                    values.str.contains(r"\s{2,}", regex=True).sum()
                )
                blank_strings = int(
                    values.str.strip().eq("").sum()
                )

                whitespace_results.append({
                    "table_name": table,
                    "column_name": column,
                    "leading_or_trailing_whitespace": leading_or_trailing,
                    "repeated_whitespace": repeated_whitespace,
                    "blank_strings": blank_strings,
                })

    table_df = pd.DataFrame(table_results)
    missing_df = pd.DataFrame(
        missing_results,
        columns=[
            "table_name", "column_name",
            "missing_count", "missing_percentage"
        ],
    )
    whitespace_df = pd.DataFrame(whitespace_results)

    output = (
        Path(__file__).resolve().parent
        / "data_quality_output"
        / "Standardized_Data_Validation.xlsx"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        table_df.to_excel(
            writer, sheet_name="Table Validation", index=False
        )
        missing_df.to_excel(
            writer, sheet_name="Missing Values", index=False
        )
        whitespace_df.to_excel(
            writer, sheet_name="Whitespace Checks", index=False
        )

    print("\nVALIDATION SUMMARY")
    print(table_df.to_string(index=False))
    print("\nValidation workbook:", output)

finally:
    engine.dispose()