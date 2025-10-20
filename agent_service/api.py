from __future__ import annotations

import asyncio
import base64
import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent_service.config import get_settings
from agent_service.service import AgentService


app = FastAPI(title="Hebrew Medical Sales Call Agent", version="0.1.0")
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


def _extract_keypoints(markdown_text: str) -> list[str]:
	points: list[str] = []
	for line in markdown_text.splitlines():
		if re.match(r"^\s*([-*•—])\s+", line):
			points.append(re.sub(r"^\s*([-*•—])\s+", "", line).strip())
	return points[:10]


@app.post("/analyze")
async def analyze(req: AnalyzeRequest) -> JSONResponse:
	result = await service.summarizer.summarize(req.transcript)
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
	}
	return JSONResponse({"summary_markdown": markdown, "analysis": analysis})

