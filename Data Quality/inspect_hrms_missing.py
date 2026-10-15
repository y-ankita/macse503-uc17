
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

    missing_report = pd.DataFrame({
        "column_name": df.columns,
        "missing_count": df.isna().sum().values,
        "missing_percentage": (
            df.isna().mean().values * 100
        ).round(2),
    })

    missing_report = missing_report[
        missing_report["missing_count"] > 0
    ].sort_values(
        "missing_percentage",
        ascending=False,
    )

    print("\nHRMS MISSING-VALUE REPORT")
    print(missing_report.to_string(index=False))

    print("\nTOTAL HRMS ROWS:", len(df))
    print(
        "ROWS WITH ANY MISSING VALUE:",
        int(df.isna().any(axis=1).sum()),
    )

finally:
    engine.dispose()

