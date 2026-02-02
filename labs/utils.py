import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def generate_lab_pdf(test):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 50, "CITY GENERAL HOSPITAL - LABORATORY")
    
    # Patient Info
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Patient: {test.medical_record.patient.user.get_full_name()}")
    p.drawString(50, height - 120, f"Test: {test.test_name}")
    p.drawString(50, height - 140, f"Date: {test.updated_at.strftime('%Y-%m-%d %H:%M')}")
    
    p.line(50, height - 150, width - 50, height - 150)

    # Findings
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 180, "Clinical Findings:")
    
    p.setFont("Helvetica", 11)
    text_object = p.beginText(50, height - 200)
    for line in test.findings.split('\n'):
        text_object.textLine(line)
    p.drawText(text_object)

    p.showPage()
    p.save()
    
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data