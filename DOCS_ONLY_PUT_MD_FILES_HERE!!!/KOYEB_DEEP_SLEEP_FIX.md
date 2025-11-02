# Fixing Koyeb Deep Sleep / Constant Restarts

## 🚨 Problem: Instance Keeps Starting and Stopping

Your Koyeb instance is constantly cycling:
1. Starts → Health checks pass
2. After 300 seconds (5 min) of no traffic → "Transitioning to deep sleep"
3. Stops
4. New request arrives → Wakes up → Cold start (slow)
5. Repeat...

## ✅ Solution: Configure Scaling to Keep Instance Always Running

### Option 1: Koyeb Dashboard (Recommended)

1. **Go to Koyeb Dashboard** → Your App → **Services**
2. **Click on your API service** → **"Scaling"** tab
3. **Set Minimum Instances:**
   - **Min Instances**: `1` (instead of `0`)
   - **Max Instances**: Keep at `3` (or your preferred max)
   - **Save**

This ensures at least 1 instance stays running at all times, preventing deep sleep.

### Option 2: Update koyeb.yaml

Update your `koyeb.yaml` to set `min: 1`:

```yaml
services:
  - name: api
    type: web
    dockerfile: Dockerfile
    ports:
      - port: 8000
    env:
      - name: PORT
        value: "8000"
      - name: PYTHONUNBUFFERED
        value: "1"
    healthcheck:
      path: /healthz
      interval: 30
      timeout: 10
    scaling:
      min: 1  # ✅ Keep at least 1 instance always running
      max: 3
```

Then redeploy or let auto-deploy pick it up.

## 🎯 Why This Happens

**Koyeb's Auto-Scaling:**
- Default behavior: Scale to `0` when idle (saves resources)
- After 300 seconds of no traffic → Deep sleep
- Cold start takes 10-30 seconds when waking up

**Impact:**
- Slow response on first request after sleep
- User uploads timeout during cold start
- Constant restart cycling in logs

## 📊 Resource Considerations

**Keeping 1 Instance Running:**
- ✅ **Fast response times** (no cold starts)
- ✅ **Better user experience** (uploads work immediately)
- ✅ **Stable service** (no constant restarts)
- ⚠️ **Cost**: Instance runs 24/7 (check your plan)

**Free Tier Note:**
- Some free tiers have limitations on min instances
- Pro trial should allow `min: 1`
- If not available, consider upgrading plan

## 🔧 Alternative Solutions (If Min: 1 Not Available)

### 1. Keep-Alive Ping (Frontend)

Add a periodic health check to prevent sleep:

```typescript
// In your frontend, add keepalive ping
setInterval(async () => {
  try {
    await fetch(`${API_BASE_URL}/healthz`);
  } catch (e) {
    // Ignore errors - just prevent sleep
  }
}, 4 * 60 * 1000); // Every 4 minutes (before 5 min timeout)
```

### 2. Longer Health Check Interval

If possible, configure health checks to ping more frequently:
- Health checks keep instance "active"
- More frequent checks = less likely to sleep

### 3. Upgrade Plan

Some Koyeb plans have different auto-sleep policies:
- **Hobby**: May auto-sleep after inactivity
- **Pro**: Better scaling control, less aggressive sleep
- **Enterprise**: Full control over scaling

## ✅ Recommended Configuration

**Best Practice:**
```yaml
scaling:
  min: 1    # Always keep 1 instance running
  max: 3    # Scale up during high traffic
```

**Benefits:**
- No cold starts
- Consistent performance
- Better user experience
- Stable uploads

## 🐛 Verify It's Working

After setting `min: 1`:

1. **Check Service Status:**
   - Dashboard → Service → Should show "Running" (not "Stopped")
   - Even after 10+ minutes of no traffic

2. **Check Logs:**
   - Should NOT see "No traffic detected in the past 300 seconds"
   - Should NOT see constant "Instance created" / "Instance stopped" cycles

3. **Test Upload:**
   - Should respond immediately (no 10-30s cold start delay)

## 💡 Pro Tip

If you're on Pro trial and still seeing deep sleep:
- Check if there's a "Always On" or "No Sleep" setting in service settings
- Contact Koyeb support if `min: 1` isn't preventing sleep
- Verify you're not on a plan that enforces sleep regardless of scaling

---

**The fix is simple: Set `scaling.min: 1` to keep your instance always running!** 🚀

