from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SessionStartResponse(BaseModel):
    session_id: int
    start_time: datetime
    message: str

    class Config:
        from_attributes = True


class PingRequest(BaseModel):
    session_id: int
    latitude: float
    longitude: float
    accuracy: Optional[float] = None


class PingResponse(BaseModel):
    status: str
    recorded_at: datetime


class StopRequest(BaseModel):
    session_id: int


class StopResponse(BaseModel):
    status: str
    session_id: int
    end_time: datetime


class CurrentStatusResponse(BaseModel):
    is_active: bool
    session_id: Optional[int] = None
    start_time: Optional[datetime] = None


class SellerTrackingStatus(BaseModel):
    seller_id: int
    username: str
    email: str
    is_tracking: bool
    session_id: Optional[int] = None
    last_seen: Optional[datetime] = None
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None


class SessionSummary(BaseModel):
    session_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool
    duration_minutes: Optional[float] = None
    ping_count: int


class RoutePoint(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    recorded_at: datetime

    class Config:
        from_attributes = True


class RouteResponse(BaseModel):
    session_id: int
    points: list[RoutePoint]
