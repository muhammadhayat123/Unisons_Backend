from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import datetime

from src.backend.config.db import get_db
from src.backend.models.customer_model import Customer, Personnel
from src.backend.models.inquiry_model import Inquiry
from src.backend.schemas.customer_schema import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse,
    PersonnelCreate, PersonnelUpdate, PersonnelResponse
)
from src.backend.utils.util_helper import get_current_user, require_admin
from src.backend.services.ref_id_service import get_next_customer_ref, get_next_personnel_ref

customer_route = APIRouter(prefix="/api/customers", tags=["customers"])

@customer_route.get("", response_model=dict)
def list_customers(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    q = db.query(Customer)
    if search:
        q = q.filter(or_(
            Customer.customer_name.ilike(f"%{search}%"),
            Customer.customer_ref_id.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%"),
            Customer.phone.ilike(f"%{search}%"),
            Customer.sector.ilike(f"%{search}%"),
        ))
    total = q.count()
    customers = q.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for c in customers:
        inquiries_q = db.query(Inquiry).filter(Inquiry.customer_id == c.id).order_by(Inquiry.created_at.desc())
        inquiry_count = inquiries_q.count()
        latest_inq = inquiries_q.first()
        result.append({
            "id": c.id,
            "customer_ref_id": c.customer_ref_id,
            "customer_name": c.customer_name,
            "sector": c.sector,
            "phone": c.phone,
            "email": c.email,
            "website": c.website,
            "inquiry_count": inquiry_count,
            "latest_inquiry_id": latest_inq.id if latest_inq else None,
            "created_at": c.created_at,
        })
    return {"total": total, "customers": result}

@customer_route.post("", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    ref_id = get_next_customer_ref(db)
    customer = Customer(
        customer_ref_id=ref_id,
        customer_name=data.customer_name,
        inquiry_date=data.inquiry_date,
        sector=data.sector,
        factory_address=data.factory_address,
        phone=data.phone,
        ho_address=data.ho_address,
        website=data.website,
        email=data.email,
    )
    db.add(customer)
    db.flush()
    for p in (data.personnel or []):
        p_ref = get_next_personnel_ref(db)
        personnel = Personnel(personnel_ref_id=p_ref, customer_id=customer.id, **p.model_dump())
        db.add(personnel)
    db.commit()
    db.refresh(customer)
    return customer

@customer_route.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return c

@customer_route.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return c

@customer_route.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(c)
    db.commit()

@customer_route.get("/{customer_id}/inquiries", response_model=dict)
def get_customer_inquiries(customer_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    inquiries = db.query(Inquiry).filter(Inquiry.customer_id == customer_id).order_by(Inquiry.created_at.desc()).all()
    return {"inquiries": [
        {"id": i.id, "inquiry_ref_id": i.inquiry_ref_id, "status": i.status, "created_at": i.created_at, "seller_id": i.seller_id}
        for i in inquiries
    ]}

# Personnel sub-routes
@customer_route.get("/{customer_id}/personnel", response_model=List[PersonnelResponse])
def list_personnel(customer_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return db.query(Personnel).filter(Personnel.customer_id == customer_id).all()

@customer_route.post("/{customer_id}/personnel", response_model=PersonnelResponse, status_code=201)
def add_personnel(customer_id: int, data: PersonnelCreate, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    ref_id = get_next_personnel_ref(db)
    p = Personnel(personnel_ref_id=ref_id, customer_id=customer_id, **data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@customer_route.put("/{customer_id}/personnel/{personnel_id}", response_model=PersonnelResponse)
def update_personnel(customer_id: int, personnel_id: int, data: PersonnelUpdate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    p = db.query(Personnel).filter(Personnel.id == personnel_id, Personnel.customer_id == customer_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return p

@customer_route.delete("/{customer_id}/personnel/{personnel_id}", status_code=204)
def delete_personnel(customer_id: int, personnel_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    p = db.query(Personnel).filter(Personnel.id == personnel_id, Personnel.customer_id == customer_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Personnel not found")
    db.delete(p)
    db.commit()
