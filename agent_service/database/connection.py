from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from agent_service.config import get_settings

settings = get_settings()

# Database URL from environment or default
DATABASE_URL = getattr(
	settings,
	"database_url",
	"postgresql://postgres:postgres@localhost:5432/hebrew_meetings",
)

engine: Engine = create_engine(
	DATABASE_URL,
	pool_pre_ping=True,
	pool_size=10,
	max_overflow=20,
	echo=False,  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def enable_pgvector_extension(dbapi_conn, connection_record):
	"""Enable pgvector extension on connection."""
	try:
		with dbapi_conn.cursor() as cursor:
			cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
			dbapi_conn.commit()
	except Exception:
		# Extension might already exist or not have permissions
		# This is OK, migrations will handle it
		pass


def get_db() -> Generator[Session, None, None]:
	"""
	Dependency for FastAPI to get database session.
	Usage:
		@app.get("/endpoint")
		async def endpoint(db: Session = Depends(get_db)):
			...
	"""
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
	"""
	Context manager for database sessions.
	Usage:
		with get_db_session() as db:
			db.query(Model).all()
	"""
	db = SessionLocal()
	try:
		yield db
		db.commit()
	except Exception:
		db.rollback()
		raise
	finally:
		db.close()


def init_db() -> None:
	"""
	Initialize database - create all tables.
	Should be called after running Alembic migrations in production.
	For development, can be used to create tables directly.
	"""
	from agent_service.database.models import Base  # noqa: F401

	# Enable pgvector extension
	with engine.connect() as conn:
		conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
		conn.commit()

	Base.metadata.create_all(bind=engine)

