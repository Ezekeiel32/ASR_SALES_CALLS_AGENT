"""
RunPod Serverless FastAPI Server - Consolidated Backend
This replaces the separate API server and worker - everything runs in RunPod Serverless.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Depends, HTTPException, File, Form, UploadFile, Header, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import all necessary components
from agent_service.config import get_settings
from agent_service.database import get_db
from agent_service.database.models import Meeting, Organization, Speaker, User, UserGmailCredentials, TranscriptionSegment, MeetingSummary
from agent_service.auth import verify_password, get_password_hash, create_access_token, decode_access_token
from agent_service.dependencies import get_current_user, get_current_organization
from agent_service.service import AgentService
from agent_service.services import NameSuggestionService, SpeakerService
from agent_service.services.orchestrator import ProcessingOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IvriMeet Backend API - RunPod Serverless",
    version="1.0.0",
    description="Consolidated backend API running on RunPod Serverless"
)

settings = get_settings()
service = AgentService(settings)

# ==================== CORS Configuration ====================

def get_cors_origins() -> list[str]:
    """Get CORS origins from settings or use defaults."""
    logger = logging.getLogger(__name__)
    
    # Default development origins
    default_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ==================== Exception Handlers ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure CORS headers are included in error responses."""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
    origin = request.headers.get("origin")
    if origin and origin in get_cors_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Ensure CORS headers are included in validation error responses."""
    response = JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
    origin = request.headers.get("origin")
    if origin and origin in get_cors_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Ensure CORS headers are included in all error responses."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
    origin = request.headers.get("origin")
    if origin and origin in get_cors_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# ==================== Health Check ====================

@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "runpod-serverless"}

@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "IvriMeet Backend API",
        "version": "1.0.0",
        "mode": "runpod-serverless",
        "status": "running"
    }

# ==================== Pydantic Models ====================

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

class SpeakerAssignmentRequest(BaseModel):
    speaker_label: str
    speaker_name: str

# ==================== Authentication Endpoints ====================

@app.post("/auth/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new user account."""
    try:
        if len(request.password) == 0:
            raise HTTPException(status_code=400, detail="Password cannot be empty")
        
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if not request.organization_name:
            raise HTTPException(status_code=400, detail="organization_name is required for registration")
        
        org = Organization(
            name=request.organization_name,
            subscription_plan="free",
        )
        db.add(org)
        db.flush()
        
        user = User(
            organization_id=org.id,
            email=request.email,
            name=request.name,
            password_hash=get_password_hash(request.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Login with email and password."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    org = db.get(Organization, user.organization_id)
    if not org:
        raise HTTPException(status_code=500, detail="User organization not found")
    
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
    """Get current authenticated user info from JWT token."""
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

# ==================== Meeting Endpoints ====================

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
    Creates a meeting record and triggers async processing.
    """
    import boto3
    
    try:
        org_id = organization.id
        audio_s3_key = None
        audio_bytes = None
        
        if file:
            logger.info(f"Reading uploaded file: {file.filename}")
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
                # Save to local storage
                uploads_dir = "./uploads/meetings"
                os.makedirs(uploads_dir, exist_ok=True)
                temp_meeting_id = uuid.uuid4()
                local_path = f"{uploads_dir}/{temp_meeting_id}_{file.filename or 'audio.wav'}"
                with open(local_path, "wb") as f:
                    f.write(audio_bytes)
                audio_s3_key = os.path.abspath(local_path)
                logger.info(f"Saved to local storage: {audio_s3_key}")
        else:
            raise HTTPException(status_code=400, detail="File upload required")
        
        # Create meeting record
        meeting_title = title.strip() if title and title.strip() else (file.filename or "New Meeting")
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
        db.refresh(meeting)
        
        # Update local path with actual meeting ID if using local storage
        if not settings.s3_bucket and audio_s3_key:
            old_path = audio_s3_key
            new_path = os.path.abspath(f"{uploads_dir}/{meeting.id}_{file.filename or 'audio.wav'}")
            if old_path != new_path:
                os.rename(old_path, new_path)
            audio_s3_key = new_path
            meeting.audio_s3_key = new_path
            db.commit()
        
        # Trigger async processing in background
        asyncio.create_task(
            process_meeting_async(meeting.id, org_id, audio_s3_key)
        )
        
        logger.info(f"Meeting {meeting.id} uploaded successfully, processing started")
        
        return JSONResponse(
            {
                "meeting_id": str(meeting.id),
                "status": "pending",
                "message": "Meeting uploaded and processing started",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading meeting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_meeting_async(
    meeting_id: uuid.UUID,
    organization_id: uuid.UUID,
    audio_s3_key: str | None,
):
    """Background task to process meeting."""
    from agent_service.database.connection import get_db_session
    
    try:
        with get_db_session() as db:
            orchestrator = ProcessingOrchestrator(db)
            await orchestrator.process_meeting(
                meeting_id=meeting_id,
                organization_id=organization_id,
                audio_s3_key=audio_s3_key,
            )
        logger.info(f"Successfully processed meeting {meeting_id}")
    except Exception as e:
        logger.error(f"Error processing meeting {meeting_id}: {e}", exc_info=True)

@app.get("/meetings")
async def list_meetings(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """List meetings for the authenticated user's organization."""
    query = db.query(Meeting).filter(Meeting.organization_id == current_user.organization_id)
    
    if status:
        query = query.filter(Meeting.status == status)
    
    meetings = query.order_by(Meeting.created_at.desc()).limit(limit).offset(offset).all()
    
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
async def get_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get meeting details including status."""
    meeting = db.get(Meeting, uuid.UUID(meeting_id))
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")
    
    return JSONResponse(
        {
            "id": str(meeting.id),
            "title": meeting.title,
            "status": meeting.status,
            "duration_seconds": meeting.duration_seconds,
            "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
        }
    )

@app.get("/meetings/{meeting_id}/transcript")
async def get_meeting_transcript(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get the full speaker-labeled transcript for a meeting."""
    meeting_uuid = uuid.UUID(meeting_id)
    meeting = db.get(Meeting, meeting_uuid)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
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
    """Get the AI-generated summary for a meeting."""
    meeting_uuid = uuid.UUID(meeting_id)
    meeting = db.get(Meeting, meeting_uuid)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
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
    """Delete a meeting and all associated data."""
    try:
        meeting_uuid = uuid.UUID(meeting_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid meeting_id format: {meeting_id}")
    
    meeting = db.get(Meeting, meeting_uuid)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")
    
    if meeting.status == "processing":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete meeting while it is being processed.",
        )
    
    meeting_title = meeting.title
    audio_s3_key = meeting.audio_s3_key
    
    # Delete audio file
    audio_deleted = False
    try:
        if audio_s3_key and audio_s3_key != "pending":
            if settings.s3_bucket and not os.path.exists(audio_s3_key):
                # S3 file
                import boto3
                from botocore.exceptions import ClientError
                s3_client = boto3.client(
                    "s3",
                    region_name=settings.s3_region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                )
                try:
                    s3_client.head_object(Bucket=settings.s3_bucket, Key=audio_s3_key)
                    s3_client.delete_object(Bucket=settings.s3_bucket, Key=audio_s3_key)
                    audio_deleted = True
                    logger.info(f"Deleted audio file from S3: {audio_s3_key}")
                except ClientError:
                    pass
            else:
                # Local file
                if os.path.exists(audio_s3_key):
                    os.remove(audio_s3_key)
                    audio_deleted = True
                    logger.info(f"Deleted local audio file: {audio_s3_key}")
    except Exception as e:
        logger.error(f"Error deleting audio file: {e}")
    
    # Delete meeting record
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
            "message": "Meeting deleted successfully",
        }
    )

