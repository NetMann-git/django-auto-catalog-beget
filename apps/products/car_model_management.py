"""Role-protected management of the vehicle model dictionary."""

from django.contrib import messages
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from apps.users.constants import ROLE_ADMIN, ROLE_MANAGER
from apps.users.decorators import role_required

from .cache import CatalogCache
from .car_model_forms import CarModelForm
from .models import Brand, CarModel


@role_required(ROLE_MANAGER, ROLE_ADMIN)
@require_safe
def car_model_list(request: HttpRequest) -> HttpResponse:
    """List models, optionally filtered by manufacturer."""
    brand_id = request.GET.get('brand', '')
    models = CarModel.objects.select_related('brand').annotate(
        product_count=Count('products'),
    )
    if brand_id:
        if brand_id.isascii() and brand_id.isdigit() and len(brand_id) < 19:
            models = models.filter(brand_id=brand_id)
        else:
            models = models.none()
    return render(request, 'products/car_models/list.html', {
        'car_models': models, 'brands': Brand.objects.all(),
        'selected_brand': brand_id,
    })


@role_required(ROLE_MANAGER, ROLE_ADMIN)
@require_http_methods(['GET', 'POST'])
def car_model_edit(request: HttpRequest, model_id: int | None = None) -> HttpResponse:
    """Create or edit a model without assigning products automatically."""
    instance = get_object_or_404(CarModel, pk=model_id) if model_id else None
    form = CarModelForm(
        request.POST if request.method == 'POST' else None, instance=instance,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        CatalogCache.clear_catalog()
        messages.success(request, 'Модель автомобиля сохранена.')
        return redirect('catalog:car_model_list')
    return render(request, 'products/car_models/form.html', {
        'form': form, 'car_model': instance,
    })


@role_required(ROLE_MANAGER, ROLE_ADMIN)
@require_http_methods(['GET', 'POST'])
def car_model_delete(request: HttpRequest, model_id: int) -> HttpResponse:
    """Require POST and protect models referenced by products."""
    instance = get_object_or_404(CarModel, pk=model_id)
    if request.method == 'POST':
        try:
            instance.delete()
        except ProtectedError:
            messages.error(request, 'Модель используется в товарах и не может быть удалена.')
        else:
            CatalogCache.clear_catalog()
            messages.success(request, 'Модель автомобиля удалена.')
        return redirect('catalog:car_model_list')
    return render(request, 'products/car_models/delete.html', {'car_model': instance})
