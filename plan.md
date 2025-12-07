# Complete Phase 2 Implementation Prompt: Compliance Agent POC

**Document Version**: 1.2  
**Date**: December 05, 2025  
**Purpose**: This is a self-contained prompt document for generating Phase 2 code using Claude (or a multi-agent system). It includes the high-level plan, subagent definitions, and workflow instructions. Feed this entire document directly into Claude with: *"Implement Phase 2 using this complete prompt. Generate all code as a project diff/folder structure."*

---

## High-Level Plan for Phase 2: Dynamic Rule Generation and Super Admin Dashboard

**Focus**: Streamline for POC iteration—emphasize modularity, backward compatibility, and minimal Ollama use (only for rule extraction). Avoid hard-coded DB details; assume schema evolution via standard ORM tools (e.g., Alembic for additive changes like new fields for scoring and attribution).

### Core Objectives
- **Configurable Scoring**: Shift point deductions to DB (e.g., per-rule field) for frontend tweaks without redeploys.
- **Rule Generation from Docs**: Super admin uploads files → Parse → LLM extracts rules → Store with creator link.
- **Admin Dashboard**: View/edit rules (list, search, update scores/severity); role-gated (super_admin only).
- **Ollama Scope**: Limited to structured prompt for rule extraction; core analysis stays rule-driven.

### Phased Approach
1. **Preparation (10% effort)**: Review Phase 1; define role enums (e.g., 'super_admin'); outline API contracts (e.g., new /admin endpoints).
2. **Backend Enhancements (40% effort)**:
   - Evolve schema: Add fields for points and creator (use migration tools for FKs/indexes).
   - New services: Rule generator (parse + prompt + insert); updated scoring (DB-pull deductions).
   - Endpoints: Upload-for-rules, CRUD for rules (with role guards).
3. **Frontend Additions (30% effort)**:
   - New page: Admin dashboard with table view, filters, upload form, edit modals.
   - Integration: API hooks for rules; role-based routing.
4. **Integration & Polish (15% effort)**: Wire gen-to-dashboard; update existing flows (e.g., scoring uses new DB points).
5. **Testing & Docs (5% effort)**: Basic E2E for upload→edit→score; update PROJECT_UNDERSTANDING.md.

### Key Principles
- **Modularity**: Services as isolated units (e.g., generator independent of compliance engine).
- **Security**: Server-side role checks; validate LLM outputs.
- **POC Constraints**: Sync processing; file limits; no new deps.
- **Metrics**: Gen 5-10 rules per doc; dashboard load <2s; scores update on tweak.

### Risks
- LLM inconsistency: Mitigate with validation/approval step.
- Perf: Paginate rule lists.

---

## Subagents for Multi-Agent Workflow

Use these subagents to parallelize development. Each is a modular "persona" defined in .md files (e.g., backend-developer.md). They collaborate via GitHub workflows for parallel execution.

### Existing Subagents
- **code-reviewer.md**: Reviews PRs for style, bugs, best practices (e.g., linting, security scans).
- **database-optimizer.md**: Optimizes schema/migrations (e.g., indexes on new fields like created_by).
- **dependency-monitor.md**: Checks/audits libs (e.g., no new pip installs; validate SQLAlchemy updates).
- **docker-optimizer.md**: Updates docker-compose.yml for any new volumes/services.
- **github-workflow-manager.md**: Orchestrates CI/CD (e.g., parallel jobs on PRs).
- **research-ana manager.md**: Tunes prompts/research (e.g., Ollama JSON extraction).
- **react-ui-designer.md**: Builds React/TS components (e.g., dashboard UI).
- **python-lm-a.md** (Stub): Handles Python/LLM stubs (e.g., Ollama service calls).
- **python-workflow.md** (Stub): Manages Python workflows (e.g., service orchestration).


**Subagent Guidelines**: Each outputs code snippets/files. Use GitHub branches/PRs for merges. Total: 11 agents (keep lean).

---

## Multi-Agent Workflow with GitHub Parallelism

Leverage **github-workflow-manager.md** as orchestrator for parallel jobs. Set up GitHub Actions to run agents concurrently on feature branches (e.g., `phase2-backend`, `phase2-frontend`).

