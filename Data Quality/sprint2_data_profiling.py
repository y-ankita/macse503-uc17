
import pandas as pd
from sqlalchemy import create_engine, URL
import os
from getpass import getpass

# Database connection
password = getpass("Enter your PostgreSQL password: ")

connection_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="EHCMDP_DB"
)

engine = create_engine(connection_url)

# Staging tables verified in PostgreSQL
tables = [
    "access",
    "attendance",
    "hrms",
    "leave",
    "performance"
]

# Output folder

output_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "profiling_output"
)

os.makedirs(output_folder, exist_ok=True)


# Store profiling results
shape = []
datatypes = []
missing = []
duplicates = []
numerical = []
categorical = []
categorical_values = []
dates = []
summary = []

# Profile each staging table
for table in tables:

    print("Profiling:", table)

    df = pd.read_sql(
        f'SELECT * FROM staging."{table}"',
        engine
    )

    rows, columns = df.shape
    total_missing = int(df.isnull().sum().sum())
    total_values = rows * columns
    duplicate_count = int(df.duplicated().sum())

    # Dataset shape
    shape.append({
        "table_name": table,
        "rows": rows,
        "columns": columns
    })

    # Data quality summary
    summary.append({
        "table_name": table,
        "row_count": rows,
        "column_count": columns,
        "missing_values": total_missing,
        "missing_percentage": round(
            total_missing / total_values * 100, 2
        ) if total_values else 0,
        "duplicate_rows": duplicate_count
    })

    # Duplicate summary
    duplicates.append({
        "table_name": table,
        "row_count": rows,
        "duplicate_rows": duplicate_count
    })

    # Profile each column
    for column in df.columns:

        series = df[column]
        null_count = int(series.isnull().sum())

        # Data type profile
        datatypes.append({
            "table_name": table,
            "column_name": column,
            "data_type": str(series.dtype),
            "non_null_values": int(series.notnull().sum()),
            "null_values": null_count
        })

        # Missing value details
        if null_count:
            missing.append({
                "table_name": table,
                "column_name": column,
                "missing_count": null_count,
                "missing_percentage": round(
                    null_count / rows * 100, 2
                ) if rows else 0
            })

        # Categorical profile
        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):

            categorical.append({
                "table_name": table,
                "column_name": column,
                "unique_values": int(series.nunique()),
                "missing_values": null_count
            })

            for value, count in series.value_counts(
                dropna=False
            ).items():

                categorical_values.append({
                    "table_name": table,
                    "column_name": column,
                    "value": "<NULL>" if pd.isna(value) else str(value),
                    "frequency": int(count),
                    "percentage": round(
                        count / rows * 100, 2
                    ) if rows else 0
                })

        # Numerical profile
        if pd.api.types.is_numeric_dtype(series):

            numerical.append({
                "table_name": table,
                "column_name": column,
                "minimum": series.min(),
                "maximum": series.max(),
                "mean": round(series.mean(), 2),
                "median": series.median(),
                "missing_values": null_count
            })

        # Date profile
        column_name = column.lower()

        is_date = any(
            keyword in column_name
            for keyword in [
                "date",
                "birthdate",
                "hiredate",
                "reviewdate"
            ]
        )

        if is_date:

            converted = pd.to_datetime(
                series,
                errors="coerce",
                format="mixed"
            )

            valid = int(converted.notna().sum())
            invalid = int(
                (series.notna() & converted.isna()).sum()
            )
            missing_dates = int(series.isna().sum())

            dates.append({
                "table_name": table,
                "column_name": column,
                "valid_dates": valid,
                "invalid_dates": invalid,
                "missing_dates": missing_dates,
                "minimum_date": converted.min() if valid else None,
                "maximum_date": converted.max() if valid else None
            })

# Convert results to DataFrames
reports = {
    "Dataset Shape": pd.DataFrame(shape),
    "Data Types": pd.DataFrame(datatypes),
    "Missing Values": pd.DataFrame(missing),
    "Duplicates": pd.DataFrame(duplicates),
    "Numerical Profile": pd.DataFrame(numerical),
    "Categorical Profile": pd.DataFrame(categorical),
    "Categorical Values": pd.DataFrame(categorical_values),
    "Date Profile": pd.DataFrame(dates),
    "Data Quality Summary": pd.DataFrame(summary)
}

# Create Excel report
excel_file = os.path.join(
    output_folder,
    "EHCMDP_Data_Profiling_Report.xlsx"
)

with pd.ExcelWriter(
    excel_file,
    engine="openpyxl"
) as writer:

    for sheet_name, data in reports.items():

        data.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )

    # Format the workbook
    for worksheet in writer.book.worksheets:

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for column in worksheet.columns:

            width = max(
                len(str(cell.value))
                if cell.value is not None else 0
                for cell in column
            )

            worksheet.column_dimensions[
                column[0].column_letter
            ].width = min(
                max(width + 2, 12),
                35
            )

    # Format dates so Excel does not display #######
    date_sheet = writer.book["Date Profile"]

    for row in date_sheet.iter_rows(
        min_row=2
    ):
        for cell in row:

            if cell.column in [6, 7]:
                if cell.value is not None:
                    cell.number_format = "yyyy-mm-dd"

# Completion message
print("\nData profiling completed successfully.")
print("\nProfiling report:")
print(excel_file)
print("\nAll 5 staging tables were profiled.")

print("\nReport sheets:")
for number, sheet in enumerate(
    reports.keys(),
    start=1
):
    print(f"{number}. {sheet}")