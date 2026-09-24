import asyncio
from datetime import datetime, timedelta
import random

from src.backend.config.db import SessionLocal
from src.backend.models.user_model import User, Designation
from src.backend.models.customer_model import Customer, Personnel
from src.backend.models.inquiry_model import (
    Inquiry, InquiryStatus, LocalImport, NewRepeat, MillType,
    StandCode, ArrangementType, NewReplacement,
    AdditionalInquiryInfo, FurnaceDetails, Furnace, CCMDetails,
    RollingMillDetails, RollingMillStand, Product,
    SpecialInstructions, Signature
)
from src.backend.services.ref_id_service import (
    get_next_customer_ref, get_next_personnel_ref, get_next_inquiry_ref,
    get_next_furnace_ref, get_next_product_ref, get_next_stand_ref
)

def seed_database():
    db = SessionLocal()
    try:
        # Ensure we have at least one seller
        seller = db.query(User).filter(User.designation == Designation.seller).first()
        if not seller:
            print("No seller found. Creating one...")
            seller = User(
                username="seed_seller",
                email="seller@example.com",
                password="hashed_password", # doesn't matter for seeding
                designation=Designation.seller
            )
            db.add(seller)
            db.commit()
            db.refresh(seller)

        # Create 5 diverse customers
        customers = []
        sectors = ["Manufacturing", "Steel", "Construction", "Automotive", "Aerospace"]
        for i in range(5):
            customer_ref_id = get_next_customer_ref(db)
            c = Customer(
                customer_ref_id=customer_ref_id,
                customer_name=f"Seed Company {i+1}",
                inquiry_date=datetime.utcnow().date(),
                email=f"contact{i+1}@seedco.com",
                phone=f"+1-555-010{i}",
                sector=sectors[i],
                website=f"www.seedco{i+1}.com",
                factory_address=f"{i*100} Industrial Pkwy, Sector {i}",
                ho_address=f"Downtown Suite {i+1}",
                personnel=[
                    Personnel(
                        personnel_ref_id=get_next_personnel_ref(db),
                        concerned_person=f"John Doe {i}",
                        designation="Plant Manager",
                        department="Operations",
                        email=f"johndoe{i}@seedco.com",
                        phone=f"+1-555-020{i}"
                    )
                ]
            )
            db.add(c)
            db.commit()
            db.refresh(c)
            customers.append(c)

        print("Creating 10 inquiries...")
        statuses = list(InquiryStatus)
        
        for i in range(10):
            cust = random.choice(customers)
            
            # Inquiry
            inquiry_ref_id = get_next_inquiry_ref(db)
            inq = Inquiry(
                inquiry_ref_id=inquiry_ref_id,
                customer_id=cust.id,
                seller_id=seller.id,
                status=random.choice(statuses),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            db.add(inq)
            db.commit()
            db.refresh(inq)

            # Additional Info
            add_info = AdditionalInquiryInfo(
                inquiry_id=inq.id,
                employee="Jane Smith",
                source="Trade Show",
                local_import=random.choice(list(LocalImport)),
                new_repeat=random.choice(list(NewRepeat)),
                repeat_case_no="CASE-XYZ" if random.random() > 0.5 else None,
                req_origin="Email",
                incoterms="FOB",
                department="Sales",
                sub_department="B2B",
                currency="USD"
            )
            db.add(add_info)

            # Furnace Details
            fd = FurnaceDetails(
                inquiry_id=inq.id,
                no_of_furnaces=random.randint(1, 3),
                tpd=float(random.randint(10, 50))
            )
            db.add(fd)
            db.commit()
            db.refresh(fd)

            for j in range(fd.no_of_furnaces):
                f = Furnace(
                    furnace_ref_id=get_next_furnace_ref(db),
                    furnace_details_id=fd.id,
                    furnace_no=f"F-{j+1}",
                    capacity_ton=float(random.randint(5, 20)),
                    capacity_mw=float(random.randint(2, 10))
                )
                db.add(f)
                db.commit()

            # CCM
            ccm = CCMDetails(
                inquiry_id=inq.id,
                radius="6m",
                length_of_tube="12m",
                manual_open_tanky="Yes",
                strands=random.randint(2, 6),
                cmt_size="100x100",
                sgm_size="150x150",
                tundish_nozzle_size="15mm",
                supplier="Global Steel Tech"
            )
            db.add(ccm)

            # Rolling Mill
            rm = RollingMillDetails(
                inquiry_id=inq.id,
                plant_capacity_tpd=float(random.randint(100, 500)),
                plant_capacity_tph=float(random.randint(10, 50)),
                supplier="Mill Builders Inc.",
                total_stands=random.randint(4, 8)
            )
            db.add(rm)
            db.commit()
            db.refresh(rm)

            for j in range(rm.total_stands):
                stand = RollingMillStand(
                    stand_ref_id=get_next_stand_ref(db),
                    rolling_mill_id=rm.id,
                    mill_type=random.choice(list(MillType)),
                    stand_code=random.choice(list(StandCode)),
                    arrangement_type=random.choice(list(ArrangementType))
                )
                db.add(stand)
                db.commit()

            # Products
            for j in range(random.randint(1, 3)):
                prod = Product(
                    product_ref_id=get_next_product_ref(db),
                    inquiry_id=inq.id,
                    product_name=f"Steel Billet Type {j+1}",
                    quantity=float(random.randint(50, 200)),
                    department="Production",
                    no_of_item=random.randint(10, 50),
                    new_replacement=random.choice(list(NewReplacement)),
                    required_brand="UNISONS",
                    detailed_specifications="High tensile strength requirement."
                )
                db.add(prod)
                db.commit()

            # Instructions
            si = SpecialInstructions(
                inquiry_id=inq.id,
                special_instructions="Handle with care. Urgent delivery required."
            )
            db.add(si)

            # Signature
            sig = Signature(
                inquiry_id=inq.id,
                unisons_sales_rep="Alice Rep",
                customer_signature="Bob Client"
            )
            db.add(sig)

            db.commit()
            print(f"Created {inquiry_ref_id}")

        print("Successfully seeded 10 dummy inquiries!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
