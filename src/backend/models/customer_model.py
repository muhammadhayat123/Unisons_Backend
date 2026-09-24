from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from src.backend.config.db import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    customer_ref_id = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    inquiry_date = Column(Date, nullable=True)
    sector = Column(String, nullable=True)
    factory_address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    ho_address = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    personnel = relationship("Personnel", back_populates="customer", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="customer")

class Personnel(Base):
    __tablename__ = "personnel"
    id = Column(Integer, primary_key=True, index=True)
    personnel_ref_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    concerned_person = Column(String, nullable=False)
    department = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer = relationship("Customer", back_populates="personnel")
