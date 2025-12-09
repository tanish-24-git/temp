#!/bin/bash
# =============================================================================
# EC2 Deployment Script for Compliance Agent
# =============================================================================
# Run this script on a fresh Ubuntu 22.04 EC2 instance
# Usage: chmod +x deploy.sh && ./deploy.sh

set -e

echo "=============================================="
echo "  Compliance Agent - EC2 Deployment Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run as root. Use a regular user with sudo access.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt-get update && sudo apt-get upgrade -y

echo -e "${YELLOW}Step 2: Installing Docker...${NC}"
# Remove old Docker versions
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install prerequisites
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add current user to docker group
sudo usermod -aG docker $USER

echo -e "${YELLOW}Step 3: Installing Docker Compose...${NC}"
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo -e "${YELLOW}Step 4: Installing NVIDIA Container Toolkit (for GPU support)...${NC}"
# Only install if NVIDIA GPU is detected
if lspci | grep -i nvidia > /dev/null; then
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker
    echo -e "${GREEN}NVIDIA Container Toolkit installed!${NC}"
else
    echo -e "${YELLOW}No NVIDIA GPU detected. Skipping GPU toolkit installation.${NC}"
    echo -e "${YELLOW}Note: Ollama will run on CPU (slower inference).${NC}"
fi

echo -e "${YELLOW}Step 5: Cloning the repository...${NC}"
cd ~
if [ -d "compliance-agent-poc" ]; then
    echo "Directory exists, pulling latest changes..."
    cd compliance-agent-poc
    git pull
else
    git clone https://github.com/YOUR_USERNAME/compliance-agent-poc.git
    cd compliance-agent-poc
fi

echo -e "${YELLOW}Step 6: Setting up environment variables...${NC}"
if [ ! -f ".env.production" ]; then
    cp .env.production.example .env.production
    echo -e "${RED}IMPORTANT: Edit .env.production with your actual values!${NC}"
    echo -e "${RED}Run: nano .env.production${NC}"
else
    echo ".env.production already exists"
fi

echo -e "${YELLOW}Step 7: Getting EC2 public IP...${NC}"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo -e "${GREEN}Your public IP is: ${PUBLIC_IP}${NC}"
echo -e "${YELLOW}Update VITE_API_BASE_URL in .env.production to: http://${PUBLIC_IP}:8000${NC}"

echo -e "${GREEN}=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Edit .env.production: nano .env.production"
echo "2. Update VITE_API_BASE_URL to http://${PUBLIC_IP}:8000"
echo "3. Update POSTGRES_PASSWORD with a strong password"
echo "4. Log out and log back in (for docker group to take effect)"
echo "5. Run: docker compose -f docker-compose.prod.yml up -d --build"
echo "6. Pull Ollama model: docker exec compliance-ollama ollama pull qwen2.5:7b"
echo ""
echo "Access the application at: http://${PUBLIC_IP}"
echo "API documentation at: http://${PUBLIC_IP}:8000/docs"
echo "==============================================
${NC}"
