# AWS EC2 Deployment Guide for IvriMeet Backend

Complete guide to deploy the FastAPI backend to AWS EC2 using the free tier.

## Prerequisites

- AWS account
- AWS CLI installed (optional, but helpful)
- SSH client
- Your backend code ready for deployment

## Step 1: Launch EC2 Instance

### 1.1 Create EC2 Instance

1. Log in to [AWS Console](https://console.aws.amazon.com)
2. Navigate to **EC2** > **Instances** > **Launch instance**
3. Configure:

   **Name:** `ivrimeet-backend`

   **AMI (Amazon Machine Image):**
   - Choose: **Ubuntu 22.04 LTS** (or latest LTS)
   - Architecture: x86_64

   **Instance type:**
   - Select: **t2.micro** (Free tier eligible)
   - vCPUs: 1, Memory: 1 GB

   **Key pair:**
   - Create new key pair or use existing
   - Download the `.pem` file (you'll need it to SSH)
   - Name: `ivrimeet-backend-key`

   **Network settings:**
   - Allow SSH from: Your IP (or `0.0.0.0/0` for testing - **not recommended for production**)
   - **Create security group** with:
     - SSH (22) - from your IP
     - HTTP (80) - from anywhere `0.0.0.0/0`
     - Custom TCP (8000) - from anywhere `0.0.0.0/0` (for API)

   **Storage:**
   - 20 GB gp3 (Free tier: 30 GB)

4. Click **Launch instance**

### 1.2 Note Instance Details

- **Public IP:** (e.g., `54.123.45.67`)
- **Instance ID:** (e.g., `i-0123456789abcdef0`)

## Step 2: Connect to EC2 Instance

### 2.1 Set Permissions for Key

```bash
chmod 400 ivrimeet-backend-key.pem
```

### 2.2 SSH into Instance

```bash
ssh -i ivrimeet-backend-key.pem ubuntu@YOUR_PUBLIC_IP
```

Replace `YOUR_PUBLIC_IP` with your instance's public IP.

## Step 3: Initial Server Setup

Once connected via SSH, run these commands:

### 3.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 3.2 Install Python 3.11+ and Tools

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip git curl build-essential
```

### 3.3 Install PostgreSQL (Optional - if not using RDS)

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 3.4 Install Redis

```bash
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 3.5 Install Docker (for PostgreSQL with pgvector)

```bash
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

Log out and back in for Docker group to take effect.

## Step 4: Clone and Setup Application

### 4.1 Clone Repository

```bash
cd /home/ubuntu
git clone YOUR_REPO_URL
cd ASR_SALES_CALLS_AGENT
```

Or upload your code using SCP:

```bash
# From your local machine
scp -i ivrimeet-backend-key.pem -r /path/to/ASR_SALES_CALLS_AGENT ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/
```

### 4.2 Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 4.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 5: Setup Database

### Option A: Docker PostgreSQL with pgvector

```bash
# Create docker-compose.yml if not exists
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

## Step 6: Configure Environment Variables

### 6.1 Create .env File

```bash
nano .env
```

Add your environment variables:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hebrew_meetings

# API Keys (SET THESE!)
IVRIT_API_KEY=your_ivrit_key
NVIDIA_API_KEY=your_nvidia_key
RUNPOD_API_KEY=your_runpod_key  # Optional

# RunPod Configuration
IVRIT_RUNPOD_ENDPOINT_ID=your_endpoint_id  # If using RunPod

# S3 Configuration (if using)
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# CORS (add your Netlify domain)
CORS_ORIGINS=https://ivreetmeet.netlify.app

# PyAnnote (if using)
PYANNOTE_AUTH_TOKEN=your_huggingface_token  # Optional

# App Settings
LOG_LEVEL=INFO
REQUEST_TIMEOUT_SECONDS=120
```

Save and exit (Ctrl+X, Y, Enter)

### 6.2 Secure .env File

```bash
chmod 600 .env
```

## Step 7: Run Database Migrations

```bash
source venv/bin/activate
cd /home/ubuntu/ASR_SALES_CALLS_AGENT
alembic upgrade head
```

## Step 8: Setup Systemd Services

### 8.1 Create FastAPI Service

```bash
sudo nano /etc/systemd/system/ivrimeet-api.service
```

Add:

```ini
[Unit]
Description=IvriMeet FastAPI Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ASR_SALES_CALLS_AGENT
Environment="PATH=/home/ubuntu/ASR_SALES_CALLS_AGENT/venv/bin"
ExecStart=/home/ubuntu/ASR_SALES_CALLS_AGENT/venv/bin/uvicorn agent_service.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit.

### 8.2 Create Celery Worker Service

```bash
sudo nano /etc/systemd/system/ivrimeet-celery.service
```

Add:

```ini
[Unit]
Description=IvriMeet Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ASR_SALES_CALLS_AGENT
Environment="PATH=/home/ubuntu/ASR_SALES_CALLS_AGENT/venv/bin"
ExecStart=/home/ubuntu/ASR_SALES_CALLS_AGENT/venv/bin/celery -A agent_service.services.processing_queue worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit.

### 8.3 Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable ivrimeet-api
sudo systemctl enable ivrimeet-celery
sudo systemctl start ivrimeet-api
sudo systemctl start ivrimeet-celery
```

### 8.4 Check Status

```bash
sudo systemctl status ivrimeet-api
sudo systemctl status ivrimeet-celery
```

View logs:
```bash
sudo journalctl -u ivrimeet-api -f
sudo journalctl -u ivrimeet-celery -f
```

## Step 9: Test API

From your local machine:

```bash
curl http://YOUR_PUBLIC_IP:8000/healthz
```

Should return: `{"status":"ok"}`

## Step 10: Update Netlify Environment Variable

Go back to Netlify dashboard and update:

**`VITE_API_BASE_URL`** = `http://YOUR_PUBLIC_IP:8000`

Or if you set up a domain:

**`VITE_API_BASE_URL`** = `https://api.yourdomain.com`

## Step 11: (Optional) Setup Domain and SSL

### 11.1 Point Domain to EC2 IP

In your DNS provider:
- Add A record: `api.yourdomain.com` → `YOUR_PUBLIC_IP`

### 11.2 Setup Nginx Reverse Proxy with SSL

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

```bash
sudo nano /etc/nginx/sites-available/ivrimeet-api
```

Add:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and get SSL:

```bash
sudo ln -s /etc/nginx/sites-available/ivrimeet-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d api.yourdomain.com
```

Update Netlify `VITE_API_BASE_URL` to `https://api.yourdomain.com`

## Step 12: Security Hardening

### 12.1 Update Security Group

- Remove HTTP (80) if using Nginx
- Restrict SSH (22) to your IP only
- Keep port 8000 private (only accessible from Nginx/localhost)

### 12.2 Setup Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 12.3 Regular Updates

```bash
sudo apt update && sudo apt upgrade -y
```

## Monitoring and Maintenance

### Check Service Status

```bash
sudo systemctl status ivrimeet-api
sudo systemctl status ivrimeet-celery
sudo systemctl status postgresql
sudo systemctl status redis-server
```

### View Logs

```bash
# API logs
sudo journalctl -u ivrimeet-api -n 100 -f

# Celery logs
sudo journalctl -u ivrimeet-celery -n 100 -f
```

### Restart Services

```bash
sudo systemctl restart ivrimeet-api
sudo systemctl restart ivrimeet-celery
```

## Troubleshooting

### API Not Responding

1. Check service status: `sudo systemctl status ivrimeet-api`
2. Check logs: `sudo journalctl -u ivrimeet-api -f`
3. Verify port is open: `sudo netstat -tulpn | grep 8000`
4. Check security group allows port 8000

### Database Connection Issues

1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Test connection: `psql -U postgres -d hebrew_meetings`
3. Verify DATABASE_URL in .env

### Celery Not Processing Tasks

1. Check service status: `sudo systemctl status ivrimeet-celery`
2. Check Redis: `redis-cli ping`
3. Check logs: `sudo journalctl -u ivrimeet-celery -f`

## Cost Estimation (Free Tier)

- **EC2 t2.micro:** Free for 12 months (750 hours/month)
- **EBS Storage (20 GB):** Free tier includes 30 GB
- **Data Transfer:** 100 GB/month free
- **After 12 months:** ~$8-10/month for t2.micro instance

## Next Steps

1. ✅ Backend deployed and running
2. ✅ Update Netlify `VITE_API_BASE_URL` to EC2 IP
3. ✅ Test frontend connects to backend
4. ⚠️ Monitor EC2 instance for first 24 hours
5. ⚠️ Setup CloudWatch alarms for monitoring (optional)
6. ⚠️ Consider Elastic IP for static IP address (optional)

