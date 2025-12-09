--
-- Compliance Agent POC - PostgreSQL Database Schema
-- Generated: December 2025
-- Database Version: PostgreSQL 15
--

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

-- ==========================================
-- TABLE: users
-- Purpose: Store user accounts and roles
-- ==========================================

CREATE TABLE public.users (
    id uuid NOT NULL PRIMARY KEY,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL UNIQUE,
    role character varying(50) DEFAULT 'agent',  -- agent, reviewer, super_admin
    created_at timestamp with time zone DEFAULT now()
);

COMMENT ON TABLE public.users IS 'User accounts with role-based access control';
COMMENT ON COLUMN public.users.role IS 'User role: agent (default), reviewer, super_admin';


-- ==========================================
-- TABLE: submissions
-- Purpose: Store uploaded content for compliance checking
-- ==========================================

CREATE TABLE public.submissions (
    id uuid NOT NULL PRIMARY KEY,
    title character varying(500) NOT NULL,
    content_type character varying(50) NOT NULL,  -- html, markdown, pdf, docx
    original_content text,
    file_path character varying(1000),
    submitted_by uuid REFERENCES public.users(id),
    submitted_at timestamp with time zone DEFAULT now(),
    status character varying(50) DEFAULT 'pending'  -- pending, analyzing, completed, failed
);

COMMENT ON TABLE public.submissions IS 'Marketing content submissions for compliance analysis';
COMMENT ON COLUMN public.submissions.content_type IS 'File type: html, markdown, pdf, docx';
COMMENT ON COLUMN public.submissions.status IS 'Analysis status: pending, analyzing, completed, failed';


-- ==========================================
-- TABLE: rules
-- Purpose: Compliance rules for IRDAI, Brand, and SEO
-- ==========================================

CREATE TABLE public.rules (
    id uuid NOT NULL PRIMARY KEY,
    category character varying(20) NOT NULL,  -- irdai, brand, seo
    rule_text text NOT NULL,
    severity character varying(20) NOT NULL,  -- critical, high, medium, low
    keywords jsonb,
    pattern character varying(1000),
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    points_deduction numeric(5,2) DEFAULT -5.00,  -- Phase 2: Configurable scoring
    created_by uuid REFERENCES public.users(id) ON DELETE SET NULL  -- Phase 2: Attribution
);

COMMENT ON TABLE public.rules IS 'Compliance rules with configurable point deductions';
COMMENT ON COLUMN public.rules.category IS 'Rule category: irdai (regulations), brand (guidelines), seo (optimization)';
COMMENT ON COLUMN public.rules.severity IS 'Severity level: critical, high, medium, low';
COMMENT ON COLUMN public.rules.points_deduction IS 'Points deducted when rule is violated (negative value)';
COMMENT ON COLUMN public.rules.created_by IS 'Super admin who created/uploaded this rule';

-- Indexes for performance
CREATE INDEX ix_rules_category ON public.rules(category);
CREATE INDEX ix_rules_severity ON public.rules(severity);
CREATE INDEX ix_rules_is_active ON public.rules(is_active);
CREATE INDEX ix_rules_created_by ON public.rules(created_by);


-- ==========================================
-- TABLE: compliance_checks
-- Purpose: Store compliance analysis results
-- ==========================================

CREATE TABLE public.compliance_checks (
    id uuid NOT NULL PRIMARY KEY,
    submission_id uuid REFERENCES public.submissions(id) ON DELETE CASCADE,
    check_date timestamp with time zone DEFAULT now(),
    overall_score numeric(5,2),
    irdai_score numeric(5,2),
    brand_score numeric(5,2),
    seo_score numeric(5,2),
    status character varying(50),  -- passed, flagged, failed
    ai_summary text,
    grade character varying(2)  -- A, B, C, D, F
);

