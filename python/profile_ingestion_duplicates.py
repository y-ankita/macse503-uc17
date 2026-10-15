
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

# Map each Pentaho transformation to its PostgreSQL output table.
tables = {
    "Identity_Events_Realtime_Ingestion.ktr":
        "stg_identity_events_clean",

    "HR_SaaS_Employee_Snapshot_XML_Ingestion.ktr":
        "stg_hr_saas_snapshots",

    "HR_SaaS_Leave_Request_JSON_Ingestion.ktr":
        "stg_hr_saas_leave_requests",
}


try:
    for transformation, table in tables.items():
        print("\n" + "=" * 65)
        print(f"TRANSFORMATION: {transformation}")
        print(f"TABLE: staging.{table}")
        print("=" * 65)

        # Read the table populated by the transformation.
        df = pd.read_sql(
            f'SELECT * FROM staging."{table}"',
            engine,
        )

        # Separate completely NULL rows from populated rows.
        empty_mask = df.isna().all(axis=1)
        populated = df.loc[~empty_mask]

        print(f"Total rows: {len(df)}")
        print(f"Fully empty rows: {int(empty_mask.sum())}")
        print(f"Populated rows: {len(populated)}")

        if populated.empty:
            print("No populated rows to inspect.")
            continue

        # Convert each row into a hashable representation.
        # This also supports JSON/dictionary-like values.
        normalized = populated.apply(
            lambda row: tuple(
                "<NULL>" if pd.isna(value)
                else str(value)
                for value in row
            ),
            axis=1,
        )

        # Count identical populated row patterns.
        frequencies = normalized.value_counts().rename("occurrences")

        print(f"Distinct populated patterns: {len(frequencies)}")

        print("\nOccurrences per row pattern:")
        print(
            frequencies.value_counts()
            .sort_index()
            .rename_axis("times_repeated")
            .to_string()
        )

        print("\nMost frequently repeated patterns:")
        print(
            frequencies
            .sort_values(ascending=False)
            .head(10)
            .to_string()
        )

        # Count rows that belong to repeated patterns.
        repeated_patterns = frequencies[frequencies > 1]

        print("\nDuplicate summary:")
        print(f"Repeated patterns: {len(repeated_patterns)}")
        print(
            "Rows belonging to repeated patterns: "
            f"{int(repeated_patterns.sum())}"
        )
        print(
            "Excess duplicate rows: "
            f"{int((repeated_patterns - 1).sum())}"
        )

finally:
    engine.dispose()
