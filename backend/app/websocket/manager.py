"""
AutoCodit Agent - WebSocket Manager

Real-time communication for task updates, session monitoring,
and live streaming of logs and progress.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Set, Optional, Any, List
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, Query
from fastapi.websockets import WebSocketState
import structlog

from app.core.auth import get_current_user_ws
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        # Active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Task subscriptions: task_id -> set of user_ids
        self.task_subscriptions: Dict[str, Set[str]] = {}
        
        # Session subscriptions: session_id -> set of user_ids
        self.session_subscriptions: Dict[str, Set[str]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc),
            "last_ping": datetime.now(timezone.utc)
        }
        
        logger.info(
            "WebSocket connection established",
            user_id=user_id,
            total_connections=sum(len(conns) for conns in self.active_connections.values())
        )
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket connection established successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection"""
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")
        
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from subscriptions
        if user_id:
            for task_id, subscribers in list(self.task_subscriptions.items()):
                subscribers.discard(user_id)
                if not subscribers:
                    del self.task_subscriptions[task_id]
            
            for session_id, subscribers in list(self.session_subscriptions.items()):
                subscribers.discard(user_id)
                if not subscribers:
                    del self.session_subscriptions[session_id]
        
        # Remove metadata
        self.connection_metadata.pop(websocket, None)
        
        logger.info(
            "WebSocket connection closed",
            user_id=user_id,
            total_connections=sum(len(conns) for conns in self.active_connections.values())
        )
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Send message to specific WebSocket connection"""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error("Failed to send WebSocket message", error=str(e))
                self.disconnect(websocket)
    
    async def send_user_message(self, message: Dict[str, Any], user_id: str) -> None:
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            connections = self.active_connections[user_id].copy()
            
            for websocket in connections:
                await self.send_personal_message(message, websocket)
    
    async def broadcast_task_update(self, task_id: str, update: Dict[str, Any]) -> None:
        """Broadcast task update to all subscribers"""
        if task_id in self.task_subscriptions:
            message = {
                "type": "task_update",
                "task_id": task_id,
                "data": update,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            subscribers = self.task_subscriptions[task_id].copy()
            
            for user_id in subscribers:
                await self.send_user_message(message, user_id)
    
    async def broadcast_session_update(self, session_id: str, update: Dict[str, Any]) -> None:
        """Broadcast session update to all subscribers"""
        if session_id in self.session_subscriptions:
            message = {
                "type": "session_update",
                "session_id": session_id,
                "data": update,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            subscribers = self.session_subscriptions[session_id].copy()
            
            for user_id in subscribers:
                await self.send_user_message(message, user_id)
    
    async def subscribe_to_task(self, user_id: str, task_id: str) -> None:
        """Subscribe user to task updates"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        
        self.task_subscriptions[task_id].add(user_id)
        
        logger.debug(
            "User subscribed to task updates",
            user_id=user_id,
            task_id=task_id
        )
    
    async def unsubscribe_from_task(self, user_id: str, task_id: str) -> None:
        """Unsubscribe user from task updates"""
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(user_id)
            
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]
        
        logger.debug(
            "User unsubscribed from task updates",
            user_id=user_id,
            task_id=task_id
        )
    
    async def subscribe_to_session(self, user_id: str, session_id: str) -> None:
        """Subscribe user to session updates"""
        if session_id not in self.session_subscriptions:
            self.session_subscriptions[session_id] = set()
        
        self.session_subscriptions[session_id].add(user_id)
        
        logger.debug(
            "User subscribed to session updates",
            user_id=user_id,
            session_id=session_id
        )
    
    async def unsubscribe_from_session(self, user_id: str, session_id: str) -> None:
        """Unsubscribe user from session updates"""
        if session_id in self.session_subscriptions:
            self.session_subscriptions[session_id].discard(user_id)
            
            if not self.session_subscriptions[session_id]:
                del self.session_subscriptions[session_id]
        
        logger.debug(
            "User unsubscribed from session updates",
            user_id=user_id,
            session_id=session_id
        )
    
    async def handle_ping(self, websocket: WebSocket) -> None:
        """Handle ping message and update last ping time"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["last_ping"] = datetime.now(timezone.utc)
        
        await self.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "unique_users": len(self.active_connections),
            "task_subscriptions": len(self.task_subscriptions),
            "session_subscriptions": len(self.session_subscriptions),
            "connections_per_user": {
                user_id: len(conns) for user_id, conns in self.active_connections.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time communication"""
    user = None
    
    try:
        # Authenticate user
        if token:
            # TODO: Implement proper WebSocket authentication
            # For now, use a dummy user ID
            user_id = "anonymous"
        else:
            user_id = "anonymous"
        
        await manager.connect(websocket, user_id)
        
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "ping":
                    await manager.handle_ping(websocket)
                
                elif message_type == "subscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await manager.subscribe_to_task(user_id, task_id)
                
                elif message_type == "unsubscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await manager.unsubscribe_from_task(user_id, task_id)
                
                elif message_type == "subscribe_session":
                    session_id = message.get("session_id")
                    if session_id:
                        await manager.subscribe_to_session(user_id, session_id)
                
                elif message_type == "unsubscribe_session":
                    session_id = message.get("session_id")
                    if session_id:
                        await manager.unsubscribe_from_session(user_id, session_id)
                
                else:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }, websocket)
            
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON message"
                }, websocket)
            
            except Exception as e:
                logger.error("Error processing WebSocket message", error=str(e))
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, websocket)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket connection error", error=str(e))
    finally:
        manager.disconnect(websocket)


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return manager.get_connection_stats()


# Utility functions for other parts of the application
async def broadcast_task_update(task_id: str, update: Dict[str, Any]) -> None:
    """Broadcast task update to WebSocket subscribers"""
    await manager.broadcast_task_update(task_id, update)


async def broadcast_session_update(session_id: str, update: Dict[str, Any]) -> None:
    """Broadcast session update to WebSocket subscribers"""
    await manager.broadcast_session_update(session_id, update)


async def send_user_notification(user_id: str, notification: Dict[str, Any]) -> None:
    """Send notification to specific user"""
    message = {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await manager.send_user_message(message, user_id)