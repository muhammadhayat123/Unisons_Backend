import json
from datetime import datetime
from typing import List, Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.backend.config.db import get_db
from src.backend.models.tracking_model import TrackingSession, LocationLog
from src.backend.models.user_model import User, Designation
from src.backend.schemas.tracking_schema import (
    SessionStartResponse,
    PingRequest,
    PingResponse,
    StopRequest,
    StopResponse,
    CurrentStatusResponse,
    SellerTrackingStatus,
    SessionSummary,
    RouteResponse,
    RoutePoint,
)
from src.backend.utils.util_helper import get_current_user, require_admin, decode_access_token

tracking_route = APIRouter(prefix="/api/v1/tracking", tags=["tracking"])
admin_tracking_route = APIRouter(prefix="/api/v1/admin/tracking", tags=["admin-tracking"])
ws_tracking_route = APIRouter(tags=["tracking-ws"])


# ─────────────────────────────────────────────
# Dedicated WebSocket ConnectionManager for
# admin tracking room (isolated from inquiry WS)
# ─────────────────────────────────────────────
class TrackingConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead: Set[WebSocket] = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active_connections.discard(ws)


tracking_manager = TrackingConnectionManager()


# ─────────────────────────────────────────────
# SELLER ENDPOINTS
# ─────────────────────────────────────────────

@tracking_route.post("/start", response_model=SessionStartResponse, status_code=201)
def start_tracking(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new active tracking session. Fails if the seller already has one running."""
    seller_id = current_user["user_id"]

    existing = (
        db.query(TrackingSession)
        .filter(TrackingSession.seller_id == seller_id, TrackingSession.is_active == True)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Active session already exists (id={existing.id}). Stop it first.",
        )

    session = TrackingSession(seller_id=seller_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionStartResponse(
        session_id=session.id,
        start_time=session.start_time,
        message="Tracking session started.",
    )


@tracking_route.post("/ping", response_model=PingResponse)
async def ping_location(
    data: PingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a GPS coordinate and broadcast it in real-time to admin observers."""
    seller_id = current_user["user_id"]

    session = db.query(TrackingSession).filter(
        TrackingSession.id == data.session_id,
        TrackingSession.seller_id == seller_id,
        TrackingSession.is_active == True,
    ).first()
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Active session not found or does not belong to this seller.",
        )

    log = LocationLog(
        session_id=session.id,
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Look up the seller name for the broadcast payload
    seller = db.query(User).filter(User.id == seller_id).first()

    await tracking_manager.broadcast({
        "type": "location_ping",
        "seller_id": seller_id,
        "seller_name": seller.username if seller else "",
        "session_id": session.id,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "accuracy": data.accuracy,
        "recorded_at": log.recorded_at.isoformat(),
    })

    return PingResponse(status="ok", recorded_at=log.recorded_at)


@tracking_route.post("/stop", response_model=StopResponse)
def stop_tracking(
    data: StopRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """End an active tracking session."""
    seller_id = current_user["user_id"]

    session = db.query(TrackingSession).filter(
        TrackingSession.id == data.session_id,
        TrackingSession.seller_id == seller_id,
        TrackingSession.is_active == True,
    ).first()
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Active session not found or does not belong to this seller.",
        )

    session.is_active = False
    session.end_time = datetime.utcnow()
    db.commit()
    db.refresh(session)

    return StopResponse(status="stopped", session_id=session.id, end_time=session.end_time)


@tracking_route.get("/current-status", response_model=CurrentStatusResponse)
def current_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Returns whether seller has an active session so mobile UI can restore state on reload."""
    seller_id = current_user["user_id"]
    session = (
        db.query(TrackingSession)
        .filter(TrackingSession.seller_id == seller_id, TrackingSession.is_active == True)
        .first()
    )
    if session:
        return CurrentStatusResponse(
            is_active=True, session_id=session.id, start_time=session.start_time
        )
    return CurrentStatusResponse(is_active=False)


# ─────────────────────────────────────────────
# ADMIN ENDPOINTS
# ─────────────────────────────────────────────

@admin_tracking_route.get("/sellers", response_model=List[SellerTrackingStatus])
def list_seller_tracking_status(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Grid of all sellers: online/offline badge, last ping coordinate, last seen."""
    sellers = db.query(User).filter(User.designation == Designation.seller).all()
    result = []
    for seller in sellers:
        active_session = (
            db.query(TrackingSession)
            .filter(TrackingSession.seller_id == seller.id, TrackingSession.is_active == True)
            .first()
        )
        last_log = (
            db.query(LocationLog)
            .join(TrackingSession)
            .filter(TrackingSession.seller_id == seller.id)
            .order_by(LocationLog.recorded_at.desc())
            .first()
        )
        result.append(
            SellerTrackingStatus(
                seller_id=seller.id,
                username=seller.username,
                email=seller.email,
                is_tracking=active_session is not None,
                session_id=active_session.id if active_session else None,
                last_seen=last_log.recorded_at if last_log else None,
                last_latitude=last_log.latitude if last_log else None,
                last_longitude=last_log.longitude if last_log else None,
            )
        )
    return result


@admin_tracking_route.get("/sellers/{seller_id}/sessions", response_model=List[SessionSummary])
def list_seller_sessions(
    seller_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """All historical sessions for a seller with duration and ping count."""
    seller = db.query(User).filter(User.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    sessions = (
        db.query(TrackingSession)
        .filter(TrackingSession.seller_id == seller_id)
        .order_by(TrackingSession.start_time.desc())
        .all()
    )

    result = []
    for s in sessions:
        ping_count = db.query(LocationLog).filter(LocationLog.session_id == s.id).count()
        duration = None
        if s.end_time:
            duration = round((s.end_time - s.start_time).total_seconds() / 60, 1)
        elif s.is_active:
            duration = round((datetime.utcnow() - s.start_time).total_seconds() / 60, 1)
        result.append(
            SessionSummary(
                session_id=s.id,
                start_time=s.start_time,
                end_time=s.end_time,
                is_active=s.is_active,
                duration_minutes=duration,
                ping_count=ping_count,
            )
        )
    return result


@admin_tracking_route.get("/sessions/{session_id}/route", response_model=RouteResponse)
def get_session_route(
    session_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Full ordered lat/lng log for drawing a historical polyline on the map."""
    session = db.query(TrackingSession).filter(TrackingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    logs = (
        db.query(LocationLog)
        .filter(LocationLog.session_id == session_id)
        .order_by(LocationLog.recorded_at.asc())
        .all()
    )
    return RouteResponse(
        session_id=session_id,
        points=[
            RoutePoint(
                latitude=log.latitude,
                longitude=log.longitude,
                accuracy=log.accuracy,
                recorded_at=log.recorded_at,
            )
            for log in logs
        ],
    )


# ─────────────────────────────────────────────
# WEBSOCKET ENDPOINT
# ─────────────────────────────────────────────

@ws_tracking_route.websocket("/ws/admin/tracking")
async def ws_admin_tracking(websocket: WebSocket, token: str = None):
    """
    Admin-only WebSocket room for real-time seller location pings.
    Pass ?token=<jwt> as a query param for auth validation.
    """
    if token:
        payload = decode_access_token(token)
        if not payload or payload.get("designation") != "admin":
            await websocket.close(code=4003)
            return

    await tracking_manager.connect(websocket)
    try:
        while True:
            # Keep-alive: discard any client messages (heartbeats welcome)
            await websocket.receive_text()
    except WebSocketDisconnect:
        tracking_manager.disconnect(websocket)
