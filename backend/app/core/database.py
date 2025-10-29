"""
AutoCodit Agent - Database Configuration

SQLAlchemy async database setup with connection pooling,
health checks, and migration support.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Database metadata and base
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Global variables for database connections
async_engine = None
Async_SessionLocal = None
sync_engine = None  # For migrations


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.async_engine = None
        self.session_factory = None
        self.sync_engine = None
    
    async def connect(self) -> None:
        """Initialize database connections"""
        settings = get_settings()
        
        # Create async engine
        self.async_engine = create_async_engine(
            settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.DEBUG,
            future=True,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create sync engine for migrations
        self.sync_engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            poolclass=NullPool,
        )
        
        # Test connection
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Database connection closed")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute(self, query: str, params: dict = None):
        """Execute raw SQL query"""
        async with self.async_engine.begin() as conn:
            result = await conn.execute(text(query), params or {})
            return result
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            await self.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# Global database instance
database = Database()


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session"""
    async for session in database.get_session():
        yield session