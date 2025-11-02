# Netlify Deployment Guide for IvriMeet

This guide explains how to deploy the IvriMeet frontend to Netlify.

## Prerequisites

- A Netlify account
- The IvriMeet frontend code ready for deployment
- Backend API accessible from the internet (or use tunneling service)

## Deployment Steps

### 1. Connect Repository to Netlify

1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Click "Add new site" > "Import an existing project"
3. Connect your Git repository (GitHub, GitLab, or Bitbucket)
4. Select the repository containing the IvriMeet frontend

### 2. Configure Build Settings

Netlify should auto-detect the settings from `netlify.toml`, but verify:

- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Node version**: 18 (or higher)

If auto-detection doesn't work, manually set:
- Base directory: `IvriMeet` (if repo root contains multiple projects)
- Build command: `npm run build`
- Publish directory: `dist`

### 3. Set Environment Variables

Go to **Site settings** > **Build & deploy** > **Environment variables** and add:

#### Required Variables

- **`VITE_API_BASE_URL`**: The URL of your backend API
  - If backend is on a server with public IP: `http://your-server-ip:8000` or `https://api.yourdomain.com`
  - If using tunneling (ngrok/Cloudflare Tunnel): `https://your-tunnel-url.ngrok.io`
  - Example: `http://123.456.789.0:8000` or `https://api.ivrimeet.com`

#### Optional Variables

- **`GEMINI_API_KEY`**: For live transcription feature (optional)
  - Get from: https://ai.google.dev/
  - Only needed if using live recording/transcription

### 4. Deploy

1. Click "Deploy site" or push to your connected branch
2. Netlify will:
   - Install dependencies (`npm install`)
   - Build the project (`npm run build`)
   - Deploy to `ivreetmeet.netlify.app`

### 5. Configure Custom Domain (Optional)

If you have a custom domain:

1. Go to **Site settings** > **Domain management**
2. Click "Add custom domain"
3. Follow Netlify's DNS configuration instructions

## Backend Configuration

### CORS Setup

The backend must allow requests from your Netlify domain. The backend is already configured to allow `https://ivreetmeet.netlify.app` by default.

If you need to add additional origins, set the `CORS_ORIGINS` environment variable in your backend `.env`:

```env
CORS_ORIGINS=https://ivreetmeet.netlify.app,https://custom-domain.com
```

### Backend Access

Since the backend stays on localhost, ensure it's accessible from the internet:

#### Option 1: Public IP/Server
- Deploy backend to a server with a public IP
- Update firewall to allow port 8000
- Use IP:port or set up reverse proxy

#### Option 2: Tunneling Service
- Use **ngrok**: `ngrok http 8000`
- Use **Cloudflare Tunnel**: `cloudflared tunnel --url localhost:8000`
- Update `VITE_API_BASE_URL` in Netlify to the tunnel URL

#### Option 3: Cloud Deployment
- Deploy backend to a cloud service (AWS, Heroku, Railway, etc.)
- Update `VITE_API_BASE_URL` in Netlify to the cloud service URL

## Verification

After deployment:

1. Visit `https://ivreetmeet.netlify.app`
2. Check browser console for any API errors
3. Test uploading a meeting file
4. Verify backend API connectivity

## Troubleshooting

### Build Fails

- Check Netlify build logs for errors
- Verify Node version (should be 18+)
- Ensure all dependencies are in `package.json`

### API Connection Errors

- Verify `VITE_API_BASE_URL` is set correctly in Netlify
- Check backend CORS configuration allows Netlify domain
- Test backend API directly (should respond to health check)
- Check browser console for CORS errors

### Routing Issues (404 on refresh)

- Verify `netlify.toml` has redirect rules (should be auto-configured)
- Check that redirects redirect to `/index.html` with status 200

## Continuous Deployment

Netlify will automatically deploy when you push to your connected branch:

- **Production**: Deploys from `main` or `master` branch
- **Preview**: Creates preview deployments for pull requests
- **Build status**: Check build status in Netlify dashboard

## Environment Variables in Netlify

Remember: Environment variables prefixed with `VITE_` are available in client-side code.

All sensitive variables (like API keys) should be set in Netlify dashboard, not committed to Git.

## Support

For issues:
- Check Netlify build logs
- Verify environment variables are set correctly
- Test backend API independently
- Review browser console for client-side errors

