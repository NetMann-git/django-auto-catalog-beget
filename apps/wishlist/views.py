# apps/wishlist/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from django.contrib.auth import login

from apps.products.models import Product
from .models import Favorite


class WishlistView(ListView):
    model = Favorite
    template_name = "wishlist/wishlist.html"
    context_object_name = "favorites"
    allow_empty = True

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Favorite.objects.filter(user=self.request.user).select_related("product")
        return Favorite.objects.none()  # для гостей пустой queryset, товары будем брать из сессии

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            # Для авторизованных: список товаров уже в favorites
            products = [f.product for f in context["favorites"]]
            wishlist_ids = list(self.request.user.favorites.values_list("product_id", flat=True))
        else:
            # Для гостей: берём товары из сессии
            wishlist_ids = self.request.session.get('wishlist', [])
            products = Product.objects.filter(id__in=wishlist_ids, is_active=True)

        context["products"] = products
        context["wishlist_ids"] = wishlist_ids
        context["is_guest"] = not self.request.user.is_authenticated

        return context


@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.user.is_authenticated:
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if not created:
            favorite.delete()
            is_favorite = False
        else:
            is_favorite = True
        count = Favorite.objects.filter(user=request.user).count()
    else:
        wishlist = request.session.get('wishlist', [])
        if product.id in wishlist:
            wishlist.remove(product.id)
            is_favorite = False
        else:
            wishlist.append(product.id)
            is_favorite = True
        request.session['wishlist'] = wishlist
        count = len(wishlist)

    return JsonResponse({
        "is_favorite": is_favorite,
        "count": count,
    })