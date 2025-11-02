#!/bin/bash
# Start both the backend API and Celery worker in separate terminal windows

set -e

cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

echo "🚀 Starting IvriMeet Backend Services..."

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

# Detect terminal emulator
TERMINAL_CMD=""
if command -v gnome-terminal &> /dev/null; then
    TERMINAL_CMD="gnome-terminal"
elif command -v xterm &> /dev/null; then
    TERMINAL_CMD="xterm"
elif command -v konsole &> /dev/null; then
    TERMINAL_CMD="konsole"
elif command -v xfce4-terminal &> /dev/null; then
    TERMINAL_CMD="xfce4-terminal"
else
    echo "❌ No supported terminal emulator found. Please install one of:"
    echo "   - gnome-terminal"
    echo "   - xterm"
    echo "   - konsole"
    echo "   - xfce4-terminal"
    exit 1
fi

echo "📋 Opening terminal windows..."
echo ""

# Open terminal 1 for API Server
if [ "$TERMINAL_CMD" = "gnome-terminal" ]; then
    gnome-terminal --title="IvriMeet API Server" -- bash -c "cd '$SCRIPT_DIR' && export DATABASE_URL='$DATABASE_URL' && [ -f .env ] && source .env && echo '🚀 Starting API Server on http://localhost:8000...' && python -m uvicorn agent_service.api:app --host 0.0.0.0 --port 8000 --reload; exec bash"
elif [ "$TERMINAL_CMD" = "xterm" ]; then
    xterm -T "IvriMeet API Server" -e bash -c "cd '$SCRIPT_DIR' && export DATABASE_URL='$DATABASE_URL' && [ -f .env ] && source .env && echo '🚀 Starting API Server on http://localhost:8000...' && python -m uvicorn agent_service.api:app --host 0.0.0.0 --port 8000 --reload; exec bash" &
elif [ "$TERMINAL_CMD" = "konsole" ]; then
    konsole --title "IvriMeet API Server" -e bash -c "cd '$SCRIPT_DIR' && export DATABASE_URL='$DATABASE_URL' && [ -f .env ] && source .env && echo '🚀 Starting API Server on http://localhost:8000...' && python -m uvicorn agent_service.api:app --host 0.0.0.0 --port 8000 --reload; exec bash" &
elif [ "$TERMINAL_CMD" = "xfce4-terminal" ]; then
    xfce4-terminal --title="IvriMeet API Server" -e "bash -c 'cd \"$SCRIPT_DIR\" && export DATABASE_URL=\"$DATABASE_URL\" && [ -f .env ] && source .env && echo \"🚀 Starting API Server on http://localhost:8000...\" && python -m uvicorn agent_service.api:app --host 0.0.0.0 --port 8000 --reload; exec bash'" &
fi

sleep 2

# Open terminal 2 for Celery Worker
if [ "$TERMINAL_CMD" = "gnome-terminal" ]; then
    gnome-terminal --title="IvriMeet Celery Worker" -- bash -c "cd '$SCRIPT_DIR' && export DATABASE_URL='$DATABASE_URL' && [ -f .env ] && source .env && echo '⚙️  Starting Celery Worker...' && celery -A agent_service.services.processing_queue worker --loglevel=info; exec bash"
elif [ "$TERMINAL_CMD" = "xterm" ]; then
    xterm -T "IvriMeet Celery Worker" -e bash -c "cd '$SCRIPT_DIR' && export DATABASE_URL='$DATABASE_URL' && [ -f .env ] && source .env && echo '⚙️  Starting Celery Worker...' && celery -A agent_service.services.processing_queue worker --loglevel=info; exec bash" &
elif [ "$TERMINAL_CMD" = "konsole" ]; then
    konsole --title "IvriMeet Celery Worker" -e bash -c "cd '$SCRIPT_DIR' && export DATABASE_URL='$DATABASE_URL' && [ -f .env ] && source .env && echo '⚙️  Starting Celery Worker...' && celery -A agent_service.services.processing_queue worker --loglevel=info; exec bash" &
elif [ "$TERMINAL_CMD" = "xfce4-terminal" ]; then
    xfce4-terminal --title="IvriMeet Celery Worker" -e "bash -c 'cd \"$SCRIPT_DIR\" && export DATABASE_URL=\"$DATABASE_URL\" && [ -f .env ] && source .env && echo \"⚙️  Starting Celery Worker...\" && celery -A agent_service.services.processing_queue worker --loglevel=info; exec bash'" &
fi

echo "✅ Opened 2 terminal windows:"
echo "   1. API Server (http://localhost:8000)"
echo "   2. Celery Worker"
echo ""
echo "You can close this window now. Services are running in the other terminals."
