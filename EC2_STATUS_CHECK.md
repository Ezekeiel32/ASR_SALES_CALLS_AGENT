# EC2 Instance Status Check

## Current Issue
The EC2 instance at `98.93.53.57` is **currently unreachable**:
- SSH connection times out
- API (port 8000) not responding
- Both connections fail after 5 seconds

## What Was Completed Before Connection Lost

✅ **Code Deployed**: All files uploaded to EC2
✅ **Dependencies Installed**: All Python packages installed (165 packages)
✅ **Database Setup**: PostgreSQL running in Docker, migrations completed
✅ **Services Created**: Systemd services configured for API and Celery
✅ **Compatibility Fix**: Made DiarizationService optional to fix torchaudio issue

## What Needs to Be Done

### Step 1: Check Instance Status in AWS Console
1. Go to AWS EC2 Console
2. Find instance `i-0eb48174a09defc74`
3. Check status:
   - If "stopped" → Start it
   - If "running" → Check System Status Checks
   - If "terminated" → Need to create new instance

### Step 2: Verify Security Group
The security group should allow:
- Port 22 (SSH) from your IP
- Port 8000 (FastAPI) from 0.0.0.0/0 (or your IP)
- Port 80 (HTTP) from 0.0.0.0/0
- Port 443 (HTTPS) from 0.0.0.0/0

### Step 3: Check Instance Health
If instance is running but unreachable:
- Check CloudWatch logs
- Check instance console output (Actions → Monitor and troubleshoot → Get system log)
- Instance may have crashed due to disk space (was at 97% capacity earlier)

### Step 4: If Instance Crashed Due to Disk Space
If the instance crashed because disk filled up:
1. Stop the instance
2. Increase EBS volume size (Modify Volume)
3. Extend filesystem when restarting
4. Clean up unnecessary files

## Alternative: Use S3 for Large Files

As you asked about S3 + EC2 integration:

**Yes, S3 and EC2 work perfectly together!** We can:
- Store audio files in S3 instead of on EC2 disk
- Store PyTorch models in S3 and download on-demand
- Use S3 for meeting recordings and transcripts
- Keep EC2 disk minimal (just code + database)

This would solve the disk space issue we encountered.

## Next Steps

1. **Check AWS Console** - See if instance is running
2. **If running but unreachable** - May need to reboot or check security groups
3. **If stopped/crashed** - Restart and potentially resize disk
4. **Once accessible** - Continue with:
   - Verify API is running
   - Add API keys to .env
   - Test health endpoint
   - Configure frontend to point to EC2

## Quick Test Commands (Once Connected)

```bash
# Check if API is running
sudo systemctl status ivrimeet-api

# Check logs
sudo journalctl -u ivrimeet-api -n 50

# Test API
curl http://localhost:8000/healthz

# Check disk space
df -h
```

