import os
import pandas as pd
from sqlalchemy import create_engine

# Connect to the EHCMDP PostgreSQL database
engine = create_engine(
    "postgresql+psycopg2://postgres:8975@localhost:5432/EHCMDP_DB"
)

# List of all 15 Sprint 2 staging tables
tables = [
    "stg_employee_performance",
    "stg_human_resource",
    "stg_hr_employee",
    "stg_ai_fair_recruitment",
    "stg_payroll",
    "stg_attendance_xml",
    "stg_leave",
    "stg_performance_rating",
    "stg_access_control",
    "stg_hr_saas_employee_master",
    "stg_hr_saas_snapshots",
    "stg_hr_saas_leave_requests",
    "stg_performance_eval_audio",
    "stg_performance_eval_behavior",
    "stg_performance_eval_structured"
]

# Store the Data Quality Analysis output
output_folder = r"D:\Data engg project\EHCMDP_Sprint2\data_quality_output"
os.makedirs(output_folder, exist_ok=True)

missing_report = []
duplicate_report = []
conversion_report = []
category_report = []

# Define only the fields that are expected to contain numeric values
numeric_columns = {
    "stg_employee_performance": [
        "age",
        "years_at_company",
        "performance_score",
        "monthly_salary",
        "work_hours_per_week",
        "projects_handled",
        "overtime_hours",
        "sick_days",
        "remote_work_frequency",
        "team_size",
        "training_hours",
        "promotions",
        "employee_satisfaction_score"
    ],

    "stg_human_resource": [
        "salary",
        "performance_rating"
    ],

    "stg_hr_employee": [
        "age",
        "distancefromhome (km)",
        "education",
        "salary",
        "stockoptionlevel",
        "yearsatcompany",
        "years_in_most_recent_role",
        "yearssincelastpromotion",
        "yearswithcurrmanager"
    ],

    "stg_ai_fair_recruitment": [
        "aptitude_test_score",
        "skill_score",
        "experience_years",
        "previous_companies",
        "communication_score",
        "technical_test_score",
        "certifications_count",
        "interview_score",
        "expected_salary",
        "age"
    ],

    "stg_payroll": [
        "age",
        "experience",
        "tenure",
        "basic salary",
        "allowance",
        "statutory bonus",
        "gross salary",
        "arrear special allowance",
        "total deductions",
        "arrear statutory bonus",
        "net salary",
        "tax spend",
        "reimbursement paid"
    ],

    "stg_performance_rating": [
        "environmentsatisfaction",
        "jobsatisfaction",
        "relationshipsatisfaction",
        "trainingopportunitieswithinyear",
        "trainingopportunitiestaken",
        "worklifebalance",
        "selfrating",
        "managerrating"
    ],

    "stg_access_control": [
        "id",
        "mgr_id",
        "role_rollup_1",
        "role_rollup_2",
        "role_code",
        "target"
    ],

    "stg_hr_saas_employee_master": [
        "age",
        "job_level",
        "base_salary",
        "bonus_pct",
        "equity_grant",
        "equity_pct",
        "fte",
        "training_count",
        "promotion_count"
    ],

    "stg_performance_eval_audio": [
        "speech_sentiment_score",
        "speech_energy_level",
        "speech_clarity_score",
        "tone_consistency_score",
        "speaking_speed",
        "pause_frequency",
        "pitch_variation",
        "volume_stability_score"
    ],

    "stg_performance_eval_behavior": [
        "meetings_attended",
        "collaboration_score",
        "punctuality_score",
        "training_hours_completed",
        "work_engagement_score",
        "peer_interaction_score",
        "initiative_score",
        "task_followup_score"
    ]
}

for table in tables:
    print(f"Analyzing: {table}")

    # Read the staging table for quality assessment
    df = pd.read_sql(
        f'SELECT * FROM staging."{table}"',
        engine
    )

    # Check missing values for every column
    for column in df.columns:
        missing = df[column].isna().sum()

        if missing > 0:
            missing_report.append({
                "table_name": table,
                "column_name": column,
                "missing_count": missing,
                "missing_percentage": round(
                    missing / len(df) * 100, 2
                )
            })

    # Identify exact duplicate records
    duplicates = df.duplicated().sum()

    duplicate_report.append({
        "table_name": table,
        "total_rows": len(df),
        "duplicate_rows": duplicates,
        "duplicate_percentage": round(
            duplicates / len(df) * 100, 2
        ) if len(df) else 0
    })

    # Validate only the columns expected to be numeric
    for column in numeric_columns.get(table, []):

        if column not in df.columns:
            continue

        converted = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid = (
            converted.isna() &
            df[column].notna()
        ).sum()

        if invalid > 0:
            conversion_report.append({
                "table_name": table,
                "column_name": column,
                "check_type": "Numeric Conversion",
                "invalid_values": invalid
            })

    # Capture categorical values for standardization analysis
    for column in df.select_dtypes(
        include=["object", "string"]
    ).columns:

        value_counts = (
            df[column]
            .fillna("<NULL>")
            .astype(str)
            .value_counts()
        )

        for value, count in value_counts.items():
            category_report.append({
                "table_name": table,
                "column_name": column,
                "value": value,
                "count": count
            })

# Prepare the four Data Quality Analysis reports
reports = {
    "Missing Values": pd.DataFrame(missing_report),
    "Duplicates": pd.DataFrame(duplicate_report),
    "Conversion Issues": pd.DataFrame(conversion_report),
    "Categorical Values": pd.DataFrame(category_report)
}

# Save all reports in a single Excel workbook
output_file = os.path.join(
    output_folder,
    "EHCMDP_Data_Quality_Analysis.xlsx"
)

with pd.ExcelWriter(
    output_file,
    engine="openpyxl"
) as writer:

    for sheet_name, report in reports.items():

        report.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )

        # Keep headers visible while scrolling
        worksheet = writer.sheets[sheet_name]
        worksheet.freeze_panes = "A2"

        # Enable filtering on the report headers
        worksheet.auto_filter.ref = worksheet.dimensions

        # Automatically adjust column widths for readability
        for column_cells in worksheet.columns:

            max_length = max(
                len(str(cell.value))
                if cell.value is not None else 0
                for cell in column_cells
            )

            worksheet.column_dimensions[
                column_cells[0].column_letter
            ].width = min(
                max_length + 2,
                40
            )

print("\nData Quality Analysis completed.")
print(f"Output file: {output_file}")
print("\nGenerated sheets:")

for sheet in reports:
    print(f"- {sheet}")