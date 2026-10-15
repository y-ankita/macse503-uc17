
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

try:
    # Create a separate schema; never overwrite staging.
    with engine.begin() as connection:
        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS cleaned")
        )

    for table in tables:
        print(f"\nCleaning copy of: {table}")

        df = pd.read_sql(
            f'SELECT * FROM staging."{table}"',
            engine,
        )

        original_rows = len(df)

        # Remove only rows where every field is NULL.
        df = df.dropna(how="all")

        rows_after_empty_removal = len(df)

        # Remove exact duplicate rows from the analytical copy.
        df = df.drop_duplicates()

        final_rows = len(df)

        # Write to a separate schema.
        df.to_sql(
            name=f"{table}_clean",
            schema="cleaned",
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=5000,
        )

        summary.append({
            "table_name": table,
            "original_rows": original_rows,
            "empty_rows_removed": (
                original_rows - rows_after_empty_removal
            ),
            "duplicate_rows_removed": (
                rows_after_empty_removal - final_rows
            ),
            "cleaned_rows": final_rows,
            "columns": len(df.columns),
        })

        print(f"Original rows: {original_rows}")
        print(f"Empty rows removed: {original_rows - rows_after_empty_removal}")
        print(f"Duplicate rows removed: {rows_after_empty_removal - final_rows}")
        print(f"Cleaned rows: {final_rows}")

    report = pd.DataFrame(summary)

    print("\nCLEANING SUMMARY")
    print(report.to_string(index=False))

    print("\nCleaned tables created in the 'cleaned' schema.")

finally:
    engine.dispose()