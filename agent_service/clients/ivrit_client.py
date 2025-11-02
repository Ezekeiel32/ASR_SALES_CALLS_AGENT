from __future__ import annotations

import asyncio
from typing import Any
import base64
import json
import asyncio

import httpx

from agent_service.config import Settings, TranscriptionResult, get_settings


class IvritTranscriptionError(Exception):
	pass


class IvritClient:
	def __init__(self, settings: Settings | None = None) -> None:
		self.settings = settings or get_settings()

	async def transcribe_file(self, file_path: str, language: str | None = None) -> TranscriptionResult:
		with open(file_path, "rb") as f:
			data = f.read()
			filename = file_path.split("/")[-1]
		return await self.transcribe_bytes(data=data, filename=filename, language=language)

	async def transcribe_bytes(self, data: bytes, filename: str = "audio.wav", language: str | None = None) -> TranscriptionResult:
		s = self.settings
		# Prefer RunPod if configured
		if s.ivrit_runpod_endpoint_id:
			return await self._transcribe_via_runpod(data=data, filename=filename, language=language)

		# Direct Ivrit endpoint
		url = _join_url(s.ivrit_api_url, s.ivrit_transcribe_path)
		headers: dict[str, str] = {}
		if s.ivrit_api_key:
			header_name = s.ivrit_auth_header or "Authorization"
			header_value = f"Bearer {s.ivrit_api_key}" if s.ivrit_use_bearer else s.ivrit_api_key
			headers[header_name] = header_value

		params: dict[str, Any] = {}
		if s.ivrit_language or language:
			params["language"] = language or s.ivrit_language
		if s.ivrit_additional_params:
			params.update(s.ivrit_additional_params)

		files = {s.ivrit_file_field: (filename, data)}
		async with httpx.AsyncClient(timeout=s.request_timeout_seconds) as client:
			resp = await client.post(url, headers=headers, params=params, files=files)
			if resp.status_code >= 400:
				raise IvritTranscriptionError(f"Ivrit API error {resp.status_code}: {resp.text}")
			payload = resp.json()
			text = _extract_text(payload)
			segments = payload.get("segments") if isinstance(payload, dict) else None
			speaker_labels, speaker_segments = _extract_speaker_info(segments)
			return TranscriptionResult(
				text=text,
				raw=payload if isinstance(payload, dict) else None,
				segments=segments,
				speaker_labels=speaker_labels,
				speaker_segments=speaker_segments,
			)

	async def _transcribe_via_runpod(self, data: bytes, filename: str, language: str | None) -> TranscriptionResult:
		s = self.settings
		endpoint = s.ivrit_runpod_endpoint_id
		if not endpoint:
			raise IvritTranscriptionError("RunPod endpoint ID not configured")
		base = s.ivrit_runpod_base_url.rstrip("/")
		mode = (s.ivrit_runpod_mode or "runsync").lower()
		if mode not in ("runsync", "run"):
			raise IvritTranscriptionError(f"Unsupported RunPod mode: {s.ivrit_runpod_mode}")

		url = f"{base}/{endpoint}/{mode}"
		headers = {
			"Authorization": f"Bearer {s.ivrit_api_key}" if s.ivrit_use_bearer and s.ivrit_api_key else (s.ivrit_api_key or ""),
			"Content-Type": "application/json",
		}
		
		# For large files (>50MB), use URL instead of base64 to avoid request size limits
		# Estimate: base64 encoding increases size by ~33%, and JSON has overhead
		# So ~35MB raw file ≈ ~47MB base64, which is close to typical 50MB limits
		FILE_SIZE_THRESHOLD = 35 * 1024 * 1024  # 35MB
		
		input_payload: dict[str, Any] = {
			s.ivrit_input_language_field: language or s.ivrit_language,
			s.ivrit_input_filename_field: filename,
		}
		# Provide top-level model for templates that expect it
		if s.ivrit_model:
			input_payload["model"] = s.ivrit_model
		# Some templates expect arguments under `transcribe_args`
		if s.ivrit_transcribe_args_field:
			args: dict[str, Any] = {}
			
			# Use URL for large files, blob for small files
			if len(data) > FILE_SIZE_THRESHOLD:
				# For large files, upload to S3 and use URL (if S3 configured)
				# Otherwise, we'll need to fail gracefully or use a temp URL service
				import boto3
				from botocore.exceptions import ClientError
				from agent_service.config import get_settings as get_global_settings
				global_settings = get_global_settings()
				
				if global_settings.s3_bucket:
					try:
						# Upload to S3 temporarily - use explicit credentials from settings
						s3_client = boto3.client(
							"s3",
							region_name=global_settings.s3_region,
							aws_access_key_id=global_settings.aws_access_key_id,
							aws_secret_access_key=global_settings.aws_secret_access_key,
						)
						import uuid
						temp_key = f"temp-transcriptions/{uuid.uuid4()}/{filename}"
						s3_client.put_object(
							Bucket=global_settings.s3_bucket,
							Key=temp_key,
							Body=data,
							ContentType="audio/mpeg" if filename.endswith(".mp3") else "audio/wav",
						)
						# Generate presigned URL (valid for 1 hour)
						file_url = s3_client.generate_presigned_url(
							"get_object",
							Params={"Bucket": global_settings.s3_bucket, "Key": temp_key},
							ExpiresIn=3600,  # 1 hour
						)
						args["url"] = file_url
						import logging
						logger = logging.getLogger(__name__)
						logger.info(f"Large file uploaded to S3, using URL instead of base64 blob")
					except (ClientError, Exception) as e:
						# Fall back to base64 (will likely fail, but better than nothing)
						import logging
						logger = logging.getLogger(__name__)
						logger.warning(f"S3 upload failed for large file, falling back to base64: {e}")
						audio_b64 = base64.b64encode(data).decode("ascii")
						args["blob"] = audio_b64
				else:
					# No S3 configured - can't use URL, must use base64 (will likely fail)
					import logging
					logger = logging.getLogger(__name__)
					logger.error(
						f"Large file ({len(data)/(1024*1024):.1f}MB) exceeds threshold but S3 not configured. "
						f"Base64 encoding ({len(base64.b64encode(data).decode('ascii'))/(1024*1024):.1f}MB) may exceed RunPod limits."
					)
					audio_b64 = base64.b64encode(data).decode("ascii")
					args["blob"] = audio_b64
			else:
				# Small files can use base64 blob
				audio_b64 = base64.b64encode(data).decode("ascii")
				args["blob"] = audio_b64
			if s.ivrit_model:
				args["model"] = s.ivrit_model
			# pass language and filename as part of args too for compatibility
			args["language"] = language or s.ivrit_language
			args["filename"] = filename
			args["segments"] = s.ivrit_return_segments
			input_payload[s.ivrit_transcribe_args_field] = args
		if s.ivrit_additional_params:
			# allow overriding nested args via dot-keys, but do not override top-level 'model' set from config
			for k, v in s.ivrit_additional_params.items():
				if s.ivrit_transcribe_args_field and k.startswith(f"{s.ivrit_transcribe_args_field}."):
					_, subkey = k.split(".", 1)
					input_payload.setdefault(s.ivrit_transcribe_args_field, {})[subkey] = v
				elif k in {"model", "language", "filename"}:
					# skip overriding critical keys
					continue
				else:
					input_payload[k] = v

		# Use longer timeout for RunPod (especially for large files)
		# Initial request should be quick, but status polling might take a while
		runpod_timeout = max(s.request_timeout_seconds, 900.0)  # At least 15 minutes for large files
		import logging
		logger = logging.getLogger(__name__)
		logger.info(f"RunPod request: POST {url} (timeout: {runpod_timeout}s)")
		async with httpx.AsyncClient(timeout=runpod_timeout) as client:
			logger.debug(f"RunPod payload keys: {list(input_payload.keys())}")
			resp = await client.post(url, headers=headers, json={"input": input_payload})
			if resp.status_code >= 400:
				error_msg = f"RunPod error {resp.status_code}: {resp.text}"
				logger.error(error_msg)
				logger.error(f"Request URL: {url}")
				logger.error(f"Request headers: {dict(headers)}")
				logger.error(f"Request payload structure: input keys = {list(input_payload.keys())}")
				raise IvritTranscriptionError(error_msg)
			payload = resp.json()

			# For runsync: sometimes returns IN_PROGRESS with an id → poll until done
			if mode == "runsync":
				status_value = payload.get("status") if isinstance(payload, dict) else None
				text = _extract_runpod_output_text(payload)
				segments = _extract_runpod_segments(payload)
				speaker_labels, speaker_segments = _extract_speaker_info(segments)
				if status_value in ("COMPLETED", "COMPLETED_WITH_ERRORS") and text:
					return TranscriptionResult(
						text=text,
						raw=payload if isinstance(payload, dict) else None,
						segments=segments,
						speaker_labels=speaker_labels,
						speaker_segments=speaker_segments,
					)
				# otherwise poll using id
				request_id = payload.get("id") if isinstance(payload, dict) else None
				if not request_id:
					raise IvritTranscriptionError(f"RunPod runsync did not complete and no id provided: {payload}")
				status_url = f"{base}/{endpoint}/status/{request_id}"
				while True:
					status_resp = await client.get(status_url, headers=headers)
					if status_resp.status_code >= 400:
						raise IvritTranscriptionError(f"RunPod status error {status_resp.status_code}: {status_resp.text}")
					status_payload = status_resp.json()
					state = status_payload.get("status") if isinstance(status_payload, dict) else None
					if state in ("COMPLETED", "COMPLETED_WITH_ERRORS"):
						text2 = _extract_runpod_output_text(status_payload)
						segments2 = _extract_runpod_segments(status_payload)
						speaker_labels2, speaker_segments2 = _extract_speaker_info(segments2)
						return TranscriptionResult(
							text=text2,
							raw=status_payload if isinstance(status_payload, dict) else None,
							segments=segments2,
							speaker_labels=speaker_labels2,
							speaker_segments=speaker_segments2,
						)
					if state in ("FAILED", "CANCELLED"):
						raise IvritTranscriptionError(f"RunPod job failed: {status_payload}")
					await asyncio.sleep(s.ivrit_runpod_status_poll_interval_seconds)

			# mode == "run" => poll /status until completed
			request_id = payload.get("id") if isinstance(payload, dict) else None
			if not request_id:
				raise IvritTranscriptionError(f"RunPod 'run' response missing id: {payload}")
			status_url = f"{base}/{endpoint}/status/{request_id}"
			while True:
				status_resp = await client.get(status_url, headers=headers)
				if status_resp.status_code >= 400:
					raise IvritTranscriptionError(f"RunPod status error {status_resp.status_code}: {status_resp.text}")
				status_payload = status_resp.json()
				state = status_payload.get("status") if isinstance(status_payload, dict) else None
				if state in ("COMPLETED", "COMPLETED_WITH_ERRORS"):
					text = _extract_runpod_output_text(status_payload)
					segments = _extract_runpod_segments(status_payload)
					speaker_labels, speaker_segments = _extract_speaker_info(segments)
					return TranscriptionResult(
						text=text,
						raw=status_payload if isinstance(status_payload, dict) else None,
						segments=segments,
						speaker_labels=speaker_labels,
						speaker_segments=speaker_segments,
					)
				if state in ("FAILED", "CANCELLED"):
					raise IvritTranscriptionError(f"RunPod job failed: {status_payload}")
				# Log progress for long-running jobs
				if state == "IN_PROGRESS" or state == "IN_QUEUE":
					logger.info(f"RunPod job {request_id} status: {state}, continuing to poll...")
				await asyncio.sleep(s.ivrit_runpod_status_poll_interval_seconds)


