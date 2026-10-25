"""ZIP previews reuse JSON forms, identity rules and the existing photo gallery."""
import logging
import shutil

from django import forms
from django.contrib import messages
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.products.gallery_upload import add_photo, choose_cover, limits, prepare_hashes
from apps.products.models import Product, ProductGalleryImage
from apps.users.constants import ROLE_ADMIN, ROLE_MANAGER
from apps.users.decorators import role_required
from . import package
from .forms import ImportForm, UploadForm
from .parser import parse
from .services import fingerprint, resolve_identity, save_import

logger = logging.getLogger(__name__)
PREVIEW_SALT = 'encar.package.review.v1'


class PackageForm(ImportForm):
    """Explicit photo and cover choices in addition to the existing JSON choices."""
    photo_selection = forms.MultipleChoiceField(
        required=False, label='Добавить выбранные фотографии',
        widget=forms.CheckboxSelectMultiple,
    )
    package_cover = forms.ChoiceField(required=False, label='Обложка')

    def __init__(self, *args, manifest: dict, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo_selection'].choices = [
            (str(i), p['original_filename']) for i, p in enumerate(manifest['photos'])
        ]
        self.fields['package_cover'].choices = [('', 'Сохранить текущую; если её нет — первая добавленная')]
        self.fields['package_cover'].choices += self.fields['photo_selection'].choices
        self.initial['photo_selection'] = [str(i) for i in range(len(manifest['photos']))]
        if not self.product or not self.product.image:
            self.initial['package_cover'] = next((str(i) for i, p in enumerate(manifest['photos'])
                                                   if p['path'] == manifest['cover_path']), '')

    def clean(self) -> dict:
        cleaned = super().clean()
        cover = cleaned.get('package_cover', '')
        if cover and cover not in cleaned.get('photo_selection', []):
            self.add_error('package_cover', 'Для обложки отметьте эту фотографию для добавления.')
        return cleaned


def upload_error(request, message):
    form = UploadForm()
    form.cleaned_data = {}
    form.add_error(None, message)
    return render(request, 'products/encar_import/upload.html', {'form': form})


