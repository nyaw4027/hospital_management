from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum
from django.utils import timezone
from django.http import FileResponse
from django.db import transaction
import io

# PDF Imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from .models import DispensingLog

# Model Imports
from doctors.models import Prescription
from accounts.models import Medicine  # Ensure this path is correct for your project

@login_required
@user_passes_test(lambda u: u.role == 'pharmacist')
def pharmacy_dashboard(request):
    """Unified Pharmacy Dashboard: Handles Inventory and Dispensing Queues"""
    if request.user.role not in ['pharmacist', 'manager']:
        messages.error(request, "Access denied. Pharmacist role required.")
        return redirect('dashboard')

    # 1. Incoming Prescriptions (Paid for in Cashier, ready for pickup)
    prescriptions = Prescription.objects.filter(
        status='paid'
    ).select_related('patient__user', 'doctor').order_by('-created_at')

    # 2. Inventory Watchlist (For the side table)
    inventory = Medicine.objects.all().order_by('quantity')

    # 3. Card Stats for the Top Row
    total_drugs = Medicine.objects.count()
    low_stock = Medicine.objects.filter(quantity__lte=F('reorder_level')).count()
    pending_count = Prescription.objects.filter(status='pending').count()
    
    # Calculate Today's Sales
    today = timezone.now().date()
    today_sales = Prescription.objects.filter(
        status='dispensed', 
        updated_at__date=today
    ).aggregate(total=Sum('price'))['total'] or 0.00

    context = {
        'prescriptions': prescriptions,
        'inventory': inventory,
        'total_drugs': total_drugs,
        'low_stock': low_stock,
        'today_sales': today_sales,
        'pending_count': pending_count,
    }

    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def update_prescription_status(request, record_id):
    if request.user.role not in ['pharmacist', 'manager']:
        messages.error(request, "Unauthorized.")
        return redirect('dashboard')

    if request.method == 'POST':
        prescription = get_object_or_404(Prescription, id=record_id)
        medicine = Medicine.objects.filter(name__iexact=prescription.medication_name).first()
        qty_to_deduct = getattr(prescription, 'quantity', 1) 

        try:
            with transaction.atomic():
                if medicine:
                    if medicine.expiry_date and medicine.expiry_date <= timezone.now().date():
                        messages.error(request, f"DISPENSING BLOCKED: {medicine.name} expired!")
                        return redirect('pharmacy_dashboard')

                    if medicine.quantity >= qty_to_deduct:
                        medicine.quantity -= qty_to_deduct
                        medicine.save()
                        
                        prescription.status = 'dispensed'
                        prescription.save()

                        # --- ADD AUDIT LOG HERE ---
                        DispensingLog.objects.create(
                            pharmacist=request.user,
                            patient_name=prescription.patient.get_full_name() if hasattr(prescription.patient, 'get_full_name') else str(prescription.patient),
                            medication_name=medicine.name,
                            quantity_dispensed=qty_to_deduct,
                            notes=f"Prescription ID: {prescription.id}"
                        )
                        # -------------------------

                        messages.success(request, f"Dispensed {qty_to_deduct} unit(s) of {medicine.name} and logged.")
                    else:
                        messages.error(request, f"Insufficient stock! Available: {medicine.quantity}")
                        return redirect('pharmacy_dashboard')
                else:
                    prescription.status = 'dispensed'
                    prescription.save()
                    
                    # Optional: Log even if medicine isn't in inventory
                    DispensingLog.objects.create(
                        pharmacist=request.user,
                        patient_name=str(prescription.patient),
                        medication_name=prescription.medication_name,
                        quantity_dispensed=qty_to_deduct,
                        notes="DISPENSED UNTRACKED ITEM"
                    )
                    messages.warning(request, "Dispensed (Untracked item logged).")
        
        except Exception as e:
            messages.error(request, f"A system error occurred: {str(e)}")
            
    return redirect('pharmacy_dashboard')

@login_required
def add_medicine_stock(request):
    """Handles adding new medicine via the Modal"""
    if request.method == 'POST':
        Medicine.objects.create(
            name=request.POST.get('name'),
            category=request.POST.get('category'),
            price_per_unit=request.POST.get('price'),
            quantity=request.POST.get('quantity'),
            reorder_level=request.POST.get('reorder_level', 10)
        )
        messages.success(request, "New stock registered successfully!")
    return redirect('pharmacy_dashboard')

@login_required
def generate_inventory_report(request):
    """Generates the PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("HMS CORE - PHARMACY INVENTORY REPORT", styles['Title']))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    data = [['Medicine Name', 'Category', 'Price (GHS)', 'Stock', 'Status']]
    for med in Medicine.objects.all().order_by('name'):
        status = "LOW" if med.quantity <= med.reorder_level else "OK"
        data.append([med.name, med.category, f"{med.price_per_unit:.2f}", med.quantity, status])

    table = Table(data, colWidths=[150, 100, 80, 60, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='Inventory_Report.pdf')


@login_required
def stock_alerts_summary(request):
    if request.user.role != 'manager':
        return redirect('dashboard')
        
    from .utils import get_inventory_alert_data
    context = get_inventory_alert_data()
    return render(request, 'pharmacy/alerts_summary.html', context)


@login_required
def pharmacy_audit_logs(request):
    if request.user.role != 'manager':
        messages.error(request, "Access restricted to Managers.")
        return redirect('dashboard')

    logs = DispensingLog.objects.all().select_related('pharmacist')

    # Simple Search/Filter Logic
    query = request.GET.get('q')
    if query:
        logs = logs.filter(
            models.Q(patient_name__icontains=query) | 
            models.Q(medication_name__icontains=query) |
            models.Q(pharmacist__last_name__icontains=query)
        )

    context = {
        'logs': logs[:100], # Limit to last 100 for performance
    }
    return render(request, 'pharmacy/audit_logs.html', context)





