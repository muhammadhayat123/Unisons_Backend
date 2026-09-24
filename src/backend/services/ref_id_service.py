from sqlalchemy.orm import Session

def generate_ref_id(prefix: str, count: int) -> str:
    return f"{prefix}-{count:04d}"

def get_next_customer_ref(db: Session) -> str:
    from src.backend.models.customer_model import Customer
    count = db.query(Customer).count() + 1
    return generate_ref_id("CUS", count)

def get_next_personnel_ref(db: Session) -> str:
    from src.backend.models.customer_model import Personnel
    count = db.query(Personnel).count() + 1
    return generate_ref_id("PER", count)

def get_next_inquiry_ref(db: Session) -> str:
    from src.backend.models.inquiry_model import Inquiry
    count = db.query(Inquiry).count() + 1
    return generate_ref_id("INQ", count)

def get_next_furnace_ref(db: Session) -> str:
    from src.backend.models.inquiry_model import Furnace
    count = db.query(Furnace).count() + 1
    return generate_ref_id("FUR", count)

def get_next_product_ref(db: Session) -> str:
    from src.backend.models.inquiry_model import Product
    count = db.query(Product).count() + 1
    return generate_ref_id("PRD", count)

def get_next_stand_ref(db: Session) -> str:
    from src.backend.models.inquiry_model import RollingMillStand
    count = db.query(RollingMillStand).count() + 1
    return generate_ref_id("STD", count)
