import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from src.backend.config.db import Base


class InquiryStatus(str, enum.Enum):
    new = "New"
    in_progress = "In Progress"
    contacted = "Contacted"
    completed = "Completed"
    cancelled = "Cancelled"


class LocalImport(str, enum.Enum):
    local = "Local"
    import_ = "Import"


class NewRepeat(str, enum.Enum):
    new = "New"
    repeat = "Repeat"


class MillType(str, enum.Enum):
    fully_continuous = "Fully Continuous"
    roughing_mill = "Roughing Mill"
    intermediate_mill = "Intermediate Mill"
    finishing_mill = "Finishing Mill"


class StandCode(str, enum.Enum):
    RM1 = "RM1"
    RM2 = "RM2"
    RM3 = "RM3"
    IM1 = "IM1"
    IM2 = "IM2"
    IM3 = "IM3"
    FM1 = "FM1"
    FM2 = "FM2"
    FM3 = "FM3"


class ArrangementType(str, enum.Enum):
    repeater = "Repeater (R)"
    continuous = "Continuous (C)"
    fully_continuous = "Fully Continuous (FC)"


class NewReplacement(str, enum.Enum):
    new = "New"
    replacement = "Replacement"


class Inquiry(Base):
    __tablename__ = "inquiries"
    id = Column(Integer, primary_key=True, index=True)
    inquiry_ref_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(InquiryStatus, name="inquiry_status_enum"), default=InquiryStatus.new, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer = relationship("Customer", back_populates="inquiries")
    seller = relationship("User", back_populates="inquiries")
    additional_info = relationship("AdditionalInquiryInfo", back_populates="inquiry", uselist=False, cascade="all, delete-orphan")
    furnace_details = relationship("FurnaceDetails", back_populates="inquiry", uselist=False, cascade="all, delete-orphan")
    ccm_details = relationship("CCMDetails", back_populates="inquiry", uselist=False, cascade="all, delete-orphan")
    rolling_mill_details = relationship("RollingMillDetails", back_populates="inquiry", uselist=False, cascade="all, delete-orphan")
    products = relationship("Product", back_populates="inquiry", cascade="all, delete-orphan")
    special_instructions = relationship("SpecialInstructions", back_populates="inquiry", uselist=False, cascade="all, delete-orphan")
    signature = relationship("Signature", back_populates="inquiry", uselist=False, cascade="all, delete-orphan")


class AdditionalInquiryInfo(Base):
    __tablename__ = "additional_inquiry_info"
    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), unique=True, nullable=False)
    employee = Column(String, nullable=True)
    source = Column(String, nullable=True)
    local_import = Column(SAEnum(LocalImport, name="local_import_enum"), nullable=True)
    new_repeat = Column(SAEnum(NewRepeat, name="new_repeat_enum"), nullable=True)
    repeat_case_no = Column(String, nullable=True)
    req_origin = Column(String, nullable=True)
    incoterms = Column(String, nullable=True)
    department = Column(String, nullable=True)
    sub_department = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inquiry = relationship("Inquiry", back_populates="additional_info")


class FurnaceDetails(Base):
    __tablename__ = "furnace_details"
    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), unique=True, nullable=False)
    no_of_furnaces = Column(Integer, nullable=True)
    tpd = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inquiry = relationship("Inquiry", back_populates="furnace_details")
    furnaces = relationship("Furnace", back_populates="furnace_details", cascade="all, delete-orphan")


class Furnace(Base):
    __tablename__ = "furnaces"
    id = Column(Integer, primary_key=True, index=True)
    furnace_ref_id = Column(String, unique=True, index=True, nullable=False)
    furnace_details_id = Column(Integer, ForeignKey("furnace_details.id"), nullable=False)
    furnace_no = Column(String, nullable=True)
    capacity_ton = Column(Float, nullable=True)
    capacity_mw = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    furnace_details = relationship("FurnaceDetails", back_populates="furnaces")


class CCMDetails(Base):
    __tablename__ = "ccm_details"
    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), unique=True, nullable=False)
    radius = Column(String, nullable=True)
    length_of_tube = Column(String, nullable=True)
    manual_open_tanky = Column(String, nullable=True)
    strands = Column(Integer, nullable=True)
    cmt_size = Column(String, nullable=True)
    sgm_size = Column(String, nullable=True)
    tundish_nozzle_size = Column(String, nullable=True)
    supplier = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inquiry = relationship("Inquiry", back_populates="ccm_details")


class RollingMillDetails(Base):
    __tablename__ = "rolling_mill_details"
    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), unique=True, nullable=False)
    plant_capacity_tpd = Column(Float, nullable=True)
    plant_capacity_tph = Column(Float, nullable=True)
    supplier = Column(String, nullable=True)
    total_stands = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inquiry = relationship("Inquiry", back_populates="rolling_mill_details")
    stands = relationship("RollingMillStand", back_populates="rolling_mill", cascade="all, delete-orphan")


class RollingMillStand(Base):
    __tablename__ = "rolling_mill_stands"
    id = Column(Integer, primary_key=True, index=True)
    stand_ref_id = Column(String, unique=True, index=True, nullable=False)
    rolling_mill_id = Column(Integer, ForeignKey("rolling_mill_details.id"), nullable=False)
    mill_type = Column(SAEnum(MillType, name="mill_type_enum"), nullable=True)
    stand_code = Column(SAEnum(StandCode, name="stand_code_enum"), nullable=True)
    arrangement_type = Column(SAEnum(ArrangementType, name="arrangement_type_enum"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rolling_mill = relationship("RollingMillDetails", back_populates="stands")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    product_ref_id = Column(String, unique=True, index=True, nullable=False)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=False)
    product_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    remarks = Column(Text, nullable=True)
    no_of_item = Column(Integer, nullable=True)
    detailed_specifications = Column(Text, nullable=True)
    required_model_number = Column(String, nullable=True)
    picture_name_plate = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    application_usage = Column(Text, nullable=True)
    installed_location = Column(String, nullable=True)
    required_brand = Column(String, nullable=True)
    new_replacement = Column(SAEnum(NewReplacement, name="new_replacement_enum"), nullable=True)
    drawing = Column(String, nullable=True)
    layout = Column(String, nullable=True)
    existing_brand_or_model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inquiry = relationship("Inquiry", back_populates="products")


class SpecialInstructions(Base):
    __tablename__ = "special_instructions"
    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), unique=True, nullable=False)
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inquiry = relationship("Inquiry", back_populates="special_instructions")


class Signature(Base):
    __tablename__ = "signatures"
    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), unique=True, nullable=False)
    unisons_sales_rep = Column(String, nullable=True)
    customer_signature = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inquiry = relationship("Inquiry", back_populates="signature")
