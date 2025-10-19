from __future__ import annotations

from typing import Literal

from agent_service.clients import IvritClient
from agent_service.config import Settings, TranscriptionResult, get_settings
from agent_service.summarizers.base import SummaryResult, Summarizer
from agent_service.summarizers.nvidia import NvidiaDeepSeekSummarizer


class AgentService:
	def __init__(self, settings: Settings | None = None) -> None:
		self.settings = settings or get_settings()
		self.ivrit = IvritClient(self.settings)
		self.summarizer = self._build_summarizer(provider=self.settings.summarizer_provider)

	def _build_summarizer(self, provider: str) -> Summarizer:
		if provider.lower() == "nvidia":
			return NvidiaDeepSeekSummarizer(self.settings)
		raise ValueError(f"Unsupported summarizer provider: {provider}")

	async def process_audio_bytes(self, data: bytes, filename: str = "audio.wav") -> tuple[TranscriptionResult, SummaryResult]:
		transcription = await self.ivrit.transcribe_bytes(data=data, filename=filename)
		summary = await self.summarizer.summarize(transcription.text)
		return transcription, summary

	async def process_audio_file(self, path: str) -> tuple[TranscriptionResult, SummaryResult]:
		transcription = await self.ivrit.transcribe_file(path)
		summary = await self.summarizer.summarize(transcription.text)
		return transcription, summary

