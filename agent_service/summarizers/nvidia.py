from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from agent_service.config import Settings, get_settings
from agent_service.summarizers.base import SummaryResult, Summarizer


SYSTEM_PROMPT = (
	"You are a bilingual medical sales assistant. Summarize the call in concise bullet points, "
	"highlight products, objections, next steps, commitments, dates. Redact any PHI (names, IDs)."
)


class NvidiaDeepSeekSummarizer(Summarizer):
	def __init__(self, settings: Settings | None = None) -> None:
		self.settings = settings or get_settings()
		if not self.settings.nvidia_api_key:
			raise RuntimeError("NVIDIA API key not configured. Set NVIDIA_API_KEY.")
		self.client = AsyncOpenAI(base_url=self.settings.nvidia_api_url, api_key=self.settings.nvidia_api_key)

	async def summarize(self, transcript: str) -> SummaryResult:
		s = self.settings
		messages: list[dict[str, str]] = [
			{"role": "system", "content": SYSTEM_PROMPT},
			{
				"role": "user",
				"content": (
					"Summarize the following Hebrew medical sales call transcript. Keep quotes in original language, "
					"use clear English for the summary, and structure with bullets and 'Next steps'.\n\n" + transcript
				),
			},
		]

		if s.nvidia_stream:
			# Stream and accumulate content
			summary_text_parts: list[str] = []
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
				delta = getattr(chunk.choices[0], "delta", None)
				if delta is None:
					continue
				content = getattr(delta, "content", None)
				if content:
					summary_text_parts.append(content)
			return SummaryResult(text="".join(summary_text_parts), raw=None)

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

