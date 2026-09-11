--
-- PostgreSQL database dump
--

\restrict IWlFcvqGD3Lq7VJrsQoqdfffoAX02yNJUIfN1Aptz0fcckFF88j3bxdKc9AxhbC

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

-- Started on 2026-09-11 00:58:36

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 16401)
-- Name: staging; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA staging;


ALTER SCHEMA staging OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 227 (class 1259 OID 16448)
-- Name: stg_access_control; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_access_control (
    id integer,
    resource integer,
    mgr_id integer,
    role_rollup_1 integer,
    role_rollup_2 integer,
    role_deptname integer,
    role_title integer,
    role_family_desc integer,
    role_family integer,
    role_code integer,
    target integer
);


ALTER TABLE staging.stg_access_control OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16418)
-- Name: stg_ai_fair_recruitment; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_ai_fair_recruitment (
    aptitude_test_score text,
    skill_score text,
    candidate_id text,
    hiring_decision text,
    gender text,
    education_level text,
    experience_years text,
    previous_companies text,
    communication_score text,
    technical_test_score text,
    job_role_applied text,
    certifications_count text,
    interview_score text,
    expected_salary text,
    age text,
    "Location" text
);


ALTER TABLE staging.stg_ai_fair_recruitment OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16435)
-- Name: stg_attendance_xml; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_attendance_xml (
    xml_data_type_description character varying(25),
    xml_element_id bigint,
    xml_parent_element_id bigint,
    xml_element_level bigint,
    xml_path character varying(1024),
    xml_parent_path character varying(1024),
    attendance_field character varying(1024),
    attendance_value character varying(1024)
);


ALTER TABLE staging.stg_attendance_xml OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16402)
-- Name: stg_employee_performance; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_employee_performance (
    employee_id bigint,
    department character varying(16),
    gender character varying(6),
    age bigint,
    job_title character varying(10),
    hire_date character varying(26),
    years_at_company bigint,
    education_level character varying(11),
    performance_score bigint,
    monthly_salary numeric(7,1),
    work_hours_per_week bigint,
    projects_handled bigint,
    overtime_hours bigint,
    sick_days bigint,
    remote_work_frequency bigint,
    team_size bigint,
    training_hours bigint,
    promotions bigint,
    employee_satisfaction_score numeric(6,2),
    resigned boolean
);


ALTER TABLE staging.stg_employee_performance OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16410)
-- Name: stg_hr_employee; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_hr_employee (
    "﻿employeeid" character varying(9),
    firstname character varying(15),
    lastname character varying(25),
    gender character varying(17),
    age bigint,
    businesstravel character varying(18),
    department character varying(15),
    "DistanceFromHome (KM)" bigint,
    "State" character varying(2),
    ethnicity character varying(32),
    education bigint,
    educationfield character varying(19),
    jobrole character varying(25),
    maritalstatus character varying(8),
    salary bigint,
    stockoptionlevel bigint,
    overtime character varying(3),
    hiredate timestamp without time zone,
    attrition character varying(3),
    yearsatcompany bigint,
    yearsinmostrecentrole bigint,
    yearssincelastpromotion bigint,
    yearswithcurrmanager bigint
);


ALTER TABLE staging.stg_hr_employee OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 16592)
-- Name: stg_hr_saas_employee_master; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_hr_saas_employee_master (
    employee_id integer,
    first_name text,
    last_name text,
    gender text,
    pronouns text,
    age integer,
    birth_date text,
    department text,
    business_unit text,
    job_level integer,
    job_title text,
    location text,
    manager_id text,
    base_salary integer,
    bonus_eligible boolean,
    bonus_pct numeric,
    equity_grant boolean,
    equity_pct numeric,
    employment_type text,
    employment_status text,
    hire_date text,
    termination_date text,
    ethnicity text,
    marital_status text,
    education_level text,
    pay_frequency text,
    veteran_status boolean,
    disability_status boolean,
    cost_center text,
    fte double precision,
    exemption_status text,
    high_potential_flag boolean,
    succession_plan_status text,
    aihr_certified boolean,
    training_count integer,
    last_training_date text,
    promotion_count integer,
    last_promotion_date text
);


ALTER TABLE staging.stg_hr_saas_employee_master OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 16643)
-- Name: stg_hr_saas_leave_requests; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_hr_saas_leave_requests (
    employee_id integer,
    request_date text,
    leave_type text,
    approval_status text,
    absence_code text
);


ALTER TABLE staging.stg_hr_saas_leave_requests OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 16653)
-- Name: stg_hr_saas_snapshots; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_hr_saas_snapshots (
    xml_data_type_description character varying(25),
    xml_element_id bigint,
    xml_parent_element_id bigint,
    xml_element_level bigint,
    xml_path character varying(1024),
    xml_parent_path character varying(1024),
    xml_data_name character varying(1024),
    xml_data_value character varying(1024)
);


