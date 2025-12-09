# AWS EC2 Deployment Guide - Compliance Agent

This guide walks you through deploying the Compliance Agent application to an AWS EC2 instance.

---

## Prerequisites

- AWS Account with EC2 access
- Basic knowledge of AWS Console
- SSH key pair for EC2 access

---

## Step 1: Launch EC2 Instance

### Recommended Instance Configuration

| Setting | Value |
|---------|-------|
| **AMI** | Ubuntu 22.04 LTS (HVM) |
| **Instance Type** | `g4dn.xlarge` (GPU) or `t3.large` (CPU-only) |
| **Storage** | 100 GB gp3 SSD |
| **Security Group** | See below |

### Instance Type Recommendations

| Type | vCPU | RAM | GPU | Use Case |
|------|------|-----|-----|----------|
| `t3.large` | 2 | 8 GB | ❌ | Development/Testing (slow AI) |
| `t3.xlarge` | 4 | 16 GB | ❌ | Light production (slow AI) |
| `g4dn.xlarge` | 4 | 16 GB | T4 16GB | **Recommended** (fast AI) |
| `g4dn.2xlarge` | 8 | 32 GB | T4 16GB | High traffic production |

> ⚠️ **Note**: Without GPU, Ollama LLM inference will be 5-10x slower.

### Security Group Rules

Create a security group with these inbound rules:

| Type | Port | Source | Description |
|------|------|--------|-------------|
| SSH | 22 | Your IP | SSH access |
| HTTP | 80 | 0.0.0.0/0 | Web application |
| HTTPS | 443 | 0.0.0.0/0 | SSL (future) |
| Custom TCP | 8000 | 0.0.0.0/0 | API (optional, remove in production) |

---

## Step 2: Connect to EC2

```bash
# Download your key pair (.pem file) from AWS

# Set permissions
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

## Step 3: Run Deployment Script

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/compliance-agent-poc.git
cd compliance-agent-poc

# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- Update system packages
- Install Docker & Docker Compose
- Install NVIDIA Container Toolkit (if GPU detected)
- Set up the project

---

## Step 4: Configure Environment

```bash
# Edit production environment
nano .env.production
```

**Critical settings to update:**

```env
# Use the EC2 public IP
VITE_API_BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000

# Strong database password
POSTGRES_PASSWORD=your_strong_password_here
DATABASE_URL=postgresql://compliance_user:your_strong_password_here@postgres:5432/compliance_db

# Generate a secret key
SECRET_KEY=your_generated_secret_key
```

Generate a secret key:
```bash
openssl rand -hex 32
```

---

## Step 5: Deploy Application

```bash
# Log out and back in (for docker group)
exit
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

cd compliance-agent-poc

# Build and start containers
docker compose -f docker-compose.prod.yml up -d --build

# Watch the logs
docker compose -f docker-compose.prod.yml logs -f
```

---

## Step 6: Pull Ollama Model

```bash
# Pull the LLM model (this takes a few minutes)
docker exec compliance-ollama ollama pull qwen2.5:7b

# Verify model is loaded
docker exec compliance-ollama ollama list
```

---

## Step 7: Verify Deployment

```bash
# Check all containers are running
docker compose -f docker-compose.prod.yml ps

# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:80
```

Access the application:
- **Frontend**: `http://YOUR_EC2_PUBLIC_IP`
- **API Docs**: `http://YOUR_EC2_PUBLIC_IP:8000/docs`

---

## Troubleshooting

### Check container logs
```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
docker compose -f docker-compose.prod.yml logs ollama
```

### Restart a service
```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Rebuild after code changes
```bash
docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

### Database migrations
```bash
docker exec compliance-backend alembic upgrade head
```

### Check GPU status (if using GPU instance)
```bash
nvidia-smi
docker exec compliance-ollama nvidia-smi
```

---

## Optional: Set Up Domain & SSL

### Using Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

### Update nginx.conf for HTTPS

Update the frontend nginx.conf to include SSL configuration.

---

## Maintenance

### Backup Database
```bash
docker exec compliance-postgres pg_dump -U compliance_user compliance_db > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker exec -i compliance-postgres psql -U compliance_user compliance_db
```

### Update Application
```bash
cd compliance-agent-poc
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Cost Estimation

| Instance Type | Monthly Cost (On-Demand) | Notes |
|---------------|-------------------------|-------|
| `t3.large` | ~$60/month | CPU-only, slow AI |
| `g4dn.xlarge` | ~$380/month | GPU, fast AI |
| Spot Instance | 60-70% cheaper | Can be interrupted |

**Tips to reduce costs:**
- Use Spot Instances for non-critical workloads
- Stop instance when not in use
- Use Reserved Instances for long-term use

---

## Security Checklist

- [ ] Change default postgres password
- [ ] Generate new SECRET_KEY
- [ ] Restrict security group to necessary ports
- [ ] Set up SSL/HTTPS
- [ ] Enable AWS CloudWatch logging
- [ ] Set up automated backups
- [ ] Remove port 8000 from public access (use nginx proxy)

---

*Last updated: December 2024*
