from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime, date

class PersonnelBase(BaseModel):
    concerned_person: str
    department: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class PersonnelCreate(PersonnelBase):
    pass

class PersonnelUpdate(PersonnelBase):
    concerned_person: Optional[str] = None

class PersonnelResponse(PersonnelBase):
    id: int
    personnel_ref_id: str
    customer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    customer_name: str
    inquiry_date: Optional[date] = None
    sector: Optional[str] = None
    factory_address: Optional[str] = None
    phone: Optional[str] = None
    ho_address: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None

class CustomerCreate(CustomerBase):
    personnel: Optional[List[PersonnelCreate]] = []

class CustomerUpdate(CustomerBase):
    customer_name: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    customer_ref_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    personnel: List[PersonnelResponse] = []
    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    id: int
    customer_ref_id: str
    customer_name: str
    sector: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    inquiry_count: int = 0
    latest_inquiry_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True
