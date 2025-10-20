from __future__ import annotations

import argparse
import ast
from types import SimpleNamespace
import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_service.service import AgentService
from agent_service.clients.ivrit_client import (
	_extract_runpod_output_text,
	_extract_runpod_segments,
)


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
			text = " ".join([w.get("word", "") for w in seg.get("words") if isinstance(w, dict)])
		if not isinstance(text, str):
			text = ""
		lines.append(str(index))
		lines.append(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}")
		lines.append(text.strip())
		lines.append("")
		index += 1
	return "\n".join(lines).strip() + "\n"


def _extract_keypoints(markdown_text: str) -> list[str]:
	points: list[str] = []
	for line in markdown_text.splitlines():
		if re.match(r"^\s*([-*•—])\s+", line):
			points.append(re.sub(r"^\s*([-*•—])\s+", "", line).strip())
	return points[:10]


def _load_transcript_file(path: Path) -> tuple[str, list[dict[str, Any]] | None]:
	"""Load transcript text and segments from .json or .txt file.
	If JSON has no segments but contains a stringified RunPod payload, attempt to parse it.
	"""
	if path.suffix.lower() == ".json":
		data = json.loads(path.read_text(encoding="utf-8"))
		text_val = data.get("transcript", "")
		segments = data.get("segments") if isinstance(data, dict) else None
		# If segments are missing but transcript holds a stringified dict from RunPod, parse it
		if (not segments) and isinstance(text_val, str) and text_val.strip().startswith("{"):
			try:
				payload = ast.literal_eval(text_val)
				# Extract text + segments from payload using client helpers
				text_parsed = _extract_runpod_output_text(payload)
				segments_parsed = _extract_runpod_segments(payload)
				return text_parsed or "", segments_parsed
			except Exception:
				pass
		return (text_val if isinstance(text_val, str) else str(text_val)), (segments if isinstance(segments, list) else None)

	# Fallback: treat as plain text
	return path.read_text(encoding="utf-8"), None


def main() -> None:
	parser = argparse.ArgumentParser(description="Transcribe + summarize a local audio file")
	parser.add_argument("path", help="Path to the audio file to process")
	parser.add_argument("--write-files", "-w", action="store_true", help="Write transcript outputs (JSON/TXT/SRT)")
	parser.add_argument("--out-dir", help="Directory to write outputs (defaults to the audio file directory)")
	parser.add_argument("--variant", help="Optional variant suffix to append to filenames (e.g., v2)")
	parser.add_argument("--from-transcript", help="Reuse an existing transcript file (.json or .txt); skips transcription")
	args = parser.parse_args()

	p = Path(args.path)
	if not p.exists() or not p.is_file():
		parser.error(f"File not found: {args.path}")

	async def _run() -> None:
		service = AgentService()
		if args.from_transcript:
			# Summarization-only path using an existing transcript
			transcript_path = Path(args.from_transcript)
			if not transcript_path.exists():
				raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
			transcript_text, segments = _load_transcript_file(transcript_path)
			summary = await service.summarizer.summarize(transcript_text)
			print("=== TRANSCRIPT (reused) ===")
			print(transcript_text)
			print("\n=== SUMMARY ===")
			print(summary.text)
			# Minimal holder for writing
			transcription = SimpleNamespace(text=transcript_text, segments=segments)  # type: ignore[assignment]
		else:
			# Full pipeline: transcribe + summarize
			transcription, summary = await service.process_audio_file(str(p))
			print("=== TRANSCRIPT ===")
			print(transcription.text)
			print("\n=== SUMMARY ===")
			print(summary.text)

		if args.write_files:
			out_dir = Path(args.out_dir) if args.out_dir else p.parent
			out_dir.mkdir(parents=True, exist_ok=True)
			base = p.stem + (f".{args.variant}" if args.variant else "")
			# Prepare contents
			transcript_text = transcription.text or ""
			srt_text = _format_srt(transcription.segments)
			json_payload = {
				"transcript": transcript_text,
				"segments": transcription.segments,
				"sourceFile": str(p),
				"createdAt": datetime.now(timezone.utc).isoformat(),
			}
			# Write files
			(txt_path := out_dir / f"{base}.transcript.txt").write_text(transcript_text, encoding="utf-8")
			(json_path := out_dir / f"{base}.transcript.json").write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
			(srt_path := out_dir / f"{base}.captions.srt").write_text(srt_text, encoding="utf-8")

			# Analysis artifacts
			analysis_md = summary.text or ""
			analysis_txt = analysis_md
			analysis = {
				"sourceAudio": str(p),
				"transcriptFile": str(json_path),
				"summary": analysis_md,
				"keyPoints": _extract_keypoints(analysis_md),
				"actionItems": [],
				"entities": {},
				"sentiment": None,
				"topics": [],
				"confidence": None,
				"runId": f"nvidia-{uuid.uuid4()}",
				"createdAt": datetime.now(timezone.utc).isoformat(),
			}
			(md_path := out_dir / f"{base}.analysis.md").write_text(analysis_md, encoding="utf-8")
			(aj_path := out_dir / f"{base}.analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
			(at_path := out_dir / f"{base}.analysis.txt").write_text(analysis_txt, encoding="utf-8")

			print(f"\nWrote:\n- {txt_path}\n- {json_path}\n- {srt_path}\n- {md_path}\n- {aj_path}\n- {at_path}")

	asyncio.run(_run())


if __name__ == "__main__":
	main()

