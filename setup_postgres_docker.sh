#!/bin/bash
# Setup PostgreSQL with pgvector using Docker
# This is easier if you don't want to install PostgreSQL directly

set -e

echo "🐳 Setting up PostgreSQL with pgvector using Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop existing container if it exists
docker stop pgvector-hebrew-meetings 2>/dev/null || true
docker rm pgvector-hebrew-meetings 2>/dev/null || true

# Run PostgreSQL with pgvector
echo "▶️  Starting PostgreSQL container with pgvector..."
docker run -d \
  --name pgvector-hebrew-meetings \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=hebrew_meetings \
  -p 5432:5432 \
  pgvector/pgvector:pg16

echo "⏳ Waiting for PostgreSQL to start..."
sleep 5

# Verify connection
echo "🔍 Verifying connection..."
docker exec pgvector-hebrew-meetings psql -U postgres -d hebrew_meetings -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec pgvector-hebrew-meetings psql -U postgres -d hebrew_meetings -c "\dx vector"

echo ""
echo "✅ PostgreSQL with pgvector is running!"
echo "   Container: pgvector-hebrew-meetings"
echo "   Database: hebrew_meetings"
echo "   User: postgres"
echo "   Password: postgres"
echo "   Port: 5432"
echo ""
echo "📝 Connection string: postgresql://postgres:postgres@localhost:5432/hebrew_meetings"
echo ""
echo "To stop: docker stop pgvector-hebrew-meetings"
echo "To start: docker start pgvector-hebrew-meetings"

