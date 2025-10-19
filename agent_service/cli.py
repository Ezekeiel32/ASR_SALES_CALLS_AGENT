from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from agent_service.service import AgentService


def main() -> None:
	parser = argparse.ArgumentParser(description="Transcribe + summarize a local audio file")
	parser.add_argument("path", help="Path to the audio file to process")
	args = parser.parse_args()

	p = Path(args.path)
	if not p.exists() or not p.is_file():
		parser.error(f"File not found: {args.path}")

	async def _run() -> None:
		service = AgentService()
		transcription, summary = await service.process_audio_file(str(p))
		print("=== TRANSCRIPT ===")
		print(transcription.text)
		print("\n=== SUMMARY ===")
		print(summary.text)

	asyncio.run(_run())


if __name__ == "__main__":
	main()

