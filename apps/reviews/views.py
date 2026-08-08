# apps/reviews/views.py
# from django.shortcuts import get_object_or_404, redirect

from .forms import ReviewForm
from .models import Review, ReviewVote
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse
from apps.products.models import Product

from apps.reviews.services import ReviewService

def filter_reviews(request, product_id):
    """
    Возвращает HTML-фрагмент со списком отфильтрованных и отсортированных отзывов.
    """

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )

    reviews_qs = ReviewService.get_reviews(
        product,
        request,
    )

    html = render_to_string(
        'reviews/_review_list.html',
        {
            'reviews': reviews_qs,
            'product': product,
        }
    )

    return JsonResponse({'html': html})


@require_POST
def vote_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, is_published=True)
    is_helpful = request.POST.get('is_helpful') == 'true'

    # Определяем идентификатор пользователя/сессии
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key

    # Проверяем, голосовал ли уже этот пользователь или сессия
    vote = ReviewVote.objects.filter(
        review=review,
        user=user,
        session_key=session_key
    ).first()

    if vote:
        # Если уже голосовал, изменяем или удаляем голос
        if vote.is_helpful == is_helpful:
            # Если голос такой же – удаляем (отмена голоса)
            vote.delete()
            if is_helpful:
                review.helpful_count -= 1
            else:
                review.unhelpful_count -= 1
            review.save()
            return JsonResponse({
                'status': 'removed',
                'helpful': review.helpful_count,
                'unhelpful': review.unhelpful_count,
                'user_vote': None
            })
        else:
            # Меняем голос
            vote.is_helpful = is_helpful
            vote.save()
            if is_helpful:
                review.helpful_count += 1
                review.unhelpful_count -= 1
            else:
                review.helpful_count -= 1
                review.unhelpful_count += 1
            review.save()
            return JsonResponse({
                'status': 'changed',
                'helpful': review.helpful_count,
                'unhelpful': review.unhelpful_count,
                'user_vote': is_helpful
            })
    else:
        # Новый голос
        ReviewVote.objects.create(
            review=review,
            user=user,
            session_key=session_key,
            is_helpful=is_helpful
        )
        if is_helpful:
            review.helpful_count += 1
        else:
            review.unhelpful_count += 1
        review.save()
        return JsonResponse({
            'status': 'added',
            'helpful': review.helpful_count,
            'unhelpful': review.unhelpful_count,
            'user_vote': is_helpful
        })

@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    form = ReviewForm(request.POST, request.FILES, user=request.user, product=product)
    if form.is_valid():
        review = form.save()
        messages.success(request, "Спасибо! Ваш отзыв будет опубликован после проверки.")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{error}")

    return redirect("catalog:product_detail", slug=product.slug)   