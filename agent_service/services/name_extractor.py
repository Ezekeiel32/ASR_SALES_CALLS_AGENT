from __future__ import annotations

import logging
import uuid
from typing import Any

from agent_service.database.models import NameSuggestion, TranscriptionSegment
from agent_service.services.hebrew_nlp import HebrewNLP

logger = logging.getLogger(__name__)


class NameExtractor:
	"""
	Service for extracting and suggesting names for unidentified speakers.

	Analyzes transcripts to find name mentions and associates them with
	speaker segments based on temporal proximity and context analysis.
	"""

	def __init__(self) -> None:
		"""Initialize the name extractor."""
		self.hebrew_nlp = HebrewNLP()

	def extract_names_for_speakers(
		self,
		transcript_segments: list[dict[str, Any]],
		unidentified_speakers: list[str],
	) -> dict[str, list[dict[str, Any]]]:
		"""
		Extract name suggestions for each unidentified speaker.

		Args:
			transcript_segments: List of transcript segments with speaker labels
			unidentified_speakers: List of speaker labels (e.g., ['SPK_1', 'SPK_2'])

		Returns:
			Dictionary mapping speaker labels to lists of name suggestions:
			{
				'SPK_1': [
					{'name': 'דנה', 'confidence': 0.85, 'context': '...', ...},
					...
				],
				...
			}
		"""
		speaker_suggestions: dict[str, list[dict[str, Any]]] = {
			speaker: [] for speaker in unidentified_speakers
		}

		# For each unidentified speaker, find segments and extract names nearby
		for speaker_label in unidentified_speakers:
			speaker_segments = [
				seg
				for seg in transcript_segments
				if (seg.get("speaker") or seg.get("speaker_label")) == speaker_label
			]

			if not speaker_segments:
				logger.warning(f"No segments found for speaker {speaker_label}")
				continue

			# Get the first significant segment (likely introduction)
			first_segment = speaker_segments[0] if speaker_segments else None
			if not first_segment:
				continue

			# Extract names from the segment's text
			segment_text = first_segment.get("text", "")
			if segment_text:
				names = self.hebrew_nlp.extract_names_from_text(segment_text)
				speaker_suggestions[speaker_label].extend(names)

			# Also check segments near the speaker's first appearance
			first_start = float(first_segment.get("start", 0))
			nearby_names = self.hebrew_nlp.extract_names_near_timestamp(
				transcript_segments,
				first_start,
				time_window=15.0,  # 15 seconds window
			)

			# Filter to names that appeared in or near this speaker's segments
			for name_info in nearby_names:
				name_seg_start = name_info.get("segment_start", 0)
				name_seg_end = name_info.get("segment_end", 0)

				# Check if name appeared during or just before speaker's segments
				for speaker_seg in speaker_segments[:3]:  # Check first 3 segments
					speaker_seg_start = float(speaker_seg.get("start", 0))
					speaker_seg_end = float(speaker_seg.get("end", speaker_seg_start))

					# Name should be within 5 seconds of speaker segment
					if (
						abs(name_seg_start - speaker_seg_start) <= 5.0
						or abs(name_seg_end - speaker_seg_start) <= 5.0
					):
						speaker_suggestions[speaker_label].append(name_info)
						break

			# Deduplicate and sort by confidence
			seen: set[str] = set()
			unique_suggestions: list[dict[str, Any]] = []
			for suggestion in sorted(
				speaker_suggestions[speaker_label],
				key=lambda x: x.get("confidence", 0.0),
				reverse=True,
			):
				name_key = suggestion.get("name", "").lower()
				if name_key and name_key not in seen:
					seen.add(name_key)
					unique_suggestions.append(suggestion)

			speaker_suggestions[speaker_label] = unique_suggestions[:3]  # Top 3 suggestions

		logger.info(
			f"Extracted name suggestions for {len(unidentified_speakers)} speakers: "
			f"{sum(len(v) for v in speaker_suggestions.values())} total suggestions"
		)
		return speaker_suggestions

	def create_name_suggestions_for_meeting(
		self,
		db_session: Any,
		meeting_id: uuid.UUID,
		transcript_segments: list[dict[str, Any]],
		unidentified_speakers: list[str],
	) -> list[NameSuggestion]:
		"""
		Create NameSuggestion database records for a meeting.

		Args:
			db_session: Database session
			meeting_id: Meeting UUID
			transcript_segments: Transcript segments with speaker labels
			unidentified_speakers: List of unidentified speaker labels

		Returns:
			List of created NameSuggestion objects
		"""
		suggestions = self.extract_names_for_speakers(transcript_segments, unidentified_speakers)

		created_suggestions: list[NameSuggestion] = []

		for speaker_label, name_list in suggestions.items():
			for name_info in name_list:
				name = name_info.get("name", "").strip()
				if not name:
					continue

				confidence = name_info.get("confidence", 0.5)
				context = name_info.get("context", "")
				segment_start = name_info.get("segment_start")
				segment_end = name_info.get("segment_end")

				# Create NameSuggestion record
				name_suggestion = NameSuggestion(
					meeting_id=meeting_id,
					unidentified_speaker_label=speaker_label,
					suggested_name=name,
					confidence=confidence,
					source_text=context,
					segment_start_time=segment_start,
					segment_end_time=segment_end,
					accepted=False,
				)

				db_session.add(name_suggestion)
				created_suggestions.append(name_suggestion)

		db_session.flush()
		logger.info(f"Created {len(created_suggestions)} name suggestions for meeting {meeting_id}")
		return created_suggestions

