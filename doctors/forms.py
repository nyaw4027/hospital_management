from django import forms
from .models import Prescription, PrescriptionItem, MedicalRecord
from .models import Prescription, PrescriptionItem


class MedicalRecordForm(forms.ModelForm):
    """
    Captures clinical findings and triggers paperless workflows 
    (Lab, Pharmacy, Admission) via Boolean flags.
    """
    class Meta:
        model = MedicalRecord
        # These fields MUST exist in your patients.models.MedicalRecord
        fields = ['diagnosis', 'clinical_notes', 'prescribed_medicines', 'ordered_tests', 'requires_admission']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter primary diagnosis...'}),
            'clinical_notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter detailed clinical observations...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamic Bootstrap styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['diagnosis'].required = True

class PrescriptionForm(forms.ModelForm):
    """Header for the Pharmacy order"""
    class Meta:
        model = Prescription
        # Note: We use 'clinical_notes' here to stay consistent with the MedicalRecord
        fields = ['patient', 'diagnosis', 'clinical_notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Diagnosis for pharmacist...'}),
            'clinical_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Special instructions...'}),
            'patient': forms.Select(attrs={'class': 'form-control select2'}),
        }

# --- DYNAMIC PRESCRIPTION ROWS ---
# This allows doctors to add multiple medicines in one session
PrescriptionItemFormSet = forms.inlineformset_factory(
    Prescription, 
    PrescriptionItem,
    fields=['medicine_name', 'dosage', 'frequency', 'duration', 'quantity', 'instructions'],
    extra=1, 
    can_delete=True,
    widgets={
        'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medicine Name'}),
        'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 500mg'}),
        'frequency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2x Daily'}),
        'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '7 Days'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'instructions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notes (e.g. After Meals)'}),
    }
)