def _extract_text(payload: Any) -> str:
	if isinstance(payload, dict):
		for key in ("text", "transcript", "transcription"):
			if key in payload and isinstance(payload[key], str):
				return payload[key]
		# Common nested patterns
		data = payload.get("data") if isinstance(payload.get("data"), dict) else None
		if data:
			for key in ("text", "transcript", "transcription"):
				if key in data and isinstance(data[key], str):
					return data[key]
		# Fallback
		return str(payload)
	return str(payload)


def _extract_runpod_output_text(payload: Any) -> str:
	if isinstance(payload, dict):
		output = payload.get("output")
		# Common dict-shaped output
		if isinstance(output, dict):
			for key in ("text", "transcript", "transcription"):
				val = output.get(key)
				if isinstance(val, str):
					return val
				# Some templates use nested data
				data = output.get("data") if isinstance(output.get("data"), dict) else None
				if data:
					for key in ("text", "transcript", "transcription"):
						val = data.get(key)
						if isinstance(val, str):
							return val
		# Some RunPod templates return a list with an object containing 'result' which
		# is a list (sometimes list of lists) of segment dicts that each have 'text'
		if isinstance(output, list):
			for item in output:
				if not isinstance(item, dict):
					continue
				result_obj = item.get("result")
				if isinstance(result_obj, list):
					flat: list[dict[str, Any]] = []
					for sub in result_obj:
						if isinstance(sub, list):
							for seg in sub:
								if isinstance(seg, dict):
									flat.append(seg)
						elif isinstance(sub, dict):
							flat.append(sub)
					if flat:
						texts: list[str] = []
						for seg in flat:
							t = seg.get("text")
							if isinstance(t, str) and t.strip():
								texts.append(t.strip())
						if texts:
							return " ".join(texts)
	return _extract_text(payload)


