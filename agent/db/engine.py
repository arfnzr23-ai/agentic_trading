"""
Database Engine

SQLModel/SQLAlchemy engine setup with async support.
"""

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os

from ..config import get_config


def get_sync_engine():
    """Get synchronous database engine."""
    cfg = get_config()
    db_url = cfg.database_url
    
    # Convert sqlite to sqlite+aiosqlite for async if needed
    return create_engine(db_url, echo=False)


def get_async_engine():
    """Get async database engine."""
    cfg = get_config()
    db_url = cfg.database_url
    
    # Convert sqlite:// to sqlite+aiosqlite://
    if db_url.startswith("sqlite://"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    
    return create_async_engine(db_url, echo=False)


def create_tables():
    """Create all database tables."""
    from .models import ALL_MODELS  # noqa: F401
    
    engine = get_sync_engine()
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    """Get a synchronous database session."""
    engine = get_sync_engine()
    with Session(engine) as session:
        yield session


# Async session factory
async_session_factory = None


def get_async_session_factory():
    """Get async session factory (lazy init)."""
    global async_session_factory
    if async_session_factory is None:
        engine = get_async_engine()
        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return async_session_factory


async def get_async_session():
    """Get an async database session."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session
