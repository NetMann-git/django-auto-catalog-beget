# apps/products/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings

from .constants import MAX_COMPARISON_ITEMS, MAX_RECENTLY_VIEWED
from .services import ProductService
from .context import CatalogContextBuilder

from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from django.urls import reverse
from apps.products.models import Brand

from apps.reviews.forms import ReviewForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ProductForm, GalleryImageForm

from .models import Product, ProductGalleryImage, AttributeType, AttributeValue, ProductAttribute

from .repository import CatalogRepository

from apps.users.decorators import role_required



def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    products = CatalogRepository.by_brand(brand)
    context = {
        'brand': brand,
        'products': products,
        'page': brand,  # для SEO (чтобы работал base.html)
    }
    return render(request, 'products/brand_detail.html', context)

@require_POST
def toggle_comparison_ajax(request, product_id):
    """
    AJAX-обработчик для добавления/удаления товара из сравнения.
    Возвращает JSON с новым состоянием и количеством товаров.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    comparison = request.session.get('comparison', [])
    is_added = False

    if product_id in comparison:
        comparison.remove(product_id)
        message = f"Товар «{product.title}» удалён из сравнения."
    else:
        # Проверка лимита для AJAX
        if len(comparison) >= MAX_COMPARISON_ITEMS:
            return JsonResponse({
                'error': True,
                'message': f'Можно добавить не более {MAX_COMPARISON_ITEMS} товаров.'
            }, status=400)
        comparison.append(product_id)
        is_added = True
        message = f"Товар «{product.title}» добавлен к сравнению."

    request.session['comparison'] = comparison
    count = len(comparison)

    return JsonResponse({
        'is_added': is_added,
        'count': count,
        'message': message,
    })


def catalog(request):
    context = CatalogContextBuilder.build(request)
    return render(request, "products/catalog.html", context)

def recently_viewed_list(request):
    """
    Страница со списком всех просмотренных товаров.
    """
    ids = request.session.get('recently_viewed', [])
    products = Product.objects.filter(id__in=ids, is_active=True)
    # Сохраняем порядок из сессии (сначала последние просмотренные)
    order = {id: i for i, id in enumerate(ids)}
    products = sorted(products, key=lambda p: order.get(p.id, 999))
    context = {
        'products': products,
        'catalog_url': reverse('catalog:catalog'),
    }
    return render(request, 'products/recently_viewed.html', context)

# @cache_page(60 * 5)  # 5 минут
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    context = {"product": product, "page": product}
    context.update(ProductService.context(product))
    
    # Сохраняем товар в список недавно просмотренных
    recently_viewed = request.session.get('recently_viewed', [])
    if product.id in recently_viewed:
        recently_viewed.remove(product.id)  # перемещаем в начало
    recently_viewed.insert(0, product.id)
    # Ограничиваем количество
    if len(recently_viewed) > MAX_RECENTLY_VIEWED:
        recently_viewed = recently_viewed[:MAX_RECENTLY_VIEWED]
    request.session['recently_viewed'] = recently_viewed

    # Получаем товары для блока «Недавно просмотренные» (без текущего)
    recent_ids = [pid for pid in recently_viewed if pid != product.id]
    recent_products = Product.objects.filter(id__in=recent_ids, is_active=True)
    # Сохраняем порядок из сессии
    order = {pid: i for i, pid in enumerate(recently_viewed)}
    recent_products = sorted(recent_products, key=lambda p: order.get(p.id, 999))
    context['recently_viewed_products'] = recent_products


    # Отзывы – фильтрация и сортировка
    reviews_qs = product.reviews.filter(is_published=True)

    # Фильтры
    rating_filter = request.GET.get('rating')
    if rating_filter and rating_filter.isdigit():
        reviews_qs = reviews_qs.filter(rating=int(rating_filter))

    with_photos = request.GET.get('with_photos')
    if with_photos == '1':
        reviews_qs = reviews_qs.filter(images__isnull=False).distinct()

    verified = request.GET.get('verified')
    if verified == '1':
        reviews_qs = reviews_qs.filter(is_verified=True)

    # Сортировка
    sort_by = request.GET.get('sort', '-helpful_count')
    if sort_by == 'created_at':
        reviews_qs = reviews_qs.order_by('-created_at')
    elif sort_by == 'rating':
        reviews_qs = reviews_qs.order_by('-rating')
    elif sort_by == 'helpful_count':
        reviews_qs = reviews_qs.order_by('-helpful_count')
    else:
        reviews_qs = reviews_qs.order_by('-helpful_count', '-created_at')

    context["reviews"] = reviews_qs
    context["selected_sort"] = sort_by
    context["selected_rating"] = rating_filter
    context["selected_with_photos"] = with_photos
    context["selected_verified"] = verified

    # Варианты для шаблона
    context["sort_options"] = [
        {'value': '-helpful_count', 'label': 'Новые и полезные'},
        {'value': '-created_at', 'label': 'По дате (новые)'},
        {'value': '-rating', 'label': 'С высокой оценкой'},
        {'value': 'rating', 'label': 'С низкой оценкой'},

    ]
    context["rating_options"] = [
        {'value': '', 'label': 'Все оценки'},
        {'value': '5', 'label': '5 ★'},
        {'value': '4', 'label': '4 ★ и выше'},
        {'value': '3', 'label': '3 ★ и выше'},
    ]

    context["review_form"] = ReviewForm(user=request.user)

    return render(request, "products/product_detail.html", context)

@require_POST
def clear_recently_viewed_ajax(request):
    """
    AJAX-очистка истории просмотров.
    """
    # Удаляем ключ из сессии
    if 'recently_viewed' in request.session:
        del request.session['recently_viewed']
    # Явно помечаем сессию как изменённую
    request.session.modified = True
    return JsonResponse({'success': True, 'count': 0})

def add_to_comparison(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    comparison = request.session.get('comparison', [])
    
    # Проверка лимита (добавляем)
    if len(comparison) >= MAX_COMPARISON_ITEMS:
        messages.warning(request, f"Можно добавить не более {MAX_COMPARISON_ITEMS} товаров для сравнения.")
        return redirect(request.META.get('HTTP_REFERER', 'catalog:catalog'))
    
    if product_id not in comparison:
        comparison.append(product_id)
        request.session['comparison'] = comparison
        messages.success(request, f"Товар «{product.title}» добавлен к сравнению.")
    else:
        messages.info(request, f"Товар «{product.title}» уже в списке сравнения.")
    
    return redirect(request.META.get('HTTP_REFERER', 'catalog:catalog'))


def remove_from_comparison(request, product_id):
    comparison = request.session.get('comparison', [])
    if product_id in comparison:
        comparison.remove(product_id)
        request.session['comparison'] = comparison
        messages.success(request, "Товар удалён из сравнения.")
    return redirect(request.META.get('HTTP_REFERER', 'catalog:catalog'))


def comparison_list(request):
    ids = request.session.get('comparison', [])
    products = Product.objects.filter(id__in=ids, is_active=True)
    # Сохраняем порядок, заданный пользователем
    order = {id: i for i, id in enumerate(ids)}
    products = sorted(products, key=lambda p: order.get(p.id, 999))

    # Собираем все характеристики для выбранных товаров
    attributes_data = {}
    for product in products:
        for attr in product.attributes.select_related('attribute_type').all():
            key = attr.attribute_type.name
            if key not in attributes_data:
                attributes_data[key] = {}
            attributes_data[key][product.id] = attr.attribute_value.value if attr.attribute_value else '—'

    # Формируем список строк для шаблона (упорядочиваем по типу)
    attributes_rows = []
    for attr_name, values in attributes_data.items():
        row = {'name': attr_name}
        for product in products:
            row[product.id] = values.get(product.id, '—')
        attributes_rows.append(row)

    context = {
        'products': products,
        'attributes_rows': attributes_rows,
    }
    return render(request, 'products/comparison.html', context)

@login_required
def product_list_manage(request):
    """Список товаров для управления (менеджер)."""
    if request.user.profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('users:dashboard')
    
    products = Product.objects.all().order_by('-id')  # ИСПРАВЛЕНО
    
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(title__icontains=search) |
            Q(article__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    context = {
        'products': products_page,
        'search': search,
        'total': products.count(),
    }
    return render(request, 'products/manage_list.html', context)

@role_required("manager", "admin")
def product_create(request):
    """Создание нового товара."""
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.title}" успешно создан!')
            return redirect('catalog:product_edit', product_id=product.id)
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Создание товара',
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_edit(request, product_id):
    """Редактирование товара."""
    if request.user.profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('users:dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Товар "{product.title}" успешно обновлён!')
            return redirect('catalog:product_edit', product_id=product.id)
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': 'Редактирование товара',
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, product_id):
    """Удаление товара."""
    if request.user.profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('users:dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_title = product.title
        product.delete()
        messages.success(request, f'Товар "{product_title}" удалён.')
        return redirect('catalog:product_list_manage')
    
    context = {
        'product': product,
    }
    return render(request, 'products/product_confirm_delete.html', context)


@login_required
def gallery_add(request, product_id):
    """Добавление изображения в галерею."""
    if request.user.profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('users:dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            gallery_image = form.save(commit=False)
            gallery_image.product = product
            gallery_image.save()
            messages.success(request, 'Изображение добавлено в галерею.')
        else:
            messages.error(request, 'Ошибка при добавлении изображения.')
    
    return redirect('catalog:product_edit', product_id=product.id)


@login_required
def gallery_delete(request, image_id):
    """Удаление изображения из галереи."""
    if request.user.profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('users:dashboard')
    
    image = get_object_or_404(ProductGalleryImage, id=image_id)
    product_id = image.product.id
    image.delete()
    messages.success(request, 'Изображение удалено из галереи.')
    
    return redirect('catalog:product_edit', product_id=product_id)


@login_required
def product_attributes(request, product_id):
    """Управление характеристиками товара."""
    if request.user.profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('users:dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    attribute_types = AttributeType.objects.all()
    product_attributes = product.attributes.select_related('attribute_type', 'attribute_value')
    
    # Данные для выпадающего списка значений
    values_data = {}
    for attr_type in attribute_types:
        values_data[str(attr_type.id)] = [
            {'id': v.id, 'value': v.value} 
            for v in attr_type.values.all()
        ]
    
    if request.method == 'POST':
        attr_type_id = request.POST.get('attribute_type')
        attr_value_id = request.POST.get('attribute_value')
        
        if attr_type_id and attr_value_id:
            attr_type = get_object_or_404(AttributeType, id=attr_type_id)
            attr_value = get_object_or_404(AttributeValue, id=attr_value_id)
            
            ProductAttribute.objects.update_or_create(
                product=product,
                attribute_type=attr_type,
                defaults={'attribute_value': attr_value}
            )
            messages.success(request, 'Характеристика добавлена.')
        else:
            messages.error(request, 'Выберите тип и значение.')
        
        return redirect('catalog:product_attributes', product_id=product.id)
    
    context = {
        'product': product,
        'product_attributes': product_attributes,
        'attribute_types': attribute_types,
        'values_data': values_data,
    }
    return render(request, 'products/product_attributes.html', context)

@login_required
def attribute_delete(request, attribute_id):
    """Удаление характеристики товара."""
    if request.user.profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('users:dashboard')
    
    attribute = get_object_or_404(ProductAttribute, id=attribute_id)
    product_id = attribute.product.id
    attribute.delete()
    messages.success(request, 'Характеристика удалена.')
    
    return redirect('catalog:product_attributes', product_id=product_id)