def _extract_runpod_segments(payload: Any) -> list[dict[str, Any]] | None:
	if isinstance(payload, dict):
		output = payload.get("output")
		if isinstance(output, dict):
			segments = output.get("segments")
			if isinstance(segments, list):
				return [s for s in segments if isinstance(s, dict)]
		# Handle list-shaped outputs with 'result' nested arrays
		if isinstance(output, list):
			for item in output:
				if not isinstance(item, dict):
					continue
				result_obj = item.get("result")
				if isinstance(result_obj, list):
					flat: list[dict[str, Any]] = []
					for sub in result_obj:
						if isinstance(sub, list):
							for seg in sub:
								if isinstance(seg, dict):
									flat.append(seg)
						elif isinstance(sub, dict):
							flat.append(sub)
					if flat:
						return flat
	return None


def _extract_speaker_info(
	segments: list[dict[str, Any]] | None,
) -> tuple[list[str] | None, list[dict[str, Any]] | None]:
	"""
	Extract speaker labels from segments and group segments by speaker.

	Returns:
		tuple of (speaker_labels, speaker_segments)
		- speaker_labels: List of unique speaker labels found (e.g., ['SPK_1', 'SPK_2'])
		- speaker_segments: List of dicts with 'speaker' and 'segments' keys
	"""
	if not segments:
		return None, None

	speaker_label_set: set[str] = set()
	speaker_segments_map: dict[str, list[dict[str, Any]]] = {}

	for seg in segments:
		if not isinstance(seg, dict):
			continue

		# Try multiple possible speaker label fields
		speaker_label: str | None = None
		for key in ("speaker", "speaker_label", "speaker_id", "speaker_0", "speaker_1"):
			label = seg.get(key)
			if label is not None:
				if isinstance(label, str):
					speaker_label = label
				elif isinstance(label, (int, float)):
					# Convert numeric to string label
					speaker_label = f"SPK_{int(label)}"
				break

		# If no explicit speaker field, check for speaker in nested structure
		if not speaker_label:
			# Some formats have speaker in words array
			words = seg.get("words")
			if isinstance(words, list) and words:
				first_word = words[0] if isinstance(words[0], dict) else None
				if first_word:
					speaker_label = first_word.get("speaker") or first_word.get("speaker_label")

		# Default to SPK_0 if no speaker found
		if not speaker_label:
			speaker_label = "SPK_0"

		speaker_label_set.add(speaker_label)
		if speaker_label not in speaker_segments_map:
			speaker_segments_map[speaker_label] = []
		speaker_segments_map[speaker_label].append(seg)

	# Sort speaker labels for consistent ordering
	speaker_labels = sorted(list(speaker_label_set)) if speaker_label_set else None

	# Build speaker_segments structure
	speaker_segments: list[dict[str, Any]] = []
	for label in sorted(speaker_segments_map.keys()):
		speaker_segments.append(
			{
				"speaker": label,
				"segments": speaker_segments_map[label],
			}
		)

	return speaker_labels, speaker_segments if speaker_segments else None


def _join_url(base: str, path: str) -> str:
	if base.endswith("/"):
		base = base[:-1]
	if not path.startswith("/"):
		path = "/" + path
	return base + path

