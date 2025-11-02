#!/bin/bash
# EC2 Ubuntu Setup Script for IvriMeet Backend
# Run this on your EC2 instance after connecting via SSH

set -e

echo "🚀 Starting IvriMeet Backend EC2 Setup (Ubuntu)..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3 and tools (Ubuntu 24.04 comes with Python 3.12)
echo "🐍 Installing Python 3 and tools..."
sudo apt install -y python3 python3-venv python3-pip git curl build-essential

# Install PostgreSQL
echo "🐘 Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Install Redis
echo "📮 Installing Redis..."
sudo apt install -y redis-server

# Install Docker
echo "🐳 Installing Docker..."
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Start services
echo "▶️  Starting services..."
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Setup PostgreSQL database (optional - if not using Docker)
echo "🗄️  PostgreSQL is installed. You can use local PostgreSQL or Docker."
echo "   For Docker PostgreSQL with pgvector, use docker-compose.yml"

echo ""
echo "✅ System setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone or upload your code to /home/ubuntu/ASR_SALES_CALLS_AGENT"
echo "2. Create virtual environment: python3.11 -m venv venv"
echo "3. Install dependencies: pip install -r requirements.txt"
echo "4. Create .env file with your configuration"
echo "5. Setup Docker PostgreSQL (if using): docker-compose up -d"
echo "6. Run migrations: alembic upgrade head"
echo "7. Setup systemd services (see ec2_systemd_setup.sh)"
echo ""
echo "Note: Log out and back in for Docker group changes to take effect"

