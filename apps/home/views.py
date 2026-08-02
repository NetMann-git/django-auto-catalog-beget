# apps\home\views.py

from django.shortcuts import render
from apps.products.models import Product, Category
from apps.reviews.models import Review

def home(request):
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    )[:8]
    
    categories = Category.objects.all()[:4]
    
    reviews = Review.objects.filter(
        is_published=True
    ).order_by('-created_at')[:3]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'reviews': reviews,
    }
    return render(request, 'home/home.html', context)