"""Authentication utilities for JWT tokens and password hashing."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from agent_service.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")  # TODO: Use settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""Verify a plain password against a hashed password."""
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
	"""Hash a plain password."""
	return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
	"""
	Create a JWT access token.
	
	Args:
		data: Data to encode in token (typically {"sub": user_id, "org_id": organization_id})
		expires_delta: Optional custom expiration time
	
	Returns:
		Encoded JWT token string
	"""
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.now(timezone.utc) + expires_delta
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
	"""
	Decode and verify a JWT access token.
	
	Args:
		token: JWT token string
	
	Returns:
		Decoded token payload if valid, None otherwise
	"""
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		return payload
	except JWTError:
		return None

