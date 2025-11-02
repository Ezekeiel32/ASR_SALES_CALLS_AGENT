# Fix: Change Minimum Instances from 0 to 1

## 🎯 What I See in Your Screenshot

In the **Scaling** section:
- **Minimum:** `0` ❌ **This is the problem!**
- **Maximum:** `1`
- **Idle period:** `300` seconds (5 minutes)

## ✅ Quick Fix - Two Options

### Option 1: Set Minimum to 1 (Recommended)

1. **Find the "Minimum" slider** in the Scaling section
2. **Drag it from `0` to `1`** (or type `1` in the input)
3. The cost estimate will update:
   - Min: $0.50/hr, $375.00/mo (this is the always-on cost)
   - Max: $0.50/hr, $375.00/mo (same since max is 1)
4. **Click "Relaunch to update"** button (top right) or scroll down and save

This will keep 1 instance always running, preventing deep sleep.

### Option 2: Disable Scale-to-Zero (Alternative)

Instead of setting minimum to 1, you could also:
1. Find **"Scale to zero configuration"** section
2. Set **"Idle period"** to a very high value (e.g., `999999` seconds) or disable it
3. But **Option 1 is better** because it's cleaner and more predictable

## 📊 What Changes

**Before (Current - Causes Deep Sleep):**
```
Minimum: 0  ← Instance can scale to zero
Maximum: 1
Idle period: 300 seconds
Result: Instance stops after 5 min of no traffic ❌
```

**After (Fixed - Stays Awake):**
```
Minimum: 1  ← At least 1 instance always running
Maximum: 1
Idle period: (not relevant when min=1)
Result: Instance stays running 24/7 ✅
```

## 💰 Cost Impact

**Current:** $0.00/hr (only when running)
**After Fix:** $0.50/hr = $375.00/mo (always-on instance)

**Note:** 
- You're on Pro trial, so you might have credits
- GPU instances are more expensive but provide better performance
- Consider if you need GPU 24/7 or can use a cheaper instance for API

## ⚡ After Making the Change

1. **Click "Relaunch to update"** or save the settings
2. **Wait 1-2 minutes** for the instance to update
3. **Check service status** - should show "Running" (green)
4. **Wait 10+ minutes** without making requests
5. **Verify** - status should still be "Running" (not "Stopped")
6. **Check logs** - should NOT see "No traffic detected" messages

## 🔄 Alternative: Use Standard CPU Instance (If GPU Not Needed)

If you don't need GPU for the API service:
1. You could switch to a **Standard CPU instance** (cheaper)
2. Keep GPU instance only for worker (which processes heavy ML tasks)
3. Set CPU instance `min: 1` (much cheaper than GPU)

**API Service (FastAPI):**
- Doesn't need GPU (just HTTP requests)
- Standard CPU instance would work fine
- Much cheaper for always-on

**Worker Service (Celery + ML):**
- Needs GPU for PyAnnote/SpeechBrain models
- Can keep GPU instance with `min: 1`

## ✅ Recommendation

**For Now:**
1. Change **Minimum: 0 → 1** in the screenshot
2. Click **"Relaunch to update"**
3. This will keep your instance awake

**For Later (Cost Optimization):**
- Consider separating API and Worker:
  - **API Service:** Standard CPU instance, `min: 1` (~$0.02/hr)
  - **Worker Service:** GPU instance, `min: 1` (~$0.50/hr)

---

**The fix is simple: Just drag that Minimum slider from `0` to `1` and save!** 🚀

