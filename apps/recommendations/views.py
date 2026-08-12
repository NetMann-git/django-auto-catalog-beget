# apps\recommendations\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import PromotedProduct
from .forms import PromotedProductForm

def is_manager(user):
    return user.is_authenticated and user.profile.role == 'manager'

@user_passes_test(is_manager)
def manage_recommendations(request):
    promotions = PromotedProduct.objects.select_related('product').order_by('-priority', '-id')
    form = PromotedProductForm()
    return render(request, 'recommendations/manage.html', {
        'promotions': promotions,
        'form': form,
        'page_choices': PromotedProduct.PAGE_CHOICES,
    })

@user_passes_test(is_manager)
def add_recommendation(request):
    if request.method == 'POST':
        form = PromotedProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар добавлен в рекомендации.')
            return redirect('recommendations:manage')
    return redirect('recommendations:manage')

@user_passes_test(is_manager)
def edit_recommendation(request, pk):
    promotion = get_object_or_404(PromotedProduct, pk=pk)
    if request.method == 'POST':
        form = PromotedProductForm(request.POST, instance=promotion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения сохранены.')
            return redirect('recommendations:manage')
    else:
        form = PromotedProductForm(instance=promotion)
    return render(request, 'recommendations/edit.html', {'form': form, 'promotion': promotion})

@user_passes_test(is_manager)
def delete_recommendation(request, pk):
    promotion = get_object_or_404(PromotedProduct, pk=pk)
    promotion.delete()
    messages.success(request, 'Рекомендация удалена.')
    return redirect('recommendations:manage')

@user_passes_test(is_manager)
def toggle_active(request, pk):
    promotion = get_object_or_404(PromotedProduct, pk=pk)
    promotion.is_active = not promotion.is_active
    promotion.save()
    return redirect('recommendations:manage')