# Compliance Agent POC - MVP

AI-powered compliance checking system for insurance marketing content using Ollama.

## 📖 Application Concept

### Overview

The **Compliance Agent POC** is an intelligent, AI-powered system designed to automatically validate insurance marketing content against **IRDAI (Insurance Regulatory and Development Authority of India) regulations**, **brand guidelines**, and **SEO best practices**. This system combines rule-based validation with advanced LLM analysis to provide comprehensive compliance checking, violation detection, and automated fix suggestions.

### Core Purpose

Insurance companies must ensure all marketing materials comply with strict regulatory requirements. Manual compliance checking is:
- Time-consuming and resource-intensive
- Prone to human error
- Difficult to scale across large content volumes
- Challenging to maintain consistency

This system automates compliance validation, providing instant feedback on regulatory violations, brand guideline adherence, and SEO optimization opportunities.

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  (React + TypeScript Dashboard - Upload, Review, Results)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Layer: Upload, Analysis, Admin, Dashboard          │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │  Business Logic Layer                                     │  │
│  │  • Compliance Engine (Core Analysis)                     │  │
│  │  • Ollama Service (LLM Integration)                      │  │
│  │  • Scoring Service (Point Calculation)                   │  │
│  │  • Rule Generator (Dynamic Rule Creation)                │  │
│  │  • Deep Analysis Engine (Line-by-Line)                   │  │
│  │  • Content Parser (PDF/DOCX/HTML/MD)                     │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────▼────────┐ ┌─────▼─────┐ ┌────────▼────────┐
│   PostgreSQL    │ │   Ollama  │ │     Redis       │
│   (Database)    │ │   (LLM)   │ │    (Cache)      │
│                 │ │ qwen2.5:7b│ │                 │
│ • Users         │ │           │ │ • Sessions      │
│ • Submissions   │ │ AI Models │ │ • Analysis      │
│ • Rules         │ │           │ │   Queue         │
│ • Violations    │ │           │ │                 │
│ • Deep Analysis │ │           │ │                 │
│ • Knowledge Base│ │           │ │                 │
└─────────────────┘ └───────────┘ └─────────────────┘
```

### Complete Workflow

#### 1. **Content Submission** 
```
User uploads content → System parses file → Extracts text → Stores in database
Supported formats: HTML, Markdown, PDF, DOCX
```

#### 2. **Compliance Analysis**
```
Trigger analysis → Load active rules from DB → Build AI prompt with rules
                     ↓
              Send to Ollama LLM
                     ↓
       Parse AI response (violations + suggestions)
                     ↓
       Calculate category scores (IRDAI, Brand, SEO)
                     ↓
       Compute weighted overall score
                     ↓
       Store results + violations in database
```

#### 3. **Deep Analysis (Optional)**
```
Line-by-line analysis → Each line scored independently
                        ↓
             Track which rules affect each line
                        ↓
             Store detailed impact analysis
                        ↓
             Generate governance audit trail
```

#### 4. **Results Review**
```
View dashboard → See overall scores and grades
                 ↓
      Drill into violations by category
                 ↓
      Review AI-suggested fixes
                 ↓
      Apply corrections manually or auto-fix
```

#### 5. **Rule Management (Super Admin)**
```
Upload regulatory document → AI extracts rules automatically
                              ↓
                   Rules validated and stored
                              ↓
                   Configurable point deductions
                              ↓
                   Rules immediately active for analysis
