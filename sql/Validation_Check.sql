-- EHCMDP DATA VALIDATION REPORT
-- Database: EHCMDP_PostgreSQL

-- 1. WAREHOUSE TABLE ROW COUNTS
SELECT 'dim_date' AS table_name, COUNT(*) AS row_count
FROM warehouse.dim_date
UNION ALL
SELECT 'dim_department', COUNT(*)
FROM warehouse.dim_department
UNION ALL
SELECT 'dim_employee', COUNT(*)
FROM warehouse.dim_employee
UNION ALL
SELECT 'dim_job', COUNT(*)
FROM warehouse.dim_job
UNION ALL
SELECT 'fact_access_control', COUNT(*)
FROM warehouse.fact_access_control
UNION ALL
SELECT 'fact_attendance', COUNT(*)
FROM warehouse.fact_attendance
UNION ALL
SELECT 'fact_employee_performance', COUNT(*)
FROM warehouse.fact_employee_performance
UNION ALL
SELECT 'fact_identity_events', COUNT(*)
FROM warehouse.fact_identity_events
UNION ALL
SELECT 'fact_leave', COUNT(*)
FROM warehouse.fact_leave
UNION ALL
SELECT 'fact_payroll', COUNT(*)
FROM warehouse.fact_payroll
UNION ALL
SELECT 'fact_performance_rating', COUNT(*)
FROM warehouse.fact_performance_rating
UNION ALL
SELECT 'fact_recruitment', COUNT(*)
FROM warehouse.fact_recruitment
ORDER BY table_name;


-- 2. PERFORMANCE RATING DATE-KEY VALIDATION
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE f.review_date_key IS NULL
    ) AS missing_date_keys,
    COUNT(*) FILTER (
        WHERE f.review_date_key IS NOT NULL
          AND d.date_key IS NULL
    ) AS unmatched_date_keys
FROM warehouse.fact_performance_rating f
LEFT JOIN warehouse.dim_date d
    ON f.review_date_key = d.date_key;


-- 3. RECRUITMENT JOB-KEY VALIDATION
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE f.job_key IS NULL
    ) AS missing_job_keys,
    COUNT(*) FILTER (
        WHERE f.job_key IS NOT NULL
          AND d.job_key IS NULL
    ) AS unmatched_job_keys
FROM warehouse.fact_recruitment f
LEFT JOIN warehouse.dim_job d
    ON f.job_key = d.job_key;


-- 4. DUPLICATE DIMENSION PRIMARY-KEY CHECKS
SELECT employee_key, COUNT(*) AS occurrences
FROM warehouse.dim_employee
GROUP BY employee_key
HAVING COUNT(*) > 1;

SELECT date_key, COUNT(*) AS occurrences
FROM warehouse.dim_date
GROUP BY date_key
HAVING COUNT(*) > 1;

SELECT department_key, COUNT(*) AS occurrences
FROM warehouse.dim_department
GROUP BY department_key
HAVING COUNT(*) > 1;

SELECT job_key, COUNT(*) AS occurrences
FROM warehouse.dim_job
GROUP BY job_key
HAVING COUNT(*) > 1;


-- 5. FOREIGN-KEY CONSTRAINTS IN THE WAREHOUSE
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_schema = kcu.constraint_schema
   AND tc.constraint_name = kcu.constraint_name
   AND tc.table_name = kcu.table_name
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_schema = ccu.constraint_schema
   AND tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.constraint_schema = 'warehouse'
ORDER BY tc.table_name, tc.constraint_name;


-- 6. SAFE NULL CHECKS FOR IMPORTANT IDENTIFIER COLUMNS
DO $$
DECLARE
    r RECORD;
    null_count BIGINT;
BEGIN
    FOR r IN
        SELECT *
        FROM (
            VALUES
                ('fact_recruitment', 'job_key'),
                ('fact_performance_rating', 'review_date_key'),
                ('fact_identity_events', 'employee_key'),
                ('fact_identity_events', 'date_key')
        ) AS v(table_name, column_name)
        WHERE EXISTS (
            SELECT 1
            FROM information_schema.columns c
            WHERE c.table_schema = 'warehouse'
              AND c.table_name = v.table_name
              AND c.column_name = v.column_name
        )
    LOOP
        EXECUTE format(
            'SELECT COUNT(*) FROM warehouse.%I WHERE %I IS NULL',
            r.table_name,
            r.column_name
        )
        INTO null_count;

        RAISE NOTICE '%: NULL values in % = %',
            r.table_name,
            r.column_name,
            null_count;
    END LOOP;
END $$;


-- 7. RECRUITMENT JOB-KEY ORPHAN DETAILS
SELECT f.job_key, COUNT(*) AS affected_rows
FROM warehouse.fact_recruitment f
LEFT JOIN warehouse.dim_job d
    ON f.job_key = d.job_key
WHERE f.job_key IS NOT NULL
  AND d.job_key IS NULL
GROUP BY f.job_key
ORDER BY affected_rows DESC;


-- 8. PERFORMANCE RATING DATE-KEY ORPHAN DETAILS
SELECT f.review_date_key, COUNT(*) AS affected_rows
FROM warehouse.fact_performance_rating f
LEFT JOIN warehouse.dim_date d
    ON f.review_date_key = d.date_key
WHERE f.review_date_key IS NOT NULL
  AND d.date_key IS NULL
GROUP BY f.review_date_key
ORDER BY affected_rows DESC;
