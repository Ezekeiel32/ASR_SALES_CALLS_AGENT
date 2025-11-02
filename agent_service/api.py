from __future__ import annotations

import asyncio
import base64
import logging
import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agent_service.config import get_settings
from agent_service.database import get_db
from agent_service.database.models import Meeting, Organization, Speaker, User
from agent_service.auth import (
	verify_password,
	get_password_hash,
	create_access_token,
	decode_access_token,
)
from agent_service.dependencies import get_current_user, get_current_organization
from agent_service.service import AgentService
from agent_service.services import NameSuggestionService, SpeakerService
from agent_service.services.processing_queue import enqueue_meeting_processing, get_processing_status
from agent_service.services.s3_model_storage import configure_huggingface_cache_for_s3

# Configure HuggingFace to use minimal local cache (models will be in S3)
configure_huggingface_cache_for_s3()

app = FastAPI(title="Hebrew Medical Sales Call Agent", version="0.1.0")

# Configure CORS
def get_cors_origins() -> list[str]:
	"""Get CORS origins from settings or use defaults."""
	settings = get_settings()
	logger = logging.getLogger(__name__)
	
	# Default development origins
	default_origins = [
		"http://localhost:3000",
		"http://localhost:5173",
		"http://127.0.0.1:3000",
		"http://127.0.0.1:5173",
	]
	
	# Add production Netlify domain
	production_origins = [
		"https://ivreetmeet.netlify.app",
	]
	
	# If CORS_ORIGINS is set in environment, use it (comma-separated)
	if settings.cors_origins:
		custom_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
		all_origins = list(set(default_origins + production_origins + custom_origins))
	else:
		all_origins = default_origins + production_origins
	
	logger.info(f"CORS allowed origins: {all_origins}")
	return all_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

settings = get_settings()
service = AgentService(settings)


@app.post("/process")
async def process_audio(file: UploadFile = File(...)) -> JSONResponse:  # type: ignore[call-arg]
	data = await file.read()
	transcription, summary = await service.process_audio_bytes(data=data, filename=file.filename or "audio.wav")
	return JSONResponse(
		{
			"transcript": transcription.text,
			"summary": summary.text,
			"segments": transcription.segments,
		}
	)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
	return {"status": "ok"}


# ---- Authentication Endpoints ----

class RegisterRequest(BaseModel):
	email: str
	password: str
	name: str | None = None
	organization_name: str | None = None


class LoginRequest(BaseModel):
	email: str
	password: str


class TokenResponse(BaseModel):
	access_token: str
	token_type: str = "bearer"
	user_id: str
	organization_id: str
	email: str
	name: str | None


@app.post("/auth/register", response_model=TokenResponse)
async def register(
	request: RegisterRequest,
	db: Session = Depends(get_db),
) -> TokenResponse:
	"""
	Register a new user account.
	Creates a new organization if organization_name is provided,
	otherwise assigns to default organization.
	"""
	# Check if user already exists
	existing_user = db.query(User).filter(User.email == request.email).first()
	if existing_user:
		raise HTTPException(status_code=400, detail="Email already registered")
	
	# Create organization (required)
	if not request.organization_name:
		raise HTTPException(status_code=400, detail="organization_name is required for registration")
	
	# Create new organization
	org = Organization(
		name=request.organization_name,
		subscription_plan="free",
	)
	db.add(org)
	db.flush()  # Get org ID
	
	# Create user
	user = User(
		organization_id=org.id,
		email=request.email,
		name=request.name,
		password_hash=get_password_hash(request.password),
	)
	db.add(user)
	db.commit()
	db.refresh(user)
	
	# Create access token
	access_token = create_access_token(
		data={"sub": str(user.id), "org_id": str(org.id), "email": user.email}
	)
	
	return TokenResponse(
		access_token=access_token,
		token_type="bearer",
		user_id=str(user.id),
		organization_id=str(org.id),
		email=user.email,
		name=user.name,
	)


