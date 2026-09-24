from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.backend.services.ws_manager import manager
from src.backend.utils.util_helper import decode_access_token

ws_route = APIRouter(tags=["websocket"])

@ws_route.websocket("/ws/inquiries")
async def websocket_inquiries(websocket: WebSocket, token: str = None):
    # Optional: validate token
    # payload = decode_access_token(token) if token else None
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
