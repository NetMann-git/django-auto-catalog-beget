"""Strict ZIP v1 validation and private, expiring preview storage."""
import hashlib
import io
import json
import re
import shutil
import stat
import time
import tempfile
import uuid
import zipfile
from pathlib import Path

from PIL import Image
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.dateparse import parse_datetime

from apps.products.gallery_upload import limits, validate_image
from .parser import MAX_BYTES, _unique, parse, read_json

SALT = 'encar.package.v1'
TTL = 1800
MIMES = {'.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}


def maximum() -> int:
    return int(getattr(settings, 'ENCAR_PACKAGE_MAX_BYTES', 12 * 1024**2))


def fail(message: str) -> None:
    raise ValidationError(message)


def strict_json(data: bytes) -> dict:
    try:
        result = json.loads(data.decode('utf-8'), object_pairs_hook=_unique,
                            parse_constant=lambda x: fail('Недопустимое число JSON.'))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValidationError('Некорректный UTF-8 JSON в manifest.json.') from error
    if not isinstance(result, dict):
        fail('Manifest должен быть объектом JSON.')
    return result


def check_date(value, *, utc=False, optional=False) -> None:
    if value is None and optional:
        return
    try:
        date = parse_datetime(value) if isinstance(value, str) else None
        if date is None or date.utcoffset() is None or (utc and date.utcoffset().total_seconds() != 0):
            raise ValueError
    except (ValueError, TypeError):
        fail('Некорректная дата пакета: требуется ISO 8601 с часовым поясом.')


def checked_bytes(archive, info, declared: dict, cap: int) -> bytes:
    if type(declared.get('bytes')) is not int or not 0 < declared['bytes'] <= cap:
        fail('Недопустимый заявленный размер файла.')
    digest = declared.get('sha256')
    if not isinstance(digest, str) or not re.fullmatch('[0-9a-fA-F]{64}', digest):
        fail('Недопустимый SHA-256 файла.')
    if info.file_size != declared['bytes']:
        fail('Размер файла не совпадает с manifest: ' + info.filename)
    with archive.open(info) as stream:
        data = stream.read(cap + 1)
    if len(data) != declared['bytes'] or hashlib.sha256(data).hexdigest() != digest.lower():
        fail('Не совпадает размер или SHA-256: ' + info.filename)
    return data


def validate_package(upload) -> dict:
    """Inspect central-directory entries before any file contents are read."""
    if upload.size > maximum():
        fail('ZIP слишком большой. Используйте отдельный JSON и порционную загрузку фото в галерее.')
    upload.seek(0)
    try:
        with zipfile.ZipFile(upload) as archive:
            infos = archive.infolist()
            cap = limits()
            if len(infos) > cap['files'] + 3:
                fail('В ZIP слишком много элементов.')
            names = set()
            total = 0
            for info in infos:
                name = info.filename
                mode = info.external_attr >> 16
                if (name != info.orig_filename or name in names or '\\' in name
                        or name.startswith('/') or '..' in name.split('/')
                        or any(ord(c) < 32 for c in name)):
                    fail('Опасный или повторяющийся путь в ZIP.')
                names.add(name)
                kind = stat.S_IFMT(mode)
                if (kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or info.flag_bits & (1 | 64) or info.compress_type != zipfile.ZIP_STORED):
                    fail('Нужен ZIP_STORED без шифрования, ссылок и специальных файлов.')
                if name == 'photos/' and info.is_dir():
                    if info.file_size:
                        fail('Недопустимая запись каталога.')
                    continue
                if info.is_dir() or kind == stat.S_IFDIR:
                    fail('Вложенные каталоги не разрешены.')
                allowed = name in ('manifest.json', 'car_info.json') or re.fullmatch(
                    r'photos/[^/:\\]+\.(jpg|png|webp)', name,
                )
                if not allowed:
                    fail('Файл вне разрешённой структуры ZIP: ' + name)
                file_limit = 256 * 1024 if name == 'manifest.json' else (MAX_BYTES if name == 'car_info.json' else cap['bytes'])
                if not 0 < info.file_size <= file_limit:
                    fail('Превышен лимит размера файла: ' + name)
                if info.compress_size != info.file_size:
                    fail('Недопустимый размер ZIP_STORED.')
                total += info.file_size
            if total > min(maximum(), cap['total']):
                fail('Превышен распакованный объём. Используйте отдельный JSON и загрузку фото.')
            if not {'manifest.json', 'car_info.json'} <= names:
                fail('В корне ZIP нужны manifest.json и car_info.json.')
            manifest = strict_json(archive.read('manifest.json'))
            if manifest.get('format') != 'encar-car-package':
                fail('Неизвестный формат пакета.')
            if type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1:
                fail('Неподдерживаемая версия пакета. Поддерживается версия 1.')
            check_date(manifest.get('created_at'), utc=True)
            producer = manifest.get('producer')
            if (not isinstance(producer, dict) or producer.get('name') != 'EncarPhotosApp'
                    or not isinstance(producer.get('version'), str) or not producer['version']):
                fail('Некорректные сведения о приложении-создателе.')
            source = manifest.get('source')
            if not isinstance(source, dict) or source.get('site') != 'Encar':
                fail('Некорректный источник пакета.')
            listing_id = source.get('listing_id')
            if not isinstance(listing_id, str) or not re.fullmatch('[0-9]{1,30}', listing_id):
                fail('ID объявления должен быть строкой цифр.')
            if upload.name != f'encar_{listing_id}.zip':
                fail('Имя пакета должно быть encar_' + listing_id + '.zip.')
            check_date(source.get('retrieved_at'), optional=True)
            if source.get('url') is not None and not isinstance(source['url'], str):
                fail('Некорректная ссылка источника.')
            internal = source.get('data_vehicle_id')
            if internal is not None and (type(internal) not in (str, int) or not re.fullmatch('[0-9]{1,30}', str(internal))):
                fail('Некорректный внутренний ID.')
            declared = manifest.get('data')
            if not isinstance(declared, dict) or declared.get('path') != 'car_info.json':
                fail('Неверное описание файла данных.')
            raw_bytes = checked_bytes(archive, archive.getinfo('car_info.json'), declared, MAX_BYTES)
            raw = read_json(raw_bytes)
            proposal = parse(raw)
            if proposal['listing_id'] != listing_id:
                fail('ID объявления в manifest и car_info.json различаются.')
            original_source = raw['source']
            if str(internal or '') != str(original_source.get('data_vehicle_id') or ''):
                fail('Внутренние ID в manifest и car_info.json различаются.')
            for key in ('url', 'retrieved_at'):
                if source.get(key) is not None and source[key] != original_source.get(key):
                    fail('Сведения об источнике в manifest и car_info.json различаются: ' + key)
            notices = manifest.get('warnings')
            if not isinstance(notices, list) or len(notices) > 500 or any(not isinstance(x, str) or len(x) > 5000 for x in notices):
                fail('Некорректные предупреждения пакета.')
            photos = manifest.get('photos')
            if not isinstance(photos, list) or len(photos) > cap['files']:
                fail('Некорректный список фотографий или превышен лимит количества.')
            paths, orders, hashes = set(), set(), set()
            result = []
            pixels = 0
            for photo in photos:
                if not isinstance(photo, dict):
                    fail('Некорректное описание фотографии.')
                path, order = photo.get('path'), photo.get('order')
                if (not isinstance(path, str) or not path.startswith('photos/') or path not in names
                        or path in paths or type(order) is not int or order < 1 or order in orders):
                    fail('Некорректный или повторяющийся путь/порядок фотографии.')
                paths.add(path)
                orders.add(order)
                if (not isinstance(photo.get('original_filename'), str)
                        or any(type(photo.get(k)) is not int or photo[k] <= 0 for k in ('width', 'height'))):
                    fail('Некорректные имя или размеры фотографии.')
                data = checked_bytes(archive, archive.getinfo(path), photo, cap['bytes'])
                data, digest, ext = validate_image(SimpleUploadedFile('photo', data))
                with Image.open(io.BytesIO(data)) as image:
                    if (image.width, image.height) != (photo['width'], photo['height']):
                        fail('Размеры изображения не совпадают с manifest: ' + path)
                    pixels += image.width * image.height
                if pixels > int(getattr(settings, 'ENCAR_PACKAGE_MAX_PIXELS', 80_000_000)):
                    fail('Суммарное разрешение фото слишком велико. Используйте порционную загрузку.')
                if Path(path).suffix != ext or photo.get('mime_type') != MIMES[ext]:
                    fail('Формат изображения не соответствует manifest или расширению: ' + path)
                if digest in hashes:
                    fail('Пакет содержит повторяющиеся фотографии по SHA-256.')
                hashes.add(digest)
                result.append({**photo, 'sha256': digest, 'content': data})
            if names - {'manifest.json', 'car_info.json', 'photos/'} != paths:
                fail('Состав ZIP не совпадает со списком manifest.')
            if [p['order'] for p in result] != sorted(orders):
                fail('Фотографии manifest должны идти по порядку показа.')
            cover = manifest.get('cover_path')
            if cover is not None and (not isinstance(cover, str) or cover not in paths):
                fail('Предложенная обложка отсутствует в пакете.')
            return {'manifest': manifest, 'raw_bytes': raw_bytes, 'raw': raw, 'photos': result}
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError, OSError, UnicodeError, ValueError) as error:
        raise ValidationError('Не удалось прочитать ZIP. Проверьте целостность архива.') from error


