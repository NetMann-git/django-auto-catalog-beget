"""Upload and confirmation endpoints using the existing manager access policy."""
from django.contrib import messages
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.users.constants import ROLE_ADMIN, ROLE_MANAGER
from apps.users.decorators import role_required
from .forms import ImportForm, UploadForm
from .parser import parse
from .services import fingerprint, resolve_identity, save_import

SALT = 'products.encar.preview.v1'


@role_required(ROLE_MANAGER, ROLE_ADMIN)
@require_http_methods(['GET', 'POST'])
def import_encar(request: HttpRequest) -> HttpResponse:
    """Keep previews in signed user-bound payloads, not in product records."""
    if request.method == 'POST' and (
        request.POST.get('package_token') or
        getattr(request.FILES.get('file'), 'name', '').lower().endswith('.zip')
    ):
        from .package_views import handle_package
        return handle_package(request)
    upload = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'GET':
        listing_id = request.GET.get('listing_id', '').strip()
        lookup_source = None
        lookup_product = None
        lookup_error = ''
        if listing_id:
            if not listing_id.isascii() or not listing_id.isdigit() or len(listing_id) > 30:
                lookup_error = 'Введите числовой ID исходного объявления Encar.'
            else:
                try:
                    lookup_source, lookup_product = resolve_identity(listing_id)
                except ValidationError as error:
                    lookup_error = ' '.join(error.messages)
                else:
                    if lookup_product is None:
                        lookup_error = 'Автомобиль с этим ID или артикулом не найден. Загрузите JSON для предпросмотра новой карточки.'
        return render(request, 'products/encar_import/upload.html', {
            'form': upload, 'listing_id': listing_id,
            'lookup_source': lookup_source, 'lookup_product': lookup_product,
            'lookup_error': lookup_error,
        })
    if request.POST.get('action') == 'upload':
        if not upload.is_valid():
            return render(request, 'products/encar_import/upload.html', {'form': upload})
        proposal = parse(upload.raw)
        try:
            source, product = resolve_identity(proposal['listing_id'])
        except ValidationError as error:
            upload.add_error(None, error)
            return render(request, 'products/encar_import/upload.html', {'form': upload})
        payload = {'user': request.user.pk, 'raw': upload.raw,
                   'product_id': getattr(product, 'pk', None), 'fingerprint': fingerprint(product),
                   'imported_at': source.imported_at.isoformat() if source else None}
        token = signing.dumps(payload, salt=SALT, compress=True)
        form = ImportForm(proposal=proposal, product=product, token=token)
    else:
        token = request.POST.get('token', '')
        try:
            if len(token) > 2000000:
                raise signing.BadSignature
            payload = signing.loads(token, salt=SALT, max_age=1800)
            if payload['user'] != request.user.pk:
                raise signing.BadSignature
            proposal = parse(payload['raw'])
        except (signing.BadSignature, ValidationError, ValueError, KeyError, TypeError):
            messages.error(request, 'Предпросмотр истёк или повреждён. Загрузите файл заново.')
            return redirect('catalog:import_encar')
        try:
            source, product = resolve_identity(proposal['listing_id'])
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
            return redirect('catalog:import_encar')
        form = ImportForm(request.POST, proposal=proposal, product=product, token=token)
        if request.POST.get('action') == 'save' and form.is_valid():
            try:
                product, created, changes = save_import(form, proposal, payload)
            except ValidationError as error:
                form.add_error(None, error)
            except (IntegrityError, OperationalError):
                form.add_error(None, 'Не удалось сохранить: возможен одновременный импорт или изменение справочника. Загрузите файл заново. Частичные изменения отменены.')
            else:
                summary = 'Создан черновик.' if created else 'Автомобиль обновлён.'
                summary += ' Применено: ' + (', '.join(changes) or 'только данные источника') + '.'
                skipped = len(proposal['specs']) - len(form.attribute_forms)
                summary += f' Пропущено характеристик: {skipped}. Предупреждений: {len(form.warnings)}.'
                messages.success(request, summary)
                return redirect('catalog:product_edit', product_id=product.pk)
    general = [form[name] for name in ('apply_title', 'title', 'apply_description', 'description',
               'apply_identity', 'brand', 'car_model', 'category', 'price', 'availability') if name in form.fields]
    return render(request, 'products/encar_import/preview.html', {
        'form': form, 'general': general, 'proposal': proposal, 'product': product,
        'matched_by_article': product is not None and source is None,
        'current_equipment': product.equipment.all() if product else [],
        'current_attributes': product.attributes.select_related('attribute_type', 'attribute_value') if product else [],
    })
