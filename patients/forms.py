from django import forms
from appointments.models import Appointment
from accounts.models import User

class AppointmentForm(forms.ModelForm):
    """Appointment booking form"""
    
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role='doctor'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a doctor"
    )
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'appointment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'appointment_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your reason for visit'
            }),
        }