#!/bin/bash
# Start the IvriMeet backend server

set -e

cd "$(dirname "$0")"

echo "🚀 Starting IvriMeet Backend..."

# Check if PostgreSQL is running
if ! docker ps | grep -q pgvector-hebrew-meetings; then
    echo "⚠️  PostgreSQL container not running. Starting it..."
    docker start pgvector-hebrew-meetings 2>/dev/null || {
        echo "❌ PostgreSQL container not found. Run: bash setup_postgres_docker.sh"
        exit 1
    }
    sleep 3
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis not running. Starting it..."
    redis-server --daemonize yes
    sleep 2
fi

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hebrew_meetings

# Load .env file if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Start the server
echo "▶️  Starting uvicorn server on http://0.0.0.0:8000..."
echo "📚 API Docs will be available at: http://localhost:8000/docs"
echo ""
python -m uvicorn agent_service.api:app --host 0.0.0.0 --port 8000 --reload

