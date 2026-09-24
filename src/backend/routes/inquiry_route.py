from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
import io
from datetime import datetime

from src.backend.config.db import get_db
from src.backend.models.inquiry_model import (
    Inquiry, AdditionalInquiryInfo, FurnaceDetails, Furnace,
    CCMDetails, RollingMillDetails, RollingMillStand, Product,
    SpecialInstructions, Signature
)
from src.backend.models.customer_model import Customer, Personnel
from src.backend.models.user_model import User
from src.backend.models.company_model import CompanyProfile
from src.backend.schemas.inquiry_schema import (
    InquiryCreate, InquiryStatusUpdate, InquiryListResponse, InquiryDetailResponse,
    AdditionalInfoCreate, FurnaceDetailsCreate, CCMDetailsCreate,
    RollingMillDetailsCreate, ProductCreate, SpecialInstructionsCreate, SignatureCreate,
    FurnaceItemCreate, RollingMillStandCreate
)
from src.backend.utils.util_helper import get_current_user, require_admin
from src.backend.services.ref_id_service import (
    get_next_inquiry_ref, get_next_furnace_ref, get_next_product_ref, get_next_stand_ref
)
from src.backend.services.ws_manager import manager
from src.backend.services.pdf_service import generate_inquiry_pdf

inquiry_route = APIRouter(prefix="/api/inquiries", tags=["inquiries"])


def load_full_inquiry(inquiry_id: int, db: Session) -> Inquiry:
    inquiry = (
        db.query(Inquiry)
        .options(
            joinedload(Inquiry.customer).joinedload(Customer.personnel),
            joinedload(Inquiry.seller),
            joinedload(Inquiry.additional_info),
            joinedload(Inquiry.furnace_details).joinedload(FurnaceDetails.furnaces),
            joinedload(Inquiry.ccm_details),
            joinedload(Inquiry.rolling_mill_details).joinedload(RollingMillDetails.stands),
            joinedload(Inquiry.products),
            joinedload(Inquiry.special_instructions),
            joinedload(Inquiry.signature),
        )
        .filter(Inquiry.id == inquiry_id)
        .first()
    )
    return inquiry


