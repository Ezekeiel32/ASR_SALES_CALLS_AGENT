# How to Check and Update Scaling in Koyeb Dashboard

## 📍 Step-by-Step Guide

### Step 1: Open Koyeb Dashboard
1. Go to **https://console.koyeb.com**
2. Log in to your account

### Step 2: Navigate to Your App
1. In the left sidebar, click **"Apps"** or **"Services"**
2. Find and click on your app name (e.g., "zpe" or "ivrimeet")
3. You'll see your app overview page

### Step 3: Go to Services
1. In your app page, you'll see tabs/sections:
   - **Overview**
   - **Services** ← **Click this**
   - **Domains**
   - **Secrets**
   - **Settings**
2. Click on **"Services"** tab

### Step 4: Select Your API Service
1. You'll see a list of services:
   - `api` (or your API service name) - **Click this**
   - `worker` (your Celery worker)
2. Click on the **`api`** service

### Step 5: Find Scaling Settings
1. You'll see the service details page
2. Look for tabs or sections:
   - **Overview**
   - **Logs**
   - **Scaling** ← **Click this**
   - **Environment Variables**
   - **Settings**
   - **Events**
3. Click on **"Scaling"** tab

### Step 6: Check and Update Scaling
You should see:
```
Minimum Instances: [1]  ← Should be 1, not 0
Maximum Instances: [3]
```

**If Minimum Instances is `0`:**
1. Change it to **`1`**
2. Click **"Save"** or **"Update"** button
3. Wait for the change to apply

## 🎯 What It Should Look Like

**Correct Configuration:**
```
Scaling Configuration:
├─ Minimum Instances: 1  ✅
└─ Maximum Instances: 3
```

**Wrong Configuration (Causes Deep Sleep):**
```
Scaling Configuration:
├─ Minimum Instances: 0  ❌ (This allows deep sleep!)
└─ Maximum Instances: 3
```

## 📋 Alternative Paths

If you can't find "Scaling" tab, try:

### Path A: Through Settings
1. Service → **"Settings"** tab
2. Look for **"Scaling"** or **"Resources"** section
3. Update minimum instances there

### Path B: Through Service Overview
1. Service → **"Overview"** tab
2. Look for a **"Edit"** or **"Configure"** button
3. This might open a modal with scaling options

### Path C: Through App Settings
1. Go back to App level
2. App → **"Settings"** → Look for scaling options

## 🔍 Visual Indicators

**In Koyeb Dashboard:**
- Service status should show **"Running"** (green) when `min: 1`
- Service status might show **"Stopped"** or cycle when `min: 0`

**In Service Details:**
- Look for any section labeled:
  - "Scaling"
  - "Auto-scaling"
  - "Instances"
  - "Resources"
  - "Configuration"

## ✅ Verify It's Working

After setting `min: 1`:

1. **Wait 10+ minutes** without making requests
2. **Check Service Status:**
   - Should still show **"Running"** (green)
   - Should NOT show "Stopped" or "Sleeping"

3. **Check Logs:**
   - Should NOT see "No traffic detected in the past 300 seconds"
   - Should NOT see constant "Instance created" / "Instance stopped" cycles

## 🚨 If You Can't Find Scaling Tab

**Possible Reasons:**
1. **Free Tier Limitation:** Some free tiers might not show scaling options
2. **Service Type:** Worker services might have different UI
3. **Plan Restrictions:** Lower plans might not allow `min: 1`

**Solutions:**
1. Check if you're on a plan that supports scaling (Pro trial should)
2. Try updating via `koyeb.yaml` and redeploy
3. Contact Koyeb support if options are missing

## 💡 Pro Tip

**Quick URL Pattern:**
If you know your app ID, you can try:
```
https://console.koyeb.com/apps/[APP-ID]/services/[SERVICE-ID]/scaling
```

Replace `[APP-ID]` and `[SERVICE-ID]` with your actual IDs.

## 📸 What to Look For

**The scaling section typically shows:**
- Current instance count
- Minimum/Maximum instance settings
- Scaling metrics (CPU, memory)
- Auto-scaling rules

**Key Field:**
- **"Minimum Instances"** or **"Min Instances"** - This is what you need to set to `1`

---

**The frontend keepalive ping will also help, but setting `min: 1` in the dashboard is the primary fix!** 🚀

