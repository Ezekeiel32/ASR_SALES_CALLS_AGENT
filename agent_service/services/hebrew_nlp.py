from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class HebrewNLP:
	"""
	Service for Hebrew natural language processing.

	Provides utilities for Hebrew text processing, including name extraction,
	self-introduction detection, and context analysis. Uses pattern matching
	and simple NLP techniques optimized for Hebrew conversational text.
	"""

	def __init__(self) -> None:
		"""Initialize the Hebrew NLP service."""
		# Common Hebrew self-introduction patterns
		# Patterns that typically precede a name mention
		self.introduction_patterns = [
			r"שלום[,\s]+אני\s+([א-ת\s]+)",
			r"שלום[,\s]+קוראים\s+לי\s+([א-ת\s]+)",
			r"אני\s+([א-ת\s]+)",
			r"קוראים\s+לי\s+([א-ת\s]+)",
			r"השם\s+שלי\s+([א-ת\s]+)",
			r"שמי\s+([א-ת\s]+)",
			r"אני\s+([א-ת]+)\s+(?:ו|או)\s+(?:אני|זה)",
			r"זה\s+([א-ת\s]+)",
		]

		# Common Hebrew names (first names only, for validation)
		# This is a basic list - could be expanded with a proper Hebrew name database
		self.common_hebrew_names = {
			"דנה", "יוסי", "יעל", "אבי", "מיכל", "רונן", "חן", "גל", "עמית", "דור",
			"ליאור", "רועי", "נועה", "אור", "תומר", "שרון", "טל", "אלה", "תמיר",
			"רותם", "עומר", "נעמה", "עידו", "שירה", "איל", "אילן", "רינת", "אלון",
		}

	def extract_names_from_text(self, text: str) -> list[dict[str, Any]]:
		"""
		Extract potential Hebrew names from text.

		Args:
			text: Hebrew text to analyze

		Returns:
			List of dictionaries with keys:
			- 'name': Extracted name candidate
			- 'confidence': Confidence score (0.0-1.0)
			- 'context': Surrounding text context
			- 'pattern_match': Which pattern matched
		"""
		if not text or not text.strip():
			return []

		name_candidates: list[dict[str, Any]] = []

		# Try each introduction pattern
		for pattern in self.introduction_patterns:
			matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)
			for match in matches:
				name = match.group(1).strip()

				# Clean up name (remove common words, punctuation)
				name = self._clean_name(name)

				if not name or len(name) < 2:
					continue

				# Calculate confidence based on pattern and name validation
				confidence = self._calculate_name_confidence(name, pattern)

				# Get context (50 chars before and after)
				start = max(0, match.start() - 50)
				end = min(len(text), match.end() + 50)
				context = text[start:end]

				name_candidates.append(
					{
						"name": name,
						"confidence": confidence,
						"context": context,
						"pattern_match": pattern,
					}
				)

		# Deduplicate and sort by confidence
		seen_names: set[str] = set()
		unique_candidates: list[dict[str, Any]] = []
		for candidate in sorted(name_candidates, key=lambda x: x["confidence"], reverse=True):
			name_lower = candidate["name"].lower()
			if name_lower not in seen_names:
				seen_names.add(name_lower)
				unique_candidates.append(candidate)

		logger.debug(f"Extracted {len(unique_candidates)} name candidates from text")
		return unique_candidates

	def _clean_name(self, name: str) -> str:
		"""Clean and normalize a name string."""
		# Remove common Hebrew particles and conjunctions
		name = re.sub(r"\b(?:של|את|ה|ו|או|זה|זהו)\b", "", name, flags=re.UNICODE)
		name = re.sub(r"[,\-\.;:]", " ", name)
		name = re.sub(r"\s+", " ", name).strip()

		# Remove leading/trailing common words
		stop_words = ["זה", "אני", "הוא", "היא", "אנחנו", "אתם"]
		words = name.split()
		while words and words[0] in stop_words:
			words.pop(0)
		while words and words[-1] in stop_words:
			words.pop()

		return " ".join(words).strip()

	def _calculate_name_confidence(self, name: str, pattern: str) -> float:
		"""Calculate confidence score for a name candidate."""
		confidence = 0.5  # Base confidence

		# Boost confidence for common names
		if name.split()[0] in self.common_hebrew_names:
			confidence += 0.2

		# Boost for certain patterns (more reliable)
		if "קוראים לי" in pattern or "השם שלי" in pattern or "שמי" in pattern:
			confidence += 0.15

		# Penalize very long names (likely not a single name)
		if len(name) > 20:
			confidence -= 0.2

		# Penalize names with numbers or special characters
		if re.search(r"[0-9@#$%^&*()]", name):
			confidence -= 0.3

		# Check if name contains only Hebrew letters
		if re.match(r"^[א-ת\s]+$", name):
			confidence += 0.1

		return max(0.0, min(1.0, confidence))

	def is_self_introduction(self, text: str) -> bool:
		"""
		Check if text contains a self-introduction.

		Args:
			text: Text to check

		Returns:
			True if text appears to contain a self-introduction
		"""
		text_lower = text.lower()
		intro_keywords = [
			"שלום",
			"אני",
			"קוראים לי",
			"השם שלי",
			"שמי",
		]
		return any(keyword in text_lower for keyword in intro_keywords)

	def extract_names_near_timestamp(
		self,
		transcript_segments: list[dict[str, Any]],
		timestamp: float,
		time_window: float = 10.0,
	) -> list[dict[str, Any]]:
		"""
		Extract names mentioned near a specific timestamp.

		Useful for associating names with speaker segments based on temporal proximity.

		Args:
			transcript_segments: List of transcript segments with 'start', 'end', 'text'
			timestamp: Target timestamp in seconds
			time_window: Window size in seconds (default 10.0)

		Returns:
			List of name candidates with temporal context
		"""
		candidates: list[dict[str, Any]] = []

		for seg in transcript_segments:
			seg_start = float(seg.get("start", 0))
			seg_end = float(seg.get("end", seg_start))
			text = seg.get("text", "")

			# Check if segment is within time window
			if abs(seg_start - timestamp) <= time_window or abs(seg_end - timestamp) <= time_window:
				names = self.extract_names_from_text(text)
				for name_info in names:
					candidates.append(
						{
							**name_info,
							"segment_start": seg_start,
							"segment_end": seg_end,
							"distance_from_timestamp": min(
								abs(seg_start - timestamp), abs(seg_end - timestamp)
							),
						}
					)

		# Sort by distance from timestamp (closer = higher relevance)
		candidates.sort(key=lambda x: x.get("distance_from_timestamp", float("inf")))

		return candidates

