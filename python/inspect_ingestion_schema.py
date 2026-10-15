import psycopg2
from getpass import getpass

password = getpass("Enter your PostgreSQL password: ")

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="EHCMDP_PostgreSQL",
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
              'stg_identity_events_clean',
              'stg_hr_saas_snapshots',
              'stg_hr_saas_leave_requests'
          )
        ORDER BY table_name, ordinal_position;
    """)

    rows = cur.fetchall()
    current_table = None

    if not rows:
        print("No matching tables found in the staging schema.")

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