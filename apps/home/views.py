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

    if request.user.is_authenticated:
        wishlist_ids = list(request.user.favorites.values_list("product_id", flat=True))
    else:
        wishlist_ids = request.session.get('wishlist', [])
    context["wishlist_ids"] = wishlist_ids

    return render(request, 'home/home.html', context)