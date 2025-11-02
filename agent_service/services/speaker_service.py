from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from agent_service.database.models import Organization, Speaker
from agent_service.services.voiceprint_service import VoiceprintService

logger = logging.getLogger(__name__)


class SpeakerService:
	"""
	Service for managing speakers and speaker identification within organizations.

	Handles:
	- Creating and storing speaker profiles with voiceprints
	- Matching unidentified speakers to known speakers via voiceprint similarity
	- Speaker name assignment and persistence
	"""

	def __init__(self, db: Session, voiceprint_service: VoiceprintService | None = None) -> None:
		"""
		Initialize the speaker service.

		Args:
			db: Database session
			voiceprint_service: Optional VoiceprintService instance (creates new one if None)
		"""
		self.db = db
		self.voiceprint_service = voiceprint_service or VoiceprintService()

	def create_speaker(
		self,
		organization_id: uuid.UUID,
		name: str,
		voiceprint_embedding: list[float] | None = None,
		confidence_score: float | None = None,
	) -> Speaker:
		"""
		Create a new speaker profile for an organization.

		Args:
			organization_id: Organization UUID
			name: Speaker name
			voiceprint_embedding: Optional 256-dimensional voiceprint embedding
			confidence_score: Optional confidence score for the voiceprint

		Returns:
			Created Speaker object

		Raises:
			ValueError: If speaker with same name already exists in organization
		"""
		# Check if organization exists
		org = self.db.scalar(select(Organization).where(Organization.id == organization_id))
		if not org:
			raise ValueError(f"Organization {organization_id} not found")

		# Check for duplicate name within organization
		existing = self.db.scalar(
			select(Speaker).where(
				Speaker.organization_id == organization_id,
				Speaker.name == name,
			)
		)
		if existing:
			raise ValueError(f"Speaker '{name}' already exists in organization {organization_id}")

		speaker = Speaker(
			organization_id=organization_id,
			name=name,
			voiceprint_embedding=voiceprint_embedding,
			confidence_score=confidence_score,
		)

		self.db.add(speaker)
		self.db.flush()  # Flush to get the ID

		logger.info(f"Created speaker {speaker.id} ({name}) for organization {organization_id}")
		return speaker

	def find_matching_speaker_in_db(
		self,
		embedding: list[float],
		organization_id: uuid.UUID,
		similarity_threshold: float = 0.9,
	) -> tuple[Speaker | None, float]:
		"""
		Find a matching speaker in the database using pgvector cosine similarity.

		Args:
			embedding: Query embedding vector (256-dimensional)
			organization_id: Organization ID to filter speakers
			similarity_threshold: Minimum similarity score (0.0-1.0) to consider a match

		Returns:
			Tuple of (Speaker object, similarity_score) or (None, 0.0) if no match found

		Note:
			Uses pgvector's cosine distance operator (<=>) for efficient similarity search.
			Similarity = 1 - cosine_distance, so threshold of 0.9 means max cosine_distance of 0.1.
		"""
		if not embedding or len(embedding) != 256:
			logger.warning(f"Invalid embedding dimension: {len(embedding) if embedding else 0}, expected 256")
			return None, 0.0

		try:
			# Convert embedding list to PostgreSQL vector format
			embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"

			# Query using pgvector cosine distance operator (<=>)
			# cosine_distance = 1 - cosine_similarity
			# We want similarity >= threshold, so distance <= (1 - threshold)
			max_distance = 1.0 - similarity_threshold

			query = text("""
				SELECT id, name, confidence_score,
					   1 - (voiceprint_embedding <=> :embedding::vector) as similarity
				FROM speakers
				WHERE organization_id = :org_id
				  AND voiceprint_embedding IS NOT NULL
				  AND 1 - (voiceprint_embedding <=> :embedding::vector) >= :threshold
				ORDER BY voiceprint_embedding <=> :embedding::vector
				LIMIT 1
			""")

			result = self.db.execute(
				query,
				{
					"embedding": embedding_str,
					"org_id": str(organization_id),
					"threshold": similarity_threshold,
				},
			).first()

			if result:
				speaker_id = result[0]
				similarity = float(result[3])

				speaker = self.db.get(Speaker, speaker_id)
				logger.info(
					f"Found matching speaker {speaker_id} with similarity {similarity:.3f} "
					f"for organization {organization_id}"
				)
				return speaker, similarity

			return None, 0.0

		except Exception as e:
			logger.error(f"Error finding matching speaker: {e}")
			# Fallback to non-vector search or return no match
			return None, 0.0

	def assign_name_to_speaker(
		self,
		meeting_id: uuid.UUID,
		unidentified_speaker_label: str,
		speaker_name: str,
		organization_id: uuid.UUID,
		voiceprint_embedding: list[float] | None = None,
		confidence_score: float | None = None,
	) -> tuple[Speaker, bool]:
		"""
		Assign a name to an unidentified speaker, creating or updating a speaker profile.

		Args:
			meeting_id: Meeting UUID
			unidentified_speaker_label: Label like 'SPK_1', 'SPK_2', etc.
			speaker_name: Name to assign (e.g., "Dana", "Yossi")
			organization_id: Organization UUID
			voiceprint_embedding: Optional voiceprint embedding for the speaker
			confidence_score: Optional confidence score

		Returns:
			Tuple of (Speaker object, is_new_speaker: bool)
			- is_new_speaker: True if a new speaker was created, False if existing was used
		"""
		# First, check if we should match to an existing speaker via voiceprint
		existing_speaker = None
		if voiceprint_embedding:
			matched_speaker, similarity = self.find_matching_speaker_in_db(
				voiceprint_embedding, organization_id, similarity_threshold=0.9
			)
			if matched_speaker:
				logger.info(
					f"Matched unidentified speaker '{unidentified_speaker_label}' "
					f"to existing speaker '{matched_speaker.name}' (similarity: {similarity:.3f})"
				)
				existing_speaker = matched_speaker

		if existing_speaker:
			# Use existing speaker, but update voiceprint if provided and different
			if voiceprint_embedding and existing_speaker.voiceprint_embedding != voiceprint_embedding:
				# Optionally update voiceprint (could average with existing, or replace)
				# For now, we'll keep the existing one unless it's None
				if existing_speaker.voiceprint_embedding is None:
					existing_speaker.voiceprint_embedding = voiceprint_embedding
					existing_speaker.confidence_score = confidence_score
					self.db.flush()

			return existing_speaker, False

		# Create new speaker
		try:
			speaker = self.create_speaker(
				organization_id=organization_id,
				name=speaker_name,
				voiceprint_embedding=voiceprint_embedding,
				confidence_score=confidence_score,
			)
			self.db.commit()
			logger.info(
				f"Created new speaker '{speaker_name}' for unidentified speaker '{unidentified_speaker_label}' "
				f"in meeting {meeting_id}"
			)
			return speaker, True

		except ValueError as e:
			# Speaker name already exists - get existing speaker
			logger.warning(f"Speaker '{speaker_name}' already exists, using existing: {e}")
			existing = self.db.scalar(
				select(Speaker).where(
					Speaker.organization_id == organization_id,
					Speaker.name == speaker_name,
				)
			)
			if existing:
				# Update voiceprint if provided
				if voiceprint_embedding and existing.voiceprint_embedding is None:
					existing.voiceprint_embedding = voiceprint_embedding
					existing.confidence_score = confidence_score
					self.db.flush()
				return existing, False
			raise

	def get_organization_speakers(self, organization_id: uuid.UUID) -> list[Speaker]:
		"""
		Get all known speakers for an organization.

		Args:
			organization_id: Organization UUID

		Returns:
			List of Speaker objects
		"""
		speakers = self.db.scalars(
			select(Speaker)
			.where(Speaker.organization_id == organization_id)
			.order_by(Speaker.name)
		).all()
		return list(speakers)

