from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import lab_tech_only
from .models import LabRequest

@login_required
@lab_tech_only
def lab_dashboard(request):
    # Data for the table (Paid but not finished)
    queue = LabRequest.objects.filter(status='paid').order_by('created_at')
    
    # Data for the recently completed table
    recent_completions = LabRequest.objects.filter(status='completed').order_by('-updated_at')[:5]
    
    # Stats for the cards
    current_month = timezone.now().month
    total_monthly_tests = LabRequest.objects.filter(
        status='completed', 
        updated_at__month=current_month
    ).count()

    # Data for the Chart (Example: Count of tests by name)
    # In a real app, you'd use .values('test_name').annotate(count=Count('id'))
    context = {
        'queue': queue,
        'recent_completions': recent_completions,
        'waiting_count': queue.count(),
        'total_monthly_tests': total_monthly_tests,
        'current_month_name': timezone.now().strftime('%B'),
        'chart_labels': ['Blood Test', 'Malaria', 'X-Ray', 'Urinalysis', 'Sugar'],
        'chart_data': [15, 22, 8, 12, 5],
    }
    return render(request, 'labs/dashboard.html', context)

@login_required
@lab_tech_only
def submit_lab_result(request, test_id):
    if request.method == 'POST':
        test = get_object_or_404(LabRequest, id=test_id)
        test.findings = request.POST.get('findings')
        if 'attachment' in request.FILES:
            test.attachment = request.FILES['attachment']
        test.status = 'completed'
        test.save()
        messages.success(request, f"Results for {test.patient.name} submitted successfully!")
    return redirect('lab_dashboard')