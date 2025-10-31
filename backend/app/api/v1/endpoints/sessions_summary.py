from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.session import Session, SessionStatus

router = APIRouter()

@router.get("/summary")
async def sessions_summary(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    # Active sessions
    active_stmt = select(func.count()).where(Session.status.in_([
        SessionStatus.INITIALIZING,
        SessionStatus.PLANNING,
        SessionStatus.EXECUTING,
        SessionStatus.VALIDATING
    ]))
    active_count = (await db.execute(active_stmt)).scalar() or 0

    # Average duration (completed in last 24h)
    # Use stored duration_seconds if available, else compute from timestamps
    completed_stmt = select(
        func.avg(
            func.extract('epoch', Session.completed_at) - func.extract('epoch', Session.started_at)
        )
    ).where(and_(
        Session.status == SessionStatus.COMPLETED,
        Session.completed_at.isnot(None),
        Session.started_at.isnot(None),
        Session.completed_at >= last_24h
    ))
    avg_duration_seconds = (await db.execute(completed_stmt)).scalar()
    avg_duration_seconds = int(avg_duration_seconds) if avg_duration_seconds is not None else 0

    return {
        "active_count": active_count,
        "avg_duration_seconds_24h": avg_duration_seconds
    }
