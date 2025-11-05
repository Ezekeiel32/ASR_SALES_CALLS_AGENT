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

	# Database
	# Supports Neon, Railway, or any PostgreSQL via DATABASE_URL
	database_url: str = Field(
		default="postgresql://postgres:postgres@localhost:5432/hebrew_meetings",
		validation_alias="DATABASE_URL",  # Neon/Railway/Koyeb sets this automatically
		description="PostgreSQL connection string (Neon format: postgresql://user:pass@host.neon.tech/dbname?sslmode=require)"
	)
	
	# Redis (for Celery)
	# Railway provides REDIS_URL automatically
	redis_url: str | None = Field(
		default=None,
		validation_alias="REDIS_URL",
	)

	# Storage (S3)
	s3_bucket: str | None = None
	s3_region: str = Field(default="us-east-1")
	aws_access_key_id: str | None = None
	aws_secret_access_key: str | None = None

	# PyAnnote
	pyannote_model: str = Field(default="pyannote/speaker-diarization-3.1")
	pyannote_auth_token: str | None = None

	# CORS
	cors_origins: str | None = Field(
		default=None,
		description="Comma-separated list of allowed CORS origins. Defaults to localhost origins + production domain."
	)

	# App
	request_timeout_seconds: float = Field(default=120)
	log_level: str = Field(default="INFO")

	# XG Agent (LangGraph/XGBoost)
	gmail_credentials_path: str | None = Field(default=None, description="Path to Gmail OAuth credentials JSON file (for OAuth client config only)")
	gmail_client_id: str | None = Field(default=None, description="Gmail OAuth client ID (from Google Cloud Console)")
	gmail_client_secret: str | None = Field(default=None, description="Gmail OAuth client secret (from Google Cloud Console)")
	gmail_redirect_uri: str | None = Field(default=None, description="Gmail OAuth redirect URI (auto-detected if not set)")
	xgboost_n_estimators: int = Field(default=100, description="Number of XGBoost estimators")
	xgboost_learning_rate: float = Field(default=0.1, description="XGBoost learning rate")
	xgboost_max_depth: int = Field(default=3, description="XGBoost max depth")
	xgboost_random_state: int = Field(default=42, description="XGBoost random state")

	# LangSmith (optional - for LangGraph Studio tracing)
	langsmith_api_key: str | None = Field(default=None, description="LangSmith API key for tracing and debugging")

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings()  # type: ignore[call-arg]


class TranscriptionResult(BaseModel):
	text: str
	raw: dict[str, Any] | None = None
	segments: list[dict[str, Any]] | None = None
	speaker_labels: list[str] | None = None  # Unique speaker labels found (e.g., ['SPK_1', 'SPK_2'])
	speaker_segments: list[dict[str, Any]] | None = None  # Segments grouped by speaker

