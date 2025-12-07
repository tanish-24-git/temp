# Compliance Agent POC - MVP

AI-powered compliance checking system for insurance marketing content using Ollama.

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
└── .env.example              # Environment variables template
```

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
