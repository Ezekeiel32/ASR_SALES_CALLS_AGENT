# Netlify Deployment Guide for IvriMeet Frontend

Complete step-by-step guide to deploy the IvriMeet React frontend to Netlify.

## Prerequisites

- ✅ GitHub repository with latest code pushed
- ✅ Netlify account (free tier works fine)
- 🔄 Backend API deployed and accessible (will be done after RunPod build completes)

## Step 1: Connect GitHub to Netlify

### 1.1 Go to Netlify Dashboard
1. Visit https://app.netlify.com
2. Sign in or create a new account
3. Click **"Add new site"** button
4. Select **"Import an existing project"**

### 1.2 Connect Repository
1. Choose **GitHub** as your Git provider
2. Authorize Netlify to access your GitHub account
3. Search for your repository: `ASR_SALES_CALLS_AGENT`
4. Click on the repository to select it

## Step 2: Configure Build Settings

Netlify should auto-detect settings from [`netlify.toml`](IvriMeet/netlify.toml), but verify:

### 2.1 Basic Configuration
```
Site name: ivrimeet-[your-name] (or leave auto-generated)
Branch to deploy: main
```

### 2.2 Build Settings
```
Base directory: IvriMeet
Build command: npm run build
Publish directory: dist
```

### 2.3 Build Environment
```
Node version: 18
```

**Important**: If these settings are not auto-detected:
1. Scroll to **"Build settings"** section
2. Manually enter:
   - **Base directory**: `IvriMeet`
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`

## Step 3: Environment Variables (SKIP FOR NOW)

**⚠️ WAIT**: Don't add environment variables yet! You'll add them after:
1. RunPod endpoint build completes
2. Backend API is deployed

For now, just click **"Deploy site"** to proceed with default settings.

## Step 4: Initial Deployment

1. **Click "Deploy [your-site-name]"**
2. Netlify will:
   - Clone your repository
   - Run `npm install` in the `IvriMeet` directory
   - Run `npm run build`
   - Deploy the `dist` folder
3. **Wait 3-5 minutes** for the build to complete

### Monitor Build Progress
- Click on the build in progress
- View real-time build logs
- Check for any errors (there shouldn't be any)

### Build Success
You'll see:
```
✓ Site built and deployed
```

Your site will be live at: `https://[random-name].netlify.app`

## Step 5: Configure Custom Domain (Optional)

If you have a custom domain:

### 5.1 Add Domain
1. Go to **Site settings** → **Domain management**
2. Click **"Add custom domain"**
3. Enter your domain (e.g., `ivrimeet.com`)
4. Follow Netlify's DNS configuration instructions

### 5.2 Configure DNS
Netlify will provide DNS records to add to your domain registrar:
- **A Record**: Points to Netlify's load balancer IP
- **CNAME**: Points your www subdomain to Netlify

