from django import forms
from patients.models import MedicalRecord

class MedicalRecordForm(forms.ModelForm):
    """Professional medical record form for doctor consultations"""
    
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'prescription', 'test_results', 'notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter primary diagnosis...'}),
            'prescription': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Dosage, frequency, and duration...'}),
            'test_results': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Lab results or vitals (BP, Temp, etc.)'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observation notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super(MedicalRecordForm, self).__init__(*args, **kwargs)
        # Automatically add 'form-control' to all fields without typing it 4 times
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Make critical fields required at the form level
        self.fields['diagnosis'].required = True
        self.fields['prescription'].required = True