@inquiry_route.get("", response_model=dict)
def list_inquiries(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    local_import: Optional[str] = Query(None),
    new_repeat: Optional[str] = Query(None),
    sort: Optional[str] = Query("newest"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    q = db.query(Inquiry).outerjoin(Customer).outerjoin(User, Inquiry.seller_id == User.id)
    
    if search:
        q = q.filter(or_(
            Inquiry.inquiry_ref_id.ilike(f"%{search}%"),
            Customer.customer_ref_id.ilike(f"%{search}%"),
            Customer.customer_name.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%"),
            Customer.phone.ilike(f"%{search}%"),
            User.username.ilike(f"%{search}%"),
        ))
    
    if status_filter:
        q = q.filter(Inquiry.status == status_filter)
    
    if sort == "oldest":
        q = q.order_by(Inquiry.created_at.asc())
    elif sort == "updated":
        q = q.order_by(Inquiry.updated_at.desc())
    else:
        q = q.order_by(Inquiry.created_at.desc())
    
    total = q.count()
    inquiries = q.offset(skip).limit(limit).all()
    
    result = []
    for i in inquiries:
        result.append({
            "id": i.id,
            "inquiry_ref_id": i.inquiry_ref_id,
            "status": i.status,
            "customer": {
                "id": i.customer.id,
                "customer_ref_id": i.customer.customer_ref_id,
                "customer_name": i.customer.customer_name,
                "sector": i.customer.sector,
                "phone": i.customer.phone,
                "email": i.customer.email,
            },
            "seller": {"id": i.seller.id, "username": i.seller.username, "email": i.seller.email},
            "created_at": i.created_at,
            "updated_at": i.updated_at,
        })
    return {"total": total, "inquiries": result}


@inquiry_route.post("", status_code=201)
async def create_inquiry(
    data: InquiryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        # Main inquiry
        ref_id = get_next_inquiry_ref(db)
        inquiry = Inquiry(
            inquiry_ref_id=ref_id,
            customer_id=data.customer_id,
            seller_id=current_user["user_id"],
        )
        db.add(inquiry)
        db.flush()
        
        # Additional Info
        if data.additional_info:
            ai = AdditionalInquiryInfo(inquiry_id=inquiry.id, **data.additional_info.model_dump())
            db.add(ai)
        
        # Furnace Details
        if data.furnace_details:
            furnaces_data = data.furnace_details.furnaces or []
            fd_dict = data.furnace_details.model_dump(exclude={"furnaces"})
            fd = FurnaceDetails(inquiry_id=inquiry.id, **fd_dict)
            db.add(fd)
            db.flush()
            for f_item in furnaces_data:
                f_ref = get_next_furnace_ref(db)
                furnace = Furnace(furnace_ref_id=f_ref, furnace_details_id=fd.id, **f_item.model_dump())
                db.add(furnace)
        
        # CCM Details
        if data.ccm_details:
            ccm = CCMDetails(inquiry_id=inquiry.id, **data.ccm_details.model_dump())
            db.add(ccm)
        
        # Rolling Mill Details
        if data.rolling_mill_details:
            stands_data = data.rolling_mill_details.stands or []
            rm_dict = data.rolling_mill_details.model_dump(exclude={"stands"})
            rm = RollingMillDetails(inquiry_id=inquiry.id, **rm_dict)
            db.add(rm)
            db.flush()
            for s_item in stands_data:
                s_ref = get_next_stand_ref(db)
                stand = RollingMillStand(stand_ref_id=s_ref, rolling_mill_id=rm.id, **s_item.model_dump())
                db.add(stand)
        
        # Products
        for p_item in (data.products or []):
            p_ref = get_next_product_ref(db)
            product = Product(product_ref_id=p_ref, inquiry_id=inquiry.id, **p_item.model_dump())
            db.add(product)
        
        # Special Instructions
        if data.special_instructions:
            si = SpecialInstructions(inquiry_id=inquiry.id, **data.special_instructions.model_dump())
            db.add(si)
        
        # Signature
        if data.signature:
            sig = Signature(inquiry_id=inquiry.id, **data.signature.model_dump())
            db.add(sig)
        
        db.commit()
        db.refresh(inquiry)
        
        # Broadcast WebSocket notification
        seller = db.query(User).filter(User.id == current_user["user_id"]).first()
        await manager.broadcast({
            "type": "new_inquiry",
            "inquiry_ref_id": ref_id,
            "customer_name": customer.customer_name,
            "customer_ref_id": customer.customer_ref_id,
            "seller_name": seller.username if seller else "",
            "status": inquiry.status.value,
            "created_at": inquiry.created_at.isoformat(),
        })
        
        return {"status": "success", "message": "Inquiry created", "inquiry_ref_id": ref_id, "id": inquiry.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create inquiry: {str(e)}")


@inquiry_route.get("/{inquiry_id}")
def get_inquiry(inquiry_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    inquiry = load_full_inquiry(inquiry_id, db)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return {
        "id": inquiry.id,
        "inquiry_ref_id": inquiry.inquiry_ref_id,
        "status": inquiry.status,
        "created_at": inquiry.created_at,
        "updated_at": inquiry.updated_at,
        "customer": {
            "id": inquiry.customer.id,
            "customer_ref_id": inquiry.customer.customer_ref_id,
            "customer_name": inquiry.customer.customer_name,
            "sector": inquiry.customer.sector,
            "phone": inquiry.customer.phone,
            "email": inquiry.customer.email,
            "factory_address": inquiry.customer.factory_address,
            "ho_address": inquiry.customer.ho_address,
            "website": inquiry.customer.website,
            "personnel": [
                {"id": p.id, "personnel_ref_id": p.personnel_ref_id, "concerned_person": p.concerned_person,
                 "department": p.department, "designation": p.designation, "email": p.email, "phone": p.phone}
                for p in inquiry.customer.personnel
            ]
        },
        "seller": {"id": inquiry.seller.id, "username": inquiry.seller.username, "email": inquiry.seller.email},
        "additional_info": {
            "id": inquiry.additional_info.id,
            "employee": inquiry.additional_info.employee,
            "source": inquiry.additional_info.source,
            "local_import": inquiry.additional_info.local_import,
            "new_repeat": inquiry.additional_info.new_repeat,
            "repeat_case_no": inquiry.additional_info.repeat_case_no,
            "req_origin": inquiry.additional_info.req_origin,
            "incoterms": inquiry.additional_info.incoterms,
            "department": inquiry.additional_info.department,
            "sub_department": inquiry.additional_info.sub_department,
            "currency": inquiry.additional_info.currency,
        } if inquiry.additional_info else None,
        "furnace_details": {
            "id": inquiry.furnace_details.id,
            "no_of_furnaces": inquiry.furnace_details.no_of_furnaces,
            "tpd": inquiry.furnace_details.tpd,
            "furnaces": [
                {"id": f.id, "furnace_ref_id": f.furnace_ref_id, "furnace_no": f.furnace_no,
                 "capacity_ton": f.capacity_ton, "capacity_mw": f.capacity_mw}
                for f in inquiry.furnace_details.furnaces
            ]
        } if inquiry.furnace_details else None,
        "ccm_details": {
            "id": inquiry.ccm_details.id,
            "radius": inquiry.ccm_details.radius,
            "length_of_tube": inquiry.ccm_details.length_of_tube,
            "manual_open_tanky": inquiry.ccm_details.manual_open_tanky,
            "strands": inquiry.ccm_details.strands,
            "cmt_size": inquiry.ccm_details.cmt_size,
            "sgm_size": inquiry.ccm_details.sgm_size,
            "tundish_nozzle_size": inquiry.ccm_details.tundish_nozzle_size,
            "supplier": inquiry.ccm_details.supplier,
        } if inquiry.ccm_details else None,
        "rolling_mill_details": {
            "id": inquiry.rolling_mill_details.id,
            "plant_capacity_tpd": inquiry.rolling_mill_details.plant_capacity_tpd,
            "plant_capacity_tph": inquiry.rolling_mill_details.plant_capacity_tph,
            "supplier": inquiry.rolling_mill_details.supplier,
            "total_stands": inquiry.rolling_mill_details.total_stands,
            "stands": [
                {"id": s.id, "stand_ref_id": s.stand_ref_id, "mill_type": s.mill_type,
                 "stand_code": s.stand_code, "arrangement_type": s.arrangement_type}
                for s in inquiry.rolling_mill_details.stands
            ]
        } if inquiry.rolling_mill_details else None,
        "products": [
            {"id": p.id, "product_ref_id": p.product_ref_id, "product_name": p.product_name,
             "department": p.department, "remarks": p.remarks, "no_of_item": p.no_of_item,
             "detailed_specifications": p.detailed_specifications, "required_model_number": p.required_model_number,
             "picture_name_plate": p.picture_name_plate, "quantity": p.quantity,
             "application_usage": p.application_usage, "installed_location": p.installed_location,
             "required_brand": p.required_brand, "new_replacement": p.new_replacement,
             "drawing": p.drawing, "layout": p.layout, "existing_brand_or_model": p.existing_brand_or_model}
            for p in inquiry.products
        ],
        "special_instructions": {"id": inquiry.special_instructions.id, "special_instructions": inquiry.special_instructions.special_instructions} if inquiry.special_instructions else None,
        "signature": {"id": inquiry.signature.id, "unisons_sales_rep": inquiry.signature.unisons_sales_rep, "customer_signature": inquiry.signature.customer_signature} if inquiry.signature else None,
    }


@inquiry_route.patch("/{inquiry_id}/status")
def update_inquiry_status(inquiry_id: int, data: InquiryStatusUpdate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    inquiry.status = data.status
    inquiry.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "new_status": data.status}


@inquiry_route.delete("/{inquiry_id}", status_code=204)
def delete_inquiry(inquiry_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    db.delete(inquiry)
    db.commit()


@inquiry_route.get("/{inquiry_id}/pdf")
def download_inquiry_pdf(inquiry_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    inquiry = load_full_inquiry(inquiry_id, db)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    company = db.query(CompanyProfile).first()
    personnel_list = inquiry.customer.personnel if inquiry.customer else []
    furnaces_list = inquiry.furnace_details.furnaces if inquiry.furnace_details else []
    stands_list = inquiry.rolling_mill_details.stands if inquiry.rolling_mill_details else []
    try:
        pdf_bytes = generate_inquiry_pdf(
            inquiry=inquiry,
            company=company,
            customer=inquiry.customer,
            seller=inquiry.seller,
            personnel_list=personnel_list,
            products_list=inquiry.products,
            furnaces_list=furnaces_list,
            stands_list=stands_list,
        )
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=inquiry-{inquiry.inquiry_ref_id}.pdf"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@inquiry_route.put("/{inquiry_id}", response_model=InquiryDetailResponse)
def update_inquiry(inquiry_id: int, data: InquiryCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    # Update Customer
    inquiry.customer_id = data.customer_id
    inquiry.updated_at = datetime.utcnow()

    # Clear old nested relations
    db.query(AdditionalInquiryInfo).filter(AdditionalInquiryInfo.inquiry_id == inquiry_id).delete()
    db.query(FurnaceDetails).filter(FurnaceDetails.inquiry_id == inquiry_id).delete()
    db.query(CCMDetails).filter(CCMDetails.inquiry_id == inquiry_id).delete()
    db.query(RollingMillDetails).filter(RollingMillDetails.inquiry_id == inquiry_id).delete()
    db.query(Product).filter(Product.inquiry_id == inquiry_id).delete()
    db.query(SpecialInstructions).filter(SpecialInstructions.inquiry_id == inquiry_id).delete()
    db.query(Signature).filter(Signature.inquiry_id == inquiry_id).delete()
    db.flush()

    # Recreate relationships
    if data.additional_info:
        db.add(AdditionalInquiryInfo(inquiry_id=inquiry.id, **data.additional_info.model_dump()))
    
    if data.furnace_details:
        fd_data = data.furnace_details.model_dump(exclude={"furnaces"})
        fd = FurnaceDetails(inquiry_id=inquiry.id, **fd_data)
        db.add(fd)
        db.flush()
        for f in data.furnace_details.furnaces:
            db.add(Furnace(furnace_ref_id=get_next_furnace_ref(db), furnace_details_id=fd.id, **f.model_dump()))
            db.flush()
            
    if data.ccm_details:
        db.add(CCMDetails(inquiry_id=inquiry.id, **data.ccm_details.model_dump()))
        
    if data.rolling_mill_details:
        rm_data = data.rolling_mill_details.model_dump(exclude={"stands"})
        rm = RollingMillDetails(inquiry_id=inquiry.id, **rm_data)
        db.add(rm)
        db.flush()
        for s in data.rolling_mill_details.stands:
            db.add(RollingMillStand(stand_ref_id=get_next_stand_ref(db), rolling_mill_id=rm.id, **s.model_dump()))
            db.flush()
            
    if data.products:
        for p in data.products:
            db.add(Product(product_ref_id=get_next_product_ref(db), inquiry_id=inquiry.id, **p.model_dump()))
            db.flush()
            
    if data.special_instructions:
        db.add(SpecialInstructions(inquiry_id=inquiry.id, **data.special_instructions.model_dump()))
        
    if data.signature:
        db.add(Signature(inquiry_id=inquiry.id, **data.signature.model_dump()))

    db.commit()
    
    return get_inquiry(inquiry_id, db, current_user)
