#!/bin/bash
# Setup script to configure S3 for model storage
# Run this on EC2 after setting up S3 bucket

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <s3-bucket-name> [s3-region]"
    echo "Example: $0 my-models-bucket us-east-1"
    exit 1
fi

S3_BUCKET="$1"
S3_REGION="${2:-us-east-1}"

echo "📦 Setting up S3 for model storage..."
echo "Bucket: $S3_BUCKET"
echo "Region: $S3_REGION"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Create S3 bucket structure
echo "Creating S3 bucket structure..."
aws s3 mb "s3://${S3_BUCKET}" --region "$S3_REGION" 2>/dev/null || echo "Bucket already exists"

# Set up lifecycle policy to move to cheaper storage
cat > /tmp/lifecycle.json <<EOF
{
    "Rules": [
        {
            "Id": "MoveOldModelsToGlacier",
            "Status": "Enabled",
            "Prefix": "models/",
            "Transitions": [
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket "$S3_BUCKET" \
    --lifecycle-configuration file:///tmp/lifecycle.json

rm /tmp/lifecycle.json

echo ""
echo "✅ S3 setup complete!"
echo ""
echo "Add to your .env file:"
echo "S3_BUCKET=$S3_BUCKET"
echo "S3_REGION=$S3_REGION"
echo "AWS_ACCESS_KEY_ID=your_access_key"
echo "AWS_SECRET_ACCESS_KEY=your_secret_key"