### 5.3 Enable HTTPS
1. Netlify automatically provisions SSL certificate (Let's Encrypt)
2. Wait 5-10 minutes for certificate activation
3. Enable **"Force HTTPS"** option

## Step 6: Add Environment Variables (AFTER Backend Deployed)

**⚠️ DO THIS ONLY AFTER:**
- RunPod endpoint build is complete and running
- Backend API is deployed and accessible

### 6.1 Navigate to Environment Variables
1. Go to **Site settings**
2. Click **"Build & deploy"** (left sidebar)
3. Scroll to **"Environment variables"**
4. Click **"Add a variable"**

### 6.2 Required Variables

#### VITE_API_BASE_URL (REQUIRED)
```
Key: VITE_API_BASE_URL
Value: https://your-backend-api-url.com

Examples:
- Railway: https://your-app.railway.app
- Render: https://your-app.onrender.com
- Custom: https://api.ivrimeet.com
```

**Important**: 
- Do NOT include trailing slash
- Must be the full URL with `https://`
- This is where your backend API is hosted

#### GEMINI_API_KEY (Optional)
Only needed if using live transcription feature:
```
Key: GEMINI_API_KEY
Value: your_google_gemini_api_key
```

Get from: https://ai.google.dev/

### 6.3 Redeploy After Adding Variables
1. After adding environment variables
2. Go to **Deploys** tab
3. Click **"Trigger deploy"** → **"Deploy site"**
4. Wait for new build to complete (2-3 minutes)

## Step 7: Verification

### 7.1 Access Your Site
Visit: `https://your-site-name.netlify.app`

### 7.2 Check Console
1. Open browser Dev Tools (F12)
2. Go to Console tab
3. Look for: `[API Client] Using backend URL: https://your-backend-url`
4. Should show your backend URL, not `localhost`

### 7.3 Test Functionality
**Before backend is ready:**
- [x] Site loads without errors
- [x] Login modal appears (but login won't work yet)
- [x] All pages render correctly

**After backend is ready:**
- [ ] Can log in successfully
- [ ] Can upload meeting audio file
- [ ] Upload progress displays
- [ ] Meeting processes successfully
- [ ] Can view meeting details
- [ ] Can view transcript
- [ ] Can view summary

## Troubleshooting

### Build Fails

**Problem**: `npm install` fails with dependency errors

**Solution**:
1. Check Node version: Should be 18
2. Go to Site settings → Build & deploy → Environment
3. Add: `NODE_VERSION=18`
4. Trigger new deploy

**Problem**: `Cannot find module` errors

**Solution**:
1. Clear build cache: Deploys → Deploy settings → Clear build cache
2. Trigger new deploy

### API Connection Errors

**Problem**: Frontend shows "Network error: Could not connect to server"

**Check**:
1. Is `VITE_API_BASE_URL` set correctly?
2. Is backend API actually running?
3. Is CORS configured on backend to allow Netlify domain?
4. Test backend directly: `curl https://your-backend-url/healthz`

**Problem**: CORS errors in browser console

**Solution**: Add your Netlify domain to backend CORS configuration:
```python
# In backend environment variables
CORS_ORIGINS=https://your-app.netlify.app,https://custom-domain.com
```

### Routing Issues

**Problem**: Page refresh shows 404 error

**Solution**: The [`netlify.toml`](IvriMeet/netlify.toml) should handle this:
```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

If still broken:
1. Check that netlify.toml exists in IvriMeet folder
2. Verify redirects are configured correctly
3. Trigger new deploy

## Continuous Deployment

### Automatic Deploys
Netlify automatically deploys when you push to your connected branch:

- **Production branch**: `main` (or `master`)
- **Deploy previews**: Automatically created for pull requests
- **Build notifications**: Configure in Site settings → Build & deploy → Deploy notifications

### Manual Deploy
To deploy manually:
1. Go to **Deploys** tab
2. Click **"Trigger deploy"**
3. Choose deploy type:
   - **Deploy site**: Normal deploy
   - **Clear cache and deploy**: If having build issues

### Deploy Logs
Always check deploy logs for issues:
1. Click on any deploy
2. View full log
3. Look for errors or warnings

## Performance Optimization

### Enable Caching
Netlify automatically caches static assets. Verify in Site settings:
- **Asset optimization**: Enabled
- **Pretty URLs**: Enabled
- **Post processing**: Bundle CSS, minify assets

### CDN
Netlify uses a global CDN automatically. Your site is served from the nearest edge location to your users.

### Monitoring
Use Netlify Analytics (paid) or integrate with:
- Google Analytics
- Plausible
- Fathom

## Security

### Headers
Netlify automatically adds security headers. To customize:

Create `_headers` file in `IvriMeet/public/`:
```
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
```

### Environment Variables
- Never commit `.env` files to git
- Use Netlify's environment variable manager
- Variables prefixed with `VITE_` are exposed to browser (client-side)
- Don't store sensitive secrets in `VITE_*` variables

## Cost

**Netlify Free Tier Includes:**
- 100 GB bandwidth/month
- 300 build minutes/month
- Unlimited sites
- Automatic SSL
- CDN
- Deploy previews

**Paid Plans:** Start at $19/month for:
- More bandwidth
- More build minutes
- Analytics
- Role-based access control

## Support Resources

- **Netlify Docs**: https://docs.netlify.com
- **Netlify Support**: https://answers.netlify.com
- **Status Page**: https://www.netlifystatus.com

## Next Steps After Deployment

Once frontend is deployed:

1. **Wait for RunPod endpoint build** to complete
2. **Deploy backend API** to Railway/Render/your server
3. **Add `VITE_API_BASE_URL`** to Netlify environment variables
4. **Trigger redeploy** on Netlify
5. **Test end-to-end** functionality
6. **Configure custom domain** (optional)
7. **Set up monitoring** (optional)

## Quick Commands

### Local Testing
```bash
cd ASR_SALES_CALLS_AGENT/IvriMeet

# Install dependencies
npm install

# Set backend URL for local testing
echo 'VITE_API_BASE_URL=http://localhost:8000' > .env

# Run dev server
npm run dev

# Build for production (test)
npm run build

# Preview production build
npm run preview
```

### Deploy via Netlify CLI (Alternative)
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy manually
cd IvriMeet
netlify deploy --prod
```

## Checklist

Use this checklist while deploying:

- [ ] Netlify account created
- [ ] GitHub repository connected  
- [ ] Build settings configured correctly
- [ ] First deploy successful
- [ ] Site accessible at Netlify URL
- [ ] Backend API deployed (wait for this)
- [ ] `VITE_API_BASE_URL` environment variable added
- [ ] Site redeployed after adding variables
- [ ] API connection working
- [ ] Login functionality tested
- [ ] File upload tested
- [ ] All features working
- [ ] CORS configured correctly on backend
- [ ] Custom domain configured (if applicable)
- [ ] HTTPS enabled
- [ ] Performance acceptable
- [ ] No console errors

---

**Deployment Timeline:**
- Initial setup: 10 minutes
- First deploy: 3-5 minutes
- Add environment variables: 2 minutes
- Redeploy: 2-3 minutes
- **Total**: ~20 minutes (after backend is ready)

**You are here**: ✅ Step 1-5 (Deploy without backend)
**Next**: Wait for RunPod build, deploy backend, then complete Step 6-7