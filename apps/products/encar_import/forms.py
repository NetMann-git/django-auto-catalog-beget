"""Explicit manager choices for a single JSON import."""
import unicodedata

from django import forms

from apps.products.constants import AVAILABILITY_CHOICES
from apps.products.models import AttributeType, AttributeValue, Brand, CarModel, Category, EquipmentOption
from apps.products.product_attribute_forms import ProductAttributeForm
from .parser import MAX_BYTES, read_json


def normalize_choice(value: str) -> str:
    """Compare labels consistently on SQLite/MySQL without guessing synonyms."""
    return ' '.join(unicodedata.normalize('NFC', str(value)).split()).casefold()


class UploadForm(forms.Form):
    file = forms.FileField(label='Файл автомобиля', help_text='car_info.json (до 1 МБ) или пакет encar_<ID>.zip версии 1. Большие подборки загружайте отдельным JSON и через галерею.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .package import maximum
        self.fields['file'].help_text = (
            f'car_info.json до 1 МиБ или ZIP версии 1 до {maximum() / 1024**2:g} МиБ. '
            'Большие подборки: отдельный JSON и порционная загрузка фото в галерее.'
        )
        self.fields['file'].widget.attrs.update({
            'accept': '.json,.zip', 'data-package-max-bytes': maximum(),
        })

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        if uploaded.size > MAX_BYTES:
            raise forms.ValidationError('Максимальный размер — 1 МБ.')
        self.raw = read_json(uploaded.read(MAX_BYTES + 1))
        return uploaded


class ImportForm(forms.Form):
    """Unchecked update switches preserve manually edited product values."""

    token = forms.CharField(widget=forms.HiddenInput)
    regenerate_slug = forms.BooleanField(
        required=False, label='Обновить URL из итогового названия',
    )
    apply_title = forms.BooleanField(required=False, label='Применить название')
    title = forms.CharField(max_length=255, required=False, label='Название')
    apply_description = forms.BooleanField(required=False, label='Применить русское описание')
    description = forms.CharField(required=False, max_length=100000, label='Русское описание', widget=forms.Textarea(attrs={'rows': 8}))
    apply_identity = forms.BooleanField(required=False, label='Применить марку, модель и категорию')
    brand = forms.ModelChoiceField(queryset=Brand.objects.all(), required=False, label='Марка')
    car_model = forms.ModelChoiceField(queryset=CarModel.objects.select_related('brand'), required=False, label='Модель')
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, label='Категория')
    price = forms.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=0, label='Цена продажи на сайте, ₽ (введите вручную)')
    availability = forms.ChoiceField(required=False, choices=[('', 'Выберите наличие')] + AVAILABILITY_CHOICES, label='Наличие (выберите вручную)')
    equipment_mode = forms.ChoiceField(label='Комплектация', choices=[('add', 'Добавить выбранное, сохранив имеющееся'), ('keep', 'Не менять'), ('replace', 'Заменить набор выбранными опциями')])
    equipment = forms.ModelMultipleChoiceField(queryset=EquipmentOption.objects.none(), required=False, label='Распознанные опции из файла', widget=forms.CheckboxSelectMultiple)
    confirm_replace = forms.BooleanField(required=False, label='Подтверждаю удаление прежних опций, не выбранных в списке выше')

    def __init__(self, *args, proposal: dict, product=None, token='', **kwargs):
        super().__init__(*args, **kwargs)
        self.proposal, self.product = proposal, product
        existing = product is not None
        recognized = EquipmentOption.objects.filter(
            is_active=True, encar_standard_code__in=proposal['codes'],
        ).exclude(encar_standard_code__in=proposal['blocked']).select_related('group')
        self.fields['equipment'].queryset = recognized
        self.initial.update(token=token, title=proposal['title'], description=proposal['description'],
                            apply_title=not existing, apply_description=not existing and bool(proposal['description']),
                            apply_identity=not existing, equipment_mode='add', equipment=list(recognized.values_list('pk', flat=True)))
        matches = list(Brand.objects.filter(name__iexact=proposal['manufacturer'])[:2]) if proposal['manufacturer'] else []
        brand = matches[0] if len(matches) == 1 else None
        if brand:
            self.initial['brand'] = brand.pk
            models = list(CarModel.objects.filter(brand=brand, name__iexact=proposal['model'])[:2])
            if len(models) == 1:
                self.initial['car_model'] = models[0].pk
        if existing:
            self.fields.pop('price')
            self.fields.pop('availability')
            for name in ('brand', 'car_model', 'category'):
                self.initial[name] = getattr(product, name + '_id')
        else:
            self.fields['price'].required = True
            self.fields['availability'].required = True
            self.fields['title'].required = True
        # QueryDict is immutable; never modify request.POST itself.
        if self.is_bound:
            self.data = self.data.copy()
        self.rows = []
        self.warnings = list(proposal['warnings'])
        recognized_codes = set(recognized.values_list('encar_standard_code', flat=True))
        unknown = sorted((set(proposal['codes']) | set(proposal['raw'].get('equipment', {}).get('unresolved_standard_codes', []))) - recognized_codes)
        if unknown:
            self.warnings.append('Не сопоставлены или отключены коды: ' + ', '.join(unknown))
        if not existing and not brand:
            self.warnings.append('Марка не сопоставлена однозначно. Выберите её вручную или оставьте пустой.')
        current = {a.attribute_type_id: a.attribute_value.value if a.attribute_value else ''
                   for a in product.attributes.select_related('attribute_value')} if existing else {}
        for index, spec in enumerate(proposal['specs']):
            prefix = f'attr_{index}'
            kinds = list(AttributeType.objects.filter(slug__in=spec['slugs'])[:2])
            kind = kinds[0] if len(kinds) == 1 else None
            posted = self.data.get(prefix + '_type') if self.is_bound else None
            if self.is_bound:
                if posted:
                    kind = AttributeType.objects.filter(pk=posted).first() if posted.isascii() and posted.isdigit() and len(posted) < 19 else None
                elif kind:
                    self.data[prefix + '_type'] = str(kind.pk)
            self.fields[prefix + '_apply'] = forms.BooleanField(required=False, label='Применить', initial=not existing and kind is not None)
            self.fields[prefix + '_type'] = forms.ModelChoiceField(queryset=AttributeType.objects.all(), required=False, label='Характеристика на сайте', initial=kind)
            self.fields[prefix + '_text'] = forms.CharField(required=False, max_length=255, label='Число или текст', initial=spec['value'])
            choices = AttributeValue.objects.filter(attribute_type=kind) if kind else AttributeValue.objects.none()
            match = [
                value for value in choices
                if normalize_choice(value.value) == normalize_choice(spec['value'])
            ] if kind and kind.data_type == 'choice' else []
            if self.is_bound and kind:
                if kind.data_type == 'choice':
                    if not self.data.get(prefix + '_choice') and len(match) == 1:
                        self.data[prefix + '_choice'] = str(match[0].pk)
                elif not str(self.data.get(prefix + '_text', '')).strip():
                    self.data[prefix + '_text'] = spec['value']
            self.fields[prefix + '_choice'] = forms.ModelChoiceField(queryset=choices, required=False, label='Значение из справочника (для типа «выбор»)', initial=match[0] if len(match) == 1 else None)
            if not kind or (kind.data_type == 'choice' and len(match) != 1):
                self.warnings.append(f'{spec["label"]}: проверьте сопоставление со справочником.')
                self.fields[prefix + '_apply'].initial = False
            self.rows.append({
                              'data_type': kind.data_type if kind else '',
                              'needs_review': not kind or (kind.data_type == 'choice' and len(match) != 1),
                              'label': spec['label'], 'incoming': spec['value'], 'current': current.get(kind.pk, '') if kind else '',
                              'fields': [self[prefix + suffix] for suffix in ('_apply', '_type', '_choice', '_text')]})

    @property
    def error_summary(self) -> list[dict]:
        """Describe every validation error, including hidden controls."""
        result = []
        for name, errors in self.errors.items():
            target = 'encar-main'
            label = self.fields[name].label if name in self.fields else 'Общая проверка'
            if name.startswith('attr_'):
                index = int(name.split('_')[1])
                target = f'encar-attribute-{index}'
                label = 'Характеристики · ' + self.rows[index]['label'] + ' · ' + str(label)
            elif name in ('equipment', 'equipment_mode', 'confirm_replace'):
                target = 'encar-equipment'
                label = 'Комплектация · ' + str(label)
            elif name in ('photo_selection', 'package_cover', 'replace_photos'):
                target = 'encar-photos'
                label = 'Фотографии · ' + str(label)
            elif name == 'token':
                label = 'Срок действия предпросмотра'
            else:
                label = 'Основные данные · ' + str(label)
            result.append({'target': target, 'label': label, 'messages': errors})
        return result

    def clean(self) -> dict:
        cleaned = super().clean()
        if cleaned.get('apply_title') and not cleaned.get('title'):
            self.add_error('title', 'Пустое значение не может заменить название.')
        if cleaned.get('apply_description') and not cleaned.get('description'):
            self.add_error('description', 'Пустое описание не заменяет существующий текст.')
        brand, model = cleaned.get('brand'), cleaned.get('car_model')
        if cleaned.get('apply_identity') and model and model.brand_id != getattr(brand, 'pk', None):
            self.add_error('car_model', 'Модель должна принадлежать выбранной марке.')
        if cleaned.get('equipment_mode') == 'replace' and not cleaned.get('confirm_replace'):
            self.add_error('confirm_replace', 'Подтвердите полную замену. Отсутствие кода не доказывает отсутствие опции.')
        self.attribute_forms = []
        seen = set()
        for index, spec in enumerate(self.proposal['specs']):
            prefix = f'attr_{index}'
            if not cleaned.get(prefix + '_apply'):
                continue
            kind = cleaned.get(prefix + '_type')
            if kind is None or kind.pk in seen:
                self.add_error(prefix + '_type', 'Выберите характеристику; нельзя применить один тип дважды.')
                continue
            seen.add(kind.pk)
            value = cleaned.get(prefix + '_choice')
            data = {'attribute_type': kind.pk, 'attribute_value': getattr(value, 'pk', ''),
                    'free_value': cleaned.get(prefix + '_text', ''), 'sort_order': index}
            instance = self.product.attributes.filter(attribute_type=kind).first() if self.product else None
            form = ProductAttributeForm(data=data, instance=instance)
            if form.is_valid():
                self.attribute_forms.append(form)
            else:
                self.add_error(prefix + ('_choice' if kind.data_type == 'choice' else '_text'), ' '.join(str(message) for errors in form.errors.values() for message in errors))
        return cleaned