ALTER TABLE staging.stg_hr_saas_snapshots OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16405)
-- Name: stg_human_resource; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_human_resource (
    employee_id character varying(11),
    first_name character varying(11),
    last_name character varying(11),
    gender character varying(6),
    state character varying(14),
    city character varying(14),
    hiredate timestamp without time zone,
    department character varying(16),
    job_title character varying(31),
    education_level character varying(11),
    salary bigint,
    performance_rating character varying(17),
    overtime character varying(3),
    birthdate timestamp without time zone,
    termdate timestamp without time zone
);


ALTER TABLE staging.stg_human_resource OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 16659)
-- Name: stg_leave; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_leave (
    "Employee Name" character varying(21),
    department character varying(10),
    "Position" character varying(21),
    "Leave Type" character varying(15),
    "Start Date" date,
    "End Date" date,
    "Days Taken" bigint,
    "Total Leave Entitlement" bigint,
    "Leave Taken So Far" bigint,
    "Remaining Leaves" bigint,
    month character varying(3)
);


ALTER TABLE staging.stg_leave OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16423)
-- Name: stg_payroll; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_payroll (
    "Emp Count" double precision,
    "Employee ID" character varying(50),
    "First Name" text,
    "Last Name" text,
    "Business Unit Code" text,
    "Busines Unit Name" text,
    "Continuous Service Date" text,
    "Country Name" text,
    "Date Of Birth" text,
    age double precision,
    "Age Range" text,
    "Date Of Joining" text,
    experience text,
    tenure text,
    "Date Of Termination" timestamp without time zone,
    "EfectiveStart Date" timestamp without time zone,
    "Effective End Date" timestamp without time zone,
    "Employee Catagery" text,
    "Employee Status" text,
    "Employee Type" text,
    etinicity text,
    departments text,
    gender text,
    grade text,
    designations text,
    "Last Working Date" timestamp without time zone,
    "Leave Status" text,
    country text,
    "Martial Status" text,
    continent text,
    frequency text,
    "Payroll Employee Status" text,
    "Payroll End Date" timestamp without time zone,
    "Payroll Start Date" timestamp without time zone,
    "Pay Period " timestamp without time zone,
    "ReHire Date" text,
    "Resignation Date" text,
    "Basic Salary" double precision,
    allowance double precision,
    "Statutory Bonus" double precision,
    "Gross Salary" double precision,
    "Arrear Special Allowance" double precision,
    "Total Deductions" text,
    "Arrear Statutory Bonus" text,
    "Net Salary" double precision,
    "Tax Spend" double precision,
    "Reimbursement Paid" double precision
);


ALTER TABLE staging.stg_payroll OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 16541)
-- Name: stg_performance_eval_audio; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_performance_eval_audio (
    employee_id integer,
    speech_sentiment_score integer,
    speech_energy_level integer,
    speech_clarity_score integer,
    tone_consistency_score integer,
    speaking_speed integer,
    pause_frequency integer,
    pitch_variation integer,
    volume_stability_score integer,
    performance_rating text
);


ALTER TABLE staging.stg_performance_eval_audio OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16490)
-- Name: stg_performance_eval_behavior; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_performance_eval_behavior (
    employee_id integer,
    meetings_attended integer,
    collaboration_score integer,
    punctuality_score integer,
    training_hours_completed numeric,
    work_engagement_score integer,
    peer_interaction_score integer,
    initiative_score integer,
    task_followup_score integer,
    performance_rating character varying
);


ALTER TABLE staging.stg_performance_eval_behavior OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 16485)
-- Name: stg_performance_eval_structured; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_performance_eval_structured (
    xml_data_type_description character varying(25),
    xml_element_id bigint,
    xml_parent_element_id bigint,
    xml_element_level bigint,
    xml_path character varying(1024),
    xml_parent_path character varying(1024),
    xml_data_name character varying(1024),
    xml_data_value character varying(1024)
);


ALTER TABLE staging.stg_performance_eval_structured OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16413)
-- Name: stg_performance_rating; Type: TABLE; Schema: staging; Owner: postgres
--

CREATE TABLE staging.stg_performance_rating (
    "﻿performanceid" character varying(6),
    employeeid character varying(9),
    reviewdate timestamp without time zone,
    environmentsatisfaction bigint,
    jobsatisfaction bigint,
    relationshipsatisfaction bigint,
    trainingopportunitieswithinyear bigint,
    trainingopportunitiestaken bigint,
    worklifebalance bigint,
    selfrating bigint,
    managerrating bigint
);


ALTER TABLE staging.stg_performance_rating OWNER TO postgres;

-- Completed on 2026-09-11 00:58:37

--
-- PostgreSQL database dump complete
--

\unrestrict IWlFcvqGD3Lq7VJrsQoqdfffoAX02yNJUIfN1Aptz0fcckFF88j3bxdKc9AxhbC

