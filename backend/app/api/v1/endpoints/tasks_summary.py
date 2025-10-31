from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.task import Task, TaskStatus
from app.models.session import Session, SessionStatus

router = APIRouter()

@router.get("/summary")
async def tasks_summary(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_30d = now - timedelta(days=30)

    # Active tasks
    active_stmt = select(func.count()).where(Task.status.in_([TaskStatus.RUNNING, TaskStatus.QUEUED]))
    active_count = (await db.execute(active_stmt)).scalar() or 0

    # Completed today
    completed_stmt = select(func.count()).where(
        and_(Task.status == TaskStatus.COMPLETED, Task.updated_at >= start_of_day)
    )
    completed_today = (await db.execute(completed_stmt)).scalar() or 0

    # Success rate last 30 days = completed / (completed+failed)
    completed_30_stmt = select(func.count()).where(
        and_(Task.status == TaskStatus.COMPLETED, Task.updated_at >= last_30d)
    )
    completed_30 = (await db.execute(completed_30_stmt)).scalar() or 0

    failed_30_stmt = select(func.count()).where(
        and_(Task.status == TaskStatus.FAILED, Task.updated_at >= last_30d)
    )
    failed_30 = (await db.execute(failed_30_stmt)).scalar() or 0

    denom = completed_30 + failed_30
    success_rate_30d = (completed_30 / denom * 100.0) if denom > 0 else 0.0

    # Placeholder for cost (could be computed from AI usage table if exists)
    cost_today = 0.0

    return {
        "active_count": active_count,
        "completed_today": completed_today,
        "success_rate_30d": round(success_rate_30d, 2),
        "cost_today": cost_today,
    }
