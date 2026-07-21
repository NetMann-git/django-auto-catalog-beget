# apps/products/forms.py
from django import forms
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from .models import Product, ProductGalleryImage, Badge


class ImagePreviewWidget(forms.ClearableFileInput):
    """Виджет для отображения текущего изображения."""
    
    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        
        if value and hasattr(value, 'url'):
            preview_html = f'''
                <div style="margin-bottom: 10px;">
                    <img src="{value.url}" style="max-width: 200px; max-height: 200px; border-radius: 4px; border: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #999; margin-top: 5px;">Текущее изображение</p>
                </div>
            '''
            return mark_safe(preview_html + html)
        
        return html


class ProductForm(forms.ModelForm):
    """Форма для создания и редактирования товара."""
    
    # Поле для бейджей - чекбоксы
    badges = forms.ModelMultipleChoiceField(
        queryset=Badge.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'badges-checkbox'}),
        label='Бейджи'
    )
    
    class Meta:
        model = Product
        fields = [
            'title', 'slug', 'category', 'brand', 'price', 'currency',
            'short_description', 'description', 'image', 'is_active', 'is_featured',
            'availability_status', 'article', 'product_type', 'meta_title', 'meta_description',
            'badges'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Название товара',
                'id': 'id_title'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'url-адрес (автозаполнение)',
                'id': 'id_slug'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'image': ImagePreviewWidget(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'availability_status': forms.Select(attrs={'class': 'form-control'}),
            'article': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Артикул'}),
            'product_type': forms.Select(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO заголовок'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['badges'].initial = self.instance.badges.all()
    
    def save(self, commit=True):
        product = super().save(commit=False)
        if commit:
            product.save()
            self.save_m2m()
            product.badges.set(self.cleaned_data['badges'])
        return product
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        
        if not slug and title:
            slug = slugify(title)
        
        return slug


# ДОБАВИТЬ ЭТУ ФОРМУ
class GalleryImageForm(forms.ModelForm):
    """Форма для добавления изображений в галерею."""
    
    class Meta:
        model = ProductGalleryImage
        fields = ['image', 'alt']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'alt': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Описание изображения'}),
        }