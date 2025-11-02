# Starting Celery Worker on Koyeb

## 🚨 Error: "instance with status STOPPED"

If you see this error, the Koyeb service is **stopped** and needs to be started.

## ✅ Solution: Start the Service

### Option 1: Koyeb Dashboard (Recommended)

1. **Go to Koyeb Dashboard**: https://console.koyeb.com
2. **Navigate to your App** → "Services"
3. **Find your worker service** (should be named `worker` or similar)
4. **Check Status:**
   - If status shows "Stopped" → Click **"Start"** or **"Restart"**
   - Wait for status to change to "Running"

### Option 2: Koyeb CLI

```bash
# List your services
koyeb services list

# Start a specific service
koyeb services start <service-id>

# Or restart
koyeb services restart <service-id>
```

## 🔍 Verify Service is Running

1. **Check Service Status:**
   - Dashboard → Your App → Services
   - Status should be **"Running"** (green indicator)

2. **Check Logs:**
   - Click on worker service → "Logs" tab
   - You should see:
     ```
     celery@... ready.
     [INFO] Connected to redis://...
     ```

3. **Test Connection:**
   - If logs show connection errors, check:
     - `REDIS_URL` environment variable is set
     - Redis service is accessible
     - SSL configuration is correct (for `rediss://`)

## 🐛 Troubleshooting

### Service Keeps Stopping

**Possible Causes:**
- **Memory limit exceeded**: Worker crashed due to memory
- **Startup errors**: Check logs for Python/Celery errors
- **Resource limits**: Free tier has limits

**Solutions:**
- Check logs for crash reasons
- Increase service resources if needed
- Verify all environment variables are set

### Service Won't Start

**Check:**
1. **Build Status**: Service must build successfully first
2. **Environment Variables**: All required vars must be set
3. **Dockerfile**: Must be valid and buildable
4. **Command**: Start command must be correct

### Auto-Start Configuration

By default, Koyeb services auto-start when deployed. If your service stops:

1. **Check Scaling Settings:**
   - Min instances should be ≥ 1 for worker
   - Go to service → "Scaling" → Set min: 1

2. **Check Auto-Scaling:**
   - Worker should not scale to 0
   - Ensure minimum is always 1

## 📋 Quick Start Checklist

- [ ] Service is created in Koyeb dashboard
- [ ] Service status is "Running" (not "Stopped")
- [ ] Environment variables are set (especially `REDIS_URL`)
- [ ] Logs show "celery@... ready"
- [ ] No errors in logs about Redis connection
- [ ] Scaling min is set to 1

## 💡 Pro Tip

**Keep Worker Always Running:**
- Set scaling minimum to 1
- This ensures tasks are processed immediately
- Free tier allows this, you just pay for what you use

## 🎯 Next Steps

Once service is running:

1. **Upload a test meeting** from frontend
2. **Watch worker logs** for processing messages
3. **Verify meeting status** changes from `pending` → `processing` → `completed`

---

**Your worker is ready to process meetings once the service is started!** 🚀

