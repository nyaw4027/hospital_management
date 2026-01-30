from django import forms
from .models import Bill, Payment
from patients.models import Patient

class BillForm(forms.ModelForm):
    """Bill creation form"""
    
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a patient"
    )
    
    class Meta:
        model = Bill
        fields = ['patient', 'bill_type', 'description', 'amount', 'discount']
        widgets = {
            'bill_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Bill description'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Discount (optional)',
                'value': 0
            }),
        }

class PaymentForm(forms.ModelForm):
    """Payment processing form"""
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Payment amount'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Payment notes (optional)'
            }),
        }