#!/bin/bash
# Setup script for PostgreSQL with pgvector
# Run this script with: bash setup_postgres.sh

set -e

echo "🚀 Setting up PostgreSQL with pgvector extension..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Check if PostgreSQL is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo "▶️  Starting PostgreSQL..."
    sudo systemctl start postgresql
fi

# Create database and user
echo "📊 Creating database and user..."
sudo -u postgres psql << EOF
-- Create database
CREATE DATABASE hebrew_meetings;

-- Set password for postgres user (if needed)
ALTER USER postgres WITH PASSWORD 'postgres';

-- Connect to database and install pgvector
\c hebrew_meetings
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension
\dx vector

-- Show database info
\l hebrew_meetings
EOF

echo ""
echo "✅ PostgreSQL setup complete!"
echo "   Database: hebrew_meetings"
echo "   User: postgres"
echo "   Password: postgres"
echo "   pgvector extension: installed"
echo ""
echo "📝 Connection string: postgresql://postgres:postgres@localhost:5432/hebrew_meetings"

