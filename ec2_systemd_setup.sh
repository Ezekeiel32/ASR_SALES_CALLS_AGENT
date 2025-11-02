#!/bin/bash
# Setup Systemd Services for IvriMeet Backend
# Run this on EC2 after installing the application

set -e

APP_DIR="/home/ubuntu/ASR_SALES_CALLS_AGENT"
VENV_PATH="$APP_DIR/venv"

if [ ! -d "$APP_DIR" ]; then
    echo "❌ Error: Application directory not found at $APP_DIR"
    echo "Please clone or upload your code first."
    exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it first: python3.11 -m venv venv"
    exit 1
fi

echo "🔧 Setting up systemd services..."

# Create FastAPI service
echo "Creating FastAPI service..."
sudo tee /etc/systemd/system/ivrimeet-api.service > /dev/null <<EOF
[Unit]
Description=IvriMeet FastAPI Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/uvicorn agent_service.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Celery worker service
echo "Creating Celery worker service..."
sudo tee /etc/systemd/system/ivrimeet-celery.service > /dev/null <<EOF
[Unit]
Description=IvriMeet Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/celery -A agent_service.services.processing_queue worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling services..."
sudo systemctl enable ivrimeet-api
sudo systemctl enable ivrimeet-celery

echo "✅ Services created and enabled!"
echo ""
echo "To start services:"
echo "  sudo systemctl start ivrimeet-api"
echo "  sudo systemctl start ivrimeet-celery"
echo ""
echo "To check status:"
echo "  sudo systemctl status ivrimeet-api"
echo "  sudo systemctl status ivrimeet-celery"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u ivrimeet-api -f"
echo "  sudo journalctl -u ivrimeet-celery -f"

