"""
WebSocket event handler + broadcaster.
Single WebSocket at ws://localhost:8080/ws for all real-time browser-server communication.
"""
import json
import logging
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("diabeetech.ws")


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events to all connected clients."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def send_event(self, websocket: WebSocket, event_type: str, data: dict):
        """Send an event to a specific client."""
        try:
            await websocket.send_json({"type": event_type, "data": data})
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            self.active_connections.discard(websocket)

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast an event to all connected clients."""
        message = json.dumps({"type": event_type, "data": data})
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_full_state(self, websocket: WebSocket, state: dict):
        """Send the full current state to a newly connected client."""
        for event_type, data in state.items():
            if data is not None:
                await self.send_event(websocket, event_type, data)


# Singleton
ws_manager = ConnectionManager()
