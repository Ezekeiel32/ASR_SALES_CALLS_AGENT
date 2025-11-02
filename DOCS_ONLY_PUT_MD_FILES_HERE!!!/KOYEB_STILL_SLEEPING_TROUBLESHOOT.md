# Troubleshooting: Still Sleeping Even with Min: 1

## 🔍 If Minimum is Already 1 But Still Sleeping

### Possible Causes:

#### 1. **Changes Not Applied Yet**
- Did you click **"Relaunch to update"** after changing Minimum to 1?
- The instance needs to be relaunched for scaling changes to take effect
- Check service status - it should relaunch after the change

#### 2. **Idle Period Still Active**
Even with `min: 1`, if there's an "Idle period" setting:
- Try setting **"Idle period"** to a very high value (e.g., `999999` seconds)
- Or check if there's an option to **disable** scale-to-zero entirely
- With `min: 1`, idle period shouldn't matter, but some Koyeb versions might have bugs

#### 3. **Multiple Services - Check Both**
Make sure BOTH services have `min: 1`:
- **API Service** - Should have `min: 1`
- **Worker Service** - Should also have `min: 1`

Go to:
- Services → `api` → Scaling → Check Minimum
- Services → `worker` → Scaling → Check Minimum

#### 4. **Plan/Trial Limitations**
Your Pro trial might have limitations:
- Some trial plans still allow deep sleep even with `min: 1`
- Check if there's an "Always On" or "No Sleep" option
- Verify trial features in Koyeb docs

#### 5. **Region-Specific Settings**
If you have multiple regions:
- Check scaling per region
- Each region might need `min: 1` separately

## ✅ Verification Steps

1. **Check Current State:**
   - Settings → Scaling → Minimum should be `1`
   - Settings → Scaling → Maximum should be `1` (or higher)
   - Settings → Scale to zero → Idle period (try disabling/increasing)

2. **Verify It's Applied:**
   - Check service status (should show "Running")
   - Look at service events for any scaling actions
   - Check if instance was relaunched after change

3. **Test After 10 Minutes:**
   - Wait 10+ minutes without making requests
   - Service should stay "Running" (green)
   - Should NOT see "No traffic detected" in logs

## 🔧 Additional Fixes to Try

### Fix 1: Disable Idle Period Entirely
In "Scale to zero configuration":
- Set "Idle period" to `999999` (very high number)
- Or look for a checkbox to disable scale-to-zero

### Fix 2: Verify Both API and Worker
Check both services:
```bash
API Service:
  Min: 1
  Max: 1 (or higher)
  
Worker Service:
  Min: 1
  Max: 2
```

### Fix 3: Check Service Events
1. Go to service → **"Events"** tab
2. Look for scaling events
3. Check if there are any errors preventing `min: 1` from working

### Fix 4: Force Relaunch
1. Settings → Click **"Relaunch to update"**
2. Or manually trigger a redeploy
3. Wait for service to fully start
4. Check scaling is applied

## 💡 The Keepalive Ping Should Help

Even if Koyeb has a bug with `min: 1`, the frontend keepalive ping (every 4 minutes) should prevent sleep by keeping traffic active.

**Check if keepalive is working:**
- Frontend deployed? (Netlify should auto-deploy)
- Open browser console
- Should see health check requests every 4 minutes
- Backend logs should show `/healthz` requests

## 🐛 If Still Not Working

**Last Resort Options:**

1. **Contact Koyeb Support:**
   - Report that `min: 1` isn't preventing deep sleep
   - Might be a bug with GPU instances or Pro trial

2. **Alternative: Increase Idle Period:**
   - If you can't prevent sleep entirely
   - Set idle period to very high (e.g., 1 hour = 3600 seconds)
   - This at least reduces frequency of sleep cycles

3. **Check if it's the Worker Sleeping:**
   - Maybe it's the worker service that's sleeping, not API?
   - Check worker service scaling settings too

## 📊 What to Check Right Now

1. **API Service Scaling:**
   - Min: `1` ✅
   - Max: `1` or higher
   - Idle period: Try `999999` or disable

2. **Worker Service Scaling:**
   - Min: `1` ✅
   - Max: `2`

3. **Service Status:**
   - Both should show "Running" (green)
   - Not "Stopped" or cycling

4. **Recent Logs:**
   - Should NOT see "No traffic detected in the past 300 seconds"
   - Should NOT see constant restarts

---

**The keepalive ping should help regardless of Koyeb's scaling behavior!** 🚀

