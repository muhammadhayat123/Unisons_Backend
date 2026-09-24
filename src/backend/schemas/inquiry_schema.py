from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from src.backend.models.inquiry_model import (
    InquiryStatus, LocalImport, NewRepeat, MillType, StandCode, ArrangementType, NewReplacement
)

# ---- Furnace ----
class FurnaceItemCreate(BaseModel):
    furnace_no: Optional[str] = None
    capacity_ton: Optional[float] = None
    capacity_mw: Optional[float] = None

class FurnaceItemResponse(FurnaceItemCreate):
    id: int
    furnace_ref_id: str
    furnace_details_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Furnace Details ----
class FurnaceDetailsCreate(BaseModel):
    no_of_furnaces: Optional[int] = None
    tpd: Optional[float] = None
    furnaces: Optional[List[FurnaceItemCreate]] = []

class FurnaceDetailsResponse(BaseModel):
    id: int
    inquiry_id: int
    no_of_furnaces: Optional[int] = None
    tpd: Optional[float] = None
    furnaces: List[FurnaceItemResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

# ---- CCM ----
class CCMDetailsCreate(BaseModel):
    radius: Optional[str] = None
    length_of_tube: Optional[str] = None
    manual_open_tanky: Optional[str] = None
    strands: Optional[int] = None
    cmt_size: Optional[str] = None
    sgm_size: Optional[str] = None
    tundish_nozzle_size: Optional[str] = None
    supplier: Optional[str] = None

class CCMDetailsResponse(CCMDetailsCreate):
    id: int
    inquiry_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Rolling Mill Stand ----
class RollingMillStandCreate(BaseModel):
    mill_type: Optional[MillType] = None
    stand_code: Optional[StandCode] = None
    arrangement_type: Optional[ArrangementType] = None

class RollingMillStandResponse(RollingMillStandCreate):
    id: int
    stand_ref_id: str
    rolling_mill_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Rolling Mill Details ----
class RollingMillDetailsCreate(BaseModel):
    plant_capacity_tpd: Optional[float] = None
    plant_capacity_tph: Optional[float] = None
    supplier: Optional[str] = None
    total_stands: Optional[int] = None
    stands: Optional[List[RollingMillStandCreate]] = []

class RollingMillDetailsResponse(BaseModel):
    id: int
    inquiry_id: int
    plant_capacity_tpd: Optional[float] = None
    plant_capacity_tph: Optional[float] = None
    supplier: Optional[str] = None
    total_stands: Optional[int] = None
    stands: List[RollingMillStandResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Additional Info ----
class AdditionalInfoCreate(BaseModel):
    employee: Optional[str] = None
    source: Optional[str] = None
    local_import: Optional[LocalImport] = None
    new_repeat: Optional[NewRepeat] = None
    repeat_case_no: Optional[str] = None
    req_origin: Optional[str] = None
    incoterms: Optional[str] = None
    department: Optional[str] = None
    sub_department: Optional[str] = None
    currency: Optional[str] = None

class AdditionalInfoResponse(AdditionalInfoCreate):
    id: int
    inquiry_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Product ----
class ProductCreate(BaseModel):
    product_name: str
    department: Optional[str] = None
    remarks: Optional[str] = None
    no_of_item: Optional[int] = None
    detailed_specifications: Optional[str] = None
    required_model_number: Optional[str] = None
    picture_name_plate: Optional[str] = None
    quantity: Optional[int] = None
    application_usage: Optional[str] = None
    installed_location: Optional[str] = None
    required_brand: Optional[str] = None
    new_replacement: Optional[NewReplacement] = None
    drawing: Optional[str] = None
    layout: Optional[str] = None
    existing_brand_or_model: Optional[str] = None

class ProductResponse(ProductCreate):
    id: int
    product_ref_id: str
    inquiry_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Special Instructions ----
class SpecialInstructionsCreate(BaseModel):
    special_instructions: Optional[str] = None

class SpecialInstructionsResponse(SpecialInstructionsCreate):
    id: int
    inquiry_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Signature ----
class SignatureCreate(BaseModel):
    unisons_sales_rep: Optional[str] = None
    customer_signature: Optional[str] = None

class SignatureResponse(SignatureCreate):
    id: int
    inquiry_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Inquiry ----
class InquiryCreate(BaseModel):
    customer_id: int
    additional_info: Optional[AdditionalInfoCreate] = None
    furnace_details: Optional[FurnaceDetailsCreate] = None
    ccm_details: Optional[CCMDetailsCreate] = None
    rolling_mill_details: Optional[RollingMillDetailsCreate] = None
    products: Optional[List[ProductCreate]] = []
    special_instructions: Optional[SpecialInstructionsCreate] = None
    signature: Optional[SignatureCreate] = None

class InquiryStatusUpdate(BaseModel):
    status: InquiryStatus

class SellerInfo(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        from_attributes = True

class CustomerBasicInfo(BaseModel):
    id: int
    customer_ref_id: str
    customer_name: str
    sector: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    factory_address: Optional[str] = None
    ho_address: Optional[str] = None
    website: Optional[str] = None
    class Config:
        from_attributes = True

class InquiryListResponse(BaseModel):
    id: int
    inquiry_ref_id: str
    status: InquiryStatus
    customer: CustomerBasicInfo
    seller: SellerInfo
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class InquiryDetailResponse(BaseModel):
    id: int
    inquiry_ref_id: str
    status: InquiryStatus
    customer: CustomerBasicInfo
    seller: SellerInfo
    additional_info: Optional[AdditionalInfoResponse] = None
    furnace_details: Optional[FurnaceDetailsResponse] = None
    ccm_details: Optional[CCMDetailsResponse] = None
    rolling_mill_details: Optional[RollingMillDetailsResponse] = None
    products: List[ProductResponse] = []
    special_instructions: Optional[SpecialInstructionsResponse] = None
    signature: Optional[SignatureResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True
