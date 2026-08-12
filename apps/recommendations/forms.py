# apps/recommendations/forms.py

from django import forms
from .models import PromotedProduct

class PromotedProductForm(forms.ModelForm):
    class Meta:
        model = PromotedProduct
        fields = ['product', 'page', 'priority', 'is_active', 'start_date', 'end_date']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }