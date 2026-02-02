from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum
from django.utils import timezone
from django.http import FileResponse
import io

# PDF Imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# Model Imports
from doctors.models import Prescription
from accounts.models import Medicine  # Ensure this path is correct for your project

@login_required
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
    """Handles the actual dispensing and inventory deduction"""
    if request.method == 'POST':
        prescription = get_object_or_404(Prescription, id=record_id)
        
        # We match medication_name from Prescription to name in Medicine
        medicine = Medicine.objects.filter(name__iexact=prescription.medication_name).first()
        
        if medicine:
            if medicine.quantity >= 1:
                medicine.quantity -= 1
                medicine.save()
                
                prescription.status = 'dispensed'
                prescription.save()
                messages.success(request, f"Successfully dispensed {medicine.name}.")
            else:
                messages.error(request, f"Out of stock! Cannot dispense {medicine.name}.")
        else:
            # Dispense even if not in inventory system, but warn
            prescription.status = 'dispensed'
            prescription.save()
            messages.warning(request, "Dispensed, but item not found in inventory tracking.")
            
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