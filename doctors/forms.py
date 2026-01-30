from django import forms
from patients.models import MedicalRecord

class MedicalRecordForm(forms.ModelForm):
    """Medical record form"""
    
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'prescription', 'test_results', 'notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter diagnosis'
            }),
            'prescription': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter prescription details'
            }),
            'test_results': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter test results (if any)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }