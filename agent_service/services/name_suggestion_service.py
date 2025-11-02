from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from agent_service.database.models import Meeting, NameSuggestion
from agent_service.services.name_extractor import NameExtractor

logger = logging.getLogger(__name__)


class NameSuggestionService:
	"""
	Service for managing name suggestions for unidentified speakers.

	Coordinates name extraction, suggestion generation, and user acceptance/correction.
	"""

	def __init__(self, db: Session) -> None:
		"""
		Initialize the name suggestion service.

		Args:
			db: Database session
		"""
		self.db = db
		self.name_extractor = NameExtractor()

	def get_suggestions_for_meeting(
		self,
		meeting_id: uuid.UUID,
		speaker_label: str | None = None,
	) -> list[NameSuggestion]:
		"""
		Get name suggestions for a meeting.

		Args:
			meeting_id: Meeting UUID
			speaker_label: Optional speaker label to filter by

		Returns:
			List of NameSuggestion objects, sorted by confidence (highest first)
		"""
		query = select(NameSuggestion).where(NameSuggestion.meeting_id == meeting_id)

		if speaker_label:
			query = query.where(NameSuggestion.unidentified_speaker_label == speaker_label)

		suggestions = self.db.scalars(
			query.order_by(NameSuggestion.confidence.desc())
		).all()

		return list(suggestions)

	def get_unidentified_speakers_with_suggestions(
		self,
		meeting_id: uuid.UUID,
	) -> dict[str, list[dict[str, Any]]]:
		"""
		Get all unidentified speakers with their name suggestions.

		Args:
			meeting_id: Meeting UUID

		Returns:
			Dictionary mapping speaker labels to suggestion data:
			{
				'SPK_1': [
					{'suggestion_id': uuid, 'name': 'דנה', 'confidence': 0.85, ...},
					...
				],
				...
			}
		"""
		suggestions = self.get_suggestions_for_meeting(meeting_id)

		speakers_dict: dict[str, list[dict[str, Any]]] = {}

		for suggestion in suggestions:
			speaker_label = suggestion.unidentified_speaker_label
			if speaker_label not in speakers_dict:
				speakers_dict[speaker_label] = []

			speakers_dict[speaker_label].append(
				{
					"suggestion_id": str(suggestion.id),
					"name": suggestion.suggested_name,
					"confidence": suggestion.confidence,
					"source_text": suggestion.source_text,
					"accepted": suggestion.accepted,
					"segment_start_time": suggestion.segment_start_time,
					"segment_end_time": suggestion.segment_end_time,
				}
			)

		return speakers_dict

	def accept_suggestion(
		self,
		suggestion_id: uuid.UUID,
		custom_name: str | None = None,
	) -> NameSuggestion:
		"""
		Accept a name suggestion (or provide custom name).

		Args:
			suggestion_id: NameSuggestion UUID
			custom_name: Optional custom name to use instead of suggested name

		Returns:
			Updated NameSuggestion object

		Raises:
			ValueError: If suggestion not found
		"""
		suggestion = self.db.get(NameSuggestion, suggestion_id)
		if not suggestion:
			raise ValueError(f"Name suggestion {suggestion_id} not found")

		suggestion.accepted = True
		if custom_name:
			suggestion.suggested_name = custom_name

		self.db.flush()
		logger.info(f"Accepted name suggestion {suggestion_id}: {suggestion.suggested_name}")
		return suggestion

	def create_custom_suggestion(
		self,
		meeting_id: uuid.UUID,
		speaker_label: str,
		name: str,
	) -> NameSuggestion:
		"""
		Create a custom name suggestion (user-provided).

		Args:
			meeting_id: Meeting UUID
			speaker_label: Speaker label (e.g., 'SPK_1')
			name: User-provided name

		Returns:
			Created NameSuggestion object with accepted=True
		"""
		suggestion = NameSuggestion(
			meeting_id=meeting_id,
			unidentified_speaker_label=speaker_label,
			suggested_name=name,
			confidence=1.0,  # User-provided = highest confidence
			source_text=None,
			accepted=True,
		)

		self.db.add(suggestion)
		self.db.flush()
		logger.info(f"Created custom name suggestion for {speaker_label}: {name}")
		return suggestion

