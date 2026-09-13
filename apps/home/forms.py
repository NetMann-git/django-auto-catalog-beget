from django import forms

from .models import ClientShowcase


class ClientShowcaseForm(forms.ModelForm):
    class Meta:
        model = ClientShowcase
        fields = ("name", "vehicle", "image", "sort_order", "is_published")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Например, Александр"}),
            "vehicle": forms.TextInput(attrs={"class": "form-control", "placeholder": "Например, KIA Sorento"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk and not cleaned.get("image"):
            self.add_error("image", "Для нового клиента загрузите фотографию.")
        elif self.instance.pk and not cleaned.get("image") and not self.instance.legacy_image:
            self.add_error("image", "У карточки должна быть фотография.")
        return cleaned
