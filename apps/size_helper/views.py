# apps/size_helper/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import SizeRecommendation, SizeTable

def size_helper_modal(request):
    return render(request, 'size_helper/_size_helper_modal.html')

def size_helper_form(request):
    """
    Страница с формой размерного помощника.
    """
    return render(request, 'size_helper/form.html')

def size_table_modal(request):
    """
    Возвращает HTML-фрагмент с таблицей размеров.
    """
    sizes = SizeTable.objects.all().order_by('sort_order')
    return render(request, 'size_helper/_size_table_modal.html', {'sizes': sizes})


@require_GET
def get_size_recommendation(request):
    """
    AJAX-эндпоинт: по параметрам пользователя возвращает рекомендуемый размер.
    """
    height = request.GET.get('height')
    bust = request.GET.get('bust')
    waist = request.GET.get('waist')
    hips = request.GET.get('hips')

    # Проверяем, что все параметры переданы и являются числами
    try:
        height = int(height)
        bust = int(bust)
        waist = int(waist)
        hips = int(hips)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Все параметры должны быть числами'}, status=400)

    # Ищем подходящую рекомендацию
    recommendation = SizeRecommendation.objects.filter(
        height_min__lte=height,
        height_max__gte=height,
        bust_min__lte=bust,
        bust_max__gte=bust,
        waist_min__lte=waist,
        waist_max__gte=waist,
        hips_min__lte=hips,
        hips_max__gte=hips,
    ).first()

    if recommendation:
        return JsonResponse({
            'success': True,
            'size': recommendation.size,
            'description': recommendation.description,
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Не удалось подобрать размер. Попробуйте скорректировать параметры или обратитесь к консультанту.',
        })