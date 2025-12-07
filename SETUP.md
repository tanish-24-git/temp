# Quick Setup Guide

## Prerequisites Check

Before starting, ensure you have:
- [ ] Docker Desktop installed and running
- [ ] At least 8GB RAM available
- [ ] 20GB free disk space
- [ ] Ports 5432, 6379, 8000, 5173, 11434 are free

## Step-by-Step Setup (10 minutes)

### Step 1: Environment Setup (30 seconds)

```bash
# Navigate to project directory
cd C:\Users\diwak\OneDrive\Desktop\compliance-agent-poc

# Copy environment file (no changes needed for local dev)
cp .env.example .env
```

### Step 2: Start Services (2-3 minutes)

```bash
# Start all containers
docker-compose up -d

# Wait for services to be ready (check logs)
docker-compose logs -f

# Press Ctrl+C to exit logs when you see:
# - "Starting Compliance Agent Backend"
# - "✅ Ollama service is available" OR "⚠️ Ollama service is not available"
# - Frontend: "Local: http://localhost:5173"
```

### Step 3: Pull Ollama Model (3-5 minutes)

```bash
# Download qwen2.5:7b model (~4.7GB)
docker-compose exec ollama ollama pull qwen2.5:7b

# Verify model is ready
docker-compose exec ollama ollama list
# You should see: qwen2.5:7b
```

### Step 4: Initialize Database (1 minute)

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed with compliance rules
docker-compose exec backend python -m app.seed_data

# You should see:
# ✅ Seeded 2 users
# ✅ Seeded 13 rules
# ✅ Database seeding completed!
```

### Step 5: Verify Setup (30 seconds)

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","ollama_available":true}

# Open frontend in browser
start http://localhost:5173
```

## Quick Test

1. Go to http://localhost:5173
2. Click **Upload** in navigation
3. Create a test HTML file:

```html
<!-- test.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Test Insurance Product</title>
</head>
<body>
    <h1>Guaranteed Returns Insurance</h1>
    <p>Get guaranteed returns of 20% per year!</p>
    <p>Best insurance in the market!</p>
</body>
</html>
```

4. Upload the file:
   - Title: "Test Insurance Product"
   - Type: HTML
   - File: test.html

5. Go to **Submissions** page
6. Click **Analyze** button
7. Wait 10-30 seconds
8. Click **View Results**
9. You should see violations detected!

## Common Issues

### Issue: "Port is already allocated"

```bash
# Check what's using the port
netstat -ano | findstr :8000

# Stop the process or change port in docker-compose.yml
```

### Issue: "Ollama service is not available"

```bash
# Check Ollama logs
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama

# Wait 30 seconds, then check again
docker-compose logs backend | findstr "Ollama"
```

### Issue: "Database connection failed"

```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait for it to be healthy
docker-compose ps

# Re-run migrations
docker-compose exec backend alembic upgrade head
```

## Stopping the Application

```bash
# Stop all containers (keeps data)
docker-compose stop

# Stop and remove containers (keeps data in volumes)
docker-compose down

# Complete reset (removes all data)
docker-compose down -v
```

## Restarting After Stop

```bash
# Start all services again
docker-compose up -d

# No need to re-pull Ollama model or re-seed database
# (unless you ran 'docker-compose down -v')
```

## Next Steps

Once setup is complete:

1. Read the [README.md](README.md) for full documentation
2. Explore the API docs at http://localhost:8000/docs
3. Try uploading different file types (Markdown, PDF, DOCX)
4. Experiment with different compliance violations

## Need Help?

- Check logs: `docker-compose logs -f [service_name]`
- Services: `backend`, `frontend`, `postgres`, `redis`, `ollama`
- View all containers: `docker-compose ps`
- Check resource usage: `docker stats`

## Development Mode

To make code changes:

```bash
# Backend changes auto-reload (--reload flag in docker-compose)
# Just edit files in backend/app/

# Frontend changes auto-reload
# Edit files in frontend/src/

# Both containers watch for file changes
```

---

**Setup Time**: ~10 minutes
**First Analysis**: ~30 seconds
**Ready to use!** 🎉
