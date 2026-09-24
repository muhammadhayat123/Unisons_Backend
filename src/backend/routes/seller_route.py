from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from src.backend.config.db import get_db
from src.backend.models.user_model import User, Designation
from src.backend.models.inquiry_model import Inquiry
from src.backend.utils.util_helper import require_admin, hash_password

seller_route = APIRouter(prefix="/api/sellers", tags=["sellers"])


@seller_route.get("")
def list_sellers(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    sellers = db.query(User).filter(User.designation == Designation.seller).all()
    result = []
    for s in sellers:
        inquiry_count = db.query(func.count(Inquiry.id)).filter(Inquiry.seller_id == s.id).scalar()
        result.append({"id": s.id, "username": s.username, "email": s.email,
                       "phone": s.phone, "is_active": s.is_active, "created_at": s.created_at,
                       "inquiry_count": inquiry_count})
    return result


@seller_route.post("", status_code=201)
def create_seller(data: dict, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    existing = db.query(User).filter((User.email == data["email"]) | (User.username == data["username"])).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already taken")
    user = User(
        username=data["username"],
        email=data["email"],
        password=hash_password(data["password"]),
        designation=Designation.seller,
        phone=data.get("phone"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email, "designation": user.designation}


@seller_route.put("/{seller_id}")
def update_seller(seller_id: int, data: dict, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == seller_id, User.designation == Designation.seller).first()
    if not user:
        raise HTTPException(status_code=404, detail="Seller not found")
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


@seller_route.patch("/{seller_id}/toggle-active")
def toggle_seller_active(seller_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == seller_id, User.designation == Designation.seller).first()
    if not user:
        raise HTTPException(status_code=404, detail="Seller not found")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@seller_route.delete("/{seller_id}", status_code=204)
def delete_seller(seller_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    user = db.query(User).filter(User.id == seller_id, User.designation == Designation.seller).first()
    if not user:
        raise HTTPException(status_code=404, detail="Seller not found")
    db.delete(user)
    db.commit()
