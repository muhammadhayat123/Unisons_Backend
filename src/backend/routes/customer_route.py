from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import datetime

from src.backend.config.db import get_db
from src.backend.models.customer_model import CustomerModel, PersonnelModel
from src.backend.models.inquiry_model import Inquiry
from src.backend.schemas.customer_schema import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse
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
    q = db.query(CustomerModel)
    if search:
        q = q.filter(or_(
            CustomerModel.customer_name.ilike(f"%{search}%"),
            CustomerModel.customer_ref_id.ilike(f"%{search}%"),
            CustomerModel.email.ilike(f"%{search}%"),
            CustomerModel.phone.ilike(f"%{search}%"),
            CustomerModel.sector.ilike(f"%{search}%"),
        ))
    total = q.count()
    customers = q.order_by(CustomerModel.created_at.desc()).offset(skip).limit(limit).all()
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
            "city": c.city,
            "inquiry_count": inquiry_count,
            "latest_inquiry_id": latest_inq.id if latest_inq else None,
            "created_at": c.created_at,
        })
    return {"total": total, "customers": result}

@customer_route.post("", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    ref_id = get_next_customer_ref(db)
    dump_data = data.model_dump(exclude={"personnel"})
    customer = CustomerModel(customer_ref_id=ref_id, **dump_data)
    
    db.add(customer)
    db.flush()
    
    for p in (data.personnel or []):
        p_ref = get_next_personnel_ref(db)
        personnel = PersonnelModel(personnel_ref_id=p_ref, customer_id=customer.id, **p.model_dump())
        db.add(personnel)
        
    db.commit()
    db.refresh(customer)
    return customer

@customer_route.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    c = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return c

@customer_route.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    c = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        dump_data = data.model_dump(exclude={"personnel"}, exclude_unset=True)
        for k, v in dump_data.items():
            setattr(c, k, v)
        c.updated_at = datetime.utcnow()
        
        if data.personnel is not None:
            db.query(PersonnelModel).filter(PersonnelModel.customer_id == customer_id).delete()
            for p in data.personnel:
                p_ref = get_next_personnel_ref(db)
                personnel = PersonnelModel(personnel_ref_id=p_ref, customer_id=c.id, **p.model_dump())
                db.add(personnel)
                
        db.commit()
        db.refresh(c)
        return c
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print("Update payload was:", data.model_dump())
        raise HTTPException(status_code=500, detail=str(e))

@customer_route.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    c = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(c)
    db.commit()

@customer_route.get("/{customer_id}/inquiries", response_model=dict)
def get_customer_inquiries(customer_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    c = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    inquiries = db.query(Inquiry).filter(Inquiry.customer_id == customer_id).order_by(Inquiry.created_at.desc()).all()
    return {"inquiries": [
        {"id": i.id, "inquiry_ref_id": i.inquiry_ref_id, "status": i.status, "created_at": i.created_at, "seller_id": i.seller_id}
        for i in inquiries
    ]}
