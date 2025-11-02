from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from agent_service.config import Settings, get_settings
from agent_service.summarizers.base import SummaryResult, Summarizer


SYSTEM_PROMPT = (
	"You are an expert meeting analyst specializing in comprehensive, speaker-aware summaries. "
	"Your goal is to create detailed, useful, and concise summaries that clearly identify who said what. "
	"When speaker labels are provided, you MUST maintain speaker identity throughout the summary. "
	"Structure your summary based on the meeting context: "
	"- For business/formal meetings: Use structured sections (Participants, Agenda, Discussion, Decisions, Action Items). "
	"- For sales calls: Focus on products, objections, commitments, next steps with clear speaker attribution. "
	"- For informal discussions: Use a narrative flow with speaker attribution. "
	"Always be specific about which speaker made each point. Format should be context-aware and professional."
)


class NvidiaDeepSeekSummarizer(Summarizer):
	def __init__(self, settings: Settings | None = None) -> None:
		self.settings = settings or get_settings()
		if not self.settings.nvidia_api_key:
			raise RuntimeError("NVIDIA API key not configured. Set NVIDIA_API_KEY.")
		self.client = AsyncOpenAI(base_url=self.settings.nvidia_api_url, api_key=self.settings.nvidia_api_key)

	async def summarize(
		self, transcript: str, speaker_segments: list[dict[str, Any]] | None = None
	) -> SummaryResult:
		"""
		Summarize transcript with optional speaker awareness.

		Args:
			transcript: Full transcript text
			speaker_segments: Optional list of segments grouped by speaker with format:
				[{'speaker': 'SPK_1', 'segments': [{'start': 0.0, 'end': 2.5, 'text': '...'}, ...]}, ...]

		Returns:
			SummaryResult with speaker-aware summary
		"""
		s = self.settings

		# Format transcript with speaker labels if provided
		formatted_transcript = transcript
		if speaker_segments:
			formatted_transcript = self._format_speaker_labeled_transcript(speaker_segments)

		# Build context-aware prompt based on transcript content
		detected_languages = self._detect_languages(formatted_transcript)
		meeting_type = self._detect_meeting_type(formatted_transcript)
		
		user_prompt = self._build_user_prompt(
			formatted_transcript, 
			has_speakers=bool(speaker_segments and len(speaker_segments) > 1),
			meeting_type=meeting_type,
			detected_languages=detected_languages
		)

		messages: list[dict[str, str]] = [
			{"role": "system", "content": SYSTEM_PROMPT},
			{"role": "user", "content": user_prompt},
		]

		if s.nvidia_stream:
			# Stream and accumulate content with reasoning support
			summary_text_parts: list[str] = []
			reasoning_parts: list[str] = []
			resp = await self.client.chat.completions.create(
				model=s.nvidia_model,
				messages=messages,
				temperature=s.nvidia_temperature,
				top_p=s.nvidia_top_p,
				max_tokens=s.nvidia_max_tokens,
				extra_body={"chat_template_kwargs": {"thinking": s.nvidia_enable_thinking}},
				stream=True,
			)
			async for chunk in resp:  # type: ignore[attr-defined]
				if not chunk.choices or len(chunk.choices) == 0:
					continue
				delta = getattr(chunk.choices[0], "delta", None)
				if delta is None:
					continue
				# Extract reasoning content if available
				reasoning = getattr(delta, "reasoning_content", None)
				if reasoning:
					reasoning_parts.append(reasoning)
				# Extract regular content
				content = getattr(delta, "content", None)
				if content:
					summary_text_parts.append(content)
			# Combine reasoning and content if reasoning was captured
			full_text = "".join(summary_text_parts)
			if reasoning_parts and s.nvidia_enable_thinking:
				# Optionally prepend reasoning if enabled
				reasoning_text = "".join(reasoning_parts)
				# For now, just return content (reasoning can be logged separately)
			return SummaryResult(text=full_text, raw=None)

		# Non-streaming simple path
		resp = await self.client.chat.completions.create(
			model=s.nvidia_model,
			messages=messages,
			temperature=s.nvidia_temperature,
			top_p=s.nvidia_top_p,
			max_tokens=s.nvidia_max_tokens,
			extra_body={"chat_template_kwargs": {"thinking": s.nvidia_enable_thinking}},
		)
		data: Any = resp
		choice0 = resp.choices[0]
		message = getattr(choice0, "message", None)
		content = getattr(message, "content", None) if message is not None else None
		text = content if isinstance(content, str) else str(data)
		return SummaryResult(text=text, raw=None)

	def _format_speaker_labeled_transcript(self, speaker_segments: list[dict[str, Any]]) -> str:
		"""
		Format transcript segments with speaker labels for summarization.
		Preserves chronological order and includes timing information.

		Args:
			speaker_segments: List of dicts with 'speaker' and 'segments' keys

		Returns:
			Formatted transcript string with speaker labels in chronological order
		"""
		if not speaker_segments:
			return ""

		# Flatten all segments with their speakers and sort by start time
		all_segments: list[dict[str, Any]] = []
		for speaker_group in speaker_segments:
			speaker_label = speaker_group.get("speaker", "Unknown")
			segments = speaker_group.get("segments", [])
			
			for seg in segments:
				if not isinstance(seg, dict):
					continue
				all_segments.append({
					"speaker": speaker_label,
					"start": seg.get("start", 0),
					"end": seg.get("end", 0),
					"text": seg.get("text", "").strip(),
				})
		
		# Sort by start time
		all_segments.sort(key=lambda x: float(x.get("start", 0)))
		
		# Format in chronological order with speaker labels
		formatted_lines: list[str] = []
		for seg in all_segments:
			speaker_label = seg.get("speaker", "Unknown")
			text = seg.get("text", "").strip()
			start_time = seg.get("start", 0)
			
			if not text:
				continue
			
			# Use numeric speaker ID (SPK_1 -> Speaker 1)
			speaker_num = speaker_label.replace("SPK_", "") if speaker_label.startswith("SPK_") else speaker_label
			formatted_speaker = f"Speaker {speaker_num}"
			
			# Format with time for context
			time_str = self._format_time(float(start_time))
			formatted_lines.append(f"[{time_str}] {formatted_speaker}: {text}")

		return "\n".join(formatted_lines) if formatted_lines else ""
	
	def _format_time(self, seconds: float) -> str:
		"""Format seconds to MM:SS or HH:MM:SS format."""
		hours = int(seconds // 3600)
		minutes = int((seconds % 3600) // 60)
		secs = int(seconds % 60)
		if hours > 0:
			return f"{hours:02d}:{minutes:02d}:{secs:02d}"
		return f"{minutes:02d}:{secs:02d}"
	
	def _detect_languages(self, text: str) -> list[str]:
		"""Detect languages in the transcript."""
		languages = []
		# Simple heuristic: Hebrew has Unicode range U+0590-U+05FF
		if any('\u0590' <= char <= '\u05ff' for char in text):
			languages.append("Hebrew")
		if any(char.isascii() and char.isalpha() for char in text):
			languages.append("English")
		return languages or ["Unknown"]
	
	def _detect_meeting_type(self, text: str) -> str:
		"""Detect meeting type from transcript content."""
		text_lower = text.lower()
		
		# Council/Government meetings
		if any(word in text_lower for word in ["council", "mayor", "councillor", "bylaw", "municipality", "resolution"]):
			return "government_council"
		
		# Sales calls
		if any(word in text_lower for word in ["product", "price", "deal", "client", "sales", "contract", "quote"]):
			return "sales_call"
		
		# Medical/Sales
		if any(word in text_lower for word in ["patient", "doctor", "prescription", "treatment", "medical"]):
			return "medical_sales"
		
		# General business
		if any(word in text_lower for word in ["meeting", "agenda", "discussion", "decision", "action"]):
			return "business_meeting"
		
		return "general"
	
	def _build_user_prompt(
		self, 
		transcript: str, 
		has_speakers: bool, 
		meeting_type: str,
		detected_languages: list[str]
	) -> str:
		"""Build context-aware user prompt for summarization."""
		language_note = f"The transcript contains {', '.join(detected_languages)}." if detected_languages else ""
		
		if meeting_type == "government_council":
			base_prompt = (
				"Summarize the following council/government meeting transcript. "
				"Structure the summary as:\n"
				"1. Meeting Overview (date, participants, agenda)\n"
				"2. Key Discussion Points (organized by topic with speaker attribution)\n"
				"3. Decisions Made (with votes/motions if mentioned)\n"
				"4. Action Items (who is responsible for what, with deadlines if mentioned)\n"
				"5. Next Steps\n\n"
			)
		elif meeting_type == "sales_call" or meeting_type == "medical_sales":
			base_prompt = (
				"Summarize the following sales call transcript. "
				"Structure the summary as:\n"
				"1. Call Overview (participants, date, purpose)\n"
				"2. Products/Services Discussed (with speaker attribution)\n"
				"3. Objections and Responses (who raised what, how addressed)\n"
				"4. Commitments and Next Steps (specific actions, dates, responsible parties)\n"
				"5. Key Quotes (important statements in original language with speaker attribution)\n\n"
			)
		elif meeting_type == "business_meeting":
			base_prompt = (
				"Summarize the following business meeting transcript. "
				"Structure the summary with clear sections for:\n"
				"- Agenda Items Discussed\n"
				"- Key Decisions (with speaker attribution)\n"
				"- Action Items (who does what by when)\n"
				"- Important Discussion Points\n\n"
			)
		else:
			base_prompt = (
				"Summarize the following meeting transcript comprehensively. "
				"Organize by topics discussed, maintain speaker identity throughout, "
				"and include action items, decisions, and key points.\n\n"
			)
		
		speaker_instruction = ""
		if has_speakers:
			speaker_instruction = (
				"CRITICAL: This transcript contains multiple speakers. "
				"You MUST maintain speaker identity throughout the summary. "
				"For each point, clearly state which speaker made it (e.g., 'Speaker 1 stated...', "
				"'Speaker 2 responded...', 'According to Speaker 3...'). "
				"Do NOT merge statements from different speakers. "
				"Speaker attribution is essential for understanding the meeting dynamics.\n\n"
			)
		else:
			speaker_instruction = (
				"Note: This transcript may contain multiple speakers, but speaker labels are not clearly identified. "
				"Summarize the content while noting any apparent speaker changes when detectable.\n\n"
			)
		
		return (
			f"{base_prompt}"
			f"{speaker_instruction}"
			f"{language_note}\n" if language_note else ""
			f"Keep quotes in original language when relevant. Use clear English for the summary structure. "
			f"Be comprehensive, detailed, useful, and concise. Ensure every key point includes speaker attribution when available.\n\n"
			f"TRANSCRIPT:\n{transcript}"
		)