def storage_root() -> Path:
    project_key = hashlib.sha256(str(settings.BASE_DIR).encode()).hexdigest()[:16]
    default = Path(tempfile.gettempdir()) / ('carstar-encar-' + project_key)
    path = Path(getattr(settings, 'ENCAR_PACKAGE_TEMP_ROOT', default))
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def cleanup_expired() -> int:
    """Remove only our UUID preview directories, never arbitrary paths."""
    removed = 0
    for path in storage_root().iterdir():
        if re.fullmatch('[0-9a-f]{32}', path.name) and not path.is_symlink() and path.is_dir():
            if path.stat().st_mtime < time.time() - TTL:
                shutil.rmtree(path)
                removed += 1
    return removed


def stage(package: dict, user_id: int) -> str:
    cleanup_expired()
    path = storage_root() / uuid.uuid4().hex
    path.mkdir(mode=0o700)
    try:
        (path / 'manifest.json').write_text(json.dumps(package['manifest']), encoding='utf-8')
        (path / 'car_info.json').write_bytes(package['raw_bytes'])
        for index, photo in enumerate(package['photos']):
            (path / f'photo-{index}').write_bytes(photo['content'])
            with Image.open(io.BytesIO(photo['content'])) as image:
                image.thumbnail((240, 180))
                image.convert('RGB').save(path / f'thumb-{index}.jpg', 'JPEG', quality=80)
        return signing.dumps({'id': path.name, 'user': user_id}, salt=SALT)
    except Exception:
        shutil.rmtree(path)
        raise


def locate(token: str, user_id: int) -> Path:
    try:
        if len(token) > 1000:
            raise signing.BadSignature
        data = signing.loads(token, salt=SALT, max_age=TTL)
        if data['user'] != user_id or not re.fullmatch('[0-9a-f]{32}', data['id']):
            raise signing.BadSignature
        path = storage_root() / data['id']
        if not path.is_dir() or path.is_symlink():
            raise signing.BadSignature
        return path
    except (signing.BadSignature, KeyError, TypeError):
        cleanup_expired()
        fail('Предпросмотр пакета истёк или недоступен. Загрузите ZIP заново.')


def load(token: str, user_id: int) -> tuple:
    path = locate(token, user_id)
    manifest = strict_json((path / 'manifest.json').read_bytes())
    data = (path / 'car_info.json').read_bytes()
    if (len(data) != manifest['data']['bytes']
            or hashlib.sha256(data).hexdigest() != manifest['data']['sha256'].lower()):
        fail('Временные данные повреждены. Загрузите пакет заново.')
    raw = read_json(data)
    return path, manifest, raw
