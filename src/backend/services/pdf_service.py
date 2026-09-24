import io
import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

DARK_CHARCOAL = colors.HexColor("#111827")
LIGHT_GRAY = colors.HexColor("#f3f4f6")
BORDER_COLOR = colors.HexColor("#d1d5db")
WHITE = colors.white

LOGO_PATH = str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'signup' / 'public' / 'logo.png')

def val(v) -> str:
    if v is None or str(v).strip() == "":
        return ""
    if hasattr(v, 'value'):
        return str(v.value)
    return str(v)

def cell(text, bold=False, align=TA_LEFT, size=7.5, text_color=DARK_CHARCOAL, underline=False):
    style = ParagraphStyle(
        'Cell',
        fontName='Helvetica-Bold' if bold else 'Helvetica',
        fontSize=size,
        leading=size + 2,
        alignment=align,
        textColor=text_color
    )
    if underline:
        text = f"<u>{text}</u>"
    return Paragraph(text, style)

def get_base_table_style():
    return TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ])

def section_title(text):
    t = Table([[cell(text, bold=True, size=8.5)]], colWidths=[539])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    return [Spacer(1, 4), t, Spacer(1, 2)]

def generate_inquiry_pdf(inquiry, company, customer, seller, personnel_list, products_list, furnaces_list, stands_list) -> bytes:
    buffer = io.BytesIO()
    
    # A4 is 595.27 x 841.89 points
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28,
        title=f"Inquiry {inquiry.inquiry_ref_id}",
    )
    
    story = []

    # --- 1. HEADER ---
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=4*cm, height=1.2*cm, kind='proportional')
        except:
            logo = cell("UNISONS", bold=True, size=16)
    else:
        logo = cell("UNISONS", bold=True, size=16)

    contact_str = "<b>Email:</b> uss@unisons.com.pk &nbsp; | &nbsp; <b>Mobile:</b> +92 346-55-55-22-6 &nbsp; | &nbsp; <b>Website:</b> unisons.com.pk"
    
    header_data = [
        [logo, cell(inquiry.inquiry_ref_id, bold=True, size=14, align=TA_CENTER), cell("CUSTOMER INQUIRY FORM", bold=True, size=14, align=TA_RIGHT)]
    ]
    t_header = Table(header_data, colWidths=[150, 100, 289])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_header)

    meta_data = [
        [cell(contact_str, size=6, text_color=colors.HexColor("#4b5563")), cell(f"<b>Date:</b> <u>{inquiry.created_at.strftime('%d/%m/%y')}</u>", align=TA_CENTER), cell(f"<b>Sector:</b> <u>{val(customer.sector) if customer else ''}</u>", align=TA_RIGHT)]
    ]
    t_meta = Table(meta_data, colWidths=[150, 200, 189])
    story.append(t_meta)
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_CHARCOAL, spaceBefore=4, spaceAfter=2))

    # --- 2. CUSTOMER DETAILS ---
    story.extend(section_title("Customer Details"))
    c_row1 = Table([[cell("<b>Customer:</b>"), cell(val(customer.customer_name if customer else ''), underline=True), cell("<b>H.O Address:</b>", align=TA_RIGHT), cell(val(customer.ho_address if customer else ''), underline=True)]], colWidths=[50, 230, 60, 199])
    c_row2 = Table([[cell("<b>Factory Address:</b>"), cell(val(customer.factory_address if customer else ''), underline=True), cell("<b>Phone:</b>", align=TA_RIGHT), cell(val(customer.phone if customer else ''), underline=True), cell("<b>Website:</b>", align=TA_RIGHT), cell(val(customer.website if customer else ''), underline=True), cell("<b>Email:</b>", align=TA_RIGHT), cell(val(customer.email if customer else ''), underline=True)]], colWidths=[70, 130, 30, 70, 40, 80, 30, 89])
    c_row1.setStyle(get_base_table_style())
    c_row2.setStyle(get_base_table_style())
    story.append(c_row1)
    story.append(c_row2)

    # --- 3. PERSONNEL DETAILS ---
    story.extend(section_title("Personnel Details"))
    p_head = [[cell("Concerned Person", bold=True, align=TA_CENTER), cell("Department", bold=True, align=TA_CENTER), cell("Designation", bold=True, align=TA_CENTER), cell("Email", bold=True, align=TA_CENTER), cell("Phone", bold=True, align=TA_CENTER)]]
    p_rows = []
    if personnel_list:
        for p in personnel_list:
            p_rows.append([cell(val(p.concerned_person), align=TA_CENTER), cell(val(p.department), align=TA_CENTER), cell(val(p.designation), align=TA_CENTER), cell(val(p.email), align=TA_CENTER), cell(val(p.phone), align=TA_CENTER)])
    else:
        p_rows.append([cell(""), cell(""), cell(""), cell(""), cell("")])
    
    t_pers = Table(p_head + p_rows, colWidths=[120, 100, 100, 120, 99])
    t_pers.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_pers)

    # --- 4. ADDITIONAL INFO ---
    story.extend(section_title("Additional Information (Mandatory)"))
    ai = inquiry.additional_info
    
    li_val = val(ai.local_import if ai else "")
    chk_local = "[X]" if li_val.lower() == "local" else "[ ]"
    chk_import = "[X]" if li_val.lower() == "import" else "[ ]"
    
    nr_val = val(ai.new_repeat if ai else "")
    chk_new = "[X]" if nr_val.lower() == "new" else "[ ]"
    chk_repeat = "[X]" if nr_val.lower() == "repeat" else "[ ]"

    ai_row1 = Table([[
        cell("<b>Employee:</b>"), cell(val(ai.employee if ai else ""), underline=True),
        cell("<b>Source:</b>"), cell(val(ai.source if ai else ""), underline=True),
        cell(f"Local/Import &nbsp; {chk_local} Local &nbsp; {chk_import} Import"),
        cell(f"New/Repeat &nbsp; {chk_new} New &nbsp; {chk_repeat} Repeat"),
        cell("<b>Repeat Case#:</b>"), cell(val(ai.repeat_case_no if ai else ""), underline=True)
    ]], colWidths=[45, 80, 40, 80, 110, 100, 50, 34])
    
    ai_row2 = Table([[
        cell("<b>Req. Origin:</b>"), cell(val(ai.req_origin if ai else ""), underline=True),
        cell("<b>IncoTerms:</b>", align=TA_RIGHT), cell(val(ai.incoterms if ai else ""), underline=True),
        cell("<b>Dept.:</b>", align=TA_RIGHT), cell(val(ai.department if ai else ""), underline=True),
        cell("<b>Sub Dept.:</b>", align=TA_RIGHT), cell(val(ai.sub_department if ai else ""), underline=True),
        cell("<b>Currency:</b>", align=TA_RIGHT), cell(val(ai.currency if ai else ""), underline=True)
    ]], colWidths=[50, 80, 50, 70, 30, 80, 50, 70, 40, 19])
    
    ai_row1.setStyle(get_base_table_style())
    ai_row2.setStyle(get_base_table_style())
    story.append(ai_row1)
    story.append(ai_row2)

    # --- 5. FURNACE DETAILS ---
    story.extend(section_title("Furnace Details (Optional for New Customers)"))
    fd = inquiry.furnace_details
    no_furnaces = val(fd.no_of_furnaces if fd else "")
    tpd = val(fd.tpd if fd else "")

    f_cols = []
    for i in range(6):
        if i < len(furnaces_list):
            f = furnaces_list[i]
            f_cols.extend([val(f.capacity_ton), val(f.capacity_mw), val(f.furnace_no)])
        else:
            f_cols.extend(["", "", ""])
            
    f_data = [
        [cell(""), cell(""), cell("Ton", align=TA_CENTER), cell("MW", align=TA_CENTER), cell("No.", align=TA_CENTER), cell("Ton", align=TA_CENTER), cell("MW", align=TA_CENTER), cell("No.", align=TA_CENTER), cell("Ton", align=TA_CENTER), cell("MW", align=TA_CENTER), cell("No.", align=TA_CENTER), cell("Ton", align=TA_CENTER), cell("MW", align=TA_CENTER), cell("No.", align=TA_CENTER), cell("Ton", align=TA_CENTER), cell("MW", align=TA_CENTER), cell("No.", align=TA_CENTER), cell("Ton", align=TA_CENTER), cell("MW", align=TA_CENTER), cell("No.", align=TA_CENTER), cell("")],
        [cell("No. Of Furnaces", align=TA_RIGHT), cell(no_furnaces, align=TA_CENTER), cell("Capacity", align=TA_RIGHT),
         cell(f_cols[0], align=TA_CENTER), cell(f_cols[1], align=TA_CENTER), cell(f_cols[2], align=TA_CENTER),
         cell(f_cols[3], align=TA_CENTER), cell(f_cols[4], align=TA_CENTER), cell(f_cols[5], align=TA_CENTER),
         cell(f_cols[6], align=TA_CENTER), cell(f_cols[7], align=TA_CENTER), cell(f_cols[8], align=TA_CENTER),
         cell(f_cols[9], align=TA_CENTER), cell(f_cols[10], align=TA_CENTER), cell(f_cols[11], align=TA_CENTER),
         cell(f_cols[12], align=TA_CENTER), cell(f_cols[13], align=TA_CENTER), cell(f_cols[14], align=TA_CENTER),
         cell(f_cols[15], align=TA_CENTER), cell(f_cols[16], align=TA_CENTER), cell(f_cols[17], align=TA_CENTER),
         cell("TPD", align=TA_RIGHT), cell(tpd, align=TA_CENTER)]
    ]
    t_furnace = Table(f_data, colWidths=[65, 30, 45, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 25, 30])
    t_furnace.setStyle(TableStyle([
        ('GRID', (1, 1), (1, 1), 0.5, DARK_CHARCOAL),
        ('GRID', (3, 1), (20, 1), 0.5, DARK_CHARCOAL),
        ('GRID', (22, 1), (22, 1), 0.5, DARK_CHARCOAL),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 1),
        ('RIGHTPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(t_furnace)

    # --- 6. CCM DETAILS ---
    story.extend(section_title("CCM Details (Optional for New Customers)"))
    ccm = inquiry.ccm_details
    ccm_row1 = Table([[
        cell("Radius"), cell(val(ccm.radius if ccm else ""), underline=True),
        cell("Length of Tube", align=TA_RIGHT), cell(val(ccm.length_of_tube if ccm else ""), underline=True),
        cell("Manual/Open Tanky", align=TA_RIGHT), cell(val(ccm.manual_open_tanky if ccm else ""), underline=True),
        cell("Strands", align=TA_RIGHT), cell(val(ccm.strands if ccm else ""), underline=True),
        cell("CMT Size", align=TA_RIGHT), cell(val(ccm.cmt_size if ccm else ""), underline=True)
    ]], colWidths=[35, 55, 60, 55, 80, 55, 35, 30, 45, 89])
    
    ccm_row2 = Table([[
        cell("SGM Size"), cell(val(ccm.sgm_size if ccm else ""), underline=True),
        cell("Tundish Nozzle Size", align=TA_RIGHT), cell(val(ccm.tundish_nozzle_size if ccm else ""), underline=True),
        cell("Supplier", align=TA_RIGHT), cell(val(ccm.supplier if ccm else ""), underline=True)
    ]], colWidths=[45, 60, 90, 60, 40, 244])
    ccm_row1.setStyle(get_base_table_style())
    ccm_row2.setStyle(get_base_table_style())
    story.append(ccm_row1)
    story.append(ccm_row2)

    # --- 7. ROLLING MILL DETAILS ---
    story.extend(section_title("Rolling Mill Details (Optional for New Customers)"))
    rm = inquiry.rolling_mill_details
    rm_top = Table([[
        cell("Plant Capacity (TPD)"), cell(val(rm.plant_capacity_tpd if rm else ""), underline=True),
        cell("Plant Capacity (TPH)", align=TA_RIGHT), cell(val(rm.plant_capacity_tph if rm else ""), underline=True),
        cell("Supplier", align=TA_RIGHT), cell(val(rm.supplier if rm else ""), underline=True)
    ]], colWidths=[90, 80, 90, 80, 40, 159])
    rm_top.setStyle(get_base_table_style())
    story.append(rm_top)
    story.append(Spacer(1, 4))

    stand_dict = {val(hasattr(s.stand_code, 'value') and s.stand_code.value or s.stand_code): s for s in stands_list}
    
    rm_data = [
        [cell("Total Stands: " + val(rm.total_stands if rm else ""), bold=True), cell("Fully Continuous", align=TA_CENTER), cell("Roughing Mill", align=TA_CENTER), "", "", cell("Intermediate Mill", align=TA_CENTER), "", "", cell("Finishing Mill", align=TA_CENTER), "", ""],
        [cell("Types of Mill/Stand Arrangement", bold=True), cell(""), cell("RM 1", align=TA_CENTER), cell("RM 2", align=TA_CENTER), cell("RM 3", align=TA_CENTER), cell("IM 1", align=TA_CENTER), cell("IM 2", align=TA_CENTER), cell("IM 3", align=TA_CENTER), cell("FM 1", align=TA_CENTER), cell("FM 2", align=TA_CENTER), cell("FM 3", align=TA_CENTER)]
    ]
    
    r_mill = [cell("Repeater-R/Continuous-C\n/Fully Continuous-FC"), cell("")]
    r_type = [cell(""), cell("")]
    
    for code in ['RM 1', 'RM 2', 'RM 3', 'IM 1', 'IM 2', 'IM 3', 'FM 1', 'FM 2', 'FM 3']:
        lookup = code.replace(" ", "_")
        s = stand_dict.get(lookup) or stand_dict.get(code)
        if s:
            r_mill.append(cell(val(hasattr(s.arrangement_type, 'value') and s.arrangement_type.value or s.arrangement_type), align=TA_CENTER))
            r_type.append(cell(val(hasattr(s.mill_type, 'value') and s.mill_type.value or s.mill_type), align=TA_CENTER))
        else:
            r_mill.append(cell(""))
            r_type.append(cell(""))
            
    rm_data.append(r_type)
    rm_data.append(r_mill)
    
    t_rm = Table(rm_data, colWidths=[150, 65, 36, 36, 36, 36, 36, 36, 36, 36, 36])
    t_rm.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('SPAN', (2, 0), (4, 0)), # Roughing
        ('SPAN', (5, 0), (7, 0)), # Intermediate
        ('SPAN', (8, 0), (10, 0)),# Finishing
        ('SPAN', (0, 2), (1, 2)), # Empty cell span left headers
        ('SPAN', (0, 3), (1, 3)),
        ('BACKGROUND', (0, 0), (-1, 1), LIGHT_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(t_rm)

    # --- 8. PRODUCT DETAILS ---
    story.extend(section_title("Product Details (Completion of all fields is required)"))
    
    if products_list:
        for idx, p in enumerate(products_list):
            if idx > 0:
                story.append(Spacer(1, 10))
            
            p_data = [
                [cell("Description", bold=True, align=TA_CENTER), cell("Department", bold=True, align=TA_CENTER), cell("Remarks", bold=True, align=TA_CENTER)],
                [cell("Product Name", align=TA_CENTER), cell(val(p.product_name), align=TA_CENTER), cell(val(p.remarks))],
                [cell("No. of Item/Specify Individual", align=TA_CENTER), cell(val(p.no_of_item), align=TA_CENTER), ""],
                [cell("Detailed Specifications", align=TA_CENTER), cell(val(p.detailed_specifications), align=TA_CENTER), ""],
                [cell("Required Model Number", align=TA_CENTER), cell(val(p.required_model_number), align=TA_CENTER), ""],
                [cell("Picture/Name Plate", align=TA_CENTER), cell(val(p.picture_name_plate), align=TA_CENTER), ""],
                [cell("Quantity", align=TA_CENTER), cell(val(p.quantity), align=TA_CENTER), ""],
                [cell("Application & Usage", align=TA_CENTER), cell(val(p.application_usage), align=TA_CENTER), ""],
                [cell("Installed Location", align=TA_CENTER), cell(val(p.installed_location), align=TA_CENTER), ""],
                [cell("Required Brand (If Suggested)", align=TA_CENTER), cell(val(p.required_brand), align=TA_CENTER), ""],
                [cell("New/Replacement", align=TA_CENTER), cell(val(hasattr(p.new_replacement, 'value') and p.new_replacement.value or p.new_replacement), align=TA_CENTER), ""],
                [cell("Drawing", align=TA_CENTER), cell(val(p.drawing), align=TA_CENTER), ""],
                [cell("Layout", align=TA_CENTER), cell(val(p.layout), align=TA_CENTER), ""],
                [cell("Existing Brand or Model", align=TA_CENTER), cell(val(p.existing_brand_or_model), align=TA_CENTER), ""]
            ]
            t_prod = Table(p_data, colWidths=[150, 150, 239])
            t_prod.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
                ('BACKGROUND', (0, 1), (0, -1), LIGHT_GRAY),
                ('SPAN', (2, 1), (2, 13)), 
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('VALIGN', (2, 1), (2, 13), 'TOP'),
                ('LEFTPADDING', (2, 1), (2, 13), 6),
                ('TOPPADDING', (2, 1), (2, 13), 6),
            ]))
            story.append(t_prod)
    else:
        p_data = [
            [cell("Description", bold=True, align=TA_CENTER), cell("Department", bold=True, align=TA_CENTER), cell("Remarks", bold=True, align=TA_CENTER)],
            [cell("Product Name", align=TA_CENTER), "", ""],
            [cell("No. of Item/Specify Individual", align=TA_CENTER), "", ""],
            [cell("Detailed Specifications", align=TA_CENTER), "", ""],
            [cell("Required Model Number", align=TA_CENTER), "", ""],
            [cell("Picture/Name Plate", align=TA_CENTER), "", ""],
            [cell("Quantity", align=TA_CENTER), "", ""],
            [cell("Application & Usage", align=TA_CENTER), "", ""],
            [cell("Installed Location", align=TA_CENTER), "", ""],
            [cell("Required Brand", align=TA_CENTER), "", ""],
            [cell("New/Replacement", align=TA_CENTER), "", ""],
            [cell("Drawing", align=TA_CENTER), "", ""],
            [cell("Layout", align=TA_CENTER), "", ""],
            [cell("Existing Brand", align=TA_CENTER), "", ""]
        ]
        t_prod = Table(p_data, colWidths=[150, 150, 239])
        t_prod.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
            ('BACKGROUND', (0, 1), (0, -1), LIGHT_GRAY),
            ('SPAN', (2, 1), (2, 13)),
        ]))
        story.append(t_prod)

    # --- 9. SPECIAL INSTRUCTIONS & SIGNATURES ---
    story.extend(section_title("Special Instructions (If Any)"))
    si_val = val(inquiry.special_instructions.special_instructions if inquiry.special_instructions else "")
    t_si = Table([[cell(si_val)]], colWidths=[539], minRowHeights=[30])
    t_si.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('PADDING', (0, 0), (-1, -1), 4)]))
    story.append(t_si)
    story.append(Spacer(1, 15))

    sig = inquiry.signature
    sig_data = [
        [cell(val(sig.unisons_sales_rep if sig else ""), align=TA_CENTER, underline=True), "", cell(val(sig.customer_signature if sig else ""), align=TA_CENTER, underline=True)],
        [cell("Unisons Sales Rep", align=TA_CENTER), "", cell("Customer", align=TA_CENTER)]
    ]
    t_sig = Table(sig_data, colWidths=[150, 239, 150])
    story.append(t_sig)

    doc.build(story)
    return buffer.getvalue()
