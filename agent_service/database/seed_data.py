"""Helper functions to seed initial data or get/create default resources."""

from __future__ import annotations

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from agent_service.database.models import Organization, User


def get_or_create_default_organization(db: Session) -> Organization:
	"""
	Get or create the default organization.
	This fixes the "Organization not found" error.
	"""
	default_org_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
	
	# Try to get existing organization
	org = db.get(Organization, default_org_id)
	
	if not org:
		# Create default organization
		org = Organization(
			id=default_org_id,
			name="Default Organization",
			subscription_plan="free",
		)
		db.add(org)
		db.commit()
		db.refresh(org)
	
	return org


def ensure_default_organization_exists(db: Session) -> bool:
	"""
	Ensure default organization exists, return True if created, False if already existed.
	"""
	default_org_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
	org = db.get(Organization, default_org_id)
	
	if not org:
		org = Organization(
			id=default_org_id,
			name="Default Organization",
			subscription_plan="free",
		)
		db.add(org)
		db.commit()
		return True
	
	return False

