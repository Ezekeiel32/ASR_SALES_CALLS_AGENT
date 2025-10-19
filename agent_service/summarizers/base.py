from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SummaryResult:
	text: str
	raw: dict[str, Any] | None = None


class Summarizer(ABC):
	@abstractmethod
	async def summarize(self, transcript: str) -> SummaryResult:  # pragma: no cover - interface
		...



