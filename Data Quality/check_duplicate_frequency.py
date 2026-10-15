
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
    database="EHCMDP_DB",
)

engine = create_engine(url)

tables = ["access", "attendance", "hrms", "leave", "performance"]

try:
    for table in tables:
        print(f"\n{'=' * 55}")
        print(f"TABLE: {table}")
        print("=" * 55)

        df = pd.read_sql(
            f'SELECT * FROM staging."{table}"',
            engine,
        )

        # Separate fully empty rows from populated rows
        empty_mask = df.isna().all(axis=1)
        populated = df.loc[~empty_mask]

        print(f"Total rows: {len(df)}")
        print(f"Fully empty rows: {int(empty_mask.sum())}")
        print(f"Populated rows: {len(populated)}")

        if populated.empty:
            print("No populated rows to inspect.")
            continue

        # Count occurrences of each distinct populated row
        frequencies = (
            populated.value_counts(dropna=False)
            .rename("occurrences")
            .reset_index()
        )

        print(f"Distinct populated patterns: {len(frequencies)}")
        print("\nOccurrences per row pattern:")
        print(
            frequencies["occurrences"]
            .value_counts()
            .sort_index()
            .rename_axis("times_repeated")
            .to_string()
        )

        print("\nMost frequently repeated patterns:")
        print(
            frequencies["occurrences"]
            .value_counts()
            .sort_values(ascending=False)
            .head(10)
            .to_string()
        )

finally:
    engine.dispose()