```

### Key Components

#### **Compliance Engine**
- Core analysis orchestrator
- Coordinates between rule loading, AI analysis, and scoring
- Implements retry logic and error handling
- Generates structured compliance reports

#### **Ollama LLM Integration**
- Uses Qwen 2.5 (7B parameter model) for intelligent analysis
- Structured prompt engineering for consistent outputs
- Violation detection beyond simple keyword matching
- Context-aware suggestion generation
- Rule extraction from regulatory documents

#### **Scoring System**
- **Configurable Point Deductions**: Each rule has customizable penalty points
- **Category-Based Scoring**: Separate scores for IRDAI, Brand, SEO
- **Weighted Overall Score**: IRDAI (50%), Brand (30%), SEO (20%)
- **Dynamic Recalculation**: Scores update when rule points are adjusted
- **Grading System**: A-F letter grades based on overall performance

#### **Rule Management System** (Phase 2)
- **Dynamic Rule Generation**: Upload PDFs/DOCX → AI extracts rules
- **Manual Rule Creation**: Admin interface for custom rules
- **Rule Attribution**: Track which super admin created each rule
- **Configurable Penalties**: Adjust point deductions without redeployment
- **Rule Activation**: Enable/disable rules without deletion

#### **Deep Analysis Engine** (Phase 2+)
- **Line-by-Line Scoring**: Individual compliance score per line
- **Rule Impact Tracking**: See which rules affect each line
- **Governance Audit Trail**: Snapshot of severity weights used
- **Statistical Summary**: Min/max/average scores across document
- **Performance Optimized**: JSON storage for fast retrieval

### Database Schema

The system uses **10 core tables** (see `db_schema.sql` for complete schema):

1. **users** - User accounts with role-based access (agent, reviewer, super_admin)
2. **submissions** - Uploaded marketing content for analysis
3. **rules** - Compliance rules with configurable scoring weights
4. **compliance_checks** - High-level analysis results with scores and grades
5. **violations** - Individual rule violations with suggested fixes
6. **deep_analysis** - Line-by-line analysis with JSON storage
7. **knowledge_base** - Regulatory documents for RAG (Retrieval-Augmented Generation)
8. **agent_executions** - Agent execution tracking for observability
9. **tool_invocations** - Individual tool calls made by agents
10. **alembic_version** - Database migration versioning

**Key Relationships**:
- Users → Submissions (1:N) - Track who uploaded content
- Users → Rules (1:N) - Track who created rules  
- Submissions → Compliance Checks (1:N) - Multiple analyses per submission
- Compliance Checks → Violations (1:N) - Multiple violations per check
- Compliance Checks → Deep Analysis (1:1) - Optional detailed analysis
- Rules → Violations (1:N) - Track which rules triggered violations
- Agent Executions → Tool Invocations (1:N) - Observability tracking

### Scoring Algorithm

```python
# Base score for each category
base_score = 100.0

# Deduct points for each violation
for violation in violations:
    rule = get_rule(violation.rule_id)
    category_score -= rule.points_deduction  # e.g., -20 for critical, -5 for medium

# Ensure scores don't go below 0
category_score = max(0, min(100, category_score))

# Calculate weighted overall score
overall_score = (irdai_score * 0.50) + \
                (brand_score * 0.30) + \
                (seo_score * 0.20)

# Determine grade and status
grade = calculate_grade(overall_score)  # A-F
status = "passed" if overall_score >= 80 else \
         "flagged" if overall_score >= 60 else "failed"
```

**Default Point Deductions** (Configurable):
- Critical violations: -20 points
- High severity: -10 points
- Medium severity: -5 points
- Low severity: -2 points

### Technology Stack

**Backend**:
- FastAPI (Python 3.11) - High-performance async API framework
- PostgreSQL 15 - Relational database with JSONB support
- SQLAlchemy 2.0 - Modern ORM with async capabilities
- Alembic - Database migration management
- Redis 7 - Caching and session storage

**AI/ML**:
- Ollama - Local LLM inference
- Qwen 2.5 (7B) - Primary language model
- Structured prompt engineering for consistency
- JSON-based output parsing

**Frontend**:
- React 18 with TypeScript - Type-safe UI development
- Vite 5 - Fast build tooling
- Tailwind CSS - Utility-first styling
- TanStack Table - High-performance data grids
- Axios - HTTP client with interceptors

**DevOps**:
- Docker & Docker Compose - Containerization 
- Multi-stage builds for optimization
- Health checks and auto-restart policies

### Security & Access Control

**Role-Based Access Control (RBAC)**:
- **Agent**: Upload content, view own submissions, trigger analysis
- **Reviewer**: View all submissions, approve content
- **Super Admin**: Full access + rule management + user management

**Current Implementation** (POC):
- Header-based authentication (`X-User-Id`)
- Role validation at API endpoint level
- Database-level foreign key constraints

**Production Roadmap**:
- JWT/OAuth2 token-based authentication
- Session management with Redis
- CSRF protection
- Content Security Policy (CSP)
- Rate limiting on uploads
- File upload virus scanning

### Advanced Features (Phase 2+)

#### **Multi-Country Support**
- Knowledge base stores regulations by country code
- Extensible to GDPR (EU), FCA (UK), SEC (US), etc.
- Locale-specific rule sets

#### **Agent Observability**
- Track every agent execution
- Monitor token usage and costs
- Debug tool invocations
- Performance optimization insights

#### **Governance & Audit Trail**
- Snapshot of rule weights used for each analysis
- Track who created/modified rules
- Immutable violation records
- Compliance report generation

### Use Cases

✅ **Marketing Teams**: Validate ad copy before publishing  
✅ **Compliance Officers**: Audit existing materials at scale  
✅ **Content Writers**: Get real-time feedback during creation  
✅ **Legal Teams**: Ensure regulatory adherence  
✅ **Operations**: Automate manual review processes  

### Performance Characteristics

- **Upload Processing**: < 2 seconds for typical documents
- **AI Analysis**: 10-30 seconds (depends on content length and Ollama performance)
- **Deep Analysis**: 15-45 seconds for line-by-line scoring
- **Dashboard Load**: < 500ms for 1000+ submissions
- **Rule Generation**: 15-35 seconds per regulatory document

**Optimization Tips**:
- Use GPU-enabled Ollama for 3-5x faster inference
- Enable Redis caching for frequently accessed data
- Implement background job queue (Celery) for async processing
- Use pagination for large datasets

---

## Features

- **Content Upload**: Support for HTML, Markdown, PDF, and DOCX files
- **AI Analysis**: Powered by Ollama (qwen2.5:7b model) for intelligent compliance checking
- **Multi-Category Scoring**: IRDAI regulations (50%), Brand guidelines (30%), SEO (20%)
- **Violation Detection**: Identifies and categorizes compliance issues with severity levels
- **Dashboard**: Real-time statistics and analytics
- **Automated Suggestions**: AI-generated fixes for compliance violations

## Prerequisites

- **Docker & Docker Compose**: For running all services
- **Git**: For version control
- **8GB+ RAM**: Recommended for running Ollama with qwen2.5:7b model

## Quick Start

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd compliance-agent-poc
```

