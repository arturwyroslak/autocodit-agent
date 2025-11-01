from datetime import datetime, timezone
from typing import Any, Dict

from app.websocket.manager import broadcast_session_update, broadcast_task_update

async def emit_phase(session_id: str, phase: str, message: str) -> None:
    payload: Dict[str, Any] = {
        "type": "session:event",
        "phase": phase,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await broadcast_session_update(session_id, payload)

async def emit_file_modified(session_id: str, path: str, added: list[str], removed: list[str]) -> None:
    payload: Dict[str, Any] = {
        "type": "session:filemodified",
        "path": path,
        "added": added,
        "removed": removed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await broadcast_session_update(session_id, payload)

async def emit_progress(task_id: str, iteration: int, total: int | None = None, percent: float | None = None) -> None:
    payload: Dict[str, Any] = {
        "type": "task:progress",
        "iteration": iteration,
        "total": total,
        "percent": percent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await broadcast_task_update(task_id, payload)

async def emit_completed(task_id: str, status: str, pr_number: int | None = None, branch: str | None = None, summary: str | None = None) -> None:
    payload: Dict[str, Any] = {
        "type": "task:completed",
        "status": status,
        "pr_number": pr_number,
        "branch": branch,
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await broadcast_task_update(task_id, payload)

async def emit_tool_invoked(session_id: str, name: str, args: Dict[str, Any] | None = None) -> None:
    await broadcast_session_update(session_id, {
        "type": "tool:invoked",
        "name": name,
        "args": args or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

async def emit_tool_result(session_id: str, name: str, ok: bool, output: str | None = None, error: str | None = None) -> None:
    await broadcast_session_update(session_id, {
        "type": "tool:result",
        "name": name,
        "ok": ok,
        "output": output,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

async def emit_test_result(session_id: str, passed: int, failed: int, coverage: float | None = None) -> None:
    await broadcast_session_update(session_id, {
        "type": "test:result",
        "passed": passed,
        "failed": failed,
        "coverage": coverage,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

async def emit_linter_result(session_id: str, errors: int, warnings: int) -> None:
    await broadcast_session_update(session_id, {
        "type": "linter:result",
        "errors": errors,
        "warnings": warnings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

async def emit_build_status(session_id: str, status: str, logs_url: str | None = None) -> None:
    await broadcast_session_update(session_id, {
        "type": "build:status",
        "status": status,
        "logs_url": logs_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
