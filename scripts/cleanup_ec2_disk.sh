#!/bin/bash
# Cleanup script to free up disk space on EC2
# Moves large files to S3 and removes local copies

set -e

echo "🧹 Cleaning up EC2 disk space..."

# Clean pip cache
echo "Cleaning pip cache..."
pip cache purge 2>/dev/null || true

# Clean apt cache
echo "Cleaning apt cache..."
sudo apt clean
sudo apt autoremove -y

# Remove HuggingFace cache if it exists
HF_CACHE="${HOME}/.cache/huggingface"
if [ -d "$HF_CACHE" ]; then
    echo "Removing HuggingFace cache: $HF_CACHE"
    rm -rf "$HF_CACHE"
fi

# Remove temp HuggingFace cache
TEMP_HF_CACHE="/tmp/hf_cache"
if [ -d "$TEMP_HF_CACHE" ]; then
    echo "Removing temp HuggingFace cache: $TEMP_HF_CACHE"
    rm -rf "$TEMP_HF_CACHE"
fi

# Remove any .pth, .pt model files in project (should be in S3)
echo "Checking for local model files..."
find . -name "*.pth" -o -name "*.pt" -o -name "*.ckpt" 2>/dev/null | while read -r file; do
    echo "Found model file (should be in S3): $file"
done

# Clean Docker if not needed
echo "Cleaning Docker..."
docker system prune -f --volumes 2>/dev/null || true

# Show disk usage
echo ""
echo "📊 Disk usage after cleanup:"
df -h /

echo ""
echo "✅ Cleanup complete!"