### 2. Environment Setup

```bash
# Copy environment file
cp .env.example .env

# No changes needed for local development
```

### 3. Start All Services

```bash
# Start all containers (PostgreSQL, Redis, Ollama, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Pull Ollama Model

```bash
# This will download the qwen2.5:7b model (~4.7GB)
docker-compose exec ollama ollama pull qwen2.5:7b

# Verify model is loaded
docker-compose exec ollama ollama list
```

### 5. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed database with compliance rules
docker-compose exec backend python -m app.seed_data
```

### 6. Access Application

- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## Project Structure

```
compliance-agent-poc/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Settings and configuration
│   │   ├── database.py        # Database connection
│   │   ├── models/            # SQLAlchemy models (5 files)
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── ollama_service.py      # Ollama integration ⭐
│   │   │   ├── compliance_engine.py   # Core compliance logic ⭐
│   │   │   ├── content_parser.py      # File parsing
│   │   │   └── scoring_service.py     # Score calculation
│   │   └── api/routes/        # API endpoints
│   ├── migrations/            # Alembic database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/            # Dashboard, Upload, Submissions, Results
│   │   ├── components/       # Reusable UI components
│   │   ├── lib/              # API client, types, utilities
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml         # Service orchestration
├── db_schema.sql              # 📊 Complete database schema (10 tables)
└── .env.example              # Environment variables template
```

> 💡 **Database Schema**: See [`db_schema.sql`](./db_schema.sql) for the complete database structure with all tables, relationships, indexes, and detailed comments.

## Usage Guide

### 1. Upload Content

1. Navigate to **Upload** page
2. Enter a title for your content
3. Select content type (HTML, Markdown, PDF, or DOCX)
4. Choose file to upload
5. Click "Upload and Check Compliance"

### 2. Trigger Analysis

1. Go to **Submissions** page
2. Find your uploaded content
3. Click "Analyze" button
4. Wait for AI analysis to complete (~10-30 seconds)

### 3. View Results

- **Overall Score**: Weighted average of all categories
- **Category Scores**: IRDAI, Brand, SEO individual scores
- **Grade**: Letter grade (A-F) based on overall score
- **Violations**: Detailed list with:
  - Severity level (critical, high, medium, low)
  - Category (irdai, brand, seo)
  - Current problematic text
  - Suggested fix

## API Endpoints

### Submissions

- `POST /api/submissions/upload` - Upload content file
- `GET /api/submissions` - List all submissions
- `GET /api/submissions/{id}` - Get submission details
- `POST /api/submissions/{id}/analyze` - Trigger compliance analysis

