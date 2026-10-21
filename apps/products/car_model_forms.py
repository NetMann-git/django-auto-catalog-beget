"""Shared model selector for manager and admin product editors."""

from typing import Any

from django import forms

from .manager_slugs import AutoSlugMixin
from .models import CarModel, Product


class CarModelSelect(forms.Select):
    """Expose manufacturer identifiers for the dependent select."""

    def create_option(self, *args: Any, **kwargs: Any) -> dict:
        option = super().create_option(*args, **kwargs)
        value = option['value']
        if hasattr(value, 'instance'):
            option['attrs']['data-brand'] = str(value.instance.brand_id)
        return option


class ProductModelForm(forms.ModelForm):
    """Keep server-side model validation available without JavaScript."""

    car_model = forms.ModelChoiceField(
        queryset=CarModel.objects.select_related('brand'), required=False,
        label='Модель автомобиля',
        help_text='Сначала выберите марку. Если модели нет, добавьте её в справочник моделей.',
        widget=CarModelSelect(attrs={
            'class': 'form-control', 'data-car-model-select': '',
        }),
    )

    class Meta:
        model = Product
        fields = '__all__'

    class Media:
        js = ('products/js/car-model-select.js',)


class CarModelForm(AutoSlugMixin, forms.ModelForm):
    """Create Latin model codes using the existing manager convention."""

    slug_source = 'name'
    slug = forms.SlugField(
        required=False, label='Код модели',
        help_text='Автоматически формируется латиницей, если оставить пустым.',
    )

    class Meta:
        model = CarModel
        fields = ('brand', 'name', 'slug', 'sort_order')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['slug'].required = True
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        if self.instance.pk and self.instance.products.exists():
            self.fields['brand'].disabled = True
            self.fields['brand'].help_text = 'Марка закреплена: модель используется в товарах.'

    def clean(self) -> dict:
        """Prevent duplicate model names within a brand in normal editors."""
        cleaned = super().clean()
        brand, name = cleaned.get('brand'), cleaned.get('name')
        if brand and name and CarModel.objects.filter(
            brand=brand, name__iexact=name,
        ).exclude(pk=self.instance.pk).exists():
            self.add_error('name', 'Такая модель у этой марки уже существует.')
        return cleaned
