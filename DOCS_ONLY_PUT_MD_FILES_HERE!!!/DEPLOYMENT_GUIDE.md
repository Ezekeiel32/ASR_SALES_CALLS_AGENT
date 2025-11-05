# 🚀 Complete Deployment Guide for IvriMeet

This guide covers deploying both the frontend (Netlify) and backend (Railway/Koyeb) with Gmail OAuth integration.

## 📋 Prerequisites

- [ ] GitHub repository with code pushed
- [ ] Netlify account (for frontend)
- [ ] Railway or Koyeb account (for backend)
- [ ] Google Cloud Console project (for Gmail OAuth)
- [ ] PostgreSQL database (Railway/Koyeb or external)
- [ ] Redis instance (for Celery, optional)

---

## 🎨 Frontend Deployment (Netlify)

### 1. Connect Repository to Netlify

1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect your GitHub repository
4. Select the repository containing `IvriMeet` folder

### 2. Configure Build Settings

Netlify should auto-detect from `netlify.toml`, but verify:

- **Base directory**: `IvriMeet`
- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Node version**: 18 (or higher)

### 3. Set Environment Variables

Go to **Site settings** → **Build & deploy** → **Environment variables**:

```bash
# Backend API URL (set after backend is deployed)
VITE_API_BASE_URL=https://your-backend.railway.app
# OR
VITE_API_BASE_URL=https://your-backend.koyeb.app
```

**Important**: The frontend code will override this if it detects `koyeb` or `netlify` in the URL, so for production, make sure your backend URL doesn't contain these strings.

### 4. Deploy

Netlify will automatically deploy on every push to your connected branch.

Your site will be available at: `https://ivreetmeet.netlify.app` (or your custom domain)

---

## 🔧 Backend Deployment

Choose one: **Railway** (recommended for simplicity) or **Koyeb** (for GPU support).

### Option A: Railway Deployment

#### 1. Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click **"New Project"**

#### 2. Connect Repository

1. Click **"Deploy from GitHub repo"**
2. Select your repository: `ASR_SALES_CALLS_AGENT`
3. Railway will auto-detect Python

#### 3. Add Services

You'll need **2 services**:

**A. Main API Service (FastAPI)**

- Uses the root directory (`ASR_SALES_CALLS_AGENT`)
- Railway auto-detects from `Dockerfile` or `Procfile`

**B. PostgreSQL Database**

1. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway creates DB automatically
3. Copy the `DATABASE_URL` connection string

**Optional: Redis (for Celery)**

1. Click **"New"** → **"Database"** → **"Add Redis"**
2. Copy the `REDIS_URL` connection string

#### 4. Configure Environment Variables

Go to your **API service** → **Variables** tab, add:

```bash
# Database (Railway automatically sets this if you use service reference)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (if using Celery)
REDIS_URL=${{Redis.REDIS_URL}}

# CORS (for Netlify frontend)
CORS_ORIGINS=https://ivreetmeet.netlify.app

# Gmail OAuth (from Google Cloud Console)
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
# Auto-detected redirect URI (will use BACKEND_URL or Railway domain)
# GMAIL_REDIRECT_URI=https://your-app.railway.app/auth/gmail/callback

# Backend URL (for OAuth redirect URI auto-detection)
BACKEND_URL=https://your-app.railway.app

# API Keys
IVRIT_API_KEY=your_ivrit_key
NVIDIA_API_KEY=your_nvidia_key
RUNPOD_API_KEY=your_runpod_key
IVRIT_RUNPOD_ENDPOINT_ID=your_endpoint_id

# JWT Secret (generate a secure random string)
JWT_SECRET=your-secure-random-string-here

# Optional - PyAnnote
PYANNOTE_AUTH_TOKEN=your_huggingface_token

# Optional - S3 (for large files)
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# LangSmith (optional, for LangGraph Studio)
LANGSMITH_API_KEY=your_langsmith_key

# Port (Railway sets this automatically)
PORT=8000
```

#### 5. Run Database Migrations

