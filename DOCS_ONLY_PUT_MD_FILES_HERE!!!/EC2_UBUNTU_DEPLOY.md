# EC2 Ubuntu Deployment Guide for IvriMeet Backend

Complete step-by-step guide to deploy the FastAPI backend on Ubuntu 24.04 EC2 instance.

## Instance Details

- **Instance ID**: `i-0eb48174a09defc74`
- **Public IP**: `98.93.53.57`
- **OS**: Ubuntu 24.04.3 LTS
- **Username**: `ubuntu`

## Step 1: Connect to Instance

From your local machine:

```bash
cd /home/chezy/ASR/ASR_SALES_CALLS_AGENT
chmod 400 ivrimeet-backend-key.pem
ssh -i ivrimeet-backend-key.pem ubuntu@98.93.53.57
```

## Step 2: Run Initial Setup

Once connected to EC2:

```bash
# Download and run the setup script
curl -o setup.sh https://raw.githubusercontent.com/YOUR_REPO/ec2_ubuntu_setup.sh
# OR upload the file using SCP from your local machine:
```

Or manually run these commands:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git curl build-essential
sudo apt install -y postgresql postgresql-contrib redis-server docker.io docker-compose
sudo systemctl start docker postgresql redis-server
sudo systemctl enable docker postgresql redis-server
sudo usermod -aG docker ubuntu
```

**Important**: Log out and back in for Docker group to take effect.

## Step 3: Upload Your Code

### Option A: Using Git (if your code is in a repo)

```bash
cd /home/ubuntu
git clone YOUR_REPO_URL
cd ASR_SALES_CALLS_AGENT
```

### Option B: Using SCP (from your local machine)

```bash
# From your local machine
cd /home/chezy/ASR/ASR_SALES_CALLS_AGENT
scp -i ivrimeet-backend-key.pem -r . ubuntu@98.93.53.57:/home/ubuntu/ASR_SALES_CALLS_AGENT
```

## Step 4: Setup Python Environment

```bash
cd /home/ubuntu/ASR_SALES_CALLS_AGENT
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 5: Setup Database

### Option A: Docker PostgreSQL with pgvector (Recommended)

```bash
# Create docker-compose.yml if it doesn't exist
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: pgvector-hebrew-meetings
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: hebrew_meetings
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
EOF

docker-compose up -d
```

### Option B: Local PostgreSQL

```bash
sudo -u postgres psql
```

Then in psql:
```sql
CREATE DATABASE hebrew_meetings;
CREATE USER postgres WITH PASSWORD 'postgres';
ALTER ROLE postgres SUPERUSER;
\q
```

## Step 6: Create Environment File

```bash
nano .env
```

Add your configuration:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hebrew_meetings

# API Keys (SET THESE!)
IVRIT_API_KEY=your_ivrit_key
NVIDIA_API_KEY=your_nvidia_key
RUNPOD_API_KEY=your_runpod_key

# RunPod Configuration
IVRIT_RUNPOD_ENDPOINT_ID=your_endpoint_id

# S3 Configuration (if using)
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# CORS (add your Netlify domain)
CORS_ORIGINS=https://ivreetmeet.netlify.app

# PyAnnote (if using)
PYANNOTE_AUTH_TOKEN=your_huggingface_token

# App Settings
LOG_LEVEL=INFO
REQUEST_TIMEOUT_SECONDS=120
```

Save and exit (Ctrl+X, Y, Enter)

```bash
chmod 600 .env
```

## Step 7: Run Database Migrations

```bash
source venv/bin/activate
alembic upgrade head
```

## Step 8: Setup Systemd Services

```bash
# Make the setup script executable
chmod +x ec2_systemd_setup.sh

# Run it
./ec2_systemd_setup.sh
```

Or manually create services (see `ec2_systemd_setup.sh` for details).

## Step 9: Start Services

```bash
sudo systemctl start ivrimeet-api
sudo systemctl start ivrimeet-celery
```

## Step 10: Check Status

```bash
sudo systemctl status ivrimeet-api
sudo systemctl status ivrimeet-celery
```

## Step 11: Test API

From your local machine:

```bash
curl http://98.93.53.57:8000/healthz
```

Should return: `{"status":"ok"}`

## Step 12: Update Netlify

Go to Netlify dashboard and update environment variable:

**`VITE_API_BASE_URL`** = `http://98.93.53.57:8000`

## Troubleshooting

### Check Service Logs

```bash
sudo journalctl -u ivrimeet-api -f
sudo journalctl -u ivrimeet-celery -f
```

### Restart Services

```bash
sudo systemctl restart ivrimeet-api
sudo systemctl restart ivrimeet-celery
```

### Check Ports

```bash
sudo netstat -tulpn | grep 8000
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -d hebrew_meetings

# Check if Docker PostgreSQL is running
docker ps | grep postgres
```

## Next Steps

1. ✅ Backend deployed and running
2. ✅ Update Netlify `VITE_API_BASE_URL` to `http://98.93.53.57:8000`
3. ✅ Test frontend connects to backend
4. ⚠️ Consider setting up Nginx reverse proxy with SSL (optional)
5. ⚠️ Consider Elastic IP for static IP address (optional)

