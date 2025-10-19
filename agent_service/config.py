from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	# Ivrit.ai
	ivrit_api_url: str = Field(default="https://api.ivrit.ai")
	ivrit_api_key: str | None = None
	ivrit_transcribe_path: str = Field(default="/v1/transcribe")
	ivrit_file_field: str = Field(default="file")
	ivrit_language: str = Field(default="he")
	ivrit_auth_header: str = Field(default="Authorization")
	ivrit_use_bearer: bool = Field(default=True)
	ivrit_additional_params: dict[str, Any] | None = None

	# Ivrit via RunPod Serverless (optional)
	ivrit_runpod_base_url: str = Field(default="https://api.runpod.ai/v2")
	ivrit_runpod_endpoint_id: str | None = None
	ivrit_runpod_mode: str = Field(default="runsync")  # "runsync" or "run"
	ivrit_runpod_status_poll_interval_seconds: float = Field(default=2.0)
	ivrit_input_audio_field: str = Field(default="audio")
	ivrit_input_language_field: str = Field(default="language")
	ivrit_input_filename_field: str = Field(default="filename")
	ivrit_transcribe_args_field: str | None = Field(default="transcribe_args")
	ivrit_model: str | None = None
	ivrit_return_segments: bool = Field(default=True)

	# Summarizer (NVIDIA DeepSeek only)
	summarizer_provider: str = Field(default="nvidia")
	nvidia_api_url: str = Field(default="https://integrate.api.nvidia.com/v1")
	nvidia_api_key: str | None = None
	nvidia_model: str = Field(default="deepseek-ai/deepseek-v3.1-terminus")
	nvidia_temperature: float = Field(default=0.2)
	nvidia_top_p: float = Field(default=0.7)
	nvidia_max_tokens: int = Field(default=8192)
	nvidia_enable_thinking: bool = Field(default=True)
	nvidia_stream: bool = Field(default=False)

	# App
	request_timeout_seconds: float = Field(default=120)
	log_level: str = Field(default="INFO")

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings()  # type: ignore[call-arg]


class TranscriptionResult(BaseModel):
	text: str
	raw: dict[str, Any] | None = None
	segments: list[dict[str, Any]] | None = None