@app.post("/auth/login", response_model=TokenResponse)
async def login(
	request: LoginRequest,
	db: Session = Depends(get_db),
) -> TokenResponse:
	"""
	Login with email and password.
	Returns JWT access token.
	"""
	# Find user by email
	user = db.query(User).filter(User.email == request.email).first()
	if not user:
		raise HTTPException(status_code=401, detail="Invalid email or password")
	
	# Verify password
	if not user.password_hash or not verify_password(request.password, user.password_hash):
		raise HTTPException(status_code=401, detail="Invalid email or password")
	
	# Get organization
	org = db.get(Organization, user.organization_id)
	if not org:
		raise HTTPException(status_code=500, detail="User organization not found")
	
	# Create access token
	access_token = create_access_token(
		data={"sub": str(user.id), "org_id": str(org.id), "email": user.email}
	)
	
	return TokenResponse(
		access_token=access_token,
		token_type="bearer",
		user_id=str(user.id),
		organization_id=str(org.id),
		email=user.email,
		name=user.name,
	)


@app.get("/auth/me", response_model=TokenResponse)
async def get_me(
	current_user: User = Depends(get_current_user),
	organization: Organization = Depends(get_current_organization),
) -> TokenResponse:
	"""
	Get current authenticated user info from JWT token.
	"""
	# Recreate token with current user data
	access_token = create_access_token(
		data={"sub": str(current_user.id), "org_id": str(organization.id), "email": current_user.email}
	)
	
	return TokenResponse(
		access_token=access_token,
		token_type="bearer",
		user_id=str(current_user.id),
		organization_id=str(organization.id),
		email=current_user.email,
		name=current_user.name,
	)


# ---- Power Automate friendly endpoints ----


class TranscribeUrlRequest(BaseModel):
	url: str
	language: str | None = None
	filename: str | None = None


def _format_srt_timestamp(seconds: float) -> str:
	if seconds < 0:
		seconds = 0
	ms_total = int(round(seconds * 1000))
	hours, rem_ms = divmod(ms_total, 3600_000)
	minutes, rem_ms = divmod(rem_ms, 60_000)
	secs, millis = divmod(rem_ms, 1000)
	return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_srt(segments: list[dict[str, Any]] | None) -> str:
	if not segments:
		return ""
	lines: list[str] = []
	index = 1
	for seg in segments:
		start = float(seg.get("start", 0))
		end = float(seg.get("end", max(start, start + 0.01)))
		text = seg.get("text")
		if not isinstance(text, str) and isinstance(seg.get("words"), list):
			# join word-level tokens into a line
			text = " ".join([w.get("word", "") for w in seg.get("words") if isinstance(w, dict)])
		if not isinstance(text, str):
			text = ""
		lines.append(str(index))
		lines.append(f"{_format_srt_timestamp(start)} --> { _format_srt_timestamp(end)}")
		lines.append(text.strip())
		lines.append("")
		index += 1
	return "\n".join(lines).strip() + "\n"


def _safe_text_from_segments(segments: list[dict[str, Any]] | None) -> str:
	if not segments:
		return ""
	parts: list[str] = []
	for seg in segments:
		text = seg.get("text")
		if isinstance(text, str) and text.strip():
			parts.append(text.strip())
	return " ".join(parts)


