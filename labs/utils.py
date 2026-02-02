import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def generate_lab_pdf(test):
    """Returns raw PDF bytes for a Lab Investigation Report"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width/2, height - 60, "CITY GENERAL HOSPITAL")
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, height - 75, "Diagnostic Services Division | Tel: +233 555 0123")
    p.line(50, height - 90, width - 50, height - 90)

    # Patient Details Table-like layout
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 120, f"PATIENT: {test.medical_record.patient.user.get_full_name().upper()}")
    p.drawString(50, height - 135, f"ID: #PT-{test.medical_record.patient.patient_id}")
    p.drawString(350, height - 120, f"DATE: {test.updated_at.strftime('%d %b %Y')}")
    p.drawString(350, height - 135, f"TEST: {test.test_name}")

    p.line(50, height - 150, width - 50, height - 150)

    # Findings
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 180, "CLINICAL FINDINGS & RESULTS")
    
    p.setFont("Helvetica", 12)
    text_object = p.beginText(50, height - 210)
    text_object.setLeading(18)
    
    # Auto-wrap basic text
    lines = test.findings.split('\n')
    for line in lines:
        text_object.textLine(line)
    p.drawText(text_object)

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 100, f"Authorized by: {test.lab_tech_name if hasattr(test, 'lab_tech_name') else 'On-duty Technician'}")
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 30, "This document is an official medical record. Forged copies are subject to legal action.")

    p.showPage()
    p.save()
    
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value