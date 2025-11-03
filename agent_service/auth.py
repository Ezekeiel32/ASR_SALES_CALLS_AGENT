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
# Note: We're using bcrypt directly in our functions to avoid passlib initialization issues
# with newer bcrypt versions. This avoids AttributeError during passlib's bcrypt backend detection.

# JWT settings
# Get secret from environment or generate a default (NOT secure for production!)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
	import secrets
	SECRET_KEY = secrets.token_urlsafe(32)
	print(f"WARNING: JWT_SECRET_KEY not set, using auto-generated key: {SECRET_KEY[:20]}...")
	print("WARNING: This is NOT secure for production! Set JWT_SECRET_KEY environment variable.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""
	Verify a plain password against a hashed password.
	Handles both regular passwords and pre-hashed passwords (for >72 bytes).
	Uses bcrypt directly to avoid passlib initialization issues.
	"""
	import bcrypt as bcrypt_lib
	
	password_bytes = plain_password.encode('utf-8')
	hashed_bytes = hashed_password.encode('utf-8')
	
	# Try direct verification first
	try:
		if bcrypt_lib.checkpw(password_bytes, hashed_bytes):
			return True
	except Exception:
		pass
	
	# If password is >72 bytes, try pre-hashing with SHA256
	if len(password_bytes) > 72:
		import hashlib
		pre_hashed = hashlib.sha256(password_bytes).digest()  # 32 bytes raw digest
		try:
			return bcrypt_lib.checkpw(pre_hashed, hashed_bytes)
		except Exception:
			pass
	
	return False


def get_password_hash(password: str) -> str:
	"""
	Hash a plain password.
	Bcrypt has a 72-byte limit, so we pre-hash long passwords with SHA256.
	Uses bcrypt directly to avoid passlib initialization issues.
	"""
	import bcrypt as bcrypt_lib
	
	# Bcrypt has a 72-byte limit, so for longer passwords we pre-hash them
	# This is a common pattern to support longer passwords
	password_bytes = password.encode('utf-8')
	if len(password_bytes) > 72:
		import hashlib
		# Pre-hash with SHA256 to get a fixed 64-byte hex string (32 bytes when decoded)
		# But hexdigest is 64 chars, so we need to encode it as bytes
		pre_hashed = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
		# SHA256 hexdigest is 64 bytes, still > 72 bytes when encoded, so use raw digest
		pre_hashed = hashlib.sha256(password_bytes).digest()  # 32 bytes
		hashed = bcrypt_lib.hashpw(pre_hashed, bcrypt_lib.gensalt())
		return hashed.decode('utf-8')
	else:
		# Use bcrypt directly for short passwords
		hashed = bcrypt_lib.hashpw(password_bytes, bcrypt_lib.gensalt())
		return hashed.decode('utf-8')


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

