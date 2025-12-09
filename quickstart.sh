#!/bin/bash
# =============================================================================
# Quick Start: After EC2 is Running
# =============================================================================
# Run this after connecting to your EC2 instance
# Usage: chmod +x quickstart.sh && ./quickstart.sh YOUR_DOMAIN

set -e

DOMAIN=${1:-"your-domain.com"}
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo "=============================================="
echo "  Compliance Agent - Quick Start"
echo "  Domain: $DOMAIN"
echo "  Public IP: $PUBLIC_IP"
echo "=============================================="

# Step 1: Clone repo (if not already done)
cd ~
if [ ! -d "compliance-agent-poc" ]; then
    git clone https://github.com/YOUR_USERNAME/compliance-agent-poc.git
fi
cd compliance-agent-poc

# Step 2: Create production env
if [ ! -f ".env.production" ]; then
    cat > .env.production << EOF
# Database
POSTGRES_USER=compliance_user
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=compliance_db
DATABASE_URL=postgresql://compliance_user:\${POSTGRES_PASSWORD}@postgres:5432/compliance_db

# Redis
REDIS_URL=redis://redis:6379/0

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=120
OLLAMA_MAX_RETRIES=5

# Frontend
VITE_API_BASE_URL=http://$PUBLIC_IP:8000

# Application
ENVIRONMENT=production
LOG_LEVEL=WARNING

# Security
SECRET_KEY=$(openssl rand -hex 32)
EOF
    echo "✅ Created .env.production with auto-generated passwords"
fi

# Step 3: Build and start
echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d --build

# Step 4: Wait for Ollama and pull model
echo "⏳ Waiting for Ollama to start..."
sleep 30

echo "📥 Pulling Ollama model (this takes 5-10 minutes)..."
docker exec compliance-ollama ollama pull qwen2.5:7b

echo ""
echo "=============================================="
echo "  ✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://$PUBLIC_IP"
echo "   API Docs: http://$PUBLIC_IP:8000/docs"
echo ""
echo "📋 Next steps for SSL/HTTPS with domain '$DOMAIN':"
echo "   1. Point your domain DNS to: $PUBLIC_IP"
echo "   2. Run: sudo apt install certbot python3-certbot-nginx"
echo "   3. Run: sudo certbot --nginx -d $DOMAIN"
echo ""
