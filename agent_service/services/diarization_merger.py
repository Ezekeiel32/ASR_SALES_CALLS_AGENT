from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DiarizationMerger:
	"""
	Service for merging diarization results from multiple sources.

	Combines results from Ivrit.ai (primary) and PyAnnote (validation)
	to create a high-confidence speaker timeline. Uses temporal overlap
	analysis and confidence scoring to resolve discrepancies.
	"""

	def __init__(self, overlap_threshold: float = 0.5, confidence_penalty: float = 0.1) -> None:
		"""
		Initialize the diarization merger.

		Args:
			overlap_threshold: Minimum temporal overlap (0.0-1.0) required to consider segments matching
			confidence_penalty: Penalty applied to segments with low confidence or mismatches
		"""
		self.overlap_threshold = overlap_threshold
		self.confidence_penalty = confidence_penalty

	def merge(
		self,
		ivrit_segments: list[dict[str, Any]],
		pyannote_segments: list[dict[str, Any]] | None = None,
	) -> list[dict[str, Any]]:
		"""
		Merge diarization results from Ivrit.ai and PyAnnote.

		Args:
			ivrit_segments: Segments from Ivrit.ai (primary source, includes transcription)
			pyannote_segments: Segments from PyAnnote (validation source, optional)

		Returns:
			Merged list of segment dictionaries with:
			- 'start', 'end': time boundaries
			- 'speaker': merged speaker label
			- 'text': transcription text (from Ivrit)
			- 'confidence': merged confidence score
			- 'validation_status': 'validated', 'discrepancy', or 'unvalidated'
		"""
		if not ivrit_segments:
			logger.warning("No Ivrit segments provided, returning empty result")
			return []

		# If no PyAnnote segments, return Ivrit segments with validation status
		if not pyannote_segments:
			logger.info("No PyAnnote segments provided, using Ivrit segments only")
			return [
				{
					**seg,
					"validation_status": "unvalidated",
					"confidence": seg.get("confidence", 0.8),  # Default confidence
				}
				for seg in ivrit_segments
			]

		logger.info(
			f"Merging {len(ivrit_segments)} Ivrit segments with {len(pyannote_segments)} PyAnnote segments"
		)

		# Build speaker mapping between Ivrit and PyAnnote
		speaker_mapping = self._build_speaker_mapping(ivrit_segments, pyannote_segments)

		# Merge segments
		merged_segments: list[dict[str, Any]] = []

		for ivrit_seg in ivrit_segments:
			ivrit_start = float(ivrit_seg.get("start", 0))
			ivrit_end = float(ivrit_seg.get("end", ivrit_start))
			ivrit_speaker = ivrit_seg.get("speaker") or ivrit_seg.get("speaker_label") or "SPK_0"

			# Find overlapping PyAnnote segments
			overlapping_pyannote = [
				pseg
				for pseg in pyannote_segments
				if self._segments_overlap(
					ivrit_start,
					ivrit_end,
					float(pseg.get("start", 0)),
					float(pseg.get("end", 0)),
				)
			]

			if not overlapping_pyannote:
				# No overlap - use Ivrit segment as-is with lower confidence
				merged_segments.append(
					{
						**ivrit_seg,
						"speaker": ivrit_speaker,
						"validation_status": "unvalidated",
						"confidence": (ivrit_seg.get("confidence") or 0.8) - self.confidence_penalty,
					}
				)
				continue

			# Check if speakers agree
			pyannote_speakers = [
				pseg.get("speaker") or pseg.get("speaker_label")
				for pseg in overlapping_pyannote
			]
			most_common_pyannote = self._most_common_speaker(pyannote_speakers)

			# Map PyAnnote speaker to Ivrit speaker namespace
			mapped_pyannote_speaker = speaker_mapping.get(most_common_pyannote, ivrit_speaker)

			if mapped_pyannote_speaker == ivrit_speaker:
				# Agreement - validated segment with high confidence
				overlap_ratio = self._calculate_overlap_ratio(
					ivrit_start,
					ivrit_end,
					overlapping_pyannote,
				)
				merged_segments.append(
					{
						**ivrit_seg,
						"speaker": ivrit_speaker,
						"validation_status": "validated",
						"confidence": min(0.95, (ivrit_seg.get("confidence") or 0.8) + 0.1 * overlap_ratio),
					}
				)
			else:
				# Discrepancy - flag for review, use Ivrit speaker but lower confidence
				logger.warning(
					f"Speaker discrepancy at {ivrit_start:.2f}-{ivrit_end:.2f}: "
					f"Ivrit={ivrit_speaker}, PyAnnote={most_common_pyannote} (mapped={mapped_pyannote_speaker})"
				)
				merged_segments.append(
					{
						**ivrit_seg,
						"speaker": ivrit_speaker,  # Prefer Ivrit since it has transcription
						"validation_status": "discrepancy",
						"confidence": (ivrit_seg.get("confidence") or 0.8) - self.confidence_penalty,
						"alternative_speaker": mapped_pyannote_speaker,
					}
				)

		logger.info(f"Merged diarization completed: {len(merged_segments)} segments")
		return merged_segments

	def _build_speaker_mapping(
		self,
		ivrit_segments: list[dict[str, Any]],
		pyannote_segments: list[dict[str, Any]],
	) -> dict[str, str]:
		"""
		Build a mapping between PyAnnote speaker labels and Ivrit speaker labels.

		Uses temporal overlap to find which speakers correspond to each other.

		Args:
			ivrit_segments: Ivrit segments
			pyannote_segments: PyAnnote segments

		Returns:
			Dictionary mapping PyAnnote speaker labels to Ivrit speaker labels
		"""
		mapping: dict[str, str] = {}

		# Get unique speakers from each source
		ivrit_speakers = set()
		for seg in ivrit_segments:
			speaker = seg.get("speaker") or seg.get("speaker_label")
			if speaker:
				ivrit_speakers.add(speaker)

		pyannote_speakers = set()
		for seg in pyannote_segments:
			speaker = seg.get("speaker") or seg.get("speaker_label")
			if speaker:
				pyannote_speakers.add(speaker)

		# For each PyAnnote speaker, find the Ivrit speaker with most temporal overlap
		for pyannote_speaker in pyannote_speakers:
			pyannote_segs_for_speaker = [
				s for s in pyannote_segments
				if (s.get("speaker") or s.get("speaker_label")) == pyannote_speaker
			]

			best_ivrit_speaker: str | None = None
			max_overlap_time = 0.0

			for ivrit_speaker in ivrit_speakers:
				ivrit_segs_for_speaker = [
					s for s in ivrit_segments
					if (s.get("speaker") or s.get("speaker_label")) == ivrit_speaker
				]

				total_overlap = 0.0
				for ivrit_seg in ivrit_segs_for_speaker:
					ivrit_start = float(ivrit_seg.get("start", 0))
					ivrit_end = float(ivrit_seg.get("end", ivrit_start))

					for pyannote_seg in pyannote_segs_for_speaker:
						pyannote_start = float(pyannote_seg.get("start", 0))
						pyannote_end = float(pyannote_seg.get("end", pyannote_start))

						overlap = self._calculate_overlap(ivrit_start, ivrit_end, pyannote_start, pyannote_end)
						total_overlap += overlap

				if total_overlap > max_overlap_time:
					max_overlap_time = total_overlap
					best_ivrit_speaker = ivrit_speaker

			if best_ivrit_speaker:
				mapping[pyannote_speaker] = best_ivrit_speaker

		logger.info(f"Built speaker mapping: {mapping}")
		return mapping

	def _segments_overlap(self, start1: float, end1: float, start2: float, end2: float) -> bool:
		"""Check if two time segments overlap."""
		return not (end1 <= start2 or end2 <= start1)

	def _calculate_overlap(self, start1: float, end1: float, start2: float, end2: float) -> float:
		"""Calculate overlap duration between two segments."""
		if not self._segments_overlap(start1, end1, start2, end2):
			return 0.0
		overlap_start = max(start1, start2)
		overlap_end = min(end1, end2)
		return overlap_end - overlap_start

	def _calculate_overlap_ratio(
		self,
		start: float,
		end: float,
		overlapping_segments: list[dict[str, Any]],
	) -> float:
		"""Calculate what portion of the segment is covered by overlapping segments."""
		total_overlap = sum(
			self._calculate_overlap(start, end, float(s.get("start", 0)), float(s.get("end", 0)))
			for s in overlapping_segments
		)
		segment_duration = end - start
		return total_overlap / segment_duration if segment_duration > 0 else 0.0

	def _most_common_speaker(self, speakers: list[str]) -> str:
		"""Find the most common speaker in a list."""
		if not speakers:
			return "SPK_0"
		from collections import Counter

		counter = Counter(speakers)
		return counter.most_common(1)[0][0]