@app.post("/transcribe")
async def transcribe(request: Request, file: UploadFile | None = File(None)) -> JSONResponse:
	data: bytes | None = None
	filename: str = request.headers.get("x-filename", "audio.wav")
	language: str | None = None
	# 1) If multipart file provided, prefer that
	if file is not None:
		data = await file.read()
		filename = file.filename or filename
	else:
		# 2) If content-type is audio/* or application/octet-stream, read raw body as audio
		ct = (request.headers.get("content-type") or "").lower()
		if ct.startswith("audio/") or ct.startswith("application/octet-stream"):
			data = await request.body()
		else:
			# 3) Otherwise, accept JSON body with { url, language, filename } or { base64, filename }
			try:
				body = await request.json()
				# base64 path
				if isinstance(body, dict) and "base64" in body:
					b64 = body.get("base64")
					if not isinstance(b64, str):
						raise ValueError("base64 field must be a string")
					# handle potential data URI prefix
					if "," in b64 and b64.strip().startswith("data:"):
						b64 = b64.split(",", 1)[1]
					data = base64.b64decode(b64)
					language = body.get("language") or None
					if isinstance(body.get("filename"), str):
						filename = body.get("filename")
				else:
					model = TranscribeUrlRequest(**body)
					language = model.language
					filename = model.filename or filename
					async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
						resp = await client.get(model.url)
						resp.raise_for_status()
						data = resp.content
			except Exception as e:  # noqa: BLE001
				raise HTTPException(status_code=400, detail=f"Provide a file upload, raw audio body, JSON with base64, or JSON with url. Error: {e}")

	if data is None:
		raise HTTPException(status_code=400, detail="No audio data provided")

	transcription, _ = await service.process_audio_bytes(data=data, filename=filename)
	# If text missing, try to build from segments
	transcript_text = transcription.text or _safe_text_from_segments(transcription.segments)
	srt_text = _format_srt(transcription.segments)
	return JSONResponse(
		{
			"transcript": transcript_text,
			"segments": transcription.segments,
			"srt": srt_text,
			"txt": transcript_text,
		}
	)


class AnalyzeRequest(BaseModel):
	transcript: str
	sourceAudio: str | None = None
	transcriptFile: str | None = None
	persona: str | None = None
	length: str | None = None
	speaker_segments: list[dict[str, Any]] | None = None


class MeetingUploadRequest(BaseModel):
	title: str
	organization_id: str
	audio_s3_key: str | None = None


class SpeakerAssignmentRequest(BaseModel):
	speaker_label: str
	speaker_name: str


def _extract_keypoints(markdown_text: str) -> list[str]:
	points: list[str] = []
	for line in markdown_text.splitlines():
		if re.match(r"^\s*([-*•—])\s+", line):
			points.append(re.sub(r"^\s*([-*•—])\s+", "", line).strip())
	return points[:10]


@app.post("/analyze")
async def analyze(req: AnalyzeRequest) -> JSONResponse:
	# Parse speaker_segments if provided in the request
	speaker_segments: list[dict[str, Any]] | None = None
	if hasattr(req, "speaker_segments") and req.speaker_segments:
		speaker_segments = req.speaker_segments
	elif isinstance(req.transcript, dict) and "speaker_segments" in req.transcript:
		# Support legacy format where transcript might be a dict with segments
		speaker_segments = req.transcript.get("speaker_segments")

	result = await service.summarizer.summarize(req.transcript, speaker_segments=speaker_segments)
	markdown = result.text
	key_points = _extract_keypoints(markdown)
	run_id = f"nvidia-{uuid.uuid4()}"
	analysis = {
		"sourceAudio": req.sourceAudio,
		"transcriptFile": req.transcriptFile,
		"summary": markdown,
		"keyPoints": key_points,
		"actionItems": [],
		"entities": {},
		"sentiment": None,
		"topics": [],
		"confidence": None,
		"runId": run_id,
		"createdAt": datetime.now(timezone.utc).isoformat(),
		"speakerAware": speaker_segments is not None,
	}
	return JSONResponse({"summary_markdown": markdown, "analysis": analysis})


# ---- New Meeting & Speaker Endpoints ----


