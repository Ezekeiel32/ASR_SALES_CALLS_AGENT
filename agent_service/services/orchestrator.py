from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session

from agent_service.clients import IvritClient
from agent_service.config import get_settings
from agent_service.database.models import Meeting, MeetingSummary, TranscriptionSegment
from agent_service.services.audio_processor import AudioProcessor
from agent_service.services.diarization_merger import DiarizationMerger
# Import DiarizationService conditionally to avoid startup errors
try:
	from agent_service.services.diarization_service import DiarizationService
except (AttributeError, ImportError, Exception) as e:
	logger.warning(f"DiarizationService not available: {e}. PyAnnote diarization will be disabled.")
	DiarizationService = None  # type: ignore[assignment,misc]
from agent_service.services.name_extractor import NameExtractor
from agent_service.services.name_suggestion_service import NameSuggestionService
from agent_service.services.snippet_extractor import SnippetExtractor
from agent_service.services.speaker_service import SpeakerService
from agent_service.services.voiceprint_service import VoiceprintService
from agent_service.summarizers.nvidia import NvidiaDeepSeekSummarizer

logger = logging.getLogger(__name__)
settings = get_settings()


class ProcessingOrchestrator:
	"""
	Orchestrates the complete post-meeting processing pipeline.

	Coordinates:
	1. Audio transcription (Ivrit.ai)
	2. Speaker diarization (Ivrit.ai + PyAnnote)
	3. Audio snippet extraction (15-second samples)
	4. Voiceprint generation and matching
	5. Hebrew name extraction and suggestions
	6. Speaker-aware summarization (DeepSeek)
	7. Database storage and status updates
	"""

	def __init__(
		self,
		db: Session,
		s3_bucket: str | None = None,
		s3_region: str = "us-east-1",
	) -> None:
		"""
		Initialize the processing orchestrator.

		Args:
			db: Database session
			s3_bucket: S3 bucket name for audio storage
			s3_region: AWS region
		"""
		self.db = db
		self.s3_bucket = s3_bucket or getattr(settings, "s3_bucket", None)
		self.s3_region = s3_region

		# Initialize services
		self.ivrit_client = IvritClient(settings)
		# Initialize PyAnnote diarization service if available
		if DiarizationService is not None:
			try:
				self.diarization_service = DiarizationService(
					model_name=getattr(settings, "pyannote_model", "pyannote/speaker-diarization-3.1"),
					use_auth_token=getattr(settings, "pyannote_auth_token", None),
				)
			except Exception as e:
				logger.warning(f"Failed to initialize DiarizationService: {e}. PyAnnote diarization will be disabled.")
				self.diarization_service = None
		else:
			self.diarization_service = None
		self.diarization_merger = DiarizationMerger()
		self.audio_processor = AudioProcessor()
		self.snippet_extractor = SnippetExtractor(s3_bucket=self.s3_bucket, s3_region=self.s3_region)
		self.voiceprint_service = VoiceprintService()
		self.speaker_service = SpeakerService(db, self.voiceprint_service)
		self.name_extractor = NameExtractor()
		self.name_suggestion_service = NameSuggestionService(db)
		self.summarizer = NvidiaDeepSeekSummarizer(settings)

	async def process_meeting(
		self,
		meeting_id: uuid.UUID,
		organization_id: uuid.UUID,
		audio_s3_key: str | None = None,
		audio_bytes: bytes | None = None,
		audio_path: str | None = None,
	) -> dict[str, Any]:
		"""
		Process a complete meeting: transcription, diarization, speaker recognition, summarization.

		Args:
			meeting_id: Meeting UUID
			organization_id: Organization UUID
			audio_s3_key: S3 key for audio file (if already uploaded)
			audio_bytes: Raw audio bytes (alternative to S3)
			audio_path: Local file path (alternative to S3/bytes)

		Returns:
			Dictionary with processing results and status

		Raises:
			ValueError: If no audio source provided
			RuntimeError: If processing fails
		"""
		meeting = self.db.get(Meeting, meeting_id)
		if not meeting:
			raise ValueError(f"Meeting {meeting_id} not found")

		# Update status to processing
		meeting.status = "processing"
		self.db.commit()

		try:
			logger.info(f"Starting processing for meeting {meeting_id}")

			# Step 1: Get audio data
			audio_data = self._get_audio_data(audio_s3_key, audio_bytes, audio_path)
			if not audio_data:
				raise ValueError("No audio data provided")

			# Step 2: Transcription via Ivrit.ai (includes basic diarization)
			logger.info("Step 1/7: Transcription via Ivrit.ai")
			transcription_result = await self.ivrit_client.transcribe_bytes(
				data=audio_data["bytes"],
				filename=audio_data.get("filename", "audio.wav"),
			)

			ivrit_segments = transcription_result.segments or []

			# Step 3: PyAnnote diarization (validation and improvement)
			logger.info("Step 2/7: PyAnnote diarization validation")
			pyannote_segments = None
			if self.diarization_service is None:
				logger.warning("PyAnnote diarization service not available, skipping PyAnnote diarization")
			else:
				try:
					# PyAnnote can handle the audio file directly or via bytes
					# It will auto-detect format and convert as needed
					audio_path_for_pyannote = audio_path
					if not audio_path_for_pyannote:
						# Use bytes - PyAnnote will create temp file internally
						logger.info("Running PyAnnote diarization on audio bytes")
						pyannote_segments = self.diarization_service.diarize(
							audio_path=None,
							audio_bytes=audio_data["bytes"],
						)
					else:
						logger.info(f"Running PyAnnote diarization on audio file: {audio_path_for_pyannote}")
						pyannote_segments = self.diarization_service.diarize(
							audio_path=audio_path_for_pyannote,
							audio_bytes=None,
						)
					
					if pyannote_segments:
						unique_speakers = set(s.get("speaker") for s in pyannote_segments if s.get("speaker"))
						logger.info(f"PyAnnote detected {len(unique_speakers)} speakers: {sorted(unique_speakers)}")
					else:
						logger.warning("PyAnnote returned no segments")
				except Exception as e:
					logger.warning(f"PyAnnote diarization failed, continuing with Ivrit only: {e}", exc_info=True)

			# Step 4: Merge diarization results
			logger.info("Step 3/7: Merging diarization results")
			merged_segments = self.diarization_merger.merge(ivrit_segments, pyannote_segments)
			
			# Extract unique speakers from merged segments
			merged_speaker_labels: set[str] = set()
			for seg in merged_segments:
				speaker = seg.get("speaker") or seg.get("speaker_label") or "SPK_0"
				merged_speaker_labels.add(speaker)
			
			logger.info(f"Detected {len(merged_speaker_labels)} unique speakers in merged segments: {sorted(merged_speaker_labels)}")
			
			# Build speaker_segments from merged segments for better accuracy
			merged_speaker_segments_map: dict[str, list[dict[str, Any]]] = {}
			for seg in merged_segments:
				speaker = seg.get("speaker") or seg.get("speaker_label") or "SPK_0"
				if speaker not in merged_speaker_segments_map:
					merged_speaker_segments_map[speaker] = []
				merged_speaker_segments_map[speaker].append(seg)
			
			merged_speaker_segments: list[dict[str, Any]] = [
				{"speaker": label, "segments": segs}
				for label, segs in sorted(merged_speaker_segments_map.items())
			]
			
			# Use merged speaker segments if available, otherwise fall back to Ivrit
			final_speaker_segments = merged_speaker_segments if merged_speaker_segments else (transcription_result.speaker_segments or [])
			final_speaker_labels = sorted(list(merged_speaker_labels)) if merged_speaker_labels else (transcription_result.speaker_labels or [])

			# Step 5: Extract speaker snippets and generate voiceprints
			logger.info("Step 4/7: Extracting speaker snippets and generating voiceprints")
			unidentified_speakers = final_speaker_labels
			speaker_snippets = self.snippet_extractor.extract_speaker_snippets(
				speaker_segments=final_speaker_segments,
				meeting_id=meeting_id,
				audio_path=audio_path,
				audio_bytes=audio_data["bytes"],
			)

			# Generate voiceprints and match to known speakers
			speaker_voiceprints: dict[str, list[float] | None] = {}
			for snippet_info in speaker_snippets:
				speaker_label = snippet_info["speaker_label"]
				snippet_url = snippet_info.get("snippet_url")
				snippet_path = snippet_info.get("file_path")

				try:
					# Generate voiceprint from snippet
					if snippet_path:
						embedding = self.voiceprint_service.generate_embedding(audio_path=snippet_path)
					elif snippet_url and snippet_url.startswith("http"):
						# Download from S3/URL if needed
						import tempfile
						import httpx
						import os
						async with httpx.AsyncClient(timeout=30.0) as client:
							resp = await client.get(snippet_url)
							resp.raise_for_status()
							content = resp.content
						tmp_path = None
						try:
							with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
								tmp.write(content)
								tmp.flush()
								tmp_path = tmp.name
							embedding = self.voiceprint_service.generate_embedding(audio_path=tmp_path)
						finally:
							# Clean up temp file
							if tmp_path and os.path.exists(tmp_path):
								try:
									os.unlink(tmp_path)
								except Exception:
									pass
					else:
						embedding = None

					speaker_voiceprints[speaker_label] = embedding

					# Try to match to existing speaker
					if embedding:
						matched_speaker, similarity = self.speaker_service.find_matching_speaker_in_db(
							embedding, organization_id, similarity_threshold=0.9
						)
						if matched_speaker:
							logger.info(
								f"Matched {speaker_label} to existing speaker '{matched_speaker.name}' "
								f"(similarity: {similarity:.3f})"
							)

				except Exception as e:
					logger.error(f"Failed to generate voiceprint for {speaker_label}: {e}")
					speaker_voiceprints[speaker_label] = None

			# Step 6: Extract names from transcript and create suggestions
			logger.info("Step 5/7: Extracting Hebrew names and creating suggestions")
			name_suggestions = self.name_extractor.create_name_suggestions_for_meeting(
				db_session=self.db,
				meeting_id=meeting_id,
				transcript_segments=merged_segments,
				unidentified_speakers=unidentified_speakers,
			)

			# Step 7: Store transcription segments in database
			logger.info("Step 6/7: Storing transcription segments")
			self._store_transcription_segments(meeting_id, merged_segments, organization_id)

			# Step 8: Generate speaker-aware summary using merged speaker segments
			logger.info("Step 7/7: Generating speaker-aware summary")
			summary_result = await self.summarizer.summarize(
				transcription_result.text,
				speaker_segments=final_speaker_segments,
			)

			# Store summary
			summary_data = {
				"summary": summary_result.text,
				"keyPoints": self._extract_keypoints(summary_result.text),
				"actionItems": [],
				"speakerAware": True,
			}

			meeting_summary = MeetingSummary(
				meeting_id=meeting_id,
				summary_json=summary_data,
			)
			self.db.add(meeting_summary)

			# Update meeting status
			meeting.status = "completed"
			self.db.commit()

			logger.info(f"Processing completed for meeting {meeting_id}")

			return {
				"meeting_id": str(meeting_id),
				"status": "completed",
				"transcription_segments": len(merged_segments),
				"speakers_detected": len(unidentified_speakers),
				"name_suggestions": len(name_suggestions),
				"summary_available": True,
			}

		except Exception as e:
			import traceback
			error_details = traceback.format_exc()
			logger.error(f"Processing failed for meeting {meeting_id}: {e}\n{error_details}", exc_info=True)
			meeting.status = "failed"
			# Store error message for debugging (if we add an error_message field later)
			self.db.commit()
			raise RuntimeError(f"Meeting processing failed: {e}") from e

	def _get_audio_data(
		self,
		s3_key: str | None,
		audio_bytes: bytes | None,
		audio_path: str | None,
	) -> dict[str, Any] | None:
		"""Get audio data from S3, bytes, or file path."""
		if audio_bytes:
			return {"bytes": audio_bytes, "filename": "audio.wav"}

		if audio_path:
			with open(audio_path, "rb") as f:
				return {"bytes": f.read(), "filename": audio_path.split("/")[-1]}

		# Check if s3_key is actually a local file path (starts with ./ or /)
		if s3_key and (s3_key.startswith("./") or s3_key.startswith("/")):
			try:
				# Convert relative path to absolute if needed
				file_path = s3_key
				if s3_key.startswith("./"):
					# Try relative to current working directory first
					if os.path.exists(s3_key):
						file_path = os.path.abspath(s3_key)
					else:
						# Try relative to orchestrator file location (project root)
						orchestrator_dir = os.path.dirname(os.path.abspath(__file__))
						project_root = os.path.dirname(os.path.dirname(orchestrator_dir))
						file_path = os.path.join(project_root, s3_key[2:])  # Remove ./ prefix
				
				if os.path.exists(file_path):
					logger.info(f"Reading audio file from: {file_path}")
					with open(file_path, "rb") as f:
						return {
							"bytes": f.read(),
							"filename": os.path.basename(file_path),
						}
				else:
					logger.error(f"Local file does not exist: {file_path} (original: {s3_key}, cwd: {os.getcwd()})")
					return None
			except Exception as e:
				logger.error(f"Failed to read local file {s3_key}: {e}", exc_info=True)
				return None

		# Try S3 if bucket is configured and s3_key looks like an S3 key
		if s3_key and self.s3_bucket and not s3_key.startswith("./") and not os.path.exists(s3_key):
			try:
				from agent_service.config import get_settings as get_global_settings
				global_settings = get_global_settings()
				s3_client = boto3.client(
					"s3",
					region_name=self.s3_region,
					aws_access_key_id=global_settings.aws_access_key_id,
					aws_secret_access_key=global_settings.aws_secret_access_key,
				)
				response = s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
				return {
					"bytes": response["Body"].read(),
					"filename": s3_key.split("/")[-1],
				}
			except ClientError as e:
				logger.error(f"Failed to download from S3: {e}")
				return None

		return None

	def _store_transcription_segments(
		self,
		meeting_id: uuid.UUID,
		segments: list[dict[str, Any]],
		organization_id: uuid.UUID,
	) -> None:
		"""Store transcription segments in database."""
		for seg in segments:
			# Try to find matching speaker if voiceprint matched
			speaker_id = None
			unidentified_label = seg.get("speaker") or seg.get("speaker_label") or "SPK_0"

			# TODO: Match to speaker_id if voiceprint was matched
			# This would require storing the mapping during processing

			transcription_seg = TranscriptionSegment(
				meeting_id=meeting_id,
				speaker_id=speaker_id,
				unidentified_speaker_label=unidentified_label,
				start_time_seconds=float(seg.get("start", 0)),
				end_time_seconds=float(seg.get("end", 0)),
				hebrew_text=seg.get("text", ""),
				confidence=seg.get("confidence"),
			)
			self.db.add(transcription_seg)

		self.db.flush()

	def _extract_keypoints(self, markdown_text: str) -> list[str]:
		"""Extract key points from markdown summary."""
		import re

		points: list[str] = []
		for line in markdown_text.splitlines():
			if re.match(r"^\s*([-*•—])\s+", line):
				points.append(re.sub(r"^\s*([-*•—])\s+", "", line).strip())
		return points[:10]

