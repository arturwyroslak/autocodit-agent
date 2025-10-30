import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.session import Session, SessionStatus
from ..models.task import Task
from ..core.database import get_db
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RunnerService:
    """Service for managing container-based code execution runners"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def create_session(
        self,
        task: Task,
        db: AsyncSession = None
    ) -> Session:
        """Create and start a new execution session"""
        
        if db is None:
            db = await anext(get_db())
        
        try:
            # Create session record
            session = Session(
                task_id=task.id,
                status=SessionStatus.INITIALIZING,
                ai_model_used=settings.DEFAULT_AI_MODEL,
                context_data={
                    "repository": task.repository.full_name,
                    "base_branch": task.base_branch,
                    "action_type": task.github_event_type
                }
            )
            
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            # Start container execution
            await self._start_container_execution(session)
            
            logger.info(f"Created session {session.id} for task {task.id}")
            
            return session
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session_status(
        self,
        session_id: str,
        db: AsyncSession = None
    ) -> Optional[Dict[str, Any]]:
        """Get current status of a session"""
        
        if db is None:
            db = await anext(get_db())
        
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        return {
            "id": session.id,
            "status": session.status.value,
            "progress": session.progress_percentage,
            "current_step": session.current_step,
            "total_steps": session.total_steps,
            "started_at": session.started_at,
            "duration": session.duration_seconds,
            "memory_usage": session.memory_usage_mb,
            "cpu_usage": session.cpu_usage_percent,
            "error_details": session.error_details
        }
    
    async def stop_session(
        self,
        session_id: str,
        db: AsyncSession = None
    ) -> bool:
        """Stop a running session"""
        
        if db is None:
            db = await anext(get_db())
        
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return False
            
            # Stop container if running
            if session.container_id and session_id in self.active_sessions:
                await self._stop_container(session.container_id)
                del self.active_sessions[session_id]
            
            # Update session status
            session.status = SessionStatus.CANCELLED
            session.completed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Stopped session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping session: {e}")
            return False
    
    async def _start_container_execution(self, session: Session):
        """Start container for session execution"""
        
        try:
            # This would integrate with Docker API or Kubernetes
            container_config = {
                "image": "autocodit-agent-runner:latest",
                "environment": {
                    "SESSION_ID": session.id,
                    "TASK_ID": session.task_id,
                    "AI_MODEL": session.ai_model_used,
                    "CONTEXT_DATA": session.context_data
                },
                "resources": {
                    "memory": "2Gi",
                    "cpu": "1000m"
                },
                "timeout": 3600  # 1 hour
            }
            
            # Simulate container creation
            container_id = f"container-{session.id}"
            session.container_id = container_id
            session.status = SessionStatus.EXECUTING
            session.started_at = datetime.utcnow()
            
            # Track active session
            self.active_sessions[session.id] = {
                "container_id": container_id,
                "started_at": datetime.utcnow(),
                "config": container_config
            }
            
            logger.info(f"Started container {container_id} for session {session.id}")
            
        except Exception as e:
            session.status = SessionStatus.FAILED
            session.error_details = str(e)
            logger.error(f"Failed to start container for session {session.id}: {e}")
            raise
    
    async def _stop_container(self, container_id: str):
        """Stop a running container"""
        
        try:
            # This would use Docker API or Kubernetes API
            logger.info(f"Stopping container {container_id}")
            
            # Simulate container stop
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {e}")
    
    async def list_active_sessions(
        self,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """List all currently active sessions"""
        
        if db is None:
            db = await anext(get_db())
        
        result = await db.execute(
            select(Session).where(
                Session.status.in_([
                    SessionStatus.INITIALIZING,
                    SessionStatus.PLANNING, 
                    SessionStatus.EXECUTING,
                    SessionStatus.VALIDATING
                ])
            )
        )
        
        sessions = result.scalars().all()
        
        return [
            {
                "id": session.id,
                "task_id": session.task_id,
                "status": session.status.value,
                "started_at": session.started_at,
                "duration": session.duration_seconds,
                "progress": session.progress_percentage,
                "container_id": session.container_id
            }
            for session in sessions
        ]
    
    async def cleanup_finished_sessions(
        self,
        older_than_hours: int = 24,
        db: AsyncSession = None
    ) -> int:
        """Clean up finished sessions older than specified hours"""
        
        if db is None:
            db = await anext(get_db())
        
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        result = await db.execute(
            select(Session).where(
                and_(
                    Session.status.in_([
                        SessionStatus.COMPLETED,
                        SessionStatus.FAILED,
                        SessionStatus.CANCELLED
                    ]),
                    Session.completed_at < cutoff_time
                )
            )
        )
        
        sessions_to_cleanup = result.scalars().all()
        
        cleanup_count = 0
        for session in sessions_to_cleanup:
            try:
                # Clean up any remaining containers
                if session.container_id:
                    await self._stop_container(session.container_id)
                
                # Remove session from active tracking
                if session.id in self.active_sessions:
                    del self.active_sessions[session.id]
                
                cleanup_count += 1
                
            except Exception as e:
                logger.error(f"Error cleaning up session {session.id}: {e}")
        
        logger.info(f"Cleaned up {cleanup_count} finished sessions")
        
        return cleanup_count