@app.post("/meetings/upload")
async def upload_meeting(
	file: UploadFile = File(...),
	title: str = Form(""),
	current_user: User = Depends(get_current_user),
	organization: Organization = Depends(get_current_organization),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""
	Upload a new audio file for processing.
	Requires authentication - uses organization from logged-in user.
	Creates a meeting record and triggers async processing.
	"""
	import boto3
	from agent_service.config import get_settings
	from agent_service.services.orchestrator import ProcessingOrchestrator
	import logging

	logger = logging.getLogger(__name__)

	try:
		settings = get_settings()
		# Use organization from authenticated user
		org_id = organization.id

		# Save audio to S3 or local storage
		audio_s3_key = None
		audio_bytes = None
		import os

		if file:
			logger.info(f"Reading uploaded file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
			audio_bytes = await file.read()
			logger.info(f"Read {len(audio_bytes)/(1024*1024):.1f}MB from uploaded file")
			
			# Upload to S3 if configured
			if settings.s3_bucket:
				logger.info(f"Uploading to S3 bucket: {settings.s3_bucket}")
				s3_client = boto3.client(
					"s3",
					region_name=settings.s3_region,
					aws_access_key_id=settings.aws_access_key_id,
					aws_secret_access_key=settings.aws_secret_access_key,
				)
				audio_s3_key = f"meetings/{org_id}/{uuid.uuid4()}/{file.filename or 'audio.wav'}"
				s3_client.put_object(
					Bucket=settings.s3_bucket,
					Key=audio_s3_key,
					Body=audio_bytes,
					ContentType=file.content_type or "audio/wav",
				)
				logger.info(f"Successfully uploaded to S3: {audio_s3_key}")
			else:
				# Save to local storage when S3 is not configured
				uploads_dir = "./uploads/meetings"
				os.makedirs(uploads_dir, exist_ok=True)
				# Create a temporary meeting ID first to save the file
				temp_meeting_id = uuid.uuid4()
				local_path = f"{uploads_dir}/{temp_meeting_id}_{file.filename or 'audio.wav'}"
				with open(local_path, "wb") as f:
					f.write(audio_bytes)
				# Store absolute path to avoid working directory issues
				audio_s3_key = os.path.abspath(local_path)
				logger.info(f"Saved to local storage: {audio_s3_key}")
		else:
			raise HTTPException(status_code=400, detail="File upload required")

		# Create meeting record
		# Use filename as default title if no title provided
		meeting_title = title.strip() if title and title.strip() else (file.filename or "New Meeting")
		# Remove file extension for cleaner title
		if meeting_title.endswith(('.mp3', '.wav', '.m4a', '.aac', '.webm')):
			meeting_title = meeting_title.rsplit('.', 1)[0]
		
		meeting = Meeting(
			organization_id=org_id,
			title=meeting_title,
			audio_s3_key=audio_s3_key or "pending",
			status="pending",
		)
		db.add(meeting)
		db.commit()

		# Update the local path with the actual meeting ID if using local storage
		if not settings.s3_bucket and audio_s3_key:
			# Rename file to use actual meeting ID
			old_path = audio_s3_key
			new_path = os.path.abspath(f"{uploads_dir}/{meeting.id}_{file.filename or 'audio.wav'}")
			if old_path != new_path:
				os.rename(old_path, new_path)
			audio_s3_key = new_path
			meeting.audio_s3_key = new_path
			db.commit()

		# Trigger async processing
		task_id = enqueue_meeting_processing(
			meeting_id=meeting.id,
			organization_id=org_id,
			audio_s3_key=audio_s3_key,
		)

		logger.info(f"Meeting {meeting.id} uploaded successfully, task {task_id} enqueued")

		return JSONResponse(
			{
				"meeting_id": str(meeting.id),
				"status": "pending",
				"processing_task_id": task_id,
				"message": "Meeting uploaded and processing started",
			}
		)
	except HTTPException:
		# Re-raise HTTP exceptions (they already have proper status codes)
		raise
	except Exception as e:
		logger.error(f"Error uploading meeting: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/meetings")
async def list_meetings(
	status: str | None = None,
	limit: int = 50,
	offset: int = 0,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""List meetings for the authenticated user's organization. Requires authentication."""
	# Filter by user's organization automatically
	query = db.query(Meeting).filter(Meeting.organization_id == current_user.organization_id)
	
	if status:
		query = query.filter(Meeting.status == status)
	
	meetings = query.order_by(Meeting.created_at.desc() if Meeting.created_at else None).limit(limit).offset(offset).all()
	
	return JSONResponse(
		{
			"meetings": [
				{
					"id": str(m.id),
					"title": m.title,
					"status": m.status,
					"duration_seconds": m.duration_seconds,
					"created_at": m.created_at.isoformat() if m.created_at else None,
					"organization_id": str(m.organization_id),
				}
				for m in meetings
			],
			"total": query.count(),
			"limit": limit,
			"offset": offset,
		}
	)


@app.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: str, db: Session = Depends(get_db)) -> JSONResponse:
	"""Get meeting details including status."""
	meeting = db.get(Meeting, uuid.UUID(meeting_id))
	if not meeting:
		raise HTTPException(status_code=404, detail="Meeting not found")

	return JSONResponse(
		{
			"id": str(meeting.id),
			"title": meeting.title,
			"status": meeting.status,
			"duration_seconds": meeting.duration_seconds,
			"created_at": meeting.created_at.isoformat() if meeting.created_at else None,
		}
	)


