"""Original-byte photo uploads into the existing product gallery."""
import hashlib
import io
import logging
import warnings
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Max

from .models import Product, ProductGalleryImage

logger = logging.getLogger(__name__)
FORMATS = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}


def limits() -> dict:
    """Return project-overridable per-selection and per-file limits."""
    return {
        'files': int(getattr(settings, 'GALLERY_UPLOAD_MAX_FILES', 60)),
        'bytes': int(getattr(settings, 'GALLERY_UPLOAD_MAX_FILE_BYTES', 12 * 1024**2)),
        'total': int(getattr(settings, 'GALLERY_UPLOAD_MAX_TOTAL_BYTES', 240 * 1024**2)),
        'pixels': int(getattr(settings, 'GALLERY_UPLOAD_MAX_PIXELS', 40_000_000)),
        'gallery': int(getattr(settings, 'GALLERY_UPLOAD_MAX_GALLERY', 300)),
    }


def lock_product(pk: int) -> Product:
    """Serialize gallery mutations, including on SQLite (no row-lock support)."""
    Product.objects.filter(pk=pk).update(id=F('id'))
    return Product.objects.select_for_update().get(pk=pk)


def digest_file(field) -> str:
    """Read storage in chunks without modifying the original file."""
    digest = hashlib.sha256()
    with field.storage.open(field.name, 'rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_hashes(pk: int) -> bool:
    """Cache at most five legacy hashes per request, never in a migration."""
    with transaction.atomic():
        product = lock_product(pk)
        pending = []
        if product.image and not product.image_sha256:
            pending.append(product)
        pending.extend(product.gallery.filter(image_sha256='')[:5 - len(pending)])
        for obj in pending:
            if not obj.image:
                raise ValidationError('В галерее есть запись без файла. Удалите её перед загрузкой.')
            # Cover and gallery may safely reference the same stored original.
            cached = product.gallery.filter(image=obj.image.name).exclude(image_sha256='').first()
            digest = cached.image_sha256 if cached else digest_file(obj.image)
            type(obj).objects.filter(pk=obj.pk).update(image_sha256=digest)
        return not product.gallery.filter(image_sha256='').exists()


def validate_image(upload) -> tuple[bytes, str, str]:
    """Check actual format, full decoding and pixel bounds; retain exact bytes."""
    cap = limits()
    if not upload.size or upload.size > cap['bytes']:
        raise ValidationError('Файл пуст или превышает допустимый размер.')
    upload.seek(0)
    data = upload.read(cap['bytes'] + 1)
    if len(data) != upload.size or len(data) > cap['bytes']:
        raise ValidationError('Размер файла не соответствует заявленному.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                extension = FORMATS.get(image.format)
                if not extension:
                    raise ValidationError('Допустимы только JPEG, PNG и WebP.')
                if image.width * image.height > cap['pixels']:
                    raise ValidationError('Слишком большое разрешение изображения.')
                if getattr(image, 'n_frames', 1) != 1:
                    raise ValidationError('Выберите статичное изображение, без анимации.')
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                image.load()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as error:
        raise ValidationError('Изображение повреждено или имеет недопустимое разрешение.') from error
    return data, hashlib.sha256(data).hexdigest(), extension


def add_photo(pk: int, upload, expected: dict, *, journal=None) -> str:
    """Append one validated original; roll back its storage write on DB failure."""
    from django.core.files.base import ContentFile

    data, digest, extension = validate_image(upload)
    if digest != expected['sha256'] or len(data) != expected['size']:
        raise ValidationError('Файл изменился после предпросмотра. Выберите его заново.')
    field = ProductGalleryImage._meta.get_field('image')
    stored_name = None
    try:
        with transaction.atomic():
            product = lock_product(pk)
            if ((product.image and not product.image_sha256)
                    or product.gallery.filter(image_sha256='').exists()):
                raise ValidationError('Галерея изменилась. Повторите загрузку для проверки старых файлов.')
            if ((product.image and product.image_sha256 == digest)
                    or product.gallery.filter(image_sha256=digest).exists()):
                return 'duplicate'
            if product.gallery.count() >= limits()['gallery']:
                raise ValidationError('Достигнут предел количества фотографий автомобиля.')
            last = product.gallery.aggregate(value=Max('sort_order'))['value']
            stored_name = field.storage.save(
                f'products/gallery/{uuid4().hex}{extension}', ContentFile(data),
            )
            if journal is not None:
                journal.append((field.storage, stored_name))
            photo = ProductGalleryImage.objects.create(
                product=product, image=stored_name,
                sort_order=0 if last is None else last + 1,
            )
            ProductGalleryImage.objects.filter(pk=photo.pk).update(image_sha256=digest)
            if not product.image:
                product.image = stored_name
                product.save(update_fields=['image'])
                Product.objects.filter(pk=pk).update(image_sha256=digest)
        return 'added'
    except Exception:
        if stored_name:
            # The transaction rolled back; this UUID belongs only to this upload.
            try:
                field.storage.delete(stored_name)
            except OSError:
                logger.exception('Не удалось убрать файл отменённой загрузки %s', stored_name)
        raise


def choose_cover(product: Product, photo: ProductGalleryImage) -> None:
    """Preserve an older standalone cover as a gallery item before switching."""
    if product.image and not product.gallery.filter(image=product.image.name).exists():
        last = product.gallery.aggregate(value=Max('sort_order'))['value']
        old = ProductGalleryImage.objects.create(
            product=product, image=product.image.name,
            sort_order=0 if last is None else last + 1,
        )
        ProductGalleryImage.objects.filter(pk=old.pk).update(image_sha256=product.image_sha256)
    product.image = photo.image.name
    product.save(update_fields=['image'])
    Product.objects.filter(pk=product.pk).update(image_sha256=photo.image_sha256)
