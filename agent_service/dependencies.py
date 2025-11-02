"""FastAPI dependencies for authentication and database access."""

from __future__ import annotations

import uuid
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from agent_service.auth import decode_access_token
from agent_service.database import get_db
from agent_service.database.models import User, Organization


def get_current_user(
	authorization: str = Header(..., alias="Authorization"),
	db: Session = Depends(get_db),
) -> User:
	"""
	Get the current authenticated user from JWT token.
	
	Raises:
		HTTPException: If authentication fails or user not found
	"""
	if not authorization or not authorization.startswith("Bearer "):
		raise HTTPException(status_code=401, detail="Not authenticated")
	
	token = authorization.replace("Bearer ", "")
	payload = decode_access_token(token)
	
	if not payload:
		raise HTTPException(status_code=401, detail="Invalid or expired token")
	
	user_id = payload.get("sub")
	if not user_id:
		raise HTTPException(status_code=401, detail="Invalid token")
	
	# Get user from database
	user = db.get(User, uuid.UUID(user_id))
	if not user:
		raise HTTPException(status_code=401, detail="User not found")
	
	return user


def get_current_organization(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> Organization:
	"""
	Get the current user's organization.
	
	Raises:
		HTTPException: If organization not found
	"""
	org = db.get(Organization, current_user.organization_id)
	if not org:
		raise HTTPException(status_code=500, detail="User organization not found")
	
	return org