COMMENT ON TABLE public.compliance_checks IS 'Results of AI compliance analysis';
COMMENT ON COLUMN public.compliance_checks.overall_score IS 'Weighted score: (IRDAI*0.5) + (Brand*0.3) + (SEO*0.2)';
COMMENT ON COLUMN public.compliance_checks.grade IS 'Letter grade: A(90-100), B(80-89), C(70-79), D(60-69), F(<60)';
COMMENT ON COLUMN public.compliance_checks.status IS 'passed (>=80), flagged (60-79), failed (<60)';

CREATE INDEX ix_compliance_checks_submission_id ON public.compliance_checks(submission_id);
CREATE INDEX ix_compliance_checks_status ON public.compliance_checks(status);


-- ==========================================
-- TABLE: violations
-- Purpose: Store individual rule violations
-- ==========================================

CREATE TABLE public.violations (
    id uuid NOT NULL PRIMARY KEY,
    check_id uuid REFERENCES public.compliance_checks(id) ON DELETE CASCADE,
    rule_id uuid REFERENCES public.rules(id),
    severity character varying(20) NOT NULL,
    category character varying(20) NOT NULL,
    description text NOT NULL,
    location character varying(500),
    current_text text,
    suggested_fix text,
    is_auto_fixable boolean DEFAULT false
);

COMMENT ON TABLE public.violations IS 'Individual compliance violations found in content';
COMMENT ON COLUMN public.violations.is_auto_fixable IS 'Whether AI can automatically fix this violation';

CREATE INDEX ix_violations_check_id ON public.violations(check_id);
CREATE INDEX ix_violations_rule_id ON public.violations(rule_id);
CREATE INDEX ix_violations_severity ON public.violations(severity);


-- ==========================================
-- TABLE: deep_analysis
-- Purpose: Line-by-line compliance analysis (Phase 2+)
-- ==========================================

CREATE TABLE public.deep_analysis (
    id uuid NOT NULL PRIMARY KEY,
    check_id uuid NOT NULL UNIQUE REFERENCES public.compliance_checks(id) ON DELETE CASCADE,
    total_lines numeric(10,0) DEFAULT 0,
    average_score numeric(5,2) DEFAULT 100.0,
    min_score numeric(5,2) DEFAULT 100.0,
    max_score numeric(5,2) DEFAULT 100.0,
    document_title text,
    severity_config_snapshot jsonb NOT NULL,  -- Governance: exact weights used
    status text DEFAULT 'pending',  -- pending, processing, completed, failed
    analysis_data jsonb DEFAULT '[]',  -- Complete line-by-line analysis
    created_at timestamp with time zone DEFAULT now()
);

COMMENT ON TABLE public.deep_analysis IS 'Line-by-line compliance analysis with governance tracking';
COMMENT ON COLUMN public.deep_analysis.severity_config_snapshot IS 'Snapshot of severity weights used for this analysis (audit trail)';
COMMENT ON COLUMN public.deep_analysis.analysis_data IS 'JSON array of line-by-line analysis results with rule impacts';
COMMENT ON COLUMN public.deep_analysis.status IS 'Analysis status: pending, processing, completed, failed';

CREATE INDEX ix_deep_analysis_check_id ON public.deep_analysis(check_id);
CREATE INDEX ix_deep_analysis_status ON public.deep_analysis(status);


-- ==========================================
-- TABLE: knowledge_base
-- Purpose: Store regulatory documents for RAG (Phase 2+)
-- ==========================================

