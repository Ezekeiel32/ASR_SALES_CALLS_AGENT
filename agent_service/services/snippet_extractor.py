from __future__ import annotations

import logging
import uuid
from typing import Any

import boto3
from botocore.exceptions import ClientError

from agent_service.config import get_settings
from agent_service.services.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)
settings = get_settings()


class SnippetExtractor:
	"""
	Service for extracting 15-second audio snippets for each detected speaker.

	Extracts representative audio samples for speaker identification and
	name assignment. Snippets are stored in S3 with signed URLs for secure access.
	"""

	def __init__(self, s3_bucket: str | None = None, s3_region: str = "us-east-1") -> None:
		"""
		Initialize the snippet extractor.

		Args:
			s3_bucket: S3 bucket name (from config if None)
			s3_region: AWS region for S3
		"""
		self.s3_bucket = s3_bucket or getattr(settings, "s3_bucket", None)
		self.s3_region = s3_region
		self.audio_processor = AudioProcessor()
		self.s3_client: boto3.client | None = None

		if self.s3_bucket:
			try:
				from agent_service.config import get_settings as get_global_settings
				global_settings = get_global_settings()
				self.s3_client = boto3.client(
					"s3",
					region_name=self.s3_region,
					aws_access_key_id=global_settings.aws_access_key_id,
					aws_secret_access_key=global_settings.aws_secret_access_key,
				)
				logger.info(f"SnippetExtractor initialized with S3 bucket: {self.s3_bucket}")
			except Exception as e:
				logger.warning(f"Failed to initialize S3 client: {e}. Snippets will be stored locally only.")

	def extract_speaker_snippets(
		self,
		speaker_segments: list[dict[str, Any]],
		meeting_id: uuid.UUID,
		audio_path: str | None = None,
		audio_bytes: bytes | None = None,
		snippet_duration: float = 15.0,
	) -> list[dict[str, Any]]:
		"""
		Extract 15-second snippets for each unique speaker.

		Args:
			audio_path: Path to full audio file
			audio_bytes: Raw audio bytes
			speaker_segments: List of segments with speaker labels (from diarization)
			meeting_id: Meeting UUID for organizing snippets
			snippet_duration: Duration of each snippet in seconds (default 15.0)

		Returns:
			List of snippet dictionaries with keys:
			- 'speaker_label': Speaker identifier (e.g., 'SPK_1')
			- 'start_time': Start time in original audio (seconds)
			- 'end_time': End time in original audio (seconds)
			- 'snippet_url': Signed S3 URL or local file path
			- 's3_key': S3 object key (if stored in S3)
			- 'file_path': Local file path (if stored locally)
		"""
		if not speaker_segments:
			logger.warning("No speaker segments provided")
			return []

		# Group segments by speaker
		speaker_groups: dict[str, list[dict[str, Any]]] = {}
		for seg in speaker_segments:
			speaker_label = seg.get("speaker") or seg.get("speaker_label") or "SPK_0"
			if speaker_label not in speaker_groups:
				speaker_groups[speaker_label] = []
			speaker_groups[speaker_label].append(seg)

		logger.info(f"Extracting snippets for {len(speaker_groups)} speakers")

		snippets: list[dict[str, Any]] = []

		for speaker_label, segments in speaker_groups.items():
			# Find the longest segment for this speaker (most representative)
			longest_segment = max(segments, key=lambda s: float(s.get("end", 0)) - float(s.get("start", 0)))

			segment_start = float(longest_segment.get("start", 0))
			segment_end = float(longest_segment.get("end", segment_start))
			segment_duration = segment_end - segment_start

			# If segment is shorter than snippet_duration, use the whole segment
			# Otherwise, extract from the middle of the segment
			if segment_duration <= snippet_duration:
				snippet_start = segment_start
				snippet_end = segment_end
			else:
				# Extract from middle of segment
				center = (segment_start + segment_end) / 2
				snippet_start = max(segment_start, center - snippet_duration / 2)
				snippet_end = min(segment_end, snippet_start + snippet_duration)

			try:
				# Extract audio snippet
				audio_segment, sr = self.audio_processor.extract_segment(
					audio_path=audio_path,
					audio_bytes=audio_bytes,
					start_time=snippet_start,
					end_time=snippet_end,
					sample_rate=16000,  # Standard for speech
				)

				# Save snippet
				snippet_info = self._save_snippet(
					audio_segment=audio_segment,
					sample_rate=sr,
					meeting_id=meeting_id,
					speaker_label=speaker_label,
				)

				snippets.append(
					{
						"speaker_label": speaker_label,
						"start_time": snippet_start,
						"end_time": snippet_end,
						**snippet_info,
					}
				)

				logger.info(
					f"Extracted snippet for {speaker_label}: {snippet_start:.2f}-{snippet_end:.2f}s"
				)

			except Exception as e:
				logger.error(f"Failed to extract snippet for {speaker_label}: {e}")
				continue

		return snippets

	def _save_snippet(
		self,
		audio_segment: Any,
		sample_rate: int,
		meeting_id: uuid.UUID,
		speaker_label: str,
	) -> dict[str, Any]:
		"""
		Save snippet to S3 or local filesystem.

		Args:
			audio_segment: Audio data array
			sample_rate: Sample rate
			meeting_id: Meeting UUID
			speaker_label: Speaker identifier

		Returns:
			Dictionary with snippet metadata (snippet_url, s3_key, file_path)
		"""
		import tempfile
		from pathlib import Path

		# Generate filename
		filename = f"{meeting_id}_{speaker_label}_snippet.wav"
		s3_key = f"meetings/{meeting_id}/snippets/{filename}"

		if self.s3_client and self.s3_bucket:
			# Save to S3
			try:
				# Write to temp file first
				with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
					tmp_path = Path(tmp_file.name)
					self.audio_processor.save_audio(audio_segment, str(tmp_path), sample_rate)

					# Upload to S3
					self.s3_client.upload_file(
						str(tmp_path),
						self.s3_bucket,
						s3_key,
						ExtraArgs={"ContentType": "audio/wav"},
					)

					# Generate signed URL (valid for 7 days)
					snippet_url = self.s3_client.generate_presigned_url(
						"get_object",
						Params={"Bucket": self.s3_bucket, "Key": s3_key},
						ExpiresIn=604800,  # 7 days
					)

					# Clean up temp file
					tmp_path.unlink()

					logger.debug(f"Saved snippet to S3: {s3_key}")
					return {"snippet_url": snippet_url, "s3_key": s3_key, "file_path": None}

			except ClientError as e:
				logger.error(f"S3 upload failed: {e}, falling back to local storage")
				# Fall through to local storage

		# Fallback to local storage
		local_path = Path(f"agent_service/snippets/{meeting_id}/{filename}")
		local_path.parent.mkdir(parents=True, exist_ok=True)

		self.audio_processor.save_audio(audio_segment, str(local_path), sample_rate)

		logger.debug(f"Saved snippet locally: {local_path}")
		return {
			"snippet_url": str(local_path),
			"s3_key": None,
			"file_path": str(local_path),
		}

