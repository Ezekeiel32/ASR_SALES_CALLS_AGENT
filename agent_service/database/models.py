from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
	BIGINT,
	Float,
	ForeignKey,
	Index,
	String,
	Text,
	TIMESTAMP,
	UUID,
	JSON,
	VARCHAR,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	"""Base class for all database models."""

	pass


class Organization(Base):
	"""Organization/tenant for multi-tenancy."""

	__tablename__ = "organizations"

	id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
	name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
	subscription_plan: Mapped[str] = mapped_column(
		VARCHAR(50), default="free", nullable=False
	)
	created_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
	)

	# Relationships
	users: Mapped[list["User"]] = relationship("User", back_populates="organization")
	speakers: Mapped[list["Speaker"]] = relationship(
		"Speaker", back_populates="organization"
	)
	meetings: Mapped[list["Meeting"]] = relationship(
		"Meeting", back_populates="organization"
	)

	def __repr__(self) -> str:
		return f"<Organization(id={self.id}, name={self.name})>"


class User(Base):
	"""User account within an organization."""

	__tablename__ = "users"

	id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
	organization_id: Mapped[uuid.UUID] = mapped_column(
		UUID, ForeignKey("organizations.id"), nullable=False
	)
	email: Mapped[str] = mapped_column(VARCHAR(255), unique=True, nullable=False)
	name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
	sso_provider: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
	)

	# Relationships
	organization: Mapped["Organization"] = relationship(
		"Organization", back_populates="users"
	)

	__table_args__ = (Index("idx_users_organization_id", "organization_id"),)

	def __repr__(self) -> str:
		return f"<User(id={self.id}, email={self.email})>"


class Speaker(Base):
	"""Known speaker with voiceprint for an organization."""

	__tablename__ = "speakers"

	id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
	organization_id: Mapped[uuid.UUID] = mapped_column(
		UUID, ForeignKey("organizations.id"), nullable=False
	)
	name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
	voiceprint_embedding: Mapped[list[float] | None] = mapped_column(
		Vector(256), nullable=True
	)  # 256-dimensional embedding vector
	confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
	)
	updated_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True),
		default=lambda: datetime.now(timezone.utc),
		onupdate=lambda: datetime.now(timezone.utc),
	)

	# Relationships
	organization: Mapped["Organization"] = relationship(
		"Organization", back_populates="speakers"
	)
	transcription_segments: Mapped[list["TranscriptionSegment"]] = relationship(
		"TranscriptionSegment", back_populates="speaker"
	)

	__table_args__ = (
		Index("idx_speakers_organization_id", "organization_id"),
		Index(
			"idx_speakers_voiceprint",
			"voiceprint_embedding",
			postgresql_using="ivfflat",
			postgresql_with={"lists": 100},
		),
		Index(
			"idx_speakers_org_name_unique",
			"organization_id",
			"name",
			unique=True,
		),
	)

	def __repr__(self) -> str:
		return f"<Speaker(id={self.id}, name={self.name}, org_id={self.organization_id})>"


class Meeting(Base):
	"""Meeting/recording session."""

	__tablename__ = "meetings"

	id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
	organization_id: Mapped[uuid.UUID] = mapped_column(
		UUID, ForeignKey("organizations.id"), nullable=False
	)
	title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
	audio_s3_key: Mapped[str] = mapped_column(VARCHAR(1024), nullable=False)
	status: Mapped[str] = mapped_column(
		VARCHAR(50), nullable=False, default="pending"
	)  # pending, processing, completed, failed
	duration_seconds: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
	)
	updated_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True),
		default=lambda: datetime.now(timezone.utc),
		onupdate=lambda: datetime.now(timezone.utc),
	)

	# Relationships
	organization: Mapped["Organization"] = relationship(
		"Organization", back_populates="meetings"
	)
	transcription_segments: Mapped[list["TranscriptionSegment"]] = relationship(
		"TranscriptionSegment", back_populates="meeting", cascade="all, delete-orphan"
	)
	summary: Mapped["MeetingSummary | None"] = relationship(
		"MeetingSummary", back_populates="meeting", uselist=False
	)
	name_suggestions: Mapped[list["NameSuggestion"]] = relationship(
		"NameSuggestion", back_populates="meeting", cascade="all, delete-orphan"
	)

	__table_args__ = (
		Index("idx_meetings_organization_id", "organization_id"),
		Index("idx_meetings_status", "status"),
		Index("idx_meetings_created_at", "created_at"),
	)

	def __repr__(self) -> str:
		return f"<Meeting(id={self.id}, title={self.title}, status={self.status})>"


