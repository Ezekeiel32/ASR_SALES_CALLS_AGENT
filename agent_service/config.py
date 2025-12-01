from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field, model_validator
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

	# RunPod (General)
	runpod_api_key: str | None = Field(default=None, validation_alias="RUNPOD_API_KEY")

	# WhisperX via RunPod
	whisperx_endpoint_id: str | None = Field(default=None, validation_alias="WHISPERX_ENDPOINT_ID")

	# AWS S3 (for audio storage)
	aws_access_key_id: str | None = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
	aws_secret_access_key: str | None = Field(default=None, validation_alias="AWS_SECRET_ACCESS_KEY")
	aws_region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
	s3_bucket_name: str | None = Field(default=None, validation_alias="S3_BUCKET_NAME")

	# Summarizer settings
	# Primary: OpenRouter (Grok)
	summarizer_provider: str = Field(default="openrouter")
	
	# OpenRouter (Primary)
	openrouter_api_key: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
	openrouter_api_key0: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY0")
	openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
	openrouter_model: str = Field(default="x-ai/grok-4-fast")

	# Gemini API settings (For Embeddings ONLY)
	gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
	gemini_api_key0: str | None = Field(default=None, validation_alias="GEMINI_API_KEY0")

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
		default="redis://redis:6379/0",
		validation_alias="REDIS_URL",
	)

	# PyAnnote
	pyannote_model: str = Field(default="pyannote/speaker-diarization-3.1")
	pyannote_auth_token: str | None = None

	# CORS
	cors_origins: str | None = Field(
		default=None,
		description="Comma-separated list of allowed CORS origins. Defaults to localhost origins + production domain."
	)

	# App
	request_timeout_seconds: float = Field(default=300)  # 5 minutes for summarization (Gemini is faster)
	log_level: str = Field(default="INFO")
	jwt_secret_key: str = Field(
		default="dev-secret-key-change-me",
		validation_alias="JWT_SECRET_KEY",
		description="JWT signing key. Override in production via JWT_SECRET_KEY env var.",
	)

	@model_validator(mode="after")
	def _normalize_urls(self) -> "Settings":
		if self.redis_url is not None:
			cleaned = self.redis_url.strip()
			if not cleaned:
				self.redis_url = None
			elif not cleaned.startswith(("redis://", "rediss://")):
				self.redis_url = None
			else:
				# Fix for "Invalid SSL Certificate Requirements Flag: CERT_NONE"
				if cleaned.startswith("rediss://") and "ssl_cert_reqs" not in cleaned:
					if "?" in cleaned:
						cleaned += "&ssl_cert_reqs=none"
					else:
						cleaned += "?ssl_cert_reqs=none"
				self.redis_url = cleaned
		return self

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

	# Email / SMTP Settings
	smtp_server: str | None = Field(default=None, validation_alias="SMTP_SERVER")
	smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
	smtp_username: str | None = Field(default=None, validation_alias="SMTP_USERNAME")
	smtp_password: str | None = Field(default=None, validation_alias="SMTP_PASSWORD")
	smtp_from_email: str = Field(default="noreply@ivrimeet.ai", validation_alias="SMTP_FROM_EMAIL")
	smtp_from_name: str = Field(default="IvreetMeet AI", validation_alias="SMTP_FROM_NAME")

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

