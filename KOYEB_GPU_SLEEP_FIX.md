# Fixing Deep Sleep on GPU Instances (No Light Sleep)

## 🚨 Problem: GPU Instance Limitations

**Your Situation:**
- Using **RTX-4000-SFF-ADA GPU instance**
- **Light sleep** is NOT available (only for Standard CPU instances)
- Even with `min: 1`, GPU instances might still deep sleep due to cost-saving measures
- **Idle period: 300 seconds** is triggering deep sleep

## ✅ Solutions

### Solution 1: Increase Idle Period (Quick Fix)

Since you can't use light sleep, make deep sleep very unlikely:

1. In **"Scale to zero configuration"** section:
   - Change **"Idle period"** from `300` seconds to `999999` seconds
   - This is ~277 hours (effectively disables auto-sleep)
2. Click **"Relaunch to update"**
3. Instance should now stay awake much longer

**Pros:** Simple, quick fix
**Cons:** Still might sleep if idle for days, but unlikely in normal use

### Solution 2: Use Keepalive Ping (Already Implemented) ✅

The frontend keepalive ping will prevent sleep:
- Pings every 4 minutes (before 5 min timeout)
- Works regardless of GPU/CPU instance type
- No configuration needed once deployed

**This is your best bet!** The keepalive will keep the instance awake.

### Solution 3: Split Services (Cost Optimization)

**Current Setup:**
- API + Worker both on GPU (expensive, $375/mo)

**Better Setup:**
- **API Service:** Standard CPU instance
  - Min: 1, Max: 1
  - Cost: ~$15-30/mo (much cheaper)
  - Light sleep available ✅
  - Fast enough for HTTP requests
  
- **Worker Service:** GPU instance
  - Min: 1, Max: 2
  - Cost: ~$375/mo (for ML processing)
  - Only worker needs GPU for PyAnnote/SpeechBrain

**Benefits:**
- Total cost similar or less
- API stays awake reliably (CPU instances respect min: 1 better)
- Better resource allocation (GPU only where needed)

### Solution 4: Accept Sleep, Use Keepalive

If GPU instances have limitations with `min: 1`:
- Keep current setup
- Rely on frontend keepalive ping (every 4 min)
- First request after long idle might have 10-30s cold start
- But keepalive should prevent most sleeps

## 🎯 Recommended Action Plan

### Immediate (Do Now):
1. Set **"Idle period"** to `999999` seconds
2. Click **"Relaunch to update"**
3. Wait for frontend to deploy with keepalive ping

### Short Term:
- Verify keepalive is working (check browser console for `/healthz` requests)
- Monitor logs - should see health checks every 4 minutes

### Long Term (Cost Optimization):
- Consider splitting API to CPU instance
- Keep GPU only for worker service
- Much better cost/performance ratio

## 📊 Cost Comparison

**Current (Both on GPU):**
- API: GPU min:1 = $375/mo
- Worker: GPU min:1 = $375/mo
- **Total: $750/mo** 💰💰

**Optimized (API on CPU):**
- API: CPU min:1 = $15-30/mo
- Worker: GPU min:1 = $375/mo
- **Total: $390-405/mo** 💰 (Savings: $345-360/mo!)

## 🔍 Verify It's Working

After increasing idle period and deploying keepalive:

1. **Wait 10+ minutes** without using app
2. **Check service status:** Should stay "Running"
3. **Check logs:** 
   - Should see `/healthz` requests every ~4 minutes
   - Should NOT see "No traffic detected" or deep sleep messages
4. **Test upload:** Should work immediately (no cold start)

## ⚠️ GPU Instance Behavior

**Why GPU instances might still sleep:**
- GPU instances are expensive ($0.50/hr)
- Koyeb might have aggressive cost-saving for GPU
- Even `min: 1` might have exceptions for GPU
- Pro trial might have different behavior

**Why keepalive helps:**
- Traffic keeps instance awake regardless of settings
- Works with any instance type
- Automatic and reliable

## 💡 Best Practice

**For Production:**
1. **API Service:** Use Standard CPU instance
   - Cheaper, more reliable, light sleep available
   - HTTP requests don't need GPU
   
2. **Worker Service:** Use GPU instance
   - Only service that needs GPU for ML models
   - Set min: 1 to keep processing queue active

3. **Frontend Keepalive:** Add as backup
   - Prevents sleep even if scaling misbehaves
   - Works universally

---

**For now: Increase idle period to 999999 and let the keepalive ping handle it!** 🚀

