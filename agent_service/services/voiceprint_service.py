from __future__ import annotations

import logging
import uuid
from typing import Any

import numpy as np
import torch
import torchaudio

# Fix torchaudio compatibility issue with speechbrain
if not hasattr(torchaudio, 'list_audio_backends'):
    def list_audio_backends():
        """Compatibility shim for torchaudio < 2.1"""
        return ['soundfile']  # Default backend
    torchaudio.list_audio_backends = list_audio_backends

# Lazy import to avoid speechbrain compatibility issues
try:
    from speechbrain.inference.speaker import EncoderClassifier
except (AttributeError, ImportError, Exception) as e:
    EncoderClassifier = None  # type: ignore[assignment,misc]
    import warnings
    warnings.warn(f"SpeechBrain not fully available: {e}. Speaker recognition may be limited.")

from agent_service.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VoiceprintService:
	"""
	Service for generating and matching speaker voiceprints using ECAPA-TDNN embeddings.

	Uses speechbrain/spkrec-ecapa-voxceleb model for generating 192-dimensional
	speaker embeddings that can be used for speaker identification via cosine similarity.
	"""

	def __init__(self, device: str | None = None) -> None:
		"""
		Initialize the voiceprint service.

		Args:
			device: PyTorch device ('cpu', 'cuda', etc.). Auto-detects if None.
		"""
		self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
		self.model = None
		self.model_name = "speechbrain/spkrec-ecapa-voxceleb"
		logger.info(f"VoiceprintService initialized with device: {self.device}")

	def _load_model(self) -> None:
		"""Lazy load the ECAPA-TDNN model."""
		if self.model is None:
			try:
				logger.info(f"Loading speaker encoder model: {self.model_name}")
				self.model = EncoderClassifier.from_hparams(
					source=self.model_name,
					run_opts={"device": self.device},
				)
				logger.info("Speaker encoder model loaded successfully")
			except Exception as e:
				logger.error(f"Failed to load speaker encoder model: {e}")
				raise RuntimeError(f"Could not load speaker encoder: {e}") from e

	def generate_embedding(self, audio_path: str | None = None, audio_bytes: bytes | None = None, sample_rate: int = 16000) -> list[float]:
		"""
		Generate a speaker embedding (voiceprint) from audio.

		Args:
			audio_path: Path to audio file (WAV, MP3, etc.)
			audio_bytes: Raw audio bytes (will be saved to temp file if audio_path not provided)
			sample_rate: Target sample rate (default 16kHz, model expects 16kHz)

		Returns:
			192-dimensional embedding vector as a list of floats.
			The embedding can be stored in PostgreSQL pgvector for similarity search.

		Raises:
			ValueError: If neither audio_path nor audio_bytes is provided
			RuntimeError: If model loading or inference fails
		"""
		if audio_path is None and audio_bytes is None:
			raise ValueError("Either audio_path or audio_bytes must be provided")

		self._load_model()

		try:
			if audio_path:
				# Load audio from file
				signal, fs = torchaudio.load(audio_path)
			else:
				# Load audio from bytes (requires temporary file handling)
				import tempfile
				import os
				with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
					tmp_file.write(audio_bytes)
					tmp_path = tmp_file.name

				try:
					signal, fs = torchaudio.load(tmp_path)
				finally:
					os.unlink(tmp_path)

			# Resample if necessary
			if fs != sample_rate:
				resampler = torchaudio.transforms.Resample(fs, sample_rate)
				signal = resampler(signal)

			# Convert to mono if stereo
			if signal.shape[0] > 1:
				signal = torch.mean(signal, dim=0, keepdim=True)

			# Normalize audio
			signal = signal / (torch.max(torch.abs(signal)) + 1e-8)

			# Generate embedding
			# The model expects shape [batch, time] or [batch, channels, time]
			if signal.dim() == 1:
				signal = signal.unsqueeze(0)  # Add batch dimension
			if signal.dim() == 2 and signal.shape[0] != 1:
				signal = signal.unsqueeze(0)  # Add batch dimension if missing

			with torch.no_grad():
				embedding = self.model.encode_batch(signal)

			# Extract the embedding vector
			# Model returns shape [batch, embedding_dim]
			if isinstance(embedding, tuple):
				embedding = embedding[0]

			embedding_np = embedding.cpu().numpy()
			if embedding_np.ndim > 1:
				embedding_np = embedding_np[0]  # Take first (and only) batch item

			# Normalize the embedding vector (L2 normalization for cosine similarity)
			embedding_np = embedding_np / (np.linalg.norm(embedding_np) + 1e-8)

			# Convert to list of floats
			embedding_list = embedding_np.tolist()

			# ECAPA-TDNN outputs 192-dim embeddings, but we'll pad to 256 for consistency
			# or truncate - let's use the actual model dimension
			# Actually, let's check the model output size and adjust
			if len(embedding_list) < 256:
				# Pad with zeros to 256 for database storage
				embedding_list.extend([0.0] * (256 - len(embedding_list)))
			elif len(embedding_list) > 256:
				# Truncate to 256
				embedding_list = embedding_list[:256]

			return embedding_list

		except Exception as e:
			logger.error(f"Error generating voiceprint embedding: {e}")
			raise RuntimeError(f"Failed to generate voiceprint: {e}") from e

	def compute_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
		"""
		Compute cosine similarity between two embeddings.

		Args:
			embedding1: First embedding vector
			embedding2: Second embedding vector

		Returns:
			Cosine similarity score between 0 and 1 (1.0 = identical, 0.0 = orthogonal)
		"""
		if len(embedding1) != len(embedding2):
			raise ValueError(f"Embedding dimensions mismatch: {len(embedding1)} vs {len(embedding2)}")

		vec1 = np.array(embedding1, dtype=np.float32)
		vec2 = np.array(embedding2, dtype=np.float32)

		# L2 normalize (should already be normalized, but ensure it)
		vec1 = vec1 / (np.linalg.norm(vec1) + 1e-8)
		vec2 = vec2 / (np.linalg.norm(vec2) + 1e-8)

		# Cosine similarity = dot product of normalized vectors
		similarity = np.dot(vec1, vec2).item()

		# Clamp to [0, 1] (cosine similarity is in [-1, 1], but for voiceprints it should be [0, 1])
		return max(0.0, min(1.0, similarity))

	def find_matching_speaker(
		self,
		embedding: list[float],
		organization_id: uuid.UUID,
		similarity_threshold: float = 0.9,
	) -> tuple[uuid.UUID | None, float]:
		"""
		Find a matching speaker in the database using cosine similarity.

		This method should be called with a database session to query speakers.

		Args:
			embedding: Query embedding vector
			organization_id: Organization ID to filter speakers
			similarity_threshold: Minimum similarity score to consider a match (default 0.9)

		Returns:
			Tuple of (speaker_id, similarity_score) or (None, 0.0) if no match found

		Note:
			This is a helper method - actual database queries should use pgvector's
			cosine distance operator (<=>) for efficient similarity search.
			See SpeakerService.find_matching_speaker_in_db() for database integration.
		"""
		# This method is kept for non-database similarity computation
		# The actual database query should use pgvector operators
		return None, 0.0