def handle_package(request):
    """Called only behind import_encar's manager role and POST/CSRF checks."""
    token = request.POST.get('package_token', '')
    try:
        if not token:
            validated = package.validate_package(request.FILES['file'])
            token = package.stage(validated, request.user.pk)
        folder, manifest, raw = package.load(token, request.user.pk)
        if request.POST.get('action') == 'cancel_package':
            shutil.rmtree(folder)
            messages.success(request, 'Импорт отменён. Временные фотографии удалены.')
            return redirect('catalog:import_encar')
        proposal = parse(raw)
        candidates = Product.objects.filter(article=proposal['listing_id']).order_by('pk')
        # Choices are limited to exact manual matches and revalidated at save time.
        candidates = candidates.exclude(import_sources__source='encar')
        review = request.POST.get('review_token', '')
        expected = None
        selected_id = None
        if review:
            expected = signing.loads(review, salt=PREVIEW_SALT, max_age=package.TTL)
            if expected['package_token'] != token or expected['user'] != request.user.pk:
                raise signing.BadSignature
            selected_id = expected.get('selected_product_id')
        elif request.POST.get('action') == 'choose_product':
            try:
                selected_id = int(request.POST.get('product_id', ''))
            except ValueError:
                raise ValidationError('Выберите автомобиль из списка.')
            if not candidates.filter(pk=selected_id).exists():
                raise ValidationError('Выбранная карточка не соответствует артикулу.')
        try:
            source, product = resolve_identity(proposal['listing_id'], selected_id=selected_id)
        except ValidationError:
            if (selected_id is None and candidates.exists()
                    and Product.objects.filter(article=proposal['listing_id']).count() > 1):
                return render(request, 'products/encar_import/package_choose.html', {
                    'candidates': candidates, 'package_token': token,
                    'listing_id': proposal['listing_id'],
                })
            raise
        if expected is None:
            expected = {
                'user': request.user.pk, 'package_token': token,
                'product_id': getattr(product, 'pk', None), 'fingerprint': fingerprint(product),
                'imported_at': source.imported_at.isoformat() if source else None,
                'selected_product_id': selected_id,
            }
            review = signing.dumps(expected, salt=PREVIEW_SALT, compress=True)
        bound = request.POST if request.POST.get('action') in ('save_package', 'review_package') else None
        form = PackageForm(bound, proposal=proposal, product=product, token=review, manifest=manifest)
        if request.POST.get('action') == 'save_package' and form.is_valid():
            journal = []
            try:
                with transaction.atomic():
                    product, created, changes = save_import(form, proposal, expected)
                    selected = set(form.cleaned_data['photo_selection'])
                    if selected:
                        while not prepare_hashes(product.pk):
                            pass
                    added = duplicates = 0
                    for index, photo in enumerate(manifest['photos']):
                        if str(index) not in selected:
                            continue
                        data = (folder / f'photo-{index}').read_bytes()
                        result = add_photo(product.pk, SimpleUploadedFile('photo', data),
                                           {'size': photo['bytes'], 'sha256': photo['sha256'].lower()}, journal=journal)
                        added += result == 'added'
                        duplicates += result == 'duplicate'
                    cover_index = form.cleaned_data.get('package_cover', '')
                    if cover_index:
                        digest = manifest['photos'][int(cover_index)]['sha256'].lower()
                        cover = ProductGalleryImage.objects.filter(product=product, image_sha256=digest).first()
                        product.refresh_from_db()
                        if cover:
                            choose_cover(product, cover)
                        elif product.image_sha256 != digest:
                            raise ValidationError('Не удалось выбрать обложку. Повторите предпросмотр.')
            except Exception:
                for storage, name in journal:
                    try:
                        if not ProductGalleryImage.objects.filter(image=name).exists() and not Product.objects.filter(image=name).exists():
                            storage.delete(name)
                    except OSError:
                        logger.exception('Не удалось удалить файл отменённого пакета %s', name)
                raise
            try:
                shutil.rmtree(folder)
            except OSError:
                logger.exception('Не удалось удалить завершённый предпросмотр %s', folder.name)
            messages.success(request, (
                ('Создан черновик. ' if created else 'Автомобиль обновлён. ')
                + f'Фото добавлено: {added}, дублей пропущено: {duplicates}. '
                + 'Применено: ' + (', '.join(changes) or 'только данные источника')
            ))
            return redirect('catalog:product_edit', product_id=product.pk)
        selected_photos = set(form['photo_selection'].value() or [])
        return render(request, 'products/encar_import/preview.html', {
            'form': form, 'proposal': proposal, 'product': product,
            'general': [form[name] for name in ('apply_title', 'title', 'apply_description', 'description',
                        'apply_identity', 'brand', 'car_model', 'category', 'price', 'availability') if name in form.fields],
            'current_equipment': product.equipment.all() if product else [],
            'current_attributes': product.attributes.select_related('attribute_type', 'attribute_value') if product else [],
            'matched_by_article': product is not None and source is None,
            'package_token': token, 'review_token': review, 'package_manifest': manifest,
            'package_photos': [{**p, 'index': i, 'selected': str(i) in selected_photos} for i, p in enumerate(manifest['photos'])],
        })
    except (ValidationError, signing.BadSignature) as error:
        # Staging remains available for a retry until TTL, but no DB changes commit.
        if isinstance(error, ValidationError):
            return upload_error(request, error)
        return upload_error(request, 'Предпросмотр истёк или повреждён. Загрузите ZIP заново.')
    except (OSError, DatabaseError, KeyError) as error:
        logger.exception('Не удалось импортировать пакет Encar')
        return upload_error(request, 'Не удалось завершить импорт пакета. Проверьте карточку, доступность файлов и свободное место. Повторная загрузка не создаёт дублей.')


@role_required(ROLE_MANAGER, ROLE_ADMIN)
@require_GET
def package_thumbnail(request, token: str, index: int):
    """Serve generated thumbnails only to the owner of a live preview."""
    try:
        folder = package.locate(token, request.user.pk)
        if not 0 <= index < limits()['files']:
            raise Http404
        response = FileResponse((folder / f'thumb-{index}.jpg').open('rb'), content_type='image/jpeg')
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except (ValidationError, OSError):
        raise Http404