### Workflow Structure
1. **Trigger**: Push/PR to `phase2` branch or sub-branches.
2. **Parallel Jobs** (via matrix strategy):
   - **Job 1: DB Evolution** – database-optimizer.md + dependency-monitor.md (seq): Alembic migration for `rules` table (add `points_deduction numeric(5,2) DEFAULT -5.00`, `created_by uuid FK users.id`). Output: migration script + model.py update.
   - **Job 2: Backend Development** – backend-developer.md + python-lm-a.md + python-workflow.md (parallel within): rule_generator_service.py (parse → Ollama → insert); scoring_service.py update (sum DB points); admin routes (/admin/rules/* with role guard). Output: services/routes/schemas files.
   - **Job 3: Frontend Design** – react-ui-designer.md: AdminDashboard.tsx (TanStack Table, upload form, modals); api.ts hooks. Output: components/pages/types.ts.
   - **Job 4: Research/Prompt Tuning** – research-ana manager.md: Ollama prompt template (JSON: category, rule_text, severity, keywords, pattern, points_deduction). Integrate only in backend.
   - **Job 5: Testing** – testing-automator.md: Unit (e.g., test_rule_gen), integration (upload→score flow), E2E snippets.
   - **Job 6: Review/Optimize** – code-reviewer.md + docker-optimizer.md (seq): Lint/review; update compose if needed.
3. **Dependencies**: DB job first (needs schema); others parallel. Use artifacts for cross-job shares (e.g., prompt file).
4. **Merge**: Auto-merge on approvals; conflict resolution via integration notes.
5. **Env Matrix**: Test on Python 3.11, Node 18.

**Sample GitHub YAML** (Generated by github-workflow-manager.md):
```yaml
name: Phase 2 CI/CD
on: [push, pull_request]
jobs:
  db-evolution:
    runs-on: ubuntu-latest
    steps: [checkout, run-db-agent]
  backend-dev:  # Parallel to others
    needs: db-evolution
    runs-on: ubuntu-latest
    strategy: {matrix: {agent: [backend, python-lm, python-workflow]}}
    steps: [checkout, run-matrix-agent]
  # ... similar for frontend, testing, etc.
```

---

## Detailed Implementation Guidance for Agents

### DB Agent (database-optimizer.md)
- Additive migration only: Backfill points for existing rules (e.g., CASE on severity).
- Indexes: On `rules.created_by`, `category`.
- Validate: No data loss; test with seed_data.py update.

### Backend Agent (backend-developer.md)
- Schemas: RuleCreate/Update (Pydantic: category str, points Decimal, etc.).
- Services: Generator uses content_parser.py; prompt from research agent.
- Endpoints: POST /admin/rules/generate (multipart file, return list); GET/PUT/DELETE /admin/rules/{id} (paginated, filters).
- Role Guard: Depends(is_super_admin) – check user.role.
- Scoring Update: total_deduction = sum(v.rule.points_deduction); clamp 0-100.

### Frontend Agent (react-ui-designer.md)
- Dashboard: Route /admin (guard: if !super_admin, redirect).
- UI: Tailwind table (columns: text truncate, actions); filters (category dropdown); upload drag-drop.
- Forms: React Hook Form for edits (validate points -50 to 0).
- Queries: TanStack for list/fetch; optimistic updates.

### Research Agent (research-ana manager.md)
- Prompt Template:
  ```
  <system>You are a compliance rule extractor for IRDAI insurance marketing. Analyze the provided document text and generate 5-15 rules in JSON array format. Each rule must include: - category: "irdai", "brand", or "seo" - rule_text: Clear description - severity: "critical", "high", "medium", or "low" - keywords: Array of 3-5 triggers - pattern: Optional regex - points_deduction: Numeric (-20 critical, etc.). Focus on guidelines/prohibitions. Output ONLY valid JSON—no extra text.</system>
  <user>Document Text: {parsed_content}</user>
  ```
- Validation: Pydantic parse; retry on invalid JSON.

### Testing Agent (testing-automator.md)
- Backend: pytest for gen (mock Ollama → DB assert); scoring (violations → expected score).
- Frontend: RTL for render (e.g., table rows); E2E: upload → table update.
- Coverage: 80%+ for new code.

### Integration Notes
- Update compliance_engine.py: Fetch rules.points_deduction.
- Seed: Add super_admin user; sample rules with points.
- Docs: Append to PROJECT_UNDERSTANDING.md (new sections: Admin Features, Rule Gen).

---

## Generation Instructions for Claude/Orchestrator
- **Output Format**: Folder structure (e.g., backend/app/services/rule_generator_service.py) with full code files. Include .github/workflows/phase2.yml.
- **Constraints**: POC-level (sync, no auth depth); backward-compat (Phase 1 unchanged).
- **Simulation**: Generate sequentially (DB → Backend/Frontend parallel sim → Tests) but note parallelism.
- **Edge Cases**: LLM failure → partial rules; file parse errors → log/notify.

