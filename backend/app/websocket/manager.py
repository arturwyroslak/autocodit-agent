"""
AutoCodit Agent - WebSocket Manager

Manages real-time WebSocket connections for live updates.
"""

import json
from typing import Dict, List, Set, Any
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # Active connections by connection ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Subscriptions: topic -> set of connection IDs
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept WebSocket connection"""
        await websocket.accept()
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "connected_at": datetime.now(timezone.utc),
            "subscriptions": set(),
            "message_count": 0
        }
        
        logger.info(
            "WebSocket connection established",
            connection_id=connection_id,
            total_connections=len(self.active_connections)
        )
    
    def disconnect(self, connection_id: str) -> None:
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            # Remove from all subscriptions
            metadata = self.connection_metadata.get(connection_id, {})
            for topic in metadata.get("subscriptions", set()):
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(connection_id)
                    if not self.subscriptions[topic]:
                        del self.subscriptions[topic]
            
            # Remove connection
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            logger.info(
                "WebSocket connection closed",
                connection_id=connection_id,
                total_connections=len(self.active_connections)
            )
    
    async def subscribe(self, connection_id: str, topic: str) -> None:
        """Subscribe connection to topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(connection_id)
        
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].add(topic)
        
        logger.debug(
            "Connection subscribed to topic",
            connection_id=connection_id,
            topic=topic,
            subscribers=len(self.subscriptions[topic])
        )
    
    async def unsubscribe(self, connection_id: str, topic: str) -> None:
        """Unsubscribe connection from topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].discard(topic)
        
        logger.debug(
            "Connection unsubscribed from topic",
            connection_id=connection_id,
            topic=topic
        )
    
    async def send_personal_message(self, message: dict, connection_id: str) -> None:
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
                
                # Update message count
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["message_count"] += 1
                
            except Exception as e:
                logger.error(
                    "Failed to send personal message",
                    connection_id=connection_id,
                    error=str(e)
                )
                # Connection might be dead, remove it
                self.disconnect(connection_id)
    
    async def broadcast_to_topic(self, message: dict, topic: str) -> int:
        """Broadcast message to all subscribers of a topic"""
        if topic not in self.subscriptions:
            return 0
        
        message["topic"] = topic
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        sent_count = 0
        failed_connections = []
        
        for connection_id in self.subscriptions[topic].copy():
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_json(message)
                    sent_count += 1
                    
                    # Update message count
                    if connection_id in self.connection_metadata:
                        self.connection_metadata[connection_id]["message_count"] += 1
                
                except Exception as e:
                    logger.error(
                        "Failed to send broadcast message",
                        connection_id=connection_id,
                        topic=topic,
                        error=str(e)
                    )
                    failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            self.disconnect(connection_id)
        
        if sent_count > 0:
            logger.debug(
                "Broadcast message sent",
                topic=topic,
                sent_count=sent_count,
                message_type=message.get("type")
            )
        
        return sent_count
    
    async def broadcast_to_all(self, message: dict) -> int:
        """Broadcast message to all connected clients"""
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        sent_count = 0
        failed_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
                sent_count += 1
                
                # Update message count
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["message_count"] += 1
            
            except Exception as e:
                logger.error(
                    "Failed to send global broadcast",
                    connection_id=connection_id,
                    error=str(e)
                )
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            self.disconnect(connection_id)
        
        logger.info(
            "Global broadcast sent",
            sent_count=sent_count,
            message_type=message.get("type")
        )
        
        return sent_count
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "total_subscriptions": len(self.subscriptions),
            "topics": {
                topic: len(subscribers)
                for topic, subscribers in self.subscriptions.items()
            },
            "connections": {
                connection_id: {
                    "connected_at": metadata["connected_at"].isoformat(),
                    "message_count": metadata["message_count"],
                    "subscription_count": len(metadata["subscriptions"])
                }
                for connection_id, metadata in self.connection_metadata.items()
            }
        }


# Global connection manager
websocket_manager = ConnectionManager()


# WebSocket router
websocket_router = APIRouter()


@websocket_router.websocket("/notifications/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """Main WebSocket endpoint for user notifications"""
    
    connection_id = f"user:{user_id}:{id(websocket)}"
    
    await websocket_manager.connect(websocket, connection_id)
    
    # Subscribe to user-specific topics
    await websocket_manager.subscribe(connection_id, f"user:{user_id}")
    await websocket_manager.subscribe(connection_id, "global")
    
    try:
        while True:
            # Listen for client messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(connection_id, message)
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON message"},
                    connection_id
                )
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(connection_id)
    
    except Exception as e:
        logger.error(
            "WebSocket error",
            connection_id=connection_id,
            error=str(e)
        )
        websocket_manager.disconnect(connection_id)


async def handle_websocket_message(connection_id: str, message: dict) -> None:
    """Handle incoming WebSocket message from client"""
    
    message_type = message.get("type")
    
    if message_type == "ping":
        await websocket_manager.send_personal_message(
            {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()},
            connection_id
        )
    
    elif message_type == "subscribe":
        topic = message.get("topic")
        if topic:
            await websocket_manager.subscribe(connection_id, topic)
            await websocket_manager.send_personal_message(
                {"type": "subscribed", "topic": topic},
                connection_id
            )
    
    elif message_type == "unsubscribe":
        topic = message.get("topic")
        if topic:
            await websocket_manager.unsubscribe(connection_id, topic)
            await websocket_manager.send_personal_message(
                {"type": "unsubscribed", "topic": topic},
                connection_id
            )
    
    elif message_type == "get_stats":
        stats = websocket_manager.get_connection_stats()
        await websocket_manager.send_personal_message(
            {"type": "stats", "data": stats},
            connection_id
        )
    
    else:
        logger.warning(
            "Unknown WebSocket message type",
            connection_id=connection_id,
            message_type=message_type
        )


# Helper functions for broadcasting updates

async def broadcast_task_update(task_id: str, update: dict) -> None:
    """Broadcast task status update"""
    message = {
        "type": "task_update",
        "task_id": task_id,
        "data": update
    }
    
    # Broadcast to task-specific topic and user topic
    await websocket_manager.broadcast_to_topic(message, f"task:{task_id}")
    
    # If update contains user_id, also broadcast to user topic
    if "user_id" in update:
        await websocket_manager.broadcast_to_topic(message, f"user:{update['user_id']}")


async def broadcast_session_update(session_id: str, update: dict) -> None:
    """Broadcast session status update"""
    message = {
        "type": "session_update",
        "session_id": session_id,
        "data": update
    }
    
    await websocket_manager.broadcast_to_topic(message, f"session:{session_id}")


async def broadcast_system_alert(alert: dict) -> None:
    """Broadcast system-wide alert"""
    message = {
        "type": "system_alert",
        "data": alert
    }
    
    await websocket_manager.broadcast_to_all(message)