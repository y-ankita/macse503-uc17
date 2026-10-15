
from getpass import getpass
import pandas as pd
from sqlalchemy import URL, create_engine, text

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

query = text("""
    SELECT
        table_name,
        ordinal_position,
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'standardized'
      AND table_name IN (
          'access_standardized',
          'attendance_standardized',
          'hrms_standardized',
          'leave_standardized',
          'performance_standardized'
      )
    ORDER BY table_name, ordinal_position
""")

try:
    with engine.connect() as connection:
        columns = pd.read_sql(query, connection)

    print("\nSTANDARDIZED TABLE COLUMNS")
    for table, group in columns.groupby("table_name", sort=True):
        print(f"\n--- {table} ---")
        print(group[
            ["column_name", "data_type", "is_nullable"]
        ].to_string(index=False))

    output = "data_quality_output/Warehouse_Source_Columns.xlsx"
    columns.to_excel(output, index=False)
    print(f"\nColumn inventory saved to: {output}")

finally:
    engine.dispose()