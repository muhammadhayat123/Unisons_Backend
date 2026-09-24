from typing import Literal
from pydantic import BaseModel, EmailStr
from datetime import datetime

from src.backend.models.user_model import Designation


class UserCreate(BaseModel):
    """
    Model for creating a new user.
    """
    username: str
    email: EmailStr
    password: str
    designation: Literal["admin", "seller"] = "seller"


class UserResponse(BaseModel):
    """
    Response model for returning user details.
    Includes created_at and id fields.
    """
    id: int
    username: str
    email: EmailStr
    designation: Designation
    created_at: datetime

    class Config:
        from_attributes = True  # For Pydantic v2 compatibility


class LoginUser(BaseModel):
    """
    Model for user login.
    """
    email: EmailStr
    password: str

    class Config:
        from_attributes = True


class EmailRequest(BaseModel):
    """
    Model for validating email input.
    """
    email: EmailStr




class StatusResponse(BaseModel):
    message: str = ""
    data: list = None
    status: str = ""