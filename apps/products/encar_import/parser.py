"""Validate the observed EncarPhotosApp schema, without guessing field names."""
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

MAX_BYTES = 1024 * 1024


def text(value: object) -> str:
    """Accept text and simple numbers; never stringify nested structures."""
    return str(value).strip() if isinstance(value, (str, int, float)) and not isinstance(value, bool) else ''


def _unique(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Повторяющееся поле в JSON.')
        result[key] = value
    return result


def read_json(content: bytes) -> dict:
    """Reject oversized, malformed and ambiguous JSON before any DB write."""
    if len(content) > MAX_BYTES:
        raise ValidationError('Файл слишком большой. Максимум 1 МБ.')
    try:
        raw = json.loads(content.decode('utf-8-sig'), object_pairs_hook=_unique,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValidationError('Не удалось прочитать JSON. Проверьте файл и кодировку UTF-8.') from error
    validate(raw)
    return raw


def validate(raw: dict) -> None:
    """Validate only known schema sections and source-specific code lists."""
    if not isinstance(raw, dict) or (type(raw.get('schema_version')) is not int or raw.get('schema_version') != 1):
        raise ValidationError('Поддерживается car_info.json версии 1.')
    for key in ('source', 'vehicle'):
        if not isinstance(raw.get(key), dict):
            raise ValidationError('В файле нет сведений об источнике или автомобиле.')
    for key in ('equipment', 'translation', 'price'):
        if key in raw and not isinstance(raw[key], dict):
            raise ValidationError('Неверная структура описания, цены или комплектации.')
    source = raw['source']
    if source.get('site') != 'Encar' or not re.fullmatch(r'[0-9]{1,30}', str(source.get('listing_id', ''))):
        raise ValidationError('Нужны источник Encar и ID исходного объявления.')
    internal = source.get('data_vehicle_id')
    if internal not in (None, '') and not re.fullmatch(r'[0-9]{1,30}', str(internal)):
        raise ValidationError('Некорректный внутренний ID автомобиля.')
    try:
        url = urlsplit(text(source.get('url')))
        valid = (url.scheme == 'https' and url.hostname in ('fem.encar.com', 'www.encar.com', 'encar.com')
                 and not url.username and not url.password and url.port in (None, 443)
                 and url.path.rstrip('/') == '/cars/detail/' + str(source['listing_id']))
    except ValueError:
        valid = False
    if not valid:
        raise ValidationError('Ссылка должна вести на это объявление Encar по HTTPS.')
    equipment = raw.get('equipment', {})
    for key in ('standard_codes', 'unresolved_standard_codes', 'ambiguous_standard_codes'):
        values = equipment.get(key, [])
        if not isinstance(values, list) or len(values) > 500 or any(not isinstance(code, str) or len(code) > 40 for code in values):
            raise ValidationError('Коды оборудования должны быть списком строк (с ведущими нулями).')
    items = equipment.get('standard_items', [])
    if not isinstance(items, list) or len(items) > 500 or any(not isinstance(item, dict) or (not isinstance(item.get('code'), str) or len(item['code']) > 40) for item in items):
        raise ValidationError('Неверная структура списка оборудования.')
    for key in ('vehicle_ru', 'vehicle_en'):
        if key in raw.get('translation', {}) and not isinstance(raw['translation'][key], dict):
            raise ValidationError('Неверная структура перевода характеристик.')


def parse(raw: dict) -> dict:
    """Build explicit proposals; optional malformed values remain diagnostic only."""
    validate(raw)
    source, vehicle = raw['source'], raw['vehicle']
    translation, equipment = raw.get('translation', {}), raw.get('equipment', {})
    ru = translation.get('vehicle_ru', {}) if translation.get('language') == 'ru' else {}
    en = translation.get('vehicle_en', {})
    warnings = [text(item) for item in raw.get('warnings', []) if isinstance(item, str)] if isinstance(raw.get('warnings'), list) else []
    title = ' '.join(filter(None, [text(vehicle.get('manufacturer_english') or vehicle.get('manufacturer_original')),
        text(vehicle.get('model_english') or en.get('model') or vehicle.get('model_group_english') or vehicle.get('model_original')),
        text(vehicle.get('grade_english') or en.get('grade')), text(vehicle.get('grade_detail_english') or en.get('grade_detail')),
        text(vehicle.get('model_year'))]))[:255]
    description = text(translation.get('seller_text_ru')) if translation.get('language') == 'ru' else ''
    if not description:
        warnings.append('Русского описания нет. При необходимости вставьте перевод вручную.')
    if translation.get('source_changed'):
        warnings.append('Парсер сообщает об изменении источника: проверьте актуальность перевода.')
    retrieved = None
    if source.get('retrieved_at'):
        try:
            retrieved = parse_datetime(str(source['retrieved_at']))
            if retrieved is None or retrieved.utcoffset() is None:
                raise ValueError
        except (ValueError, TypeError):
            retrieved = None
            warnings.append('Дата получения парсером не распознана; оригинал сохранится в данных источника.')
    price, currency = None, ''
    price_data = raw.get('price', {})
    if price_data.get('amount') is not None:
        try:
            price = Decimal(str(price_data['amount']))
            currency = text(price_data.get('currency'))
            if not price.is_finite() or price < 0 or price >= Decimal('1e16') or price.as_tuple().exponent < -2 or not re.fullmatch('[A-Z]{3}', currency):
                raise ValueError
        except (ValueError, InvalidOperation):
            price, currency = None, ''
            warnings.append('Цена источника не распознана; она сохранится только в исходном файле.')
    specs = []
    definitions = [
        ('model_year', 'Год выпуска', ('year',), False),
        ('registration_year_month', 'Первая регистрация', ('registration_date', 'registration_year_month'), False),
        ('mileage_km', 'Пробег, км', ('mileage',), True),
        ('engine_displacement_cc', 'Объём двигателя, л', ('engine_volume',), True),
        ('fuel_original', 'Тип топлива', ('engine_type', 'fuel_type'), False),
        ('transmission_original', 'Коробка передач', ('transmission',), False),
        ('color_original', 'Цвет', ('color',), False),
        ('seats', 'Количество мест', ('seats',), True),
        ('body_type_original', 'Тип кузова', ('body_type', 'body_type_original'), False),
    ]
    for key, label, slugs, numeric in definitions:
        value = text(ru.get(key) or vehicle.get(key))
        if not value:
            warnings.append(f'{label}: не указано.')
            continue
        if numeric:
            try:
                if len(value) > 30:
                    raise ValueError
                number = Decimal(value)
                if not number.is_finite() or number < 0 or number >= Decimal('1e15') or number.as_tuple().exponent < -6:
                    raise ValueError
                if key == 'engine_displacement_cc':
                    number /= 1000
                value = format(number.normalize(), 'f')
            except (ValueError, InvalidOperation):
                warnings.append(f'{label}: значение не распознано.')
                continue
        specs.append({'key': key, 'label': label, 'value': value, 'slugs': slugs})
    codes = set(equipment.get('standard_codes', []))
    item_codes = {item['code'] for item in equipment.get('standard_items', [])}
    if 'standard_codes' not in equipment:
        codes = item_codes
    elif item_codes - codes:
        warnings.append('Расшифрованные опции расходятся со списком кодов; не назначаются: ' + ', '.join(sorted(item_codes - codes)))
    ambiguous = set(equipment.get('ambiguous_standard_codes', [])) | {'002', '003'}
    if equipment.get('choice_codes') or equipment.get('other_codes') or equipment.get('tuning_codes'):
        warnings.append('Дополнительные пакеты и прочие коды сохранены в источнике, но не сопоставляются со стандартными опциями.')
    return dict(raw=raw, listing_id=str(source['listing_id']), internal_id=text(source.get('data_vehicle_id')),
                url=text(source['url']), retrieved= retrieved, title=title, description=description,
                original_description=text(raw.get('description_original')), price=price, currency=currency,
                specs=specs, codes=sorted(codes), blocked=ambiguous, warnings=warnings,
                manufacturer=text(vehicle.get('manufacturer_english')), model=text(vehicle.get('model_group_english')))
