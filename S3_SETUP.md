# S3 Integration for EC2 - Reduce Disk Usage

## Problem
EC2 instances have limited disk space (8GB default). Large PyTorch models and HuggingFace cache can fill up the disk quickly.

## Solution
Store all large files in S3 and download on-demand.

## What Gets Stored in S3

✅ **Audio Files**: All meeting recordings
✅ **Audio Snippets**: 15-second speaker snippets
✅ **Models**: PyAnnote and SpeechBrain models (after first download)
✅ **HuggingFace Cache**: Configured to use temp directory, cleaned up automatically

## Setup Instructions

### 1. Create S3 Bucket

```bash
aws s3 mb s3://ivrimeet-models --region us-east-1
```

Or use the setup script:

```bash
./scripts/setup_s3_models.sh ivrimeet-models us-east-1
```

### 2. Configure IAM Permissions

Create an IAM user with S3 access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ivrimeet-models/*",
        "arn:aws:s3:::ivrimeet-models"
      ]
    }
  ]
}
```

### 3. Update .env on EC2

Add to `/home/ubuntu/ASR_SALES_CALLS_AGENT/.env`:

```bash
S3_BUCKET=ivrimeet-models
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 4. Run Cleanup Script

On EC2, run:

```bash
cd /home/ubuntu/ASR_SALES_CALLS_AGENT
./scripts/cleanup_ec2_disk.sh
```

This will:
- Remove pip cache
- Remove HuggingFace cache
- Clean apt cache
- Clean Docker
- Show disk usage

## How It Works

### Models
- Models download from HuggingFace on first use
- If S3 is configured, models are uploaded to S3 after download
- Local model files are deleted after upload
- Next time, models download from S3 (faster) or HuggingFace (if not in S3)

### Audio Files
- All uploaded audio goes directly to S3
- Snippets are stored in S3
- Only temporary files stay on EC2 (cleaned up automatically)

### HuggingFace Cache
- Configured to use `/tmp/hf_cache` (cleaned on reboot)
- Cache is minimal - only keeps what's actively being used
- Old cache files are automatically cleaned up

## Disk Space Savings

Before S3:
- PyTorch models: ~2-3GB
- HuggingFace cache: ~1-2GB
- Audio files: Variable (can be huge)
- Total: Can easily fill 8GB

After S3:
- Code + dependencies: ~1GB
- Database: ~500MB
- Temp files: ~100MB
- Total: ~2GB (safe for 8GB instance)

## Monitoring Disk Usage

```bash
# Check disk usage
df -h /

# Check what's using space
du -sh /home/ubuntu/ASR_SALES_CALLS_AGENT/*
```

## Troubleshooting

### Models Not Loading from S3
- Check S3 bucket permissions
- Verify AWS credentials in .env
- Check logs for S3 errors

### Disk Still Filling Up
- Run cleanup script: `./scripts/cleanup_ec2_disk.sh`
- Check for temp files: `find /tmp -type f -size +100M`
- Verify S3 uploads are working

### Models Downloading Every Time
- This is expected on first run for each model
- After first download, models should be in S3
- Check S3 bucket to verify models were uploaded