class TranscriptionSegment(Base):
	"""Individual transcription segment with speaker information."""

	__tablename__ = "transcription_segments"

	id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
	meeting_id: Mapped[uuid.UUID] = mapped_column(
		UUID, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
	)
	speaker_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID, ForeignKey("speakers.id"), nullable=True
	)
	unidentified_speaker_label: Mapped[str | None] = mapped_column(
		VARCHAR(50), nullable=True
	)  # e.g., 'SPK_1', 'speaker_0'
	start_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
	end_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
	hebrew_text: Mapped[str] = mapped_column(Text, nullable=False)
	confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

	# Relationships
	meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="transcription_segments")
	speaker: Mapped["Speaker | None"] = relationship("Speaker", back_populates="transcription_segments")

	__table_args__ = (
		Index("idx_segments_meeting_id", "meeting_id"),
		Index("idx_segments_speaker_id", "speaker_id"),
		Index("idx_segments_start_time", "start_time_seconds"),
	)

	def __repr__(self) -> str:
		return f"<TranscriptionSegment(id={self.id}, meeting_id={self.meeting_id}, speaker_label={self.unidentified_speaker_label})>"


class MeetingSummary(Base):
	"""AI-generated summary for a meeting."""

	__tablename__ = "meeting_summaries"

	id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
	meeting_id: Mapped[uuid.UUID] = mapped_column(
		UUID, ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, nullable=False
	)
	summary_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
	)

	# Relationships
	meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="summary")

	__table_args__ = (Index("idx_summaries_meeting_id", "meeting_id"),)

	def __repr__(self) -> str:
		return f"<MeetingSummary(id={self.id}, meeting_id={self.meeting_id})>"


class NameSuggestion(Base):
	"""Name suggestions extracted from transcript for unidentified speakers."""

	__tablename__ = "name_suggestions"

	id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
	meeting_id: Mapped[uuid.UUID] = mapped_column(
		UUID, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
	)
	unidentified_speaker_label: Mapped[str] = mapped_column(
		VARCHAR(50), nullable=False
	)  # e.g., 'SPK_1'
	suggested_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
	confidence: Mapped[float] = mapped_column(Float, nullable=False)
	source_text: Mapped[str] = mapped_column(Text, nullable=True)  # The text segment that contained the name
	segment_start_time: Mapped[float | None] = mapped_column(Float, nullable=True)
	segment_end_time: Mapped[float | None] = mapped_column(Float, nullable=True)
	accepted: Mapped[bool] = mapped_column(default=False, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
	)

	# Relationships
	meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="name_suggestions")

	__table_args__ = (
		Index("idx_name_suggestions_meeting_id", "meeting_id"),
		Index("idx_name_suggestions_speaker_label", "unidentified_speaker_label"),
	)

	def __repr__(self) -> str:
		return f"<NameSuggestion(id={self.id}, speaker_label={self.unidentified_speaker_label}, name={self.suggested_name})>"


class AuditLog(Base):
	"""Audit log for security and compliance."""

	__tablename__ = "audit_logs"

	id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
	organization_id: Mapped[uuid.UUID | None] = mapped_column(
		UUID, ForeignKey("organizations.id"), nullable=True
	)
	user_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)
	action: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
	resource_type: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
	resource_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
	ip_address: Mapped[str | None] = mapped_column(VARCHAR(45), nullable=True)  # IPv6 compatible
	action_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
	)

	__table_args__ = (
		Index("idx_audit_logs_organization_id", "organization_id"),
		Index("idx_audit_logs_user_id", "user_id"),
		Index("idx_audit_logs_created_at", "created_at"),
		Index("idx_audit_logs_action", "action"),
	)

	def __repr__(self) -> str:
		return f"<AuditLog(id={self.id}, action={self.action}, created_at={self.created_at})>"

