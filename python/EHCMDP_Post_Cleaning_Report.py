
import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text, inspect
from openpyxl.styles import Font, PatternFill

user = "postgres"
password = os.getenv("EHCMDP_DB_PASSWORD", "8975")
database = "EHCMDP_DB"
schema = "staging"

output = (
    Path(__file__).resolve().parent
    / "EHCMDP_Post_Cleaning_Quality_Report.xlsx"
)

tables = [
    "stg_access_control",
    "stg_ai_fair_recruitment",
    "stg_attendance_xml",
    "stg_employee_performance",
    "stg_hr_employee",
    "stg_hr_saas_employee_master",
    "stg_hr_saas_leave_requests",
    "stg_hr_saas_snapshots",
    "stg_human_resource",
    "stg_leave",
    "stg_payroll",
    "stg_performance_eval_audio",
    "stg_performance_eval_behavior",
    "stg_performance_eval_structured",
    "stg_performance_rating",
]

connection_url = (
    f"postgresql+psycopg2://{user}:{quote_plus(password)}"
    f"@localhost:5432/{database}"
)

engine = create_engine(connection_url)

summary = []
columns_report = []
duplicates_report = []
issues = []
payroll_audit = []
payroll_review_records = pd.DataFrame()

try:
    with engine.connect() as conn:
        inspector = inspect(conn)
        available = inspector.get_table_names(schema=schema)

        for table in tables:
            if table not in available:
                issues.append({
                    "table": table,
                    "column": "",
                    "issue": "Table not found",
                    "count": 1,
                })

                summary.append({
                    "table": table,
                    "row_count": 0,
                    "column_count": 0,
                    "primary_key": "",
                    "columns_with_nulls": 0,
                    "columns_with_blanks": 0,
                    "duplicate_rows": 0,
                    "status": "Table not found",
                })
                continue

            full_table = f'"{schema}"."{table}"'

            row_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {full_table}")
            ).scalar_one()

            metadata = pd.read_sql(
                text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                      AND table_name = :table
                    ORDER BY ordinal_position
                """),
                conn,
                params={"schema": schema, "table": table},
            )

            primary_key = inspector.get_pk_constraint(
                table, schema=schema
            ).get("constrained_columns") or []

            null_columns = 0
            blank_columns = 0

            for _, column_info in metadata.iterrows():
                column_name = column_info["column_name"]
                quoted_column = (
                    '"' + column_name.replace('"', '""') + '"'
                )

                if column_info["data_type"] in [
                    "text",
                    "character varying",
                    "character",
                ]:
                    blank_check = (
                        f"COUNT(*) FILTER (WHERE {quoted_column} "
                        f"IS NOT NULL AND BTRIM("
                        f"{quoted_column}::text) = '')"
                    )
                else:
                    blank_check = "0"

                result = conn.execute(text(f"""
                    SELECT
                        COUNT(*) FILTER (
                            WHERE {quoted_column} IS NULL
                        ) AS nulls,
                        {blank_check} AS blanks,
                        COUNT(DISTINCT {quoted_column})
                            AS distinct_values
                    FROM {full_table}
                """)).mappings().one()

                null_count = result["nulls"]
                blank_count = result["blanks"]
                distinct_count = result["distinct_values"]

                null_columns += int(null_count > 0)
                blank_columns += int(blank_count > 0)

                columns_report.append({
                    "table": table,
                    "column": column_name,
                    "data_type": column_info["data_type"],
                    "primary_key": (
                        "Yes" if column_name in primary_key else "No"
                    ),
                    "row_count": row_count,
                    "null_count": null_count,
                    "blank_count": blank_count,
                    "distinct_values": distinct_count,
                    "missing_percentage": round(
                        (null_count + blank_count) * 100 / row_count, 2
                    ) if row_count else 0,
                })

                if null_count:
                    issues.append({
                        "table": table,
                        "column": column_name,
                        "issue": "NULL values",
                        "count": null_count,
                    })

                if blank_count:
                    issues.append({
                        "table": table,
                        "column": column_name,
                        "issue": "Blank strings",
                        "count": blank_count,
                    })

            if len(metadata):
                quoted_columns = ", ".join(
                    '"' + name.replace('"', '""') + '"'
                    for name in metadata["column_name"]
                )

                duplicate_result = conn.execute(text(f"""
                    SELECT
                        COUNT(*) AS duplicate_groups,
                        COALESCE(SUM(n - 1), 0)
                            AS extra_duplicate_rows
                    FROM (
                        SELECT COUNT(*) AS n
                        FROM {full_table}
                        GROUP BY {quoted_columns}
                        HAVING COUNT(*) > 1
                    ) AS duplicate_groups_query
                """)).mappings().one()

                duplicate_groups = duplicate_result["duplicate_groups"]
                extra_duplicate_rows = duplicate_result[
                    "extra_duplicate_rows"
                ]
            else:
                duplicate_groups = 0
                extra_duplicate_rows = 0

            duplicates_report.append({
                "table": table,
                "row_count": row_count,
                "duplicate_groups": duplicate_groups,
                "extra_duplicate_rows": extra_duplicate_rows,
            })

            if extra_duplicate_rows:
                issues.append({
                    "table": table,
                    "column": "All columns",
                    "issue": "Exact duplicate rows",
                    "count": extra_duplicate_rows,
                })

            summary.append({
                "table": table,
                "row_count": row_count,
                "column_count": len(metadata),
                "primary_key": ", ".join(primary_key),
                "columns_with_nulls": null_columns,
                "columns_with_blanks": blank_columns,
                "duplicate_rows": extra_duplicate_rows,
                "status": "Profiled",
            })

        if "stg_payroll" in available:
            payroll_counts = conn.execute(text("""
                SELECT
                    COUNT(*) AS total_payroll_rows,

                    COUNT(*) FILTER (
                        WHERE NULLIF(BTRIM("First Name"), '') IS NULL
                    ) AS missing_first_names,

                    COUNT(*) FILTER (
                        WHERE NULLIF(BTRIM("Last Name"), '') IS NULL
                    ) AS missing_last_names,

                    COUNT(*) FILTER (
                        WHERE "Pay Period " IS NULL
                    ) AS missing_pay_periods,

                    COUNT(*) FILTER (
                        WHERE "Total Deductions" IS NULL
                           OR BTRIM("Total Deductions"::text) = ''
                    ) AS missing_deductions,

                    COUNT(*) FILTER (
                        WHERE "Arrear Statutory Bonus" IS NULL
                           OR BTRIM(
                               "Arrear Statutory Bonus"::text
                           ) = ''
                    ) AS missing_arrear_bonus,

                    COUNT(*) FILTER (
                        WHERE "Date Of Termination" IS NULL
                    ) AS missing_termination_dates,

                    COUNT(*) FILTER (
                        WHERE "Employee Status" IS DISTINCT FROM
                              "Payroll Employee Status"
                    ) AS status_differences,

                    COUNT(*) FILTER (
                        WHERE allowance < 0
                    ) AS negative_allowances,

                    COUNT(*) FILTER (
                        WHERE "Date Of Termination" IS NOT NULL
                          AND "Last Working Date" IS NOT NULL
                          AND "Date Of Termination" >
                              "Last Working Date"
                    ) AS termination_after_last_working

                FROM staging.stg_payroll
            """)).mappings().one()

            audit_definitions = [
                (
                    "Total payroll rows",
                    "total_payroll_rows",
                    "Informational",
                    "Total records checked",
                ),
                (
                    "Missing first names",
                    "missing_first_names",
                    "Unresolved",
                    "No verified HR source match found",
                ),
                (
                    "Missing last names",
                    "missing_last_names",
                    "Unresolved",
                    "No verified HR source match found",
                ),
                (
                    "Missing pay periods",
                    "missing_pay_periods",
                    "Unresolved",
                    "Do not infer without an authoritative source",
                ),
                (
                    "Missing total deductions",
                    "missing_deductions",
                    "Unresolved",
                    "Do not assume missing values are zero",
                ),
                (
                    "Missing arrear statutory bonus",
                    "missing_arrear_bonus",
                    "Unresolved",
                    "Do not assume missing values are zero",
                ),
                (
                    "Missing termination dates",
                    "missing_termination_dates",
                    "Review",
                    "May be legitimate for active employees",
                ),
                (
                    "Employee/payroll status differences",
                    "status_differences",
                    "Review",
                    "Check business definitions before changing",
                ),
                (
                    "Negative allowances",
                    "negative_allowances",
                    "Review",
                    "Could be payroll adjustments",
                ),
                (
                    "Termination after last working date",
                    "termination_after_last_working",
                    "Review",
                    "Check date semantics before changing",
                ),
            ]

            for label, key, action, note in audit_definitions:
                payroll_audit.append({
                    "check": label,
                    "affected_rows": payroll_counts[key],
                    "recommended_action": action,
                    "notes": note,
                })

            payroll_review_records = pd.read_sql(text("""
                SELECT
                    "Employee ID",
                    "First Name",
                    "Last Name",
                    "Employee Status",
                    "Payroll Employee Status",
                    "Pay Period ",
                    "Total Deductions",
                    "Arrear Statutory Bonus",
                    allowance,
                    "Date Of Joining",
                    "Date Of Termination",
                    "Last Working Date",

                    CONCAT_WS('; ',
                        CASE
                            WHEN NULLIF(
                                BTRIM("First Name"), ''
                            ) IS NULL
                            THEN 'Missing first name'
                        END,
                        CASE
                            WHEN NULLIF(
                                BTRIM("Last Name"), ''
                            ) IS NULL
                            THEN 'Missing last name'
                        END,
                        CASE
                            WHEN "Pay Period " IS NULL
                            THEN 'Missing pay period'
                        END,
                        CASE
                            WHEN "Total Deductions" IS NULL
                              OR BTRIM(
                                  "Total Deductions"::text
                              ) = ''
                            THEN 'Missing total deductions'
                        END,
                        CASE
                            WHEN "Arrear Statutory Bonus" IS NULL
                              OR BTRIM(
                                  "Arrear Statutory Bonus"::text
                              ) = ''
                            THEN 'Missing arrear statutory bonus'
                        END,
                        CASE
                            WHEN "Employee Status" IS DISTINCT FROM
                                 "Payroll Employee Status"
                            THEN 'Employee/payroll status difference'
                        END,
                        CASE
                            WHEN allowance < 0
                            THEN 'Negative allowance'
                        END,
                        CASE
                            WHEN "Date Of Termination" IS NOT NULL
                             AND "Last Working Date" IS NOT NULL
                             AND "Date Of Termination" >
                                 "Last Working Date"
                            THEN 'Termination after last working date'
                        END
                    ) AS review_reason

                FROM staging.stg_payroll

                WHERE NULLIF(BTRIM("First Name"), '') IS NULL
                   OR NULLIF(BTRIM("Last Name"), '') IS NULL
                   OR "Pay Period " IS NULL
                   OR "Total Deductions" IS NULL
                   OR BTRIM("Total Deductions"::text) = ''
                   OR "Arrear Statutory Bonus" IS NULL
                   OR BTRIM(
                       "Arrear Statutory Bonus"::text
                   ) = ''
                   OR "Employee Status" IS DISTINCT FROM
                      "Payroll Employee Status"
                   OR allowance < 0
                   OR (
                       "Date Of Termination" IS NOT NULL
                       AND "Last Working Date" IS NOT NULL
                       AND "Date Of Termination" >
                           "Last Working Date"
                   )

                ORDER BY "Employee ID"
            """), conn)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([
            {"Metric": "Database", "Value": database},
            {"Metric": "Schema", "Value": schema},
            {"Metric": "Tables expected", "Value": len(tables)},
            {
                "Metric": "Tables profiled",
                "Value": sum(
                    item["status"] == "Profiled"
                    for item in summary
                ),
            },
            {
                "Metric": "Total rows",
                "Value": sum(
                    item["row_count"] for item in summary
                ),
            },
            {
                "Metric": "General quality findings",
                "Value": len(issues),
            },
            {
                "Metric": "Payroll audit checks",
                "Value": len(payroll_audit),
            },
            {
                "Metric": "Database modified",
                "Value": "No",
            },
        ]).to_excel(
            writer, sheet_name="Overall Summary", index=False
        )

        pd.DataFrame(summary).to_excel(
            writer, sheet_name="Table Summary", index=False
        )

        pd.DataFrame(columns_report).to_excel(
            writer, sheet_name="Column Quality", index=False
        )

        pd.DataFrame(duplicates_report).to_excel(
            writer, sheet_name="Duplicate Analysis", index=False
        )

        pd.DataFrame(
            issues,
            columns=["table", "column", "issue", "count"],
        ).to_excel(
            writer, sheet_name="Quality Issues", index=False
        )

        pd.DataFrame(payroll_audit).to_excel(
            writer, sheet_name="Payroll Audit Summary", index=False
        )

        payroll_review_records.to_excel(
            writer, sheet_name="Payroll Review Records", index=False
        )

        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            sheet.sheet_view.showGridLines = False

            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(
                    "solid", fgColor="1F4E78"
                )

            for cells in sheet.columns:
                width = min(
                    max(
                        len(str(cell.value or ""))
                        for cell in list(cells)[:100]
                    ) + 2,
                    40,
                )

                sheet.column_dimensions[
                    cells[0].column_letter
                ].width = width

    profiled_count = sum(
        item["status"] == "Profiled"
        for item in summary
    )

    print("Report created:", output)
    print("Tables profiled:", profiled_count, "of", len(tables))
    print("Payroll audit checks added:", len(payroll_audit))
    print("Payroll review records:", len(payroll_review_records))
    print("Database modified: No")

finally:
    engine.dispose()
