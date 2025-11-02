# S3 Integration for Koyeb - Model Storage

## Overview
Store all large ML models in S3 and download on-demand to reduce container disk usage and improve cold start times.

## Solution
Store PyAnnote and SpeechBrain models in S3, download on-demand when needed.

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

### 3. Configure Environment Variables

In Koyeb dashboard, add these environment variables:

```bash
S3_BUCKET=ivrimeet-models
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

Or if using `.env` file locally:

```bash
S3_BUCKET=ivrimeet-models
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## How It Works

### Models
- Models download from HuggingFace on first use
- If S3 is configured, models are uploaded to S3 after download
- Local model files are deleted after upload
- Next time, models download from S3 (faster) or HuggingFace (if not in S3)

### Audio Files
- All uploaded audio goes directly to S3
- Snippets are stored in S3
- Only temporary files stay in container (cleaned up automatically)

### HuggingFace Cache
- Configured to use temp directory (automatically cleaned)
- Cache is minimal - only keeps what's actively being used
- Old cache files are automatically cleaned up on container restart

## Benefits

**Storage Efficiency:**
- Models stored in S3 (persistent, shared across deployments)
- Minimal local cache (reduces container size)
- Faster cold starts (smaller container images)

**Cost Savings:**
- S3 storage is cheaper than larger container storage
- Models can be shared across multiple deployments
- Automatic cleanup of temporary files

## Troubleshooting

### Models Not Loading from S3
- Check S3 bucket permissions
- Verify AWS credentials in .env
- Check logs for S3 errors

### Disk Still Filling Up
- Check Koyeb container logs for disk usage warnings
- Verify S3 uploads are working (check logs)
- Models should auto-cleanup after use

### Models Downloading Every Time
- This is expected on first run for each model
- After first download, models should be in S3
- Check S3 bucket to verify models were uploaded

