"""
db.py — SQLite engine setup and session dependency.
"""

import os
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/patients.db")

# Extract the file path from the URL to ensure the directory exists
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    # Handle both relative and absolute paths
    if db_path.startswith("/"):
        db_file = Path(db_path)
    else:
        db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

# connect_args is SQLite-specific: allows multi-threaded access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set True for SQL debug logs
)


def create_all_tables() -> None:
    """Create all tables defined in SQLModel metadata. Safe to call on every startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: yields a database session and closes it after the request."""
    with Session(engine) as session:
        yield session
