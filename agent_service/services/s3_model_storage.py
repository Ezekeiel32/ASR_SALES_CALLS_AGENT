"""
S3-based model storage to reduce EC2 disk usage.

Downloads models from S3 on-demand instead of storing them locally.
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from agent_service.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class S3ModelStorage:
	"""
	Manages model storage in S3 and downloads on-demand.
	
	Stores:
	- PyAnnote models
	- SpeechBrain models
	- HuggingFace cache
	"""

	def __init__(self, s3_bucket: str | None = None, s3_region: str = "us-east-1") -> None:
		"""Initialize S3 model storage."""
		self.s3_bucket = s3_bucket or settings.s3_bucket
		self.s3_region = s3_region
		self.s3_client: boto3.client | None = None
		
		if self.s3_bucket:
			try:
				self.s3_client = boto3.client(
					"s3",
					region_name=self.s3_region,
					aws_access_key_id=settings.aws_access_key_id,
					aws_secret_access_key=settings.aws_secret_access_key,
				)
				logger.info(f"S3ModelStorage initialized with bucket: {self.s3_bucket}")
			except Exception as e:
				logger.warning(f"Failed to initialize S3 client: {e}. Models will be stored locally.")
	
	def get_model_path(self, model_name: str, cache_dir: Path | None = None) -> Path | None:
		"""
		Get model path from S3 or return None to download on-demand.
		
		Args:
			model_name: HuggingFace model identifier (e.g., "pyannote/speaker-diarization-3.1")
			cache_dir: Local cache directory for HuggingFace
		
		Returns:
			Path to local model file if found in S3, None otherwise
		"""
		if not self.s3_client or not self.s3_bucket:
			return None
		
		# Convert model name to S3 key
		s3_key = f"models/{model_name.replace('/', '_')}"
		
		try:
			# Check if model exists in S3
			self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
			
			# Download to temp directory
			if cache_dir is None:
				cache_dir = Path(tempfile.gettempdir()) / "hf_models"
			cache_dir.mkdir(parents=True, exist_ok=True)
			
			local_path = cache_dir / Path(s3_key).name
			
			if not local_path.exists():
				logger.info(f"Downloading model from S3: {s3_key}")
				self.s3_client.download_file(self.s3_bucket, s3_key, str(local_path))
			
			return local_path
		except ClientError as e:
			if e.response["Error"]["Code"] == "404":
				logger.debug(f"Model not found in S3: {s3_key}, will download from HuggingFace")
			else:
				logger.warning(f"Error checking S3 for model {s3_key}: {e}")
			return None
	
	def upload_model(self, local_path: Path, model_name: str) -> bool:
		"""
		Upload a model to S3 after downloading from HuggingFace.
		
		Args:
			local_path: Local path to model file
			model_name: HuggingFace model identifier
		
		Returns:
			True if upload successful, False otherwise
		"""
		if not self.s3_client or not self.s3_bucket:
			return False
		
		if not local_path.exists():
			logger.warning(f"Local model file not found: {local_path}")
			return False
		
		s3_key = f"models/{model_name.replace('/', '_')}"
		
		try:
			logger.info(f"Uploading model to S3: {s3_key}")
			self.s3_client.upload_file(
				str(local_path),
				self.s3_bucket,
				s3_key,
			)
			logger.info(f"Model uploaded to S3: {s3_key}")
			
			# Delete local file to save space
			try:
				local_path.unlink()
				logger.info(f"Deleted local model file: {local_path}")
			except Exception as e:
				logger.warning(f"Failed to delete local model file: {e}")
			
			return True
		except Exception as e:
			logger.error(f"Failed to upload model to S3: {e}")
			return False


def configure_huggingface_cache_for_s3() -> None:
	"""
	Configure HuggingFace to use S3 for cache when possible.
	
	Sets environment variables to minimize local cache usage.
	"""
	import os
	
	# Set HuggingFace cache to temp directory (will be cleaned up)
	cache_dir = os.path.join(tempfile.gettempdir(), "hf_cache")
	os.environ["HF_HOME"] = cache_dir
	os.environ["TRANSFORMERS_CACHE"] = cache_dir
	os.environ["HF_DATASETS_CACHE"] = cache_dir
	
	logger.info(f"HuggingFace cache configured to: {cache_dir}")