CREATE TABLE public.knowledge_base (
    id uuid NOT NULL PRIMARY KEY,
    country_code character varying(10) NOT NULL,
    regulation_name character varying(255) NOT NULL,
    document_title character varying(500),
    content text NOT NULL,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

COMMENT ON TABLE public.knowledge_base IS 'Regulatory documents for Retrieval-Augmented Generation (RAG)';
COMMENT ON COLUMN public.knowledge_base.country_code IS 'ISO country code (e.g., IN for India)';
COMMENT ON COLUMN public.knowledge_base.regulation_name IS 'Name of regulation (e.g., IRDAI Marketing Guidelines)';

CREATE INDEX ix_knowledge_base_country_code ON public.knowledge_base(country_code);
CREATE INDEX ix_knowledge_base_regulation_name ON public.knowledge_base(regulation_name);


-- ==========================================
-- TABLE: agent_executions
-- Purpose: Track agent execution for observability (Phase 2+)
-- ==========================================

CREATE TABLE public.agent_executions (
    id uuid NOT NULL PRIMARY KEY,
    agent_type character varying(50) NOT NULL,
    session_id uuid NOT NULL,
    user_id uuid REFERENCES public.users(id) ON DELETE SET NULL,
    status character varying(20) DEFAULT 'running',  -- running, completed, failed
    input_data jsonb,
    output_data jsonb,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    total_tokens_used integer DEFAULT 0,
    execution_time_ms integer
);

COMMENT ON TABLE public.agent_executions IS 'Agent execution tracking for observability and debugging';
COMMENT ON COLUMN public.agent_executions.agent_type IS 'Type of agent executed (e.g., compliance_analyzer, rule_generator)';
COMMENT ON COLUMN public.agent_executions.session_id IS 'Session identifier for grouping related executions';

CREATE INDEX ix_agent_executions_agent_type ON public.agent_executions(agent_type);
CREATE INDEX ix_agent_executions_session_id ON public.agent_executions(session_id);
CREATE INDEX ix_agent_executions_status ON public.agent_executions(status);


-- ==========================================
-- TABLE: tool_invocations
-- Purpose: Track individual tool calls by agents (Phase 2+)
-- ==========================================

CREATE TABLE public.tool_invocations (
    id uuid NOT NULL PRIMARY KEY,
    execution_id uuid REFERENCES public.agent_executions(id) ON DELETE CASCADE,
    tool_name character varying(100) NOT NULL,
    tool_input jsonb,
    tool_output jsonb,
    status character varying(20) DEFAULT 'running',  -- running, success, error
    error_message text,
    invoked_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    tokens_used integer DEFAULT 0
);

COMMENT ON TABLE public.tool_invocations IS 'Individual tool calls made by agents during execution';
COMMENT ON COLUMN public.tool_invocations.tool_name IS 'Name of the tool invoked (e.g., ollama_chat, rule_lookup)';

CREATE INDEX ix_tool_invocations_execution_id ON public.tool_invocations(execution_id);
CREATE INDEX ix_tool_invocations_tool_name ON public.tool_invocations(tool_name);
CREATE INDEX ix_tool_invocations_status ON public.tool_invocations(status);


-- ==========================================
-- TABLE: alembic_version
-- Purpose: Track database migrations
-- ==========================================

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL PRIMARY KEY
);

COMMENT ON TABLE public.alembic_version IS 'Alembic migration version tracking';


-- ==========================================
-- Database Relationships Summary
-- ==========================================

/*
ENTITY RELATIONSHIPS:

users (1) ─────< (N) submissions
users (1) ─────< (N) rules (created_by)
users (1) ─────< (N) agent_executions

submissions (1) ─────< (N) compliance_checks

compliance_checks (1) ─────< (N) violations
compliance_checks (1) ───── (1) deep_analysis

rules (1) ─────< (N) violations

agent_executions (1) ─────< (N) tool_invocations

SCORING ALGORITHM:
- Base score: 100 points
- Deduction per violation: rules.points_deduction (configurable)
- Category weights: IRDAI (50%), Brand (30%), SEO (20%)
- Overall = (irdai_score * 0.50) + (brand_score * 0.30) + (seo_score * 0.20)

GRADING SCALE:
- A: 90-100 (Excellent)
- B: 80-89 (Good)
- C: 70-79 (Acceptable)
- D: 60-69 (Poor)
- F: <60 (Failed)

STATUS DETERMINATION:
- passed: overall_score >= 80
- flagged: 60 <= overall_score < 80
- failed: overall_score < 60
*/
