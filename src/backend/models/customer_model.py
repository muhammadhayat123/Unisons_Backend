from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.backend.config.db import Base

class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    customer_ref_id = Column(String, unique=True, index=True, nullable=False)
    sector = Column(String, nullable=False)
    party = Column(String, nullable=True)
    customer_name = Column(String, nullable=False)
    customer_initials = Column(String, nullable=True)
    ho_address = Column(Text, nullable=False)
    factory_address = Column(Text, nullable=True)
    city = Column(String, nullable=False)
    website = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    ntn = Column(String, nullable=True)
    gst = Column(String, nullable=True)
    cnic = Column(String, nullable=True)
    cust_relation = Column(String, nullable=True)
    cust_priority = Column(String, nullable=True)
    cust_type = Column(String, nullable=False)
    cust_culture = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    payment_terms = Column(String, nullable=True)
    tax_type = Column(String, nullable=True)
    sales_rep_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    additional_details = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    personnel = relationship("PersonnelModel", back_populates="customer", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="customer")
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])

class PersonnelModel(Base):
    __tablename__ = "personnel"
    id = Column(Integer, primary_key=True, index=True)
    personnel_ref_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    cp_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    desg = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("CustomerModel", back_populates="personnel")
