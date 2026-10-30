from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

class PersonnelBase(BaseModel):
    cp_name: str
    department: Optional[str] = None
    desg: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class PersonnelCreate(PersonnelBase):
    pass

class PersonnelUpdate(PersonnelBase):
    cp_name: Optional[str] = None

class PersonnelResponse(PersonnelBase):
    id: int
    personnel_ref_id: str
    customer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    sector: str
    party: Optional[str] = None
    customer_name: str
    customer_initials: Optional[str] = None
    ho_address: str
    factory_address: Optional[str] = None
    city: str
    website: str
    email: str
    phone: str
    ntn: Optional[str] = None
    gst: Optional[str] = None
    cnic: Optional[str] = None
    cust_relation: Optional[str] = None
    cust_priority: Optional[str] = None
    cust_type: str
    cust_culture: Optional[str] = None
    payment_method: Optional[str] = None
    payment_terms: Optional[str] = None
    tax_type: Optional[str] = None
    sales_rep_id: Optional[int] = None
    additional_details: Optional[str] = None

class CustomerCreate(CustomerBase):
    personnel: Optional[List[PersonnelCreate]] = []

class CustomerUpdate(CustomerBase):
    sector: Optional[str] = None
    customer_name: Optional[str] = None
    ho_address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    cust_type: Optional[str] = None
    personnel: Optional[List[PersonnelCreate]] = []

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
    city: Optional[str] = None
    inquiry_count: int = 0
    latest_inquiry_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True