### Compliance

- `GET /api/compliance/{submission_id}` - Get compliance check results
- `GET /api/compliance/{submission_id}/violations` - Get violations only

### Dashboard

- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/recent` - Get recent submissions

## Configuration

### Environment Variables

```bash
# Backend
DATABASE_URL=postgresql://compliance_user:compliance_pass@postgres:5432/compliance_db
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=30
OLLAMA_MAX_RETRIES=3

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

### Compliance Rules

The system comes pre-seeded with 13 compliance rules:

**IRDAI Rules (5)**:
- Misleading claims about returns
- Risk disclosure requirements
- Medical condition misrepresentation
- Competitor comparisons
- Fee disclosure

**Brand Rules (4)**:
- Use of full company name
- Prohibited words
- Tone and voice
- Visual guidelines

**SEO Rules (4)**:
- Title length optimization
- Meta description
- Keyword placement
- Image alt text

## Scoring Algorithm

```python
# Base score: 100
# Deductions per violation:
critical: -20 points
high: -10 points
medium: -5 points
low: -2 points

# Overall score (weighted):
overall = (irdai_score * 0.50) + (brand_score * 0.30) + (seo_score * 0.20)

# Status determination:
< 60: failed
< 80: flagged
>= 80: passed

# Grades:
90-100: A
80-89: B
70-79: C
60-69: D
< 60: F
```

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Ollama Not Responding

```bash
# Check Ollama status
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama

# Verify model is loaded
docker-compose exec ollama ollama list
```

### Database Issues

```bash
# Reset database
docker-compose down
docker volume rm compliance-agent-poc_postgres_data
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.seed_data
```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the ports
# Windows:
netstat -ano | findstr :5432
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Linux/Mac:
lsof -i :5432
lsof -i :8000
lsof -i :5173
```

Edit `docker-compose.yml` to use different ports.

### Slow Analysis

- **Reason**: Ollama processing time for large content
- **Solution**:
  - Use smaller model: `qwen2.5:0.5b`
  - Reduce content size (currently limited to first 3000 chars)
  - Increase timeout in `.env`: `OLLAMA_TIMEOUT=60`

## System Requirements

### Minimum

- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 20GB free space
- **OS**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)

### Recommended

- **CPU**: 8 cores
- **RAM**: 16GB
- **Storage**: 50GB SSD
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster inference)

## Known Limitations (MVP)

1. **No Authentication**: All users have same access
2. **Synchronous Analysis**: No background job queue
3. **Content Truncation**: Only first 3000 characters analyzed
4. **File Size Limit**: 50MB maximum upload
5. **Single Session**: No concurrent user handling
6. **No Real-time Updates**: Manual refresh needed
7. **Basic Error Handling**: Limited retry logic for file operations

## Future Enhancements

- [ ] JWT authentication and role-based access
- [ ] Celery for async background processing
- [ ] WebSocket for real-time progress updates
- [ ] Advanced analytics dashboard
- [ ] Rule management interface
- [ ] Auto-correction implementation
- [ ] CMS integrations (WordPress, Contentful)
- [ ] Email/Slack notifications
- [ ] Multi-language support
- [ ] Mobile app

## Technical Stack

### Backend

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0.23
- **Migrations**: Alembic 1.13.0
- **Cache**: Redis 7
- **AI**: Ollama (qwen2.5:7b)
- **HTTP Client**: HTTPX 0.25.2 (async)
- **Validation**: Pydantic 2.5.0

### Frontend

- **Framework**: React 18
- **Language**: TypeScript 5.3.3
- **Build Tool**: Vite 5.0.8
- **Styling**: Tailwind CSS 3.3.6
- **HTTP Client**: Axios 1.6.0
- **Routing**: React Router 6.20.0
- **Icons**: Lucide React
- **Date Handling**: date-fns

### DevOps

- **Containerization**: Docker & Docker Compose
- **Python**: 3.11
- **Node**: 20 (Alpine)

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs -f`
3. Create an issue on GitHub

## License

MIT License - feel free to use for your projects

## Credits

- Built following the OLLAMA_INTEGRATION_GUIDE.md patterns
- Based on plan.md 12-week architecture
- Ollama for local LLM inference
- FastAPI for modern Python APIs
- React for interactive UIs

---

**Version**: 1.0.0 MVP
**Last Updated**: December 2024
**Status**: Ready for Testing
