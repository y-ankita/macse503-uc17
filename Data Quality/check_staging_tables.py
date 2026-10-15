
import psycopg2
from getpass import getpass

password = getpass("Enter your PostgreSQL password: ")

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="EHCMDP_DB",
    user="postgres",
    password=password
)

try:
    cur = conn.cursor()

    cur.execute("""
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'staging'
          AND table_name IN (
              'access',
              'attendance',
              'hrms',
              'leave',
              'performance'
          )
        ORDER BY table_name, ordinal_position;
    """)

    rows = cur.fetchall()
    current_table = None

    for table, column, dtype, nullable in rows:
        if table != current_table:
            print(f"\n--- staging.{table} ---")
            current_table = table

        print(
            f"{column} | Type: {dtype} | "
            f"Nullable: {nullable}"
        )

    cur.close()
finally:
    conn.close()