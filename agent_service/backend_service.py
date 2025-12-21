from __future__ import annotations

from typing import Literal

from agent_service.clients import IvritClient
from agent_service.config import Settings, TranscriptionResult, get_settings
from agent_service.summarizers.base import SummaryResult, Summarizer
from agent_service.summarizers.grok import GrokSummarizer


class AgentService:
	def __init__(self, settings: Settings | None = None) -> None:
		self.settings = settings or get_settings()
		self.ivrit = IvritClient(self.settings)
		self.summarizer = self._build_summarizer()


	def _build_summarizer(self) -> Summarizer:
		"""Build the Grok summarizer."""
		return GrokSummarizer(self.settings)

	async def process_audio_bytes(self, data: bytes, filename: str = "audio.wav") -> tuple[TranscriptionResult, SummaryResult]:
		transcription = await self.ivrit.transcribe_bytes(data=data, filename=filename)
		summary = await self.summarizer.summarize(
			transcription.text, speaker_segments=transcription.speaker_segments
		)
		return transcription, summary

	async def process_audio_file(self, path: str) -> tuple[TranscriptionResult, SummaryResult]:
		transcription = await self.ivrit.transcribe_file(path)
		summary = await self.summarizer.summarize(
			transcription.text, speaker_segments=transcription.speaker_segments
		)
		return transcription, summary

	# ---- Experiment Logic ----
	
	# Simple in-memory store for experiment results (since this is ephemeral/demo)
	# In production, use Redis.
	_experiments: dict[str, dict] = {}

	def _get_redis(self):
		import redis
		import os
		redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
		return redis.from_url(redis_url, decode_responses=True)

	async def run_comparison_experiment(self, experiment_id: str, audio_path: str) -> None:
		"""
		Run side-by-side comparison: Standard Whisper vs ZPE.
		Updates Redis state.
		"""
		import asyncio
		import json
		from agent_service.clients import WhisperXClient

		r = self._get_redis()
		
		initial_state = {
			"status": "processing",
			"progress_standard": 0,
			"progress_zpe": 0,
			"results": None,
			"sneak_peek": {"summary_text": "מעבד סיכום..."},  # Placeholder for immediate UI feedback
			"audio_path": audio_path # Persist audio path for later conversion
		}
		
		# Save initial state to Redis (24h TTL)
		r.setex(f"experiment:{experiment_id}", 86400, json.dumps(initial_state, ensure_ascii=False))

		try:
			# Define sub-tasks
			async def run_standard():
				try:
					# Standard client
					whisperx = WhisperXClient(self.settings)
					# WhisperXClient needs bytes
					with open(audio_path, "rb") as f:
						audio_bytes = f.read()
					res = await whisperx.transcribe(audio_bytes=audio_bytes)
					return res
				except Exception as e:
					print(f"Standard model failed: {e}")
					return None

			async def run_zpe():
				try:
					# Use IvritClient (ZPE)
					res = await self.ivrit.transcribe_file(audio_path)
					return res
				except Exception as e:
					print(f"ZPE model failed: {e}")
					return None

			# Run both in parallel
			standard_res, zpe_res = await asyncio.gather(run_standard(), run_zpe())
			
			# Generate Sneak Peek Summary (from ZPE text if available)
			sneak_peek_summary = SummaryResult(text="No summary available", raw={})
			zpe_segments_flat = []
			full_text = ""
			speaker_segments = []
			
			if zpe_res:
				# Format ZPE segments for frontend 
				# Format ZPE segments for frontend 
				zpe_segments_flat = []
				for s in (zpe_res.segments if not isinstance(zpe_res, dict) else zpe_res.get("segments", [])):
					if isinstance(s, dict):
						zpe_segments_flat.append({
							"speaker": s.get("speaker"),
							"text": s.get("text"),
							"start": s.get("start"),
							"end": s.get("end")
						})
					else:
						zpe_segments_flat.append({
							"speaker": getattr(s, "speaker", None),
							"text": getattr(s, "text", ""),
							"start": getattr(s, "start", 0),
							"end": getattr(s, "end", 0)
						})

				full_text = zpe_res.get("text", "") if isinstance(zpe_res, dict) else getattr(zpe_res, "text", "")
				speaker_segments = zpe_res.get("speaker_segments", []) if isinstance(zpe_res, dict) else getattr(zpe_res, "speaker_segments", [])
				
				try:
					# Use existing summarizer
					sneak_peek_summary = await self.summarizer.summarize(full_text, speaker_segments=speaker_segments)
				except Exception as e:
					print(f"Summary failed: {e}")

			# Extract summary text safely from various possible formats
			summary_text = ""
			if sneak_peek_summary.raw and isinstance(sneak_peek_summary.raw, dict):
				raw = sneak_peek_summary.raw
				# Check for Grok/MCP nested format
				# The user's pasted text implies we should extract it here
				if "content" in raw and isinstance(raw["content"], dict):
					summary_text = raw["content"].get("executive_summary", "")
				
				if not summary_text:
					summary_text = raw.get("executive_summary", "") or raw.get("meeting_summary", "") or raw.get("summary", "")
			
			if not summary_text:
				summary_text = sneak_peek_summary.text or "סיכום טרם זמין..."

			# Prepare Final Result State
			standard_segments = []
			if standard_res and isinstance(standard_res, dict):
				standard_segments = standard_res.get("segments", [])
				# Ensure segments are in expected format if needed, but dict is consistent with what we need mostly
				# Standard segments in WhisperX client return dicts: {start, end, text, speaker...}
			
			standard_text = STANDARD_ERROR_MSG = "Error or Timeout"
			if standard_res and isinstance(standard_res, dict):
				standard_text = standard_res.get("text", "")

			final_state = {
				"status": "completed",
				"progress_standard": 100,
				"progress_zpe": 100,
				"audio_path": audio_path,
				"results": {
					"standard": {
						"text": standard_text,
						"segments": standard_segments
					},
					"zpe": {
						"text": full_text,
						"segments": zpe_segments_flat
					}
				},
				"sneak_peek": {
					"summary_text": summary_text
				}
			}

			# Update Redis
			r.setex(f"experiment:{experiment_id}", 86400, json.dumps(final_state, ensure_ascii=False))
			
		except Exception as e:
			print(f"Experiment failed: {e}")
			error_state = initial_state.copy()
			error_state["status"] = "failed"
			error_state["error"] = str(e)
			r.setex(f"experiment:{experiment_id}", 86400, json.dumps(error_state, ensure_ascii=False))

	async def get_experiment_status(self, experiment_id: str) -> dict | None:
		"""Get experiment status from Redis."""
		import json
		try:
			r = self._get_redis()
			data = r.get(f"experiment:{experiment_id}")
			if data:
				return json.loads(data)
			return None
		except Exception as e:
			print(f"Redis get failed: {e}")
			return None

	async def generate_experiment_pdf(self, experiment_id: str) -> bytes | None:
		"""
		Generate a PDF for the ZPE transcription results of an experiment.
		Uses WeasyPrint for HTML-to-PDF conversion.
		"""
		experiment = await self.get_experiment_status(experiment_id)
		
		if not experiment or experiment.get("status") != "completed":
			return None
		
		zpe_results = experiment.get("results", {}).get("zpe", {})
		segments = zpe_results.get("segments", [])
		transcript_text = zpe_results.get("transcript", "")
		
		# Generate HTML
		html_content = f"""
		<!DOCTYPE html>
		<html dir="rtl" lang="he">
		<head>
			<meta charset="UTF-8">
			<style>
				body {{ font-family: 'Arial', sans-serif; padding: 40px; color: #333; }}
				.header {{ text-align: center; margin-bottom: 40px; border-bottom: 2px solid #14B8A6; padding-bottom: 20px; }}
				.logo {{ font-size: 24px; font-weight: bold; color: #14B8A6; }}
				.title {{ font-size: 18px; margin-top: 10px; }}
				<div>ID: {experiment_id}</div>
				.segment {{ margin-bottom: 20px; page-break-inside: avoid; }}
				.speaker {{ font-weight: bold; color: #14B8A6; margin-bottom: 5px; }}
				.text {{ line-height: 1.6; font-size: 14px; }}
				.footer {{ margin-top: 50px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 20px; }}
			</style>
		</head>
		<body>
			<div class="header">
				<div class="logo">IvriMeet ZPE</div>
				<div class="title">תמליל שיחה (זיהוי דוברים מתקדם)</div>
				<div>ID: {experiment_id}</div>
			</div>
			
			<div class="content">
		"""
		
		if segments:
			for seg in segments:
				speaker = seg.get("speaker", "Unknown") or "Unknown"
				text = seg.get("text", "")
				html_content += f"""
				<div class="segment">
					<div class="speaker">{speaker}</div>
					<div class="text">{text}</div>
				</div>
				"""
		else:
			html_content += f"<div class='text'>{transcript_text}</div>"
			
		html_content += """
			</div>
			<div class="footer">
				Generated by IvriMeet ZPE-2025 • www.ivreetmeet.com
			</div>
		</body>
		</html>
		"""
		
		# Generate PDF
		try:
			from weasyprint import HTML
			pdf_bytes = HTML(string=html_content).write_pdf()
			return pdf_bytes
		except Exception as e:
			print(f"Error generating PDF: {e}")
			return None
