--
-- PostgreSQL database dump
--

\restrict t0qaFYonIg9oDrxgBUzJh5aJhfhMkPade3xQtwQVmh9Fojh9ncaIUnzIJGuXMwv

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: compliance_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO compliance_user;

--
-- Name: compliance_checks; Type: TABLE; Schema: public; Owner: compliance_user
--

CREATE TABLE public.compliance_checks (
    id uuid NOT NULL,
    submission_id uuid,
    check_date timestamp with time zone DEFAULT now(),
    overall_score numeric(5,2),
    irdai_score numeric(5,2),
    brand_score numeric(5,2),
    seo_score numeric(5,2),
    status character varying(50),
    ai_summary text,
    grade character varying(2)
);


ALTER TABLE public.compliance_checks OWNER TO compliance_user;

--
-- Name: rules; Type: TABLE; Schema: public; Owner: compliance_user
--

CREATE TABLE public.rules (
    id uuid NOT NULL,
    category character varying(20) NOT NULL,
    rule_text text NOT NULL,
    severity character varying(20) NOT NULL,
    keywords jsonb,
    pattern character varying(1000),
    is_active boolean,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.rules OWNER TO compliance_user;

--
-- Name: submissions; Type: TABLE; Schema: public; Owner: compliance_user
--

CREATE TABLE public.submissions (
    id uuid NOT NULL,
    title character varying(500) NOT NULL,
    content_type character varying(50) NOT NULL,
    original_content text,
    file_path character varying(1000),
    submitted_by uuid,
    submitted_at timestamp with time zone DEFAULT now(),
    status character varying(50)
);


ALTER TABLE public.submissions OWNER TO compliance_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: compliance_user
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    role character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO compliance_user;

--
-- Name: violations; Type: TABLE; Schema: public; Owner: compliance_user
--

CREATE TABLE public.violations (
    id uuid NOT NULL,
    check_id uuid,
    rule_id uuid,
    severity character varying(20) NOT NULL,
    category character varying(20) NOT NULL,
    description text NOT NULL,
    location character varying(500),
    current_text text,
    suggested_fix text,
    is_auto_fixable boolean
);


ALTER TABLE public.violations OWNER TO compliance_user;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: compliance_checks compliance_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.compliance_checks
    ADD CONSTRAINT compliance_checks_pkey PRIMARY KEY (id);


--
-- Name: rules rules_pkey; Type: CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.rules
    ADD CONSTRAINT rules_pkey PRIMARY KEY (id);


--
-- Name: submissions submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: violations violations_pkey; Type: CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.violations
    ADD CONSTRAINT violations_pkey PRIMARY KEY (id);


--
-- Name: compliance_checks compliance_checks_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.compliance_checks
    ADD CONSTRAINT compliance_checks_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE;


--
-- Name: submissions submissions_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(id);


--
-- Name: violations violations_check_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.violations
    ADD CONSTRAINT violations_check_id_fkey FOREIGN KEY (check_id) REFERENCES public.compliance_checks(id) ON DELETE CASCADE;


--
-- Name: violations violations_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: compliance_user
--

ALTER TABLE ONLY public.violations
    ADD CONSTRAINT violations_rule_id_fkey FOREIGN KEY (rule_id) REFERENCES public.rules(id);


--
-- PostgreSQL database dump complete
--

\unrestrict t0qaFYonIg9oDrxgBUzJh5aJhfhMkPade3xQtwQVmh9Fojh9ncaIUnzIJGuXMwv

