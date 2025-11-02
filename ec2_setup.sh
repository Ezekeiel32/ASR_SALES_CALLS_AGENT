#!/bin/bash
# EC2 Initial Setup Script for IvriMeet Backend
# Run this on your EC2 instance after connecting via SSH

set -e

echo "🚀 Starting IvriMeet Backend EC2 Setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and tools
echo "🐍 Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip git curl build-essential

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

# Setup PostgreSQL database (if using local PostgreSQL)
echo "🗄️  Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE hebrew_meetings;" 2>/dev/null || echo "Database may already exist"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" || echo "User already configured"

echo "✅ System setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone or upload your code to /home/ubuntu/ASR_SALES_CALLS_AGENT"
echo "2. Create virtual environment: python3.11 -m venv venv"
echo "3. Install dependencies: pip install -r requirements.txt"
echo "4. Create .env file with your configuration"
echo "5. Run migrations: alembic upgrade head"
echo "6. Setup systemd services (see AWS_EC2_DEPLOY.md)"
echo ""
echo "Note: Log out and back in for Docker group changes to take effect"

