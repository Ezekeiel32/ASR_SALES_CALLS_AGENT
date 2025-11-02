from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import torchaudio
from pyannote.audio import Pipeline

from agent_service.services.s3_model_storage import configure_huggingface_cache_for_s3

# Configure HuggingFace to use minimal local cache
configure_huggingface_cache_for_s3()

logger = logging.getLogger(__name__)


class DiarizationService:
	"""
	Service for speaker diarization using PyAnnote.audio.

	This service provides a second, independent diarization pass to validate
	and enhance the speaker labels from Ivrit.ai. PyAnnote uses state-of-the-art
	neural networks for speaker diarization and can provide higher accuracy in
	certain scenarios (e.g., overlapping speech, heavy accents).

	Note: This requires HuggingFace authentication token for accessing
	pyannote/speaker-diarization models.
	"""

	def __init__(
		self,
		model_name: str = "pyannote/speaker-diarization-3.1",
		use_auth_token: str | None = None,
		device: str | None = None,
	) -> None:
		"""
		Initialize the PyAnnote diarization service.

		Args:
			model_name: HuggingFace model identifier (default: pyannote/speaker-diarization-3.1)
			use_auth_token: HuggingFace authentication token (required for private models)
			device: PyTorch device ('cpu', 'cuda', etc.). Auto-detects if None.
		"""
		self.model_name = model_name
		self.use_auth_token = use_auth_token
		self.device = device or ("cuda" if self._is_cuda_available() else "cpu")
		self.pipeline: Pipeline | None = None
		logger.info(f"DiarizationService initialized with model: {model_name}, device: {self.device}")

	def _is_cuda_available(self) -> bool:
		"""Check if CUDA is available for PyTorch."""
		try:
			import torch
			return torch.cuda.is_available()
		except ImportError:
			return False

	def _load_pipeline(self) -> None:
		"""Lazy load the PyAnnote diarization pipeline."""
		if self.pipeline is None:
			try:
				logger.info(f"Loading PyAnnote pipeline: {self.model_name}")
				self.pipeline = Pipeline.from_pretrained(
					self.model_name,
					use_auth_token=self.use_auth_token,
				)
				if self.device == "cuda" and hasattr(self.pipeline, "to"):
					self.pipeline = self.pipeline.to(torch.device(self.device))
				logger.info("PyAnnote pipeline loaded successfully")
			except Exception as e:
				logger.error(f"Failed to load PyAnnote pipeline: {e}")
				raise RuntimeError(f"Could not load PyAnnote pipeline: {e}") from e

	def diarize(
		self,
		audio_path: str | None = None,
		audio_bytes: bytes | None = None,
		num_speakers: int | None = None,
		min_speakers: int | None = None,
		max_speakers: int | None = None,
	) -> list[dict[str, Any]]:
		"""
		Perform speaker diarization on audio.

		Args:
			audio_path: Path to audio file (WAV, MP3, etc.)
			audio_bytes: Raw audio bytes (will be saved to temp file if audio_path not provided)
			num_speakers: Exact number of speakers (if known)
			min_speakers: Minimum number of speakers
			max_speakers: Maximum number of speakers

		Returns:
			List of segment dictionaries with keys:
			- 'start': start time in seconds
			- 'end': end time in seconds
			- 'speaker': speaker label (e.g., 'SPEAKER_00', 'SPEAKER_01')
			- 'confidence': confidence score (if available)

		Raises:
			ValueError: If neither audio_path nor audio_bytes is provided
			RuntimeError: If pipeline loading or inference fails
		"""
		if audio_path is None and audio_bytes is None:
			raise ValueError("Either audio_path or audio_bytes must be provided")

		self._load_pipeline()

		# Handle audio bytes by writing to temp file
		temp_file: Path | None = None
		try:
			if audio_bytes and not audio_path:
				with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
					tmp_file.write(audio_bytes)
					temp_file = Path(tmp_file.name)
					audio_path = str(temp_file)

			if not audio_path:
				raise ValueError("audio_path must be provided")

			# Prepare diarization parameters
			diarization_params: dict[str, Any] = {}
			if num_speakers is not None:
				diarization_params["num_speakers"] = num_speakers
			if min_speakers is not None:
				diarization_params["min_speakers"] = min_speakers
			if max_speakers is not None:
				diarization_params["max_speakers"] = max_speakers

			# Run diarization
			logger.info(f"Running PyAnnote diarization on {audio_path}")
			diarization = self.pipeline(audio_path, **diarization_params)

			# Convert PyAnnote Annotation to list of segment dicts
			segments: list[dict[str, Any]] = []
			for segment, track, label in diarization.itertracks(yield_label=True):
				# PyAnnote uses labels like 'SPEAKER_00', 'SPEAKER_01', etc.
				# Convert to our format (SPK_0, SPK_1, etc.)
				speaker_label = label.replace("SPEAKER_", "SPK_")

				segments.append(
					{
						"start": segment.start,
						"end": segment.end,
						"speaker": speaker_label,
						"confidence": None,  # PyAnnote doesn't provide per-segment confidence
					}
				)

			logger.info(f"PyAnnote diarization completed: {len(segments)} segments, {len(set(s['speaker'] for s in segments))} speakers")
			return segments

		except Exception as e:
			logger.error(f"Error during PyAnnote diarization: {e}")
			raise RuntimeError(f"PyAnnote diarization failed: {e}") from e

		finally:
			# Clean up temp file
			if temp_file and temp_file.exists():
				try:
					temp_file.unlink()
				except Exception as e:
					logger.warning(f"Failed to delete temp file {temp_file}: {e}")

	def get_speaker_count(self, audio_path: str, audio_bytes: bytes | None = None) -> int:
		"""
		Estimate the number of speakers in the audio.

		Args:
			audio_path: Path to audio file
			audio_bytes: Optional raw audio bytes

		Returns:
			Estimated number of speakers
		"""
		segments = self.diarize(audio_path=audio_path, audio_bytes=audio_bytes)
		unique_speakers = set(seg["speaker"] for seg in segments)
		return len(unique_speakers)

