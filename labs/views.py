from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from accounts.decorators import lab_tech_only
from doctors.models import LabRequest
from .utils import generate_lab_pdf
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

@login_required
@lab_tech_only
def lab_dashboard(request):
    """
    Advanced Lab Dashboard: Tracks the queue, monthly stats, 
    and provides data for analytics charts.
    """
    # 1. THE QUEUE: Tests that are ready to be worked on
    # Assuming 'paid' or 'pending' is the starting status for the lab
    queue = LabRequest.objects.filter(status='pending').select_related(
        'medical_record__patient__user'
    ).order_by('created_at')
    
    # 2. RECENT ACTIVITY: The last 5 tests completed
    recent_completions = LabRequest.objects.filter(status='completed').select_related(
        'medical_record__patient__user'
    ).order_by('-updated_at')[:5]
    
    # 3. STATS: Monthly performance tracking
    current_date = timezone.now()
    total_monthly_tests = LabRequest.objects.filter(
        status='completed', 
        updated_at__month=current_date.month,
        updated_at__year=current_date.year
    ).count()

    # 4. CHART DATA: Group tests by name for the bar chart
    test_distribution = LabRequest.objects.filter(
        updated_at__month=current_date.month
    ).values('test_name').annotate(count=Count('id')).order_by('-count')[:5]

    context = {
        'queue': queue,
        'recent_completions': recent_completions,
        'waiting_count': queue.count(),
        'total_monthly_tests': total_monthly_tests,
        'current_month_name': current_date.strftime('%B'),
        'chart_labels': [item['test_name'] for item in test_distribution] or ['No Data'],
        'chart_data': [item['count'] for item in test_distribution] or [0],
    }
    return render(request, 'labs/dashboard.html', context)

@login_required
@lab_tech_only
def submit_lab_result(request, test_id):
    """
    Captures findings and optional file attachments (PDFs/Images).
    """
    if request.method == 'POST':
        test = get_object_or_404(LabRequest, id=test_id)
        
        # Capture the lab findings
        test.findings = request.POST.get('findings')
        
        # Handle paperless attachments (Scans, X-rays, etc.)
        if 'attachment' in request.FILES:
            test.attachment = request.FILES['attachment']
            
        test.status = 'completed'
        test.updated_at = timezone.now() # Track when results were ready
        test.save()
        
        patient_name = test.medical_record.patient.user.get_full_name()
        messages.success(request, f"Results for {patient_name} submitted successfully!")
        
    return redirect('lab_dashboard')



@login_required
@lab_tech_only
def print_lab_report(request, test_id):
    test = get_object_or_404(LabRequest, id=test_id)
    
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- Header Section ---
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height - 50, "CITY GENERAL HOSPITAL")
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, height - 65, "123 Medical Drive, Health City | Tel: +233 555 0123")
    p.drawCentredString(width/2, height - 80, "Official Laboratory Investigation Report")
    
    p.line(50, height - 100, width - 50, height - 100)

    # --- Patient & Test Info ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 130, f"Patient Name: {test.medical_record.patient.user.get_full_name()}")
    p.drawString(50, height - 150, f"Patient ID: #PT-{test.medical_record.patient.patient_id}")
    p.drawString(350, height - 130, f"Date: {test.updated_at.strftime('%d %b %Y')}")
    p.drawString(350, height - 150, f"Test Type: {test.test_name}")

    p.line(50, height - 170, width - 50, height - 170)

    # --- Results Section ---
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 200, "INVESTIGATION FINDINGS")
    
    p.setFont("Helvetica", 12)
    # Using textobject to handle multiline findings
    text_object = p.beginText(50, height - 230)
    text_object.setFont("Helvetica", 11)
    text_object.setLeading(15)
    
    # Wrap text if findings are long
    lines = test.findings.split('\n')
    for line in lines:
        text_object.textLine(line)
    p.drawText(text_object)

    # --- Footer / Signatures ---
    p.line(50, 150, 200, 150)
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(50, 135, "Lab Technician Signature")
    
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 30, "This is a computer-generated report. No physical signature required.")

    # Finalize PDF
    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename=f"Lab_Report_{test.id}.pdf")



@login_required
@lab_tech_only
def email_lab_report(request, test_id):
    test = get_object_or_404(LabRequest, id=test_id)
    patient_user = test.medical_record.patient.user
    
    if not patient_user.email:
        messages.error(request, "Error: Patient has no email address on file.")
        return redirect('lab_dashboard')

    # Generate PDF using the helper
    pdf_content = generate_lab_pdf(test)

    # Prepare Email
    subject = f"Your Lab Results: {test.test_name}"
    message_body = render_to_string('labs/email_template.txt', {
        'patient_name': patient_user.get_full_name(),
        'test_name': test.test_name,
    })

    email = EmailMessage(
        subject,
        message_body,
        settings.DEFAULT_FROM_EMAIL,
        [patient_user.email],
    )
    
    # Attach the PDF
    email.attach(f"Lab_Result_{test.id}.pdf", pdf_content, 'application/pdf')

    try:
        email.send()
        messages.success(request, f"Email sent successfully to {patient_user.email}")
    except Exception as e:
        messages.error(request, "Failed to send email. Check SMTP settings.")
    
    return redirect('lab_dashboard')


