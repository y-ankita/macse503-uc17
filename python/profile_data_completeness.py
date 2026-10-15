
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

tables = {
    "Identity Events": 'staging."stg_identity_events_clean"',
    "Employee Snapshots": 'staging."stg_hr_saas_snapshots"',
    "Leave Requests": 'staging."stg_hr_saas_leave_requests"',
}

key_fields = [
    "employee_id",
    "first_name",
    "last_name",
    "department",
    "job_title",
    "hire_date",
    "employment_status",
    "manager_id",
]

try:
    for table_label, table_name in tables.items():
        print("\n" + "=" * 60)
        print(f"TABLE: {table_label}")
        print(f"SOURCE: {table_name}")
        print("=" * 60)

        try:
            df = pd.read_sql(
                f"SELECT * FROM {table_name}",
                engine,
            )
        except Exception as error:
            print(f"Could not read this table: {error}")
            continue

        print(f"\nTotal rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")

        if df.empty:
            print("Table has no rows to analyze.")
            continue

        # 1. Count populated columns per row
        populated_count = df.notna().sum(axis=1)

        print("\n1. POPULATED COLUMNS PER ROW")
        print(
            populated_count.value_counts()
            .sort_index()
            .to_string()
        )

        # 2. Column completeness
        print("\n2. COLUMN COMPLETENESS")

        completeness = pd.DataFrame({
            "column": df.columns,
            "populated_count": df.notna().sum().values,
            "missing_count": df.isna().sum().values,
        })

        completeness["populated_percentage"] = (
            df.notna().mean().values * 100
        ).round(2)

        print(
            completeness.sort_values(
                "populated_percentage"
            ).to_string(index=False)
        )

        # 3. Most common missing-value patterns
        pattern = (
            df.notna()
            .astype(int)
            .astype(str)
            .agg("".join, axis=1)
        )

        print("\n3. MOST COMMON MISSING-VALUE PATTERNS")
        print(
            pattern.value_counts()
            .head(10)
            .rename_axis("pattern")
            .reset_index(name="row_count")
            .to_string(index=False)
        )

        # 4. Key-field completeness where applicable
        print("\n4. KEY-FIELD COMPLETENESS")

        matching_fields = [
            column for column in key_fields
            if column in df.columns
        ]

        if matching_fields:
            for column in matching_fields:
                print(
                    f"{column}: "
                    f"{df[column].notna().sum()} populated, "
                    f"{df[column].isna().sum()} missing"
                )
        else:
            print(
                "No employee-specific key fields found "
                "in this table."
            )

finally:
    engine.dispose()