@app.get("/meetings/{meeting_id}/unidentified_speakers")
async def get_unidentified_speakers(
	meeting_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""
	Get unidentified speakers with their 15-second snippets and name suggestions.
	Requires authentication.
	"""
	from agent_service.database.models import TranscriptionSegment

	meeting_uuid = uuid.UUID(meeting_id)
	meeting = db.get(Meeting, meeting_uuid)
	if not meeting:
		raise HTTPException(status_code=404, detail="Meeting not found")
	
	# Verify meeting belongs to user's organization
	if meeting.organization_id != current_user.organization_id:
		raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")

	# Get all unique unidentified speaker labels from transcription segments
	segments = db.query(TranscriptionSegment).filter(
		TranscriptionSegment.meeting_id == meeting_uuid,
		TranscriptionSegment.speaker_id.is_(None),
	).all()
	
	speaker_labels = set()
	for seg in segments:
		if seg.unidentified_speaker_label:
			speaker_labels.add(seg.unidentified_speaker_label)

	# Get name suggestions for each speaker
	name_service = NameSuggestionService(db)
	speakers_with_suggestions: dict[str, list[dict[str, Any]]] = {}
	
	for speaker_label in speaker_labels:
		suggestions = name_service.get_name_suggestions_for_speaker(
			meeting_id=meeting_uuid,
			speaker_label=speaker_label,
		)
		if suggestions:
			speakers_with_suggestions[speaker_label] = [
				{
					"suggestion_id": str(s.id),
					"name": s.suggested_name,
					"confidence": float(s.confidence_score) if s.confidence_score else 0.0,
					"source_text": s.source_text,
					"accepted": s.accepted,
					"segment_start_time": float(seg.start_time_seconds) if (seg := db.query(TranscriptionSegment).filter(
						TranscriptionSegment.meeting_id == meeting_uuid,
						TranscriptionSegment.unidentified_speaker_label == speaker_label,
					).first()) else None,
					"segment_end_time": float(seg.end_time_seconds) if seg else None,
				}
				for s in suggestions
			]

	return JSONResponse(
		{
			"meeting_id": meeting_id,
			"unidentified_speakers": speakers_with_suggestions,
		}
	)


@app.put("/meetings/{meeting_id}/speakers/assign")
async def assign_speaker_name(
	meeting_id: str,
	request: SpeakerAssignmentRequest,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""
	Assign a name to an unidentified speaker.
	Creates or updates speaker profile and associates voiceprint.
	Requires authentication.
	"""
	from agent_service.services.orchestrator import ProcessingOrchestrator

	meeting_uuid = uuid.UUID(meeting_id)
	meeting = db.get(Meeting, meeting_uuid)
	if not meeting:
		raise HTTPException(status_code=404, detail="Meeting not found")
	
	# Verify meeting belongs to user's organization
	if meeting.organization_id != current_user.organization_id:
		raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")

	# Get speaker service
	speaker_service = SpeakerService(db)

	# Find the speaker's voiceprint from meeting processing
	# TODO: Retrieve voiceprint from meeting metadata

	# Assign name (creates new speaker or matches existing)
	speaker, is_new = speaker_service.assign_name_to_speaker(
		meeting_id=meeting_uuid,
		unidentified_speaker_label=request.speaker_label,
		speaker_name=request.speaker_name,
		organization_id=meeting.organization_id,
		voiceprint_embedding=None,  # TODO: Retrieve from meeting
	)

	db.commit()

	return JSONResponse(
		{
			"speaker_id": str(speaker.id),
			"name": speaker.name,
			"is_new": is_new,
			"message": f"Speaker '{request.speaker_name}' assigned to {request.speaker_label}",
		}
	)


@app.get("/organizations/{org_id}/speakers")
async def list_organization_speakers(
	org_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""List all known speakers for an organization. Requires authentication."""
	org_uuid = uuid.UUID(org_id)
	
	# Verify user belongs to this organization
	if current_user.organization_id != org_uuid:
		raise HTTPException(status_code=403, detail="You don't have access to this organization")
	
	speaker_service = SpeakerService(db)
	speakers = speaker_service.get_organization_speakers(org_uuid)

	return JSONResponse(
		{
			"organization_id": org_id,
			"speakers": [
				{
					"id": str(s.id),
					"name": s.name,
					"created_at": s.created_at.isoformat() if s.created_at else None,
				}
				for s in speakers
			],
		}
	)


@app.get("/meetings/{meeting_id}/transcript")
async def get_meeting_transcript(
	meeting_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""Get the full speaker-labeled transcript for a meeting. Requires authentication."""
	from agent_service.database.models import TranscriptionSegment

	meeting_uuid = uuid.UUID(meeting_id)
	meeting = db.get(Meeting, meeting_uuid)
	if not meeting:
		raise HTTPException(status_code=404, detail="Meeting not found")
	
	# Verify meeting belongs to user's organization
	if meeting.organization_id != current_user.organization_id:
		raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")

	segments = db.query(TranscriptionSegment).filter(
		TranscriptionSegment.meeting_id == meeting_uuid
	).order_by(TranscriptionSegment.start_time_seconds).all()

	transcript_segments = [
		{
			"start": seg.start_time_seconds,
			"end": seg.end_time_seconds,
			"text": seg.hebrew_text,
			"speaker": seg.unidentified_speaker_label,
			"speaker_id": str(seg.speaker_id) if seg.speaker_id else None,
		}
		for seg in segments
	]

	return JSONResponse(
		{
			"meeting_id": meeting_id,
			"transcript_segments": transcript_segments,
		}
	)


@app.get("/meetings/{meeting_id}/summary")
async def get_meeting_summary(
	meeting_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""Get the AI-generated summary for a meeting. Requires authentication."""
	from agent_service.database.models import MeetingSummary

	meeting_uuid = uuid.UUID(meeting_id)
	meeting = db.get(Meeting, meeting_uuid)
	if not meeting:
		raise HTTPException(status_code=404, detail="Meeting not found")
	
	# Verify meeting belongs to user's organization
	if meeting.organization_id != current_user.organization_id:
		raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")

	summary = db.query(MeetingSummary).filter(MeetingSummary.meeting_id == meeting_uuid).first()

	if not summary:
		raise HTTPException(status_code=404, detail="Summary not found for this meeting")

	return JSONResponse(
		{
			"meeting_id": meeting_id,
			"summary": summary.summary_json,
		}
	)


@app.delete("/meetings/{meeting_id}")
async def delete_meeting(
	meeting_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> JSONResponse:
	"""
	Delete a meeting and all associated data.
	Requires authentication.
	
	Deletes:
	- Meeting record (cascades to transcription_segments, meeting_summaries, name_suggestions)
	- Audio file from S3 or local storage
	- Speaker snippet files
	
	Args:
		meeting_id: Meeting UUID to delete
	
	Returns:
		Success response with deleted meeting details
	"""
	import logging
	import os
	import shutil
	from pathlib import Path
	
	logger = logging.getLogger(__name__)
	
	try:
		meeting_uuid = uuid.UUID(meeting_id)
	except ValueError:
		raise HTTPException(status_code=400, detail=f"Invalid meeting_id format: {meeting_id}")
	
	meeting = db.get(Meeting, meeting_uuid)
	if not meeting:
		raise HTTPException(status_code=404, detail="Meeting not found")
	
	# Verify meeting belongs to user's organization
	if meeting.organization_id != current_user.organization_id:
		raise HTTPException(
			status_code=403, detail="Meeting does not belong to your organization"
		)
	
	# Prevent deletion of meetings in processing status (optional - could allow with warning)
	if meeting.status == "processing":
		raise HTTPException(
			status_code=409,
			detail="Cannot delete meeting while it is being processed. Please wait for processing to complete or fail.",
		)
	
	# Store meeting info for response
	meeting_title = meeting.title
	audio_s3_key = meeting.audio_s3_key
	
	# Delete audio file
	audio_deleted = False
	try:
		settings = get_settings()
		
		# Check if audio_s3_key is an S3 key or local file path
		if audio_s3_key and audio_s3_key != "pending":
			if settings.s3_bucket and not os.path.exists(audio_s3_key):
				# Assume it's an S3 key
				try:
					s3_client = boto3.client(
						"s3",
						region_name=settings.s3_region,
						aws_access_key_id=settings.aws_access_key_id,
						aws_secret_access_key=settings.aws_secret_access_key,
					)
					# Check if key exists before deleting
					try:
						s3_client.head_object(Bucket=settings.s3_bucket, Key=audio_s3_key)
						s3_client.delete_object(Bucket=settings.s3_bucket, Key=audio_s3_key)
						audio_deleted = True
						logger.info(f"Deleted audio file from S3: {audio_s3_key}")
					except ClientError as e:
						if e.response["Error"]["Code"] == "404":
							logger.warning(f"Audio file not found in S3: {audio_s3_key}")
						else:
							logger.error(f"Failed to delete audio from S3: {e}")
				except Exception as e:
					logger.error(f"Error deleting audio from S3: {e}")
			else:
				# Local file path
				try:
					if os.path.exists(audio_s3_key):
						os.remove(audio_s3_key)
						audio_deleted = True
						logger.info(f"Deleted local audio file: {audio_s3_key}")
				except Exception as e:
					logger.error(f"Failed to delete local audio file: {e}")
		
		# Delete snippet files (if they exist)
		snippets_deleted = 0
		
		# Try S3 snippets
		if settings.s3_bucket:
			try:
				s3_client = boto3.client(
					"s3",
					region_name=settings.s3_region,
					aws_access_key_id=settings.aws_access_key_id,
					aws_secret_access_key=settings.aws_secret_access_key,
				)
				# List and delete all objects in the snippets prefix
				snippet_prefix = f"meetings/{meeting_id}/snippets/"
				paginator = s3_client.get_paginator("list_objects_v2")
				pages = paginator.paginate(Bucket=settings.s3_bucket, Prefix=snippet_prefix)
				
				for page in pages:
					if "Contents" in page:
						for obj in page["Contents"]:
							try:
								s3_client.delete_object(Bucket=settings.s3_bucket, Key=obj["Key"])
								snippets_deleted += 1
							except Exception as e:
								logger.warning(f"Failed to delete snippet {obj['Key']}: {e}")
			except Exception as e:
				logger.warning(f"Error deleting snippets from S3: {e}")
		
		# Try local snippets
		local_snippets_dir = Path(f"agent_service/snippets/{meeting_id}")
		if local_snippets_dir.exists() and local_snippets_dir.is_dir():
			try:
				# Count files before deletion
				snippet_files = list(local_snippets_dir.glob("*"))
				snippets_deleted = len(snippet_files)
				shutil.rmtree(local_snippets_dir)
				logger.info(f"Deleted local snippets directory: {local_snippets_dir} ({snippets_deleted} files)")
			except Exception as e:
				logger.warning(f"Failed to delete local snippets directory: {e}")
		
	except Exception as e:
		logger.error(f"Error during file cleanup: {e}", exc_info=True)
		# Continue with database deletion even if file deletion fails
	
	# Delete meeting record (cascade will handle related records)
	try:
		db.delete(meeting)
		db.commit()
		logger.info(f"Deleted meeting {meeting_id}: {meeting_title}")
	except Exception as e:
		db.rollback()
		logger.error(f"Failed to delete meeting from database: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Failed to delete meeting: {str(e)}")
	
	return JSONResponse(
		{
			"meeting_id": meeting_id,
			"title": meeting_title,
			"status": "deleted",
			"audio_deleted": audio_deleted,
			"snippets_deleted": snippets_deleted,
			"message": "Meeting deleted successfully",
		}
	)

