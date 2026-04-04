import logging
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

logger = logging.getLogger(__name__)

# Resolve to absolute path so SQLite doesn't care about cwd
_db_path = Path(settings.db_path).resolve()
_db_url = f"sqlite:///{_db_path}"

engine = create_engine(
    _db_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """Create all SQLModel tables if they don't already exist."""
    # Import models so SQLModel's metadata is populated before create_all
    import app.models  # noqa: F401

    logger.info("Initialising database at %s", _db_path)
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Return a new SQLModel session.  Callers must use 'with' or close manually."""
    return Session(engine)
