# apps/reviews/forms.py

from django import forms
from django.contrib.auth import get_user_model

from .models import Review, ReviewImage

User = get_user_model()


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "title", "text", "guest_name")
        widgets = {
            "rating": forms.RadioSelect(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Краткий заголовок"}),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Ваш отзыв..."}),
            "guest_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ваше имя"}),
        }
        labels = {
            "rating": "Ваша оценка",
            "title": "Заголовок",
            "text": "Текст отзыва",
            "guest_name": "Ваше имя",
        }

    images = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput,
        label="Фотография",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.product = kwargs.pop("product", None)  # ← добавляем
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            self.fields["guest_name"].widget = forms.HiddenInput()
            self.fields["guest_name"].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and self.user.is_authenticated:
            instance.user = self.user
        if self.product:
            instance.product = self.product
        instance.is_published = False
        instance.is_verified = False

        if commit:
            instance.save()

        # Сохраняем фото
        image = self.cleaned_data.get("images")
        if image:
            ReviewImage.objects.create(review=instance, image=image)

        return instance