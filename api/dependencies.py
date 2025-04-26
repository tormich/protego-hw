"""
Dependencies for FastAPI application.
"""
from typing import Generator

from settings import SessionLocal


def get_db() -> Generator:
    """
    Get database session.
    
    Yields:
        SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
