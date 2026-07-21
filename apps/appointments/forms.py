# apps/appointments/forms.py

from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('product', 'name', 'phone', 'email', 'date', 'time', 'comment')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'date-picker'}),
            'time': forms.Select(attrs={'class': 'time-select', 'disabled': 'disabled'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Дополнительные пожелания...'}),
            'product': forms.HiddenInput(),
        }
        labels = {
            'name': 'Ваше имя',
            'phone': 'Телефон',
            'email': 'Email',
            'date': 'Дата примерки',
            'time': 'Время примерки',
            'comment': 'Комментарий',
        }
        help_texts = {
            'phone': 'Например: +7 (999) 123-45-67',
            'email': 'Не обязательно, но мы пришлём подтверждение',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Поле time будет заполняться через AJAX, пока оно disabled
        self.fields['time'].widget.attrs['disabled'] = 'disabled'