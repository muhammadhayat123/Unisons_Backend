from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from src.backend.config.db import get_db
from src.backend.models.user_model import User, Designation
from src.backend.utils.util_helper import require_admin, hash_password, get_current_user

admin_route = APIRouter(prefix="/api/admins", tags=["admins"])


@admin_route.get("")
def list_admins(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    admins = db.query(User).filter(User.designation == Designation.admin).all()
    return [{"id": a.id, "username": a.username, "email": a.email, "phone": a.phone,
             "is_active": a.is_active, "created_at": a.created_at} for a in admins]


@admin_route.post("", status_code=201)
def create_admin(data: dict, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    existing = db.query(User).filter((User.email == data["email"]) | (User.username == data["username"])).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already taken")
    user = User(
        username=data["username"],
        email=data["email"],
        password=hash_password(data["password"]),
        designation=Designation.admin,
        phone=data.get("phone"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email, "designation": user.designation}


@admin_route.put("/{admin_id}")
def update_admin(admin_id: int, data: dict, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == admin_id, User.designation == Designation.admin).first()
    if not user:
        raise HTTPException(status_code=404, detail="Admin not found")
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "phone" in data:
        user.phone = data["phone"]
    if "password" in data and data["password"]:
        user.password = hash_password(data["password"])
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email}


@admin_route.patch("/{admin_id}/toggle-active")
def toggle_admin_active(admin_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == admin_id, User.designation == Designation.admin).first()
    if not user:
        raise HTTPException(status_code=404, detail="Admin not found")
    if user.is_active:
        # Deactivating — check if last active admin
        active_count = db.query(User).filter(User.designation == Designation.admin, User.is_active == True).count()
        if active_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot deactivate the last active admin")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@admin_route.delete("/{admin_id}", status_code=204)
def delete_admin(admin_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == admin_id, User.designation == Designation.admin).first()
    if not user:
        raise HTTPException(status_code=404, detail="Admin not found")
    # Safety: prevent deleting last active admin
    active_count = db.query(User).filter(User.designation == Designation.admin, User.is_active == True).count()
    if user.is_active and active_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last active admin")
    db.delete(user)
    db.commit()
