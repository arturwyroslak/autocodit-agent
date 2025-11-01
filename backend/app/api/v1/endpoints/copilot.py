from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.task_service import TaskService
from app.services.copilot_mapper import CopilotAction, mapCopilotToTask

router = APIRouter()

class CopilotJobRequest(BaseModel):
    action: CopilotAction
    repository: str
    issue_number: int | None = None
    pr_number: int | None = None
    description: str | None = None
    timeout_minutes: int | None = 59
    priority: str | None = "normal"

@router.post("/jobs")
async def receive_copilot_job(
    req: CopilotJobRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = mapCopilotToTask(req.model_dump())
        task = await TaskService(db).create_task(
            title=payload["title"],
            description=payload["description"],
            repository_full_name=payload["repository"],
            action_type=payload["action_type"],
            priority=payload["priority"],
            issue_number=payload.get("issue_number"),
            pull_request_number=payload.get("pull_request_number"),
            timeout_minutes=payload["timeout_minutes"],
            user_id=current_user.id,
        )
        return {"status": "accepted", "task_id": str(task.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to accept job: {e}")
