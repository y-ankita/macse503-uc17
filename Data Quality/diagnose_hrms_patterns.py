
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

try:
    df = pd.read_sql(
        'SELECT * FROM cleaned."hrms_clean"',
        engine,
    )

    # 1. Count populated columns per row
    populated_count = df.notna().sum(axis=1)

    print("\n1. POPULATED COLUMNS PER ROW")
    print(
        populated_count.value_counts()
        .sort_index()
        .to_string()
    )

    # 2. Show the most frequently populated columns
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

    # 3. Group rows by identical missing-value patterns
    pattern = df.notna().astype(int).astype(str).agg(
        "".join, axis=1
    )

    print("\n3. MOST COMMON MISSING-VALUE PATTERNS")
    print(
        pattern.value_counts()
        .head(10)
        .rename_axis("pattern")
        .reset_index(name="row_count")
        .to_string(index=False)
    )

    # 4. Check key-field completeness without printing employee data
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

    print("\n4. KEY-FIELD COMPLETENESS")
    for column in key_fields:
        if column in df.columns:
            print(
                f"{column}: "
                f"{df[column].notna().sum()} populated, "
                f"{df[column].isna().sum()} missing"
            )

finally:
    engine.dispose()

