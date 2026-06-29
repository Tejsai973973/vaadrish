from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
import asyncio
import json
from datetime import datetime

router = APIRouter()

active_connections: list[WebSocket] = []


async def broadcast(message: dict):
    """Send message to all connected clients."""
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        active_connections.remove(ws)


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket connected. Total: {len(active_connections)}")

    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({
                "type":      "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "clients":   len(active_connections),
            })
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(active_connections)}")