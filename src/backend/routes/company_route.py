from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from src.backend.config.db import get_db
from src.backend.models.company_model import CompanyProfile
from src.backend.schemas.company_schema import CompanyCreate, CompanyUpdate, CompanyResponse
from src.backend.utils.util_helper import get_current_user, require_admin

company_route = APIRouter(prefix="/api/company", tags=["company"])

@company_route.get("", response_model=CompanyResponse)
def get_company(db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    company = db.query(CompanyProfile).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return company

@company_route.post("", response_model=CompanyResponse, status_code=201)
def create_company(data: CompanyCreate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    existing = db.query(CompanyProfile).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company profile already exists. Use PUT to update.")
    company = CompanyProfile(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@company_route.put("", response_model=CompanyResponse)
def update_company(data: CompanyUpdate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    company = db.query(CompanyProfile).first()
    if not company:
        company = CompanyProfile(**data.model_dump())
        db.add(company)
    else:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(company, k, v)
        company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(company)
    return company
