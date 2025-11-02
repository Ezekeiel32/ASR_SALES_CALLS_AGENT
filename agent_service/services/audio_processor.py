from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioProcessor:
	"""
	Service for audio manipulation and processing.

	Provides utilities for loading, resampling, normalizing, and extracting
	segments from audio files. Supports various formats (WAV, MP3, M4A, etc.)
	using librosa and soundfile.
	"""

	def __init__(self, default_sample_rate: int = 16000) -> None:
		"""
		Initialize the audio processor.

		Args:
			default_sample_rate: Default target sample rate (Hz). 16kHz is standard for speech.
		"""
		self.default_sample_rate = default_sample_rate

	def load_audio(
		self,
		audio_path: str | None = None,
		audio_bytes: bytes | None = None,
		sample_rate: int | None = None,
		mono: bool = True,
	) -> tuple[np.ndarray, int]:
		"""
		Load audio from file or bytes.

		Args:
			audio_path: Path to audio file
			audio_bytes: Raw audio bytes
			sample_rate: Target sample rate (uses default if None)
			mono: Convert to mono if True

		Returns:
			Tuple of (audio_data, sample_rate)
			- audio_data: numpy array of shape (n_samples,) for mono, (n_channels, n_samples) for stereo
			- sample_rate: Actual sample rate of loaded audio

		Raises:
			ValueError: If neither audio_path nor audio_bytes provided
			RuntimeError: If audio loading fails
		"""
		if audio_path is None and audio_bytes is None:
			raise ValueError("Either audio_path or audio_bytes must be provided")

		target_sr = sample_rate or self.default_sample_rate
		temp_file: Path | None = None

		try:
			if audio_bytes and not audio_path:
				# Write bytes to temp file for librosa
				with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
					tmp_file.write(audio_bytes)
					temp_file = Path(tmp_file.name)
					audio_path = str(temp_file)

			if not audio_path:
				raise ValueError("audio_path must be provided")

			# Load audio with librosa (handles resampling automatically)
			logger.debug(f"Loading audio from {audio_path} at {target_sr}Hz")
			audio_data, sr = librosa.load(audio_path, sr=target_sr, mono=mono)

			return audio_data, sr

		except Exception as e:
			logger.error(f"Error loading audio: {e}")
			raise RuntimeError(f"Failed to load audio: {e}") from e

		finally:
			if temp_file and temp_file.exists():
				try:
					temp_file.unlink()
				except Exception as e:
					logger.warning(f"Failed to delete temp file {temp_file}: {e}")

	def extract_segment(
		self,
		audio_path: str | None = None,
		audio_bytes: bytes | None = None,
		start_time: float = 0.0,
		end_time: float | None = None,
		duration: float | None = None,
		sample_rate: int | None = None,
	) -> tuple[np.ndarray, int]:
		"""
		Extract a time segment from audio.

		Args:
			audio_path: Path to audio file
			audio_bytes: Raw audio bytes
			start_time: Start time in seconds
			end_time: End time in seconds (optional if duration provided)
			duration: Duration in seconds (optional if end_time provided)
			sample_rate: Target sample rate

		Returns:
			Tuple of (audio_segment, sample_rate)

		Raises:
			ValueError: If time parameters are invalid
		"""
		if end_time is None and duration is None:
			raise ValueError("Either end_time or duration must be provided")

		if duration is not None:
			end_time = start_time + duration

		if end_time <= start_time:
			raise ValueError(f"Invalid time range: {start_time} to {end_time}")

		# Load full audio
		audio_data, sr = self.load_audio(audio_path, audio_bytes, sample_rate=sample_rate)

		# Convert times to sample indices
		start_sample = int(start_time * sr)
		end_sample = int(end_time * sr)

		# Ensure indices are within bounds
		start_sample = max(0, min(start_sample, len(audio_data)))
		end_sample = max(start_sample, min(end_sample, len(audio_data)))

		# Extract segment
		segment = audio_data[start_sample:end_sample]

		logger.debug(f"Extracted segment: {start_time:.2f}-{end_time:.2f}s ({len(segment)} samples)")
		return segment, sr

	def save_audio(
		self,
		audio_data: np.ndarray,
		output_path: str,
		sample_rate: int | None = None,
		format: str = "WAV",
	) -> None:
		"""
		Save audio data to file.

		Args:
			audio_data: Audio data array
			output_path: Output file path
			sample_rate: Sample rate (uses default if None)
			format: Audio format (WAV, FLAC, etc.)

		Raises:
			RuntimeError: If saving fails
		"""
		try:
			sr = sample_rate or self.default_sample_rate
			sf.write(output_path, audio_data, sr, format=format)
			logger.debug(f"Saved audio to {output_path}")
		except Exception as e:
			logger.error(f"Error saving audio: {e}")
			raise RuntimeError(f"Failed to save audio: {e}") from e

	def get_audio_info(self, audio_path: str, audio_bytes: bytes | None = None) -> dict[str, Any]:
		"""
		Get metadata about audio file.

		Args:
			audio_path: Path to audio file
			audio_bytes: Raw audio bytes

		Returns:
			Dictionary with keys:
			- 'duration_seconds': Audio duration
			- 'sample_rate': Sample rate
			- 'channels': Number of channels (1=mono, 2=stereo)
			- 'total_samples': Total number of samples
		"""
		audio_data, sr = self.load_audio(audio_path, audio_bytes)
		duration = len(audio_data) / sr

		return {
			"duration_seconds": duration,
			"sample_rate": sr,
			"channels": 1 if audio_data.ndim == 1 else audio_data.shape[0],
			"total_samples": len(audio_data),
		}