1. Go to your API service → **"Deployments"** → **"View Logs"**
2. Wait for first deployment to complete
3. Go to **"Settings"** → **"Generate Domain"** to get your Railway URL
4. Update `BACKEND_URL` in environment variables with your Railway URL
5. Go to **"Shell"** tab or use **"Run Command"**:
   ```bash
   alembic upgrade head
   ```

#### 6. Deploy

Railway auto-deploys on every git push! Or manually:

1. Click **"Deploy"** button
2. Watch the logs
3. Once deployed, your API is live at `your-app.railway.app`

---

### Option B: Koyeb Deployment

#### 1. Create Koyeb Account

1. Go to [koyeb.com](https://www.koyeb.com)
2. Sign up/login with GitHub
3. Get $5.50 free credit/month!

#### 2. Create PostgreSQL Database in Koyeb

1. Go to **"Databases"** → **"Create Database"**
2. Select **PostgreSQL**
3. Choose plan (Free tier or Starter)
4. Wait for provisioning (~1-2 minutes)
5. Click on the database → **Copy the Connection String**

#### 3. Create Redis in Koyeb (Optional)

1. Go to **"Databases"** → **"Create Database"**
2. Select **Redis**
3. Copy the **REDIS_URL** connection string

#### 4. Deploy Your App

**From GitHub (Recommended)**

1. Go to **"Apps"** → **"Create App"**
2. Select **"GitHub"** as source
3. Choose your repository: `ASR_SALES_CALLS_AGENT`
4. Koyeb will auto-detect `Dockerfile`

#### 5. Configure Environment Variables

In your Koyeb App → **Settings** → **Environment Variables**:

```bash
# Database (from Koyeb PostgreSQL you created above)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (if using Celery)
REDIS_URL=redis://host:port

# CORS (for Netlify frontend)
CORS_ORIGINS=https://ivreetmeet.netlify.app

# Gmail OAuth (from Google Cloud Console)
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
# Auto-detected redirect URI (will use KOYEB_SERVICE_URL)
# GMAIL_REDIRECT_URI=https://your-app.koyeb.app/auth/gmail/callback

# Backend URL (for OAuth redirect URI auto-detection)
KOYEB_SERVICE_URL=https://your-app.koyeb.app

# API Keys
IVRIT_API_KEY=your_ivrit_key
NVIDIA_API_KEY=your_nvidia_key
RUNPOD_API_KEY=your_runpod_key
IVRIT_RUNPOD_ENDPOINT_ID=your_endpoint_id

# JWT Secret (generate a secure random string)
JWT_SECRET=your-secure-random-string-here

# Optional - PyAnnote
PYANNOTE_AUTH_TOKEN=your_huggingface_token

# Optional - S3
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# LangSmith (optional)
LANGSMITH_API_KEY=your_langsmith_key

# Port (Koyeb sets this automatically)
PORT=8000
```

#### 6. Run Database Migrations

**Via Koyeb Shell**

1. Go to your app → **"Runtime"** → **"Shell"**
2. Run:
   ```bash
   alembic upgrade head
   ```

#### 7. Deploy

Koyeb auto-deploys on every git push!

---

## 🔐 Gmail OAuth Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable **Gmail API**:
   - Go to **"APIs & Services"** → **"Library"**
   - Search for "Gmail API"
   - Click **"Enable"**

### 2. Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (or Internal for Google Workspace)
   - App name: **IvriMeet**
   - User support email: Your email
   - Developer contact: Your email
   - Add scopes: `https://www.googleapis.com/auth/gmail.readonly`
4. Create OAuth client:
   - Application type: **Web application**
   - Name: **IvriMeet Backend**
   - **Authorized redirect URIs**:
     - `https://your-backend.railway.app/auth/gmail/callback` (Railway)
     - OR `https://your-backend.koyeb.app/auth/gmail/callback` (Koyeb)
     - Add `http://localhost:8000/auth/gmail/callback` for local development
5. Copy **Client ID** and **Client Secret**
6. Add these to your backend environment variables:
   - `GMAIL_CLIENT_ID`
   - `GMAIL_CLIENT_SECRET`

### 3. Update Backend Environment Variables

Make sure your backend has:

```bash
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
BACKEND_URL=https://your-backend.railway.app  # or KOYEB_SERVICE_URL for Koyeb
```

The redirect URI will be auto-detected as: `{BACKEND_URL}/auth/gmail/callback`

---

## ✅ Post-Deployment Checklist

### Backend

- [ ] Database migrations ran successfully (`alembic upgrade head`)
- [ ] Backend health check works: `https://your-backend.railway.app/healthz`
- [ ] CORS is configured for Netlify domain
- [ ] Gmail OAuth credentials are set
- [ ] Redirect URI is added to Google Cloud Console
- [ ] All API keys are set (IVRIT, NVIDIA, RUNPOD, etc.)

### Frontend

- [ ] `VITE_API_BASE_URL` is set to your backend URL
- [ ] Frontend builds successfully on Netlify
- [ ] Frontend can connect to backend (check browser console)
- [ ] Gmail OAuth flow works (test clicking Gmail button)

### Testing

1. **Test Authentication**:

   - Register a new user
   - Login with existing user
2. **Test Gmail OAuth**:

   - Click Gmail button in header
   - Complete Google OAuth flow
   - Verify credentials are stored in database
3. **Test Email Analysis**:

   - After Gmail is connected, go to Analytics → Email tab
   - Click "Analyze Emails"
   - Verify communication health analysis works
4. **Test Meeting Analysis**:

   - Upload a meeting audio file
   - Wait for processing to complete
   - Verify communication health analysis for meeting

---

## 🔧 Troubleshooting

### Backend Issues

**Database Connection Errors**

- Verify `DATABASE_URL` is correct
- Check if database is accessible from your deployment platform
- Ensure migrations have run: `alembic upgrade head`

**Gmail OAuth Errors**

- Verify `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` are set
- Check redirect URI in Google Cloud Console matches your backend URL
- Ensure `BACKEND_URL` or `KOYEB_SERVICE_URL` is set correctly

**CORS Errors**

- Verify `CORS_ORIGINS` includes `https://ivreetmeet.netlify.app`
- Check backend logs for CORS-related errors

### Frontend Issues

**API Connection Errors**

- Verify `VITE_API_BASE_URL` is set correctly in Netlify
- Check browser console for CORS errors
- Ensure backend is accessible (test with curl)

**Gmail OAuth Popup Not Working**

- Check browser popup blocker settings
- Verify OAuth callback URL is correct
- Check backend logs for OAuth errors

### Migration Issues

**"Target database is not up to date"**

- Run: `alembic upgrade head` first
- Then create new migration: `alembic revision --autogenerate -m "description"`

**Migration Fails**

- Check database connection string
- Verify you have write permissions
- Check Alembic logs for specific errors

---

## 📚 Additional Resources

- [Railway Deployment Docs](DOCS_ONLY_PUT_MD_FILES_HERE!!!/RAILWAY_DEPLOY.md)
- [Koyeb Deployment Docs](DOCS_ONLY_PUT_MD_FILES_HERE!!!/KOYEB_DEPLOY.md)
- [Netlify Deployment Docs](IvriMeet/NETLIFY_DEPLOY.md)

---

## 🎯 Quick Reference

### Backend URLs

- Railway: `https://your-app.railway.app`
- Koyeb: `https://your-app.koyeb.app`

### Frontend URL

- Netlify: `https://ivreetmeet.netlify.app`

### Key Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `GMAIL_CLIENT_ID` - Google OAuth client ID
- `GMAIL_CLIENT_SECRET` - Google OAuth client secret
- `BACKEND_URL` / `KOYEB_SERVICE_URL` - Backend URL for OAuth redirect
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `JWT_SECRET` - Secret for JWT token signing

---

**Ready to deploy?** Follow the steps above, and you'll have IvriMeet running in production! 🚀