# ==================== Speaker Endpoints ====================

@app.get("/meetings/{meeting_id}/unidentified_speakers")
async def get_unidentified_speakers(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get unidentified speakers with their snippets and name suggestions."""
    meeting_uuid = uuid.UUID(meeting_id)
    meeting = db.get(Meeting, meeting_uuid)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")
    
    segments = db.query(TranscriptionSegment).filter(
        TranscriptionSegment.meeting_id == meeting_uuid,
        TranscriptionSegment.speaker_id.is_(None),
    ).all()
    
    speaker_labels = set()
    for seg in segments:
        if seg.unidentified_speaker_label:
            speaker_labels.add(seg.unidentified_speaker_label)
    
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
    """Assign a name to an unidentified speaker."""
    meeting_uuid = uuid.UUID(meeting_id)
    meeting = db.get(Meeting, meeting_uuid)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if meeting.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Meeting does not belong to your organization")
    
    speaker_service = SpeakerService(db)
    
    speaker, is_new = speaker_service.assign_name_to_speaker(
        meeting_id=meeting_uuid,
        unidentified_speaker_label=request.speaker_label,
        speaker_name=request.speaker_name,
        organization_id=meeting.organization_id,
        voiceprint_embedding=None,
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
    """List all known speakers for an organization."""
    org_uuid = uuid.UUID(org_id)
    
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

# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting IvriMeet Backend API on {host}:{port}")
    logger.info(f"RunPod Serverless Mode - Consolidated Backend")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
