# apps/wishlist/context_processors.py

from .models import Favorite

def wishlist_count(request):
    if request.user.is_authenticated:
        count = Favorite.objects.filter(user=request.user).count()
    else:
        count = len(request.session.get('wishlist', []))
    return {"wishlist_count": count}