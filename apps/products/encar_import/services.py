"""Atomic application of reviewed data with stale-preview protection."""
import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.products.cache import CatalogCache
from apps.products.manager_slugs import unique_slug
from apps.products.models import Product, VehicleImportSource


def fingerprint(product) -> str:
    """Detect edits made after preview, including equipment and attributes."""
    if product is None:
        return ''
    state = {'fields': {field.attname: str(getattr(product, field.attname)) for field in product._meta.fields},
             'equipment': sorted(product.equipment.values_list('pk', flat=True)),
             'attributes': list(product.attributes.order_by('pk').values_list('pk', 'attribute_type_id', 'attribute_value_id', 'sort_order'))}
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


@transaction.atomic
def save_import(form, proposal: dict, expected: dict) -> tuple:
    """Create a draft or modify only explicitly selected values, all-or-nothing."""
    source = VehicleImportSource.objects.select_for_update().filter(source='encar', listing_id=proposal['listing_id']).first()
    product = Product.objects.select_for_update().get(pk=source.product_id) if source else None
    if getattr(product, 'pk', None) != expected['product_id'] or fingerprint(product) != expected['fingerprint']:
        raise ValidationError('Карточка изменилась после предпросмотра. Загрузите файл заново и проверьте изменения.')
    if source and source.imported_at.isoformat() != expected.get('imported_at'):
        raise ValidationError('После предпросмотра уже выполнен другой импорт. Загрузите файл заново.')
    cleaned = form.cleaned_data
    created = product is None
    changed = []
    if created:
        product = Product(title=cleaned['title'], slug=unique_slug(Product, cleaned['title']),
                          price=cleaned['price'], currency='RUB', is_active=False,
                          availability_status=cleaned['availability'])
    for field, switch, label in [('title', 'apply_title', 'название'), ('description', 'apply_description', 'описание')]:
        if cleaned.get(switch) and cleaned.get(field):
            setattr(product, field, cleaned[field])
            changed.append(label)
    if cleaned.get('apply_identity'):
        brand = cleaned.get('brand')
        if brand and product.car_model_id and product.car_model.brand_id != brand.pk and not cleaned.get('car_model'):
            raise ValidationError('Для смены марки выберите соответствующую модель: прежняя модель относится к другой марке.')
        for field in ('brand', 'car_model', 'category'):
            if cleaned.get(field):
                setattr(product, field, cleaned[field])
                changed.append({'brand': 'марка', 'car_model': 'модель', 'category': 'категория'}[field])
    product.full_clean()
    product.save()
    for attr_form in form.attribute_forms:
        attr = attr_form.save(commit=False)
        attr.product = product
        attr.save()
    if form.attribute_forms:
        changed.append(f'характеристики: {len(form.attribute_forms)}')
    if cleaned['equipment_mode'] == 'replace':
        product.equipment.set(cleaned['equipment'])
        changed.append('комплектация заменена')
    elif cleaned['equipment_mode'] == 'add':
        product.equipment.add(*cleaned['equipment'])
        changed.append(f'комплектация: выбрано {len(cleaned["equipment"])}')
    if source is None:
        source = VehicleImportSource(product=product, source='encar', listing_id=proposal['listing_id'])
    source.raw_json = proposal['raw']
    source.source_url = proposal['url']
    if proposal['internal_id']:
        source.internal_vehicle_id = proposal['internal_id']
    if proposal['retrieved']:
        source.retrieved_at = proposal['retrieved']
    if proposal['price'] is not None:
        source.source_price, source.source_currency = proposal['price'], proposal['currency']
    if proposal['original_description']:
        source.original_description = proposal['original_description']
    source.save()
    transaction.on_commit(CatalogCache.clear_catalog)
    return product, created, changed
